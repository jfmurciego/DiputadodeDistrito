#!/usr/bin/env python3
"""Research-only rooted connectivity-cut MILP for the authenticated PV M04."""
from __future__ import annotations

import collections
import hashlib
import json
import math
import os
import pathlib
import resource
import time
import zipfile

import numpy as np
import scipy
from scipy.optimize import Bounds, LinearConstraint, milp
from scipy.sparse import coo_matrix
from connectivity_cut import rooted_cut_terms

EVIDENCE = pathlib.Path('/Users/macbookpro/Desarrollo/DDD_PV_A2_G1_EVIDENCIAS')
INPUT = EVIDENCE / 'extracted/M04/cache/pais_vasco_2025_m04_semillas.geojson.zip'
GRAPH = EVIDENCE / 'extracted/M03/cache/pais_vasco_2025_m03_grafo.json'
OUT = pathlib.Path(__file__).with_name('rooted_result.json')
ASSIGNMENT_OUT = pathlib.Path(__file__).with_name('rooted_candidate_assignment.json')
MAX_WALL = 120.0
MAX_NODES = 100_000
MAX_RESOLVES = 12
MAX_VMEM = 6 * 1024**3

resource.setrlimit(resource.RLIMIT_AS, (MAX_VMEM, MAX_VMEM))
start = time.monotonic()
cpu_start = time.process_time()

with zipfile.ZipFile(INPUT) as zf:
    geo_name = next(n for n in zf.namelist() if n.endswith('.geojson'))
    geo = json.loads(zf.read(geo_name))
graph_obj = json.loads(GRAPH.read_text())
report = json.loads((EVIDENCE / 'extracted/M04/cache/pais_vasco_2025_m04_informe.json').read_text())

sec_unit = {}
sec_district = {}
sec_pop = {}
units = collections.defaultdict(list)
unit_pop = collections.Counter()
unit_prov = {}
unit_mun = {}
unit_district = {}
unit_frozen = {}
district_prov = {}
district_pop = collections.Counter()
municipality_units = collections.defaultdict(set)
municipality_pop = collections.Counter()

for feature in geo['features']:
    p = feature['properties']
    s = str(p['CUSEC_KEY'])
    u = str(p['ddd_unit_id'])
    d = str(p['district_id'])
    prov = str(p['CPRO']).zfill(2)
    mun = str(p['CUMUN'])
    pop = int(p['POP_2024'])
    if s in sec_unit:
        raise SystemExit(f'duplicate CUSEC {s}')
    sec_unit[s], sec_district[s], sec_pop[s] = u, d, pop
    units[u].append(s)
    unit_pop[u] += pop
    unit_prov[u], unit_mun[u], unit_district[u] = prov, mun, d
    unit_frozen[u] = bool(p.get('ddd_closed_urban', False))
    district_prov[d] = prov
    district_pop[d] += pop
    municipality_units[mun].add(u)
    municipality_pop[mun] += pop

if len(sec_unit) != len(geo['features']) or len(district_pop) != int(report['K']):
    raise SystemExit('M04 identity check failed')
if any(len({unit_mun[u] for u in {sec_unit[s] for s in ss}}) != 1 for ss in units.values()):
    raise SystemExit('an indivisible unit crosses municipalities')

sec_adj = collections.defaultdict(set)
for edge in graph_obj['edges']:
    a, b = str(edge['u']), str(edge['v'])
    sec_adj[a].add(b)
    sec_adj[b].add(a)
unit_adj = {u: set() for u in units}
for s, u in sec_unit.items():
    for t in sec_adj[s]:
        v = sec_unit.get(t)
        if v is not None and v != u and unit_prov[v] == unit_prov[u]:
            unit_adj[u].add(v)
for u, neighbors in unit_adj.items():
    for v in neighbors:
        unit_adj[v].add(u)

K = int(report['K'])
target, floor, cap = float(report['target']), float(report['floor']), float(report['cap'])
tolerance = float(report['tolerance'])
provinces = collections.defaultdict(list)
for d, p in district_prov.items():
    provinces[p].append(d)
