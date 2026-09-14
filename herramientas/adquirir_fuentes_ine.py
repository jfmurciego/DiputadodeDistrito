#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PROYECTO: Diputado de Distrito
HERRAMIENTA: Adquisición de fuentes oficiales INE
VERSIÓN: 1.0.1
NOMBRE DE VERSIÓN: Materialización oficial Aragón 2025 — Gobernanza R015
FECHA: 2026-09-11
QUÉ HACE: descarga población 65034 y cartografía Secciones_2025 directamente del INE; materializa solo secciones de Aragón y registra procedencia y SHA-256.
POR QUÉ EXISTE: evita almacenar o trocear grandes fuentes públicas en GitHub y hace reproducible su adquisición.
INPUTS REMOTOS: INE JAXI tabla 65034; INE OGC API Features Secciones_2025.
OUTPUTS: inputs/65034.csv, inputs/seccionado_2025_aragon.geojson, inputs/FUENTES_ADQUIRIDAS.json.
ESTADO: vigente — R015 de gobernanza; lógica funcional heredada sin cambios.
CAMBIOS: normaliza cabecera y predecesor legacy; no modifica algoritmo ni contrato funcional.
MOTIVO: cerrar la deuda de auditoría y hacer verificable la disciplina de versiones.
ANTERIOR: legacy/herramientas/adquirir_fuentes_ine_v1.0.0.py
"""
from __future__ import annotations
import argparse,hashlib,json,time
from datetime import datetime,timezone
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request,urlopen

ROOT=Path(__file__).resolve().parents[1]
POP_URL='https://www.ine.es/jaxiT3/files/t/csv_bdsc/65034.csv'
OGC_BASE='https://www.ine.es/geoserver/ogc/features/v1/collections/WMS_INE_SECCIONES_G01%3ASecciones_2025/items'
PROVINCIAS=('22','44','50')
EXPECTED_SECTIONS=1463

def get_bytes(url,retries=4,timeout=120):
    last=None
    for n in range(retries):
        try:
            req=Request(url,headers={'User-Agent':'DiputadoDeDistrito/1.0 (+GitHub Actions; fuente estadistica INE)'})
            with urlopen(req,timeout=timeout) as r:return r.read()
        except Exception as exc:
            last=exc
            if n+1<retries:time.sleep(2**n)
    raise RuntimeError(f'No se pudo descargar {url}: {last}')

def sha256(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
    return h.hexdigest()

def descargar_geojson(out):
    features=[];seen=set();urls=[]
    for prov in PROVINCIAS:
        params={'f':'application/geo+json','filter':f"CPRO='{prov}' AND TIPO='SECCION'",'filter-lang':'cql2-text','limit':'10000'}
        url=OGC_BASE+'?'+urlencode(params);urls.append(url)
        data=json.loads(get_bytes(url).decode('utf-8-sig'))
        fs=data.get('features',[])
        if not fs:raise RuntimeError(f'INE devolvió 0 secciones para CPRO={prov}; no se continúa')
        for feat in fs:
            props=feat.get('properties') or {};cusec=str(props.get('CUSEC','')).strip()
            if not cusec or cusec in seen:continue
            if str(props.get('CPRO','')).zfill(2)!=prov:raise RuntimeError(f'CPRO inesperado para {cusec}')
            seen.add(cusec);features.append(feat)
    if len(features)!=EXPECTED_SECTIONS:raise RuntimeError(f'Cardinalidad territorial inesperada: {len(features)}; esperadas {EXPECTED_SECTIONS}')
    features.sort(key=lambda f:str((f.get('properties') or {}).get('CUSEC','')))
    out.write_text(json.dumps({'type':'FeatureCollection','features':features},ensure_ascii=False,separators=(',',':')),encoding='utf-8')
    return urls

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--out-dir',default='inputs');a=ap.parse_args();d=(ROOT/a.out_dir).resolve();d.mkdir(parents=True,exist_ok=True)
    pop=d/'65034.csv';geo=d/'seccionado_2025_aragon.geojson';prov=d/'FUENTES_ADQUIRIDAS.json'
    pop.write_bytes(get_bytes(POP_URL));urls=descargar_geojson(geo)
    record={'schema_version':'1.0.0','acquired_at_utc':datetime.now(timezone.utc).isoformat(),'provider':'Instituto Nacional de Estadística (INE)','citation':'Seccionado cedido por el Instituto Nacional de Estadística','sources':{'population_65034':{'url':POP_URL,'path':str(pop.relative_to(ROOT)),'sha256':sha256(pop),'bytes':pop.stat().st_size},'secciones_2025_aragon':{'collection':'WMS_INE_SECCIONES_G01:Secciones_2025','urls':urls,'provinces':list(PROVINCIAS),'expected_sections':EXPECTED_SECTIONS,'path':str(geo.relative_to(ROOT)),'sha256':sha256(geo),'bytes':geo.stat().st_size}}}
    prov.write_text(json.dumps(record,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(record,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
