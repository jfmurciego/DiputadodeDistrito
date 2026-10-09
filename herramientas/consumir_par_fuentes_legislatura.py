#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from herramientas import catalogo_preparacion
from herramientas.compatibilidad_poblacion_seccionado import validate_compatibility_package
from herramientas.identidad_fuentes_legislatura import (
    geometric_reuse_compatible,
    territorial_identity,
)
from herramientas.registrar_par_fuentes_legislatura import (
    PAIR_SCHEMA,
    validate_pair_receipt,
)
from herramientas.seleccionar_paquete_fuentes import validate_prepared_package
from herramientas.validar_paquete_electoral import validate_package as validate_electoral_package


class PreparedPairExecutionBlock(ValueError):
    pass


def _json(path: Path, *, label: str) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise PreparedPairExecutionBlock(f"PREPARED_SOURCE_BLOCK: {label} ilegible") from exc
    if not isinstance(data, dict):
        raise PreparedPairExecutionBlock(f"PREPARED_SOURCE_BLOCK: {label} inválido")
    return data


def _catalog_row(root: Path, territory: str, edition: str) -> dict:
    return catalogo_preparacion.lookup(
        territory,
        str(edition),
        root / "configuracion/catalogo_preparacion.yaml",
    )


def validate_territorial_receipt(
    *,
    root_dir: Path,
    territory: str,
    edition: str,
) -> tuple[dict, dict]:
    """Consume sólo la acreditación territorial durable de #179, sin construir un par."""
    root = root_dir.resolve()
    row = _catalog_row(root, territory, edition)
    if row.get("territorial_sources_prepared") is not True:
        raise PreparedPairExecutionBlock(
            f"PREPARED_TERRITORIAL_BLOCK: fuente territorial no preparada para {row['name']} {edition}"
        )
    evidence = row.get("preparation_evidence")
    if not isinstance(evidence, dict):
        raise PreparedPairExecutionBlock(
            "PREPARED_TERRITORIAL_BLOCK: falta preparation_evidence territorial"
        )
    receipt_rel = str(evidence.get("receipt_path") or "")
    if not receipt_rel:
        raise PreparedPairExecutionBlock(
            "PREPARED_TERRITORIAL_BLOCK: falta receipt territorial versionado de #179"
        )
    receipt_path = root / receipt_rel
    if not receipt_path.is_file():
        raise PreparedPairExecutionBlock(
            f"PREPARED_TERRITORIAL_BLOCK: receipt territorial no disponible: {receipt_rel}"
        )
    receipt = _json(receipt_path, label="receipt territorial")
    if receipt.get("schema") != "ddd.territorial-source-receipt/1.0":
        raise PreparedPairExecutionBlock(
            "PREPARED_TERRITORIAL_BLOCK: schema de receipt territorial no reconocido"
        )
    if (
        str(receipt.get("territory_id") or "") != str(row["territory_id"])
        or str(receipt.get("edition") or "") != str(edition)
    ):
        raise PreparedPairExecutionBlock(
            "PREPARED_TERRITORIAL_BLOCK: receipt territorial pertenece a otra identidad"
        )

    required = (
        "run_id",
        "artifact_name",
        "artifact_sha256",
        "package_sha256",
        "population_year",
        "section_year",
        "territorial_identity_sha256",
        "compatibility_report_member",
        "compatibility_report_sha256",
        "compatibility_identity_sha256",
    )
    missing = [key for key in required if receipt.get(key) in (None, "")]
    if missing:
        raise PreparedPairExecutionBlock(
            "PREPARED_TERRITORIAL_BLOCK: receipt territorial incompleto para #179: "
            + ", ".join(missing)
        )
    for key in required:
        expected = evidence.get(key)
        if expected not in (None, "") and str(receipt.get(key)) != str(expected):
            raise PreparedPairExecutionBlock(
                f"PREPARED_TERRITORIAL_BLOCK: receipt territorial contradice preparation_evidence.{key}"
            )

    identity = territorial_identity(
        territory_id=str(row["territory_id"]),
        edition=str(edition),
        population_year=int(receipt["population_year"]),
        section_year=int(receipt["section_year"]),
        package_sha256=str(receipt["package_sha256"]),
        compatibility_identity_sha256=str(receipt["compatibility_identity_sha256"]),
    )
    if identity["territorial_identity_sha256"] != str(receipt["territorial_identity_sha256"]):
        raise PreparedPairExecutionBlock(
            "PREPARED_TERRITORIAL_BLOCK: territorial_identity_sha256 no reconcilia"
        )
    return row, receipt


