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
    s4 = (cfg.get("modulos") or {}).get("modulo_04_generar_semi