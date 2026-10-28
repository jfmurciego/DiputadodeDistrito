import sys,json,time,hashlib,pathlib
sys.path.insert(0,'/private/tmp/MADRID-M05-REPAIR-EXPERIMENT')
from madrid110 import case,kw,S
from ddd_core import m05_population_repair as r
solution=json.loads(pathlib.Path('/private/tmp/MADRID-M05-REPAIR-EXPERIMENT/solucion_validada.json').read_text())
unit_ids=sorted(S,key=str); districts=sorted(set(S.values()),key=str); width=max(1,(max(1,len(districts)-1).bit_length()+7)//8);di={d:i for i,d in enumerate(districts)}
def encode(s):return b''.join(di[s[u]].to_bytes(width,'little') for u in unit_ids)
states=[dict(S)]
for moved,d,recv in solution['moves'][:5]:
 n=dict(states[-1]);[n.__setitem__(u,recv) for u in moved];states.append(n)
keys=[encode(s) for s in states]; original=r._select_expanded_frontier; call=0; out=[]
class Stop(Exception):pass
def wrapped(candidates,parents,frontier,rank,ceiling):
 global call
 call+=1; target=keys[5] if call==5 else None
 selected=original(candidates,parents,frontier,rank,ceiling)
 event={'call':call,'frontier_count':len(frontier),'candidate_count':len(candidates),'ceiling':ceiling,'selected_target':target in selected if target is not None else None}
 if target is not None and target in candidates:
  parent=parents[target][0]; sibling=sorted((k for k in candidates if parents[k][0]==parent),key=rank)
  event['target_moved']=parents[target][1];event['target_route']=parents[target][2:4]
  event['parent_siblings_top15']=[{'local_rank':j+1,'unit':parents[k][1][0],'donor':parents[k][2],'receiver':parents[k][3],'rank_prefix':rank(k)[:-1]} for j,k in enumerate(sibling[:15])]
  def alt(k):
   p=candidates[k]; vals=list(p.values()); outliers=sum(abs(v-kw['target'])>kw['tolerance'] for v in vals); maxdev=max((abs(v-kw['target'])/kw['target'] for v in vals),default=0.0); totaldev=sum(abs(v-kw['target'])/kw['target'] for v in vals); q=rank(k)
   return (q[0],round(maxdev,12),round(totaldev,12),q[1],outliers,k)
  alt_rank=sorted(candidates,key=alt);event['target_alternative_rank_1based']=alt_rank.index(target)+1
  half=ceiling//2; chosen=set(selected[:half]);
  for i in range(half): chosen.add(alt_rank[min(len(alt_rank)-1,round((i+.5)*len(alt_rank)/half))])
  event['target_selected_in_half_beams']=target in chosen; event['alternative_selected_count']=len(chosen)
  event['hard_signature_candidate_counts']={str(rank(k)[0]):sum(rank(z)[0]==rank(k)[0] for z in candidates) for k in list(candidates)[:1]}
  ordered=sorted(candidates,key=rank)
  rows=[]
  for k in ordered:
   q=rank(k);meta=parents[k]
   rows.append({'key_sha':hashlib.sha256(k).hexdigest(),'parent_sha':hashlib.sha256(meta[0]).hexdigest(),'donor':meta[2],'receiver':meta[3],'unit':meta[1][0],'primary_rank':q[:-1],'alternative_rank':alt(k)[:-1]})
  pathlib.Path('/private/tmp/madrid110_fifth_children.json').write_text(json.dumps(rows))
 out.append(event)
 if target is not None and target in candidates:raise Stop
 return selected
r._select_expanded_frontier=wrapped
limits=r.SearchLimits(max_depth=3,max_transfer_set=2,max_candidates=400000,max_seconds=5,expanded_max_candidates=400000,expanded_max_seconds=180,expanded_max_memory_mib=640,expanded_max_depth=96,expanded_beam_per_district=2,expanded_beam_width=128,expanded_max_radius=8)
t=time.monotonic()
try:r._expanded_hard_search(**{k:v for k,v in kw.items() if k!='assignments'},state=S,limits=limits,candidate_budget=400000)
except Stop:pass
finally:r._select_expanded_frontier=original
result={'outcome':'WITNESS_CHILD_CAPTURED' if out and out[-1].get('target_generated') else 'NOT_GENERATED','elapsed_seconds':time.monotonic()-t,'witness_sha256':hashlib.sha256(pathlib.Path('/private/tmp/MADRID-M05-REPAIR-EXPERIMENT/solucion_validada.json').read_bytes()).hexdigest(),'trace':out};pathlib.Path('/private/tmp/madrid110_trace_global_rank.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
