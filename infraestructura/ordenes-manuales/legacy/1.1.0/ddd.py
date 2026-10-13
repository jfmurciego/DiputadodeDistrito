#!/usr/bin/env python3
"""DDD 1.1.0 — 2026-10-10, controlador local candidato.
Cambio: auto con pruebas, revisión separada y diario; motivo: campaña local autónoma.
Origen/predecesor: legacy/1.0.0/ddd.py. No concede autoridad productiva.
"""
import argparse
import datetime
import fcntl
import json
import os
import queue
import shutil
import signal
import subprocess
import sys
import threading
import time
from pathlib import Path

BASE = Path(__file__).resolve().parent
DATA = Path(os.environ.get('DDD_LAUNCHER_HOME', str(BASE)))
CAT = json.loads((BASE / 'catalogo.json').read_text())
EXTRA = json.loads((BASE / 'encargos.json').read_text())
CFG = json.loads((BASE / 'parametros.json').read_text())
TASKS = {t['id']: t for t in CAT['tasks']}
FRONTS = {'fuentes-oficiales': 'FUENTES', 'distritos-autonomicos': 'AUTONÓMICOS', 'distritos-nacionales': 'NACIONALES'}
PLAN_ROOT = Path(os.environ.get('DDD_PLAN_DIR', str(Path.home() / 'Desarrollo/DDD-control/planes/ddd-maestro-20261008')))
WORK_ROOT = Path(os.environ.get('DDD_WORK_ROOT', str(Path.home() / 'Desarrollo')))


def real_repo(front):
    name = Path(CAT['worktrees'][front]['path'].replace('~/', '')).name
    return WORK_ROOT / name


def local_plan_status():
    p = PLAN_ROOT / 'estado.json'
    try:
        x = json.loads(p.read_text())
        return {t['id']: t.get('status','?') for t in x['tasks']}
    except (OSError, ValueError, KeyError) as e:
        print(f'AVISO: no se puede leer estado formal local: {e}', file=sys.stderr)
        return {}


def history():
    p = DATA / 'historial.jsonl'
    out = []
    if p.is_file():
        for line in p.read_text().splitlines():
            try:out.append(json.loads(line))
            except ValueError: pass
    return out


def shown_status(task_id, hist):
    x = [v for v in hist if v.get('task') == task_id]
    return x[-1]['result'] if x else '—'


def print_catalog():
    sts = local_plan_status(); hist=history()
    print('TABLA MAESTRA DDD — 32 tareas formales (estado tomado de estado.json local)')
    print(f'{"ID":10} {"FRENTE":12} {"FORMAL":15} {"ULTIMO INTENTO":18} {"DEPENDE":16} TAREA')
    for t in CAT['tasks']:
        print(f"{t['id']:10} {FRONTS[t['front']]:12} {sts.get(t['id'], '?'):15} {shown_status(t['id'], hist):18} {','.join(t['depends_on']) or '—':16} {t['title']}")
    print('\nÓRDENES DE CONTINUACIÓN (independientes del cierre formal de las 32 tareas):')
    for k,v in EXTRA.items():
        print(f"{k:21} {FRONTS[v['front']]:12} {v['role']:9} último={shown_status(k,hist)} — {v['title']}")
    print('\nUsa: ddd run F04 | ddd run A03 | ddd run N03. Nunca se encadenan; no repiten ID ya intentados.')
    print('FORMAL no se actualiza solo. DONE_REVIEW indica intento completado, NO PASS. Aprobaciones humanas nunca son automáticas.')


def print_info(name):
    if name in EXTRA:
        t=EXTRA[name]
        print(f"{name} | {FRONTS[t['front']]} | {t['title']}\nRevisor/Ejecutor: {t['role']} | Esfuerzo: {t['effort']}")
        print('Ruta:',real_repo(t['front']))
        print('Encargo:', (BASE/t['prompt_file']).resolve())
        print((BASE/t['prompt_file']).read_text())
    elif name in TASKS:
        t=TASKS[name]
        print(f"{name} | {FRONTS[t['front']]} | {t['title']}\nTipo: {t['execution']}\nDepende: {', '.join(t['depends_on']) or 'ninguna'}")
        print('Criterio de cierre:','; '.join(t['acceptance']))
        print('Estado formal registrado:',local_plan_status().get(name,'DESCONOCIDO'))
        if t['execution']=='approval':print('DECISIÓN HUMANA: ddd run ofrece instrucciones; no invoca Codex.')
    else:
        raise SystemExit(f'Orden desconocida: {name}. Usa "ddd list".')
    print('\nParámetros comunes:', json.dumps({k:CFG[k] for k in ('approval_policy','sandbox_ejecutor','sandbox_revisor','segundos_maximos','presupuesto_tokens_reportados_suave')},ensure_ascii=False))


