#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PROYECTO: Diputado de Distrito
COMPONENTE: informe de ejecución basado en evidencias
VERSIÓN: 1.0.0
FECHA: 2026-09-17
FUNCIÓN: consolidar artefactos estructurados del workflow en inventario_ejecucion.json e informe_ejecucion.md.
REGLAS: no lee logs ni documentación manual; sólo contexto automático y evidencias publicadas por la ejecución.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

BUSINESS_STEPS = [
    ("Fuentes oficiales", ("inventario_fuentes.json", "decision_preparacion.json")),
    ("Base territorial y población", ("_m01_",)),
    ("Relaciones de vecindad", ("_m02_",)),
    ("Grafo territorial", ("_m03_",)),
    ("Preparación de unidades internas", ("job.json", "M03U")),
    ("Creación de distritos", ("_m04_",)),
    ("Equilibrado de distritos", ("_m05_",)),
    ("Control geográfico", ("contiguedad_geometrica", "production_status.json")),
    ("Incorporación electoral", ("decision_fuente_electoral.json", "_m07_")),
    ("Publicación y visor", ("publicacion_visor.json", "_m08_")),
]


def load_json(path: Path) -> Any | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def all_json(root: Path) -> list[tuple[Path, Any]]:
    rows: list[tuple[Path, Any]] = []
    if not root.exists():
        return rows
    for path in sorted(root.rglob("*.json")):
        value = load_json(path)
        if value is not None:
            rows.append((path, value))
    return rows


def first_by_name(rows: list[tuple[Path, Any]], name: str) -> tuple[Path, Any] | None:
    for path, value in rows:
        if path.name == name:
            return path, value
    return None


def first_contains(rows: list[tuple[Path, Any]], token: str) -> tuple[Path, Any] | None:
    token = token.lower()
    for path, value in rows:
        if token in path.name.lower():
            return path, value
    return None


def get_any(obj: Any, *keys: str, default=None):
    if not isinstance(obj, dict):
        return default
    for key in keys:
        if key in obj and obj[key] is not None:
            return obj[key]
    return default


def find_scalar(obj: Any, keys: set[str]) -> Any | None:
    if isinstance(obj, dict):
        for key, value in obj.items():
            if key in keys and not isinstance(value, (dict, list)):
                return value
        for value in obj.values():
            found = find_scalar(value, keys)
            if found is not None:
                return found
    elif isinstance(obj, list):
        for value in obj:
            found = find_scalar(value, keys)
            if found is not None:
                return found
    return None


