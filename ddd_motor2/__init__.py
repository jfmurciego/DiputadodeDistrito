"""Motor 2 de Diputado de Distrito (T-160). Vive aparte: producción (M04/M05/ddd_core) no lo importa.

T-257 (D-88): el núcleo de la competición es el paquete Deslinde (paquetes/deslinde/src/deslinde/), fuente única.
`ddd_motor2.<módulo>` de los módulos movidos ES el módulo de Deslinde (mismo objeto en sys.modules: mismas clases y
excepciones). Al importar ddd_motor2 se registran en Deslinde el resolutor de la tabla maestra (semilla.py) y las
tablas de naturalidad del repo (tablas_repo.py)."""
import importlib
import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parents[1] / "paquetes" / "deslinde" / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

MOVIDOS = ("reglas", "reglas.modelo", "reglas.evaluar", "reglas.enumerar", "reglas.estado", "reglas.criterios",
           "reglas.metodo", "reglas.cota", "adaptadores", "calidad", "exhaustivo", "excepcion_d66", "competicion",
           "naturalidad_clave", "informe")

for _n in MOVIDOS:
    _m = importlib.import_module(f"deslinde.{_n}")
    sys.modules[f"{__name__}.{_n}"] = _m
    if "." not in _n:
        globals()[_n] = _m

from . import semilla, tablas_repo  # noqa: E402,F401  (registran el resolutor y las tablas del repo)
