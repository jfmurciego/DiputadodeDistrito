"""Laboratorio M05 para GerryChain/ReCom, sin dependencias del repositorio DDD.

La frontera correcta es sección censal: el ``id`` del grafo M03 se une con
``CUSEC_KEY`` del GeoJSON M04. ``ddd_unit_id`` NO es la clave de unión; es la
unidad atómica de asignación y puede repetirse en varias secciones.

Este módulo separa tres responsabilidades:
1. adaptar y validar M03 + M04 (+ tabla comarcal opcional),
2. evaluar restricciones duras y métricas comarcales sin GerryChain,
3. ejecutar ReCom cuando GerryChain 1.0 está instalado.
"""
from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import asdict, dataclass
import copy
import csv
import hashlib
import json
import math
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence
import zipfile


class InputContractError(ValueError):
    """La entrada no puede cruzar la frontera M03/M04 de forma inequívoca."""


@dataclass(frozen=True)
class Contract:
    k: int
    target_tolerance_ratio: float
    population_floor_ratio: float = 0.80
    population_cap_ratio: float = 1.75
    municipality_atomicity_limit_ratio: float = 1.75
    require_single_province: bool = True
    require_contiguity: bool = True
    province_districts: dict[str, int] | None = None
    require_municipality_discipline: bool = True
    max_mixed_districts_per_split_municipality: int = 1
    preserve_closed_urban: bool = True


@dataclass(frozen=True)
class Weights:
    population: float = 1.0
    cut_edges: float = 0.20
    comarca_fragmentation: float = 0.75
    churn: float = 0.05


@dataclass
class AdaptedInputs:
    nodes: dict[str, dict[str, Any]]
    edges: list[tuple[str, str]]
    initial_assignment: dict[str, Any]
    geojson: dict[str, Any]
    section_field: str
    district_field: str


def _text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value).strip()


def _read_json_or_zip(path: str | Path) -> dict[str, Any]:
    path = Path(path)
    if path.suffix.lower() == ".zip":
        with zipfile.ZipFile(path) as archive:
            names = [n for n in archive.namelist() if n.lower().endswith((".json", ".geojson"))]
            if len(names) != 1:
                raise InputContractError(f"ZIP debe contener un único JSON/GeoJSON; contiene {names}")
            return json.loads(archive.read(names[0]).decode("utf-8"))
    return json.loads(path.read_text(encoding="utf-8"))


def load_comarca_lookup(
    path: str | Path,
    *,
    municipality_col: str = "Municipio código",
    comarca_code_col: str = "Comarca código",
    comarca_name_col: str = "Comarca nombre",
) -> dict[str, tuple[str, str]]:
    """Carga una relación municipio->comarca y rechaza asignaciones ambiguas."""
    path = Path(path)
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        sample = handle.read(8192)
        handle.seek(0)
        try:
            dialect = csv.Sniffer().sniff(sample, delimiters=",;\t")
        except csv.Error:
            dialect = csv.excel
        reader = csv.DictReader(handle, dialect=dialect)
        required = {municipality_col, comarca_code_col, comarca_name_col}
        missing = required - set(reader.fieldnames or [])
        if missing:
            raise InputContractError(f"Tabla comarcal sin columnas {sorted(missing)}")
        result: dict[str, tuple[str, str]] = {}
        for row_no, row in enumerate(reader, start=2):
            municipality = _text(row[municipality_col])
            value = (_text(row[comarca_code_col]), _text(row[comarca_name_col]))
            if not municipality or not all(value):
                raise InputContractError(f"Fila comarcal {row_no} incompleta")
            previous = result.get(municipality)
            if previous is not None and previous != value:
                raise InputContractError(
                    f"Municipio {municipality} asignado a dos comarcas: {previous} y {value}"
                )
            result[municipality] = value
    return result


def _feature_index(geojson: Mapping[str, Any], section_field: str) -> dict[str, dict[str, Any]]:
    index: dict[str, dict[str, Any]] = {}
    for position, feature in enumerate(geojson.get("features", [])):
        props = feature.get("properties") or {}
        section_id = _text(props.get(section_field))
        if not section_id:
            raise InputContractError(f"Feature {position} sin {section_field}")
        if section_id in index:
            raise InputContractError(f"Sección duplicada en M04: {section_id}")
        index[section_id] = feature
    return index


