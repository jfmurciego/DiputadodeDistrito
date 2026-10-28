#!/usr/bin/env python3
"""Independent synthetic mechanisms; no historical code copied. Version 1.0.0."""
import argparse
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import platform
import random
import resource
import statistics
import subprocess
import sys
import time
import tracemalloc

import shapely
from shapely.geometry import box
from shapely import union_all

ROOT = Path(__file__).resolve().parent
DDD = Path('/Users/macbookpro/Desarrollo/DDD-distritos-autonomicos')


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()


def tally(populations, assignment, k):
    sums = [0] * k
    for p, d in zip(populations, assignment):
        sums[d] += p
    return sums


def dissolve(geometries, assignment, k):
    groups = [[] for _ in range(k)]
    for geom, d in zip(geometries, assignment):
        groups[d].append(geom)
    return [union_all(group) for group in groups]


def metrics(pops):
    target = sum(pops) / len(pops)
    deviations = [abs(p - target) for p in pops]
    return {'population': pops, 'target': target, 'L1': sum(deviations),
            'max_relative': max(deviations) / target,
            'std_absolute': statistics.stdev(deviations)}


def verify_grid(assignment, pops, geometries, width, height, k, tolerance):
    assert len(assignment) == width * height == len(pops)
    assert set(assignment) == set(range(k))
    sums = tally(pops, assignment, k)
    assert sum(sums) == sum(pops)
    assert metrics(sums)['max_relative'] <= tolerance + 1e-12
    district_geoms = dissolve(geometries, assignment, k)
    for d, geometry in enumerate(district_geoms):
        assert geometry.geom_type == 'Polygon' and geometry.is_valid
        wanted = {i for i, value in enumerate(assignment) if value == d}
        visited = set()
        stack = [min(wanted)]
        while stack:
            i = stack.pop()
            if i in visited:
                continue
            visited.add(i)
            x, y = i % width, i // width
            neighbors = []
            if x: neighbors.append(i - 1)
            if x + 1 < width: neighbors.append(i + 1)
            if y: neighbors.append(i - width)
            if y + 1 < height: neighbors.append(i + width)
            stack.extend(n for n in neighbors if n in wanted and n not in visited)
        assert visited == wanted
    universe = union_all(district_geoms)
    assert universe.equals(box(0, 0, width, height))
    assert sum(g.area for g in district_geoms) == width * height
    return district_geoms


