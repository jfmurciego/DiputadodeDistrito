#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Adaptador productivo entre la política durable y adquirir_fuentes_oficiales.

La decisión REUSE/BLOCK ocurre antes de construir el descargador. Sólo ACQUIRE
puede llegar a acquire_sources(). El checkpoint congela como una sola unidad
reproducible todas las evidencias y entradas materializadas de la edición; REUSE
restaura ese paquete sin red y vuelve a exponer exactamente los mismos inputs.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import zipfile
from pathlib import Path

import yaml

from herramientas.adquirir_fuentes_oficiales import acquire, load_yaml
from herramientas.gestionar_fuentes_checkpoint import execute_source_policy

BUNDLE_NAME = "prepared_sources.zip"
FIXED_ZIP_TIME = (1980, 1, 1, 0, 0, 0)


def _declaration(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def _edition(declaration: Path) -> int:
    return int((_declaration(declaration).get("territory") or {})["edition"])


def _territory_id(declaration: Path) -> str:
    return str((_declaration(declaration).get("territory") or {})["id"])


def _expected_records(declaration: Path) -> int | None:
    value = (_declaration(declaration).get("coverage_checks") or {}).get("expected_sections")
    return int(value) if value not in (None, "") else None


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _source_rows(evidence: Path) -> tuple[list[dict], list[dict]]:
    inventory = json.loads((evidence / "inventario_fuentes.json").read_text(encoding="utf-8"))
    provenance = json.loads((evidence / "manifiesto_procedencia.json").read_text(encoding="utf-8"))
    inv_rows = inventory.get("sources") or inventory.get("fuentes") or []
    prov_rows = provenance.get("sources") or provenance.get("fuentes") or []
    if not isinstance(inv_rows, list) or not inv_rows:
        raise RuntimeError("La adquisición no produjo inventario de fuentes")
    if not isinstance(prov_rows, list):
        prov_rows = []
    return inv_rows, prov_rows


def _write_deterministic_bundle(evidence: Path, destination: Path) -> None:
    files = sorted(p for p in evidence.rglob("*") if p.is_file())
    if not files:
        raise RuntimeError("No hay evidencias ni entradas materializadas que congelar")
    destination.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(destination, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in files:
            rel = path.relative_to(evidence).as_posix()
            info = zipfile.ZipInfo(rel, FIXED_ZIP_TIME)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, path.read_bytes())


def _manifest_from_acquisition(evidence: Path, working: Path, territory_id: str, edition: int,
                               expected_records: int | None) -> dict:
    inv_rows, prov_rows = _source_rows(evidence)
    working.mkdir(parents=True, exist_ok=True)
    frozen = working / BUNDLE_NAME
    _write_deterministic_bundle(evidence, frozen)

    urls: set[str] = set()
    acquired: list[str] = []
    source_ids: list[str] = []
    for row in [*inv_rows, *prov_rows]:
        if not isinstance(row, dict):
            continue
        sid = row.get("source_id") or row.get("id")
        if sid:
            source_ids.append(str(sid))
        for key in ("official_origin_url", "source_url", "url", "origin"):
            value = row.get(key)
            if value:
                urls.add(str(value))
        for value in row.get("urls") or []:
            if value:
                urls.add(str(value))
        date = row.get("acquired_at") or row.get("retrieved_at") or row.get("acquisition_date")
        if date:
            acquired.append(str(date))

    records = expected_records
    if records is None:
        values = [row.get("records") or row.get("rows") or row.get("features") for row in inv_rows if isinstance(row, dict)]
        numeric = [int(v) for v in values if v not in (None, "")]
        records = max(numeric) if numeric else len(inv_rows)

    return {
        "source_id": "prepared-territorial-sources:" + ",".join(sorted(set(source_ids))),
        "territory_id": territory_id,
        "edition": edition,
        "origin": " | ".join(sorted(urls)) or "declared-official-sources",
        "path": frozen.name,
        "bytes": frozen.stat().st_size,
        "sha256": _sha256(frozen),
        "records": int(records),
        "acquired_at": max(acquired) if acquired else "unknown-acquisition-date",
        "bundle_schema": "ddd-prepared-sources-bundle/1.0",
    }


def _restore_acquisition_evidence(working: Path, evidence: Path) -> None:
    manifest = json.loads((working / "manifest.json").read_text(encoding="utf-8"))
    bundle = working / str(manifest["path"])
    if not bundle.is_file():
        raise RuntimeError(f"Paquete congelado ausente: {bundle}")
    if evidence.exists():
        shutil.rmtree(evidence)
    evidence.mkdir(parents=True, exist_ok=True)
    root = evidence.resolve()
    with zipfile.ZipFile(bundle) as archive:
        for member in archive.infolist():
            target = (evidence / member.filename).resolve()
            if target != root and root not in target.parents:
                raise RuntimeError(f"Ruta insegura en paquete congelado: {member.filename}")
        archive.extractall(evidence)


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
    territory_id = _territory_id(args.declaration)
    expected_records = args.expected_records if args.expected_records is not None else _expected_records(args.declaration)

    def downloader(working: Path) -> dict:
        if args.acquisition_evidence.exists():
            shutil.rmtree(args.acquisition_evidence)
        args.acquisition_evidence.mkdir(parents=True, exist_ok=True)
        catalog = load_yaml(args.root_dir / "fuentes/catalogo_oficial.yaml")
        declaration = load_yaml(args.declaration)
        _, _, _, acquisition = acquire(
            catalog=catalog,
            declaration=declaration,
            evidence_dir=args.acquisition_evidence,
            environment=args.environment,
            acquisition_mode=args.acquisition_mode,
            root_dir=args.root_dir,
        )
        if acquisition.get("decision") != "READY":
            raise RuntimeError(
                "Adquisición oficial bloqueada: "
                + json.dumps(acquisition.get("reasons") or [], ensure_ascii=False)
            )
        return _manifest_from_acquisition(args.acquisition_evidence, working, territory_id, edition, expected_records)

    evidence = execute_source_policy(
        requested_edition=edition,
        working=args.working,
        checkpoint_in=args.checkpoint_in if args.checkpoint_in and args.checkpoint_in.exists() else None,
        checkpoint_out=args.checkpoint_out,
        official_available=True,
        downloader=downloader,
        expected_records=expected_records,
    )
    if evidence["decision"] == "REUSE":
        _restore_acquisition_evidence(args.working, args.acquisition_evidence)
    print(json.dumps(evidence, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
