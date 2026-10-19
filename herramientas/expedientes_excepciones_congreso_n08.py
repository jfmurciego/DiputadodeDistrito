"""Read-only decision dossiers for five N08 physically disconnected provinces.

Input: exactly the versioned, SHA-pinned N08 provincial product. This module
cannot accredit an administrative enclave, approve an exception or create a
single electoral district. Every named component is derived from CUSEC IDs,
not a separately inferred boundary.
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
from collections import defaultdict
from pathlib import Path

from ddd_core.congreso_readiness import (
    N08_TRUSTED_MANIFEST_SHA256, provincial_preflight,
)

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "territorios/congreso/contrato_congreso_2026.json"
PRODUCT = ROOT / "docs/ESTUDIOS/N08_TOPOLOGIA_NACIONAL_20251012/producto"
PROVINCES = ("07", "09", "17", "34", "36")
EXPECTED_COMPONENT_COUNTS = {"07": 4, "09": 4, "17": 2, "34": 3, "36": 2}
EXPECTED_REASONS = {
    "07": "COMPONENT_POPULATION_BOUNDS_IMPOSSIBLE",
    "09": "PHYSICAL_COMPONENTS_EXCEED_K",
    "17": "COMPONENT_POPULATION_BOUNDS_IMPOSSIBLE",
    "34": "PHYSICAL_COMPONENTS_EXCEED_K",
    "36": "COMPONENT_POPULATION_BOUNDS_IMPOSSIBLE",
}


def build_dossier() -> dict:
    contract = json.loads(CONTRACT.read_bytes())
    original_manifest = (PRODUCT / "manifest.json").read_bytes()
    if hashlib.sha256(original_manifest).hexdigest() != N08_TRUSTED_MANIFEST_SHA256:
        raise ValueError("UNTRUSTED_ORIGINAL_N08_MANIFEST")
    provinces = []
    exception_candidates = []
    for code in PROVINCES:
        gate = provincial_preflight(contract, PRODUCT, code)
        if gate["structural_necessary_condition"] or gate["structural_necessary_reason"] != EXPECTED_REASONS[code]:
            raise ValueError("PHYSICAL_BLOCK_NO_LONGER_MATCHES:" + code)
        # provincial_preflight has already checked the original immutable
        # manifest and the compressed/uncompressed provincial hashes.
        with gzip.open(PRODUCT / "unidades" / (code + ".json.gz"), "rt", encoding="utf-8") as stream:
            unit = json.load(stream)
        nodes = unit["nodes"]
        by_id = {r["id"]: r for r in nodes}
        components = unit["physical_components"]
        if len(components) != EXPECTED_COMPONENT_COUNTS[code]:
            raise ValueError("PHYSICAL_COMPONENT_COUNT_REGRESSION:" + code)
        covered = [uid for c in components for uid in c["sections"]]
        if len(covered) != len(by_id) or sorted(covered) != sorted(by_id):
            raise ValueError("SECTION_COVERAGE_IN_COMPONENTS_INVALID:" + code)
        k = gate["k"]
        floor = gate["structural_population_floor"]
        cap = gate["structural_population_cap"]
        desc = []
        for c in components:
            members = sorted(c["sections"])
            assert members
            cpop = sum(by_id[uid]["pop"] for uid in members)
            if cpop != c["population"]:
                raise ValueError("COMPONENT_POPULATION_INCONSISTENT:" + code)
            municipals = defaultdict(lambda: {"sections": 0, "population": 0})
            for uid in members:
                n = by_id[uid]
                if n["CPRO"] != code or uid[:5] != n["CUMUN"]:
                    raise ValueError("COMPONENT_ADMIN_IDENTITY_MISMATCH:" + uid)
                municipals[n["CUMUN"]]["sections"] += 1
                municipals[n["CUMUN"]]["population"] += n["pop"]
            min_seats = max(1, (cpop + cap - 1) // cap)
            max_seats = cpop // floor
            desc.append({
                "component_id": c["id"],
                "sections": len(members),
                "population_2025": cpop,
                "municipalities": [{"CUMUN": mid, **v} for mid, v in sorted(municipals.items())],
                "minimum_districts_required_by_cap": min_seats,
                "maximum_districts_allowed_by_floor": max_seats,
                "population_bounds_possible_in_isolation": min_seats <= max_seats,
                "CUSEC_list": members if len(members) <= 30 else None,
                "CUSEC_complete_list_sha256": hashlib.sha256(
                    ("\n".join(members) + "\n").encode("ascii")
                ).hexdigest(),
                "CUSEC_first": members[:5],
            })
        desc.sort(key=lambda c: (-c["population_2025"], c["component_id"]))
        largest_id = desc[0]["component_id"]
        # N08 main section-graph component is selected reproducibly as the
        # largest by population; does not classify island/enclave legality.
        for i, c in enumerate(desc):
            c["main_component_by_population"] = (i == 0)
            if i > 0:
                exception_candidates.append({
                    "CPRO": code,
                    "component_id": c["component_id"],
                    "population_2025": c["population_2025"],
                    "CUSEC_list": c["CUSEC_list"],
                    "CUSEC_sha256": c["CUSEC_complete_list_sha256"],
                    "municipalities": [m["CUMUN"] for m in c["municipalities"]],
                    "administrative_cause": "NOT_YET_ACCREDITED",
                    "legal_geographic_exception_status": "NOT_APPROVED",
                    "source_effective_2025_cnig_verified": False,
                    "requires_individual_owner_decision": True,
                })
        provinces.append({
            "CPRO": code, "approved_K": k,
            "population_2025": gate["population"], "sections": gate["sections"],
            "population_floor": floor, "population_cap": cap,
            "strict_disconnected_component_count": len(desc),
            "main_component_id": largest_id,
            "necessary_condition_passed": False,
            "necessary_condition_reason": gate["structural_necessary_reason"],
            "components": desc,
        })
    if len(exception_candidates) != 10:
        raise ValueError("EXPECTED_TEN_SECONDARY_COMPONENT_CANDIDATES")
    return {
        "schema": "ddd.n08.nominal-exception-dossiers/1.0",
        "scope": "five original strict connectivity/population impossible provinces",
        "original_n08_manifest_sha256": N08_TRUSTED_MANIFEST_SHA256,
        "source_population_year": 2025,
        "candidate_provinces": list(PROVINCES),
        "approved_national_K": 407,
        "provinces": provinces,
        "secondary_components_requiring_classification": exception_candidates,
        "secondary_count": len(exception_candidates),
        "provenance": "N08 original INE 2025, protected by pinned byte hash",
        "cnig_2025_independent_boundary_crossvalidation": False,
        "individual_geographical_exceptions_approved": False,
        "full_52_province_feasibility_proven": False,
        "generation_authorized": False,
        "districts_generated": 0,
        "interpretation": (
            "Component membership is mechanically certified only against the "
            "hash-pinned N08 section graph; isolated municipalities cannot be "
            "classified as legal enclaves or repaired without external dated "
            "geographic proof and named owner decisions."
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="N08 five-province read-only nominal component dossier")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    dossier = build_dossier()
    if args.output:
        if args.output.exists():
            raise FileExistsError("N08_DOSSIER_OUTPUT_ALREADY_EXISTS")
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open("x", encoding="utf-8") as out:
            json.dump(dossier, out, ensure_ascii=False, sort_keys=True, indent=2)
            out.write("\n")
    summary = {
        "provinces": dossier["candidate_provinces"],
        "secondary": dossier["secondary_count"],
        "per_province": {p["CPRO"]: {"K": p["approved_K"],
                                    "components": p["strict_disconnected_component_count"],
                                    "secondary_population": sum(
                                        x["population_2025"] for x in p["components"][1:])}
                         for p in dossier["provinces"]},
        "generation_authorized": False, "official_exceptions_approved": False,
    }
    print("DDD_N08_NOMINAL_DOSSIERS " + json.dumps(summary, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