def ranking_case():
    row = [1150, 950, 950, 950]
    col = [1100, 1100, 900, 900]
    matrix = [[50] * 4 for _ in range(4)]
    r = [p - 200 for p in row]
    c = [p - 200 for p in col]
    for y in range(4):
        for x in range(4):
            amount = min(r[y], c[x])
            matrix[y][x] += amount
            r[y] -= amount
            c[x] -= amount
    pops = [p for line in matrix for p in line]
    geoms = [box(x, y, x+1, y+1) for y in range(4) for x in range(4)]
    assignments = {'A_lower_L1': [y for y in range(4) for x in range(4)],
                   'B_lower_max': [x for y in range(4) for x in range(4)]}
    invalid = list(assignments['A_lower_L1'])
    invalid[4] = invalid[5] = 0
    assignments['C_hard_invalid'] = invalid
    details = {}
    for name, assignment in assignments.items():
        ds = dissolve(geoms, assignment, 4)
        m = metrics(tally(pops, assignment, 4))
        m['shape_polsby_popper_median'] = statistics.median(
            4*math.pi*g.area/(g.length*g.length) for g in ds)
        m['comarca_retention'] = 1.0  # One immutable comarca/municipality per atomic cell.
        m['hard_all_pass'] = m['max_relative'] <= .20
        m['assignment_sha256'] = digest(assignment)
        details[name] = m
        if m['hard_all_pass']:
            verify_grid(assignment, pops, geoms, 4, 4, 4, .20)
    a, b = details['A_lower_L1'], details['B_lower_max']
    assert a['L1'] < b['L1'] and a['max_relative'] > b['max_relative']
    assert a['shape_polsby_popper_median'] == b['shape_polsby_popper_median']
    assert not details['C_hard_invalid']['hard_all_pass']
    reports = ROOT / 'ranking_reports'
    reports.mkdir(exist_ok=True)
    candidates = []
    for name, m in details.items():
        candidates.append({'candidate_id': name, 'profile': 'controlled', 'seed': 0, 'parameters': {}})
        target_dir = reports / name
        target_dir.mkdir(exist_ok=True)
        report = {'candidate_id': name, 'hard_constraints': {'all_pass': m['hard_all_pass']},
                  'assignment_hash': m['assignment_sha256'],
                  'metrics': {'population': {'max_deviation': m['max_relative']},
                              'shape': {'polsby_popper_median': m['shape_polsby_popper_median'], 'corridor_alerts': []},
                              'comarca': {'retention_ratio': 1.0},
                              'stability': {'assignment_delta': 0.0}}}
        (target_dir/'report.json').write_text(json.dumps(report, indent=2))
    plan = {'schema': 'ddd.ensemble-plan/1.0', 'candidates': candidates,
            'profiles': ['controlled'], 'shards': [], 'territory_id': 'SYNTHETIC',
            'prepared_bundle_id': 'synthetic-grid', 'plan_sha256': digest(candidates)}
    plan_path = ROOT/'ranking_plan.json'
    plan_path.write_text(json.dumps(plan, indent=2))
    spec = importlib.util.spec_from_file_location('ddd_assembler_under_test', DDD/'ddd_ensemble/ensemble_assembler.py')
    assembler = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(assembler)
    summary = assembler.assemble(str(plan_path), str(reports), shortlist_size=2)
    assert summary['pareto_candidates'] == ['B_lower_max']
    assert summary['invalid_candidates'] == ['C_hard_invalid']
    assert summary['shortlist'][0] == 'B_lower_max'
    (ROOT/'ensemble_summary.json').write_text(json.dumps(summary, indent=2))
    engine_path = DDD/'ddd_core/m05_gerrychain_engine.py'
    engine_spec = importlib.util.spec_from_file_location('ddd_engine_under_test', engine_path)
    engine = importlib.util.module_from_spec(engine_spec)
    sys.modules[engine_spec.name] = engine
    engine_spec.loader.exec_module(engine)
    ids = [str(i) for i in range(16)]
    edges = []
    for i in range(16):
        if i%4 < 3: edges.append((str(i), str(i+1)))
        if i//4 < 3: edges.append((str(i), str(i+4)))
    data = engine.AdaptedInputs(
        nodes={s: {'population': pops[i], 'province': 'SYNTHETIC', 'municipality': s,
                   'atomic_unit': s, 'closed_urban': False, 'comarca': s}
               for i,s in enumerate(ids)},
        edges=edges, initial_assignment=dict(zip(ids, assignments['A_lower_L1'])),
        geojson={}, section_field='synthetic_id', district_field='district',
        section_areas={s:1.0 for s in ids}, section_perimeters={s:4.0 for s in ids},
        shared_border_lengths={tuple(sorted(e)):1.0 for e in edges},
        section_components={s:(s,) for s in ids}, component_edges=edges)
    contract = engine.Contract(k=4, target_tolerance_ratio=.20,
                               province_districts={'SYNTHETIC':4})
    engine_results = {}
    for name, assignment in assignments.items():
        converted = dict(zip(ids, assignment))
        violations = engine.hard_constraint_violations(data, converted, contract)
        measured = engine.plan_metrics(data, converted, contract)
        assert math.isclose(measured['shape']['polsby_popper_median'],
                            details[name]['shape_polsby_popper_median'], abs_tol=1e-12)
        engine_results[name] = {'violations':violations, 'metrics':measured,
                                'score':engine.score_metrics(measured,edge_count=len(edges))}
    selected, _, step = engine.select_best_state(data, [dict(zip(ids,a)) for a in assignments.values()], contract)
    assert selected == dict(zip(ids, assignments['B_lower_max']))
    assert not engine_results['A_lower_L1']['violations']
    assert not engine_results['B_lower_max']['violations']
    assert engine_results['C_hard_invalid']['violations']
    (ROOT/'engine_ranking_results.json').write_text(json.dumps(engine_results,indent=2))
    return {'same_universe_population': sum(pops), 'K': 4, 'tolerance': .20,
            'cell_population_matrix': matrix, 'candidates': details,
            'historical_L1_winner': 'A_lower_L1', 'max_relative_winner': 'B_lower_max',
            'actual_DDD_ensemble_winner': summary['shortlist'][0],
            'actual_DDD_invalid': summary['invalid_candidates'],
            'actual_DDD_engine_winner': 'B_lower_max', 'actual_DDD_engine_selected_step':step,
            'actual_DDD_engine_results':engine_results,
            'note': 'No MarkovChain; controlled assignments with equal A/B geometry and comarca metrics.'}


def analytic_cases():
    k_cases = []
    for components, expected_k in [([1490, 1490, 1020], 4), ([1510, 1510, 980], 4), ([500,500,1000], 2)]:
        counts = [round(p/1000) for p in components]
        k_cases.append({'component_population': components, 'target': 1000,
                        'contract_K': expected_k, 'componentwise_round': counts,
                        'sum_round': sum(counts), 'violates_contract_K': sum(counts) != expected_k})
    island_population, mainland_population, target, epsilon = 100, 4000, 1000, .05
    remove = (target-island_population)/island_population > epsilon
    retained = mainland_population if remove else mainland_population+island_population
    assert remove and retained != mainland_population+island_population
    return {'K_rounding_cases': k_cases,
            'island_removal_case': {'input_units': 5, 'output_units': 4,
                                    'input_population': 4100, 'retained_population': retained,
                                    'lost_population': 4100-retained, 'lost_geometric_area_units': 1,
                                    'formula_difference': 9.0, 'epsilon': epsilon,
                                    'mechanism_predicate_true': remove},
            'warning': 'Mechanism-level counterexamples, not executions of licensed historic code. '
                       'Component populations alone do not prove feasible K under hard tolerances; '
                       'a contract-aware feasibility gate must reject impossible disconnected allocation.'}


