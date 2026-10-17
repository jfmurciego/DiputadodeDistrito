"""Diagnóstico read-only de las nueve provincias N08 usando geometría original INE 2025.

No acredita límites administrativos ni crea aristas, excepciones o distritos.
Reutiliza el lector contractual hash-locked y el grafo N08 sin tolerancias.
"""
from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter
from pathlib import Path

import numpy as np
import shapely
from shapely import STRtree

from ddd_core.congreso_topology import canonical_components, contacts
from herramientas.preflight_topologico_nacional import ROOT, load_inputs

CASES = ("04", "07", "09", "15", "17", "27", "30", "34", "36")
MATRIX = ROOT / "docs/ESTUDIOS/CAMPANA_NACIONAL_20261013/D04_COMPONENTES_MAYORES_QUE_K.csv"


def closest_pair(left, right, lookup):
    """Closest pair of *original* section geometries across two components.

    A nearest point/overlap is evidence for inspection, never an adjacency.
    """
    if len(left) > len(right):
        left, right = right, left
    others = [lookup[uid]["geometry"] for uid in right]
    tree = STRtree(others)
    best = None
    for uid in left:
        left_geom = lookup[uid]["geometry"]
        ix = int(tree.nearest(left_geom))
        other = right[ix]
        geom = others[ix]
        distance = float(shapely.distance(left_geom, geom))
        record = {
            "CUSEC_1": min(uid, other), "CUSEC_2": max(uid, other),
            "distance_m": distance,
            "CUMUN_1": lookup[min(uid, other)]["CUMUN"],
            "CUMUN_2": lookup[max(uid, other)]["CUMUN"],
            "contact_kind": (
                "separated" if distance > 0
                else "overlap" if float(shapely.area(shapely.intersection(left_geom, geom))) > 0
                else "linear" if float(shapely.length(shapely.intersection(
                    shapely.boundary(left_geom), shapely.boundary(geom)))) > 0
                else "point_only"
            ),
        }
        # Exact tie-break is stable and never round/buffer coordinates.
        rank = (distance, record["CUSEC_1"], record["CUSEC_2"])
        if best is None or rank < best[0]:
            best = rank, record
    return best[1]


def run():
    # load_inputs verifies SHA-256 of each protected part, the complete ZIP,
    # all 36,554 CUSEC WKB identities, population joins and approved K=407.
    frame, contract, evidence = load_inputs(ROOT / "inputs/partes")
    if contract["accreditation"]["generation_authorized"] is not False:
        raise ValueError("PRODUCTION_MUST_REMAIN_BLOCKED")
    with MATRIX.open(encoding="utf-8", newline="") as stream:
        expected = {r["CPRO"]: r for r in csv.DictReader(stream)}
    if set(CASES) - set(expected):
        raise ValueError("NINE_CASE_MATRIX_INCOMPLETE")
    reports = []
    for cpro in CASES:
        unit = frame.loc[frame.CPRO == cpro].sort_values("CUSEC").copy()
        ids = unit.CUSEC.tolist()
        geometry = unit.geometry.to_numpy()
        contact_records = contacts(geometry, ids)
        edges = [record for record in contact_records if record["kind"] == "linear"]
        components = canonical_components(ids, edges)
        record = expected[cpro]
        if (len(components) != int(record["componentes_grafo_seccional"])
                or len(ids) != int(record["secciones"])
                or int(unit.POB_2025.sum()) != int(record["poblacion"])):
            raise ValueError("ORIGINAL_GRAPH_ARCHIVE_REGRESSION:" + cpro)
        lookup = {str(row.CUSEC): {"geometry": row.geometry,
                                   "CUMUN": str(row.CUMUN),
                                   "pop": int(row.POB_2025)}
                  for row in unit.itertuples()}
        component_info = []
        for ix, group in enumerate(components):
            municipalities = Counter(lookup[uid]["CUMUN"] for uid in group)
            component_info.append({
                "component": ix + 1, "section_count": len(group),
                "population_2025": sum(lookup[uid]["pop"] for uid in group),
                "municipality_count": len(municipalities),
                "municipalities": sorted(municipalities.items()) if len(group) <= 15
                                  else sorted(municipalities.items())[:12],
                "all_CUSEC": group if len(group) <= 20 else None,
                "CUSEC_sample": group[:12],
            })
        nearest = []
        for i in range(len(components)):
            for j in range(i + 1, len(components)):
                nearest.append({"component_1": i + 1, "component_2": j + 1,
                                **closest_pair(components[i], components[j], lookup)})
        report = {
            "CPRO": cpro,
            "K_approved": int(record["K_aprobado"]),
            "sections": len(ids),
            "section_components": len(components),
            "component_over_K": len(components) > int(record["K_aprobado"]),
            "components": component_info,
            "nearest_original_pairs": nearest,
            "point_contacts": sum(r["kind"] == "point" for r in contact_records),
            "overlap_pairs": sum(r["kind"] == "overlap" for r in contact_records),
            "linear_edges": len(edges),
            "source_sha256": contract["sources"]["geometry"]["sha256"],
            "contract_version": contract["metadata"]["version"],
            "generation_authorized": False,
        }
        reports.append(report)
        print("DDD_N08_CASE " + json.dumps(report, ensure_ascii=False, sort_keys=True,
                                           separators=(",", ":")), flush=True)
    assert len(reports) == 9
    assert [r["CPRO"] for r in reports if r["component_over_K"]] == ["09", "34"]
    summary = {"cases":len(reports), "section_components_count_verified":True,
               "blocking_CPPO":["09","34"], "source_sha256":evidence["source_binding"]["geometry"]["sha256"],
               "generation_authorized":False}
    print("DDD_N08_FINAL " + json.dumps(summary, sort_keys=True), flush=True)


if __name__ == "__main__":
    run()
