#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Validación de paquetes territoriales preparados antes de reutilizarlos."""
from __future__ import annotations

import argparse
import hashlib
import json
import zipfile
from pathlib import Path

from herramientas.politica_reutilizacion_fuentes import validate_frozen_copy

REQUIRED_BUNDLE_FILES = {
    "declaracion_materializacion.json",
    "inventario_fuentes.json",
    "manifiesto_procedencia.json",
    "decision_adquisicion.json",
}


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _json_member(archive: zipfile.ZipFile, name: str) -> dict:
    try:
        raw = archive.read(name)
    except KeyError as exc:
        raise ValueError(f"archivo requerido ausente en paquete: {name}") from exc
    data = json.loads(raw.decode("utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{name} no contiene un objeto JSON")
    return data


def validate_prepared_package(package: Path, *, territory_id: str, edition: str | int) -> tuple[bool, list[str]]:
    reasons: list[str] = []
    manifest_path = package / "manifest.json"
    if not manifest_path.is_file():
        return False, ["manifest.json ausente"]
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except Exception as exc:
        return False, [f"manifest.json ilegible: {exc}"]
    if not isinstance(manifest, dict):
        return False, ["manifest.json no contiene un objeto"]

    valid_copy, copy_reasons = validate_frozen_copy(
        manifest, package, expected_edition=edition
    )
    reasons.extend(copy_reasons)

    declared_territory = str(manifest.get("territory_id") or "").strip()
    if declared_territory and declared_territory != territory_id:
        reasons.append(f"territorio de manifiesto distinto: {declared_territory} != {territory_id}")

    bundle = package / str(manifest.get("path") or "")
    if not bundle.is_file():
        return False, reasons or ["paquete congelado ausente"]
    if not zipfile.is_zipfile(bundle):
        reasons.append("paquete congelado no es ZIP válido")
        return False, reasons

    try:
        with zipfile.ZipFile(bundle) as archive:
            names = set(archive.namelist())
            missing_bundle = sorted(REQUIRED_BUNDLE_FILES - names)
            if missing_bundle:
                reasons.append("archivos requeridos ausentes: " + ", ".join(missing_bundle))
                return False, reasons

            inventory = _json_member(archive, "inventario_fuentes.json")
            provenance = _json_member(archive, "manifiesto_procedencia.json")
            decision = _json_member(archive, "decision_adquisicion.json")

            for label, document in (
                ("inventario", inventory),
                ("procedencia", provenance),
                ("decisión", decision),
            ):
                actual_territory = str(document.get("territory_id") or "").strip()
                if actual_territory != territory_id:
                    reasons.append(f"territorio en {label} distinto: {actual_territory or 'vacío'} != {territory_id}")
                if str(document.get("edition")) != str(edition):
                    reasons.append(f"edición en {label} distinta: {document.get('edition')} != {edition}")

            if decision.get("decision") != "READY":
                reasons.append(f"decisión de adquisición no reutilizable: {decision.get('decision')}")

            sources = inventory.get("sources")
            if not isinstance(sources, list) or not sources:
                reasons.append("inventario sin fuentes")
            else:
                for source in sources:
                    if not isinstance(source, dict):
                        reasons.append("entrada de inventario inválida")
                        continue
                    source_id = str(source.get("source_id") or "desconocida")
                    rel = str(source.get("path") or "")
                    expected_bytes = source.get("bytes")
                    expected_sha = str(source.get("sha256") or "").lower()
                    if not rel or expected_bytes in (None, "") or not expected_sha:
                        reasons.append(f"{source_id}: path/bytes/sha256 incompletos")
                        continue
                    member = "materialized/" + rel.lstrip("/")
                    if member not in names:
                        reasons.append(f"{source_id}: archivo materializado ausente: {member}")
                        continue
                    payload = archive.read(member)
                    if len(payload) != int(expected_bytes):
                        reasons.append(f"{source_id}: tamaño incorrecto: {len(payload)} != {expected_bytes}")
                    if _sha256(payload).lower() != expected_sha:
                        reasons.append(f"{source_id}: checksum incorrecto")
    except Exception as exc:
        reasons.append(f"paquete congelado ilegible: {exc}")

    return not reasons, reasons


def select_first_valid(candidates: list[Path], *, territory_id: str, edition: str | int,
                       reuse_enabled: bool = True) -> tuple[Path | None, list[dict]]:
    if not reuse_enabled:
        return None, []
    diagnostics: list[dict] = []
    for candidate in candidates:
        valid, reasons = validate_prepared_package(candidate, territory_id=territory_id, edition=edition)
        diagnostics.append({"package": str(candidate), "valid": valid, "reasons": reasons})
        if valid:
            return candidate, diagnostics
    return None, diagnostics


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--package", required=True, type=Path)
    ap.add_argument("--territory-id", required=True)
    ap.add_argument("--edition", required=True)
    args = ap.parse_args()
    valid, reasons = validate_prepared_package(
        args.package, territory_id=args.territory_id, edition=args.edition
    )
    print(json.dumps({"valid": valid, "reasons": reasons}, ensure_ascii=False))
    return 0 if valid else 2


if __name__ == "__main__":
    raise SystemExit(main())
