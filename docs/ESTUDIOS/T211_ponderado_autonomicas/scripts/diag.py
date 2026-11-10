"""T-211 diagnóstico: competición (Ponderado) frente al laboratorio sobre el mismo territorio."""
import json, sys, time
from collections import Counter
from pathlib import Path
sys.path.insert(0, "/home/user/DiputadodeDistrito")
from ddd_motor2 import naturalidad_competicion as lab_mod
from ddd_motor2.adaptadores import problema_y_plan
from ddd_motor2.naturalidad_clave import natural_desde_m06
from ddd_motor2.reglas import Criterio, Reglas, evaluar
from ddd_motor2.generadores import entrada_bateria

t, out = sys.argv[1], Path(sys.argv[2])
comp = out / "competicion" / t
C = json.loads((comp / "COMPETICION.json").read_text())
print("== candidatos competición (r3 local)")
for c in C["candidatos"]:
    print(" ", c["id"] if "id" in c else c.get("nombre"), c.get("estado"), "fuera", c.get("fuera_tolerancia"),
          "clave_nat", (c.get("clave_naturalidad") or [])[:3])
can = next(comp.rglob("canonico/*_m06_composicion_distritos.csv"), None) or next(comp.rglob("*canonico*/*.csv"))
ent = entrada_bateria(t, out)
reglas = Reglas.desde_contrato(ent.cfg, Criterio())
prob, plan, av = problema_y_plan(can, ent.grafo_m03, ent.cfg)
nat = natural_desde_m06(prob, reglas, can, ent.grafo_m03, ent.cfg)
dv = nat.desvios(plan); tr = nat.tol / nat.objetivo
fuera = sorted(d for d, (p, o) in dv.items() if abs(p - o) / o > tr)
m = evaluar(prob, reglas, plan).metricas
print("== canónico (unidades M04)", len(prob.unidades), "aristas", len(prob.aristas), "obj", float(nat.objetivo),
      "obj_circ", {k: float(v) for k, v in nat.obj_circ.items()}, "cuotas", reglas.cuotas[:6])
print("   fuera (clave)", len(fuera), "fuera (evaluar)", m.get("fuera_tolerancia"))
mun = Counter(u.municipio for u in prob.unidades)
pobs = sorted(u.poblacion for u in prob.unidades)
print("   pob. unidad: mediana", pobs[len(pobs)//2], "máx", pobs[-1], "unidades > tol", sum(p > float(nat.tol) for p in pobs))
for d in fuera:
    us = [u for u, x in plan.items() if x == d]
    print("   fuera", d, dv[d][0], round(float(dv[d][1])), "unidades", len(us), "mayor", max(nat.pob_u[u] for u in us))
# cadena instrumentada: cuántas propuestas acepta el núcleo y mínimo de fuera visto
nat.u0 = plan
import gerrychain.chain as gc
for sem in [int(s) for s in sys.argv[3:]] or [1]:
    t0 = time.time()
    r = lab_mod.cadena(nat, sem, 300, ("D8",), nat.recargos(0.5, 0.3, 0.2, 0.3))
    k = r["mejor"]["D8"][0]
    print(f"   cadena {sem}: unicos {r['unicos']} fallo {r['fallo']!r} mejor fuera {k[0]} t {time.time()-t0:.0f}s")
