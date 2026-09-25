#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""M05: reparación poblacional genérica, dirigida, acotada y determinista."""
from __future__ import annotations

from collections import deque
from dataclasses import asdict, dataclass
import heapq
import time

RESULT_REPAIRED = "REPAIRED"
RESULT_IMPROVED = "IMPROVED_NOT_REPAIRED"
RESULT_NONE = "NO_FEASIBLE_REPAIR_FOUND"


@dataclass(frozen=True)
class SearchLimits:
    max_depth: int = 3
    max_transfer_set: int = 2
    max_candidates: int = 5000
    max_seconds: float = 5.0
    seed: int = 0


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


def objective(populations, *, target, tolerance, floor, cap, cohesion=0):
    vals=list(populations.values())
    hard=sum(p < floor or p > cap for p in vals)
    outside=sum(abs(p-target) > tolerance for p in vals)
    maxdev=max((abs(p-target)/target for p in vals),default=0.0)
    totaldev=sum(abs(p-target)/target for p in vals)
    return (hard,outside,round(maxdev,12),round(totaldev,12),int(cohesion))


def _hard_population_signature(populations, *, floor, cap):
    hard_count = 0
    hard_magnitude = 0
    for population in populations.values():
        if population < floor:
            hard_count += 1
            hard_magnitude += floor - population
        elif population > cap:
            hard_count += 1
            hard_magnitude += population - cap
    return (int(hard_count), int(hard_magnitude))


def _controlled_population_transition(before, after, *, floor, cap):
    """Never worsen hard floor/cap compliance while a multi-step repair is in flight."""
    before_sig = _hard_population_signature(before, floor=floor, cap=cap)
    after_sig = _hard_population_signature(after, floor=floor, cap=cap)
    return after_sig <= before_sig, before_sig, after_sig


def _verify_final_constraints(state, units, adjacency, *, expected_districts, floor, cap):
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
    hard_count, hard_magnitude = _hard_population_signature(populations, floor=floor, cap=cap)
    return {
        "valid": True,
        "hard_limits_met": hard_count == 0,
        "hard_population_violations": hard_count,
        "hard_violation_magnitude": hard_magnitude,
        "populations": populations,
    }


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


def _valid_transfer(state,units,adjacency,moved,donor,receiver,*,floor,cap):
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
    controlled,before_sig,after_sig=_controlled_population_transition(before_pops,after_pops,floor=floor,cap=cap)
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


def _step_evidence(state,trial,units,adjacency,moved,donor,receiver,checks,*,target,tolerance,floor,cap):
    before=_district_pops(state,units); after=_district_pops(trial,units); tm=territorial_metrics(trial,adjacency,boundary_units_moved=len(moved))
    obj=objective(after,target=target,tolerance=tolerance,floor=floor,cap=cap,cohesion=tm["cut_boundary_edges"])
    return {"units":sorted(moved,key=str),"donor":donor,"receiver":receiver,"population_before":before,"population_after":after,
        "deviation_before":_deviations(before,target),"deviation_after":_deviations(after,target),"objective_after_step":list(obj),
        "territorial_metrics":tm,**checks,"reason":"ACCEPTED_VALID_CANDIDATE"}


def _state_key(state): return tuple(sorted(state.items(),key=lambda x:str(x[0])))


def _churn(path):
    units=sum(len(s["units"]) for s in path); districts=len({d for s in path for d in (s["donor"],s["receiver"])})
    return (units,districts,len(path))


def _rank(state,path,units,adjacency,target,tolerance,floor,cap):
    pops=_district_pops(state,units); tm=territorial_metrics(state,adjacency); obj=objective(pops,target=target,tolerance=tolerance,floor=floor,cap=cap,cohesion=tm["cut_boundary_edges"])
    hard_count,hard_magnitude=_hard_population_signature(pops,floor=floor,cap=cap)
    return (hard_count,hard_magnitude,obj[1],obj[2],_outlier_distance(pops,target,tolerance),obj[3],obj[4],*_churn(path),len(path),_state_key(state)),obj


