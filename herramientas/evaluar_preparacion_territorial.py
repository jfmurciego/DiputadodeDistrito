#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PROYECTO: Diputado de Distrito
COMPONENTE: evaluación automática de preparación territorial
VERSIÓN: 1.1.0
NOMBRE DE VERSIÓN: Igualdad estricta y validación de contenido
FECHA: 2026-09-17
ESTADO: candidato
FUNCIÓN: bloquear o aprobar la preparación de fuentes antes de cualquier módulo territorial.
CAMBIOS: compara declaración resuelta, inventario y procedencia campo a campo y revalida población, cobertura y artefactos consumibles.
MOTIVO: impedir que una evidencia parcial o incoherente habilite producción.
ANTERIOR: legacy/herramientas/evaluar_preparacion_territorial_v1.0.0.py
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import zipfile
from pathlib import Path

import yaml

CORE_FIELDS = ("source_id", "path", "sha256", "bytes", "urls", "edition")


def load_yaml(path: Path) -> dict:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"Documento YAML no válido: {path}")
    return data


def _resolve(root_dir: Path, configured: str) -> Path:
    path = Path(configured)
    return path if path.is_absolute() else root_dir / path


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _core(row: dict) -> dict:
    return {key: row.get(key) for key in CORE_FIELDS}


def _index_sources(document: dict) -> tuple[dict[str, dict], list[str]]:
    rows = document.get("sources")
    if not isinstance(rows, list):
        return {}, ["Documento sin lista sources"]
    indexed: dict[str, dict] = {}
    errors: list[str] = []
    for row in rows:
        if not isinstance(row, dict) or not row.get("source_id"):
            errors.append("Fuente sin source_id estable")
            continue
        source_id = str(row["source_id"])
        if source_id in indexed:
            errors.append(f"source_id duplicado: {source_id}")
        indexed[source_id] = row
    return indexed, errors


def _csv_payload(path: Path) -> bytes:
    payload = path.read_bytes()
    bio = io.BytesIO(payload)
    if zipfile.is_zipfile(bio):
        with zipfile.ZipFile(bio) as zf:
            members = [n for n in zf.namelist() if n.lower().endswith((".csv", ".tsv", ".txt")) and "__macosx/" not in n.lower()]
            if not members:
                raise ValueError("ZIP de población sin CSV")
            payload = zf.read(members[0])
    prefix = payload[:2048].lstrip().lower()
    if prefix.startswith(b"<html") or prefix.startswith(b"<!doctype html") or b"<body" in prefix:
        raise ValueError("HTML detectado en lugar de CSV")
    return payload


def _delimiter(text: str) -> str:
    first = text.splitlines()[0] if text.splitlines() else ""
    counts = {d: first.count(d) for d in ("\t", ";", ",")}
    delim = max(counts, key=counts.get)
    if counts[delim] == 0:
        raise ValueError("CSV sin delimitador reconocible")
    return delim


def _section_id(value: object) -> str:
    digits = "".join(ch for ch in str(value or "") if ch.isdigit())
    if not digits:
        return ""
    return digits.zfill(10)[:10]


def _validate_population(path: Path, declaration: dict, edition: int, expected_provinces: set[str]) -> dict:
    payload = _csv_payload(path)
    text = payload.decode("utf-8-sig")
    delim = _delimiter(text)
    reader = csv.DictReader(io.StringIO(text), delimiter=delim)
    rules = declaration.get("population_validation") or {}
    required = [str(x) for x in (rules.get("required_columns") or ["Periodo", "Sexo", "Edad", "Secciones", "Total"])]
    if not reader.fieldnames:
        raise ValueError("CSV de población sin cabecera")
    missing = [col for col in required if col not in reader.fieldnames]
    if missing:
        raise ValueError("Faltan columnas obligatorias: " + ", ".join(missing))
    year_col = str(rules.get("year_col") or "Periodo")
    sex_col = str(rules.get("sex_col") or "Sexo")
    age_col = str(rules.get("age_col") or "Edad")
    section_col = str(rules.get("section_col") or "Secciones")
    sex_values = {str(x) for x in (rules.get("sex_total_values") or ["Total"])}
    age_values = {str(x) for x in (rules.get("age_total_values") or ["Todas las edades"])}
    provinces: set[str] = set()
    rows = 0
    for row in reader:
        if str(row.get(year_col, "")).strip() != str(edition):
            raise ValueError(f"Edición incorrecta en población: {row.get(year_col)!r}; esperada {edition}")
        if str(row.get(sex_col, "")).strip() not in sex_values:
            raise ValueError("La población materializada contiene filas fuera del filtro Sexo=Total")
        if str(row.get(age_col, "")).strip() not in age_values:
            raise ValueError("La población materializada contiene filas fuera del filtro Edad=Todas las edades")
        sid = _section_id(row.get(section_col))
        if not sid:
            raise ValueError("Fila de población materializada sin sección censal")
        provinces.add(sid[:2])
        rows += 1
    if rows == 0:
        raise ValueError("CSV de población materializado vacío")
    if provinces != expected_provinces:
        raise ValueError(f"Provincias de población {sorted(provinces)} != declaradas {sorted(expected_provinces)}")
    return {"rows": rows, "provinces": sorted(provinces), "edition": edition}


