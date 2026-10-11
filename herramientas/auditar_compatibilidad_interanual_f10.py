"""Auditoría local F10, versión 1.0.0, 2026-10-12.

Alcance: reutilización de adquisiciones conservadas; estado candidato.
Cambios/motivo: reproduce conciliación sin adquirir, promover ni generar distritos.
Origen: herramientas/compatibilidad_poblacion_seccionado.py (F10).
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from herramientas.compatibilidad_poblacion_seccionado import (
    _geometry_frame_from_zip, _inventory_by_role, _population_rows_from_zip,
    _verified_geometry_audit_context, normalize_geometry_frames,
    reconcile_population_sectioning,
)


def audit(evidence: Path) -> dict:
    inventory_path = evidence / "inventario_fuentes.json"
    inventory = json.loads(inventory_path.read_text(encoding="utf-8"))
    population_year = int(inventory["population_year"])
    section_year = int(inventory["section_year"])
    roles = _inventory_by_role(inventory, population_year=population_year,
                               section_year=section_year)
    identities = {}
    for role, row in roles.items():
        path = evidence / "materialized" / row["path"]
        payload = path.read_bytes()
        actual_sha = hashlib.sha256(payload).hexdigest()
        if actual_sha != row["sha256"] or len(payload) != int(row["bytes"]):
            raise ValueError(f"INPUT_INVENTORY_BINDING_MISMATCH: {role}")
        identities[role] = dict(role=role, source_id=row.get("source_id", ""),
                                path=row["path"], member="materialized/" + row["path"],
                                sha256=actual_sha, bytes=len(payload))
    target, target_id = _geometry_frame_from_zip(
        evidence / identities["target_sectioning"]["member"])
    origin, origin_id = _geometry_frame_from_zip(
        evidence / identities["population_sectioning_origin"]["member"])
    target_rows, origin_rows, crs = normalize_geometry_frames(
        target_gdf=target, target_id_field=target_id, origin_gdf=origin,
        origin_id_field=origin_id, cross_year=True)
    audits, reasons = _verified_geometry_audit_context(
        roles, read_member_bytes=lambda member: (evidence / member).read_bytes(),
        required_roles=("target_sectioning", "population_sectioning_origin"))
    if reasons:
        raise ValueError("GEOMETRY_EVIDENCE_INVALID: " + "; ".join(reasons))
    return reconcile_population_sectioning(
        territory_id=inventory["territory_id"], edition=str(inventory["edition"]),
        population_year=population_year, section_year=section_year,
        population_rows=_population_rows_from_zip(
            evidence / identities["population"]["member"]),
        target_geometry_rows=target_rows, origin_geometry_rows=origin_rows,
        input_identities=identities, crs_audit=crs, geometry_audits=audits)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evidence", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    report = audit(args.evidence)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    # No se sobrescribe evidencia ni se promueve este informe.
    with args.output.open("x", encoding="utf-8") as stream:
        json.dump(report, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    print(json.dumps({"decision": report["decision"], "population": {
        k: v for k, v in report["population"].items() if k != "unassigned_by_section"
    }, "causes": report["causes"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
