#!/usr/bin/env python3
"""Visualización aislada de un candidato León, ligada al seccionado INE 2025.

No certifica ni publica producto territorial. No altera geometrías originales;
la unión disuelve secciones exclusivamente para representación cartográfica.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import tempfile
import zipfile
from pathlib import Path

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
    if (candidate.get("schema")!="ddd.congress-leon-analytical-candidate/1.0"
        or candidate.get("cpro")!="24" or candidate.get("k")!=4
        or candidate.get("generation_authorized") is not False
        or candidate.get("product_certification")!="NOT_PERFORMED"):
        raise ValueError("CANDIDATE_CONTRACT_INVALID")
    groups=candidate["districts"]
    assigned=[c for d in groups for c in d["cusecs"]]
    if len(groups)!=4 or len(assigned)!=len(set(assigned)):
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
    frame=frame[frame["CPRO"].astype(str).str.zfill(2)=="24"].copy()
    frame["CUSEC"]=frame["CUSEC"].astype(str)
    if len(frame)!=len(assigned) or set(frame["CUSEC"])!=set(assigned):
        raise ValueError("INE_LEON_CUSEC_COVERAGE_MISMATCH")
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
            "candidate_sha256":candidate["witness_sha256"]
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
    result=make_geojson(json.loads(a.candidate.read_text(encoding="utf-8")),a.root,a.output)
    print("LEON_GEOJSON_READY districts="+str(len(result["features"]))+" sha256="+file_sha(a.output))
if __name__=="__main__":main()
