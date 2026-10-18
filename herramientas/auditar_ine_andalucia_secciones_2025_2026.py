#!/usr/bin/env python3
"""Evidence-only geometry comparison for Andalucia INE sections 2025/2026.

Persists official WFS responses BEFORE parsing. Never allocates votes, alters geometry,
approves crosswalks, modifies contracts, or changes any F10 gate.
"""
from __future__ import annotations

import argparse
import concurrent.futures
import hashlib
import json
import os
from pathlib import Path
import urllib.parse
import urllib.request

REPO = Path(__file__).resolve().parents[1]
EVIDENCE = REPO / "docs/AUDITORIAS/CIERRE_FUENTES_20261017"
INE = EVIDENCE / "IDENTIDADES_INE_2025_2026_F10.json"
BASE = "https://www.ine.es/geoserver/WMS_INE_SECCIONES_G01/wfs"
LAYERS = {
    2025: "WMS_INE_SECCIONES_G01:Secciones_2025",
    2026: "WMS_INE_SECCIONES_G01:SU.VectorStatisticalUnit",
}
SOURCE_CRS = "EPSG:25830"
WORK_CRS = "EPSG:3035"

def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def source_url(municipality: str, year: int) -> str:
    params = {
        "service": "WFS", "version": "2.0.0", "request": "GetFeature",
        "typeNames": LAYERS[year], "outputFormat": "application/json",
        "count": 2000, "CQL_FILTER": f"CUMUN='{municipality}' AND TIPO='SECCIONADO'",
    }
    return BASE + "?" + urllib.parse.urlencode(params)

def required_groups() -> dict:
    doc = json.loads(INE.read_text(encoding="utf-8"))
    provinces = doc["andaluces"]["provinces"]
    assert len(provinces) == 8
    groups: dict[str, dict[str, set[str]]] = {}
    for province in provinces:
        for kind, field in [("added","added_2026"),("removed","removed_since_2025")]:
            for c in province[field]:
                if len(c) != 10 or not c.isdigit() or c[:2] != province["CPRO"]:
                    raise ValueError("INVALID_EXPECTED_CUSEC:"+str(c))
                groups.setdefault(c[:5],{"added":set(),"removed":set()})[kind].add(c)
    if sum(len(g["added"]) for g in groups.values()) != 25 or sum(len(g["removed"]) for g in groups.values()) != 9:
        raise ValueError("EXPECTED_34_IDENTITY_CHANGES")
    return groups

def acquire(municipality: str, year: int, out: Path) -> dict:
    raw_file = out / "raw" / municipality / f"{year}.geojson"
    url = source_url(municipality,year)
    if raw_file.exists():
        raw = raw_file.read_bytes()
    else:
        req = urllib.request.Request(url, headers={"User-Agent":"DDD-F10-INE-Temporal-Evidence/1.0"})
        # No automatic retry; on partial availability preserve successful files for handoff.
        with urllib.request.urlopen(req, timeout=55) as response:
            if response.status != 200:
                raise ValueError(f"HTTP_{response.status}")
            raw = response.read(30_000_001)
        if len(raw) > 30_000_000:
            raise ValueError("RESPONSE_OVER_30MB")
        raw_file.parent.mkdir(parents=True,exist_ok=True)
        temp = raw_file.with_suffix(".tmp")
        temp.write_bytes(raw)
        os.replace(temp,raw_file)
    obj = json.loads(raw)
    if obj.get("type") != "FeatureCollection" or not isinstance(obj.get("features"),list):
        raise ValueError("INVALID_OFFICIAL_WFS_FEATURE_COLLECTION")
    n = len(obj["features"])
    if obj.get("numberMatched") != n or obj.get("numberReturned") != n:
        raise ValueError(f"WFS_INCOMPLETE_{municipality}_{year}: {n} of {obj.get('numberMatched')}")
    codes=[]
    for row in obj["features"]:
        attrs = row["properties"]
        code = attrs.get("CUSEC")
        if attrs.get("CUMUN") != municipality or attrs.get("TIPO") != "SECCIONADO":
            raise ValueError(f"WRONG_WFS_FILTER_RESULT_{municipality}_{year}")
        if not isinstance(code,str) or len(code)!=10 or code[:5]!=municipality:
            raise ValueError("BAD_OFFICIAL_SECTION_CODE")
        codes.append(code)
    if len(set(codes))!=len(codes):
        raise ValueError("DUPLICATE_OFFICIAL_SECTION_CODE")
    return {
        "municipality":municipality,"year":year,"uri":url,"raw_relpath":str(raw_file.relative_to(out)),
        "sha256":digest(raw),"bytes":len(raw),"count":n,
        "timestamp":obj.get("timeStamp"),"features":obj["features"],
    }