def git(repo, *args):
    p=subprocess.run(['git','-C',str(repo),*args],text=True,capture_output=True)
    if p.returncode: raise RuntimeError((p.stderr or p.stdout or 'Git error').strip())
    return p.stdout.strip()


def verify_repo(front):
    p=real_repo(front)
    if not p.is_dir():raise RuntimeError(f'Worktree no encontrado: {p}')
    expected={'fuentes-oficiales':'codex/fuentes-oficiales', 'distritos-autonomicos':'codex/distritos-autonomicos','distritos-nacionales':'codex/distritos-nacionales'}[front]
    current=git(p,'branch','--show-current')
    if current!=expected:raise RuntimeError(f'RAMA INCORRECTA: {current}, se esperaba {expected}')
    head=git(p,'rev-parse','HEAD')
    first=CAT['worktrees'][front]['expected_head_prefix']
    check=subprocess.run(['git','-C',str(p),'merge-base','--is-ancestor',first,'HEAD'], capture_output=True)
    if check.returncode!=0:raise RuntimeError(f'El HEAD {head[:12]} no contiene el punto de partida esperado {first}; revisar manualmente')
    dirty=git(p,'status','--porcelain')
    return p,head,dirty


def prompt_master(t, missing=None, formal_status='UNKNOWN'):
    missing = missing or []
    deps = ', '.join(t['depends_on']) or 'ninguna'
    missing_text = ', '.join(missing) or 'ninguna registrada'
    return (f"Actúa en DDD bajo la dirección de Work. Frente: {FRONTS[t['front']]}.\n"
        f"ORDEN EXACTA {t['id']}: {t['title']}.\n"
        f"Criterios de aceptación: {'; '.join(t['acceptance'])}.\n"
        f"Dependencias declaradas: {deps}.\n"
        f"Estado formal actual: {formal_status}. Dependencias NO CERRADAS formalmente: {missing_text}.\n"
        "ALCANCE ÚNICAMENTE LOCAL NO PRODUCTIVO: investiga, verifica, prepara y cuando proceda implementa cambios locales con pruebas dirigidas. "
        "Si faltan dependencias, puedes preparar/revisar el trabajo independiente, pero NO realizar acciones que necesiten la dependencia, "
        "ni certificar la tarea, aprobar un contrato o alterar estado de producción. Indica precisamente lo que queda bloqueado.\n"
        "Antes de trabajar, consulta en el Plan Maestro la ficha de esta tarea y SOLO su evidencia directa, incluidos resultados Codex v3/v4/v4.1/v4.2; "
        "si el objetivo ya está acreditado, NO lo repitas: verifica que la evidencia existe y reporta lo pendiente.\n"
        "Compara con el HEAD, worktree y estado Git existentes; no deshagas cambios previos. Usa scripts deterministas y tests focalizados, no suites masivas.\n"
        "No alteres restricciones duras, topología, población, contratos ni procedencia para obtener un PASS artificial.\n"
        "PROHIBIDO: nuevas generaciones territoriales, 00, M04/M05 productivos, workflows, adquisición de fuentes por red, "
        "push, PR, merge, publicación, promoción, operación en otro worktree.\n"
        "ENTREGA: estado BLOCKED/READY_FOR_REVIEW/ALREADY_EVIDENCED según evidencia; SHAs; archivos; tests; "
        "criterios acreditados; bloqueos y siguiente paso. NO actualices estado.json formal ni encadenes tareas.\n")


def stop_process(p):
    if p.poll() is not None:return
    try:os.killpg(p.pid, signal.SIGTERM)
    except ProcessLookupError:return
    try:p.wait(timeout=4)
    except subprocess.TimeoutExpired:
        try:os.killpg(p.pid,signal.SIGKILL)
        except ProcessLookupError:pass
        p.wait(timeout=3)


def run(name, rerun=False):
    from ddd_auto import worktree_lock
    t = EXTRA.get(name) or TASKS.get(name)
    if t is None:
        raise RuntimeError('Tarea desconocida')
    with worktree_lock(real_repo(t['front'])):
        return run_manual(name, rerun)


