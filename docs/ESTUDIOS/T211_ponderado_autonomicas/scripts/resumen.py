"""T-211: por territorio, granularidad de las unidades M04, objetivo por circunscripción y fuera de tolerancia."""
import json, sys
from collections import defaultdict
from pathlib import Path
sys.path.insert(0, "/home/user/DiputadodeDistrito")
from ddd_motor2.adaptadores import problema_y_plan
from ddd_motor2.generadores import entrada_bateria
from ddd_motor2.naturalidad_clave import natural_desde_m06
from ddd_motor2.reglas import Criterio, Reglas
t, out = sys.argv[1], Path(sys.argv[2])
comp = out / "competicion" / t
ent = entrada_bateria(t, out)
can = next((comp / "canonico").glob("*_m06_composicion_distritos.csv"))
reglas = Reglas.desde_contrato(ent.cfg, Criterio())
prob, plan, _ = problema_y_plan(can, ent.grafo_m03, ent.cfg)
nat = natural_desde_m06(prob, reglas, can, ent.grafo_m03, ent.cfg)
obj = float(nat.objetivo)
sin_circ = sum(1 for u in prob.unidades if nat.obj_circ and u.provincia not in nat.obj_circ)
internas = [u for u in prob.unidades if ":U" in u.id or ":F" in u.id]
grandes = [u for u in internas if u.poblacion >= 0.5 * obj]
print(f"{t}: unidades {len(prob.unidades)} (internas {len(internas)}, de ellas >= 0,5 x objetivo {len(grandes)}); "
      f"objetivo {obj:.0f}; circunscripciones {len(nat.obj_circ) or 1}; unidades sin objetivo de su circunscripción {sin_circ}")
C = json.loads((comp / "COMPETICION.json").read_text())
tr = nat.tol / nat.objetivo
for c in C["candidatos"]:
    if c["id"] in ("canonico", C.get("ganador")):
        print(f"  {c['id']}: fuera (clave, objetivo de circunscripción) {c['clave_naturalidad'][0]}, "
              f"fuera (evaluar, objetivo regional) {c['fuera_tolerancia']}")
