#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PROYECTO: Diputado de Distrito
Módulo 07 — Agregar resultados electorales
VERSIÓN: 7.3.0
NOMBRE DE VERSIÓN: Contrato electoral universal
FECHA: 2026-09-14
QUÉ HACE: verifica convocatoria, fuentes y partidos antes de agregar votos a distritos.
POR QUÉ ES SEPARADO: la elección nunca condiciona fronteras; M07 solo proyecta sobre M06.
ESTADO: vigente — R039
CAMBIOS: añade reconciliación declarativa de cambios de seccionado 2023→2025 con aliases 1:1 y splits ponderados por población, conservando exactamente los votos.
MOTIVO: permitir nuevas elecciones sin tablas ni lógica territorial en M07.
ANTERIOR: legacy/modulo07/07_agregar_resultados_electorales_v7.1.0.py
"""
from __future__ import annotations

import argparse
import io
import json
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


def read_results(path, adapter, section_field, parties: PartyDictionary):
    source = Path(path)
    text = source.read_text(encoding="utf-8", errors="replace").lstrip()
    if text.startswith(("{", "[")):
        obj = json.loads(text)
        if adapter.get("kind") != "nested_json":
            raise ValueError(f"El contenido JSON requiere adaptador nested_json: {source}")
        zones = dotted(obj, require(adapter.get("records_path"), "Falta records_path"))
        rows = []
        section_ids = set()
        section_key = require(adapter.get("section_field"), "Falta section_field")
        party_list = require(adapter.get("party_records_field"), "Falta party_records_field")
        party_key = require(adapter.get("party_field"), "Falta party_field")
        votes_key = require(adapter.get("votes_field"), "Falta votes_field")
        for zone in zones or []:
            section_id = zone.get(section_key)
            if section_id is not None:
                section_ids.add(str(section_id))
            for item in zone.get(party_list, []) or []:
                try:
                    votes = int(float(item.get(votes_key, 0)))
                except (TypeError, ValueError):
                    continue
                party = parties.canonicalize(item.get(party_key))
                if section_id is not None and party:
                    rows.append({section_field: str(section_id), "party": party, "votes": votes})
        if not rows:
            raise ValueError(f"No se pudieron extraer votos del JSON: {source}")
        return pd.DataFrame(rows), section_ids

    if adapter.get("kind") == "wide_polling_station_csv":
        first = text.splitlines()[0] if text else ""
        separator = adapter.get("separator", "auto")
        if separator == "auto":
            separator = ";" if first.count(";") > first.count(",") else ","
        frame = pd.read_csv(io.StringIO(text), sep=separator, dtype=str)
        province_field = require(adapter.get("province_field"), "Falta province_field")
        municipality_field = require(adapter.get("municipality_field"), "Falta municipality_field")
        polling_field = require(adapter.get("polling_station_field"), "Falta polling_station_field")
        polling_regex = require(adapter.get("polling_station_regex"), "Falta polling_station_regex")
        party_columns = require(adapter.get("party_columns"), "Falta party_columns")
        missing = [c for c in [province_field, municipality_field, polling_field, *party_columns] if c not in frame.columns]
        if missing:
            raise ValueError(f"CSV electoral ancho carece de columnas: {missing}")
        match = frame[polling_field].fillna("").str.extract(polling_regex)
        if not {"district", "section"}.issubset(match.columns):
            raise ValueError("polling_station_regex debe exponer grupos district y section")
        valid = (
            match["district"].notna()
            & match["section"].notna()
            & frame[province_field].fillna("").str.fullmatch(r"\d+")
            & frame[municipality_field].fillna("").str.fullmatch(r"\d+")
        )
        frame = frame.loc[valid].copy()
        match = match.loc[valid]
        frame[section_field] = (
            frame[province_field].astype(str).str.zfill(int(adapter.get("province_width", 2)))
            + frame[municipality_field].astype(str).str.zfill(int(adapter.get("municipality_width", 3)))
            + match["district"].astype(str).str.zfill(int(adapter.get("district_width", 2)))
            + match["section"].astype(str).str.zfill(int(adapter.get("section_width", 3)))
        )
        section_ids = set(frame[section_field])
        rows = []
        for raw_party in party_columns:
            canonical = parties.canonicalize(raw_party)
            batch = frame[[section_field, raw_party]].rename(columns={raw_party: "votes"})
            batch["party"] = canonical
            batch["votes"] = pd.to_numeric(batch["votes"], errors="coerce").fillna(0).astype("int64")
            rows.append(batch[[section_field, "party", "votes"]])
        if not rows:
            raise ValueError(f"No se pudieron extraer partidos del CSV ancho: {source}")
        return pd.concat(rows, ignore_index=True), section_ids

    if adapter.get("kind") != "long_csv":
        raise ValueError(f"El contenido tabular requiere adaptador long_csv o wide_polling_station_csv: {source}")
    first = text.splitlines()[0] if text else ""
    separator = adapter.get("separator", "auto")
    if separator == "auto":
        separator = ";" if first.count(";") > first.count(",") else ","
    frame = pd.read_csv(io.StringIO(text), sep=separator, dtype=str)
    section_source = require(adapter.get("section_field"), "Falta section_field")
    party_col = require(adapter.get("party_field"), "Falta party_field")
    votes_col = require(adapter.get("votes_field"), "Falta votes_field")
    if not section_source or party_col not in frame.columns or votes_col not in frame.columns:
        raise ValueError("CSV electoral no cumple contrato long section/party/votes")
    result = frame[[section_source, party_col, votes_col]].rename(
        columns={section_source: section_field, party_col: "party", votes_col: "votes"}
    )
    result[section_field] = result[section_field].astype(str)
    section_ids = set(result[section_field])
    result["party"] = result["party"].map(parties.canonicalize)
    result["votes"] = pd.to_numeric(result["votes"], errors="coerce").fillna(0).astype("int64")
    result = result.loc[result["party"] != ""].copy()
    return result, section_ids



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
    policy = contract.get("section_reconciliation") or {}
    aliases = policy.get("aliases") or []
    splits = policy.get("splits") or []
    if not aliases and not splits:
        return section_party, {"status": "NOT_REQUIRED", "aliases": [], "splits": [], "votes_before": int(section_party["votes"].sum()), "votes_after": int(section_party["votes"].sum())}

    out = section_party.copy()
    out[section_field] = out[section_field].astype(str)
    votes_before = int(out["votes"].sum())
    evidence = {"status": "APPLIED", "aliases": [], "splits": [], "votes_before": votes_before}

    alias_map = {}
    for item in aliases:
        source = str(require(item.get("from"), "Alias electoral sin from"))
        target = str(require(item.get("to"), "Alias electoral sin to"))
        if source in alias_map and alias_map[source] != target:
            raise ValueError(f"Alias electoral ambiguo para {source}")
        alias_map[source] = target
        evidence["aliases"].append({"from": source, "to": target, "method": item.get("method")})
    if alias_map:
        out[section_field] = out[section_field].map(lambda value: alias_map.get(str(value), str(value)))
        out = out.groupby([section_field, "party"], as_index=False)["votes"].sum()

    for rule in splits:
        source = str(require(rule.get("source_section"), "Split electoral sin source_section"))
        targets = [str(value) for value in require(rule.get("target_sections"), "Split electoral sin target_sections")]
        if len(targets) < 2 or source not in targets:
            raise ValueError(f"Split electoral inválido para {source}: {targets}")
        if str(rule.get("weighting") or "") != "current_population":
            raise ValueError(f"Weighting no soportado en split {source}: {rule.get('weighting')}")
        population_field = str(require(rule.get("population_field"), f"Split {source} sin population_field"))
        if population_field not in gdf.columns:
            raise ValueError(f"Split {source}: falta {population_field} en geometría territorial")
        map_rows = gdf[[section_field, population_field]].copy()
        map_rows[section_field] = map_rows[section_field].astype(str)
        if map_rows[section_field].duplicated().any():
            raise ValueError("La geometría territorial contiene secciones duplicadas al reconciliar elecciones")
        weights = {}
        for target in targets:
            rows = map_rows.loc[map_rows[section_field] == target, population_field]
            if len(rows) != 1:
                raise ValueError(f"Split {source}: target {target} ausente o duplicado")
            weights[target] = float(pd.to_numeric(rows.iloc[0], errors="raise"))
        source_rows = out.loc[out[section_field] == source].copy()
        if source_rows.empty:
            raise ValueError(f"Split declarado pero source_section ausente de resultados: {source}")
        out = out.loc[out[section_field] != source].copy()
        allocated = []
        source_total = int(source_rows["votes"].sum())
        for row in source_rows.itertuples(index=False):
            party = getattr(row, "party")
            votes = int(getattr(row, "votes"))
            allocation = _largest_remainder(votes, [(target, weights[target]) for target in targets])
            for target, amount in allocation.items():
                allocated.append({section_field: target, "party": party, "votes": amount})
        out = pd.concat([out, pd.DataFrame(allocated)], ignore_index=True)
        out = out.groupby([section_field, "party"], as_index=False)["votes"].sum()
        evidence["splits"].append({
            "source_section": source,
            "target_sections": targets,
            "population_field": population_field,
            "weights": weights,
            "votes_reallocated": source_total,
            "method": "current_population_largest_remainder",
            "spatial_evidence": rule.get("spatial_evidence"),
        })

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
    input_geo = require(m07.get("in_geojson"), "Falta M07 geometría")
    section_field = require(m07.get("section_id_field"), "Falta M07 section_id")
    district_field = require(m07.get("district_field"), "Falta M07 district_id")
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
    mapping = gdf[[section_field, district_field]].copy()
    result_batches = [
        read_results(source["resolved_path"], source["adapter"], section_field, parties)
        for source in contract["sources"]
    ]
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
    assigned, report = reconcile_sections(
        mapping,
        section_party,
        section_field=section_field,
        district_field=district_field,
        policy=contract["reconciliation"],
        result_section_ids=result_section_ids,
    )
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
        write_geo(enriched, out_enriched)

    print(
        f"[Módulo 7] OK status={report['status']} "
        f"districts={len(summary)} unassigned_votes={report['unassigned_votes']}"
    )


if __name__ == "__main__":
    main()
