#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


from ddd_core.m05_gerrychain_engine import (
    Contract,
    Weights,
    adapt_files,
    load_comarca_lookup,
)
from ddd_ensemble.candidate_metrics import measure_candidate
from ddd_ensemble.ensemble_assembler import assemble
from ddd_ensemble.ensemble_plan import (
    GERRYCHAIN50_ENTRYPOINT,
    PROFILES,
    build_gerrychain50_plan,
    build_plan,
)
from ddd_ensemble.gallery import build_gallery
from ddd_ensemble.prepared_bundle import validate_prepared_bundle
from ddd_ensemble.statistical_quality import (
    ChainQualityError,
    DegeneracyPolicy,
    StatisticalSamplingPolicy,
    aggregate_statistical_results,
    run_statistical_gerrychain,
    write_statistical_records,
)


SCHEMA = "ddd.ensemble-runner/1.0"


def _read(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


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


def ensure_plan(
    config: dict[str, Any],
    output: Path,
    count_override: int | None = None,
    seed_override: int | None = None,
) -> dict[str, Any]:
    ensemble = config.get("ensemble", {})
    count = count_override if count_override is not None else int(ensemble.get("candidate_count", 50))
    seed = seed_override if seed_override is not None else ensemble.get("seed")
    require_unique_hashes = ensemble.get("require_unique_hashes")
    entrypoint = str(ensemble.get("entrypoint") or "generic")
    if count == 50 and entrypoint != GERRYCHAIN50_ENTRYPOINT:
        raise ValueError(
            "candidate_count=50 requiere ensemble.entrypoint=gerrychain_50"
        )
    if entrypoint == GERRYCHAIN50_ENTRYPOINT:
        if seed is None:
            raise ValueError("GerryChain 50 requiere ensemble.seed o --seed")
        expected = build_gerrychain50_plan(
            config["territory_id"],
            config["prepared_bundle_id"],
            seed=int(seed),
            candidate_count=count,
            require_unique_hashes=(
                True if require_unique_hashes is None else require_unique_hashes
            ),
        )
    elif entrypoint == "generic":
        expected = build_plan(
            config["territory_id"],
            config["prepared_bundle_id"],
            count,
            seed=None if seed is None else int(seed),
            require_unique_hashes=None if require_unique_hashes is None else bool(require_unique_hashes),
        )
    else:
        raise ValueError(f"ensemble.entrypoint desconocido: {entrypoint}")
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
        preserve_atomic_multipart_sections=bool(
            topology.get("preserve_atomic_multipart_sections", False)
        ),
    )


def contract(config: dict[str, Any]) -> Contract:
    values = config["contract"]
    allowed = Contract.__dataclass_fields__.keys()
    return Contract(**{key: values[key] for key in allowed if key in values})


def _degeneracy_policy(config: dict[str, Any]) -> DegeneracyPolicy:
    values = config.get("statistical", {}).get("degeneracy_gate", {})
    return DegeneracyPolicy(
        min_unique_state_ratio=float(values.get("min_unique_state_ratio", 0.10)),
        max_self_loop_rate=float(values.get("max_self_loop_rate", 0.90)),
        require_full_length=bool(values.get("require_full_length", True)),
    )


def _sampling_policy(config: dict[str, Any]) -> StatisticalSamplingPolicy:
    values = config.get("statistical", {}).get("sampling", {})
    return StatisticalSamplingPolicy(max_samples=int(values.get("max_samples", 5000)))


def _valid_existing(report_path: Path, candidate_id: str) -> bool:
    manifest_path = report_path.parent / "candidate-manifest.json"
    if not report_path.is_file() or not manifest_path.is_file():
        return False
    try:
        report = _read(report_path)
        manifest = _read(manifest_path)
    except (OSError, json.JSONDecodeError):
        return False
    geojson = Path(report.get("geojson", ""))
    if not geojson.is_absolute():
        geojson = report_path.parent / geojson
    chain_quality = report.get("engine_run", {}).get("chain_quality", {})
    statistical_path = report_path.parent / "statistical-states.jsonl"
    assignment_hash = str(report.get("assignment_hash") or "")
    return (
        report.get("candidate_id") == candidate_id
        and manifest.get("candidate_id") == candidate_id
        and manifest.get("assignment_hash") == assignment_hash
        and assignment_hash
        and report.get("hard_constraints", {}).get("all_pass") is True
        and chain_quality.get("all_pass") is True
        and statistical_path.is_file()
        and geojson.is_file()
        and manifest.get("geojson_sha256") == _sha256_file(geojson)
        and manifest.get("report_sha256") == _sha256_file(report_path)
    )


