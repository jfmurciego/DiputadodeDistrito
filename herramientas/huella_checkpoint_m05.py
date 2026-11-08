#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Huella determinista de compatibilidad de M05 para checkpoints productivos.

PROYECTO: Diputado de Distrito
VERSIÓN: 1.1.0
NOMBRE DE VERSIÓN: Huella M05 calculada desde el motor activo
FECHA: 2026-11-08
ESTADO: candidato
CAMBIOS: ENGINE_FILES deja de ser una lista a mano: se calcula como el cierre de imports `ddd_core` desde
  modulos/05_optimizar_distritos.py, incluido el motor base que carga por ruta (BASE_ENGINE = ROOT/"ddd_core"/"x.py").
MOTIVO: T-108. La lista fija tenía m05_opt_engine_v740.py (inactivo) y no el v741 (activo), ni m05_private_annealing,
  m05_atomic_output, population_floor_exemptions ni config: cambiar el motor real no invalidaba «Reutilizar».
ANTERIOR: legacy/herramientas/huella_checkpoint_m05_v1.0.0_20261108.py
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
import re
from pathlib import Path

import yaml

ENTRY = "modulos/05_optimizar_distritos.py"
PAQUETE = "ddd_core"
_RUTA_LITERAL = re.compile(r"""["']ddd_core["']\s*\)?\s*/\s*["'](\w+\.py)["']|["']ddd_core/(\w+\.py)["']""")
REPO_ROOT = Path(__file__).resolve().parents[1]


def _deps(path: Path, root_dir: Path) -> set[str]:
    """Ficheros de ddd_core que `path` importa o carga por ruta literal."""
    text = path.read_text(encoding="utf-8")
    found: set[str] = set()
    try:
        tree = ast.parse(text)
    except SyntaxError:  # fichero no Python (p. ej. sintético en tests): se hashea, sin dependencias
        tree = ast.Module(body=[], type_ignores=[])
    for node in ast.walk(tree):
        names = []
        if isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            names = [node.module] + [f"{node.module}.{a.name}" for a in node.names]
        elif isinstance(node, ast.Import):
            names = [a.name for a in node.names]
        for name in names:
            parts = name.split(".")
            if parts[0] == PAQUETE and len(parts) >= 2:
                rel = f"{PAQUETE}/{parts[1]}.py"
                if (root_dir / rel).is_file():
                    found.add(rel)
    for m in _RUTA_LITERAL.finditer(text):
        rel = f"{PAQUETE}/{m.group(1) or m.group(2)}"
        if (root_dir / rel).is_file():
            found.add(rel)
    return found


def engine_files(root_dir: Path = REPO_ROOT, entry: str = ENTRY) -> tuple[str, ...]:
    """Cierre transitivo de ficheros del motor M05 activo, empezando por el punto de entrada de la 00."""
    root_dir = Path(root_dir).resolve()
    if not (root_dir / entry).is_file():
        raise FileNotFoundError(f"No existe componente M05 para huella: {entry}")
    seen = {entry}
    pending = [entry]
    while pending:
        for dep in _deps(root_dir / pending.pop(), root_dir):
            if dep not in seen:
                seen.add(dep)
                pending.append(dep)
    return (entry, *sorted(seen - {entry}))


ENGINE_FILES = engine_files()


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _canonical_json(data) -> bytes:
    return json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def build_fingerprint(*, params: Path, root_dir: Path = Path(".")) -> dict:
    root_dir = root_dir.resolve()
    params_path = params if params.is_absolute() else root_dir / params
    cfg = yaml.safe_load(params_path.read_text(encoding="utf-8")) or {}
    m05 = (cfg.get("modulos") or {}).get("modulo_05_optimizar_distritos") or cfg.get("step5_optimize_swaps") or {}
    files = {}
    for rel in engine_files(root_dir):
        files[rel] = _sha256_bytes((root_dir / rel).read_bytes())
    payload = {
        "schema": "ddd.m05-checkpoint-compatibility/1.0",
        "engine_files": files,
        "m05_config_sha256": _sha256_bytes(_canonical_json(m05)),
    }
    payload["fingerprint"] = _sha256_bytes(_canonical_json(payload))
    return payload


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--params", required=True, type=Path)
    ap.add_argument("--root-dir", default=".", type=Path)
    ap.add_argument("--output", type=Path)
    args = ap.parse_args()
    payload = build_fingerprint(params=args.params, root_dir=args.root_dir)
    text = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
