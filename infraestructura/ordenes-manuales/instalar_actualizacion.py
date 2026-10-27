#!/usr/bin/env python3
"""DDD installer 1.3.0, 2026-10-11; candidate local reversible installation.
Predecessor: legacy/1.2.0/instalar_actualizacion.py. Changes: exact review/pilot
checks, external backup, inherited lock protection and rollback; no campaign.
"""
from __future__ import annotations
import argparse
import contextlib
from datetime import datetime, timezone
import fcntl
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import stat
import sys
import tempfile

BASE = Path(__file__).resolve().parent
REAL_TARGET = Path.home() / 'Desarrollo/DDD-control/ordenes-manuales'
FILES = ('ddd.py', 'ddd_auto.py', 'instalar_actualizacion.py', 'validar_piloto.py', 'validar_tarea_local.py',
         'migrar_plan.py', 'review.schema.json', 'executor.schema.json', 'catalogo.json', 'AUTO.md')
PROTECTED = ('parametros.json', 'encargos.json', 'historial.jsonl', 'auto-policy.json', 'logs', 'legacy')


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def jsonread(path):
    return json.loads(Path(path).read_text())


def bundle_hashes():
    files = [n for n in FILES if (BASE/n).is_file()]
    files += [str(p.relative_to(BASE)) for p in sorted((BASE/'PROMPTS_TAREAS').glob('*.md'))]
    return {n: digest(BASE/n) for n in files}


def file_record(path):
    return {'sha256': digest(path), 'mode': stat.S_IMODE(path.stat().st_mode)}


def protected_state(target):
    result = {}
    for name in PROTECTED:
        path = target/name
        for item in list(path.rglob('*')) if path.is_dir() else [path]:
            if item.is_file():
                result[str(item.relative_to(target))] = file_record(item)
    return result


def validate_reference(ref):
    if not isinstance(ref, dict) or not ref.get('path') or not ref.get('sha256'):
        raise RuntimeError('EVIDENCE_REFERENCE_MISSING')
    path = Path(ref['path']).expanduser().resolve()
    if not path.is_file() or digest(path) != ref['sha256']:
        raise RuntimeError('EVIDENCE_REFERENCE_INVALID: '+str(path))
    return path


