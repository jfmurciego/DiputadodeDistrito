import sys, json, csv, copy, tempfile, shutil, collections, hashlib
from pathlib import Path
import yaml
ROOT=Path('/home/user/DiputadodeDistrito'); S=Path(sys.argv[1]); ZIP=S/'zip/02202307_MESA.zip'
sys.path.insert(0,str(ROOT)); sys.path.insert(0,str(ROOT/'herramientas'))
import fuente_infoelectoral_mesas as fim, resultados_partidos as rp, resultados_ligeros as rl
import homologacion_candidaturas_2026 as hc, reparto_art162 as ra
import registro_publicaciones_visor as rv
raw=yaml.safe_load((ROOT/'configuracion/contratos_infoelectoral.yaml').read_text())
uni=yaml.safe_load((ROOT/'configuracion/elecciones_generales_2026.yaml').read_text())
reglas=json.load(open(ROOT/'datos/homologacion_siglas/reglas_candidaturas_2026.json'))
cand=collections.defaultdict(set)
for c in csv.DictReader(open(ROOT/'configuracion/candidaturas_congreso_2026.csv',encoding='utf-8')): cand[c['codigo']].add(c['siglas'])
m08=rl.vigentes(); res=ROOT/'datos/resultados'; comp=ROOT/'datos/composicion'
rep={}
for circ in uni['circunscripciones']:
    t=circ['territory_id']; r={'escanos_2026':circ['escanos_2026'],'escanos_2023':circ['escanos_2023']}
    rep[t]=r
    try:
        c=copy.deepcopy(raw['contracts'][f'{t}_2023-07-23']); c['election_date']='2026-11-29'
        # resolver con identidad 2026 (usa un YAML temporal con la clave 2026)
        tmp=S/'out'/'contratos_2026.yaml'
        yaml.safe_dump({'schema':raw['schema'],'contracts':{circ['election_id']:c}},tmp.open('w'),allow_unicode=True)
        ct=fim.resolve(election_id=circ['election_id'],territory_id=t,election_date='2026-11-29',root_dir=Path('/'),contract_path=tmp)
        r['contrato']='OK'
        with tempfile.TemporaryDirectory() as d:
            sm=fim.convert(ZIP,ct,Path(d)/'m.csv'); rows=list(csv.DictReader(open(Path(d)/'m.csv',encoding='utf-8')))
        r['ingesta']=f"{sm['sections']} secc, {sm['polling_stations']} mesas, {sm['candidate_votes']} votos"
        votos=collections.Counter()
        for x in rows: votos[x['partido']]+=int(x['votos'])
        # homologación
        cod=circ['codigo']; hom=collections.Counter(); sin=[]
        for s,v in votos.items():
            h,cert,rid=hc.resolver(reglas,s)
            hom[h]+=v
            if rid=='IDENTIDAD' and s not in cand[cod]: sin.append(s)
        r['siglas_zip']=len(votos); r['sin_candidatura_2026']=sorted(sin)
        r['votos_en_siglas_sin_cand']=sum(votos[s] for s in sin)
        # D'Hondt 2026 (K=escaños 2026) sobre votos 2023, umbral 3 % sobre votos válidos (blancos incl. no: solo candidaturas)
        tot=sum(votos.values()) ; blank=sum(1 for _ in [])
        bl=sm['blank_votes']; umbral=0.03*(tot+bl)
        ok={p:v for p,v in hom.items() if v>=umbral}
        r['escanos']=ra.dhondt(ok,circ['escanos_2026'])
        # asignación por distrito
        if t in m08:
            gan=rl.ganadores(res,t,m08[t]); cm=json.load(open(comp/'MANIFEST.json'))['territorios'][t]
            cm_=rp.leer_composicion(comp/f'{t}.csv')
            eq=rp.leer_equivalencia(); pob=rp.leer_poblacion(comp/f'{t}.csv')
            body,inf=rp.agregar_informe(ZIP,ct,cm_,gan,eq,pob)
            ref=(res/f'{t}_partidos.csv')
            r['distritos']=len(gan); r['igual_que_2023_publicado']= ref.exists() and ref.read_bytes()==body
            r['desajuste_pct']=inf.get('pct_desajuste',0) if inf else 0
            (S/'out'/f'{t}_partidos_2026sim.csv').write_bytes(body)
        else: r['distritos']=None; r['error_dist']='sin canonical_m08 vigente'
    except Exception as e:
        r['error']=f'{type(e).__name__}: {str(e)[:200]}'
json.dump(rep,open(S/'out/informe.json','w'),ensure_ascii=False,indent=1)
n=len(rep); print('52?',n,'errores',sum('error' in r for r in rep.values()),'igual',sum(r.get('igual_que_2023_publicado') is True for r in rep.values()))
for t,r in rep.items():
    if 'error' in r or r.get('igual_que_2023_publicado') is False or 'error_dist' in r or r.get('sin_candidatura_2026'): print(t,{k:r[k] for k in r if k in('error','error_dist','igual_que_2023_publicado','sin_candidatura_2026','votos_en_siglas_sin_cand','desajuste_pct')})
