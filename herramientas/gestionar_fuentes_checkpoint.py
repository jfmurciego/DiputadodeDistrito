#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Orquestación durable de fuentes para producción y reanudación DDD.

La decisión se toma antes de invocar el descargador. REUSE restaura y valida
el paquete congelado; BLOCK nunca cae a adquisición; ACQUIRE llama exactamente
una vez al adaptador suministrado y congela el resultado para checkpoints
posteriores.
"""
from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path
from typing import Callable

from herramientas.politica_reutilizacion_fuentes import resolve_source_action, validate_frozen_copy

Downloader = Callable[[Path], dict]


def _read_manifest(package: Path) -> dict | None:
    path = package / "manifest.json"
    if not path.is_file():
        return None
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("manifest.json no contiene un objeto")
    return data


def restore_checkpoint_package(checkpoint: Path, working: Path) -> dict | None:
    """Restaura literalmente sources/ del checkpoint, sin red."""
    src = checkpoint / "sources"
    if not src.is_dir():
        return None
    if working.exists():
        shutil.rmtree(working)
    shutil.copytree(src, working)
    return _read_manifest(working)


def freeze_into_checkpoint(working: Path, checkpoint: Path) -> None:
    dst = checkpoint / "sources"
    if dst.exists():
        shutil.rmtree(dst)
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(working, dst)


def execute_source_policy(*, requested_edition: str | int, working: Path,
                          checkpoint_in: Path | None, checkpoint_out: Path,
                          official_available: bool, downloader: Downloader,
                          expected_records: int | None = None,
                          force_update: bool = False, official_changed: bool = False) -> dict:
    manifest = None
    restored = False
    if checkpoint_in is not None:
        manifest = restore_checkpoint_package(checkpoint_in, working)
        restored = manifest is not None
    elif working.is_dir():
        manifest = _read_manifest(working)

    decision = resolve_source_action(
        prepared_manifest=manifest,
        root=working,
        requested_edition=requested_edition,
        official_available=official_available,
        force_update=force_update,
        official_changed=official_changed,
        expected_records=expected_records,
    )
    mode = decision["decision"]
    if mode == "BLOCK":
        raise RuntimeError("Fuentes BLOQUEADAS: " + decision["reason"])
    if mode == "ACQUIRE":
        if working.exists():
            shutil.rmtree(working)
        working.mkdir(parents=True, exist_ok=True)
        manifest = downloader(working)
        (working / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        valid, reasons = validate_frozen_copy(manifest, working, expected_edition=requested_edition,
                                               expected_records=expected_records)
        if not valid:
            raise RuntimeError("Adquisición inválida: " + "; ".join(reasons))
    else:
        # Punto crítico: en REUSE no se evalúa ni se invoca downloader.
        manifest = decision["manifest"]

    freeze_into_checkpoint(working, checkpoint_out)
    evidence = {
        "schema": "ddd-source-execution/1.0",
        "decision": mode,
        "restored_from_checkpoint": restored,
        "edition": str(requested_edition),
        "sha256": manifest["sha256"],
        "bytes": int(manifest["bytes"]),
        "records": int(manifest["records"]),
        "origin": manifest["origin"],
        "acquired_at": manifest["acquired_at"],
    }
    (checkpoint_out / "source_execution.json").write_text(json.dumps(evidence, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return evidence


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--edition", required=True)
    p.add_argument("--working", required=True, type=Path)
    p.add_argument("--checkpoint-in", type=Path)
    p.add_argument("--checkpoint-out", required=True, type=Path)
    p.add_argument("--expected-records", type=int)
    p.add_argument("--official-available", action="store_true")
    args = p.parse_args()
    # El CLI sólo admite REUSE/BLOCK. ACQUIRE debe suministrar un adaptador explícito
    # desde el workflow para que ninguna descarga pueda ocurrir accidentalmente aquí.
    def forbidden(_: Path) -> dict:
        raise RuntimeError("ACQUIRE requiere adaptador de adquisición explícito")
    evidence = execute_source_policy(requested_edition=args.edition, working=args.working,
        checkpoint_in=args.checkpoint_in, checkpoint_out=args.checkpoint_out,
        official_available=args.official_available, downloader=forbidden,
        expected_records=args.expected_records)
    print(json.dumps(evidence, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