def validate_gates(gate_file, hashes, candidate_plan=None, install_target=None, plan_target=None):
    if gate_file is None:
        raise RuntimeError('NO_READY: independent final review and REAL Codex pilot receipt required')
    gate_path = Path(gate_file).expanduser().resolve()
    gates = jsonread(gate_path)
    if gates.get('schema') != 'ddd.install-gates/1.0':
        raise RuntimeError('NO_READY: invalid installation gate schema')
    review = gates.get('technical_review', {})
    if review.get('verdict') not in ('GO', 'GO_ACOTADO') or review.get('mode') != 'SEPARATE_READ_ONLY_SESSION':
        raise RuntimeError('NO_READY: independent technical review missing')
    validate_reference(review.get('evidence'))
    if review.get('bundle_hashes') != hashes:
        raise RuntimeError('NO_READY: review does not cover final bundle bytes')
    pilot = gates.get('real_pilot', {})
    if pilot.get('mode') != 'REAL_CODEX' or pilot.get('result') != 'PASS':
        raise RuntimeError('NO_READY: real Codex pilot has not passed')
    receipt_path = validate_reference(pilot.get('evidence'))
    loader = importlib.util.spec_from_file_location('ddd_installer_pilot_verifier', BASE/'ddd_auto.py')
    verifier = importlib.util.module_from_spec(loader)
    loader.loader.exec_module(verifier)
    try:
        verifier.validate_real_pilot(pilot['evidence'])
    except (ValueError, OSError, KeyError, TypeError) as exc:
        raise RuntimeError('NO_READY: real pilot evidence invalid: '+str(exc)) from exc
    tasks = pilot.get('tasks', [])
    if len(tasks) != 2 or {t.get('front') for t in tasks} != {'distritos-autonomicos','distritos-nacionales'} or len({t.get('task_id') for t in tasks}) != 2:
        raise RuntimeError('NO_READY: exactly two independent A/N READ_ONLY pilot tasks required')
    ids = {t.get('task_id') for t in tasks}
    real_results = [jsonread(Path(item['result_path'])) for item in jsonread(receipt_path)['tasks']]
    if {(r['task'],r['front']) for r in real_results} != {(t['task_id'],t['front']) for t in tasks}:
        raise RuntimeError('NO_READY: real receipt and gate task identities differ')
    for result in real_results:
        for role in ('executor', 'reviewer'):
            argv = result.get(role, {}).get('argv', [])
            command = ' '.join(argv) if isinstance(argv, list) else str(argv)
            if '--sandbox read-only' not in command or '--ask-for-approval never' not in command:
                raise RuntimeError('NO_READY: pilot sessions must be read-only/never')
        if not result.get('reviewer_session'):
            raise RuntimeError('NO_READY: independent pilot reviewer session missing')
    for task in tasks:
        if task.get('work_class') != 'READ_ONLY' or task.get('validator') != 'PASS' or task.get('review') not in ('GO', 'GO_ACOTADO'):
            raise RuntimeError('NO_READY: pilot validator/review missing')
        if any(dependency in ids for dependency in task.get('depends_on', [])):
            raise RuntimeError('NO_READY: pilot tasks are not independent')
        validate_reference(task.get('evidence'))
        validate_reference(task.get('review_evidence'))
    auth_path = validate_reference(gates.get('authorization_ref'))
    authorization = jsonread(auth_path)
    now = datetime.now(timezone.utc)
    try:
        start = datetime.fromisoformat(authorization['valid_from'].replace('Z', '+00:00'))
        end = datetime.fromisoformat(authorization['valid_until'].replace('Z', '+00:00'))
        current = start <= now <= end
    except (KeyError, ValueError, TypeError) as exc:
        raise RuntimeError('NO_READY: bounded owner installation authorization required') from exc
    if authorization.get('status') != 'APPROVED' or authorization.get('approved_by') != 'OWNER' or not current:
        raise RuntimeError('NO_READY: owner installation authorization absent or expired')
    if 'INSTALL_LOCAL_CONTROLLER' not in authorization.get('allowed_actions', []):
        raise RuntimeError('NO_READY: installation scope not authorized')
    if authorization.get('bundle_hashes') != hashes:
        raise RuntimeError('NO_READY: authorization does not cover final bundle bytes')
    if install_target is not None and Path(authorization.get('install_target', '')).expanduser().resolve() != Path(install_target).resolve():
        raise RuntimeError('NO_READY: installation target is outside owner scope')
    if candidate_plan:
        candidate_plan = Path(candidate_plan).resolve()
        plan_hashes = {str(p.relative_to(candidate_plan)): digest(p) for p in candidate_plan.rglob('*') if p.is_file()}
        if gates.get('migration_review', {}).get('candidate_hashes') != plan_hashes:
            raise RuntimeError('NO_READY: final candidate plan bytes are not reviewed')
        if 'MIGRATE_LOCAL_PLAN' not in authorization.get('allowed_actions', []):
            raise RuntimeError('NO_READY: live plan migration scope not authorized')
        if plan_target is None or Path(authorization.get('plan_target', '')).expanduser().resolve() != Path(plan_target).resolve():
            raise RuntimeError('NO_READY: plan target is outside owner scope')
    return {'path': str(gate_path), 'sha256': digest(gate_path), 'pilot': 'REAL_CODEX',
            'installation_status': 'READY_FOR_PILOT', 'launch_authorized': False}


def check_predecessor(target, hashes):
    if not (target/'ddd.py').is_file():
        raise RuntimeError('INSTALLED_LAUNCHER_MISSING')
    installed = digest(target/'ddd.py')
    if installed == hashes['ddd.py']:
        if any(not (target/n).is_file() or digest(target/n) != sha for n, sha in hashes.items()):
            raise RuntimeError('PARTIAL_OR_CONTRADICTORY_INSTALLATION')
        return 'CURRENT'
    for version in ('1.2.0', '1.0.0'):
        previous = BASE/'legacy'/version
        if not (previous/'ddd.py').is_file() or installed != digest(previous/'ddd.py'):
            continue
        for name in hashes:
            old, actual = previous/name, target/name
            if old.is_file() and (not actual.is_file() or digest(actual) != digest(old)):
                raise RuntimeError('INSTALLED_BYTES_CHANGED: '+name)
            if not old.is_file() and actual.exists() and version == '1.0.0' and name != 'catalogo.json':
                raise RuntimeError('UNREVIEWED_EXISTING_FILE: '+name)
        return version
    raise RuntimeError('INSTALLED_LAUNCHER_CHANGED: compare current diff')


