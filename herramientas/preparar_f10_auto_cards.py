#!/usr/bin/env python3
"""Materialize F10 card overlays for the existing ddd auto controller.

This is a deterministic adapter only: it does not select, execute, or orchestrate tasks.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from herramientas.validar_f10_auto_task import CARDS, EXPECTED, validate


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def materialize(repo: Path, launcher: Path, plan_source: Path, output: Path) -> dict:
    repo, launcher, plan_source, output = map(Path.resolve, (repo, launcher, plan_source, output))
    if output.exists() and any(output.iterdir()):
        raise ValueError("Salida no vacía; preservar overlays/checkpoints existentes")
    cards_path = repo / CARDS
    registry = json.loads(cards_path.read_text(encoding="utf-8"))
    if registry.get("schema") != "ddd.f10-auto-task-cards/1.0":
        raise ValueError("Schema de fichas F10 desconocido")
    if {card.get("id") for card in registry.get("cards", [])} != set(EXPECTED):
        raise ValueError("El lote debe contener exactamente las cuatro fichas electorales F10")
    catalog = json.loads((launcher / "catalogo.json").read_text(encoding="utf-8"))
    policy = json.loads((launcher / "auto-policy.json").read_text(encoding="utf-8"))
    plan = json.loads((plan_source / "estado.json").read_text(encoding="utf-8"))
    catalog_ids = {task["id"] for task in catalog["tasks"]}
    plan_ids = {task["id"] for task in plan["tasks"]}
    if catalog_ids != plan_ids:
        raise ValueError("Catálogo y Plan fuente no tienen el mismo universo de tareas")
    for card in registry["cards"]:
        task_id = card["id"]
        if task_id in catalog_ids or task_id in plan_ids or task_id in policy.get("tasks", {}):
            raise ValueError(f"La tarea ya existe en el controlador/Plan: {task_id}")
        validate(repo, task_id)
        task = {
            "id": task_id,
            "front": "fuentes-oficiales",
            "title": card["title"],
            "depends_on": [],
            "execution": "codex",
            "acceptance": card["acceptance"],
            "initial_status": "PENDING",
            "technical_status": "UNRECONCILED",
            "origin": "proposed_extension:f10_20261013",
            "origin_date": "2026-10-13",
            "aliases": [],
            "dedup_targets": [],
            "preparation_dependencies": [],
            "acceptance_dependencies": [],
            "integration_dependencies": [],
            "production_dependencies": [],
            "artifact_requirements": [],
            "authority_class": "local_read_only",
            "reserved": False,
            "prompt_file": None,
            "priority": 20,
            "estimated_seconds": 600,
            "resource_class": "local",
            "evidence_pointers": [item["path"] for item in card["evidence"]],
            "context": card["context"],
        }
        catalog["tasks"].append(task)
        plan["tasks"].append({
            "id": task_id, "status": "PENDING", "front": "fuentes-oficiales",
            "depends_on": [], "acceptance": card["acceptance"], "execution": "codex",
        })
        policy.setdefault("tasks", {})[task_id] = card["spec"]
    output.mkdir(parents=True, exist_ok=True)
    (output / "plan").mkdir()
    (output / "runtime").mkdir()
    (output / "catalogo.json").write_text(json.dumps(catalog, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (output / "auto-policy.json").write_text(json.dumps(policy, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (output / "plan" / "estado.json").write_text(json.dumps(plan, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    shutil_plan_catalog = plan_source / "catalogo.json"
    if shutil_plan_catalog.is_file():
        (output / "plan" / "catalogo.json").write_bytes(shutil_plan_catalog.read_bytes())
    manifest = {
        "schema": "ddd.f10-auto-card-materialization/1.0",
        "cards_sha256": digest(cards_path),
        "launcher_catalog_sha256": digest(launcher / "catalogo.json"),
        "launcher_policy_sha256": digest(launcher / "auto-policy.json"),
        "plan_state_sha256": digest(plan_source / "estado.json"),
        "task_ids": sorted(EXPECTED),
        "controller": "existing ddd auto; invoked separately by operator",
        "network": False,
        "production": False,
        "writes_to_authoritative_plan": False,
    }
    (output / "materializacion.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return manifest


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--launcher", type=Path, required=True)
    parser.add_argument("--plan-source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        print(json.dumps(materialize(args.repo, args.launcher, args.plan_source, args.output), ensure_ascii=False, indent=2))
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
        parser.error(str(exc))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
