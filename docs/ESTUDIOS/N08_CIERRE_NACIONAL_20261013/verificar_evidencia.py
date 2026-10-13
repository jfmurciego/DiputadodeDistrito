#!/usr/bin/env python3
"""Independent read-only verification of carried N08 and Cáceres evidence."""
from __future__ import annotations

import csv
import gzip
import hashlib
import json
from decimal import Decimal, ROUND_CEILING, ROUND_FLOOR
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
N08 = ROOT / "docs/ESTUDIOS/N08_TOPOLOGIA_NACIONAL_20251012"
CAC = ROOT / "docs/ESTUDIOS/N08_CACERES_20261012"
OUT = ROOT / "docs/ESTUDIOS/N08_CIERRE_NACIONAL_20261013"
HISTORIC = {
    "ddd_core/congreso_contract.py": "legacy/n08_caceres_20261012/congreso_contract_v1_1.py",
    "territorios/congreso/contrato_congreso_2026.json": "legacy/n08_caceres_20261012/contrato_congreso_2026_v0_3.json",
    "tests/test_preflight_caceres_n08.py": "legacy/n08_caceres_20261012/test_preflight_caceres_n08_v1.py",
    "ddd_core/congreso_preflight_adapter.py": "legacy/n08_caceres_20261012/congreso_preflight_adapter_v0_1.py",
    "ddd_core/m05_population_repair.py": "legacy/n08_caceres_20261012/m05_population_repair_v1_6.py",
    "herramientas/preflight_caceres_n08.py": "legacy/n08_caceres_20261012/preflight_caceres_n08_v1.py",
}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def check_manifest(path: Path, *, root_relative: bool, mapping=None):
    manifest = json.loads(path.read_text())
    entries = manifest.get("files_sha256", manifest.get("files", {}))
    result = []
    for rel, expected in entries.items():
        expected_sha = expected if isinstance(expected, str) else expected["sha256"]
        target = (ROOT / (mapping or {}).get(rel, rel)) if root_relative else path.parent / rel
        actual = sha(target) if target.is_file() else None
        size_ok = not isinstance(expected, dict) or target.stat().st_size == expected.get("bytes")
        result.append({"path": rel, "expected_sha256": expected_sha, "actual_sha256": actual,
                       "verified": actual == expected_sha and size_ok})
    return result


