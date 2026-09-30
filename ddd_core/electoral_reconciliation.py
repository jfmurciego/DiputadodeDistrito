"""
PROYECTO: Diputado de Distrito
COMPONENTE: Reconciliación electoral M07
VERSIÓN: 2.0.0
NOMBRE DE VERSIÓN: Pérdida atribuible a DDD
FECHA: 2026-09-30
QUÉ HACE: separa población, votos presentes en la fuente aceptada y votos incorporados por DDD.
ESTADO: vigente
MOTIVO: la población no es denominador electoral; el hueco de la fuente frente al definitivo
no se imputa a DDD y la pérdida adicional de transformación queda limitada al 1,5 %.
"""
from __future__ import annotations

from fractions import Fraction
from typing import Any, Mapping

import pandas as pd

MAX_PROVISIONAL_DDD_LOSS_RATIO = Fraction(3, 200)


def _declared(items: Any) -> dict[str, Mapping[str, Any]]:
    declared = {}
    for item in items or []:
        if isinstance(item, Mapping) and item.get("section_id") not in (None, ""):
            declared[str(item["section_id"])] = item
    return declared


def _loss_limit(policy: Mapping[str, Any]) -> Fraction:
    raw = policy.get("max_ddd_loss_ratio", MAX_PROVISIONAL_DDD_LOSS_RATIO)
    try:
        value = raw if isinstance(raw, Fraction) else Fraction(str(raw))
    except (TypeError, ValueError, ZeroDivisionError) as exc:
        raise ValueError("margen de pérdida DDD no medible") from exc
    if value < 0 or value > MAX_PROVISIONAL_DDD_LOSS_RATIO:
        raise ValueError(
            "margen de pérdida DDD fuera del máximo provisional: "
            f"{float(value):.6f} > {float(MAX_PROVISIONAL_DDD_LOSS_RATIO):.6f}"
        )
    return value


