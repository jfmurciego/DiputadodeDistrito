from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import yaml
from shapely.geometry import box

from ddd_core.config import load_params_yaml
from herramientas._resolver_ejecucion_completa_core import _contract_generation_binding
from herramientas.catalogo_preparacion import rows_for
from herramientas.compatibilidad_poblacion_seccionado import reconcile_population_sectioning
from herramientas.materializar_evidencia_pre_m04 import _enable_contract_after_pre_m04
from herramientas.promover_catalogo_tras_preparacion import _set_catalog_state
from herramientas.resolver_ejecucion_completa import generation_enablement


ROOT = Path(__file__).resolve().parents[1]
MATRIX = ROOT / "configuracion/preparacion_legislatura_vigente.yaml"


def source_baseline(population_year: int = 2023, section_year: int = 2023) -> dict:
    return {
        "schema": "ddd.source-baseline/1.0",
        "edition": "2025",
        "population_year": population_year,
        "section_year": section_year,
        "population_total": 100,
        "target_section_count": 2,
        "package_sha256": "b" * 64,
        "compatibility_report_sha256": "9" * 64,
        "compatibility_identity_sha256": "c" * 64,
    }


def contract(population_year: int = 2023, section_year: int = 2023) -> dict:
    baseline = source_baseline(population_year, section_year)
    return {
        "meta": {
            "territory_id": "demo",
            "year": 2025,
            "source_population_year": population_year,
            "source_section_year": section_year,
            "contract_level": "production_m01_m06",
            "production_authorization": "AUTHORIZED",
            "status": "source_prepared_pending_pre_m04",
        },
        "territory_contract": {
            "k_districts": 2,
            "population_floor_ratio": 0.8,
            "population_cap_ratio": 1.2,
            "target_tolerance_ratio": 0.1,
            "oversized_municipality_rule": "split",
            "municipality_atomicity_limit_ratio": 1.0,
            "status": "source_prepared_pending_pre_m04",
        },
        "modulos": {
            "modulo_01_preparar_base_territorial": {
                "out_geojson": "m01.geojson.zip",
            },
            "modulo_02_construir_adyacencias": {
                "predicate": "contact",
                "working_crs": "EPSG:3035",
                "min_shared_border_m": 1.0,
                "max_precision_overlap_area_m2": 1.0,
                "buffer_m": 0.0,
                "simplify_m": 0.0,
                "topology_bridges": [],
            },
            "modulo_03_construir_grafo": {
                "out_graph_json": "m03.json",
                "pop_field": "POP_{population_year}",
            },
            "modulo_04_generar_semillas": {
                "in_graph_json": "m03.json",
                "in_geojson": "m01.geojson.zip",
                "out_geojson": "m04.geojson.zip",
                "municipality_field": "CUMUN",
                "k_districts": 2,
                "pop_field": "POP_{population_year}",
            },
            "modulo_05_optimizar_distritos": {
                "in_graph_json": "m03.json",
                "in_geojson": "m04.geojson.zip",
                "out_geojson": "m05.geojson.zip",
                "municipality_field": "CUMUN",
                "pop_field": "POP_{population_year}",
            },
            "modulo_06_consolidar_distritos": {
                "in_geojson": "m05.geojson.zip",
                "municipality_field": "CUMUN",
                "expected_districts": 2,
                "pop_field": "POP_{population_year}",
            },
        },
        "validation": {
            "expected_districts": 2,
            "require_graph_contiguity": True,
            "require_municipality_discipline": True,
            "municipality_field": "CUMUN",
            "source_baseline": baseline,
        },
        "generation_state": {
            "source_prepared": True,
            "generation_enabled": False,
            "package_sha256": baseline["package_sha256"],
            "compatibility_identity_sha256": baseline["compatibility_identity_sha256"],
        },
    }


def preparation_evidence(population_year: int = 2023, section_year: int = 2023) -> dict:
    return {
        "run_id": 7,
        "artifact_name": "ddd-source-package-demo-2025-7",
        "artifact_sha256": "a" * 64,
        "package_sha256": "b" * 64,
        "compatibility_identity_sha256": "c" * 64,
        "population_year": population_year,
        "section_year": section_year,
        "source_commit": "d" * 40,
    }