def resolve_territorial_source(
    *,
    root_dir: Path,
    territory: str,
    edition: str,
) -> dict:
    root = root_dir.resolve()
    row, receipt = validate_territorial_receipt(
        root_dir=root,
        territory=territory,
        edition=edition,
    )
    return {
        "receipt_path": str((row.get("preparation_evidence") or {})["receipt_path"]),
        "territorial_source": receipt,
        "geometric_reuse": resolve_geometric_reuse(
            root_dir=root,
            territory_id=str(row["territory_id"]),
            edition=str(edition),
            current_identity=str(receipt["territorial_identity_sha256"]),
        ),
    }


def resolve_pair(
    *,
    root_dir: Path,
    territory: str,
    edition: str,
) -> dict:
    """Consume exclusivamente el receipt durable del par para el camino electoral."""
    root = root_dir.resolve()
    row = _catalog_row(root, territory, edition)
    pair_rel = str((row.get("evidence") or {}).get("prepared_source_pair") or "")
    if not pair_rel:
        raise PreparedPairExecutionBlock(
            f"PREPARED_PAIR_BLOCK: falta evidence.prepared_source_pair para "
            f"{row['name']} edición {edition}; complete la preparación conjunta antes de ejecutar"
        )
    pair_path = root / pair_rel
    if not pair_path.is_file():
        raise PreparedPairExecutionBlock(
            f"PREPARED_PAIR_BLOCK: receipt durable del par no disponible: {pair_rel}"
        )
    try:
        pair = validate_pair_receipt(
            root_dir=root,
            pair_path=pair_path,
            expected_territory_id=str(row["territory_id"]),
            expected_edition=str(edition),
        )
    except Exception as exc:
        raise PreparedPairExecutionBlock(str(exc)) from exc
    if pair.get("schema") != PAIR_SCHEMA:
        raise PreparedPairExecutionBlock("PREPARED_PAIR_BLOCK: schema de par no reconocido")
    territorial = pair.get("territorial_source") or {}
    return {
        "receipt_path": pair_rel,
        "pair": pair,
        "geometric_reuse": resolve_geometric_reuse(
            root_dir=root,
            territory_id=str(pair["territory_id"]),
            edition=str(pair["edition"]),
            current_identity=str(territorial.get("territorial_identity_sha256") or ""),
        ),
    }


def resolve_geometric_reuse(
    *,
    root_dir: Path,
    territory_id: str,
    edition: str,
    current_identity: str,
) -> dict:
    """La reutilización M06 depende sólo de la identidad territorial acreditada."""
    root = root_dir.resolve()
    if not current_identity:
        raise PreparedPairExecutionBlock(
            "PREPARED_TERRITORIAL_BLOCK: falta identidad territorial acreditada"
        )
    row = _catalog_row(root, territory_id, edition)
    if row.get("territorial_product_available") is not True:
        return {
            "available": False,
            "compatible": False,
            "reason": "NO_TERRITORIAL_PRODUCT",
            "current_territorial_identity_sha256": current_identity,
        }
    evidence = row.get("evidence") or {}
    lineage_rel = str(evidence.get("territorial_product_source_lineage") or "")
    product_rel = str(evidence.get("territorial_product") or "")
    if not lineage_rel or not (root / lineage_rel).is_file():
        return {
            "available": True,
            "compatible": False,
            "reason": "PRODUCT_SOURCE_LINEAGE_MISSING",
            "current_territorial_identity_sha256": current_identity,
        }
    if not product_rel or not (root / product_rel).is_file():
        return {
            "available": True,
            "compatible": False,
            "reason": "PRODUCT_RECEIPT_MISSING",
            "current_territorial_identity_sha256": current_identity,
        }
    lineage = _json(root / lineage_rel, label="linaje producto→fuente")
    product = _json(root / product_rel, label="receipt de producto territorial")
    if (
        lineage.get("schema") != "ddd.territorial-product-source-lineage/1.0"
        or str(lineage.get("territory_id") or "") != territory_id
        or str(lineage.get("edition") or "") != str(edition)
    ):
        raise PreparedPairExecutionBlock(
            "PREPARED_TERRITORIAL_BLOCK: linaje del producto territorial inválido"
        )
    historical_identity = str(
        (lineage.get("territorial_source") or {}).get("territorial_identity_sha256") or ""
    )
    compatible = geometric_reuse_compatible(
        product_territorial_identity_sha256=historical_identity,
        current_territorial_identity_sha256=current_identity,
    )
    return {
        "available": True,
        "compatible": bool(compatible),
        "reason": "SOURCE_IDENTITY_MATCH" if compatible else "SOURCE_IDENTITY_MISMATCH",
        "product_run_id": product.get("run_id"),
        "product_artifact_name": product.get("artifact_name"),
        "product_artifact_sha256": product.get("artifact_sha256"),
        "product_source_territorial_identity_sha256": historical_identity,
        "current_territorial_identity_sha256": current_identity,
        "lineage_path": lineage_rel,
        "product_receipt_path": product_rel,
    }


