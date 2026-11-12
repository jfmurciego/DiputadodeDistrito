#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""T-270 · Tiempo de la certificación completa (herramientas/estado_produccion.py, --motor motor2).

PROYECTO: Diputado de Distrito
VERSIÓN: 1.0.0
FECHA: 2026-11-12
ANTERIOR: ninguna (fichero nuevo)
QUÉ HACE: solo mide. Tras `medir.py --p30` de T-254 (P30 de producción, M06 rehecho y auditoría geométrica en
  <salida>/<t>/), ejecuta la certificación de la 00 (`estado_produccion.py`, mismos argumentos que
  `_reutilizable-generacion-territorial.yml`: M01→M06, outcome success, decisión de la auditoría) con el run de la
  batería (`bateria-<t>-7.4.4`) y anota tiempo, rc y decisión en <salida>/CERTIFICACION.json.
USO: python3 docs/ESTUDIOS/T270_MEDICION_DESLINDE_OPTIMIZADO/certificar.py --res <dir de medir> t1 t2 …
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("territorios", nargs="+")
    ap.add_argument("--res", required=True, help="directorio con <t>/auditoria_<t>.json y <t>/runs/<t> (medir.py)")
    ap.add_argument("--salida", default=str(Path(__file__).resolve().parent / "resultados"))
    a = ap.parse_args(argv)
    from herramientas import bateria_motor as bm
    res, dest = Path(a.res), Path(a.salida)
    dest.mkdir(parents=True, exist_ok=True)
    f = dest / "CERTIFICACION.json"
    informe = json.loads(f.read_text(encoding="utf-8")) if f.is_file() else {}
    for t in a.territorios:
        run_id = f"bateria-{t}-7.4.4"
        audit = res / t / f"auditoria_{t}.json"
        decision = json.loads(audit.read_text(encoding="utf-8")).get("decision", "UNKNOWN")
        out = dest / "_estado" / t / "production_status.json"
        env = dict(os.environ, PYTHONHASHSEED="0", DDD_RUN_ID=run_id)
        t0 = time.perf_counter()
        r = subprocess.run([sys.executable, "herramientas/estado_produccion.py", "--params", str(bm.contrato(t)),
                            "--territory-id", t, "--run-id", run_id, "--from-stage", "M01", "--to-stage", "M06",
                            "--execution-outcome", "success", "--geometric-outcome", "success",
                            "--geometric-decision", decision, "--geometric-audit", str(audit), "--motor", "motor2",
                            "--runs-dir", str(res / t / "runs" / t), "--output", str(out)],
                           cwd=ROOT, env=env, capture_output=True, text=True)
        fila = {"estado_produccion_s": round(time.perf_counter() - t0, 3), "rc": r.returncode,
                "salida": (r.stdout.strip().splitlines() or [""])[0], "auditoria_decision": decision}
        if r.returncode:
            fila["error"] = (r.stdout + r.stderr)[-800:]
        elif out.is_file():
            d = json.loads(out.read_text(encoding="utf-8"))
            fila.update({k: d.get(k) for k in ("decision", "block_cause", "population_status")})
        informe[t] = fila
        print(json.dumps({"t": t, **fila}, ensure_ascii=False), flush=True)
        f.write_text(json.dumps(informe, indent=1, ensure_ascii=False, default=str) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