def _territorial_breakdown(items: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    by_province: dict[str, int] = {}
    by_municipality: dict[str, int] = {}
    for item in items:
        section_id = str(item.get("section_id") or "")
        votes = int(item.get("votes") or 0)
        if section_id.isdigit() and len(section_id) >= 5:
            province = section_id[:2]
            municipality = section_id[:5]
            by_province[province] = by_province.get(province, 0) + votes
            by_municipality[municipality] = by_municipality.get(municipality, 0) + votes
    return {
        "by_section": items,
        "by_province": [
            {"province_code": key, "votes": value} for key, value in sorted(by_province.items())
        ],
        "by_municipality": [
            {"municipality_code": key, "votes": value}
            for key, value in sorted(by_municipality.items())
        ],
    }


def reconcile_sections(
    mapping: pd.DataFrame,
    section_party: pd.DataFrame,
    *,
    section_field: str,
    district_field: str,
    policy: Mapping[str, Any],
    result_section_ids: set[str] | None = None,
    population_field: str | None = None,
    definitive_candidate_votes: int | None = None,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Account for accepted-source votes without using population as an electoral denominator."""
    required_mapping = [section_field, district_field]
    if population_field:
        required_mapping.append(population_field)
    mapping = mapping[required_mapping].copy()
    mapping[section_field] = mapping[section_field].astype(str)
    section_party = section_party[[section_field, "party", "votes"]].copy()
    section_party[section_field] = section_party[section_field].astype(str)
    section_party["votes"] = pd.to_numeric(
        section_party["votes"], errors="coerce"
    ).fillna(0).astype("int64")

    errors: list[str] = []
    warnings: list[str] = []
    duplicated = sorted(
        mapping.loc[mapping[section_field].duplicated(False), section_field].unique()
    )
    if duplicated:
        errors.append(f"secciones cartográficas duplicadas: {duplicated}")

    mapping_for_join = mapping.drop_duplicates(section_field, keep="first")
    map_sections = set(mapping_for_join[section_field])
    result_sections = (
        {str(section_id) for section_id in result_section_ids}
        if result_section_ids is not None
        else set(section_party[section_field])
    )
    result_only_ids = sorted(result_sections - map_sections)
    map_only_ids = sorted(map_sections - result_sections)
    votes_by_section = section_party.groupby(section_field)["votes"].sum().to_dict()
    result_only = [
        {"section_id": section_id, "votes": int(votes_by_section.get(section_id, 0))}
        for section_id in result_only_ids
    ]

    population_by_section: dict[str, int | float] = {}
    territory_population: int | float | None = None
    if population_field:
        numeric_population = pd.to_numeric(
            mapping_for_join[population_field], errors="coerce"
        )
        if numeric_population.isna().any():
            errors.append("población territorial no medible en todas las secciones")
        else:
            population_by_section = {
                str(section_id): float(pop)
                for section_id, pop in zip(
                    mapping_for_join[section_field], numeric_population, strict=False
                )
            }
            total = float(numeric_population.sum())
            territory_population = int(total) if total.is_integer() else total

    map_only = []
    for section_id in map_only_ids:
        item: dict[str, Any] = {"section_id": section_id}
        if section_id in population_by_section:
            pop = population_by_section[section_id]
            item["population"] = int(pop) if float(pop).is_integer() else pop
        map_only.append(item)

    # Las declaraciones históricas se conservan como evidencia, pero ya no son la
    # puerta que fuerza concordancias entre seccionados distintos.
    declared_result = _declared(policy.get("allowed_result_only_sections"))
    declared_map = _declared(policy.get("allowed_map_only_sections"))
    stale_result = sorted(set(declared_result) - set(result_only_ids))
    stale_map = sorted(set(declared_map) - set(map_only_ids))
    if stale_result or stale_map:
        warnings.append(
            f"declaraciones históricas no activas: result_only={stale_result}, map_only={stale_map}"
        )
    for item in result_only:
        expected = declared_result.get(item["section_id"], {}).get("expected_votes")
        if expected is not None and int(expected) != item["votes"]:
            errors.append(
                f"votos inesperados en {item['section_id']}: "
                f"{item['votes']} != {int(expected)}"
            )

    merged = section_party.merge(
        mapping_for_join[[section_field, district_field]],
        on=section_field,
        how="left",
        validate="many_to_one",
        indicator=True,
    )
    numeric_district = pd.to_numeric(merged[district_field], errors="coerce")
    assigned_mask = merged[district_field].notna() & (numeric_district >= 0)
    assigned = merged.loc[assigned_mask].drop(columns=["_merge"]).copy()
    unassigned_rows = merged.loc[~assigned_mask, [section_field, "votes"]].copy()
    unassigned_by_section = (
        unassigned_rows.groupby(section_field, as_index=False)["votes"].sum()
        if not unassigned_rows.empty
        else pd.DataFrame(columns=[section_field, "votes"])
    )
    unassigned_sections = [
        {"section_id": str(row[section_field]), "votes": int(row["votes"])}
        for row in unassigned_by_section.to_dict("records")
    ]

    source_votes = int(section_party["votes"].sum())
    incorporated_votes = int(assigned["votes"].sum())
    ddd_unassigned_votes = source_votes - incorporated_votes
    if sum(item["votes"] for item in unassigned_sections) != ddd_unassigned_votes:
        errors.append("desglose territorial de votos no asignados no reconcilia con el total")
    try:
        max_loss_fraction = _loss_limit(policy)
    except ValueError as exc:
        max_loss_fraction = MAX_PROVISIONAL_DDD_LOSS_RATIO
        errors.append(str(exc))
    max_loss_ratio = float(max_loss_fraction)

    ddd_loss_ratio: float | None = None
    if source_votes <= 0:
        errors.append(
            "no se puede medir la pérdida adicional de DDD: la fuente electoral aceptada no contiene votos"
        )
    elif ddd_unassigned_votes < 0:
        errors.append(
            "la incorporación produjo más votos que la fuente electoral aceptada"
        )
    else:
        loss_fraction = Fraction(ddd_unassigned_votes, source_votes)
        ddd_loss_ratio = float(loss_fraction)
        if loss_fraction > max_loss_fraction:
            errors.append(
                "pérdida adicional atribuible a DDD por encima del margen: "
                f"{ddd_unassigned_votes}/{source_votes}={float(loss_fraction):.6%} > "
                f"{float(max_loss_fraction):.6%}"
            )

    source_gap_votes: int | None = None
    source_gap_ratio: float | None = None
    if definitive_candidate_votes is not None:
        definitive = int(definitive_candidate_votes)
        source_gap_votes = definitive - source_votes
        if definitive > 0:
            source_gap_ratio = source_gap_votes / definitive

    has_exceptions = bool(result_only_ids or map_only_ids or ddd_unassigned_votes)
    status = (
        "FAIL"
        if errors
        else "PASS_WITH_DECLARED_EXCEPTIONS"
        if has_exceptions
        else "PASS"
    )
    report = {
        "schema_version": "2.0.0",
        "policy": "accepted_source_ddd_loss_budget",
        "status": status,
        "population_total": territory_population,
        "source_votes": source_votes,
        "incorporated_votes": incorporated_votes,
        "ddd_unassigned_votes": ddd_unassigned_votes,
        "ddd_loss_ratio": ddd_loss_ratio,
        "max_ddd_loss_ratio": max_loss_ratio,
        "source_gap_to_definitive_votes": source_gap_votes,
        "source_gap_to_definitive_ratio": source_gap_ratio,
        # aliases históricos para consumidores existentes
        "input_votes": source_votes,
        "assigned_votes": incorporated_votes,
        "unassigned_votes": ddd_unassigned_votes,
        "map_sections": len(map_sections),
        "result_sections": len(result_sections),
        "result_only_sections": result_only,
        "map_only_sections": map_only,
        "unassigned_votes_breakdown": _territorial_breakdown(unassigned_sections),
        "errors": errors,
        "warnings": warnings,
    }
    return assigned, report
