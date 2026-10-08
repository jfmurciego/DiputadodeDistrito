#!/usr/bin/env python3
"""Reproducción aislada M05, versión 1.0.0, 2026-10-08, CI_PENDIENTE.

Origen: encargo Work La Rioja/Cantabria; sin predecesor (herramienta nueva).
Alcance: leer checkpoints exactos, ejecutar solo repair en La Rioja y medir.
No genera soluciones base ni certifica resultados. Cantabria es solo lectura.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import resource
import sys
import time
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from ddd_core import m05_population_repair as core

CHECKPOINTS = {
    "la_rioja": {"run_id": 37473252569, "source_commit": "b9244a523d54016e4364fc0eab19200571aeb336",
                 "sha256": "a949dd2a2ac6e187ccf30f4952073f9490dfa76cca09180c8cb46cf1c3c30fd4", "stage": "M05"},
    "cantabria": {"run_id": 37318299003, "source_commit": "3938c97a8b46590a54016173416acf34c165d5a1",
                  "sha256": "ad72c3856b45a639fd9eb4223d6f3af8fef4e7450568311e1c213b1990e55121", "stage": "M06"},
}


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def decode_checkpoint(raw, territory, expected_sha256):
    """Adaptador JSON equivalente al agrupado del wrapper, sin dependencia GIS.

    Solo La Rioja DISABLED/NOT_NEEDED acredita que el output conservado es
    también el input del reparador posterior. Nunca se infiere el input M05
    base desde su output: no se ejecuta ese motor ni M04.
    """
    if digest(raw) != expected_sha256:
        raise ValueError("CHECKPOINT_SHA256_MISMATCH")
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        report_raw = z.read(f"cache/{territory}_2025_m05_informe.json")
        graph_raw = z.read(f"cache/{territory}_2025_m03_grafo.json")
        geo_raw = z.read(f"cache/{territory}_2025_m05_distritos_optimizados.geojson.zip")
        compatibility = json.loads(z.read("compatibility/m05.json"))
        base_raw = z.read(f"cache/{territory}_2025_m04_semillas.geojson.zip") if territory == "la_rioja" else None
    with zipfile.ZipFile(io.BytesIO(geo_raw)) as z:
        names = [n for n in z.namelist() if n.endswith(".geojson")]
        if len(names) != 1:
            raise ValueError("AMBIGUOUS_GEOJSON")
        features = json.loads(z.read(names[0]))["features"]
    graph = json.loads(graph_raw)
    report = json.loads(report_raw)
    pop = {str(n["id"]): int(n["pop"]) for n in graph["nodes"]}
    if len(pop) != len(graph["nodes"]):
        raise ValueError("DUPLICATE_GRAPH_NODE")
    sections = {}
    groups = {}
    district_closed = {}
    for feature in features:
        row = feature["properties"]
        section = str(row["CUSEC_KEY"])
        unit = row["ddd_unit_id"]
        if not isinstance(unit, str) or not unit or section in sections:
            raise ValueError("INVALID_UNIT_OR_DUPLICATE_SECTION")
        if type(row["district_id"]) is not int or type(row["ddd_closed_urban"]) is not bool:
            raise ValueError("INVALID_DISTRICT_OR_CLOSED_FLAG")
        sections[section] = unit
        groups.setdefault(unit, []).append(row)
        district_closed.setdefault(row["district_id"], []).append(row["ddd_closed_urban"])
    if set(sections) != set(pop):
        raise ValueError("SECTION_GRAPH_COVERAGE")
    units, assignments = {}, {}
    for unit, rows in sorted(groups.items()):
        districts = {r["district_id"] for r in rows}
        provinces = {str(r["CPRO"]).zfill(2) for r in rows}
        if len(districts) != 1 or len(provinces) != 1:
            raise ValueError("SPLIT_ATOMIC_UNIT")
        assignments[unit] = next(iter(districts))
        units[unit] = {"population": sum(pop[str(r["CUSEC_KEY"])] for r in rows),
                       "province": next(iter(provinces)),
                       "municipality_group": unit if unit.endswith(":M") else None}
    adjacency = {u: set() for u in units}
    for edge in graph["edges"]:
        a, b = sections[str(edge["u"])], sections[str(edge["v"])]
        if a != b:
            adjacency[a].add(b)
            adjacency[b].add(a)
    frozen_districts = {d for d, flags in district_closed.items() if all(flags)}
    frozen = {u: d for u, d in assignments.items() if d in frozen_districts}
    protected = {u: {v for v in vs if not ((u in frozen) ^ (v in frozen))}
                 for u, vs in adjacency.items()}
    if report.get("population_floor_exempt_partitions"):
        raise ValueError("FLOOR_EXEMPTION_NOT_SUPPORTED_BY_THIS_REPLAY")
    if sum(pop.values()) != report["total_pop"] or len(set(assignments.values())) != report["K"]:
        raise ValueError("REPORT_TOTAL_OR_K_MISMATCH")
    kwargs = dict(assignments=assignments, units=units, adjacency=protected,
                  target=report["target"], tolerance=report["tolerance_absolute"],
                  floor=report["population_floor"], cap=report["population_cap"],
                  district_floors={d: report["population_floor"] for d in set(assignments.values())})
    check = core.verify_partition_constraints(assignments, units, protected,
                                             floor=kwargs["floor"], cap=kwargs["cap"])
    if not check["valid"]:
        raise ValueError(f"INVALID_PARTITION: {check}")
    historical = report["population_repair"]
    if historical.get("enabled"):
        expected_pops = historical["population_after"]
    else:
        expected_pops = {d: r["population"] for d, r in report["population_status_by_district"].items()}
    if {str(d): p for d, p in check["populations"].items()} != expected_pops:
        raise ValueError("REPORT_POPULATIONS_MISMATCH")
    base_assignments = None
    if base_raw is not None:
        with zipfile.ZipFile(io.BytesIO(base_raw)) as z:
            names = [n for n in z.namelist() if n.endswith(".geojson")]
            if len(names) != 1:
                raise ValueError("AMBIGUOUS_M04_GEOJSON")
            base_features = json.loads(z.read(names[0]))["features"]
        base_sections, base_assignments = {}, {}
        for f in base_features:
            row = f["properties"]
            section, unit, district = str(row["CUSEC_KEY"]), row["ddd_unit_id"], row["district_id"]
            if section in base_sections or sections.get(section) != unit:
                raise ValueError("M04_UNIT_COVERAGE_MISMATCH")
            if unit in base_assignments and base_assignments[unit] != district:
                raise ValueError("M04_SPLIT_ATOMIC_UNIT")
            base_sections[section] = unit
            base_assignments[unit] = district
        if base_sections != sections or set(base_assignments.values()) != set(assignments.values()):
            raise ValueError("M04_SECTION_OR_DISTRICT_COVERAGE_MISMATCH")
    return {"kwargs": kwargs, "frozen": frozen, "raw_adjacency": adjacency,
            "report": report, "compatibility": compatibility,
            "m05_base_input_assignments": base_assignments,
            "section_count": len(sections),
            "member_hashes": {"graph": digest(graph_raw), "geojson_zip": digest(geo_raw),
                              "report": digest(report_raw),
                              **({"m04_geojson_zip": digest(base_raw)} if base_raw else {})}}


def metrics(case, assignments):
    kw = case["kwargs"]
    check = core.verify_partition_constraints(assignments, kw["units"], kw["adjacency"],
                                             floor=kw["floor"], cap=kw["cap"], district_floors=kw["district_floors"])
    pops = check.get("populations", {})
    objective = core.objective(pops, target=kw["target"], tolerance=kw["tolerance"],
                               floor=kw["floor"], cap=kw["cap"], district_floors=kw["district_floors"],
                               cohesion=core.territorial_metrics(assignments, kw["adjacency"])["cut_boundary_edges"])
    return {"structural_constraints": check, "objective": list(objective),
            "population_min": min(pops.values()), "population_max": max(pops.values()),
            "max_relative_deviation": objective[2], "total_relative_deviation": objective[3],
            "outside_districts": {d: p for d, p in pops.items() if abs(p-kw["target"]) > kw["tolerance"]},
            "frozen_preserved": all(assignments[u] == d for u, d in case["frozen"].items())}


def connected_band_obstruction(case, seed, max_states=1000):
    """Enumera conjuntos conectados que contienen seed bajo el techo fino.

    Con población no negativa, podar un conjunto por exceso es definitivo.
    Una cola agotada sin conjunto en banda prueba imposibilidad para esa
    unidad bajo ESTE grafo/atomicidad. Un corte por presupuesto no la prueba.
    No altera asignaciones y no pretende resolver una partición global.
    """
    kw = case["kwargs"]
    units, adjacency = kw["units"], kw["adjacency"]
    if seed not in units or any(u["population"] < 0 for u in units.values()):
        raise ValueError("INVALID_OBSTRUCTION_INPUT")
    lower, upper = kw["target"]-kw["tolerance"], kw["target"]+kw["tolerance"]
    initial = frozenset([seed])
    queue, seen, explored, rejected = [initial], {initial}, [], []
    witness = None
    while queue and len(explored) < max_states:
        nodes = queue.pop(0)
        population = sum(units[u]["population"] for u in nodes)
        explored.append({"units": sorted(nodes), "population": population})
        if population > upper:
            continue
        if population >= lower:
            witness = sorted(nodes)
            break
        neighbors = {v for u in nodes for v in adjacency[u]} - set(nodes)
        for v in sorted(neighbors):
            trial = nodes | {v}
            if trial in seen:
                continue
            seen.add(trial)
            trial_pop = population + units[v]["population"]
            if trial_pop > upper:
                rejected.append({"units": sorted(trial), "population": trial_pop})
            else:
                queue.append(trial)
    complete = witness is None and not queue
    return {"seed": seed, "band_lower": lower, "band_upper": upper,
            "max_states": max_states, "explored": explored, "over_upper": rejected,
            "feasible_connected_set": witness, "exhaustive_no_feasible_set": complete,
            "scope": "protected_atomic_graph_only"}


def replay(case, limits=None):
    historical = case["report"]["population_repair"]
    if historical.get("enabled") is not False or historical.get("activation") != "NOT_NEEDED":
        raise ValueError("PRE_REPAIR_STATE_NOT_PROVEN")
    expected = case["compatibility"]["engine_files"]["ddd_core/m05_population_repair.py"]
    observed = digest((ROOT / "ddd_core/m05_population_repair.py").read_bytes())
    if observed != expected:
        raise ValueError("REPAIR_CODE_DIFFERS_FROM_RUN")
    limits = limits or core.SearchLimits()
    if not (0 < limits.max_seconds <= 5 and 0 < limits.max_candidates <= 20000
            and 0 <= limits.max_depth <= 3 and 1 <= limits.max_transfer_set <= 2):
        raise ValueError("OPERATIONAL_LIMIT_EXCEEDED")
    before = metrics(case, case["kwargs"]["assignments"])
    usage = resource.getrusage(resource.RUSAGE_SELF)
    start = time.perf_counter()
    result = core.repair(**case["kwargs"], limits=limits)
    wall = time.perf_counter() - start
    after_usage = resource.getrusage(resource.RUSAGE_SELF)
    after = metrics(case, result["assignments"])
    if not after["frozen_preserved"] or not after["structural_constraints"]["valid"]:
        raise ValueError("FINAL_CONSTRAINT_FAILURE")
    return {"before": before, "after": after, "repair": result,
            "cost": {"wall_seconds": wall, "user_cpu_seconds": after_usage.ru_utime-usage.ru_utime,
                     "system_cpu_seconds": after_usage.ru_stime-usage.ru_stime,
                     "process_peak_rss": after_usage.ru_maxrss,
                     "peak_rss_unit": "bytes" if sys.platform == "darwin" else "KiB",
                     "peak_rss_scope": "whole_process_high_water_mark"}}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rioja-checkpoint", type=Path, required=True)
    parser.add_argument("--cantabria-checkpoint", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    cases = {t: decode_checkpoint(p.read_bytes(), t, CHECKPOINTS[t]["sha256"])
             for t, p in (("la_rioja", args.rioja_checkpoint), ("cantabria", args.cantabria_checkpoint))}
    result = {"schema": "ddd.isolated-repair-experiment/1.0", "status": "CI_PENDIENTE",
              "certification": False, "checkpoints": CHECKPOINTS,
              "la_rioja": replay(cases["la_rioja"]),
              "cantabria": {"recalculated": False, "metrics": metrics(cases["cantabria"], cases["cantabria"]["kwargs"]["assignments"]),
                            "historical_repair": cases["cantabria"]["report"]["population_repair"]}}
    result["la_rioja"]["focal_only_experiment"] = replay(
        cases["la_rioja"], core.SearchLimits(max_depth=0))
    result["la_rioja"]["obstruction"] = connected_band_obstruction(cases["la_rioja"], "26:26125:M")
    result["la_rioja"]["m05_base_input_metrics"] = metrics(
        cases["la_rioja"], cases["la_rioja"]["m05_base_input_assignments"])
    for t, case in cases.items():
        result[t]["member_hashes"] = case["member_hashes"]
        result[t]["sections"] = case["section_count"]
        result[t]["atomic_units"] = len(case["kwargs"]["units"])
        result[t]["frozen_districts"] = sorted(set(case["frozen"].values()))
    args.output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"before": result["la_rioja"]["before"]["objective"],
                      "after": result["la_rioja"]["after"]["objective"],
                      "result": result["la_rioja"]["repair"]["result"],
                      "cost": result["la_rioja"]["cost"]}))


if __name__ == "__main__":
    main()
