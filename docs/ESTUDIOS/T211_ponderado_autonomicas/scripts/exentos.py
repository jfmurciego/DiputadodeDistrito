"""T-211: ¿cuántos distritos fuera de tolerancia (recuento del contrato) contienen un municipio o partición exentos de
suelo? El recuento de reglas.evaluar no los descuenta; esto mide cuánto cambiaría si se descontaran."""
import json, sys
from pathlib import Path
sys.path.insert(0, "/home/user/DiputadodeDistrito")
from ddd_motor2.adaptadores import problema_y_plan
from ddd_motor2.generadores import entrada_bateria
from ddd_motor2.reglas import Criterio, Reglas, evaluar
from ddd_motor2.reglas.evaluar import exento_de_suelo
for arg in sys.argv[1:]:
    t, out = arg.split("=")
    out = Path(out); comp = out / "competicion" / t
    C = json.loads((comp / "COMPETICION.json").read_text())
    ent = entrada_bateria(t, out); reglas = Reglas.desde_contrato(ent.cfg, Criterio())
    for cid in ("canonico", C["ganador"]):
        csvp = next((comp / cid).glob("*_m06_composicion_distritos.csv"))
        prob, plan, _ = problema_y_plan(csvp, ent.grafo_m03, ent.cfg)
        fuera = evaluar(prob, reglas, plan).metricas["fuera_tolerancia"]
        us = {u.id: u for u in prob.unidades}
        ex = [d for d in fuera if exento_de_suelo(reglas, [us[u] for u, x in plan.items() if x == d])]
        print(f"{t} {cid}: fuera {len(fuera)}, con exentos de suelo {len(ex)}; exentos en el contrato: "
              f"{len(reglas.exentos_municipio)} municipios, {len(reglas.exentas_particion)} particiones")