def rel(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except Exception:
        return path.as_posix()


def normalize_sources(inventory: Any, provenance: Any) -> list[dict]:
    candidates = []
    for document in (provenance, inventory):
        if isinstance(document, dict) and isinstance(document.get("sources"), list):
            candidates = document["sources"]
            break
    out = []
    for row in candidates:
        if not isinstance(row, dict):
            continue
        urls = row.get("urls")
        if urls is None:
            url = row.get("source_url") or row.get("url") or row.get("official_url")
            urls = [url] if url else []
        out.append({
            "identificador": row.get("source_id") or row.get("id"),
            "edicion": row.get("edition"),
            "ruta": row.get("path"),
            "checksum_sha256": row.get("sha256"),
            "bytes": row.get("bytes"),
            "urls_oficiales": urls,
            "fecha_adquisicion": row.get("acquired_at") or row.get("retrieved_at") or row.get("acquisition_date"),
            "procedencia": row.get("publisher") or row.get("provenance") or row.get("origin"),
        })
    return out


def blockers_from(*documents: Any) -> list[str]:
    values: list[str] = []
    for doc in documents:
        if not isinstance(doc, dict):
            continue
        for key in ("reasons", "blockers", "contract_blockers"):
            raw = doc.get(key)
            if isinstance(raw, list):
                values.extend(str(x) for x in raw if x)
        for key in ("reason", "block_cause", "population_evidence_error"):
            raw = doc.get(key)
            if raw:
                values.append(str(raw))
    return list(dict.fromkeys(values))


def build_inventory(evidence_root: Path, context: dict) -> dict:
    rows = all_json(evidence_root)
    inv_doc = first_by_name(rows, "inventario_fuentes.json")
    prov_doc = first_by_name(rows, "manifiesto_procedencia.json")
    prep_doc = first_by_name(rows, "decision_preparacion.json")
    acquire_doc = first_by_name(rows, "decision_adquisicion.json")
    prod_status_doc = first_by_name(rows, "production_status.json")
    electoral_doc = first_by_name(rows, "decision_fuente_electoral.json")
    publication_doc = first_by_name(rows, "publicacion_visor.json")

    inventory = inv_doc[1] if inv_doc else {}
    provenance = prov_doc[1] if prov_doc else {}
    preparation = prep_doc[1] if prep_doc else {}
    acquisition = acquire_doc[1] if acquire_doc else {}
    production_status = prod_status_doc[1] if prod_status_doc else {}
    electoral_source = electoral_doc[1] if electoral_doc else {}
    publication = publication_doc[1] if publication_doc else {}

    m01 = first_contains(rows, "_m01_informe")
    m04 = first_contains(rows, "_m04_informe")
    m05 = first_contains(rows, "_m05_informe")
    m06 = first_contains(rows, "_m06_informe")
    m07_recon = first_contains(rows, "_m07_reconciliacion")
    geom = next(((p, v) for p, v in rows if isinstance(v, dict) and str(v.get("schema", "")).startswith("ddd.geometric-components-audit")), None)

    m01v = m01[1] if m01 else {}
    m04v = m04[1] if m04 else {}
    m05v = m05[1] if m05 else {}
    m06v = m06[1] if m06 else {}
    m07v = m07_recon[1] if m07_recon else {}
    geomv = geom[1] if geom else {}

    sections = find_scalar(m01v, {"sections", "section_count", "sections_count", "n_sections"})
    population = find_scalar(m01v, {"population_total", "total_population", "population"})
    expected_districts = (find_scalar(m06v, {"expected_districts", "district_count", "districts"}) or find_scalar(m05v, {"expected_districts", "district_count", "districts"}) or find_scalar(m04v, {"expected_districts", "district_count", "districts", "K", "k"}))
    created_districts = find_scalar(m04v, {"district_count", "districts", "K", "k"})
    balanced_districts = find_scalar(m05v, {"district_count", "districts", "K", "k"})

    pop_repair = get_any(m05v, "population_repair", default={})
    pop_decision = get_any(production_status, "population_decision") or get_any(pop_repair, "result")
    pop_outcome = get_any(production_status, "population_outcome")
    geom_decision = get_any(production_status, "geometric_decision") or get_any(geomv, "decision")
    governed_exceptions = get_any(geomv, "governed_exceptions", default=0)
    blocked_districts = get_any(geomv, "blocked_districts", default=0)

    unassigned_votes = find_scalar(m07v, {"unassigned_votes", "votes_unassigned", "unassigned_vote_count", "votos_no_asignados"})
    selected = get_any(electoral_source, "selected_source", default={}) or {}
    artifact_files = sorted(p.relative_to(evidence_root).as_posix() for p in evidence_root.rglob("*") if p.is_file()) if evidence_root.exists() else []
    m08_products = [p for p in artifact_files if "_m08_" in p.lower()]

    reached = []
    for business_name, markers in BUSINESS_STEPS:
        if any(any(marker.lower() in path.lower() for marker in markers) for path in artifact_files):
            reached.append(business_name)
    reached_until = reached[-1] if reached else "No iniciada"

    source_decision = get_any(preparation, "decision") or get_any(acquisition, "decision")
    electoral_decision = get_any(electoral_source, "decision")
    publication_status = get_any(publication, "status")
    blockers = blockers_from(preparation, acquisition, production_status, electoral_source, publication)
    evidence_block = any(str(x).upper() in {"BLOCK", "HARD_BLOCK", "FAIL", "FAILED", "FAILURE"} for x in (source_decision, electoral_decision, get_any(production_status, "decision"), publication_status) if x is not None)
    chain_result = str(context.get("production_job_result") or "")
    if chain_result in {"failure", "cancelled"}:
        evidence_block = True
        if not blockers:
            blockers.append(f"La cadena terminó con estado automático {chain_result}.")
    complete = bool(publication_status == "SUCCESS" or m08_products)
    final_decision = "BLOCK" if evidence_block else ("COMPLETE" if complete else "INCOMPLETE")

    integrity_checks = {}
    for doc in (preparation, m01v):
        if isinstance(doc, dict) and isinstance(doc.get("checks"), dict):
            integrity_checks.update(doc["checks"])

    return {
        "schema": "ddd-execution-inventory/1.0",
        "metadatos": {"territorio_id": context.get("territory_id"), "operacion": context.get("operation"), "run_id": context.get("workflow_run_id"), "intento": context.get("workflow_run_attempt"), "tramo_solicitado": {"desde": context.get("requested_from"), "hasta": context.get("requested_to")}, "resultado_trabajo_cadena": context.get("production_job_result")},
        "progreso": {"ultimo_paso_de_negocio_con_evidencia": reached_until, "pasos_con_evidencia": reached, "artefactos_observados": len(artifact_files)},
        "fuentes_oficiales": {"decision": source_decision, "modo": get_any(inventory, "acquisition_mode"), "edicion": get_any(inventory, "edition"), "fuentes": normalize_sources(inventory, provenance), "evidencias": [rel(x[0], evidence_root) for x in (inv_doc, prov_doc, prep_doc, acquire_doc) if x]},
        "base_territorial_y_poblacion": {"unidades_territoriales": sections, "poblacion_total": population, "controles_integridad": integrity_checks, "evidencia": rel(m01[0], evidence_root) if m01 else None},
        "creacion_y_equilibrado_de_distritos": {"distritos_creados": created_districts, "distritos_equilibrados": balanced_districts, "distritos_esperados": expected_districts, "cumplimiento_poblacional": {"decision": pop_decision, "resultado": pop_outcome, "detalle_reparacion": pop_repair if isinstance(pop_repair, dict) else None}, "evidencia_creacion": rel(m04[0], evidence_root) if m04 else None, "evidencia_equilibrado": rel(m05[0], evidence_root) if m05 else None},
        "control_geografico": {"decision": geom_decision, "distritos_bloqueados": blocked_districts, "excepciones_justificadas": governed_exceptions, "evidencia": rel(geom[0], evidence_root) if geom else (rel(prod_status_doc[0], evidence_root) if prod_status_doc else None)},
        "incorporacion_electoral": {"decision_fuente": electoral_decision, "fuente_seleccionada": {"identificador": selected.get("id"), "url": selected.get("url"), "checksum_sha256": selected.get("sha256"), "bytes": selected.get("bytes"), "resolucion": selected.get("declared_resolution")} if isinstance(selected, dict) else None, "reconciliacion": m07v if isinstance(m07v, dict) else None, "votos_no_asignados": unassigned_votes, "evidencia_fuente": rel(electoral_doc[0], evidence_root) if electoral_doc else None, "evidencia_reconciliacion": rel(m07_recon[0], evidence_root) if m07_recon else None},
        "publicacion_y_visor": {"estado": publication_status, "url_visor": get_any(publication, "viewer_url"), "mapas_generados": get_any(publication, "maps_generated", default=[]), "resultados_en_visor": get_any(publication, "result_count"), "productos_m08": m08_products, "evidencia": rel(publication_doc[0], evidence_root) if publication_doc else None},
        "decision_final": {"decision": final_decision, "causas_de_bloqueo": blockers, "hasta_donde_llego": reached_until},
    }


def render_markdown(inv: dict) -> str:
    meta = inv["metadatos"]; final = inv["decision_final"]; fuentes = inv["fuentes_oficiales"]; base = inv["base_territorial_y_poblacion"]; distr = inv["creacion_y_equilibrado_de_distritos"]; geo = inv["control_geografico"]; elec = inv["incorporacion_electoral"]; pub = inv["publicacion_y_visor"]
    def show(value, fallback="No consta en las evidencias"):
        return fallback if value in (None, "", []) else str(value)
    lines = ["# Informe de ejecución", "", f"**Decisión final:** {final['decision']}", f"**Hasta dónde llegó:** {final['hasta_donde_llego']}", f"**Territorio:** {show(meta.get('territorio_id'))}", "", "## Fuentes oficiales", f"- Estado: {show(fuentes.get('decision'))}.", f"- Edición: {show(fuentes.get('edicion'))}."]
    if fuentes["fuentes"]:
        lines += ["", "| Fuente | Fecha | Procedencia | SHA-256 |", "|---|---|---|---|"]
        for row in fuentes["fuentes"]:
            lines.append(f"| {show(row.get('identificador'))} | {show(row.get('fecha_adquisicion'))} | {show(row.get('procedencia'))} | {show(row.get('checksum_sha256'))} |")
    else:
        lines.append("- No hay una fuente oficial materializada en las evidencias recuperadas.")
    lines += ["", "## Base territorial y población", f"- Unidades territoriales: {show(base.get('unidades_territoriales'))}.", f"- Población total: {show(base.get('poblacion_total'))}.", f"- Controles de integridad: {show(base.get('controles_integridad'))}.", "", "## Creación y equilibrado de distritos", f"- Distritos creados: {show(distr.get('distritos_creados'))}.", f"- Distritos equilibrados: {show(distr.get('distritos_equilibrados'))}.", f"- Distritos esperados: {show(distr.get('distritos_esperados'))}.", f"- Cumplimiento poblacional: {show((distr.get('cumplimiento_poblacional') or {}).get('decision'))}.", "", "## Control geográfico", f"- Conectividad: {show(geo.get('decision'))}.", f"- Distritos bloqueados: {show(geo.get('distritos_bloqueados'))}.", f"- Excepciones justificadas: {show(geo.get('excepciones_justificadas'))}.", "", "## Incorporación electoral", f"- Fuente electoral: {show(elec.get('decision_fuente'))}.", f"- Votos no asignados: {show(elec.get('votos_no_asignados'))}.", f"- Reconciliación: {'disponible' if elec.get('reconciliacion') else 'no disponible en las evidencias'}.", "", "## Publicación y visor", f"- Estado: {show(pub.get('estado'))}.", f"- Visor: {show(pub.get('url_visor'))}.", f"- Mapas generados: {len(pub.get('mapas_generados') or [])}.", f"- Productos electorales territoriales: {len(pub.get('productos_m08') or [])}.", "", "## Cierre"]
    if final["causas_de_bloqueo"]:
        lines.append("La ejecución terminó bloqueada por las siguientes causas registradas:")
        lines.extend(f"- {reason}" for reason in final["causas_de_bloqueo"])
    elif final["decision"] == "COMPLETE":
        lines.append("La cadena dispone de evidencia de publicación y no registra causas de bloqueo.")
    else:
        lines.append("La ejecución no registra un bloqueo explícito, pero las evidencias recuperadas no acreditan todavía una publicación completa.")
    lines += ["", "_Los códigos internos de módulos y rutas se conservan únicamente en el inventario JSON como metadatos de trazabilidad._", ""]
    return "\n".join(lines)


def main() -> None:
    ap = argparse.ArgumentParser(); ap.add_argument("--evidence-root", required=True); ap.add_argument("--context", required=True); ap.add_argument("--out-dir", required=True); args = ap.parse_args()
    root = Path(args.evidence_root); context = load_json(Path(args.context))
    if not isinstance(context, dict): raise SystemExit("El contexto automático de ejecución no es JSON válido")
    out = Path(args.out_dir); out.mkdir(parents=True, exist_ok=True); inventory = build_inventory(root, context)
    (out / "inventario_ejecucion.json").write_text(json.dumps(inventory, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (out / "informe_ejecucion.md").write_text(render_markdown(inventory), encoding="utf-8")


if __name__ == "__main__":
    main()