def _validate_sections(path: Path, expected_provinces: set[str], expected_sections: int = 0) -> dict:
    if not path.is_file():
        raise FileNotFoundError(f"No existe el seccionado materializado: {path}")
    if path.suffix.lower() == ".zip":
        with zipfile.ZipFile(path) as zf:
            shp_members = [n for n in zf.namelist() if n.lower().endswith(".shp") and "__macosx/" not in n.lower()]
            if not shp_members:
                raise ValueError("El seccionado consumible no contiene .shp")
        try:
            import geopandas as gpd
        except Exception as exc:  # pragma: no cover
            raise RuntimeError(f"geopandas es obligatorio para evaluar secciones: {exc}")
        gdf = gpd.read_file(f"zip://{path}")
    else:
        import geopandas as gpd
        gdf = gpd.read_file(path)
    if "CPRO" not in gdf.columns:
        raise ValueError("Seccionado sin columna CPRO")
    provinces = set(gdf["CPRO"].astype(str).str.zfill(2).unique())
    if provinces != expected_provinces:
        raise ValueError(f"Provincias de secciones {sorted(provinces)} != declaradas {sorted(expected_provinces)}")
    if expected_sections and len(gdf) != expected_sections:
        raise ValueError(f"Secciones materializadas {len(gdf)} != esperadas {expected_sections}")
    return {"sections": len(gdf), "provinces": sorted(provinces)}


def evaluate(*, catalog: dict, declaration: dict, resolved_declaration: dict | None, inventory: dict | None, provenance: dict | None, environment: str, root_dir: Path | None = None, acquisition_decision: dict | None = None) -> dict:
    root_dir = (root_dir or Path.cwd()).resolve()
    territory = declaration.get("territory") or {}
    territory_id = str(territory.get("id") or "")
    territory_name = str(territory.get("business_name") or "Territorio sin nombre")
    edition = territory.get("edition")
    provinces = {str(row.get("code")).zfill(2) for row in (territory.get("territorial_codes") or []) if isinstance(row, dict)}
    required = [str(x) for x in (declaration.get("required_sources") or [])]
    reasons: list[str] = []
    checks = {
        "catalog_complete": True,
        "headers_equal": True,
        "sources_exact": True,
        "artifacts_exact": True,
        "population_valid": True,
        "province_coverage_exact": True,
        "environment_policy_satisfied": True,
        "acquisition_ready": True,
    }

    catalog_sources = catalog.get("sources") or {}
    for source_id in required:
        source = catalog_sources.get(source_id)
        if not isinstance(source, dict) or source.get("id") != source_id:
            checks["catalog_complete"] = False
            reasons.append(f"Fuente requerida no catalogada o con id inestable: {source_id}")

    if not resolved_declaration or not inventory or not provenance:
        checks["headers_equal"] = False
        checks["sources_exact"] = False
        reasons.append("Falta declaración resuelta, inventario o manifiesto de procedencia")
        mode = None
    else:
        mode = inventory.get("acquisition_mode")
        expected_header = {"territory_id": territory_id, "territory": territory_name, "edition": edition, "environment": environment, "acquisition_mode": mode}
        for document_name, document in (("declaración", resolved_declaration), ("inventario", inventory), ("procedencia", provenance)):
            for key, expected in expected_header.items():
                if document.get(key) != expected:
                    checks["headers_equal"] = False
                    reasons.append(f"{document_name}: {key}={document.get(key)!r} no coincide con {expected!r}")

        allowed = (declaration.get("environment_policy") or {}).get(environment) or []
        if mode not in allowed or (mode == "simulated" and environment != "test"):
            checks["environment_policy_satisfied"] = False
            reasons.append(f"Modo {mode!r} no permitido en {environment}")

        docs = []
        for name, document in (("declaración", resolved_declaration), ("inventario", inventory), ("procedencia", provenance)):
            idx, errors = _index_sources(document)
            docs.append((name, idx))
            for error in errors:
                checks["sources_exact"] = False
                reasons.append(f"{name}: {error}")
        expected_ids = set(required)
        for name, idx in docs:
            if set(idx) != expected_ids:
                checks["sources_exact"] = False
                reasons.append(f"{name}: fuentes {sorted(idx)} != requeridas {sorted(expected_ids)}")
        if all(set(idx) == expected_ids for _, idx in docs):
            ref = docs[0][1]
            for source_id in required:
                ref_core = _core(ref[source_id])
                for name, idx in docs[1:]:
                    if _core(idx[source_id]) != ref_core:
                        checks["sources_exact"] = False
                        reasons.append(f"{source_id}: {name} no coincide exactamente en id/ruta/huella/bytes/URLs/edición")
                inv_row = docs[1][1][source_id]
                if inv_row.get("availability") != "AVAILABLE":
                    checks["acquisition_ready"] = False
                    reasons.append(f"{source_id}: fuente no disponible")
                path_value = ref_core.get("path")
                if path_value:
                    path = _resolve(root_dir, str(path_value))
                    if not path.is_file():
                        checks["artifacts_exact"] = False
                        reasons.append(f"{source_id}: no existe {path_value}")
                    else:
                        actual_hash = _sha256(path)
                        actual_bytes = path.stat().st_size
                        if actual_hash != ref_core.get("sha256") or actual_bytes != ref_core.get("bytes"):
                            checks["artifacts_exact"] = False
                            reasons.append(f"{source_id}: huella o bytes reales no coinciden con la evidencia")

        bindings = declaration.get("source_bindings") or {}
        pop_ids = [sid for sid in required if (catalog_sources.get(sid) or {}).get("kind") == "static_csv"]
        section_ids = [sid for sid in required if (catalog_sources.get(sid) or {}).get("kind") == "ogc_features"]
        for source_id in pop_ids:
            try:
                path = _resolve(root_dir, str((bindings.get(source_id) or {}).get("materialized_path") or ""))
                _validate_population(path, declaration, int(edition), provinces)
            except Exception as exc:
                checks["population_valid"] = False
                checks["province_coverage_exact"] = False
                reasons.append(f"{source_id}: {exc}")
        expected_sections = int((declaration.get("coverage_checks") or {}).get("expected_sections", 0) or 0)
        for source_id in section_ids:
            try:
                path = _resolve(root_dir, str((bindings.get(source_id) or {}).get("materialized_path") or ""))
                _validate_sections(path, provinces, expected_sections)
            except Exception as exc:
                checks["province_coverage_exact"] = False
                reasons.append(f"{source_id}: {exc}")

    if acquisition_decision and acquisition_decision.get("decision") != "READY":
        checks["acquisition_ready"] = False
        reasons.append("La adquisición terminó bloqueada")

    decision = "READY" if all(checks.values()) and not reasons else "BLOCKED"
    return {"schema": "ddd-territory-readiness/1.1", "territory_id": territory_id, "territory": territory_name, "edition": edition, "environment": environment, "acquisition_mode": mode, "decision": decision, "checks": checks, "reasons": reasons}


