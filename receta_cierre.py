#!/usr/bin/env python3
"""Version 1.0.3; 2026-10-10; C3 reproducción local; revisión pendiente; nuevo.
Uso: python receta_cierre.py DIRECTORIO_NUEVO [--proj-data DIRECTORIO].
ANTERIOR: legacy/receta_cierre_v1.0.2.py. CAMBIOS: rutas relativas y redacción de localizadores privados.
No red, generación ni macros.
"""
import argparse,gzip,hashlib,json,sys,platform
import pyproj,shapely,numpy,certifi
from importlib.metadata import version
from pathlib import Path
from herramientas.inventariar_cartografia_historica import incorporate,SECTIONING_2025_BASELINE_SHA256,read_json_verified
from herramientas.evaluar_alternativas_nacionales import evaluate,population_diagnostic
ANALYTICAL_INPUT_SHA256={
 'modelo.json':'c183f71e7a433eaaff77456d82a13f8afbc3f1fd2ec08e73ca3fce371d7d7ee4',
 'fuente_poblacion.json':'6a5f16d1bf354bebb1d05ad0f9afc350d8dc1c7ea251aac3ce6002e392b16a7c'}
def load_analytical_input(path, name):
 return read_json_verified(path,ANALYTICAL_INPUT_SHA256[name])

root=Path(__file__).resolve().parent
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('output',type=Path)
parser.add_argument('--proj-data',type=Path,help='explicit PROJ data for source-built pyproj; wheel builds use their own bundled data')
args=parser.parse_args()
pyproj.network.set_network_enabled(False)
if args.proj_data is not None:
 data=args.proj_data.resolve()
else:
 data=Path(pyproj.__file__).resolve().parent/'proj_dir/share/proj'
 if not data.is_dir():raise ValueError('SOURCE_BUILT_PYPROJ_REQUIRES_EXPLICIT_PROJ_DATA')
if not (data/'proj.db').is_file():raise ValueError('PROJ_DATABASE_MISSING')
pyproj.datadir.set_data_dir(str(data))
out=args.output.resolve();out.mkdir(exist_ok=False,parents=True)
software={'python':sys.version,'platform':platform.platform(),
          'packages':{name:version(name) for name in ('pyproj','shapely','numpy','certifi')},
          'proj_runtime':pyproj.proj_version_str,'geos_runtime':shapely.geos_version_string,
          'proj_database_sha256':hashlib.sha256((data/'proj.db').read_bytes()).hexdigest(),
          'proj_network_enabled':pyproj.network.is_network_enabled(),
          'proj_data_selection':'explicit_argument' if args.proj_data is not None else 'wheel_bundled'}
(out/'software.json').write_text(json.dumps(software,sort_keys=True,indent=2)+'\n')
print(json.dumps(software,sort_keys=True))
folder=root/'docs/ESTUDIOS/cartografia_nacional_20261008'
inventory=json.loads((folder/'inventario.json').read_text()); found=[]
for index,record in enumerate(inventory['files']):
 raw=gzip.decompress((folder/record['archived_path']).read_bytes())
 if hashlib.sha256(raw).hexdigest()!=record['file_sha256']:raise ValueError('INPUT_HASH_MISMATCH')
 path=out/'restored'/str(index)/record['name'];path.parent.mkdir(parents=True);path.write_bytes(raw);found.append(path.relative_to(out).as_posix())
historical_search=dict(inventory['search'])
historical_search['root']='PRIVATE_ROOT_REDACTED'
historical_search['found']=[{'source_id':item['source_id'] if isinstance(item,dict) else f'historical-source-{i+1:02d}','name':item['name'] if isinstance(item,dict) else Path(item).name,'original_location':'PRIVATE_PATH_REDACTED'} for i,item in enumerate(historical_search['found'])]
search={'found':found,'origin':'hash-verified archived inputs; portable restored-relative routes, not a new discovery','historical_search':historical_search}
report=out/'busqueda.json';report.write_text(json.dumps(search,indent=2))
section=out/'seccionado_2025.zip'
with section.open('wb') as sink:
 for part in sorted((root/'inputs/partes').glob('seccionado_2025.zip.part*')):
  with part.open('rb') as source:
   while chunk:=source.read(1024*1024):sink.write(chunk)
print(incorporate(report,out/'inventory',section,SECTIONING_2025_BASELINE_SHA256))
model=load_analytical_input(root/'docs/ESTUDIOS/modelo_nacional_2025_120000/modelo.json','modelo.json')
counts=json.loads((out/'inventory/recuentos_historicos.json').read_text())
(out/'evaluacion.json').write_text(json.dumps(evaluate(model,counts),sort_keys=True,indent=2))
reference=load_analytical_input(root/'docs/ESTUDIOS/modelo_nacional_2025_120000/fuente_poblacion.json','fuente_poblacion.json')
(out/'poblacion.json').write_text(json.dumps(population_diagnostic(json.loads((out/'inventory/atributos_historicos.json').read_text()),reference),sort_keys=True,indent=2))
print('PASS C3: inputs verified, search reconstructed, inventory and analysis reproduced in clean directory')