def workload(width, height, seed):
    rng = random.Random(seed)
    pops = [100] * (width * height)
    geoms = [box(x, y, x+1, y+1) for y in range(height) for x in range(width)]
    assignments = []
    for _ in range(56):
        cuts = [width//4+rng.randint(-2,2), width//2+rng.randint(-2,2), 3*width//4+rng.randint(-2,2)]
        assignments.append([sum(x >= cut for cut in cuts) for y in range(height) for x in range(width)])
    return pops, geoms, assignments


def bench_worker(width, height, seed, mode):
    pops, geoms, assignments = workload(width, height, seed)
    target = sum(pops)/4
    tracemalloc.start()
    start = time.perf_counter()
    all_geoms = {}
    ranking = []
    populations = []
    for index, assignment in enumerate(assignments):
        sums = tally(pops, assignment, 4)
        populations.append(sums)
        ranking.append((sum(abs(p-target) for p in sums), index))
        if mode == 'all_dissolves':
            all_geoms[index] = dissolve(geoms, assignment, 4)
    selected = [i for _, i in sorted(ranking)[:10]]
    if mode == 'tally_then_top':
        for index in selected:
            all_geoms[index] = dissolve(geoms, assignments[index], 4)
    elapsed = time.perf_counter()-start
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    # macOS ru_maxrss is bytes; Linux ru_maxrss is kilobytes.
    rss_bytes = rss if sys.platform == 'darwin' else rss*1024
    fingerprints = [[i, populations[i], [g.wkb_hex for g in all_geoms[i]]] for i in selected]
    # Verification excluded from measured timing; identical selected candidates in both paths.
    for index in selected:
        checked = verify_grid(assignments[index], pops, geoms, width, height, 4, .20)
        assert all(a.equals_exact(b, 0) for a,b in zip(checked, all_geoms[index]))
    assert all(metrics(p)['max_relative'] <= .20 for p in populations)
    return {'mode': mode, 'width': width, 'height': height, 'N': len(pops), 'S': 56, 'top': 10,
            'K': 4, 'seed': seed, 'target': target, 'tolerance': .20,
            'seconds': elapsed, 'tracemalloc_peak_bytes': peak, 'process_peak_RSS_bytes': rss_bytes,
            'input_sha256': digest([pops, assignments]), 'selected_steps': selected,
            'selected_population_geometry_fingerprint': digest(fingerprints),
            'unique_assignments': len({digest(a) for a in assignments}),
            'valid_prebuilt_assignments': 56, 'hard_violations': 0,
            'selected_contiguous_topologically_geometrically': True,
            'universe_and_atomicity_preserved': True, 'dissolve_count': len(all_geoms)*4}


def run_all():
    results = {'schema': 'ddd.nacho-synthetic-mechanisms/1.0',
               'script_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
               'DDD_source_sha256': {str(p.relative_to(DDD)): hashlib.sha256(p.read_bytes()).hexdigest()
                    for p in [DDD/'ddd_ensemble/ensemble_assembler.py',DDD/'ddd_core/m05_gerrychain_engine.py']},
               'environment': {'python': sys.version, 'shapely': shapely.__version__,
                               'platform': platform.platform(), 'executable': sys.executable},
               'ranking': ranking_case(), 'analytical_counterexamples': analytic_cases(), 'benchmarks': []}
    for width,height in [(80,10), (160,20)]:
        for seed in [17,29,43]:
            pair = []
            for mode in ['all_dissolves', 'tally_then_top']:
                cp = subprocess.run([sys.executable, str(Path(__file__)), '--worker', mode,
                                     '--width', str(width), '--height', str(height), '--seed', str(seed)],
                                    capture_output=True, text=True, timeout=60, check=True)
                (ROOT/f'log_N{width*height}_seed{seed}_{mode}.json').write_text(cp.stdout)
                pair.append(json.loads(cp.stdout))
            old,new = pair
            assert old['input_sha256'] == new['input_sha256']
            assert old['selected_steps'] == new['selected_steps']
            assert old['selected_population_geometry_fingerprint'] == new['selected_population_geometry_fingerprint']
            results['benchmarks'].append({'N': width*height, 'seed': seed, 'paths': pair,
                                          'speedup': old['seconds']/new['seconds'],
                                          'python_allocation_peak_ratio': old['tracemalloc_peak_bytes']/new['tracemalloc_peak_bytes'],
                                          'RSS_ratio': old['process_peak_RSS_bytes']/new['process_peak_RSS_bytes'],
                                          'exact_selected_WKB_population_assignment_match': True})
            (ROOT/'results.json').write_text(json.dumps(results, indent=2))
    print(json.dumps({'ranking': results['ranking'], 'benchmark_summary': [
        {k:v for k,v in b.items() if k != 'paths'} for b in results['benchmarks']]}, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--worker', choices=['all_dissolves', 'tally_then_top'])
    parser.add_argument('--width', type=int)
    parser.add_argument('--height', type=int)
    parser.add_argument('--seed', type=int)
    args = parser.parse_args()
    if args.worker:
        print(json.dumps(bench_worker(args.width,args.height,args.seed,args.worker)))
    else:
        run_all()
