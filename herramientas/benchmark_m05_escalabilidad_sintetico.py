#!/usr/bin/env python3
"""Benchmark reproducible de escala M05 sobre grafos sintéticos en cadena.

No carga fuentes, topología ni asignaciones territoriales reales. Mide el coste
incremental de repair() tras construir el fixture y declara explícitamente el
presupuesto temporal/candidato empleado.
"""
from __future__ import annotations

import argparse
import json
import platform
from pathlib import Path
import sys
import time
import tracemalloc

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from ddd_core.m05_population_repair import SearchLimits, repair


def fixture(node_count: int, block_size: int = 10):
    if node_count < block_size or node_count % block_size:
        raise ValueError("node_count must be a positive multiple of block_size")
    units = {}
    assignments = {}
    adjacency = {f"u{i:06d}": set() for i in range(node_count)}
    for i in range(node_count):
        unit = f"u{i:06d}"
        units[unit] = {"population": 10, "province": "SYNTHETIC"}
        assignments[unit] = f"d{i // block_size:06d}"
        if i:
            previous = f"u{i - 1:06d}"
            adjacency[unit].add(previous)
            adjacency[previous].add(unit)
    return assignments, units, adjacency


def fixture_summary(node_count: int, block_size: int = 10):
    assignments, units, adjacency = fixture(node_count, block_size)
    return assignments, units, adjacency, sum(map(len, adjacency.values())) // 2


def measure(node_count: int, *, seconds: float, candidates: int, block_size: int):
    assignments, units, adjacency, edge_count = fixture_summary(node_count, block_size)
    tracemalloc.start()
    start = time.perf_counter()
    result = repair(
        assignments=assignments,
        units=units,
        adjacency=adjacency,
        target=block_size * 10,
        tolerance=0.10,
        floor=block_size * 10 - 10,
        cap=block_size * 10 + 10,
        limits=SearchLimits(
            max_depth=2,
            max_transfer_set=1,
            max_candidates=candidates,
            max_seconds=seconds,
            seed=0,
        ),
    )
    elapsed = time.perf_counter() - start
    _, peak_bytes = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    return {
        "nodes": node_count,
        "edges": edge_count,
        "districts": node_count // block_size,
        "repair_wall_seconds": round(elapsed, 6),
        "repair_peak_tracemalloc_bytes": peak_bytes,
        "candidate_budget": candidates,
        "time_budget_seconds": seconds,
        "candidates_examined": result["candidates_examined"],
        "transitions_evaluated": result["transitions_evaluated"],
        "termination_reason": result["termination_reason"],
        "result": result["result"],
        "baseline_restored": result["baseline_restored"],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sizes", nargs="+", type=int, default=[100, 500, 1000])
    parser.add_argument("--seconds", type=float, default=0.5)
    parser.add_argument("--candidates", type=int, default=2000)
    parser.add_argument("--block-size", type=int, default=10)
    args = parser.parse_args()
    rows = [measure(size, seconds=args.seconds, candidates=args.candidates,
                    block_size=args.block_size) for size in args.sizes]
    print(json.dumps({
        "schema": "ddd.n08.m05-synthetic-scalability/1",
        "python": platform.python_version(),
        "platform": platform.platform(),
        "fixture": "undirected path; equal 10-person units; contiguous equal-population districts; no municipality groups",
        "notes": [
            "synthetic diagnostic only; no official data or districts generated",
            "tracemalloc peak is incremental allocations during repair(), excluding the prebuilt fixture",
            "the declared per-call time budget is soft: elapsed time may overshoot between internal checks",
            "elapsed time and explored work vary by machine and load",
        ],
        "results": rows,
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
