import sys, json
from pathlib import Path
sys.path.insert(0, "/home/user/DiputadodeDistrito")
from ddd_motor2.adaptadores import problema_y_plan
from ddd_motor2.generadores import entrada_bateria
from ddd_motor2.reglas import Criterio, Reglas, evaluar
t, out = sys.argv[1], Path(sys.argv[2])
e = entrada_bateria(t, out); r = Reglas.desde_contrato(e.cfg, Criterio())
d = out / "competicion" / t
can = next((d / "canonico").glob("*_m06_composicion_distritos.csv"))
vig = next((d / "vigente").glob("*_m06_composicion_distritos.csv"))
for ref, nombre in ((can, "referencia = canónico"), (vig, "referencia = el propio vigente")):
    p, plan, _ = problema_y_plan(vig, e.grafo_m03, e.cfg, referencia_nucleos=ref)
    inf = evaluar(p, r, plan)
    print(f"{t} vigente ({nombre}): válido {inf.valido}, fuera (contrato) {len(inf.metricas['fuera_tolerancia'])}, "
          f"violaciones {[(v.regla, v.ambito) for v in inf.violaciones][:5]}")
