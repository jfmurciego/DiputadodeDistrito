#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PROYECTO: Diputado de Distrito
Módulo 04 — Generar distritos iniciales
VERSIÓN: 7.4.6
NOMBRE DE VERSIÓN: Factibilidad provincial tras cierres urbanos
FECHA: 2026-09-11
FUNCIÓN: ejecutar el motor M04 v7.4.5 y reajustar únicamente fronteras internas núcleo-residuo de municipios partidos cuando un núcleo urbano cerrado haría imposible que los distritos abiertos restantes de su provincia entren en la banda objetivo.
ENTRADAS: grafo M03, salida territorial M04 v7.4.5 y configuración territorial.
SALIDAS: GeoJSON M04 con district_id, ddd_unit_id y ddd_closed_urban; informe M04 actualizado.
REGLAS DURAS: no cruza provincias; no crea ni elimina distritos; solo mueve secciones entre un núcleo U* y el residuo R del mismo municipio; conserva conectividad de ambos distritos, pasarelas topológicas y salida territorial del residuo; el núcleo cerrado permanece dentro de ±tolerancia.
ESTADO: candidato CYL-03.
CAMBIOS: añade una invariante de factibilidad provincial para cierres irreversibles. Los núcleos cerrados se aproximan al promedio poblacional exigido por la cuota provincial cuando ello puede hacerse moviendo secciones contiguas del mismo municipio; se rechaza cualquier cierre que deje a los distritos abiertos con una masa total imposible de repartir dentro de ±12 %.
MOTIVO: M04 v7.4.5 cerraba Segovia-U1 con 26.220 habitantes, cifra individualmente válida, pero dejaba 132.031 habitantes para cuatro distritos abiertos cuyo máximo conjunto era 131.188,66. M05 no podía resolver matemáticamente esa semilla. La factibilidad del subproblema restante debe ser una condición del cierre, no una responsabilidad posterior de M05.
ANTERIOR: legacy/modulo04/04_generar_semillas_v7.4.5.py
"""
from __future__ import annotations

import argparse
import importlib.util
import io
import json
import sys
import zipfile
from pathlib import Path

import geopandas as gpd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ddd_core.config import load_params_yaml, module_cfg, require

BASE_ENGINE = ROOT / "ddd_core" / "m04_seed_engine_v745.py"


def _load_base_engine():
    spec = importlib.util.spec_from_file_location("ddd_m04_seed_engine_v745", BASE_ENGINE)
    if spec is None or spec.loader is None:
        raise SystemExit(f"M04: no se puede cargar motor base {BASE_ENGINE}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _load_geo(path):
    p = Path(path)
    if p.suffix.lower() == ".zip":
        with zipfile.ZipFile(p) as z:
            name = next(n for n in z.namelist() if n.lower().endswith((".geojson", ".json")) and not n.endswith("/"))
            return gpd.read_file(io.BytesIO(z.read(name)))
    return gpd.read_file(p)


def _write_geo(gdf, path):
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    tmp = out.parent / (out.stem.replace(".geojson", "") + ".geojson")
    gdf.to_file(tmp, driver="GeoJSON")
    with zipfile.ZipFile(out, "w", compression=zipfile.ZIP_DEFLATED) as z:
        z.write(tmp, arcname=tmp.name)
    tmp.unlink(missing_ok=True)


def _connected(nodes, adj):
    nodes = set(nodes)
    if not nodes:
        return False
    seen = {next(iter(nodes))}
    stack = list(seen)
    while stack:
        u = stack.pop()
        for v in adj.get(u, set()):
            if v in nodes and v not in seen:
                seen.add(v)
                stack.append(v)
    return len(seen) == len(nodes)


def _main_args():
    ap = argparse.ArgumentParser(add_help=False)
    ap.add_argument("--params", required=True)
    args, _ = ap.parse_known_args()
    return args


def _adjust_province_feasibility(params_path):
    cfg = load_params_yaml(params_path)
    s4 = module_cfg(cfg, "modulo_04_generar_semillas", "step4_seed_districts")
    s2 = module_cfg(cfg, "modulo_02_construir_adyacencias", "step2_export_edges")
    val = cfg.get("validation", {}) or {}

    ing = require(s4.get("in_graph_json"), "Falta M04 grafo")
    out = require(s4.get("out_geojson"), "Falta salida M04")
    report_path = s4.get("out_report", "")
    idf = require(s4.get("id_field"), "Falta id M04")
    provf = s4.get("province_field", "CPRO")
    munf = s4.get("municipality_field", "CUMUN")
    did = "district_id"

    graph = json.loads(Path(ing).read_text(encoding="utf-8"))
    pop = {str(n["id"]): int(n.get("pop", 0)) for n in graph["nodes"]}
    adj = {n: set() for n in pop}
    for e in graph["edges"]:
        u, v = str(e["u"]), str(e["v"])
        if u in adj and v in adj:
            adj[u].add(v)
            adj[v].add(u)

    g = _load_geo(out)
    g[idf] = g[idf].astype(str)
    g[provf] = g[provf].astype(str).str.zfill(2)
    g[munf] = g[munf].astype(str)
    g[did] = g[did].astype(int)
    g["ddd_unit_id"] = g["ddd_unit_id"].astype(str)

    K = int(g[did].nunique())
    total = sum(pop.values())
    target = total / K
    tol = target * float(val.get("target_tolerance_ratio", 0.12))
    lo, hi = target - tol, target + tol
    quota = {str(k).zfill(2): int(v) for k, v in (val.get("province_districts") or {}).items()}

    bridge_nodes = set()
    for b in s2.get("topology_bridges", []) or []:
        for x in (b.get("u"), b.get("v")):
            if x is not None:
                bridge_nodes.add(str(x))

    adjustments = []

    def district_nodes(d):
        return set(g.loc[g[did] == d, idf].astype(str))

    def district_pop(d):
        return int(g.loc[g[did] == d, "district_pop_section"].sum())

    def residual_has_external_gateway(res_nodes, municipality_nodes):
        return any(any(nb not in municipality_nodes for nb in adj.get(n, set())) for n in res_nodes)

    def move_candidate(prov, direction, required_delta, province_average):
        candidates = []
        prov_rows = g[g[provf] == prov]
        for mun, mx in prov_rows.groupby(munf):
            unit_ids = set(mx["ddd_unit_id"].astype(str))
            residual_ids = sorted(u for u in unit_ids if u.endswith(":R"))
            core_ids = sorted(u for u in unit_ids if ":U" in u)
            if not residual_ids or not core_ids:
                continue
            municipality_nodes = set(mx[idf].astype(str))
            for rid in residual_ids:
                rnodes = set(g.loc[g["ddd_unit_id"] == rid, idf].astype(str))
                if not rnodes:
                    continue
                rdists = set(g.loc[g["ddd_unit_id"] == rid, did].astype(int))
                if len(rdists) != 1:
                    continue
                rd = next(iter(rdists))
                for cid in core_ids:
                    cnodes = set(g.loc[g["ddd_unit_id"] == cid, idf].astype(str))
                    if not cnodes:
                        continue
                    cdists = set(g.loc[g["ddd_unit_id"] == cid, did].astype(int))
                    if len(cdists) != 1:
                        continue
                    cd = next(iter(cdists))
                    cpop = sum(pop[n] for n in cnodes)
                    if direction == "open_to_closed":
                        source, recv = rnodes, cnodes
                        movable = rnodes - bridge_nodes
                    else:
                        source, recv = cnodes, rnodes
                        movable = cnodes - bridge_nodes
                    for n in movable:
                        if not any(nb in recv for nb in adj.get(n, set())):
                            continue
                        new_source = source - {n}
                        new_recv = recv | {n}
                        if not new_source or not _connected(new_source, adj) or not _connected(new_recv, adj):
                            continue
                        if direction == "open_to_closed":
                            if not residual_has_external_gateway(new_source, municipality_nodes):
                                continue
                            new_core_pop = cpop + pop[n]
                        else:
                            if not residual_has_external_gateway(new_recv, municipality_nodes):
                                continue
                            new_core_pop = cpop - pop[n]
                        if not (lo <= new_core_pop <= hi):
                            continue
                        new_source_dnodes = district_nodes(rd if direction == "open_to_closed" else cd) - {n}
                        new_recv_dnodes = district_nodes(cd if direction == "open_to_closed" else rd) | {n}
                        if not _connected(new_source_dnodes, adj) or not _connected(new_recv_dnodes, adj):
                            continue
                        # Prefer reaching the provincial equilibrium with the smallest boundary change.
                        after_gap = abs(new_core_pop - province_average)
                        enough = pop[n] >= required_delta
                        score = (0 if enough else 1, after_gap, abs(pop[n] - required_delta), pop[n], n, cid, rid)
                        candidates.append((score, n, cid, rid, cd, rd, direction, pop[n]))
        return min(candidates, key=lambda x: x[0]) if candidates else None

    for prov in sorted(quota):
        q = quota[prov]
        prov_mask = g[provf] == prov
        province_pop = int(g.loc[prov_mask, "district_pop_section"].sum())
        province_average = province_pop / q

        for _ in range(200):
            district_ids = sorted(g.loc[prov_mask, did].unique())
            closed_ids = [d for d in district_ids if bool(g.loc[g[did] == d, "ddd_closed_urban"].all())]
            open_ids = [d for d in district_ids if d not in closed_ids]
            open_pop = sum(district_pop(d) for d in open_ids)
            open_min = len(open_ids) * lo
            open_max = len(open_ids) * hi

            # Also move closed cores toward the unavoidable provincial equilibrium when possible.
            closed_gap = 0.0
            direction = None
            if open_pop > open_max + 1e-9:
                direction = "open_to_closed"
                closed_gap = open_pop - open_max
            elif open_pop < open_min - 1e-9:
                direction = "closed_to_open"
                closed_gap = open_min - open_pop
            else:
                # Feasible already: reduce avoidable imbalance of irreversible cores toward province average.
                core_pops = [(d, district_pop(d)) for d in closed_ids]
                low_core = min(core_pops, key=lambda x: x[1], default=None)
                high_core = max(core_pops, key=lambda x: x[1], default=None)
                if low_core and low_core[1] < province_average - 250:
                    direction = "open_to_closed"
                    closed_gap = province_average - low_core[1]
                elif high_core and high_core[1] > province_average + 250:
                    direction = "closed_to_open"
                    closed_gap = high_core[1] - province_average
                else:
                    break

            cand = move_candidate(prov, direction, closed_gap, province_average)
            if cand is None:
                # If aggregate feasibility is already satisfied, inability to improve local equilibrium is not fatal.
                if open_min - 1e-9 <= open_pop <= open_max + 1e-9:
                    break
                raise SystemExit(
                    f"M04 v7.4.6: cierre urbano hace imposible provincia {prov}; "
                    f"open_pop={open_pop} rango=[{open_min:.2f},{open_max:.2f}] sin ajuste núcleo-residuo válido"
                )

            _, n, cid, rid, cd, rd, direction, p = cand
            old_unit = str(g.loc[g[idf] == n, "ddd_unit_id"].iloc[0])
            old_d = int(g.loc[g[idf] == n, did].iloc[0])
            if direction == "open_to_closed":
                new_unit, new_d, new_closed = cid, cd, True
            else:
                new_unit, new_d, new_closed = rid, rd, False
            g.loc[g[idf] == n, "ddd_unit_id"] = new_unit
            g.loc[g[idf] == n, did] = new_d
            g.loc[g[idf] == n, "ddd_closed_urban"] = new_closed
            adjustments.append({
                "province": prov,
                "section": n,
                "population": int(p),
                "direction": direction,
                "from_unit": old_unit,
                "to_unit": new_unit,
                "from_district": old_d,
                "to_district": new_d,
                "province_average": province_average,
            })

        # Hard postcondition: every irreversible closure leaves the residual provincial problem feasible.
        district_ids = sorted(g.loc[prov_mask, did].unique())
        closed_ids = [d for d in district_ids if bool(g.loc[g[did] == d, "ddd_closed_urban"].all())]
        open_ids = [d for d in district_ids if d not in closed_ids]
        open_pop = sum(district_pop(d) for d in open_ids)
        if not (len(open_ids) * lo - 1e-9 <= open_pop <= len(open_ids) * hi + 1e-9):
            raise SystemExit(f"M04 v7.4.6: factibilidad provincial residual incumplida en {prov}")

    # Revalidate district connectivity and update reports.
    pops = g.groupby(did)["district_pop_section"].sum()
    for d, x in g.groupby(did):
        ns = set(x[idf].astype(str))
        if not _connected(ns, adj):
            raise SystemExit(f"M04 v7.4.6: distrito {d} desconectado tras balance de núcleos")
        if x[provf].nunique() != 1:
            raise SystemExit(f"M04 v7.4.6: distrito {d} cruza provincia")

    _write_geo(g, out)
    rep = json.loads(Path(report_path).read_text(encoding="utf-8")) if report_path and Path(report_path).exists() else {}
    rep["version"] = "7.4.6"
    rep["min_pop"] = int(pops.min())
    rep["max_pop"] = int(pops.max())
    rep["outside_target_tolerance"] = int((abs(pops - target) > tol).sum())
    rep["province_feasibility_adjustments"] = adjustments
    rep.setdefault("rules", {})["closed_cores_preserve_province_residual_feasibility"] = True
    rep["rules"]["closed_cores_bias_toward_province_quota_average"] = True
    if report_path:
        Path(report_path).write_text(json.dumps(rep, ensure_ascii=False, indent=2), encoding="utf-8")
    print(
        f"[Módulo 4] OK v7.4.6 K={K} ajustes_factibilidad={len(adjustments)} "
        f"outside_tol={rep.get('outside_target_tolerance')} min={int(pops.min())} max={int(pops.max())} out={out}"
    )


def main():
    args = _main_args()
    base = _load_base_engine()
    base.main()
    _adjust_province_feasibility(args.params)


if __name__ == "__main__":
    main()
