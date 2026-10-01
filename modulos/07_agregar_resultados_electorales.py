#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PROYECTO: Diputado de Distrito
Módulo 07 — Agregar resultados electorales
VERSIÓN: 7.3.1
NOMBRE DE VERSIÓN: Contrato electoral universal
FECHA: 2026-09-14
QUÉ HACE: verifica convocatoria, fuentes y partidos antes de agregar votos a distritos.
POR QUÉ ES SEPARADO: la elección nunca condiciona fronteras; M07 solo proyecta sobre M06.
ESTADO: vigente — R039
CAMBIOS: endurece la frontera electoral: votos enteros decimales exactos y rechazo fail-closed de filas/zonas con localizador, sección o partido inválidos, sin descartes silenciosos.
MOTIVO: permitir nuevas elecciones sin tablas ni lógica territorial en M07.
ANTERIOR: legacy/modulo07/07_agregar_resultados_electorales_v7.1.0.py
"""
from __future__ import annotations

import argparse
import csv
import io
import json
import re
import sys
import zipfile
from pathlib import Path

import geopandas as gpd
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ddd_core.config import load_params_yaml, module_cfg, require
from ddd_core.electoral_contract import PartyDictionary, load_election_contract
from ddd_core.electoral_reconciliation import reconcile_sections


def load_geo(path):
    source = Path(path)
    if source.suffix.lower() == ".zip":
        with zipfile.ZipFile(source) as archive:
            member = next(
                name for name in archive.namelist()
                if name.lower().endswith((".geojson", ".json")) and not name.endswith("/")
            )
            return gpd.read_file(io.BytesIO(archive.read(member)))
    return gpd.read_file(source)


def write_geo(gdf, path):
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.parent / (output.stem.replace(".geojson", "") + ".geojson")
    gdf.to_file(temporary, driver="GeoJSON")
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.write(temporary, arcname=temporary.name)
    temporary.unlink(missing_ok=True)


def dotted(obj, path):
    current = obj
    for part in path.split("."):
        if not isinstance(current, dict):
            return None
        current = current.get(part)
    return current



def _exact_nonnegative_votes(value, *, source: Path, adapter_kind: str, row: str, field: str) -> int:
    """Acepta sólo enteros decimales explícitos >= 0; nunca rellena, trunca ni descarta."""
    if isinstance(value, bool) or value is None:
        raise ValueError(
            f"ELECTORAL_VOTES_INVALID source={source} adapter={adapter_kind} "
            f"row={row} field={field} value={value!r}: votos ausentes o no enteros"
        )
    if isinstance(value, int):
        votes = value
    elif isinstance(value, str):
        raw = value.strip()
        if not re.fullmatch(r"[0-9]+", raw):
            raise ValueError(
                f"ELECTORAL_VOTES_INVALID source={source} adapter={adapter_kind} "
                f"row={row} field={field} value={value!r}: se exige entero decimal exacto no negativo"
            )
        votes = int(raw)
    else:
        raise ValueError(
            f"ELECTORAL_VOTES_INVALID source={source} adapter={adapter_kind} "
            f"row={row} field={field} value={value!r}: se exige entero exacto, sin truncamiento"
        )
    if votes < 0:
        raise ValueError(
            f"ELECTORAL_VOTES_INVALID source={source} adapter={adapter_kind} "
            f"row={row} field={field} value={value!r}: votos negativos prohibidos"
        )
    return votes


def _input_invalid(*, source: Path, adapter_kind: str, row: str, field: str, value, cause: str) -> None:
    raise ValueError(
        f"ELECTORAL_INPUT_INVALID source={source} adapter={adapter_kind} "
        f"row={row} field={field} value={value!r} cause={cause}"
    )


def _required_text(value, *, source: Path, adapter_kind: str, row: str, field: str, cause: str) -> str:
    if value is None or bool(pd.isna(value)):
        _input_invalid(
            source=source, adapter_kind=adapter_kind, row=row, field=field,
            value=value, cause=cause,
        )
    text = str(value).strip()
    if not text:
        _input_invalid(
            source=source, adapter_kind=adapter_kind, row=row, field=field,
            value=value, cause=cause,
        )
    return text


def _canonical_party(value, *, parties: PartyDictionary, source: Path, adapter_kind: str, row: str, field: str) -> str:
    raw = _required_text(
        value,
        source=source,
        adapter_kind=adapter_kind,
        row=row,
        field=field,
        cause="PARTY_MISSING",
    )
    try:
        canonical = parties.canonicalize(raw)
    except ValueError:
        _input_invalid(
            source=source,
            adapter_kind=adapter_kind,
            row=row,
            field=field,
            value=value,
            cause="PARTY_NOT_RECOGNIZED",
        )
    if not canonical:
        _input_invalid(
            source=source,
            adapter_kind=adapter_kind,
            row=row,
            field=field,
            value=value,
            cause="PARTY_NOT_RECOGNIZED",
        )
    return canonical


def _accepted(frame: pd.DataFrame) -> pd.DataFrame:
    # Sólo se llega aquí si todos los registros de entrada superaron la validación.
    frame.attrs["rejected_rows"] = 0
    return frame


def _json_object(pairs):
    obj = {}
    for key, value in pairs:
        if key in obj:
            raise ValueError(f"ELECTORAL_INPUT_INVALID: JSON duplicate key {key!r}")
        obj[key] = value
    return obj


def _read_csv_strict(text, separator, *, source, adapter_kind):
    # pandas infers an index for surplus cells and skips empty lines by default.
    # Check the raw records first, so neither behavior can hide rejected input.
    records = list(csv.reader(io.StringIO(text), delimiter=separator, strict=True))
    if not records or not records[0]:
        raise ValueError(f"ELECTORAL_INPUT_INVALID source={source}: CSV header missing")
    header = records[0]
    if len(set(header)) != len(header) or any(not value.strip() for value in header):
        _input_invalid(source=source, adapter_kind=adapter_kind, row="header",
                       field="columns", value=header, cause="CSV_HEADER_INVALID")
    for index, record in enumerate(records[1:], start=2):
        if len(record) != len(header):
            _input_invalid(source=source, adapter_kind=adapter_kind, row=f"csv[{index}]",
                           field="columns", value=record, cause="CSV_ROW_WIDTH_INVALID")
    return pd.read_csv(io.StringIO(text), sep=separator, dtype=str,
                       keep_default_na=False, skip_blank_lines=False)


def read_results(path, adapter, section_field, parties: PartyDictionary):
    source = Path(path)
    text = source.read_text(encoding="utf-8").lstrip()
    if text.startswith(("{", "[")):
        obj = json.loads(text, object_pairs_hook=_json_object)
        if adapter.get("kind") != "nested_json":
            raise ValueError(f"El contenido JSON requiere adaptador nested_json: {source}")
        zones = dotted(obj, require(adapter.get("records_path"), "Falta records_path"))
        if not isinstance(zones, list):
            _input_invalid(source=source, adapter_kind="nested_json", row="root",
                           field=adapter["records_path"], value=zones, cause="ZONES_NOT_LIST")
        rows = []
        section_ids = set()
        section_key = require(adapter.get("section_field"), "Falta section_field")
        party_list = require(adapter.get("party_records_field"), "Falta party_records_field")
        party_key = require(adapter.get("party_field"), "Falta party_field")
        votes_key = require(adapter.get("votes_field"), "Falta votes_field")
        for zone_index, zone in enumerate(zones, start=1):
            zone_row = f"zone[{zone_index}]"
            if not isinstance(zone, dict):
                _input_invalid(
                    source=source, adapter_kind="nested_json", row=zone_row,
                    field="zone", value=zone, cause="ZONE_NOT_OBJECT",
                )
            party_records = zone.get(party_list, [])
            if not isinstance(party_records, list):
                _input_invalid(
                    source=source, adapter_kind="nested_json", row=zone_row,
                    field=party_list, value=party_records, cause="PARTY_RECORDS_NOT_LIST",
                )
            section_value = zone.get(section_key)
            if party_records:
                section_id = _required_text(
                    section_value,
                    source=source,
                    adapter_kind="nested_json",
                    row=zone_row,
                    field=section_key,
                    cause="SECTION_ID_MISSING_WITH_RESULTS",
                )
            elif section_value is None or str(section_value).strip() == "":
                # Una zona sin resultados puede carecer de sección sin perder votos.
                continue
            else:
                section_id = str(section_value).strip()
            section_ids.add(section_id)
            for party_index, item in enumerate(party_records, start=1):
                item_row = f"zone[{zone_index}].{party_list}[{party_index}]"
                if not isinstance(item, dict):
                    _input_invalid(
                        source=source, adapter_kind="nested_json", row=item_row,
                        field=party_list, value=item, cause="PARTY_RECORD_NOT_OBJECT",
                    )
                votes = _exact_nonnegative_votes(
                    item.get(votes_key), source=source, adapter_kind="nested_json",
                    row=item_row, field=votes_key,
                )
                party = _canonical_party(
                    item.get(party_key),
                    parties=parties,
                    source=source,
                    adapter_kind="nested_json",
                    row=item_row,
                    field=party_key,
                )
                rows.append({section_field: section_id, "party": party, "votes": votes})
        if not rows:
            raise ValueError(f"No se pudieron extraer votos del JSON: {source}")
        return _accepted(pd.DataFrame(rows)), section_ids

    if adapter.get("kind") == "wide_polling_station_csv":
        first = text.splitlines()[0] if text else ""
        separator = adapter.get("separator", "auto")
        if separator == "auto":
            separator = ";" if first.count(";") > first.count(",") else ","
        frame = _read_csv_strict(text, separator, source=source, adapter_kind="wide_polling_station_csv")
        province_field = require(adapter.get("province_field"), "Falta province_field")
        municipality_field = require(adapter.get("municipality_field"), "Falta municipality_field")
        polling_field = require(adapter.get("polling_station_field"), "Falta polling_station_field")
        polling_regex = require(adapter.get("polling_station_regex"), "Falta polling_station_regex")
        party_columns = require(adapter.get("party_columns"), "Falta party_columns")
        missing = [c for c in [province_field, municipality_field, polling_field, *party_columns] if c not in frame.columns]
        if missing:
            raise ValueError(f"CSV electoral ancho carece de columnas: {missing}")
        polling_values = frame[polling_field].fillna("")
        match = polling_values.str.extract(polling_regex)
        if not {"district", "section"}.issubset(match.columns):
            raise ValueError("polling_station_regex debe exponer grupos district y section")
        province_width = int(adapter.get("province_width", 2))
        municipality_width = int(adapter.get("municipality_width", 3))
        district_width = int(adapter.get("district_width", 2))
        section_width = int(adapter.get("section_width", 3))
        province_values = frame[province_field].fillna("").str.strip()
        municipality_values = frame[municipality_field].fillna("").str.strip()
        locator_valid = (
            polling_values.str.fullmatch(polling_regex)
            & match["district"].notna()
            & match["section"].notna()
            & match["district"].fillna("").str.len().le(district_width)
            & match["section"].fillna("").str.len().le(section_width)
        )
        province_valid = (
            province_values.str.fullmatch(r"\d+")
            & province_values.str.len().le(province_width)
        )
        municipality_valid = (
            municipality_values.str.fullmatch(r"\d+")
            & municipality_values.str.len().le(municipality_width)
        )
        for index in frame.index:
            row = f"csv[{int(index) + 2}]"
            if not bool(locator_valid.loc[index]):
                _input_invalid(
                    source=source,
                    adapter_kind="wide_polling_station_csv",
                    row=row,
                    field=polling_field,
                    value=frame.at[index, polling_field],
                    cause="POLLING_STATION_LOCATOR_INVALID",
                )
            if not bool(province_valid.loc[index]):
                _input_invalid(
                    source=source,
                    adapter_kind="wide_polling_station_csv",
                    row=row,
                    field=province_field,
                    value=frame.at[index, province_field],
                    cause="PROVINCE_CODE_INVALID",
                )
            if not bool(municipality_valid.loc[index]):
                _input_invalid(
                    source=source,
                    adapter_kind="wide_polling_station_csv",
                    row=row,
                    field=municipality_field,
                    value=frame.at[index, municipality_field],
                    cause="MUNICIPALITY_CODE_INVALID",
                )
        frame = frame.copy()
        frame[section_field] = (
            province_values.str.zfill(province_width)
            + municipality_values.str.zfill(municipality_width)
            + match["district"].astype(str).str.zfill(district_width)
            + match["section"].astype(str).str.zfill(section_width)
        )
        section_ids = set(frame[section_field])
        rows = []
        for raw_party in party_columns:
            canonical = _canonical_party(
                raw_party,
                parties=parties,
                source=source,
                adapter_kind="wide_polling_station_csv",
                row="header",
                field="party_columns",
            )
            batch = frame[[section_field, raw_party]].rename(columns={raw_party: "votes"})
            batch["party"] = canonical
            batch["votes"] = [
                _exact_nonnegative_votes(
                    value, source=source, adapter_kind="wide_polling_station_csv",
                    row=f"csv[{int(index) + 2}]", field=raw_party,
                )
                for index, value in batch["votes"].items()
            ]
            rows.append(batch[[section_field, "party", "votes"]])
        if not rows:
            raise ValueError(f"No se pudieron extraer partidos del CSV ancho: {source}")
        return _accepted(pd.concat(rows, ignore_index=True)), section_ids

    if adapter.get("kind") != "long_csv":
        raise ValueError(f"El contenido tabular requiere adaptador long_csv o wide_polling_station_csv: {source}")
    first = text.splitlines()[0] if text else ""
    separator = adapter.get("separator", "auto")
    if separator == "auto":
        separator = ";" if first.count(";") > first.count(",") else ","
    frame = _read_csv_strict(text, separator, source=source, adapter_kind="long_csv")
    section_source = require(adapter.get("section_field"), "Falta section_field")
    party_col = require(adapter.get("party_field"), "Falta party_field")
    votes_col = require(adapter.get("votes_field"), "Falta votes_field")
    missing = [c for c in (section_source, party_col, votes_col) if c not in frame.columns]
    if missing:
        raise ValueError(f"CSV electoral no cumple contrato long section/party/votes; faltan columnas: {missing}")
    result = frame[[section_source, party_col, votes_col]].rename(
        columns={section_source: section_field, party_col: "party", votes_col: "votes"}
    )
    validated_sections = []
    validated_parties = []
    validated_votes = []
    for index, row_data in result.iterrows():
        row = f"csv[{int(index) + 2}]"
        validated_sections.append(
            _required_text(
                row_data[section_field],
                source=source,
                adapter_kind="long_csv",
                row=row,
                field=section_source,
                cause="SECTION_ID_MISSING",
            )
        )
        validated_parties.append(
            _canonical_party(
                row_data["party"],
                parties=parties,
                source=source,
                adapter_kind="long_csv",
                row=row,
                field=party_col,
            )
        )
        validated_votes.append(
            _exact_nonnegative_votes(
                row_data["votes"],
                source=source,
                adapter_kind="long_csv",
                row=row,
                field=votes_col,
            )
        )
    result[section_field] = validated_sections
    result["party"] = validated_parties
    result["votes"] = validated_votes
    section_ids = set(result[section_field])
    return _accepted(result), section_ids



def _largest_remainder(total: int, weighted_targets: list[tuple[str, float]]) -> dict[str, int]:
    if total < 0:
        raise ValueError("No se pueden reconciliar votos negativos")
    denominator = sum(max(0.0, float(weight)) for _, weight in weighted_targets)
    if denominator <= 0:
        raise ValueError("Split electoral sin peso positivo")
    exact = [(target, total * max(0.0, float(weight)) / denominator) for target, weight in weighted_targets]
    base = {target: int(value // 1) for target, value in exact}
    remaining = total - sum(base.values())
    order = sorted(exact, key=lambda item: (-(item[1] - int(item[1] // 1)), item[0]))
    for target, _ in order[:remaining]:
        base[target] += 1
    if sum(base.values()) != total:
        raise AssertionError("El reparto electoral no conserva votos")
    return base


def apply_section_reconciliation(
    section_party: pd.DataFrame,
    gdf,
    *,
    section_field: str,
    contract: dict,
) -> tuple[pd.DataFrame, dict]:
    """Aplica únicamente equivalencias 1:1 demostradas; nunca reparte votos por población."""
    policy = contract.get("section_reconciliation") or {}
    aliases = policy.get("aliases") or []
    splits = policy.get("splits") or []

    out = section_party.copy()
    out[section_field] = out[section_field].astype(str)
    votes_before = int(out["votes"].sum())
    current_sections = set(gdf[section_field].astype(str))
    exact_methods = {
        "ine_geometry_exact_overlap_1_to_1",
        "exact_1_to_1",
        "exact_geometry_1_to_1",
    }
    evidence = {
        "status": "NOT_REQUIRED" if not aliases and not splits else "GOVERNED_NO_REDISTRIBUTION",
        "aliases_applied": [],
        "aliases_not_applied": [],
        "splits_not_applied": [],
        "votes_before": votes_before,
    }

    alias_map: dict[str, str] = {}
    source_sections = set(out[section_field].astype(str))
    for item in aliases:
        source = str(require(item.get("from"), "Alias electoral sin from"))
        target = str(require(item.get("to"), "Alias electoral sin to"))
        method = str(item.get("method") or "")
        reason = None
        if method not in exact_methods:
            reason = "ALIAS_NOT_PROVEN_EXACT_1_TO_1"
        elif source in current_sections:
            reason = "SOURCE_SECTION_ALREADY_EXISTS_IN_CURRENT_MAP"
        elif target not in current_sections:
            reason = "TARGET_SECTION_NOT_IN_CURRENT_MAP"
        elif source not in source_sections:
            reason = "SOURCE_SECTION_NOT_IN_ACCEPTED_RESULTS"
        elif source in alias_map and alias_map[source] != target:
            raise ValueError(f"Alias electoral ambiguo para {source}")
        if reason:
            evidence["aliases_not_applied"].append(
                {"from": source, "to": target, "method": method, "reason": reason}
            )
            continue
        alias_map[source] = target
        evidence["aliases_applied"].append(
            {"from": source, "to": target, "method": method}
        )

    if alias_map:
        out[section_field] = out[section_field].map(
            lambda value: alias_map.get(str(value), str(value))
        )
        out = out.groupby([section_field, "party"], as_index=False)["votes"].sum()

    # Un split entre seccionados de años distintos no autoriza a DDD a inventar
    # una distribución. Los votos permanecen en la sección de la fuente aceptada;
    # si esa sección no existe en el mapa actual, M07 los contabiliza como
    # ddd_unassigned_votes y aplica el presupuesto del 1,5 %.
    for rule in splits:
        evidence["splits_not_applied"].append(
            {
                "source_section": str(rule.get("source_section") or ""),
                "target_sections": [str(v) for v in (rule.get("target_sections") or [])],
                "declared_weighting": rule.get("weighting"),
                "reason": "NO_VOTE_REDISTRIBUTION_BETWEEN_EDITIONS",
                "spatial_evidence": rule.get("spatial_evidence"),
            }
        )

    votes_after = int(out["votes"].sum())
    if votes_after != votes_before:
        raise ValueError(f"Reconciliación electoral altera votos: {votes_before} -> {votes_after}")
    evidence["votes_after"] = votes_after
    return out, evidence

def electoral_outputs(assigned, district_field, parties: PartyDictionary):
    by_party = assigned.groupby([district_field, "party"], as_index=False)["votes"].sum()
    by_party = by_party.rename(columns={district_field: "district_id"})
    by_party["bloc"] = by_party["party"].map(parties.classification)
    totals = by_party.groupby("district_id", as_index=False)["votes"].sum()
    totals = totals.rename(columns={"votes": "total_votes"})
    ranked = by_party.merge(totals, on="district_id")
    ranked["vote_share"] = ranked["votes"] / ranked["total_votes"].replace({0: pd.NA})
    winners = ranked.loc[ranked.groupby("district_id")["votes"].idxmax()]
    winners = winners[["district_id", "party", "votes", "vote_share", "bloc"]].rename(
        columns={
            "party": "winner_party",
            "votes": "winner_votes",
            "vote_share": "winner_share",
            "bloc": "winner_bloc",
        }
    )
    return by_party, totals.merge(winners, on="district_id").sort_values("district_id")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--params", required=True)
    args = parser.parse_args()
    config = load_params_yaml(args.params)
    m07 = module_cfg(config, "modulo_07_agregar_resultados_electorales", "step7_elections")
    m06 = module_cfg(config, "modulo_06_consolidar_distritos", "step6_export_final")
    m03 = module_cfg(config, "modulo_03_construir_grafo", "step3_graph")
    input_geo = require(m07.get("in_geojson"), "Falta M07 geometría")
    section_field = require(m07.get("section_id_field"), "Falta M07 section_id")
    district_field = require(m07.get("district_field"), "Falta M07 district_id")
    population_field = require(
        m07.get("population_field") or m06.get("pop_field") or m03.get("pop_field"),
        "Falta M07 campo de población para informar cobertura electoral",
    )
    contract_path = require(m07.get("election_contract"), "Falta M07 contrato electoral")
    report_path = require(
        m07.get("out_reconciliation_report"),
        "Falta M07 informe de reconciliación",
    )

    project_root = config["_internal"]["root"]
    territory_id = require((config.get("meta") or {}).get("territory_id"), "Falta territory_id")
    contract, parties = load_election_contract(
        contract_path,
        project_root=project_root,
        expected_territory_id=territory_id,
    )
    gdf = load_geo(input_geo)
    mapping = gdf[[section_field, district_field, population_field]].copy()
    result_batches = [
        read_results(source["resolved_path"], source["adapter"], section_field, parties)
        for source in contract["sources"]
    ]
    rejected_rows = sum(int(batch[0].attrs.get("rejected_rows", 0)) for batch in result_batches)
    if rejected_rows != 0:
        raise ValueError(f"ELECTORAL_INPUT_REJECTED_ROWS: rejected_rows={rejected_rows}")
    results = pd.concat([batch[0] for batch in result_batches], ignore_index=True)
    result_section_ids = set().union(*(batch[1] for batch in result_batches))
    section_party = results.groupby([section_field, "party"], as_index=False)["votes"].sum()
    section_party, section_reconciliation_report = apply_section_reconciliation(
        section_party,
        gdf,
        section_field=section_field,
        contract=contract,
    )
    result_section_ids = set(section_party[section_field].astype(str))
    source_verification = contract.get("source_verification") or {}
    reconciliation_policy = contract.get("reconciliation") or {}
    definitive_candidate_votes = source_verification.get("official_candidate_votes")
    if definitive_candidate_votes is None:
        definitive_candidate_votes = reconciliation_policy.get("definitive_candidate_votes")
    assigned, report = reconcile_sections(
        mapping,
        section_party,
        section_field=section_field,
        district_field=district_field,
        policy=reconciliation_policy,
        result_section_ids=result_section_ids,
        population_field=population_field,
        definitive_candidate_votes=definitive_candidate_votes,
    )
    report["input_validation"] = {"rejected_rows": rejected_rows, "accepted_rows": int(len(results))}
    report["section_reconciliation"] = section_reconciliation_report
    report["source_verification"] = contract.get("source_verification") or {}
    report["non_geocodable_votes"] = contract.get("non_geocodable_votes") or {}
    report_file = Path(report_path)
    report_file.parent.mkdir(parents=True, exist_ok=True)
    report_file.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    if report["status"] == "FAIL":
        raise SystemExit(
            "M07 bloqueado por reconciliación electoral: " + "; ".join(report["errors"])
        )

    by_party, summary = electoral_outputs(
        assigned,
        district_field,
        parties,
    )
    out_party = Path(require(m07.get("out_district_party_csv"), "Falta M07 salida partido"))
    out_summary = Path(require(m07.get("out_district_summary_csv"), "Falta M07 salida resumen"))
    out_party.parent.mkdir(parents=True, exist_ok=True)
    by_party.sort_values(
        ["district_id", "votes"],
        ascending=[True, False],
    ).to_csv(out_party, index=False)
    summary.to_csv(out_summary, index=False)

    out_enriched = m07.get("out_sections_enriched_geojson", "")
    if out_enriched:
        section_totals = section_party.groupby(section_field, as_index=False)["votes"].sum()
        section_totals = section_totals.rename(columns={"votes": "section_total_votes"})
        indexes = section_party.groupby(section_field)["votes"].idxmax()
        section_winners = section_party.loc[
            indexes,
            [section_field, "party", "votes"],
        ].rename(
            columns={
                "party": "section_winner_party",
                "votes": "section_winner_votes",
            }
        )
        enriched = gdf.copy()
        enriched[section_field] = enriched[section_field].astype(str)
        enriched = enriched.merge(section_totals, on=section_field, how="left")
        enriched = enriched.merge(section_winners, on=section_field, how="left")
        enriched["electoral_data_status"] = enriched["section_total_votes"].map(
            lambda value: "NO_RESULT_IN_ACCEPTED_SOURCE" if pd.isna(value) else "AVAILABLE"
        )
        write_geo(enriched, out_enriched)

    print(
        f"[Módulo 7] OK status={report['status']} "
        f"districts={len(summary)} unassigned_votes={report['unassigned_votes']}"
    )


if __name__ == "__main__":
    main()
