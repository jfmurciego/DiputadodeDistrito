#!/usr/bin/env python3
"""Genera el fichero JS de DOI por mapa a partir de un catálogo CSV verificado.
No inventa DOI: las entradas con DOI inválidos se rechazan.
Uso: python generar_catalogo.py plantilla_doi_por_mapa.csv
"""
import csv
import json
import re
import sys
from pathlib import Path

fields = ['id','nombre','territorio','nivel','version','fecha','sha256','doi']
doi_pat = re.compile(r'^10\.\d{4,9}/\S+$')
sha_pat = re.compile(r'^[0-9a-fA-F]{64}$')

def main(path: Path):
    out=[]
    ids=set()
    with path.open(encoding='utf-8-sig', newline='') as f:
        reader=csv.DictReader(f)
        if not reader.fieldnames or any(x not in reader.fieldnames for x in fields):
            raise SystemExit('Faltan columnas: '+', '.join(x for x in fields if x not in (reader.fieldnames or [])))
        for n,row in enumerate(reader,2):
            ident=row['id'].strip()
            if not ident or ident in ids: raise SystemExit(f'ID ausente o duplicado en fila {n}: {ident!r}')
            ids.add(ident)
            doi=row['doi'].strip()
            if not doi_pat.fullmatch(doi):raise SystemExit(f'DOI ausente o inválido en fila {n}. No se publicará un DOI no validado.')
            sha=row['sha256'].strip()
            if sha and not sha_pat.fullmatch(sha):raise SystemExit(f'SHA-256 inválido en fila {n}')
            out.append({k:(v or '').strip() for k,v in row.items() if k in fields})
    target=path.parent/'catalogo-mapas.js'
    target.write_text('/* DOI por mapa; catálogo importado tras revisión documental. */\nwindow.DDD_MAPS = '+json.dumps(out,ensure_ascii=False,indent=2)+';\n',encoding='utf8')
    print(f'{len(out)} registros exportados a {target}.')

if __name__=='__main__':
    if len(sys.argv)!=2:raise SystemExit('Uso: python generar_catalogo.py ruta/catalogo.csv')
    main(Path(sys.argv[1]))