def validate_effective_territorial_package(
    *,
    root_dir: Path,
    territorial_receipt_path: Path,
    territorial_package: Path,
) -> dict:
    """Valida todos los bytes territoriales efectivos con el contrato de #179."""
    root = root_dir.resolve()
    receipt_path = (
        territorial_receipt_path
        if territorial_receipt_path.is_absolute()
        else root / territorial_receipt_path
    )
    receipt = _json(receipt_path, label="receipt territorial")
    territory_id = str(receipt.get("territory_id") or "")
    edition = str(receipt.get("edition") or "")
    population_year = int(receipt.get("population_year"))
    section_year = int(receipt.get("section_year"))

    valid, reasons = validate_prepared_package(
        territorial_package,
        territory_id=territory_id,
        edition=edition,
        population_year=population_year,
        section_year=section_year,
    )
    if not valid:
        raise PreparedPairExecutionBlock(
            "PREPARED_TERRITORIAL_BLOCK: paquete territorial efectivo inválido: "
            + "; ".join(reasons)
        )

    manifest = _json(territorial_package / "manifest.json", label="manifest territorial efectivo")
    if str(manifest.get("sha256") or "") != str(receipt.get("package_sha256") or ""):
        raise PreparedPairExecutionBlock(
            "PREPARED_TERRITORIAL_BLOCK: package_sha256 efectivo no coincide con el receipt"
        )

    report, report_sha, compatibility_reasons = validate_compatibility_package(
        territorial_package,
        territory_id=territory_id,
        edition=edition,
        population_year=population_year,
        section_year=section_year,
        require_ready=True,
    )
    if compatibility_reasons:
        raise PreparedPairExecutionBlock(
            "PREPARED_TERRITORIAL_BLOCK: compatibilidad población↔seccionado inválida: "
            + "; ".join(compatibility_reasons)
        )
    if report_sha != str(receipt.get("compatibility_report_sha256") or ""):
        raise PreparedPairExecutionBlock(
            "PREPARED_TERRITORIAL_BLOCK: digest del informe de compatibilidad no coincide"
        )
    compatibility_identity = str(report.get("compatibility_identity_sha256") or "")
    if compatibility_identity != str(receipt.get("compatibility_identity_sha256") or ""):
        raise PreparedPairExecutionBlock(
            "PREPARED_TERRITORIAL_BLOCK: identidad de compatibilidad no coincide"
        )
    identity = territorial_identity(
        territory_id=territory_id,
        edition=edition,
        population_year=population_year,
        section_year=section_year,
        package_sha256=str(receipt["package_sha256"]),
        compatibility_identity_sha256=compatibility_identity,
    )["territorial_identity_sha256"]
    if identity != str(receipt.get("territorial_identity_sha256") or ""):
        raise PreparedPairExecutionBlock(
            "PREPARED_TERRITORIAL_BLOCK: identidad territorial efectiva no coincide"
        )
    return {
        "schema": "ddd.prepared-territorial-source-execution-validation/1.0",
        "decision": "READY",
        "territory_id": territory_id,
        "edition": edition,
        "territorial_identity_sha256": identity,
        "compatibility_report_sha256": report_sha,
        "compatibility_identity_sha256": compatibility_identity,
    }