def _province_rank_from_pops(pops,districts,target,tolerance,floor,cap):
    selected={d:pops[d] for d in districts}
    hard_count,hard_magnitude=_hard_population_signature(selected,floor=floor,cap=cap)
    outliers={d for d in districts if abs(pops[d]-target)>tolerance}
    distance=round(sum(max(0,abs(pops[d]-target)-tolerance) for d in districts)/target,12)
    maxdev=round(max((abs(pops[d]-target)/target for d in outliers),default=0.0),12)
    totaldev=round(sum(abs(pops[d]-target)/target for d in districts),12)
    return (hard_count,hard_magnitude,len(outliers),distance,maxdev,totaldev),outliers


def _province_state_key(state,units,province):
    return tuple(sorted(((u,state[u]) for u in state if str(units[u].get("province"))==province),key=lambda x:str(x[0])))


def _focal_single_transfer(state,pops,province_units,units,adjacency,u,donor,receiver,*,floor,cap):
    checks={"province_verified":True,"donor_contiguity_verified":False,
        "receiver_contiguity_verified":True,"atomic_units_verified":True,"municipal_integrity_verified":False}
    group=units[u].get("municipality_group")
    if group:
        owned={v for v in province_units if state[v]==donor and units[v].get("municipality_group")==group}
        if owned and owned != {u}: return False,"MUNICIPAL_INTEGRITY",checks
    checks["municipal_integrity_verified"]=True
    donor_nodes={v for v in province_units if state[v]==donor and v!=u}
    if not donor_nodes or not connected(donor_nodes,adjacency): return False,"DONOR_CONTIGUITY",checks
    checks["donor_contiguity_verified"]=True
    after_donor=pops[donor]-int(units[u]["population"]); after_receiver=pops[receiver]+int(units[u]["population"])
    trial_pops=dict(pops); trial_pops[donor]=after_donor; trial_pops[receiver]=after_receiver
    controlled,before_sig,after_sig=_controlled_population_transition(pops,trial_pops,floor=floor,cap=cap)
    checks["population_transition_verified"]=controlled
    checks["hard_signature_before"]=list(before_sig)
    checks["hard_signature_after"]=list(after_sig)
    if not controlled:
        return False,"POPULATION_REGRESSION",checks
    return True,"VALID",checks


