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
import hashlib
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
from ddd_core.electoral_contract import (
    PartyDictionary,
    STRUCTURAL_PROVENANCE_SCHEMA,
    load_election_contract,
    validate_structural_provenance_document,
)
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


def _structural_rows(adapter, source: Path, frame: pd.DataFrame):
    declared_scope = adapter.get("party_applicability") or {}
    record = adapter.get("structural_provenance")
    if not record:
        if declared_scope:
            raise ValueError(
                "ELECTORAL_STRUCTURAL_PROVENANCE_REQUIRED "
                f"source={source}"
            )
        return None, None
    if not isinstance(record, dict):
        raise ValueError(
            "ELECTORAL_STRUCTURAL_PROVENANCE_INVALID: declaración"
        )
    raw_path = str(
        record.get("resolved_path")
        or record.get("path")
        or ""
    ).strip()
    if not raw_path:
        raise ValueError(
            "ELECTORAL_STRUCTURAL_PROVENANCE_INVALID: path ausente"
        )
    provenance_path = Path(raw_path)
    if not provenance_path.is_absolute():
        provenance_path = (ROOT / provenance_path).resolve()
    if not provenance_path.is_file():
        raise ValueError(
            "ELECTORAL_STRUCTURAL_PROVENANCE_INVALID: fichero ausente"
        )
    actual_provenance_sha = hashlib.sha256(
        provenance_path.read_bytes()
    ).hexdigest()
    declared_provenance_sha = str(
        record.get("sha256") or ""
    ).lower()
    if (
        not re.fullmatch(r"[0-9a-f]{64}", declared_provenance_sha)
        or actual_provenance_sha != declared_provenance_sha
    ):
        raise ValueError(
            "ELECTORAL_STRUCTURAL_PROVENANCE_INVALID: "
            "checksum del sidecar no coincide"
        )
    document = json.loads(provenance_path.read_text(encoding="utf-8"))
    actual_source_sha = hashlib.sha256(source.read_bytes()).hexdigest()
    validate_structural_provenance_document(
        document,
        context="procedencia estructural M07",
        expected_source_sha256=actual_source_sha,
    )
    merged = document["merged_source"]
    if merged["records"] != len(frame):
        raise ValueError(
            "ELECTORAL_STRUCTURAL_PROVENANCE_INVALID: "
            "número de filas no coincide"
        )
    if list(merged["columns"]) != list(frame.columns):
        raise ValueError(
            "ELECTORAL_STRUCTURAL_PROVENANCE_INVALID: "
            "cabecera fusionada no coincide"
        )

    rows = [None] * len(frame)
    summaries = []
    for source_record in document["sources"]:
        start = source_record["merged_row_index_start"]
        end = source_record["merged_row_index_end_exclusive"]
        normalized = {
            **source_record,
            "source_id": source_record["source_id"].strip(),
            "raw_file": source_record["raw_file"].strip(),
            "raw_sha256": source_record["raw_sha256"].lower(),
            "original_columns": list(source_record["original_columns"]),
        }
        for index in range(start, end):
            rows[index] = normalized
        summaries.append({
            "source_id": normalized["source_id"],
            "raw_file": normalized["raw_file"],
            "raw_sha256": normalized["raw_sha256"],
            "records": normalized["records"],
            "original_columns": list(normalized["original_columns"]),
        })
    if any(row is None for row in rows):
        raise ValueError(
            "ELECTORAL_STRUCTURAL_PROVENANCE_INVALID: "
            "cobertura de filas incompleta"
        )
    return rows, {
        "schema": STRUCTURAL_PROVENANCE_SCHEMA,
        "sha256": actual_provenance_sha,
        "merged_source_sha256": actual_source_sha,
        "sources": summaries,
    }


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
        adapter_kind = "wide_polling_station_csv"
        first = text.splitlines()[0] if text else ""
        separator = adapter.get("separator", "auto")
        if separator == "auto":
            separator = ";" if first.count(";") > first.count(",") else ","
        frame = _read_csv_strict(
            text,
            separator,
            source=source,
            adapter_kind=adapter_kind,
        )
        province_field = require(
            adapter.get("province_field"),
            "Falta province_field",
        )
        municipality_field = require(
            adapter.get("municipality_field"),
            "Falta municipality_field",
        )
        polling_field = require(
            adapter.get("polling_station_field"),
            "Falta polling_station_field",
        )
        polling_regex = require(
            adapter.get("polling_station_regex"),
            "Falta polling_station_regex",
        )
        party_columns = require(
            adapter.get("party_columns"),
            "Falta party_columns",
        )
        classification = adapter.get("record_classification") or {}
        if not isinstance(classification, dict):
            raise ValueError(
                "record_classification debe ser un objeto"
            )
        aggregate_rules = classification.get("aggregates") or []
        party_applicability = adapter.get("party_applicability") or {}
        if not isinstance(party_applicability, dict):
            raise ValueError("party_applicability debe ser un objeto")
        structural_rows, structural_evidence = _structural_rows(
            adapter,
            source,
            frame,
        )
        require_aggregate_for_each_block = False
        if classification:
            polling_cfg = classification.get("polling_station") or {}
            if polling_cfg.get("mode") != "locator_contract":
                raise ValueError(
                    "record_classification.polling_station.mode "
                    "debe ser locator_contract"
                )
            if not isinstance(aggregate_rules, list):
                raise ValueError(
                    "record_classification.aggregates debe ser una lista"
                )
            require_value = classification.get(
                "require_aggregate_for_each_block"
            )
            if not isinstance(require_value, bool):
                raise ValueError(
                    "record_classification."
                    "require_aggregate_for_each_block debe ser booleano"
                )
            if require_value and not aggregate_rules:
                raise ValueError(
                    "record_classification no puede exigir agregados "
                    "sin declarar reglas"
                )
            require_aggregate_for_each_block = require_value

        contract_fields = [
            province_field,
            municipality_field,
            polling_field,
            *party_columns,
            *[
                rule.get("field")
                for rule in party_applicability.values()
                if isinstance(rule, dict)
            ],
        ]
        aggregate_partition_fields = set()
        for rule in aggregate_rules:
            if not isinstance(rule, dict):
                raise ValueError(
                    "record_classification.aggregates contiene "
                    "una regla inválida"
                )
            match_cfg = rule.get("match") or {}
            scope_cfg = rule.get("scope") or {}
            partition_field = scope_cfg.get("partition_field")
            if partition_field:
                aggregate_partition_fields.add(str(partition_field))
            contract_fields.extend(
                [
                    match_cfg.get("field"),
                    *list(match_cfg.get("required_empty_fields") or []),
                    partition_field,
                ]
            )
        if len(aggregate_partition_fields) > 1:
            raise ValueError(
                "record_classification.aggregates debe usar un único "
                "scope.partition_field"
            )
        block_partition_field = (
            next(iter(aggregate_partition_fields))
            if aggregate_partition_fields
            else None
        )
        missing = [
            field
            for field in contract_fields
            if field and field not in frame.columns
        ]
        if missing:
            raise ValueError(
                f"CSV electoral ancho carece de columnas: "
                f"{sorted(set(missing))}"
            )

        polling_values = frame[polling_field].fillna("").str.strip()
        match = polling_values.str.extract(polling_regex)
        if not {"district", "section"}.issubset(match.columns):
            raise ValueError(
                "polling_station_regex debe exponer grupos "
                "district y section"
            )
        province_width = int(adapter.get("province_width", 2))
        municipality_width = int(adapter.get("municipality_width", 3))
        district_width = int(adapter.get("district_width", 2))
        section_width = int(adapter.get("section_width", 3))
        province_values = frame[province_field].fillna("").str.strip()
        municipality_values = (
            frame[municipality_field].fillna("").str.strip()
        )
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

        def _field_text(index, field):
            value = frame.at[index, field]
            if value is None or bool(pd.isna(value)):
                return ""
            return str(value).strip()

        def _aggregate_matches(index, rule):
            match_cfg = rule.get("match") or {}
            marker_field = match_cfg.get("field")
            equals = match_cfg.get("equals")
            values = equals if isinstance(equals, list) else [equals]
            expected = {str(value).strip() for value in values}
            if _field_text(index, marker_field) not in expected:
                return False
            for field in match_cfg.get("required_empty_fields") or []:
                if _field_text(index, field):
                    return False
            return True

        def _source_record(index):
            if structural_rows is None:
                return None
            return structural_rows[int(index)]

        def _party_scope_rule(raw_party):
            rule = party_applicability.get(raw_party)
            return rule if isinstance(rule, dict) else None

        def _party_applicable_for_value(raw_party, value):
            rule = _party_scope_rule(raw_party)
            if rule is None:
                return True
            equals = rule.get("equals")
            values = equals if isinstance(equals, list) else [equals]
            expected = {str(item).strip() for item in values}
            return str(value).strip() in expected

        record_classes = []
        for index in frame.index:
            row = f"csv[{int(index) + 2}]"
            aggregate_matches = [
                rule
                for rule in aggregate_rules
                if _aggregate_matches(index, rule)
            ]
            polling_ok = (
                bool(locator_valid.loc[index])
                and bool(province_valid.loc[index])
                and bool(municipality_valid.loc[index])
            )
            if polling_ok and not aggregate_matches:
                record_classes.append(
                    {
                        "index": index,
                        "kind": "polling_station",
                        "rule": None,
                    }
                )
                continue
            if len(aggregate_matches) == 1 and not polling_ok:
                record_classes.append(
                    {
                        "index": index,
                        "kind": "aggregate",
                        "rule": aggregate_matches[0],
                    }
                )
                continue
            if len(aggregate_matches) > 1 or (
                polling_ok and aggregate_matches
            ):
                _input_invalid(
                    source=source,
                    adapter_kind=adapter_kind,
                    row=row,
                    field="record_classification",
                    value={
                        "polling_station": polling_ok,
                        "aggregates": [
                            item.get("id") for item in aggregate_matches
                        ],
                    },
                    cause="RECORD_CLASS_AMBIGUOUS",
                )

            polling_value = _field_text(index, polling_field)
            if not polling_value:
                _input_invalid(
                    source=source,
                    adapter_kind=adapter_kind,
                    row=row,
                    field=polling_field,
                    value=frame.at[index, polling_field],
                    cause=(
                        "RECORD_CLASS_INVALID"
                        if classification
                        else "POLLING_STATION_LOCATOR_INVALID"
                    ),
                )
            if not bool(locator_valid.loc[index]):
                _input_invalid(
                    source=source,
                    adapter_kind=adapter_kind,
                    row=row,
                    field=polling_field,
                    value=frame.at[index, polling_field],
                    cause="POLLING_STATION_LOCATOR_INVALID",
                )
            if not bool(province_valid.loc[index]):
                _input_invalid(
                    source=source,
                    adapter_kind=adapter_kind,
                    row=row,
                    field=province_field,
                    value=frame.at[index, province_field],
                    cause="PROVINCE_CODE_INVALID",
                )
            if not bool(municipality_valid.loc[index]):
                _input_invalid(
                    source=source,
                    adapter_kind=adapter_kind,
                    row=row,
                    field=municipality_field,
                    value=frame.at[index, municipality_field],
                    cause="MUNICIPALITY_CODE_INVALID",
                )
            _input_invalid(
                source=source,
                adapter_kind=adapter_kind,
                row=row,
                field="record_classification",
                value="unclassified",
                cause="RECORD_CLASS_INVALID",
            )

        canonical_parties = {}
        canonical_owners = {}
        for raw_party in party_columns:
            canonical = _canonical_party(
                raw_party,
                parties=parties,
                source=source,
                adapter_kind=adapter_kind,
                row="header",
                field="party_columns",
            )
            owner = canonical_owners.get(canonical)
            if owner is not None:
                _input_invalid(
                    source=source,
                    adapter_kind=adapter_kind,
                    row="header",
                    field="party_columns",
                    value=[owner, raw_party],
                    cause="PARTY_COLUMNS_CANONICAL_DUPLICATE",
                )
            canonical_owners[canonical] = raw_party
            canonical_parties[raw_party] = canonical

        vote_rows = []
        section_ids = set()
        pending_polling_rows = []
        recognized_aggregates = []
        polling_station_rows = 0
        source_identity = {
            "name": source.name,
            "sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        }
        not_applicable_counts = {}

        def _record_not_applicable(
            raw_party,
            scope_field,
            scope_value,
            source_record,
        ):
            rule = _party_scope_rule(raw_party) or {}
            key = (
                raw_party,
                str(scope_field),
                str(scope_value),
                str(rule.get("reason") or ""),
                str((source_record or {}).get("source_id") or ""),
                str((source_record or {}).get("raw_sha256") or ""),
            )
            not_applicable_counts[key] = (
                int(not_applicable_counts.get(key, 0)) + 1
            )

        for classified in record_classes:
            index = classified["index"]
            row = f"csv[{int(index) + 2}]"
            if classified["kind"] == "polling_station":
                source_record = _source_record(index)
                current_source_id = str(
                    (source_record or {}).get("source_id") or ""
                )
                current_partition = None
                if block_partition_field is not None:
                    current_partition = _field_text(
                        index,
                        block_partition_field,
                    )
                    if not current_partition:
                        _input_invalid(
                            source=source,
                            adapter_kind=adapter_kind,
                            row=row,
                            field=block_partition_field,
                            value=frame.at[index, block_partition_field],
                            cause="AGGREGATE_SCOPE_VALUE_MISSING",
                        )
                if pending_polling_rows:
                    previous_partition = (
                        str(
                            pending_polling_rows[-1]["fields"].get(
                                block_partition_field,
                                "",
                            )
                        ).strip()
                        if block_partition_field is not None
                        else None
                    )
                    previous_source_id = str(
                        pending_polling_rows[-1].get("source_id") or ""
                    )
                    partition_changed = (
                        block_partition_field is not None
                        and current_partition != previous_partition
                    )
                    source_changed = (
                        structural_rows is not None
                        and current_source_id != previous_source_id
                    )
                    if partition_changed or source_changed:
                        if require_aggregate_for_each_block:
                            _input_invalid(
                                source=source,
                                adapter_kind=adapter_kind,
                                row=row,
                                field=(
                                    block_partition_field
                                    if partition_changed
                                    else "structural_provenance"
                                ),
                                value={
                                    "previous_partition": previous_partition,
                                    "current_partition": current_partition,
                                    "previous_source_id": previous_source_id,
                                    "current_source_id": current_source_id,
                                },
                                cause="MISSING_EXPECTED_AGGREGATE",
                            )
                        pending_polling_rows = []
                section_id = (
                    _field_text(index, province_field).zfill(province_width)
                    + _field_text(
                        index,
                        municipality_field,
                    ).zfill(municipality_width)
                    + str(match.at[index, "district"]).zfill(
                        district_width
                    )
                    + str(match.at[index, "section"]).zfill(
                        section_width
                    )
                )
                raw_votes = {}
                source_columns = set(
                    (source_record or {}).get("original_columns") or []
                )
                for raw_party in party_columns:
                    scope_rule = _party_scope_rule(raw_party)
                    if scope_rule is not None:
                        scope_field = str(scope_rule.get("field") or "")
                        if scope_field not in source_columns:
                            _input_invalid(
                                source=source,
                                adapter_kind=adapter_kind,
                                row=row,
                                field=scope_field,
                                value=None,
                                cause="PARTY_SCOPE_FIELD_MISSING_IN_RAW",
                            )
                        scope_value = _field_text(index, scope_field)
                        if not scope_value:
                            _input_invalid(
                                source=source,
                                adapter_kind=adapter_kind,
                                row=row,
                                field=scope_field,
                                value=frame.at[index, scope_field],
                                cause="PARTY_SCOPE_VALUE_MISSING",
                            )
                        in_scope = _party_applicable_for_value(
                            raw_party,
                            scope_value,
                        )
                        physically_present = raw_party in source_columns
                        if not in_scope:
                            if physically_present:
                                _input_invalid(
                                    source=source,
                                    adapter_kind=adapter_kind,
                                    row=row,
                                    field=raw_party,
                                    value=frame.at[index, raw_party],
                                    cause=(
                                        "PARTY_COLUMN_PRESENT_OUTSIDE_"
                                        "DECLARED_SCOPE"
                                    ),
                                )
                            _record_not_applicable(
                                raw_party,
                                scope_field,
                                scope_value,
                                source_record,
                            )
                            continue
                        if not physically_present:
                            _input_invalid(
                                source=source,
                                adapter_kind=adapter_kind,
                                row=row,
                                field=raw_party,
                                value=None,
                                cause=(
                                    "PARTY_COLUMN_MISSING_IN_"
                                    "DECLARED_SCOPE"
                                ),
                            )
                    votes = _exact_nonnegative_votes(
                        frame.at[index, raw_party],
                        source=source,
                        adapter_kind=adapter_kind,
                        row=row,
                        field=raw_party,
                    )
                    raw_votes[raw_party] = votes
                    vote_rows.append(
                        {
                            section_field: section_id,
                            "party": canonical_parties[raw_party],
                            "votes": votes,
                        }
                    )
                if not raw_votes:
                    _input_invalid(
                        source=source,
                        adapter_kind=adapter_kind,
                        row=row,
                        field="party_applicability",
                        value="no_applicable_parties",
                        cause="NO_PARTIES_IN_DECLARED_SCOPE",
                    )
                section_ids.add(section_id)
                polling_station_rows += 1
                pending_polling_rows.append(
                    {
                        "row": row,
                        "raw_index": int(index),
                        "raw_votes": raw_votes,
                        "source_id": current_source_id,
                        "raw_sha256": str(
                            (source_record or {}).get("raw_sha256") or ""
                        ),
                        "fields": {
                            field: _field_text(index, field)
                            for field in frame.columns
                        },
                    }
                )
                continue

            rule = classified["rule"]
            rule_id = str(rule.get("id") or "")
            scope_cfg = rule.get("scope") or {}
            scope_kind = scope_cfg.get("kind")
            partition_field = scope_cfg.get("partition_field")
            if scope_kind != "preceding_polling_station_block":
                _input_invalid(
                    source=source,
                    adapter_kind=adapter_kind,
                    row=row,
                    field="record_classification",
                    value=scope_kind,
                    cause="AGGREGATE_SCOPE_KIND_INVALID",
                )
            if not pending_polling_rows:
                _input_invalid(
                    source=source,
                    adapter_kind=adapter_kind,
                    row=row,
                    field=partition_field,
                    value=None,
                    cause="AGGREGATE_SCOPE_MISSING",
                )
            partition_values = {
                item["fields"].get(partition_field, "").strip()
                for item in pending_polling_rows
                if item["fields"].get(partition_field, "").strip()
            }
            if len(partition_values) != 1:
                _input_invalid(
                    source=source,
                    adapter_kind=adapter_kind,
                    row=row,
                    field=partition_field,
                    value=sorted(partition_values),
                    cause="AGGREGATE_SCOPE_AMBIGUOUS",
                )
            partition_value = next(iter(partition_values))
            aggregate_source_record = _source_record(index)
            aggregate_source_id = str(
                (aggregate_source_record or {}).get("source_id") or ""
            )
            pending_source_ids = {
                str(item.get("source_id") or "")
                for item in pending_polling_rows
            }
            if structural_rows is not None and (
                len(pending_source_ids) != 1
                or aggregate_source_id not in pending_source_ids
            ):
                _input_invalid(
                    source=source,
                    adapter_kind=adapter_kind,
                    row=row,
                    field="structural_provenance",
                    value={
                        "aggregate_source_id": aggregate_source_id,
                        "polling_source_ids": sorted(pending_source_ids),
                    },
                    cause="AGGREGATE_SOURCE_PROVENANCE_MISMATCH",
                )
            reconciliation = rule.get("vote_reconciliation") or {}
            reconciliation_kind = reconciliation.get("kind")
            comparisons = []
            differences = []

            if reconciliation_kind != "party_columns_exact_sum":
                _input_invalid(
                    source=source,
                    adapter_kind=adapter_kind,
                    row=row,
                    field="vote_reconciliation.kind",
                    value=reconciliation_kind,
                    cause="AGGREGATE_RECONCILIATION_INVALID",
                )
            if reconciliation.get("empty_aggregate_value") != "reject":
                _input_invalid(
                    source=source,
                    adapter_kind=adapter_kind,
                    row=row,
                    field="vote_reconciliation.empty_aggregate_value",
                    value=reconciliation.get("empty_aggregate_value"),
                    cause="AGGREGATE_EMPTY_POLICY_INVALID",
                )

            for raw_party in party_columns:
                scope_rule = _party_scope_rule(raw_party)
                if scope_rule is not None:
                    scope_field = str(scope_rule.get("field") or "")
                    aggregate_columns = set(
                        (aggregate_source_record or {}).get(
                            "original_columns"
                        ) or []
                    )
                    if scope_field not in aggregate_columns:
                        _input_invalid(
                            source=source,
                            adapter_kind=adapter_kind,
                            row=row,
                            field=scope_field,
                            value=None,
                            cause="PARTY_SCOPE_FIELD_MISSING_IN_RAW",
                        )
                    block_values = {
                        str(item["fields"].get(scope_field, "")).strip()
                        for item in pending_polling_rows
                    }
                    if "" in block_values or len(block_values) != 1:
                        _input_invalid(
                            source=source,
                            adapter_kind=adapter_kind,
                            row=row,
                            field=scope_field,
                            value=sorted(block_values),
                            cause=(
                                "PARTY_SCOPE_VALUE_MISSING"
                                if "" in block_values
                                else "PARTY_SCOPE_AMBIGUOUS"
                            ),
                        )
                    block_value = next(iter(block_values))
                    in_scope = _party_applicable_for_value(
                        raw_party,
                        block_value,
                    )
                    physically_present = raw_party in aggregate_columns
                    if not in_scope:
                        if physically_present:
                            _input_invalid(
                                source=source,
                                adapter_kind=adapter_kind,
                                row=row,
                                field=raw_party,
                                value=frame.at[index, raw_party],
                                cause=(
                                    "PARTY_AGGREGATE_COLUMN_PRESENT_"
                                    "OUTSIDE_DECLARED_SCOPE"
                                ),
                            )
                        comparisons.append(
                            {
                                "party_column": raw_party,
                                "canonical_party": canonical_parties[raw_party],
                                "status": "NOT_COMPARABLE",
                                "reason": "PARTY_OUTSIDE_DECLARED_SCOPE",
                                "scope_field": scope_field,
                                "scope_value": block_value,
                                "source_id": aggregate_source_id,
                                "raw_sha256": str(
                                    (aggregate_source_record or {}).get(
                                        "raw_sha256"
                                    ) or ""
                                ),
                                "polling_station_sum": None,
                                "aggregate_value": None,
                            }
                        )
                        continue
                    if not physically_present:
                        _input_invalid(
                            source=source,
                            adapter_kind=adapter_kind,
                            row=row,
                            field=raw_party,
                            value=None,
                            cause=(
                                "PARTY_AGGREGATE_COLUMN_MISSING_IN_"
                                "DECLARED_SCOPE"
                            ),
                        )
                observed = sum(
                    int(item["raw_votes"][raw_party])
                    for item in pending_polling_rows
                )
                expected = _exact_nonnegative_votes(
                    frame.at[index, raw_party],
                    source=source,
                    adapter_kind=adapter_kind,
                    row=row,
                    field=raw_party,
                )
                status = "MATCH" if observed == expected else "MISMATCH"
                comparison = {
                    "party_column": raw_party,
                    "canonical_party": canonical_parties[raw_party],
                    "status": status,
                    "polling_station_sum": observed,
                    "aggregate_value": expected,
                }
                comparisons.append(comparison)
                if status == "MISMATCH":
                    differences.append(comparison)

            evidence = {
                "aggregate_id": rule_id,
                "row": row,
                "source": dict(source_identity),
                "marker": {
                    "field": (rule.get("match") or {}).get("field"),
                    "value": _field_text(
                        index,
                        (rule.get("match") or {}).get("field"),
                    ),
                },
                "scope": {
                    "kind": scope_kind,
                    "partition_field": partition_field,
                    "partition_value": partition_value,
                    "polling_station_rows": len(
                        pending_polling_rows
                    ),
                },
                "vote_reconciliation": {
                    "kind": reconciliation_kind,
                    "status": (
                        "MISMATCH"
                        if differences
                        else (
                            "MATCH_WITH_OUT_OF_SCOPE"
                            if any(
                                item.get("status") == "NOT_COMPARABLE"
                                for item in comparisons
                            )
                            else "MATCH"
                        )
                    ),
                    "comparisons": comparisons,
                },
                "included_in_vote_rows": False,
            }
            recognized_aggregates.append(evidence)
            if differences:
                raise ValueError(
                    "ELECTORAL_AGGREGATE_MISMATCH "
                    f"source={source} adapter={adapter_kind} "
                    f"row={row} aggregate_id={rule_id} "
                    f"scope={partition_field}:{partition_value} "
                    f"differences="
                    + json.dumps(
                        differences,
                        ensure_ascii=False,
                        sort_keys=True,
                        separators=(",", ":"),
                    )
                )
            pending_polling_rows = []

        if require_aggregate_for_each_block and pending_polling_rows:
            last = pending_polling_rows[-1]
            raise ValueError(
                "ELECTORAL_INPUT_INVALID "
                f"source={source} adapter={adapter_kind} "
                f"row={last['row']} field=record_classification "
                "value='open_polling_station_block' "
                "cause=MISSING_EXPECTED_AGGREGATE"
            )

        if not vote_rows:
            raise ValueError(
                f"No se pudieron extraer partidos del CSV ancho: {source}"
            )
        result = pd.DataFrame(vote_rows)
        result.attrs["recognized_aggregates"] = recognized_aggregates
        result.attrs["recognized_aggregate_rows"] = len(
            recognized_aggregates
        )
        result.attrs["polling_station_rows"] = polling_station_rows
        applicability_evidence = [
            {
                "party_column": party,
                "scope_field": scope_field,
                "scope_value": scope_value,
                "reason": reason,
                "source_id": source_id,
                "raw_sha256": raw_sha256,
                "polling_station_rows": count,
            }
            for (
                party,
                scope_field,
                scope_value,
                reason,
                source_id,
                raw_sha256,
            ), count in sorted(not_applicable_counts.items())
        ]
        result.attrs["structural_provenance"] = structural_evidence
        result.attrs["party_applicability"] = applicability_evidence
        result.attrs["not_applicable_party_cells"] = sum(
            int(item["polling_station_rows"])
            for item in applicability_evidence
        )
        result.attrs["record_classification"] = {
            "polling_station_rows": polling_station_rows,
            "recognized_aggregate_rows": len(recognized_aggregates),
            "invalid_rows": 0,
        }
        return _accepted(result), section_ids

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
    rejected_rows = sum(
        int(batch[0].attrs.get("rejected_rows", 0))
        for batch in result_batches
    )
    if rejected_rows != 0:
        raise ValueError(
            f"ELECTORAL_INPUT_REJECTED_ROWS: rejected_rows={rejected_rows}"
        )
    aggregate_evidence = [
        evidence
        for batch in result_batches
        for evidence in batch[0].attrs.get(
            "recognized_aggregates",
            [],
        )
    ]
    structural_provenance_evidence = [
        evidence
        for batch in result_batches
        for evidence in [batch[0].attrs.get("structural_provenance")]
        if evidence
    ]
    party_applicability_evidence = [
        evidence
        for batch in result_batches
        for evidence in batch[0].attrs.get(
            "party_applicability",
            [],
        )
    ]
    not_applicable_party_cells = sum(
        int(batch[0].attrs.get("not_applicable_party_cells", 0))
        for batch in result_batches
    )
    polling_station_rows = sum(
        int(batch[0].attrs.get("polling_station_rows", 0))
        for batch in result_batches
    )
    results = pd.concat(
        [batch[0] for batch in result_batches],
        ignore_index=True,
    )
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
    report["input_validation"] = {
        "rejected_rows": rejected_rows,
        "accepted_rows": int(len(results)),
        "polling_station_rows": polling_station_rows,
        "recognized_aggregate_rows": len(aggregate_evidence),
        "recognized_aggregates": aggregate_evidence,
        "aggregate_rows_counted_as_votes": 0,
        "structural_provenance": structural_provenance_evidence,
        "party_applicability": party_applicability_evidence,
        "not_applicable_party_cells": not_applicable_party_cells,
    }
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
