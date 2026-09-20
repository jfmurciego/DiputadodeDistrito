"""Laboratorio M05 para GerryChain/ReCom, sin dependencias del repositorio DDD.

VERSIÓN DEL ADAPTADOR: 1.2.0. La continuidad se valida tanto sobre secciones
como sobre cada componente poligonal, incluidas las secciones MultiPolygon.

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
from dataclasses import asdict, dataclass, field
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
    geometric_shape: float = 0.55
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
    section_areas: dict[str, float] = field(default_factory=dict)
    section_perimeters: dict[str, float] = field(default_factory=dict)
    shared_border_lengths: dict[tuple[str, str], float] = field(default_factory=dict)
    section_components: dict[str, tuple[str, ...]] = field(default_factory=dict)
    component_edges: list[tuple[str, str]] = field(default_factory=list)
    component_adjacency: dict[str, set[str]] = field(default_factory=dict)


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


def _polygon_components(geometry: Any) -> list[Any]:
    if geometry.geom_type == "Polygon":
        return [geometry]
    if geometry.geom_type == "MultiPolygon":
        return list(geometry.geoms)
    # La adaptación conserva geometrías auxiliares (por ejemplo, puntos de
    # pruebas o depuración). Se representan como un único componente aislado:
    # no pueden fabricar aristas geométricas y, si se agrupan con otra sección,
    # la restricción geometric_contiguity bloqueará la partición.
    return [geometry]


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
    min_shared_border_m: float = 0.0,
    preserve_atomic_multipart_sections: bool = False,
    declared_topology_bridges: Sequence[tuple[str, str]] = (),
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
    geometries: dict[str, Any] = {}
    section_areas: dict[str, float] = {}
    section_perimeters: dict[str, float] = {}
    geometry_components: dict[str, list[Any]] = {}
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
        raw_geometry = features[section_id].get("geometry")
        if raw_geometry is not None:
            try:
                from shapely.geometry import shape
            except ImportError as exc:
                raise RuntimeError("Shapely 2.x es necesario para validar la topología") from exc
            geometry = shape(raw_geometry)
            if geometry.is_empty or not geometry.is_valid:
                raise InputContractError(f"Geometría inválida en {section_id}")
            geometries[section_id] = geometry
            geometry_components[section_id] = _polygon_components(geometry)
            section_areas[section_id] = float(geometry.area)
            section_perimeters[section_id] = float(geometry.length)

    if geometries and len(geometries) != len(nodes):
        if min_shared_border_m > 0:
            raise InputContractError("Cobertura geométrica parcial")
        geometries.clear()
        section_areas.clear()
        section_perimeters.clear()
        geometry_components.clear()

    edges: list[tuple[str, str]] = []
    seen: set[tuple[str, str]] = set()
    shared_border_lengths: dict[tuple[str, str], float] = {}
    section_components = {
        section: tuple(f"{section}#{index}" for index in range(len(parts)))
        for section, parts in geometry_components.items()
    }
    component_edges: set[tuple[str, str]] = set()
    logical_bridges = {
        tuple(sorted((_text(left), _text(right))))
        for left, right in declared_topology_bridges
    }
    if any(not left or not right or left == right for left, right in logical_bridges):
        raise InputContractError("Pasarela topológica declarada inválida")
    unknown_bridge_nodes = {
        node for edge in logical_bridges for node in edge if node not in nodes
    }
    if unknown_bridge_nodes:
        raise InputContractError(
            f"Pasarelas con secciones ajenas al universo: {sorted(unknown_bridge_nodes)[:10]}"
        )
    if preserve_atomic_multipart_sections:
        # Una sección censal es la unidad mínima de población y voto. Cuando
        # su geometría oficial es MultiPolygon, sus piezas no pueden recibir
        # distritos distintos. La arista lógica solo une piezas de esa misma
        # sección; nunca fabrica continuidad entre secciones diferentes.
        for components in section_components.values():
            if len(components) > 1:
                anchor = components[0]
                component_edges.update(
                    tuple(sorted((anchor, component)))
                    for component in components[1:]
                )
    for raw in raw_edges:
        u, v = _text(raw.get("u")), _text(raw.get("v"))
        if u not in nodes or v not in nodes or u == v:
            raise InputContractError(f"Arista inválida: {(u, v)}")
        edge = tuple(sorted((u, v)))
        if edge not in seen:
            if geometries:
                shared = float(geometries[u].boundary.intersection(geometries[v].boundary).length)
                shared_border_lengths[edge] = shared
                if (
                    min_shared_border_m > 0
                    and edge not in logical_bridges
                    and shared + 1e-9 < min_shared_border_m
                ):
                    raise InputContractError(
                        f"Arista sin frontera métrica suficiente: {edge}, "
                        f"shared_border_m={shared:.6f} < {min_shared_border_m:.6f}"
                    )
                for left_index, left_part in enumerate(geometry_components[u]):
                    for right_index, right_part in enumerate(geometry_components[v]):
                        component_shared = float(
                            left_part.boundary.intersection(right_part.boundary).length
                        )
                        if component_shared > 1e-9:
                            component_edges.add(tuple(sorted((
                                section_components[u][left_index],
                                section_components[v][right_index],
                            ))))
                if edge in logical_bridges and section_components.get(u) and section_components.get(v):
                    # Las pasarelas son política territorial declarada: no inventan
                    # frontera métrica, pero sí forman parte de la continuidad operativa.
                    component_edges.add(tuple(sorted((
                        section_components[u][0], section_components[v][0]
                    ))))
            seen.add(edge)
            edges.append(edge)
    missing_bridges = logical_bridges - seen
    if missing_bridges:
        raise InputContractError(
            f"Pasarelas declaradas ausentes del grafo M03: {sorted(missing_bridges)[:10]}"
        )
    return AdaptedInputs(
        nodes,
        sorted(edges),
        initial,
        copy.deepcopy(dict(geojson)),
        section_field,
        district_field,
        section_areas,
        section_perimeters,
        shared_border_lengths,
        section_components,
        sorted(component_edges),
    )


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
        if data.section_components:
            if not data.component_adjacency:
                data.component_adjacency = _adjacency(
                    {
                        component: {}
                        for components in data.section_components.values()
                        for component in components
                    },
                    data.component_edges,
                )
            component_adj = data.component_adjacency
            district_components: dict[Any, set[str]] = defaultdict(set)
            for section, district in assignment.items():
                district_components[district].update(data.section_components[section])
            for district, wanted in district_components.items():
                start = next(iter(wanted))
                reached, queue = {start}, deque([start])
                while queue:
                    current = queue.popleft()
                    for neighbor in component_adj[current] & wanted:
                        if neighbor not in reached:
                            reached.add(neighbor)
                            queue.append(neighbor)
                if reached != wanted:
                    violations.append(f"geometric_contiguity:{district}")
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


def geometric_shape_metrics(data: AdaptedInputs, assignment: Mapping[str, Any]) -> dict[str, Any]:
    """Calcula Polsby–Popper en O(n+e) sin disolver geometrías en cada estado."""
    if len(data.section_areas) != len(data.nodes) or len(data.section_perimeters) != len(data.nodes):
        return {"available": False, "penalty": 0.0}
    areas: dict[Any, float] = defaultdict(float)
    perimeters: dict[Any, float] = defaultdict(float)
    for section, district in assignment.items():
        areas[district] += data.section_areas[section]
        perimeters[district] += data.section_perimeters[section]
    for edge, shared in data.shared_border_lengths.items():
        left, right = edge
        if assignment[left] == assignment[right]:
            perimeters[assignment[left]] -= 2.0 * shared
    values = {
        district: 4.0 * math.pi * area / (perimeters[district] ** 2)
        if area > 0 and perimeters[district] > 0 else 0.0
        for district, area in areas.items()
    }
    ordered = sorted(values.values())
    median = (
        ordered[len(ordered) // 2]
        if len(ordered) % 2
        else (ordered[len(ordered) // 2 - 1] + ordered[len(ordered) // 2]) / 2.0
    )
    minimum = min(ordered, default=0.0)
    # Penaliza la forma general y, con mayor fuerza, cualquier distrito por
    # debajo del umbral histórico de publicación 0.15.
    penalty = (1.0 - median) + max(0.0, (0.15 - minimum) / 0.15)
    return {
        "available": True,
        "polsby_popper_min": minimum,
        "polsby_popper_median": median,
        "polsby_popper_mean": sum(ordered) / len(ordered) if ordered else 0.0,
        "districts_below_0_15": sum(value < 0.15 for value in ordered),
        "district_values": {str(key): value for key, value in sorted(values.items(), key=lambda item: str(item[0]))},
        "penalty": penalty,
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
    result["shape"] = geometric_shape_metrics(data, assignment)
    return result


def score_metrics(metrics: Mapping[str, Any], *, weights: Weights = Weights(), edge_count: int = 1) -> float:
    comarca = metrics["comarca"]
    retention = comarca.get("population_retention")
    comarca_penalty = 0.0 if retention is None else 1.0 - retention
    return (
        weights.population * float(metrics["population_max_abs_deviation"])
        + weights.cut_edges * float(metrics["cut_edges"]) / max(1, edge_count)
        + weights.geometric_shape * float(metrics.get("shape", {}).get("penalty", 0.0))
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
    failures: list[str] = []
    observed = 0
    unique_hashes: set[str] = set()
    previous_hash: str | None = None
    self_loops = 0
    best: tuple[float, str, dict[str, Any], dict[str, Any], int] | None = None
    try:
        for partition in chain:
            state = _partition_assignment_by_section(partition)
            state_hash = assignment_hash(state)
            if previous_hash == state_hash:
                self_loops += 1
            previous_hash = state_hash
            unique_hashes.add(state_hash)
            step = observed
            observed += 1
            metrics = plan_metrics(data, state, contract)
            score = score_metrics(metrics, weights=weights, edge_count=len(data.edges))
            rank = (score, state_hash, state, metrics, step)
            if best is None or rank[:2] < best[:2]:
                best = rank
    except RuntimeError as exc:
        failures.append(str(exc))
    if observed == 0:
        raise RuntimeError(f"La cadena no produjo estados: {failures}")
    if best is None:
        raise InputContractError("Ningún estado satisface las restricciones duras")
    selected, metrics, best_step = best[2], best[3], best[4]
    selected_violations = hard_constraint_violations(data, selected, contract)
    report = {
        "engine": {"id": "gerrychain_recom", "library_version": "1.0.0", "adapter_version": "1.1.0"},
        "run": {"seed": seed, "steps_requested": total_steps, "states_observed": observed, "best_step": best_step},
        "telemetry": {"unique_states": len(unique_hashes), "self_loops": self_loops, "failures": failures, "selection_memory": "streaming_constant_states"},
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
        "selected_metrics": metrics,
        "configuration": {"contract": asdict(contract), "weights": asdict(weights), "comarca_surcharge": comarca_surcharge},
    }
    return output_geojson(data, selected), report


# ---------------------------------------------------------------------------
# Estrategia de optimización GerryChain para el paso funcional 2.5.
# Mantiene run_gerrychain() intacto para compatibilidad con los ensembles
# históricos y añade una ruta que admite semillas M04 todavía fuera del
# objetivo poblacional, igual que el M05 canónico.
# ---------------------------------------------------------------------------


def population_target_quality(
    data: AdaptedInputs,
    assignment: Mapping[str, Any],
    contract: Contract,
) -> dict[str, Any]:
    total = sum(node["population"] for node in data.nodes.values())
    target = total / contract.k
    populations: dict[Any, float] = defaultdict(float)
    for section, district in assignment.items():
        populations[district] += data.nodes[section]["population"]
    deviations = {
        district: abs(population - target) / target
        for district, population in populations.items()
    }
    outside = {
        district: value
        for district, value in deviations.items()
        if value > contract.target_tolerance_ratio + 1e-12
    }
    return {
        "target": target,
        "district_populations": {
            str(key): value for key, value in sorted(populations.items(), key=lambda item: str(item[0]))
        },
        "districts_outside_tolerance": len(outside),
        "outside_districts": {
            str(key): value for key, value in sorted(outside.items(), key=lambda item: str(item[0]))
        },
        "max_relative_deviation": max(deviations.values(), default=0.0),
        "total_relative_deviation": sum(deviations.values()),
    }


def structural_constraint_violations(
    data: AdaptedInputs,
    assignment: Mapping[str, Any],
    contract: Contract,
) -> list[str]:
    """Restricciones duras del M05 productivo, sin convertir ±target en hard gate."""
    return [
        violation
        for violation in hard_constraint_violations(data, assignment, contract)
        if not violation.startswith("population_tolerance:")
    ]


def _optimization_rank(
    data: AdaptedInputs,
    assignment: Mapping[str, Any],
    contract: Contract,
    *,
    weights: Weights,
) -> tuple[tuple[Any, ...], dict[str, Any], dict[str, Any]]:
    quality = population_target_quality(data, assignment, contract)
    metrics = plan_metrics(data, assignment, contract)
    score = score_metrics(metrics, weights=weights, edge_count=len(data.edges))
    rank = (
        int(quality["districts_outside_tolerance"]),
        round(float(quality["max_relative_deviation"]), 12),
        round(float(quality["total_relative_deviation"]), 12),
        round(float(score), 12),
        metrics["assignment_sha256"],
    )
    return rank, quality, metrics


def _epsilon_schedule(initial_max_deviation: float, target: float, rounds: int) -> list[float]:
    rounds = max(1, int(rounds))
    target = float(target)
    if rounds == 1:
        return [target]
    start = max(target, min(0.45, max(float(initial_max_deviation) + 0.02, target * 1.5)))
    values = [start + (target - start) * index / (rounds - 1) for index in range(rounds)]
    result: list[float] = []
    for value in values:
        value = round(max(target, value), 12)
        if not result or not math.isclose(value, result[-1], rel_tol=0, abs_tol=1e-12):
            result.append(value)
    if not math.isclose(result[-1], target, rel_tol=0, abs_tol=1e-12):
        result.append(target)
    return result


def _run_recom_optimization_stage(
    data: AdaptedInputs,
    contract: Contract,
    initial_assignment: Mapping[str, Any],
    *,
    epsilon: float,
    total_steps: int,
    seed: int,
    comarca_surcharge: float,
    weights: Weights,
) -> tuple[dict[str, Any], dict[str, Any]]:
    if total_steps < 1:
        raise InputContractError("total_steps debe ser positivo")
    try:
        import networkx as nx
        from gerrychain import MarkovChain, Partition, updaters
        from gerrychain.proposals import ReCom
    except ImportError as exc:
        raise RuntimeError("GerryChain 1.0 no está instalado en este entorno") from exc

    nx_graph = nx.Graph()
    for section, attrs in data.nodes.items():
        node_attrs = dict(attrs)
        node_attrs["district"] = initial_assignment[section]
        nx_graph.add_node(section, **node_attrs)
    nx_graph.add_edges_from(data.edges)
    initial = Partition(
        nx_graph,
        assignment="district",
        updaters={
            "population": updaters.Tally("population", alias="population"),
            "cut_edges": updaters.cut_edges,
        },
    )
    ideal = sum(node["population"] for node in data.nodes.values()) / contract.k

    def ddd_structural_contract(partition: Any) -> bool:
        return not structural_constraint_violations(
            data, _partition_assignment_by_section(partition), contract
        )

    surcharge = (
        {"comarca": comarca_surcharge}
        if comarca_surcharge and all(node.get("comarca") for node in data.nodes.values())
        else None
    )
    chain = MarkovChain(
        proposal_fn=ReCom.district_pairs_mst(
            pop_col="population",
            pop_target=ideal,
            epsilon=float(epsilon),
            region_surcharge=surcharge,
            allow_pair_reselection=True,
        ),
        constraints=[ddd_structural_contract],
        initial_partition=initial,
        total_steps=int(total_steps),
        rng=int(seed),
    )

    baseline = dict(initial_assignment)
    best_rank, best_quality, best_metrics = _optimization_rank(
        data, baseline, contract, weights=weights
    )
    best_assignment = baseline
    best_step = -1
    previous_hash = assignment_hash(baseline)
    unique_hashes = {previous_hash}
    self_loops = 0
    observed = 0
    failures: list[str] = []
    try:
        for step, partition in enumerate(chain):
            state = _partition_assignment_by_section(partition)
            state_hash = assignment_hash(state)
            if state_hash == previous_hash:
                self_loops += 1
            previous_hash = state_hash
            unique_hashes.add(state_hash)
            observed += 1
            rank, quality, metrics = _optimization_rank(data, state, contract, weights=weights)
            if rank < best_rank:
                best_rank = rank
                best_quality = quality
                best_metrics = metrics
                best_assignment = dict(state)
                best_step = step
    except RuntimeError as exc:
        failures.append(str(exc))

    return best_assignment, {
        "epsilon": float(epsilon),
        "seed": int(seed),
        "steps_requested": int(total_steps),
        "states_observed": observed,
        "unique_states": len(unique_hashes),
        "self_loops": self_loops,
        "best_step": best_step,
        "best_rank": list(best_rank[:-1]),
        "best_quality": best_quality,
        "best_metrics": best_metrics,
        "failures": failures,
    }


def run_gerrychain_optimization(
    data: AdaptedInputs,
    contract: Contract,
    *,
    steps_per_stage: int = 250,
    warmup_rounds: int = 4,
    seed: int = 20260920,
    comarca_surcharge: float = 0.30,
    weights: Weights = Weights(),
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Optimización ReCom compatible con semillas M04 todavía fuera de ±target.

    El suelo/techo poblacional, K, provincia, cuotas, atomicidad, disciplina
    municipal, núcleos urbanos cerrados y continuidad siguen siendo hard gates.
    La tolerancia objetivo se usa como objetivo lexicográfico y como epsilon
    final de ReCom, igualando la semántica productiva del M05 canónico.
    """
    structural = structural_constraint_violations(data, data.initial_assignment, contract)
    if structural:
        raise InputContractError(
            "La partición inicial incumple restricciones estructurales: "
            + ", ".join(structural[:30])
        )
    before_rank, before_quality, before_metrics = _optimization_rank(
        data, data.initial_assignment, contract, weights=weights
    )
    schedule = _epsilon_schedule(
        float(before_quality["max_relative_deviation"]),
        contract.target_tolerance_ratio,
        warmup_rounds,
    )
    current = dict(data.initial_assignment)
    best = dict(current)
    best_rank = before_rank
    best_quality = before_quality
    best_metrics = before_metrics
    stages: list[dict[str, Any]] = []
    for index, epsilon in enumerate(schedule):
        stage_assignment, stage_report = _run_recom_optimization_stage(
            data,
            contract,
            current,
            epsilon=epsilon,
            total_steps=steps_per_stage,
            seed=int(seed) + index * 1009,
            comarca_surcharge=comarca_surcharge,
            weights=weights,
        )
        current = stage_assignment
        rank, quality, metrics = _optimization_rank(data, current, contract, weights=weights)
        stage_report["selected_rank"] = list(rank[:-1])
        stage_report["selected_quality"] = quality
        stages.append(stage_report)
        if rank < best_rank:
            best = dict(current)
            best_rank = rank
            best_quality = quality
            best_metrics = metrics

    final_structural = structural_constraint_violations(data, best, contract)
    if final_structural:
        raise InputContractError(
            "GerryChain produjo una solución estructuralmente inválida: "
            + ", ".join(final_structural[:30])
        )
    if int(best_quality["districts_outside_tolerance"]) == 0:
        status = "REPAIRED"
    elif best_rank < before_rank:
        status = "IMPROVED_NOT_REPAIRED"
    else:
        status = "NO_IMPROVEMENT"
    report = {
        "schema": "ddd.m05-gerrychain-optimization/1.0",
        "engine": {
            "id": "gerrychain_recom",
            "library_version": "1.0.0",
            "adapter_version": "1.2.0",
        },
        "optimization_status": status,
        "hard_constraints": {
            "all_pass": True,
            "violations": [],
            "checks": [
                "unit_universe", "k", "population_floor", "population_cap",
                "province", "province_apportionment", "atomic_unit",
                "municipality", "closed_urban", "contiguity",
                "geometric_contiguity", "declared_topology_bridges",
            ],
        },
        "target_tolerance": {
            "ratio": contract.target_tolerance_ratio,
            "before": before_quality,
            "after": best_quality,
            "met": int(best_quality["districts_outside_tolerance"]) == 0,
        },
        "objective": {
            "before": list(before_rank[:-1]),
            "after": list(best_rank[:-1]),
            "non_degrading": best_rank <= before_rank,
        },
        "initial_metrics": before_metrics,
        "selected_metrics": best_metrics,
        "schedule": schedule,
        "stages": stages,
        "configuration": {
            "contract": asdict(contract),
            "weights": asdict(weights),
            "steps_per_stage": int(steps_per_stage),
            "warmup_rounds": int(warmup_rounds),
            "seed": int(seed),
            "comarca_surcharge": comarca_surcharge,
        },
    }
    return output_geojson(data, best), report