def main():
    contract = json.loads((ROOT / "territorios/congreso/contrato_congreso_2026.json").read_text())
    quotas = {row["code"]: row["k"] for row in contract["quotas_by_origin_unit"]}
    inv = list(csv.DictReader((N08 / "INVENTARIO_52.csv").open(newline="")))
    component_rows = list(csv.DictReader((N08 / "COMPONENTES_POBLACION.csv").open(newline="")))
    uncredited = {c for row in component_rows for c in row["CUSEC_sin_desagregacion"].split(",") if c}
    matrix = []
    total_sections = total_population = total_k = total_edges = overlap_pairs = cross_component_overlaps = 0
    cusecs_over_cap = []
    components_exceeding_k = []
    for row in inv:
        cpro = row["CPRO"]
        artifact = N08 / f"producto/unidades/{cpro}.json.gz"
        product = json.loads(gzip.open(artifact, "rt", encoding="utf-8").read())
        pop, k = int(row["poblacion_2025"]), quotas[cpro]
        floor = int((Decimal(17) * pop / (20 * k)).to_integral_value(rounding=ROUND_CEILING))
        cap = int((Decimal(23) * pop / (20 * k)).to_integral_value(rounding=ROUND_FLOOR))
        nodes = {node["id"]: node for node in product["nodes"]}
        overlaps = product["overlaps"]
        cross = sum(nodes[o["u"]]["physical_component"] != nodes[o["v"]]["physical_component"] for o in overlaps)
        missing_here = sorted(uncredited.intersection(nodes))
        part_components = len(product["polygon_part_components"])
        oversized = sorted((node["id"], int(node["pop"])) for node in product["nodes"] if int(node["pop"]) > cap)
        cusecs_over_cap.extend((cpro, ident, population, cap) for ident, population in oversized)
        if part_components > k:
            components_exceeding_k.append(cpro)
        overlap_pairs += len(overlaps)
        cross_component_overlaps += cross
        total_sections += len(nodes)
        total_population += sum(int(node["pop"]) for node in nodes.values())
        total_k += k
        total_edges += len(product["edges"])
        matrix.append({
            "CPRO": cpro, "sections": len(nodes), "population_2025": pop, "K_approved": k,
            "target_exact": f"{Decimal(pop) / Decimal(k):.12f}", "floor_85pct": floor, "cap_115pct": cap,
            "physical_edges": len(product["edges"]), "section_components": len(product["physical_components"]),
            "polygon_part_components": part_components, "components_gt_K": part_components > k,
            "overlap_pairs": len(overlaps), "cross_component_overlaps_excluded": cross,
            "uncredited_multipart_CUSEC": len(missing_here), "CUSEC_over_cap": len(oversized),
            "preflight_state": row["factibilidad"], "necessary_conditions": "NOT_SUFFICIENT_FOR_FEASIBILITY",
            "generation_authorized": str(product.get("generation_authorized", False)).lower(),
        })
    assert len(inv) == len(quotas) == 52
    assert len({row["CPRO"] for row in inv}) == 52
    assert total_sections == 36554 and total_population == 49128297 and total_k == 407
    assert overlap_pairs == 498 and cross_component_overlaps == 9
    assert len(components_exceeding_k) == 9 and len(uncredited) == 115 and not cusecs_over_cap
    with (OUT / "MATRIZ_FACTIBILIDAD_52.csv").open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(matrix[0]), lineterminator="\n")
        writer.writeheader(); writer.writerows(matrix)
    national = check_manifest(N08 / "MANIFEST_ENTREGA.json", root_relative=False)
    caceres = check_manifest(CAC / "MANIFEST.json", root_relative=True, mapping=HISTORIC)
    assert len(national) == 74 and all(x["verified"] for x in national)
    assert len(caceres) == 26 and all(x["verified"] for x in caceres)
    report = {
        "schema": "ddd.n08-national-close-verification/1.0", "read_only": True,
        "source_evidence": "existing versioned artifacts only; no source download or dataset regeneration",
        "national_manifest": {"entries": len(national), "verified": sum(x["verified"] for x in national), "files": national},
        "caceres_manifest": {"entries": len(caceres), "verified": sum(x["verified"] for x in caceres), "files": caceres},
        "coverage": {"origin_units": len(inv), "sections": total_sections, "population_2025": total_population,
                     "K": total_k, "physical_edges": total_edges},
        "derived_results": {"CUSec_over_115pct_cap": cusecs_over_cap,
                             "polygon_component_count_gt_K": components_exceeding_k,
                             "overlap_pairs": overlap_pairs, "overlaps_between_distinct_physical_components": cross_component_overlaps,
                             "CUSec_without_multipart_population_attribution": len(uncredited),
                             "limitations": ["necessary conditions only; no constructive partition certified",
                                             "overlaps are not admitted as graph edges"]},
        "contract_sha256": sha(ROOT / "territorios/congreso/contrato_congreso_2026.json"),
        "matrix_sha256": sha(OUT / "MATRIZ_FACTIBILIDAD_52.csv"),
        "generation_authorized": False,
    }
    (OUT / "VERIFICACION.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    local_files = ["INFORME.md", "TRANSICION.json", "MATRIZ_FACTIBILIDAD_52.csv", "VERIFICACION.json",
                   "REVISION_INDEPENDIENTE.md", "INCIDENCIA_PUBLICACION.md", "verificar_evidencia.py"]
    local_manifest = {
        "schema": "ddd.n08-campaign-evidence-manifest/1.0", "status": "DIAGNOSTIC_ONLY",
        "generation_authorized": False,
        "files_sha256": {name: sha(OUT / name) for name in local_files},
    }
    (OUT / "MANIFEST.json").write_text(json.dumps(local_manifest, ensure_ascii=False, indent=2) + "\n")
    print(f"PASS: N08 {len(national)}/74; Cáceres histórico {len(caceres)}/26; 52/52; {total_sections} CUSEC; P={total_population}; K={total_k}; {total_edges} aristas")
    print(f"Derivados: overcap={len(cusecs_over_cap)}; componentes>K={len(components_exceeding_k)}; overlap={overlap_pairs}; cross-component overlap={cross_component_overlaps}; multipart sin atribución={len(uncredited)}")


if __name__ == "__main__":
    main()
