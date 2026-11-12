#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""T-270 (c) / T-260 · ¿Cambia el ganador del exhaustivo si elige por D8 y no por la función A?

PROYECTO: Diputado de Distrito
VERSIÓN: 1.0.0
FECHA: 2026-11-12
ANTERIOR: ninguna (fichero nuevo)
QUÉ HACE: solo mide; no cambia el motor. Sobre la composición canónica que dejó la batería
  (bateria/competicion/<t>/COMPETICION.json), rehace el problema como `competicion._exhaustivo` y enumera con
  `reglas.enumerar` (mismo presupuesto del Criterio) guardando TODOS los planes válidos. Ordena esos planes con la
  clave A (`calidad.metricas[...]["clave"]`, la que usa hoy `exhaustivo.enumerar_exacto`) y con la clave D8 de la
  competición (`naturalidad_clave.natural_desde_m06(...).clave(plan, "D8")`, la de `juzgar`), y dice si el mejor
  coincide. Escribe <salida>/A_FRENTE_D8.json.
USO: PYTHONHASHSEED=0 python3 docs/ESTUDIOS/T270_MEDICION_DESLINDE_OPTIMIZADO/a_frente_d8.py ceuta melilla congreso_alava
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))


def uno(t: str, out: Path) -> dict:
    from ddd_motor2.adaptadores import problema_y_plan
    from ddd_motor2.calidad import huella_plan, metricas
    from ddd_motor2.generadores import entrada_bateria
    from ddd_motor2.naturalidad_clave import natural_desde_m06
    from ddd_motor2.reglas import Criterio, Reglas, enumerar
    d = json.loads((out / "competicion" / t / "COMPETICION.json").read_text(encoding="utf-8"))
    can = next(c for c in d["candidatos"] if c["id"] == d["canonico"])
    entrada = entrada_bateria(t, out)
    criterio = Criterio()
    reglas = Reglas.desde_contrato(entrada.cfg, criterio)
    comp = can["composicion"]
    referencia = entrada.referencia_nucleos or Path(comp)
    problema, plan, _ = problema_y_plan(comp, entrada.grafo_m03, entrada.cfg, referencia_nucleos=referencia,
                                        atributos_secciones=entrada.atributos_secciones,
                                        respaldo_municipio_cusec=criterio.respaldo_municipio_cusec)
    r = enumerar(problema, reglas, criterio.presupuesto_nodos, max_planes=10 ** 7)
    fila = {"k": reglas.k, "unidades": len(problema.unidades), "completo": r["completo"], "nodos": r["nodos"],
            "validos": r["validos"], "exhaustivo_en_competicion": {k: (d.get("exhaustivo") or {}).get(k)
                                                                  for k in ("metodo", "completo", "validos")}}
    if not r["completo"] or not r["planes"]:
        return {**fila, "mismo_mejor": None, "motivo": "enumeración incompleta o sin planes válidos"}
    nat = natural_desde_m06(problema, reglas, comp, entrada.grafo_m03, entrada.cfg)
    filas = []
    for p in r["planes"]:
        h = huella_plan(p)
        filas.append((metricas(problema, reglas, p)["clave"], (0, *nat.clave(p, "D8", huella=h)), h))
    mejor_a = min(filas, key=lambda x: x[0])[2]
    mejor_d8 = min(filas, key=lambda x: x[1])[2]
    return {**fila, "mejor_A": mejor_a, "mejor_D8": mejor_d8, "mismo_mejor": mejor_a == mejor_d8,
            "mejor_A_es_canonico": mejor_a == can["huella_plan"], "ganador_competicion": d["ganador"]}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("territorios", nargs="+")
    ap.add_argument("--out", default=str(ROOT / "bateria"))
    ap.add_argument("--salida", default=str(Path(__file__).resolve().parent / "resultados"))
    a = ap.parse_args(argv)
    dest = Path(a.salida)
    dest.mkdir(parents=True, exist_ok=True)
    f = dest / "A_FRENTE_D8.json"
    informe = json.loads(f.read_text(encoding="utf-8")) if f.is_file() else {}
    for t in a.territorios:
        try:
            informe[t] = uno(t, Path(a.out))
        except Exception as exc:  # el territorio queda con su error
            informe[t] = {"error": f"{type(exc).__name__}: {exc}"}
        print(json.dumps({"t": t, **informe[t]}, ensure_ascii=False, default=str), flush=True)
        f.write_text(json.dumps(informe, indent=1, ensure_ascii=False, default=str) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
