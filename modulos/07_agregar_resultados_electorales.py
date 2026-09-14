#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PROYECTO: Diputado de Distrito
Módulo 07 — Agregar resultados electorales
VERSIÓN: 7.2.0
NOMBRE DE VERSIÓN: Contrato electoral universal
FECHA: 2026-09-14
QUÉ HACE: verifica convocatoria, fuentes y partidos antes de agregar votos a distritos.
POR QUÉ ES SEPARADO: la elección nunca condiciona fronteras; M07 solo proyecta sobre M06.
ESTADO: vigente — R039
CAMBIOS: sustituye parámetros de proveedor incrustados por contrato, checksum, adaptador y diccionario.
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

    if adapter.get("kind") != "long_csv":
        raise ValueError(f"El contenido tabular requiere adaptador long_csv: {source}")
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
    assigned, report = reconcile_sections(
        mapping,
        section_party,
        section_field=section_field,
        district_field=district_field,
        policy=contract["reconciliation"],
        result_section_ids=result_section_ids,
    )
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
