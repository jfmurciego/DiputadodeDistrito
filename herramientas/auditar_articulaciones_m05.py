#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PROYECTO: Diputado de Distrito
HERRAMIENTA: auditar_articulaciones_m05.py
VERSIÓN: 1.0.0
NOMBRE: Diagnóstico de articulaciones y lóbulos movibles M05
FECHA: 2026-09-11
FUNCIÓN: explicar la estructura topológica de los distritos fuera de tolerancia a nivel de unidad DDD.
ENTRADAS: grafo M03, GeoJSON resultante de M05 y configuración territorial.
SALIDAS: JSON con unidades articuladoras, componentes/lóbulos que aparecen al retirarlas, población,
municipios, fronteras exteriores y paquetes mínimos candidatos para movimientos compuestos.
REGLAS: solo diagnostica; no modifica asignaciones. La conectividad se deriva exclusivamente del grafo M03.
MOTIVO: EXT-03 demostró que no existe movimiento unitario ni swap 1x1 válido para los distritos 32 y 59;
antes de ampliar M05 necesitamos conocer el paquete conexo mínimo impuesto por la topología.
ANTERIOR: ninguno — herramienta nueva.
"""
from __future__ import annotations

import argparse
import io
import json
import sys
import zipfile
from collections import deque
from pathlib import Path

import geopandas as gpd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ddd_core.config import load_params_yaml, module_cfg


def load_geo(path):
    p = Path(path)
    if p.suffix.lower() == ".zip":
        with zipfile.ZipFile(p) as z:
            n = next(
                n for n in z.namelist()
                if n.lower().endswith((".geojson", ".json")) and not n.endswith("/")
            )
            return gpd.read_file(io.BytesIO(z.read(n)))
    return gpd.read_file(p)


def components(nodes, adj):
    remaining = set(nodes)
    result = []
    while remaining:
        start = min(remaining)
        seen = {start}
        q = deque([start])
        remaining.remove(start)
        while q:
            u = q.popleft()
            for v in adj.get(u, set()):
                if v in remaining:
                    remaining.remove(v)
                    seen.add(v)
                    q.append(v)
        result.append(seen)
    return sorted(result, key=lambda x: (-len(x), min(x)))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--params", required=True)
    ap.add_argument("--geojson", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    cfg = load_params_yaml(a.params)
    s5 = module_cfg(cfg, "modulo_05_optimizar_distritos", "step5_optimize_swaps")
    val = cfg.get("validation", {}) or {}

    graph = json.loads(Path(s5["in_graph_json"]).read_text(encoding="utf-8"))
    pop = {str(n["id"]): int(n.get("pop", 0)) for n in graph["nodes"]}
    sec_adj = {n: set() for n in pop}
    for e in graph["edges"]:
        u, v = str(e["u"]), str(e["v"])
        sec_adj.setdefault(u, set()).add(v)
        sec_adj.setdefault(v, set()).add(u)

    g = load_geo(a.geojson)
    idf = s5.get("id_field", "CUSEC_KEY")
    did = s5.get("district_field", "district_id")
    provf = s5.get("province_field", "CPRO")
    munf = s5.get("municipality_field", "CUMUN")
    g[idf] = g[idf].astype(str)
    g[did] = g[did].astype(int)
    g[provf] = g[provf].astype(str).str.zfill(2)
    if "ddd_unit_id" not in g.columns:
        raise SystemExit("Diagnóstico de articulaciones requiere ddd_unit_id en M05")
    g["ddd_unit_id"] = g["ddd_unit_id"].astype(str)

    section_unit = dict(zip(g[idf], g["ddd_unit_id"]))
    unit_nodes = {u: set(x[idf]) for u, x in g.groupby("ddd_unit_id")}
    unit_pop = {u: sum(pop[n] for n in ns) for u, ns in unit_nodes.items()}
    unit_dist = {u: int(x[did].iloc[0]) for u, x in g.groupby("ddd_unit_id")}
    unit_muns = {u: sorted(set(x[munf].astype(str))) for u, x in g.groupby("ddd_unit_id")}
    d_units = {d: set(x["ddd_unit_id"]) for d, x in g.groupby(did)}
    d_pop = {d: sum(unit_pop[u] for u in us) for d, us in d_units.items()}
    d_prov = {d: str(g[g[did] == d][provf].iloc[0]) for d in d_units}

    uadj = {u: set() for u in unit_nodes}
    for n, u in section_unit.items():
        for nb in sec_adj.get(n, set()):
            v = section_unit.get(nb)
            if v is not None and v != u:
                uadj[u].add(v)

    total = sum(pop.values())
    K = len(d_units)
    target = total / K
    floor = target * float(val.get("population_floor_ratio", 0.8))
    cap = target * float(val.get("population_cap_ratio", 1.75))
    tol = target * float(val.get("target_tolerance_ratio", 0.12))
    outliers = sorted(d for d, p in d_pop.items() if abs(p - target) > tol)

    diagnostics = []
    for d in outliers:
        us = set(d_units[d])
        internal_adj = {u: set(v for v in uadj[u] if v in us) for u in us}
        articulations = []

        for cut in sorted(us):
            rest = us - {cut}
            if len(rest) <= 1:
                continue
            comps = components(rest, internal_adj)
            if len(comps) <= 1:
                continue

            lobes = []
            for comp in comps:
                comp_pop = sum(unit_pop[u] for u in comp)
                municipalities = sorted({m for u in comp for m in unit_muns[u]})
                external = sorted({
                    unit_dist[v]
                    for u in comp
                    for v in uadj[u]
                    if unit_dist[v] != d and d_prov.get(unit_dist[v]) == d_prov[d]
                })
                touch_cut = sorted(u for u in comp if cut in internal_adj.get(u, set()))
                # Si se moviera el lóbulo completo dejando el corte en el donante,
                # el resto del distrito queda constituido por el corte + los demás lóbulos.
                donor_after = d_pop[d] - comp_pop
                lobes.append({
                    "units": sorted(comp),
                    "unit_count": len(comp),
                    "population": comp_pop,
                    "municipalities": municipalities,
                    "external_neighbor_districts": external,
                    "units_touching_articulation": touch_cut,
                    "donor_population_if_lobe_moves": donor_after,
                    "donor_within_floor_cap": floor <= donor_after <= cap,
                    "population_delta_to_target": comp_pop - (d_pop[d] - target),
                })

            articulations.append({
                "unit": cut,
                "population": unit_pop[cut],
                "municipalities": unit_muns[cut],
                "component_count_after_removal": len(comps),
                "lobes": sorted(lobes, key=lambda x: (x["population"], x["unit_count"], x["units"])),
            })

        # Paquetes frontera conexos de tamaño 1 y 2 que podrían salir juntos sin desconectar el donante.
        # Sirve de puente directo hacia un eventual operador 1→N / N→1.
        boundary = sorted(u for u in us if any(unit_dist[v] != d for v in uadj[u]))
        bundles = []
        candidate_sets = [{u} for u in boundary]
        for i, u in enumerate(boundary):
            for v in boundary[i + 1:]:
                if v in internal_adj.get(u, set()):
                    candidate_sets.append({u, v})

        for bundle in candidate_sets:
            remainder = us - bundle
            if not remainder:
                continue
            if len(components(remainder, internal_adj)) != 1:
                continue
            bp = sum(unit_pop[u] for u in bundle)
            ext = sorted({
                unit_dist[v]
                for u in bundle
                for v in uadj[u]
                if unit_dist[v] != d and d_prov.get(unit_dist[v]) == d_prov[d]
            })
            if not ext:
                continue
            donor_after = d_pop[d] - bp
            bundles.append({
                "units": sorted(bundle),
                "unit_count": len(bundle),
                "population": bp,
                "municipalities": sorted({m for u in bundle for m in unit_muns[u]}),
                "external_neighbor_districts": ext,
                "donor_population_if_bundle_moves": donor_after,
                "donor_within_floor_cap": floor <= donor_after <= cap,
                "absolute_residual_deviation_if_removed": abs(donor_after - target),
            })

        diagnostics.append({
            "district": d,
            "province": d_prov[d],
            "population": d_pop[d],
            "relative_deviation": (d_pop[d] - target) / target,
            "unit_count": len(us),
            "boundary_unit_count": len(boundary),
            "articulation_unit_count": len(articulations),
            "articulations": articulations,
            "movable_boundary_bundles_size_le_2": sorted(
                bundles,
                key=lambda x: (
                    not x["donor_within_floor_cap"],
                    x["absolute_residual_deviation_if_removed"],
                    x["unit_count"],
                    x["units"],
                ),
            )[:100],
        })

    result = {
        "K": K,
        "target": target,
        "floor": floor,
        "cap": cap,
        "tolerance": tol,
        "outliers": diagnostics,
    }
    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({
        "outliers": [
            {
                "district": x["district"],
                "rel_dev": round(x["relative_deviation"], 4),
                "articulations": x["articulation_unit_count"],
                "movable_bundles_le_2": len(x["movable_boundary_bundles_size_le_2"]),
            }
            for x in diagnostics
        ]
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