for p in provinces:
    provinces[p].sort(key=int)
district_units = collections.defaultdict(set)
for u, d in unit_district.items():
    district_units[d].add(u)
frozen_districts = {d for d, us in district_units.items() if all(unit_frozen[u] for u in us)}
allowed = {}
for u in units:
    d = unit_district[u]
    allowed[u] = [d] if unit_frozen[u] or d in frozen_districts else [d2 for d2 in provinces[unit_prov[u]] if d2 not in frozen_districts]
    if unit_frozen[u] and allowed[u] != [d]:
        raise SystemExit(f'frozen unit is not pinned: {u}')

# Binary assignment/municipality indicators, as in the authenticated experiment 07.
lower, upper, integrality, objective, var_index = [], [], [], [], {}
def var(key, lo=0, hi=1, integer=1, cost=0.0):
    i = len(lower)
    var_index[key] = i
    lower.append(lo); upper.append(hi); integrality.append(integer); objective.append(cost)
    return i

x = {}
for u in sorted(units):
    for d in allowed[u]:
        x[u, d] = var(('x', u, d), cost=0.0 if d == unit_district[u] else 1.0)
root_choice = {}
for u, d in x:
    root_choice[u, d] = var(('root', u, d))
y = {}
municipality_allowed = {m: sorted({d for u in us for d in allowed[u]}, key=int) for m, us in municipality_units.items()}
for m, ds in municipality_allowed.items():
    for d in ds:
        y[m, d] = var(('y', m, d))
mix = {d: var(('mix', d)) for d in sorted(district_pop, key=int)}
z = {}
for m, ds in municipality_allowed.items():
    for d in ds:
        z[m, d] = var(('z', m, d))

base_constraints = []
def add_constraint(terms, lo=-np.inf, hi=np.inf):
    base_constraints.append((terms, float(lo), float(hi)))

for u in sorted(units):
    add_constraint({x[u, d]: 1 for d in allowed[u]}, 1, 1)
for d in sorted(district_pop, key=int):
    add_constraint({x[u, d]: unit_pop[u] for u in units if (u, d) in x}, floor, cap)
    add_constraint({root_choice[u, d]: 1 for u in units if (u, d) in root_choice}, 1, 1)
    for u in units:
        if (u, d) in x:
            add_constraint({root_choice[u, d]: 1, x[u, d]: -1}, hi=0)
for u in units:
    if unit_frozen[u] or unit_district[u] in frozen_districts:
        add_constraint({x[u, unit_district[u]]: 1}, 1, 1)
for m, us in sorted(municipality_units.items()):
    ds = municipality_allowed[m]
    minimum = max(1, math.ceil(municipality_pop[m] / cap))
    maximum = max(1, math.ceil(municipality_pop[m] / target))
    add_constraint({y[m, d]: 1 for d in ds}, minimum, maximum)
    for d in ds:
        xv = [x[u, d] for u in us if (u, d) in x]
        for j in xv:
            add_constraint({j: 1, y[m, d]: -1}, hi=0)
        terms = {y[m, d]: 1}
        terms.update({j: -1 for j in xv})
        add_constraint(terms, hi=0)
for d in sorted(district_pop, key=int):
    ms = [m for m, ds in municipality_allowed.items() if d in ds]
    terms = {y[m, d]: 1 for m in ms}; terms[mix[d]] = -1
    add_constraint(terms, lo=1)
    terms = {y[m, d]: 1 for m in ms}; terms[mix[d]] = -(len(ms) - 1)
    add_constraint(terms, hi=1)
    for m in ms:
        add_constraint({z[m, d]: 1, y[m, d]: -1}, hi=0)
        add_constraint({z[m, d]: 1, mix[d]: -1}, hi=0)
        add_constraint({z[m, d]: 1, y[m, d]: -1, mix[d]: -1}, lo=-1)
