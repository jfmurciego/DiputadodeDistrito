#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PROYECTO: Diputado de Distrito
HERRAMIENTA: Registro de ejecución
VERSIÓN: 1.1.0
NOMBRE DE VERSIÓN: Manifiesto inmutable por ejecución
FECHA: 2026-09-11
ESTADO: candidato
QUÉ HACE: registra commit, configuración, módulos, entradas y salidas dentro de ejecuciones/<run_id>/MANIFIESTO_EJECUCION.json.
POR QUÉ CAMBIA: el manifiesto deja de ser global y no puede ser sobrescrito por la corrida siguiente.
VERSIÓN ANTERIOR: legacy/herramientas/registrar_ejecucion_v1.0.1.py
"""
from __future__ import annotations
import argparse,datetime as dt,hashlib,json,os,platform,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def sha256(p:Path):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
    return h.hexdigest()
def git(cmd):
    try:return subprocess.check_output(['git',*cmd],cwd=ROOT,text=True,stderr=subprocess.DEVNULL).strip()
    except Exception:return None
def meta(p:Path):return {'bytes':p.stat().st_size,'sha256':sha256(p)}
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--params',required=True);ap.add_argument('--phase',choices=['start','finish'],required=True);ap.add_argument('--run-id',required=True);a=ap.parse_args()
    run=ROOT/'ejecuciones'/a.run_id;run.mkdir(parents=True,exist_ok=True);p=run/'MANIFIESTO_EJECUCION.json';data={}
    if p.exists():
        try:data=json.loads(p.read_text(encoding='utf-8'))
        except Exception:data={}
    now=dt.datetime.now(dt.timezone.utc).isoformat();params=(ROOT/a.params).resolve() if not Path(a.params).is_absolute() else Path(a.params)
    data.update({'run_id':a.run_id,'git_commit':os.getenv('GITHUB_SHA') or git(['rev-parse','HEAD']),'python':sys.version,'platform':platform.platform(),'configuracion':a.params})
    if params.exists():data['configuracion_sha256']=sha256(params)
    if a.phase=='start':
        data['started_at_utc']=now;data['inputs']={str(x.relative_to(ROOT)):meta(x) for x in sorted((ROOT/'inputs').glob('*')) if x.is_file() and x.name!='README.md'};data['modulos']={str(x.relative_to(ROOT)):meta(x) for x in sorted((ROOT/'modulos').glob('*.py'))}
    else:
        data['finished_at_utc']=now;data['outputs']={str(x.relative_to(run)):meta(x) for x in sorted(run.rglob('*')) if x.is_file() and x.name!='MANIFIESTO_EJECUCION.json'}
    p.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
if __name__=='__main__':main()
