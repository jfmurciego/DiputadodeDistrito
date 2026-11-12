#!/usr/bin/env python3
"""Resuelve la configuración de ensemble de un territorio para el workflow «06 Escenarios y Ensembles».

PROYECTO: Diputado de Distrito
VERSIÓN: 1.1.0 · FECHA: 2026-11-09 · ESTADO: candidato
ANTERIOR: legacy/herramientas/leer_config_ensemble_v1.0.0_20261109.py
CAMBIOS 1.1.0 (T-128): admite la fase ensemble_25 (25 candidatas) además de ensemble_10; el Gestor la sigue rechazando hasta que haya una corrida válida.
QUÉ HACE: lee configuracion/ensemble/<territorio>.json y emite líneas clave=valor para GITHUB_OUTPUT.
  Aragón conserva su circuito propio (kind=aragon). Cualquier otro territorio es kind=territorial: su bloque
  «workflow» declara contrato, caché, distritos y CRS, y el paquete de fuentes sale del catálogo de preparación.
  Las fases admitidas son ensemble_10 y ensemble_25; el lote de 50 sigue bloqueado.
MOTIVO: T-26, el ensemble no debe depender de rutas ni de 67 distritos fijos fuera de la rama de Aragón.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

ARAGON_STAGES = {"aragon_10": 10, "aragon_50": 50}
TERRITORIAL_STAGES = {"ensemble_10": 10, "ensemble_25": 25}
REQUIRED_WORKFLOW_KEYS = ("contract", "cache_dir", "expected_districts", "working_crs", "edition")


def describe(territory_id: str, stage: str, root: Path = Path("."), resolve_sources: bool = True) -> dict[str, str]:
    config_path = root / "configuracion" / "ensemble" / f"{territory_id}.json"
    if not config_path.is_file():
        raise SystemExit(f"Sin configuración de ensemble para {territory_id}: {config_path}")
    config = json.loads(config_path.read_text(encoding="utf-8"))
    if config.get("territory_id") != territory_id:
        raise SystemExit(f"{config_path}: territory_id no coincide")
    if territory_id == "aragon":
        if stage not in ARAGON_STAGES and stage != "synthetic":
            raise SystemExit(f"Fase no admitida para Aragón: {stage}")
        return {"kind": "aragon", "config": str(config_path)}
    if stage not in TERRITORIAL_STAGES and stage != "synthetic":
        raise SystemExit(f"Fase no admitida para {territory_id}: {stage} (solo ensemble_10 y ensemble_25; el lote de 50 sigue bloqueado)")
    block = config.get("workflow") or {}
    missing = [key for key in REQUIRED_WORKFLOW_KEYS if block.get(key) in (None, "")]
    if missing:
        raise SystemExit(f"{config_path}: falta workflow.{', workflow.'.join(missing)}")
    out = {
        "kind": "territorial",
        "config": str(config_path),
        "contract": str(block["contract"]),
        "cache_dir": str(block["cache_dir"]),
        "expected_districts": str(int(block["expected_districts"])),
        "working_crs": str(block["working_crs"]),
        "source_package_run_id": "",
        "source_package_artifact_name": "",
    }
    if resolve_sources:
        row = json.loads(subprocess.run(
            [sys.executable, "herramientas/catalogo_preparacion.py", "--root-dir", str(root), "resolve", "--mode", "generation",
             "--territory", territory_id, "--edition", str(block["edition"])],
            check=True, capture_output=True, text=True).stdout)
        evidence = row.get("preparation_evidence") or {}
        if not evidence.get("run_id") or not evidence.get("artifact_name"):
            raise SystemExit(f"{territory_id}: el catálogo no acredita paquete de fuentes (preparation_evidence)")
        out["source_package_run_id"] = str(evidence["run_id"])
        out["source_package_artifact_name"] = str(evidence["artifact_name"])
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--territory", required=True)
    ap.add_argument("--stage", required=True)
    ap.add_argument("--root-dir", type=Path, default=Path("."))
    args = ap.parse_args()
    for key, value in describe(args.territory, args.stage, args.root_dir).items():
        print(f"{key}={value}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
