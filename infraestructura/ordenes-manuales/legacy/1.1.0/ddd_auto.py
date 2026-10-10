"""DDD auto 1.1.0; 2026-10-10; local candidate, no production authority.
New module of ddd, origin: manual launcher 1.0.0. Append-only attempts,
technical dependencies, deterministic gates and separate read-only review.
"""
import contextlib
import datetime
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import signal
import subprocess
import tempfile
import time
import uuid

TERMINAL = {'TECH_PASS', 'BLOCKED', 'REVIEW_NO_GO', 'WAIT_OWNER'}
RESERVED = {'F01', 'N01'}
ACTIVE_LOCKS = []


def digest(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def load(path):
    return json.loads(Path(path).read_text())


def write_new(path, value):
    with Path(path).open('x', encoding='utf-8') as f:
        json.dump(value, f, ensure_ascii=False, indent=2)
        f.write('\n'); f.flush(); os.fsync(f.fileno())


def read_events(path):
    if not path.exists():
        return []
    # Corrupt journals fail closed: never silently forget a STARTED attempt.
    events = [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
    if any(not isinstance(e, dict) or 'task' not in e for e in events):
        raise ValueError('Registro de historial/diario inválido')
    return events


def append(path, value):
    value = dict(value, date_utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
    with path.open('a', encoding='utf-8') as f:
        f.write(json.dumps(value, ensure_ascii=False) + '\n')
        f.flush(); os.fsync(f.fileno())


@contextlib.contextmanager
def lock(path):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('a+') as f:
        try:
            fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise RuntimeError(f'Concurrencia bloqueada: {path}')
        ACTIVE_LOCKS.append(f.fileno())
        try:
            yield
        finally:
            ACTIVE_LOCKS.remove(f.fileno())


def worktree_lock(repo):
    # Independent of launcher DATA and identical for manual and auto.
    key = hashlib.sha256(str(Path(repo).resolve()).encode()).hexdigest()
    return lock(Path(tempfile.gettempdir()) / 'ddd-worktree-locks' / (key + '.lock'))


def graph(tasks):
    visited, active = set(), set()
    def visit(tid):
        if tid in active:
            raise ValueError('Ciclo de dependencias: ' + tid)
        if tid not in tasks:
            raise ValueError('Dependencia desconocida: ' + tid)
        if tid in visited:
            return
        active.add(tid)
        for dep in tasks[tid]['depends_on']:
            visit(dep)
        active.remove(tid); visited.add(tid)
    for tid in tasks:
        visit(tid)


def seed_status(policy):
    out = {}
    for tid, seed in policy.get('technical_seeds', {}).items():
        try:
            p = Path(seed['path']).expanduser()
            if digest(p) != seed['sha256'] or seed['kind'] != 'F02_14_OFFLINE' or tid != 'F02':
                raise ValueError('Credencial F02 inválida')
            x = load(p)
            rows = x['rows']
            if len(rows) != 14 or len({r['territory_id'] for r in rows}) != 14:
                raise ValueError('F02 exige 14 identidades únicas')
            if x['originals_unchanged'] is not True or x['network'] != 'FORBIDDEN':
                raise ValueError('F02 sin integridad/sin red')
            for r in rows:
                for c in ('F02_inventory_receipt_origin', 'F02_bytes_hashes_editions'):
                    if r['controls'][c] != 'PASS':
                        raise ValueError('F02 no acreditado')
                if digest(r['artifact_path']) != r['artifact_sha256']:
                    raise ValueError('Bytes F02 cambiaron: ' + r['territory_id'])
                receipt = Path(seed['repo']).expanduser() / r['receipt_path']
                if digest(receipt) != r['details']['F02_inventory_receipt_origin']['receipt_sha256']:
                    raise ValueError('Receipt F02 cambió')
            out[tid] = {'state': 'TECH_PASS', 'evidence': str(p), 'sha256': seed['sha256'],
                        'scope': '14 paquetes offline; no cierre formal ni generación'}
        except (OSError, ValueError, KeyError, TypeError) as e:
            out[tid] = {'state': 'BLOCKED', 'reason': str(e)}
    return out


def criteria(task, policy):
    spec = policy.get('tasks', {}).get(task['id'], {})
    checks = spec.get('validators', [])
    covered = {c for v in checks for c in v.get('covers', [])}
    expected = set(range(len(task['acceptance'])))
    sufficient = bool(checks) and covered == expected and all(
        v.get('argv') and v.get('local_only') is True for v in checks)
    return spec, sufficient


def assess(app, selected, policy, events):
    formal = app.local_plan_status()
    seeds = seed_status(policy)
    latest = {e['task']: e for e in events if 'task' in e}
    historic = {h['task']: h for h in read_events(app.DATA/'historial.jsonl') if 'task' in h}
    states = {}
    for tid, task in app.TASKS.items():
        previous = latest.get(tid)
        if previous:
            states[tid] = previous.get('state', 'BLOCKED')
        elif tid in policy.get('formal_pending', []):
            states[tid] = 'WAIT_OWNER'
        elif formal.get(tid) == 'PASS' and tid not in policy.get('revalidate', []):
            states[tid] = 'FORMAL_PASS'
        elif seeds.get(tid, {}).get('state') == 'TECH_PASS':
            states[tid] = 'TECH_PASS'
        else:
            states[tid] = 'PENDING'
    rows = []
    for tid in selected:
        t = app.TASKS[tid]
        spec, sufficient = criteria(t, policy)
        deps = [{'task': d, 'state': states[d], 'external_to_batch': d not in selected,
                 'satisfied': states[d] in ('TECH_PASS', 'FORMAL_PASS')}
                for d in t['depends_on']]
        ancestors = set()
        def collect(node):
            for dep in app.TASKS[node]['depends_on']:
                if dep not in ancestors:
                    ancestors.add(dep); collect(dep)
        collect(tid)
        formal_pending = sorted(d for d in ancestors if formal.get(d) != 'PASS' or d in policy.get('formal_pending', []))
        pending = [d['task'] for d in deps if not d['satisfied']]
        reasons = []
        state = states[tid]
        if tid in latest:
            reasons.append('Intento anterior conservado; sin repetición automática')
            if state == 'STARTED':
                state = 'BLOCKED'; reasons.append('Intento interrumpido; requiere decisión humana')
        elif state in ('TECH_PASS', 'FORMAL_PASS'):
            reasons.append('Ya acreditada; se conserva evidencia')
        elif t['execution'] == 'approval' or tid in RESERVED or tid in policy.get('formal_pending', []):
            state = 'WAIT_OWNER'; reasons.append('Autoridad humana reservada')
        elif tid not in policy.get('authorized_local_tasks', []):
            state = 'WAIT_OWNER'; reasons.append('Sin encargo local autorizado en la política de campaña')
        elif pending:
            state = 'BLOCKED'; reasons.append('Dependencias técnicas ausentes: ' + ', '.join(pending))
        elif not sufficient:
            state = 'BLOCKED'; reasons.append('Criterios ejecutables insuficientes')
        elif tid in historic and historic[tid].get('result') != 'DONE_REVIEW':
            state = 'WAIT_OWNER'; reasons.append('Intento manual fallido; no retry automático')
        else:
            state = 'ENABLED'
        rows.append({'task': tid, 'state': state, 'reasons': reasons, 'dependencies': deps,
                     'formal_dependencies_pending': formal_pending,
                     'mode': 'validate_existing' if tid in historic or spec.get('validate_existing') else 'execute'})
    return rows, seeds


def run_process(argv, cwd, prompt, logfile, timeout, stop_process):
    started = time.monotonic()
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1')
    with logfile.open('x') as log:
        p = subprocess.Popen(argv, cwd=cwd, env=env, stdin=subprocess.PIPE if prompt is not None else subprocess.DEVNULL,
                             stdout=log, stderr=subprocess.STDOUT, text=True, start_new_session=True,
                             pass_fds=tuple(ACTIVE_LOCKS))
        write_new(logfile.with_suffix('.process.json'), {'pid': p.pid, 'argv': argv, 'cwd': str(cwd)})
        try:
            p.communicate(input=prompt, timeout=timeout)
        except subprocess.TimeoutExpired:
            stop_process(p)
            return {'argv': argv, 'exit_code': p.returncode, 'timeout': True, 'seconds': time.monotonic()-started}
        except BaseException:
            stop_process(p)
            raise
    return {'argv': argv, 'exit_code': p.returncode, 'timeout': False, 'seconds': time.monotonic()-started}


def codex_cmd(app, role, schema=None, output=None):
    sandbox = 'workspace-write' if role == 'executor' else 'read-only'
    effort = app.CFG['esfuerzo_ejecutor' if role == 'executor' else 'esfuerzo_revisor']
    cmd = [app.CFG['codex_bin'], '--sandbox', sandbox, '--ask-for-approval', 'never',
           '-c', f'model_reasoning_effort={effort}', '-c', 'sandbox_workspace_write.network_access=false',
           'exec', '--json', '--ephemeral']
    if schema:
        cmd += ['--skip-git-repo-check', '--output-schema', str(schema), '--output-last-message', str(output)]
    return cmd + ['-']


def session_id(logfile):
    ids = []
    completed = False
    for line in logfile.read_text().splitlines():
        try:
            v = json.loads(line)
        except ValueError:
            continue
        if v.get('type') == 'thread.started':
            ids.append(v.get('thread_id'))
        if v.get('type') in ('turn.failed', 'error'):
            raise ValueError('Codex emitió error aunque el proceso terminara')
        if v.get('type') == 'turn.completed':
            completed = True
    if len(ids) != 1 or not ids[0] or not completed:
        raise ValueError('No existe identidad inequívoca de sesión Codex')
    return ids[0]


def repo_files(app, repo):
    raw = subprocess.check_output(['git', '-C', str(repo), 'ls-files', '-z', '--cached', '--others', '--exclude-standard'])
    out = {}
    for name in set(raw.decode().split('\0')) - {''}:
        path = repo / name
        if path.is_symlink():
            raise ValueError('Entrega con enlaces no admitida: ' + name)
        if path.is_file():
            out[name] = digest(path)
    return out


def copy_tree(repo, target, files):
    target.mkdir()
    for name, expected in files.items():
        source = repo / name
        dest = target / name
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, dest)
        if digest(dest) != expected:
            raise ValueError('Archivo cambió durante captura: ' + name)


def manifest_files(root):
    return {str(p.relative_to(root)): digest(p) for p in sorted(root.rglob('*')) if p.is_file()}


def seal(root):
    for p in root.rglob('*'):
        p.chmod(0o555 if p.is_dir() else (0o555 if os.access(p, os.X_OK) else 0o444))
    root.chmod(0o555)


def validate_schema(value, schema, location='$'):
    """Closed JSON Schema subset used by review.schema.json; unsupported keywords fail."""
    supported = {'$schema', 'title', 'type', 'properties', 'required', 'additionalProperties',
                 'enum', 'const', 'items', 'minItems', 'minLength', 'pattern'}
    if set(schema) - supported:
        raise ValueError('Keyword de esquema no soportado')
    types = {'object': dict, 'array': list, 'string': str, 'boolean': bool}
    if 'type' in schema and not isinstance(value, types[schema['type']]):
        raise ValueError('Tipo inválido en ' + location)
    if 'enum' in schema and value not in schema['enum']:
        raise ValueError('Enum inválido en ' + location)
    if 'const' in schema and value != schema['const']:
        raise ValueError('Const inválido en ' + location)
    if isinstance(value, dict):
        props = schema.get('properties', {})
        if set(schema.get('required', [])) - set(value):
            raise ValueError('Campos requeridos ausentes en ' + location)
        if schema.get('additionalProperties') is False and set(value) - set(props):
            raise ValueError('Campos desconocidos en ' + location)
        for k, v in value.items():
            if k in props:
                validate_schema(v, props[k], location + '.' + k)
    if isinstance(value, list):
        if len(value) < schema.get('minItems', 0):
            raise ValueError('Array vacío en ' + location)
        for v in value:
            validate_schema(v, schema.get('items', {}), location + '[]')
    if isinstance(value, str):
        if len(value) < schema.get('minLength', 0) or ('pattern' in schema and not re.search(schema['pattern'], value)):
            raise ValueError('Cadena inválida en ' + location)


def check_review(verdict, schema, task, bundle_hash, head, files):
    validate_schema(verdict, schema)
    if verdict['task'] != task['id'] or verdict['delivery_sha256'] != bundle_hash or verdict['head'] != head:
        raise ValueError('Dictamen de otra entrega')
    if any(p not in files for p in verdict['evidence']):
        raise ValueError('Referencia de evidencia fuera de entrega')
    if verdict['verdict'] == 'PASS':
        if verdict['findings'] or set(verdict['criteria_passed']) != set(task['acceptance']):
            raise ValueError('PASS sin todos los criterios o con hallazgos')
    if verdict['verdict'] == 'NO_GO' and not verdict['findings']:
        raise ValueError('NO_GO sin hallazgo')


def capture_failure(app, task, folder, record):
    """Collect actual partial bytes/HEAD even if Codex's event stream is broken."""
    try:
        repo = app.real_repo(task['front'])
        files = repo_files(app, repo)
        baseline = load(folder/'before.json')['files'] if (folder/'before.json').exists() else {}
        record.update(head_end=app.git(repo, 'rev-parse', 'HEAD'),
                      changes=sorted(n for n in set(baseline) | set(files) if baseline.get(n) != files.get(n)))
        partial = folder/'failure-delivery'; partial.mkdir()
        copy_tree(repo, partial/'tree', files)
        write_new(partial/'capture.json', {'head': record['head_end'], 'files': files,
                  'status': app.git(repo, 'status', '--porcelain'), 'diff': app.git(repo, 'diff', 'HEAD', '--binary')})
        seal(partial)
        record['partial_delivery'] = str(partial)
    except (OSError, ValueError, RuntimeError, KeyError) as e:
        record['capture_error'] = str(e)


def attempt(app, row, policy, folder, journal):
    tid = row['task']; task = app.TASKS[tid]; spec, _ = criteria(task, policy)
    folder.mkdir()
    append(journal, {'task': tid, 'state': 'STARTED', 'attempt': str(folder), 'dependencies': row['dependencies']})
    record = {'task': tid, 'front': task['front'], 'dependencies': row['dependencies'], 'attempt': str(folder), 'mode': row['mode']}
    try:
        repo, head, dirty = app.verify_repo(task['front'])
        before = repo_files(app, repo)
        record.update(head_start=head, dirty_start=dirty)
        write_new(folder/'before.json', {'head': head, 'status': dirty, 'files': before,
                                        'diff': app.git(repo, 'diff', 'HEAD', '--binary')})
        executor_id = None
        if row['mode'] == 'execute':
            # Existing modifications cannot be attributed safely to this attempt.
            if dirty:
                previous = [e for e in read_events(journal) if e.get('front') == task['front'] and e.get('worktree_files')]
                checkpoint = previous[-1] if previous else {}
                if checkpoint.get('worktree_files') != before or checkpoint.get('head_end') != head:
                    raise ValueError('Worktree sucio sin checkpoint propio: conservar y someter a decisión humana')
            prompt = app.prompt_master(task) + '\nModo AUTO: no preguntes al propietario entre tareas. No encadenes. No cambies Plan, historial ni política del controlador. No hagas commit; el controlador captura la entrega. No ejecutes tareas productivas, red, push, PR, merge o publicación.\n'
            write_new(folder/'executor-prompt.json', {'prompt': prompt})
            result = run_process(codex_cmd(app, 'executor'), repo, prompt, folder/'executor.jsonl',
                                 app.CFG['segundos_maximos'], app.stop_process)
            record['executor'] = result
        after = repo_files(app, repo)
        record['worktree_files'] = after
        record['head_end'] = app.git(repo, 'rev-parse', 'HEAD')
        changes = sorted(n for n in set(before) | set(after) if before.get(n) != after.get(n))
        record['changes'] = changes
        delivery = folder/'delivery'; delivery.mkdir()
        copy_tree(repo, delivery/'tree', after)
        write_new(delivery/'changes.json', dict(record, files=after, diff=app.git(repo, 'diff', head, '--binary')))
        shutil.copy2(folder/'before.json', delivery/'before.json')
        verified_seeds = seed_status(policy)
        for dependency in row['dependencies']:
            if dependency['task'] in verified_seeds and verified_seeds[dependency['task']]['state'] != 'TECH_PASS':
                raise ValueError('Credencial de dependencia cambió durante ejecución')
        write_new(delivery/'dependencies.json', {'technical': row['dependencies'],
                  'formal_pending': row['formal_dependencies_pending'], 'seeds': verified_seeds})
        inputs = delivery/'inputs'; inputs.mkdir()
        for seed_id, seed in verified_seeds.items():
            if seed['state'] == 'TECH_PASS':
                shutil.copy2(seed['evidence'], inputs/(seed_id+'-seed.json'))
                if digest(inputs/(seed_id+'-seed.json')) != seed['sha256']:
                    raise ValueError('Credencial cambió durante captura')
        controller = delivery/'controller'; controller.mkdir()
        for name in ('ddd_auto.py', 'validar_piloto.py', 'review.schema.json'):
            shutil.copy2(app.BASE/name, controller/name)
        write_new(controller/'policy.json', policy)
        for name, item in spec.get('inputs', {}).items():
            if not re.fullmatch(r'[a-zA-Z0-9_.-]+', name):
                raise ValueError('Nombre de entrada inválido')
            source = Path(item['path']).expanduser()
            if digest(source) != item['sha256']:
                raise ValueError('Entrada cambió: ' + name)
            shutil.copy2(source, inputs/name)
            if digest(inputs/name) != item['sha256']:
                raise ValueError('Entrada cambió durante captura')
        if executor_id:
            shutil.copy2(folder/'executor.jsonl', delivery/'executor.jsonl')
        elif (folder/'executor.jsonl').exists():
            shutil.copy2(folder/'executor.jsonl', delivery/'executor.jsonl')
        if repo_files(app, repo) != after:
            raise ValueError('Worktree cambió durante captura')
        if row['mode'] == 'execute' and (result['exit_code'] != 0 or result['timeout']):
            raise ValueError('Ejecutor falló o agotó tiempo')
        if row['mode'] == 'execute':
            executor_id = session_id(folder/'executor.jsonl')
        if record['head_end'] != head:
            raise ValueError('Ejecutor cambió HEAD; revisión de alcance requerida')
        prefixes = spec.get('allowed_change_prefixes', ['docs/AUDITORIAS/', 'tests/', 'herramientas/'])
        if any(not any(n.startswith(p) for p in prefixes) for n in changes):
            raise ValueError('Cambios fuera del alcance local')
        tests = []
        for i, validator in enumerate(spec['validators']):
            variables = {'python': app.CFG['python_gis'], 'base': str(controller), 'repo': str(delivery/'tree'), 'inputs': str(inputs),
                         'output': str(delivery/f'validator-{i}.json')}
            argv = [s.format(**variables) for s in validator['argv']]
            r = run_process(argv, delivery/'tree', None, delivery/f'validator-{i}.log',
                            app.CFG['segundos_maximos'], app.stop_process)
            r['covers'] = validator['covers']; tests.append(r)
        write_new(delivery/'tests.json', tests); record['tests'] = tests
        if repo_files(app, repo) != after:
            raise ValueError('El worktree cambió durante pruebas')
        if seed_status(policy) != verified_seeds:
            raise ValueError('Credencial de dependencia cambió durante pruebas')
        if manifest_files(delivery/'tree') != after:
            raise ValueError('Validador alteró la entrega')
        files = manifest_files(delivery)
        write_new(folder/'delivery-manifest.json', {'task': tid, 'head': record['head_end'], 'files': files})
        bundle_hash = digest(folder/'delivery-manifest.json'); record['delivery_sha256'] = bundle_hash
        seal(delivery)
        if any(t['exit_code'] != 0 or t['timeout'] for t in tests):
            raise ValueError('Validadores deterministas fallidos; sin TECH_PASS')
        record['technical_validation'] = 'TECH_PASS'
        schema_path = folder/'review.schema.json'
        shutil.copy2(app.BASE/'review.schema.json', schema_path)
        review_prompt = (f'Actúa como Revisor DDD en sesión separada, solo lectura. Work dirige. '
                         f'Tarea {tid}: {task["title"]}. Criterios: {json.dumps(task["acceptance"],ensure_ascii=False)}. '
                         f'Entrega congelada {delivery}; manifiesto {folder/"delivery-manifest.json"}; '
                         f'SHA256 del manifiesto {bundle_hash}; HEAD {record["head_end"]}. '
                         'Lee cambios, contexto, pruebas y evidencias. Revisa cada criterio y casos negativos. '
                         'No ejecutes tests, código del paquete, red, producción, push, PR, merge ni publicación. '
                         'No modifiques nada. PASS es solo técnico local, nunca formal. '
                         'Devuelve exclusivamente JSON conforme al esquema. Referencia evidencia con rutas relativas a delivery. '
                         'Si falta prueba esencial: NO_GO. Si requiere autoridad humana: WAIT_OWNER.')
        write_new(folder/'review-prompt.json', {'prompt': review_prompt})
        result = run_process(codex_cmd(app, 'reviewer', schema_path, folder/'review.json'), delivery,
                             review_prompt, folder/'reviewer.jsonl', app.CFG['segundos_maximos'], app.stop_process)
        record['reviewer'] = result
        reviewer_id = session_id(folder/'reviewer.jsonl')
        record.update(executor_session=executor_id, reviewer_session=reviewer_id)
        if reviewer_id == executor_id or result['exit_code'] != 0 or result['timeout']:
            raise ValueError('Revisión no completada o sin separación')
        if digest(folder/'delivery-manifest.json') != bundle_hash or manifest_files(delivery) != files:
            raise ValueError('Entrega alterada durante revisión')
        verdict = load(folder/'review.json')
        check_review(verdict, load(schema_path), task, bundle_hash, record['head_end'], files)
        record['review'] = verdict
        record['state'] = {'PASS': 'TECH_PASS', 'NO_GO': 'REVIEW_NO_GO', 'WAIT_OWNER': 'WAIT_OWNER'}[verdict['verdict']]
    except KeyboardInterrupt:
        record.update(state='BLOCKED', reason='INTERRUPTED; sin repetición automática')
        capture_failure(app, task, folder, record)
        write_new(folder/'result.json', record)
        write_new(folder/'evidence-hashes.json', manifest_files(folder)); append(journal, record)
        raise
    except (OSError, ValueError, KeyError, RuntimeError, TypeError) as e:
        record.update(state='BLOCKED', reason=str(e))
        capture_failure(app, task, folder, record)
    write_new(folder/'result.json', record)
    # Failed attempts retain partial logs as well, with their own final hash list.
    write_new(folder/'evidence-hashes.json', manifest_files(folder))
    append(journal, record)
    return record


def campaign(app, args):
    def interrupted(signum, frame):
        raise KeyboardInterrupt('Signal ' + str(signum))
    old = signal.signal(signal.SIGTERM, interrupted)
    try:
        return run_campaign(app, args)
    finally:
        signal.signal(signal.SIGTERM, old)


def run_campaign(app, args):
    graph(app.TASKS)
    selected = args.tasks or list(app.TASKS)
    if len(set(selected)) != len(selected) or any(t not in app.TASKS for t in selected):
        raise ValueError('IDs desconocidos o repetidos')
    policy = load(args.policy)
    root = app.DATA/'auto'; journal = root/'eventos.jsonl'
    events = read_events(journal)
    rows, seeds = assess(app, selected, policy, events)
    if args.dry_run:
        for row in rows:
            print(json.dumps(row, ensure_ascii=False))
        print('F01: pendiente formal en esta campaña; Plan e historial conservados. Cero Codex.')
        return 0
    root.mkdir(parents=True, exist_ok=True)
    with lock(root/'.controller.lock'):
        events = read_events(journal)
        if args.resume:
            if not re.fullmatch(r'[a-zA-Z0-9_-]+', args.resume):
                raise ValueError('Identidad de campaña inválida')
            folder = root/args.resume
            original = load(folder/'campaign.json')
            if (original['selected'] != selected or original['policy'] != policy or
                original['catalog'] != app.CAT or original['parameters'] != app.CFG):
                raise ValueError('Reanudar requiere el mismo lote, política, catálogo y parámetros')
        else:
            stamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ') + '-' + uuid.uuid4().hex[:8]
            folder = root/stamp; folder.mkdir()
            write_new(folder/'campaign.json', {'selected': selected, 'policy': policy, 'catalog': app.CAT,
                       'parameters': app.CFG, 'plan_states': app.local_plan_status(), 'technical_seeds': seeds,
                       'legacy_history_sha256': digest(app.DATA/'historial.jsonl') if (app.DATA/'historial.jsonl').exists() else None})
        # A persisted STARTED is a spent attempt, even after SIGKILL.
        latest = {e['task']: e for e in events if 'task' in e}
        for tid, e in latest.items():
            if e.get('state') == 'STARTED':
                append(journal, dict(e, state='BLOCKED', reason='INTERRUPTED_OR_ORPHAN; requiere decisión humana'))
        print('CAMPAÑA', folder.name, flush=True)
        deferred = {}
        while True:
            rows, seeds = assess(app, selected, policy, read_events(journal))
            rows = [dict(r, state='BLOCKED', reasons=[deferred[r['task']]]) if r['task'] in deferred else r for r in rows]
            enabled = next((r for r in rows if r['state'] == 'ENABLED'), None)
            if enabled is None:
                break
            t = app.TASKS[enabled['task']]
            # Also interlock installed legacy manual/batch controllers.
            try:
                with contextlib.ExitStack() as stack:
                    stack.enter_context(worktree_lock(app.real_repo(t['front'])))
                    stack.enter_context(lock(app.DATA/f'.manual-{t["front"]}.lock'))
                    stack.enter_context(lock(app.DATA/f'.batch-{t["front"]}.lock'))
                    result = attempt(app, enabled, policy, folder/enabled['task'], journal)
                    print(enabled['task'], result['state'], result.get('reason', ''), flush=True)
            except RuntimeError as e:
                # Not attempted: preserve availability for a later campaign.
                deferred[enabled['task']] = str(e)
        summary = {'campaign': folder.name, 'tasks': rows, 'technical_seeds': seeds,
                   'formal_reservations': policy.get('formal_pending', []), 'production_authorized': False}
        # Each resumption adds a new summary; prior evidence is never rewritten.
        output = folder/('summary-' + uuid.uuid4().hex + '.json')
        write_new(output, summary)
        print('RESUMEN', output)
        for row in rows:
            print(row['task'], row['state'], '; '.join(row['reasons']))
        return 0 if all(r['state'] in ('TECH_PASS', 'FORMAL_PASS') for r in rows) else 1
