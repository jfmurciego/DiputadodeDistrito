#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""M05: reparación poblacional genérica, dirigida, acotada y determinista.

Versión 1.9.0 — 2026-10-10 — diversidad de trayectorias preparatorias.
Alcance: reparación poblacional M05 de cualquier territorio.
Estado: experimental; búsqueda ampliada con carril de diversidad por estado padre; revisión independiente pendiente.
Cambios/motivo: reservar parte del beam para descendientes de padres distintos,
incluidas continuaciones que cambian de pareja donante/receptor.
Predecesor: ../legacy/core/m05_population_repair_v1.8.0_2026-10-10.py
"""
from __future__ import annotations

from collections import deque
from dataclasses import asdict, dataclass
import heapq
import time
import tracemalloc

RESULT_REPAIRED = "REPAIRED"
RESULT_IMPROVED = "IMPROVED_NOT_REPAIRED"
RESULT_NONE = "NO_FEASIBLE_REPAIR_FOUND"


@dataclass(frozen=True)
class SearchLimits:
    max_depth: int = 3
    max_transfer_set: int = 2
    max_candidates: int = 20000
    max_seconds: float = 5.0
    seed: int = 0
    expanded_max_states: int = 400000
    expanded_max_candidates: int = 400000
    expanded_max_seconds: float = 180.0
    expanded_max_memory_mib: int = 640
    expanded_max_depth: int = 96
    expanded_beam_per_district: int = 4
    expanded_beam_width: int = 128
    expanded_max_radius: int = 8


def connected(nodes, adjacency):
    nodes=set(nodes)
    if not nodes: return False
    seen={next(iter(nodes))}; q=deque(seen)
    while q:
        u=q.popleft()
        for v in adjacency.get(u,()):
            if v in nodes and v not in seen: seen.add(v); q.append(v)
    return seen == nodes


def _cut_edges(state, adjacency):
    seen=set(); cuts=0
    for u in sorted(state,key=str):
        for v in adjacency.get(u,()):
            if v not in state: continue
            edge=frozenset((u,v))
            if len(edge)!=2 or edge in seen: continue
            seen.add(edge)
            if state[u] != state[v]: cuts += 1
    return cuts


def territorial_metrics(state, adjacency, *, boundary_units_moved=0):
    return {"cut_boundary_edges":_cut_edges(state,adjacency),"boundary_units_moved":int(boundary_units_moved),
            "corridor_penalty":None,"base_compactness":None}


def _district_floor(district, floor, district_floors=None):
    if district_floors is None:
        return floor
    return float(district_floors.get(district, floor))


def objective(populations, *, target, tolerance, floor, cap, cohesion=0, district_floors=None):
    vals=list(populations.values())
    hard=sum(
        p < _district_floor(d, floor, district_floors) or p > cap
        for d,p in populations.items()
    )
    outside=sum(abs(p-target) > tolerance for p in vals)
    maxdev=max((abs(p-target)/target for p in vals),default=0.0)
    totaldev=sum(abs(p-target)/target for p in vals)
    return (hard,outside,round(maxdev,12),round(totaldev,12),int(cohesion))


def _hard_population_signature(populations, *, floor, cap, district_floors=None):
    hard_count = 0
    hard_magnitude = 0
    for district,population in populations.items():
        effective_floor = _district_floor(district, floor, district_floors)
        if population < effective_floor:
            hard_count += 1
            hard_magnitude += effective_floor - population
        elif population > cap:
            hard_count += 1
            hard_magnitude += population - cap
    return (int(hard_count), int(hard_magnitude))


def _controlled_population_transition(before, after, *, floor, cap, district_floors=None):
    """Monotone hard-population transition used by the primary search."""
    before_sig = _hard_population_signature(
        before, floor=floor, cap=cap, district_floors=district_floors
    )
    after_sig = _hard_population_signature(
        after, floor=floor, cap=cap, district_floors=district_floors
    )
    return after_sig <= before_sig, before_sig, after_sig


def _single_transfer_hard_signature(pops, donor, receiver, delta, *, floor, cap,
                                   district_floors=None, before_signature=None,
                                   before_magnitude_exact=None):
    before_signature=before_signature or _hard_population_signature(
        pops,floor=floor,cap=cap,district_floors=district_floors)
    def magnitude(d,p):
        low=_district_floor(d,floor,district_floors)
        return max(0.0,low-p,p-cap)
    old_d=magnitude(donor,pops[donor]); old_r=magnitude(receiver,pops[receiver])
    new_d=magnitude(donor,pops[donor]-delta); new_r=magnitude(receiver,pops[receiver]+delta)
    count=before_signature[0]-int(old_d>0)-int(old_r>0)+int(new_d>0)+int(new_r>0)
    total=(float(before_magnitude_exact) if before_magnitude_exact is not None else
           float(before_signature[1]))-old_d-old_r+new_d+new_r
    return (int(count),int(total))



def _verify_final_constraints(
    state, units, adjacency, *, expected_districts, floor, cap, district_floors=None
):
    districts = set(state.values())
    if districts != set(expected_districts):
        return {"valid": False, "reason": "DISTRICT_SET_CHANGED"}

    for district in districts:
        owned = {u for u, d in state.items() if d == district}
        if not owned or not connected(owned, adjacency):
            return {"valid": False, "reason": "DISTRICT_CONTIGUITY", "district": district}
        provinces = {str(units[u].get("province")) for u in owned}
        if len(provinces) != 1:
            return {"valid": False, "reason": "CROSS_PROVINCE", "district": district}

    municipality_groups = {}
    for unit, row in units.items():
        group = row.get("municipality_group")
        if group:
            municipality_groups.setdefault(group, set()).add(state[unit])
    split_groups = sorted((str(group) for group, ds in municipality_groups.items() if len(ds) != 1))
    if split_groups:
        return {"valid": False, "reason": "MUNICIPAL_INTEGRITY", "groups": split_groups}

    populations = _district_pops(state, units)
    hard_count, hard_magnitude = _hard_population_signature(
        populations, floor=floor, cap=cap, district_floors=district_floors
    )
    return {
        "valid": True,
        "hard_limits_met": hard_count == 0,
        "hard_population_violations": hard_count,
        "hard_violation_magnitude": hard_magnitude,
        "populations": populations,
    }


def verify_partition_constraints(
    state, units, adjacency, *, floor, cap, district_floors=None
):
    """Validate structural invariants of a partition and report hard population violations."""
    return _verify_final_constraints(
        state,
        units,
        adjacency,
        expected_districts=set(state.values()),
        floor=floor,
        cap=cap,
        district_floors=district_floors,
    )


def _district_pops(state, units):
    out={}
    for u,d in state.items(): out[d]=out.get(d,0)+int(units[u]["population"])
    return out


def _deviations(pops,target): return {d:round((p-target)/target,12) for d,p in pops.items()}


def _outliers(pops,target,tolerance): return {d for d,p in pops.items() if abs(p-target)>tolerance}


def _outlier_distance(pops,target,tolerance):
    return round(sum(max(0,abs(p-target)-tolerance) for p in pops.values())/target,12)


def _primary_improves(obj, baseline_obj): return obj[1] < baseline_obj[1] or obj[2] < baseline_obj[2]


def _municipality_complete(moved,donor,state,units):
    moved=set(moved); groups={units[u].get("municipality_group") for u in moved if units[u].get("municipality_group")}
    for group in groups:
        owned={u for u,d in state.items() if d==donor and units[u].get("municipality_group")==group}
        if owned and not owned <= moved: return False
    return True


def _valid_transfer(
    state,units,adjacency,moved,donor,receiver,*,floor,cap,district_floors=None
):
    moved=set(moved); checks={"province_verified":False,"donor_contiguity_verified":False,
        "receiver_contiguity_verified":False,"atomic_units_verified":False,"municipal_integrity_verified":False}
    if not moved or any(state.get(u)!=donor for u in moved): return False,"NOT_OWNED",checks
    checks["atomic_units_verified"]=True
    provinces={units[u].get("province") for u in moved}; receiver_provinces={units[v].get("province") for v in state if state[v]==receiver}
    if len(provinces)!=1 or len(receiver_provinces)!=1 or provinces!=receiver_provinces: return False,"CROSS_PROVINCE",checks
    checks["province_verified"]=True
    if not _municipality_complete(moved,donor,state,units): return False,"MUNICIPAL_INTEGRITY",checks
    checks["municipal_integrity_verified"]=True
    if not connected(moved,adjacency): return False,"TRANSFER_SET_DISCONNECTED",checks
    donor_nodes={u for u,d in state.items() if d==donor}-moved; receiver_nodes={u for u,d in state.items() if d==receiver}|moved
    if not donor_nodes or not connected(donor_nodes,adjacency): return False,"DONOR_CONTIGUITY",checks
    checks["donor_contiguity_verified"]=True
    if not connected(receiver_nodes,adjacency): return False,"RECEIVER_CONTIGUITY",checks
    checks["receiver_contiguity_verified"]=True
    trial=dict(state)
    for u in moved: trial[u]=receiver
    before_pops=_district_pops(state,units); after_pops=_district_pops(trial,units)
    controlled,before_sig,after_sig=_controlled_population_transition(
        before_pops,after_pops,floor=floor,cap=cap,district_floors=district_floors
    )
    checks["population_transition_verified"]=controlled
    checks["hard_signature_before"]=list(before_sig)
    checks["hard_signature_after"]=list(after_sig)
    if not controlled: return False,"POPULATION_REGRESSION",checks
    return True,"VALID",checks


def _boundary_sets(state,adjacency,donor,receiver,max_size):
    owned=sorted((u for u,d in state.items() if d==donor),key=str)
    seeds=[u for u in owned if any(state.get(v)==receiver for v in adjacency.get(u,()))]
    result={frozenset((u,)) for u in seeds}; frontier=list(result)
    while frontier:
        s=frontier.pop()
        if len(s)>=max_size: continue
        for u in sorted(s,key=str):
            for v in adjacency.get(u,()):
                ns=frozenset(set(s)|{v})
                if state.get(v)==donor and len(ns)<=max_size and ns not in result and connected(ns,adjacency): result.add(ns); frontier.append(ns)
    return sorted(result,key=lambda x:(len(x),tuple(sorted(x,key=str))))


def _district_neighbors(state,adjacency):
    out={d:set() for d in set(state.values())}
    for u,d in state.items():
        for v in adjacency.get(u,()):
            if v in state and state[v]!=d: out[d].add(state[v])
    return out


def _relevant_districts(state,units,adjacency,target,tolerance,remaining_depth):
    out=_outliers(_district_pops(state,units),target,tolerance)
    if not out: return set(state.values())
    dn=_district_neighbors(state,adjacency); relevant=set(out); frontier=set(out)
    for _ in range(max(1,remaining_depth)):
        nxt={n for d in frontier for n in dn.get(d,())}-relevant
        relevant |= nxt; frontier=nxt
        if not frontier: break
    return relevant


def _step_evidence(
    state,trial,units,adjacency,moved,donor,receiver,checks,*,
    target,tolerance,floor,cap,district_floors=None
):
    before=_district_pops(state,units); after=_district_pops(trial,units); tm=territorial_metrics(trial,adjacency,boundary_units_moved=len(moved))
    obj=objective(
        after,target=target,tolerance=tolerance,floor=floor,cap=cap,
        cohesion=tm["cut_boundary_edges"],district_floors=district_floors
    )
    return {"units":sorted(moved,key=str),"donor":donor,"receiver":receiver,"population_before":before,"population_after":after,
        "deviation_before":_deviations(before,target),"deviation_after":_deviations(after,target),"objective_after_step":list(obj),
        "territorial_metrics":tm,**checks,"reason":"ACCEPTED_VALID_CANDIDATE"}


def _state_key(state): return tuple(sorted(state.items(),key=lambda x:str(x[0])))


def _churn(path):
    units=sum(len(s["units"]) for s in path); districts=len({d for s in path for d in (s["donor"],s["receiver"])})
    return (units,districts,len(path))


def _rank(state,path,units,adjacency,target,tolerance,floor,cap,district_floors=None):
    pops=_district_pops(state,units); tm=territorial_metrics(state,adjacency); obj=objective(
        pops,target=target,tolerance=tolerance,floor=floor,cap=cap,
        cohesion=tm["cut_boundary_edges"],district_floors=district_floors
    )
    hard_count,hard_magnitude=_hard_population_signature(
        pops,floor=floor,cap=cap,district_floors=district_floors
    )
    return (hard_count,hard_magnitude,obj[1],obj[2],_outlier_distance(pops,target,tolerance),obj[3],obj[4],*_churn(path),len(path),_state_key(state)),obj


def _province_rank_from_pops(
    pops,districts,target,tolerance,floor,cap,district_floors=None
):
    selected={d:pops[d] for d in districts}
    hard_count,hard_magnitude=_hard_population_signature(
        selected,floor=floor,cap=cap,district_floors=district_floors
    )
    outliers={d for d in districts if abs(pops[d]-target)>tolerance}
    distance=round(sum(max(0,abs(pops[d]-target)-tolerance) for d in districts)/target,12)
    maxdev=round(max((abs(pops[d]-target)/target for d in outliers),default=0.0),12)
    totaldev=round(sum(abs(pops[d]-target)/target for d in districts),12)
    return (hard_count,hard_magnitude,len(outliers),distance,maxdev,totaldev),outliers


def _province_state_key(state,units,province):
    return tuple(sorted(((u,state[u]) for u in state if str(units[u].get("province"))==province),key=lambda x:str(x[0])))


def _articulation_points(nodes, adjacency):
    """Return cut vertices of one connected district in linear graph time."""
    nodes=set(nodes); discovery={}; low={}; parent={}; cuts=set(); tick=0
    def visit(u):
        nonlocal tick
        tick+=1; discovery[u]=low[u]=tick; children=0
        for v in adjacency.get(u,()):
            if v not in nodes: continue
            if v not in discovery:
                parent[v]=u; children+=1; visit(v); low[u]=min(low[u],low[v])
                if u not in parent and children>1: cuts.add(u)
                if u in parent and low[v]>=discovery[u]: cuts.add(u)
            elif parent.get(u)!=v: low[u]=min(low[u],discovery[v])
    for u in sorted(nodes,key=str):
        if u not in discovery: visit(u)
    return cuts


def _select_expanded_frontier(candidates, parents, frontier, rank, ceiling):
    """Combine the ranked beam with one continuation from distinct parents.

    A useful preparation can change donor/receiver between consecutive steps.
    Keep the global top half, then preserve one best descendant per parent in
    frontier order. The reservation comes out of the existing beam width.
    """
    if not candidates or ceiling <= 0:
        return []
    ordered = sorted(candidates, key=lambda key: (rank(key), key))
    primary_slots = (ceiling + 1) // 2
    selected = ordered[:primary_slots]
    selected_set = set(selected)
    continuation_by_parent = {}
    for key in ordered:
        record = parents.get(key)
        if not record:
            continue
        parent = record[0]
        if parent not in continuation_by_parent:
            continuation_by_parent[parent] = key
    for parent in frontier:
        if len(selected) >= ceiling:
            break
        key = continuation_by_parent.get(parent)
        if key is not None and key not in selected_set:
            selected.append(key)
            selected_set.add(key)
    if len(selected) < ceiling:
        for key in ordered:
            if key not in selected_set:
                selected.append(key)
                selected_set.add(key)
                if len(selected) >= ceiling:
                    break
    return selected


def _focal_single_transfer(
    state,
    pops,
    province_units,
    units,
    adjacency,
    u,
    donor,
    receiver,
    *,
    floor,
    cap,
    district_floors=None,
    donor_unit_count=None,
    donor_articulations=None,
    municipality_owned=None,
    hard_signature=None,
    hard_magnitude_exact=None,
):
    checks={"province_verified":True,"donor_contiguity_verified":False,
        "receiver_contiguity_verified":True,"atomic_units_verified":True,"municipal_integrity_verified":False}
    group=units[u].get("municipality_group")
    if group:
        owned=(municipality_owned or {}).get(group) if municipality_owned is not None else None
        if owned is None:
            owned={v for v in province_units if state[v]==donor and units[v].get("municipality_group")==group}
        if owned and owned != {u}: return False,"MUNICIPAL_INTEGRITY",checks
    checks["municipal_integrity_verified"]=True
    if donor_unit_count is not None and donor_articulations is not None:
        if donor_unit_count<=1 or u in donor_articulations: return False,"DONOR_CONTIGUITY",checks
    else:
        donor_nodes={v for v in province_units if state[v]==donor and v!=u}
        if not donor_nodes or not connected(donor_nodes,adjacency): return False,"DONOR_CONTIGUITY",checks
    checks["donor_contiguity_verified"]=True
    after_donor=pops[donor]-int(units[u]["population"]); after_receiver=pops[receiver]+int(units[u]["population"])
    before_sig=hard_signature or _hard_population_signature(
        pops,floor=floor,cap=cap,district_floors=district_floors)
    after_sig=_single_transfer_hard_signature(pops,donor,receiver,int(units[u]["population"]),
        floor=floor,cap=cap,district_floors=district_floors,before_signature=before_sig,
        before_magnitude_exact=hard_magnitude_exact)
    controlled=after_sig<=before_sig
    checks["population_transition_verified"]=controlled
    checks["hard_signature_before"]=list(before_sig)
    checks["hard_signature_after"]=list(after_sig)
    if not controlled:
        return False,"POPULATION_REGRESSION",checks
    return True,"VALID",checks

def _focal_chain_search(
    *,state,units,adjacency,target,tolerance,floor,cap,limits,deadline,
    candidate_budget,district_floors=None,frozen_assignments=None
):
    """Beam search focal con dos modos explícitos.

    Si entra con infracciones duras, su responsabilidad termina al alcanzar
    suelo/techo en todos los distritos. La banda objetivo sigue siendo un
    objetivo blando de Optimización y no se promueve aquí a restricción dura.
    Si entra sin infracciones duras, conserva el modo histórico de refinamiento
    hasta cerrar los outliers de tolerancia.
    """
    phase_start=time.monotonic()
    hard_repair_mode=_hard_population_signature(
        _district_pops(state,units),floor=floor,cap=cap,district_floors=district_floors
    )[0] > 0
    working=dict(state); all_steps=[]; candidate_attempts=0; transitions_evaluated=0; states_explored=0
    rejection_counts={}; province_reports=[]; termination="QUEUE_EMPTY"
    provinces=sorted({str(units[u].get("province")) for u in units},key=str)
    for province in provinces:
        if candidate_attempts>=candidate_budget:
            termination="CANDIDATE_BUDGET_EXHAUSTED"; break
        if time.monotonic()>=deadline:
            termination="TIME_BUDGET_EXHAUSTED"; break
        province_units=sorted((u for u in working if str(units[u].get("province"))==province),key=str)
        if not province_units: continue
        local_base={u:working[u] for u in province_units}
        districts=sorted(set(local_base.values()),key=str)
        start_pops={d:0 for d in districts}
        for u,d in local_base.items(): start_pops[d]+=int(units[u]["population"])
        start_rank,start_outliers=_province_rank_from_pops(
            start_pops,districts,target,tolerance,floor,cap,district_floors
        )
        if start_rank[0]==0 and not start_outliers: continue
        hard_districts={
            d for d in districts
            if start_pops[d] < _district_floor(d,floor,district_floors)
            or start_pops[d] > cap
        }
        district_neighbors=_district_neighbors(local_base,adjacency)
        preparatory_districts=set(hard_districts); prep_frontier=set(hard_districts)
        for _ in range(2):
            nxt={n for d in prep_frontier for n in district_neighbors.get(d,())}-preparatory_districts
            preparatory_districts |= nxt; prep_frontier=nxt
            if not prep_frontier: break
        depth_limit=min(12,max(int(limits.max_depth)+3,2*len(start_outliers)+5))
        beam_width=min(64,max(24,8*len(start_outliers)))
        frontier=[(local_base,start_pops,[],start_rank)]
        seen={_state_key(local_base)}
        province_states=0; depth_exhausted=0; found=None
        for depth in range(depth_limit+1):
            next_frontier=[]
            for current,pops,path,rank in frontier:
                if candidate_attempts>=candidate_budget:
                    termination="CANDIDATE_BUDGET_EXHAUSTED"; break
                if time.monotonic()>=deadline:
                    termination="TIME_BUDGET_EXHAUSTED"; break
                states_explored+=1; province_states+=1
                # Reparación dura y refinamiento blando tienen contratos distintos:
                # no consumir presupuesto de reparación dura una vez hard == 0.
                if (hard_repair_mode and rank[0]==0) or ((not hard_repair_mode) and rank[2]==0):
                    found=(current,pops,path,rank); break
                if depth>=depth_limit:
                    depth_exhausted+=1; continue
                _,outliers=_province_rank_from_pops(
                    pops,districts,target,tolerance,floor,cap,district_floors
                )
                hard_now={
                    d for d in districts
                    if pops[d] < _district_floor(d,floor,district_floors) or pops[d] > cap
                }
                for u in province_units:
                    if u in (frozen_assignments or {}): continue
                    donor=current[u]
                    receivers=sorted({current[v] for v in adjacency.get(u,()) if v in current and current[v]!=donor},key=str)
                    for receiver in receivers:
                        if candidate_attempts>=candidate_budget:
                            termination="CANDIDATE_BUDGET_EXHAUSTED"; break
                        if time.monotonic()>=deadline:
                            termination="TIME_BUDGET_EXHAUSTED"; break
                        if hard_repair_mode:
                            donor_high=donor in hard_now and pops[donor] > cap
                            receiver_low=(
                                receiver in hard_now
                                and pops[receiver] < _district_floor(receiver,floor,district_floors)
                            )
                        else:
                            donor_high=donor in outliers and pops[donor] > target+tolerance
                            receiver_low=receiver in outliers and pops[receiver] < target-tolerance
                        targeted=donor_high or receiver_low
                        preparatory=(donor in preparatory_districts and receiver in preparatory_districts)
                        if not (targeted or preparatory): continue
                        transitions_evaluated+=1
                        candidate_attempts+=1
                        ok,reason,checks=_focal_single_transfer(
                            current,pops,province_units,units,adjacency,u,donor,receiver,
                            floor=floor,cap=cap,district_floors=district_floors,
                        )
                        if not ok:
                            rejection_counts[reason]=rejection_counts.get(reason,0)+1
                            continue
                        trial_pops=dict(pops); delta=int(units[u]["population"])
                        trial_pops[donor]-=delta; trial_pops[receiver]+=delta
                        trial_rank,trial_outliers=_province_rank_from_pops(
                            trial_pops,districts,target,tolerance,floor,cap,district_floors
                        )
                        if (not hard_repair_mode) and len(trial_outliers)>len(outliers)+1: continue
                        trial=current.copy(); trial[u]=receiver
                        key=_state_key(trial)
                        if key in seen: continue
                        seen.add(key)
                        next_frontier.append((trial_rank,key,trial,trial_pops,path+[(u,donor,receiver,checks)]))
                    if termination.endswith("EXHAUSTED"): break
                if termination.endswith("EXHAUSTED"): break
            if found or termination.endswith("EXHAUSTED"): break
            next_frontier.sort(key=lambda x:(x[0],x[1]))
            frontier=[(row[2],row[3],row[4],row[0]) for row in next_frontier[:beam_width]]
            if not frontier: break
        rejection_counts["DEPTH_EXHAUSTED"]=rejection_counts.get("DEPTH_EXHAUSTED",0)+depth_exhausted
        report={"province":province,"outliers_before":len(start_outliers),"hard_districts_before":len(hard_districts),
                "preparatory_districts":sorted(preparatory_districts,key=str),"depth_limit":depth_limit,
                "beam_width":beam_width,"states_explored":province_states,
                "depth_exhausted_states":depth_exhausted,"repaired":found is not None}
        if found is not None:
            found_local,_,moves,final_rank=found
            replay=dict(working); steps=[]
            for u,donor,receiver,checks in moves:
                trial=dict(replay); trial[u]=receiver
                steps.append(_step_evidence(
                    replay,trial,units,adjacency,(u,),donor,receiver,checks,
                    target=target,tolerance=tolerance,floor=floor,cap=cap,
                    district_floors=district_floors,
                ))
                replay=trial
            for u,d in found_local.items(): working[u]=d
            all_steps.extend(steps); report["outliers_after"]=final_rank[2]
        else:
            report["outliers_after"]=start_rank[2]
        province_reports.append(report)
        if termination.endswith("EXHAUSTED"): break
    final_pops=_district_pops(working,units)
    final_hard=_hard_population_signature(
        final_pops,floor=floor,cap=cap,district_floors=district_floors
    )
    complete=(final_hard[0]==0) if hard_repair_mode else (not _outliers(final_pops,target,tolerance))
    elapsed=time.monotonic()-phase_start
    classification={
        "contiguity": rejection_counts.get("DONOR_CONTIGUITY",0)+rejection_counts.get("RECEIVER_CONTIGUITY",0)+rejection_counts.get("TRANSFER_SET_DISCONNECTED",0),
        "population_limit": rejection_counts.get("HARD_POPULATION_LIMIT",0)+rejection_counts.get("POPULATION_REGRESSION",0),
        "cross_province": rejection_counts.get("CROSS_PROVINCE",0),
        "municipal_integrity": rejection_counts.get("MUNICIPAL_INTEGRITY",0),
        "depth_exhaustion": rejection_counts.get("DEPTH_EXHAUSTED",0),
    }
    return working,all_steps,{"enabled":True,"complete":complete,
        "completion_target":"HARD_POPULATION_LIMITS" if hard_repair_mode else "TARGET_TOLERANCE",
        "candidate_budget":candidate_budget,
        "candidate_attempts":candidate_attempts,"transitions_evaluated":transitions_evaluated,
        "states_explored":states_explored,"termination_reason":termination,
        "elapsed_seconds":round(elapsed,6),"provinces":province_reports,"rejection_counts":rejection_counts,
        "rejection_classification":classification}


def _expanded_hard_search(
    *, state, units, adjacency, target, tolerance, floor, cap, limits,
    district_floors=None, frozen_assignments=None, deadline=None, candidate_budget=None,
):
    """Bounded, stratified single-unit search for hard feasibility.

    Every edge is checked by the same transfer validator as the primary
    search. The per-district beam keeps preparatory reservoirs across the
    whole reachable neighborhood rather than fixing a focal halo in advance.
    """
    expanded_seconds=float(limits.expanded_max_seconds)
    started=time.monotonic(); local_deadline=started+max(0.0,expanded_seconds)
    deadline=min(local_deadline,deadline) if deadline is not None else local_deadline
    state_limit=max(1,int(limits.expanded_max_states)); depth_limit=max(0,int(limits.expanded_max_depth))
    candidate_limit=max(0,int(candidate_budget if candidate_budget is not None else
        min(400000,limits.expanded_max_candidates)))
    mem_limit=max(1,int(limits.expanded_max_memory_mib))*1024*1024
    own_trace=not tracemalloc.is_tracing()
    if own_trace: tracemalloc.start()
    unit_ids=sorted(state,key=str); unit_index={u:i for i,u in enumerate(unit_ids)}
    districts=sorted(set(state.values()),key=str); district_index={d:i for i,d in enumerate(districts)}
    code_width=max(1,(max(1,len(districts)-1).bit_length()+7)//8)
    def encode(assignments):
        return b"".join(district_index[assignments[u]].to_bytes(code_width,"little") for u in unit_ids)
    def decode(key):
        return {u:districts[int.from_bytes(key[i*code_width:(i+1)*code_width],"little")]
                for i,u in enumerate(unit_ids)}
    start_key=encode(state); parents={start_key:None}; frontier=[start_key]
    hard_start=_hard_population_signature(
        _district_pops(state,units),floor=floor,cap=cap,district_floors=district_floors)
    dn=_district_neighbors(state,adjacency); allowed=set()
    wave={d for d,p in _district_pops(state,units).items()
          if p < _district_floor(d,floor,district_floors) or p > cap}
    allowed.update(wave)
    for _ in range(max(0,int(limits.expanded_max_radius))):
        wave={n for d in wave for n in dn.get(d,())}-allowed
        if not wave: break
        allowed.update(wave)
    if not allowed: allowed=districts
    distance={d:0 for d,p in _district_pops(state,units).items()
              if p < _district_floor(d,floor,district_floors) or p > cap}
    wave=set(distance)
    for radius in range(1,max(1,int(limits.expanded_max_radius))+1):
        wave={n for d in wave for n in dn.get(d,()) if n in allowed and n not in distance}
        for d in wave: distance[d]=radius
        if not wave: break
    def reservoir_potential(pops):
        # Generic handoff heuristic: prefer viable population capacity closer
        # to the initial hard-violating districts, without changing constraints.
        return sum(max(0,min(float(pops[d])-_district_floor(d,floor,district_floors),
                             float(cap)-_district_floor(d,floor,district_floors)))
                   * max(1,int(limits.expanded_max_radius)+1-distance.get(d,int(limits.expanded_max_radius)+1))
                   for d in sorted(allowed,key=str))
    units_by_province={}
    for u,row in units.items(): units_by_province.setdefault(str(row.get("province")),[]).append(u)
    frozen_districts=set((frozen_assignments or {}).values())
    expanded=generated=pruned=candidate_attempts=deduplicated=selected_total=0
    found=None; termination="QUEUE_EMPTY"; peak_mib=0.0; max_depth_reached=0
    for depth in range(depth_limit+1):
        candidates={}
        for key in frontier:
            if time.monotonic()>=deadline: termination="TIME_BUDGET_EXHAUSTED"; break
            current=decode(key); pops=_district_pops(current,units)
            expanded+=1; max_depth_reached=max(max_depth_reached,depth)
            owned_by_district={d:[] for d in districts}; groups_by_district={d:{} for d in districts}
            for unit,district in current.items():
                owned_by_district[district].append(unit)
                group=units[unit].get("municipality_group")
                if group: groups_by_district[district].setdefault(group,set()).add(unit)
            articulation_cache={}
            sig=_hard_population_signature(pops,floor=floor,cap=cap,district_floors=district_floors)
            hard_magnitude_exact=sum(max(0.0,_district_floor(d,floor,district_floors)-p,p-cap)
                                     for d,p in pops.items())
            if sig[0]==0: found=key; break
            if depth>=depth_limit: continue
            if len(parents)>=state_limit: termination="STATE_BUDGET_EXHAUSTED"; break
            _,peak=tracemalloc.get_traced_memory(); peak_mib=max(peak_mib,peak/(1024*1024))
            if peak>=mem_limit: termination="MEMORY_BUDGET_EXHAUSTED"; break
            for u in sorted(current,key=str):
                if u in (frozen_assignments or {}): continue
                donor=current[u]
                if donor not in allowed: continue
                province=str(units[u].get("province")); province_units=units_by_province.get(province,())
                receivers=sorted({current[v] for v in adjacency.get(u,())
                    if v in current and current[v]!=donor and current[v] in allowed
                    and str(units[v].get("province"))==province
                    and current[v] not in frozen_districts},key=str)
                for receiver in receivers:
                    if time.monotonic()>=deadline: termination="TIME_BUDGET_EXHAUSTED"; break
                    if candidate_attempts>=candidate_limit: termination="CANDIDATE_BUDGET_EXHAUSTED"; break
                    candidate_attempts+=1
                    if donor not in articulation_cache:
                        articulation_cache[donor]=_articulation_points(owned_by_district[donor],adjacency)
                    ok,reason,checks=_focal_single_transfer(current,pops,province_units,units,adjacency,u,donor,receiver,
                        floor=floor,cap=cap,district_floors=district_floors,
                        donor_unit_count=len(owned_by_district[donor]),
                        donor_articulations=articulation_cache[donor],
                        municipality_owned=groups_by_district[donor],hard_signature=sig,
                        hard_magnitude_exact=hard_magnitude_exact)
                    if not ok: continue
                    trial_code=bytearray(key); offset=unit_index[u]*code_width
                    trial_code[offset:offset+code_width]=district_index[receiver].to_bytes(code_width,"little")
                    next_key=bytes(trial_code)
                    if next_key in parents:
                        deduplicated+=1
                        continue
                    moved=(u,)
                    parents[next_key]=(key,moved,donor,receiver,checks)
                    trial_pops=dict(pops); delta=int(units[u]["population"])
                    trial_pops[donor]-=delta; trial_pops[receiver]+=delta
                    candidates[next_key]=trial_pops; generated+=1
                    if _hard_population_signature(trial_pops,floor=floor,cap=cap,district_floors=district_floors)[0]==0:
                        found=next_key; break
                    if len(parents)>=state_limit:
                        termination="STATE_BUDGET_EXHAUSTED"; break
                    _,peak=tracemalloc.get_traced_memory(); peak_mib=max(peak_mib,peak/(1024*1024))
                    if peak>=mem_limit: termination="MEMORY_BUDGET_EXHAUSTED"; break
                if found or termination.endswith("EXHAUSTED"): break
            if found or termination.endswith("EXHAUSTED"): break
        if found or termination.endswith("EXHAUSTED"):
            # No incomplete generation wave is promoted to the next frontier.
            # Count its undispatched unique states as pruned, separately from
            # duplicates rejected by the state-key registry.
            pruned+=len(candidates)-int(found is not None)
            break
        if not candidates:
            termination="DEPTH_BUDGET_EXHAUSTED" if depth>=depth_limit else "QUEUE_EMPTY"
            break
        # All valid candidates reach this one global beam. Do not prefilter by
        # district, parent, or route: a locally modest prefix may be required
        # to prepare a later hard-feasibility transfer.
        per=max(1,int(limits.expanded_beam_per_district))
        ceiling=min(max(per,per*len(districts)),max(1,int(limits.expanded_beam_width)))
        def expanded_rank(k):
            p=candidates[k]; vals=list(p.values())
            outliers=sum(abs(v-target)>tolerance for v in vals)
            maxdev=max((abs(v-target)/target for v in vals),default=0.0)
            totaldev=sum(abs(v-target)/target for v in vals)
            return (_hard_population_signature(p,floor=floor,cap=cap,district_floors=district_floors),
                    -reservoir_potential(p),outliers,round(maxdev,12),round(totaldev,12),k)
        keep=_select_expanded_frontier(candidates,parents,frontier,expanded_rank,ceiling)
        selected_total+=len(keep)
        pruned+=len(candidates)-len(keep); frontier=keep
    else:
        if termination=="QUEUE_EMPTY": termination="DEPTH_BUDGET_EXHAUSTED"
    path=[]
    if found is not None:
        cursor=found
        while parents[cursor] is not None:
            previous,moved,donor,receiver,checks=parents[cursor]
            path.append((moved,donor,receiver,checks)); cursor=previous
        path.reverse(); termination="HARD_LIMITS_REPAIRED"
    result=dict(state); steps=[]
    for moved,donor,receiver,checks in path:
        trial=result.copy()
        for u in moved: trial[u]=receiver
        steps.append(_step_evidence(result,trial,units,adjacency,moved,donor,receiver,checks,
            target=target,tolerance=tolerance,floor=floor,cap=cap,district_floors=district_floors))
        result=trial
    verified=_verify_final_constraints(result,units,adjacency,expected_districts=districts,
        floor=floor,cap=cap,district_floors=district_floors)
    if any(result.get(u)!=d for u,d in (frozen_assignments or {}).items()):
        verified={"valid":False,"reason":"FROZEN_UNIT_CHANGED"}
    if found is not None and (not verified["valid"] or not verified["hard_limits_met"]):
        raise RuntimeError("expanded M05 search returned an invalid hard-feasible state")
    elapsed=time.monotonic()-started
    if own_trace:
        _,trace_peak=tracemalloc.get_traced_memory(); peak_mib=max(peak_mib,trace_peak/(1024*1024)); tracemalloc.stop()
    outcome=("REPAIRED" if found is not None else
             "EXHAUSTED" if termination=="QUEUE_EMPTY" and pruned==0 else "INCONCLUSIVE")
    return result,steps,{"enabled":True,"complete":found is not None,"outcome":outcome,"termination_reason":termination,
        "max_depth":depth_limit,"max_radius":int(limits.expanded_max_radius),"states_generated":generated,
        "candidate_attempts":candidate_attempts,"candidate_limit":candidate_limit,
        "max_depth_reached":max_depth_reached,"beam_width":int(limits.expanded_beam_width),
        "states_expanded":expanded,"states_selected":selected_total,
        "states_pending_expansion":max(0,1+selected_total-expanded),
        "states_discovered":len(parents),"states_deduplicated":deduplicated,
        "states_pruned":pruned,
        "state_limit":state_limit,"time_limit_seconds":expanded_seconds,
        "memory_limit_mib":int(limits.expanded_max_memory_mib),"peak_traced_memory_mib":round(peak_mib,3),
        "elapsed_seconds":round(elapsed,6),"hard_signature_before":list(hard_start),
        "hard_signature_after":list(_hard_population_signature(_district_pops(result,units),floor=floor,cap=cap,district_floors=district_floors))}


def repair(
    *,assignments,units,adjacency,target,tolerance,floor,cap,limits=None,
    district_floors=None,frozen_assignments=None
):
    """Búsqueda best-first + reparación focal bajo un único presupuesto temporal y de candidatos."""
    limits=limits or SearchLimits(); start=time.monotonic(); deadline=start+float(limits.max_seconds)
    expanded_deadline=start+max(0.0,min(float(limits.expanded_max_seconds),180.0))
    examined=0; primary_transitions_evaluated=0; created=1; secondary_only=0
    baseline=dict(assignments); baseline_pops=_district_pops(baseline,units); baseline_tm=territorial_metrics(baseline,adjacency)
    baseline_obj=objective(
        baseline_pops,target=target,tolerance=tolerance,floor=floor,cap=cap,
        cohesion=baseline_tm["cut_boundary_edges"],district_floors=district_floors
    )
    baseline_outliers=baseline_obj[1]
    baseline_hard=_hard_population_signature(
        baseline_pops,floor=floor,cap=cap,district_floors=district_floors
    )
    # Ante violaciones duras, la primaria conserva una fracción acotada para
    # capturar mejoras directas o por conjuntos conectados; la mayoría del
    # presupuesto y del tiempo queda reservada para cadenas focales.
    total_candidate_budget=max(0,min(int(limits.max_candidates),int(limits.expanded_max_candidates),400000))
    if baseline_hard[0] > 0:
        primary_budget=min(total_candidate_budget,int(limits.max_candidates))//4
        primary_deadline=start+(float(limits.max_seconds)*0.25)
    else:
        primary_budget=(
            total_candidate_budget - total_candidate_budget//2
            if baseline_outliers else total_candidate_budget
        )
        primary_deadline=deadline
    best_primary=None; rejected=[]; rejection_counts={}; depth_exhausted=0; seen={_state_key(baseline)}; heap=[]
    baseline_rank,_=_rank(
        baseline,[],units,adjacency,target,tolerance,floor,cap,district_floors
    )
    rank=baseline_rank; heapq.heappush(heap,(rank,0,baseline,[]))
    serial=0; termination="QUEUE_EMPTY"
    while heap:
        if primary_transitions_evaluated>=primary_budget: termination="PRIMARY_BUDGET_RESERVED_FOR_FOCAL"; break
        if time.monotonic()>=primary_deadline:
            termination="PRIMARY_TIME_RESERVED_FOR_FOCAL" if primary_deadline < deadline else "TIME_BUDGET_EXHAUSTED"
            break
        _,_,state,path=heapq.heappop(heap)
        if len(path)>=limits.max_depth:
            depth_exhausted+=1
            continue
        relevant=_relevant_districts(state,units,adjacency,target,tolerance,limits.max_depth-len(path))
        districts=sorted(relevant,key=str)
        pairs=[]
        current_out=_outliers(_district_pops(state,units),target,tolerance)
        for a in districts:
            for b in districts:
                if a==b: continue
                pri=0 if a in current_out or b in current_out else 1
                pairs.append((pri,str(a),str(b),a,b))
        pairs.sort(key=lambda x:(x[0],x[1],x[2]))
        for _,_,_,donor,receiver in pairs:
            for moved in _boundary_sets(state,adjacency,donor,receiver,limits.max_transfer_set):
                if primary_transitions_evaluated>=primary_budget: termination="PRIMARY_BUDGET_RESERVED_FOR_FOCAL"; break
                if time.monotonic()>=primary_deadline:
                    termination="PRIMARY_TIME_RESERVED_FOR_FOCAL" if primary_deadline < deadline else "TIME_BUDGET_EXHAUSTED"
                    break
                primary_transitions_evaluated+=1
                ok,reason,checks=_valid_transfer(
                    state,units,adjacency,moved,donor,receiver,
                    floor=floor,cap=cap,district_floors=district_floors
                )
                frozen_districts=set((frozen_assignments or {}).values())
                if donor in frozen_districts or receiver in frozen_districts or any(u in (frozen_assignments or {}) for u in moved):
                    rejection_counts["FROZEN_URBAN_PROTECTED"]=rejection_counts.get("FROZEN_URBAN_PROTECTED",0)+1
                    continue
                if not ok:
                    rejection_counts[reason]=rejection_counts.get(reason,0)+1
                    if len(rejected)<100: rejected.append({"units":sorted(moved,key=str),"districts":[donor,receiver],"reason":reason,**checks})
                    continue
                examined+=1
                trial=dict(state)
                for u in moved: trial[u]=receiver
                key=_state_key(trial)
                if key in seen: continue
                seen.add(key); step=_step_evidence(
                    state,trial,units,adjacency,moved,donor,receiver,checks,
                    target=target,tolerance=tolerance,floor=floor,cap=cap,
                    district_floors=district_floors,
                )
                new_path=path+[step]; rank,obj=_rank(
                    trial,new_path,units,adjacency,target,tolerance,floor,cap,district_floors
                ); created+=1
                primary_improves=(
                    (baseline_hard[0] > 0 and rank[:-1] < baseline_rank[:-1])
                    or _primary_improves(obj,baseline_obj)
                )
                if primary_improves:
                    candidate=(rank,trial,new_path,obj)
                    if best_primary is None or rank < best_primary[0]: best_primary=candidate
                elif obj < baseline_obj: secondary_only += 1
                if len(new_path)<limits.max_depth:
                    serial+=1; heapq.heappush(heap,(rank,serial,trial,new_path))
            if termination in {"PRIMARY_BUDGET_RESERVED_FOR_FOCAL","PRIMARY_TIME_RESERVED_FOR_FOCAL","TIME_BUDGET_EXHAUSTED"}: break
        if termination in {"PRIMARY_BUDGET_RESERVED_FOR_FOCAL","PRIMARY_TIME_RESERVED_FOR_FOCAL","TIME_BUDGET_EXHAUSTED"}: break

    if best_primary is None:
        best_state=baseline; best_path=[]; best_obj=baseline_obj; status=RESULT_NONE; baseline_restored=True
    else:
        _,best_state,best_path,best_obj=best_primary
        status=RESULT_REPAIRED if best_obj[1]==0 else RESULT_IMPROVED; baseline_restored=False

    focal_meta={"enabled":False,"complete":best_obj[1]==0,"candidate_budget":0,"candidate_attempts":0,
        "transitions_evaluated":0,"states_explored":0,"termination_reason":"NOT_NEEDED","elapsed_seconds":0.0,"provinces":[],
        "rejection_counts":{},"rejection_classification":{}}
    remaining_candidates=max(0,total_candidate_budget-primary_transitions_evaluated)
    if best_obj[1] != 0 and remaining_candidates>0 and time.monotonic()<deadline:
        focal_state,focal_steps,focal_meta=_focal_chain_search(
            state=best_state,units=units,adjacency=adjacency,target=target,tolerance=tolerance,
            floor=floor,cap=cap,limits=limits,deadline=deadline,
            candidate_budget=remaining_candidates,district_floors=district_floors,
            frozen_assignments=frozen_assignments)
        focal_pops=_district_pops(focal_state,units); focal_tm=territorial_metrics(focal_state,adjacency)
        focal_obj=objective(
            focal_pops,target=target,tolerance=tolerance,floor=floor,cap=cap,
            cohesion=focal_tm["cut_boundary_edges"],district_floors=district_floors
        )
        focal_hard=_hard_population_signature(focal_pops,floor=floor,cap=cap,district_floors=district_floors)
        best_hard=_hard_population_signature(_district_pops(best_state,units),floor=floor,cap=cap,district_floors=district_floors)
        if focal_hard < best_hard or (focal_hard == best_hard and focal_obj < best_obj):
            best_state=focal_state; best_path=best_path+focal_steps; best_obj=focal_obj
            status=RESULT_REPAIRED if best_obj[1]==0 else RESULT_IMPROVED; baseline_restored=False

    expanded_meta={"enabled":False,"complete":False,"termination_reason":"NOT_NEEDED"}
    current_hard=_hard_population_signature(_district_pops(best_state,units),floor=floor,cap=cap,district_floors=district_floors)
    if baseline_hard[0]>0 and current_hard[0]>0:
        expanded_state,expanded_steps,expanded_meta=_expanded_hard_search(
            state=best_state,units=units,adjacency=adjacency,target=target,tolerance=tolerance,
            floor=floor,cap=cap,limits=limits,district_floors=district_floors,
            frozen_assignments=frozen_assignments,
            deadline=expanded_deadline,
            candidate_budget=max(0,total_candidate_budget-primary_transitions_evaluated-
                int(focal_meta.get("candidate_attempts",0))))
        expanded_hard=_hard_population_signature(_district_pops(expanded_state,units),floor=floor,cap=cap,district_floors=district_floors)
        if expanded_hard[0]==0:
            best_state=expanded_state; best_path=best_path+expanded_steps
            best_obj=objective(_district_pops(best_state,units),target=target,tolerance=tolerance,
                floor=floor,cap=cap,cohesion=territorial_metrics(best_state,adjacency)["cut_boundary_edges"],
                district_floors=district_floors)
            status=RESULT_REPAIRED; baseline_restored=False

    focal_attempts=int(focal_meta.get("candidate_attempts",0))
    total_candidates=primary_transitions_evaluated+int(focal_meta.get("candidate_attempts",0))+int(expanded_meta.get("candidate_attempts",0))
    elapsed=time.monotonic()-start
    if expanded_meta.get("enabled") and best_obj[1] != 0:
        termination=expanded_meta.get("termination_reason") or "QUEUE_EMPTY"
        if expanded_meta.get("outcome")=="INCONCLUSIVE" and termination=="QUEUE_EMPTY":
            termination="INCONCLUSIVE_BEAM_PRUNED"
    elif elapsed>=max(float(limits.max_seconds),float(limits.expanded_max_seconds)) and best_obj[1] != 0:
        termination="TIME_BUDGET_EXHAUSTED"
    elif total_candidates>=total_candidate_budget and best_obj[1] != 0:
        termination="CANDIDATE_BUDGET_EXHAUSTED"
    elif focal_meta.get("enabled") and best_obj[1] != 0:
        # Una vez ejecutada la fase focal, su causa de terminación describe
        # el estado final de la búsqueda. La reserva de presupuesto de la
        # primaria es un detalle intermedio y no debe sobrevivir como razón
        # final cuando la focal sí consumió ese relevo.
        termination=focal_meta.get("termination_reason") or "QUEUE_EMPTY"

    rejection_counts["DEPTH_EXHAUSTED"]=rejection_counts.get("DEPTH_EXHAUSTED",0)+depth_exhausted
    for reason,count in (focal_meta.get("rejection_counts") or {}).items():
        rejection_counts[reason]=rejection_counts.get(reason,0)+int(count)
    rejection_classification={
        "contiguity": rejection_counts.get("DONOR_CONTIGUITY",0)+rejection_counts.get("RECEIVER_CONTIGUITY",0)+rejection_counts.get("TRANSFER_SET_DISCONNECTED",0),
        "population_limit": rejection_counts.get("HARD_POPULATION_LIMIT",0)+rejection_counts.get("POPULATION_REGRESSION",0),
        "cross_province": rejection_counts.get("CROSS_PROVINCE",0),
        "municipal_integrity": rejection_counts.get("MUNICIPAL_INTEGRITY",0),
        "depth_exhaustion": rejection_counts.get("DEPTH_EXHAUSTED",0),
    }
    final_pops=_district_pops(best_state,units); final_tm=territorial_metrics(best_state,adjacency,boundary_units_moved=sum(len(s["units"]) for s in best_path))
    final_hard=_hard_population_signature(
        final_pops,floor=floor,cap=cap,district_floors=district_floors
    )
    final_verification=_verify_final_constraints(
        best_state,units,adjacency,
        expected_districts=set(baseline.values()),
        floor=floor,cap=cap,district_floors=district_floors,
    )
    if baseline_hard[0] > 0 and final_hard[0] == 0:
        termination="HARD_LIMITS_REPAIRED"
        status=RESULT_REPAIRED
    elif baseline_hard[0] == 0 and baseline_outliers > 0 and best_obj[1] == 0:
        termination="TARGET_TOLERANCE_REPAIRED"
    if not final_verification.get("valid"):
        raise RuntimeError(f"M05 repair produjo estado estructuralmente inválido: {final_verification}")
    if any(best_state.get(u)!=d for u,d in (frozen_assignments or {}).items()):
        raise RuntimeError("M05 repair modificó una unidad urbana congelada")
    affected=sorted({d for s in best_path for d in (s["donor"],s["receiver"])},key=str)
    floor_overrides={
        str(district):float(value)
        for district,value in sorted((district_floors or {}).items(),key=lambda item:str(item[0]))
        if float(value)!=float(floor)
    }
    return {"schema":"ddd.m05-population-repair/1.9","result":status,"limits":asdict(limits),
        "hard_population_floor":float(floor),"hard_population_cap":float(cap),
        "district_floor_overrides":floor_overrides,
        "candidates_examined":total_candidates,"candidate_attempts_total":total_candidates,
        "candidate_limit":total_candidate_budget,"primary_candidates_examined":examined,
        "primary_candidate_budget":primary_budget,
        "primary_transitions_evaluated":primary_transitions_evaluated,
        "transitions_evaluated":primary_transitions_evaluated+int(focal_meta.get("transitions_evaluated",0)),
        "termination_reason":termination,"elapsed_seconds":round(elapsed,6),"queue_states_created":created,"queue_states_examined":examined,
        "primary_improvement_found":best_primary is not None,"secondary_only_candidates":secondary_only,"baseline_restored":baseline_restored,
        # objective_* mantiene el contrato durable histórico de cinco posiciones.
        # La magnitud dura pertenece al ranking interno y se expone por separado.
        "objective_hierarchy":["hard_violation_count","outliers","max_deviation","total_deviation","cohesion"],"queue_priority":["hard_violation_count","hard_violation_magnitude","outliers","max_deviation","outlier_distance_to_tolerance","total_deviation","cohesion","units_moved","districts_affected","chain_length","depth","deterministic_key"],
        "objective_before":list(baseline_obj),"objective_after":list(best_obj),
        "hard_signature_before":list(baseline_hard),"hard_signature_after":list(final_hard),
        "hard_violation_magnitude_before":int(baseline_hard[1]),"hard_violation_magnitude_after":int(final_hard[1]),
        "territorial_metrics_before":baseline_tm,"territorial_metrics_after":final_tm,
        "population_before":baseline_pops,"population_after":final_pops,"populations_before":baseline_pops,"populations_after":final_pops,"assignments":best_state,
        "hard_limits_met":bool(final_verification["hard_limits_met"]),
        "final_hard_population_violations":int(final_verification["hard_population_violations"]),
        "final_hard_violation_magnitude":int(final_hard[1]),
        "controlled_improvement_verified":all(bool(step.get("population_transition_verified",False)) for step in best_path),
        "repairs":best_path,"districts_affected":affected,
        "constraints_checked":["EXACT_DISTRICT_COUNT","PROVINCE","CONTIGUITY","ATOMIC_UNITS","MUNICIPAL_INTEGRITY","FROZEN_URBAN","HARD_POPULATION_LIMITS_FINAL"],
        "constraints_verified":[
            "EXACT_DISTRICT_COUNT","PROVINCE","CONTIGUITY","ATOMIC_UNITS","MUNICIPAL_INTEGRITY","FROZEN_URBAN",
            *(["HARD_POPULATION_LIMITS_FINAL"] if final_verification["hard_limits_met"] else []),
        ],
        "territorial_metric_availability":{"cut_boundary_edges":True,"boundary_units_moved":True,"corridor_penalty":False,"base_compactness":False},
        "focal_search":focal_meta,
        "expanded_hard_search":expanded_meta,
        "rejection_counts":rejection_counts,"rejection_classification":rejection_classification,
        "rejections":rejected,"baseline_preserved":best_state==baseline}

