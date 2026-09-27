#!/usr/bin/env python3
from __future__ import annotations
import argparse,json,sqlite3,sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from herramientas.adaptador_eleccionesdb import ELECTIONS,sha256

def build(source:Path,out:Path,meta:Path):
 specs=sorted({(v[0],v[1]) for v in ELECTIONS.values()})
 ids=sorted({eid for eid,_ in specs})
 src=sqlite3.connect(source); src.row_factory=sqlite3.Row
 if out.exists(): out.unlink()
 dst=sqlite3.connect(out)
 tables=['elecciones','elecciones_fuentes','territorios','partidos','resumen_territorial','votos_territoriales']
 for table in tables:
  sql=src.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name=?",(table,)).fetchone()
  if not sql: raise ValueError(f'Tabla ausente en snapshot upstream: {table}')
  decl=[]
  for r in src.execute(f'PRAGMA table_info({table})'):
   decl.append('"%s" %s'%(r[1],r[2] or 'TEXT'))
  dst.execute(f'CREATE TABLE "{table}" ({",".join(decl)})')
 def copy(table,where='',params=()):
  cols=[r[1] for r in src.execute(f'PRAGMA table_info({table})')]
  q=f'SELECT * FROM {table}'+((' WHERE '+where) if where else '')
  rows=src.execute(q,params).fetchall()
  if rows: dst.executemany(f'INSERT INTO {table} VALUES ({",".join("?"*len(cols))})',[tuple(r) for r in rows])
  return len(rows)

 tids=set()
 for eid,ccaa in specs:
  tids.update(r[0] for r in src.execute(
   """SELECT DISTINCT t.id
      FROM resumen_territorial r JOIN territorios t ON t.id=r.territorio_id
      WHERE r.eleccion_id=? AND t.tipo='seccion'
        AND printf('%02d',CAST(t.codigo_ccaa AS INTEGER))=?""",(eid,ccaa)))
 if not tids: raise ValueError('Snapshot EleccionesDB sin secciones para elecciones configuradas')

 ph_ids=','.join('?'*len(ids)); ph_tids=','.join('?'*len(tids))
 vote_params=tuple(ids)+tuple(tids)
 pids={r[0] for r in src.execute(
  f'SELECT DISTINCT partido_id FROM votos_territoriales WHERE eleccion_id IN ({ph_ids}) AND territorio_id IN ({ph_tids})',
  vote_params)}
 if not pids: raise ValueError('Snapshot EleccionesDB sin partidos para elecciones configuradas')
 ph_pids=','.join('?'*len(pids))

 counts={}
 counts['elecciones']=copy('elecciones',f'id IN ({ph_ids})',tuple(ids))
 counts['elecciones_fuentes']=copy('elecciones_fuentes',f'eleccion_id IN ({ph_ids})',tuple(ids))
 counts['territorios']=copy('territorios',f'id IN ({ph_tids})',tuple(tids))
 counts['partidos']=copy('partidos',f'id IN ({ph_pids})',tuple(pids))
 counts['resumen_territorial']=copy('resumen_territorial',
  f'eleccion_id IN ({ph_ids}) AND territorio_id IN ({ph_tids})',vote_params)
 counts['votos_territoriales']=copy('votos_territoriales',
  f'eleccion_id IN ({ph_ids}) AND territorio_id IN ({ph_tids})',vote_params)
 dst.commit(); dst.execute('VACUUM'); dst.close(); src.close()
 payload={
  'schema':'ddd-eleccionesdb-snapshot/1.1',
  'upstream_sha256':sha256(source),
  'snapshot_sha256':sha256(out),
  'election_ids':ids,
  'logical_election_count':len(ELECTIONS),
  'territory_slices':[{'eleccionesdb_election_id':eid,'codigo_ccaa':ccaa} for eid,ccaa in specs],
  'elections':sorted(ELECTIONS),
  'counts':counts
 }
 meta.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 return payload

def main():
 ap=argparse.ArgumentParser()
 ap.add_argument('--source',type=Path,required=True)
 ap.add_argument('--out',type=Path,required=True)
 ap.add_argument('--meta',type=Path,required=True)
 a=ap.parse_args()
 print(json.dumps(build(a.source,a.out,a.meta),ensure_ascii=False,indent=2))

if __name__=='__main__': main()