def run_manual(name, rerun=False):
    if name not in EXTRA and name not in TASKS:raise RuntimeError('Tarea desconocida. Usa ddd list')
    is_extra=name in EXTRA
    t=EXTRA[name] if is_extra else TASKS[name]
    if not is_extra and t['execution']=='approval':
        print(f"{name}: DECISIÓN O AUTORIZACIÓN RESERVADA. No se invoca Codex ni se cambia el estado.")
        print('Consulta: ddd show',name)
        print('Condiciones:', '; '.join(t['acceptance']))
        return 0
    if not is_extra and name in ('F01','N01'):
        print(f'{name}: RESPALDO EXTERNO/LOCAL GOBERNADO; no se ejecuta desde Codex sandbox.')
        print('Consulta: ddd show',name)
        print('Condiciones:', '; '.join(t['acceptance']))
        return 0
    sts=local_plan_status() if not is_extra else {}
    missing=[] if is_extra else [f'{d}={sts.get(d,"UNKNOWN")}' for d in t['depends_on'] if sts.get(d) not in ('PASS','DONE','COMPLETED','CERTIFIED')]
    if not is_extra and sts.get(name) in ('PASS','DONE','COMPLETED','CERTIFIED'):
        print(f'{name} ya figura como formalmente cerrado ({sts[name]}). No se repite.')
        return 0
    if missing:
        print('AVISO: DEPENDENCIAS AÚN SIN CIERRE FORMAL: '+', '.join(missing))
        print('Se permite SOLO investigación/preparación local de esta tarea. Sin ejecución productiva ni promoción.')
    attempts=[a for a in history() if a.get('task')==name]
    if attempts and not rerun:
        raise RuntimeError(f'{name} ya se ejecutó con este lanzador ({attempts[-1]["result"]}). Ver ddd history; solo repetición manual explícita con --rerun.')
    if not shutil.which(CFG['codex_bin']):raise RuntimeError('No encuentro Codex CLI en PATH')
    p,sha,dirty=verify_repo(t['front'])
    print(f'ORDEN: {name} — {t["title"]}\nWORKTREE: {p}\nHEAD: {sha[:12]}\n')
    if dirty:
        print('ADVERTENCIA: cambios locales ya existentes. Se preservarán; este encargo puede trabajar sobre ellos.\n'+('\n'.join(dirty.splitlines()[:25])))
    role=t.get('role') or ('revisor' if t['execution'] in ('research','manual') or name=='N02' else 'ejecutor')
    sandbox=CFG['sandbox_revisor'] if role=='revisor' else CFG['sandbox_ejecutor']
    effort=t.get('effort') or ('medium' if t['front']=='distritos-autonomicos' else CFG['esfuerzo_ejecutor'])
    scope=(BASE/t['prompt_file']).read_text() if is_extra else prompt_master(t,missing,sts.get(name,'UNKNOWN'))
    pre=(f"Contexto operativo: director Work; Mac local, un solo encargo. Worktree {p}, HEAD inicial {sha}. "
         f"Usa GIS sólo si hace falta y está disponible: {CFG['python_gis']}. "
         "No actualizar estado.json del Plan Maestro ni declarar PASS formal. Cero ejecuciones productivas.\n\n")
    cmd=[CFG['codex_bin'],'--sandbox',sandbox,'--ask-for-approval',CFG['approval_policy'], '-c',f'model_reasoning_effort={effort}', 'exec','--json','-']
    print(f'COMANDO: codex --sandbox {sandbox} --ask-for-approval never -c model_reasoning_effort={effort} exec --json -')
    print(f'TIEMPO MÁXIMO: {CFG["segundos_maximos"]} s. BUDGET SUAVE: {CFG["presupuesto_tokens_reportados_suave"]} tokens reportados (NO HARD CAP).')
    answer=input('¿Lanzar exclusivamente esta tarea? [s/N] ').strip().lower()
    if answer not in ('s','si','sí'):print('Cancelado.');return 0
    DATA.mkdir(parents=True,exist_ok=True)
    logfile=DATA / 'logs';logfile.mkdir(exist_ok=True)
    runid=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    out=logfile/f'{runid}-{name}.jsonl'
    lock=DATA / ('.manual-' + t['front'] + '.lock')
    with lock.open('a+') as lf:
        try:fcntl.flock(lf,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError:raise RuntimeError('OTRA TAREA DDD MANUAL ACTIVA: espera a que termine.')
        print('INICIO; log:',out)
        started=time.monotonic(); q=queue.Queue(); usage={'input_tokens':0,'cached_input_tokens':0,'output_tokens':0,'total_tokens':0,'turns_reported':0}
        from ddd_auto import ACTIVE_LOCKS
        pr=subprocess.Popen(cmd,cwd=p,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,bufsize=1,text=True,start_new_session=True,pass_fds=tuple(ACTIVE_LOCKS))
        pr.stdin.write(pre+scope);pr.stdin.close()
        def read():
            for ln in pr.stdout:q.put(ln)
            q.put(None)
        reader=threading.Thread(target=read,daemon=True);reader.start()
        stop=None;ended=False
        with out.open('w') as f:
            while True:
                elapsed=time.monotonic()-started
                if elapsed>=CFG['segundos_maximos'] and pr.poll() is None:
                    stop='TIME_LIMIT'; stop_process(pr)
                try:line=q.get(timeout=0.5)
                except queue.Empty:
                    if pr.poll() is not None and not reader.is_alive():break
                    continue
                if line is None:ended=True;break
                f.write(line);f.flush()
                try:item=json.loads(line)
                except ValueError:
                    print(line[:350].rstrip());continue
                typ=item.get('type')
                if typ=='turn.completed':
                    raw=item.get('usage') or {}
                    for k in ('input_tokens','cached_input_tokens','output_tokens','total_tokens'):
                        usage[k]+=int(raw.get(k) or 0)
                    usage['turns_reported']+=1
                    print(f"TURNO COMPLETADO: tokens {usage['total_tokens']} (cached_input={usage['cached_input_tokens']})")
                    if usage['total_tokens']>CFG['presupuesto_tokens_reportados_suave'] and pr.poll() is None:
                        stop='SOFT_BUDGET_EXCEEDED';stop_process(pr)
                elif typ in ('turn.failed','error'):
                    print('INCIDENCIA:',str(item.get('error') or item)[:600])
                elif typ=='item.completed':
                    it=item.get('item') or {}
                    if it.get('type')=='agent_message' and it.get('text'):
                        print('CODEX:',it['text'][:1800])
            stop_process(pr) if pr.poll() is None else None
            rc=pr.wait()
            pr.stdout.close()
        result=stop or ('DONE_REVIEW' if rc==0 else 'ERROR')
        record={'task':name,'date_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'front':t['front'],'head_start':sha,'result':result,'exit_code':rc,'seconds':round(time.monotonic()-started,1),'usage':usage,'log':str(out)}
        with (DATA/'historial.jsonl').open('a') as f:f.write(json.dumps(record,ensure_ascii=False)+'\n')
        print(f'FIN: {name} => {result}; duracion={record["seconds"]}s, tokens reportados={usage["total_tokens"]}, log={out}')
        print('NOTA: DONE_REVIEW = terminó la ejecución, NO significa PASS ni GO de integración.')
        return 0 if rc==0 and not stop else 1


def main():
    parser=argparse.ArgumentParser(description='DDD: una tarea Codex por orden explícita; sin encadenamiento.')
    sub=parser.add_subparsers(dest='cmd',required=True)
    sub.add_parser('list');sub.add_parser('history')
    show=sub.add_parser('show');show.add_argument('name')
    go=sub.add_parser('run');go.add_argument('name');go.add_argument('--rerun',action='store_true',help='Repetir explícitamente una tarea que ya se ejecutó con este lanzador')
    auto=sub.add_parser('auto',help='Campaña local con dependencias técnicas y revisión por entrega')
    auto.add_argument('tasks',nargs='*',help='IDs; por defecto los 32 del catálogo')
    auto.add_argument('--dry-run',action='store_true',help='Solo lectura, cero Codex')
    auto.add_argument('--policy',type=Path,default=BASE/'auto-policy.json')
    auto.add_argument('--resume',help='Identidad de campaña; nunca repite intentos')
    a=parser.parse_args()
    try:
        if a.cmd=='auto':
            from ddd_auto import campaign
            return campaign(sys.modules[__name__],a)
        if a.cmd=='list':print_catalog()
        elif a.cmd=='show':print_info(a.name)
        elif a.cmd=='history':
            h=history()
            if not h:print('Sin ejecuciones con este lanzador (no borra ni importa los registros de v3/v4).')
            for x in h:print(f'{x["date_utc"]} {x["task"]} {x["result"]} {x["seconds"]}s {x["usage"]["total_tokens"]} tokens')
        else:return run(a.name,a.rerun)
        return 0
    except (RuntimeError,OSError,ValueError,EOFError,KeyboardInterrupt) as ex:
        print('\nNO EJECUTADO / DETENIDO:',ex,file=sys.stderr)
        return 2

if __name__=='__main__':sys.exit(main())
