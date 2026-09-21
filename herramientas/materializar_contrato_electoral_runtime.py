#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

import yaml


def materialize(params: Path, validation: Path, output: Path) -> Path:
    cfg = yaml.safe_load(params.read_text(encoding="utf-8")) or {}
    result = json.loads(validation.read_text(encoding="utf-8"))
    if result.get("decision") != "READY_PACKAGE":
        raise ValueError("La validación electoral no está READY_PACKAGE")

    runtime_contract = str(result.get("runtime_contract_path") or "")
    if not runtime_contract:
        raise ValueError("La validación electoral no publica runtime_contract_path")

    modules = cfg.setdefault("modulos", {})
    m06 = modules.get("modulo_06_consolidar_distritos") or {}
    existing_m07 = modules.get("modulo_07_agregar_resultados_electorales") or {}

    # Los contratos históricos ya materializados (Galicia/Aragón/CyL) permanecen
    # intactos. Sólo se genera overlay para territorios sin M07/M08 productivo.
    if existing_m07.get("election_contract"):
        return params

    cache_dir = str(((cfg.get("io") or {}).get("cache") or {}).get("dir") or ".cache/ddd/preparacion/{run_name}")
    id_field = str(m06.get("id_field") or "CUSEC_KEY")
    district_field = str(m06.get("district_field") or "district_id")
    m06_sections = m06.get("out_geojson")
    m06_districts = m06.get("out_district_geojson")
    if not m06_sections or not m06_districts:
        raise ValueError("M06 no declara geometrías requeridas para construir M07/M08")

    m07 = {
        "in_geojson": m06_sections,
        "section_id_field": id_field,
        "district_field": district_field,
        "election_contract": runtime_contract,
        "out_district_party_csv": f"{cache_dir}/{{run_name}}_m07_resultados_partido.csv",
        "out_district_summary_csv": f"{cache_dir}/{{run_name}}_m07_resumen_electoral.csv",
        "out_reconciliation_report": f"{cache_dir}/{{run_name}}_m07_reconciliacion.json",
        "out_sections_enriched_geojson": f"{cache_dir}/{{run_name}}_m07_secciones_resultados.geojson.zip",
    }
    m08 = {
        "in_district_geojson": m06_districts,
        "in_district_summary_csv": m07["out_district_summary_csv"],
        "out_districts_with_results_geojson": f"{cache_dir}/{{run_name}}_m08_distritos_resultados.geojson.zip",
    }
    modules["modulo_07_agregar_resultados_electorales"] = m07
    modules["modulo_08_integrar_resultados"] = m08

    # El contrato runtime vive fuera del directorio territorial original. Recalcular
    # project_root preserva exactamente el mismo root lógico que tenía el contrato
    # M01–M06 y evita que ../../.. desde .ddd-electoral-runtime apunte a '/'.
    io_cfg = cfg.setdefault("io", {})
    project_root_cfg = io_cfg.setdefault("project_root", {})
    original_raw = str(project_root_cfg.get("path") or "")
    if original_raw:
        original_path = Path(original_raw).expanduser()
        original_root = original_path.resolve() if original_path.is_absolute() else (params.resolve().parent / original_path).resolve()
    else:
        original_root = params.resolve().parent
    output_parent = output.resolve().parent
    project_root_cfg["path"] = os.path.relpath(original_root, output_parent)
    cfg.setdefault("_runtime", {})["electoral_contract_mode"] = result.get("mode")
    cfg["_runtime"]["electoral_package_election_id"] = result.get("election_id")

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(yaml.safe_dump(cfg, sort_keys=False, allow_unicode=True), encoding="utf-8")
    return output


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--params", type=Path, required=True)
    ap.add_argument("--validation", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    path = materialize(args.params, args.validation, args.output)
    print(path.as_posix())


if __name__ == "__main__":
    main()