def _focal_chain_search(*,state,units,adjacency,target,tolerance,floor,cap,limits,deadline,candidate_budget):
    """Beam search focal: presupuesto global, tiempo real y estados exclusivamente provinciales."""
    phase_start=time.monotonic()
    working=dict(state); all_steps=[]; candidate_attempts=0; states_explored=0
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
        start_rank,start_outliers=_province_rank_from_pops(start_pops,districts,target,tolerance,floor,cap)
        if not start_outliers: continue
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
                if rank[0]==0 and rank[2]==0:
                    found=(current,pops,path,rank); break
                if depth>=depth_limit:
                    depth_exhausted+=1; continue
                _,outliers=_province_rank_from_pops(pops,districts,target,tolerance,floor,cap)
                for u in province_units:
                    donor=current[u]
                    receivers=sorted({current[v] for v in adjacency.get(u,()) if v in current and current[v]!=donor},key=str)
                    for receiver in receivers:
                        if candidate_attempts>=candidate_budget:
                            termination="CANDIDATE_BUDGET_EXHAUSTED"; break
                        if time.monotonic()>=deadline:
                            termination="TIME_BUDGET_EXHAUSTED"; break
                        donor_high=donor in outliers and pops[donor] > target+tolerance
                        receiver_low=receiver in outliers and pops[receiver] < target-tolerance
                        if not (donor_high or receiver_low): continue
                        candidate_attempts+=1
                        ok,reason,checks=_focal_single_transfer(current,pops,province_units,units,adjacency,u,donor,receiver,floor=floor,cap=cap)
                        if not ok:
                            rejection_counts[reason]=rejection_counts.get(reason,0)+1
                            continue
                        trial_pops=dict(pops); delta=int(units[u]["population"])
                        trial_pops[donor]-=delta; trial_pops[receiver]+=delta
                        trial_rank,trial_outliers=_province_rank_from_pops(trial_pops,districts,target,tolerance,floor,cap)
                        if len(trial_outliers)>len(outliers)+1: continue
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
        report={"province":province,"outliers_before":len(start_outliers),"depth_limit":depth_limit,
                "beam_width":beam_width,"states_explored":province_states,
                "depth_exhausted_states":depth_exhausted,"repaired":found is not None}
        if found is not None:
            found_local,_,moves,final_rank=found
            replay=dict(working); steps=[]
            for u,donor,receiver,checks in moves:
                trial=dict(replay); trial[u]=receiver
                steps.append(_step_evidence(replay,trial,units,adjacency,(u,),donor,receiver,checks,target=target,tolerance=tolerance,floor=floor,cap=cap))
                replay=trial
            for u,d in found_local.items(): working[u]=d
            all_steps.extend(steps); report["outliers_after"]=final_rank[2]
        else:
            report["outliers_after"]=start_rank[0]
        province_reports.append(report)
        if termination.endswith("EXHAUSTED"): break
    final_pops=_district_pops(working,units)
    final_hard=_hard_population_signature(final_pops,floor=floor,cap=cap)
    complete=final_hard[0]==0 and not _outliers(final_pops,target,tolerance)
    elapsed=time.monotonic()-phase_start
    classification={
        "contiguity": rejection_counts.get("DONOR_CONTIGUITY",0)+rejection_counts.get("RECEIVER_CONTIGUITY",0)+rejection_counts.get("TRANSFER_SET_DISCONNECTED",0),
        "population_limit": rejection_counts.get("HARD_POPULATION_LIMIT",0)+rejection_counts.get("POPULATION_REGRESSION",0),
        "cross_province": rejection_counts.get("CROSS_PROVINCE",0),
        "municipal_integrity": rejection_counts.get("MUNICIPAL_INTEGRITY",0),
        "depth_exhaustion": rejection_counts.get("DEPTH_EXHAUSTED",0),
    }
    return working,all_steps,{"enabled":True,"complete":complete,"candidate_budget":candidate_budget,
        "candidate_attempts":candidate_attempts,"states_explored":states_explored,"termination_reason":termination,
        "elapsed_seconds":round(elapsed,6),"provinces":province_reports,"rejection_counts":rejection_counts,
        "rejection_classification":classification}


