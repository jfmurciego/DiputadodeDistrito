from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import geopandas as gpd
import importlib.util
from shapely.geometry import MultiPolygon, Point, box

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ddd_core.m05_gerrychain_strategy import (
    StrategyConfig,
    StrategyContract,
    contract_from_yaml,
    resolve_paths,
    strategy_config_from_yaml,
    PreparedProblem,
    build_report,
    candidate_rank,
    geometric_shape_metrics,
    hard_constraint_violations,
    physical_geometry_diagnostics,
    prepare_problem,
    _run_seed,
)

GALICIA = Path(os.environ.get("DDD_GALICIA_M06_DIR", "/mnt/data/galicia_m06/cache"))
GRAPH = GALICIA / "galicia_2025_m03_grafo.json"
M04 = GALICIA / "galicia_2025_m04_semillas.geojson.zip"
ENGINE = ROOT / "ddd_core/m05_gerrychain_strategy.py"


class ContractTests(unittest.TestCase):
    def test_contract_reads_current_ddd_names(self):
        cfg = {
            "meta": {"territory_id": "x"},
            "validation": {
                "expected_districts": 3,
                "target_tolerance_ratio": 0.09,
                "population_floor_ratio": 0.80,
                "population_cap_ratio": 1.75,
                "require_graph_contiguity": True,
                "province_districts": {"1": 1, "2": 2},
            },
        }
        c = contract_from_yaml(cfg)
        self.assertEqual(c.expected_k, 3)
        self.assertTrue(c.require_contiguity)
        self.assertEqual(c.province_districts, {"01": 1, "02": 2})
        self.assertEqual(c.municipality_discipline_field, "CUMUN")
        cfg["partitioning"] = {
            "enabled": True,
            "strategy": "connected_internal_units",
            "partition_unit_field": "M04_PARTITION_UNIT",
        }
        cfg["modulos"] = {
            "modulo_02_construir_adyacencias": {
                "working_crs": "EPSG:3035",
                "min_shared_border_m": 1.0,
            },
            "modulo_05_optimizar_distritos": {
                "gerrychain": {"population_band": 0.005},
            },
        }
        c = contract_from_yaml(cfg)
        self.assertEqual(c.municipality_discipline_field, "M04_PARTITION_UNIT")
        s = strategy_config_from_yaml(cfg)
        self.assertEqual(s.proposal_epsilon, 0.09)
        self.assertEqual(s.comarca_surcharge, 0.0)
        self.assertEqual(s.population_band, 0.005)
        self.assertEqual(s.metric_crs, "EPSG:3035")
        self.assertEqual(s.min_shared_border_m, 1.0)

    def test_asturias_contract_uses_declared_internal_partition_unit(self):
        import yaml
        cfg = yaml.safe_load(
            (ROOT / "territorios/principado_de_asturias/config/principado_de_asturias_2025.yaml")
            .read_text(encoding="utf-8")
        ) or {}
        contract = contract_from_yaml(cfg)
        self.assertEqual(contract.municipality_discipline_field, "M04_PARTITION_UNIT")

    def test_strategy_config_default_comarca_is_neutral(self):
        self.assertEqual(StrategyConfig().comarca_surcharge, 0.0)
        self.assertEqual(strategy_config_from_yaml({}).comarca_surcharge, 0.0)

    def test_resolve_paths_honours_project_root(self):
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            params = repo / "territorios/x/config/x_2025.yaml"
            params.parent.mkdir(parents=True)
            cfg = {
                "meta": {"year": 2025, "run_name": "x_2025"},
                "io": {"project_root": {"path": "../../.."}},
                "modulos": {
                    "modulo_03_construir_grafo": {"out_graph_json": "territorios/x/.cache/g.json"},
                    "modulo_04_generar_semillas": {"out_geojson": "territorios/x/.cache/m04.zip"},
                    "modulo_05_optimizar_distritos": {
                        "in_graph_json": "territorios/x/.cache/g.json",
                        "in_geojson": "territorios/x/.cache/m04.zip",
                        "out_geojson": "territorios/x/.cache/m05.zip",
                        "out_report": "territorios/x/.cache/m05.json",
                    },
                },
            }
            params.write_text("meta: {}\n", encoding="utf-8")
            paths = resolve_paths(cfg, params, "r1")
            self.assertEqual(paths["graph"], repo / "territorios/x/.cache/g.json")

    def test_invalid_strategy_config_is_rejected(self):
        with self.assertRaises(ValueError):
            StrategyConfig(steps_per_seed=0).validate()
        with self.assertRaises(ValueError):
            StrategyConfig(proposal_epsilon=0).validate()

    def test_production_wiring_keeps_canonical_default_and_isolates_gerrychain(self):
        procedure = (ROOT / "procedimiento.sh").read_text(encoding="utf-8")
        dockerfile = (ROOT / "Dockerfile").read_text(encoding="utf-8")
        self.assertIn('m05.get("optimization_strategy") or "canonical"', procedure)
        self.assertIn("gerrychain_recom)", procedure)
        self.assertIn("/opt/ddd-gerrychain/bin/python ddd_core/m05_gerrychain_strategy.py", procedure)
        self.assertIn("PYTHONHASHSEED=0", procedure)
        self.assertIn("python -m venv /opt/ddd-gerrychain", dockerfile)
        self.assertIn("requirements-gerrychain-m05.lock", dockerfile)

    def test_business_profiles_map_to_expected_candidate_counts(self):
        procedure = (ROOT / "procedimiento.sh").read_text(encoding="utf-8")
        self.assertIn('"GerryChain"|gerrychain_recom) printf', procedure)
        self.assertIn('"GerryChain 25"|gerrychain_25)', procedure)
        self.assertIn('"GerryChain 50"|gerrychain_50)', procedure)
        self.assertIn("gerrychain_recom 1", procedure)
        self.assertIn("gerrychain_recom 25", procedure)
        self.assertIn("gerrychain_recom 50", procedure)
        self.assertIn('--seed-count "$candidate_count"', procedure)

    def test_gerrychain_failure_falls_back_to_canonical_without_aborting_generation(self):
        procedure = (ROOT / "procedimiento.sh").read_text(encoding="utf-8")
        self.assertIn("gerry_rc=${PIPESTATUS[0]}", procedure)
        self.assertIn("--validate-baseline-only", procedure)
        self.assertIn("baseline_rc=${PIPESTATUS[0]}", procedure)
        self.assertIn("baseline_rc != 0", procedure)
        self.assertIn("gerry_rc == 42", procedure)
        self.assertIn("no se permite fallback", procedure)
        self.assertIn("falló después de validar la entrada", procedure)
        self.assertIn("Canónico como fallback", procedure)
        self.assertIn("OPTIMIZATION_FALLBACK.json", procedure)
        self.assertIn("OPTIMIZATION_EXECUTION.json", procedure)
        self.assertIn("registrar_optimizacion", procedure)
        self.assertIn('"fallback_strategy":"canonical"', procedure)
        self.assertIn('"baseline_validated":True', procedure)
        self.assertIn('modulo_${n}_fallback_canonical.log', procedure)

    def test_invalid_baseline_has_reserved_non_fallback_exit_code(self):
        engine = ENGINE.read_text(encoding="utf-8")
        procedure = (ROOT / "procedimiento.sh").read_text(encoding="utf-8")
        self.assertIn("BASELINE_INVALID", engine)
        self.assertIn("SystemExit(42)", engine)
        self.assertIn("gerry_rc == 42", procedure)
        self.assertIn("exit 42", procedure)

    def test_invalid_baseline_preflight_exits_42_before_optimizer(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            geo = root / "m04.geojson"
            gdf = gpd.GeoDataFrame(
                {
                    "CUSEC_KEY": ["A"],
                    "ddd_unit_id": ["A"],
                    "CPRO": ["01"],
                    "CUMUN": ["m1"],
                    "ddd_closed_urban": [False],
                    "district_id": [1],
                },
                geometry=[box(0, 0, 100, 100)],
                crs="EPSG:3035",
            )
            geo.write_text(gdf.to_json(), encoding="utf-8")
            graph = root / "m03.json"
            graph.write_text(json.dumps({"nodes": [{"id": "A", "pop": 100}], "edges": []}), encoding="utf-8")
            completed = subprocess.run(
                [
                    sys.executable, str(ENGINE),
                    "--graph", str(graph), "--initial", str(geo),
                    "--output", str(root / "unused.zip"), "--report", str(root / "unused.json"),
                    "--expected-k", "2", "--validate-baseline-only",
                ],
                capture_output=True, text=True,
                env=dict(os.environ, PYTHONHASHSEED="0", PYTHONPATH=str(ROOT)),
            )
            self.assertEqual(completed.returncode, 42)
            self.assertIn("BASELINE_INVALID", completed.stderr)
            self.assertFalse((root / "unused.zip").exists())

    def test_unrelated_bridge_does_not_explain_physical_discontinuity(self):
        problem = PreparedProblem(
            sections=gpd.GeoDataFrame(),
            units={u: {"population": 1.0, "province": "01", "municipality": u, "closed_urban": False}
                   for u in ("A", "B", "C", "D")},
            edges=[("A", "B"), ("C", "D")],
            initial_assignment={u: 1 for u in ("A", "B", "C", "D")},
            frozen_districts={},
            target_population=4.0,
            unit_components={u: (f"{u}#0",) for u in ("A", "B", "C", "D")},
            component_edges=[("A#0", "B#0"), ("C#0", "D#0")],
            operational_edge_types={("A", "B"): ("declared_bridge",), ("C", "D"): ("geometric",)},
        )
        diagnostic = physical_geometry_diagnostics(problem, problem.initial_assignment)
        self.assertEqual(diagnostic["count"], 1)
        self.assertEqual(
            diagnostic["districts"][0]["classification"],
            "UNEXPLAINED_PHYSICAL_DISCONTINUITY",
        )
        self.assertEqual(diagnostic["districts"][0]["causal_topology_bridge_edges"], [])

    def test_multipart_section_cannot_create_new_geometric_bridge(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            center = gpd.GeoSeries([Point(-3.7, 41.6)], crs="EPSG:4326").to_crs("EPSG:3035").iloc[0]
            x0, y0 = center.x, center.y
            geometries = [
                box(x0, y0, x0 + 100, y0 + 100),
                MultiPolygon([
                    box(x0 + 100, y0, x0 + 200, y0 + 100),
                    box(x0 + 7100, y0, x0 + 7200, y0 + 100),
                ]),
                box(x0 + 7200, y0, x0 + 7300, y0 + 100),
                box(x0 + 7300, y0, x0 + 7400, y0 + 100),
                box(x0 + 7400, y0, x0 + 7500, y0 + 100),
            ]
            ids = ["A", "B", "C", "D", "E"]
            initial = [1, 2, 3, 3, 3]
            gdf = gpd.GeoDataFrame(
                {
                    "CUSEC_KEY": ids,
                    "ddd_unit_id": ids,
                    "CPRO": ["01"] * 5,
                    "CUMUN": ids,
                    "ddd_closed_urban": [False] * 5,
                    "district_id": initial,
                },
                geometry=geometries,
                crs="EPSG:3035",
            ).to_crs("EPSG:4326")
            geo = root / "m04.geojson"
            geo.write_text(gdf.to_json(), encoding="utf-8")
            graph = {
                "nodes": [{"id": section, "pop": 1.0} for section in ids],
                "edges": [
                    {"u": "A", "v": "B"},
                    {"u": "B", "v": "C"},
                    {"u": "C", "v": "D"},
                    {"u": "D", "v": "E"},
                ],
            }
            graph_path = root / "m03.json"
            graph_path.write_text(json.dumps(graph), encoding="utf-8")
            contract = StrategyContract(
                expected_k=3,
                target_tolerance_ratio=0.12,
                population_floor_ratio=0.0,
                population_cap_ratio=10.0,
                require_single_province=False,
                require_municipality_discipline=False,
                preserve_closed_urban=False,
            )
            problem = prepare_problem(
                graph_path,
                geo,
                contract,
                metric_crs="EPSG:3035",
                min_shared_border_m=1.0,
            )
            self.assertEqual(hard_constraint_violations(problem, problem.initial_assignment, contract), [])
            candidate = {"A": 1, "B": 1, "C": 1, "D": 2, "E": 3}
            violations = hard_constraint_violations(problem, candidate, contract)
            self.assertNotIn("geometric_contiguity:1", violations)
            diagnostic = physical_geometry_diagnostics(problem, candidate)
            row = next(r for r in diagnostic["districts"] if r["district_id"] == "1")
            self.assertEqual(row["classification"], "ATOMIC_MULTIPART")
            self.assertTrue(row["causal_atomic_multipart_edges"])
            self.assertEqual(diagnostic["semantics"], "diagnostic_only_operational_graph_is_authoritative")

    def test_municipality_discipline_uses_m04_declared_partition_unit(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            ids = ["A", "B", "C", "D", "E", "F"]
            gdf = gpd.GeoDataFrame(
                {
                    "CUSEC_KEY": ids,
                    "ddd_unit_id": ids,
                    "CPRO": ["33"] * 6,
                    "CUMUN": ["BIG", "BIG", "BIG", "S1", "S2", "S3"],
                    "M04_PARTITION_UNIT": ["BIG#P1", "BIG#P2", "BIG#P3", "S1", "S2", "S3"],
                    "ddd_closed_urban": [False] * 6,
                    "district_id": [1, 2, 3, 1, 2, 3],
                },
                geometry=[
                    box(0, 0, 1, 1), box(10, 0, 11, 1), box(20, 0, 21, 1),
                    box(1, 0, 2, 1), box(11, 0, 12, 1), box(21, 0, 22, 1),
                ],
                crs="EPSG:3035",
            )
            geo = root / "m04.geojson"
            geo.write_text(gdf.to_json(), encoding="utf-8")
            graph = {
                "nodes": [{"id": section, "pop": 100} for section in ids],
                "edges": [
                    {"u": "A", "v": "D", "edge_type": "geometric"},
                    {"u": "B", "v": "E", "edge_type": "geometric"},
                    {"u": "C", "v": "F", "edge_type": "geometric"},
                ],
            }
            graph_path = root / "m03.json"
            graph_path.write_text(json.dumps(graph), encoding="utf-8")

            raw_contract = StrategyContract(
                expected_k=3,
                target_tolerance_ratio=0.12,
                population_floor_ratio=0.0,
                population_cap_ratio=1.75,
                province_districts={"33": 3},
                municipality_discipline_field="CUMUN",
                preserve_closed_urban=False,
            )
            raw_problem = prepare_problem(graph_path, geo, raw_contract, metric_crs="EPSG:3035")
            raw_violations = hard_constraint_violations(
                raw_problem, raw_problem.initial_assignment, raw_contract
            )
            self.assertIn("municipality:BIG", raw_violations)
            self.assertIn("municipality_mixed:BIG", raw_violations)

            contractual = StrategyContract(
                expected_k=3,
                target_tolerance_ratio=0.12,
                population_floor_ratio=0.0,
                population_cap_ratio=1.75,
                province_districts={"33": 3},
                municipality_discipline_field="M04_PARTITION_UNIT",
                preserve_closed_urban=False,
            )
            problem = prepare_problem(graph_path, geo, contractual, metric_crs="EPSG:3035")
            self.assertEqual(
                hard_constraint_violations(problem, problem.initial_assignment, contractual),
                [],
            )
            self.assertEqual(
                {row["municipality"] for row in problem.units.values()},
                {"BIG#P1", "BIG#P2", "BIG#P3", "S1", "S2", "S3"},
            )

    def test_operational_graph_bridge_is_authoritative_even_without_physical_contact(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            gdf = gpd.GeoDataFrame(
                {
                    "CUSEC_KEY": ["A", "B"],
                    "ddd_unit_id": ["A", "B"],
                    "CPRO": ["01", "01"],
                    "CUMUN": ["m1", "m2"],
                    "ddd_closed_urban": [False, False],
                    "district_id": [1, 1],
                },
                geometry=[box(0, 0, 100, 100), box(1000, 0, 1100, 100)],
                crs="EPSG:3035",
            )
            geo = root / "m04.geojson"
            geo.write_text(gdf.to_json(), encoding="utf-8")
            graph = {
                "nodes": [{"id": "A", "pop": 50}, {"id": "B", "pop": 50}],
                "edges": [{
                    "u": "A", "v": "B",
                    "edge_type": "island_administrative_bridge",
                    "reason": "conexión territorial declarada",
                }],
            }
            graph_path = root / "m03.json"
            graph_path.write_text(json.dumps(graph), encoding="utf-8")
            contract = StrategyContract(
                expected_k=1,
                target_tolerance_ratio=0.12,
                population_floor_ratio=0.0,
                population_cap_ratio=10.0,
                require_single_province=False,
                require_municipality_discipline=False,
                preserve_closed_urban=False,
            )
            problem = prepare_problem(
                graph_path, geo, contract,
                metric_crs="EPSG:3035", min_shared_border_m=1.0,
            )
            self.assertEqual(hard_constraint_violations(problem, problem.initial_assignment, contract), [])
            diagnostic = physical_geometry_diagnostics(problem, problem.initial_assignment)
            self.assertEqual(diagnostic["count"], 1)
            self.assertEqual(diagnostic["districts"][0]["district_id"], "1")
            self.assertEqual(diagnostic["districts"][0]["classification"], "DECLARED_TOPOLOGY_BRIDGE")
            self.assertEqual(
                diagnostic["districts"][0]["declared_topology_bridge_types"],
                ["island_administrative_bridge"],
            )
            self.assertEqual(
                problem.operational_edge_types[("A", "B")],
                ("island_administrative_bridge",),
            )

    def test_shape_score_is_orientation_invariant_after_metric_reprojection(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            center = gpd.GeoSeries([Point(-3.7, 41.6)], crs="EPSG:4326").to_crs("EPSG:3035").iloc[0]
            contract = StrategyContract(
                expected_k=1,
                target_tolerance_ratio=0.12,
                population_floor_ratio=0.0,
                population_cap_ratio=10.0,
                require_single_province=False,
                require_municipality_discipline=False,
                preserve_closed_urban=False,
            )

            def score(name: str, width: float, height: float) -> float:
                x0 = center.x - width / 2
                y0 = center.y - height / 2
                gdf = gpd.GeoDataFrame(
                    {
                        "CUSEC_KEY": [name],
                        "ddd_unit_id": [name],
                        "CPRO": ["01"],
                        "CUMUN": [name],
                        "ddd_closed_urban": [False],
                        "district_id": [1],
                    },
                    geometry=[box(x0, y0, x0 + width, y0 + height)],
                    crs="EPSG:3035",
                ).to_crs("EPSG:4326")
                geo = root / f"{name}.geojson"
                geo.write_text(gdf.to_json(), encoding="utf-8")
                graph_path = root / f"{name}.json"
                graph_path.write_text(
                    json.dumps({"nodes": [{"id": name, "pop": 100.0}], "edges": []}),
                    encoding="utf-8",
                )
                problem = prepare_problem(
                    graph_path,
                    geo,
                    contract,
                    metric_crs="EPSG:3035",
                    min_shared_border_m=1.0,
                )
                return float(geometric_shape_metrics(problem, problem.initial_assignment)["polsby_popper_min"])

            east_west = score("EW", 3000.0, 1000.0)
            north_south = score("NS", 1000.0, 3000.0)
            self.assertAlmostEqual(east_west, north_south, places=6)

    def test_more_compact_map_wins_inside_same_population_band(self):
        units = {
            "u1": {"population": 50.2},
            "u2": {"population": 50.2},
            "u3": {"population": 50.1},
            "u4": {"population": 49.5},
        }
        edges = [("u1", "u2"), ("u1", "u3"), ("u2", "u4"), ("u3", "u4")]
        problem = PreparedProblem(
            sections=gpd.GeoDataFrame(),
            units=units,
            edges=edges,
            initial_assignment={"u1": 1, "u2": 1, "u3": 2, "u4": 2},
            frozen_districts={},
            target_population=100.0,
            unit_areas={unit: 1.0 for unit in units},
            unit_perimeters={unit: 4.0 for unit in units},
            shared_border_lengths={edge: 1.0 for edge in edges},
        )
        contract = StrategyContract(
            expected_k=2,
            target_tolerance_ratio=0.12,
            population_floor_ratio=0.0,
            population_cap_ratio=10.0,
            require_single_province=False,
            require_municipality_discipline=False,
            preserve_closed_urban=False,
        )
        compact = {"u1": 1, "u2": 1, "u3": 2, "u4": 2}
        dispersed = {"u1": 1, "u2": 2, "u3": 2, "u4": 1}
        compact_rank = candidate_rank(problem, compact, contract, compact, population_band=0.005)
        dispersed_rank = candidate_rank(problem, dispersed, contract, compact, population_band=0.005)
        self.assertEqual(compact_rank[1], dispersed_rank[1])
        self.assertGreater(compact_rank[3], dispersed_rank[3])
        self.assertLess(compact_rank[2], dispersed_rank[2])
        self.assertLess(compact_rank, dispersed_rank)

    def test_report_lists_frozen_geometric_exceptions(self):
        with tempfile.TemporaryDirectory() as td:
            td = Path(td)
            graph = td / "graph.json"
            initial = td / "initial.bin"
            output = td / "output.bin"
            graph.write_text("{}", encoding="utf-8")
            initial.write_bytes(b"initial")
            output.write_bytes(b"output")
            problem = PreparedProblem(
                sections=gpd.GeoDataFrame(),
                units={
                    "u1": {
                        "population": 100.0,
                        "province": "01",
                        "municipality": "m1",
                        "closed_urban": False,
                    }
                },
                edges=[],
                initial_assignment={"u1": 7},
                frozen_districts={},
                target_population=100.0,
                initial_geometric_exceptions={7: frozenset({"u1#0", "u1#1"})},
            )
            contract = StrategyContract(
                expected_k=1,
                target_tolerance_ratio=0.12,
                population_floor_ratio=0.0,
                population_cap_ratio=10.0,
                require_single_province=False,
                require_municipality_discipline=False,
                preserve_closed_urban=False,
            )
            strategy = StrategyConfig(seed_count=1, steps_per_seed=1)
            portfolio = {
                "runs": [{
                    "seed": 20260921,
                    "states_observed": 1,
                    "unique_states": 1,
                    "self_loops": 0,
                    "proposal_failures": 0,
                    "seconds": 0.0,
                    "rank": [0],
                    "assignment_hash": "x",
                    "assignment": {"u1": 7},
                }],
                "selected": {
                    "seed": 20260921,
                    "assignment_hash": "x",
                    "assignment": {"u1": 7},
                },
            }
            report = build_report(
                problem, contract, strategy, portfolio, graph, initial, output
            )
            self.assertEqual(
                report["search"]["frozen_geometric_exceptions"],
                {"count": 1, "district_ids": ["7"]},
            )

    def test_aragon_and_galicia_declare_gerrychain_parameters_explicitly(self):
        import yaml
        expected_common = {
            "population_band": 0.005,
            "metric_crs": "EPSG:3035",
            "min_shared_border_m": 1.0,
        }
        expected_surcharge = {
            "territorios/aragon/config/aragon_2025.yaml": 0.30,
            "territorios/galicia/config/galicia_2025.yaml": 0.0,
        }
        for relative, surcharge in expected_surcharge.items():
            cfg = yaml.safe_load((ROOT / relative).read_text(encoding="utf-8")) or {}
            gerry = cfg["modulos"]["modulo_05_optimizar_distritos"]["gerrychain"]
            for key, value in expected_common.items():
                self.assertIn(key, gerry, f"{relative}: falta {key}")
                self.assertEqual(gerry[key], value, f"{relative}: {key}")
            self.assertIn("comarca_surcharge", gerry, f"{relative}: falta comarca_surcharge")
            self.assertEqual(gerry["comarca_surcharge"], surcharge, f"{relative}: comarca_surcharge")
        galicia = yaml.safe_load(
            (ROOT / "territorios/galicia/config/galicia_2025.yaml").read_text(encoding="utf-8")
        ) or {}
        note = galicia["modulos"]["modulo_05_optimizar_distritos"]["gerrychain"].get("comarca_surcharge_note")
        self.assertIn("no tiene datos comarcales cargados", note)

    def test_positive_comarca_surcharge_requires_full_coverage_in_m01(self):
        import yaml
        offenders = []
        for params in sorted((ROOT / "territorios").glob("*/config/*_2025.yaml")):
            cfg = yaml.safe_load(params.read_text(encoding="utf-8")) or {}
            gerry = (
                ((cfg.get("modulos") or {}).get("modulo_05_optimizar_distritos") or {})
                .get("gerrychain")
                or {}
            )
            surcharge = float(gerry.get("comarca_surcharge", 0.0) or 0.0)
            if surcharge <= 0:
                continue
            comarcas = (((cfg.get("io") or {}).get("input") or {}).get("comarcas") or {})
            if comarcas.get("enabled") is not True or comarcas.get("require_full_coverage") is not True:
                offenders.append(str(params.relative_to(ROOT)))
        self.assertEqual(
            offenders,
            [],
            "Todo territorio con comarca_surcharge > 0 debe activar comarcas en M01 con cobertura completa.",
        )

    def test_02_and_00_expose_same_algorithm_selector(self):
        import yaml
        def load(path):
            data=yaml.safe_load(path.read_text(encoding="utf-8")) or {}
            return data.get("on") or data.get(True) or {}
        w02=load(ROOT/".github/workflows/produccion-distritos.yml")
        w00=load(ROOT/".github/workflows/ejecucion-completa-proyecto.yml")
        expected=["Canónico","GerryChain","GerryChain 25","GerryChain 50"]
        self.assertEqual(w02["workflow_dispatch"]["inputs"]["optimization_algorithm"]["options"],expected)
        self.assertEqual(w00["workflow_dispatch"]["inputs"]["optimization_algorithm"]["options"],expected)
        text00=(ROOT/".github/workflows/ejecucion-completa-proyecto.yml").read_text(encoding="utf-8")
        self.assertIn("optimization_algorithm: ${{ needs.planificar.outputs.optimization_algorithm }}",text00)


@unittest.skipUnless(importlib.util.find_spec("gerrychain"), "GerryChain no instalado")
class GerryChainRuntimeTests(unittest.TestCase):
    def test_declared_water_bridge_does_not_block_gerrychain_start(self):
        units = {
            u: {
                "unit_id": u, "population": 10.0, "province": "01",
                "municipality": u, "closed_urban": False, "comarca": None,
            }
            for u in ("A", "B", "C", "D")
        }
        problem = PreparedProblem(
            sections=gpd.GeoDataFrame(),
            units=units,
            edges=[("A", "B"), ("B", "C"), ("C", "D")],
            initial_assignment={"A": 1, "B": 1, "C": 2, "D": 2},
            frozen_districts={},
            target_population=20.0,
            operational_edge_types={
                ("A", "B"): ("water_bridge",),
                ("B", "C"): ("geometric",),
                ("C", "D"): ("geometric",),
            },
        )
        contract = StrategyContract(
            expected_k=2, target_tolerance_ratio=0.50,
            population_floor_ratio=0.0, population_cap_ratio=10.0,
            province_districts={"01": 2},
            require_municipality_discipline=False,
            preserve_closed_urban=False,
        )
        config = StrategyConfig(
            steps_per_seed=3, seed_base=200, seed_count=1,
            proposal_epsilon=0.50,
        )
        old_hash = os.environ.get("PYTHONHASHSEED")
        os.environ["PYTHONHASHSEED"] = "0"
        try:
            result = _run_seed(problem, contract, config, 201)
        finally:
            if old_hash is None:
                os.environ.pop("PYTHONHASHSEED", None)
            else:
                os.environ["PYTHONHASHSEED"] = old_hash
        self.assertEqual(result["states_observed"], 3)

    def test_recoverable_recom_failure_becomes_self_loop(self):
        units = {
            "u1": {"unit_id": "u1", "population": 10.0, "province": "01", "municipality": "m1", "closed_urban": True},
            "u2": {"unit_id": "u2", "population": 10.0, "province": "01", "municipality": "m2", "closed_urban": True},
        }
        problem = PreparedProblem(
            sections=gpd.GeoDataFrame(),
            units=units,
            edges=[("u1", "u2")],
            initial_assignment={"u1": 1, "u2": 2},
            frozen_districts={1: frozenset({"u1"}), 2: frozenset({"u2"})},
            target_population=10.0,
        )
        contract = StrategyContract(
            expected_k=2, target_tolerance_ratio=0.12,
            population_floor_ratio=0.80, population_cap_ratio=1.75,
            province_districts={"01": 2}, require_municipality_discipline=False,
        )
        config = StrategyConfig(steps_per_seed=4, seed_base=100, seed_count=1, proposal_epsilon=0.12)
        old = os.environ.get("PYTHONHASHSEED")
        os.environ["PYTHONHASHSEED"] = "0"
        try:
            result = _run_seed(problem, contract, config, 101)
        finally:
            if old is None:
                os.environ.pop("PYTHONHASHSEED", None)
            else:
                os.environ["PYTHONHASHSEED"] = old
        self.assertEqual(result["states_observed"], 4)
        self.assertGreaterEqual(result["proposal_failures"], 1)
        self.assertEqual(result["assignment_hash"], __import__("ddd_core.m05_gerrychain_strategy", fromlist=["_assignment_hash"])._assignment_hash(problem.initial_assignment))


@unittest.skipUnless(GRAPH.is_file() and M04.is_file(), "Checkpoint M03/M04 de Galicia no disponible")
class GaliciaEndToEndTests(unittest.TestCase):
    contract = StrategyContract(
        expected_k=75,
        target_tolerance_ratio=0.12,
        population_floor_ratio=0.80,
        population_cap_ratio=1.75,
        province_districts={"15": 31, "27": 9, "32": 9, "36": 26},
    )

    def invoke(self, out: Path, report: Path, steps: int = 250):
        env = dict(os.environ, PYTHONHASHSEED="0", PYTHONPATH=str(ROOT))
        return subprocess.run(
            [
                sys.executable, str(ENGINE),
                "--graph", str(GRAPH), "--initial", str(M04),
                "--output", str(out), "--report", str(report),
                "--expected-k", "75", "--province-quotas", "15=31,27=9,32=9,36=26",
                "--steps-per-seed", str(steps), "--seed-base", "20260920", "--seed-count", "1",
                "--proposal-epsilon", "0.12", "--max-bipartition-attempts", "500",
            ],
            check=True, capture_output=True, text=True, env=env,
        )

    def test_reproducible_assignment_and_bytes(self):
        with tempfile.TemporaryDirectory() as td:
            td = Path(td)
            out = td / "m05.zip"
            report = td / "m05.json"
            self.invoke(out, report)
            first = json.loads(report.read_text(encoding="utf-8"))
            first_bytes = out.read_bytes()
            self.invoke(out, report)
            second = json.loads(report.read_text(encoding="utf-8"))
            self.assertEqual(first["search"]["selected_assignment_hash"], second["search"]["selected_assignment_hash"])
            self.assertEqual(first["objective_final"], second["objective_final"])
            self.assertEqual(hashlib.sha256(first_bytes).hexdigest(), hashlib.sha256(out.read_bytes()).hexdigest())

    def test_output_is_m06_consumable(self):
        with tempfile.TemporaryDirectory() as td:
            td = Path(td)
            out = td / "m05.zip"
            report = td / "m05.json"
            self.invoke(out, report, steps=500)
            rep = json.loads(report.read_text(encoding="utf-8"))
            g = gpd.read_file("zip://" + str(out))
            g["CUSEC_KEY"] = g["CUSEC_KEY"].astype(str)
            g["CPRO"] = g["CPRO"].astype(str).str.zfill(2)
            g["district_id"] = g["district_id"].astype(int)
            self.assertEqual(len(g), 2134)
            self.assertEqual(g["CUSEC_KEY"].nunique(), 2134)
            self.assertEqual(int(g["POP_2025"].sum()), 2714741)
            self.assertEqual(g["district_id"].nunique(), 75)
            self.assertEqual(int(g.groupby("district_id")["CPRO"].nunique().max()), 1)
            self.assertEqual(
                g.groupby("district_id")["CPRO"].first().value_counts().to_dict(),
                {"15": 31, "36": 26, "27": 9, "32": 9},
            )
            target = g["POP_2025"].sum() / 75
            pops = g.groupby("district_id")["POP_2025"].sum()
            self.assertTrue((pops >= target * 0.80 - 1e-9).all())
            self.assertTrue((pops <= target * 1.75 + 1e-9).all())
            self.assertEqual(rep["hard_constraints_after"], [])
            self.assertEqual(rep["districts_below_floor"], 0)
            self.assertEqual(rep["districts_above_cap"], 0)
            dissolved = g[["district_id", "POP_2025", "geometry"]].dissolve(
                by="district_id", aggfunc={"POP_2025": "sum"}, as_index=False
            )
            self.assertEqual(len(dissolved), 75)
            self.assertEqual(int(dissolved["POP_2025"].sum()), 2714741)

    def test_runtime_refuses_unpinned_hash_seed(self):
        with tempfile.TemporaryDirectory() as td:
            td = Path(td)
            env = dict(os.environ, PYTHONPATH=str(ROOT))
            env.pop("PYTHONHASHSEED", None)
            completed = subprocess.run(
                [sys.executable, str(ENGINE), "--graph", str(GRAPH), "--initial", str(M04),
                 "--output", str(td / "o.zip"), "--report", str(td / "r.json"),
                 "--expected-k", "75", "--province-quotas", "15=31,27=9,32=9,36=26",
                 "--steps-per-seed", "2", "--seed-count", "1"],
                capture_output=True, text=True, env=env,
            )
            self.assertNotEqual(completed.returncode, 0)
            self.assertIn("PYTHONHASHSEED=0", completed.stderr)


if __name__ == "__main__":
    unittest.main()
