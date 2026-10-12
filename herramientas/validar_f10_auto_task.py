#!/usr/bin/env python3
"""Deterministic, offline evidence validator for executable F10 research cards."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys


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


def validate(root: Path, task_id: str, cards_path: Path = CARDS) -> dict:
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
        checks.append(check)

    if not evidence_paths or not evidence_paths <= set(spec.get("read_only_paths", [])):
        raise ValueError("Entradas probatorias fuera del alcance READ_ONLY del controlador")
    if not {CARDS.as_posix(), "herramientas/validar_f10_auto_task.py"} <= set(spec["read_only_paths"]):
        raise ValueError("La ficha o el validador no están fijados en el snapshot READ_ONLY")

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
        report = validate(args.repo.resolve(), args.task, args.cards)
        args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
        print(f"BLOCKED: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(report, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