def lock_paths(target, plan_target=None):
    paths = set(target.glob('.*.lock')) | set(target.rglob('.controller.lock'))
    if plan_target:
        paths.update(plan_target.rglob('*.lock'))
    for root in {Path(tempfile.gettempdir()), Path('/private/tmp')}:
        directory = root/'ddd-worktree-locks'
        if directory.exists():
            paths.update(directory.glob('*.lock'))
    return sorted(paths)


@contextlib.contextmanager
def acquire_existing_locks(target, plan_target=None):
    with contextlib.ExitStack() as stack:
        for path in lock_paths(target, plan_target):
            handle = stack.enter_context(path.open('rb'))
            try:
                fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError as exc:
                raise RuntimeError('ACTIVE_CONTROLLER_LOCK: '+str(path)) from exc
        yield


def check_plan_idle(plan_target):
    if plan_target and (plan_target/'estado.json').is_file():
        running = [t['id'] for t in jsonread(plan_target/'estado.json').get('tasks', []) if t.get('status') == 'RUNNING']
        if running:
            raise RuntimeError('NO_HOT_MIGRATION: RUNNING '+','.join(running))


def replace_bytes(path, data, mode):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix='.ddd-install-', dir=path.parent)
    try:
        with os.fdopen(fd, 'wb') as stream:
            stream.write(data); stream.flush(); os.fsync(stream.fileno())
        os.chmod(tmp, mode)
        os.replace(tmp, path)
        directory = os.open(path.parent, os.O_RDONLY)
        try: os.fsync(directory)
        finally: os.close(directory)
    finally:
        if os.path.exists(tmp): os.unlink(tmp)


def write_json(path, value):
    replace_bytes(path, json.dumps(value, ensure_ascii=False, indent=2).encode()+b'\n', 0o600)


def restore_files(target, backup, records):
    for name, record in records.items():
        path = target/name
        if record['existed']:
            replace_bytes(path, (backup/name).read_bytes(), record['mode'])
        elif path.exists():
            path.unlink()


def validate_relative(name):
    path = Path(name)
    if path.is_absolute() or '..' in path.parts or str(path) != name:
        raise RuntimeError('UNSAFE_MANIFEST_PATH: '+name)
    return path


def prepare_plan(candidate, target, backup):
    if not target: raise RuntimeError('PLAN_TARGET_REQUIRED')
    target, candidate = Path(target).resolve(), Path(candidate).resolve()
    if target == candidate: raise RuntimeError('ISOLATED_CANDIDATE_REQUIRED')
    migration = jsonread(candidate/'migration.json')
    for name, expected in migration['outputs'].items():
        validate_relative(name)
        if digest(candidate/name) != expected['sha256']: raise RuntimeError('CANDIDATE_PLAN_BYTES_CHANGED')
    for name in ('plan.md', 'estado.json', 'eventos.jsonl'):
        if digest(target/name) != migration['inputs'][name]['sha256']: raise RuntimeError('LIVE_PLAN_CHANGED_SINCE_CANDIDATE')
    original = (target/'eventos.jsonl').read_bytes()
    proposed = (candidate/'eventos.jsonl').read_bytes()
    if not proposed.startswith(original): raise RuntimeError('PLAN_LEDGER_PREFIX_CHANGED')
    files = {}
    for name in migration['outputs']:
        path = target/name
        if path.is_symlink(): raise RuntimeError('PLAN_SYMLINK_REFUSED')
        existed = path.is_file()
        files[name] = {'existed': existed, **(file_record(path) if existed else {})}
        if existed:
            destination = backup/'plan-before'/name
            destination.parent.mkdir(parents=True, exist_ok=True); shutil.copy2(path, destination)
        staged = backup/'plan-stage'/name
        staged.parent.mkdir(parents=True, exist_ok=True); shutil.copy2(candidate/name, staged)
    return {'target': str(target), 'files': files, 'ledger_prefix_bytes': len(original),
            'candidate_hashes': {n: v['sha256'] for n, v in migration['outputs'].items()},
            'source_ledger_sha256': hashlib.sha256(original).hexdigest()}


