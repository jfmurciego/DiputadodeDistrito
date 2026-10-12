#!/usr/bin/env python3
# Versión: 1.0.0; nombre: Validador determinista de tareas F10; fecha: 2026-10-13.
# Alcance: verificar evidencias locales fijadas y entregas estructuradas READ_ONLY.
# Estado: candidato. Cambios/motivo: validar las cuatro fichas F10 ejecutables.
# Anterior: no existía validador de fichas F10; predecesor histórico no recuperado.
"""Deterministic, offline evidence validator for executable F10 research cards."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import yaml


CARDS = Path("configuracion/f10_auto_tareas.json")
EXPECTED = {
    "F10-AND-CROSSWALK-2025-2026": "BLOCKED_CROSSWALK_NOT_PROVEN",
    "F10-ARA-CROSSWALK-2025-2026": "BLOCKED_CROSSWALK_NOT_PROVEN",
    "F10-CYL-CROSSWALK-2025-2026": "BLOCKED_CROSSWALK_NOT_PROVEN",
    "F10-EXT-ELECTORAL-SOURCE": "BLOCKED_FINAL_GRANULAR_SOURCE",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def card_for(root: Path, task_id: str, cards_path: Path = CARDS) -> dict:
    catalog = json.loads((root / cards_path).read_text(encoding="utf-8"))
    if catalog.get("schema") != "ddd.f10-auto-task-cards/1.0":
        raise ValueError("Esquema de fichas F10 desconocido")
    matches = [card for card in catalog.get("cards", []) if card.get("id") == task_id]
    if len(matches) != 1 or task_id not in EXPECTED:
        raise ValueError("Ficha F10 ausente, duplicada o no admitida")
    return matches[0]


def dotted(value, key):
    for part in key.split("."):
        if not isinstance(value, dict) or part not in value:
            raise ValueError(f"Campo JSON ausente: {key}")
        value = value[part]
    return value


def validate_executor_summary(card: dict, task_id: str, summary: dict) -> None:
    acceptance = card.get("acceptance", [])
    spec = card.get("spec", {})
    required_evidence = {item["path"] for item in card.get("evidence", [])}
    cited = set(summary.get("evidence", []))
    if (summary.get("task") != task_id or summary.get("status") != "READY_FOR_REVIEW"
            or summary.get("criteria_verified") != acceptance
            or not required_evidence <= cited
            or not cited <= set(spec.get("read_only_paths", []))
            or not summary.get("tests") or not summary.get("limitations")):
        raise ValueError("Salida estructurada no cubre criterios, fuentes y limitaciones de la ficha")
    limitation_text = " ".join(summary["limitations"]).casefold()
    if not any(word in limitation_text for word in ("bloque", "blocked", "no acredit", "no disponible")):
        raise ValueError("La salida no declara el límite electoral pendiente")


def validate(root: Path, task_id: str, cards_path: Path = CARDS,
             summary_path: Path | None = None) -> dict:
    card = card_for(root, task_id, cards_path)
    task = card.get("task", {})
    spec = card.get("spec", {})
    acceptance = card.get("acceptance", [])
    validators = spec.get("validators", [])
    covered = {index for validator in validators for index in validator.get("covers", [])}
    if (task.get("front") != "fuentes-oficiales" or task.get("authority_class") != "local_read_only"
            or task.get("reserved") is not False or task.get("execution") != "codex"
            or task.get("depends_on") != [] or spec.get("work_class") != "READ_ONLY"
            or spec.get("allowed_change_prefixes") != [] or covered != set(range(len(acceptance)))
            or not validators or any(v.get("local_only") is not True or not v.get("argv") for v in validators)):
        raise ValueError("Contrato ejecutable/card no es READ_ONLY completo o desborda su autorización")

    checks = []
    evidence_paths = set()
    for item in card.get("evidence", []):
        relative = Path(item["path"])
        if relative.is_absolute() or ".." in relative.parts:
            raise ValueError("Ruta de evidencia fuera del repositorio")
        evidence_paths.add(relative.as_posix())
        source = root / relative
        actual_hash = sha256(source)
        if actual_hash != item.get("sha256"):
            raise ValueError(f"Hash de evidencia distinto: {relative}")
        check = {"path": relative.as_posix(), "sha256": actual_hash, "identity": "HASH_MATCH"}
        if "json_equals" in item or "json_contains" in item:
            document = json.loads(source.read_text(encoding="utf-8"))
            for key, expected in item.get("json_equals", {}).items():
                if dotted(document, key) != expected:
                    raise ValueError(f"Identidad/valor distinto en {relative}: {key}")
            serialized = json.dumps(document, ensure_ascii=False, sort_keys=True)
            for expected in item.get("json_contains", []):
                if str(expected) not in serialized:
                    raise ValueError(f"Evidencia JSON no contiene {expected}: {relative}")
            check["json_identity"] = "MATCH"
        if "yaml_equals" in item:
            document = yaml.safe_load(source.read_text(encoding="utf-8"))
            for key, expected in item["yaml_equals"].items():
                if dotted(document, key) != expected:
                    raise ValueError(f"Identidad/valor distinto en {relative}: {key}")
            check["yaml_identity"] = "MATCH"
        checks.append(check)

    if not evidence_paths or not evidence_paths <= set(spec.get("read_only_paths", [])):
        raise ValueError("Entradas probatorias fuera del alcance READ_ONLY del controlador")
    if not {CARDS.as_posix(), "herramientas/validar_f10_auto_task.py"} <= set(spec["read_only_paths"]):
        raise ValueError("La ficha o el validador no están fijados en el snapshot READ_ONLY")

    summary_check = "NOT_SUPPLIED"
    if summary_path is not None:
        summary = json.loads(summary_path.read_text(encoding="utf-8"))
        # A technical task can finish while the underlying electoral gate remains blocked.
        validate_executor_summary(card, task_id, summary)
        summary_check = "MATCH"

    computed = []
    if task_id == "F10-ARA-CROSSWALK-2025-2026":
        contract = json.loads((root / "territorios/aragon/config/elecciones/aragon_cortes_2026.json").read_text())
        reconc = contract["reconciliation"]
        result_only = reconc["allowed_result_only_sections"]
        map_only = reconc["allowed_map_only_sections"]
        actual = {"result_only_count": len(result_only), "result_only_votes": sum(row["expected_votes"] for row in result_only),
                  "map_only_count": len(map_only), "result_only_cusec": [row["section_id"] for row in result_only],
                  "map_only_cusec": [row["section_id"] for row in map_only]}
        if actual != {"result_only_count": 1, "result_only_votes": 608, "map_only_count": 1,
                      "result_only_cusec": ["5002501003"], "map_only_cusec": ["2221301003"]}:
            raise ValueError("Excepciones Aragón no reconcilian con el contrato fijado")
        computed.append(actual)
    elif task_id == "F10-CYL-CROSSWALK-2025-2026":
        reconc = json.loads((root / "territorios/castilla_y_leon/evidencia/reconciliacion_secciones_2025_2026.json").read_text())
        actual = {"electoral_only_count": len(reconc["electoral_only"]), "map_only_count": len(reconc["m06_only"]),
                  "electoral_only_votes_sum": sum(reconc["electoral_only_votes"].values()),
                  "declared_electoral_only_votes": reconc["electoral_only_total_votes"],
                  "electoral_sections_minus_common": reconc["electoral_sections"] - reconc["intersection"],
                  "map_sections_minus_common": reconc["m06_sections"] - reconc["intersection"]}
        if actual != {"electoral_only_count": 24, "map_only_count": 2, "electoral_only_votes_sum": 15656,
                      "declared_electoral_only_votes": 15656, "electoral_sections_minus_common": 24,
                      "map_sections_minus_common": 2}:
            raise ValueError("Recuentos Castilla y León no concilian")
        computed.append(actual)
    elif task_id == "F10-EXT-ELECTORAL-SOURCE":
        blocked = json.loads((root / "territorios/extremadura/config/elecciones/bloqueo_fuente_oficial_2025.json").read_text())
        definite = blocked["definitive_reconciliation_reference"]["candidate_votes"]
        provisional = blocked["provisional_granular_evidence"]["candidate_votes"]
        actual = {"definitive_votes": definite, "provisional_votes": provisional,
                  "computed_delta": definite - provisional,
                  "declared_delta": blocked["delta_definitive_minus_provisional"]}
        if actual != {"definitive_votes": 524837, "provisional_votes": 522418,
                      "computed_delta": 2419, "declared_delta": 2419}:
            raise ValueError("Total o delta Extremadura no reconcilia con el expediente")
        computed.append(actual)
    elif task_id == "F10-AND-CROSSWALK-2025-2026":
        contract_path = root / "configuracion/adquisiciones_electorales_especiales.yaml"
        contract = yaml.safe_load(contract_path.read_text(encoding="utf-8"))
        acquisition = contract["acquisitions"]["andalucia_parlamento_2026"]
        actual = {"source_status": acquisition["source_status"],
                  "expected_sections": acquisition["provider_config"]["expected_sections"],
                  "official_candidate_votes": acquisition["provider_config"]["official_candidate_votes"],
                  "result_url": acquisition["provider_config"]["official_reference"]}
        if actual != {"source_status": "VERIFIED_OFFICIAL_FINAL", "expected_sections": 6044,
                      "official_candidate_votes": 4157539,
                      "result_url": "https://www.juntadeandalucia.es/boja/2026/115/1"}:
            raise ValueError("Contrato electoral Andalucía no concilia con sus cifras declaradas")
        computed.append(actual)

    state = EXPECTED[task_id]
    return {
        "schema": "ddd.f10-auto-task-validation/1.0",
        "task": task_id,
        "territory_id": card["territory_id"],
        "technical_result": "EVIDENCE_VERIFIED",
        "underlying_electoral_gate": state,
        "acceptance_count": len(acceptance),
        "acceptance_covered": sorted(covered),
        "evidence": checks,
        "recomputed_checks": computed,
        "executor_summary": summary_check,
        "network": False,
        "production": False,
        "promotion": False,
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--task", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--cards", type=Path, default=CARDS)
    args = parser.parse_args(argv)
    try:
        report = validate(args.repo.resolve(), args.task, args.cards,
                          summary_path=args.output.parent / "executor-summary.json")
        args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
        print(f"BLOCKED: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(report, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
