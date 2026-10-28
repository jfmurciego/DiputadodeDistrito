import sys,json,pathlib,time,hashlib
sys.path.insert(0,'/private/tmp/MADRID-M05-REPAIR-EXPERIMENT')
from madrid110 import case,kw,S,U,A,pops,check
from ddd_core import m05_population_repair as c
W=json.loads(pathlib.Path('/private/tmp/MADRID-M05-REPAIR-EXPERIMENT/solucion_validada.json').read_text())
unit_ids=sorted(S,key=str); districts=sorted(set(S.values()),key=str); width=max(1,(max(1,len(districts)-1).bit_length()+7)//8); di={d:i for i,d in enumerate(districts)}
def encode(s): return b''.join(di[s[u]].to_bytes(width,'little') for u in unit_ids)
states=[dict(S)]
for moved,donor,receiver in W['moves']:
    n=dict(states[-1])
    for u in moved:
        assert n[u]==donor,(len(states),u,n[u],donor)
        n[u]=receiver
    states.append(n)
assert states[-1]==W['final_assignments']
assert W['artifact_sha256']['11353290857']=='6a5181ddeca846dae3afde8e560ac51077d30ca82a09c85277d57406fe289d9c'
assert W['floor']==kw['floor'] and W['cap']==kw['cap'] and W['target']==kw['target'] and W['target']*.12==kw['tolerance']
# Validate every witness move with the exact v1.8 transition validator.
state=dict(S); move_checks=[]
for i,(m,d,r) in enumerate(W['moves'],1):
    ok,reason,checks=c._valid_transfer(state,U,A,m,d,r,floor=kw['floor'],cap=kw['cap'])
    assert ok,(i,reason,checks)
    for u in m: state[u]=r
    move_checks.append({'step':i,'hard':list(c._hard_population_signature(pops(state),floor=kw['floor'],cap=kw['cap'])),'valid':check(state)['valid']})
assert check(state)['hard_limits_met'] and state==W['final_assignments']
keys=[encode(s) for s in states]
original=c._select_expanded_frontier
orig_transfer=c._focal_single_transfer
calls=0; events=[]; t0=time.monotonic()
class Stop(Exception): pass

def transfer(current,pops0,province_units,units,adjacency,u,donor,receiver,**kwargs):
    # Record whether the exact next witness move was reached by the transfer validator.
    idx=calls+1
    record={'step':idx,'unit':u,'donor':donor,'receiver':receiver}
    witness=W['moves'][idx-1] if idx<=len(W['moves']) else None
    if witness and (u,) == tuple(witness[0]) and donor==witness[1] and receiver==witness[2] and current==states[idx-1]:
        result=orig_transfer(current,pops0,province_units,units,adjacency,u,donor,receiver,**kwargs)
        events.append({'validator_attempt':idx,'validator_result':result[0],'reason':result[1],'checks':result[2]})
        return result
    return orig_transfer(current,pops0,province_units,units,adjacency,u,donor,receiver,**kwargs)

def select(candidates,parents,frontier,rank,ceiling):
    global calls
    calls+=1
    frame=sys._getframe(1).f_locals
    i=calls
    target=keys[i]; parent=keys[i-1]
    selected=original(candidates,parents,frontier,rank,ceiling)
    event={'wave':i,'witness_step':i,'expected_parent_in_frontier':parent in frontier,
      'candidate_count':len(candidates),'frontier_count':len(frontier),'ceiling':ceiling,
      'candidate_attempts_cumulative':frame.get('candidate_attempts'),
      'unique_generated_cumulative':frame.get('generated'),
      'states_discovered_cumulative':len(frame.get('parents',{})),
      'states_expanded_cumulative':frame.get('expanded'),
      'deduplicated_cumulative':frame.get('deduplicated'),
      'target_in_candidates':target in candidates,'target_in_selected':target in selected}
    if target in candidates:
      event['target_parent_matches_expected']=parents[target][0]==parent
      event['target_parent_existing_record']=parents[target][0].hex() if isinstance(parents[target][0],bytes) else str(parents[target][0])
    elif target in frame.get('parents',{}):
      old=frame['parents'][target]
      event['dedup_existing_parent']=old[0].hex() if isinstance(old[0],bytes) else str(old[0])
      event['dedup_existing_move']=[list(old[1]),old[2],old[3]]
    if i<=len(W['moves']):
      event['expected_move']=W['moves'][i-1]
      event['expected_hard_after']=move_checks[i-1]['hard']
    events.append(event)
    if not event['target_in_selected']:
      raise Stop
    return selected

c._focal_single_transfer=transfer
c._select_expanded_frontier=select
limits=c.SearchLimits(max_seconds=180,expanded_max_seconds=180,expanded_max_states=400000,
 expanded_max_candidates=400000,expanded_max_memory_mib=640,expanded_max_depth=96,
 expanded_beam_per_district=2,expanded_beam_width=128,expanded_max_radius=8)
termination=None
try:
 c._expanded_hard_search(**{k:v for k,v in kw.items() if k!='assignments'},state=S,limits=limits,candidate_budget=400000)
except Stop:
 termination='FIRST_WITNESS_PREFIX_NOT_SELECTED'
finally:
 c._focal_single_transfer=orig_transfer; c._select_expanded_frontier=original
out={'candidate_sha256':hashlib.sha256(pathlib.Path('/Users/macbookpro/Desarrollo/DDD-distritos-autonomicos/ddd_core/m05_population_repair.py').read_bytes()).hexdigest(),
 'witness_sha256':hashlib.sha256(pathlib.Path('/private/tmp/MADRID-M05-REPAIR-EXPERIMENT/solucion_validada.json').read_bytes()).hexdigest(),
 'checkpoint_sha256':'6a5181ddeca846dae3afde8e560ac51077d30ca82a09c85277d57406fe289d9c',
 'termination':termination,'elapsed_to_capture_seconds':time.monotonic()-t0,'events':events,
 'witness_move_validation':{'count':len(move_checks),'all_valid':True,'final_hard':move_checks[-1]['hard'],'final_assignment_matches':True}}
pathlib.Path('/private/tmp/madrid110_v18_prefix_diagnostic.json').write_text(json.dumps(out,indent=2))
print(json.dumps(out,indent=2))
