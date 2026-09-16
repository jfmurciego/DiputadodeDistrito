#!/usr/bin/env python3
"""Materialización de checkpoints de orquestación v1.1.0 con verificación de integridad."""
from __future__ import annotations
import argparse,hashlib,json,os,shutil,tempfile
from pathlib import Path
CANONICAL={"CANONICAL_VERIFIED_LEGACY","CERTIFIED"}
RUNTIME={
 "TERRITORY_PREPARATION":(), "TERRITORY_ADJACENCY":("TERRITORY_PREPARATION",),
 "TERRITORY_GRAPH":("TERRITORY_PREPARATION","TERRITORY_ADJACENCY"),
 "DISTRICT_FORMATION":("TERRITORY_GRAPH",),
 "DISTRICT_BALANCING":("TERRITORY_GRAPH","DISTRICT_FORMATION"),
 "TERRITORIAL_CERTIFICATION":("TERRITORY_GRAPH","DISTRICT_BALANCING"),
 "ELECTORAL_ENRICHMENT":("TERRITORIAL_CERTIFICATION",),
 "PUBLIC_PRODUCT_PUBLICATION":("TERRITORIAL_CERTIFICATION","ELECTORAL_ENRICHMENT"),
}
def sha256(path:Path)->str:
 h=hashlib.sha256()
 with path.open("rb") as f:
  for block in iter(lambda:f.read(1024*1024),b""):h.update(block)
 return h.hexdigest()
def plan(index:dict,territory_id:str,from_stage:str)->dict:
 if from_stage not in RUNTIME: raise ValueError(f"Etapa desconocida: {from_stage}")
 territory=next((x for x in index.get("territories",[]) if x.get("territory")==territory_id),None)
 if not territory: raise ValueError(f"Territorio no encontrado: {territory_id}")
 if territory.get("release_status")=="EXPERIMENTAL_BLOCKED": raise ValueError(f"Territorio bloqueado experimentalmente: {territory_id}")
 available={x.get("stage_id"):x for x in territory.get("checkpoints",[]) if x.get("status") in CANONICAL}
 required=RUNTIME[from_stage]; missing=[x for x in required if x not in available]
 if missing: raise ValueError(f"Faltan checkpoints runtime: {missing}")
 return {"schema_version":"1.0","territory":territory_id,"from_stage":from_stage,"source_run":territory.get("source_run"),"checkpoints":[{"stage_id":x,"products_manifest":available[x]["products_manifest"],"target":"CACHE" if x.startswith("TERRITORY_") else "RUN"} for x in required]}
def safe(root:Path,raw:str)->Path:
 path=(root/raw).resolve()
 try:path.relative_to(root)
 except ValueError as exc: raise ValueError(f"Ruta fuera del repositorio: {raw}") from exc
 return path
def materialize(job:dict,*,root:Path,cache:Path,run:Path)->dict:
 report={"schema_version":"1.0","status":"REUSED_MATERIALIZED","job":job,"artifacts":[]}
 for checkpoint in job["checkpoints"]:
  manifest=safe(root,checkpoint["products_manifest"])
  products=json.loads(manifest.read_text(encoding="utf-8")).get("products",[])
  if not products: raise ValueError(f"Manifiesto vacío: {manifest}")
  target_dir=cache if checkpoint["target"]=="CACHE" else run
  target_dir.mkdir(parents=True,exist_ok=True)
  for product in products:
   source=safe(root,str(product["path"]))
   if not source.is_file(): raise FileNotFoundError(source)
   expected=str(product["sha256"]);size=int(product["bytes"])
   if source.stat().st_size!=size or sha256(source)!=expected: raise ValueError(f"Integridad fuente inválida: {source}")
   destination=target_dir/source.name
   if source.resolve()!=destination.resolve():
    fd,tmp=tempfile.mkstemp(prefix=destination.name+".",dir=target_dir);os.close(fd)
    try:shutil.copyfile(source,tmp);os.replace(tmp,destination)
    finally:
     if os.path.exists(tmp):os.unlink(tmp)
   if destination.stat().st_size!=size or sha256(destination)!=expected: raise ValueError(f"Integridad destino inválida: {destination}")
   report["artifacts"].append({"stage_id":checkpoint["stage_id"],"source":str(source.relative_to(root)),"destination":str(destination),"sha256":expected})
 return report
def main()->int:
 ap=argparse.ArgumentParser(description="Materializa checkpoints de orquestación con verificación de integridad");ap.add_argument("--index",required=True);ap.add_argument("--territory",required=True);ap.add_argument("--from-stage",required=True);ap.add_argument("--cache-dir",required=True);ap.add_argument("--run-dir",required=True);ap.add_argument("--report",required=True);ap.add_argument("--root",default=".");a=ap.parse_args()
 root=Path(a.root).resolve();job=plan(json.loads(safe(root,a.index).read_text(encoding="utf-8")),a.territory,a.from_stage)
 report=materialize(job,root=root,cache=Path(a.cache_dir),run=Path(a.run_dir));out=Path(a.report);out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
 print(f"ORQUESTACION MATERIALIZACION PASS: {len(report['artifacts'])} productos")
 return 0
if __name__=="__main__":raise SystemExit(main())
