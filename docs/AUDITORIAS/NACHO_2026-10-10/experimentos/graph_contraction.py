#!/usr/bin/env python3
"""Version1.0.0, 2026-10-10. Independent stdlib synthetic quotient experiment."""
from collections import defaultdict
import argparse
import hashlib
import json
from pathlib import Path
import random
import resource
import statistics
import subprocess
import sys
import time
import tracemalloc

ROOT = Path(__file__).resolve().parent


def fingerprint(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()


def connected(wanted, adjacency):
    if not wanted:
        return False
    seen = {next(iter(wanted))}
    stack = list(seen)
    while stack:
        node = stack.pop()
        for neighbor in adjacency[node]:
            if neighbor in wanted and neighbor not in seen:
                seen.add(neighbor)
                stack.append(neighbor)
    return seen == wanted


def quotient(mapping, edges, population):
    units = set(mapping)
    adjacency = {u: set() for u in units}
    populations = {u:0 for u in units}
    for s,p in enumerate(population):
        populations[mapping[s]] += p
    for s,t in edges:
        u,v = mapping[s], mapping[t]
        if u != v:
            adjacency[u].add(v)
            adjacency[v].add(u)
    return adjacency,populations


def check(assignment, adjacency, populations, target):
    groups = [set() for _ in range(4)]
    sums = [0]*4
    for node,d in enumerate(assignment):
        groups[d].add(node)
        sums[d] += populations[node]
    good = all(connected(group,adjacency) for group in groups)
    hard = len({d for d in assignment}) == 4 and all(abs(p-target) <= target*.25 for p in sums)
    return good and hard,sums


def fixture(q, seed, states):
    width,height = 16*q,8
    n=width*height
    mapping=[(s//width)*16+(s%width)//q for s in range(n)]
    pops=[100]*n
    edges=[]
    adj=[set() for _ in range(n)]
    for s in range(n):
        x,y=s%width,s//width
        for t in ([s+1] if x+1<width else []) + ([s+width] if y+1<height else []):
            edges.append((s,t))
            adj[s].add(t)
            adj[t].add(s)
    rng=random.Random(seed)
    assignments=[]
    for _ in range(states):
        delta=rng.choice([-1,0,1])
        labels=list(range(4))
        rng.shuffle(labels)
        cuts=[4+delta,8+delta,12+delta]
        assignments.append([labels[sum(u%16 >= cut for cut in cuts)] for u in range(128)])
    return mapping,pops,edges,adj,assignments


def worker(q,seed,states,mode):
    mapping,pops,edges,section_adj,assignments=fixture(q,seed,states)
    target=sum(pops)/4
    tracemalloc.start()
    started=time.perf_counter()
    build_seconds=0
    if mode=='quotient':
        started_build=time.perf_counter()
        adjacency,population=quotient(mapping,edges,pops)
        build_seconds=time.perf_counter()-started_build
    else:
        adjacency,population=section_adj,pops
    validation_start=time.perf_counter()
    outcomes=[]
    for municipal in assignments:
        assignment=municipal if mode=='quotient' else [municipal[u] for u in mapping]
        outcomes.append(check(assignment,adjacency,population,target))
    validation_seconds=time.perf_counter()-validation_start
    elapsed=time.perf_counter()-started
    _,peak=tracemalloc.get_traced_memory()
    tracemalloc.stop()
    rss=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    rss_bytes=rss if sys.platform=='darwin' else rss*1024
    assert all(good for good,pop in outcomes)
    qa,qp=quotient(mapping,edges,pops)
    members=defaultdict(set)
    for s,u in enumerate(mapping): members[u].add(s)
    assert len(members)==128 and sum(map(len,members.values()))==len(mapping)
    assert set().union(*members.values())==set(range(len(mapping)))
    assert all(connected(group,section_adj) for group in members.values())
    assert sum(qp.values())==sum(pops)
    wanted_edges={tuple(sorted((mapping[s],mapping[t]))) for s,t in edges if mapping[s]!=mapping[t]}
    actual_edges={tuple(sorted((u,v))) for u,neighbors in qa.items() for v in neighbors}
    assert wanted_edges==actual_edges
    # Expansion/restriction roundtrip is bijective on municipality-admissible assignments.
    for municipal in assignments:
        expanded=[municipal[u] for u in mapping]
        restricted=[expanded[min(members[u])] for u in range(128)]
        assert restricted==municipal
        assert all(len({expanded[s] for s in members[u]})==1 for u in members)
    return {'mode':mode,'sections_per_municipality':q,'N_sections':len(mapping),
            'E_sections':len(edges),'N_units':128,'E_units':len(wanted_edges),
            'seed':seed,'state_budget':states,'K':4,'P':sum(pops),'target':target,'tolerance':.25,
            'total_seconds':elapsed,'quotient_build_seconds':build_seconds,
            'BFS_population_validation_seconds':validation_seconds,
            'tracemalloc_peak_bytes':peak,'process_peak_RSS_bytes':rss_bytes,
            'input_sha256':fingerprint([mapping,pops,edges,assignments]),
            'outcome_sha256':fingerprint(outcomes),'hard_violations':0,
            'valid_prebuilt_assignment_fraction':sum(good for good,pop in outcomes)/states,
            'unique_municipal_assignments':len({fingerprint(a) for a in assignments}),
            'verified_connected_units_exact_quotient_population_and_roundtrip':True}


def negative_discontinuous():
    mapping=[0,1,0]
    edges=[(0,1),(1,2)]
    adj=[{1},{0,2},{1}]
    qa,qp=quotient(mapping,edges,[100]*3)
    source_A_connected=connected({0,2},adj)
    contracted_A_connected=connected({0},qa)
    assert not source_A_connected and contracted_A_connected
    return {'section_edges':edges,'section_to_municipality':mapping,
            'assignment_sections':[0,1,0],'assignment_units':[0,1],
            'source_district_A_connected':source_A_connected,
            'quotient_district_A_connected':contracted_A_connected,
            'exact_population_preserved':sum(qp.values())==300,
            'decision':'REJECT pure contraction: municipal atomicity does not prove physical connectedness. '
                       'Keep independent polygon/component gate and accredited exceptions. '
                       'Section-to-unit mapping itself is many-to-one, not bijective.'}


def run(states):
    results={'schema':'ddd.synthetic-graph-contraction/1.0',
             'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
             'python_version':sys.version,'executable':sys.executable,
             'negative':negative_discontinuous(),'pairs':[]}
    for q in [4,8,16]:
        for seed in [17,29,43]:
            pair=[]
            for mode in ['sections','quotient']:
                cp=subprocess.run([sys.executable,str(Path(__file__)),'--worker',mode,'--q',str(q),
                                   '--seed',str(seed),'--states',str(states)],timeout=60,
                                  capture_output=True,text=True,check=True)
                (ROOT/f'graph_q{q}_seed{seed}_{mode}.json').write_text(cp.stdout)
                pair.append(json.loads(cp.stdout))
            old,new=pair
            assert old['input_sha256']==new['input_sha256']
            assert old['outcome_sha256']==new['outcome_sha256']
            results['pairs'].append({'q':q,'seed':seed,'paths':pair,
                                     'end_to_end_speedup':old['total_seconds']/new['total_seconds'],
                                     'validation_only_speedup':old['BFS_population_validation_seconds']/new['BFS_population_validation_seconds'],
                                     'same_population_and_connectivity_results':True})
            (ROOT/'graph_results.json').write_text(json.dumps(results,indent=2))
    print(json.dumps({'negative':results['negative'],'summary':[{
        'sections_per_municipality':q,
        'median_total_speedup':statistics.median(p['end_to_end_speedup'] for p in results['pairs'] if p['q']==q)}
        for q in [4,8,16]]},indent=2))


if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--worker',choices=['sections','quotient'])
    p.add_argument('--q',type=int)
    p.add_argument('--seed',type=int)
    p.add_argument('--states',type=int,default=2000)
    a=p.parse_args()
    if a.worker: print(json.dumps(worker(a.q,a.seed,a.states,a.worker)))
    else: run(a.states)
