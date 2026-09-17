#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PROYECTO: Diputado de Distrito
COMPONENTE: evaluación automática de preparación territorial
VERSIÓN: 1.0.0
NOMBRE DE VERSIÓN: Puerta declarativa de fuentes
FECHA: 2026-09-17
ESTADO: candidato
FUNCIÓN: evaluar catálogo, política de entorno, cobertura y procedencia sin ejecutar módulos territoriales.
CAMBIOS: genera decisión estructurada e informe legible a partir de evidencia de adquisición.
MOTIVO: separar preparación de fuentes de la ejecución M01-M06 y hacerla auditable.
ANTERIOR: herramientas/calcular_clave_preparacion.py
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import yaml


def load_yaml(path: Path) -> dict:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"Documento YAML no válido: {path}")
    return data


def evaluate(*, catalog: dict, declaration: dict, inventory: dict | None, provenance: dict | None, environment: str) -> dict:
    territory = declaration.get("territory") or {}
    territory_name = str(territory.get("business_name") or "Territorio sin nombre")
    required = declaration.get("required_sources") or []
    sources = catalog.get("sources") or {}
    allowed = (declaration.get("environment_policy") or {}).get(environment) or []
    reasons: list[str] = []

    missing_catalog = [name for name in required if name not in sources]
    if missing_catalog:
        reasons.append("Faltan fuentes requeridas en el catálogo oficial")

    if not inventory or not provenance:
        reasons.append("Falta evidencia materializada de fuentes oficiales")
        mode = None
    else:
        mode = inventory.get("acquisition_mode")
        if mode not in allowed:
            reasons.append("La procedencia materializada no está permitida en este entorno")
        available = {
            row.get("business_name")
            for row in inventory.get("sources", [])
            if row.get("availability") == "AVAILABLE"
        }
        required_business = [
            sources[name].get("business_name")
            for name in required
            if isinstance(sources.get(name), dict)
        ]
        edition = territory.get("edition")
        if any(name not in available and f"{name} {edition}" not in available for name in required_business):
            reasons.append("No están disponibles todas las fuentes oficiales requeridas")
        expected_sections = int((declaration.get("coverage_checks") or {}).get("expected_sections", 0) or 0)
        if expected_sections:
            section_rows = [
                row for row in inventory.get("sources", [])
                if str(row.get("business_name", "")).startswith("Secciones censales")
            ]
            if not section_rows or int(section_rows[0].get("sections", -1)) != expected_sections:
                reasons.append("La cobertura de secciones censales no coincide con la declarada")
        prov_names = {row.get("business_name") for row in provenance.get("sources", [])}
        inv_names = {row.get("business_name") for row in inventory.get("sources", [])}
        if prov_names != inv_names:
            reasons.append("Inventario y manifiesto de procedencia no describen las mismas fuentes")
        for row in provenance.get("sources", []):
            if not row.get("sha256") or not row.get("urls"):
                reasons.append("Hay una fuente sin checksum o URL de procedencia")
                break

    decision = "READY" if not reasons else "BLOCKED"
    return {
        "schema": "ddd-territory-readiness/1.0",
        "territory": territory_name,
        "edition": territory.get("edition"),
        "environment": environment,
        "decision": decision,
        "acquisition_mode": mode,
        "checks": {
            "catalog_complete": not missing_catalog,
            "environment_policy_satisfied": mode in allowed if mode else False,
            "evidence_present": bool(inventory and provenance),
            "coverage_satisfied": not any("cobertura" in reason.lower() for reason in reasons),
            "traceability_satisfied": not any("checksum" in reason.lower() or "procedencia" in reason.lower() for reason in reasons),
        },
        "reasons": reasons,
    }


def readable_report(decision: dict) -> str:
    status = "LISTO" if decision["decision"] == "READY" else "BLOQUEADO"
    lines = [
        f"# Preparación territorial — {decision['territory']}",
        "",
        f"- Edición: {decision['edition']}",
        f"- Entorno: {decision['environment']}",
        f"- Estado: **{status}**",
        f"- Procedencia: {decision.get('acquisition_mode') or 'sin evidencia'}",
        "",
        "## Comprobaciones",
    ]
    labels = {
        "catalog_complete": "Catálogo oficial completo",
        "environment_policy_satisfied": "Política de entorno satisfecha",
        "evidence_present": "Evidencia materializada presente",
        "coverage_satisfied": "Cobertura territorial satisfecha",
        "traceability_satisfied": "Trazabilidad y checksum presentes",
    }
    for key, label in labels.items():
        lines.append(f"- {label}: {'sí' if decision['checks'][key] else 'no'}")
    if decision["reasons"]:
        lines.extend(["", "## Bloqueos"])
        lines.extend(f"- {reason}" for reason in decision["reasons"])
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--catalog", type=Path, default=Path("fuentes/catalogo_oficial.yaml"))
    parser.add_argument("--territory", type=Path, required=True)
    parser.add_argument("--evidence-dir", type=Path, required=True)
    parser.add_argument("--environment", choices=["development", "test", "production"], required=True)
    args = parser.parse_args()
    catalog = load_yaml(args.catalog)
    declaration = load_yaml(args.territory)
    inventory_path = args.evidence_dir / "inventario_fuentes.json"
    provenance_path = args.evidence_dir / "manifiesto_procedencia.json"
    inventory = json.loads(inventory_path.read_text(encoding="utf-8")) if inventory_path.exists() else None
    provenance = json.loads(provenance_path.read_text(encoding="utf-8")) if provenance_path.exists() else None
    decision = evaluate(catalog=catalog, declaration=declaration, inventory=inventory, provenance=provenance, environment=args.environment)
    args.evidence_dir.mkdir(parents=True, exist_ok=True)
    (args.evidence_dir / "decision_preparacion.json").write_text(json.dumps(decision, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (args.evidence_dir / "informe_preparacion.md").write_text(readable_report(decision), encoding="utf-8")
    print(f"{decision['territory']}: {decision['decision']}")


if __name__ == "__main__":
    main()
