#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""M05 v1.1.0 — private annealing repair with atomic admission.

Version: 1.1.0; name: private bounded annealing with municipal discipline; date: 2026-10-29.
Changes 1.1.0: a move is rejected if it increases the split municipalities that have more than one
mixed district (validar_ejecucion R012); Andalucía 40969274807 reached hard=0 and was then rejected
by the official gate with VALIDAR_EJECUCION_FAIL. Predecessor:
legacy/ddd_core/m05_private_annealing_v1.0.0_20261029.py.
Version 1.0.0; name: private bounded annealing; date: 2026-10-11.
Scope: opt-in autonomous M05 repair; status: experimental candidate.
Changes: bounded seeded walk, private transient population violations, final
constraint validation and immutable-origin fallback. Reason: support preparatory
moves without changing the monotone strategy. Predecessor: new component; none.
"""
from __future__ import annotations

from collections import Counter
import math
import random
import time

from ddd_core.m05_population_repair import _district_pops, _verify_final_constraints


def _unit_municipality(unit):
    """Unidades M04 '{partición}:{municipio}:M|R|Un' → municipio; None si no sigue el formato."""
    parts=str(unit).split(":")
    return parts[1] if len(parts)>=3 else None


def _mixed_discipline_violations(municipalities, state, owned, municipality_units):
    """Municipios partidos con más de un distrito mixto (R012 de validar_ejecucion)."""
    bad=0
    for municipality in municipalities:
        districts={state[u] for u in municipality_units.get(municipality,())}
        if len(districts)<=1:
            continue
        mixed=sum(1 for d in districts if len({_unit_municipality(u) for u in owned[d]})>1)
        bad+=mixed>1
    return bad


def repair_private(*, assignments, units, adjacency, target, tolerance, floor, cap,
                   district_floors=None, frozen_units=(), frozen_districts=(),
                   seed=0, max_candidates=700000, max_seconds=65.0):
    original=dict(assignments); keys=sorted(original,key=str); districts=sorted(set(original.values()),key=str)
    frozen_units=set(frozen_units); frozen_districts=set(frozen_districts)
    if (set(keys)!=set(units) or set(keys)!=set(adjacency) or not districts or max_candidates<1 or max_seconds<=0
            or any(not adjacency[u] <= set(keys) for u in keys)):
        return {"result":"INVALID_INPUT","assignments":original,"accepted":False,"candidates":0,"expanded":0,"termination_reason":"INVALID_INPUT"}
    groups={d:{u for u in keys if original[u]==d} for d in districts}
    province={u:str(units[u].get("province")) for u in keys}
    district_province={d:{province[u] for u in keys if original[u]==d} for d in districts}
    if any(len(v)!=1 for v in district_province.values()):
        return {"result":"INVALID_INPUT","assignments":original,"accepted":False,"candidates":0,"expanded":0,"termination_reason":"CROSS_PROVINCE_BASELINE"}
    district_province={d:next(iter(v)) for d,v in district_province.items()}
    base_group={}
    for u in keys:
        group=units[u].get("municipality_group")
        if group: base_group.setdefault(str(group),set()).add(u)
    if any(len({original[u] for u in members})!=1 for members in base_group.values()):
        return {"result":"INVALID_INPUT","assignments":original,"accepted":False,"candidates":0,"expanded":0,"termination_reason":"SPLIT_MUNICIPAL_BASELINE"}
    composite={u for members in base_group.values() if len(members)>1 for u in members}
    pop={u:int(units[u]["population"]) for u in keys}; initial_pops=_district_pops(original,units)
    hard=lambda p,d: max(0.0,(district_floors or {}).get(d,floor)-p,p-cap)
    if not any(hard(p,d)>0 for d,p in initial_pops.items()):
        return {"result":"NOT_NEEDED","assignments":original,"accepted":True,"candidates":0,"expanded":0,"termination_reason":"ALREADY_FEASIBLE"}
    soft_center=math.floor(target*1000)/1000
    soft_width=math.floor(tolerance*100)/100
    def objective(pd,assignment):
        h=sum((hard(p,d)/1000)**2 for d,p in pd.items()); cnt=sum(bool(hard(p,d)) for d,p in pd.items())
        soft=sum(max(0,abs(p-soft_center)-soft_width)/10000 for d,p in pd.items() if d not in frozen_districts)
        churn=sum(assignment[u]!=original[u] for u in keys if u not in frozen_units)
        return h*.85+cnt*4+soft*.025+churn*.008
    def connected(nodes):
        if not nodes:return False
        seen={next(iter(nodes))};todo=list(seen)
        while todo:
            for v in adjacency[todo.pop()]:
                if v in nodes and v not in seen:seen.add(v);todo.append(v)
        return len(seen)==len(nodes)

    rng=random.Random(int(seed)); state=dict(original); owned={d:set(us) for d,us in groups.items()}; pops=dict(initial_pops)
    municipality_units={}
    for u in keys:
        municipality=_unit_municipality(u)
        if municipality: municipality_units.setdefault(municipality,set()).add(u)
    def touched_municipalities(*districts_):
        return {m for d in districts_ for m in (_unit_municipality(u) for u in owned[d]) if m}
    # These counters describe private search states only; they are never written
    # to the checkpoint or catalog. Record transient population violations so
    # reviewers can distinguish preparatory moves from feasible admissions.
    accepted_steps_with_nonzero_hard=0
    max_private_hard_count=sum(hard(p,d)>0 for d,p in pops.items())
    max_private_violation=max((hard(p,d) for d,p in pops.items()), default=0.0)
    score=objective(pops,state); best=(score,dict(state),dict(pops),0); count=accepted=expanded=0; rejects=Counter(); last_improve=0; started=time.monotonic()
    termination="CANDIDATE_BUDGET_EXHAUSTED"
    while count<int(max_candidates) and time.monotonic()-started<float(max_seconds):
        count+=1; unit=rng.choice(keys); donor=state[unit]
        if unit in frozen_units or donor in frozen_districts or unit in composite or len(owned[donor])<=1:
            rejects["IMMOVABLE_OR_SINGLETON"]+=1; continue
        receivers=sorted({state[v] for v in adjacency[unit] if state[v]!=donor and state[v] not in frozen_districts and district_province[state[v]]==province[unit]},key=str)
        if not receivers: rejects["NO_RECEIVER"]+=1; continue
        receiver=rng.choice(receivers)
        if not connected(owned[donor]-{unit}):rejects["DONOR_DISCONNECT"]+=1;continue
        touched=touched_municipalities(donor,receiver)
        discipline_before=_mixed_discipline_violations(touched,state,owned,municipality_units)
        owned[donor].remove(unit);owned[receiver].add(unit);state[unit]=receiver
        discipline_after=_mixed_discipline_violations(touched,state,owned,municipality_units)
        owned[receiver].remove(unit);owned[donor].add(unit);state[unit]=donor
        if discipline_after>discipline_before:
            rejects["MUNICIPAL_DISCIPLINE"]+=1; continue
        expanded+=1; before_d= pops[donor]; before_r=pops[receiver]
        pops[donor]-=pop[unit];pops[receiver]+=pop[unit];state[unit]=receiver
        candidate=objective(pops,state); temp=12*(.97**(accepted/2000))+.5
        if candidate<=score or rng.random()<math.exp(min(0,(score-candidate)/temp)):
            owned[donor].remove(unit);owned[receiver].add(unit);score=candidate;accepted+=1
            private_hard_count=sum(hard(p,d)>0 for d,p in pops.items())
            private_violation=max((hard(p,d) for d,p in pops.items()), default=0.0)
            if private_hard_count:
                accepted_steps_with_nonzero_hard+=1
            max_private_hard_count=max(max_private_hard_count,private_hard_count)
            max_private_violation=max(max_private_violation,private_violation)
            if candidate<best[0]:best=(candidate,dict(state),dict(pops),count);last_improve=count
            if not any(hard(p,d)>0.01 for d,p in pops.items()):
                check=_verify_final_constraints(state,units,adjacency,expected_districts=set(districts),floor=floor,cap=cap,district_floors=district_floors)
                frozen_ok=all(state[u]==original[u] for u in frozen_units)
                if check.get("valid") and check.get("hard_limits_met") and frozen_ok:
                    return {"result":"REPAIRED","assignments":dict(state),"accepted":True,"candidates":count,"generated_candidates":count,"expanded":expanded,"accepted_moves":accepted,"discarded_candidates":count-accepted,"unique_states":None,"pending_states":0,"rejected":dict(rejects),"seed":int(seed),"elapsed_seconds":time.monotonic()-started,"hard_population_violations":0,"accepted_steps_with_nonzero_hard":accepted_steps_with_nonzero_hard,"max_private_hard_count":max_private_hard_count,"max_private_violation":max_private_violation,"final_validation":check,"termination_reason":"HARD_FEASIBLE_ATOMIC_ADMISSION"}
                rejects["FINAL_VALIDATION"]+=1
        else:
            rejects["ANNEALING_SCORE"]+=1
            state[unit]=donor;pops[donor]=before_d;pops[receiver]=before_r
        if count-last_improve>45000 and count%5000==0:
            score,state,pops,_=best;state=dict(state);pops=dict(pops);owned={d:set() for d in districts}
            for u,d in state.items():owned[d].add(u)
            last_improve=count
    if time.monotonic()-started>=float(max_seconds):termination="TIME_BUDGET_EXHAUSTED"
    return {"result":"NO_FEASIBLE_REPAIR_FOUND","assignments":original,"accepted":False,"candidates":count,"generated_candidates":count,"expanded":expanded,"accepted_moves":accepted,"discarded_candidates":count-accepted,"unique_states":None,"pending_states":0,"rejected":dict(rejects),"seed":int(seed),"elapsed_seconds":time.monotonic()-started,"termination_reason":termination,"best_private_score":best[0],"best_private_state_retained":True,"accepted_steps_with_nonzero_hard":accepted_steps_with_nonzero_hard,"max_private_hard_count":max_private_hard_count,"max_private_violation":max_private_violation}
