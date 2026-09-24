#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Resolver genérico de declaraciones de fuentes para pruebas desde cero."""
from __future__ import annotations

import argparse
import json
import unicodedata
from pathlib import Path
import yaml

try:
    from herramientas.catalogo_territorios import load_master, normalize_territory_input
except ModuleNotFoundError:  # ejecución directa como script
    from catalogo_territorios import load_master, normalize_territory_input

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REGISTRY = ROOT / "fuentes/territorios_espana.yaml"
DEFAULT_CATALOG = ROOT / "fuentes/catalogo_oficial.yaml"
DEFAULT_MASTER = ROOT / "configuracion/catalogo_territorios_espana_2025.yaml"


def load_yaml(path: Path) -> dict:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"YAML inválido: {path}")
    return data


def norm(value: str) -> str:
    text = normalize_territory_input(str(value))
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    return " ".join(text.casefold().replace("_", " ").split())


def territories(registry_path: Path = DEFAULT_REGISTRY) -> list[dict]:
    rows = load_yaml(registry_path).get("territories") or []
    if not isinstance(rows, list) or not rows:
        raise ValueError("Registro territorial vacío")
    by_id = {str(row.get("id") or ""): row for row in rows}
    unknown = sorted(set(by_id) - {row["territory_id"] for row in load_master(DEFAULT_MASTER)})
    if unknown:
        raise ValueError(f"Registro de fuentes contiene territorios ajenos al catálogo maestro: {unknown}")
    result = []
    for canonical in load_master(DEFAULT_MASTER):
        row = by_id.get(canonical["territory_id"])
        if row is None:
            continue
        result.append({
            **row,
            "id": canonical["territory_id"],
            "name": canonical["name"],
            "autonomous_community_code_ine": canonical["autonomous_community_code_ine"],
        })
    return result


def resolve_territory(value: str, registry_path: Path = DEFAULT_REGISTRY) -> dict:
    wanted = norm(value)
    for row in territories(registry_path):
        if wanted in {norm(row.get("id", "")), norm(row.get("name", ""))}:
            return row
    raise KeyError(f"Territorio no registrado: {value}")


def build_declaration(territory: str, edition: int, *, registry_path: Path = DEFAULT_REGISTRY,
                      catalog_path: Path = DEFAULT_CATALOG) -> dict:
    row = resolve_territory(territory, registry_path)
    catalog = load_yaml(catalog_path)
    sources = catalog.get("sources") or {}
    required = list(sources)
    if not required:
        raise ValueError("Catálogo de fuentes vacío")
    codes = [str(x).zfill(2) for x in row.get("province_codes") or []]
    if not codes:
        raise ValueError(f"{row['name']} no declara provincias")
    bindings = {}
    for source_id in required:
        source = sources[source_id]
        if source.get("kind") == "static_csv":
            bindings[source_id] = {
                "materialized_path": f"inputs/{source.get('output_name','source.csv')}.zip",
                "archive_member": source.get("output_name", "source.csv"),
            }
        elif source.get("kind") == "ogc_features":
            bindings[source_id] = {
                "materialized_path": f"inputs/seccionado_{edition}.zip",
            }
        else:
            raise ValueError(f"Tipo de fuente no soportado por el test: {source.get('kind')}")
    return {
        "schema": "ddd-territory-sources/1.1",
        "territory": {
            "id": row["id"],
            "business_name": row["name"],
            "edition": int(edition),
            "territorial_codes": [{"code": c, "business_name": c} for c in codes],
        },
        "required_sources": required,
        "source_bindings": bindings,
        "population_validation": {
            "required_columns": ["Periodo", "Sexo", "Edad", "Secciones", "Total"],
            "year_col": "Periodo",
            "sex_col": "Sexo",
            "age_col": "Edad",
            "section_col": "Secciones",
            "population_col": "Total",
            "sex_total_values": ["Total"],
            "age_total_values": ["Todas las edades"],
        },
        "coverage_checks": {"required_territorial_codes": codes},
        "default_mode": {"development": "official_live", "test": "official_live", "production": "official_live"},
        "environment_policy": {
            "development": ["official_live"],
            "test": ["official_live"],
            "production": ["official_live"],
        },
    }


def matrix(territory: str, registry_path: Path = DEFAULT_REGISTRY) -> list[str]:
    if norm(territory) == "todos":
        return [row["name"] for row in territories(registry_path)]
    return [resolve_territory(territory, registry_path)["name"]]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("command", choices=["list", "matrix", "declaration"])
    ap.add_argument("--territory", default="Todos")
    ap.add_argument("--edition", default="2025")
    ap.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY)
    ap.add_argument("--catalog", type=Path, default=DEFAULT_CATALOG)
    ap.add_argument("--output", type=Path)
    args = ap.parse_args()

    if args.command == "list":
        print(json.dumps([r["name"] for r in territories(args.registry)], ensure_ascii=False))
        return 0
    if args.command == "matrix":
        print(json.dumps(matrix(args.territory, args.registry), ensure_ascii=False))
        return 0

    declaration = build_declaration(
        args.territory, int(args.edition), registry_path=args.registry, catalog_path=args.catalog
    )
    rendered = yaml.safe_dump(declaration, allow_unicode=True, sort_keys=False)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
