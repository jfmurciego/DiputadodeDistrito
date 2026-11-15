#!/usr/bin/env python3
"""r4 en flujo continuo (frase del propietario 15-11): cada territorio P10 -> verificación -> archivo -> P00 con cadena,
con cupo de cadenas P00 en vuelo (5 hasta que las 5 primeras salgan limpias, luego 8).
Sale (para avisar) con: 0 hito (5 primeras / cada 10 cadenas OK / fin), 2 PARADA, 10 relevo por tiempo.
Reanudable: el estado está en los TSV de docs/autorizaciones y en $Q."""
import calendar, json, os, re, subprocess, sys, time
R = 'jfmurciego/DiputadodeDistrito'
Q = '/tmp/claude-0/-home-user-DiputadodeDistrito/5a52b161-2314-5f9d-b922-721b3406fb2a/scratchpad/r4'
D = '/home/user/DiputadodeDistrito/docs/autorizaciones/'
L, P, PK, A, O, E = (D + f for f in ('regeneracion_71_2026-11-14.txt', 'p10_r4_resultado.tsv', 'p10_r4_paquetes.tsv',
                                     'archivo_p10_r4_resultado.tsv', 'regeneracion_r4_resultado.tsv', 'cadenas_r4.tsv'))
V = Q + '/verif.txt'
P10_CUPO, ADELANTO, MAX_SEG = 10, 12, 100 * 60
os.chdir('/home/user/DiputadodeDistrito')
T0 = time.time()

def log(*a): print(time.strftime('%H:%M', time.gmtime()), *a, flush=True)
def gh(*a):
    for i in range(4):
        p = subprocess.run(['gh', 'api', *a], capture_output=True, text=True)
        if p.returncode == 0: return p.stdout
        time.sleep(10 * (i + 1))
    raise RuntimeError('gh ' + ' '.join(a) + ': ' + p.stderr[:200])
def tsv(f): return [l.rstrip('\n').split('\t') for l in open(f)] if os.path.exists(f) else []
def wtsv(f, rows): open(f, 'w').write(''.join('\t'.join(r) + '\n' for r in rows))
def parada(msg): log('PARADA', msg); sys.exit(2)
def ahora(): return time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())

def main_ok():
    runs = json.loads(gh('repos/%s/actions/workflows/pruebas-plataforma.yml/runs?branch=main&status=completed&per_page=30' % R))['workflow_runs']
    c = [x['conclusion'] for x in runs if x['conclusion'] != 'cancelled']
    if not c or c[0] != 'success': return 'main en rojo'
    subprocess.run(['git', 'fetch', '-q', 'origin', 'main'])
    base = open(Q + '/base').read().strip()
    d = subprocess.run(['git', 'diff', '--name-only', base, 'origin/main', '--', 'ddd_motor2', 'ddd_core', 'modulos', 'paquetes/deslinde',
                        '.github/workflows/ejecucion-completa-proyecto.yml', '.github/workflows/preparacion-fuentes.yml',
                        '.github/workflows/produccion-distritos.yml', '.github/workflows/preparacion-legislatura-vigente.yml',
                        '.github/workflows/incorporacion-resultados-electorales.yml', '.github/workflows/bateria-motor.yml'],
                       capture_output=True, text=True).stdout.split()
    return ('congelación: ' + ' '.join(d)) if d else ''

def ultimo(wf, bot=False):
    runs = json.loads(gh('repos/%s/actions/workflows/%s/runs?event=workflow_dispatch&per_page=10' % (R, wf)))['workflow_runs']
    runs = [x for x in runs if (x['actor']['login'] == 'github-actions[bot]') == bot]
    return str(runs[0]['id']) if runs else ''
def despacha(wf, inputs):
    prev = ultimo(wf)
    gh('-X', 'POST', 'repos/%s/actions/workflows/%s/dispatches' % (R, wf), '-f', 'ref=main', *sum((['-f', 'inputs[%s]=%s' % kv] for kv in inputs.items()), []))
    for _ in range(30):
        time.sleep(5); n = ultimo(wf)
        if n and n != prev: return n
    parada('sin id tras despachar %s %s' % (wf, inputs))
def estado(run):
    j = json.loads(gh('repos/%s/actions/runs/%s' % (R, run))); return j['status'], j['conclusion'] or ''

terr = [l.strip() for l in open(L) if l.strip()]
nombre_id = {}
cat = subprocess.check_output(['git', 'show', 'origin/main:configuracion/catalogo_territorios_espana_2025.yaml']).decode()
for tid, name in re.findall(r"territory_id: (aut\d\d|nac\d\d),.*?name: ([^,]+),", cat): nombre_id[name.strip()] = tid
def cid(t):
    k = re.sub(r'^\d\d ', '', t)
    if k not in nombre_id: parada('SIN_ID ' + t)
    return nombre_id[k]

