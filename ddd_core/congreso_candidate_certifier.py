#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Versión 0.1.0; certificador independiente de candidatos Congreso; 2026-10-13.

Scope: validate a CUSEC-to-district candidate independently from M05 and the
partition generator. It accepts explicitly marked synthetic fixtures for
diagnostic tests. Only a complete, source-bound 2025 national candidate may
receive PRODUCT_CERTIFIED; certification never authorizes generation.

Multipart sections and case exceptions fail closed because the current
Congress contract approves only the general rule, not nominal exceptions.
Municipal splits are independently checked with bounded exhaustive search;
the proof is conditional on other CUSECs remaining fixed. Search exhaustion
is NOT_CERTIFIABLE, never proof of necessity. Changes/motivo: gate de candidato
fail-closed para pruebas y productos nacionales fuente-vinculados. Origin: new,
no predecessor.
"""
from __future__ import annotations

from collections import defaultdict, deque
import hashlib
import csv
import gzip
import json
import math
import re
from itertools import combinations
from pathlib import Path
from typing import Any, Mapping, Sequence

from ddd_core.congreso_contract import validate_congress_identity
from ddd_core.congreso_product_manifest import validate_candidate_manifest


VERSION = "0.1.0"
SCHEMA = "ddd.congreso-candidate-certification/0.1"
NATIONAL_SECTIONS = 36554
NATIONAL_POPULATION = 49128297
NATIONAL_K = 407
SHA256 = re.compile(r"[0-9a-f]{64}\Z")
CUSEC = re.compile(r"[0-9]{10}\Z")
PROVINCES = tuple(f"{i:02d}" for i in range(1, 53))
SOURCE_ROLES = ("geometry", "population")
DECISION_K_ID = "N06-OWNER-20261012-K"
N08_DECISION_ID = "N08-OWNER-20261013-7RULES"
N08_POLICY_KEYS = (
    "minimum_unit", "contiguity", "population_limits", "municipal_indivisibility",
    "islands", "enclaves", "physical_discontinuities",
)
# Independent trust anchors for the checked-in N08 delivery and INE 2025
# source manifest. A candidate cannot nominate its own topology hash.
N08_DELIVERY_MANIFEST_SHA256 = "0744fcaed562b5ff9b0c22acbeebebea238ec84416b5dc54733624f2202b6e33"
INE_SOURCE_MANIFEST_SHA256 = "f99e1690071b6383d90094b35fe024865d5bc75ef95983014452d1d25dbadc37"
N08_TOPOLOGY_SCHEMA = "ddd.congress-topology-diagnostic/1.0"


class _Reject(ValueError):
    pass


def _require(condition: bool, reason: str) -> None:
    if not condition:
        raise _Reject(reason)


def _canonical(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":"), allow_nan=False).encode("utf-8")


def _sha(value: Any) -> str:
    return hashlib.sha256(_canonical(value)).hexdigest()


def _file_sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _anchored_file(root: Path, relative: str, expected_sha: str) -> Path:
    path = (root / relative).resolve(strict=True)
    _require(path.is_relative_to(root.resolve()), "TRUSTED_EVIDENCE_PATH_ESCAPES_ROOT")
    _require(path.is_file() and _file_sha(path) == expected_sha,
             "TRUSTED_EVIDENCE_HASH_MISMATCH:" + relative)
    return path


def _trusted_evidence(root_value: Any, contract: Mapping[str, Any]) -> dict[str, Any]:
    """Load only source/topology artifacts pinned by repository trust anchors."""
    _require(isinstance(root_value, (str, Path)), "TRUSTED_EVIDENCE_ROOT_REQUIRED")
    root = Path(root_value).resolve(strict=True)
    delivery_rel = "docs/ESTUDIOS/N08_TOPOLOGIA_NACIONAL_20251012/MANIFEST_ENTREGA.json"
    delivery_path = _anchored_file(root, delivery_rel, N08_DELIVERY_MANIFEST_SHA256)
    delivery = json.loads(delivery_path.read_text(encoding="utf-8"))
    file_entries = delivery.get("files_sha256")
    _require(isinstance(file_entries, Mapping) and len(file_entries) == 74,
             "N08_DELIVERY_MANIFEST_INVALID")
    # Verify every listed delivery object, not just the topology products used
    # below, so the manifest acts as the complete historical evidence anchor.
    delivery_base = delivery_path.parent.resolve()
    for relative, expected in file_entries.items():
        _require(isinstance(relative, str) and isinstance(expected, str)
                 and SHA256.fullmatch(expected) is not None,
                 "N08_DELIVERY_ENTRY_INVALID")
        _anchored_file(delivery_base, relative, expected)

    product_rel = "docs/ESTUDIOS/N08_TOPOLOGIA_NACIONAL_20251012/producto/manifest.json"
    product_path = delivery_base / "producto/manifest.json"
    product_hash = file_entries.get("producto/manifest.json")
    _require(isinstance(product_hash, str), "N08_TOPOLOGY_MANIFEST_UNPINNED")
    _require(_file_sha(product_path) == product_hash, "N08_TOPOLOGY_MANIFEST_HASH_MISMATCH")
    topology = json.loads(product_path.read_text(encoding="utf-8"))
    identity_body = dict(topology)
    claimed_identity = identity_body.pop("identity_sha256", None)
    _require(topology.get("schema") == N08_TOPOLOGY_SCHEMA
             and claimed_identity == _sha(identity_body),
             "N08_TOPOLOGY_MANIFEST_IDENTITY_INVALID")
    _require(topology.get("generation_authorized") is False,
             "N08_TOPOLOGY_GENERATION_FLAG_INVALID")
    topology_gate = topology.get("gates", {}).get("A_topological_integrity")
    _require(topology_gate in {"PASS", "BLOCKED", "NOT_EVIDENCED"},
             "NATIONAL_TOPOLOGY_GATE_INVALID")
    bound = topology.get("evidence", {}).get("source_binding")

    source_rel = "territorios/congreso/fuentes/ine_2025_2025/manifest.json"
    source_path = _anchored_file(root, source_rel, INE_SOURCE_MANIFEST_SHA256)
    source_manifest = json.loads(source_path.read_text(encoding="utf-8"))
    sources = contract.get("sources", {})
    for role in SOURCE_ROLES:
        source = sources.get(role, {})
        topo_source = bound.get(role, {}) if isinstance(bound, Mapping) else {}
        manifest_source = source_manifest.get("sources", {}).get(role, {})
        _require(source.get("edition") == 2025 and source.get("year") == 2025
                 and source.get("sha256") == manifest_source.get("sha256")
                 and topo_source.get("edition") == 2025
                 and topo_source.get("sha256") == source.get("sha256"),
                 "TRUSTED_SOURCE_BINDING_MISMATCH:" + role)

    base = source_path.parent
    population = source_manifest.get("outputs", {}).get("poblacion_por_seccion_2025.csv", {})
    crosswalk = source_manifest.get("crosswalk", {})
    population_path = _anchored_file(
        base, "poblacion_por_seccion_2025.csv", population.get("sha256", ""))
    crosswalk_path = _anchored_file(base, crosswalk.get("path", ""), crosswalk.get("sha256", ""))
    source_rows: dict[str, dict[str, Any]] = {}
    with population_path.open(encoding="utf-8-sig", newline="") as stream:
        for row in csv.DictReader(stream):
            ident = row.get("CUSEC")
            _require(isinstance(ident, str) and ident not in source_rows,
                     "TRUSTED_SOURCE_CUSEC_DUPLICATE")
            source_rows[ident] = {**row, "pop": int(row["POB_2025"])}
    crosswalk_rows: dict[str, dict[str, str]] = {}
    with crosswalk_path.open(encoding="utf-8-sig", newline="") as stream:
        for row in csv.DictReader(stream):
            ident = row.get("CUSEC")
            _require(isinstance(ident, str) and ident not in crosswalk_rows,
                     "TRUSTED_CROSSWALK_CUSEC_DUPLICATE")
            crosswalk_rows[ident] = row
    _require(set(source_rows) == set(crosswalk_rows) == set(topology.get("inventory_cusec", []))
             if isinstance(topology.get("inventory_cusec"), list)
             else len(source_rows) == NATIONAL_SECTIONS and len(crosswalk_rows) == NATIONAL_SECTIONS,
             "TRUSTED_SOURCE_COVERAGE_MISMATCH")

    units = {}
    topology_root = delivery_base / "producto"
    for code in PROVINCES:
        relative = f"unidades/{code}.json.gz"
        descriptor = topology.get("artifacts", {}).get(relative)
        _require(isinstance(descriptor, Mapping), "N08_UNIT_ARTIFACT_UNPINNED:" + code)
        unit_path = topology_root / relative
        _require(_file_sha(unit_path) == descriptor.get("sha256")
                 and _file_sha(unit_path) == file_entries.get("producto/" + relative),
                 "N08_UNIT_ARTIFACT_HASH_MISMATCH:" + code)
        raw = gzip.decompress(unit_path.read_bytes())
        unit = json.loads(raw)
        _require(raw == _canonical(unit) + b"\n"
                 and hashlib.sha256(raw).hexdigest() == descriptor.get("canonical_json_sha256"),
                 "N08_UNIT_CANONICAL_HASH_MISMATCH:" + code)
        _require(unit.get("summary", {}).get("CPRO") == code,
                 "N08_UNIT_IDENTITY_MISMATCH:" + code)
        units[code] = unit
    return {"topology": topology, "units": units, "source_rows": source_rows,
            "crosswalk_rows": crosswalk_rows, "topology_manifest_sha256": product_hash,
            "topology_gate": topology_gate,
            "delivery_manifest_sha256": N08_DELIVERY_MANIFEST_SHA256,
            "source_manifest_sha256": INE_SOURCE_MANIFEST_SHA256}


def _verify_against_trusted(nodes: Sequence[Mapping[str, Any]], edges: Sequence[Mapping[str, Any]],
                            trusted: Mapping[str, Any]) -> None:
    expected_nodes: dict[str, Mapping[str, Any]] = {}
    expected_edges: dict[str, Mapping[str, Any]] = {}
    for province, unit in trusted["units"].items():
        for node in unit.get("nodes", []):
            ident = node.get("CUSEC")
            _require(ident not in expected_nodes, "TRUSTED_TOPOLOGY_CUSEC_DUPLICATE")
            expected_nodes[ident] = node
        for edge in unit.get("edges", []):
            pair = "|".join(sorted((edge["u"], edge["v"])))
            _require(pair not in expected_edges, "TRUSTED_TOPOLOGY_EDGE_DUPLICATE")
            expected_edges[pair] = edge
    _require(set(expected_nodes) == set(trusted["source_rows"]),
             "TRUSTED_TOPOLOGY_SOURCE_COVERAGE_MISMATCH")
    supplied = {row["id"]: row for row in nodes}
    _require(set(supplied) == set(expected_nodes), "CANDIDATE_CUSEC_TRUST_MISMATCH")
    for ident, candidate in supplied.items():
        original = expected_nodes[ident]
        source_row = trusted["source_rows"][ident]
        crosswalk_row = trusted["crosswalk_rows"][ident]
        expected_cumun = source_row["CUMUN"]
        expected_cpro = source_row["CPRO"]
        _require(candidate.get("CPRO") == expected_cpro == original.get("CPRO")
                 and candidate.get("CUMUN") == expected_cumun == original.get("CUMUN")
                 and candidate.get("pop") == source_row["pop"] == original.get("POB_2025")
                 and crosswalk_row.get("CUSEC") == ident
                 and crosswalk_row.get("CUMUN") == expected_cumun
                 and crosswalk_row.get("CPRO") == expected_cpro,
                 "CANDIDATE_ADMIN_OR_POPULATION_TRUST_MISMATCH:" + ident)
        _require(candidate.get("geometry_sha256") == original.get("geometry_sha256")
                 and candidate.get("source_geometry_sha256") == original.get("source_geometry_sha256"),
                 "CANDIDATE_GEOMETRY_HASH_TRUST_MISMATCH:" + ident)
        trusted_parts = original.get("physical_part_components")
        candidate_parts = candidate.get("physical_parts", [])
        _require(isinstance(trusted_parts, list)
                 and [part.get("id") for part in candidate_parts] == trusted_parts
                 and all(part.get("physical_component") == original.get("physical_component")
                         for part in candidate_parts),
                 "CANDIDATE_PHYSICAL_PARTS_TRUST_MISMATCH:" + ident)
        if len(trusted_parts) == 1:
            _require(candidate_parts[0].get("geometry_sha256") == original.get("geometry_sha256"),
                     "CANDIDATE_PART_GEOMETRY_HASH_TRUST_MISMATCH:" + ident)

    supplied_edges = {"|".join(sorted((row["u"], row["v"]))): row for row in edges}
    _require(set(supplied_edges) == set(expected_edges), "CANDIDATE_EDGE_SET_TRUST_MISMATCH")
    for pair, candidate in supplied_edges.items():
        original = expected_edges[pair]
        for field in ("shared_border_m", "overlap_m2", "contact_sha256", "edge_type"):
            _require(candidate.get(field) == original.get(field),
                     "CANDIDATE_EDGE_EVIDENCE_TRUST_MISMATCH:" + pair)


def _require_product_gates(trusted: Mapping[str, Any], splits: Sequence[Mapping[str, Any]]) -> None:
    _require(trusted.get("topology_gate") == "PASS", "NATIONAL_TOPOLOGY_GATE_BLOCKED")
    for split in splits:
        _require(split.get("proof", {}).get("method") == "POPULATION_CAP_LOWER_BOUND",
                 "MUNICIPAL_SPLIT_PROOF_SCOPE_INSUFFICIENT")


def _ceil_ratio(numerator: int, denominator: int) -> int:
    return (numerator + denominator - 1) // denominator


def _contract_inputs(contract: Mapping[str, Any], source_binding: Mapping[str, Any]) -> dict[str, Any]:
    try:
        identity = validate_congress_identity(contract)
    except (TypeError, ValueError) as exc:
        raise _Reject("CONGRESS_CONTRACT_INVALID") from exc
    _require(contract.get("accreditation", {}).get("generation_authorized") is False,
             "GENERATION_AUTHORIZATION_MUST_REMAIN_FALSE")
    decisions = contract.get("decisions")
    _require(isinstance(decisions, Mapping), "CONTRACT_DECISIONS_MISSING")
    for name in N08_POLICY_KEYS:
        decision = decisions.get(name)
        _require(isinstance(decision, Mapping)
                 and decision.get("status") == "APPROVED"
                 and decision.get("decision_id") == N08_DECISION_ID,
                 "APPROVED_N08_POLICY_REQUIRED:" + name)
    population_reference = decisions.get("population_reference")
    _require(isinstance(population_reference, Mapping)
             and population_reference.get("status") == "APPROVED"
             and population_reference.get("decision_id") == DECISION_K_ID
             and population_reference.get("value") == 2025,
             "APPROVED_2025_POPULATION_REFERENCE_REQUIRED")
    k_decision = contract.get("k_decision")
    _require(isinstance(k_decision, Mapping)
             and k_decision.get("status") == "APPROVED_BY_OWNER"
             and k_decision.get("decision_id") == DECISION_K_ID
             and k_decision.get("source_scope") == "congreso"
             and isinstance(k_decision.get("quota_method"), str)
             and k_decision["quota_method"].startswith("max(1,(P_i+60000)//120000)")
             and type(k_decision.get("total")) is int
             and k_decision["total"] == NATIONAL_K,
             "APPROVED_K_407_REQUIRED")
    barriers = contract.get("barriers")
    _require(isinstance(barriers, Mapping)
             and barriers.get("province_circumscription") == "hard"
             and barriers.get("ceuta_melilla_separate") is True
             and barriers.get("cross_circumscription_edges") is False,
             "CONGRESS_PROVINCIAL_BARRIERS_REQUIRED")
    sources = contract.get("sources")
    _require(isinstance(sources, Mapping), "CONTRACT_SOURCES_MISSING")
    for role in SOURCE_ROLES:
        source = sources.get(role)
        bound = source_binding.get(role) if isinstance(source_binding, Mapping) else None
        _require(isinstance(source, Mapping)
                 and source.get("accreditation") == "ACCREDITED"
                 and source.get("edition") == 2025
                 and source.get("year") == 2025
                 and isinstance(source.get("sha256"), str)
                 and SHA256.fullmatch(source["sha256"]) is not None,
                 "ACCREDITED_2025_SOURCE_REQUIRED:" + role)
        _require(isinstance(bound, Mapping)
                 and bound.get("edition") == 2025
                 and bound.get("sha256") == source["sha256"],
                 "SOURCE_BINDING_MISMATCH:" + role)
    quotas = contract.get("quotas_by_origin_unit", contract.get("quotas_by_circumscription"))
    _require(isinstance(quotas, list) and len(quotas) == 52,
             "CONTRACT_QUOTAS_52_REQUIRED")
    quota_map: dict[str, int] = {}
    for row in quotas:
        _require(isinstance(row, Mapping) and set(row) == {"code", "k"}
                 and row.get("code") in PROVINCES
                 and type(row.get("k")) is int and row["k"] > 0,
                 "CONTRACT_QUOTA_INVALID")
        _require(row["code"] not in quota_map, "CONTRACT_QUOTA_DUPLICATE")
        quota_map[row["code"]] = row["k"]
    _require(set(quota_map) == set(PROVINCES) and sum(quota_map.values()) == NATIONAL_K,
             "CONTRACT_QUOTAS_INVALID")
    return {"identity": identity, "sources": sources, "quotas": quota_map}


def _validate_nodes(nodes: Sequence[Mapping[str, Any]], sources: Mapping[str, Any]) -> dict[str, Mapping[str, Any]]:
    _require(isinstance(nodes, (list, tuple)) and bool(nodes), "CANDIDATE_NODES_EMPTY")
    by_id: dict[str, Mapping[str, Any]] = {}
    for node in nodes:
        _require(isinstance(node, Mapping), "NODE_INVALID")
        ident = node.get("id")
        province, municipality = node.get("CPRO"), node.get("CUMUN")
        _require(isinstance(ident, str) and CUSEC.fullmatch(ident) is not None,
                 "CUSEC_INVALID")
        _require(ident not in by_id, "CUSEC_DUPLICATE")
        _require(province in PROVINCES and ident[:2] == province
                 and isinstance(municipality, str) and re.fullmatch(r"[0-9]{5}", municipality)
                 and ident[:5] == municipality,
                 "CUSEC_CPRO_CUMUN_IDENTITY_MISMATCH")
        _require(type(node.get("pop")) is int and node["pop"] >= 0,
                 "SECTION_POPULATION_INVALID")
        _require(isinstance(node.get("geometry_sha256"), str)
                 and SHA256.fullmatch(node["geometry_sha256"]) is not None,
                 "SECTION_GEOMETRY_HASH_INVALID")
        _require(node.get("source_geometry_sha256") == sources["geometry"]["sha256"],
                 "SECTION_SOURCE_GEOMETRY_HASH_MISMATCH")
        parts = node.get("physical_parts")
        _require(isinstance(parts, list) and bool(parts), "PHYSICAL_PARTS_MISSING")
        part_ids = set()
        for part in parts:
            _require(isinstance(part, Mapping)
                     and isinstance(part.get("id"), str) and part["id"]
                     and part["id"].startswith(ident + ":p")
                     and part["id"] not in part_ids
                     and isinstance(part.get("geometry_sha256"), str)
                     and SHA256.fullmatch(part["geometry_sha256"]) is not None
                     and isinstance(part.get("physical_component"), str)
                     and part["physical_component"], "PHYSICAL_PART_EVIDENCE_INVALID")
            part_ids.add(part["id"])
        # The approved contract contains only a general exception process and
        # explicitly no nominal cases. Never infer a passage across parts.
        _require(len(parts) == 1, "MULTIPART_NOMINAL_EXCEPTION_NOT_APPROVED")
        by_id[ident] = node
    return by_id


def _validate_edges(edges: Sequence[Mapping[str, Any]], nodes: Mapping[str, Mapping[str, Any]]):
    _require(isinstance(edges, (list, tuple)), "CANDIDATE_EDGES_INVALID")
    adjacency = {ident: set() for ident in nodes}
    pairs = set()
    for edge in edges:
        _require(isinstance(edge, Mapping), "EDGE_INVALID")
        u, v = edge.get("u"), edge.get("v")
        _require(u in nodes and v in nodes and u != v, "EDGE_ENDPOINT_INVALID")
        pair = tuple(sorted((u, v)))
        _require(pair not in pairs, "EDGE_DUPLICATE_OR_ASYMMETRIC")
        pairs.add(pair)
        _require(nodes[u]["CPRO"] == nodes[v]["CPRO"], "EDGE_CROSSES_PROVINCES")
        length, overlap = edge.get("shared_border_m"), edge.get("overlap_m2")
        _require(type(length) in (int, float) and math.isfinite(length) and length > 0,
                 "EDGE_NOT_POSITIVE_LINEAR_BOUNDARY")
        _require(type(overlap) in (int, float) and math.isfinite(overlap) and overlap == 0,
                 "EDGE_OVERLAP_NOT_ALLOWED")
        _require(edge.get("edge_type") == "geometric", "EDGE_NOT_GEOMETRIC")
        contact_hash = edge.get("contact_sha256")
        _require(isinstance(contact_hash, str) and SHA256.fullmatch(contact_hash) is not None,
                 "EDGE_CONTACT_EVIDENCE_HASH_INVALID")
        # Edge input uses a canonical undirected record. Build both arcs and
        # assert symmetry, so omission of the reverse neighbor cannot go unnoticed.
        adjacency[u].add(v)
        adjacency[v].add(u)
    _require(all(u in adjacency[v] and v in adjacency[u]
                 for u in adjacency for v in adjacency[u]), "EDGE_GRAPH_NOT_SYMMETRIC")
    return adjacency, len(pairs)


def _connected(members: set[str], adjacency: Mapping[str, set[str]]) -> bool:
    if not members:
        return False
    seen = {min(members)}
    queue = deque(seen)
    while queue:
        current = queue.popleft()
        for neighbor in adjacency[current] & members:
            if neighbor not in seen:
                seen.add(neighbor)
                queue.append(neighbor)
    return seen == members


def _district_bounds(population: int, quota: int) -> tuple[int, int]:
    denominator = 20 * quota
    return (_ceil_ratio(17 * population, denominator), (23 * population) // denominator)


def _prove_split_minimum(
    municipality: str,
    assignments: Mapping[str, str],
    nodes: Mapping[str, Mapping[str, Any]],
    adjacency: Mapping[str, set[str]],
    district_population: Mapping[str, int],
    floor: int,
    cap: int,
    *,
    node_budget: int,
) -> dict[str, Any]:
    """Independent bounded search; other CUSECs remain fixed by design."""
    members = sorted(ident for ident, row in nodes.items() if row["CUMUN"] == municipality)
    current_labels = {assignments[ident] for ident in members}
    total = sum(nodes[ident]["pop"] for ident in members)
    arithmetic_minimum = max(1, _ceil_ratio(total, cap))
    if len(current_labels) < arithmetic_minimum:
        return {"proven": False, "reason": "MUNICIPAL_SPLIT_BELOW_ARITHMETIC_MINIMUM"}
    if len(current_labels) == arithmetic_minimum:
        return {"proven": True, "method": "POPULATION_CAP_LOWER_BOUND",
                "minimum_districts": arithmetic_minimum}

    province = nodes[members[0]]["CPRO"]
    labels = sorted(d for d in district_population
                    if any(nodes[u]["CPRO"] == province and assignments[u] == d for u in nodes))
    fixed = {ident: district for ident, district in assignments.items() if ident not in members}
    fixed_population = defaultdict(int)
    for ident, district in fixed.items():
        fixed_population[district] += nodes[ident]["pop"]
    visits = 0

    def candidate_valid(target):
        populations = dict(fixed_population)
        trial = dict(fixed)
        trial.update(target)
        for ident, district in target.items():
            populations[district] = populations.get(district, 0) + nodes[ident]["pop"]
        if set(populations) != set(district_population):
            return False
        if any(populations.get(d, 0) < floor or populations.get(d, 0) > cap
               for d in district_population):
            return False
        return all(_connected({u for u, d in trial.items() if d == label}, adjacency)
                   for label in district_population)

    for count in range(arithmetic_minimum, len(current_labels)):
        for allowed_tuple in combinations(labels, count):
            allowed = set(allowed_tuple)
            if any(fixed_population.get(label, 0) > cap for label in allowed):
                continue
            target: dict[str, str] = {}

            def search(index: int) -> bool:
                nonlocal visits
                visits += 1
                if visits > node_budget:
                    raise OverflowError
                if index == len(members):
                    return len(set(target.values())) < len(current_labels) and candidate_valid(target)
                ident = members[index]
                for label in sorted(allowed):
                    if fixed_population.get(label, 0) + sum(
                        nodes[u]["pop"] for u, assigned in target.items() if assigned == label
                    ) + nodes[ident]["pop"] > cap:
                        continue
                    target[ident] = label
                    if search(index + 1):
                        return True
                    target.pop(ident)
                return False

            try:
                if search(0):
                    return {"proven": False, "reason": "MUNICIPAL_SPLIT_NOT_MINIMAL",
                            "smaller_feasible_count": count, "assignments_examined": visits}
            except OverflowError:
                return {"proven": False, "reason": "MUNICIPAL_MINIMALITY_SEARCH_EXHAUSTED",
                        "assignments_examined": visits, "node_budget": node_budget}
    return {"proven": True, "method": "BOUNDED_EXHAUSTIVE_FIXED_OTHER_CUSECS",
            "minimum_districts": len(current_labels), "assignments_examined": visits,
            "scope": "OTHER_CUSECS_FIXED"}


def _validate_assignments(
    assignments: Sequence[Mapping[str, Any]], nodes: Mapping[str, Mapping[str, Any]],
    adjacency: Mapping[str, set[str]], quotas: Mapping[str, int], *, node_budget: int,
) -> dict[str, Any]:
    _require(isinstance(assignments, (list, tuple)), "ASSIGNMENTS_INVALID")
    by_unit = {}
    district_nodes: dict[str, set[str]] = defaultdict(set)
    for row in assignments:
        _require(isinstance(row, Mapping) and set(row) == {"CUSEC", "district_id", "population"},
                 "ASSIGNMENT_ROW_INVALID")
        ident, district = row.get("CUSEC"), row.get("district_id")
        _require(ident in nodes and ident not in by_unit, "ASSIGNMENT_COVERAGE_OR_DUPLICATE")
        _require(type(row.get("population")) is int
                 and row["population"] == nodes[ident]["pop"],
                 "ASSIGNMENT_POPULATION_MISMATCH")
        _require(isinstance(district, str) and district.strip(), "DISTRICT_ID_INVALID")
        by_unit[ident] = district
        district_nodes[district].add(ident)
    _require(set(by_unit) == set(nodes), "ASSIGNMENT_COVERAGE_INCOMPLETE")

    district_province = {}
    for district, members in district_nodes.items():
        provinces = {nodes[ident]["CPRO"] for ident in members}
        _require(len(provinces) == 1, "DISTRICT_CROSSES_PROVINCES")
        district_province[district] = next(iter(provinces))
        _require(_connected(members, adjacency), "DISTRICT_NOT_PHYSICALLY_CONNECTED")

    by_province = defaultdict(list)
    for ident, node in nodes.items():
        by_province[node["CPRO"]].append(ident)
    province_populations, district_populations, bounds = {}, {}, {}
    for province, members in by_province.items():
        population = sum(nodes[ident]["pop"] for ident in members)
        quota = quotas[province]
        expected = max(1, (population + 60000) // 120000)
        _require(quota == expected, "PROVINCIAL_POPULATION_DOES_NOT_MATCH_CONTRACT_QUOTA")
        floor, cap = _district_bounds(population, quota)
        province_populations[province] = population
        bounds[province] = {"floor": floor, "cap": cap, "quota": quota}
        owned = [district for district, code in district_province.items() if code == province]
        _require(len(owned) == quota, "PROVINCIAL_DISTRICT_COUNT_MISMATCH")
        for district in owned:
            district_pop = sum(nodes[ident]["pop"] for ident in district_nodes[district])
            _require(floor <= district_pop <= cap, "DISTRICT_POPULATION_OUTSIDE_EXACT_BOUNDS")
            district_populations[district] = district_pop

    # The contract approves preservation when feasible, not arbitrary cuts.
    # A divided municipality must have a separately recomputed need proof.
    municipality_rows = defaultdict(list)
    for ident, node in nodes.items():
        municipality_rows[node["CUMUN"]].append(ident)
    municipal_splits = []
    for municipality, members in sorted(municipality_rows.items()):
        labels = {by_unit[ident] for ident in members}
        if len(labels) <= 1:
            continue
        proof = _prove_split_minimum(
            municipality, by_unit, nodes, adjacency, district_populations,
            bounds[nodes[members[0]]["CPRO"]]["floor"],
            bounds[nodes[members[0]]["CPRO"]]["cap"], node_budget=node_budget,
        )
        _require(proof.get("proven") is True, proof.get("reason", "MUNICIPAL_SPLIT_NOT_PROVEN"))
        municipal_splits.append({"CUMUN": municipality, "CUSEC": sorted(members),
                                 "districts": len(labels), "proof": proof})
    return {"districts": len(district_nodes), "district_populations": district_populations,
            "provincial_populations": province_populations, "population_bounds": bounds,
            "municipal_splits": municipal_splits}


def certify_candidate(
    contract: Mapping[str, Any],
    nodes: Sequence[Mapping[str, Any]],
    edges: Sequence[Mapping[str, Any]],
    assignments: Sequence[Mapping[str, Any]],
    source_binding: Mapping[str, Any],
    *,
    synthetic_fixture: bool = False,
    product_manifest: Mapping[str, Any] | None = None,
    trusted_evidence_root: str | Path | None = None,
    municipal_search_budget: int = 100000,
) -> dict[str, Any]:
    """Return diagnostic/certification result; never authorizes generation.

    Synthetic subsets must explicitly set ``synthetic_fixture=True`` and can
    only yield ``SYNTHETIC_DIAGNOSTIC_PASS``. A non-synthetic product must
    cover all 52 origin units, 36,554 CUSEC, 49,128,297 inhabitants and K=407,
    plus a hash-bound product manifest, before it can yield ``PRODUCT_CERTIFIED``.
    """
    result_base = {"schema": SCHEMA, "certifier_version": VERSION,
                   "generation_authorized": False}
    try:
        _require(type(synthetic_fixture) is bool, "SYNTHETIC_FIXTURE_FLAG_INVALID")
        _require(type(municipal_search_budget) is int and municipal_search_budget > 0,
                 "MUNICIPAL_SEARCH_BUDGET_INVALID")
        contract_info = _contract_inputs(contract, source_binding)
        by_id = _validate_nodes(nodes, contract_info["sources"])
        adjacency, edge_count = _validate_edges(edges, by_id)
        quotas = contract_info["quotas"]
        audited = _validate_assignments(assignments, by_id, adjacency, quotas,
                                        node_budget=municipal_search_budget)

        represented = {node["CPRO"] for node in by_id.values()}
        total_population = sum(row["pop"] for row in by_id.values())
        complete = (len(by_id) == NATIONAL_SECTIONS
                    and represented == set(PROVINCES)
                    and total_population == NATIONAL_POPULATION
                    and audited["districts"] == NATIONAL_K)
        _require(synthetic_fixture or complete,
                 "NATIONAL_PRODUCT_COVERAGE_REQUIRED_OR_MARK_FIXTURE_SYNTHETIC")

        product_digest = None
        if synthetic_fixture:
            _require(product_manifest is None, "SYNTHETIC_FIXTURE_CANNOT_BIND_PRODUCT_MANIFEST")
            status = "SYNTHETIC_DIAGNOSTIC_PASS"
        else:
            trusted = _trusted_evidence(trusted_evidence_root, contract)
            _verify_against_trusted(nodes, edges, trusted)
            _require_product_gates(trusted, audited["municipality_splits"])
            manifest = product_manifest
            _require(isinstance(manifest, Mapping), "PRODUCT_MANIFEST_REQUIRED")
            topology_sha = manifest.get("topology_manifest_sha256")
            _require(topology_sha == trusted["topology_manifest_sha256"],
                     "PRODUCT_TOPOLOGY_MANIFEST_HASH_UNTRUSTED")
            try:
                validate_candidate_manifest(
                    manifest, contract=contract, source_binding=source_binding,
                    nodes=nodes, edges=edges, assignments=assignments,
                    trusted_topology_manifest_sha256=trusted["topology_manifest_sha256"],
                )
            except ValueError as exc:
                _require(False, str(exc))
            product_digest = _sha(manifest)
            status = "PRODUCT_CERTIFIED"
        return {**result_base, "status": status, "product_manifest_sha256": product_digest,
                "units": len(by_id), "edges": edge_count,
                "population": total_population, "districts": audited["districts"],
                "district_populations": audited["district_populations"],
                "provincial_populations": audited["provincial_populations"],
                "population_bounds": audited["population_bounds"],
                "municipality_splits": audited["municipal_splits"],
                "contract_sha256": _sha(contract),
                "source_binding": dict(source_binding)}
    except _Reject as exc:
        return {**result_base, "status": "NOT_CERTIFIABLE", "blockers": [str(exc)]}
    except (KeyError, TypeError, ValueError, OverflowError) as exc:
        return {**result_base, "status": "NOT_CERTIFIABLE",
                "blockers": [f"MALFORMED_CANDIDATE:{type(exc).__name__}"]}

