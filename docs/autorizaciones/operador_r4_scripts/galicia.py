#!/usr/bin/env python3
"""aut12 Galicia con espejo R2 (frase del propietario 16-11): espera pruebas verdes en main, lanza una vez, sigue la cadena. Sin reintento."""
import json, subprocess, sys, time
R = 'jfmurciego/DiputadodeDistrito'; T = '12 Galicia'
def log(*a): print(time.strftime('%H:%M', time.gmtime()), *a, flush=True)
def gh(*a):
    for i in range(4):
        p = subprocess.run(['gh', 'api', *a], capture_output=True, text=True)
        if p.returncode == 0: return p.stdout
        time.sleep(10 * (i + 1))
    raise RuntimeError(p.stderr[:200])
def J(*a): return json.loads(gh(*a))
t0 = time.time()
while True:
    runs = J('repos/%s/actions/workflows/pruebas-plataforma.yml/runs?branch=main&per_page=30' % R)['workflow_runs']
    c = [x for x in runs if x['status'] == 'completed' and x['conclusion'] != 'cancelled']
    if c and c[0]['created_at'] > '2026-11-16T07:46:00Z':
        if c[0]['conclusion'] != 'success': log('NO LANZADO: main en rojo', c[0]['id']); sys.exit(3)
        log('main verde', c[0]['id'], c[0]['head_sha'][:8]); break
    if time.time() - t0 > 3600: log('NO LANZADO: sin pruebas terminadas en 1 h'); sys.exit(4)
    time.sleep(90)
wf = 'ejecucion-completa-proyecto.yml'
prev = J('repos/%s/actions/workflows/%s/runs?event=workflow_dispatch&per_page=5' % (R, wf))['workflow_runs'][0]['id']
inp = {'territory_id': T, 'data_edition': '2025', 'execution_mode': 'Generar desde fuente territorial acreditada', 'optimization_algorithm': 'Canónico',
       'motor': 'motor2', 'publication_mode': 'territorial_only', 'publish_result': 'false', 'cadena_electoral': 'true'}
gh('-X', 'POST', 'repos/%s/actions/workflows/%s/dispatches' % (R, wf), '-f', 'ref=main', *sum((['-f', 'inputs[%s]=%s' % kv] for kv in inp.items()), []))
desde = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime(time.time() - 60))
for _ in range(30):
    time.sleep(5)
    rs = [x for x in J('repos/%s/actions/workflows/%s/runs?event=workflow_dispatch&per_page=5' % (R, wf))['workflow_runs'] if x['actor']['login'] != 'github-actions[bot]']
    if rs and rs[0]['id'] != prev: mio = rs[0]['id']; break
else: log('PARADA sin id tras despachar'); sys.exit(2)
log('P00 lanzada', T, mio)
open('/home/user/DiputadodeDistrito/docs/autorizaciones/cadenas_r4.tsv', 'a').write('%s\t%s\t-\t-\t-\tEN_VUELO\t%s\n' % (T, mio, desde))
while True:
    time.sleep(240)
    runs = []
    for w in (wf, 'preparacion-legislatura-vigente.yml'):
        runs += J('repos/%s/actions/workflows/%s/runs?created=>=%s&per_page=100' % (R, w, desde))['workflow_runs']
    m = [x for x in runs if x['id'] == mio]
    h = [x for x in runs if x['actor']['login'] == 'github-actions[bot]' and ('· %s ·' % T) in x['display_title']]
    act = [x for x in h if x['name'].startswith('Activación')]; ele = [x for x in h if 'Reutilizar' in x['display_title']]
    todos = m + act[-1:] + ele[-1:]
    malos = [x for x in todos if x['status'] == 'completed' and x['conclusion'] != 'success']
    ids = '/'.join('%s:%s' % (x['id'], x['status'] if x['status'] != 'completed' else x['conclusion']) for x in todos)
    if malos: log('PARADA cadena', T, ids); sys.exit(2)
    if ele and ele[-1]['status'] == 'completed': log('cadena OK', T, ids); sys.exit(0)
    if m and m[0]['status'] == 'completed' and not act and time.time() - time.mktime(time.strptime(m[0]['updated_at'], '%Y-%m-%dT%H:%M:%SZ')) + time.timezone > 1800:
        log('PARADA sin Activación en 30 min', ids); sys.exit(2)
