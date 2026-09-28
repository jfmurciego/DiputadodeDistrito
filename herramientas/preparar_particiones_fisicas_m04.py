#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import importlib.util
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
        module.prepare_hard_partitions(str(params))
        resolved = module.load_params_yaml(str(params))
        m04 = ((resolved.get("modulos") or {}).get("modulo_04_generar_semillas") or {})
        output = Path(str(m04.get("in_geojson") or ""))
        if not output.is_file():
            raise RuntimeError("la entrada física de Formación inicial no fue materializada")
        gdf = module.load_geo(output)
    finally:
        if previous_run_id is None:
            os.environ.pop("DDD_RUN_ID", None)
        else:
            os.environ["DDD_RUN_ID"] = previous_run_id

    field = hard["partition_field"]
    municipality_field = hard["municipality_field"]
    if field not in gdf.columns or municipality_field not in gdf.columns:
        raise ValueError("la entrada física no contiene los campos contractuales de partición")
    actual = {str(k): int(v) for k, v in gdf[field].astype(str).value_counts().to_dict().items()}
    if actual != hard["component_sections"]:
        raise ValueError(
            "inventario de secciones por componente no coincide: "
            f"esperado={hard['component_sections']} actual={actual}"
        )
    if int(len(gdf)) != hard["expected_graph_nodes"]:
        raise ValueError("la entrada física no conserva el inventario de secciones")

    return {
        "schema": "ddd.internal-units-job/1.0",
        "status": "PREPARED",
        "strategy": "physical_components",
        "run_id": str(run_id),
        "input_geojson": hard["source_geojson"],
        "output_geojson": str(output),
        "hard_partition_lookup": hard["lookup"],
        "hard_partition_lookup_sha256": hard["lookup_sha256"],
        "partition_field": field,
        "municipality_field": municipality_field,
        "component_sections": hard["component_sections"],
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
