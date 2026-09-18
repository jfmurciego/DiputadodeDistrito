#!/usr/bin/env python3
from __future__ import annotations
import argparse,hashlib,json,shutil
from pathlib import Path
import yaml

def sha256(path:Path)->str:
    h=hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda:f.read(1024*1024),b""): h.update(chunk)
    return h.hexdigest()

def validate_package(*,package:Path,params:Path,territory_id:str,edition:str,root:Path,materialize:bool=False)->dict:
    root=root.resolve()
    manifest=json.loads((package/"manifest.json").read_text(encoding="utf-8"))
    if manifest.get("schema")!="ddd-electoral-package/1.0": raise ValueError("schema electoral package inválido")
    if manifest.get("decision") not in {"REUSE","ACQUIRE"}: raise ValueError("paquete electoral no utilizable")
    if str(manifest.get("territory_id"))!=territory_id or str(manifest.get("edition"))!=str(edition):
        raise ValueError("territorio o edición del paquete electoral no coincide")
    selected=manifest.get("selected_source") or {}
    source=package/str(selected.get("path") or "")
    if not source.is_file(): raise ValueError("fuente electoral ausente del paquete")
    actual=sha256(source).lower(); declared=str(selected.get("sha256") or "").lower()
    if not declared or actual!=declared: raise ValueError("hash interno del paquete electoral no coincide")
    if source.stat().st_size!=int(selected.get("bytes") or -1): raise ValueError("tamaño interno del paquete electoral no coincide")

    cfg=yaml.safe_load(params.read_text(encoding="utf-8")) or {}
    meta=cfg.get("meta") or {}
    if str(meta.get("territory_id") or "")!=territory_id or str(meta.get("year") or "")!=str(edition):
        raise ValueError("contrato territorial no corresponde al paquete electoral")
    m07=(cfg.get("modulos") or {}).get("modulo_07_agregar_resultados_electorales") or {}
    contract_raw=m07.get("election_contract")
    if not contract_raw: raise ValueError("M07 no declara election_contract")
    contract_path=root/str(contract_raw)
    contract=json.loads(contract_path.read_text(encoding="utf-8"))
    matches=[s for s in (contract.get("sources") or []) if str(s.get("sha256") or "").lower()==actual]
    if len(matches)!=1: raise ValueError("hash de procedencia electoral distinto del hash contractual")
    target_raw=matches[0].get("path")
    if not target_raw: raise ValueError("fuente contractual sin path")
    target=root/str(target_raw)
    if materialize:
        target.parent.mkdir(parents=True,exist_ok=True)
        if source.resolve()!=target.resolve(): shutil.copy2(source,target)
        if sha256(target).lower()!=actual: raise ValueError("materialización electoral alteró el hash")
    return {
        "schema":"ddd-electoral-package-validation/1.0",
        "decision":"READY_PACKAGE",
        "territory_id":territory_id,
        "edition":str(edition),
        "package_sha256":actual,
        "contract_sha256":str(matches[0].get("sha256")).lower(),
        "provenance_hash_matches_contract":True,
        "contract_source_path":str(target_raw),
        "package_source_path":str(selected.get("path")),
        "materialized":bool(materialize),
    }

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--package",type=Path,required=True); ap.add_argument("--params",type=Path,required=True)
    ap.add_argument("--territory-id",required=True); ap.add_argument("--edition",required=True)
    ap.add_argument("--root-dir",type=Path,default=Path(".")); ap.add_argument("--materialize",action="store_true")
    ap.add_argument("--output",type=Path)
    a=ap.parse_args()
    try:
        payload=validate_package(package=a.package,params=a.params,territory_id=a.territory_id,edition=a.edition,root=a.root_dir,materialize=a.materialize)
    except Exception as exc:
        payload={"schema":"ddd-electoral-package-validation/1.0","decision":"BLOCK","reason":str(exc)}
        if a.output:
            a.output.parent.mkdir(parents=True,exist_ok=True)
            a.output.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
        print(json.dumps(payload,ensure_ascii=False))
        raise SystemExit(2)
    if a.output:
        a.output.parent.mkdir(parents=True,exist_ok=True)
        a.output.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(payload,ensure_ascii=False))
if __name__=="__main__": main()
