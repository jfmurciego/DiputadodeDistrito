#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PROYECTO: Diputado de Distrito
HERRAMIENTA: Registro de ejecución
VERSIÓN: 1.0.1
NOMBRE DE VERSIÓN: Trazabilidad reproducible
FECHA: 2026-09-11
ESTADO: candidato
QUÉ HACE: registra identidad del código, configuración, entorno, entradas y salidas en MANIFIESTO_EJECUCION.json.
VERSIÓN ANTERIOR: legacy/2026-09-11_registro_v1.0.0/registrar_ejecucion.py
"""
from __future__ import annotations
import argparse,datetime as dt,hashlib,json,os,platform,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
def sha256(p:Path):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
    return h.hexdigest()
def git(cmd):
    try:return subprocess.check_output(['git',*cmd],cwd=ROOT,text=True,stderr=subprocess.DEVNULL).strip()
    except Exception:return None
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--params',required=True);ap.add_argument('--phase',choices=['start','finish'],required=True);ap.add_argument('--run-id',required=True);a=ap.parse_args()
    out=ROOT/'output';out.mkdir(exist_ok=True);p=out/'MANIFIESTO_EJECUCION.json';data={}
    if p.exists():
        try:data=json.loads(p.read_text(encoding='utf-8'))
        except Exception:data={}
    now=dt.datetime.now(dt.timezone.utc).isoformat();data.update({'run_id':a.run_id,'git_commit':os.getenv('GITHUB_SHA') or git(['rev-parse','HEAD']),'python':sys.version,'platform':platform.platform(),'configuracion':a.params})
    params=(ROOT/a.params).resolve() if not Path(a.params).is_absolute() else Path(a.params)
    if params.exists():data['configuracion_sha256']=sha256(params)
    if a.phase=='start':
        data['started_at_utc']=now;inputs={}
        for fp in sorted((ROOT/'inputs').glob('*')):
            if fp.is_file() and fp.name!='README.md':inputs[str(fp.relative_to(ROOT))]={'bytes':fp.stat().st_size,'sha256':sha256(fp)}
        data['inputs']=inputs
    else:
        data['finished_at_utc']=now;outputs={}
        for fp in sorted(out.glob('*')):
            if fp.is_file() and fp.name!='MANIFIESTO_EJECUCION.json':outputs[str(fp.relative_to(ROOT))]={'bytes':fp.stat().st_size,'sha256':sha256(fp)}
        data['outputs']=outputs
    p.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
if __name__=='__main__':main()
