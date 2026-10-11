#!/usr/bin/env python3
"""Ejecuta la puerta #179 territorial de Extremadura en un catálogo scratch.

Versión: 1.0.1; nombre: Validador aislado F10 Extremadura; fecha: 2026-10-11.
Alcance: validar receipt territorial sin modificar el catálogo productivo; estado: candidato.
Cambios: tomar receipt preview del directorio de salida aislado.
Motivo: mantener separados el ensayo contractual y los receipts versionados.
Origen: e3cd903e70f9fbf88c044dcf3c8b5b7cc63fb4ac; predecesor: legacy/auditorias/CIERRE_FUENTES_20261011/transferencia-autentica-20261011/validar_extremadura_aislada_v1.0.0.py.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from herramientas.consumir_par_fuentes_legislatura import validate_territorial_receipt  # noqa: E402
from herramientas.compatibilidad_poblacion_seccionado import validate_compatibility_package  # noqa: E402
from herramientas.seleccionar_paquete_fuentes import validate_prepared_package  # noqa: E402


def run(validated_root: Path, scratch: Path) -> dict:
    if scratch.exists() or not scratch.resolve().is_relative_to(Path("/private/tmp")):
        raise ValueError("scratch debe ser una ruta nueva bajo /private/tmp")
    receipt_path = validated_root / "receipt-previews/extremadura-run-38091144559.json"
    receipt = json.loads(receipt_path.read_text())
    if (receipt["territory_id"], receipt["edition"], receipt["population_year"],
            receipt["section_year"]) != ("extremadura", "2025", 2025, 2025):
        raise ValueError("la identidad recibida no es Extremadura 2025/2025")
    package = validated_root / "validated/extremadura"
    if not package.is_dir():
        raise ValueError("falta el paquete verificado de Extremadura")
    valid, reasons = validate_prepared_package(
        package, territory_id="extremadura", edition="2025", population_year=2025,
        section_year=2025,
    )
    compatibility, report_sha, report_reasons = validate_compatibility_package(
        package, territory_id="extremadura", edition="2025", population_year=2025,
        section_year=2025, require_ready=True,
    )
    package_sha = hashlib.sha256((package / "prepared_sources.zip").read_bytes()).hexdigest()
    if (not valid or reasons or report_reasons or report_sha != receipt["compatibility_report_sha256"]
            or package_sha != receipt["package_sha256"]
            or compatibility.get("compatibility_identity_sha256") != receipt["compatibility_identity_sha256"]):
        raise ValueError(f"paquete/informe de compatibilidad no coincide: {reasons + report_reasons}")

    catalog_source = ROOT / "configuracion/catalogo_preparacion.yaml"
    original_sha = hashlib.sha256(catalog_source.read_bytes()).hexdigest()
    catalog = yaml.safe_load(catalog_source.read_text(encoding="utf-8"))
    row = next(item for item in catalog["territories"] if item["territory_id"] == "extremadura")
    state = row["editions"]["2025"]
    receipt_rel = (Path("territorios/extremadura/evidencia/fuentes_territoriales") / "2025"
                   / receipt["territorial_identity_sha256"] / str(receipt["run_id"]) / "receipt.json")
    state["territorial_sources_prepared"] = True
    state["preparation_evidence"] = {
        key: receipt[key] for key in (
            "run_id", "artifact_name", "artifact_sha256", "package_sha256",
            "population_year", "section_year", "territorial_identity_sha256",
            "compatibility_report_member", "compatibility_report_sha256",
            "compatibility_identity_sha256",
        )
    }
    state["preparation_evidence"]["receipt_path"] = receipt_rel.as_posix()
    (scratch / "configuracion").mkdir(parents=True)
    (scratch / "configuracion/catalogo_preparacion.yaml").write_text(
        yaml.safe_dump(catalog, allow_unicode=True, sort_keys=False), encoding="utf-8"
    )
    receipt_path = scratch / receipt_rel
    receipt_path.parent.mkdir(parents=True)
    receipt_path.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n")

    _, accepted = validate_territorial_receipt(
        root_dir=scratch, territory="extremadura", edition="2025"
    )
    if accepted != receipt or hashlib.sha256(catalog_source.read_bytes()).hexdigest() != original_sha:
        raise ValueError("receipt devuelto o catálogo productivo contradictorio")
    result = {
        "status": "PASS_ISOLATED_TERRITORIAL_RECEIPT_ONLY",
        "validator": "herramientas.consumir_par_fuentes_legislatura.validate_territorial_receipt",
        "territory_id": "extremadura", "edition": "2025",
        "run_id": receipt["run_id"],
        "territorial_identity_sha256": receipt["territorial_identity_sha256"],
        "source_catalog_sha256_before_after": original_sha,
        "scratch_catalog_and_receipt_only": True,
        "catalogue_registration": False,
        "promotion": False,
        "electoral_source_evaluated": False,
    }
    (scratch / "result.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--validated-root", type=Path, required=True)
    parser.add_argument("--scratch", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(run(args.validated_root, args.scratch), ensure_ascii=False))
