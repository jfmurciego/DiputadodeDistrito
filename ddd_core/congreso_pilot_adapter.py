"""Version 1.1.0; 2026-10-26; physical evidence is not self-attesting.

Predecessor: legacy/nac_piloto_20261026/ddd_core/congreso_pilot_adapter.py.
No authorization, exception, tolerance or K is inferred here.
"""
from __future__ import annotations
from collections import defaultdict
import hashlib
import json
import math
from pathlib import Path

from ddd_core.congreso_contract import validate_congress_identity
from ddd_core.m05_population_repair import connected, verify_partition_constraints, MUNICIPAL_POLICY_N08

def canonical_sha(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest()

def assignment_witness_sha(state):
    payload = sorted(sorted(members) for members in groups(state).values())
    return hashlib.sha256(json.dumps(payload, separators=(",", ":")).encode()).hexdigest()

def model(unit, contract):
    identity = validate_congress_identity(contract)
    if identity["status"] != "STRUCTURAL_SCOPE_ADMITTED":
        raise ValueError("CONTRACT_INVALID")
    if identity["generation_authorized"] is not False or contract["accreditation"]["generation_authorized"] is not False:
        raise ValueError("GENERATION_AUTHORIZATION_CHANGED")
    nodes = unit.get("nodes")
    if not isinstance(nodes, list) or any(not isinstance(n, dict) for n in nodes):
        raise ValueError("SOURCE_NODES_INVALID")
    ids = [n["CUSEC"] for n in nodes]
    if len(ids) != len(set(ids)) or not ids:
        raise ValueError("SOURCE_CUSEC_DUPLICATE_OR_EMPTY")
    provinces = {n.get("CPRO") for n in nodes}
    if len(provinces) != 1:
        raise ValueError("SOURCE_CROSS_PROVINCE")
    cpro = next(iter(provinces))
    quota_rows = contract.get("quotas_by_origin_unit", contract.get("quotas_by_circumscription"))
    quotas = {r["code"]: r["k"] for r in quota_rows}
    if type(quotas.get(cpro)) is not int or quotas[cpro] < 1:
        raise ValueError("CONTRACT_QUOTA_INVALID")
    k = quotas[cpro]
    units = {}
    for n in nodes:
        ident, pop = n.get("CUSEC"), n.get("POB_2025")
        if (not isinstance(ident, str) or len(ident) != 10 or not ident.isdigit()
                or type(pop) is not int or pop < 0 or ident[:2] != cpro
                or ident[:5] != n.get("CUMUN") or n.get("id") != ident
                or not isinstance(n.get("NMUN"), str)):
            raise ValueError("SOURCE_NODE_INVALID")
        units[ident] = {"population": pop, "province": cpro, "CUMUN": n["CUMUN"],
                        "municipality_group": n["CUMUN"], "name": n["NMUN"]}
    graph = {n: set() for n in ids}
    edges = unit.get("edges")
    if not isinstance(edges, list):
        raise ValueError("SOURCE_EDGES_INVALID")
    for e in edges:
        if not isinstance(e, dict):
            raise ValueError("SOURCE_EDGE_INVALID")
        if (e.get("kind") != "linear" or e.get("edge_type") != "geometric"
                or type(e.get("shared_border_m")) not in (int, float)
                or not math.isfinite(e["shared_border_m"]) or e["shared_border_m"] <= 0):
            raise ValueError("NON_PHYSICAL_EDGE")
        a, b = e["u"], e["v"]
        if a not in graph or b not in graph or a == b or b in graph[a]:
            raise ValueError("SOURCE_EDGE_INVALID")
        graph[a].add(b); graph[b].add(a)
    population = sum(n["population"] for n in units.values())
    floor = (17 * population + 20 * k - 1) // (20 * k)
    cap = (23 * population) // (20 * k)
    return units, graph, cpro, k, population, floor, cap

def state_from_candidate(candidate, units, cpro, k):
    if not isinstance(candidate, dict):
        raise ValueError("CANDIDATE_NOT_OBJECT")
    if candidate.get("schema") not in {
        "ddd.congress-leon-analytical-candidate/1.0",
        "ddd.congress-provincial-analytical-candidate/1.0",
    }:
        raise ValueError("CANDIDATE_SCHEMA_INVALID")
    if candidate.get("cpro") != cpro or type(candidate.get("k")) is not int or candidate["k"] != k:
        raise ValueError("CANDIDATE_PROVINCE_OR_K")
    if candidate.get("generation_authorized") is not False:
        raise ValueError("CANDIDATE_AUTHORIZATION_INVALID")
    rows = candidate.get("districts", [])
    if (not isinstance(rows, list) or any(not isinstance(r, dict) for r in rows)
            or len(rows) != k or any(not isinstance(r.get("id"), str) for r in rows)
            or len({r["id"] for r in rows}) != k):
        raise ValueError("DISTRICT_COUNT_OR_DUPLICATE")
    state = {}
    for row in rows:
        if (not isinstance(row["id"], str) or not isinstance(row.get("cusecs"), list)
                or not row["cusecs"] or any(not isinstance(x, str) for x in row["cusecs"])):
            raise ValueError("DISTRICT_ID_OR_EMPTY")
        for ident in row["cusecs"]:
            if ident not in units or ident in state:
                raise ValueError("CUSEC_UNKNOWN_OR_DUPLICATE")
            state[ident] = row["id"]
        if type(row.get("population")) is not int or row["population"] != sum(units[i]["population"] for i in row["cusecs"]):
            raise ValueError("DISTRICT_POPULATION_MISMATCH")
    if set(state) != set(units):
        raise ValueError("CUSEC_COVERAGE")
    return state

def groups(state):
    out = defaultdict(set)
    for u, d in state.items(): out[d].add(u)
    return out

def split_inventory(state, units):
    mun = defaultdict(lambda: defaultdict(list))
    for u, d in state.items(): mun[units[u]["CUMUN"]][d].append(u)
    return [{"CUMUN": m, "name": units[sorted(u for ns in ds.values() for u in ns)[0]]["name"],
             "population": sum(units[u]["population"] for ns in ds.values() for u in ns),
             "fragments": [{"district": d, "CUSEC": sorted(ns), "population": sum(units[u]["population"] for u in ns)} for d, ns in sorted(ds.items())]}
            for m, ds in sorted(mun.items()) if len(ds) > 1]

def audit_candidate(candidate, unit, contract, *, expected_binding=None):
    units, graph, cpro, k, pop, floor, cap = model(unit, contract)
    state = state_from_candidate(candidate, units, cpro, k)
    if candidate.get("witness_sha256") != assignment_witness_sha(state):
        raise ValueError("CANDIDATE_ASSIGNMENT_WITNESS_MISMATCH")
    if (candidate.get("generation_authorized") is not False
            or candidate.get("publication_authorized") is not False
            or candidate.get("product_certification") != "NOT_PERFORMED"
            or candidate.get("pilot_only") is not True
            or candidate.get("municipal_policy_certified") is not False
            or candidate.get("external_boundaries_accredited") is not False):
        raise ValueError("CANDIDATE_PILOT_GATES_INVALID")
    if (type(candidate.get("population")) is not int or candidate["population"] != pop
            or type(candidate.get("floor")) is not int or candidate["floor"] != floor
            or type(candidate.get("cap")) is not int or candidate["cap"] != cap):
        raise ValueError("PROVINCIAL_POPULATION_OR_BOUNDS_MISMATCH")
    if expected_binding is not None and candidate.get("source_binding") != expected_binding:
        raise ValueError("SOURCE_BINDING_MISMATCH")
    district_groups = groups(state)
    populations = {d: sum(units[u]["population"] for u in ns) for d, ns in district_groups.items()}
    graph_ok = all(connected(ns, graph) for ns in district_groups.values())
    limits_ok = all(floor <= p <= cap for p in populations.values())
    splits = split_inventory(state, units)
    verified = verify_partition_constraints(state, units, graph, floor=floor, cap=cap,
                                            municipality_policy=MUNICIPAL_POLICY_N08)
    municipal = "DEMOSTRADO" if verified.get("valid") and verified.get("hard_limits_met") else "PENDIENTE"
    if verified.get("reason") == "MUNICIPAL_SPLIT_NOT_MINIMAL": municipal = "INCUMPLIDO"
    checks = {"CUSEC_coverage_and_atomicity": "DEMOSTRADO", "population_conservation": "DEMOSTRADO",
              "province_and_K": "DEMOSTRADO", "population_bounds": "DEMOSTRADO" if limits_ok else "INCUMPLIDO",
              "section_graph_contiguity": "DEMOSTRADO" if graph_ok else "INCUMPLIDO",
              "original_polygon_part_contiguity": "PENDIENTE",
              "municipal_discipline": municipal, "administrative_accreditation": "PENDIENTE",
              "named_exceptions": "PENDIENTE", "artifact_geometry_traceability": "PENDIENTE"}
    return {"schema": "ddd.congress-provincial-analytical-audit/1.0", "cpro": cpro, "k": k,
            "sections": len(units), "population": pop, "floor": floor, "cap": cap,
            "checks": checks, "district_populations": dict(sorted(populations.items())),
            "municipalities_split": splits, "existing_M05_validation": verified,
            "physical_evidence": {"status": "PENDIENTE", "reason": "SEPARATE_PHYSICAL_AUDIT_REQUIRES_REVIEWED_ARTIFACT"},
            "no_named_exceptions_applied": True, "candidate_sha256": canonical_sha(candidate),
            "generation_authorized": False, "product_certification": "NOT_PERFORMED"}

def consolidate_avoidable_splits(state, units, graph, *, floor, cap, max_trials=30000):
    """Finite local correction; reuse M05 connectedness and hard final validator.

    Try complete-municipality consolidation, then one district evacuation and
    one whole-municipality population rescue. Never claim global impossibility.
    Intermediate below-floor states are not emitted as admissible candidates.
    """
    if type(max_trials) is not int or max_trials < 1: raise ValueError("REPAIR_BUDGET_INVALID")
    current = dict(state); expected = set(state.values()); trials = 0; log = []
    municipalities = defaultdict(set)
    for u in units: municipalities[units[u]["CUMUN"]].add(u)
    def structural(s, require_bounds=True):
        ds = groups(s)
        return (set(s) == set(units) and set(ds) == expected
                and all(connected(ns, graph) for ns in ds.values())
                and (not require_bounds or all(floor <= sum(units[u]["population"] for u in ns) <= cap for ns in ds.values())))
    def improvement(s):
        nonlocal trials
        if trials >= max_trials: return False
        trials += 1
        return structural(s) and len(split_inventory(s, units)) < len(split_inventory(current, units))
    while trials < max_trials:
        accepted = False
        for m in [r["CUMUN"] for r in split_inventory(current, units)]:
            members = municipalities[m]; destinations = sorted({current[u] for u in members})
            for dest in destinations:
                direct = dict(current)
                for u in members: direct[u] = dest
                if improvement(direct):
                    log.append({"kind": "WHOLE_MUNICIPALITY_CONSOLIDATION", "CUMUN": m, "to": dest}); current=direct;accepted=True;break
            if accepted: break
        if accepted: continue
        for m in [r["CUMUN"] for r in split_inventory(current, units)]:
            members=municipalities[m]; destinations=sorted({current[u] for u in members})
            for dest in destinations:
                for receiver in sorted(expected-{dest}):
                    swapped=dict(current)
                    for u in members: swapped[u]=dest
                    for u in current:
                        if current[u]==dest and u not in members: swapped[u]=receiver
                    if improvement(swapped):
                        current=swapped;log.append({"kind":"DISTRICT_EVACUATION","CUMUN":m,"to":dest,"receiver":receiver});accepted=True;break
                    if not structural(swapped, False): continue
                    for rescue, ns in sorted(municipalities.items()):
                        owners={swapped[u] for u in ns}
                        if len(owners)!=1 or rescue==m: continue
                        for target in sorted(expected-owners):
                            trial=dict(swapped)
                            for u in ns:trial[u]=target
                            if improvement(trial):
                                current=trial;log.append({"kind":"DISTRICT_EVACUATION_WITH_WHOLE_MUNICIPALITY_RESCUE","CUMUN":m,"to":dest,"receiver":receiver,"rescue_CUMUN":rescue,"rescue_to":target});accepted=True;break
                            if trials>=max_trials:break
                        if accepted or trials>=max_trials:break
                    if accepted or trials>=max_trials:break
                if accepted or trials>=max_trials:break
            if accepted or trials>=max_trials:break
        if not accepted: break
    final=verify_partition_constraints(current, units, graph, floor=floor, cap=cap,municipality_policy=MUNICIPAL_POLICY_N08)
    # A pending municipal proof never promotes an invalid final state.
    return {"state":current,"moves":log,"trials":trials,"budget":max_trials,"validation":final,
            "municipal_minimum":"PROVEN_ZERO_SPLITS_ON_SECTION_GRAPH" if not split_inventory(current,units) else "NOT_PROVEN",
            "status":"CORRECTED_ANALYTICAL" if current!=state else "NO_LOCAL_CORRECTION_FOUND"}
