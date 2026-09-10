#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""DDD unified params loader (v1.1)

Single-source-of-truth:
- One YAML file for all steps (ddd_params.yaml).
- Resolves relative paths against io.project_root.path (recommended) otherwise YAML directory.
- Applies placeholders: {run_name}, {year}, {scope}.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

EXT_HINTS = (".zip", ".geojson", ".json", ".csv", ".jsonl", ".shp", ".gpkg", ".parquet", ".yaml", ".yml")

def load_params_yaml(params_path: str) -> Dict[str, Any]:
    try:
        import yaml  # type: ignore
    except ImportError as e:
        raise SystemExit("Falta dependencia: PyYAML. Instala con: pip install pyyaml") from e

    p = Path(params_path).expanduser().resolve()
    if not p.exists():
        raise FileNotFoundError(f"Params YAML no encontrado: {p}")

    data = yaml.safe_load(p.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("El YAML debe tener un objeto raíz (mapping).")

    io_cfg = data.get("io", {}) or {}
    root = p.parent.resolve()
    pr = (io_cfg.get("project_root", {}) or {}).get("path", "")
    if pr:
        pr_path = Path(pr).expanduser()
        root = pr_path.resolve() if pr_path.is_absolute() else (p.parent / pr_path).resolve()

    meta = data.get("meta", {}) or {}
    run_name = meta.get("run_name", p.stem)
    year = int(meta.get("year", 2025))
    scope = meta.get("scope", "national") or "national"
    fmt = {"run_name": run_name, "year": year, "scope": scope}

    def _res(x: str) -> str:
        if not x:
            return x
        xp = Path(str(x))
        if xp.is_absolute():
            return str(xp)
        return str((root / xp).resolve())

    def _fmt(s: str) -> str:
        if not s:
            return s
        try:
            return s.format(**fmt)
        except Exception:
            return s

    def _looks_like_path(s: str) -> bool:
        return ("/" in s) or s.endswith(EXT_HINTS)

    def _walk(obj):
        if isinstance(obj, dict):
            return {k: _walk(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [_walk(v) for v in obj]
        if isinstance(obj, str):
            s = _fmt(obj)
            return _fmt(_res(s)) if _looks_like_path(s) else s
        return obj

    resolved = _walk(data)
    resolved.setdefault("meta", {})
    resolved["meta"].setdefault("run_name", run_name)
    resolved["meta"].setdefault("year", year)
    resolved["meta"].setdefault("scope", scope)
    resolved.setdefault("io", {})
    resolved["io"].setdefault("project_root", {})
    resolved["io"]["project_root"].setdefault("path", str(root))
    resolved["_internal"] = {"params_path": str(p), "root": str(root), "fmt": fmt}
    return resolved


def step_cfg(cfg: Dict[str, Any], step_key: str) -> Dict[str, Any]:
    steps = cfg.get("steps", {}) or {}
    step = steps.get(step_key, {}) or {}
    if not isinstance(step, dict):
        raise ValueError(f"steps.{step_key} debe ser un mapping.")
    return step


def require(value: Any, msg: str):
    if value is None:
        raise SystemExit(msg)
    if isinstance(value, str) and not value.strip():
        raise SystemExit(msg)
    if isinstance(value, list) and len(value) == 0:
        raise SystemExit(msg)
    return value
