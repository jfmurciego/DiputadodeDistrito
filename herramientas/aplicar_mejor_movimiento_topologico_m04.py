#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PROYECTO: Diputado de Distrito
HERRAMIENTA: aplicar_mejor_movimiento_topologico_m04.py
VERSIÓN: 1.0.0
NOMBRE: Aplicador experimental del mejor movimiento topológico M04
FECHA: 2026-09-11
ESTADO: experimental; NO forma parte del motor activo.
FUNCIÓN: leer el JSON producido por `auditar_movimientos_topologicos_m04.py`, tomar el primer candidato
`guarded_population=true`, aplicar exactamente ese único movimiento de `ddd_unit_id` al GeoJSON M04 crudo
y escribir una nueva solución para prueba A/B posterior con M05.
REGLAS: no busca ni inventa movimientos; consume una decisión auditada. Solo acepta un candidato que mantenga
hard=0, no aumente el número de outliers ni el máximo desvío según el auditor. Cambia exclusivamente
`district_id` de las features pertenecientes a la unidad seleccionada y conserva todas las demás propiedades.
MOTIVO: EXT-12 Run 34647432729 encontró 123 movimientos reductores de fragilidad, 70 bajo guard poblacional.
El mejor reduce la firma de [53,122,...] a [52,120,...] sin empeorar outside=5 ni maxdev=13,30 %. Debe
probarse causalmente un solo movimiento antes de diseñar un pulido iterativo o modificar M04.
ANTERIOR: ninguno — herramienta experimental nueva.
"""
from __future__ import annotations
import argparse, json, zipfile
from pathlib import Path

def read_raw(path: Path):
    if path.suffix.lower()=='.zip':
        with zipfile.ZipFile(path) as z:
            name=next(n for n in z.namelist() if n.lower().endswith(('.geojson','.json')) and not n.endswith('/'))
            return json.loads(z.read(name).decode('utf-8')), name
    return json.loads(path.read_text(encoding='utf-8')), path.name

def normalise(v):
    if isinstance(v,list):
        if len(v)!=1: raise SystemExit(f'ddd_unit_id multivaluado: {v!r}')
        v=v[0]
    return str(v)

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--in-geojson',required=True); ap.add_argument('--audit-json',required=True); ap.add_argument('--out-geojson',required=True); ap.add_argument('--out-report',required=True); ap.add_argument('--district-field',default='district_id'); a=ap.parse_args()
    audit=json.loads(Path(a.audit_json).read_text(encoding='utf-8'))
    candidates=[x for x in audit.get('best',[]) if x.get('guarded_population')]
    if not candidates: raise SystemExit('No hay candidato guarded_population en auditoría')
    move=candidates[0]; unit=str(move['unit']); src=int(move['from']); dst=int(move['to'])
    data,inner=read_raw(Path(a.in_geojson)); changed=0; before=set()
    for f in data.get('features',[]):
        p=f.get('properties') or {}; u=p.get('ddd_unit_id')
        if u is None: continue
        if normalise(u)!=unit: continue
        before.add(int(p[a.district_field])); p[a.district_field]=dst; changed+=1
    if not changed: raise SystemExit(f'Unidad {unit} no encontrada')
    if before!={src}: raise SystemExit(f'Unidad {unit}: distrito origen inesperado {sorted(before)}, esperado {src}')
    out=Path(a.out_geojson); out.parent.mkdir(parents=True,exist_ok=True)
    raw=json.dumps(data,ensure_ascii=False,separators=(',',':')).encode('utf-8')
    if out.suffix.lower()=='.zip':
        with zipfile.ZipFile(out,'w',compression=zipfile.ZIP_DEFLATED) as z:z.writestr(inner if inner.lower().endswith(('.geojson','.json')) else 'data.geojson',raw)
    else: out.write_bytes(raw)
    rep={'version':'1.0.0','unit':unit,'from':src,'to':dst,'changed_features':changed,'population':move.get('population'),'municipalities':move.get('municipalities'),'population_objective_after':move.get('population_objective'),'fragility_signature_after':move.get('fragility_signature'),'source_audit':str(a.audit_json)}
    Path(a.out_report).parent.mkdir(parents=True,exist_ok=True);Path(a.out_report).write_text(json.dumps(rep,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(rep,ensure_ascii=False))
if __name__=='__main__':main()
