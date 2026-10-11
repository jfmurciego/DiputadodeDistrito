#!/usr/bin/env python3
"""Revalida la transferencia F10 y prepara receipts fuera del catálogo.

Versión: 1.0.1; nombre: Verificador de transferencia F10; fecha: 2026-10-11.
Alcance: validar bytes auténticos y generar borradores locales; estado: candidato.
Cambios: limitar todas las salidas al directorio --output.
Motivo: preservar inmutable el expediente versionado durante reproducciones.
Origen: e3cd903e70f9fbf88c044dcf3c8b5b7cc63fb4ac; predecesor: legacy/auditorias/CIERRE_FUENTES_20261011/transferencia-autentica-20261011/verificar_transferencia_v1.0.0.py.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import zipfile
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from herramientas.compatibilidad_poblacion_seccionado import (  # noqa: E402
    REPORT_NAME,
    validate_compatibility_package,
)
from herramientas.almacen_fuentes_local import inspect_zip  # noqa: E402
from herramientas.identidad_fuentes_legislatura import territorial_identity  # noqa: E402
from herramientas.seleccionar_paquete_fuentes import validate_prepared_package  # noqa: E402

TRANSFER_SHA256 = "d44f79be353f6c5df469189d47cce9667d451da21a1b60c0eef28f2b34afd66c"


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def extract_checked(archive: zipfile.ZipFile, destination: Path) -> None:
    inspect_zip(archive)
    names: set[str] = set()
    for item in archive.infolist():
        name = item.filename
        path = PurePosixPath(name)
        if (not name or path.is_absolute() or ".." in path.parts or "\\" in name
                or ":" in name or name in names):
            raise ValueError(f"ruta ZIP inválida o duplicada: {name!r}")
        names.add(name)
    if archive.testzip() is not None:
        raise ValueError("CRC ZIP incorrecto")
    archive.extractall(destination)


def verify(transfer: Path, output: Path) -> dict:
    data = transfer.read_bytes()
    if sha256(data) != TRANSFER_SHA256:
        raise ValueError("SHA-256 de transferencia contradictorio")
    if output.exists() or not output.resolve().is_relative_to(Path("/private/tmp")):
        raise ValueError("la salida debe ser nueva y estar en /private/tmp")
    output.mkdir(parents=True)
    receipt_output = output / "receipt-previews"
    receipt_output.mkdir()
    with zipfile.ZipFile(transfer) as outer:
        extract_checked(outer, output)

    sums: dict[str, str] = {}
    for line in (output / "SHA256SUMS").read_text().splitlines():
        checksum, name = line.split(maxsplit=1)
        sums[name.lstrip("* ")] = checksum
    source = json.loads((output / "manifest_F10_5.json").read_text())
    actions = json.loads((HERE.parent / "actions.json").read_text())
    action_rows = {row["run"]["id"]: row for row in actions["rows"]}
    rows: list[dict] = []
    receipts: list[dict] = []
    for item in source["artifacts"]:
        artifact = output / item["file"]
        artifact_sha = sha256(artifact.read_bytes())
        action = action_rows[item["run_id"]]
        remote = action["selected"]
        if (artifact_sha != item["artifact_zip_sha256"]
                or artifact.stat().st_size != item["size_bytes"]
                or sums[item["file"]] != artifact_sha
                or remote["id"] != item["artifact_id"]
                or remote["digest"] != "sha256:" + artifact_sha
                or remote["size_in_bytes"] != artifact.stat().st_size
                or remote["name"] != item["artifact_name"]
                or action["run"]["head_sha"] != item["source_commit"]):
            raise ValueError(f"metadatos de Actions contradictorios: {item['territory_id']}")

        package_dir = output / "validated" / item["territory_id"]
        package_dir.mkdir(parents=True)
        with zipfile.ZipFile(artifact) as zipped:
            extract_checked(zipped, package_dir)
        if set(p.name for p in package_dir.iterdir()) != {"manifest.json", "prepared_sources.zip"}:
            raise ValueError(f"estructura exterior inesperada: {item['territory_id']}")
        package_manifest = json.loads((package_dir / "manifest.json").read_text())
        package_sha = sha256((package_dir / "prepared_sources.zip").read_bytes())
        if (package_sha != item["prepared_sources_zip_sha256"]
                or package_sha != package_manifest["sha256"]
                or any(str(package_manifest[key]) != str(item[key]) for key in
                       ("territory_id", "edition", "population_year", "section_year"))):
            raise ValueError(f"identidad/manifiesto de paquete contradictorio: {item['territory_id']}")

        valid, reasons = validate_prepared_package(
            package_dir, territory_id=item["territory_id"], edition=str(item["edition"]),
            population_year=item["population_year"], section_year=item["section_year"],
        )
        compatibility, report_sha, report_reasons = validate_compatibility_package(
            package_dir, territory_id=item["territory_id"], edition=str(item["edition"]),
            population_year=item["population_year"], section_year=item["section_year"],
            require_ready=True,
        )
        if not valid or reasons or report_reasons or compatibility.get("decision") != "READY":
            raise ValueError(f"validación de paquete fallida: {item['territory_id']}: {reasons + report_reasons}")

        identity = territorial_identity(
            territory_id=item["territory_id"], edition=str(item["edition"]),
            population_year=item["population_year"], section_year=item["section_year"],
            package_sha256=package_sha,
            compatibility_identity_sha256=compatibility["compatibility_identity_sha256"],
        )["territorial_identity_sha256"]
        receipt = {
            "schema": "ddd.territorial-source-receipt/1.0",
            "kind": "territorial_source",
            "territory_id": item["territory_id"],
            "edition": str(item["edition"]),
            "population_year": item["population_year"],
            "section_year": item["section_year"],
            "run_id": item["run_id"],
            "artifact_name": item["artifact_name"],
            "artifact_sha256": artifact_sha,
            "package_sha256": package_sha,
            "source_commit": item["source_commit"],
            "territorial_identity_sha256": identity,
            "compatibility_report_member": REPORT_NAME,
            "compatibility_report_sha256": report_sha,
            "compatibility_identity_sha256": compatibility["compatibility_identity_sha256"],
        }
        receipt_path = receipt_output / f"{item['territory_id']}-run-{item['run_id']}.json"
        receipt_path.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n")
        receipts.append(receipt)
        rows.append({**receipt, "artifact_id": item["artifact_id"],
                     "artifact_bytes": artifact.stat().st_size,
                     "prepared_validation": "PASS", "compatibility_validation": "PASS",
                     "receipt_preview_filename": receipt_path.name})

    result = {
        "schema": "ddd.f10-authenticated-transfer-validation/1.0",
        "transfer_sha256": TRANSFER_SHA256,
        "manifest_sha256": sha256((output / "manifest_F10_5.json").read_bytes()),
        "sha256sums_sha256": sha256((output / "SHA256SUMS").read_bytes()),
        "status": "VERIFIED_RECEIPTS_PREPARED_NOT_REGISTERED_NOT_PROMOTED",
        "rows": rows,
    }
    (output / "validacion.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    (output / "receipts-pendientes.json").write_text(json.dumps({
        "schema": "ddd.f10-receipt-draft-set/1.0",
        "status": result["status"], "receipts": receipts,
    }, ensure_ascii=False, indent=2) + "\n")
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--transfer", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = verify(args.transfer, args.output)
    print(json.dumps({"status": result["status"], "territories": len(result["rows"]),
                      "identities": {row["territory_id"]: row["territorial_identity_sha256"]
                                     for row in result["rows"]}}, ensure_ascii=False))
