#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Huella determinista de compatibilidad de M05 para checkpoints productivos."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import yaml

ENGINE_FILES = (
    "modulos/05_optimizar_distritos.py",
    "ddd_core/m05_opt_engine_v740.py",
    "ddd_core/m05_swap_polish.py",
    "ddd_core/m05_population_repair.py",
)


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
    for rel in ENGINE_FILES:
        path = root_dir / rel
        if not path.is_file():
            raise FileNotFoundError(f"No existe componente M05 para huella: {rel}")
        files[rel] = _sha256_bytes(path.read_bytes())
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