class TemporalSourcePreflightContractTests(unittest.TestCase):
    def test_current_matrix_has_19_codauto_ordered_temporal_combinations(self):
        matrix = yaml.safe_load(MATRIX.read_text(encoding="utf-8"))
        observed = [
            (
                row["territory_id"],
                int(row["territorial"]["population_selected_year"]),
                int(row["territorial"]["section_selected_year"]),
            )
            for row in matrix["territories"]
        ]
        expected = [
            ("andalucia", 2025, 2026),
            ("aragon", 2025, 2026),
            ("principado_de_asturias", 2023, 2023),
            ("illes_balears", 2023, 2023),
            ("canarias", 2023, 2023),
            ("cantabria", 2023, 2023),
            ("castilla_y_leon", 2025, 2026),
            ("castilla_la_mancha", 2023, 2023),
            ("cataluna", 2024, 2024),
            ("comunidad_valenciana", 2023, 2023),
            ("extremadura", 2025, 2025),
            ("galicia", 2024, 2024),
            ("madrid", 2023, 2023),
            ("region_de_murcia", 2023, 2023),
            ("comunidad_foral_de_navarra", 2023, 2023),
            ("pais_vasco", 2024, 2024),
            ("la_rioja", 2023, 2023),
            ("ceuta", 2023, 2023),
            ("melilla", 2023, 2023),
        ]
        self.assertEqual(observed, expected)
        self.assertEqual(sum(pair[1:] == (2025, 2025) for pair in observed), 1)

    def test_config_separates_edition_population_and_section_years(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            params = root / "params.yaml"
            params.write_text(
                yaml.safe_dump({
                    "meta": {
                        "year": 2025,
                        "source_population_year": 2023,
                        "source_section_year": 2024,
                    },
                    "io": {
                        "input": {
                            "seccionado": {"path": "inputs/seccionado_{section_year}.zip"},
                            "population_cip": {"paths": ["inputs/poblacion_{population_year}.zip"]},
                        }
                    },
                }),
                encoding="utf-8",
            )
            loaded = load_params_yaml(str(params))
            self.assertEqual(loaded["meta"]["year"], 2025)
            self.assertEqual(loaded["meta"]["source_population_year"], 2023)
            self.assertEqual(loaded["meta"]["source_section_year"], 2024)
            self.assertTrue(loaded["io"]["input"]["seccionado"]["path"].endswith("seccionado_2024.zip"))
            self.assertTrue(loaded["io"]["input"]["population_cip"]["paths"][0].endswith("poblacion_2023.zip"))

            no_edition = root / "no-edition.yaml"
            no_edition.write_text("meta: {}\nio: {}\n", encoding="utf-8")
            generic = load_params_yaml(str(no_edition))
            self.assertNotIn("year", generic["meta"])

    def test_population_and_geometry_invalidity_are_structured_blocks(self):
        geom = box(0, 0, 1, 1)
        missing = reconcile_population_sectioning(
            territory_id="demo",
            edition="2025",
            population_year=2023,
            section_year=2023,
            population_rows=[("0100101001", None)],
            target_geometry_rows=[("0100101001", geom)],
            origin_geometry_rows=None,
        )
        self.assertEqual(missing["decision"], "BLOCKED")
        self.assertIn("POPULATION_VALUE_MISSING", missing["causes"])

        negative = reconcile_population_sectioning(
            territory_id="demo",
            edition="2025",
            population_year=2023,
            section_year=2023,
            population_rows=[("0100101001", -1)],
            target_geometry_rows=[("0100101001", geom)],
            origin_geometry_rows=None,
        )
        self.assertEqual(negative["decision"], "BLOCKED")
        self.assertIn("NEGATIVE_POPULATION", negative["causes"])

        invalid_geometry = reconcile_population_sectioning(
            territory_id="demo",
            edition="2025",
            population_year=2023,
            section_year=2023,
            population_rows=[("0100101001", 10)],
            target_geometry_rows=[("0100101001", None)],
            origin_geometry_rows=None,
        )
        self.assertEqual(invalid_geometry["decision"], "BLOCKED")
        self.assertIn("INVALID_TARGET_GEOMETRY", invalid_geometry["causes"])

    def test_historical_flags_do_not_enable_a_source_without_pre_m04_evidence(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            cfg = contract()
            cfg["meta"]["status"] = "generation_ready"
            cfg["territory_contract"]["status"] = "generation_ready"
            path = root / "contract.yaml"
            path.write_text(yaml.safe_dump(cfg, sort_keys=False), encoding="utf-8")
            gate = generation_enablement(
                root_dir=root,
                contract_path="contract.yaml",
                territory_id="demo",
                certified_product_ready=False,
                first_generation_evidence=None,
                preparation_evidence=preparation_evidence(),
                require_source=True,
            )
            self.assertFalse(gate["allowed"])
            self.assertEqual(gate["capability"], "CAP_PRE_M04_EVIDENCE")

    def test_pre_m04_gate_is_bound_to_exact_package_compatibility_and_years(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            cfg = contract()
            path = root / "contract.yaml"
            path.write_text(yaml.safe_dump(cfg, sort_keys=False), encoding="utf-8")
            prep = preparation_evidence()
            implementation = {"synthetic": "binding"}
            evidence = {
                "schema": "ddd.catalog-evidence/1.0",
                "kind": "generation_preflight",
                "territory_id": "demo",
                "edition": "2025",
                "run_id": 7,
                "source_commit": "e" * 40,
                "artifact_name": "ddd-state-7-M03U",
                "artifact_sha256": "1" * 64,
                "decision": "READY_FOR_FIRST_GENERATION",
                "stage": "M03U",
                "source": {
                    "artifact_name": prep["artifact_name"],
                    "artifact_sha256": prep["artifact_sha256"],
                    "package_sha256": prep["package_sha256"],
                    "compatibility_identity_sha256": prep["compatibility_identity_sha256"],
                    "population_year": prep["population_year"],
                    "section_year": prep["section_year"],
                },
                "implementation": implementation,
                "adjacency": {
                    "predicate": "contact",
                    "working_crs": "EPSG:3035",
                    "min_shared_border_m": 1.0,
                    "max_precision_overlap_area_m2": 1.0,
                    "buffer_m": 0.0,
                    "simplify_m": 0.0,
                    "topology_bridges": [],
                },
                "graph": {
                    "artifact_name": "ddd-state-7-M03",
                    "artifact_sha256": "2" * 64,
                    "nodes": 2,
                    "population": 100,
                    "isolated": 0,
                    "global_components": 1,
                    "province_disconnected": 0,
                    "municipality_disconnected": 0,
                },
                "partitioning": {
                    "job_artifact_name": "ddd-internal-units-7",
                    "job_artifact_sha256": "3" * 64,
                    "status": "NOOP",
                    "strategy": None,
                    "contract_output_geojson": "m01.geojson.zip",
                    "resolved_output_geojson": "m01.geojson.zip",
                },
                "contract_binding": _contract_generation_binding(cfg),
            }
            with mock.patch(
                "herramientas._resolver_ejecucion_completa_core._pre_m04_implementation_binding",
                return_value=implementation,
            ):
                gate = generation_enablement(
                    root_dir=root,
                    contract_path="contract.yaml",
                    territory_id="demo",
                    first_generation_evidence=evidence,
                    preparation_evidence=prep,
                    require_source=True,
                )
                self.assertEqual(gate, {"allowed": True, "route": "validated_pre_m04_topology"})

                altered = json.loads(json.dumps(evidence))
                altered["source"]["package_sha256"] = "4" * 64
                blocked = generation_enablement(
                    root_dir=root,
                    contract_path="contract.yaml",
                    territory_id="demo",
                    first_generation_evidence=altered,
                    preparation_evidence=prep,
                    require_source=True,
                )
                self.assertFalse(blocked["allowed"])
                self.assertEqual(blocked["capability"], "CAP_PRE_M04_EVIDENCE")

    def test_source_promotion_preserves_previous_product_and_disables_generation(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            catalog = root / "catalog.yaml"
            catalog.write_text(
                yaml.safe_dump({
                    "territories": [{
                        "territory_id": "demo",
                        "name": "Demo",
                        "editions": {"2025": {
                            "territorial_sources_prepared": True,
                            "territorial_contract_complete": True,
                            "territorial_product_available": True,
                            "territorial_certification": "PASS",
                            "production_authorization": "AUTHORIZED",
                            "evidence": {
                                "territorial_product": "product.json",
                                "generation_preflight": "old-preflight.json",
                            },
                        }},
                    }],
                }, sort_keys=False),
                encoding="utf-8",
            )
            _set_catalog_state(
                catalog,
                territory_id="demo",
                edition="2025",
                source_declaration="sources.yaml",
                contract_complete=True,
                run_id=9,
                artifact_name="ddd-source-package-demo-2025-9",
                artifact_sha256="a" * 64,
                package_sha256="b" * 64,
                compatibility_report_sha256="9" * 64,
                compatibility_identity_sha256="c" * 64,
                compatibility_report_member="compatibilidad_poblacion_seccionado.json",
                population_year=2023,
                section_year=2023,
            )
            state = yaml.safe_load(catalog.read_text(encoding="utf-8"))["territories"][0]["editions"]["2025"]
            self.assertTrue(state["territorial_product_available"])
            self.assertEqual(state["territorial_certification"], "PASS")
            self.assertFalse(state["generation_enabled"])
            self.assertEqual(state["evidence"]["territorial_product"], "product.json")
            self.assertNotIn("generation_preflight", state["evidence"])

    def test_generation_state_changes_only_after_matching_pre_m04(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            cfg = contract()
            path = root / "contract.yaml"
            path.write_text(yaml.safe_dump(cfg, sort_keys=False), encoding="utf-8")
            evidence = {
                "run_id": 7,
                "source_commit": "e" * 40,
                "artifact_sha256": "1" * 64,
                "source": {
                    "package_sha256": "4" * 64,
                    "compatibility_identity_sha256": "c" * 64,
                },
            }
            with self.assertRaisesRegex(ValueError, "SOURCE_MISMATCH"):
                _enable_contract_after_pre_m04(
                    root_dir=root,
                    contract_path="contract.yaml",
                    evidence=evidence,
                )
            unchanged = yaml.safe_load(path.read_text(encoding="utf-8"))
            self.assertFalse(unchanged["generation_state"]["generation_enabled"])

            evidence["source"]["package_sha256"] = "b" * 64
            _enable_contract_after_pre_m04(
                root_dir=root,
                contract_path="contract.yaml",
                evidence=evidence,
            )
            enabled = yaml.safe_load(path.read_text(encoding="utf-8"))
            self.assertTrue(enabled["generation_state"]["generation_enabled"])
            self.assertEqual(enabled["meta"]["status"], "generation_ready")

    def test_workflows_bind_preflight_to_promotion_sha_and_explicit_years(self):
        preparation = (ROOT / ".github/workflows/preparacion-fuentes.yml").read_text(encoding="utf-8")
        reusable = (ROOT / ".github/workflows/_reutilizable-generacion-territorial.yml").read_text(encoding="utf-8")
        producer = (ROOT / ".github/workflows/producir-territorio-por-contrato.yml").read_text(encoding="utf-8")
        production = (ROOT / ".github/workflows/produccion-distritos.yml").read_text(encoding="utf-8")
        resolver = (ROOT / "herramientas/resolver_ejecucion_completa.py").read_text(encoding="utf-8")

        self.assertIn("promotion_sha", preparation)
        self.assertIn("source_ref: ${{ needs.registrar.outputs.promotion_sha }}", preparation)
        self.assertNotIn('legacy_year="$EDITION"', preparation)
        for body in (reusable, producer, production):
            self.assertIn("--population-year", body)
            self.assertIn("--section-year", body)
        self.assertNotIn("declared_generation_ready", resolver)
        self.assertNotIn("linked_internal_partitioning", resolver)
        self.assertIn('"compatibility_identity_sha256": source.get("compatibility_identity_sha256")', production)
        self.assertIn('"population_year": source.get("population_year")', production)
        self.assertIn('"section_year": source.get("section_year")', production)



    def test_recalculation_and_historical_product_do_not_bypass_pre_m04(self):
        contract = {
            "meta": {
                "territory_id": "demo",
                "contract_level": "production_m01_m06",
                "production_authorization": "AUTHORIZED",
            },
            "territory_contract": {
                "k_districts": 1,
                "population_floor_ratio": 0.8,
                "population_cap_ratio": 1.75,
                "target_tolerance_ratio": 0.12,
                "oversized_municipality_rule": "split_only_above_hard_cap",
                "municipality_atomicity_limit_ratio": 1.75,
            },
            "modulos": {
                "modulo_01_preparar_base_territorial": {"out_geojson": "m01.zip"},
                "modulo_02_construir_adyacencias": {
                    "predicate": "contact", "working_crs": "EPSG:3035",
                    "min_shared_border_m": 1.0, "max_precision_overlap_area_m2": 1.0,
                    "buffer_m": 0.0, "simplify_m": 0.0, "topology_bridges": [],
                },
                "modulo_03_construir_grafo": {"out_graph_json": "m03.json"},
                "modulo_04_generar_semillas": {
                    "in_graph_json": "m03.json", "in_geojson": "m01.zip",
                    "out_geojson": "m04.zip", "municipality_field": "CUMUN",
                    "k_districts": 1,
                },
                "modulo_05_optimizar_distritos": {
                    "in_graph_json": "m03.json", "in_geojson": "m04.zip",
                    "out_geojson": "m05.zip", "municipality_field": "CUMUN",
                },
                "modulo_06_consolidar_distritos": {
                    "in_geojson": "m05.zip", "municipality_field": "CUMUN",
                    "expected_districts": 1,
                },
            },
            "validation": {
                "expected_districts": 1,
                "municipality_field": "CUMUN",
                "require_graph_contiguity": True,
                "require_municipality_discipline": True,
            },
        }
        prep = {
            "run_id": 1,
            "artifact_name": "ddd-source-package-demo-2025-1",
            "artifact_sha256": "a" * 64,
            "package_sha256": "b" * 64,
            "compatibility_identity_sha256": "c" * 64,
            "population_year": 2023,
            "section_year": 2023,
        }
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            path = root / "contract.yaml"
            path.write_text(yaml.safe_dump(contract, sort_keys=False), encoding="utf-8")
            for kwargs in (
                {"source_recalculation_planned": True},
                {"certified_product_ready": True},
            ):
                with self.subTest(kwargs=kwargs):
                    gate = generation_enablement(
                        root_dir=root,
                        contract_path="contract.yaml",
                        territory_id="demo",
                        preparation_evidence=prep,
                        require_source=True,
                        **kwargs,
                    )
                    self.assertFalse(gate["allowed"])
                    self.assertEqual(gate["capability"], "CAP_PRE_M04_EVIDENCE")

    def test_catalog_generation_requires_enabled_preflight_or_certified_product(self):
        with tempfile.TemporaryDirectory() as td:
            catalog = Path(td) / "catalog.yaml"
            base_state = {
                "territory_declared": True,
                "preparation_status": "READY",
                "contract_path": "contract.yaml",
                "territorial_source_declaration": "sources.yaml",
                "electoral_source_declaration": None,
                "territorial_sources_prepared": True,
                "territorial_contract_complete": True,
                "territorial_product_available": False,
                "electoral_source_prepared": False,
                "electoral_product_available": False,
                "territorial_certification": "NOT_CERTIFIED",
                "production_authorization": "AUTHORIZED",
                "last_valid_checkpoint": None,
                "generation_enabled": False,
            }
            catalog.write_text(
                yaml.safe_dump({
                    "schema": "ddd-preparation-catalog/1.1",
                    "default_edition": "2025",
                    "territories": [{
                        "territory_id": "demo",
                        "name": "Demo",
                        "editions": {"2025": base_state},
                    }],
                }, sort_keys=False),
                encoding="utf-8",
            )
            self.assertEqual(rows_for("generation", catalog), [])

            data = yaml.safe_load(catalog.read_text(encoding="utf-8"))
            data["territories"][0]["editions"]["2025"]["generation_enabled"] = True
            catalog.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
            self.assertEqual([row["territory_id"] for row in rows_for("generation", catalog)], ["demo"])

            data["territories"][0]["editions"]["2025"]["generation_enabled"] = False
            data["territories"][0]["editions"]["2025"]["territorial_product_available"] = True
            catalog.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
            self.assertEqual([row["territory_id"] for row in rows_for("generation", catalog)], ["demo"])


if __name__ == "__main__":
    unittest.main()