def analyze(municipality: str, group: dict, snapshots: dict[int,dict]) -> dict:
    from pyproj import Transformer
    from shapely.geometry import shape
    from shapely.ops import transform, unary_union
    transformer=Transformer.from_crs(SOURCE_CRS,WORK_CRS,always_xy=True).transform
    shapes: dict[int,dict] = {}
    errors=[]
    for year in (2025,2026):
        bycode={}
        for feat in snapshots[year]["features"]:
            c=feat["properties"]["CUSEC"]
            g=shape(feat["geometry"])
            if g.is_empty or not g.is_valid:
                errors.append({"year":year,"CUSEC":c,"error":"SOURCE_GEOMETRY_EMPTY_OR_INVALID"})
            else:
                bycode[c]=transform(transformer,g)
        shapes[year]=bycode
    codes25={x["properties"]["CUSEC"] for x in snapshots[2025]["features"]}
    codes26={x["properties"]["CUSEC"] for x in snapshots[2026]["features"]}
    observed_added=codes26-codes25
    observed_removed=codes25-codes26
    if observed_added!=group["added"] or observed_removed!=group["removed"]:
        errors.append({
            "error":"MUNICIPAL_CUSEC_CHANGE_MISMATCH",
            "expected_added":sorted(group["added"]),"observed_added":sorted(observed_added),
            "expected_removed":sorted(group["removed"]),"observed_removed":sorted(observed_removed),
        })
    results=[]
    for year,key,others in [
        (2026,c,2025) for c in sorted(group["added"])
    ] + [
        (2025,c,2026) for c in sorted(group["removed"])
    ]:
        geo=shapes[year].get(key)
        candidates=shapes[others]
        if geo is None or not candidates:
            results.append({"CUSEC":key,"status":"GEOMETRY_NOT_EVALUABLE"})
            continue
        matches=[]
        for k,g in candidates.items():
            if not geo.intersects(g):
                continue
            try: area=float(geo.intersection(g).area)
            except Exception as exc:
                errors.append({"CUSEC":key,"neighbor":k,"error":type(exc).__name__})
                continue
            if area>0:
                matches.append({"CUSEC":k,"overlap_m2":round(area,5),
                                "target_fraction":round(area/geo.area,9)})
        matches.sort(key=lambda x:-x["overlap_m2"])
        try: union_area=float(geo.intersection(unary_union(list(candidates.values()))).area)
        except Exception:
            union_area=None
        results.append({
            "CUSEC":key,"direction":f"{year}_to_{others}",
            "target_area_m2":round(geo.area,5),
            "covered_fraction":round(union_area/geo.area,9) if union_area is not None else None,
            "spatial_candidates":matches,
            "status":"GEOMETRY_SPATIAL_CANDIDATES_ONLY",
        })
    return {
        "CUMUN":municipality, "source_snapshots":{
            str(y):{k:v for k,v in snapshots[y].items() if k!="features"} for y in (2025,2026)
        },
        "observed_changes":{"added_2026":sorted(observed_added),"retired_2025":sorted(observed_removed)},
        "changed_sections":results,"errors":errors,
    }

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--out",required=True,type=Path)
    parser.add_argument("--workers",type=int,default=3)
    args=parser.parse_args()
    if args.workers not in (1,2,3,4):
        parser.error("--workers must be 1..4")
    out=args.out.resolve()
    out.mkdir(parents=True,exist_ok=True)
    groups=required_groups()
    jobs=[(mun,year) for mun in sorted(groups) for year in (2025,2026)]
    snapshots={}
    failures=[]
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as executor:
        futures={executor.submit(acquire,mun,year,out):(mun,year) for mun,year in jobs}
        for future in concurrent.futures.as_completed(futures):
            mun,year=futures[future]
            try:
                data=future.result()
                snapshots[mun,year]=data
                print(json.dumps({"event":"SOURCE_SAVED","CUMUN":mun,"year":year,
                                  "sha256":data["sha256"],"n":data["count"]}),flush=True)
            except Exception as exc:
                failures.append({"CUMUN":mun,"year":year,"error":repr(exc)})
    results=[]
    for mun,group in sorted(groups.items()):
        if (mun,2025) in snapshots and (mun,2026) in snapshots:
            results.append(analyze(mun,group,{
                2025:snapshots[mun,2025],2026:snapshots[mun,2026]
            }))
    report={
        "schema":"ddd.f10-ine-andalucia-crossyear-spatial-evidence/1.0",
        "scope":"Official 2025/2026 WFS section geometry; NO electoral vote redistribution",
        "authority":"Instituto Nacional de Estadistica",
        "municipalities_expected":len(groups),
        "municipalities_analyzed":len(results),
        "sources_expected":len(jobs),
        "sources_archived":len(snapshots),
        "new_sections_expected":25,"retired_sections_expected":9,
        "source_crs":SOURCE_CRS,"working_crs":WORK_CRS,
        "results":results,"acquisition_errors":failures,
        "source_data_sha256":digest(INE.read_bytes()),
        "crosswalk_accredited":False,"generation_authorized":False,
        "policy":"NO_TRANSPORT_OF_ELECTORAL_VOTES_BY_SPATIAL_APPROXIMATION",
    }
    report_path=out/"crossyear_geometry_evidence.json"
    report_path.write_text(json.dumps(report,ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps({"event":"SUMMARY","sources":len(snapshots),
                      "municipalities":len(results),"errors":len(failures),
                      "report":str(report_path)}),flush=True)
    if failures or any(x["errors"] for x in results):
        raise SystemExit("EVIDENCE_PARTIAL_OR_GEOMETRY_BLOCKED; report preserved")
    if len(results)!=len(groups) or len(snapshots)!=len(jobs):
        raise SystemExit("COVERAGE_INCOMPLETE; report preserved")

if __name__=="__main__":
    main()