for m, ds in municipality_allowed.items():
    add_constraint({z[m, d]: 1 for d in ds}, hi=1)

base_info = {
    'sections': len(sec_unit), 'units': len(units), 'districts': K,
    'population': sum(sec_pop.values()), 'unit_edges': sum(map(len, unit_adj.values())) // 2,
    'frozen_units': sum(unit_frozen.values()), 'fully_frozen_districts': sorted(frozen_districts, key=int),
    'variables': len(lower), 'root_variables': len(root_choice), 'base_constraints': len(base_constraints),
    'M04_zip_sha256': hashlib.sha256(INPUT.read_bytes()).hexdigest(),
    'M03_graph_sha256': hashlib.sha256(GRAPH.read_bytes()).hexdigest(),
    'python': os.sys.version.split()[0], 'numpy': np.__version__, 'scipy': scipy.__version__,
    'budget': {'wall_seconds': MAX_WALL, 'aggregate_nodes': MAX_NODES, 'max_resolves': MAX_RESOLVES, 'virtual_memory_bytes': MAX_VMEM},
}
print('MODEL', json.dumps(base_info, sort_keys=True), flush=True)

def connected_components_for(d, assignment):
    remaining = {u for u, assigned in assignment.items() if assigned == d}
    comps = []
    while remaining:
        root = min(remaining)
        stack = [root]
        remaining.remove(root)
        comp = {root}
        while stack:
            u = stack.pop()
            for v in unit_adj[u] & remaining:
                if assignment.get(v) == d:
                    remaining.remove(v); comp.add(v); stack.append(v)
        comps.append(comp)
    return comps

def make_sparse(constraints):
    rows, cols, vals, lows, highs = [], [], [], [], []
    for r, (terms, lo, hi) in enumerate(constraints):
        for j, value in terms.items():
            if value:
                rows.append(r); cols.append(j); vals.append(float(value))
        lows.append(lo); highs.append(hi)
    A = coo_matrix((vals, (rows, cols)), shape=(len(constraints), len(lower))).tocsr()
    return A, np.asarray(lows), np.asarray(highs)

