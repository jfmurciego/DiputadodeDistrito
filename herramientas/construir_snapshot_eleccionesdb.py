#!/usr/bin/env python3
from __future__ import annotations
import argparse,hashlib,json,sqlite3
from pathlib import Path
from herramientas.adaptador_eleccionesdb import ELECTIONS,sha256

def build(source:Path,out:Path,meta:Path):
 ids=sorted(v[0] for v in ELECTIONS.values()); src=sqlite3.connect(source); src.row_factory=sqlite3.Row
 if out.exists(): out.unlink()
 dst=sqlite3.connect(out)
 tables=['elecciones','elecciones_fuentes','territorios','partidos','resumen_territorial','votos_territoriales']
 for table in tables:
  sql=src.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name=?",(table,)).fetchone()
  if not sql: raise ValueError(f'Tabla ausente en snapshot upstream: {table}')
  # Esquema portable sin índices/constraints: copia columnas y datos seleccionados.
  cols=[r[1] for r in src.execute(f'PRAGMA table_info({table})')]
  decl=[]
  for r in src.execute(f'PRAGMA table_info({table})'):
   decl.append('"%s" %s'%(r[1],r[2] or 'TEXT'))
  dst.execute(f'CREATE TABLE "{table}" ({",".join(decl)})')
 ph=','.join('?'*len(ids))
 tids={r[0] for r in src.execute(f'SELECT DISTINCT territorio_id FROM resumen_territorial WHERE eleccion_id IN ({ph})',ids)}
 pids={r[0] for r in src.execute(f'SELECT DISTINCT partido_id FROM votos_territoriales WHERE eleccion_id IN ({ph})',ids)}
 def copy(table,where='',params=()):
  cols=[r[1] for r in src.execute(f'PRAGMA table_info({table})')]; q=f'SELECT * FROM {table}'+((' WHERE '+where) if where else '')
  rows=src.execute(q,params).fetchall()
  if rows: dst.executemany(f'INSERT INTO {table} VALUES ({",".join("?"*len(cols))})',[tuple(r) for r in rows])
  return len(rows)
 counts={}
 counts['elecciones']=copy('elecciones',f'id IN ({ph})',ids); counts['elecciones_fuentes']=copy('elecciones_fuentes',f'eleccion_id IN ({ph})',ids)
 tp=','.join('?'*len(tids)); pp=','.join('?'*len(pids))
 counts['territorios']=copy('territorios',f'id IN ({tp})',tuple(tids)); counts['partidos']=copy('partidos',f'id IN ({pp})',tuple(pids))
 counts['resumen_territorial']=copy('resumen_territorial',f'eleccion_id IN ({ph})',ids); counts['votos_territoriales']=copy('votos_territoriales',f'eleccion_id IN ({ph})',ids)
 dst.commit(); dst.execute('VACUUM'); dst.close(); src.close()
 payload={'schema':'ddd-eleccionesdb-snapshot/1.0','upstream_sha256':sha256(source),'snapshot_sha256':sha256(out),'election_ids':ids,'elections':sorted(ELECTIONS),'counts':counts}
 meta.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n',encoding='utf-8'); return payload

def main():
 ap=argparse.ArgumentParser(); ap.add_argument('--source',type=Path,required=True); ap.add_argument('--out',type=Path,required=True); ap.add_argument('--meta',type=Path,required=True); a=ap.parse_args(); print(json.dumps(build(a.source,a.out,a.meta),ensure_ascii=False,indent=2))
if __name__=='__main__': main()