def apply_plan(transaction, backup):
    target = Path(transaction['target'])
    for name in transaction['files']:
        if name != 'eventos.jsonl':
            source = backup/'plan-stage'/name
            replace_bytes(target/name, source.read_bytes(), stat.S_IMODE(source.stat().st_mode))
    ledger = target/'eventos.jsonl'
    if digest(ledger) != transaction['source_ledger_sha256']: raise RuntimeError('LIVE_LEDGER_CHANGED_CONCURRENTLY')
    suffix = (backup/'plan-stage/eventos.jsonl').read_bytes()[transaction['ledger_prefix_bytes']:]
    with ledger.open('ab') as stream:
        stream.write(suffix); stream.flush(); os.fsync(stream.fileno())


def rollback_plan(transaction, backup):
    target = Path(transaction['target'])
    restore_files(target, backup/'plan-before', {n: r for n, r in transaction['files'].items() if n != 'eventos.jsonl'})
    ledger = target/'eventos.jsonl'
    original = (backup/'plan-before/eventos.jsonl').read_bytes()
    current = ledger.read_bytes()
    if current == original: return
    if not current.startswith(original) or not current.endswith(b'\n'):
        raise RuntimeError('ROLLBACK_LEDGER_RECONCILIATION_REQUIRED: no bytes removed')
    previous = jsonread(backup/'plan-before/estado.json')
    event = {'schema': 'ddd.plan-event/1.1', 'event': 'PLAN_INDEX_RECONCILIATION',
             'at': datetime.now(timezone.utc).isoformat(), 'actor': 'installer',
             'authority_ref': {'path': str(backup/'manifest.json'), 'sha256': digest(backup/'manifest.json')},
             'reason': 'Rollback of installation; appended migration events retained unchanged',
             'formal_snapshot': {t['id']: t['status'] for t in previous['tasks']},
             'previous_ledger_sha256': hashlib.sha256(current).hexdigest()}
    event['event_id'] = hashlib.sha256(json.dumps(event, sort_keys=True).encode()).hexdigest()
    with ledger.open('ab') as stream:
        stream.write(json.dumps(event, ensure_ascii=False).encode()+b'\n'); stream.flush(); os.fsync(stream.fileno())


def install(target, gates, candidate_plan=None, plan_target=None):
    target = Path(target).expanduser().resolve()
    candidate_plan = Path(candidate_plan).resolve() if candidate_plan else None
    plan_target = Path(plan_target).resolve() if plan_target else None
    hashes = bundle_hashes()
    gate = validate_gates(gates, hashes, candidate_plan, target, plan_target)
    predecessor = check_predecessor(target, hashes)
    if predecessor == 'CURRENT' and not candidate_plan: return {'status': 'ALREADY_INSTALLED', 'target': str(target)}
    check_plan_idle(plan_target)
    with acquire_existing_locks(target, plan_target):
        protected = protected_state(target)
        timestamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
        backup = target.parent/(target.name+'-backups')/timestamp
        if backup.resolve().is_relative_to(target): raise RuntimeError('EXTERNAL_BACKUP_REQUIRED')
        backup.mkdir(parents=True)
        records = {}
        for name in hashes:
            actual = target/name
            if actual.is_symlink(): raise RuntimeError('SYMLINK_TARGET_REFUSED: '+name)
            existed = actual.is_file()
            records[name] = {'existed': existed, **(file_record(actual) if existed else {})}
            if existed:
                destination = backup/name
                destination.parent.mkdir(parents=True, exist_ok=True); shutil.copy2(actual, destination)
                if file_record(destination) != file_record(actual): raise RuntimeError('BACKUP_VERIFICATION_FAILED')
        report = {'schema': 'ddd.install-backup/1.0', 'target': str(target), 'predecessor': predecessor,
                  'created_at': timestamp, 'files': records, 'installed_hashes': hashes,
                  'protected': protected, 'gate': gate, 'status': 'PREPARED'}
        write_json(backup/'manifest.json', report)
        stage = backup/'stage'
        for name, sha in hashes.items():
            destination = stage/name
            destination.parent.mkdir(parents=True, exist_ok=True); shutil.copy2(BASE/name, destination)
            if digest(destination) != sha: raise RuntimeError('STAGED_BYTES_CHANGED: '+name)
        if candidate_plan:
            report['plan_transaction'] = prepare_plan(candidate_plan, plan_target, backup)
            write_json(backup/'manifest.json', report)
        try:
            for name in [n for n in hashes if n != 'ddd.py']+['ddd.py']:
                if records[name]['existed'] and digest(target/name) != records[name]['sha256']:
                    raise RuntimeError('TARGET_CHANGED_CONCURRENTLY: '+name)
                replace_bytes(target/name, (stage/name).read_bytes(), stat.S_IMODE((stage/name).stat().st_mode))
            if protected_state(target) != protected: raise RuntimeError('PROTECTED_FILES_CHANGED_CONCURRENTLY')
            if candidate_plan: apply_plan(report['plan_transaction'], backup)
            report['status'] = 'APPLIED'; write_json(backup/'manifest.json', report)
        except BaseException:
            restore_files(target, backup, records)
            if 'plan_transaction' in report: rollback_plan(report['plan_transaction'], backup)
            report['status'] = 'ROLLED_BACK_ON_ERROR'; write_json(backup/'manifest.json', report)
            raise
        return {'status': 'INSTALLED_LOCAL_READY_FOR_PILOT', 'target': str(target), 'backup': str(backup),
                'gate': gate, 'campaign_started': False}


