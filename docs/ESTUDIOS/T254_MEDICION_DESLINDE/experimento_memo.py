#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""T-254 · Experimento (no es un cambio del motor): ¿cuánto se gana memorizando `Contexto.rango_municipal`?

PROYECTO: Diputado de Distrito
VERSIÓN: 1.0.0
FECHA: 2026-11-11
ANTERIOR: ninguna (fichero nuevo)
QUÉ HACE: en este proceso sustituye `ddd_motor2.reglas.evaluar.Contexto.rango_municipal` (función pura de
  p, techo y objetivo, con dos divisiones de Fraction por llamada) por una versión con caché, ejecuta la competición
  de la batería de un territorio y compara la huella del resultado y el sha256 de cada composición con los de la
  repetición 0 de resultados/MEDICION.json (medir.py, sin caché). No escribe en el motor.
USO: PYTHONHASHSEED=0 python3 docs/ESTUDIOS/T254_MEDICION_DESLINDE/experimento_memo.py congreso_huesca [la_rioja ...]
"""
from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

AQUI = Path(__file__).resolve().parent
ROOT = AQUI.parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(AQUI))


def main() -> int:
    if os.environ.get("PYTHONHASHSEED") != "0":
        os.environ["PYTHONHASHSEED"] = "0"
        os.execv(sys.executable, [sys.executable, *sys.argv])
    import medir
    import importlib
    evaluar = importlib.import_module("ddd_motor2.reglas.evaluar")
    original = evaluar.Contexto.rango_municipal
    cache: dict = {}

    def rango(self, p):
        k = (p, self.techo, self.objetivo)
        r = cache.get(k)
        if r is None:
            r = cache[k] = original(self, p)
        return r
    evaluar.Contexto.rango_municipal = rango
    sub = medir.instrumentar()
    from ddd_motor2.competir import competir_territorio
    base = json.loads((AQUI / "resultados" / "MEDICION.json").read_text(encoding="utf-8"))["territorios"]
    out = {}
    for t in sys.argv[1:]:
        medir.T.clear(); sub.clear(); cache.clear()
        t0 = time.perf_counter()
        competir_territorio(t, ROOT / "bateria", 10)
        total = time.perf_counter() - t0
        h = medir.huellas(t, ROOT / "bateria")
        ref = base[t]["repeticiones"][0]
        out[t] = {"total_s": round(total, 3), "fases_s": {k: round(v, 3) for k, v in sorted(medir.T.items())},
                  "total_s_sin_cache": ref["total_s"],
                  "fases_s_sin_cache": {k: ref["fases_s"].get(k) for k in ("exhaustivo", "cadenas", "juzgar")},
                  "misma_huella_resultado": h["huella_resultado"] == ref["huellas"]["huella_resultado"],
                  "mismas_composiciones": h["candidatos"] == ref["huellas"]["candidatos"],
                  "mismo_ganador": h["ganador"] == ref["huellas"]["ganador"], "entradas_cache": len(cache)}
        print(json.dumps({t: out[t]}, ensure_ascii=False), flush=True)
    (AQUI / "resultados" / "EXPERIMENTO_MEMO.json").write_text(json.dumps(out, indent=1, ensure_ascii=False) + "\n",
                                                               encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
