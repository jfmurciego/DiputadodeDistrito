#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PROYECTO: Diputado de Distrito
Módulo 07 — Agregar resultados electorales
VERSIÓN: 7.1.0
NOMBRE DE VERSIÓN: Reconciliación íntegra y código auditable
FECHA: 2026-09-13
QUÉ HACE: agrega votos a distritos y publica toda discrepancia entre resultados y mapa.
POR QUÉ ES SEPARADO: la elección nunca condiciona fronteras; M07 solo proyecta sobre M06.
ESTADO: vigente — Paquete A, C-05/C-09
CAMBIOS: sustituye el inner join silencioso por left join reconciliado e informe obligatorio.
MOTIVO: impedir la pérdida silenciosa de votos y hacer revisable el módulo electoral.
ANTERIOR: legacy/modulo07/07_agregar_resultados_electorales_v7.0.1.py
"""
from __future__ import annotations

import argparse
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


def norm_party(value):
    return re.sub(r"\s+", " ", str(value or "").strip())


def read_results(path, config, section_field):
    source = Path(path)
    text = source.read_text(encoding="utf-8", errors="replace").lstrip()
    if text.startswith(("{", "[")):
        obj = json.loads(text)
        zones = dotted(obj, config.get("json_rtve_zonas_path", "mapa.zonas"))
        rows = []
        section_ids = set()
        section_key = config.get("json_rtve_section_field", "cod")
        party_list = config.get("json_rtve_party_list_field", "lp")
        party_key = config.get("json_rtve_party_field", "s")
        votes_key = config.get("json_rtve_votes_field", "v")
        for zone in zones or []:
            section_id = zone.get(section_key)
            if section_id is not None:
                section_ids.add(str(section_id))
            for item in zone.get(party_list, []) or []:
                try:
                    votes = int(float(item.get(votes_key, 0)))
                except (TypeError, ValueError):
                    continue
                party = norm_party(item.get(party_key))
                if section_id is not None and party:
                    rows.append({section_field: str(section_id), "party": party, "votes": votes})
        if not rows:
            raise ValueError(f"No se pudieron extraer votos del JSON: {source}")
        return pd.DataFrame(rows), section_ids

    first = text.splitlines()[0] if text else ""
    separator = ";" if first.count(";") > first.count(",") else ","
    frame = pd.read_csv(io.StringIO(text), sep=separator, dtype=str)
    party_col = config.get("party_col", "PARTIDO")
    votes_col = config.get("votes_col", "VOTOS")
    candidates = [section_field, "CUSEC_KEY", "CUSEC", "CESUC", "SECCION"]
    section_source = next((column for column in candidates if column in frame.columns), None)
    if not section_source or party_col not in frame.columns or votes_col not in frame.columns:
        raise ValueError("CSV electoral no cumple contrato long section/party/votes")
    result = frame[[section_source, party_col, votes_col]].rename(
        columns={section_source: section_field, party_col: "party", votes_col: "votes"}
    )
    result[section_field] = result[section_field].astype(str)
    section_ids = set(result[section_field])
    result["party"] = result["party"].map(norm_party)
    result["votes"] = pd.to_numeric(result["votes"], errors="coerce").fillna(0).astype("int64")
    result = result.loc[result["party"] != ""].copy()
    return result, section_ids


def electoral_outputs(assigned, district_field, blocs):
    by_party = assigned.groupby([district_field, "party"], as_index=False)["votes"].sum()
    by_party = by_party.rename(columns={district_field: "district_id"})
    by_party["bloc"] = by_party["party"].map(lambda party: blocs.get(party, ""))
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
    files = require(m07.get("results_files"), "Falta M07 resultados")
    report_path = require(
        m07.get("out_reconciliation_report"),
        "Falta M07 informe de reconciliación",
    )

    gdf = load_geo(input_geo)
    mapping = gdf[[section_field, district_field]].copy()
    result_batches = [read_results(path, m07, section_field) for path in files]
    results = pd.concat([batch[0] for batch in result_batches], ignore_index=True)
    result_section_ids = set().union(*(batch[1] for batch in result_batches))
    results["party"] = results["party"].map(norm_party)
    section_party = results.groupby([section_field, "party"], as_index=False)["votes"].sum()
    assigned, report = reconcile_sections(
        mapping,
        section_party,
        section_field=section_field,
        district_field=district_field,
        policy=m07.get("reconciliation") or {},
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
        m07.get("blocs", {}) or {},
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
