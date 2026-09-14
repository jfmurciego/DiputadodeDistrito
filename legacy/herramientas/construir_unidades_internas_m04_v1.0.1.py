#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PROYECTO: Diputado de Distrito
HERRAMIENTA: construir_unidades_internas_m04.py
VERSIÓN: 1.0.1
NOMBRE: Macro-unidades internas conexas con entrada M01 ZIP
FECHA: 2026-09-11
FUNCIÓN: construir una identidad de partición distinta del municipio administrativo real. Los municipios
pequeños permanecen atómicos; los sobredimensionados se dividen determinísticamente en macro-unidades
internas conexas de tamaño controlado respecto del target distrital.
ENTRADAS: GeoJSON o GeoJSON.zip M01, grafo M03, K, campos de sección/municipio/población y ratios de atomicidad/chunk.
SALIDAS: GeoJSON con `partition_unit_field` y JSON de auditoría.
REGLAS: no modifica CUMUN; no cambia población ni geometría; cada macro-unidad es conexa en M03; la
partición solo se abre para municipios por encima de `atomicity_ratio × target`.
CAMBIOS: añade lectura explícita del GeoJSON comprimido producido por M01; la lógica de partición 1.0.0 no cambia.
MOTIVO: el contrato real M01→M04 usa `.geojson.zip`; la herramienta debe consumir directamente esa salida sin pasos manuales.
ANTERIOR: legacy/herramientas/construir_unidades_internas_m04_v1.0.0.py
"""
from __future__ import annotations

import argparse
import importlib.util
import io
import json
import math
import sys
import zipfile
from pathlib import Path

import geopandas as gpd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

ENGINE = ROOT / "ddd_core" / "m04_seed_engine_v745.py"


def load_engine():
    spec = importlib.util.spec_from_file_location("ddd_m04_seed_engine_v745_for_units", ENGINE)
    if spec is None or spec.loader is None:
        raise SystemExit(f"No se puede cargar {ENGINE}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


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


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--geojson", required=True)
    ap.add_argument("--graph", required=True)
    ap.add_argument("--out-geojson", required=True)
    ap.add_argument("--out-report", required=True)
    ap.add_argument("--k", required=True, type=int)
    ap.add_argument("--id-field", default="CUSEC_KEY")
    ap.add_argument("--municipality-field", default="CUMUN")
    ap.add_argument("--population-field", default="POP_2025")
    ap.add_argument("--partition-unit-field", default="M04_PARTITION_UNIT")
    ap.add_argument("--atomicity-ratio", type=float, default=1.10)
    ap.add_argument("--chunk-ratio", type=float, required=True)
    a = ap.parse_args()

    if a.k <= 0 or a.atomicity_ratio <= 0 or not (0 < a.chunk_ratio <= 1.0):
        raise SystemExit("Parámetros inválidos")

    eng = load_engine()
    g = load_geo(a.geojson)
    g[a.id_field] = g[a.id_field].astype(str)
    g[a.municipality_field] = g[a.municipality_field].astype(str)
    g[a.population_field] = g[a.population_field].astype(int)

    graph = json.loads(Path(a.graph).read_text(encoding="utf-8"))
    pop = {str(n["id"]): int(n.get("pop", 0)) for n in graph["nodes"]}
    adj = {n: set() for n in pop}
    for e in graph["edges"]:
        u, v = str(e["u"]), str(e["v"])
        if u in adj and v in adj:
            adj[u].add(v)
            adj[v].add(u)

    total = int(g[a.population_field].sum())
    target = total / a.k
    atomic_limit = target * a.atomicity_ratio
    desired_chunk = target * a.chunk_ratio

    g[a.partition_unit_field] = g[a.municipality_field].astype(str)
    report_municipalities = []

    for mun, x in sorted(g.groupby(a.municipality_field), key=lambda kv: str(kv[0])):
        mun = str(mun)
        nodes = set(x[a.id_field].astype(str))
        mp = sum(pop[n] for n in nodes)
        if mp <= atomic_limit or len(nodes) <= 1:
            continue
        if not eng.connected(nodes, adj):
            raise SystemExit(f"Municipio {mun} no conexo antes de particionar")

        q = max(2, int(math.ceil(mp / desired_chunk)))
        q = min(q, len(nodes))
        avg = mp / q

        parts = eng.hybrid_partition(nodes, q, adj, pop, label=f"unidad interna {mun}")
        parts, pvals, pobj = eng.rebalance(
            parts,
            adj,
            pop,
            avg,
            avg * 0.55,
            avg * 1.45,
            avg * 0.30,
            30000,
        )

        ordered = sorted(
            zip(parts, pvals),
            key=lambda z: (min(str(n) for n in z[0]), z[1]),
        )
        chunks = []
        for seq, (part, pval) in enumerate(ordered, start=1):
            if not eng.connected(part, adj):
                raise SystemExit(f"Macro-unidad desconectada {mun} P{seq}")
            uid = f"{mun}#P{seq:02d}"
            g.loc[g[a.id_field].isin(part), a.partition_unit_field] = uid
            exterior_sections = sorted(
                n for n in part
                if any(nb not in nodes for nb in adj.get(n, set()))
            )
            chunks.append({
                "partition_unit": uid,
                "sections": sorted(part),
                "section_count": len(part),
                "population": int(pval),
                "ratio_to_target": float(pval / target),
                "touches_municipal_exterior": bool(exterior_sections),
                "exterior_gateway_sections": exterior_sections,
            })

        report_municipalities.append({
            "municipality": mun,
            "population": int(mp),
            "ratio_to_target": float(mp / target),
            "chunk_count": len(chunks),
            "chunk_average_population": float(mp / len(chunks)),
            "chunk_average_ratio_to_target": float((mp / len(chunks)) / target),
            "rebalance_objective": list(pobj),
            "chunks": chunks,
        })

    if g[a.partition_unit_field].isna().any():
        raise SystemExit("Hay secciones sin unidad de partición")
    for uid, x in g.groupby(a.partition_unit_field):
        nodes = set(x[a.id_field].astype(str))
        if not eng.connected(nodes, adj):
            raise SystemExit(f"Unidad de partición final desconectada: {uid}")
        if x[a.municipality_field].nunique() != 1:
            raise SystemExit(f"Unidad de partición cruza municipios: {uid}")

    out_geo = Path(a.out_geojson)
    out_geo.parent.mkdir(parents=True, exist_ok=True)
    g.to_file(out_geo, driver="GeoJSON")

    split_muns = {
        str(m): int(x[a.partition_unit_field].nunique())
        for m, x in g.groupby(a.municipality_field)
        if x[a.partition_unit_field].nunique() > 1
    }
    result = {
        "version": "1.0.1",
        "K": a.k,
        "total_population": total,
        "target": target,
        "atomicity_ratio": a.atomicity_ratio,
        "atomicity_limit": atomic_limit,
        "chunk_ratio": a.chunk_ratio,
        "desired_chunk_population": desired_chunk,
        "partition_unit_field": a.partition_unit_field,
        "partition_unit_count": int(g[a.partition_unit_field].nunique()),
        "oversized_municipality_count": len(report_municipalities),
        "split_municipalities": split_muns,
        "municipalities": report_municipalities,
    }
    out_rep = Path(a.out_report)
    out_rep.parent.mkdir(parents=True, exist_ok=True)
    out_rep.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({
        "target": round(target, 3),
        "chunk_ratio": a.chunk_ratio,
        "partition_units": result["partition_unit_count"],
        "oversized_municipalities": result["oversized_municipality_count"],
        "split_municipalities": split_muns,
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
