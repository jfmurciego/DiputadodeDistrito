from __future__ import annotations

import importlib.util
from pathlib import Path

import geopandas as gpd
from shapely.geometry import Point

ROOT=Path(__file__).resolve().parents[1]
MODULE=ROOT/"modulos/08_integrar_resultados.py"
spec=importlib.util.spec_from_file_location("m08_integrar_resultados",MODULE)
m08=importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(m08)


def _sections():
    return gpd.GeoDataFrame(
        {
            "CUSEC_KEY":["A","B","C"],
            "district_id":[39,39,1],
            "POP_2025":[1200,900,1500],
        },
        geometry=[Point(0,0),Point(1,0),Point(2,0)],
        crs="EPSG:25830",
    )


def test_map_only_gate_requires_explicit_population_threshold():
    report={"map_only_sections":[{"section_id":"A"},{"section_id":"B"}]}
    try:
        m08.derive_declared_missing_districts(
            _sections(),report,
            section_field="CUSEC_KEY",district_field="district_id",
            population_field="POP_2025",max_map_only_population=None,
        )
    except ValueError as exc:
        assert "max_map_only_population" in str(exc)
    else:
        raise AssertionError("Debe bloquear sin umbral poblacional explícito")


def test_map_only_gate_blocks_when_declared_population_exceeds_threshold():
    report={"map_only_sections":[{"section_id":"A"},{"section_id":"B"}]}
    try:
        m08.derive_declared_missing_districts(
            _sections(),report,
            section_field="CUSEC_KEY",district_field="district_id",
            population_field="POP_2025",max_map_only_population=2000,
        )
    except ValueError as exc:
        assert "2100 > 2000" in str(exc)
    else:
        raise AssertionError("Debe bloquear cuando map_only supera el umbral")


def test_map_only_gate_can_authorize_only_wholly_declared_district_below_threshold():
    report={"map_only_sections":[{"section_id":"A"},{"section_id":"B"}]}
    allowed=m08.derive_declared_missing_districts(
        _sections(),report,
        section_field="CUSEC_KEY",district_field="district_id",
        population_field="POP_2025",max_map_only_population=2200,
    )
    assert allowed==["39"]


def test_runtime_materializer_does_not_enable_map_only_by_default():
    text=(ROOT/"herramientas/materializar_contrato_electoral_runtime.py").read_text(encoding="utf-8")
    assert '"allow_declared_map_only_districts": False' in text
    assert '"allow_declared_map_only_districts": True' not in text
