#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PROYECTO: Diputado de Distrito
Módulo 04 — Generar distritos iniciales
VERSIÓN: 7.4.7
NOMBRE DE VERSIÓN: Ajuste mínimo dirigido de factibilidad provincial
FECHA: 2026-09-11
FUNCIÓN: ejecutar M04 v7.4.5 y corregir exclusivamente cierres urbanos que hagan matemáticamente imposible repartir la población abierta restante de una provincia dentro de ±tolerancia.
ENTRADAS: grafo M03, salida M04 v7.4.5 y configuración territorial.
SALIDAS: GeoJSON M04 e informe recalculado desde el estado final.
REGLAS DURAS: provincia única; K y cuotas invariantes; movimientos solo entre U* y R del mismo municipio; conectividad de núcleo, residuo y distritos; pasarelas topológicas preservadas; núcleo cerrado dentro de ±tolerancia; suelo/techo final recalculado y obligatorio.
ESTADO: candidato CYL-03.
CAMBIOS: elimina el reequilibrado opcional hacia la media provincial de v7.4.6. Solo actúa cuando open_pop queda fuera de N_abiertos×[target−tol,target+tol], selecciona el movimiento fronterizo mínimo que repara el déficit y se detiene inmediatamente al recuperar factibilidad. Recalcula hard/outside/min/max en vez de heredar métricas del motor base.
MOTIVO: v7.4.6 demostró la invariante pero realizó 1.021 movimientos innecesarios, empeoró outside_tol 4→9 y produjo min=22.275 mientras el informe heredado seguía declarando hard=0. La corrección debe ser mínima, dirigida y autoauditada.
ANTERIOR: legacy/modulo04/04_generar_semillas_v7.4.6.py
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

from ddd_core.config import load_params_yaml, module_cfg, require, hard_limits

BASE_ENGINE = ROOT / "ddd_core" / "m04_seed_engine_v745.py"


