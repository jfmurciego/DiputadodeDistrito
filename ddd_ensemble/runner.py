#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


from ddd_core.m05_gerrychain_engine import (
    Contract,
    Weights,
    adapt_files,
    load_comarca_lookup,
    run_gerrychain,
)
from ddd_ensemble.candidate_metrics import measure_candidate
from ddd_ensemble.ensemble_assembler import assemble
from ddd_ensemble.ensemble_plan import PROFILES, build_plan
from ddd_ensemble.gallery import build_gallery
from ddd_ensemble.prepared_bundle import validate_prepared_bundle


SCHEMA = "ddd.ensemble-runner/1.0"


def _read(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def load_config(path: str) -> tuple[dict[str, Any], Path]:
    config_path = Path(path).resolve()
    config = _read(config_path)
    if config.get("schema") != SCHEMA:
        raise ValueError(f"Esquema requerido: {SCHEMA}")
    for key in ("territory_id", "prepared_bundle_id", "inputs", "fields", "contract", "engine"):
        if key not in config:
            raise ValueError(f"Falta {key} en la configuración")
    if config["engine"].get("id") != "gerrychain_recom":
        raise ValueError("Este candidato solo admite el motor gerrychain_recom")
    return config, config_path.parent


def _path(base: Path, value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else (base / path).resolve()


def _initial_geojson_key(inputs: dict[str, Any]) -> str:
    if inputs.get("initial_geojson"):
        return "initial_geojson"
    if inputs.get("m04_initial_geojson"):
        return "m04_initial_geojson"
    raise ValueError("Falta inputs.initial_geojson")


def validate_inputs(config: dict[str, Any], base: Path) -> None:
    inputs = config["inputs"]
    if inputs.get("prepared_bundle"):
        result = validate_prepared_bundle(
            str(_path(base, inputs["prepared_bundle"])), config["territory_id"]
        )
        if result.manifest["bundle_id"] != config["prepared_bundle_id"]:
            raise ValueError("prepared_bundle_id no coincide con el manifiesto")
    for key in ("m03_graph", _initial_geojson_key(inputs)):
        if not _path(base, inputs[key]).is_file():
            raise FileNotFoundError(f"No existe {key}: {_path(base, inputs[key])}")


def resolve_prepared_bundle_id(config: dict[str, Any], base: Path) -> None:
    """Vincula las semillas al contenido real cuando el identificador es AUTO."""
    if config["prepared_bundle_id"] != "AUTO":
        return
    import hashlib

    digest = hashlib.sha256()
    for key in ("m03_graph", _initial_geojson_key(config["inputs"]), "comarca_lookup"):
        value = config["inputs"].get(key)
        if value:
            digest.update(key.encode("utf-8"))
            digest.update(_path(base, value).read_bytes())
    config["prepared_bundle_id"] = f"sha256:{digest.hexdigest()}"


def plan_path(output: Path) -> Path:
    return output / "plan.json"


def ensure_plan(config: dict[str, Any], output: Path, count_override: int | None = None) -> dict[str, Any]:
    count = count_override or int(config.get("ensemble", {}).get("candidate_count", 50))
    expected = build_plan(config["territory_id"], config["prepared_bundle_id"], count)
    path = plan_path(output)
    if path.exists():
        current = _read(path)
        if current.get("plan_sha256") != expected["plan_sha256"]:
            raise ValueError("El plan existente no coincide; use otro directorio de salida")
        return current
    _write(path, expected)
    return expected


def adapt(config: dict[str, Any], base: Path):
    inputs, fields = config["inputs"], config["fields"]
    topology = config.get("topology", {})
    comarca_lookup = None
    if inputs.get("comarca_lookup"):
        columns = config.get("comarca_lookup_columns", {})
        comarca_lookup = load_comarca_lookup(
            _path(base, inputs["comarca_lookup"]),
            municipality_col=columns.get("municipality", "Municipio código"),
            comarca_code_col=columns.get("comarca_code", "Comarca código"),
            comarca_name_col=columns.get("comarca_name", "Comarca nombre"),
        )
    return adapt_files(
        _path(base, inputs["m03_graph"]),
        _path(base, inputs[_initial_geojson_key(inputs)]),
        section_field=fields["section"],
        district_field=fields["district"],
        municipality_field=fields["municipality"],
        province_field=fields["province"],
        population_field=fields.get("population"),
        atomic_unit_field=fields.get("atomic_unit", "ddd_unit_id"),
        closed_urban_field=fields.get("closed_urban", "ddd_closed_urban"),
        comarca_code_fields=tuple(fields.get("comarca_code_candidates", [fields.get("comarca", "COMARCA_COD")])),
        comarca_name_fields=tuple(fields.get("comarca_name_candidates", ["COMARCA_NOM"])),
        comarca_lookup=comarca_lookup,
        comarca_enabled=bool(config.get("comarca", {}).get("enabled", False)),
        min_shared_border_m=float(topology.get("min_shared_border_m", 0.0)),
    )


def contract(config: dict[str, Any]) -> Contract:
    values = config["contract"]
    allowed = Contract.__dataclass_fields__.keys()
    return Contract(**{key: values[key] for key in allowed if key in values})


def _valid_existing(report_path: Path, candidate_id: str) -> bool:
    if not report_path.is_file():
        return False
    try:
        report = _read(report_path)
    except (OSError, json.JSONDecodeError):
        return False
    geojson = Path(report.get("geojson", ""))
    if not geojson.is_absolute():
        geojson = report_path.parent / geojson
    return (
        report.get("candidate_id") == candidate_id
        and report.get("hard_constraints", {}).get("all_pass") is True
        and geojson.is_file()
    )


def run_candidates(
    config: dict[str, Any],
    base: Path,
    output: Path,
    plan: dict[str, Any],
    profile: str | None,
) -> dict[str, int]:
    if profile and profile not in PROFILES:
        raise ValueError(f"Perfil desconocido: {profile}")
    data = adapt(config, base)
    ddd_contract = contract(config)
    fields = config["fields"]
    steps = int(config["engine"].get("steps", 1000))
    executed = skipped = failed = 0
    for candidate in plan["candidates"]:
        if profile and candidate["profile"] != profile:
            continue
        candidate_dir = output / "results" / candidate["candidate_id"]
        report_path = candidate_dir / "report.json"
        if _valid_existing(report_path, candidate["candidate_id"]):
            skipped += 1
            continue
        candidate_dir.mkdir(parents=True, exist_ok=True)
        try:
            parameters = candidate["parameters"]
            geojson, engine_report = run_gerrychain(
                data,
                ddd_contract,
                total_steps=steps,
                seed=int(candidate["seed"]),
                comarca_surcharge=float(parameters["comarca_surcharge"]),
                weights=Weights(
                    population=float(parameters["population"]),
                    cut_edges=float(config["engine"].get("cut_edges_weight", 0.20)),
                    geometric_shape=float(parameters["shape"])
                    * float(config["engine"].get("geometric_shape_weight_scale", 1.0)),
                    comarca_fragmentation=float(parameters["comarca"]),
                    churn=float(config["engine"].get("churn_weight", 0.05)),
                ),
            )
            geojson_path = candidate_dir / "candidate.geojson"
            _write(geojson_path, geojson)
            _write(candidate_dir / "engine-report.json", engine_report)
            measured = measure_candidate(
                str(geojson_path),
                candidate["candidate_id"],
                candidate["profile"],
                int(candidate["seed"]),
                district_field=fields["district"],
                population_field=fields["population"],
                municipality_field=fields["municipality"],
                comarca_field=fields.get("comarca", "COMARCA_COD"),
                hard_constraints=engine_report["hard_constraints"],
                engine_run=engine_report,
            )
            # Ruta portable entre artifacts/jobs de GitHub Actions.
            measured["geojson"] = "candidate.geojson"
            measured["metrics"]["stability"]["assignment_delta"] = float(
                engine_report["selected_metrics"]["assignment_churn"]
            )
            _write(report_path, measured)
            executed += 1
        except Exception as exc:  # El lote continúa y la reanudación apunta al fallo.
            _write(candidate_dir / "failure.json", {
                "candidate_id": candidate["candidate_id"],
                "error_type": type(exc).__name__,
                "message": str(exc),
            })
            failed += 1
    return {"executed": executed, "skipped": skipped, "failed": failed}


def finish(output: Path, shortlist_size: int) -> dict[str, Any]:
    summary = assemble(str(plan_path(output)), str(output / "results"), shortlist_size)
    analysis_dir = output / "analysis"
    _write(analysis_dir / "summary.json", summary)
    _write(analysis_dir / "retry-matrix.json", summary["retry_matrix"])
    build_gallery(str(analysis_dir / "summary.json"), str(output / "site"))
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Ejecutor unificado DDD GerryChain + ensemble")
    parser.add_argument("--config", required=True)
    parser.add_argument("--mode", choices=("plan", "run", "assemble", "all"), default="all")
    parser.add_argument("--profile", choices=tuple(PROFILES))
    parser.add_argument("--count", type=int)
    parser.add_argument("--output")
    parser.add_argument("--allow-partial", action="store_true")
    args = parser.parse_args()

    config, base = load_config(args.config)
    validate_inputs(config, base)
    resolve_prepared_bundle_id(config, base)
    output = Path(args.output).resolve() if args.output else _path(base, config.get("output", "ensemble-output"))
    output.mkdir(parents=True, exist_ok=True)
    plan = ensure_plan(config, output, args.count)
    result: dict[str, Any] = {"mode": args.mode, "output": str(output), "plan_sha256": plan["plan_sha256"]}
    if args.mode in ("run", "all"):
        result["run"] = run_candidates(config, base, output, plan, args.profile)
    if args.mode in ("assemble", "all"):
        result["summary"] = finish(output, int(config.get("ensemble", {}).get("shortlist_size", 10)))
    _write(output / "last-run.json", result)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if result.get("summary", {}).get("complete") is False and not args.allow_partial:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