def validate_effective_packages(
    *,
    root_dir: Path,
    pair_path: Path,
    territorial_package: Path,
    electoral_package: Path,
    params: Path,
) -> dict:
    """Camino electoral: valida par completo y bytes territoriales + electorales."""
    root = root_dir.resolve()
    pair = validate_pair_receipt(root_dir=root, pair_path=pair_path)
    territorial = pair["territorial_source"]
    territorial_validation = validate_effective_territorial_package(
        root_dir=root,
        territorial_receipt_path=Path(str(territorial["receipt_path"])),
        territorial_package=territorial_package,
    )
    if (
        territorial_validation["territorial_identity_sha256"]
        != str(territorial.get("territorial_identity_sha256") or "")
    ):
        raise PreparedPairExecutionBlock(
            "PREPARED_PAIR_BLOCK: fuente territorial efectiva no coincide con el par"
        )

    electoral_validation = validate_electoral_package(
        package=electoral_package,
        params=params,
        territory_id=str(pair["territory_id"]),
        edition=str(pair["edition"]),
        root=root,
        materialize=False,
    )
    if electoral_validation.get("decision") != "READY_PACKAGE":
        raise PreparedPairExecutionBlock(
            "PREPARED_PAIR_BLOCK: paquete electoral efectivo no está READY_PACKAGE"
        )
    expected_election_id = str((pair.get("election") or {}).get("election_id") or "")
    if str(electoral_validation.get("election_id") or "") != expected_election_id:
        raise PreparedPairExecutionBlock(
            "PREPARED_PAIR_BLOCK: election_id efectivo no coincide con el receipt"
        )

    return {
        "schema": "ddd.prepared-source-pair-execution-validation/1.0",
        "decision": "READY",
        "pair_sha256": pair["pair_sha256"],
        "territory_id": pair["territory_id"],
        "edition": pair["edition"],
        "territorial_identity_sha256": territorial_validation["territorial_identity_sha256"],
        "compatibility_report_sha256": territorial_validation["compatibility_report_sha256"],
        "compatibility_identity_sha256": territorial_validation["compatibility_identity_sha256"],
        "electoral_identity_sha256": pair["electoral_source"]["electoral_identity_sha256"],
        "electoral_package_sha256": electoral_validation.get("package_sha256"),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root-dir", type=Path, default=Path("."))
    sub = ap.add_subparsers(dest="command", required=True)

    resolve_pair_cmd = sub.add_parser("resolve")
    resolve_pair_cmd.add_argument("--territory", required=True)
    resolve_pair_cmd.add_argument("--edition", required=True)
    resolve_pair_cmd.add_argument("--output", type=Path)

    resolve_t_cmd = sub.add_parser("resolve-territorial")
    resolve_t_cmd.add_argument("--territory", required=True)
    resolve_t_cmd.add_argument("--edition", required=True)
    resolve_t_cmd.add_argument("--output", type=Path)

    verify_pair_cmd = sub.add_parser("verify")
    verify_pair_cmd.add_argument("--pair-receipt", type=Path, required=True)
    verify_pair_cmd.add_argument("--territorial-package", type=Path, required=True)
    verify_pair_cmd.add_argument("--electoral-package", type=Path, required=True)
    verify_pair_cmd.add_argument("--params", type=Path, required=True)
    verify_pair_cmd.add_argument("--output", type=Path)

    verify_t_cmd = sub.add_parser("verify-territorial")
    verify_t_cmd.add_argument("--territorial-receipt", type=Path, required=True)
    verify_t_cmd.add_argument("--territorial-package", type=Path, required=True)
    verify_t_cmd.add_argument("--output", type=Path)

    args = ap.parse_args()
    try:
        if args.command == "resolve":
            payload = {"decision": "READY", **resolve_pair(
                root_dir=args.root_dir,
                territory=args.territory,
                edition=args.edition,
            )}
        elif args.command == "resolve-territorial":
            payload = {"decision": "READY", **resolve_territorial_source(
                root_dir=args.root_dir,
                territory=args.territory,
                edition=args.edition,
            )}
        elif args.command == "verify-territorial":
            payload = validate_effective_territorial_package(
                root_dir=args.root_dir,
                territorial_receipt_path=args.territorial_receipt,
                territorial_package=args.territorial_package,
            )
        else:
            payload = validate_effective_packages(
                root_dir=args.root_dir,
                pair_path=args.pair_receipt,
                territorial_package=args.territorial_package,
                electoral_package=args.electoral_package,
                params=args.params,
            )
    except Exception as exc:
        payload = {"decision": "BLOCKED", "reason": str(exc)}
        print(json.dumps(payload, ensure_ascii=False))
        return 2

    output = getattr(args, "output", None)
    if output:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
