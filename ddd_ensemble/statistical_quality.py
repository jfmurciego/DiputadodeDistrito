"""Statistical quality layer for the GerryChain ensemble subsystem.

This module deliberately lives outside the canonical M01-M06 engine. It
separates two products that had previously been conflated:

* the candidate gallery: one optimized/best state per chain; and
* the statistical ensemble: compact metric observations from visited states.

No full geometry is retained for statistical observations.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import json
import math
import random
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from ddd_core.m05_gerrychain_engine import (
    AdaptedInputs,
    Contract,
    InputContractError,
    Weights,
    assignment_hash,
    hard_constraint_violations,
    output_geojson,
    plan_metrics,
    score_metrics,
)


STATISTICAL_STATE_SCHEMA = "ddd.statistical-state/1.0"
STATISTICAL_SUMMARY_SCHEMA = "ddd.statistical-ensemble-summary/1.0"


@dataclass(frozen=True)
class DegeneracyPolicy:
    """Minimal pathology gate; passing it is not evidence of Markov-chain mixing."""

    min_unique_state_ratio: float = 0.10
    max_self_loop_rate: float = 0.90
    require_full_length: bool = True

    def __post_init__(self) -> None:
        if not 0.0 < self.min_unique_state_ratio <= 1.0:
            raise ValueError("min_unique_state_ratio debe estar en (0, 1]")
        if not 0.0 <= self.max_self_loop_rate < 1.0:
            raise ValueError("max_self_loop_rate debe estar en [0, 1)")


@dataclass(frozen=True)
class StatisticalSamplingPolicy:
    """Uniform reservoir of compact observations; never retains state geometry."""

    max_samples: int = 5000

    def __post_init__(self) -> None:
        if self.max_samples < 1:
            raise ValueError("max_samples debe ser positivo")


class ChainQualityError(RuntimeError):
    """The Markov chain completed with insufficient exploration quality."""

    def __init__(self, message: str, report: dict[str, Any], records: list[dict[str, Any]]):
        super().__init__(message)
        self.report = report
        self.records = records


class MetricReservoir:
    """Algorithm R reservoir sampler with deterministic local RNG."""

    def __init__(self, max_samples: int, seed: int):
        if max_samples < 1:
            raise ValueError("max_samples debe ser positivo")
        self.max_samples = max_samples
        self._rng = random.Random(seed)
        self._seen = 0
        self._records: list[dict[str, Any]] = []

    def observe(self, record: Mapping[str, Any]) -> None:
        self._seen += 1
        item = dict(record)
        if len(self._records) < self.max_samples:
            self._records.append(item)
            return
        index = self._rng.randrange(self._seen)
        if index < self.max_samples:
            self._records[index] = item

    @property
    def seen(self) -> int:
        return self._seen

    def records(self) -> list[dict[str, Any]]:
        return sorted((dict(item) for item in self._records), key=lambda item: int(item["step"]))


def exploration_diagnostics(
    *,
    steps_requested: int,
    states_observed: int,
    unique_states: int,
    self_loops: int,
    policy: DegeneracyPolicy = DegeneracyPolicy(),
) -> dict[str, Any]:
    """Evaluate a hard exploration gate from explicit, auditable telemetry."""
    if steps_requested < 1:
        raise ValueError("steps_requested debe ser positivo")
    if not 0 <= states_observed <= steps_requested:
        raise ValueError("states_observed fuera de rango")
    if not 0 <= unique_states <= states_observed:
        raise ValueError("unique_states fuera de rango")
    transition_count = max(0, states_observed - 1)
    if not 0 <= self_loops <= transition_count:
        raise ValueError("self_loops fuera de rango")

    unique_ratio = unique_states / steps_requested
    self_loop_rate = self_loops / transition_count if transition_count else (1.0 if states_observed else 0.0)
    completion_ratio = states_observed / steps_requested
    reasons: list[str] = []
    if policy.require_full_length and states_observed != steps_requested:
        reasons.append("incomplete_chain")
    if unique_ratio + 1e-15 < policy.min_unique_state_ratio:
        reasons.append("unique_state_ratio_below_minimum")
    if self_loop_rate - 1e-15 > policy.max_self_loop_rate:
        reasons.append("self_loop_rate_above_maximum")

    return {
        "all_pass": not reasons,
        "status": "PASS" if not reasons else "FAIL_DEGENERATE_CHAIN",
        "reasons": reasons,
        "steps_requested": steps_requested,
        "states_observed": states_observed,
        "completion_ratio": completion_ratio,
        "unique_states": unique_states,
        "unique_state_ratio": unique_ratio,
        "self_loops": self_loops,
        "transition_count": transition_count,
        "self_loop_rate": self_loop_rate,
        "policy": asdict(policy),
        "interpretation": "sanity_floor_not_mixing_proof",
    }


def compact_state_metrics(
    *,
    step: int,
    state_hash: str,
    metrics: Mapping[str, Any],
    score: float,
) -> dict[str, Any]:
    shape = metrics.get("shape", {})
    comarca = metrics.get("comarca", {})
    return {
        "schema": STATISTICAL_STATE_SCHEMA,
        "step": int(step),
        "assignment_sha256": str(state_hash),
        "population_max_abs_deviation": float(metrics["population_max_abs_deviation"]),
        "polsby_popper_min": _optional_float(shape.get("polsby_popper_min")),
        "polsby_popper_mean": _optional_float(shape.get("polsby_popper_mean")),
        "polsby_popper_median": _optional_float(shape.get("polsby_popper_median")),
        "comarca_population_retention": _optional_float(comarca.get("population_retention")),
        "comarca_split_communities": int(comarca.get("split_communities", 0)),
        "assignment_churn": float(metrics["assignment_churn"]),
        "cut_edges": int(metrics["cut_edges"]),
        "optimization_score": float(score),
    }


def _optional_float(value: Any) -> float | None:
    if value is None:
        return None
    result = float(value)
    return result if math.isfinite(result) else None


def _reference_metrics(data: AdaptedInputs, contract: Contract, weights: Weights) -> dict[str, Any]:
    metrics = plan_metrics(data, data.initial_assignment, contract)
    score = score_metrics(metrics, weights=weights, edge_count=len(data.edges))
    return compact_state_metrics(
        step=-1,
        state_hash=metrics["assignment_sha256"],
        metrics=metrics,
        score=score,
    )


def evaluate_state_stream(
    data: AdaptedInputs,
    states: Iterable[Mapping[str, Any]],
    contract: Contract,
    *,
    total_steps: int,
    seed: int,
    weights: Weights = Weights(),
    degeneracy_policy: DegeneracyPolicy = DegeneracyPolicy(),
    sampling_policy: StatisticalSamplingPolicy = StatisticalSamplingPolicy(),
    failures: Sequence[str] = (),
) -> tuple[dict[str, Any], dict[str, Any], list[dict[str, Any]]]:
    """Stream states, optimize one candidate, and retain a compact statistical sample."""
    if total_steps < 1:
        raise InputContractError("total_steps debe ser positivo")
    initial_violations = hard_constraint_violations(data, data.initial_assignment, contract)
    if initial_violations:
        raise InputContractError(
            "La partición inicial no satisface el contrato: " + ", ".join(initial_violations[:30])
        )

    sampling_seed = int(seed) ^ 0x5DEECE66D
    reservoir = MetricReservoir(sampling_policy.max_samples, sampling_seed)
    unique_hashes: set[str] = set()
    previous_hash: str | None = None
    self_loops = 0
    observed = 0
    best: tuple[float, str, dict[str, Any], dict[str, Any], int] | None = None

    for state_value in states:
        if observed >= total_steps:
            break
        state = dict(state_value)
        violations = hard_constraint_violations(data, state, contract)
        if violations:
            raise InputContractError(
                f"Estado {observed} viola el contrato: " + ", ".join(violations[:30])
            )
        state_hash = assignment_hash(state)
        if previous_hash == state_hash:
            self_loops += 1
        previous_hash = state_hash
        unique_hashes.add(state_hash)

        metrics = plan_metrics(data, state, contract)
        score = score_metrics(metrics, weights=weights, edge_count=len(data.edges))
        rank = (score, state_hash, state, metrics, observed)
        if best is None or rank[:2] < best[:2]:
            best = rank
        reservoir.observe(
            compact_state_metrics(step=observed, state_hash=state_hash, metrics=metrics, score=score)
        )
        observed += 1

    if observed == 0 or best is None:
        raise RuntimeError("La cadena no produjo estados")

    quality = exploration_diagnostics(
        steps_requested=total_steps,
        states_observed=observed,
        unique_states=len(unique_hashes),
        self_loops=self_loops,
        policy=degeneracy_policy,
    )
    selected, selected_metrics, best_step = best[2], best[3], best[4]
    selected_violations = hard_constraint_violations(data, selected, contract)
    records = reservoir.records()
    reference = _reference_metrics(data, contract, weights)
    report = {
        "engine": {
            "id": "gerrychain_recom",
            "library_version": "1.0.0",
            "adapter_version": "ensemble-statistical-1.1.0",
        },
        "run": {
            "seed": int(seed),
            "steps_requested": total_steps,
            "states_observed": observed,
            "best_step": best_step,
        },
        "telemetry": {
            "unique_states": len(unique_hashes),
            "self_loops": self_loops,
            "failures": list(failures),
            "selection_memory": "best_state_plus_compact_reservoir",
        },
        "chain_quality": quality,
        "hard_constraints": {
            "all_pass": not selected_violations,
            "violations": selected_violations,
            "checks": [
                "unit_universe", "k", "population", "province",
                "province_apportionment", "atomic_unit", "municipality",
                "closed_urban", "contiguity", "geometric_contiguity",
            ],
        },
        "initial_metrics": plan_metrics(data, data.initial_assignment, contract),
        "selected_metrics": selected_metrics,
        "statistical_sample": {
            "schema": STATISTICAL_STATE_SCHEMA,
            "method": "uniform_reservoir_algorithm_r",
            "sampling_seed": sampling_seed,
            "states_observed": observed,
            "stored_state_count": len(records),
            "max_samples": sampling_policy.max_samples,
            "stores_full_geometry": False,
            "reference_map": reference,
        },
        "semantics": {
            "candidate_gallery": "optimized_best_state_per_chain",
            "statistical_ensemble": "compact_metrics_of_visited_states",
        },
        "configuration": {
            "contract": asdict(contract),
            "weights": asdict(weights),
            "degeneracy_policy": asdict(degeneracy_policy),
            "sampling_policy": asdict(sampling_policy),
        },
    }
    if not quality["all_pass"]:
        raise ChainQualityError(
            "Cadena GerryChain degenerada: " + ", ".join(quality["reasons"]),
            report,
            records,
        )
    return selected, report, records


def _partition_assignment_by_section(partition: Any) -> dict[str, Any]:
    raw = partition.assignment.to_dict() if hasattr(partition.assignment, "to_dict") else dict(partition.assignment)
    result: dict[str, Any] = {}
    for node_id, district in raw.items():
        attrs = partition.graph.node_data(node_id)
        result[str(attrs["section_id"]).strip()] = district
    return result


def run_statistical_gerrychain(
    data: AdaptedInputs,
    contract: Contract,
    *,
    total_steps: int,
    seed: int,
    comarca_surcharge: float = 0.30,
    weights: Weights = Weights(),
    degeneracy_policy: DegeneracyPolicy = DegeneracyPolicy(),
    sampling_policy: StatisticalSamplingPolicy = StatisticalSamplingPolicy(),
) -> tuple[dict[str, Any], dict[str, Any], list[dict[str, Any]]]:
    """GerryChain/ReCom runner for the ensemble subsystem only."""
    if total_steps < 1:
        raise InputContractError("total_steps debe ser positivo")
    if not 0 <= comarca_surcharge <= 1:
        raise InputContractError("comarca_surcharge debe estar entre 0 y 1")
    initial_violations = hard_constraint_violations(data, data.initial_assignment, contract)
    if initial_violations:
        raise InputContractError(
            "La partición inicial no satisface el contrato: " + ", ".join(initial_violations[:30])
        )
    try:
        import networkx as nx
        from gerrychain import MarkovChain, Partition, updaters
        from gerrychain.proposals import ReCom
    except ImportError as exc:
        raise RuntimeError("GerryChain 1.0 no está instalado en este entorno") from exc

    nx_graph = nx.Graph()
    for section, attrs in data.nodes.items():
        nx_graph.add_node(section, **attrs)
    nx_graph.add_edges_from(data.edges)
    initial = Partition(
        nx_graph,
        assignment="district",
        updaters={"population": updaters.Tally("population", alias="population"), "cut_edges": updaters.cut_edges},
    )
    ideal = sum(n["population"] for n in data.nodes.values()) / contract.k

    def ddd_contract(partition: Any) -> bool:
        return not hard_constraint_violations(data, _partition_assignment_by_section(partition), contract)

    surcharge = {
        "comarca": comarca_surcharge
    } if comarca_surcharge and all(n.get("comarca") for n in data.nodes.values()) else None
    chain = MarkovChain(
        proposal_fn=ReCom.district_pairs_mst(
            pop_col="population",
            pop_target=ideal,
            epsilon=contract.target_tolerance_ratio,
            region_surcharge=surcharge,
            allow_pair_reselection=True,
        ),
        constraints=[ddd_contract],
        initial_partition=initial,
        total_steps=total_steps,
        rng=seed,
    )

    failures: list[str] = []

    def state_stream() -> Iterable[Mapping[str, Any]]:
        try:
            for partition in chain:
                yield _partition_assignment_by_section(partition)
        except RuntimeError as exc:
            failures.append(str(exc))

    selected, report, records = evaluate_state_stream(
        data,
        state_stream(),
        contract,
        total_steps=total_steps,
        seed=seed,
        weights=weights,
        degeneracy_policy=degeneracy_policy,
        sampling_policy=sampling_policy,
        failures=failures,
    )
    report["configuration"]["comarca_surcharge"] = comarca_surcharge
    return output_geojson(data, selected), report, records


def write_statistical_records(path: str | Path, records: Iterable[Mapping[str, Any]]) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(dict(record), ensure_ascii=False, sort_keys=True, separators=(",", ":")))
            handle.write("\n")


def read_statistical_records(path: str | Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    with Path(path).open("r", encoding="utf-8") as handle:
        for line_no, raw in enumerate(handle, start=1):
            line = raw.strip()
            if not line:
                continue
            record = json.loads(line)
            if record.get("schema") != STATISTICAL_STATE_SCHEMA:
                raise ValueError(f"Esquema estadístico inválido en línea {line_no}: {path}")
            records.append(record)
    return records


def empirical_percentile_rank(values: Sequence[float], reference: float) -> float:
    """Mid-rank empirical CDF in [0, 100], deterministic in the presence of ties."""
    finite = [float(value) for value in values if math.isfinite(float(value))]
    if not finite:
        raise ValueError("Se necesita al menos un valor finito")
    less = sum(value < reference for value in finite)
    equal = sum(value == reference for value in finite)
    return 100.0 * (less + 0.5 * equal) / len(finite)


def _quantile(values: Sequence[float], probability: float) -> float:
    ordered = sorted(float(value) for value in values)
    if not ordered:
        raise ValueError("No hay valores")
    if len(ordered) == 1:
        return ordered[0]
    position = (len(ordered) - 1) * probability
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[lower]
    weight = position - lower
    return ordered[lower] * (1.0 - weight) + ordered[upper] * weight


DISTRIBUTION_METRICS: dict[str, str] = {
    "population_max_abs_deviation": "lower_is_better",
    "polsby_popper_min": "higher_is_better",
    "polsby_popper_mean": "higher_is_better",
    "polsby_popper_median": "higher_is_better",
    "comarca_population_retention": "higher_is_better",
    "comarca_split_communities": "lower_is_better",
    "assignment_churn": "lower_is_better",
    "cut_edges": "lower_is_better",
}


def summarize_distribution(
    records: Sequence[Mapping[str, Any]],
    reference_map: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    distributions: dict[str, Any] = {}
    reference_positions: dict[str, Any] = {}
    for metric, direction in DISTRIBUTION_METRICS.items():
        values = [float(record[metric]) for record in records if record.get(metric) is not None]
        if not values:
            continue
        distributions[metric] = {
            "count": len(values),
            "min": min(values),
            "p05": _quantile(values, 0.05),
            "p25": _quantile(values, 0.25),
            "p50": _quantile(values, 0.50),
            "p75": _quantile(values, 0.75),
            "p95": _quantile(values, 0.95),
            "max": max(values),
            "direction": direction,
        }
        if reference_map is not None and reference_map.get(metric) is not None:
            reference = float(reference_map[metric])
            raw = empirical_percentile_rank(values, reference)
            favorability = raw if direction == "higher_is_better" else 100.0 - raw
            reference_positions[metric] = {
                "value": reference,
                "raw_percentile": raw,
                "favorability_percentile": favorability,
                "direction": direction,
                "tie_method": "midrank",
            }
    return {"distributions": distributions, "reference_position": reference_positions}


def aggregate_statistical_results(
    results_dir: str | Path,
    *,
    candidate_count_expected: int,
    candidate_gallery_count: int,
) -> dict[str, Any]:
    root = Path(results_dir)
    records: list[dict[str, Any]] = []
    valid_chain_ids: list[str] = []
    missing_or_failed: list[str] = []
    states_observed_total = 0
    reference: dict[str, Any] | None = None

    candidate_dirs = sorted(path for path in root.iterdir() if path.is_dir()) if root.is_dir() else []
    for candidate_dir in candidate_dirs:
        engine_path = candidate_dir / "engine-report.json"
        states_path = candidate_dir / "statistical-states.jsonl"
        if not engine_path.is_file() or not states_path.is_file():
            if (candidate_dir / "report.json").is_file() or (candidate_dir / "failure.json").is_file():
                missing_or_failed.append(candidate_dir.name)
            continue
        engine = json.loads(engine_path.read_text(encoding="utf-8"))
        if engine.get("chain_quality", {}).get("all_pass") is not True:
            missing_or_failed.append(candidate_dir.name)
            continue
        chain_records = read_statistical_records(states_path)
        expected_stored = int(engine.get("statistical_sample", {}).get("stored_state_count", -1))
        if expected_stored != len(chain_records):
            raise ValueError(f"Conteo estadístico inconsistente en {candidate_dir.name}")
        chain_reference = engine.get("statistical_sample", {}).get("reference_map")
        if not isinstance(chain_reference, dict):
            raise ValueError(f"Falta mapa de referencia en {candidate_dir.name}")
        if reference is None:
            reference = chain_reference
        elif _reference_signature(reference) != _reference_signature(chain_reference):
            raise ValueError("Las cadenas no comparten el mismo mapa de referencia")
        records.extend(chain_records)
        states_observed_total += int(engine.get("run", {}).get("states_observed", 0))
        valid_chain_ids.append(candidate_dir.name)

    distribution = summarize_distribution(records, reference) if records else {
        "distributions": {}, "reference_position": {}
    }
    return {
        "schema": STATISTICAL_SUMMARY_SCHEMA,
        "complete": len(valid_chain_ids) == candidate_count_expected,
        "candidate_count_expected": int(candidate_count_expected),
        "candidate_gallery_count": int(candidate_gallery_count),
        "statistical_chain_count": len(valid_chain_ids),
        "states_observed_total": states_observed_total,
        "statistical_state_count": len(records),
        "chain_ids": valid_chain_ids,
        "missing_or_failed_chains": sorted(set(missing_or_failed)),
        "sampling_note": "visited-state metrics; reservoir is uniform when chain length exceeds max_samples",
        "stores_full_geometry": False,
        "semantics": {
            "candidate_gallery_count": "number_of_optimized_best-state_alternatives",
            "statistical_state_count": "number_of_compact_visited-state_observations",
        },
        **distribution,
    }


def _reference_signature(reference: Mapping[str, Any]) -> str:
    comparable = {key: reference.get(key) for key in sorted(DISTRIBUTION_METRICS)}
    comparable["assignment_sha256"] = reference.get("assignment_sha256")
    return json.dumps(comparable, sort_keys=True, separators=(",", ":"))