def load_base():
    spec = importlib.util.spec_from_file_location("ddd_m04_seed_engine_v745", BASE_ENGINE)
    if spec is None or spec.loader is None:
        raise SystemExit(f"M04: no se puede cargar {BASE_ENGINE}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def load_geo(path):
    p = Path(path)
    if p.suffix.lower() == ".zip":
        with zipfile.ZipFile(p) as z:
            name = next(n for n in z.namelist() if n.lower().endswith((".geojson", ".json")) and not n.endswith("/"))
            return gpd.read_file(io.BytesIO(z.read(name)))
    return gpd.read_file(p)


def write_geo(gdf, path):
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    tmp = out.parent / (out.stem.replace(".geojson", "") + ".geojson")
    gdf.to_file(tmp, driver="GeoJSON")
    with zipfile.ZipFile(out, "w", compression=zipfile.ZIP_DEFLATED) as z:
        z.write(tmp, arcname=tmp.name)
    tmp.unlink(missing_ok=True)


def connected(nodes, adj):
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


def postprocess(params_path):
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

    g = load_geo(out)
    g[idf] = g[idf].astype(str)
    g[provf] = g[provf].astype(str).str.zfill(2)
    g[munf] = g[munf].astype(str)
    g[did] = g[did].astype(int)
    g["ddd_unit_id"] = g["ddd_unit_id"].astype(str)

    K = int(g[did].nunique())
    total = sum(pop.values())
    target, floor, cap, tol = hard_limits(cfg, k=K, total_pop=total)
    lo, hi = target - tol, target + tol
    quota = {str(k).zfill(2): int(v) for k, v in (val.get("province_districts") or {}).items()}

    bridge_nodes = set()
    for b in s2.get("topology_bridges", []) or []:
        for x in (b.get("u"), b.get("v")):
            if x is not None:
                bridge_nodes.add(str(x))

    def dnodes(d):
        return set(g.loc[g[did] == d, idf].astype(str))

    def dpop(d):
        return int(g.loc[g[did] == d, "district_pop_section"].sum())

    def residual_gateway_ok(nodes, municipality_nodes):
        return any(any(nb not in municipality_nodes for nb in adj.get(n, set())) for n in nodes)

    def candidates(prov, direction, required):
        result = []
        for mun, mx in g[g[provf] == prov].groupby(munf):
            municipality_nodes = set(mx[idf].astype(str))
            unit_ids = set(mx["ddd_unit_id"].astype(str))
            residuals = sorted(u for u in unit_ids if u.endswith(":R"))
            cores = sorted(u for u in unit_ids if ":U" in u)
            for rid in residuals:
                rnodes = set(g.loc[g["ddd_unit_id"] == rid, idf].astype(str))
                rds = set(g.loc[g["ddd_unit_id"] == rid, did].astype(int))
                if not rnodes or len(rds) != 1:
                    continue
                rd = next(iter(rds))
                for cid in cores:
                    cnodes = set(g.loc[g["ddd_unit_id"] == cid, idf].astype(str))
                    cds = set(g.loc[g["ddd_unit_id"] == cid, did].astype(int))
                    if not cnodes or len(cds) != 1:
                        continue
                    cd = next(iter(cds))
                    cpop = sum(pop[n] for n in cnodes)
                    source, recv = (rnodes, cnodes) if direction == "open_to_closed" else (cnodes, rnodes)
                    source_d, recv_d = (rd, cd) if direction == "open_to_closed" else (cd, rd)
                    for n in sorted(source - bridge_nodes):
                        if not any(nb in recv for nb in adj.get(n, set())):
                            continue
                        new_source = source - {n}
                        new_recv = recv | {n}
                        if not new_source or not connected(new_source, adj) or not connected(new_recv, adj):
                            continue
                        new_core_pop = cpop + pop[n] if direction == "open_to_closed" else cpop - pop[n]
                        if not (lo <= new_core_pop <= hi):
                            continue
                        new_residual = new_source if direction == "open_to_closed" else new_recv
                        if not residual_gateway_ok(new_residual, municipality_nodes):
                            continue
                        if not connected(dnodes(source_d) - {n}, adj):
                            continue
                        if not connected(dnodes(recv_d) | {n}, adj):
                            continue
                        # Exact repair first; otherwise smallest legal step toward feasibility.
                        enough = pop[n] >= required
                        overshoot = max(0.0, pop[n] - required)
                        score = (0 if enough else 1, overshoot if enough else -pop[n], pop[n], n, cid, rid)
                        result.append((score, n, cid, rid, cd, rd, int(pop[n])))
        return sorted(result, key=lambda x: x[0])

    adjustments = []
    for prov in sorted(quota):
        for _ in range(50):
            ids = sorted(g.loc[g[provf] == prov, did].unique())
            closed = [d for d in ids if bool(g.loc[g[did] == d, "ddd_closed_urban"].all())]
            open_ids = [d for d in ids if d not in closed]
            open_pop = sum(dpop(d) for d in open_ids)
            open_min, open_max = len(open_ids) * lo, len(open_ids) * hi
            if open_min - 1e-9 <= open_pop <= open_max + 1e-9:
                break
            if open_pop > open_max:
                direction, required = "open_to_closed", open_pop - open_max
            else:
                direction, required = "closed_to_open", open_min - open_pop

            cs = candidates(prov, direction, required)
            if not cs:
                raise SystemExit(
                    f"M04 v7.4.7: provincia {prov} agregadamente imposible y sin ajuste núcleo-residuo válido; "
                    f"open_pop={open_pop} rango=[{open_min:.2f},{open_max:.2f}] delta={required:.2f}"
                )
            _, n, cid, rid, cd, rd, p = cs[0]
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
                "population": p,
                "direction": direction,
                "required_before_move": required,
                "from_unit": old_unit,
                "to_unit": new_unit,
                "from_district": old_d,
                "to_district": new_d,
            })
        else:
            raise SystemExit(f"M04 v7.4.7: demasiados ajustes en provincia {prov}")

    pops = g.groupby(did)["district_pop_section"].sum()
    hard = int(((pops < floor) | (pops > cap)).sum())
    outside = int((abs(pops - target) > tol).sum())

    if g[did].nunique() != K:
        raise SystemExit(f"M04 v7.4.7: K alterado {g[did].nunique()} != {K}")
    counts = {str(x[provf].iloc[0]).zfill(2): 0 for _, x in g.groupby(did)}
    for _, x in g.groupby(did):
        counts[str(x[provf].iloc[0]).zfill(2)] += 1
    if counts != quota:
        raise SystemExit(f"M04 v7.4.7: cuotas provinciales alteradas {counts} != {quota}")

    for d, x in g.groupby(did):
        ns = set(x[idf].astype(str))
        if not connected(ns, adj):
            raise SystemExit(f"M04 v7.4.7: distrito {d} desconectado")
        if x[provf].astype(str).str.zfill(2).nunique() != 1:
            raise SystemExit(f"M04 v7.4.7: distrito {d} cruza provincia")
        if bool(x["ddd_closed_urban"].all()):
            p = int(x["district_pop_section"].sum())
            if not (lo <= p <= hi):
                raise SystemExit(f"M04 v7.4.7: núcleo cerrado {d} fuera de tolerancia: {p}")

    # Final aggregate feasibility after all irreversible closures.
    for prov in sorted(quota):
        ids = sorted(g.loc[g[provf] == prov, did].unique())
        closed = [d for d in ids if bool(g.loc[g[did] == d, "ddd_closed_urban"].all())]
        open_ids = [d for d in ids if d not in closed]
        open_pop = sum(dpop(d) for d in open_ids)
        if not (len(open_ids) * lo - 1e-9 <= open_pop <= len(open_ids) * hi + 1e-9):
            raise SystemExit(f"M04 v7.4.7: factibilidad residual incumplida en {prov}")

    if hard:
        raise SystemExit(f"M04 v7.4.7: {hard} violaciones duras tras ajuste")

    write_geo(g, out)
    rep = json.loads(Path(report_path).read_text(encoding="utf-8")) if report_path and Path(report_path).exists() else {}
    rep.update({
        "version": "7.4.7",
        "min_pop": int(pops.min()),
        "max_pop": int(pops.max()),
        "outside_target_tolerance": outside,
        "hard_population_violations": hard,
        "province_counts": counts,
        "province_feasibility_adjustments": adjustments,
    })
    rep.setdefault("rules", {})["closed_cores_preserve_province_residual_feasibility"] = True
    rep["rules"]["province_feasibility_adjustment_is_minimal_and_conditional"] = True
    rep["rules"]["final_population_metrics_recomputed_after_postprocess"] = True
    if report_path:
        Path(report_path).write_text(json.dumps(rep, ensure_ascii=False, indent=2), encoding="utf-8")
    print(
        f"[Módulo 4] OK v7.4.7 K={K} ajustes_factibilidad={len(adjustments)} "
        f"hard={hard} outside_tol={outside} min={int(pops.min())} max={int(pops.max())} out={out}"
    )


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--params", required=True)
    args = ap.parse_args()
    load_base().main()
    postprocess(args.params)


if __name__ == "__main__":
    main()
