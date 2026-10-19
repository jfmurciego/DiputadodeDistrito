"""Reproduce a conditional one-district witness from accredited N08 artifacts.

This diagnostic never runs M04-M06, certifies an electoral product or changes
authorization gates. A witness is conditional on the source-bound topology
product and its represented CUSEC universe; external territorial boundary and
exception accreditation remain separate and may stay insufficient.

Version: 1.0.0 (new isolated Congress diagnostic; 2026-10-13)
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import math
from pathlib import Path
from typing import Any

from ddd_core.congreso_contract import N08_OWNER_DECISION_ID

RATIOS = {"population_floor_ratio": (17, 20), "population_cap_ratio": (23, 20)}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def canonical_sha256(value: Any) -> str:
    payload = (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def evaluate_unit(
    *,
    preflight_path: Path,
    checkpoint_path: Path,
    unit_path: Path,
    product_manifest_path: Path,
    contract_path: Path,
) -> dict[str, Any]:
    """Evaluate one real preflight/product binding; never generate a partition.

    For K=1 only, a single CUSEC-atomic assignment is an immediate graph witness
    if exact file bindings, full node/part coverage, positive-linear-edge
    topology, connectedness and approved population bounds all verify. Its
    status is conditional to the versioned topology product. Any external
    boundary or exception uncertainty is separately reported as insufficient
    evidence and does not become a factibility/product PASS.
    """
    paths = {
        "preflight": preflight_path,
        "checkpoint": checkpoint_path,
        "unit_product": unit_path,
        "product_manifest": product_manifest_path,
        "contract": contract_path,
    }
    hashes = {key: sha256_file(path) for key, path in paths.items()}
    preflight = _read_json(preflight_path)
    checkpoint = _read_json(checkpoint_path)
    product_manifest = _read_json(product_manifest_path)
    contract = _read_json(contract_path)
    with gzip.open(unit_path, "rt", encoding="utf-8") as stream:
        unit = json.load(stream)

    errors: list[str] = []
    cpro = preflight.get("province")
    if not isinstance(cpro, str) or len(cpro) != 2 or not cpro.isdigit():
        errors.append("PREFLIGHT_CPRO_INVALID")
        cpro = "??"
    if checkpoint.get("province") != cpro:
        errors.append("CHECKPOINT_CPRO_MISMATCH")
    if checkpoint.get("preflight_sha256") != hashes["preflight"]:
        errors.append("PREFLIGHT_CHECKPOINT_HASH_MISMATCH")
    if checkpoint.get("topology_unit_sha256") != hashes["unit_product"]:
        errors.append("CHECKPOINT_UNIT_HASH_MISMATCH")
    if checkpoint.get("topology_manifest_identity_sha256") != product_manifest.get("identity_sha256"):
        errors.append("CHECKPOINT_PRODUCT_IDENTITY_MISMATCH")
    if checkpoint.get("tool_sha256") != preflight.get("tool_sha256"):
        errors.append("CHECKPOINT_TOOL_HASH_MISMATCH")
    # The checkpoint is a separate trust boundary: its content is not covered
    # by the preflight file hash, so bind its schema/version, source inputs and
    # closed generation state explicitly.
    if preflight.get("version") != "1.2.0" or checkpoint.get("version") != preflight.get("version"):
        errors.append("PREFLIGHT_CHECKPOINT_VERSION_MISMATCH")
    if checkpoint.get("source_binding") != preflight.get("source_binding"):
        errors.append("CHECKPOINT_SOURCE_BINDING_MISMATCH")
    if checkpoint.get("generation_authorized") is not False:
        errors.append("CHECKPOINT_GENERATION_GATE_NOT_CLOSED")
    if type(checkpoint.get("districts_generated")) is not int or checkpoint.get("districts_generated") != 0:
        errors.append("CHECKPOINT_DISTRICT_COUNT_INVALID")
    contract_hash = hashes["contract"]
    source_evidence = preflight.get("source_evidence", {})
    if source_evidence.get("contract_sha256") != contract_hash:
        errors.append("PREFLIGHT_CONTRACT_HASH_MISMATCH")
    source_binding = preflight.get("source_binding", {})
    for source_name in ("geometry", "population"):
        source_record = contract.get("sources", {}).get(source_name, {})
        declared = source_record.get("sha256")
        observed = source_binding.get(source_name, {}).get("sha256")
        if declared != observed:
            errors.append(f"PREFLIGHT_{source_name.upper()}_SOURCE_HASH_MISMATCH")
        if source_record.get("accreditation") != "ACCREDITED" or source_record.get("edition") != 2025:
            errors.append(f"CONTRACT_{source_name.upper()}_SOURCE_NOT_ACCREDITED_2025")
    if product_manifest.get("identity_sha256") != preflight.get("topology_manifest_identity_sha256"):
        errors.append("PREFLIGHT_PRODUCT_IDENTITY_MISMATCH")
    # The official topology-manifest identity convention is canonical JSON
    # without a trailing newline (artifact payload hashes use other rules).
    identity_payload = json.dumps(
        {key: value for key, value in product_manifest.items() if key != "identity_sha256"},
        ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False,
    ).encode("utf-8")
    expected_identity = hashlib.sha256(identity_payload).hexdigest()
    if product_manifest.get("schema") != "ddd.congress-topology-diagnostic/1.0" or product_manifest.get("identity_sha256") != expected_identity:
        errors.append("TOPOLOGY_MANIFEST_CANONICAL_IDENTITY_INVALID")
    if product_manifest.get("generation_authorized") is not False:
        errors.append("TOPOLOGY_MANIFEST_GENERATION_GATE_NOT_CLOSED")
    manifest_evidence = product_manifest.get("evidence", {})
    transition = preflight.get("artifact_transition", {})
    if (transition.get("status") != "CANDIDATE_DIAGNOSTIC_ONLY"
            or transition.get("generation_authorized") is not False
            or transition.get("product_certification") != "NOT_PERFORMED"
            or transition.get("product_manifest_sha256") != hashes["product_manifest"]
            or transition.get("current_contract_sha256") != contract_hash
            or transition.get("historical_contract_sha256") != manifest_evidence.get("contract_sha256")):
        errors.append("ARTIFACT_TRANSITION_BINDING_INVALID")
    for source_name in ("geometry", "population"):
        if manifest_evidence.get("source_binding", {}).get(source_name) != source_binding.get(source_name):
            errors.append(f"TOPOLOGY_MANIFEST_{source_name.upper()}_BINDING_MISMATCH")
    artifact = product_manifest.get("artifacts", {}).get(f"unidades/{cpro}.json.gz")
    if not isinstance(artifact, dict) or artifact.get("sha256") != hashes["unit_product"]:
        errors.append("UNIT_PRODUCT_MANIFEST_HASH_MISMATCH")
    if artifact and artifact.get("canonical_json_sha256") != canonical_sha256(unit):
        errors.append("UNIT_PRODUCT_CANONICAL_HASH_MISMATCH")
    if unit.get("run_binding") != product_manifest.get("run_binding"):
        errors.append("UNIT_PRODUCT_RUN_BINDING_MISMATCH")

    quotas = contract.get("quotas_by_origin_unit")
    quota_rows = [row for row in quotas or [] if isinstance(row, dict) and row.get("code") == cpro]
    if (not isinstance(quotas, list)
            or sorted(row.get("code") for row in quotas if isinstance(row, dict)) != [f"{n:02d}" for n in range(1, 53)]
            or any(type(row.get("k")) is not int or row["k"] < 1 for row in quotas if isinstance(row, dict))
            or sum(row.get("k", 0) for row in quotas if isinstance(row, dict) and type(row.get("k")) is int) != 407):
        errors.append("CONTRACT_NATIONAL_QUOTA_COVERAGE_INVALID")
    if len(quota_rows) != 1 or type(quota_rows[0].get("k")) is not int:
        errors.append("CONTRACT_K_QUOTA_MISSING_OR_DUPLICATE")
        k = None
    else:
        k = quota_rows[0]["k"]
    policy = contract.get("decisions", {}).get("population_limits", {})
    if (policy.get("status") != "APPROVED"
            or policy.get("decision_id") != N08_OWNER_DECISION_ID
            or policy.get("value") != {
                "population_floor_ratio": 0.85,
                "population_cap_ratio": 1.15,
                "target_tolerance_ratio": 0.15,
            }):
        errors.append("APPROVED_POPULATION_POLICY_NOT_BOUND")
    required_policies = {
        "minimum_unit": "official_2025_CUSEC_indivisible",
        "contiguity": "positive_line_shared_boundary_on_original_polygon_parts",
        "municipal_indivisibility": "preserve_when_feasible_split_by_whole_CUSEC_when_necessary",
    }
    for policy_name, expected_value in required_policies.items():
        decision = contract.get("decisions", {}).get(policy_name, {})
        if (decision.get("status") != "APPROVED"
                or decision.get("decision_id") != N08_OWNER_DECISION_ID
                or decision.get("value") != expected_value):
            errors.append(f"CONTRACT_POLICY_NOT_OWNER_APPROVED:{policy_name}")
    if contract.get("accreditation", {}).get("generation_authorized") is not False:
        errors.append("GENERATION_GATE_NOT_CLOSED")
    if (contract.get("k_decision", {}).get("status") != "APPROVED_BY_OWNER"
            or contract.get("k_decision", {}).get("total") != 407
            or contract.get("k_decision", {}).get("quota_method") != "max(1,(P_i+60000)//120000); nearest_half_up_independent; reference_2025"):
        errors.append("K_DECISION_NOT_OWNER_APPROVED")
    modules = preflight.get("modules", {})
    if any(modules.get(name, {}).get("status") != "PASS" for name in ("M01", "M02", "M03")):
        errors.append("M01_M03_INPUT_GATES_NOT_PASS")
    if preflight.get("generation_authorized") is not False or preflight.get("districts_generated") != 0:
        errors.append("PREFLIGHT_GENERATION_GATE_NOT_CLOSED")
    if source_evidence.get("geometry_operations") != "none; no CRS transform, buffer, simplify, repair or precision rounding in physical graph":
        errors.append("PHYSICAL_GRAPH_OPERATIONS_NOT_BOUND")

    summary = unit.get("summary", {})
    nodes = unit.get("nodes")
    edges = unit.get("edges")
    part_components = unit.get("polygon_part_components")
    inputs = preflight.get("inputs", {})
    if not isinstance(nodes, list) or not isinstance(edges, list) or not isinstance(part_components, list):
        errors.append("PRODUCT_TOPOLOGY_FIELDS_INVALID")
        nodes, edges, part_components = [], [], []
    ids = [node.get("CUSEC") for node in nodes if isinstance(node, dict)]
    if len(ids) != len(nodes) or len(set(ids)) != len(ids) or any(not isinstance(x, str) for x in ids):
        errors.append("CUSEC_IDENTITY_INVALID_OR_DUPLICATED")
    if any(node.get("CPRO") != cpro or node.get("id") != node.get("CUSEC") for node in nodes):
        errors.append("NODE_ADMIN_IDENTITY_MISMATCH")
    ids = sorted(ids)
    pops = [node.get("POB_2025") for node in nodes]
    if any(type(pop) is not int or pop < 0 for pop in pops):
        errors.append("NODE_POPULATION_INVALID")
    population = sum(pop for pop in pops if type(pop) is int)
    if summary.get("CPRO") != cpro or summary.get("sections") != len(nodes):
        errors.append("PRODUCT_SUMMARY_NODE_COVERAGE_MISMATCH")
    if summary.get("population") != population or inputs.get("population") != population:
        errors.append("POPULATION_TOTAL_MISMATCH")
    if inputs.get("sections") != len(nodes) or inputs.get("physical_edges") != len(edges):
        errors.append("PREFLIGHT_TOPOLOGY_COVERAGE_MISMATCH")
    if summary.get("edges") != len(edges):
        errors.append("PRODUCT_EDGE_COUNT_MISMATCH")
    if inputs.get("k_approved") != k or summary.get("k") != k:
        errors.append("PREFLIGHT_CONTRACT_K_MISMATCH")
    geometry_sha = contract.get("sources", {}).get("geometry", {}).get("sha256")
    if any(node.get("source_geometry_sha256") != geometry_sha for node in nodes):
        errors.append("NODE_GEOMETRY_SOURCE_HASH_MISMATCH")

    # The product's part-component inventory must account for each original
    # polygon part exactly once. It is kept distinct from CUSEC identity.
    component_ids = [component.get("id") for component in part_components if isinstance(component, dict)]
    if len(component_ids) != len(part_components) or len(set(component_ids)) != len(component_ids):
        errors.append("PHYSICAL_PART_COMPONENT_ID_INVALID")
    if any(not isinstance(component.get("parts"), list) for component in part_components if isinstance(component, dict)):
        errors.append("PHYSICAL_PART_COMPONENT_PART_LIST_INVALID")
    inventoried_parts = [part for component in part_components if isinstance(component, dict)
                         for part in component.get("parts", []) if isinstance(component.get("parts"), list)]
    part_cusecs = [part.split(":", 1)[0] for part in inventoried_parts if isinstance(part, str) and ":" in part]
    if (len(inventoried_parts) != summary.get("polygon_parts")
            or len(set(inventoried_parts)) != len(inventoried_parts)
            or len(part_cusecs) != len(inventoried_parts)
            or set(part_cusecs) != set(ids)):
        errors.append("PHYSICAL_PART_COVERAGE_MISMATCH")
    if len(part_components) != summary.get("physical_part_components"):
        errors.append("PHYSICAL_PART_COMPONENT_COUNT_MISMATCH")
    component_by_part = {
        part: component.get("id") for component in part_components for part in component.get("parts", [])
    }
    for node in nodes:
        expected_component_ids = sorted({component_by_part.get(part) for part, cusec in zip(inventoried_parts, part_cusecs) if cusec == node.get("CUSEC")})
        if sorted(node.get("physical_part_components", [])) != expected_component_ids:
            errors.append("NODE_PHYSICAL_COMPONENT_BINDING_MISMATCH")

    adjacency = {node_id: set() for node_id in ids}
    accepted_edges: set[tuple[str, str]] = set()
    for edge in edges:
        if not isinstance(edge, dict):
            errors.append("EDGE_RECORD_INVALID")
            continue
        left, right = edge.get("u"), edge.get("v")
        if (left not in adjacency or right not in adjacency or left == right
                or edge.get("edge_type") != "geometric"
                or edge.get("kind") != "linear"
                or not isinstance(edge.get("shared_border_m"), (int, float))
                or isinstance(edge.get("shared_border_m"), bool)
                or not math.isfinite(edge.get("shared_border_m", 0))
                or edge.get("shared_border_m", 0) <= 0
                or not isinstance(edge.get("overlap_m2"), (int, float))
                or isinstance(edge.get("overlap_m2"), bool)
                or not math.isfinite(edge.get("overlap_m2", float("nan")))
                or edge.get("overlap_m2") != 0
                or not isinstance(edge.get("contact_sha256"), str)
                or len(edge.get("contact_sha256", "")) != 64
                or any(char not in "0123456789abcdef" for char in edge.get("contact_sha256", ""))):
            errors.append("EDGE_NOT_VALID_POSITIVE_LINEAR_CONTACT")
            continue
        pair = tuple(sorted((left, right)))
        if pair in accepted_edges:
            errors.append("DUPLICATE_PHYSICAL_EDGE")
        accepted_edges.add(pair)
        adjacency[left].add(right)
        adjacency[right].add(left)
    if len(accepted_edges) != len(edges):
        errors.append("EDGE_ACCEPTANCE_COUNT_MISMATCH")

    def component_count(graph: dict[str, set[str]]) -> int:
        if not graph:
            return 0
        unseen = set(graph)
        components = 0
        while unseen:
            components += 1
            start = min(unseen)
            unseen.remove(start)
            stack = [start]
            while stack:
                node = stack.pop()
                reached = graph[node] & unseen
                unseen.difference_update(reached)
                stack.extend(reached)
        return components

    actual_section_components = component_count(adjacency)
    section_connected = actual_section_components == 1
    part_connected = len(part_components) == 1 and len(inventoried_parts) > 0
    if summary.get("section_graph_components") != actual_section_components:
        errors.append("SECTION_GRAPH_COMPONENTS_MISMATCH")
    if summary.get("physical_part_components") != len(part_components):
        errors.append("PHYSICAL_PART_COMPONENTS_MISMATCH")
    external_boundary = summary.get("external_gap_accreditation")
    unresolved_exceptions = bool(
        summary.get("discontinuous_municipalities")
        or summary.get("multipart_sections_spanning_physical_components")
        or summary.get("isolated_sections")
    )
    territory_evidence = "INSUFFICIENT_EVIDENCE"

    floor = cap = None
    if k and k > 0:
        floor = (17 * population + 20 * k - 1) // (20 * k)
        cap = (23 * population) // (20 * k)
    base = {
        "schema": "ddd.congress-conditional-witness/1.0",
        "province": cpro,
        "input_sha256": hashes,
        "product_run_binding": product_manifest.get("run_binding"),
        "sections": len(nodes),
        "population": population,
        "k": k,
        "floor": floor,
        "cap": cap,
        "section_graph_connected": section_connected,
        "physical_part_graph_connected": part_connected,
        "external_boundary_accreditation": external_boundary,
        "unresolved_exception_indicators": unresolved_exceptions,
        "territorial_factibility_status": territory_evidence,
        "generation_authorized": False,
        "districts_generated": 0,
        "product_certification": "NOT_PERFORMED",
        "errors": sorted(set(errors)),
    }
    if errors:
        return {**base, "diagnostic_status": "INSUFFICIENT_EVIDENCE", "assignment": []}
    if k is not None and len(part_components) > k:
        return {**base, "diagnostic_status": "NECESSARY_CONDITION_FAILED_CONDITIONAL", "assignment": [],
                "condition": "PHYSICAL_PART_COMPONENTS_EXCEED_K_IN_SOURCE_PRODUCT"}
    if k != 1:
        return {**base, "diagnostic_status": "SEARCH_NOT_RUN", "assignment": []}
    if not section_connected or not part_connected:
        return {**base, "diagnostic_status": "INSUFFICIENT_EVIDENCE", "assignment": []}
    if not floor <= population <= cap:
        return {**base, "diagnostic_status": "NECESSARY_CONDITION_FAILED_CONDITIONAL", "assignment": [],
                "condition": "SINGLE_DISTRICT_POPULATION_OUTSIDE_APPROVED_BOUNDS"}
    assignment = [{"CUSEC": node_id, "district_id": "01"} for node_id in sorted(ids)]
    if external_boundary == "ACCREDITED" and not unresolved_exceptions:
        territory_evidence = "CONDITIONAL_WITNESS_ONLY"
    return {
        **base,
        "territorial_factibility_status": territory_evidence,
        "diagnostic_status": "WITNESS_FOUND_CONDITIONAL",
        "assignment": assignment,
        "assignment_sha256": canonical_sha256(assignment),
        "witness_scope": "single connected bounded group over the listed source-product CUSECs and edges only",
    }


def evaluate_national_batch(
    *, preflight_root: Path, product_root: Path, contract_path: Path,
    output_path: Path | None = None,
) -> dict[str, Any]:
    manifest_path = product_root / "manifest.json"
    results = []
    for number in range(1, 53):
        cpro = f"{number:02d}"
        # Support the established single-province layout and the resumable
        # campaign runner's numeric per-province layout.
        folder = preflight_root / f"PREFLIGHT_CPRO{cpro}"
        if not folder.exists():
            folder = preflight_root / cpro
        results.append(evaluate_unit(
            preflight_path=folder / "PREFLIGHT.json",
            checkpoint_path=folder / "CHECKPOINT.json",
            unit_path=product_root / "unidades" / f"{cpro}.json.gz",
            product_manifest_path=manifest_path,
            contract_path=contract_path,
        ))
    report = {
        "schema": "ddd.congress-conditional-witness-batch/1.0",
        "results": results,
        "counts": {status: sum(row["diagnostic_status"] == status for row in results)
                   for status in sorted({row["diagnostic_status"] for row in results})},
        "generation_authorized": False,
        "districts_generated": 0,
        "product_certification": "NOT_PERFORMED",
    }
    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--preflight-root", required=True, type=Path)
    parser.add_argument("--product-root", required=True, type=Path)
    parser.add_argument("--contract", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    report = evaluate_national_batch(
        preflight_root=args.preflight_root, product_root=args.product_root,
        contract_path=args.contract, output_path=args.output,
    )
    print(json.dumps(report["counts"], sort_keys=True))
    return 2 if any(row["errors"] for row in report["results"]) else 0


if __name__ == "__main__":
    raise SystemExit(main())
