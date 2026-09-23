#!/usr/bin/env python3
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import zipfile
from pathlib import Path
from typing import Any

import yaml

CONFIRMATION = "EXECUTE_CAMPAIGN_CONFIRMED"
ENTRYPOINT = "gerrychain_50"
EXPECTED_FIELDS = {
    "schema": "ddd.campaign-manifest/1.1",
    "data_edition": "2025",
    "execution_mode": "Reutilizar fuente explícita",
    "optimization_algorithm": "GerryChain 50",
    "entrypoint": ENTRYPOINT,
    "candidate_count": 50,
    "require_unique_hashes": True,
    "fail_fast": False,
    "max_parallel": 5,
    "retry_failed": False,
    "campaign_confirmation": CONFIRMATION,
}
EXPECTED_TERRITORIES = [
    ("01", "aragon", "Aragón", "electoral"),
    ("02", "principado_de_asturias", "Principado de Asturias", "electoral"),
    ("03", "galicia", "Galicia", "electoral"),
    ("04", "castilla_y_leon", "Castilla y León", "electoral"),
    ("05", "extremadura", "Extremadura", "territorial_only"),
]
REUSE_FIELDS = (
    "run_id",
    "checkpoint_stage",
    "artifact_name",
    "artifact_sha256",
    "source_sha",
    "m01_artifact_name",
    "m01_artifact_sha256",
    "expected_population_total",
    "expected_section_count",
    "expected_district_count",
    "expected_certification",
)


