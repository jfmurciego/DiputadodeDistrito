#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Adaptador productivo entre la política durable y adquirir_fuentes_oficiales.

La decisión REUSE/BLOCK ocurre antes de construir el descargador. Sólo ACQUIRE
puede llegar a acquire_sources(). El paquete congelado se conserva bajo sources/
del checkpoint y source_execution.json deja la evidencia de la decisión.
"""
from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

import yaml

from herramientas.adquirir_fuentes_oficiales import acquire_sources
from herramientas.gestionar_fuentes_checkpoint import execute_source_policy


def _edition(declaration: Path) -> int:
    data = yaml.safe_load(declaration.read_text(encoding="utf-8")) or {}
    return int((data.get("territory") or {})["edition"])


def _manifest_from_acquisition(evidence: Path, working: Path, edition: int) -> dict:
    inventory = json.loads((evidence / "inventario_fuentes.json").read_text(encoding="utf-8"))
    provenance = json.loads((evidence / "manifiesto_procedencia.json").read_text(encoding="utf-8"))
    rows = inventory.get("sources") or inventory.get("fuentes") or []
    if len(rows) != 1:
        raise RuntimeError("El adaptador durable exige una fuente congelada por paquete")
    row = rows[0]
    source_path = Path(str(row.get("path") or row.get("materialized_path") or ""))
    if not source_path.is_absolute():
        source_path = evidence / "materialized" / source_path
    if not source_path.is_file():
        candidates = [p for p in (evidence / "materialized").rglob("*") if p.is_file()]
        if len(candidates) != 1:
            raise RuntimeError("No se puede identificar inequívocamente el fichero materializado")
        source_path = candidates[0]
    working.mkdir(parents=True, exist_ok=True)
    frozen = working / source_path.name
    shutil.copy2(source_path, frozen)
    prov_rows = provenance.get("sources") or provenance.get("fuentes") or []
    prov = prov_rows[0] if prov_rows else provenance
    return {
        "source_id": row.get("source_id") or row.get("id") or prov.get("source_id") or "official",
        "edition": edition,
        "origin": prov.get("official_origin_url") or prov.get("origin") or prov.get("url") or "declared-official-source",
        "path": frozen.name,
        "bytes": frozen.stat().st_size,
        "sha256": row.get("sha256"),
        "records": row.get("records") or row.get("rows") or row.get("features"),
        "acquired_at": prov.get("acquired_at") or row.get("acquired_at"),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--declaration", required=True, type=Path)
    ap.add_argument("--working", required=True, type=Path)
    ap.add_argument("--checkpoint-in", type=Path)
    ap.add_argument("--checkpoint-out", required=True, type=Path)
    ap.add_argument("--acquisition-evidence", required=True, type=Path)
    ap.add_argument("--environment", default="production")
    ap.add_argument("--acquisition-mode", required=True)
    ap.add_argument("--root-dir", default=".", type=Path)
    ap.add_argument("--expected-records", type=int)
    args = ap.parse_args()
    edition = _edition(args.declaration)

    def downloader(working: Path) -> dict:
        args.acquisition_evidence.mkdir(parents=True, exist_ok=True)
        acquire_sources(args.declaration, args.acquisition_evidence, environment=args.environment,
                        acquisition_mode=args.acquisition_mode, root_dir=args.root_dir)
        return _manifest_from_acquisition(args.acquisition_evidence, working, edition)

    evidence = execute_source_policy(
        requested_edition=edition,
        working=args.working,
        checkpoint_in=args.checkpoint_in if args.checkpoint_in and args.checkpoint_in.exists() else None,
        checkpoint_out=args.checkpoint_out,
        official_available=True,
        downloader=downloader,
        expected_records=args.expected_records,
    )
    print(json.dumps(evidence, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
