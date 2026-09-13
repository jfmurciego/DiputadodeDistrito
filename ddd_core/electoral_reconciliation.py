"""
PROYECTO: Diputado de Distrito
COMPONENTE: Reconciliación electoral M07
VERSIÓN: 1.0.0
NOMBRE DE VERSIÓN: Ningún voto desaparece
FECHA: 2026-09-13
QUÉ HACE: concilia los universos cartográfico y electoral y contabiliza cada voto.
ESTADO: vigente — Paquete A, C-05
MOTIVO: impedir descartes silenciosos al cruzar seccionados de años distintos.
ANTERIOR: ninguno — componente nuevo.
"""
from __future__ import annotations

from typing import Any, Mapping

import pandas as pd


def _declared(items: Any) -> dict[str, Mapping[str, Any]]:
    declared = {}
    for item in items or []:
        if isinstance(item, Mapping) and item.get("section_id") not in (None, ""):
            declared[str(item["section_id"])] = item
    return declared


def reconcile_sections(
    mapping: pd.DataFrame,
    section_party: pd.DataFrame,
    *,
    section_field: str,
    district_field: str,
    policy: Mapping[str, Any],
    result_section_ids: set[str] | None = None,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Preserve electoral rows, account for every vote and classify mismatches."""
    mapping = mapping[[section_field, district_field]].copy()
    mapping[section_field] = mapping[section_field].astype(str)
    section_party = section_party[[section_field, "party", "votes"]].copy()
    section_party[section_field] = section_party[section_field].astype(str)
    section_party["votes"] = pd.to_numeric(
        section_party["votes"],
        errors="coerce",
    ).fillna(0).astype("int64")

    errors = []
    duplicated = sorted(
        mapping.loc[
            mapping[section_field].duplicated(False),
            section_field,
        ].unique()
    )
    if duplicated:
        errors.append(f"secciones cartográficas duplicadas: {duplicated}")

    map_sections = set(mapping[section_field])
    result_sections = (
        {str(section_id) for section_id in result_section_ids}
        if result_section_ids is not None
        else set(section_party[section_field])
    )
    result_only_ids = sorted(result_sections - map_sections)
    map_only_ids = sorted(map_sections - result_sections)
    votes_by_section = section_party.groupby(section_field)["votes"].sum().to_dict()
    result_only = [
        {
            "section_id": section_id,
            "votes": int(votes_by_section.get(section_id, 0)),
        }
        for section_id in result_only_ids
    ]

    declared_result = _declared(policy.get("allowed_result_only_sections"))
    declared_map = _declared(policy.get("allowed_map_only_sections"))
    missing_reason = sorted(
        section_id
        for section_id, item in {**declared_result, **declared_map}.items()
        if not str(item.get("reason", "")).strip()
    )
    unexpected_result = sorted(set(result_only_ids) - set(declared_result))
    unexpected_map = sorted(set(map_only_ids) - set(declared_map))
    stale_result = sorted(set(declared_result) - set(result_only_ids))
    stale_map = sorted(set(declared_map) - set(map_only_ids))
    if unexpected_result:
        errors.append(
            f"secciones solo en resultados no declaradas: {unexpected_result}"
        )
    if unexpected_map:
        errors.append(f"secciones solo en mapa no declaradas: {unexpected_map}")
    if stale_result or stale_map:
        errors.append(
            f"excepciones obsoletas: result_only={stale_result}, map_only={stale_map}"
        )
    if missing_reason:
        errors.append(f"excepciones sin motivo documentado: {missing_reason}")
    for item in result_only:
        expected = declared_result.get(item["section_id"], {}).get("expected_votes")
        if expected is not None and int(expected) != item["votes"]:
            errors.append(
                f"votos inesperados en {item['section_id']}: "
                f"{item['votes']} != {int(expected)}"
            )

    mapping_for_join = mapping.drop_duplicates(section_field, keep="first")
    merged = section_party.merge(
        mapping_for_join,
        on=section_field,
        how="left",
        validate="many_to_one",
        indicator=True,
    )
    numeric_district = pd.to_numeric(merged[district_field], errors="coerce")
    assigned_mask = merged[district_field].notna() & (numeric_district >= 0)
    assigned = merged.loc[assigned_mask].drop(columns=["_merge"]).copy()
    input_votes = int(section_party["votes"].sum())
    assigned_votes = int(assigned["votes"].sum())
    has_exceptions = bool(result_only_ids or map_only_ids)
    report = {
        "schema_version": "1.0.0",
        "policy": policy.get("policy", "fail_unless_declared"),
        "status": (
            "FAIL"
            if errors
            else "PASS_WITH_DECLARED_EXCEPTIONS"
            if has_exceptions
            else "PASS"
        ),
        "input_votes": input_votes,
        "assigned_votes": assigned_votes,
        "unassigned_votes": input_votes - assigned_votes,
        "map_sections": len(map_sections),
        "result_sections": len(result_sections),
        "result_only_sections": result_only,
        "map_only_sections": [
            {"section_id": section_id} for section_id in map_only_ids
        ],
        "errors": errors,
    }
    return assigned, report
