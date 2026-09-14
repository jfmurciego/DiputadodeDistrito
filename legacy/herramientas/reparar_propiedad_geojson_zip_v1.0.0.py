#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PROYECTO: Diputado de Distrito
HERRAMIENTA: reparar_propiedad_geojson_zip.py
VERSIÓN: 1.0.0
NOMBRE: Reparación de propiedad GeoJSON sin OGR
FECHA: 2026-09-11
FUNCIÓN: abrir un GeoJSON comprimido, recalcular una propiedad feature a feature como string escalar y volver a empaquetar sin pasar por GeoPandas/OGR.
MOTIVO: determinados esquemas OGR conservan un campo como StringList aunque sus valores se sustituyan; M05 necesita ddd_unit_id como string escalar.
ANTERIOR: ninguno — herramienta nueva.
"""
from __future__ import annotations
import argparse, json, pathlib, zipfile


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--zip',required=True)
    ap.add_argument('--property',required=True)
    ap.add_argument('--province-field',default='CPRO')
    ap.add_argument('--unit-field',default='M04_MUN')
    ap.add_argument('--suffix',default='G')
    args=ap.parse_args()
    zp=pathlib.Path(args.zip)
    with zipfile.ZipFile(zp,'r') as z:
        name=next(n for n in z.namelist() if n.lower().endswith(('.geojson','.json')) and not n.endswith('/'))
        data=json.loads(z.read(name).decode('utf-8'))
    changed=0
    for f in data.get('features',[]):
        p=f.setdefault('properties',{})
        prov=str(p.get(args.province_field,'')).zfill(2)
        unit=str(p.get(args.unit_field,''))
        p[args.property]=f'{prov}:{unit}:{args.suffix}'
        if 'ddd_closed_urban' in p:
            p['ddd_closed_urban']=False
        changed+=1
    tmp=zp.with_suffix('').with_suffix('.geojson')
    tmp.write_text(json.dumps(data,ensure_ascii=False,separators=(',',':')),encoding='utf-8')
    zp.unlink()
    with zipfile.ZipFile(zp,'w',compression=zipfile.ZIP_DEFLATED) as z:
        z.write(tmp,arcname=tmp.name)
    tmp.unlink()
    print(f'[GeoJSON repair] property={args.property} features={changed} zip={zp}')

if __name__=='__main__':
    main()
