#!/usr/bin/env python3
"""Version 1.0.0; 2026-10-09; C3 reproducción local; revisión pendiente; nuevo.
Uso: python receta_cierre.py DIRECTORIO_NUEVO. No red, generación ni macros.
"""
import gzip,hashlib,json,sys
from pathlib import Path
from herramientas.inventariar_cartografia_historica import incorporate,SECTIONING_2025_BASELINE_SHA256
from herramientas.evaluar_alternativas_nacionales import evaluate,population_diagnostic
root=Path(__file__).resolve().parent
out=Path(sys.argv[1]).resolve();out.mkdir(exist_ok=False,parents=True)
folder=root/'docs/ESTUDIOS/cartografia_nacional_20261008'
inventory=json.loads((folder/'inventario.json').read_text()); found=[]
for index,record in enumerate(inventory['files']):
 raw=gzip.decompress((folder/record['archived_path']).read_bytes())
 if hashlib.sha256(raw).hexdigest()!=record['file_sha256']:raise ValueError('INPUT_HASH_MISMATCH')
 path=out/'restored'/str(index)/record['name'];path.parent.mkdir(parents=True);path.write_bytes(raw);found.append(str(path))
search={'found':found,'origin':'inventario.json and hash-verified archived bytes; reconstructed routes, not a new discovery','historical_search':inventory['search']}
report=out/'busqueda.json';report.write_text(json.dumps(search,indent=2))
section=out/'seccionado_2025.zip'
with section.open('wb') as sink:
 for part in sorted((root/'inputs/partes').glob('seccionado_2025.zip.part*')):
  with part.open('rb') as source:
   while chunk:=source.read(1024*1024):sink.write(chunk)
print(incorporate(report,out/'inventory',section,SECTIONING_2025_BASELINE_SHA256))
model=json.loads((root/'docs/ESTUDIOS/modelo_nacional_2025_120000/modelo.json').read_text())
counts=json.loads((out/'inventory/recuentos_historicos.json').read_text())
(out/'evaluacion.json').write_text(json.dumps(evaluate(model,counts),sort_keys=True,indent=2))
reference=json.loads((root/'docs/ESTUDIOS/modelo_nacional_2025_120000/fuente_poblacion.json').read_text())
(out/'poblacion.json').write_text(json.dumps(population_diagnostic(json.loads((out/'inventory/atributos_historicos.json').read_text()),reference),sort_keys=True,indent=2))
print('PASS C3: inputs verified, search reconstructed, inventory and analysis reproduced in clean directory')
