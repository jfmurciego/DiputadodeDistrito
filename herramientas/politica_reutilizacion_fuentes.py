#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Política genérica de reutilización de fuentes DDD.

Resuelve REUSE / ACQUIRE / BLOCK sin efectuar red. Una copia preparada sólo
es reutilizable si su manifiesto y el fichero congelado superan validación
factual. La adquisición queda en manos del adaptador de fuente correspondiente.
"""
from __future__ import annotations

import hashlib
from pathlib import Path

REQUIRED = ("source_id", "edition", "origin", "path", "bytes", "sha256", "records", "acquired_at")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def validate_frozen_copy(manifest: dict, root: str | Path, *, expected_edition: str | int,
                         expected_records: int | None = None) -> tuple[bool, list[str]]:
    reasons: list[str] = []
    missing = [key for key in REQUIRED if manifest.get(key) in (None, "")]
    if missing:
        return False, ["manifiesto incompleto: " + ", ".join(missing)]
    if str(manifest["edition"]) != str(expected_edition):
        reasons.append(f"edición distinta: {manifest['edition']} != {expected_edition}")
    path = Path(root) / str(manifest["path"])
    if not path.is_file():
        reasons.append(f"copia congelada ausente: {manifest['path']}")
        return False, reasons
    actual_bytes = path.stat().st_size
    if actual_bytes != int(manifest["bytes"]):
        reasons.append(f"tamaño incorrecto: {actual_bytes} != {manifest['bytes']}")
    actual_sha = sha256_file(path)
    if actual_sha.lower() != str(manifest["sha256"]).lower():
        reasons.append("checksum incorrecto")
    if expected_records is not None and int(manifest["records"]) != int(expected_records):
        reasons.append(f"registros incorrectos: {manifest['records']} != {expected_records}")
    if not str(manifest["origin"]).strip():
        reasons.append("procedencia vacía")
    if not str(manifest["acquired_at"]).strip():
        reasons.append("fecha de adquisición vacía")
    return not reasons, reasons


def resolve_source_action(*, prepared_manifest: dict | None, root: str | Path,
                          requested_edition: str | int, official_available: bool,
                          force_update: bool = False, official_changed: bool = False,
                          expected_records: int | None = None) -> dict:
    """Decide sin red. Una copia dañada BLOQUEA: nunca se sustituye silenciosamente."""
    if force_update or official_changed:
        if official_available:
            return {"decision": "ACQUIRE", "reason": "actualización requerida"}
        return {"decision": "BLOCK", "reason": "actualización requerida pero fuente oficial no disponible"}

    if prepared_manifest is not None:
        same_edition = str(prepared_manifest.get("edition", "")) == str(requested_edition)
        if same_edition:
            valid, reasons = validate_frozen_copy(
                prepared_manifest, root,
                expected_edition=requested_edition,
                expected_records=expected_records,
            )
            if valid:
                return {"decision": "REUSE", "reason": "copia preparada válida", "manifest": prepared_manifest}
            return {"decision": "BLOCK", "reason": "copia preparada dañada: " + "; ".join(reasons)}

    if official_available:
        return {"decision": "ACQUIRE", "reason": "no existe copia preparada para la edición solicitada"}
    return {"decision": "BLOCK", "reason": "no existe copia preparada y la fuente oficial no está disponible"}
