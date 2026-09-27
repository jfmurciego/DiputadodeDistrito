#!/usr/bin/env python3
from __future__ import annotations
import argparse,csv,hashlib,json,sqlite3
from datetime import datetime,timezone,timedelta
from pathlib import Path

# Única configuración territorial: el algoritmo es común para todas las elecciones.
ELECTIONS={
 'illes_balears_parlament_2023':(235,'04','illes_balears','2023-05-28'),
 'canarias_parlamento_2023':(236,'05','canarias','2023-05-28'),
 'cantabria_parlamento_2023':(237,'06','cantabria','2023-05-28'),
 'castilla_la_mancha_cortes_2023':(238,'08','castilla_la_mancha','2023-05-28'),
 'comunidad_madrid_asamblea_2023':(240,'13','madrid','2023-05-28'),
 'region_murcia_asamblea_2023':(241,'14','region_de_murcia','2023-05-28'),
 'navarra_parlamento_2023':(242,'15','comunidad_foral_de_navarra','2023-05-28'),
 'la_rioja_parlamento_2023':(243,'17','la_rioja','2023-05-28'),
 'comunidad_valenciana_corts_2023':(244,'10','comunidad_valenciana','2023-05-28'),
 'pais_vasco_parlamento_2024':(250,'16','pais_vasco','2024-04-21'),
 'ceuta_asamblea_local_2023':(247,'18','ceuta','2023-05-28'),
 'melilla_asamblea_local_2023':(247,'19','melilla','2023-05-28'),
}

def sha256(path:Path)->str:
 h=hashlib.sha256()
 with path.open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''): h.update(b)
 return h.hexdigest()

def _normalize_date(value)->str:
 """Normaliza ISO o serial Unix-days usado por el export SQLite de EleccionesDB."""
 if value is None or value=='': return ''
 if isinstance(value,(int,float)):
  return (datetime(1970,1,1,tzinfo=timezone.utc)+timedelta(days=float(value))).date().isoformat()
 text=str(value).strip()
 try:
  numeric=float(text)
 except ValueError:
  return text[:10]
 return (datetime(1970,1,1,tzinfo=timezone.utc)+timedelta(days=numeric)).date().isoformat()

def _columns(con,table): return {r[1] for r in con.execute(f'PRAGMA table_info({table})')}
def _party_expr(con):
 cols=_columns(con,'partidos')
 if 'siglas' in cols: return "COALESCE(NULLIF(p.siglas,''),NULLIF(p.denominacion,''),CAST(p.id AS TEXT))"
 return 'CAST(p.id AS TEXT)'

