#!/usr/bin/env python3
"""VERSIÓN: 1.0.1; NOMBRE: incorporación reproducible de cartografía histórica.
FECHA: 2026-10-09; ALCANCE: sólo archivos locales nombrados, sin red ni macros.
ESTADO: CI_PENDIENTE; CAMBIOS: conserva bytes, inventario y diagnósticos comparables.
MOTIVO: no confundir descubrimiento de archivos con acreditación de edición.
ANTERIOR: legacy/herramientas/inventariar_cartografia_historica.py; CAMBIOS C2: equivalencia sólo con prueba positiva.
"""
from __future__ import annotations
import argparse
from collections import Counter
from decimal import Decimal
import gzip
import hashlib
import json
from pathlib import Path
import sys
import struct
import zipfile
from pyproj import CRS

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from herramientas.comparar_cartografia_nacional import metadata, inspect_geojson, workbook_summary, compare_maps, identity, province, population

NAMES={"spain-districts-selected.json", "assembled_districts_spain.xlsm", "map.geojson"}
SECTIONING_2025_BASELINE_SHA256='55c9da7e34d3bb3cb725400c35b58e72f4db2ea8321ef91237a89e708d2dbcc4'


def descriptor():
    return {"id_field":"district", "province_field":"province_id", "population_field":"pob_t_total",
            "geometry_edition":None,"population_edition":None,"unit_kind":"districts",
            "scope":"historical_national_candidate_not_certified","require_connected":False,
            "provenance":{"accredited":False,"evidence":[]},"stable_identity_accredited":False}


def write_json(path, payload):
    path.write_text(json.dumps(payload,ensure_ascii=False,sort_keys=True,indent=2)+"\n",encoding="utf-8")


def sectioning_reference(path, expected_hash):
    """Identidad con el baseline INE conservado; sólo atributos DBF y PRJ, no overlay."""
    path=Path(path);digest=hashlib.sha256(path.read_bytes()).hexdigest()
    if expected_hash != SECTIONING_2025_BASELINE_SHA256 or digest != expected_hash:
        raise ValueError("SECTIONING_REFERENCE_HASH_MISMATCH")
    with zipfile.ZipFile(path) as archive:
        dbf=next(n for n in archive.namelist() if n.lower().endswith('.dbf'))
        prj=next(n for n in archive.namelist() if n.lower().endswith('.prj'))
        raw=archive.read(dbf);count=struct.unpack('<I',raw[4:8])[0]
        header,length=struct.unpack('<HH',raw[8:12]);fields=[];offset=1
        for position in range(32,header-1,32):
            name=raw[position:position+11].split(b'\0')[0].decode();size=raw[position+16]
            fields.append((name,offset,size));offset+=size
        if len(raw)<header+count*length or offset != length:
            raise ValueError("DBF_TRUNCATED_OR_LENGTH_INCONSISTENT")
        provinces=Counter();keys=set()
        for index in range(count):
            record=raw[header+index*length:header+(index+1)*length]
            if record[0:1] != b' ':
                raise ValueError("DBF_DELETED_OR_INVALID_ROW")
            values={name:record[start:start+size].decode('latin1').strip() for name,start,size in fields}
            key=identity(values['CUSEC']);code=province(values['CPRO'])
            if key in keys:raise ValueError("SECTION_ID_DUPLICATE")
            keys.add(key);provinces[code]+=1
        crs=CRS.from_wkt(archive.read(prj).decode())
    return {"metadata":metadata(),"path":str(path),"file_sha256":digest,
            "edition":2025,"edition_evidence":"exact bytes match protected inputs/MANIFEST.sha256 baseline INE 2025; not inferred solely from filename",
            "unit_kind":"census_sections","unit_id_field":"CUSEC","unit_count":count,
            "unique_ids":len(keys),"province_counts":dict(sorted(provinces.items())),"fields":[f[0] for f in fields],
            "crs":crs.to_string(),"geometry_validity":"NOT_TESTED_ATTRIBUTE_INVENTORY_ONLY",
            "compatibility_with_historical_district_map":"different geographic unit; not a national 2025 district map"}


