#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

CONFIRMATION = "EXECUTE_CAMPAIGN_CONFIRMED"
EXPECTED_FIELDS = {
    "schema": "ddd.campaign-manifest/1.0",
    "data_edition": "2025",
    "execution_mode": "Reutilizar progreso existente",
    "optimization_algorithm": "GerryChain 50",
    "candidate_count": 50,
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


def _load(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("El manifiesto de campaña debe ser un objeto JSON")
    return data


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate_manifest(path: Path) -> dict:
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
    return data


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
) -> dict:
    data = validate_manifest(path)
    if confirmation != CONFIRMATION:
        raise ValueError("Confirmación explícita incorrecta")
    if len(source_sha) != 40 or any(
        ch not in "0123456789abcdef" for ch in source_sha.lower()
    ):
        raise ValueError("source_sha debe ser un SHA Git completo de 40 hexadecimales")
    digest = sha256(path)
    include = []
    for territory in data["territories"]:
        slot = territory["slot"]
        territory_id = territory["territory_id"]
        namespace = f"{campaign_instance}/{slot}/{territory_id}"
        include.append(
            {
                "campaign_instance": campaign_instance,
                "slot": slot,
                "territory_id": territory_id,
                "territory_name": territory["territory_name"],
                "namespace": namespace,
                "artifact_namespace": artifact_namespace(
                    campaign_instance, slot, territory_id
                ),
                "source_sha": source_sha.lower(),
                "manifest_sha256": digest,
                "data_edition": data["data_edition"],
                "execution_mode": data["execution_mode"],
                "optimization_algorithm": data["optimization_algorithm"],
                "candidate_count": data["candidate_count"],
                "publication_mode": territory["publication_mode"],
                "campaign_confirmation": confirmation,
                "retry_failed": data["retry_failed"],
            }
        )
    return {"include": include}


def aggregate(
    path: Path,
    reports_root: Path,
    *,
    campaign_instance: str,
    source_sha: str,
) -> dict:
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
            item = dict(row)
            mismatches = []
            if row.get("slot") != territory["slot"]:
                mismatches.append("slot")
            if row.get("publication_mode") != territory["publication_mode"]:
                mismatches.append("publication_mode")
            if row.get("source_sha") != source_sha:
                mismatches.append("source_sha")
            if row.get("manifest_sha256") != digest:
                mismatches.append("manifest_sha256")
            if row.get("candidate_count_expected") != 50:
                mismatches.append("candidate_count_expected")
            if mismatches:
                item["status"] = "FAIL"
                item["reason"] = "Identidad inconsistente: " + ", ".join(mismatches)
        rows.append(item)
        if item.get("status") != "PASS":
            failed.append(territory_id)

    return {
        "schema": "ddd.campaign-summary/1.0",
        "campaign_id": data["campaign_id"],
        "campaign_instance": campaign_instance,
        "source_sha": source_sha,
        "manifest_sha256": digest,
        "territory_count_expected": 5,
        "territory_count_reported": len(reports),
        "failed_territories": failed,
        "status": "PASS" if not failed else "FAIL",
        "territories": rows,
    }


def write_markdown(summary: dict, path: Path) -> None:
    lines = [
        "# Campaña " + summary["campaign_instance"],
        "",
        "- estado: " + summary["status"],
        "- source SHA: " + summary["source_sha"],
        "- manifest SHA-256: " + summary["manifest_sha256"],
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


def main() -> None:
    parser = argparse.ArgumentParser()
    commands = parser.add_subparsers(dest="command", required=True)
    validate = commands.add_parser("validate")
    validate.add_argument("--manifest", type=Path, required=True)
    matrix = commands.add_parser("matrix")
    matrix.add_argument("--manifest", type=Path, required=True)
    matrix.add_argument("--source-sha", required=True)
    matrix.add_argument("--campaign-instance", required=True)
    matrix.add_argument("--confirmation", required=True)
    aggregate_parser = commands.add_parser("aggregate")
    aggregate_parser.add_argument("--manifest", type=Path, required=True)
    aggregate_parser.add_argument("--reports-root", type=Path, required=True)
    aggregate_parser.add_argument("--campaign-instance", required=True)
    aggregate_parser.add_argument("--source-sha", required=True)
    aggregate_parser.add_argument("--output-json", type=Path, required=True)
    aggregate_parser.add_argument("--output-md", type=Path, required=True)
    args = parser.parse_args()

    if args.command == "validate":
        data = validate_manifest(args.manifest)
        print(
            json.dumps(
                {
                    "status": "VALID",
                    "campaign_id": data["campaign_id"],
                    "manifest_sha256": sha256(args.manifest),
                },
                ensure_ascii=False,
            )
        )
        return

    if args.command == "matrix":
        print(
            json.dumps(
                build_matrix(
                    args.manifest,
                    source_sha=args.source_sha,
                    campaign_instance=args.campaign_instance,
                    confirmation=args.confirmation,
                ),
                ensure_ascii=False,
                separators=(",", ":"),
            )
        )
        return

    summary = aggregate(
        args.manifest,
        args.reports_root,
        campaign_instance=args.campaign_instance,
        source_sha=args.source_sha,
    )
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    write_markdown(summary, args.output_md)
    print(json.dumps(summary, ensure_ascii=False))
    raise SystemExit(0 if summary["status"] == "PASS" else 2)


if __name__ == "__main__":
    main()
