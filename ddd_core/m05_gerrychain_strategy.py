#!/usr/bin/env python3
"""
PROYECTO: Diputado de Distrito
COMPONENTE: 02.5 Estrategia de Optimización — GerryChain/ReCom
VERSIÓN PROPUESTA: 2.1.0
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
import pandas as pd
import yaml

try:
    import gerrychain
    import networkx as nx
    import rustworkx
    from gerrychain import MarkovChain, Partition, updaters
    from gerrychain.proposals.tree_proposals import MetagraphError, build_recom_proposal_fn
    from gerrychain.tree import BalanceError, PopulationBalanceError, ReselectException, bipartition_tree
except Exception as exc:  # pragma: no cover - exercised by explicit dependency preflight
    gerrychain = None
    nx = None
    rustworkx = None
    _GERRYCHAIN_IMPORT_ERROR = exc
else:
    _GERRYCHAIN_IMPORT_ERROR = None

STRATEGY_VERSION = "2.1.0"


@dataclass(frozen=True)
class StrategyContract:
    expected_k: int
    target_tolerance_ratio: float
    population_floor_ratio: float
    population_cap_ratio: float
    province_districts: Mapping[str, int] = field(default_factory=dict)
    population_floor_exempt_partitions: tuple[str, ...] = ()
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
    comarca_surcharge: float = 0.0
    population_band: float = 0.005
    metric_crs: str = "EPSG:3035"
    min_shared_border_m: float = 1.0
    max_bipartition_attempts: int = 500
    require_pythonhashseed_zero: bool = True

    def validate(self) -> None:
        if self.steps_per_seed < 1:
            raise ValueError("steps_per_seed debe ser >= 1")
        if self.seed_count < 1:
            raise ValueError("seed_count debe ser >= 1")
        if not 0 < self.proposal_epsilon < 1:
            raise ValueError("proposal_epsilon debe estar entre 0 y 1")
        if not 0 <= self.comarca_surcharge <= 1:
            raise ValueError("comarca_surcharge debe estar entre 0 y 1")
        if not 0 < self.population_band < 1:
            raise ValueError("population_band debe estar entre 0 y 1")
        if not self.metric_crs:
            raise ValueError("metric_crs no puede estar vacío")
        if self.min_shared_border_m <= 0:
            raise ValueError("min_shared_border_m debe ser > 0")
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
    unit_areas: dict[str, float] = field(default_factory=dict)
    unit_perimeters: dict[str, float] = field(default_factory=dict)
    shared_border_lengths: dict[tuple[str, str], float] = field(default_factory=dict)
    unit_components: dict[str, tuple[str, ...]] = field(default_factory=dict)
    component_edges: list[tuple[str, str]] = field(default_factory=list)
    internal_component_edges: list[tuple[str, str]] = field(default_factory=list)
    initial_geometric_exceptions: dict[Any, frozenset[str]] = field(default_factory=dict)
    component_adjacency: dict[str, set[str]] = field(default_factory=dict)
    operational_edge_types: dict[tuple[str, str], tuple[str, ...]] = field(default_factory=dict)


class BaselineValidationError(RuntimeError):
    """Entrada/contrato inválido: no es un fallo recuperable de GerryChain."""


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


def _polygon_components(geometry: Any) -> list[Any]:
    if geometry.geom_type == "Polygon":
        return [geometry]
    if geometry.geom_type == "MultiPolygon":
        return list(geometry.geoms)
    return [geometry]


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
        population_floor_exempt_partitions=tuple(str(x) for x in (validation.get("population_floor_exempt_partitions") or [])),
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
    s2 = (cfg.get("modulos") or {}).get("modulo_02_construir_adyacencias") or {}
    s6 = (cfg.get("modulos") or {}).get("modulo_06_consolidar_distritos") or {}
    default_epsilon = float(validation.get("target_tolerance_ratio", 0.12))
    result = StrategyConfig(
        steps_per_seed=int(raw.get("steps_per_seed", 3000)),
        seed_base=int(raw.get("seed_base", 20260920)),
        seed_count=int(raw.get("seed_count", 4)),
        proposal_epsilon=float(raw.get("proposal_epsilon", default_epsilon)),
        comarca_surcharge=float(raw.get("comarca_surcharge", 0.0)),
        population_band=float(raw.get("population_band", 0.005)),
        metric_crs=str(raw.get("metric_crs") or s6.get("metric_crs") or s2.get("working_crs") or "EPSG:3035"),
        min_shared_border_m=float(raw.get("min_shared_border_m", s2.get("min_shared_border_m", 1.0))),
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
    metric_crs: str = "EPSG:3035",
    min_shared_border_m: float = 1.0,
) -> PreparedProblem:
    graph = json.loads(graph_path.read_text(encoding="utf-8"))
    graph_nodes = {str(n["id"]): n for n in graph.get("nodes", [])}
    node_population = {section: float(node.get("pop", 0)) for section, node in graph_nodes.items()}
    sections = _load_geojson_any(initial_geojson)
    required = {id_field, district_field, unit_field, province_field, municipality_field, closed_urban_field}
    missing = sorted(required - set(sections.columns))
    if missing:
        raise ValueError("M04 carece de columnas requeridas: " + ", ".join(missing))
    if sections.crs is None:
        raise ValueError("M04 no declara CRS")
    if min_shared_border_m <= 0:
        raise ValueError("min_shared_border_m debe ser > 0")

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

    metric_sections = sections.to_crs(metric_crs)

    section_unit = dict(zip(sections[id_field], sections[unit_field]))
    units: dict[str, dict[str, Any]] = {}
    initial: dict[str, Any] = {}
    unit_areas: dict[str, float] = {}
    unit_perimeters: dict[str, float] = {}
    unit_geometries: dict[str, Any] = {}
    section_components: dict[str, list[tuple[str, Any]]] = {}
    unit_components: dict[str, list[str]] = defaultdict(list)
    component_edges: set[tuple[str, str]] = set()
    internal_component_edges: set[tuple[str, str]] = set()

    for section_id, geometry in zip(metric_sections[id_field], metric_sections.geometry):
        if geometry is None or geometry.is_empty or not geometry.is_valid:
            raise ValueError(f"Geometría inválida en {section_id}")
        components = _polygon_components(geometry)
        named = [(f"{section_id}#{index}", part) for index, part in enumerate(components)]
        section_components[str(section_id)] = named
        unit = str(section_unit[str(section_id)])
        unit_components[unit].extend(name for name, _ in named)
        if len(named) > 1:
            anchor = named[0][0]
            internal_component_edges.update(tuple(sorted((anchor, name))) for name, _ in named[1:])

    for unit, rows in metric_sections.groupby(unit_field, sort=True):
        districts = set(rows[district_field])
        provinces = set(rows[province_field])
        municipalities = set(rows[municipality_field])
        if len(districts) != 1:
            raise ValueError(f"Unidad indivisible ya partida en M04: {unit}")
        if len(provinces) != 1:
            raise ValueError(f"Unidad cruza provincias: {unit}")
        if len(municipalities) != 1:
            raise ValueError(f"Unidad cruza municipios: {unit}")

        comarca_values: set[str] = set()
        for section_id in rows[id_field]:
            node = graph_nodes[str(section_id)]
            value = node.get("COMARCA_CODIGO") or node.get("COMARCA_COD")
            if value not in (None, ""):
                comarca_values.add(str(value).strip())
        for column in ("COMARCA_CODIGO", "COMARCA_COD", "ddd_comarca_codigo"):
            if column in rows.columns:
                comarca_values.update(
                    str(value).strip()
                    for value in rows[column].dropna()
                    if str(value).strip()
                )
        if len(comarca_values) > 1:
            raise ValueError(f"Unidad cruza comarcas: {unit}")

        geometry = rows.geometry.union_all() if hasattr(rows.geometry, "union_all") else rows.geometry.unary_union
        unit_key = str(unit)
        unit_geometries[unit_key] = geometry
        unit_areas[unit_key] = float(geometry.area)
        unit_perimeters[unit_key] = float(geometry.length)
        units[unit_key] = {
            "unit_id": unit_key,
            "population": float(sum(node_population[s] for s in rows[id_field])),
            "province": next(iter(provinces)),
            "municipality": next(iter(municipalities)),
            "closed_urban": bool(rows[closed_urban_field].fillna(False).astype(bool).all()),
            "comarca": next(iter(comarca_values), None),
        }
        initial[unit_key] = next(iter(districts))

    edges: set[tuple[str, str]] = set()
    operational_edge_types: dict[tuple[str, str], set[str]] = defaultdict(set)
    for edge in graph.get("edges", []):
        section_u, section_v = str(edge["u"]), str(edge["v"])
        u = section_unit.get(section_u)
        v = section_unit.get(section_v)
        if u is None or v is None:
            raise ValueError("M03 contiene arista fuera del universo M04")
        unit_u, unit_v = str(u), str(v)
        for left_name, left_part in section_components.get(section_u, []):
            for right_name, right_part in section_components.get(section_v, []):
                shared_component_border = float(left_part.boundary.intersection(right_part.boundary).length)
                if shared_component_border + 1e-9 >= min_shared_border_m:
                    component_edges.add(tuple(sorted((left_name, right_name))))
        if unit_u != unit_v:
            unit_edge = tuple(sorted((unit_u, unit_v)))
            edges.add(unit_edge)
            operational_edge_types[unit_edge].add(str(edge.get("edge_type") or "unclassified"))

    shared_border_lengths = {
        edge: float(unit_geometries[edge[0]].boundary.intersection(unit_geometries[edge[1]].boundary).length)
        for edge in edges
    }

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

    def component_connected(wanted: set[str], edges_for_check: Iterable[tuple[str, str]]) -> bool:
        if not wanted:
            return True
        adjacency = {component: set() for component in wanted}
        for left, right in edges_for_check:
            if left in wanted and right in wanted:
                adjacency[left].add(right)
                adjacency[right].add(left)
        start = next(iter(wanted))
        reached = {start}
        queue: deque[str] = deque([start])
        while queue:
            component = queue.popleft()
            for neighbor in adjacency[component]:
                if neighbor not in reached:
                    reached.add(neighbor)
                    queue.append(neighbor)
        return reached == wanted

    initial_geometric_exceptions: dict[Any, frozenset[str]] = {}
    initial_components: dict[Any, set[str]] = defaultdict(set)
    for unit, district in initial.items():
        initial_components[district].update(unit_components.get(unit, ()))
    combined_component_edges = set(component_edges) | set(internal_component_edges)
    for district, wanted in initial_components.items():
        if component_connected(wanted, component_edges):
            continue
        if component_connected(wanted, combined_component_edges):
            # Excepción heredada estricta: solo se conserva mientras el distrito
            # mantenga exactamente el mismo conjunto de componentes de M04.
            initial_geometric_exceptions[district] = frozenset(wanted)

    total = sum(row["population"] for row in units.values())
    target = total / contract.expected_k
    problem = PreparedProblem(
        sections=sections,
        units=units,
        edges=sorted(edges),
        initial_assignment=initial,
        frozen_districts=frozen,
        target_population=target,
        unit_areas=unit_areas,
        unit_perimeters=unit_perimeters,
        shared_border_lengths=shared_border_lengths,
        unit_components={unit: tuple(components) for unit, components in unit_components.items()},
        component_edges=sorted(component_edges),
        internal_component_edges=sorted(internal_component_edges),
        initial_geometric_exceptions=initial_geometric_exceptions,
        operational_edge_types={
            edge: tuple(sorted(types))
            for edge, types in operational_edge_types.items()
        },
    )
    violations = hard_constraint_violations(problem, initial, contract)
    if violations:
        raise BaselineValidationError(
            "Formación inicial viola restricciones duras: " + ", ".join(violations[:20])
        )
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

    floor_exempt = set(contract.population_floor_exempt_partitions)
    for district, population in pops.items():
        partition = next(iter(provinces.get(district, set())), "")
        if population < floor - 1e-9 and str(partition) not in floor_exempt:
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


def physical_geometry_diagnostics(
    problem: PreparedProblem,
    assignment: Mapping[str, Any],
) -> dict[str, Any]:
    """Diagnóstico físico, nunca una segunda puerta de validez territorial."""
    if not problem.unit_components:
        return {"available": False, "districts": [], "count": 0, "unexplained_count": 0}

    if not problem.component_adjacency:
        component_nodes = {
            component
            for components in problem.unit_components.values()
            for component in components
        }
        component_adjacency = {component: set() for component in component_nodes}
        for left, right in problem.component_edges:
            component_adjacency[left].add(right)
            component_adjacency[right].add(left)
        problem.component_adjacency = component_adjacency

    district_units: dict[Any, set[str]] = defaultdict(set)
    district_components: dict[Any, set[str]] = defaultdict(set)
    for unit, district in assignment.items():
        district_units[district].add(unit)
        district_components[district].update(problem.unit_components.get(unit, ()))

    rows: list[dict[str, Any]] = []
    for district, wanted in district_components.items():
        if not wanted:
            continue
        start = next(iter(wanted))
        reached = {start}
        queue: deque[str] = deque([start])
        while queue:
            component = queue.popleft()
            for neighbor in problem.component_adjacency.get(component, set()) & wanted:
                if neighbor not in reached:
                    reached.add(neighbor)
                    queue.append(neighbor)
        if reached == wanted:
            continue

        units = district_units[district]
        bridge_types: set[str] = set()
        for edge, types in problem.operational_edge_types.items():
            if edge[0] in units and edge[1] in units:
                bridge_types.update(t for t in types if t not in {"geometric", "unclassified"})

        atomic_multipart = any(
            left in wanted and right in wanted
            for left, right in problem.internal_component_edges
        )
        if bridge_types:
            classification = "DECLARED_TOPOLOGY_BRIDGE"
        elif atomic_multipart:
            classification = "ATOMIC_MULTIPART"
        else:
            classification = "UNEXPLAINED_PHYSICAL_DISCONTINUITY"

        rows.append({
            "district_id": str(district),
            "classification": classification,
            "declared_topology_bridge_types": sorted(bridge_types),
            "atomic_multipart_present": atomic_multipart,
        })

    rows.sort(key=lambda row: (
        not row["district_id"].isdigit(),
        int(row["district_id"]) if row["district_id"].isdigit() else row["district_id"],
    ))
    return {
        "available": True,
        "districts": rows,
        "count": len(rows),
        "unexplained_count": sum(
            row["classification"] == "UNEXPLAINED_PHYSICAL_DISCONTINUITY"
            for row in rows
        ),
        "semantics": "diagnostic_only_operational_graph_is_authoritative",
    }

def geometric_shape_metrics(
    problem: PreparedProblem,
    assignment: Mapping[str, Any],
) -> dict[str, float | bool]:
    if len(problem.unit_areas) != len(problem.units) or len(problem.unit_perimeters) != len(problem.units):
        return {"available": False, "polsby_popper_min": 0.0, "polsby_popper_median": 0.0, "penalty": 0.0}
    areas: dict[Any, float] = defaultdict(float)
    perimeters: dict[Any, float] = defaultdict(float)
    for unit, district in assignment.items():
        areas[district] += problem.unit_areas[unit]
        perimeters[district] += problem.unit_perimeters[unit]
    for edge, shared in problem.shared_border_lengths.items():
        left, right = edge
        if assignment[left] == assignment[right]:
            perimeters[assignment[left]] -= 2.0 * shared
    polsby_popper = [
        4.0 * math.pi * area / (perimeters[district] ** 2)
        if area > 0 and perimeters[district] > 0 else 0.0
        for district, area in areas.items()
    ]
    ordered = sorted(polsby_popper)
    median = (
        ordered[len(ordered) // 2]
        if len(ordered) % 2
        else (ordered[len(ordered) // 2 - 1] + ordered[len(ordered) // 2]) / 2.0
    ) if ordered else 0.0
    minimum = min(ordered, default=0.0)
    compactness_penalty = (1.0 - median) + max(0.0, (0.15 - minimum) / 0.15)
    return {
        "available": True,
        "polsby_popper_min": minimum,
        "polsby_popper_median": median,
        "penalty": compactness_penalty,
    }


def candidate_rank(
    problem: PreparedProblem,
    assignment: Mapping[str, Any],
    contract: StrategyContract,
    initial: Mapping[str, Any],
    population_band: float = 0.005,
) -> tuple[Any, ...]:
    pop = population_metrics(problem, assignment, contract)
    shape = geometric_shape_metrics(problem, assignment)
    cut_edges = sum(1 for u, v in problem.edges if assignment[u] != assignment[v])
    churn = sum(assignment[u] != initial[u] for u in initial) / max(1, len(initial))
    # Orden técnico declarativo y no partidista. El hash resuelve empates de
    # forma determinista; no intervienen votos ni composición electoral.
    max_rel_dev = float(pop["max_relative_deviation"])
    rms = float(pop["rms_relative_deviation"])
    return (
        int(pop["districts_outside_tolerance"]),
        int(math.ceil(max_rel_dev / population_band)),
        float(shape["penalty"]),
        max_rel_dev,
        rms,
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


def _proposal_graph(problem: PreparedProblem) -> nx.Graph:
    graph = nx.Graph()
    frozen_by_unit = {
        unit: district
        for district, units in problem.frozen_districts.items()
        for unit in units
    }
    for unit, row in problem.units.items():
        attrs = dict(row)
        # Si un territorio no aporta comarcas, cada unidad recibe una región
        # sintética propia: el sobrecargo queda neutral en vez de inventar una
        # comarca o agrupar artificialmente unidades sin cobertura.
        attrs["comarca"] = attrs.get("comarca") or f"__sin_comarca__:{unit}"
        graph.add_node(unit, **attrs, district=problem.initial_assignment[unit])
    for u, v in problem.edges:
        # Una transición ReCom no puede cruzar provincias porque la provincia es
        # restricción dura y la cuota distrital provincial es invariante.
        if problem.units[u]["province"] != problem.units[v]["province"]:
            continue
        fu, fv = frozen_by_unit.get(u), frozen_by_unit.get(v)
        # Los distritos urbanos cerrados quedan aislados del metagrafo de
        # propuestas, en lugar de generar miles de propuestas que luego serían rechazadas.
        if (fu is not None or fv is not None) and fu != fv:
            continue
        graph.add_edge(
            u, v,
            edge_types=problem.operational_edge_types.get(tuple(sorted((u, v))), ("unclassified",)),
        )
    return graph


def _run_seed(
    problem: PreparedProblem,
    contract: StrategyContract,
    config: StrategyConfig,
    seed: int,
) -> dict[str, Any]:
    require_runtime(config)
    graph = _proposal_graph(problem)
    initial_partition = Partition(
        graph,
        assignment="district",
        updaters={
            "population": updaters.Tally("population", alias="population"),
            "cut_edges": updaters.cut_edges,
        },
    )

    def hard(partition: Any) -> bool:
        return not hard_constraint_violations(problem, _partition_assignment(partition), contract)

    raw_proposal = build_recom_proposal_fn(
        pop_col="population",
        pop_target=problem.target_population,
        epsilon=config.proposal_epsilon,
        region_surcharge={"comarca": config.comarca_surcharge},
        bipartition_tree_fn=partial(
            bipartition_tree,
            max_attempts=config.max_bipartition_attempts,
            allow_pair_reselection=False,
        ),
        pair_selection="district_pairs",
    )
    proposal_failures = 0

    def safe_proposal(partition: Any, *, rng: Any) -> Any:
        nonlocal proposal_failures
        try:
            return raw_proposal(partition, rng=rng)
        except (BalanceError, PopulationBalanceError, ReselectException, MetagraphError, RuntimeError):
            # Fallos esperables de ReCom en pares que no admiten una bipartición
            # equilibrada. Se modelan como self-loop; no deben abortar la cadena.
            proposal_failures += 1
            return partition

    chain = MarkovChain(
        proposal_fn=safe_proposal,
        constraints=[hard],
        initial_partition=initial_partition,
        total_steps=config.steps_per_seed,
        rng=seed,
    )

    best_assignment = dict(problem.initial_assignment)
    best_rank = candidate_rank(problem, best_assignment, contract, problem.initial_assignment, config.population_band)
    unique: set[str] = set()
    self_loops = 0
    previous_hash: str | None = None
    observed = 0
    started = time.perf_counter()
    for partition in chain:
        observed += 1
        assignment = _partition_assignment(partition)
        digest = _assignment_hash(assignment)
        unique.add(digest)
        if previous_hash == digest:
            self_loops += 1
        previous_hash = digest
        rank = candidate_rank(problem, assignment, contract, problem.initial_assignment, config.population_band)
        if rank < best_rank:
            best_rank = rank
            best_assignment = assignment
    elapsed = time.perf_counter() - started
    return {
        "seed": seed,
        "states_observed": observed,
        "unique_states": len(unique),
        "self_loops": self_loops,
        "proposal_failures": proposal_failures,
        "seconds": elapsed,
        "rank": list(best_rank[:-1]),
        "assignment_hash": _assignment_hash(best_assignment),
        "assignment": best_assignment,
    }


def run_portfolio(
    problem: PreparedProblem,
    contract: StrategyContract,
    config: StrategyConfig,
) -> dict[str, Any]:
    initial_rank = candidate_rank(problem, problem.initial_assignment, contract, problem.initial_assignment, config.population_band)
    runs = [_run_seed(problem, contract, config, seed) for seed in config.seeds()]
    selected = min(
        runs,
        key=lambda r: candidate_rank(problem, r["assignment"], contract, problem.initial_assignment, config.population_band),
    )
    selected_assignment = selected["assignment"]
    selected_rank = candidate_rank(problem, selected_assignment, contract, problem.initial_assignment, config.population_band)
    if selected_rank > initial_rank:
        raise AssertionError("El portfolio GerryChain intentó degradar M04; esto no debe ser posible")
    return {"runs": runs, "selected": selected}


def materialise_output(
    problem: PreparedProblem,
    assignment: Mapping[str, Any],
    output_path: Path,
    *,
    unit_field: str = "ddd_unit_id",
    district_field: str = "district_id",
) -> gpd.GeoDataFrame:
    out = problem.sections.copy()
    mapped = out[unit_field].astype(str).map(dict(assignment))
    if mapped.isna().any():
        raise ValueError("La asignación GerryChain no cubre todas las unidades")
    out[district_field] = pd.to_numeric(mapped, errors="raise").astype(int)
    _write_geojson_zip(out, output_path)
    return out


def materialise_portfolio(
    problem: PreparedProblem,
    portfolio: Mapping[str, Any],
    output_path: Path,
) -> list[dict[str, Any]]:
    """Materializa un escenario por semilla para perfiles GerryChain 25/50.

    El candidato seleccionado sigue siendo el único que pasa a M06. El portfolio
    completo queda dentro del cache/checkpoint para comparación posterior.
    """
    base_name = output_path.name
    token = "_m05_distritos_optimizados.geojson.zip"
    if base_name.endswith(token):
        directory_name = base_name[:-len(token)] + "_m05_gerrychain_portfolio"
    else:
        directory_name = output_path.stem + "_gerrychain_portfolio"
    portfolio_dir = output_path.parent / directory_name
    if portfolio_dir.exists():
        import shutil
        shutil.rmtree(portfolio_dir)
    portfolio_dir.mkdir(parents=True, exist_ok=True)

    rows: list[dict[str, Any]] = []
    for index, run in enumerate(portfolio["runs"], start=1):
        candidate = portfolio_dir / f"candidate_{index:03d}_seed_{run['seed']}.geojson.zip"
        materialise_output(problem, run["assignment"], candidate)
        rows.append({
            "index": index,
            "seed": run["seed"],
            "assignment_hash": run["assignment_hash"],
            "rank": run["rank"],
            "states_observed": run["states_observed"],
            "unique_states": run["unique_states"],
            "proposal_failures": run["proposal_failures"],
            "geojson": str(candidate),
            "sha256": _sha256(candidate),
            "selected": run["assignment_hash"] == portfolio["selected"]["assignment_hash"],
        })
    (portfolio_dir / "portfolio.json").write_text(
        json.dumps({
            "schema": "ddd.m05-gerrychain-portfolio/1.0",
            "candidate_count": len(rows),
            "unique_candidate_count": len({row["assignment_hash"] for row in rows}),
            "selected_assignment_hash": portfolio["selected"]["assignment_hash"],
            "candidates": rows,
        }, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return rows


def build_report(
    problem: PreparedProblem,
    contract: StrategyContract,
    config: StrategyConfig,
    portfolio: Mapping[str, Any],
    graph_path: Path,
    initial_path: Path,
    output_path: Path,
    portfolio_rows: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    initial_metrics = population_metrics(problem, problem.initial_assignment, contract)
    selected_assignment = portfolio["selected"]["assignment"]
    final_metrics = population_metrics(problem, selected_assignment, contract)
    hard_before = hard_constraint_violations(problem, problem.initial_assignment, contract)
    hard_after = hard_constraint_violations(problem, selected_assignment, contract)
    if hard_after:
        raise AssertionError("Salida GerryChain viola restricciones duras: " + ", ".join(hard_after[:20]))
    graph_payload = json.loads(graph_path.read_text(encoding="utf-8"))
    source_edge_type_counts = Counter(
        str(edge.get("edge_type") or "unclassified")
        for edge in graph_payload.get("edges", [])
    )
    proposal_edge_type_counts = Counter(
        edge_type
        for types in problem.operational_edge_types.values()
        for edge_type in types
    )
    physical_before = physical_geometry_diagnostics(problem, problem.initial_assignment)
    physical_after = physical_geometry_diagnostics(problem, selected_assignment)
    cut_start = sum(1 for u, v in problem.edges if problem.initial_assignment[u] != problem.initial_assignment[v])
    cut_final = sum(1 for u, v in problem.edges if selected_assignment[u] != selected_assignment[v])
    churn = sum(selected_assignment[u] != problem.initial_assignment[u] for u in problem.initial_assignment)
    # Compatible con estado_produccion.py: índices 0,2,3 = hard, outliers, maxdev.
    objective_start = [
        len(hard_before),
        0.0,
        initial_metrics["districts_outside_tolerance"],
        round(initial_metrics["max_relative_deviation"], 12),
        round(initial_metrics["rms_relative_deviation"] ** 2, 12),
    ]
    objective_final = [
        0,
        0.0,
        final_metrics["districts_outside_tolerance"],
        round(final_metrics["max_relative_deviation"], 12),
        round(final_metrics["rms_relative_deviation"] ** 2, 12),
    ]
    floor = final_metrics["target"] * contract.population_floor_ratio
    cap = final_metrics["target"] * contract.population_cap_ratio
    final_pops = list(final_metrics["district_populations"].values())
    return {
        "schema": "ddd.m05-gerrychain-strategy/2.0",
        "strategy": "gerrychain_recom",
        "strategy_version": STRATEGY_VERSION,
        "engine": {
            "gerrychain": "1.0.0",
            "rustworkx": getattr(rustworkx, "__version__", "unknown") if rustworkx else None,
            "python": platform.python_version(),
        },
        "objective_start": objective_start,
        "objective_final": objective_final,
        "districts_below_floor": sum(
            1 for district, p in final_metrics["district_populations"].items()
            if p < floor - 1e-9
            and str(next(iter({
                problem.units[u]["province"] for u, d in selected_assignment.items()
                if str(d) == str(district)
            }), "")) not in set(contract.population_floor_exempt_partitions)
        ),
        "districts_above_cap": sum(p > cap + 1e-9 for p in final_pops),
        "districts_outside_tolerance": final_metrics["districts_outside_tolerance"],
        "best_max_rel_dev": round(final_metrics["max_relative_deviation"], 12),
        "target_population": final_metrics["target"],
        "cut_edges_start": cut_start,
        "cut_edges_final": cut_final,
        "changed_units": churn,
        "changed_unit_ratio": churn / max(1, len(problem.initial_assignment)),
        "hard_constraints_before": hard_before,
        "hard_constraints_after": hard_after,
        "operational_graph": {
            "authority": "M03",
            "source_graph_edge_type_counts": dict(sorted(source_edge_type_counts.items())),
            "proposal_graph_edge_type_counts": dict(sorted(proposal_edge_type_counts.items())),
            "contiguity_semantics": "operational_graph_including_declared_topology_bridges",
        },
        "physical_geometry_diagnostics": {
            "initial": physical_before,
            "selected": physical_after,
        },
        "search": {
            "steps_per_seed": config.steps_per_seed,
            "seed_base": config.seed_base,
            "seed_count": config.seed_count,
            "seeds": config.seeds(),
            "proposal_epsilon": config.proposal_epsilon,
            "population_band": config.population_band,
            "metric_crs": config.metric_crs,
            "min_shared_border_m": config.min_shared_border_m,
            "max_bipartition_attempts": config.max_bipartition_attempts,
            "pythonhashseed": os.environ.get("PYTHONHASHSEED"),
            "runs": [
                {k: v for k, v in run.items() if k != "assignment"}
                for run in portfolio["runs"]
            ],
            "selected_seed": portfolio["selected"]["seed"],
            "selected_assignment_hash": portfolio["selected"]["assignment_hash"],
            "frozen_geometric_exceptions": {
                "count": len(problem.initial_geometric_exceptions),
                "district_ids": sorted(
                    (str(district) for district in problem.initial_geometric_exceptions),
                    key=lambda value: (not value.isdigit(), int(value) if value.isdigit() else value),
                ),
            },
        },
        "inputs": {
            "graph": str(graph_path),
            "graph_sha256": _sha256(graph_path),
            "initial": str(initial_path),
            "initial_sha256": _sha256(initial_path),
        },
        "output": {
            "geojson": str(output_path),
            "sha256": _sha256(output_path),
        },
        "portfolio": {
            "candidate_count": len(portfolio_rows or []),
            "unique_candidate_count": len({row["assignment_hash"] for row in (portfolio_rows or [])}),
            "candidates": portfolio_rows or [],
        },
        "nonpartisan_contract": {
            "electoral_fields_consumed": [],
            "party_fields_consumed": [],
            "expected_k": contract.expected_k,
            "target_tolerance_ratio": contract.target_tolerance_ratio,
            "population_floor_ratio": contract.population_floor_ratio,
            "population_cap_ratio": contract.population_cap_ratio,
            "province_districts": dict(contract.province_districts),
            "population_floor_exempt_partitions": list(contract.population_floor_exempt_partitions),
        },
    }


def run_from_paths(
    *,
    graph_path: Path,
    initial_path: Path,
    output_path: Path,
    report_path: Path,
    contract: StrategyContract,
    strategy: StrategyConfig,
) -> dict[str, Any]:
    try:
        problem = prepare_problem(
            graph_path,
            initial_path,
            contract,
            metric_crs=strategy.metric_crs,
            min_shared_border_m=strategy.min_shared_border_m,
        )
    except BaselineValidationError:
        raise
    except (ValueError, FileNotFoundError, KeyError) as exc:
        raise BaselineValidationError(str(exc)) from exc
    portfolio = run_portfolio(problem, contract, strategy)
    materialise_output(problem, portfolio["selected"]["assignment"], output_path)
    portfolio_rows = materialise_portfolio(problem, portfolio, output_path)
    report = build_report(
        problem, contract, strategy, portfolio, graph_path, initial_path, output_path,
        portfolio_rows=portfolio_rows,
    )
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return report


def _main_impl() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--params", type=Path)
    ap.add_argument("--run-id", default="local-gerrychain")
    ap.add_argument("--graph", type=Path)
    ap.add_argument("--initial", type=Path)
    ap.add_argument("--output", type=Path)
    ap.add_argument("--report", type=Path)
    ap.add_argument("--expected-k", type=int)
    ap.add_argument("--province-quotas", default="")
    ap.add_argument("--target-tolerance", type=float, default=0.12)
    ap.add_argument("--population-floor", type=float, default=0.80)
    ap.add_argument("--population-cap", type=float, default=1.75)
    ap.add_argument("--steps-per-seed", type=int)
    ap.add_argument("--seed-base", type=int)
    ap.add_argument("--seed-count", type=int)
    ap.add_argument("--proposal-epsilon", type=float)
    ap.add_argument("--population-band", type=float)
    ap.add_argument("--max-bipartition-attempts", type=int)
    args = ap.parse_args()

    try:
        if args.params:
            params_path = args.params.expanduser().resolve()
            cfg = yaml.safe_load(params_path.read_text(encoding="utf-8")) or {}
            contract = contract_from_yaml(cfg)
            strategy = strategy_config_from_yaml(cfg)
            paths = resolve_paths(cfg, params_path, args.run_id)
        else:
            if not all((args.graph, args.initial, args.output, args.report, args.expected_k)):
                ap.error("Sin --params son obligatorios --graph --initial --output --report --expected-k")
            quotas: dict[str, int] = {}
            if args.province_quotas:
                quotas = {
                    k.strip().zfill(2): int(v)
                    for k, v in (item.split("=", 1) for item in args.province_quotas.split(","))
                }
            contract = StrategyContract(
                expected_k=args.expected_k,
                target_tolerance_ratio=args.target_tolerance,
                population_floor_ratio=args.population_floor,
                population_cap_ratio=args.population_cap,
                province_districts=quotas,
            )
            strategy = StrategyConfig()
            paths = {
                "graph": args.graph,
                "initial": args.initial,
                "output": args.output,
                "report": args.report,
            }

        strategy = StrategyConfig(
            steps_per_seed=args.steps_per_seed if args.steps_per_seed is not None else strategy.steps_per_seed,
            seed_base=args.seed_base if args.seed_base is not None else strategy.seed_base,
            seed_count=args.seed_count if args.seed_count is not None else strategy.seed_count,
            proposal_epsilon=args.proposal_epsilon if args.proposal_epsilon is not None else strategy.proposal_epsilon,
            comarca_surcharge=strategy.comarca_surcharge,
            population_band=args.population_band if args.population_band is not None else strategy.population_band,
            metric_crs=strategy.metric_crs,
            min_shared_border_m=strategy.min_shared_border_m,
            max_bipartition_attempts=args.max_bipartition_attempts if args.max_bipartition_attempts is not None else strategy.max_bipartition_attempts,
            require_pythonhashseed_zero=strategy.require_pythonhashseed_zero,
        )
        strategy.validate()
    except (ValueError, FileNotFoundError, KeyError) as exc:
        raise BaselineValidationError(str(exc)) from exc
    report = run_from_paths(
        graph_path=Path(paths["graph"]),
        initial_path=Path(paths["initial"]),
        output_path=Path(paths["output"]),
        report_path=Path(paths["report"]),
        contract=contract,
        strategy=strategy,
    )
    print(json.dumps({
        "strategy": report["strategy"],
        "objective_start": report["objective_start"],
        "objective_final": report["objective_final"],
        "selected_seed": report["search"]["selected_seed"],
        "output": report["output"],
    }, ensure_ascii=False, indent=2))


def main() -> None:
    try:
        _main_impl()
    except BaselineValidationError as exc:
        print(f"[FATAL] BASELINE_INVALID: {exc}", file=__import__("sys").stderr)
        raise SystemExit(42) from exc


if __name__ == "__main__":
    main()