def rollback(target, backup):
    target, backup = Path(target).resolve(), Path(backup).resolve()
    report = jsonread(backup/'manifest.json')
    if report.get('target') != str(target) or backup.is_relative_to(target): raise RuntimeError('ROLLBACK_TARGET_MISMATCH')
    if report['status'] != 'APPLIED': raise RuntimeError('ROLLBACK_NOT_APPLICABLE')
    for name in report['files']: validate_relative(name)
    plan = report.get('plan_transaction'); plan_target = Path(plan['target']) if plan else None
    check_plan_idle(plan_target)
    with acquire_existing_locks(target, plan_target):
        for name, sha in report['installed_hashes'].items():
            if not (target/name).is_file() or digest(target/name) != sha: raise RuntimeError('ROLLBACK_CHANGED_BYTES: '+name)
        if protected_state(target) != report['protected']: raise RuntimeError('ROLLBACK_PROTECTED_BYTES_CHANGED')
        for name, rec in report['files'].items():
            if rec['existed'] and file_record(backup/name) != {k: rec[k] for k in ('sha256', 'mode')}:
                raise RuntimeError('ROLLBACK_BACKUP_INVALID')
        if plan:
            for name, sha in plan['candidate_hashes'].items():
                if name != 'eventos.jsonl' and digest(plan_target/name) != sha: raise RuntimeError('ROLLBACK_PLAN_CHANGED_BYTES')
        restore_files(target, backup, report['files'])
        if plan: rollback_plan(plan, backup)
        report['status'] = 'ROLLED_BACK'; write_json(backup/'manifest.json', report)
    return {'status': 'ROLLED_BACK', 'target': str(target), 'backup': str(backup)}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--target', type=Path, default=REAL_TARGET)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--apply', action='store_true'); mode.add_argument('--dry-run', action='store_true')
    mode.add_argument('--rollback', type=Path)
    parser.add_argument('--gate-file', type=Path); parser.add_argument('--candidate-plan', type=Path)
    parser.add_argument('--plan-target', type=Path)
    args = parser.parse_args(argv); target = args.target.expanduser().resolve()
    plan_target = args.plan_target.resolve() if args.plan_target else None
    try:
        if args.rollback: result = rollback(target, args.rollback)
        elif args.apply: result = install(target, args.gate_file, args.candidate_plan, plan_target)
        else:
            hashes = bundle_hashes(); predecessor = check_predecessor(target, hashes); reasons = []
            try: validate_gates(args.gate_file, hashes, args.candidate_plan, target, plan_target)
            except (RuntimeError, OSError, ValueError) as exc: reasons.append(str(exc))
            try:
                check_plan_idle(plan_target)
                with acquire_existing_locks(target, plan_target): pass
            except (RuntimeError, OSError) as exc: reasons.append(str(exc))
            result = {'status': 'DRY_RUN', 'writes': 0, 'target': str(target), 'predecessor': predecessor,
                      'apply': 'NO_READY' if reasons else 'GATES_PASS', 'causes': reasons, 'bundle_hashes': hashes}
        print(json.dumps(result, ensure_ascii=False)); return 0
    except (RuntimeError, OSError, ValueError, KeyError) as exc:
        print('NO_READY: '+str(exc), file=sys.stderr); return 2


if __name__ == '__main__':
    raise SystemExit(main())
