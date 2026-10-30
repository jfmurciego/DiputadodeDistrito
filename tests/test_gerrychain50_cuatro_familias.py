"""Versión 1.0.0; 2026-10-30; candidato. Regresiones de las cuatro familias de fallo del lote GerryChain 50.
Origen: nuevo, sin predecesor. Lote de 18 runs del 30-10-2026 (6 PASS, 12 FAIL en M05).
"""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

import geopandas as gpd
from shapely.geometry import box

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ddd_core.m05_gerrychain_strategy import (  # noqa: E402
    BaselineValidationError,
    StrategyContract,
    contract_from_yaml,
    ensemble_cardinality_check,
    hard_constraint_violations,
    prepare_problem,
)


def _write(root: Path, rows: list[dict], pops: list[int]) -> tuple[Path, Path]:
    """Cadena de secciones contiguas; cada fila trae sus columnas M04."""
    ids = [r["CUSEC_KEY"] for r in rows]
    gdf = gpd.GeoDataFrame(
        {key: [r[key] for r in rows] for key in rows[0]},
        geometry=[box(i, 0, i + 1, 1) for i in range(len(rows))],
        crs="EPSG:3035",
    )
    geo = root / "m04.geojson"
    geo.write_text(gdf.to_json(), encoding="utf-8")
    graph = {
        "nodes": [{"id": s, "pop": p} for s, p in zip(ids, pops)],
        "edges": [{"u": a, "v": b, "edge_type": "geometric"} for a, b in zip(ids, ids[1:])],
    }
    graph_path = root / "m03.json"
    graph_path.write_text(json.dumps(graph), encoding="utf-8")
    return graph_path, geo


def _row(cusec, unit, cpro, part, mun, district):
    return {"CUSEC_KEY": cusec, "ddd_unit_id": unit, "CPRO": cpro, "DDD_PARTITION": part,
            "CUMUN": mun, "ddd_closed_urban": False, "district_id": district}


class PartitionFieldTests(unittest.TestCase):
    def test_island_quotas_and_floor_exemption_use_declared_partition(self):
        # Dos islas de la misma provincia: 2 distritos en C01 y 1 en C02 (exenta, bajo el suelo).
        rows = [_row("a", "07:A:M", "07", "07-C01", "A", 1), _row("b", "07:B:M", "07", "07-C01", "B", 2),
                _row("c", "07:C:M", "07", "07-C02", "C", 3)]
        with tempfile.TemporaryDirectory() as td:
            graph, geo = _write(Path(td), rows, [100, 100, 10])
            common = dict(expected_k=3, target_tolerance_ratio=0.12, population_floor_ratio=0.8,
                          population_cap_ratio=1.75, province_districts={"07-C01": 2, "07-C02": 1},
                          population_floor_exempt_partitions=("07-C02",), preserve_closed_urban=False,
                          require_contiguity=False)
            with self.assertRaises(BaselineValidationError) as raw:
                prepare_problem(graph, geo, StrategyContract(**common, partition_field="CPRO"), metric_crs="EPSG:3035")
            self.assertIn("province_count:07-C01", str(raw.exception))
            fixed = StrategyContract(**common, partition_field="DDD_PARTITION")
            problem = prepare_problem(graph, geo, fixed, metric_crs="EPSG:3035")
            self.assertEqual([], hard_constraint_violations(problem, problem.initial_assignment, fixed))

    def test_contract_reads_partition_field_and_municipal_exemptions(self):
        cfg = {"validation": {"expected_districts": 3, "population_floor_exempt_municipalities": ["30010"]},
               "modulos": {"modulo_04_generar_semillas": {"province_field": "DDD_PARTITION"}}}
        contract = contract_from_yaml(cfg)
        self.assertEqual("DDD_PARTITION", contract.partition_field)
        self.assertEqual(("30010",), contract.population_floor_exempt_municipalities)