def incorporate(search_report, output, section_zip=None, section_hash=None):
    output=Path(output); search=json.loads(Path(search_report).read_text())
    paths=[Path(p) for p in search["found"] if Path(p).name in NAMES]
    if not paths:
        raise ValueError("NO_PHYSICAL_CARTOGRAPHIC_INPUTS")
    # Valida disponibilidad física antes de crear salida; no fuerza descarga iCloud.
    for path in paths:
        if path.stat().st_flags & 0x40000000:
            raise ValueError("CLOUD_PLACEHOLDER_NOT_PHYSICAL")
    output.mkdir(parents=True,exist_ok=False);(output/"inputs").mkdir()
    records=[];maps={};books=[];stored={}
    for path in paths:
        raw=path.read_bytes();digest=hashlib.sha256(raw).hexdigest()
        if digest not in stored:
            relative=f"inputs/{digest[:12]}_{path.name}.gz"
            (output/relative).write_bytes(gzip.compress(raw,mtime=0));stored[digest]=relative
        record={"original_path":str(path),"name":path.name,"file_sha256":digest,"byte_size":len(raw),
                "archived_path":stored[digest],"geometry_edition":None,"population_edition":None,
                "provenance_status":"LOCAL_PROJECT_MATERIAL_EDITION_NOT_ACCREDITED"}
        if path.suffix in {".json",".geojson"}:
            desc=descriptor();desc["file_sha256"]=digest
            report,_,_=inspect_geojson(path,desc)
            record["inspection"]=report
            maps.setdefault(path.name,(path,json.loads(raw),desc))
        else:
            book=workbook_summary(path);book.pop("rows")
            record["inspection"]=book;books.append(record)
        records.append(record)
    selected_path,selected,selected_desc=maps["spain-districts-selected.json"]
    other_path,other,other_desc=maps["map.geojson"]
    def raw_records(data):
        result={}
        for feature in data["features"]:
            key=identity(feature["properties"].get("district"))
            if key in result:raise ValueError("HISTORICAL_ID_DUPLICATE")
            result[key]=feature
        return result
    left=raw_records(selected);right=raw_records(other)
    common=sorted(set(left)&set(right));counts=Counter();populations=Counter()
    for feature in left.values():
        code=province(feature["properties"]["province_id"]);counts[code]+=1
        populations[code]+=population(feature["properties"]["pob_t_total"])
    if set(counts) != {f'{i:02d}' for i in range(1,53)}:
        raise ValueError("HISTORICAL_ATTRIBUTE_COVERAGE_INCOMPLETE")
    same_properties=0
    for key in common:
        a=left[key]["properties"];b=right[key]["properties"]
        if province(a["province_id"])==province(b["province_id"]) and population(a["pob_t_total"])==population(b["pob_t_total"]) and population(a["target_pob"])==population(b["target_pob"]) and str(a["map_iteration"])==str(b["map_iteration"]):
            same_properties+=1
    attributes={"metadata":metadata(),"historical_geometry_edition":None,"historical_population_edition":None,
                "historical_feature_count":len(left),"province_counts":dict(sorted(counts.items())),
                "province_population_reported_decimal":{c:str(p) for c,p in sorted(populations.items())},
                "population_reported_decimal_total":str(sum(populations.values(),Decimal(0))),
                "district_population_minimum_reported":str(min(population(f["properties"]["pob_t_total"]) for f in left.values())),
                "district_population_maximum_reported":str(max(population(f["properties"]["pob_t_total"]) for f in left.values())),
                "numeric_warning":"Decimal preserves source values; tiny non-integer residues are not corrected or promoted as official counts",
                "all_geometries_valid":False if any(r.get("inspection",{}).get("errors") for r in records) else True}
    equivalence={"metadata":metadata(),"scope":"file_variant_diagnostic_not_2022_2025_comparison",
                 "identifier_intersection_count":len(common),"raw_coordinate_identical_pairs":sum(left[k]["geometry"]==right[k]["geometry"] for k in common),
                 "normalized_attribute_identical_pairs":same_properties,
                 "workbook_sheet_xml_identical":len({r["inspection"]["sheet_xml_sha256"] for r in books})==1,
                 "workbook_members_with_different_hashes": sorted({key for r in books for key in r["inspection"]["member_sha256"] if len({other["inspection"]["member_sha256"].get(key) for other in books}) > 1}),
                 "interpretation":"INSUFFICIENT_EVIDENCE",
                 "temporal_change_metrics":None}
    equivalence['interpretation'] = historical_material_verdict(
        set(left), set(right), equivalence['raw_coordinate_identical_pairs'],
        same_properties, [b['inspection'].get('sheet_xml_sha256') for b in books])
    gate=compare_maps(selected_path,selected_desc,other_path,other_desc)
    gate["attempt_scope"]="admissibility_of_historical_variants; neither input is accredited as 2022 or 2025"
    gate["national_2025_district_map_available"]=False
    write_json(output/"inventario.json",{"metadata":metadata(),"search":search,"files":records})
    write_json(output/"atributos_historicos.json",attributes)
    write_json(output/"recuentos_historicos.json",dict(sorted(counts.items())))
    write_json(output/"equivalencia_archivos.json",equivalence)
    write_json(output/"comparabilidad_temporal.json",gate)
    write_json(output/"descriptor_historico_seleccionado.json",selected_desc)
    write_json(output/"descriptor_historico_map.json",other_desc)
    if section_zip is not None:
        write_json(output/"referencia_seccionado_2025.json",sectioning_reference(section_zip,section_hash))
    return {"archived_unique_inputs":len(stored),"files_found":len(paths),"historical_k":len(left),"temporal_status":gate["status"]}


def historical_material_verdict(left_ids, right_ids, geometry_pairs, attribute_pairs, sheet_hashes):
    if not left_ids or not right_ids or len(sheet_hashes) < 2 or any(not h for h in sheet_hashes):
        return 'INSUFFICIENT_EVIDENCE'
    if (left_ids != right_ids or geometry_pairs != len(left_ids)
            or attribute_pairs != len(left_ids) or len(set(sheet_hashes)) != 1):
        return 'DIFFERENT_HISTORICAL_MATERIAL'
    return 'same_historical_material; creation timestamps do not establish dataset editions'


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--search-report",required=True,type=Path);parser.add_argument("--output",required=True,type=Path)
    parser.add_argument("--section-zip",type=Path);parser.add_argument("--section-sha256")
    args=parser.parse_args();print(json.dumps(incorporate(args.search_report,args.output,args.section_zip,args.section_sha256),sort_keys=True))


if __name__=="__main__":
    main()
