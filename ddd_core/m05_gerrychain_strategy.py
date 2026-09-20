#!/usr/bin/env python3
"""
PROYECTO: Diputado de Distrito
COMPONENTE: 02.5 Estrategia de Optimización — GerryChain/ReCom
VERSIÓN PROPUESTA: 2.0.1
ESTADO: candidato de integración, genérico multi-territorio

Objetivo
========
Implementar GerryChain/ReCom como estrategia alternativa de M05 sin alterar
M01–M04 ni M06. Consume exactamente el grafo M03 y la partición M04,
trabaja sobre las unidades declarativas indivisibles ``ddd_unit_id`` y emite
el mismo contrato de salida que M05: GeoJSON de secciones con ``district_id``
y un informe poblacional verificable por ``herramientas/estado_produccion.py``.

Principios
==========
* Ningún dato electoral o partidista participa en el cálculo.
* La tolerancia objetivo (p. ej. ±12 %) es un objetivo de optimización, no una
  restricción dura de todos los estados intermedios. Los límites poblacionales
  duros, provincia, cuotas, unidades indivisibles, disciplina municipal,
  distritos urbanos cerrados y contigüidad sí son invariantes.
* GerryChain opera sobre ``ddd_unit_id`` colapsado, no sobre secciones, de modo
  que una unidad indivisible no puede partirse ni siquiera transitoriamente.
* Las transiciones no cruzan provincias y no atraviesan distritos urbanos
  cerrados. Esto elimina propuestas inválidas de raíz en vez de generarlas y
  rechazarlas después.
* Un fallo de bipartición ReCom se convierte en self-loop controlado, no aborta
  una cadena completa.
* Cada semilla conserva siempre su estado inicial como candidato; el portfolio
  nunca puede devolver un resultado peor que M04 según el orden técnico
  declarado en ``candidate_rank``.
* La salida no se promociona automáticamente. M06 y su auditoría geométrica
  siguen siendo la puerta independiente posterior.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import platform
import time
import zipfile
from collections import Counter, defaultdict, deque
from dataclasses import dataclass, field
from functools import partial
from pathlib import Path
from typing import Any, Iterable, Mapping

import geopandas as gpd
import networkx as nx
import pandas as pd
import yaml

try:
    import gerrychain
    import rustworkx
    from gerrychain import MarkovChain, Partition, updaters
    from gerrychain.proposals.tree_proposals import MetagraphError, build_recom_proposal_fn
    from gerrychain.tree import BalanceError, PopulationBalanceError, ReselectException, bipartition_tree
except Exception as exc:  # pragma: no cover - exercised by explicit dependency preflight
    gerrychain = None
    rustworkx = None
    _GERRYCHAIN_IMPORT_ERROR = exc
else:
    _GERRYCHAIN_IMPORT_ERROR = None

STRATEGY_VERSION = "2.0.1"


@dataclass(frozen=True)
class StrategyContract:
    expected_k: int
    target_tolerance_ratio: float
    population_floor_ratio: float
    population_cap_ratio: float
    province_districts: Mapping[str, int] = field(default_factory=dict)
    require_single_province: bool = True
    require_contiguity: bool = True
    require_municipality_discipline: bool = True
    max_mixed_districts_per_split_municipality: int = 1
    preserve_closed_urban: bool = True


@dataclass(frozen=True)
class StrategyConfig:
    steps_per_seed: int = 3000
    seed_base: int = 20260920
    seed_count: int = 4
    proposal_epsilon: float = 0.12
    max_bipartition_attempts: int = 500
    require_pythonhashseed_zero: bool = True

    def validate(self) -> None:
        if self.steps_per_seed < 1:
            raise ValueError("steps_per_seed debe ser >= 1")
        if self.seed_count < 1:
            raise ValueError("seed_count debe ser >= 1")
        if not 0 < self.proposal_epsilon < 1:
            raise ValueError("proposal_epsilon debe estar entre 0 y 1")
        if self.max_bipartition_attempts < 1:
            raise ValueError("max_bipartition_attempts debe ser >= 1")

    def seeds(self) -> list[int]:
        self.validate()
        return [self.seed_base + i + 1 for i in range(self.seed_count)]


@dataclass
class PreparedProblem:
    sections: gpd.GeoDataFrame
    units: dict[str, dict[str, Any]]
    edges: list[tuple[str, str]]
    initial_assignment: dict[str, Any]
    frozen_districts: dict[Any, frozenset[str]]
    target_population: float


def require_runtime(config: StrategyConfig | None = None) -> None:
    if _GERRYCHAIN_IMPORT_ERROR is not None:
        raise RuntimeError(
            "GerryChain no está disponible. Instalar requirements-ensemble.lock; "
            f"error de importación: {_GERRYCHAIN_IMPORT_ERROR}"
        )
    if config is not None and config.require_pythonhashseed_zero:
        if os.environ.get("PYTHONHASHSEED") != "0":
            raise RuntimeError(
                "Ejecución reproducible requerida: exportar PYTHONHASHSEED=0 antes de iniciar Python. "
                "La semilla de MarkovChain por sí sola no fue suficiente en la integración DDD."
            )


def _load_geojson_any(path: Path) -> gpd.GeoDataFrame:
    path = path.expanduser().resolve()
    if path.suffix.lower() == ".zip":
        return gpd.read_file("zip://" + str(path))
    return gpd.read_file(path)


def _write_geojson_zip(gdf: gpd.GeoDataFrame, path: Path) -> None:
    path = path.expanduser().resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    inner = path.name[:-4] if path.name.lower().endswith(".zip") else path.name + ".geojson"
    if not inner.lower().endswith((".json", ".geojson")):
        inner += ".geojson"
    payload = json.loads(gdf.to_json(drop_id=True))
    content = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    # ZIP determinista: la marca temporal por defecto hace variar el SHA-256 aunque
    # la asignación sea idéntica. M05 forma parte de una cadena auditable y debe
    # producir los mismos bytes con las mismas entradas/configuración.
    info = zipfile.ZipInfo(inner, date_time=(1980, 1, 1, 0, 0, 0))
    info.compress_type = zipfile.ZIP_DEFLATED
    info.external_attr = 0o644 << 16
    with zipfile.ZipFile(path, "w") as zf:
        zf.writestr(info, content)


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def _assignment_hash(assignment: Mapping[str, Any]) -> str:
    payload = json.dumps(
        sorted((str(k), str(v)) for k, v in assignment.items()),
        ensure_ascii=False,
        separators=(",", ":"),
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _normalise_district(v: Any) -> Any:
    if isinstance(v, bool):
        return int(v)
    try:
        f = float(v)
    except (TypeError, ValueError):
        return str(v)
    return int(f) if f.is_integer() else str(v)


def contract_from_yaml(cfg: Mapping[str, Any]) -> StrategyContract:
    validation = cfg.get("validation") or {}
    meta = cfg.get("meta") or {}
    s4 = (cfg.get("modulos") or {}).get("modulo_04_generar_semillas") or {}
    s5 = (cfg.get("modulos") or {}).get("modulo_05_optimizar_distritos") or {}
    k = int(
        s5.get("expected_districts")
        or s4.get("expected_districts")
        or validation.get("expected_districts")
        or meta.get("expected_districts")
        or 0
    )
    if k <= 0:
        raise ValueError("No se pudo resolver expected_k desde el contrato")
    tol = float(
        s5.get("target_tolerance_ratio")
        or validation.get("target_tolerance_ratio")
        or 0.12
    )
    floor = float(s5.get("population_floor_ratio") or validation.get("population_floor_ratio") or 0.80)
    cap = float(s5.get("population_cap_ratio") or validation.get("population_cap_ratio") or 1.75)
    quotas_raw = (
        s5.get("province_districts")
        or s4.get("province_districts")
        or validation.get("province_districts")
        or {}
    )
    quotas = {str(k).zfill(2): int(v) for k, v in dict(quotas_raw).items()}
    return StrategyContract(
        expected_k=k,
        target_tolerance_ratio=tol,
        population_floor_ratio=floor,
        population_cap_ratio=cap,
        province_districts=quotas,
        require_single_province=bool(validation.get("require_single_province_per_district", True)),
        require_contiguity=bool(validation.get("require_graph_contiguity", validation.get("require_contiguity", True))),
        require_municipality_discipline=bool(validation.get("require_municipality_discipline", True)),
        max_mixed_districts_per_split_municipality=int(
            validation.get("max_mixed_districts_per_split_municipality", 1)
        ),
        preserve_closed_urban=bool(validation.get("preserve_closed_urban", True)),
    )


def strategy_config_from_yaml(cfg: Mapping[str, Any]) -> StrategyConfig:
    s5 = (cfg.get("modulos") or {}).get("modulo_05_optimizar_distritos") or {}
    raw = s5.get("gerrychain") or {}
    validation = cfg.get("validation") or {}
    default_epsilon = float(validation.get("target_tolerance_ratio", 0.12))
    result = StrategyConfig(
        steps_per_seed=int(raw.get("steps_per_seed", 3000)),
        seed_base=int(raw.get("seed_base", 20260920)),
        seed_count=int(raw.get("seed_count", 4)),
        proposal_epsilon=float(raw.get("proposal_epsilon", default_epsilon)),
        max_bipartition_attempts=int(raw.get("max_bipartition_attempts", 500)),
        require_pythonhashseed_zero=bool(raw.get("require_pythonhashseed_zero", True)),
    )
    result.validate()
    return result


def resolve_paths(cfg: Mapping[str, Any], params_path: Path, run_id: str) -> dict[str, Path]:
    meta = cfg.get("meta") or {}
    values = {
        "year": meta.get("year", ""),
        "run_name": meta.get("run_name", params_path.stem),
        "run_id": run_id,
    }
    s3 = (cfg.get("modulos") or {}).get("modulo_03_construir_grafo") or {}
    s4 = (cfg.get("modulos") or {}).get("modulo_04_generar_semillas") or {}
    s5 = (cfg.get("modulos") or {}).get("modulo_05_optimizar_distritos") or {}
    graph = s5.get("in_graph_json") or s4.get("in_graph_json") or s3.get("out_graph_json")
    initial = s5.get("in_geojson") or s4.get("out_geojson")
    output = s5.get("out_geojson")
    report = s5.get("out_report")
    if not all((graph, initial, output, report)):
        raise ValueError("El contrato no declara rutas completas M03/M04/M05")

    io_cfg = cfg.get("io") or {}
    project_root_raw = (io_cfg.get("project_root") or {}).get("path", "")
    root = params_path.parent.resolve()
    if project_root_raw:
        declared = Path(str(project_root_raw)).expanduser()
        root = declared.resolve() if declared.is_absolute() else (params_path.parent / declared).resolve()

    def render(raw: str) -> Path:
        p = Path(str(raw).format(**values)).expanduser()
        return p if p.is_absolute() else (root / p).resolve()

    return {"graph": render(graph), "initial": render(initial), "output": render(output), "report": render(report)}


def prepare_problem(
    graph_path: Path,
    initial_geojson: Path,
    contract: StrategyContract,
    *,
    id_field: str = "CUSEC_KEY",
    population_field: str = "POP_2025",
    district_field: str = "district_id",
    unit_field: str = "ddd_unit_id",
    province_field: str = "CPRO",
    municipality_field: str = "CUMUN",
    closed_urban_field: str = "ddd_closed_urban",
) -> PreparedProblem:
    graph = json.loads(graph_path.read_text(encoding="utf-8"))
    node_population = {str(n["id"]): float(n.get("pop", 0)) for n in graph.get("nodes", [])}
    sections = _load_geojson_any(initial_geojson)
    required = {id_field, district_field, unit_field, province_field, municipality_field, closed_urban_field}
    missing = sorted(required - set(sections.columns))
    if missing:
        raise ValueError("M04 carece de columnas requeridas: " + ", ".join(missing))
    if sections.crs is None:
        raise ValueError("M04 no declara CRS")

    sections = sections.copy()
    sections[id_field] = sections[id_field].astype(str)
    sections[unit_field] = sections[unit_field].astype(str)
    sections[province_field] = sections[province_field].astype(str).str.zfill(2)
    sections[municipality_field] = sections[municipality_field].astype(str)
    sections[district_field] = sections[district_field].map(_normalise_district)

    if sections[id_field].duplicated().any():
        raise ValueError("M04 contiene secciones duplicadas")
    if set(sections[id_field]) != set(node_population):
        raise ValueError("El universo de M04 no coincide exactamente con M03")

    section_unit = dict(zip(sections[id_field], sections[unit_field]))
    units: dict[str, dict[str, Any]] = {}
    initial: dict[str, Any] = {}
    for unit, rows in sections.groupby(unit_field, sort=True):
        districts = set(rows[district_field])
        provinces = set(rows[province_field])
        municipalities = set(rows[municipality_field])
        if len(districts) != 1:
            raise ValueError(f"Unidad indivisible ya partida en M04: {unit}")
        if len(provinces) != 1:
            raise ValueError(f"Unidad cruza provincias: {unit}")
        if len(municipalities) != 1:
            raise ValueError(f"Unidad cruza municipios: {unit}")
        units[str(unit)] = {
            "unit_id": str(unit),
            "population": float(sum(node_population[s] for s in rows[id_field])),
            "province": next(iter(provinces)),
            "municipality": next(iter(municipalities)),
            "closed_urban": bool(rows[closed_urban_field].fillna(False).astype(bool).all()),
        }
        initial[str(unit)] = next(iter(districts))

    edges: set[tuple[str, str]] = set()
    for edge in graph.get("edges", []):
        u = section_unit.get(str(edge["u"]))
        v = section_unit.get(str(edge["v"]))
        if u is None or v is None:
            raise ValueError("M03 contiene arista fuera del universo M04")
        if u != v:
            edges.add(tuple(sorted((u, v))))

    members: dict[Any, set[str]] = defaultdict(set)
    closed_members: dict[Any, set[str]] = defaultdict(set)
    for unit, district in initial.items():
        members[district].add(unit)
        if units[unit]["closed_urban"]:
            closed_members[district].add(unit)
    frozen = {
        district: frozenset(unit_set)
        for district, unit_set in members.items()
        if contract.preserve_closed_urban and unit_set and unit_set == closed_members[district]
    }

    total = sum(row["population"] for row in units.values())
    target = total / contract.expected_k
    problem = PreparedProblem(
        sections=sections,
        units=units,
        edges=sorted(edges),
        initial_assignment=initial,
        frozen_districts=frozen,
        target_population=target,
    )
    violations = hard_constraint_violations(problem, initial, contract)
    if violations:
        raise ValueError("M04 viola restricciones duras previas a GerryChain: " + ", ".join(violations[:20]))
    return problem


def population_metrics(problem: PreparedProblem, assignment: Mapping[str, Any], contract: StrategyContract) -> dict[str, Any]:
    pops: dict[Any, float] = defaultdict(float)
    for unit, district in assignment.items():
        pops[district] += problem.units[unit]["population"]
    target = problem.target_population
    dev = {d: abs(p - target) / target for d, p in pops.items()}
    signed = {d: (p - target) / target for d, p in pops.items()}
    return {
        "target": target,
        "district_populations": {str(k): v for k, v in pops.items()},
        "district_relative_deviation": {str(k): v for k, v in signed.items()},
        "districts_outside_tolerance": sum(v > contract.target_tolerance_ratio + 1e-12 for v in dev.values()),
        "max_relative_deviation": max(dev.values(), default=0.0),
        "rms_relative_deviation": math.sqrt(sum(v * v for v in dev.values()) / len(dev)) if dev else 0.0,
    }


def hard_constraint_violations(
    problem: PreparedProblem,
    assignment: Mapping[str, Any],
    contract: StrategyContract,
) -> list[str]:
    violations: list[str] = []
    if set(assignment) != set(problem.units):
        return ["unit_universe"]
    districts = set(assignment.values())
    if len(districts) != contract.expected_k:
        violations.append(f"district_count:{len(districts)}")

    target = problem.target_population
    floor = target * contract.population_floor_ratio
    cap = target * contract.population_cap_ratio
    pops: dict[Any, float] = defaultdict(float)
    provinces: dict[Any, set[str]] = defaultdict(set)
    members: dict[Any, set[str]] = defaultdict(set)
    municipalities: dict[str, set[Any]] = defaultdict(set)
    district_municipalities: dict[Any, set[str]] = defaultdict(set)
    municipality_pop: dict[str, float] = defaultdict(float)

    for unit, district in assignment.items():
        row = problem.units[unit]
        members[district].add(unit)
        pops[district] += row["population"]
        provinces[district].add(row["province"])
        municipalities[row["municipality"]].add(district)
        district_municipalities[district].add(row["municipality"])
        municipality_pop[row["municipality"]] += row["population"]

    for district, population in pops.items():
        if population < floor - 1e-9:
            violations.append(f"population_floor:{district}")
        if population > cap + 1e-9:
            violations.append(f"population_cap:{district}")

    if contract.require_single_province:
        for district, values in provinces.items():
            if len(values) != 1:
                violations.append(f"province:{district}")

    if contract.province_districts:
        observed = Counter(next(iter(v)) for v in provinces.values() if len(v) == 1)
        for province, expected in contract.province_districts.items():
            if observed.get(str(province).zfill(2), 0) != int(expected):
                violations.append(f"province_count:{province}")

    if contract.require_municipality_discipline:
        for municipality, district_set in municipalities.items():
            pop = municipality_pop[municipality]
            minimum = max(1, math.ceil(pop / cap)) if pop > 0 else 1
            maximum = max(1, math.ceil(pop / target)) if pop > 0 else 1
            if not (minimum <= len(district_set) <= maximum):
                violations.append(f"municipality:{municipality}")
            mixed = sum(1 for d in district_set if len(district_municipalities[d]) > 1)
            if len(district_set) > 1 and mixed > contract.max_mixed_districts_per_split_municipality:
                violations.append(f"municipality_mixed:{municipality}")

    if contract.preserve_closed_urban:
        for district, frozen in problem.frozen_districts.items():
            if members.get(district, set()) != set(frozen):
                violations.append(f"closed_urban:{district}")

    if contract.require_contiguity:
        adjacency = {u: set() for u in problem.units}
        for u, v in problem.edges:
            adjacency[u].add(v)
            adjacency[v].add(u)
        for district, wanted in members.items():
            if not wanted:
                violations.append(f"empty_district:{district}")
                continue
            start = next(iter(wanted))
            reached = {start}
            queue: deque[str] = deque([start])
            while queue:
                u = queue.popleft()
                for v in adjacency[u] & wanted:
                    if v not in reached:
                        reached.add(v)
                        queue.append(v)
            if reached != wanted:
                violations.append(f"contiguity:{district}")

    # Deliberadamente NO se incluye target_tolerance_ratio aquí. Es objetivo,
    # no límite duro de los estados intermedios.
    return sorted(set(violations))


def candidate_rank(
    problem: PreparedProblem,
    assignment: Mapping[str, Any],
    contract: StrategyContract,
    initial: Mapping[str, Any],
) -> tuple[Any, ...]:
    pop = population_metrics(problem, assignment, contract)
    cut_edges = sum(1 for u, v in problem.edges if assignment[u] != assignment[v])
    churn = sum(assignment[u] != initial[u] for u in initial) / max(1, len(initial))
    # Orden técnico declarativo y no partidista. El hash resuelve empates de
    # forma determinista; no intervienen votos ni composición electoral.
    return (
        int(pop["districts_outside_tolerance"]),
        float(pop["max_relative_deviation"]),
        float(pop["rms_relative_deviation"]),
        int(cut_edges),
        float(churn),
        _assignment_hash(assignment),
    )


def _partition_assignment(partition: Any) -> dict[str, Any]:
    raw = partition.assignment.to_dict() if hasattr(partition.assignment, "to_dict") else dict(partition.assignment)
    return {
        str(partition.graph.node_data(node_id)["unit_id"]): district
        for node_id, district in raw.items()
    }


def _proposal_graph(problem: PreparedProb