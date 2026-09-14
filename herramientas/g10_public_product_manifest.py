#!/usr/bin/env python3
"""Genera y valida el manifiesto público v1.1.0 desde productos canónicos.

El manifiesto es un contrato de publicación, no una mera lista para el visor:
comprueba cada entidad antes de que cualquier producto público la consuma.
"""
from __future__ import annotations
import argparse,hashlib,json
from pathlib import Path

CANDIDATES={"district_id":["district_id"],"population":["district_pop","population"],"target":["target","target_population"],"relative_deviation":["relative_deviation"],"municipalities":["municipality_names","municipalities"]}
GEOMETRY_TYPES={"Polygon","MultiPolygon"}

def choose(props,names):
    return next((name for name in names if name in props),None)

def validate_product(spec,data):
    """Devuelve los campos publicados o aborta antes de empaquetar un producto."""
    features=data.get("features",[])
    if data.get("type")!="FeatureCollection" or len(features)!=spec["expected_districts"]:
        raise ValueError("Contrato público inválido: "+spec["id"])
    if not features:
        raise ValueError("Producto público vacío: "+spec["id"])
    fields={key:choose(features[0].get("properties",{}),names) for key,names in CANDIDATES.items()}
    if not fields["district_id"]:
        raise ValueError("district_id ausente: "+spec["id"])
    ids=set()
    for position,feature in enumerate(features,1):
        props=feature.get("properties") or {}
        geometry=feature.get("geometry") or {}
        if geometry.get("type") not in GEOMETRY_TYPES or not geometry.get("coordinates"):
            raise ValueError(f"Geometría pública inválida: {spec['id']} entidad {position}")
        district_id=props.get(fields["district_id"])
        if district_id in (None,""):
            raise ValueError(f"district_id vacío: {spec['id']} entidad {position}")
        if str(district_id) in ids:
            raise ValueError(f"district_id duplicado: {spec['id']}={district_id}")
        ids.add(str(district_id))
        for logical,field in fields.items():
            if field and props.get(field) in (None,""):
                raise ValueError(f"Campo público {logical} ausente: {spec['id']} entidad {position}")
    return fields

def main():
    p=argparse.ArgumentParser();p.add_argument("--registry",required=True);p.add_argument("--output",required=True);a=p.parse_args()
    registry=json.loads(Path(a.registry).read_text(encoding="utf-8")); products=[]
    for spec in registry["products"]:
        source=Path(spec["source_path"]); data=json.loads(source.read_text(encoding="utf-8"))
        fields=validate_product(spec,data)
        products.append({**spec,"sha256":hashlib.sha256(source.read_bytes()).hexdigest(),"fields":fields})
    Path(a.output).write_text(json.dumps({"schema_version":"1.0.0","products":products},ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    return 0
if __name__=="__main__": raise SystemExit(main())