def _load(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("El manifiesto de campaña debe ser un objeto JSON")
    return data


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _hex(value: object, length: int, label: str) -> str:
    text = str(value or "").lower()
    if len(text) != length or any(ch not in "0123456789abcdef" for ch in text):
        raise ValueError(f"{label} debe contener {length} hexadecimales")
    return text


def _validate_reuse(row: dict[str, Any]) -> None:
    reuse = row.get("reuse")
    if not isinstance(reuse, dict):
        raise ValueError(f"{row.get('territory_id')}: reuse ausente")
    missing = [key for key in REUSE_FIELDS if key not in reuse]
    if missing:
        raise ValueError(f"{row.get('territory_id')}: faltan campos de procedencia: {missing}")
    if not isinstance(reuse["run_id"], int) or reuse["run_id"] <= 0:
        raise ValueError("reuse.run_id inválido")
    if reuse["checkpoint_stage"] != "SOURCE_PACKAGE":
        raise ValueError("La campaña sólo admite SOURCE_PACKAGE explícito; no último checkpoint")
    _hex(reuse["artifact_sha256"], 64, "reuse.artifact_sha256")
    _hex(reuse["m01_artifact_sha256"], 64, "reuse.m01_artifact_sha256")
    _hex(reuse["source_sha"], 40, "reuse.source_sha")
    if reuse["expected_certification"] != "READY":
        raise ValueError("La fuente reutilizada debe estar certificada READY")
    for key in ("expected_population_total", "expected_section_count", "expected_district_count"):
        if not isinstance(reuse[key], int) or reuse[key] <= 0:
            raise ValueError(f"{key} debe ser entero positivo")


def validate_manifest(path: Path) -> dict[str, Any]:
    data = _load(path)
    for key, value in EXPECTED_FIELDS.items():
        if data.get(key) != value:
            raise ValueError(f"{key}: esperado {value!r}, observado {data.get(key)!r}")
    if not data.get("campaign_id"):
        raise ValueError("campaign_id ausente")
    territories = data.get("territories")
    if not isinstance(territories, list) or len(territories) != 5:
        raise ValueError("La campaña debe contener exactamente cinco territorios")
    observed = [
        (
            str(row.get("slot")),
            row.get("territory_id"),
            row.get("territory_name"),
            row.get("publication_mode"),
        )
        for row in territories
    ]
    if observed != EXPECTED_TERRITORIES:
        raise ValueError(
            "Territorios, slots o modos no coinciden con el manifiesto aprobado: "
            + repr(observed)
        )
    if len({row[0] for row in observed}) != 5 or len({row[1] for row in observed}) != 5:
        raise ValueError("Slots o territorios duplicados")
    for row in territories:
        _validate_reuse(row)
    return data


def assert_productive_launch(event_name: str, ref_name: str, confirmation: str) -> None:
    if event_name != "workflow_dispatch":
        raise ValueError("La ejecución productiva sólo está permitida desde workflow_dispatch")
    if ref_name != "main":
        raise ValueError("La ejecución productiva sólo está permitida desde main")
    if confirmation != CONFIRMATION:
        raise ValueError("Falta confirmación explícita de campaña")


def artifact_namespace(campaign_instance: str, slot: str, territory_id: str) -> str:
    raw = f"{campaign_instance}--{slot}--{territory_id}"
    allowed = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_."
    cleaned = "".join(ch if ch in allowed else "-" for ch in raw)
    if not cleaned or len(cleaned) > 180:
        raise ValueError("artifact_namespace inválido")
    return cleaned


def build_matrix(
    path: Path,
    *,
    source_sha: str,
    campaign_instance: str,
    confirmation: str,
) -> dict[str, Any]:
    data = validate_manifest(path)
    if confirmation != CONFIRMATION:
        raise ValueError("Confirmación explícita incorrecta")
    code_sha = _hex(source_sha, 40, "source_sha")
    digest = sha256(path)
    include = []
    for territory in data["territories"]:
        slot = territory["slot"]
        territory_id = territory["territory_id"]
        namespace = f"{campaign_instance}/{slot}/{territory_id}"
        reuse = territory["reuse"]
        include.append(
            {
                "campaign_instance": campaign_instance,
                "slot": slot,
                "territory_id": territory_id,
                "territory_name": territory["territory_name"],
                "namespace": namespace,
                "artifact_namespace": artifact_namespace(campaign_instance, slot, territory_id),
                "source_sha": code_sha,
                "manifest_sha256": digest,
                "data_edition": data["data_edition"],
                "execution_mode": data["execution_mode"],
                "optimization_algorithm": data["optimization_algorithm"],
                "entrypoint": data["entrypoint"],
                "candidate_count": data["candidate_count"],
                "require_unique_hashes": data["require_unique_hashes"],
                "publication_mode": territory["publication_mode"],
                "campaign_confirmation": confirmation,
                "retry_failed": data["retry_failed"],
                "reuse_run_id": reuse["run_id"],
                "reuse_artifact_name": reuse["artifact_name"],
                "reuse_artifact_sha256": reuse["artifact_sha256"],
                "reuse_source_sha": reuse["source_sha"],
                "m01_artifact_name": reuse["m01_artifact_name"],
                "m01_artifact_sha256": reuse["m01_artifact_sha256"],
                "expected_population_total": reuse["expected_population_total"],
                "expected_section_count": reuse["expected_section_count"],
                "expected_district_count": reuse["expected_district_count"],
                "expected_certification": reuse["expected_certification"],
            }
        )
    return {"include": include}


def _catalog_entry(root: Path, territory_id: str, edition: str) -> dict[str, Any]:
    catalog = yaml.safe_load(
        (root / "configuracion/catalogo_preparacion.yaml").read_text(encoding="utf-8")
    ) or {}
    for territory in catalog.get("territories", []):
        if territory.get("territory_id") == territory_id:
            edition_data = (territory.get("editions") or {}).get(str(edition))
            if not isinstance(edition_data, dict):
                break
            return edition_data
    raise ValueError(f"Catálogo sin {territory_id}/{edition}")


def _expected_k(contract: dict[str, Any]) -> int:
    validation = contract.get("validation") or {}
    if validation.get("expected_districts") is not None:
        return int(validation["expected_districts"])
    modules = contract.get("modulos") or {}
    m05 = modules.get("modulo_05_optimizar_distritos") or {}
    m04 = modules.get("modulo_04_generar_semillas") or {}
    value = m05.get("expected_districts") or m04.get("k_districts")
    if value is None:
        raise ValueError("Contrato sin número de distritos")
    return int(value)


def validate_repository_binding(
    manifest_path: Path, *, slot: str, root_dir: Path
) -> dict[str, Any]:
    data = validate_manifest(manifest_path)
    row = next((item for item in data["territories"] if item["slot"] == slot), None)
    if row is None:
        raise ValueError(f"Slot desconocido: {slot}")
    reuse = row["reuse"]
    catalog = _catalog_entry(root_dir, row["territory_id"], data["data_edition"])
    if catalog.get("preparation_status") != reuse["expected_certification"]:
        raise ValueError("Certificación de preparación distinta del manifiesto")
    if catalog.get("production_authorization") != "AUTHORIZED":
        raise ValueError("Territorio sin autorización de producción")
    contract_path = catalog.get("contract_path")
    if not contract_path:
        raise ValueError("Contrato territorial ausente")
    contract = yaml.safe_load((root_dir / contract_path).read_text(encoding="utf-8")) or {}
    meta = contract.get("meta") or {}
    if str(meta.get("year")) != data["data_edition"]:
        raise ValueError("Edición del contrato distinta del manifiesto")
    if _expected_k(contract) != reuse["expected_district_count"]:
        raise ValueError("Número de distritos del contrato distinto del manifiesto")
    return {
        "territory_id": row["territory_id"],
        "edition": data["data_edition"],
        "expected_population_total": reuse["expected_population_total"],
        "expected_section_count": reuse["expected_section_count"],
        "expected_district_count": reuse["expected_district_count"],
        "certification": reuse["expected_certification"],
    }


def _find_source_manifest(source_dir: Path) -> dict[str, Any]:
    candidates = []
    for path in source_dir.rglob("manifest.json"):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        if isinstance(data, dict) and "territory_id" in data and "edition" in data:
            candidates.append(data)
    if len(candidates) != 1:
        raise ValueError(f"Se esperaba un manifest.json territorial inequívoco; encontrados={len(candidates)}")
    return candidates[0]


def _read_m01_geojson(m01_dir: Path) -> dict[str, Any]:
    zips = sorted(m01_dir.rglob("*m01*secciones*poblacion*.geojson.zip"))
    if not zips:
        zips = sorted(m01_dir.rglob("*.geojson.zip"))
    if len(zips) != 1:
        raise ValueError(f"Checkpoint M01 no inequívoco; geojson.zip encontrados={len(zips)}")
    with zipfile.ZipFile(zips[0]) as archive:
        members = [name for name in archive.namelist() if name.lower().endswith(".geojson")]
        if len(members) != 1:
            raise ValueError("El ZIP M01 debe contener un único GeoJSON")
        return json.loads(archive.read(members[0]).decode("utf-8"))


def validate_materialized_reuse(
    manifest_path: Path,
    *,
    slot: str,
    root_dir: Path,
    source_dir: Path,
    m01_dir: Path,
) -> dict[str, Any]:
    expected = validate_repository_binding(manifest_path, slot=slot, root_dir=root_dir)
    source = _find_source_manifest(source_dir)
    if source.get("territory_id") != expected["territory_id"]:
        raise ValueError("El artefacto reutilizado pertenece a otro territorio")
    if str(source.get("edition")) != expected["edition"]:
        raise ValueError("El artefacto reutilizado pertenece a otra edición")
    geo = _read_m01_geojson(m01_dir)
    features = geo.get("features") or []
    section_count = len(features)
    pop_field = "POP_" + expected["edition"]
    values = []
    for feature in features:
        props = feature.get("properties") or {}
        value = props.get(pop_field)
        if value is None:
            raise ValueError(f"Sección M01 sin {pop_field}")
        values.append(float(value))
    population_total = sum(values)
    if section_count != expected["expected_section_count"]:
        raise ValueError(
            f"Secciones distintas: {section_count} != {expected['expected_section_count']}"
        )
    if abs(population_total - expected["expected_population_total"]) > 1e-6:
        raise ValueError(
            f"Población distinta: {population_total} != {expected['expected_population_total']}"
        )
    return {
        **expected,
        "population_total": int(population_total),
        "section_count": section_count,
        "status": "VALID",
    }


def validate_portfolio_contract(portfolio: dict[str, Any]) -> dict[str, Any]:
    candidates = portfolio.get("candidates")
    if not isinstance(candidates, list):
        candidates = []
    hashes = [str(row.get("assignment_hash") or "") for row in candidates]
    missing_hashes = sum(1 for value in hashes if not value)
    present = [value for value in hashes if value]
    unique_hashes = len(set(present))
    duplicate_hashes = len(present) - unique_hashes
    expected = 50
    candidate_count = int(portfolio.get("candidate_count") or len(candidates))
    candidate_count_valid = len(candidates)
    valid = (
        candidate_count == expected
        and candidate_count_valid == expected
        and unique_hashes == expected
        and missing_hashes == 0
        and duplicate_hashes == 0
        and int(portfolio.get("unique_candidate_count") or unique_hashes) == expected
    )
    return {
        "candidate_count_expected": expected,
        "candidate_count_valid": candidate_count_valid,
        "unique_candidate_hash_count": unique_hashes,
        "missing_candidate_hash_count": missing_hashes,
        "duplicate_candidate_hash_count": duplicate_hashes,
        "valid": valid,
    }


def aggregate(
    path: Path,
    reports_root: Path,
    *,
    campaign_instance: str,
    source_sha: str,
) -> dict[str, Any]:
    data = validate_manifest(path)
    digest = sha256(path)
    reports = {}
    for candidate in reports_root.rglob("campaign_status.json"):
        try:
            row = json.loads(candidate.read_text(encoding="utf-8"))
        except Exception:
            continue
        if row.get("campaign_instance") == campaign_instance:
            reports[row.get("territory_id")] = row

    rows = []
    failed = []
    for territory in data["territories"]:
        territory_id = territory["territory_id"]
        row = reports.get(territory_id)
        if row is None:
            item = {
                "slot": territory["slot"],
                "territory_id": territory_id,
                "territory_name": territory["territory_name"],
                "publication_mode": territory["publication_mode"],
                "status": "MISSING",
                "reason": "campaign_status.json ausente",
            }
        else:
            item = copy.deepcopy(row)
            mismatches = []
            checks = {
                "slot": territory["slot"],
                "publication_mode": territory["publication_mode"],
                "source_sha": source_sha,
                "manifest_sha256": digest,
                "entrypoint": ENTRYPOINT,
                "require_unique_hashes": True,
                "candidate_count_expected": 50,
                "candidate_count_valid": 50,
                "unique_candidate_hash_count": 50,
                "missing_candidate_hash_count": 0,
                "duplicate_candidate_hash_count": 0,
            }
            for key, expected in checks.items():
                if row.get(key) != expected:
                    mismatches.append(key)
            if mismatches:
                item["status"] = "FAIL"
                item["reason"] = "Contrato de campaña inconsistente: " + ", ".join(mismatches)
        rows.append(item)
        if item.get("status") != "PASS":
            failed.append(territory_id)

    return {
        "schema": "ddd.campaign-summary/1.1",
        "campaign_id": data["campaign_id"],
        "campaign_instance": campaign_instance,
        "source_sha": source_sha,
        "manifest_sha256": digest,
        "entrypoint": data["entrypoint"],
        "require_unique_hashes": data["require_unique_hashes"],
        "territory_count_expected": 5,
        "territory_count_reported": len(reports),
        "failed_territories": failed,
        "status": "PASS" if not failed else "FAIL",
        "territories": rows,
    }


def write_markdown(summary: dict[str, Any], path: Path) -> None:
    lines = [
        "# Campaña " + summary["campaign_instance"],
        "",
        "- estado: " + summary["status"],
        "- source SHA: " + summary["source_sha"],
        "- manifest SHA-256: " + summary["manifest_sha256"],
        "- entrypoint: " + summary["entrypoint"],
        "- require_unique_hashes: " + str(summary["require_unique_hashes"]).lower(),
        "",
        "| Slot | Territorio | Publicación | Estado |",
        "|---|---|---|---|",
    ]
    for row in summary["territories"]:
        lines.append(
            "| {slot} | {territory} | {publication} | {status} |".format(
                slot=row.get("slot", ""),
                territory=row.get("territory_name", row.get("territory_id", "")),
                publication=row.get("publication_mode", ""),
                status=row.get("status", ""),
            )
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    commands = parser.add_subparsers(dest="command", required=True)
    validate = commands.add_parser("validate")
    validate.add_argument("--manifest", type=Path, required=True)
    matrix = commands.add_parser("matrix")
    matrix.add_argument("--manifest", type=Path, required=True)
    matrix.add_argument("--source-sha", required=True)
    matrix.add_argument("--campaign-instance", required=True)
    matrix.add_argument("--confirmation", required=True)
    reuse = commands.add_parser("validate-reuse")
    reuse.add_argument("--manifest", type=Path, required=True)
    reuse.add_argument("--slot", required=True)
    reuse.add_argument("--root-dir", type=Path, default=Path("."))
    reuse.add_argument("--source-dir", type=Path, required=True)
    reuse.add_argument("--m01-dir", type=Path, required=True)
    portfolio = commands.add_parser("validate-portfolio")
    portfolio.add_argument("--portfolio", type=Path, required=True)
    aggregate_parser = commands.add_parser("aggregate")
    aggregate_parser.add_argument("--manifest", type=Path, required=True)
    aggregate_parser.add_argument("--reports-root", type=Path, required=True)
    aggregate_parser.add_argument("--campaign-instance", required=True)
    aggregate_parser.add_argument("--source-sha", required=True)
    aggregate_parser.add_argument("--output-json", type=Path, required=True)
    aggregate_parser.add_argument("--output-md", type=Path, required=True)
    return parser


def main() -> None:
    args = _parser().parse_args()
    if args.command == "validate":
        data = validate_manifest(args.manifest)
        print(json.dumps({"status": "VALID", "campaign_id": data["campaign_id"], "manifest_sha256": sha256(args.manifest)}, ensure_ascii=False))
        return
    if args.command == "matrix":
        print(json.dumps(build_matrix(args.manifest, source_sha=args.source_sha, campaign_instance=args.campaign_instance, confirmation=args.confirmation), ensure_ascii=False, separators=(",", ":")))
        return
    if args.command == "validate-reuse":
        result = validate_materialized_reuse(args.manifest, slot=args.slot, root_dir=args.root_dir, source_dir=args.source_dir, m01_dir=args.m01_dir)
        print(json.dumps(result, ensure_ascii=False, sort_keys=True))
        return
    if args.command == "validate-portfolio":
        result = validate_portfolio_contract(_load(args.portfolio))
        print(json.dumps(result, ensure_ascii=False, sort_keys=True))
        raise SystemExit(0 if result["valid"] else 2)

    summary = aggregate(args.manifest, args.reports_root, campaign_instance=args.campaign_instance, source_sha=args.source_sha)
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_markdown(summary, args.output_md)
    print(json.dumps(summary, ensure_ascii=False))
    raise SystemExit(0 if summary["status"] == "PASS" else 2)


if __name__ == "__main__":
    main()
