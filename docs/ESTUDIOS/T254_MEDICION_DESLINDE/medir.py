#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""T-254 · Tiempo por fase de Deslinde 1.0 (canónico M04/M05 + vigente + 10 cadenas + exhaustivo + elección D8 + P30).

PROYECTO: Diputado de Distrito
VERSIÓN: 1.0.0
FECHA: 2026-11-11
ANTERIOR: ninguna (fichero nuevo)
QUÉ HACE: solo mide; no cambia el motor. Envuelve (monkeypatch en este proceso) las funciones de cada fase con un
  cronómetro y ejecuta la competición de la batería (`ddd_motor2.competir.competir_territorio`, la misma que el P30)
  R veces por territorio. Los tiempos del canónico (unidades, M04, M05, M06, validación) son los que mide la propia
  batería por subproceso (`motor_uno`). Con --p30 ejecuta además, una vez, el P30 de producción
  (`ddd_motor2.produccion competir`, canónico reutilizado) y la auditoría geométrica de la certificación
  (`herramientas/auditar_componentes_geometricos.py`) sobre el M06 canónico. Escribe <salida>/MEDICION.json con cada
  repetición, la media y la desviación típica por fase, y la huella de cada mapa (sha256 de cada composición) para
  comprobar después que una optimización no cambia nada bit a bit.
REQUISITOS: entradas en bateria/entradas/<t> (`python3 herramientas/bateria_motor.py entradas <t> --seccionado shapefile`),
  requirements.lock + gerrychain 1.0.0 --no-deps (.claude/rules/motor2.md).