def adapt_inputs(
    graph_data: Mapping[str, Any],
    geojson: Mapping[str, Any],
    *,
    section_field: str = "CUSEC_KEY",
    district_field: str = "district_id",
    municipality_field: str = "CUMUN",
    province_field: str = "CPRO",
    population_field: str | None = None,
    atomic_unit_field: str = "ddd_unit_id",
    closed_urban_field: str = "ddd_closed_urban",
    comarca_code_fields: Sequence[str] = ("COMARCA_CODIGO", "COMARCA_COD"),
    comarca_name_fields: Sequence[str] = ("COMARCA_NOMBRE", "COMARCA_NOM"),
    comarca_lookup: Mapping[str, tuple[str, str]] | None = None,
    comarca_enabled: bool = False,
) -> AdaptedInputs:
    """Adapta M03/M04 usando sección como clave y ddd_unit_id como atomicidad."""
    features = _feature_index(geojson, section_field)
    raw_nodes = graph_data.get("nodes")
    raw_edges = graph_data.get("edges")
    if not isinstance(raw_nodes, list) or not isinstance(raw_edges, list):
        raise InputContractError("M03 debe contener listas nodes y edges")

    graph_nodes: dict[str, Mapping[str, Any]] = {}
    for raw in raw_nodes:
        section_id = _text(raw.get("id"))
        if not section_id or section_id in graph_nodes:
            raise InputContractError(f"Nodo M03 nulo o duplicado: {section_id!r}")
        graph_nodes[section_id] = raw

    graph_ids, feature_ids = set(graph_nodes), set(features)
    if graph_ids != feature_ids:
        raise InputContractError(
            "Universos M03/M04 distintos: "
            f"solo_m03={sorted(graph_ids-feature_ids)[:5]}, "
            f"solo_m04={sorted(feature_ids-graph_ids)[:5]}"
        )

    nodes: dict[str, dict[str, Any]] = {}
    initial: dict[str, Any] = {}
    for section_id in sorted(graph_nodes):
        raw = graph_nodes[section_id]
        props = features[section_id].get("properties") or {}
        if district_field not in props:
            raise InputContractError(f"Sección {section_id} sin {district_field}")
        district = props[district_field]
        municipality = _text(props.get(municipality_field))
        province = _text(props.get(province_field))
        atomic_unit = _text(props.get(atomic_unit_field)) or section_id
        if not municipality or not province:
            raise InputContractError(f"Sección {section_id} sin municipio o provincia")

        graph_pop = raw.get("pop")
        if graph_pop is None:
            raise InputContractError(f"Nodo {section_id} sin pop")
        population = float(graph_pop)
        if population < 0 or not math.isfinite(population):
            raise InputContractError(f"Población inválida en {section_id}: {graph_pop!r}")
        if population_field and props.get(population_field) is not None:
            feature_pop = float(props[population_field])
            if not math.isclose(population, feature_pop, rel_tol=0, abs_tol=1e-6):
                raise InputContractError(
                    f"Población M03/M04 distinta en {section_id}: {population} != {feature_pop}"
                )

        comarca_code = next((_text(props.get(c)) for c in comarca_code_fields if _text(props.get(c))), "")
        comarca_name = next((_text(props.get(c)) for c in comarca_name_fields if _text(props.get(c))), "")
        if not comarca_code:
            comarca_code = next((_text(raw.get(c)) for c in comarca_code_fields if _text(raw.get(c))), "")
            comarca_name = next((_text(raw.get(c)) for c in comarca_name_fields if _text(raw.get(c))), "")
        if not comarca_code and comarca_lookup is not None and municipality in comarca_lookup:
            comarca_code, comarca_name = comarca_lookup[municipality]
        if comarca_enabled and (not comarca_code or not comarca_name):
            raise InputContractError(f"Cobertura comarcal incompleta en {section_id}/{municipality}")

        nodes[section_id] = {
            "section_id": section_id,
            "population": population,
            "district": district,
            "municipality": municipality,
            "province": province,
            "atomic_unit": atomic_unit,
            "closed_urban": bool(props.get(closed_urban_field, False)),
            "comarca": comarca_code or None,
            "comarca_name": comarca_name or None,
        }
        initial[section_id] = district

    edges: list[tuple[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for raw in raw_edges:
        u, v = _text(raw.get("u")), _text(raw.get("v"))
        if u not in nodes or v not in nodes or u == v:
            raise InputContractError(f"Arista inválida: {(u, v)}")
        edge = tuple(sorted((u, v)))
        if edge not in seen:
            seen.add(edge)
            edges.append(edge)
    return AdaptedInputs(nodes, sorted(edges), initial, copy.deepcopy(dict(geojson)), section_field, district_field)


def adapt_files(graph_path: str | Path, geojson_path: str | Path, **kwargs: Any) -> AdaptedInputs:
    return adapt_inputs(_read_json_or_zip(graph_path), _read_json_or_zip(geojson_path), **kwargs)


def assignment_hash(assignment: Mapping[str, Any]) -> str:
    payload = json.dumps(
        [[str(k), str(v)] for k, v in sorted(assignment.items())],
        ensure_ascii=False,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _adjacency(nodes: Mapping[str, Any], edges: Iterable[tuple[str, str]]) -> dict[str, set[str]]:
    result = {node: set() for node in nodes}
    for u, v in edges:
        result[u].add(v)
        result[v].add(u)
    return result


def hard_constraint_violations(
    data: AdaptedInputs,
    assignment: Mapping[str, Any],
    contract: Contract,
) -> list[str]:
    violations: list[str] = []
    if set(assignment) != set(data.nodes):
        return ["unit_universe"]
    districts = set(assignment.values())
    if len(districts) != contract.k:
        violations.append("k")
    total = sum(node["population"] for node in data.nodes.values())
    target = total / contract.k
    pops: dict[Any, float] = defaultdict(float)
    provinces: dict[Any, set[str]] = defaultdict(set)
    by_atomic: dict[str, set[Any]] = defaultdict(set)
    by_municipality: dict[str, set[Any]] = defaultdict(set)
    municipality_pop: dict[str, float] = defaultdict(float)
    for section, district in assignment.items():
        node = data.nodes[section]
        pops[district] += node["population"]
        provinces[district].add(node["province"])
        by_atomic[node["atomic_unit"]].add(district)
        by_municipality[node["municipality"]].add(district)
        municipality_pop[node["municipality"]] += node["population"]
    for district, pop in pops.items():
        if pop < target * contract.population_floor_ratio - 1e-9:
            violations.append(f"population_floor:{district}")
        if pop > target * contract.population_cap_ratio + 1e-9:
            violations.append(f"population_cap:{district}")
        if abs(pop - target) > target * contract.target_tolerance_ratio + 1e-9:
            violations.append(f"population_tolerance:{district}")
    if contract.require_single_province:
        violations.extend(f"province:{d}" for d, values in provinces.items() if len(values) > 1)
    violations.extend(f"atomic_unit:{u}" for u, values in by_atomic.items() if len(values) > 1)
    if contract.require_single_province and contract.province_districts:
        province_counts: dict[str, int] = defaultdict(int)
        for values in provinces.values():
            if len(values) == 1:
                province_counts[next(iter(values))] += 1
        for province, expected in contract.province_districts.items():
            if province_counts.get(str(province), 0) != int(expected):
                violations.append(f"province_count:{province}")
    if contract.require_municipality_discipline:
        district_municipalities: dict[Any, set[str]] = defaultdict(set)
        for section, district in assignment.items():
            district_municipalities[district].add(data.nodes[section]["municipality"])
        cap = target * contract.population_cap_ratio
        for municipality, values in by_municipality.items():
            population = municipality_pop[municipality]
            minimum = max(1, math.ceil(population / cap)) if population > 0 else 1
            maximum = max(1, math.ceil(population / target)) if population > 0 else 1
            mixed = sum(1 for district in values if len(district_municipalities[district]) > 1)
            if not minimum <= len(values) <= maximum:
                violations.append(f"municipality:{municipality}")
            if len(values) > 1 and mixed > contract.max_mixed_districts_per_split_municipality:
                violations.append(f"municipality_mixed:{municipality}")
    if contract.preserve_closed_urban:
        closed_by_district: dict[Any, set[str]] = defaultdict(set)
        initial_members: dict[Any, set[str]] = defaultdict(set)
        for section, district in data.initial_assignment.items():
            initial_members[district].add(section)
            if data.nodes[section]["closed_urban"]:
                closed_by_district[district].add(section)
        frozen = {
            district: members
            for district, members in initial_members.items()
            if members and closed_by_district[district] == members
        }
        for district, members in frozen.items():
            current = {section for section, assigned in assignment.items() if assigned == district}
            if current != members:
                violations.append(f"closed_urban:{district}")
    if contract.require_contiguity:
        adj = _adjacency(data.nodes, data.edges)
        members: dict[Any, set[str]] = defaultdict(set)
        for section, district in assignment.items():
            members[district].add(section)
        for district, wanted in members.items():
            start = next(iter(wanted))
            reached, queue = {start}, deque([start])
            while queue:
                current = queue.popleft()
                for neighbor in adj[current] & wanted:
                    if neighbor not in reached:
                        reached.add(neighbor)
                        queue.append(neighbor)
            if reached != wanted:
                violations.append(f"contiguity:{district}")
    return sorted(set(violations))


def comarca_metrics(data: AdaptedInputs, assignment: Mapping[str, Any]) -> dict[str, Any]:
    by_comarca: dict[str, dict[Any, float]] = defaultdict(lambda: defaultdict(float))
    by_district: dict[Any, dict[str, float]] = defaultdict(lambda: defaultdict(float))
    total_population = 0.0
    covered_population = 0.0
    for section, district in assignment.items():
        node = data.nodes[section]
        pop, comarca = node["population"], node.get("comarca")
        total_population += pop
        if comarca:
            covered_population += pop
            by_comarca[comarca][district] += pop
            by_district[district][comarca] += pop
    split_count = sum(1 for pieces in by_comarca.values() if len([p for p in pieces.values() if p > 0]) > 1)
    retention_num = sum(max(pieces.values()) for pieces in by_comarca.values() if pieces)
    outside_dominant = sum(sum(parts.values()) - max(parts.values()) for parts in by_district.values() if parts)
    entropy_weighted = 0.0
    for parts in by_district.values():
        district_pop = sum(parts.values())
        if district_pop:
            entropy_weighted += district_pop * -sum(
                (p / district_pop) * math.log(p / district_pop) for p in parts.values() if p > 0
            )
    aligned_boundary_edges = 0
    intra_comarca_cut_edges = 0
    for u, v in data.edges:
        cu, cv = data.nodes[u].get("comarca"), data.nodes[v].get("comarca")
        if cu and cv and cu != cv and assignment[u] != assignment[v]:
            aligned_boundary_edges += 1
        if cu and cv and cu == cv and assignment[u] != assignment[v]:
            intra_comarca_cut_edges += 1
    return {
        "coverage_population_ratio": covered_population / total_population if total_population else 0.0,
        "split_communities": split_count,
        "communities_per_district": {str(k): len(v) for k, v in sorted(by_district.items(), key=lambda x: str(x[0]))},
        "population_retention": retention_num / covered_population if covered_population else None,
        "population_outside_dominant_comarca": outside_dominant,
        "district_comarca_entropy": entropy_weighted / covered_population if covered_population else None,
        "aligned_comarca_boundary_edges": aligned_boundary_edges,
        "intra_comarca_cut_edges": intra_comarca_cut_edges,
    }


def plan_metrics(data: AdaptedInputs, assignment: Mapping[str, Any], contract: Contract) -> dict[str, Any]:
    total = sum(node["population"] for node in data.nodes.values())
    target = total / contract.k
    district_pops: dict[Any, float] = defaultdict(float)
    for section, district in assignment.items():
        district_pops[district] += data.nodes[section]["population"]
    cut_edges = sum(1 for u, v in data.edges if assignment[u] != assignment[v])
    churn = sum(1 for s in assignment if assignment[s] != data.initial_assignment[s]) / len(assignment)
    result = {
        "population_total": total,
        "population_target": target,
        "population_max_abs_deviation": max(abs(p - target) / target for p in district_pops.values()),
        "district_populations": {str(k): v for k, v in sorted(district_pops.items(), key=lambda x: str(x[0]))},
        "cut_edges": cut_edges,
        "assignment_churn": churn,
        "assignment_sha256": assignment_hash(assignment),
    }
    result["comarca"] = comarca_metrics(data, assignment)
    return result


def score_metrics(metrics: Mapping[str, Any], *, weights: Weights = Weights(), edge_count: int = 1) -> float:
    comarca = metrics["comarca"]
    retention = comarca.get("population_retention")
    comarca_penalty = 0.0 if retention is None else 1.0 - retention
    return (
        weights.population * float(metrics["population_max_abs_deviation"])
        + weights.cut_edges * float(metrics["cut_edges"]) / max(1, edge_count)
        + weights.comarca_fragmentation * comarca_penalty
        + weights.churn * float(metrics["assignment_churn"])
    )


def select_best_state(
    data: AdaptedInputs,
    states: Iterable[Mapping[str, Any]],
    contract: Contract,
    *,
    weights: Weights = Weights(),
) -> tuple[dict[str, Any], dict[str, Any], int]:
    best: tuple[float, str, dict[str, Any], dict[str, Any], int] | None = None
    for step, state in enumerate(states):
        candidate = dict(state)
        if hard_constraint_violations(data, candidate, contract):
            continue
        metrics = plan_metrics(data, candidate, contract)
        score = score_metrics(metrics, weights=weights, edge_count=len(data.edges))
        rank = (score, metrics["assignment_sha256"], candidate, metrics, step)
        if best is None or rank[:2] < best[:2]:
            best = rank
    if best is None:
        raise InputContractError("Ningún estado satisface las restricciones duras")
    return best[2], best[3], best[4]


def output_geojson(data: AdaptedInputs, assignment: Mapping[str, Any]) -> dict[str, Any]:
    result = copy.deepcopy(data.geojson)
    for feature in result.get("features", []):
        props = feature.get("properties") or {}
        section_id = _text(props.get(data.section_field))
        props[data.district_field] = assignment[section_id]
        node = data.nodes[section_id]
        if node.get("comarca"):
            props["ddd_comarca_codigo"] = node["comarca"]
            props["ddd_comarca_nombre"] = node["comarca_name"]
        feature["properties"] = props
    return result


def _partition_assignment_by_section(partition: Any) -> dict[str, Any]:
    raw = partition.assignment.to_dict() if hasattr(partition.assignment, "to_dict") else dict(partition.assignment)
    result: dict[str, Any] = {}
    for node_id, district in raw.items():
        attrs = partition.graph.node_data(node_id)
        result[_text(attrs["section_id"])] = district
    return result


def run_gerrychain(
    data: AdaptedInputs,
    contract: Contract,
    *,
    total_steps: int,
    seed: int,
    comarca_surcharge: float = 0.30,
    weights: Weights = Weights(),
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Ejecuta GerryChain 1.0; no se llama durante las pruebas sin dependencia."""
    if total_steps < 1:
        raise InputContractError("total_steps debe ser positivo")
    if not 0 <= comarca_surcharge <= 1:
        raise InputContractError("comarca_surcharge debe estar entre 0 y 1")
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

    surcharge = {"comarca": comarca_surcharge} if comarca_surcharge and all(n.get("comarca") for n in data.nodes.values()) else None
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
    states: list[dict[str, Any]] = []
    failures: list[str] = []
    try:
        for partition in chain:
            states.append(_partition_assignment_by_section(partition))
    except RuntimeError as exc:
        failures.append(str(exc))
    if not states:
        raise RuntimeError(f"La cadena no produjo estados: {failures}")
    selected, metrics, best_step = select_best_state(data, states, contract, weights=weights)
    hashes = [assignment_hash(s) for s in states]
    selected_violations = hard_constraint_violations(data, selected, contract)
    report = {
        "engine": {"id": "gerrychain_recom", "library_version": "1.0.0", "adapter_version": "1.0.0"},
        "run": {"seed": seed, "steps_requested": total_steps, "states_observed": len(states), "best_step": best_step},
        "telemetry": {"unique_states": len(set(hashes)), "self_loops": sum(a == b for a, b in zip(hashes, hashes[1:])), "failures": failures},
        "hard_constraints": {
            "all_pass": not selected_violations,
            "violations": selected_violations,
            "checks": [
                "unit_universe", "k", "population", "province",
                "province_apportionment", "atomic_unit", "municipality",
                "closed_urban", "contiguity",
            ],
        },
        "initial_metrics": plan_metrics(data, data.initial_assignment, contract),
        "selected_metrics": metrics,
        "configuration": {"contract": asdict(contract), "weights": asdict(weights), "comarca_surcharge": comarca_surcharge},
    }
    return output_geojson(data, selected), report