class MunicipalExemptionTests(unittest.TestCase):
    def test_district_with_exempt_municipality_skips_floor(self):
        rows = [_row("a", "30:30001:M", "30", "30", "30001", 1), _row("b", "30:30010:M", "30", "30", "30010", 2)]
        with tempfile.TemporaryDirectory() as td:
            graph, geo = _write(Path(td), rows, [160, 40])
            common = dict(expected_k=2, target_tolerance_ratio=0.12, population_floor_ratio=0.8,
                          population_cap_ratio=1.75, province_districts={"30": 2}, preserve_closed_urban=False)
            with self.assertRaises(BaselineValidationError) as raw:
                prepare_problem(graph, geo, StrategyContract(**common), metric_crs="EPSG:3035")
            self.assertIn("population_floor:2", str(raw.exception))
            exempt = StrategyContract(**common, population_floor_exempt_municipalities=("30010",))
            problem = prepare_problem(graph, geo, exempt, metric_crs="EPSG:3035")
            self.assertEqual([], hard_constraint_violations(problem, problem.initial_assignment, exempt))


class AtomicGroupTests(unittest.TestCase):
    def _contract(self):
        return StrategyContract(expected_k=2, target_tolerance_ratio=0.12, population_floor_ratio=0.0,
                                population_cap_ratio=1.75, province_districts={"25": 2}, preserve_closed_urban=False)

    def test_declared_administrative_group_is_one_municipal_unit(self):
        rows = [_row("a", "25:25215|25234:M", "25", "25", "25215", 1),
                _row("b", "25:25215|25234:M", "25", "25", "25234", 1),
                _row("c", "25:25001:M", "25", "25", "25001", 2)]
        with tempfile.TemporaryDirectory() as td:
            graph, geo = _write(Path(td), rows, [50, 50, 100])
            problem = prepare_problem(graph, geo, self._contract(), metric_crs="EPSG:3035")
            self.assertEqual("25215|25234", problem.units["25:25215|25234:M"]["municipality"])

    def test_undeclared_cross_municipal_unit_is_still_rejected(self):
        rows = [_row("a", "25:25215:M", "25", "25", "25215", 1), _row("b", "25:25215:M", "25", "25", "25234", 1),
                _row("c", "25:25001:M", "25", "25", "25001", 2)]
        with tempfile.TemporaryDirectory() as td:
            graph, geo = _write(Path(td), rows, [50, 50, 100])
            with self.assertRaisesRegex(ValueError, "Unidad cruza municipios"):
                prepare_problem(graph, geo, self._contract(), metric_crs="EPSG:3035")


class CardinalityTests(unittest.TestCase):
    def test_one_unit_per_district_cannot_yield_a_portfolio(self):
        rows = [_row("a", "51:51001:A", "51", "51", "51001", 1), _row("b", "51:51001:B", "51", "51", "51001", 2)]
        contract = StrategyContract(expected_k=2, target_tolerance_ratio=0.12, population_floor_ratio=0.0,
                                    population_cap_ratio=1.75, province_districts={"51": 2},
                                    preserve_closed_urban=False, require_municipality_discipline=False)
        with tempfile.TemporaryDirectory() as td:
            graph, geo = _write(Path(td), rows, [100, 100])
            problem = prepare_problem(graph, geo, contract, metric_crs="EPSG:3035")
            ensemble_cardinality_check(problem, contract, 1)
            with self.assertRaisesRegex(BaselineValidationError, "ENSEMBLE_INFEASIBLE_AT_DECLARED_GRANULARITY"):
                ensemble_cardinality_check(problem, contract, 50)


class CanonicalSeedWiringTests(unittest.TestCase):
    def test_procedure_builds_repaired_canonical_seed_before_gerrychain(self):
        procedure = (ROOT / "procedimiento.sh").read_text(encoding="utf-8")
        self.assertIn("_semilla_canonica.geojson.zip", procedure)
        self.assertIn('--initial "$canonical_seed"', procedure)
        self.assertIn('"${initial_args[@]}"', procedure)
        self.assertIn("ENSEMBLE_INFEASIBLE_AT_DECLARED_GRANULARITY", procedure)
        # La semilla canónica se revalida con el mismo contrato antes de muestrear.
        self.assertLess(procedure.index('--initial "$canonical_seed" 2>&1'), procedure.index("/opt/ddd-gerrychain/bin/python ddd_core"))


if __name__ == "__main__":
    unittest.main()
