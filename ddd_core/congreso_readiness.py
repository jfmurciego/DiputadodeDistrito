"""Puertas de lectura del Congreso: diagnóstico provincial, nacional y autorización.

No ejecuta M01-M08, no modifica contratos y nunca concede generación.
Los productos N08 se comprueban por hash antes de emitir diagnósticos.
"""
from __future__ import annotations

import gzip
import hashlib
import json
from pathlib import Path

from ddd_core.congreso_contract import CONGRESS_CODES, production_blockers, validate_congress_identity
from ddd_core.congreso_preflight_adapter import structural_component_bound, validate_physical_product

OWNER_POLICIES = (
    "minimum_unit", "contiguity", "population_limits",
    "municipal_indivisibility", "islands", "enclaves",
    "physical_discontinuities",
)


def _require(condition: bool, reason: str) -> None:
    if not condition:
        raise ValueError(reason)


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _canonical(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":"), allow_nan=False).encode()


def provincial_preflight(contract: dict, product_root: Path, province: str) -> dict:
    """Acredita inputs provinciales N08 sin exigir acreditación 52/52.

    PASS_INPUTS es únicamente una puerta de evidencia: ni el algoritmo M04
    ni una partición territorial ni una excepción administrativa quedan
    certificados. Las decisiones del propietario se informan por separado.
    """
    validate_congress_identity(contract)
    code = str(province).zfill(2)
    _require(code in CONGRESS_CODES, "PROVINCE_CODE_INVALID")
    _require(contract.get("accreditation", {}).get("generation_authorized") is False,
             "PRODUCTION_MUST_REMAIN_DISABLED")

    manifest_path = Path(product_root) / "manifest.json"
    manifest = json.loads(manifest_path.read_bytes())
    identity = manifest.get("identity_sha256")
    _require(identity == _sha(_canonical({k: v for k, v in manifest.items()
                                         if k != "identity_sha256"})), "TOPOLOGY_MANIFEST_IDENTITY")
    _require(manifest.get("generation_authorized") is False, "TOPOLOGY_AUTHORIZATION_INVALID")

    relative = "unidades/" + code + ".json.gz"
    artifact = manifest.get("artifacts", {}).get(relative)
    _require(isinstance(artifact, dict), "PROVINCIAL_ARTIFACT_MISSING")
    binary = (Path(product_root) / relative).read_bytes()
    _require(_sha(binary) == artifact.get("sha256") and len(binary) == artifact.get("bytes"),
             "PROVINCIAL_ARTIFACT_HASH")
    raw = gzip.decompress(binary)
    unit = json.loads(raw)
    _require(_sha(raw) == artifact.get("canonical_json_sha256"),
             "PROVINCIAL_ARTIFACT_UNCOMPRESSED_HASH")
    _require(raw == _canonical(unit) + b"\n",
             "PROVINCIAL_ARTIFACT_CANONICAL")
    # Do not recompress: gzip/zlib output headers and deflate streams vary by
    # runtime. The exact published compressed bytes and decoded canonical
    # bytes are independently authenticated by the two manifest SHA-256 values.
    _require(unit.get("run_binding") == manifest.get("run_binding"),
             "PROVINCIAL_RUN_BINDING")

    source_binding = {
        kind: {"edition": contract["sources"][kind]["edition"],
               "sha256": contract["sources"][kind]["sha256"]}
        for kind in ("geometry", "population")
    }
    for kind in ("geometry", "population"):
        actual = manifest.get("evidence", {}).get("source_binding", {}).get(kind, {})
        _require(actual.get("sha256") == source_binding[kind]["sha256"]
                 and actual.get("edition") == source_binding[kind]["edition"],
                 "PROVINCIAL_SOURCE_BINDING:" + kind)

    graph = validate_physical_product(
        contract, unit["nodes"], unit["edges"], source_binding, require_national=False)
    summary = unit["summary"]
    quota = {row["code"]: row["k"] for row in contract["quotas_by_origin_unit"]}[code]
    population = sum(n["pop"] for n in unit["nodes"])
    _require(summary.get("CPRO") == code
             and all(n["CPRO"] == code for n in unit["nodes"]),
             "PROVINCIAL_IDENTITY")
    _require(summary.get("sections") == len(unit["nodes"])
             and summary.get("population") == population
             and summary.get("edges") == len(unit["edges"]),
             "PROVINCIAL_SUMMARY_MISMATCH")
    _require(type(quota) is int and summary.get("k") == quota
             and quota == max(1, (population + 60000) // 120000),
             "PROVINCIAL_K_MISMATCH")

    structural = structural_component_bound(
        [int(component["population"]) for component in unit["physical_components"]], quota)
    decisions = contract.get("decisions", {})
    pending = sorted(key for key in OWNER_POLICIES
                     if not isinstance(decisions.get(key), dict)
                     or decisions[key].get("status") != "APPROVED"
                     or decisions[key].get("value") is None)
    blockers = []
    if not structural["necessary_condition"]:
        blockers.append("PHYSICAL_COMPONENTS_EXCEED_K")
    if summary.get("discontinuous_municipalities"):
        blockers.append("MUNICIPAL_DISCONTINUITIES_REQUIRE_REVIEW")
    if summary.get("multipart_sections_spanning_physical_components"):
        blockers.append("MULTIPART_SECTIONS_REQUIRE_REVIEW")
    return {
        "gate": "PROVINCIAL_PREFLIGHT",
        "province": code,
        "input_status": "PASS_INPUTS_ONLY",
        "policy_status": "BLOCKED" if pending else "POLICY_DECLARED",
        "pending_owner_decisions": pending,
        "structural_necessary_condition": structural["necessary_condition"],
        "structural_feasibility_proven": False,
        "territorial_cautions": blockers,
        "evidence_scope": "ACCREDITED_N08_PRODUCT_NOT_REAL_M04_M06_PARTITION",
        "sections": graph["nodes"], "edges": graph["edges"],
        "population": graph["population"], "k": quota,
        "topology_sha256": _sha(binary),
        "generation_authorized": False,
    }


def national_readiness(contract: dict) -> dict:
    """La admisión 52/52 permanece nacional; nunca concede ejecución."""
    blockers = production_blockers(contract)
    return {
        "gate": "NATIONAL_READINESS",
        "status": "BLOCKED" if blockers else "CONTRACT_ADMITTED_ONLY",
        "blockers": blockers,
        "generation_authorized": False,
    }


def execution_authorization(provincial: dict, national: dict) -> dict:
    """Diagnóstico de la tercera puerta, que no emite ni acepta órdenes.

    La orden del propietario debe verificarse en un canal separado y
    expresamente autorizado; jamás se infiere de puertas técnicas.
    """
    blockers = ["EXPRESS_OWNER_EXECUTION_ORDER_ABSENT"]
    if provincial.get("input_status") != "PASS_INPUTS_ONLY":
        blockers.append("PROVINCIAL_INPUTS_NOT_ADMITTED")
    if provincial.get("policy_status") != "POLICY_DECLARED":
        blockers.append("PROVINCIAL_OWNER_POLICIES_PENDING")
    if provincial.get("territorial_cautions"):
        blockers.append("PROVINCIAL_TERRITORIAL_EXCEPTIONS_PENDING")
    if not provincial.get("structural_necessary_condition"):
        blockers.append("PROVINCIAL_STRUCTURAL_BLOCK")
    if national.get("status") != "CONTRACT_ADMITTED_ONLY":
        blockers.append("NATIONAL_READINESS_PENDING")
    return {
        "gate": "EXECUTION_AUTHORIZATION",
        "status": "DENIED",
        "blockers": blockers,
        "generation_authorized": False,
        "districts_generated": 0,
    }


def inspect_three_gates(contract: dict, product_root: Path, province: str) -> dict:
    provincial = provincial_preflight(contract, product_root, province)
    national = national_readiness(contract)
    return {
        "provincial": provincial,
        "national": national,
        "execution": execution_authorization(provincial, national),
    }
