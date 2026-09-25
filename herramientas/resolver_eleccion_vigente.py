#!/usr/bin/env python3
from __future__ import annotations
import argparse,json
from datetime import date
from pathlib import Path
import yaml

DEFAULT=Path('configuracion/elecciones_vigentes.yaml')
PREPARATION_CATALOG=Path('configuracion/catalogo_preparacion.yaml')
ELECTION_REGISTRY=Path('configuracion/registro_electoral.yaml')
DECLARATION_SCHEMA='ddd-election-official-source-declaration/1.0'

def _load_yaml(path:Path)->dict:
    if not path.is_file(): return {}
    data=yaml.safe_load(path.read_text(encoding='utf-8')) or {}
    return data if isinstance(data,dict) else {}

def load_catalog(path:Path)->dict:
    data=_load_yaml(path); rows=data.get('territories',[])
    if not isinstance(rows,list): raise ValueError('Catálogo de elecciones vigentes sin territories')
    return {'territories':rows}

def _catalog_preparation_row(root:Path,territory:str,edition:str|None):
    data=_load_yaml(root/PREPARATION_CATALOG); token=territory.strip()
    rows=[r for r in data.get('territories',[]) if token in {str(r.get('territory_id') or ''),str(r.get('name') or '')}]
    if len(rows)!=1:return None
    r=rows[0]; ed=str(edition or data.get('default_edition') or ''); state=(r.get('editions') or {}).get(ed)
    if not isinstance(state,dict):return None
    return str(r['territory_id']),str(r['name']),state,ed

def _registry_row(root:Path,territory_id:str,name:str,edition:str)->dict|None:
    data=_load_yaml(root/ELECTION_REGISTRY)
    if data.get('schema')!='ddd-election-registry/1.0': return None
    r=(data.get('territories') or {}).get(territory_id)
    if not isinstance(r,dict): return None
    for key in ('election_id','election_date'):
        if not r.get(key): raise SystemExit(f'Registro electoral incompleto para {territory_id}: falta {key}')
    declaration=str(r.get('declaration') or '')
    # El registro común identifica la elección, pero sólo una declaración oficial
    # materializada convierte esa identidad en una fuente adquirible por 03.
    if not declaration:
        return None
    if not (root/declaration).is_file(): raise SystemExit(f'Declaración registrada inexistente: {declaration}')
    return {'territory_id':territory_id,'name':name,'territorial_edition':edition,'election_id':str(r['election_id']),'election_date':str(r['election_date']),'declaration':declaration,'resolution_mode':'common_election_registry'}

def _declaration_candidates(root:Path,tid:str,state:dict)->list[Path]:
    out=[]; explicit=state.get('electoral_source_declaration')
    if explicit and (root/str(explicit)).is_file(): out.append(root/str(explicit))
    folder=root/'territorios'/tid/'config'/'elecciones'
    if folder.is_dir():
        for p in sorted(folder.glob('*.yaml')):
            if p not in out and _load_yaml(p).get('schema')==DECLARATION_SCHEMA: out.append(p)
    return out

def _from_declaration(root:Path,tid:str,name:str,edition:str,p:Path)->dict:
    d=_load_yaml(p)
    if str(d.get('territory_id') or '')!=tid: raise SystemExit(f'Declaración electoral de otro territorio: {p}')
    return {'territory_id':tid,'name':name,'territorial_edition':edition,'election_id':str(d['election_id']),'election_date':str(d['election_date']),'declaration':p.relative_to(root).as_posix(),'resolution_mode':'auto_discovered_declaration'}

def resolve(territory:str,path:Path=DEFAULT,root_dir:Path=Path('.'),edition:str|None=None)->dict:
    root=root_dir.resolve(); token=territory.strip(); override=path if path.is_absolute() else root/path
    rows=[r for r in load_catalog(override)['territories'] if token in {str(r.get('territory_id') or ''),str(r.get('name') or '')}]
    if len(rows)>1: raise SystemExit(f'Elección vigente ambigua para territorio={territory!r}')
    if len(rows)==1:
        r=dict(rows[0]); r['resolution_mode']='governed_override'; return r
    found=_catalog_preparation_row(root,token,edition)
    if found is None: raise SystemExit(f'Territorio o edición no declarados: territorio={territory!r}, edición={edition!r}')
    tid,name,state,ed=found
    registered=_registry_row(root,tid,name,ed)
    if registered is not None: return registered
    resolved=[_from_declaration(root,tid,name,ed,p) for p in _declaration_candidates(root,tid,state)]
    if resolved:
        resolved.sort(key=lambda r:date.fromisoformat(r['election_date']),reverse=True); return resolved[0]
    raise SystemExit(f'No existe elección resoluble para territorio={territory!r}')

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--territory',required=True); ap.add_argument('--edition'); ap.add_argument('--catalog',type=Path,default=DEFAULT); ap.add_argument('--root-dir',type=Path,default=Path('.')); a=ap.parse_args()
    print(json.dumps(resolve(a.territory,a.catalog,a.root_dir,a.edition),ensure_ascii=False))
if __name__=='__main__': main()