cuts = []
cut_keys = set()
trace = []
total_nodes = 0
candidate = None
termination = 'MAX_RESOLVES'
for iteration in range(1, MAX_RESOLVES + 1):
    remaining_wall = MAX_WALL - (time.monotonic() - start)
    remaining_nodes = MAX_NODES - total_nodes
    if remaining_wall <= 0 or remaining_nodes <= 0:
        termination = 'BUDGET_EXHAUSTED'
        break
    A, lows, highs = make_sparse(base_constraints + cuts)
    before = time.monotonic()
    res = milp(np.asarray(objective), integrality=np.asarray(integrality),
               bounds=Bounds(np.asarray(lower), np.asarray(upper)),
               constraints=LinearConstraint(A, lows, highs),
               options={'time_limit': remaining_wall, 'node_limit': remaining_nodes, 'mip_rel_gap': 0.0, 'presolve': True})
    solve_seconds = time.monotonic() - before
    nodes = int(getattr(res, 'mip_node_count', 0) or 0)
    total_nodes += nodes
    item = {'iteration': iteration, 'status': int(res.status), 'message': str(res.message), 'solve_seconds': solve_seconds,
            'mip_nodes': nodes, 'objective': None if res.fun is None else float(res.fun),
            'candidate_present': res.x is not None, 'cuts_before': len(cuts)}
    if res.x is None:
        trace.append(item)
        termination = 'SOLVER_NO_INCUMBENT'
        break
    assignment = {}
    for u in units:
        selected = [d for d in allowed[u] if res.x[x[u, d]] > .5]
        if len(selected) != 1:
            raise RuntimeError(f'nonunique assignment for unit {u}: {selected}')
        assignment[u] = selected[0]
    disconnected = []
    for d in sorted(district_pop, key=int):
        comps = connected_components_for(d, assignment)
        if len(comps) > 1:
            comps.sort(key=lambda c: (-len(c), sorted(c)[0]))
            root_unit = next(u for u in units
                             if (u, d) in root_choice and res.x[root_choice[u, d]] > .5)
            for comp in comps:
                if root_unit in comp:
                    continue
                boundary = {v for u in comp for v in unit_adj[u]
                            if v not in comp and unit_prov[v] == district_prov[d] and (v, d) in x}
                key = (d, tuple(sorted(comp)))
                if key in cut_keys:
                    continue
                terms, upper_bound = rooted_cut_terms(
                    comp, boundary,
                    {u: x[u, d] for u in units if (u, d) in x},
                    {u: root_choice[u, d] for u in units if (u, d) in root_choice},
                )
                cuts.append((terms, -np.inf, upper_bound))
                cut_keys.add(key)
                disconnected.append({'district': d, 'component_units': len(comp),
                                     'component_population': sum(unit_pop[u] for u in comp),
                                     'boundary_units': len(boundary), 'root_unit': root_unit,
                                     'cut': len(cuts)})
    pops = collections.Counter()
    for u, d in assignment.items():
        pops[d] += unit_pop[u]
    item.update({'disconnected_districts': len({c['district'] for c in disconnected}), 'components_cut': len(disconnected), 'cuts_after': len(cuts),
                 'units_reassigned': sum(assignment[u] != unit_district[u] for u in units),
                 'hard_violations': {d: p for d, p in pops.items() if not floor <= p <= cap},
                 'component_count_by_district': {d: len(connected_components_for(d, assignment)) for d in sorted(district_pop, key=int)},
                 'component_details': disconnected, 'unit_assignment': assignment})
    trace.append(item)
    if not disconnected:
        candidate = assignment
        termination = 'CONNECTED_CANDIDATE'
        break
    if time.monotonic() - start >= MAX_WALL or total_nodes >= MAX_NODES:
        termination = 'BUDGET_EXHAUSTED'
        break

if candidate is not None:
    pops = collections.Counter()
    for u, d in candidate.items():
        pops[d] += unit_pop[u]
    section_assignment = {s: candidate[u] for s, u in sec_unit.items()}
    assignment_payload = {'unit_assignment': candidate, 'section_assignment': section_assignment}
    assignment_bytes = json.dumps(assignment_payload, sort_keys=True, separators=(',', ':')).encode()
    ASSIGNMENT_OUT.write_bytes(assignment_bytes)
    hard = {d: pops[d] for d in pops if not floor <= pops[d] <= cap}
    moved = sum(candidate[u] != unit_district[u] for u in units)
    payload = {'candidate': True, 'candidate_assignment_sha256': hashlib.sha256(assignment_bytes).hexdigest(),
               'hard_violations': hard, 'K': len(pops), 'total_population': sum(pops.values()),
               'outside_tolerance': sum(abs(v - target) > tolerance for v in pops.values()),
               'unit_moves': moved, 'district_populations': dict(sorted(pops.items(), key=lambda kv: int(kv[0]))),
               'assignment': assignment_payload}
else:
    payload = {'candidate': False}

payload.update({'experiment': 'PV-CUT-02', 'termination': termination, 'trace': trace,
                'total_solver_nodes': total_nodes, 'cuts_total': len(cuts), 'model': base_info,
                'elapsed_wall_seconds': time.monotonic() - start,
                'max_rss_bytes': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * (1 if os.uname().sysname == 'Darwin' else 1024),
                'cpu_seconds': time.process_time() - cpu_start,
                'input_archive_sha256': base_info['M04_zip_sha256'],
                'graph_sha256': base_info['M03_graph_sha256'],
                'script_sha256': hashlib.sha256(pathlib.Path(__file__).read_bytes()).hexdigest()})
OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({k: payload[k] for k in ('candidate','termination','elapsed_wall_seconds','total_solver_nodes','cuts_total','trace','model','script_sha256') if k in payload}, ensure_ascii=False, sort_keys=True))