def readable_report(decision: dict) -> str:
    status = "LISTO" if decision["decision"] == "READY" else "BLOQUEADO"
    lines = [
        f"# Preparación territorial — {decision['territory']}",
        "",
        f"- Identificador: `{decision['territory_id']}`",
        f"- Edición: {decision['edition']}",
        f"- Entorno: {decision['environment']}",
        f"- Modo: {decision.get('acquisition_mode') or 'sin evidencia'}",
        f"- Estado: **{status}**",
        "",
        "## Comprobaciones",
    ]
    for key, value in decision["checks"].items():
        lines.append(f"- {key}: {'PASS' if value else 'BLOCK'}")
    if decision["reasons"]:
        lines.extend(["", "## Bloqueos"])
        lines.extend(f"- {reason}" for reason in decision["reasons"])
    return "\n".join(lines) + "\n"


def _read_json(path: Path) -> dict | None:
    return json.loads(path.read_text(encoding="utf-8")) if path.is_file() else None


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--catalog", type=Path, default=Path("fuentes/catalogo_oficial.yaml"))
    parser.add_argument("--territory", type=Path, required=True)
    parser.add_argument("--evidence-dir", type=Path, required=True)
    parser.add_argument("--environment", choices=["development", "test", "production"], required=True)
    parser.add_argument("--root-dir", type=Path, default=Path("."))
    args = parser.parse_args()
    catalog = load_yaml(args.catalog)
    declaration = load_yaml(args.territory)
    evidence = args.evidence_dir
    decision = evaluate(
        catalog=catalog,
        declaration=declaration,
        resolved_declaration=_read_json(evidence / "declaracion_materializacion.json"),
        inventory=_read_json(evidence / "inventario_fuentes.json"),
        provenance=_read_json(evidence / "manifiesto_procedencia.json"),
        environment=args.environment,
        root_dir=args.root_dir,
        acquisition_decision=_read_json(evidence / "decision_adquisicion.json"),
    )
    evidence.mkdir(parents=True, exist_ok=True)
    (evidence / "decision_preparacion.json").write_text(json.dumps(decision, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (evidence / "informe_preparacion.md").write_text(readable_report(decision), encoding="utf-8")
    print(f"{decision['territory']}: {decision['decision']}")
    if decision["decision"] != "READY":
        raise SystemExit(2)


if __name__ == "__main__":
    main()
