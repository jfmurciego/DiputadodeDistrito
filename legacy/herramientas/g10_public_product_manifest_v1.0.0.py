#!/usr/bin/env python3
"""Genera manifiesto público v1.0.0 desde productos territoriales canónicos."""
from __future__ import annotations
import argparse,hashlib,json
from pathlib import Path

CANDIDATES={"district_id":["district_id"],"population":["district_pop","population"],"target":["target","target_population"],"relative_deviation":["relative_deviation"],"municipalities":["municipality_names","municipalities"]}

def choose(props,names):
    return next((name for name in names if name in props),None)

def main():
    p=argparse.ArgumentParser();p.add_argument("--registry",required=True);p.add_argument("--output",required=True);a=p.parse_args()
    registry=json.loads(Path(a.registry).read_text(encoding="utf-8")); products=[]
    for spec in registry["products"]:
        source=Path(spec["source_path"]); data=json.loads(source.read_text(encoding="utf-8"))
        if data.get("type")!="FeatureCollection" or len(data.get("features",[]))!=spec["expected_districts"]: raise ValueError("Contrato público inválido: "+spec["id"])
        props=data["features"][0].get("properties",{}); fields={key:choose(props,names) for key,names in CANDIDATES.items()}
        if not fields["district_id"]: raise ValueError("district_id ausente: "+spec["id"])
        products.append({**spec,"sha256":hashlib.sha256(source.read_bytes()).hexdigest(),"fields":fields})
    Path(a.output).write_text(json.dumps({"schema_version":"1.0.0","products":products},ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    return 0
if __name__=="__main__": raise SystemExit(main())
