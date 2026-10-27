"""DDD auto 1.3.0; 2026-10-11; local candidate, no production authority.
Predecessor: legacy/1.2.0/ddd_auto.py. Expandable DAG, owner windows, night
preflight, scoped read-only snapshots, quota checkpoint and morning inbox.
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

TERMINAL = {'TECH_PASS', 'REVIEW_NO_GO'}
STATIONARY = {'BLOCKED', 'WAIT_OWNER', 'QUOTA_STOP', 'INTERRUPTED'}
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
    atomic_write(Path(path), json.dumps(value, ensure_ascii=False, indent=2)+'\n', exclusive=True)


def atomic_write(path, content, exclusive=False):
    """Publish whole files only; a killed writer cannot leave a partial event."""
    fd, name = tempfile.mkstemp(prefix='.atomic-', dir=path.parent)
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as f:
            f.write(content); f.flush(); os.fsync(f.fileno())
        if exclusive:
            os.link(name, path)
        else:
            os.replace(name, path)
        directory = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
    finally:
        if os.path.exists(name):
            os.unlink(name)


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
    # Caller owns the campaign controller lock. Old event bytes remain exact.
    old = path.read_text() if path.exists() else ''
    atomic_write(path, old + json.dumps(value, ensure_ascii=False) + '\n')


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


@contextlib.contextmanager
def session_slot():
    for i in range(2):
        slot = lock(Path(tempfile.gettempdir())/'ddd-worktree-locks'/f'codex-slot-{i}.lock')
        try:
            slot.__enter__()
        except RuntimeError:
            continue
        try:
            yield
        finally:
            slot.__exit__(None, None, None)
        return
    raise RuntimeError('Concurrencia bloqueada: máximo dos sesiones Codex')


def gis_lock(required):
    return lock(Path(tempfile.gettempdir())/'ddd-worktree-locks'/'gis.lock') if required else contextlib.nullcontext()


def object_hash(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def plan_snapshot(app):
    raw = (app.PLAN_ROOT/'estado.json').read_bytes()
    plan = json.loads(raw)
    tasks = plan['tasks']
    actual = {t['id']: t for t in tasks}
    missing = set(app.TASKS) - set(actual)
    if (len(actual) != len(tasks) or set(actual) - set(app.TASKS) or
        any(not app.TASKS[t].get('origin', '').startswith('proposed_extension') for t in missing)):
        raise ValueError('Plan y catálogo: IDs incompletos o duplicados')
    for tid, task in actual.items():
        if task['status'] not in {'PENDING','RUNNING','PASS','FAIL','BLOCKED','SKIPPED'}:
            raise ValueError('Estado formal desconocido: '+tid)
        for key in ('front','depends_on','acceptance','execution'):
            if task[key] != app.TASKS[tid][key]:
                raise ValueError('Plan y catálogo discrepan: '+tid+' '+key)
    graph(actual)
    inconsistencies = [{'task': tid, 'pending': [d for d in t['depends_on'] if actual[d]['status'] != 'PASS']}
                       for tid,t in actual.items() if t['status']=='PASS' and any(actual[d]['status']!='PASS' for d in t['depends_on'])]
    return {'path': str(app.PLAN_ROOT), 'revision': plan.get('plan_revision'),
            'sha256': hashlib.sha256(raw).hexdigest(), 'inconsistencies': inconsistencies,
            'catalog_sha256': object_hash(app.CAT),
            'states':{tid:t['status'] for tid,t in actual.items()},
            'inventory':{tid:{k:t[k] for k in ('technical_status','inventory_receipt') if k in t}
                         for tid,t in actual.items()}, 'unreconciled':sorted(missing)}


def authorization(task, spec, snapshot, repair=None, night=False):
    """Hash pins a Work decision; it never manufactures human authority."""
    try:
        reference = spec['authorization'] if repair is None else repair
        raw = Path(reference['path']).expanduser().read_bytes()
        receipt = json.loads(raw)
        if hashlib.sha256(raw).hexdigest() != reference['sha256']:
            raise ValueError('hash de autorización distinto')
        if receipt.get('schema') == 'ddd.owner-window/1.0':
            return owner_authorization(receipt, task, spec, snapshot, repair), None
        if night:
            raise ValueError('La ventana nocturna requiere aprobación explícita del propietario')
        if receipt['authority'] != 'Work' or not receipt['decision'].strip():
            raise ValueError('falta decisión de Work')
        if receipt['task'] != task['id'] or receipt['scope'] != ('local_repair' if repair is not None else 'local_prepare'):
            raise ValueError('ámbito de autorización distinto')
        if receipt['plan_sha256'] != snapshot['sha256']:
            raise ValueError('autorización de otra revisión del Plan')
        bound = {k:v for k,v in spec.items() if k not in ('authorization','repair_authorization')}
        if receipt['spec_sha256'] != object_hash(bound):
            raise ValueError('alcance o validadores no acreditados')
        if receipt['production'] is not False or receipt['network'] is not False:
            raise ValueError('autorización no exclusivamente local')
        budget=receipt['budget']
        if type(budget['seconds']) is not int or not 0 < budget['seconds'] <= 3600:
            raise ValueError('presupuesto temporal ausente/inválido')
        if type(budget['max_attempts']) is not int or not 1 <= budget['max_attempts'] <= (2 if repair is not None else 1):
            raise ValueError('presupuesto de intentos inválido')
        if repair is not None and (not receipt['cause'].strip() or not receipt['prior_attempt_sha256']):
            raise ValueError('reparación sin causa o intento acreditado')
        return receipt, None
    except (OSError, ValueError, KeyError, TypeError, AttributeError) as e:
        return None, 'Sin autorización acreditada: '+str(e)


def owner_authorization(receipt, task, spec, snapshot, repair):
    """Validate supplied owner approval; a DRAFT can never grant authority."""
    if receipt.get('authority') != 'Owner' or receipt.get('status') != 'APPROVED':
        raise ValueError('Manifiesto pendiente del propietario')
    approval = receipt['approval_ref']
    if digest(Path(approval['path']).expanduser()) != approval['sha256']:
        raise ValueError('No existe aprobación original verificable')
    now = datetime.datetime.now(datetime.timezone.utc)
    start = datetime.datetime.fromisoformat(receipt['window']['start_utc'])
    end = datetime.datetime.fromisoformat(receipt['window']['end_utc'])
    if start.tzinfo is None or end.tzinfo is None or not start <= now < end or (end-start).total_seconds() > 43200:
        raise ValueError('Ventana del propietario inválida o expirada')
    if receipt['plan_sha256'] != snapshot['sha256'] or receipt['catalog_sha256'] != snapshot['catalog_sha256']:
        raise ValueError('Manifiesto de otra revisión del plan/catálogo')
    entry = receipt['tasks'][task['id']]
    bound = {k:v for k,v in spec.items() if k not in ('authorization','repair_authorization')}
    if entry['spec_sha256'] != object_hash(bound) or entry['work_class'] != spec.get('work_class'):
        raise ValueError('Clase/alcance/validadores cambiaron')
    if entry['work_class'] not in ('READ_ONLY','LOCAL_IMPLEMENTATION') or entry['work_class'] not in receipt['classes']:
        raise ValueError('Clase local fuera de la ventana')
    if receipt['network'] is not False or receipt['production'] is not False:
        raise ValueError('Ventana no exclusivamente local')
    guards = receipt['guards']
    if guards['sessions_max'] != 2 or guards['gis_max'] != 1 or guards['review_required'] is not True:
        raise ValueError('Guardias insuficientes')
    budget = entry['budget']
    total = receipt['budget']
    if (type(budget['seconds']) is not int or not 0 < budget['seconds'] <= 3600 or
        budget['max_attempts'] != 1 or type(total['seconds']) is not int or not 0 < total['seconds'] <= 43200 or
        type(total['max_tasks']) is not int or not 0 < total['max_tasks'] <= len(receipt['tasks'])):
        raise ValueError('Presupuesto inválido')
    kind = receipt.get('window_kind')
    if kind == 'PILOT':
        if (total['max_tasks'] != 2 or len(receipt['tasks']) != 2 or receipt['classes'] != ['READ_ONLY'] or
            any(e['work_class'] != 'READ_ONLY' for e in receipt['tasks'].values())):
            raise ValueError('Piloto requiere exactamente dos tareas READ_ONLY')
    elif kind == 'NIGHT':
        validate_real_pilot(receipt['pilot_receipt'])
    else:
        raise ValueError('Falta clase de ventana PILOT/NIGHT')
    if repair is not None:
        raise ValueError('La ventana no concede reparación; requiere orden local específica')
    return dict(receipt, task=task['id'], budget=budget, campaign_budget=total)


def validate_real_pilot(reference):
    path = Path(reference['path']).expanduser()
    if digest(path) != reference['sha256']:
        raise ValueError('Receipt del piloto cambió')
    pilot = load(path)
    if pilot.get('mode') != 'REAL_CODEX' or pilot.get('result') != 'PASS':
        raise ValueError('Sin piloto real acreditado')
    if len(pilot['tasks']) != 2:
        raise ValueError('Piloto requiere exactamente dos entregas')
    fronts = set(); tasks = set(); dependencies = set()
    for item in pilot['tasks']:
        result_path = Path(item['result_path'])
        if digest(result_path) != item['result_sha256']:
            raise ValueError('Entrega del piloto cambió')
        result = load(result_path)
        if (result.get('state') != 'TECH_PASS' or result.get('executor_session') == result.get('reviewer_session') or
            not result.get('executor_session') or not result.get('reviewer_session') or
            result.get('review',{}).get('verdict') != 'PASS' or
            not result.get('tests') or any(t['exit_code'] or t['timeout'] for t in result['tests'])):
            raise ValueError('Faltan Ejecutor, pruebas o revisión del piloto')
        if result.get('work_class') != 'READ_ONLY':
            raise ValueError('Piloto requiere tareas READ_ONLY')
        for role in ('executor', 'reviewer'):
            argv = result.get(role, {}).get('argv', [])
            if (not isinstance(argv, list) or '--sandbox' not in argv or
                argv.count('--sandbox') != 1 or argv[argv.index('--sandbox')+1:argv.index('--sandbox')+2] != ['read-only'] or
                argv.count('--ask-for-approval') != 1 or
                argv[argv.index('--ask-for-approval')+1:argv.index('--ask-for-approval')+2] != ['never'] or
                'simulad' in str(argv).lower()):
                raise ValueError('Sesiones del piloto requieren Codex read-only/never')
        dependencies.update(d['task'] for d in result['dependencies'])
        hashes = result_path.parent/'evidence-hashes.json'
        if any(digest(hashes.parent/name) != expected for name,expected in load(hashes).items()):
            raise ValueError('Evidencia del piloto cambió')
        fronts.add(result['front']); tasks.add(result['task'])
    if len(tasks) != 2 or fronts != {'distritos-autonomicos','distritos-nacionales'}:
        raise ValueError('Piloto sin dos tareas independientes A/N')
    if dependencies & tasks:
        raise ValueError('Tareas del piloto no independientes')


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
    # Gates are separate DAGs; a preparation edge cannot silently be an approval.
    for key in ('preparation_dependencies','acceptance_dependencies'):
        if any(key in t for t in tasks.values()):
            graph({tid:{'depends_on':t.get(key,t['depends_on'])} for tid,t in tasks.items()})


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
    prefixes = spec.get('allowed_change_prefixes', [])
    explicit_scope = isinstance(prefixes,list) and bool(prefixes) and all(
        isinstance(p,str) and p and not p.startswith('/') and '..' not in Path(p).parts for p in prefixes)
    readonly_scope = (spec.get('work_class') == 'READ_ONLY' and bool(spec.get('read_only_paths')) and
                      all(isinstance(p,str) and p and not p.startswith('/') and '..' not in Path(p).parts
                          for p in spec['read_only_paths']))
    sufficient = (explicit_scope or readonly_scope) and bool(checks) and covered == expected and all(
        v.get('argv') and v.get('local_only') is True for v in checks)
    return spec, sufficient


def input_errors(task, spec, app):
    errors = []
    for name, item in spec.get('inputs', {}).items():
        try:
            if digest(Path(item['path']).expanduser()) != item['sha256']:
                errors.append('Entrada cambió: '+name)
        except (OSError, KeyError, TypeError):
            errors.append('Entrada ausente o sin identidad: '+name)
    if task.get('prompt_file'):
        try:
            app.prompt_master(task)
        except (OSError, ValueError, KeyError) as e:
            errors.append(str(e))
    for item in task.get('artifact_requirements', []):
        if item.get('gate', 'prepare') != 'prepare':
            continue
        try:
            if not item.get('identity') or not item.get('edition') or digest(Path(item['path'])) != item['sha256']:
                errors.append('Dependencia de artefacto no acreditada')
        except (OSError, KeyError, TypeError):
            errors.append('Dependencia de artefacto ausente')
    return errors


def held_existing(path):
    """Read-only probe: never creates a lock or mistakes its existence for ownership."""
    try:
        with path.open('r') as stream:
            try:
                fcntl.flock(stream,fcntl.LOCK_EX|fcntl.LOCK_NB)
            except BlockingIOError:
                return True
    except FileNotFoundError:
        return False
    return False


def resource_blocker(app, task, spec, events):
    try:
        repo,head,dirty = app.verify_repo(task['front'])
        if dirty and spec.get('work_class') != 'READ_ONLY' and not spec.get('validate_existing'):
            checkpoint = next((e for e in reversed(events) if e.get('front')==task['front'] and e.get('worktree_files')), {})
            old_scope = getattr(app,'AUTO_READ_PATHS',None); app.AUTO_READ_PATHS=None
            try:
                if (checkpoint.get('head_end') != head or checkpoint.get('worktree_files') != repo_files(app,repo) or
                    checkpoint.get('worktree_metadata') != repo_metadata(app,repo,checkpoint['worktree_files'])):
                    return 'Worktree sucio: requiere checkpoint propio o validación existente autorizada'
            finally:
                app.AUTO_READ_PATHS=old_scope
        lock_root = Path(tempfile.gettempdir())/'ddd-worktree-locks'
        key = hashlib.sha256(str(Path(repo).resolve()).encode()).hexdigest()
        paths = [lock_root/(key+'.lock'), app.DATA/f'.manual-{task["front"]}.lock',
                 app.DATA/f'.batch-{task["front"]}.lock', app.DATA/'.manual.lock']
        if spec.get('gis_intensive') or task['front']=='distritos-autonomicos':
            paths.append(lock_root/'gis.lock')
        if any(held_existing(path) for path in paths):
            return 'Concurrencia bloqueada: worktree/lock heredado/GIS ocupado'
        if all(held_existing(lock_root/f'codex-slot-{i}.lock') for i in range(2)):
            return 'Concurrencia bloqueada: máximo dos sesiones Codex'
    except (OSError,RuntimeError,ValueError,KeyError) as e:
        return str(e)
    return None


def assess(app, selected, policy, events):
    formal = app.AUTO_PLAN['states']
    seeds = seed_status(policy)
    latest = {e['task']: e for e in events if 'task' in e}
    historic = {h['task']: h for h in read_events(app.DATA/'historial.jsonl') if 'task' in h}
    states = {}
    for tid, task in app.TASKS.items():
        previous = latest.get(tid)
        if previous:
            states[tid] = previous.get('state', 'BLOCKED')
            if states[tid] == 'TECH_PASS':
                try:
                    hashes = Path(previous['attempt'])/'evidence-hashes.json'
                    if digest(hashes) != previous['evidence_hashes_sha256'] or any(
                        digest(hashes.parent/n) != h for n,h in load(hashes).items()):
                        raise ValueError('Evidencia cambió')
                except (OSError, ValueError, KeyError, TypeError):
                    states[tid] = 'BLOCKED'
        elif tid in policy.get('formal_pending', []):
            states[tid] = 'WAIT_OWNER'
        elif formal.get(tid) == 'PASS' and tid not in policy.get('revalidate', []):
            states[tid] = 'FORMAL_PASS'
        elif seeds.get(tid, {}).get('state') == 'TECH_PASS':
            states[tid] = 'TECH_PASS'
        else:
            states[tid] = 'PENDING'
            entry = app.AUTO_PLAN.get('inventory', {}).get(tid, {})
            if entry.get('technical_status') == 'ALREADY_EVIDENCED':
                try:
                    reference = entry['inventory_receipt']
                    if digest(Path(reference['path'])) == reference['sha256']:
                        states[tid] = 'ALREADY_EVIDENCED'
                except (OSError,KeyError,TypeError):
                    pass
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
        # Local preparation may use a smaller, explicitly approved requirement set.
        gate_requirements = t.get('preparation_dependencies', sorted(ancestors))
        requirements = spec.get('prepare_dependencies', gate_requirements)
        if not isinstance(requirements, list) or not set(requirements) <= set(gate_requirements):
            raise ValueError('Requisitos de preparación fuera del DAG: '+tid)
        pending = [d for d in requirements if states[d] not in ('TECH_PASS','FORMAL_PASS')]
        accept_requirements = t.get('acceptance_dependencies', sorted(ancestors))
        formal_pending = sorted(d for d in accept_requirements if formal.get(d) != 'PASS' or d in policy.get('formal_pending', []))
        receipt, auth_error = authorization(t, spec, app.AUTO_PLAN, night=getattr(app,'AUTO_NIGHT',False))
        broken_inputs = input_errors(t, spec, app)
        reasons = []
        state = states[tid]
        if tid in latest:
            reasons.append('Intento anterior conservado; sin repetición automática')
            if state == 'STARTED':
                state = 'BLOCKED'; reasons.append('Intento interrumpido; requiere decisión humana')
        elif state in ('TECH_PASS', 'FORMAL_PASS', 'ALREADY_EVIDENCED'):
            reasons.append('Ya acreditada; se conserva evidencia')
        elif formal.get(tid) == 'RUNNING':
            state = 'BLOCKED'; reasons.append('Plan vivo RUNNING: tarea ocupada; conservar escritor existente')
        elif t['execution'] == 'approval' or tid in RESERVED or tid in policy.get('formal_pending', []):
            state = 'WAIT_OWNER'; reasons.append('Autoridad humana reservada')
        elif tid not in policy.get('authorized_local_tasks', []):
            state = 'WAIT_OWNER'; reasons.append('Sin encargo local autorizado en la política de campaña')
        elif auth_error:
            state = 'WAIT_OWNER'; reasons.append(auth_error)
        elif pending:
            state = 'BLOCKED'; reasons.append('Dependencias técnicas ausentes: ' + ', '.join(pending))
        elif not sufficient:
            state = 'BLOCKED'; reasons.append('Criterios ejecutables insuficientes')
        elif broken_inputs:
            state = 'BLOCKED'; reasons.extend(broken_inputs)
        elif tid in historic and historic[tid].get('result') != 'DONE_REVIEW':
            state = 'WAIT_OWNER'; reasons.append('Intento manual fallido; no retry automático')
        else:
            state = 'ENABLED'
            resource = resource_blocker(app,t,spec,events)
            if resource:
                state='BLOCKED'; reasons.append(resource)
        if state == 'WAIT_OWNER' and not sufficient:
            reasons.append('Falta contrato/validador determinista suficiente')
        if state == 'WAIT_OWNER' and broken_inputs:
            reasons.extend(broken_inputs)
        rows.append({'task': tid, 'state': state, 'reasons': reasons, 'dependencies': deps,
                     'front':t['front'], 'display_state':'ALREADY_EVIDENCED' if state in ('TECH_PASS','FORMAL_PASS') else state,
                     'authorization': receipt, 'prepare_requirements': requirements, 'prepare_pending': pending,
                     'gates': {'prepare': state == 'ENABLED',
                               'accept': state in ('TECH_PASS','FORMAL_PASS') and not formal_pending,
                               'integrate': False, 'produce': False},
                     'formal_dependencies_pending': formal_pending,
                     'mode': 'validate_existing' if tid in historic or spec.get('validate_existing') else 'execute'})
    return rows, seeds


def run_process(argv, cwd, prompt, logfile, timeout, stop_process):
    with session_slot():
        return _run_process(argv, cwd, prompt, logfile, timeout, stop_process)


def _run_process(argv, cwd, prompt, logfile, timeout, stop_process):
    started = time.monotonic()
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1')
    with logfile.open('x') as log:
        p = subprocess.Popen(argv, cwd=cwd, env=env, stdin=subprocess.PIPE if prompt is not None else subprocess.DEVNULL,
                             stdout=log, stderr=subprocess.STDOUT, text=True, start_new_session=True,
                             pass_fds=tuple(ACTIVE_LOCKS))
        try:
            write_new(logfile.with_suffix('.process.json'), {'pid': p.pid, 'argv': argv, 'cwd': str(cwd)})
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
    effort = app.CFG['esfuerzo_revisor' if role == 'reviewer' else 'esfuerzo_ejecutor']
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


def process_usage(logfile):
    tokens = 0
    for line in logfile.read_text().splitlines():
        try:
            event = json.loads(line)
        except ValueError:
            continue
        if event.get('type') in ('error','turn.failed'):
            detail = json.dumps(event).lower()
            if any(s in detail for s in ('quota','usage limit','rate limit','insufficient_quota','usage_limit')):
                return tokens, True
        if event.get('type') == 'turn.completed':
            usage = event.get('usage') or {}
            tokens += int(usage.get('total_tokens') or (usage.get('input_tokens',0)+usage.get('output_tokens',0)))
    return tokens, False


def quota_pending(events):
    state = False
    for event in events:
        if event.get('state') == 'QUOTA_STOP':
            state = True
        elif event.get('state') == 'QUOTA_RESUMED':
            state = False
    return state


def repo_files(app, repo):
    scope = getattr(app, 'AUTO_READ_PATHS', None)
    if scope:
        names = set()
        for name in scope:
            path = repo/name
            if not path.resolve().is_relative_to(repo.resolve()) or path.is_symlink() or not path.exists():
                raise ValueError('Ruta READ_ONLY ausente o fuera de scope: '+name)
            names.update(str(p.relative_to(repo)) for p in path.rglob('*') if p.is_file()) if path.is_dir() else names.add(name)
        if sum((repo/name).stat().st_size for name in names) > 16*1024*1024:
            raise ValueError('Snapshot READ_ONLY supera 16 MiB; acotar contrato')
        if any((repo/n).is_symlink() for n in names):
            raise ValueError('Snapshot READ_ONLY contiene enlace')
        return {name:digest(repo/name) for name in sorted(names)}
    raw = subprocess.check_output(['git', '-C', str(repo), 'ls-files', '-z', '--cached', '--others', '--exclude-standard'])
    raw += subprocess.check_output(['git','-C',str(repo),'ls-files','-z','--others','--ignored','--exclude-standard'])
    out = {}
    size = 0
    for name in set(raw.decode().split('\0')) - {''}:
        path = repo / name
        if path.is_symlink():
            raise ValueError('Entrega con enlaces no admitida: ' + name)
        if path.is_file():
            size += path.stat().st_size
            if size > 256 * 1024 * 1024:
                raise ValueError('Captura local supera 256 MiB; requiere preparación acotada de Work')
            out[name] = digest(path)
    return out


def repo_metadata(app, repo, files):
    scope = getattr(app,'AUTO_READ_PATHS',None)
    return {'modes': {name: (repo/name).stat().st_mode & 0o777 for name in files},
            'status':app.git(repo,'status','--porcelain'),
            'diff':app.git(repo,'diff','HEAD','--binary',*(['--',*scope] if scope else [])),
            'index':app.git(repo,'ls-files','--stage',*(['--',*scope] if scope else []))}


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
        record.update(head_end=app.git(repo, 'rev-parse', 'HEAD'), worktree_files=files,
                      worktree_metadata=repo_metadata(app,repo,files),
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
    append(journal, {'task': tid, 'state': 'STARTED', 'attempt': str(folder), 'repair': bool(row.get('repair')), 'dependencies': row['dependencies']})
    record = {'task': tid, 'front': task['front'], 'work_class': spec.get('work_class'),
              'dependencies': row['dependencies'], 'attempt': str(folder), 'mode': row['mode']}
    app.AUTO_READ_PATHS = spec.get('read_only_paths') if spec.get('work_class') == 'READ_ONLY' else None
    try:
        if plan_snapshot(app) != app.AUTO_PLAN:
            raise ValueError('Plan cambió desde el preflight')
        receipt, error = authorization(task, spec, app.AUTO_PLAN, spec.get('repair_authorization') if row.get('repair') else None,
                                       night=getattr(app,'AUTO_NIGHT',False))
        if error:
            raise ValueError(error)
        record['authorization'] = receipt
        record['repair'] = bool(row.get('repair'))
        timeout = min(app.CFG['segundos_maximos'], receipt['budget']['seconds'])
        if receipt.get('window'):
            end = datetime.datetime.fromisoformat(receipt['window']['end_utc'])
            timeout = min(timeout,(end-datetime.datetime.now(datetime.timezone.utc)).total_seconds())
        deadline = time.monotonic()+timeout
        def remaining():
            if time.monotonic() >= deadline:
                raise ValueError('Presupuesto temporal local agotado')
            return deadline-time.monotonic()
        repo, head, dirty = app.verify_repo(task['front'])
        before = repo_files(app, repo)
        before_metadata = repo_metadata(app,repo,before)
        record.update(head_start=head, dirty_start=dirty)
        write_new(folder/'before.json', {'head': head, 'status': dirty, 'files': before,
                                        'metadata':before_metadata,
                                        'diff': app.git(repo, 'diff', 'HEAD', '--binary')})
        executor_id = None
        if row['mode'] == 'execute':
            # Existing modifications cannot be attributed safely to this attempt.
            if dirty and spec.get('work_class') != 'READ_ONLY':
                previous = [e for e in read_events(journal) if e.get('front') == task['front'] and e.get('worktree_files')]
                checkpoint = previous[-1] if previous else {}
                if (checkpoint.get('worktree_files') != before or checkpoint.get('head_end') != head or
                    checkpoint.get('worktree_metadata') != before_metadata):
                    raise ValueError('Worktree sucio sin checkpoint propio: conservar y someter a decisión humana')
            prompt = app.prompt_master(task, row['formal_dependencies_pending'], app.local_plan_status().get(tid)) + '\nModo AUTO: no preguntes al propietario entre tareas. No encadenes. No cambies Plan, historial ni política del controlador. No hagas commit; el controlador captura la entrega. No ejecutes tareas productivas, red, push, PR, merge o publicación.\n' + 'Autorización exacta: '+json.dumps(receipt, ensure_ascii=False)+'\nCambios permitidos: '+json.dumps(spec.get('allowed_change_prefixes', []))
            snapshot = folder/'executor-inputs'
            copy_tree(repo, snapshot, before)
            write_new(folder/'input-manifest.json', {'task':tid,'head':head,'files':before,'metadata':before_metadata})
            input_manifest_hash = digest(folder/'input-manifest.json')
            prompt += '\nFingerprints exactos: '+json.dumps({'plan':app.AUTO_PLAN['sha256'], 'catalog':app.AUTO_PLAN['catalog_sha256'],
                         'head':head,'inputs_manifest_sha256':input_manifest_hash,'task_sha256':object_hash(task),
                         'spec_sha256':object_hash({k:v for k,v in spec.items() if k not in ('authorization','repair_authorization')})})
            prompt += '\nPlan de pruebas exacto: '+json.dumps(spec['validators'],ensure_ascii=False)
            prompt += f'\nLímite total de tarea (Ejecutor, validadores y Revisor): {timeout} segundos. '
            prompt += 'Completa tu salida estructurada con manifest y SHA reales; un bloqueo se declara, no se disimula.\n'
            prompt += 'Devuelve JSON conforme al esquema: task, head, inputs_manifest_sha256, status, criteria_verified, evidence (rutas relativas a la entrega), tests, limitations.\n'
            if spec.get('work_class') == 'READ_ONLY':
                seal(snapshot)
                prompt += '\nREAD_ONLY: trabaja exclusivamente sobre esta copia de entradas. No ejecutes motores históricos ni cálculos GIS; entrega sólo contraste probatorio. '
                prompt += f'Entrada {snapshot}; manifest {folder/"input-manifest.json"}; SHA256 {input_manifest_hash}; HEAD {head}. '
                prompt += 'Devuelve JSON conforme al esquema: task, head, inputs_manifest_sha256, status, criteria_verified, evidence (rutas relativas al snapshot), tests, limitations.\n'
            write_new(folder/'executor-prompt.json', {'prompt': prompt})
            readonly = spec.get('work_class') == 'READ_ONLY'
            structured = spec.get('work_class') in ('READ_ONLY','LOCAL_IMPLEMENTATION')
            result = run_process(codex_cmd(app, 'executor_readonly' if readonly else 'executor',
                                          app.BASE/'executor.schema.json' if structured else None,
                                          folder/'executor-summary.json' if structured else None), snapshot if readonly else repo, prompt, folder/'executor.jsonl',
                                 remaining(), app.stop_process)
            record['executor'] = result
            record['tokens_reported'], exhausted = process_usage(folder/'executor.jsonl')
            if exhausted or record['tokens_reported'] >= app.CFG['presupuesto_tokens_reportados_suave']:
                raise ValueError('QUOTA_STOP: cuota o presupuesto de tokens reportados agotado')
        after = repo_files(app, repo)
        after_metadata = repo_metadata(app,repo,after)
        record['worktree_metadata'] = after_metadata
        record['worktree_files'] = after
        record['head_end'] = app.git(repo, 'rev-parse', 'HEAD')
        changes = sorted(n for n in set(before) | set(after) if before.get(n) != after.get(n) or
                         before_metadata['modes'].get(n) != after_metadata['modes'].get(n))
        record['changes'] = changes
        delivery = folder/'delivery'; delivery.mkdir()
        copy_tree(repo, delivery/'tree', after)
        write_new(delivery/'changes.json', dict(record, files=after, metadata=after_metadata, diff=app.git(repo, 'diff', head, '--binary')))
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
        for name in ('ddd_auto.py', 'validar_piloto.py', 'review.schema.json', 'executor.schema.json'):
            shutil.copy2(app.BASE/name, controller/name)
        write_new(controller/'policy.json', policy)
        write_new(controller/'plan.json', app.AUTO_PLAN)
        write_new(controller/'authorization.json', receipt)
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
            if spec.get('work_class') in ('READ_ONLY','LOCAL_IMPLEMENTATION'):
                summary = load(folder/'executor-summary.json')
                validate_schema(summary,load(app.BASE/'executor.schema.json'))
                if (summary['task'] != tid or summary['head'] != head or summary['inputs_manifest_sha256'] != input_manifest_hash
                    or any(n not in after for n in summary['evidence']) or
                    (spec.get('work_class') == 'READ_ONLY' and manifest_files(snapshot) != before)):
                    raise ValueError('Salida del Ejecutor no corresponde a entradas reales')
                shutil.copy2(folder/'executor-summary.json', delivery/'executor-summary.json')
                shutil.copy2(folder/'input-manifest.json', delivery/'input-manifest.json')
                record['executor_summary'] = summary
                if summary['status'] != 'READY_FOR_REVIEW':
                    raise ValueError('Ejecutor estacionado: '+summary['status'])
        if record['head_end'] != head:
            raise ValueError('Ejecutor cambió HEAD; revisión de alcance requerida')
        if after_metadata['index'] != before_metadata['index']:
            raise ValueError('Ejecutor cambió el índice Git; conservar y revisar alcance')
        prefixes = spec.get('allowed_change_prefixes', ['docs/AUDITORIAS/', 'tests/', 'herramientas/'])
        if spec.get('work_class') == 'READ_ONLY' and changes:
            raise ValueError('READ_ONLY alteró entradas')
        if any(not any(n.startswith(p) for p in prefixes) for n in changes):
            raise ValueError('Cambios fuera del alcance local')
        tests = []
        for i, validator in enumerate(spec['validators']):
            variables = {'python': app.CFG['python_gis'], 'base': str(controller), 'repo': str(delivery/'tree'), 'inputs': str(inputs),
                         'output': str(delivery/f'validator-{i}.json')}
            argv = [s.format(**variables) for s in validator['argv']]
            r = run_process(argv, delivery/'tree', None, delivery/f'validator-{i}.log',
                            remaining(), app.stop_process)
            r['covers'] = validator['covers']; tests.append(r)
        write_new(delivery/'tests.json', tests); record['tests'] = tests
        if repo_files(app, repo) != after or repo_metadata(app,repo,after) != after_metadata:
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
                         f'Aplica la skill {Path.home()/".codex/skills/ddd-revisor/SKILL.md"}. '
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
                             review_prompt, folder/'reviewer.jsonl', remaining(), app.stop_process)
        record['reviewer'] = result
        review_tokens, exhausted = process_usage(folder/'reviewer.jsonl')
        record['tokens_reported'] = record.get('tokens_reported',0)+review_tokens
        if exhausted or record['tokens_reported'] >= app.CFG['presupuesto_tokens_reportados_suave']:
            raise ValueError('QUOTA_STOP: cuota o presupuesto de tokens reportados agotado')
        reviewer_id = session_id(folder/'reviewer.jsonl')
        record.update(executor_session=executor_id, reviewer_session=reviewer_id)
        if reviewer_id == executor_id or result['exit_code'] != 0 or result['timeout']:
            raise ValueError('Revisión no completada o sin separación')
        if digest(folder/'delivery-manifest.json') != bundle_hash or manifest_files(delivery) != files:
            raise ValueError('Entrega alterada durante revisión')
        if repo_files(app, repo) != after or repo_metadata(app,repo,after) != after_metadata or app.git(repo,'rev-parse','HEAD') != head:
            raise ValueError('Worktree cambió durante revisión')
        if plan_snapshot(app) != app.AUTO_PLAN:
            raise ValueError('Plan cambió durante ejecución')
        current_authorization, error = authorization(task, spec, app.AUTO_PLAN, spec.get('repair_authorization') if row.get('repair') else None,
                                                     night=getattr(app,'AUTO_NIGHT',False))
        if error or current_authorization != receipt:
            raise ValueError('Autorización cambió durante ejecución')
        current_rows, _ = assess(app, list(app.TASKS), policy, read_events(journal))
        current_states = {r['task']:r['state'] for r in current_rows}
        if any(current_states[d] not in ('TECH_PASS','FORMAL_PASS') for d in row['prepare_requirements']):
            raise ValueError('Evidencia de dependencia cambió durante ejecución')
        verdict = load(folder/'review.json')
        check_review(verdict, load(schema_path), task, bundle_hash, record['head_end'], files)
        record['review'] = verdict
        record['state'] = {'PASS': 'TECH_PASS', 'NO_GO': 'REVIEW_NO_GO', 'WAIT_OWNER': 'WAIT_OWNER'}[verdict['verdict']]
    except KeyboardInterrupt:
        record.update(state='BLOCKED', reason='INTERRUPTED; sin repetición automática')
        capture_failure(app, task, folder, record)
        write_new(folder/'result.json', record)
        write_new(folder/'evidence-hashes.json', manifest_files(folder))
        record['evidence_hashes_sha256'] = digest(folder/'evidence-hashes.json'); append(journal, record)
        raise
    except (OSError, ValueError, KeyError, RuntimeError, TypeError) as e:
        record.update(state='QUOTA_STOP' if str(e).startswith('QUOTA_STOP') else 'BLOCKED', reason=str(e))
        capture_failure(app, task, folder, record)
    write_new(folder/'result.json', record)
    # Failed attempts retain partial logs as well, with their own final hash list.
    write_new(folder/'evidence-hashes.json', manifest_files(folder))
    record['evidence_hashes_sha256'] = digest(folder/'evidence-hashes.json')
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
    app.AUTO_NIGHT = getattr(args,'night',False)
    app.AUTO_PLAN = plan_snapshot(app)
    root = app.DATA/'auto'/hashlib.sha256(str(app.PLAN_ROOT).encode()).hexdigest()[:16]
    if args.resume and not re.fullmatch(r'[a-zA-Z0-9_-]+', args.resume):
        raise ValueError('Identidad de campaña inválida')
    original = load(root/args.resume/'campaign.json') if args.resume else None
    selected = args.tasks or (original['selected'] if original else list(app.TASKS))
    if len(set(selected)) != len(selected) or any(t not in app.TASKS for t in selected):
        raise ValueError('IDs desconocidos o repetidos')
    selected = [tid for tid in selected if args.front == 'all' or app.TASKS[tid]['front'] == args.front]
    if not selected:
        raise ValueError('Selección vacía')
    policy = load(args.policy)
    journal = root/'eventos.jsonl'
    events = read_events(journal)
    rows, seeds = assess(app, selected, policy, events)
    preflight = night_preflight(rows, events, app.AUTO_NIGHT)
    if args.dry_run or args.status:
        for row in rows:
            print(json.dumps(row, ensure_ascii=False))
        print(json.dumps({'plan':app.AUTO_PLAN, 'checkpoints':[p.parent.name for p in root.glob('*/campaign.json')],
                          'sessions_limit':2,'gis_limit':1,'production_authorized':False,
                          'preflight':preflight,'morning_inbox':morning_inbox(rows,events)},ensure_ascii=False))
        print('Plan e historial conservados. Cero Codex.')
        print(preflight['verdict'])
        return 0 if args.status or preflight['verdict'] in ('READY_FOR_PILOT','READY_FOR_NIGHT') else 1
    if args.repair and (args.repair not in selected or args.resume):
        raise ValueError('Reparación requiere ID seleccionado y campaña nueva')
    if not args.resume and not args.repair and preflight['verdict'] == 'NO_READY':
        for row in rows:
            print(json.dumps(row,ensure_ascii=False))
        print(json.dumps(preflight,ensure_ascii=False)); print('NO_READY: cero consumo, cero escrituras de campaña')
        return 1
    if app.AUTO_NIGHT and preflight['verdict'] == 'NO_READY' and not args.resume:
        print(json.dumps(preflight,ensure_ascii=False)); return 1
    root.mkdir(parents=True, exist_ok=True)
    with lock(root/'.controller.lock'):
        events = read_events(journal)
        if args.resume:
            folder = root/args.resume
            original = load(folder/'campaign.json')
            if (original['selected'] != selected or original['policy'] != policy or
                original['catalog'] != app.CAT or original['parameters'] != app.CFG):
                raise ValueError('Reanudar requiere el mismo lote, política, catálogo y parámetros')
            if original['plan'] != app.AUTO_PLAN:
                raise ValueError('Reanudar requiere la misma revisión del Plan')
        else:
            stamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ') + '-' + uuid.uuid4().hex[:8]
            folder = root/stamp; folder.mkdir()
            write_new(folder/'campaign.json', {'selected': selected, 'policy': policy, 'catalog': app.CAT,
                       'parameters': app.CFG, 'plan_states': app.local_plan_status(), 'technical_seeds': seeds,
                       'plan':app.AUTO_PLAN,
                       'legacy_history_sha256': digest(app.DATA/'historial.jsonl') if (app.DATA/'historial.jsonl').exists() else None})
        # A persisted STARTED is a spent attempt, even after SIGKILL.
        latest = {e['task']: e for e in events if 'task' in e}
        for tid, e in latest.items():
            if e.get('state') == 'STARTED':
                append(journal, dict(e, state='BLOCKED', reason='INTERRUPTED_OR_ORPHAN; requiere decisión humana'))
        print('CAMPAÑA', folder.name, flush=True)
        deferred = {}
        # Quota stops apply to the approval fingerprint across campaign IDs.
        quota_stop = quota_pending(events)
        if args.resume and quota_stop:
            append(journal,{'task':'__campaign__','state':'QUOTA_RESUMED','reason':'Reanudación explícita por --resume del operador',
                            'campaign':folder.name})
            quota_stop = False
        repair_spent = False
        while True:
            rows, seeds = assess(app, selected, policy, read_events(journal))
            if args.repair and not repair_spent:
                row = next(r for r in rows if r['task'] == args.repair)
                task = app.TASKS[args.repair]; spec, sufficient = criteria(task, policy)
                history = [e for e in read_events(journal) if e['task'] == args.repair]
                prior = history[-1] if history else {}
                receipt, error = authorization(task, spec, app.AUTO_PLAN, spec.get('repair_authorization', {}))
                count = sum(e.get('repair') is True and e.get('state') == 'STARTED' for e in history)
                prior_path = Path(prior.get('attempt',''))/'result.json'
                eligible = (not error and sufficient and task['execution'] != 'approval' and task['id'] not in RESERVED
                            and task['id'] in policy.get('authorized_local_tasks', [])
                            and prior.get('state') in ('BLOCKED','REVIEW_NO_GO') and prior_path.is_file()
                            and receipt['prior_attempt_sha256'] == digest(prior_path)
                            and count < receipt['budget']['max_attempts']
                            and all(r['satisfied'] for r in row['dependencies'])
                            and not row['prepare_pending'])
                if eligible:
                    row.update(state='ENABLED', repair=True, mode='execute', authorization=receipt)
                else:
                    row.update(state='WAIT_OWNER', reasons=[error or 'Reparación no acreditada, dependencias pendientes o presupuesto agotado'])
                    repair_spent = True
            rows = [dict(r, state='BLOCKED', reasons=[deferred[r['task']]]) if r['task'] in deferred else r for r in rows]
            if quota_stop:
                rows = [dict(r,state='QUOTA_STOP',reasons=['Cuota agotada; requiere reanudación explícita del usuario'])
                        if r['state']=='ENABLED' else r for r in rows]
            enabled = next((r for r in rows if r['state'] == 'ENABLED'), None)
            if enabled is None:
                break
            t = app.TASKS[enabled['task']]
            receipt = enabled['authorization']
            owner_records = [e for e in read_events(journal) if e.get('authorization',{}).get('approval_ref') == receipt.get('approval_ref') and e.get('authorization')]
            if receipt.get('campaign_budget'):
                budget = receipt['campaign_budget']
                spent = sum(sum(e.get(k,{}).get('seconds',0) for k in ('executor','reviewer')) +
                            sum(v.get('seconds',0) for v in e.get('tests',[])) for e in owner_records)
                if len(owner_records) >= budget['max_tasks'] or spent + receipt['budget']['seconds'] > budget['seconds']:
                    deferred[t['id']] = 'Presupuesto de ventana agotado o insuficiente para otra tarea'; continue
            # Also interlock installed legacy manual/batch controllers.
            try:
                with contextlib.ExitStack() as stack:
                    stack.enter_context(worktree_lock(app.real_repo(t['front'])))
                    stack.enter_context(lock(app.DATA/f'.manual-{t["front"]}.lock'))
                    stack.enter_context(lock(app.DATA/f'.batch-{t["front"]}.lock'))
                    spec = policy.get('tasks',{}).get(t['id'],{})
                    stack.enter_context(gis_lock(spec.get('gis_intensive', False) or t['front']=='distritos-autonomicos'))
                    result = attempt(app, enabled, policy, folder/enabled['task'], journal)
                    if result.get('state') == 'QUOTA_STOP':
                        quota_stop = True
                    if enabled.get('repair'):
                        repair_spent = True
                    print(enabled['task'], result['state'], result.get('reason', ''), flush=True)
            except RuntimeError as e:
                # Not attempted: preserve availability for a later campaign.
                deferred[enabled['task']] = str(e)
        summary = {'campaign': folder.name, 'plan':app.AUTO_PLAN, 'tasks': rows, 'technical_seeds': seeds,
                   'delivery':'READY_FOR_REVIEW' if all(r['state'] in ('TECH_PASS','FORMAL_PASS') for r in rows) else 'BLOCKED',
                   'integration_requirements':['Work authorization','final SHA review','CI on same SHA'],
                   'production_requirements':['separate owner authorization','readiness','no automatic retry'],
                   'formal_reservations': policy.get('formal_pending', []), 'production_authorized': False,
                   'preflight':preflight,'morning_inbox':morning_inbox(rows,read_events(journal))}
        # Each resumption adds a new summary; prior evidence is never rewritten.
        output = folder/('summary-' + uuid.uuid4().hex + '.json')
        write_new(output, summary)
        inbox = folder/('BANDEJA_MATINAL-'+uuid.uuid4().hex+'.md')
        atomic_write(inbox, inbox_markdown(summary))
        print('RESUMEN', output)
        for row in rows:
            print(row['task'], row['state'], '; '.join(row['reasons']))
        return 0 if all(r['state'] in ('TECH_PASS', 'FORMAL_PASS') for r in rows) else 1


def night_preflight(rows, events, night):
    enabled = [r for r in rows if r['state'] == 'ENABLED']
    fronts = {r['front'] for r in enabled}
    causes = []
    if not enabled:
        causes.append('enabled==0')
    real = bool(enabled) and all(r['authorization'].get('window_kind') == 'NIGHT' for r in enabled)
    if night and ((not real and not {'distritos-autonomicos','distritos-nacionales'} <= fronts) or (real and len(fronts)<2)):
        causes.append('Faltan dos tareas independientes A/N con contrato, validador y permiso verificables')
    if quota_pending(events):
        causes.append('QUOTA_STOP persistido: esperar reanudación explícita del usuario')
    # Owner authorization validates the actual final deliveries before NIGHT eligibility.
    return {'verdict':'NO_READY' if causes else ('READY_FOR_NIGHT' if real else 'READY_FOR_PILOT'), 'enabled':len(enabled),
            'by_front':{f:[r['task'] for r in enabled if r['front']==f] for f in sorted({r['front'] for r in rows})},
            'causes':causes,'real_pilot_verified':real,
            'missing_contracts':{r['task']:r['reasons'] for r in rows if r['state'] in ('WAIT_OWNER','BLOCKED')}}


def morning_inbox(rows, events):
    grouped = {}
    for row in rows:
        if row['state'] in ('WAIT_OWNER','BLOCKED','QUOTA_STOP','REVIEW_NO_GO'):
            key = '; '.join(row['reasons']) or row['state']
            grouped.setdefault(key,[]).append(row['task'])
    return {'counts':{s:sum(r['state']==s for r in rows) for s in sorted({r['state'] for r in rows})},
            'owner_decisions':grouped,
            'accumulated_deliveries':[{k:e[k] for k in ('task','state','attempt','delivery_sha256','reviewer_session','reason') if k in e}
                                      for e in events if e.get('state') != 'STARTED'],
            'next_enabled':[r['task'] for r in rows if r['state']=='ENABLED'],
            'reserved':['F10 canonical receipts/promotion','Madrid A2 official acceptance','A09/N10 integration']}


def inbox_markdown(summary):
    x = summary['morning_inbox']
    lines = ['# Bandeja matinal DDD 1.3.0', '', 'Campaña: '+summary['campaign'],
             'Preflight: '+summary['preflight']['verdict'], 'Producción autorizada: NO', '',
             'Recuentos: '+json.dumps(x['counts'],ensure_ascii=False), '', '| Tarea | Estado | Manifest SHA | Revisor |', '|---|---|---|---|']
    for e in x['accumulated_deliveries']:
        lines.append('| '+ ' | '.join(str(e.get(k,'—')) for k in ('task','state','delivery_sha256','reviewer_session')) +' |')
    lines.extend(['', 'Decisiones agrupadas:'])
    lines.extend('- '+', '.join(tasks)+': '+cause for cause,tasks in x['owner_decisions'].items())
    lines.extend(['', 'Próximas habilitadas: '+', '.join(x['next_enabled']), 'Reservas: '+ '; '.join(x['reserved'])])
    return '\n'.join(lines)+'\n'
