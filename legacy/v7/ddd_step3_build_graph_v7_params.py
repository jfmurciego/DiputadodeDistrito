#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""DDD Step 3 — Build adjacency graph (v7.1)

New in v7.1:
  - Comarca column AUTO-DETECTION: if the configured column names don't
    exist in the GeoJSON, Step 3 scans all column names for likely comarca
    ID and name columns (case-insensitive substring match on common patterns)
    and uses the first matches it finds.
  - Prints ALL GeoJSON column names when comarca columns are not found, so
    you can immediately see what to put in the YAML.
  - Prints a clear warning when edges=0 (adjacency not computed yet or
    buffer_m too small).

Auto-detection patterns:
  comarca ID:   substring matches for  cod, code, codigo, id, comarca (in that order)
  comarca name: substring matches for  nom, name, nombre, comarca

If auto-detection finds columns, Step 3 prints which ones it used — copy
those names into comarca_id_field / comarca_name_field in ddd_params.yaml
for all downstream steps (step3, step6).

Run:
  python scripts/ddd_step3_build_graph_v7_params.py --params params/ddd_params.yaml
"""
from __future__ import annotations
import sys, argparse, io, json, zipfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import geopandas as gpd
import pandas as pd

from ddd_core.config import load_params_yaml, step_cfg, require


# ── I/O ──────────────────────────────────────────────────────────────────────
def _gpd_read(path_or_buf, layer=None):
    try:
        import pyogrio; return pyogrio.read_dataframe(path_or_buf, layer=layer)
    except Exception: pass
    try:
        return gpd.read_file(path_or_buf, layer=layer, engine="pyogrio")
    except Exception:
        return gpd.read_file(path_or_buf, layer=layer)


def load_geojson(p: str) -> gpd.GeoDataFrame:
    pp = Path(p).expanduser().resolve()
    if not pp.exists(): raise FileNotFoundError(f"GeoJSON no encontrado: {pp}")
    if pp.suffix.lower() == ".zip" and pp.name.lower().endswith(".geojson.zip"):
        with zipfile.ZipFile(pp) as z:
            nm = [n for n in z.namelist()
                  if n.lower().endswith((".geojson", ".json")) and not n.endswith("/")]
            return _gpd_read(io.BytesIO(z.read(nm[0])))
    return _gpd_read(str(pp))


def load_edges_jsonl(p: str) -> List[Tuple[str, str]]:
    pp = Path(p).expanduser().resolve()
    if not pp.exists(): raise FileNotFoundError(f"Edges JSONL no encontrado: {pp}")
    out = []
    with pp.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line: continue
            o = json.loads(line)
            u, v = str(o.get("u", "")), str(o.get("v", ""))
            if u and v and u != v:
                out.append((u, v))
    return out


def write_json(obj: Any, p: str):
    pp = Path(p).expanduser().resolve()
    pp.parent.mkdir(parents=True, exist_ok=True)
    pp.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")


# ── Comarca column detection ──────────────────────────────────────────────────
_ID_PATTERNS  = ["cod", "codigo", "code", "id"]   # lowercase substrings → comarca ID
_NM_PATTERNS  = ["nom", "nombre", "name"]          # lowercase substrings → comarca name
_COMARCA_WORD = "comarca"


def _detect_comarca_cols(
    all_cols: List[str],
    configured_id: str,
    configured_name: str,
) -> Tuple[Optional[str], Optional[str]]:
    """
    Returns (id_col, name_col) — either from config (if found) or auto-detected.
    Returns (None, None) if nothing found.
    """
    # First try configured names
    found_id   = configured_id   if configured_id   in all_cols else None
    found_name = configured_name if configured_name in all_cols else None

    if found_id and found_name:
        return found_id, found_name

    # Auto-detect from columns that contain "comarca" in their name
    comarca_cols = [c for c in all_cols if _COMARCA_WORD in c.lower()]
    if not comarca_cols:
        return None, None

    # Among comarca_cols, pick the best ID col and name col
    def _score_id(c: str) -> int:
        cl = c.lower()
        for i, pat in enumerate(_ID_PATTERNS):
            if pat in cl: return len(_ID_PATTERNS) - i
        return 0

    def _score_name(c: str) -> int:
        cl = c.lower()
        for i, pat in enumerate(_NM_PATTERNS):
            if pat in cl: return len(_NM_PATTERNS) - i
        return 0

    id_candidates   = sorted(comarca_cols, key=_score_id,   reverse=True)
    name_candidates = sorted(comarca_cols, key=_score_name, reverse=True)

    auto_id   = id_candidates[0]   if not found_id   else found_id
    auto_name = name_candidates[0] if not found_name else found_name

    # Avoid using the same column for both
    if auto_id == auto_name and len(comarca_cols) > 1:
        auto_name = name_candidates[1] if len(name_candidates) > 1 else None

    return auto_id, (auto_name if auto_id != auto_name else None)


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--params", required=True)
    args = ap.parse_args()

    cfg = load_params_yaml(args.params)
    s3  = step_cfg(cfg, "step3_build_graph")

    in_geo    = require(s3.get("in_geojson", ""),     "Falta steps.step3_build_graph.in_geojson")
    in_edges  = require(s3.get("in_edges_jsonl", ""), "Falta steps.step3_build_graph.in_edges_jsonl")
    id_field  = require(s3.get("id_field", ""),       "Falta steps.step3_build_graph.id_field")
    pop_field = require(s3.get("pop_field", ""),      "Falta steps.step3_build_graph.pop_field")
    out_graph = require(s3.get("out_graph_json", ""), "Falta steps.step3_build_graph.out_graph_json")
    out_report = s3.get("out_report", "") or ""

    cfg_cid = s3.get("comarca_id_field",   "comarca_id")   or "comarca_id"
    cfg_cnm = s3.get("comarca_name_field", "comarca_name") or "comarca_name"

    gdf = load_geojson(in_geo)
    all_cols = list(gdf.columns)

    for col in (id_field, pop_field):
        if col not in gdf.columns:
            raise SystemExit(f"GeoJSON sin '{col}'.\nColumnas disponibles: {all_cols}")

    # ── Comarca column resolution ──────────────────────────────────────────
    cid_col, cnm_col = _detect_comarca_cols(all_cols, cfg_cid, cfg_cnm)

    if cid_col is None:
        print(f"\n[Step3] AVISO: No se encontraron columnas de comarca.")
        print(f"  Columnas configuradas: comarca_id_field='{cfg_cid}'  comarca_name_field='{cfg_cnm}'")
        print(f"  Columnas disponibles en el GeoJSON de Step1:")
        for c in all_cols:
            print(f"    {c}")
        print(f"\n  → Comprueba que comarcas.enabled=true en el YAML y que el CSV de comarcas")
        print(f"    se ha unido correctamente en Step1.")
        print(f"  → Luego actualiza comarca_id_field y comarca_name_field en ddd_params.yaml")
        print(f"    (steps.step3_build_graph y steps.step6_export_final) con los nombres reales.\n")
        print(f"[Step3] Continuando SIN comarca — Steps 4/5 no usarán restricción comarca.")
    else:
        auto_used = (cid_col != cfg_cid or cnm_col != cfg_cnm)
        if auto_used:
            print(f"[Step3] AVISO: Comarca auto-detectada.")
            print(f"  → comarca_id_field  detectado: '{cid_col}'  (configurado: '{cfg_cid}')")
            print(f"  → comarca_name_field detectado: '{cnm_col}' (configurado: '{cfg_cnm}')")
            print(f"  → Actualiza ddd_params.yaml para evitar este aviso:")
            print(f"       comarca_id_field:   {cid_col}")
            print(f"       comarca_name_field: {cnm_col}")
        else:
            print(f"[Step3] Comarca: id='{cid_col}'  nombre='{cnm_col}'")

    # ── Build nodes ────────────────────────────────────────────────────────
    read_cols = [id_field, pop_field]
    if cid_col: read_cols.append(cid_col)
    if cnm_col: read_cols.append(cnm_col)

    df = gdf[read_cols].copy()
    df[id_field]  = df[id_field].astype(str)
    df[pop_field] = pd.to_numeric(df[pop_field], errors="coerce").fillna(0).astype("int64")

    def _s(v: Any) -> str:
        return "" if (v is None or (isinstance(v, float) and pd.isna(v))) else str(v).strip()

    nodes: List[Dict[str, Any]] = []
    for _, row in df.iterrows():
        n: Dict[str, Any] = {"id": str(row[id_field]), "pop": int(row[pop_field])}
        if cid_col: n["comarca_id"]   = _s(row[cid_col])
        if cnm_col: n["comarca_name"] = _s(row[cnm_col])
        nodes.append(n)

    pop_map = {n["id"]: n["pop"] for n in nodes}

    # ── Load edges ─────────────────────────────────────────────────────────
    raw_edges = load_edges_jsonl(in_edges)
    edges_f   = [{"u": u, "v": v} for u, v in raw_edges if u in pop_map and v in pop_map]

    deg: Dict[str, int] = {}
    for e in edges_f:
        deg[e["u"]] = deg.get(e["u"], 0) + 1
        deg[e["v"]] = deg.get(e["v"], 0) + 1
    isolated  = sum(1 for n in pop_map if deg.get(n, 0) == 0)
    total_pop = int(sum(pop_map.values()))

    if len(edges_f) == 0:
        print(f"\n[Step3] AVISO CRÍTICO: edges=0 — ningún par de secciones está conectado.")
        print(f"  Causas más comunes:")
        print(f"  1. Step2 no se ha ejecutado o falló — el fichero JSONL existe pero está vacío.")
        print(f"  2. buffer_m demasiado pequeño: la geometría tiene huecos entre secciones.")
        print(f"     → Prueba step2_export_edges.buffer_m: 5.0  (en lugar de 0.5)")
        print(f"  3. El CRS del seccionado no se pudo convertir a ETRS89 UTM30N — ")
        print(f"     buffer en metros no funciona si la geometría está en grados (WGS84).")
        print(f"     → El script step2 proyecta a EPSG:25830 automáticamente; verifica que")
        print(f"       el GeoJSON de Step1 tiene CRS definido (no None).\n")

    comarca_ids = {n.get("comarca_id", "") for n in nodes} - {""}

    write_json({"nodes": nodes, "edges": edges_f}, out_graph)
    if out_report:
        write_json({
            "step": "step3_build_graph", "version": "7.1",
            "nodes": len(nodes), "edges": len(edges_f), "isolated": isolated,
            "total_pop": total_pop, "n_comarcas": len(comarca_ids),
            "comarca_id_used": cid_col or "", "comarca_name_used": cnm_col or "",
            "geojson_columns": all_cols,
        }, out_report)

    comarca_msg = (f"comarcas={len(comarca_ids)} id_col='{cid_col}' nm_col='{cnm_col}'"
                   if cid_col else "sin comarca")
    print(f"[Step3] OK nodes={len(nodes)} edges={len(edges_f)} isolated={isolated} "
          f"{comarca_msg} out={out_graph}")


if __name__ == "__main__":
    main()
