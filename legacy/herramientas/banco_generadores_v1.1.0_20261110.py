#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Banco de generadores (T-132 A): canónico, GerryChain de producción y GerryChain con semilla por árboles.

PROYECTO: Diputado de Distrito
VERSIÓN: 1.1.0
NOMBRE DE VERSIÓN: Banco de generadores con competidor
FECHA: 2026-11-10
ESTADO: candidato (banco de pruebas; no es ruta de producción)
CAMBIOS: 1.1.0 (D-48): generador «competidor» (orden DDD_COMPETIDOR, por defecto ``python -m ddd_motor2.competidor``,
  que sustituye a M05 con --params --run-id --semilla) y subcomando ``reproducibilidad`` (dos ejecuciones, sha256 de la
  composición M06). 1.0.0: fichero nuevo.
MOTIVO: comparar, con las mismas entradas, el mismo contrato y la misma validación (herramientas/validar_ejecucion.py),
  si los distritos válidos dependen del constructor artesanal M04 o los da también una semilla genérica por árboles.
ANTERIOR: legacy/herramientas/banco_generadores_v1.0.0_20261109.py
QUÉ HACE: por territorio, generador y semilla, sobre las entradas de herramientas/bateria_motor.py:
  canonico    unidades + M04 + M05 canónico vigente + M06.
  gerrychain  unidades + M04 + M05 GerryChain de producción (ddd_core/m05_gerrychain_strategy.py, ReCom) con
              --seed-count 1 --seed-base <semilla>; si M04 no es admisible, semilla M05 canónica (como procedimiento.sh).
  arbol       unidades + M04 solo para fijar las unidades ddd_unit_id y los núcleos cerrados; la semilla sale de
              gerrychain.tree.recursive_tree_part por provincia (K por provincia del contrato) sobre el grafo de
              unidades; se juzga con hard_constraint_violations de GerryChain de producción y, si es admisible,
              se encadena ReCom desde ella. Si no lo es, el informe dice qué regla incumple la semilla.
  Después: M06 y la validación de producción; métricas (desvío máximo, fuera de tolerancia, municipios partidos).
USO: python herramientas/banco_generadores.py ejecutar --generadores canonico gerrychain arbol --semillas 1 2 3 4 5 \
       [--todos | territorio ...]
     python herramientas/banco_generadores.py matriz
Requiere el entorno /opt/ddd-gerrychain (requirements-gerrychain-m05.lock), como la imagen de producción.
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from herramientas import bateria_motor as bm  # noqa: E402

GC_PY = os.environ.get("DDD_GERRYCHAIN_PYTHON", "/opt/ddd-gerrychain/bin/python")
GENERADORES = ("canonico", "gerrychain", "arbol", "exacto", "competidor")
# Generador competidor (D-48, T-163): orden que sustituye a M05. Recibe --params <contrato> --run-id <id> --semilla <n>,
# lee las salidas M03/M04 del contrato (como M05) y escribe el GeoJSON M05 (modulo_05.out_geojson) y su informe; la
# batería hace después M06 y la validación de producción. Se cambia con DDD_COMPETIDOR (orden separada por espacios).
COMPETIDOR = os.environ.get("DDD_COMPETIDOR", f"{sys.executable} -m ddd_motor2.competidor").split()
BANCO_PY = os.environ.get("DDD_BANCO_PYTHON", "/opt/ddd-banco/bin/python")
TIEMPO_EXACTO = float(os.environ.get("DDD_BANCO_TIEMPO_EXACTO", "900"))


