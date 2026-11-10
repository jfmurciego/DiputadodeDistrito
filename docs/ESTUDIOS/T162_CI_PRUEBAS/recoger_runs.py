import subprocess,json,os,time,datetime as d
from concurrent.futures import ThreadPoolExecutor
R="repos/jfmurciego/diputadodedistrito"
def api(p):
    for i in range(6):
        try: return json.loads(subprocess.check_output(["gh","api",p],stderr=subprocess.DEVNULL))
        except Exception: time.sleep(2**i/2)
    return None
now=d.datetime.now(d.UTC)
runs={}
for k in range(15):
    a=(now-d.timedelta(days=k)).strftime("%Y-%m-%d")
    for lo,hi in (("00:00:00","11:59:59"),("12:00:00","23:59:59")):
        pg=1
        while True:
            r=api(f"{R}/actions/workflows/359810096/runs?per_page=100&page={pg}&created={a}T{lo}Z..{a}T{hi}Z")
            if not r: break
            for x in r["workflow_runs"]: runs[x["id"]]=x
            if len(r["workflow_runs"])<100 or pg>=10: break
            pg+=1
L=[{"id":x["id"],"ev":x["event"],"concl":x["conclusion"],"br":x["head_branch"],"pr":[p["number"] for p in x["pull_requests"]],"created":x["created_at"],"att":x["run_attempt"]} for x in runs.values()]
json.dump(L,open("lista.json","w"));print(len(L),flush=True)
os.makedirs("c",exist_ok=True)
def f(r):
    fn=f"c/{r['id']}.json"
    if os.path.exists(fn):return
    j=api(f"{R}/actions/runs/{r['id']}/jobs?per_page=100&filter=all")
    if j is None:return
    json.dump([{"n":x["name"],"c":x["conclusion"],"s":x["started_at"],"e":x["completed_at"],"steps":[{"n":s["name"],"s":s["started_at"],"e":s["completed_at"]} for s in x["steps"]]} for x in j["jobs"]],open(fn,"w"))
with ThreadPoolExecutor(8) as ex: list(ex.map(f,L))
print("hecho",len(os.listdir("c")))
