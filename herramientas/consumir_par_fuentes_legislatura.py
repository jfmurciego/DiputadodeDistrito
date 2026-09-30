#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from herramientas import catalogo_preparacion
from herramientas.compatibilidad_poblacion_seccionado import validate_compatibility_package
from herramientas.identidad_fuentes_legislatura import geometric_reuse_compatible
from herramientas.registrar_par_fuentes_legislatura import (
    PAIR_SCHEMA,
    PreparedSourcePairBlock,
    validate_pair_receipt,
)
from herramientas.validar_paquete_electoral import validate_package as validate_electoral_package


class PreparedPairExecutionBlock(ValueError):
    pass


def _json(path: Path, *, label: str) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise PreparedPairExecutionBlock(f"PREPARED_PAIR_BLOCK: {label} ilegible") from exc
    if not isinstance(data, dict):
        raise PreparedPairExecutionBlock(f"PREPARED_PAIR_BLOCK: {label} inválido")
    return data


def resolve_pair(
    *,
    root_dir: Path,
    territory: str,
    edition: str,
) -> dict:
    """Consume exclusivamente el receipt durable registrado en el catálogo."""
    root = root_dir.resolve()
    row = catalogo_preparacion.lookup(
        territory,
        str(edition),
        root / "configuracion/catalogo_preparacion.yaml",
    )
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
    return {
        "receipt_path": pair_rel,
        "pair": pair,
        "geometric_reuse": resolve_geometric_reuse(root_dir=root, pair=pair),
    }


def resolve_geometric_reuse(*, root_dir: Path, pair: dict) -> dict:
    """La reutilización M06 depende sólo de la identidad territorial acreditada."""
    root = root_dir.resolve()
    territory_id = str(pair.get("territory_id") or "")
    edition = str(pair.get("edition") or "")
    current_identity = str(
        (pair.get("territorial_source") or {}).get("territorial_identity_sha256") or ""
    )
    if not current_identity:
        raise PreparedPairExecutionBlock(
            "PREPARED_PAIR_BLOCK: el par carece de identidad territorial acreditada"
        )
    row = catalogo_preparacion.lookup(
        territory_id,
        edition,
        root / "configuracion/catalogo_preparacion.yaml",
    )
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
        or str(lineage.get("edition") or "") != edition
    ):
        raise PreparedPairExecutionBlock(
            "PREPARED_PAIR_BLOCK: linaje del producto territorial inválido"
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


def validate_effective_packages(
    *,
    root_dir: Path,
    pair_path: Path,
    territorial_package: Path,
    electoral_package: Path,
    params: Path,
) -> dict:
    """Verifica los bytes efectivos descargados antes de permitir cualquier cálculo."""
    root = root_dir.resolve()
    pair = validate_pair_receipt(root_dir=root, pair_path=pair_path)
    territorial = pair["territorial_source"]
    refs = pair["references"]
    report, report_sha, reasons = validate_compatibility_package(
        territorial_package,
        territory_id=str(pair["territory_id"]),
        edition=str(pair["edition"]),
        population_year=int(refs["population"]["year"]),
        section_year=int(refs["sectioning"]["year"]),
        require_ready=True,
    )
    if reasons:
        raise PreparedPairExecutionBlock(
            "PREPARED_PAIR_BLOCK: paquete territorial efectivo incompatible: "
            + "; ".join(reasons)
        )
    expected_report_sha = str(territorial.get("compatibility_report_sha256") or "")
    if report_sha != expected_report_sha:
        raise PreparedPairExecutionBlock(
            "PREPARED_PAIR_BLOCK: digest del informe de compatibilidad efectivo no coincide con el receipt"
        )
    actual_compatibility_identity = str(report.get("compatibility_identity_sha256") or "")
    if actual_compatibility_identity != str(
        territorial.get("compatibility_identity_sha256") or ""
    ):
        raise PreparedPairExecutionBlock(
            "PREPARED_PAIR_BLOCK: identidad población↔seccionado efectiva no coincide con el receipt"
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
        "territorial_identity_sha256": territorial["territorial_identity_sha256"],
        "compatibility_report_sha256": report_sha,
        "compatibility_identity_sha256": actual_compatibility_identity,
        "electoral_identity_sha256": pair["electoral_source"]["electoral_identity_sha256"],
        "electoral_package_sha256": electoral_validation.get("package_sha256"),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root-dir", type=Path, default=Path("."))
    sub = ap.add_subparsers(dest="command", required=True)

    resolve_cmd = sub.add_parser("resolve")
    resolve_cmd.add_argument("--territory", required=True)
    resolve_cmd.add_argument("--edition", required=True)
    resolve_cmd.add_argument("--output", type=Path)

    verify_cmd = sub.add_parser("verify")
    verify_cmd.add_argument("--pair-receipt", type=Path, required=True)
    verify_cmd.add_argument("--territorial-package", type=Path, required=True)
    verify_cmd.add_argument("--electoral-package", type=Path, required=True)
    verify_cmd.add_argument("--params", type=Path, required=True)
    verify_cmd.add_argument("--output", type=Path)

    args = ap.parse_args()
    try:
        if args.command == "resolve":
            payload = resolve_pair(
                root_dir=args.root_dir,
                territory=args.territory,
                edition=args.edition,
            )
            payload = {"decision": "READY", **payload}
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