# --------------------------------------------------------------------------- semilla por árboles (venv GerryChain)
def semilla_arbol(params: str, run_id: str, salida: Path, informe: Path, semilla: int, initial: Path | None) -> int:
    """Escribe en ``salida`` una asignación por recursive_tree_part; 0 si es admisible, 3 si no."""
    from functools import partial

    import networkx as nx
    import yaml
    from gerrychain import Graph
    from gerrychain.partition import recursive_tree_part
    from gerrychain.tree import bipartition_tree

    from ddd_core import m05_gerrychain_strategy as gs

    cfg = yaml.safe_load(Path(params).read_text(encoding="utf-8"))
    contract = gs.contract_from_yaml(cfg)
    strategy = gs.strategy_config_from_yaml(cfg)
    paths = gs.resolve_paths(cfg, Path(params).resolve(), run_id)
    base = initial or Path(paths["initial"])
    res: dict = {"semilla": semilla, "unidades_desde": str(base)}
    problem = gs.prepare_problem(Path(paths["graph"]), base, contract,
                                 metric_crs=strategy.metric_crs, min_shared_border_m=strategy.min_shared_border_m)
    frozen_unit = {u: d for d, us in problem.frozen_districts.items() for u in us}
    total = sum(r["population"] for r in problem.units.values())
    tol = contract.target_tolerance_ratio
    band = min(contract.population_cap_ratio - 1, 1 - contract.population_floor_ratio)
    provincias = sorted({r["province"] for r in problem.units.values()})
    cuotas = {str(k): int(v) for k, v in (contract.province_districts or {}).items()}
    if not cuotas and len(provincias) == 1:
        cuotas = {provincias[0]: contract.expected_k}
    asignacion: dict = dict(frozen_unit)
    etiqueta = max([int(d) for d in problem.frozen_districts] + [-1]) + 1
    res["provincias"] = {}
    for prov in provincias:
        libres = [u for u, r in problem.units.items() if r["province"] == prov and u not in frozen_unit]
        k_libre = cuotas.get(str(prov), 0) - len({d for u, d in frozen_unit.items() if problem.units[u]["province"] == prov})
        info = {"unidades": len(libres), "k": k_libre}
        res["provincias"][str(prov)] = info
        if k_libre <= 0 or not libres:
            info["estado"] = "SIN_K" if libres else "VACIA"
            continue
        nxg = nx.Graph()
        for u in libres:
            nxg.add_node(u, population=problem.units[u]["population"], unit_id=u)
        nxg.add_edges_from((u, v) for u, v in problem.edges if u in nxg and v in nxg)
        info["componentes"] = nx.number_connected_components(nxg)
        g = Graph.from_networkx(nxg)
        objetivo = sum(problem.units[u]["population"] for u in libres) / k_libre
        partes = {u: 0 for u in libres} if k_libre == 1 else None
        if partes is not None:
            info["epsilon"] = None
        for eps in (() if partes is not None else (tol, band)):
            try:
                crudo = recursive_tree_part(
                    g, range(k_libre), objetivo, "population", eps, node_repeats=1,
                    bipartition_tree_fn=partial(bipartition_tree, max_attempts=strategy.max_bipartition_attempts or 10000,
                                                allow_pair_reselection=True),
                    rng=semilla)
                partes = {g.node_data(n)["unit_id"]: d for n, d in crudo.items()}
                info["epsilon"] = eps
                break
            except Exception as exc:  # BalanceError, RuntimeError de gerrychain
                info.setdefault("errores", []).append(f"eps={eps}: {type(exc).__name__}: {str(exc)[:160]}")
        if partes is None:
            info["estado"] = "RTP_INFACTIBLE"
            continue
        info["estado"] = "OK"
        for u, d in partes.items():
            asignacion[u] = etiqueta + int(d)
        etiqueta += k_libre
    faltan = [u for u in problem.units if u not in asignacion]
    res["unidades_sin_asignar"] = len(faltan)
    violaciones = ["unit_universe"] if faltan else gs.hard_constraint_violations(problem, asignacion, contract)
    res["violaciones"] = violaciones
    res["objetivo_poblacion"] = total / contract.expected_k
    res["admisible"] = not violaciones
    if not faltan:
        gs.materialise_output(problem, asignacion, salida)
    informe.write_text(json.dumps(res, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return 0 if not violaciones else 3


def _escribir_semilla(m04: Path, asignacion_csv: Path, salida: Path) -> None:
    """Copia el GeoJSON M04 (con ddd_unit_id) cambiando district_id por la asignación sección→distrito del CSV."""
    import zipfile
    with open(asignacion_csv, encoding="utf-8") as fh:
        filas = list(csv.DictReader(fh))
    etiquetas = {d: i for i, d in enumerate(sorted({f["distrito"] for f in filas}, key=str))}
    asig = {str(f["seccion"]): etiquetas[f["distrito"]] for f in filas}
    with zipfile.ZipFile(m04) as zf:
        nombre = next(n for n in zf.namelist() if n.lower().endswith((".geojson", ".json")))
        data = json.loads(zf.read(nombre))
    for feat in data["features"]:
        props = feat["properties"]
        props["district_id"] = asig[str(props["CUSEC_KEY"])]
    with zipfile.ZipFile(salida, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(nombre, json.dumps(data, ensure_ascii=False))


# --------------------------------------------------------------------------- un territorio
def ejecutar_uno(t: str, out: Path, generador: str, semilla: int) -> dict:
    etiqueta = f"{generador}-s{semilla}"
    res: dict = {"territorio": t, "generador": generador, "semilla": semilla, "m05": etiqueta, "tiempos": {}}
    cache = bm.restaurar(t, out)
    if cache is None:
        res["estado"] = "SIN_ENTRADAS"
        return res
    dest = out / "banco" / etiqueta / t
    shutil.rmtree(dest, ignore_errors=True)
    dest.mkdir(parents=True)
    log = dest / "log.txt"
    run_id = f"banco-{t}-{etiqueta}"
    env = dict(os.environ, DDD_RUN_ID=run_id, PYTHONHASHSEED="0")
    p = str(bm.contrato(t).relative_to(ROOT))
    py = sys.executable
    res["estado"] = "OK"
    for nombre, cmd in bm.pasos_m04(p, run_id, dest):
        rc, s = bm._run(cmd, log, env)
        res["tiempos"][nombre] = s
        if rc != 0:
            res.update(estado=f"FALLO_{nombre}", rc=rc)
            return bm.validar_y_resumir(t, p, run_id, dest, res, cache, log, env)
    gc = [GC_PY, "ddd_core/m05_gerrychain_strategy.py", "--params", p, "--run-id", run_id,
          "--seed-count", "1", "--seed-base", str(semilla)]
    canon = [py, "modulos/05_optimizar_distritos.py", "--params", p]
    if generador == "canonico":
        rc, s = bm._run(canon, log, env)
        res["tiempos"]["M05"] = s
    elif generador == "competidor":
        rc, s = bm._run(COMPETIDOR + ["--params", p, "--run-id", run_id, "--semilla", str(semilla)], log, env)
        res["tiempos"]["M05"] = s
        res["competidor"] = " ".join(COMPETIDOR)
    else:
        inicial: list[str] = []
        rc, s = bm._run([py, "ddd_core/m05_gerrychain_strategy.py", "--params", p, "--run-id", run_id,
                         "--validate-baseline-only", "--seed-count", "1"], log, env)
        res["tiempos"]["baseline"] = s
        res["m04_admisible"] = rc == 0
        if rc != 0:
            # Como procedimiento.sh: semilla M05 canónica reparada si la Formación M04 no es admisible.
            rc, s = bm._run(canon, log, env)
            res["tiempos"]["semilla_canonica"] = s
            out05 = next(cache.glob("*_m05_distritos_optimizados.geojson.zip"), None)
            if rc == 0 and out05:
                seed = cache / "banco_semilla_canonica.geojson.zip"
                shutil.copy2(out05, seed)
                inicial = ["--initial", str(seed)]
                res["semilla_inicial"] = "canonica"
        if generador == "exacto":
            # Semilla de factibilidad del certificador exacto (T-136 1.1.0, CP-SAT, perfil producción) sobre el M04
            # (ddd_unit_id, DDD_PARTITION, DDD_MUNICIPALITY_PARTITION).
            # Si M04 no es admisible (p. ej. sin ddd_unit_id, Cádiz), las unidades salen de la semilla canónica, como en
            # producción.
            m04 = Path(inicial[1]) if inicial else next(cache.glob("*_m04_semillas.geojson.zip"))
            graf = next(cache.glob("*_m03_grafo.json"))
            asig = dest / "SEMILLA_EXACTA.csv"
            informe = dest / "CERTIFICADOR.json"
            rc, s = bm._run([BANCO_PY, "herramientas/certificador_exacto.py", "--params", p, "--grafo", str(graf),
                             "--secciones", str(m04), "--perfil", "produccion", "--objetivo", "factibilidad",
                             "--tiempo", str(TIEMPO_EXACTO), "--hilos", "2", "--salida", str(informe),
                             "--asignacion-csv", str(asig)], log, env)
            res["tiempos"]["semilla_exacta"] = s
            cert = json.loads(informe.read_text(encoding="utf-8")) if informe.is_file() else {"error": rc}
            res["certificador"] = {k: cert.get(k) for k in ("estado", "atomos", "variables", "tiempo_s", "comprobacion")
                                   if k in cert} or cert
            if not asig.is_file():
                res["estado"] = f"SEMILLA_EXACTA_{cert.get('estado', 'FALLO')}"
                res["validacion"] = "NO_GENERADO"
                (dest / "RESULTADO.json").write_text(json.dumps(res, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
                return res
            semilla_ex = cache / "banco_semilla_exacta.geojson.zip"
            _escribir_semilla(m04, asig, semilla_ex)
            inicial = ["--initial", str(semilla_ex)]
            res["semilla_inicial"] = "exacta"
        if generador == "arbol":
            arbol = cache / "banco_semilla_arbol.geojson.zip"
            informe = dest / "SEMILLA_ARBOL.json"
            rc, s = bm._run([GC_PY, "-c",
                             "import sys;sys.path.insert(0,'.');from herramientas.banco_generadores import semilla_arbol as f;"
                             "from pathlib import Path as P;a=sys.argv[1:];"
                             "sys.exit(f(a[0],a[1],P(a[2]),P(a[3]),int(a[4]),P(a[5]) if a[5] else None))",
                             p, run_id, str(arbol), str(informe), str(semilla), inicial[1] if inicial else ""], log, env)
            res["tiempos"]["semilla_arbol"] = s
            res["semilla_arbol"] = json.loads(informe.read_text(encoding="utf-8")) if informe.is_file() else {"error": rc}
            if rc != 0:
                res["estado"] = "SEMILLA_ARBOL_NO_ADMISIBLE" if rc == 3 else f"FALLO_semilla_arbol_rc{rc}"
                res["validacion"] = "NO_GENERADO"
                (dest / "RESULTADO.json").write_text(json.dumps(res, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
                return res
            inicial = ["--initial", str(arbol)]
            res["semilla_inicial"] = "arbol"
        rc, s = bm._run(gc + inicial, log, env)
        res["tiempos"]["M05"] = s
    if rc != 0:
        res.update(estado="FALLO_M05", rc=rc)
    else:
        rc, s = bm._run([py, "modulos/06_consolidar_distritos.py", "--params", p], log, env)
        res["tiempos"]["M06"] = s
        if rc != 0:
            res.update(estado="FALLO_M06", rc=rc)
    return bm.validar_y_resumir(t, p, run_id, dest, res, cache, log, env)


def ejecutar(args) -> int:
    out = Path(args.out)
    for t in (bm.territorios() if args.todos else args.territorios):
        for g in args.generadores:
            for s in args.semillas:
                hecho = out / "banco" / f"{g}-s{s}" / t / "RESULTADO.json"
                if args.saltar_hechos and hecho.is_file():
                    continue
                r = ejecutar_uno(t, out, g, s)
                malas = [k for k, v in (r.get("reglas") or {}).items() if not v]
                print(f"{t} {g} s{s}: {r['estado']} validación={r.get('validacion')} FAIL={malas} "
                      f"{r.get('metricas', {})} t={sum(r['tiempos'].values()):.1f}s", flush=True)
    return 0


def reproducibilidad(args) -> int:
    """Ejecuta dos veces cada (territorio, generador, semilla) y compara bit a bit la composición M06 (sha256)."""
    out = Path(args.out)
    filas = []
    for t in (bm.territorios() if args.todos else args.territorios):
        for g in args.generadores:
            for s in args.semillas:
                huellas = []
                for i in (1, 2):
                    sub = out / f"_repro{i}"
                    sub.mkdir(parents=True, exist_ok=True)
                    ent = sub / "entradas"
                    if not ent.exists():
                        ent.symlink_to((out / "entradas").resolve())
                    r = ejecutar_uno(t, sub, g, s)
                    huellas.append(r.get("composicion_sha256"))
                igual = huellas[0] is not None and huellas[0] == huellas[1]
                filas.append({"territorio": t, "generador": g, "semilla": s, "sha256_1": huellas[0], "sha256_2": huellas[1],
                              "reproducible": igual})
                print(f"{t} {g} s{s}: reproducible={igual}", flush=True)
    with open(out / "REPRODUCIBILIDAD.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(filas[0]))
        w.writeheader()
        w.writerows(filas)
    return 0 if all(f["reproducible"] for f in filas) else 1


def matriz(args) -> int:
    out = Path(args.out)
    filas = []
    for f in sorted((out / "banco").glob("*/*/RESULTADO.json")):
        r = json.loads(f.read_text(encoding="utf-8"))
        m = r.get("metricas") or {}
        sa = r.get("semilla_arbol") or {}
        filas.append({
            "territorio": r["territorio"], "generador": r["generador"], "semilla": r["semilla"],
            "estado": r.get("estado"), "validacion": r.get("validacion"),
            "reglas_fail": " ".join(k for k, v in (r.get("reglas") or {}).items() if not v),
            "desvio_max": m.get("desvio_max"), "fuera_tolerancia": m.get("fuera_tolerancia"),
            "municipios_partidos": m.get("municipios_partidos"), "tiempo_s": round(sum(r["tiempos"].values()), 1),
            "m04_admisible": r.get("m04_admisible"), "semilla_inicial": r.get("semilla_inicial", "m04"),
            "arbol_violaciones": " ".join(sa.get("violaciones") or []),
            "arbol_provincias_infactibles": " ".join(p for p, i in (sa.get("provincias") or {}).items() if i.get("estado") != "OK"),
            "composicion_sha256": r.get("composicion_sha256"), "fallos": " | ".join(r.get("fallos") or []),
        })
    if not filas:
        print("sin resultados")
        return 1
    with open(out / "BANCO.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(filas[0]))
        w.writeheader()
        w.writerows(filas)
    resumen = {}
    for f in filas:
        g = resumen.setdefault(f["generador"], {"ejecuciones": 0, "PASS": 0, "territorios": set(), "territorios_siempre_pass": {}})
        g["ejecuciones"] += 1
        g["PASS"] += f["validacion"] == "PASS"
        g["territorios_siempre_pass"].setdefault(f["territorio"], True)
        g["territorios_siempre_pass"][f["territorio"]] &= f["validacion"] == "PASS"
    for g, v in resumen.items():
        print(f"{g}: PASS {v['PASS']}/{v['ejecuciones']}; territorios siempre válidos "
              f"{sum(v['territorios_siempre_pass'].values())}/{len(v['territorios_siempre_pass'])}")
    return 0


# --------------------------------------------------------------------------- calidad
def _calidad_una(m01, comp: Path, k: int, tol: float) -> dict:
    """Métricas de calidad de una composición M06 sobre las secciones M01 (municipio real CUMUN y geometría)."""
    import math

    import pandas as pd
    c = pd.read_csv(comp, dtype=str)
    sid = "CUSEC_KEY" if "CUSEC_KEY" in c.columns else c.columns[0]
    asig = c.set_index(sid)["district_id"]
    g = m01.assign(district_id=m01["CUSEC_KEY"].map(asig))
    if g["district_id"].isna().any():
        return {"error": f"secciones sin distrito: {int(g['district_id'].isna().sum())}"}
    total = float(g["_pop"].sum())
    objetivo = total / k
    pops = g.groupby("district_id")["_pop"].sum()
    rel = pops / objetivo - 1
    mun_d = g.groupby("CUMUN")["district_id"].nunique()
    d_mun = g.groupby("district_id")["CUMUN"].nunique()
    dist = g[["district_id", "geometry"]].dissolve(by="district_id")
    pp = (4 * math.pi * dist.geometry.area / dist.geometry.length ** 2)
    return {"K": int(len(pops)), "fuera_tolerancia": int((rel.abs() > tol + 1e-9).sum()),
            "desvio_max": round(float(rel.abs().max()), 5), "ecm": round(float((rel ** 2).mean()), 6),
            "municipios_partidos": int((mun_d > 1).sum()), "distritos_mixtos": int((d_mun > 1).sum()),
            "polsby_popper_medio": round(float(pp.mean()), 5)}


def calidad(args) -> int:
    """CALIDAD.csv: métricas de calidad del canónico (bateria/motor/<v>) y del banco (bateria/banco), por territorio."""
    import geopandas as gpd
    out = Path(args.out)
    casos: dict[str, list[tuple[str, int, Path]]] = {}
    for comp in sorted((out / "motor" / args.canonico).glob("*/*_m06_composicion_distritos.csv")):
        casos.setdefault(comp.parent.name, []).append(("canonico", 0, comp))
    for comp in sorted((out / "banco").glob("*/*/*_m06_composicion_distritos.csv")):
        r = json.loads((comp.parent / "RESULTADO.json").read_text(encoding="utf-8"))
        if r.get("validacion") == "PASS":
            casos.setdefault(r["territorio"], []).append((r["generador"], int(r["semilla"]), comp))
    filas = []
    for t in sorted(casos):
        if args.territorios and t not in args.territorios:
            continue
        m01p = next((out / "entradas" / t).glob("*_m01_secciones_poblacion.geojson.zip"))
        m01 = gpd.read_file(m01p).to_crs(3035)
        popc = next(c for c in m01.columns if c.startswith("POP_"))
        m01["_pop"] = pd_num(m01[popc])
        m01["CUSEC_KEY"] = m01["CUSEC_KEY"].astype(str)
        cfg = bm._cfg(t)
        tol = float((cfg.get("validation") or {}).get("target_tolerance_ratio") or 0.12)
        for gen, sem, comp in casos[t]:
            import pandas as pd
            k = int(pd.read_csv(comp, usecols=["district_id"])["district_id"].nunique())
            filas.append({"territorio": t, "generador": gen, "semilla": sem, **_calidad_una(m01, comp, k, tol)})
        print(t, len(casos[t]), flush=True)
    with open(out / "CALIDAD.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=sorted({k for f in filas for k in f}, key=lambda x: (x not in ("territorio", "generador", "semilla"), x)))
        w.writeheader()
        w.writerows(filas)
    return 0


def pd_num(serie):
    import pandas as pd
    return pd.to_numeric(serie.astype(str).str.replace(".", "", regex=False), errors="coerce").fillna(0)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Banco de generadores (T-132 A)")
    sub = ap.add_subparsers(dest="cmd", required=True)
    e = sub.add_parser("ejecutar")
    e.add_argument("territorios", nargs="*")
    e.add_argument("--todos", action="store_true")
    e.add_argument("--generadores", nargs="+", default=list(GENERADORES), choices=GENERADORES)
    e.add_argument("--semillas", nargs="+", type=int, default=[1, 2, 3, 4, 5])
    e.add_argument("--out", default=str(bm.OUT))
    e.add_argument("--saltar-hechos", action="store_true", help="no repite las combinaciones con RESULTADO.json")
    sub.add_parser("matriz").add_argument("--out", default=str(bm.OUT))
    rp = sub.add_parser("reproducibilidad")
    rp.add_argument("territorios", nargs="*")
    rp.add_argument("--todos", action="store_true")
    rp.add_argument("--generadores", nargs="+", default=["competidor"], choices=GENERADORES)
    rp.add_argument("--semillas", nargs="+", type=int, default=[1])
    rp.add_argument("--out", default=str(bm.OUT))
    c = sub.add_parser("calidad")
    c.add_argument("territorios", nargs="*")
    c.add_argument("--canonico", default="7.4.4")
    c.add_argument("--out", default=str(bm.OUT))
    a = ap.parse_args(argv)
    return {"ejecutar": ejecutar, "matriz": matriz, "calidad": calidad, "reproducibilidad": reproducibilidad}[a.cmd](a)


if __name__ == "__main__":
    raise SystemExit(main())
