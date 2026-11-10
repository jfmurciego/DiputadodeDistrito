import json,datetime as d,collections as C
R=json.load(open("runs.json"))
P=lambda s:d.datetime.fromisoformat(s.replace("Z","+00:00"))
def mins(j):
    if not j["s"] or not j["e"]:return 0
    sec=(P(j["e"])-P(j["s"])).total_seconds()
    return -(-sec//60) if sec>0 else 0   # facturación redondeada al minuto
tot=C.Counter();cnt=C.Counter();raw=C.Counter()
step=C.Counter()
byev=C.Counter();canc=0
for r in R:
    rm=0
    for j in r["jobs"]:
        k="suite" if j["n"].startswith("suite") else j["n"]
        m=mins(j);tot[k]+=m;cnt[k]+=1;rm+=m
        if j["n"].startswith("suite"):
            for s in j["steps"]:
                if s["s"] and s["e"]:step[s["n"][:40]]+=(P(s["e"])-P(s["s"])).total_seconds()/60
        if j["c"]=="cancelled": canc+=m
    byev[(r["ev"],r["concl"])]+=rm
print("runs",len(R),"min total",sum(tot.values()),"min en jobs cancelados",canc)
for k,v in tot.items():print(k,v,cnt[k],round(v/max(cnt[k],1),1))
print(byev)
for k,v in step.most_common(8):print(round(v),k)
prs=C.Counter()
for r in R:
    if r["ev"]=="pull_request":prs[(r["pr"][0] if r["pr"] else r["br"])]+=1
print("PR distintas",len(prs),"runs/PR media",sum(prs.values())/max(len(prs),1))
