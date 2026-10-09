#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import importlib.util
import hashlib
import json
import os
import time
from pathlib import Path

import yaml

from herramientas._resolver_ejecucion_completa_core import _hard_partition_spec


def _load_m04(root: Path):
    path = root / "modulos" / "04_generar_semillas.py"
    spec = importlib.util.spec_from_file_location("ddd_m04_entrypoint", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("no se puede cargar el punto de entrada de Formación inicial")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module



def _cusec_set_sha256(values) -> str:
    normalized = sorted(str(value).strip() for value in values)
    return hashlib.sha256(("\n".join(normalized) + "\n").encode("utf-8")).hexdigest()


def _section_ids(gdf, id_field: str, *, label: str) -> list[str]:
    if id_field not in gdf.columns:
        raise ValueError(f"MATERIALIZATION_DEFECT: {label} sin campo CUSEC contractual {id_field}")
    if gdf[id_field].isna().any():
        raise ValueError(f"MATERIALIZATION_DEFECT: {label} contiene CUSEC nulo")
    values = gdf[id_field].astype(str).str.strip()
    if (values == "").any():
        raise ValueError(f"MATERIALIZATION_DEFECT: {label} contiene CUSEC vacío")
    duplicated = sorted(values[values.duplicated(keep=False)].unique().tolist())
    if duplicated:
        raise ValueError(
            f"MATERIALIZATION_DEFECT: {label} contiene CUSEC duplicado; ejemplo={duplicated[:5]}"
        )
    return values.tolist()


def prepare(params_path: str | Path, run_id: str, *, root_dir: Path | None = None) -> dict:
    params = Path(params_path).resolve()
    root = (root_dir or Path.cwd()).resolve()
    contract = yaml.safe_load(params.read_text(encoding="utf-8")) or {}
    hard = _hard_partition_spec(contract, root)
    if not hard:
        raise ValueError("el contrato no declara hard_partition_mode=physical_components")

    previous_run_id = os.environ.get("DDD_RUN_ID")
    os.environ["DDD_RUN_ID"] = str(run_id)
    try:
        module = _load_m04(root)
        resolved = module.load_params_yaml(str(params))
        m04 = ((resolved.get("modulos") or {}).get("modulo_04_generar_semillas") or {})
        source = Path(str(m04.get("source_geojson") or ""))
        output = Path(str(m04.get("in_geojson") or ""))
        id_field = str(m04.get("id_field") or "")
        if not source.is_file():
            raise ValueError("MATERIALIZATION_DEFECT: fuente territorial de particiones inexistente")
        source_gdf = module.load_geo(source)
        input_ids = _section_ids(source_gdf, id_field, label="entrada territorial")
        try:
            module.prepare_hard_partitions(str(params))
        except SystemExit as exc:
            raise ValueError(f"MATERIALIZATION_DEFECT: {exc}") from exc
        if not output.is_file():
            raise ValueError("MATERIALIZATION_DEFECT: la entrada física de Formación inicial no fue materializada")
        gdf = module.load_geo(output)
        output_ids = _section_ids(gdf, id_field, label="salida de particiones")
    finally:
        if previous_run_id is None:
            os.environ.pop("DDD_RUN_ID", None)
        else:
            os.environ["DDD_RUN_ID"] = previous_run_id

    if len(input_ids) != len(output_ids) or set(input_ids) != set(output_ids):
        missing = sorted(set(input_ids) - set(output_ids))
        extra = sorted(set(output_ids) - set(input_ids))
        raise ValueError(
            "MATERIALIZATION_DEFECT: CUSEC input/output no se conservan "
            f"input={len(input_ids)} output={len(output_ids)} "
            f"missing={missing[:5]} extra={extra[:5]}"
        )

    field = hard["partition_field"]
    municipality_field = hard["municipality_field"]
    if field not in gdf.columns or municipality_field not in gdf.columns:
        raise ValueError("MATERIALIZATION_DEFECT: salida física sin campos contractuales de partición")
    if gdf[field].isna().any():
        missing = sorted(gdf.loc[gdf[field].isna(), id_field].astype(str).tolist())
        raise ValueError(f"MATERIALIZATION_DEFECT: secciones sin componente físico; ejemplo={missing[:5]}")
    partition_values = gdf[field].astype(str).str.strip()
    if (partition_values == "").any():
        missing = sorted(gdf.loc[partition_values == "", id_field].astype(str).tolist())
        raise ValueError(f"MATERIALIZATION_DEFECT: secciones con componente físico vacío; ejemplo={missing[:5]}")
    multiplicity = (
        gdf.assign(_DDD_PARTITION_CHECK=partition_values)
        .groupby(id_field)["_DDD_PARTITION_CHECK"]
        .nunique(dropna=False)
    )
    ambiguous = sorted(str(x) for x in multiplicity[multiplicity != 1].index.tolist())
    if ambiguous:
        raise ValueError(
            f"MATERIALIZATION_DEFECT: CUSEC con pertenencia física no unívoca; ejemplo={ambiguous[:5]}"
        )

    input_hash = _cusec_set_sha256(input_ids)
    output_hash = _cusec_set_sha256(output_ids)
    if input_hash != hard["universe_cusec_set_sha256"] or output_hash != hard["universe_cusec_set_sha256"]:
        raise ValueError(
            "PHYSICAL_COMPONENT_INVENTORY_MISMATCH: universo CUSEC no coincide con inventario acreditado "
            f"inventory={hard['inventory_id']} esperado={hard['universe_cusec_set_sha256']} "
            f"input={input_hash} output={output_hash}"
        )

    actual_sections = {}
    actual_hashes = {}
    for component, rows in gdf.assign(_DDD_PARTITION_CHECK=partition_values).groupby("_DDD_PARTITION_CHECK"):
        ids = rows[id_field].astype(str).tolist()
        actual_sections[str(component)] = len(ids)
        actual_hashes[str(component)] = _cusec_set_sha256(ids)

    if set(actual_sections) != set(hard["component_sections"]):
        raise ValueError(
            "PHYSICAL_COMPONENT_INVENTORY_MISMATCH: conjunto de componentes materializado no coincide "
            f"esperado={sorted(hard['component_sections'])} actual={sorted(actual_sections)}"
        )
    failures = {}
    for component in sorted(hard["component_sections"]):
        expected_count = hard["component_sections"][component]
        expected_hash = hard["component_cusec_set_sha256"][component]
        if actual_sections[component] != expected_count or actual_hashes[component] != expected_hash:
            failures[component] = {
                "expected_count": expected_count,
                "actual_count": actual_sections[component],
                "expected_cusec_set_sha256": expected_hash,
                "actual_cusec_set_sha256": actual_hashes[component],
            }
    if failures:
        raise ValueError(
            "PHYSICAL_COMPONENT_INVENTORY_MISMATCH: CUSEC por componente no coincide con inventario acreditado "
            + json.dumps(failures, ensure_ascii=False, sort_keys=True)
        )

    return {
        "schema": "ddd.internal-units-job/1.1",
        "status": "PREPARED",
        "strategy": "physical_components",
        "run_id": str(run_id),
        "input_geojson": hard["source_geojson"],
        "output_geojson": str(output),
        "hard_partition_lookup": hard["lookup"],
        "hard_partition_lookup_sha256": hard["lookup_sha256"],
        "inventory_id": hard["inventory_id"],
        "source_identity": hard["source_identity"],
        "partition_field": field,
        "municipality_field": municipality_field,
        "input_section_count": len(input_ids),
        "output_section_count": len(output_ids),
        "input_output_cusec_equal": True,
        "universe_cusec_set_sha256": output_hash,
        "component_sections": hard["component_sections"],
        "component_cusec_set_sha256": hard["component_cusec_set_sha256"],
        "component_districts": hard["component_districts"],
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--params", required=True)
    ap.add_argument("--run-id", default="")
    ap.add_argument("--job-report", required=True)
    args = ap.parse_args()
    started = time.monotonic()
    payload = {
        "schema": "ddd.internal-units-job/1.0",
        "run_id": str(args.run_id),
        "started_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
    }
    try:
        payload.update(prepare(args.params, args.run_id))
    except Exception as exc:
        payload.update({"status": "BLOCKED", "error": f"{type(exc).__name__}: {exc}"})
        Path(args.job_report).parent.mkdir(parents=True, exist_ok=True)
        payload["finished_at_utc"] = dt.datetime.now(dt.timezone.utc).isoformat()
        payload["duration_seconds"] = round(time.monotonic() - started, 6)
        Path(args.job_report).write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        raise SystemExit(f"[PARTICIONES FÍSICAS] BLOCKED: {exc}")
    payload["finished_at_utc"] = dt.datetime.now(dt.timezone.utc).isoformat()
    payload["duration_seconds"] = round(time.monotonic() - started, 6)
    Path(args.job_report).parent.mkdir(parents=True, exist_ok=True)
    Path(args.job_report).write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False))


if __name__ == "__main__":
    main()
