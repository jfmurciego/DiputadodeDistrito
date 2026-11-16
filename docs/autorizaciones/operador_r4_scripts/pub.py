#!/usr/bin/env python3
"""Paso 5 r4 (frase del propietario 16-11): P50 de las 71 composiciones, lotes de <=12 runs electorales, parada al primer fallo.
Estado en docs/autorizaciones/publicacion_r4.tsv (lote, runs, run_p50, estado). Sale: 0 fin, 2 PARADA, 10 relevo, 5 esperando aprobación (aviso)."""
import json, os, subprocess, sys, time
R = 'jfmurciego/DiputadodeDistrito'; Q = os.path.dirname(os.path.abspath(__file__))
D = '/home/user/DiputadodeDistrito/docs/autorizaciones/'; S = D + 'publicacion_r4.tsv'; T0 = time.time()
def log(*a): print(time.strftime('%H:%M', time.gmtime()), *a, flush=True)
def gh(*a):
    for i in range(4):
        p = subprocess.run(['gh', 'api', *a], capture_output=True, text=True)
        if p.returncode == 0: return p.stdout
        time.sleep(10 * (i + 1))
    raise RuntimeError(p.stderr[:200])
def J(*a): return json.loads(gh(*a))
def tsv(f): return [l.rstrip('\n').split('\t') for l in open(f)] if os.path.exists(f) else []
def main_verde():
    for pg in range(1, 6):
        rs = J('repos/%s/actions/workflows/pruebas-plataforma.yml/runs?branch=main&status=completed&per_page=100&page=%d' % (R, pg))['workflow_runs']
        c = [x['conclusion'] for x in rs if x['conclusion'] != 'cancelled']
        if c: return c[0] == 'success'
    return False
def congelado():
    subprocess.run(['git', '-C', '/home/user/DiputadodeDistrito', 'fetch', '-q', 'origin', 'main'])
    base = open(Q + '/base_p50').read().strip()
    return subprocess.run(['git', '-C', '/home/user/DiputadodeDistrito', 'diff', '--name-only', base, 'origin/main', '--', 'ddd_motor2', 'ddd_core', 'modulos',
        '.github/workflows/desplegar-visor-publico.yml', '.github/workflows/ejecucion-completa-proyecto.yml'], capture_output=True, text=True).stdout.split()
cad = [r for r in tsv(D + 'cadenas_r4.tsv') if r[5] == 'OK']
runs = [r[3] for r in cad]
assert len(runs) == 71 and len(set(runs)) == 71, len(runs)
lotes = [runs[i:i + 12] for i in range(0, len(runs), 12)]
while True:
    if time.time() - T0 > 100 * 60: log('relevo'); sys.exit(10)
    st = tsv(S)
    if st and st[-1][3] == 'EN_VUELO':
        j = J('repos/%s/actions/runs/%s' % (R, st[-1][2]))
        if j['status'] == 'completed':
            st[-1][3] = j['conclusion']; open(S, 'w').write(''.join('\t'.join(r) + '\n' for r in st))
            log('lote', st[-1][0], st[-1][2], j['conclusion'])
            if j['conclusion'] != 'success': log('PARADA lote', st[-1][0]); sys.exit(2)
        else:
            if j['status'] == 'waiting' and not os.path.exists(Q + '/avisado_' + st[-1][2]):
                open(Q + '/avisado_' + st[-1][2], 'w').write('1'); log('ESPERA APROBACIÓN', st[-1][2]); sys.exit(5)
            time.sleep(120); continue
    n = len(st)
    if n == len(lotes): log('FIN: %d lotes publicados' % n); sys.exit(0)
    if not main_verde(): log('espera: main en rojo'); time.sleep(180); continue
    c = congelado()
    if c: log('PARADA congelación', ' '.join(c)); sys.exit(2)
    lote = lotes[n]; wf = 'desplegar-visor-publico.yml'
    prev = J('repos/%s/actions/workflows/%s/runs?event=workflow_dispatch&per_page=3' % (R, wf))['workflow_runs'][0]['id']
    gh('-X', 'POST', 'repos/%s/actions/workflows/%s/dispatches' % (R, wf), '-f', 'ref=main', '-f', 'inputs[pagina_publicar]=Sitio completo',
       '-f', 'inputs[production_run_id]=' + ' '.join(lote))
    for _ in range(30):
        time.sleep(5); x = J('repos/%s/actions/workflows/%s/runs?event=workflow_dispatch&per_page=3' % (R, wf))['workflow_runs'][0]['id']
        if x != prev: break
    else: log('PARADA sin id'); sys.exit(2)
    open(S, 'a').write('%d\t%s\t%s\tEN_VUELO\n' % (n + 1, ' '.join(lote), x)); log('lote lanzado', n + 1, x, len(lote), 'runs')