USO: PYTHONHASHSEED=0 python3 docs/ESTUDIOS/T254_MEDICION_DESLINDE/medir.py --rep 3 --p30 la_rioja congreso_la_rioja
"""
from __future__ import annotations

import argparse
import functools
import json
import os
import statistics
import subprocess
import sys
import time
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

T: dict[str, float] = defaultdict(float)
N: dict[str, int] = defaultdict(int)
_pila: list[str] = []


def cronometrar(nombre, f):
    @functools.wraps(f)
    def envuelta(*a, **k):
        _pila.append(nombre)
        t0 = time.perf_counter()
        try:
            return f(*a, **k)
        finally:
            T[nombre] += time.perf_counter() - t0
            N[nombre] += 1
            _pila.pop()
    return envuelta


def instrumentar():
    from ddd_motor2 import competicion, generadores, naturalidad_clave
    from herramientas import bateria_motor as bm
    generadores.Canonico.generar = cronometrar("canonico", generadores.Canonico.generar)
    generadores.Vigente.generar = cronometrar("vigente", generadores.Vigente.generar)
    generadores.Ponderado.generar = cronometrar("cadenas", generadores.Ponderado.generar)
    generadores.reparar = cronometrar("vigente.reparacion_D66", generadores.reparar)
    pf = generadores.piezas_finas

    def piezas(*a, **k):  # se atribuye a la fase que la llama
        return cronometrar(f"{_pila[-1] if _pila else '?'}.piezas_finas", pf)(*a, **k)
    generadores.piezas_finas = piezas
    competicion.juzgar = cronometrar("juzgar", competicion.juzgar)
    competicion._exhaustivo = cronometrar("exhaustivo", competicion._exhaustivo)
    nd = naturalidad_clave.natural_desde_m06

    def nat(*a, **k):
        return cronometrar(f"{_pila[-1] if _pila else '?'}.natural_desde_m06", nd)(*a, **k)
    naturalidad_clave.natural_desde_m06 = nat
    clave = naturalidad_clave.Natural.clave

    def clave_d8(*a, **k):
        return cronometrar(f"{_pila[-1] if _pila else '?'}.clave_D8", clave)(*a, **k)
    naturalidad_clave.Natural.clave = clave_d8
    mu = bm.motor_uno
    sub: dict = {}

    def motor_uno(*a, **k):
        res = mu(*a, **k)
        sub.update(res.get("tiempos") or {})
        return res
    bm.motor_uno = motor_uno
    return sub


def media_sd(xs):
    return {"media": round(statistics.mean(xs), 3), "sd": round(statistics.stdev(xs), 3) if len(xs) > 1 else 0.0,
            "min": round(min(xs), 3), "max": round(max(xs), 3), "n": len(xs)}


def huellas(t: str, out: Path) -> dict:
    d = json.loads((out / "competicion" / t / "COMPETICION.json").read_text(encoding="utf-8"))
    return {"ganador": d["ganador"], "huella_resultado": d.get("huella_resultado"),
            "candidatos": {c["id"]: c.get("composicion_sha256") for c in d["candidatos"]},
            "exhaustivo": {k: (d.get("exhaustivo") or {}).get(k) for k in ("metodo", "motivo", "nodos", "tiempo_s")}}


def p30(t: str, out: Path, dest: Path) -> dict:
    """P30 de producción sobre el M06 canónico que dejó la batería en la caché del territorio, y auditoría geométrica."""
    from herramientas import bateria_motor as bm
    params = bm.contrato(t)
    run_id = f"bateria-{t}-7.4.4"
    env = dict(os.environ, PYTHONHASHSEED="0", DDD_RUN_ID=run_id)
    runs = dest / "runs" / t
    res = {}
    t0 = time.perf_counter()
    r = subprocess.run([sys.executable, "-m", "ddd_motor2.produccion", "competir", "--params", str(params), "--runs-dir",
                        str(runs)], cwd=ROOT, env=env, capture_output=True, text=True)
    res["p30_competir_s"] = round(time.perf_counter() - t0, 3)
    res["p30_rc"] = r.returncode
    if r.returncode:
        res["p30_error"] = (r.stdout + r.stderr)[-1500:]
    f = runs / "p30_motor2" / "P30.json"
    if f.is_file():
        d = json.loads(f.read_text(encoding="utf-8"))
        res.update(p30_estado=d.get("estado"), p30_ganador=d.get("ganador"), p30_huella=d.get("huella_resultado"))
    if res.get("p30_estado") == "P30_GANA_OTRO_PLAN":
        t0 = time.perf_counter()
        r = subprocess.run([sys.executable, "modulos/06_consolidar_distritos.py", "--params", str(params)], cwd=ROOT,
                           env=env, capture_output=True, text=True)
        res["p30_m06_s"], res["p30_m06_rc"] = round(time.perf_counter() - t0, 3), r.returncode
        t0 = time.perf_counter()
        r = subprocess.run([sys.executable, "-m", "ddd_motor2.produccion", "verificar", "--params", str(params),
                            "--runs-dir", str(runs)], cwd=ROOT, env=env, capture_output=True, text=True)
        res["p30_verificar_s"], res["p30_verificar_rc"] = round(time.perf_counter() - t0, 3), r.returncode
    cache = bm._cache(t)
    geo = next(iter(sorted(cache.glob("*_m06_secciones.geojson.zip")) or sorted(cache.glob("*_m06_secciones.geojson"))), None)
    if geo is not None:
        from ddd_core.config import load_params_yaml, module_cfg
        m6 = module_cfg(load_params_yaml(str(params)), "modulo_06_consolidar_distritos", "step6_export_final")
        t0 = time.perf_counter()
        r = subprocess.run([sys.executable, "herramientas/auditar_componentes_geometricos.py", "--sections", str(geo),
                            "--output", str(dest / f"auditoria_{t}.json"), "--section-field", str(m6["id_field"]),
                            "--district-field", str(m6["district_field"]), "--working-crs",
                            str(m6.get("metric_crs", "EPSG:3035")), "--expected-districts",
                            str(m6.get("expected_districts", 0))], cwd=ROOT, env=env, capture_output=True, text=True)
        res["certificacion_auditoria_geometrica_s"] = round(time.perf_counter() - t0, 3)
        res["certificacion_auditoria_rc"] = r.returncode
    return res


def main(argv=None) -> int:
    if os.environ.get("PYTHONHASHSEED") != "0":
        os.environ["PYTHONHASHSEED"] = "0"
        os.execv(sys.executable, [sys.executable, *sys.argv])
    ap = argparse.ArgumentParser()
    ap.add_argument("territorios", nargs="+")
    ap.add_argument("--rep", type=int, default=3)
    ap.add_argument("--cadenas", type=int, default=10)
    ap.add_argument("--out", default=str(ROOT / "bateria"))
    ap.add_argument("--salida", default=str(Path(__file__).resolve().parent / "resultados"))
    ap.add_argument("--p30", action="store_true")
    a = ap.parse_args(argv)
    out, dest = Path(a.out), Path(a.salida)
    dest.mkdir(parents=True, exist_ok=True)
    sub = instrumentar()
    from ddd_motor2.competir import competir_territorio
    import platform
    informe = {"python": sys.version.split()[0], "maquina": platform.machine(), "cpus": os.cpu_count(),
               "commit": subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True).stdout.strip(),
               "cadenas": a.cadenas, "territorios": {}}
    for t in a.territorios:
        reps = []
        for i in range(a.rep):
            T.clear(); N.clear(); sub.clear()
            t0 = time.perf_counter()
            fila = competir_territorio(t, out, a.cadenas)
            total = time.perf_counter() - t0
            rep = {"total_s": round(total, 3), "fases_s": {k: round(v, 3) for k, v in sorted(T.items())},
                   "llamadas": dict(N), "canonico_subprocesos_s": dict(sub), "estado": fila.get("estado"),
                   "huellas": huellas(t, out) if fila.get("estado") != "ERROR" else fila}
            reps.append(rep)
            print(json.dumps({"t": t, "rep": i, "total_s": rep["total_s"], "fases_s": rep["fases_s"],
                              "canonico": sub}, ensure_ascii=False), flush=True)
        fases = sorted({k for r in reps for k in r["fases_s"]} | {f"canonico.{k}" for r in reps for k in r["canonico_subprocesos_s"]})
        def valor(r, k):
            return r["canonico_subprocesos_s"].get(k.split(".", 1)[1], 0.0) if k.startswith("canonico.") else r["fases_s"].get(k, 0.0)
        estad = {k: media_sd([valor(r, k) for r in reps]) for k in fases}
        estad["total"] = media_sd([r["total_s"] for r in reps])
        def sin_tiempo(h):
            return json.dumps({**h, "exhaustivo": {k: v for k, v in (h.get("exhaustivo") or {}).items() if k != "tiempo_s"}},
                              sort_keys=True, default=str)
        iguales = len({sin_tiempo(r["huellas"]) for r in reps}) == 1
        informe["territorios"][t] = {"repeticiones": reps, "estadistica": estad, "huellas_iguales_entre_repeticiones": iguales}
        if a.p30:
            informe["territorios"][t]["p30"] = p30(t, out, dest)
            print(json.dumps({"t": t, "p30": informe["territorios"][t]["p30"]}, ensure_ascii=False), flush=True)
        (dest / "MEDICION.json").write_text(json.dumps(informe, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