def build(db:Path,election_id:str,out:Path,snapshot_sha256:str|None=None,edition:str='2025')->dict:
 if election_id not in ELECTIONS: raise ValueError(f'Elección no autorizada para adaptador EleccionesDB: {election_id}')
 edb_id,ccaa,territory,expected_date=ELECTIONS[election_id]
 actual_snapshot=sha256(db)
 if snapshot_sha256 and actual_snapshot!=snapshot_sha256: raise ValueError('Huella del snapshot EleccionesDB no coincide')
 con=sqlite3.connect(db); con.row_factory=sqlite3.Row
 e=con.execute('SELECT * FROM elecciones WHERE id=?',(edb_id,)).fetchone()
 if not e: raise ValueError(f'Elección EleccionesDB ausente: {edb_id}')
 raw_date=e['fecha'] if 'fecha' in e.keys() else None
 date=_normalize_date(raw_date)
 if date and date!=expected_date: raise ValueError(f'Fecha electoral incorrecta: {date} (raw={raw_date}) != {expected_date}')
 srcs=con.execute('SELECT * FROM elecciones_fuentes WHERE eleccion_id=?',(edb_id,)).fetchall()
 if not srcs: raise ValueError('Elección sin procedencia original verificable')
 publishers=[]
 for s in srcs:
  d=dict(s); label=str(d.get('fuente') or '').strip(); url=str(d.get('url_fuente') or '').strip()
  if label or url: publishers.append({'fuente':label,'url':url,'observaciones':str(d.get('observaciones') or '')})
 if not publishers: raise ValueError('Procedencia electoral vacía')
 rows=con.execute('''SELECT t.id,t.codigo_ccaa,t.codigo_provincia,t.codigo_municipio,t.codigo_distrito,t.codigo_seccion
                    FROM resumen_territorial r JOIN territorios t ON t.id=r.territorio_id
                    WHERE r.eleccion_id=? AND t.tipo='seccion'
                      AND printf('%02d',CAST(t.codigo_ccaa AS INTEGER))=?
                    ORDER BY t.id''',(edb_id,ccaa)).fetchall()
 if not rows:
  observed=[str(r[0] or '').zfill(2) for r in con.execute("""SELECT DISTINCT t.codigo_ccaa
    FROM resumen_territorial r JOIN territorios t ON t.id=r.territorio_id
    WHERE r.eleccion_id=? AND t.tipo='seccion' ORDER BY t.codigo_ccaa""",(edb_id,)).fetchall()]
  if observed: raise ValueError(f'Territorio equivocado en elección {edb_id}: CCAA esperada={ccaa}, observadas={observed}')
  raise ValueError('Elección con cero secciones')
 sections={}
 for r in rows:
  if str(r['codigo_ccaa'] or '').zfill(2)!=ccaa: raise ValueError(f'Territorio equivocado en elección {edb_id}: CCAA={r["codigo_ccaa"]}')
  parts=[str(r[k] or '').strip() for k in ('codigo_provincia','codigo_municipio','codigo_distrito','codigo_seccion')]
  if not all(parts) or not all(x.isdigit() for x in parts): raise ValueError(f'Sección no identificable: {dict(r)}')
  prov=parts[0].zfill(2); mun=parts[1].zfill(3); dist=parts[2].zfill(2); sec=str(int(parts[3])).zfill(3)
  cusec=prov+mun+dist+sec
  if len(cusec)!=10: raise ValueError(f'CUSEC inválido: {cusec}')
  sections[r['id']]=cusec
 pexpr=_party_expr(con)
 votes=con.execute(f'''SELECT v.territorio_id,{pexpr} party,v.votos FROM votos_territoriales v
                       JOIN territorios t ON t.id=v.territorio_id JOIN partidos p ON p.id=v.partido_id
                       WHERE v.eleccion_id=? AND t.tipo='seccion'
                         AND printf('%02d',CAST(t.codigo_ccaa AS INTEGER))=?
                       ORDER BY v.territorio_id,p.id''',(edb_id,ccaa)).fetchall()
 if not votes: raise ValueError('Elección con cero votos por sección')
 out.mkdir(parents=True,exist_ok=True)
 data_dir=out/'data'; contract_dir=out/'contract'
 data_dir.mkdir(parents=True,exist_ok=True); contract_dir.mkdir(parents=True,exist_ok=True)
 csv_path=data_dir/'resultados_electorales_normalizados.csv'; parties=set(); records=0; total_votes=0
 with csv_path.open('w',encoding='utf-8',newline='') as f:
  w=csv.DictWriter(f,fieldnames=['CUSEC_KEY','party','votes'],delimiter=';'); w.writeheader()
  for v in votes:
   if v['territorio_id'] not in sections: raise ValueError(f'Voto ligado a sección no identificable: {v["territorio_id"]}')
   party=str(v['party'] or '').strip()
   if not party: raise ValueError('Voto sin partido identificable')
   n=int(v['votos'] or 0)
   if n<0: raise ValueError('Votos negativos')
   w.writerow({'CUSEC_KEY':sections[v['territorio_id']],'party':party,'votes':n}); parties.add(party); records+=1; total_votes+=n
 if records==0 or total_votes==0: raise ValueError('Paquete sin votos válidos')

 dictionary=contract_dir/'party_dictionary.json'
 dictionary.write_text(json.dumps({
  'schema_family':'ddd-party-dictionary',
  'schema_version':'1.0.0',
  'unknown_party_policy':'reject',
  'parties':[{'canonical_id':p,'display_name':p,'aliases':[],'classification':''} for p in sorted(parties)],
 },ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

 source_url=next((str(x.get('url') or '').strip() for x in publishers if str(x.get('url') or '').strip()),'')
 publisher=' + '.join(str(x.get('fuente') or '').strip() for x in publishers if str(x.get('fuente') or '').strip()) or 'EleccionesDB'
 contract=contract_dir/'election_contract.json'
 contract_payload={
  'schema_family':'ddd-election',
  'schema_version':'1.0.0',
  'election_id':election_id,
  'territory_id':territory,
  'title':election_id,
  'election_date':expected_date,
  'input_mode':'verifiable_file',
  'boundary_independence':True,
  'sources':[{
   'path':'data/resultados_electorales_normalizados.csv',
   'sha256':sha256(csv_path),
   'publisher':publisher,
   'source_url':source_url,
   'adapter':{'kind':'long_csv','separator':';','section_field':'CUSEC_KEY','party_field':'party','votes_field':'votes'},
   'upstream_snapshot':{
    'adapter':'eleccionesdb_sqlite/1.0',
    'eleccionesdb_election_id':edb_id,
    'codigo_ccaa':ccaa,
    'snapshot_sha256':actual_snapshot,
    'provenance':publishers,
   },
  }],
  'party_dictionary':{'path':'contract/party_dictionary.json','sha256':sha256(dictionary)},
  'reconciliation':{'policy':'fail_unless_declared','allowed_result_only_sections':[],'allowed_map_only_sections':[]},
  'source_verification':{
   'status':'VERIFIED_SOURCE_CHAIN',
   'sections':len(set(sections.values())),
   'records':records,
   'candidate_votes':total_votes,
   'snapshot_sha256':actual_snapshot,
  },
 }
 contract.write_text(json.dumps(contract_payload,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

 selected_sha=sha256(csv_path)
 manifest={
  'schema':'ddd-electoral-package/1.0',
  'decision':'ACQUIRE',
  'adapter':'eleccionesdb_sqlite/1.0',
  'territory_id':territory,
  'edition':str(edition),
  'election_id':election_id,
  'election_date':expected_date,
  'source_status':'VERIFIED_SOURCE_CHAIN',
  'selected_source':{
   'path':'data/resultados_electorales_normalizados.csv',
   'sha256':selected_sha,
   'bytes':csv_path.stat().st_size,
   'source_class':'verified_snapshot',
  },
  'embedded_contract':{
   'election_contract':'contract/election_contract.json',
   'party_dictionary':'contract/party_dictionary.json',
   'contract_sha256':sha256(contract),
   'party_dictionary_sha256':sha256(dictionary),
  },
  'eleccionesdb_election_id':edb_id,
  'snapshot_sha256':actual_snapshot,
  'source_sha256':selected_sha,
  'sections':len(set(sections.values())),
  'records':records,
  'parties':len(parties),
  'candidate_votes':total_votes,
  'provenance':publishers,
  'generated_at':datetime.now(timezone.utc).isoformat(),
 }
 (out/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 con.close(); return manifest

def main():
 ap=argparse.ArgumentParser(); ap.add_argument('--sqlite',type=Path,required=True); ap.add_argument('--election-id',required=True); ap.add_argument('--out',type=Path,required=True); ap.add_argument('--snapshot-sha256'); ap.add_argument('--edition',default='2025')
 a=ap.parse_args(); print(json.dumps(build(a.sqlite,a.election_id,a.out,a.snapshot_sha256,a.edition),ensure_ascii=False,indent=2))
if __name__=='__main__': main()