aviso = int(open(Q + '/aviso_n').read()) if os.path.exists(Q + '/aviso_n') else 0
while True:
    if time.time() - T0 > MAX_SEG: log('relevo por tiempo'); sys.exit(10)
    p10 = {r[0]: r for r in tsv(P)}; arch = {r[0]: r for r in tsv(A)}; cad = {r[0]: r for r in tsv(E)}
    ver = {l.split()[0] for l in open(V)} if os.path.exists(V) else set()
    # 1. P10 en vuelo -> conclusión
    for t, r in p10.items():
        if r[2] == 'EN_VUELO':
            s, c = estado(r[1])
            if s == 'completed':
                r[2] = c; wtsv(P, list(p10.values())); log('P10', t, r[1], c)
                if c != 'success': parada('P10 %s %s %s' % (t, r[1], c))
    wtsv(PK, [['id', 'run_p10', 'artefacto', 'caduca']] + [[cid(t), r[1], '-', '-'] for t, r in p10.items()])
    # 2. verificación
    for t, r in p10.items():
        i = cid(t)
        if r[2] == 'success' and i not in ver:
            v = subprocess.run([Q + '/verif.sh', r[1], i], capture_output=True, text=True).stdout.strip()
            if not v.startswith('OK'): parada('verificación %s %s: %s' % (t, r[1], v))
            open(V, 'a').write('%s %s %s\n' % (i, r[1], v)); ver.add(i); log('verificado', t, v)
    # 3. archivo en vuelo -> conclusión
    ar = tsv(A)
    for r in ar:
        if r[3] == 'EN_VUELO':
            s, c = estado(r[2])
            if s == 'completed':
                r[3] = c; wtsv(A, ar); log('archivo', r[0], r[2], c)
                if c != 'success': parada('archivo %s %s %s' % (r[0], r[2], c))
    arch = {r[0]: r for r in ar}
    # 4. cadenas en vuelo
    vuelo = [r for r in cad.values() if r[5] == 'EN_VUELO']
    if vuelo:
        desde = min(r[6] for r in vuelo); runs = []
        for wf in ('ejecucion-completa-proyecto.yml', 'preparacion-legislatura-vigente.yml'):
            for pg in (1, 2, 3):
                w = json.loads(gh('repos/%s/actions/workflows/%s/runs?created=>=%s&per_page=100&page=%d' % (R, wf, desde, pg)))['workflow_runs']
                runs += w
                if len(w) < 100: break
        for r in vuelo:
            t = r[0]; mio = [x for x in runs if str(x['id']) == r[1]]
            hijos = [x for x in runs if x['actor']['login'] == 'github-actions[bot]' and ('· %s ·' % t) in x['display_title'] and x['created_at'] >= r[6]]
            act = [x for x in hijos if x['name'].startswith('Activación')]; ele = [x for x in hijos if 'Reutilizar' in x['display_title']]
            r[2] = str(act[-1]['id']) if act else '-'; r[3] = str(ele[-1]['id']) if ele else '-'
            todos = mio + act[-1:] + ele[-1:]
            malos = [x for x in todos if x['status'] == 'completed' and x['conclusion'] != 'success']
            if malos:
                r[4] = '/'.join('%s:%s' % (x['id'], x['conclusion']) for x in todos); r[5] = 'FALLO'; wtsv(E, list(cad.values()))
                parada('cadena %s %s' % (t, r[4]))
            if ele and ele[-1]['status'] == 'completed':
                r[4] = 'success'; r[5] = 'OK'; log('cadena OK', t, r[1], r[2], r[3])
            elif mio and mio[0]['status'] == 'completed' and not act:
                fin = mio[0]['updated_at']
                if time.time() - calendar.timegm(time.strptime(fin, "%Y-%m-%dT%H:%M:%SZ")) > 1800:
                    parada('cadena %s: territorial %s terminó y no hay Activación en 30 min' % (t, r[1]))
        wtsv(E, list(cad.values()))
    okn = sum(1 for r in cad.values() if r[5] == 'OK')
    if okn == len(terr): log('FIN: %d cadenas OK' % okn); sys.exit(0)
    if (okn >= 5 and aviso < 5) or okn // 10 > aviso // 10:
        open(Q + '/aviso_n', 'w').write(str(okn)); log('HITO %d cadenas OK' % okn); sys.exit(0)
    # 5. lanzamientos (tras comprobar main y congelación)
    m = main_ok()
    if m:
        if 'congelación' in m: parada(m)
        log('espera:', m); time.sleep(120); continue
    env = sum(1 for r in cad.values() if r[5] == 'EN_VUELO'); cupo = 8 if okn >= 5 else 5
    for t in terr:
        if env >= cupo: break
        i = cid(t)
        if t in cad or t not in p10: continue
        if p10[t][2] == 'success' and i in ver and i in arch and arch[i][3] == 'success':
            n = despacha('ejecucion-completa-proyecto.yml', {'territory_id': t, 'data_edition': '2025',
                         'execution_mode': 'Generar desde fuente territorial acreditada', 'optimization_algorithm': 'Canónico',
                         'motor': 'motor2', 'publication_mode': 'territorial_only', 'publish_result': 'false', 'cadena_electoral': 'true'})
            cad[t] = [t, n, '-', '-', '-', 'EN_VUELO', ahora()]; wtsv(E, list(cad.values()))
            open(O, 'a').write('%s\t%s\tterritorial\n' % (t, n)); env += 1; log('P00 lanzada', t, n)
    for t in terr:
        i = cid(t) if t in p10 else None
        if t in p10 and p10[t][2] == 'success' and i in ver and i not in arch:
            n = despacha('bateria-motor.yml', {'territorios': i, 'archivar_p10': p10[t][1], 'motor': 'motor2'})
            open(A, 'a').write('%s\t%s\t%s\tEN_VUELO\n' % (i, p10[t][1], n)); arch[i] = [i, p10[t][1], n, 'EN_VUELO']; log('archivo lanzado', t, n)
    pend = sum(1 for t in terr if t in p10 and t not in cad)
    vp = sum(1 for r in p10.values() if r[2] == 'EN_VUELO')
    for t in terr:
        if vp >= P10_CUPO or pend >= ADELANTO: break
        if t in p10: continue
        n = despacha('preparacion-fuentes.yml', {'territory_id': t})
        open(P, 'a').write('%s\t%s\tEN_VUELO\n' % (t, n)); p10[t] = [t, n, 'EN_VUELO']; vp += 1; pend += 1; log('P10 lanzado', t, n)
    time.sleep(120)
