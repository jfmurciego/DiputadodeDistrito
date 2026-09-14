#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PROYECTO: Diputado de Distrito
Módulo 05 — Optimizar distritos
VERSIÓN: 7.5.2
NOMBRE DE VERSIÓN: Pulido determinista — semántica de informe separada
FECHA: 2026-09-11
ESTADO: candidato multi-territorio; swap-polish opt-in, EXT-06 validado parcialmente.
FUNCIÓN: ejecutar el motor validado M05 v7.4.0, conservar la normalización robusta de `ddd_unit_id` de
v7.4.2 y, opcionalmente, aplicar una fase final determinista de swaps 1×1 que mejora estrictamente la misma
función objetivo canónica sin romper provincia, suelo/techo, `ddd_closed_urban` ni contigüidad.
ENTRADAS: grafo M03 y solución M04 con district_id, ddd_unit_id y ddd_closed_urban.
SALIDAS: GeoJSON optimizado e informe M05 con `version` del motor, `wrapper_version` y `swap_polish` cuando
está activado.
REGLAS DURAS: el motor base no cambia. El nuevo operador solo se activa con `swap_polish_max > 0`; por
defecto vale 0 para mantener idénticos los baselines ya validados. Cada swap debe mejorar lexicográficamente
la función objetivo canónica y preservar todas las restricciones duras.
CAMBIOS: preserva `report["version"]` como versión del motor optimizador v7.4.0 y añade
`report["wrapper_version"] = "7.5.2"`. No cambia algoritmo, objetivo, movimientos ni restricciones.
MOTIVO: R015 Run 34642133611 confirmó que toda la regresión territorial y el determinismo pasan, pero
bloqueó correctamente que el wrapper sobrescribiera la identidad del motor validado usada por R016.
ANTERIOR: legacy/modulo05/05_optimizar_distritos_v7.5.1.py
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
from ddd_core.m05_swap_polish import polish as swap_polish

BASE_ENGINE = ROOT / "ddd_core" / "m05_opt_engine_v740.py"
WRAPPER_VERSION = "7.5.2"


def _load_base():
    spec = importlib.util.spec_from_file_location("ddd_m05_opt_engine_v740", BASE_ENGINE)
    if spec is None or spec.loader is None:
        raise SystemExit(f"M05 v{WRAPPER_VERSION}: no se puede cargar {BASE_ENGINE}")
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
            raise SystemExit(f"M05 v{WRAPPER_VERSION}: ddd_unit_id multivaluado no normalizable: {v!r}")
        v = v[0]
    if v is None:
        raise SystemExit(f"M05 v{WRAPPER_VERSION}: ddd_unit_id nulo en GeoJSON crudo")
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


def _merge_report_metadata(report_path: Path | None, *, swap_meta: dict, normalization: dict | None = None):
    if not report_path or not report_path.exists():
        return
    rep = json.loads(report_path.read_text(encoding="utf-8"))
    # `version` pertenece al motor que produjo el informe (actualmente 7.4.0).
    # El wrapper se identifica por un campo distinto para conservar la semántica estable de R016.
    rep["wrapper_version"] = WRAPPER_VERSION
    rep["swap_polish"] = swap_meta
    if normalization is not None:
        rep["unit_id_normalization"] = normalization
    report_path.write_text(json.dumps(rep, ensure_ascii=False, indent=2), encoding="utf-8")


def _apply_swap_polish(cfg: dict, s5: dict, out_path: Path, report_path: Path | None):
    max_swaps = int(s5.get("swap_polish_max", 0) or 0)
    if max_swaps < 0:
        raise SystemExit(f"M05 v{WRAPPER_VERSION}: swap_polish_max no puede ser negativo")
    if max_swaps == 0:
        meta = {"enabled": False, "max_swaps": 0, "accepted_swaps": 0}
    else:
        graph_path = Path(str(s5.get("in_graph_json", "")))
        if not str(graph_path):
            raise SystemExit(f"M05 v{WRAPPER_VERSION}: falta in_graph_json para swap-polish")
        meta = swap_polish(
            cfg=cfg,
            graph_path=graph_path,
            geojson_path=out_path,
            out_geojson_path=out_path,
            max_swaps=max_swaps,
        )
        meta["enabled"] = True
        meta["max_swaps"] = max_swaps
    _merge_report_metadata(report_path, swap_meta=meta)
    return meta


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--params", required=True)
    args = ap.parse_args()
    params = Path(args.params).resolve()
    cfg = load_params_yaml(str(params))
    s5 = _module_cfg(cfg)
    in_path = Path(str(s5.get("in_geojson", "")))
    if not str(in_path):
        raise SystemExit(f"M05 v{WRAPPER_VERSION}: falta in_geojson")

    if _ogr_can_read_unit(in_path):
        _run_base(str(params))
        out_path = Path(str(s5.get("out_geojson", "")))
        report_path = Path(str(s5.get("out_report", ""))) if s5.get("out_report") else None
        meta = _apply_swap_polish(cfg, s5, out_path, report_path)
        print(f"[Módulo 5 wrapper] OK v{WRAPPER_VERSION} swap_polish={meta.get('accepted_swaps', 0)} out={out_path}")
        return

    data, inner = _raw_geojson(in_path)
    labels = [_normalise_label((f.get("properties") or {}).get("ddd_unit_id")) for f in data.get("features", [])]
    unique = sorted(set(labels))
    label_to_code = {label: i + 1 for i, label in enumerate(unique)}
    code_to_label = {str(code): label for label, code in label_to_code.items()}
    for f, label in zip(data.get("features", []), labels):
        f.setdefault("properties", {})["ddd_unit_id"] = int(label_to_code[label])

    with tempfile.TemporaryDirectory(prefix="ddd_m05_752_") as td_raw:
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
        meta = _apply_swap_polish(cfg2, s52, tmp_output, tmp_report)

        final_out = Path(str(s5.get("out_geojson")))
        final_report = Path(str(s5.get("out_report", ""))) if s5.get("out_report") else None
        final_out.parent.mkdir(parents=True, exist_ok=True)
        final_out.write_bytes(tmp_output.read_bytes())

        normalization = {
            "applied": True,
            "reason": "OGR dropped ddd_unit_id; raw GeoJSON labels mapped to stable integer codes",
            "units": len(unique),
            "code_to_original_label": code_to_label,
        }
        if final_report:
            final_report.parent.mkdir(parents=True, exist_ok=True)
            final_report.write_bytes(tmp_report.read_bytes())
            _merge_report_metadata(final_report, swap_meta=meta, normalization=normalization)
        print(
            f"[Módulo 5 wrapper] OK v{WRAPPER_VERSION} normalized_units={len(unique)} "
            f"swap_polish={meta.get('accepted_swaps', 0)} out={final_out}"
        )


if __name__ == "__main__":
    main()