def repair(*,assignments,units,adjacency,target,tolerance,floor,cap,limits=None):
    """Búsqueda best-first + reparación focal bajo un único presupuesto temporal y de candidatos."""
    limits=limits or SearchLimits(); start=time.monotonic(); deadline=start+float(limits.max_seconds)
    examined=0; created=1; secondary_only=0
    baseline=dict(assignments); baseline_pops=_district_pops(baseline,units); baseline_tm=territorial_metrics(baseline,adjacency)
    baseline_obj=objective(baseline_pops,target=target,tolerance=tolerance,floor=floor,cap=cap,cohesion=baseline_tm["cut_boundary_edges"])
    baseline_outliers=baseline_obj[1]
    reserve_for_focal=(int(limits.max_candidates)//2) if baseline_outliers else 0
    primary_budget=max(0,int(limits.max_candidates)-reserve_for_focal)
    best_primary=None; rejected=[]; rejection_counts={}; depth_exhausted=0; seen={_state_key(baseline)}; heap=[]
    rank,_=_rank(baseline,[],units,adjacency,target,tolerance,floor,cap); heapq.heappush(heap,(rank,0,baseline,[]))
    serial=0; termination="QUEUE_EMPTY"
    while heap:
        if examined>=primary_budget: termination="PRIMARY_BUDGET_RESERVED_FOR_FOCAL"; break
        if time.monotonic()>=deadline: termination="TIME_BUDGET_EXHAUSTED"; break
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
                if examined>=primary_budget: termination="PRIMARY_BUDGET_RESERVED_FOR_FOCAL"; break
                if time.monotonic()>=deadline: termination="TIME_BUDGET_EXHAUSTED"; break
                examined+=1
                ok,reason,checks=_valid_transfer(state,units,adjacency,moved,donor,receiver,floor=floor,cap=cap)
                if not ok:
                    rejection_counts[reason]=rejection_counts.get(reason,0)+1
                    if len(rejected)<100: rejected.append({"units":sorted(moved,key=str),"districts":[donor,receiver],"reason":reason,**checks})
                    continue
                trial=dict(state)
                for u in moved: trial[u]=receiver
                key=_state_key(trial)
                if key in seen: continue
                seen.add(key); step=_step_evidence(state,trial,units,adjacency,moved,donor,receiver,checks,target=target,tolerance=tolerance,floor=floor,cap=cap)
                new_path=path+[step]; rank,obj=_rank(trial,new_path,units,adjacency,target,tolerance,floor,cap); created+=1
                if _primary_improves(obj,baseline_obj):
                    candidate=(rank,trial,new_path,obj)
                    if best_primary is None or rank < best_primary[0]: best_primary=candidate
                elif obj < baseline_obj: secondary_only += 1
                if len(new_path)<limits.max_depth:
                    serial+=1; heapq.heappush(heap,(rank,serial,trial,new_path))
            if termination in {"PRIMARY_BUDGET_RESERVED_FOR_FOCAL","TIME_BUDGET_EXHAUSTED"}: break
        if termination in {"PRIMARY_BUDGET_RESERVED_FOR_FOCAL","TIME_BUDGET_EXHAUSTED"}: break

    if best_primary is None:
        best_state=baseline; best_path=[]; best_obj=baseline_obj; status=RESULT_NONE; baseline_restored=True
    else:
        _,best_state,best_path,best_obj=best_primary
        status=RESULT_REPAIRED if best_obj[1]==0 else RESULT_IMPROVED; baseline_restored=False

    focal_meta={"enabled":False,"complete":best_obj[1]==0,"candidate_budget":0,"candidate_attempts":0,
        "states_explored":0,"termination_reason":"NOT_NEEDED","elapsed_seconds":0.0,"provinces":[],
        "rejection_counts":{},"rejection_classification":{}}
    remaining_candidates=max(0,int(limits.max_candidates)-examined)
    if best_obj[1] != 0 and remaining_candidates>0 and time.monotonic()<deadline:
        focal_state,focal_steps,focal_meta=_focal_chain_search(
            state=best_state,units=units,adjacency=adjacency,target=target,tolerance=tolerance,
            floor=floor,cap=cap,limits=limits,deadline=deadline,candidate_budget=remaining_candidates)
        focal_pops=_district_pops(focal_state,units); focal_tm=territorial_metrics(focal_state,adjacency)
        focal_obj=objective(focal_pops,target=target,tolerance=tolerance,floor=floor,cap=cap,cohesion=focal_tm["cut_boundary_edges"])
        if focal_obj < best_obj or focal_obj[1]==0:
            best_state=focal_state; best_path=best_path+focal_steps; best_obj=focal_obj
            status=RESULT_REPAIRED if best_obj[1]==0 else RESULT_IMPROVED; baseline_restored=False

    focal_attempts=int(focal_meta.get("candidate_attempts",0))
    total_candidates=examined+focal_attempts
    elapsed=time.monotonic()-start
    if elapsed>=limits.max_seconds and best_obj[1] != 0:
        termination="TIME_BUDGET_EXHAUSTED"
    elif total_candidates>=limits.max_candidates and best_obj[1] != 0:
        termination="CANDIDATE_BUDGET_EXHAUSTED"
    elif focal_meta.get("termination_reason") not in {None,"NOT_NEEDED","QUEUE_EMPTY"} and best_obj[1] != 0:
        termination=focal_meta["termination_reason"]

    rejection_counts["DEPTH_EXHAUSTED"]=rejection_counts.get("DEPTH_EXHAUSTED",0)+depth_exhausted
    for reason,count in (focal_meta.get("rejection_counts") or {}).items():
        rejection_counts[reason]=rejection_counts.get(reason,0)+int(count)
    rejection_classification={
        "contiguity": rejection_counts.get("DONOR_CONTIGUITY",0)+rejection_counts.get("RECEIVER_CONTIGUITY",0)+rejection_counts.get("TRANSFER_SET_DISCONNECTED",0),
        "population_limit": rejection_counts.get("HARD_POPULATION_LIMIT",0),
        "cross_province": rejection_counts.get("CROSS_PROVINCE",0),
        "municipal_integrity": rejection_counts.get("MUNICIPAL_INTEGRITY",0),
        "depth_exhaustion": rejection_counts.get("DEPTH_EXHAUSTED",0),
    }
    final_pops=_district_pops(best_state,units); final_tm=territorial_metrics(best_state,adjacency,boundary_units_moved=sum(len(s["units"]) for s in best_path))
    final_verification=_verify_final_constraints(
        best_state,units,adjacency,
        expected_districts=set(baseline.values()),
        floor=floor,cap=cap,
    )
    if not final_verification.get("valid"):
        raise RuntimeError(f"M05 repair produjo estado estructuralmente inválido: {final_verification}")
    affected=sorted({d for s in best_path for d in (s["donor"],s["receiver"])},key=str)
    return {"schema":"ddd.m05-population-repair/1.5","result":status,"limits":asdict(limits),
        "candidates_examined":total_candidates,"primary_candidates_examined":examined,
        "termination_reason":termination,"elapsed_seconds":round(elapsed,6),"queue_states_created":created,"queue_states_examined":examined,
        "primary_improvement_found":best_primary is not None,"secondary_only_candidates":secondary_only,"baseline_restored":baseline_restored,
        "objective_hierarchy":["hard_constraints","outliers","max_deviation","total_deviation","cohesion"],"queue_priority":["outliers","max_deviation","outlier_distance_to_tolerance","total_deviation","cohesion","units_moved","districts_affected","chain_length","depth","deterministic_key"],
        "objective_before":list(baseline_obj),"objective_after":list(best_obj),"territorial_metrics_before":baseline_tm,"territorial_metrics_after":final_tm,
        "population_before":baseline_pops,"population_after":final_pops,"populations_before":baseline_pops,"populations_after":final_pops,"assignments":best_state,
        "hard_limits_met":bool(final_verification["hard_limits_met"]),
        "final_hard_population_violations":int(final_verification["hard_population_violations"]),
        "final_hard_violation_magnitude":int(final_verification["hard_violation_magnitude"]),
        "controlled_improvement_verified":all(bool(step.get("population_transition_verified",False)) for step in best_path),
        "repairs":best_path,"districts_affected":affected,"constraints_verified":["EXACT_DISTRICT_COUNT","PROVINCE","CONTIGUITY","ATOMIC_UNITS","MUNICIPAL_INTEGRITY","HARD_POPULATION_LIMITS_FINAL"],
        "territorial_metric_availability":{"cut_boundary_edges":True,"boundary_units_moved":True,"corridor_penalty":False,"base_compactness":False},
        "focal_search":focal_meta,"rejection_counts":rejection_counts,"rejection_classification":rejection_classification,
        "rejections":rejected,"baseline_preserved":best_state==baseline}

