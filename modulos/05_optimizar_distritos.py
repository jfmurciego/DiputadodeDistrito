#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PROYECTO: Diputado de Distrito
Módulo 05 — Optimizar distritos
VERSIÓN: 7.4.2
NOMBRE DE VERSIÓN: Identidad robusta con resolución canónica de rutas
FECHA: 2026-09-11
FUNCIÓN: ejecutar sin cambios el motor M05 v7.4.0 y, únicamente si GeoPandas/OGR pierde `ddd_unit_id`, normalizar esa identidad a códigos enteros estables antes de entrar al motor.
ENTRADAS: grafo M03 y solución M04 con district_id, ddd_unit_id y ddd_closed_urban.
SALIDAS: las mismas de M05 v7.4.0; el informe registra si hubo normalización y el mapa código→etiqueta original.
REGLAS DURAS: no modifica la función objetivo, movimientos, recocido, contigüidad, provincia ni guardarraíles poblacionales del motor v7.4.0.
ESTADO: candidato multi-territorio.
CAMBIOS: usa `ddd_core.config.load_params_yaml` también en el wrapper, por lo que `{run_name}`, `{year}` y rutas relativas quedan resueltos exactamente igual que en el resto de módulos. Conserva el fallback de v7.4.1.
MOTIVO: EXT-03 v7.4.1 alcanzó correctamente el fallback pero intentó abrir literalmente una ruta con `{run_name}` porque el wrapper leía el YAML crudo.
ANTERIOR: legacy/modulo05/05_optimizar_distritos_v7.4.1.py
"""
from __future__ import annotations

import argparse
import copy
import importlib.util
import io
import json
import sys
import tempfile
import zipfile
from pathlib import Path

import geopandas as gpd
import yaml

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ddd_core.config import load_params_yaml

BASE_ENGINE = ROOT / "ddd_core" / "m05_opt_engine_v740.py"


def _load_base():
    spec = importlib.util.spec_from_file_location("ddd_m05_opt_engine_v740", BASE_ENGINE)
    if spec is None or spec.loader is None:
        raise SystemExit(f"M05 v7.4.2: no se puede cargar {BASE_ENGINE}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _run_base(params_path: str):
    mod = _load_base()
    old = list(sys.argv)
    try:
        sys.argv = [str(BASE_ENGINE), "--params", params_path]
        mod.main()
    finally:
        sys.argv = old


def _module_cfg(cfg: dict) -> dict:
    mods = cfg.get("modulos", {}) or {}
    return mods.get("modulo_05_optimizar_distritos") or cfg.get("step5_optimize_swaps") or {}


def _raw_geojson(path: Path):
    if path.suffix.lower() == ".zip":
        with zipfile.ZipFile(path) as z:
            name = next(n for n in z.namelist() if n.lower().endswith((".geojson", ".json")) and not n.endswith("/"))
            return json.loads(z.read(name).decode("utf-8")), name
    return json.loads(path.read_text(encoding="utf-8")), path.name


def _normalise_label(v):
    if isinstance(v, list):
        if len(v) != 1:
            raise SystemExit(f"M05 v7.4.2: ddd_unit_id multivaluado no normalizable: {v!r}")
        v = v[0]
    if v is None:
        raise SystemExit("M05 v7.4.2: ddd_unit_id nulo en GeoJSON crudo")
    return str(v)


def _ogr_can_read_unit(path: Path) -> bool:
    try:
        if path.suffix.lower() == ".zip":
            with zipfile.ZipFile(path) as z:
                name = next(n for n in z.namelist() if n.lower().endswith((".geojson", ".json")) and not n.endswith("/"))
                g = gpd.read_file(io.BytesIO(z.read(name)))
        else:
            g = gpd.read_file(path)
        return "ddd_unit_id" in g.columns
    except Exception:
        return False


def _write_zip_json(data: dict, path: Path, inner_name: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    raw = json.dumps(data, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as z:
        z.writestr(inner_name if inner_name.lower().endswith((".geojson", ".json")) else "data.geojson", raw)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--params", required=True)
    args = ap.parse_args()
    params = Path(args.params).resolve()
    cfg = load_params_yaml(str(params))
    s5 = _module_cfg(cfg)
    in_path = Path(str(s5.get("in_geojson", "")))
    if not str(in_path):
        raise SystemExit("M05 v7.4.2: falta in_geojson")

    # Camino normal: no tocamos nada y delegamos directamente al motor validado.
    if _ogr_can_read_unit(in_path):
        _run_base(str(params))
        return

    data, inner = _raw_geojson(in_path)
    labels = [_normalise_label((f.get("properties") or {}).get("ddd_unit_id")) for f in data.get("features", [])]
    unique = sorted(set(labels))
    label_to_code = {label: i + 1 for i, label in enumerate(unique)}
    code_to_label = {str(code): label for label, code in label_to_code.items()}
    for f, label in zip(data.get("features", []), labels):
        f.setdefault("properties", {})["ddd_unit_id"] = int(label_to_code[label])

    with tempfile.TemporaryDirectory(prefix="ddd_m05_742_") as td_raw:
        td = Path(td_raw)
        tmp_input = td / "m05_input.geojson.zip"
        tmp_output = td / "m05_output.geojson.zip"
        tmp_report = td / "m05_report.json"
        tmp_params = td / "params.yaml"
        _write_zip_json(data, tmp_input, "m05_input.geojson")

        cfg2 = copy.deepcopy(cfg)
        s52 = _module_cfg(cfg2)
        s52["in_geojson"] = str(tmp_input)
        s52["out_geojson"] = str(tmp_output)
        s52["out_report"] = str(tmp_report)
        cfg2.setdefault("modulos", {})["modulo_05_optimizar_distritos"] = s52
        tmp_params.write_text(yaml.safe_dump(cfg2, sort_keys=False, allow_unicode=True), encoding="utf-8")

        _run_base(str(tmp_params))

        final_out = Path(str(s5.get("out_geojson")))
        final_report = Path(str(s5.get("out_report", ""))) if s5.get("out_report") else None
        final_out.parent.mkdir(parents=True, exist_ok=True)
        final_out.write_bytes(tmp_output.read_bytes())

        rep = json.loads(tmp_report.read_text(encoding="utf-8")) if tmp_report.exists() else {}
        rep["version"] = "7.4.2"
        rep["unit_id_normalization"] = {
            "applied": True,
            "reason": "OGR dropped ddd_unit_id; raw GeoJSON labels mapped to stable integer codes",
            "units": len(unique),
            "code_to_original_label": code_to_label,
        }
        if final_report:
            final_report.parent.mkdir(parents=True, exist_ok=True)
            final_report.write_text(json.dumps(rep, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"[Módulo 5 wrapper] OK v7.4.2 normalized_units={len(unique)} out={final_out}")


if __name__ == "__main__":
    main()
