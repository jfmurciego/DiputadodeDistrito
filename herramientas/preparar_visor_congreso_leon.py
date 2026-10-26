#!/usr/bin/env python3
"""Versión 1.2.0 — Rechaza JSON ambiguo de entradas analíticas.

No certifica ni publica producto territorial. No altera geometrías originales;
la unión disuelve secciones exclusivamente para representación cartográfica.
Predecesor: legacy/nac_piloto_20261026/herramientas/preparar_visor_congreso_leon_v1.1.0.py.
"""
from __future__ import annotations
import argparse
import gzip
import hashlib
import json
import tempfile
import zipfile
from pathlib import Path

from ddd_core.congreso_constructive_witness import evaluate_unit
from ddd_core.congreso_pilot_adapter import audit_candidate

def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("JSON_DUPLICATE_KEY:" + key)
        result[key] = value
    return result

def _reject_constant(value):
    raise ValueError("JSON_NONFINITE_VALUE:" + value)

def strict_json_loads(text):
    return json.loads(text, object_pairs_hook=_unique_object, parse_constant=_reject_constant)

def file_sha(path):
    h=hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda:stream.read(1024*1024),b""):
            h.update(block)
    return h.hexdigest()

def make_geojson(candidate, root, output):
    import geopandas as gpd
    import shapely
    from shapely.geometry import mapping
    from herramientas.materializar_fuentes_nacionales_ine import EXPECTED_SECTIONING_SHA
    if (candidate.get("schema")!="ddd.congress-provincial-analytical-candidate/1.0"
        or candidate.get("generation_authorized") is not False
        or candidate.get("product_certification")!="NOT_PERFORMED"):
        raise ValueError("CANDIDATE_CONTRACT_INVALID")
    groups=candidate["districts"]
    cpro=candidate["cpro"]
    preflight=root/"docs/ESTUDIOS/CAMPANA_NACIONAL_20261013"/f"PREFLIGHT_CPRO{cpro}"
    product=root/"docs/ESTUDIOS/N08_TOPOLOGIA_NACIONAL_20251012/producto"
    unit_path=product/"unidades"/f"{cpro}.json.gz"
    contract_path=root/"territorios/congreso/contrato_congreso_2026.json"
    bound=evaluate_unit(preflight_path=preflight/"PREFLIGHT.json",
        checkpoint_path=preflight/"CHECKPOINT.json",unit_path=unit_path,
        product_manifest_path=product/"manifest.json",contract_path=contract_path)
    if bound["errors"]:
        raise ValueError("PREFLIGHT_BLOCKED:"+repr(bound["errors"]))
    with gzip.open(unit_path,"rt",encoding="utf-8") as stream: unit=strict_json_loads(stream.read())
    contract=strict_json_loads(contract_path.read_text(encoding="utf-8"))
    audit=audit_candidate(candidate,unit,contract,expected_binding=bound["input_sha256"])
    if any(audit["checks"][key]!="DEMOSTRADO" for key in
        ("CUSEC_coverage_and_atomicity","population_conservation","province_and_K","population_bounds","section_graph_contiguity")):
        raise ValueError("CANDIDATE_ANALYTICAL_CHECK_FAILED")
    assigned=[c for d in groups for c in d["cusecs"]]
    if len(groups)!=candidate["k"] or len(assigned)!=len(set(assigned)):
        raise ValueError("CANDIDATE_DUPLICATE_OR_K_INVALID")
    parts=root/"inputs/partes"
    with tempfile.TemporaryDirectory(prefix="ddd-leon-visor-") as tmp:
        archive_path=Path(tmp)/"seccionado_2025.zip"
        with archive_path.open("wb") as out:
            for i in range(3):
                with (parts/f"seccionado_2025.zip.part{i:02d}").open("rb") as src:
                    for chunk in iter(lambda:src.read(1024*1024),b""):
                        out.write(chunk)
        if file_sha(archive_path)!=EXPECTED_SECTIONING_SHA:
            raise ValueError("INE_SECTIONING_SHA_MISMATCH")
        with zipfile.ZipFile(archive_path) as archive:
            names=[n for n in archive.namelist() if n.lower().endswith(".shp")]
            if len(names)!=1: raise ValueError("INE_LAYER_COUNT_INVALID")
            stem=names[0][:-4]
            for n in archive.namelist():
                if n.rsplit(".",1)[0]==stem:
                    dest=Path(tmp)/("sections."+n.rsplit(".",1)[-1])
                    dest.write_bytes(archive.read(n))
        frame=gpd.read_file(Path(tmp)/"sections.shp")
    if frame.crs is None or frame.crs.to_epsg()!=25830:
        raise ValueError("INE_CRS_INVALID")
    frame=frame[frame["CPRO"].astype(str).str.zfill(2)==cpro].copy()
    frame["CUSEC"]=frame["CUSEC"].astype(str)
    if len(frame)!=len(assigned) or set(frame["CUSEC"])!=set(assigned):
        raise ValueError("INE_CANDIDATE_CUSEC_COVERAGE_MISMATCH")
    if frame["CUSEC"].duplicated().any() or frame.geometry.isna().any():
        raise ValueError("INE_GEOMETRY_DUPLICATE_OR_MISSING")
    district_by_cusec={c:d["id"] for d in groups for c in d["cusecs"]}
    frame["district_id"]=frame["CUSEC"].map(district_by_cusec)
    projected=frame.to_crs(epsg=4326)
    features=[]
    for d in groups:
        section_geometries=projected.loc[projected["district_id"]==d["id"],"geometry"]
        if len(section_geometries)!=len(d["cusecs"]):
            raise ValueError("DISTRICT_SECTION_COVERAGE_MISMATCH")
        geom=shapely.union_all(section_geometries.to_numpy())
        if geom.is_empty or not geom.is_valid:
            raise ValueError("DISTRICT_GEOMETRY_INVALID:"+d["id"])
        features.append({"type":"Feature","properties":{
            "district_id":d["id"],"population":d["population"],
            "cusec_count":len(d["cusecs"]),
            "pilot_only":True,"certification_status":"NOT_CERTIFIED",
            "candidate_sha256":hashlib.sha256(json.dumps(candidate,ensure_ascii=False,sort_keys=True,separators=(",",":")).encode()).hexdigest(),
            "witness_sha256":candidate["witness_sha256"],
            "cpro":cpro,"generation_authorized":False
        },"geometry":mapping(geom)})
    result={"type":"FeatureCollection","features":features}
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(result,ensure_ascii=False,separators=(",",":"))+"\n",encoding="utf-8")
    return result

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--candidate",type=Path,required=True)
    p.add_argument("--root",type=Path,default=Path(__file__).resolve().parents[1])
    p.add_argument("--output",type=Path,required=True)
    a=p.parse_args()
    result=make_geojson(strict_json_loads(a.candidate.read_text(encoding="utf-8")),a.root,a.output)
    print("ANALYTICAL_GEOJSON_READY cpro="+str(result["features"][0]["properties"]["cpro"])+" districts="+str(len(result["features"]))+" sha256="+file_sha(a.output))
if __name__=="__main__":main()