def _clear_candidate_outputs(candidate_dir: Path) -> None:
    for name in (
        "candidate.geojson",
        "engine-report.json",
        "statistical-states.jsonl",
        "report.json",
        "candidate-manifest.json",
        "failure.json",
    ):
        (candidate_dir / name).unlink(missing_ok=True)


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
    degeneracy_policy = _degeneracy_policy(config)
    sampling_policy = _sampling_policy(config)
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
        _clear_candidate_outputs(candidate_dir)
        try:
            parameters = candidate["parameters"]
            geojson, engine_report, statistical_records = run_statistical_gerrychain(
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
                degeneracy_policy=degeneracy_policy,
                sampling_policy=sampling_policy,
            )
            geojson_path = candidate_dir / "candidate.geojson"
            _write(geojson_path, geojson)
            _write(candidate_dir / "engine-report.json", engine_report)
            write_statistical_records(candidate_dir / "statistical-states.jsonl", statistical_records)
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
            measured["territory_id"] = config["territory_id"]
            measured["prepared_bundle_id"] = config["prepared_bundle_id"]
            measured["assignment_hash"] = str(
                engine_report["selected_metrics"]["assignment_sha256"]
            )
            measured["metrics"]["stability"]["assignment_delta"] = float(
                engine_report["selected_metrics"]["assignment_churn"]
            )
            _write(report_path, measured)
            _write(candidate_dir / "candidate-manifest.json", {
                "schema": "ddd.candidate-manifest/1.0",
                "territory_id": config["territory_id"],
                "prepared_bundle_id": config["prepared_bundle_id"],
                "plan_sha256": plan["plan_sha256"],
                "candidate_id": candidate["candidate_id"],
                "profile": candidate["profile"],
                "seed": int(candidate["seed"]),
                "assignment_hash": measured["assignment_hash"],
                "k": int(ddd_contract.k),
                "section_count": int(measured["metrics"]["universe"]["section_count"]),
                "population_total": float(engine_report["selected_metrics"]["population_total"]),
                "hard_constraints_pass": True,
                "geojson": "candidate.geojson",
                "geojson_sha256": _sha256_file(geojson_path),
                "report": "report.json",
                "report_sha256": _sha256_file(report_path),
            })
            executed += 1
        except ChainQualityError as exc:
            _write(candidate_dir / "engine-report.json", exc.report)
            write_statistical_records(candidate_dir / "statistical-states.jsonl", exc.records)
            _write(candidate_dir / "failure.json", {
                "candidate_id": candidate["candidate_id"],
                "error_type": type(exc).__name__,
                "message": str(exc),
                "chain_quality": exc.report.get("chain_quality", {}),
            })
            failed += 1
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
    statistical = aggregate_statistical_results(
        output / "results",
        candidate_count_expected=int(summary["candidate_count_expected"]),
        candidate_gallery_count=int(summary["candidate_count_valid"]),
    )
    summary["statistical_ensemble"] = {
        "schema": statistical["schema"],
        "candidate_gallery_count": statistical["candidate_gallery_count"],
        "statistical_chain_count": statistical["statistical_chain_count"],
        "statistical_state_count": statistical["statistical_state_count"],
        "states_observed_total": statistical["states_observed_total"],
        "complete": statistical["complete"],
        "artifact": "statistical-summary.json",
    }
    summary["complete"] = bool(summary["complete"] and statistical["complete"])
    analysis_dir = output / "analysis"
    _write(analysis_dir / "summary.json", summary)
    _write(analysis_dir / "statistical-summary.json", statistical)
    _write(analysis_dir / "retry-matrix.json", summary["retry_matrix"])
    build_gallery(str(analysis_dir / "summary.json"), str(output / "site"))
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Ejecutor unificado DDD GerryChain + ensemble")
    parser.add_argument("--config", required=True)
    parser.add_argument("--mode", choices=("plan", "run", "assemble", "all"), default="all")
    parser.add_argument("--profile", choices=tuple(PROFILES))
    parser.add_argument("--count", type=int)
    parser.add_argument("--seed", type=int)
    parser.add_argument("--output")
    parser.add_argument("--allow-partial", action="store_true")
    args = parser.parse_args()

    config, base = load_config(args.config)
    validate_inputs(config, base)
    resolve_prepared_bundle_id(config, base)
    output = Path(args.output).resolve() if args.output else _path(base, config.get("output", "ensemble-output"))
    output.mkdir(parents=True, exist_ok=True)
    plan = ensure_plan(config, output, args.count, args.seed)
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
