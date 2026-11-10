import sys, json
from collections import defaultdict
from pathlib import Path
sys.path.insert(0, "/home/user/DiputadodeDistrito")
from ddd_motor2.adaptadores import problema_y_plan
from ddd_motor2.generadores import entrada_bateria
t, out = sys.argv[1], Path(sys.argv[2])
can = next((out / "competicion" / t / "canonico").glob("*_m06_composicion_distritos.csv"))
ent = entrada_bateria(t, out)
prob, plan, _ = problema_y_plan(can, ent.grafo_m03, ent.cfg)
pm = defaultdict(int); nu = defaultdict(int)
for u in prob.unidades:
    pm[u.municipio] += u.poblacion; nu[u.municipio] += 1
grandes = sorted((u for u in prob.unidades if u.poblacion > 13443 * 0.6), key=lambda u: -u.poblacion)
for u in grandes[:12]:
    print(u.id, u.poblacion, "mun", u.municipio, "pob_mun", pm[u.municipio], "unidades_mun", nu[u.municipio], "distrito", plan[u.id])
cp = ent.cfg.get("partitioning"); print("partitioning", json.dumps(cp, ensure_ascii=False)[:400])
