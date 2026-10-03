from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path

import yaml

from herramientas.materializar_contrato_generacion import _apply_source_contract
from herramientas.preparar_unidades_internas import build_command

ROOT = Path(__file__).resolve().parents[1]
M01_PATH = ROOT / "modulos/01_preparar_base_territorial.py"


def load_m01():
    spec = importlib.util.spec_from_file_location("ddd_m01_runtime_contract", M01_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class ResolvedSourceContractConsumerTests(unittest.TestCase):
    def resolved_contract(self) -> dict:
        return {
            "schema": "ddd.resolved-source-contract/1.0",
            "contract_sha256": "a" * 64,
            "territory": {
                "territory_id": "demo",
                "territory_name": "Demo",
                "project_edition": "2025",
            },
            "temporal": {
                "population_year": 2019,
                "section_year": 2021,
            },
            "sources": {
                "population": {
                    "schema": "ddd.resolved-source-binding/1.0",
                    "source_id": "demo-pop",
                    "role": "population",
                    "path": "inputs/weird_population.pkg",
                    "artifact": {
                        "path": "inputs/weird_population.pkg",
                        "sha256": "b" * 64,
                        "bytes": 10,
                    },
                    "container": "zip",
                    "materialized_format": "csv",
                    "archive_member": "population.dat",
                    "encoding": "utf-8",
                    "delimiter": "|",
                    "fields": {
                        "section_id": "voting_zone_code",
                        "population": "inhabitants_xyz",
                        "year": "obs_year",
                        "sex": "sex_total",
                        "age": "age_total",
                    },
                    "filters": {
                        "year_value": 2019,
                        "sex_total_values": ["ALL"],
                        "age_total_values": ["ALL"],
                    },
                },
                "sectioning": {
                    "schema": "ddd.resolved-source-binding/1.0",
                    "source_id": "demo-geo",
                    "role": "target_sectioning",
                    "path": "inputs/boundaries.bundle",
                    "artifact": {
                        "path": "inputs/boundaries.bundle",
                        "sha256": "c" * 64,
                        "bytes": 10,
                    },
                    "materialized_format": "shapefile",
                    "layer": "section_polygons",
                    "fields": {
                        "section_id": "ZONA_ID",
                        "territorial_filter": "PROV_CODE",
                    },
                },
            },
            "runtime": {
                "section_id_field": "voting_zone_code_normalized",
                "population_field": "population_runtime",
                "province_field": "PROV_CODE",
                "municipality_field": "ADM2_CODE",
            },
            "transformations": [],
        }

    def source_inputs(self) -> list[dict]:
        return [
            {
                "source_id": "demo-pop",
                "role": "population",
                "path": "inputs/weird_population.pkg",
                "sha256": "b" * 64,
            },
            {
                "source_id": "demo-geo",
                "role": "target_sectioning",
                "path": "inputs/boundaries.bundle",
                "sha256": "c" * 64,
            },
        ]

    def test_materializer_propagates_physical_and_runtime_bindings(self):
        cfg = {
            "meta": {"year": 2025},
            "io": {"input": {"seccionado": {}, "population_cip": {}}},
            "modulos": {
                "modulo_02_construir_adyacencias": {"id_field": "LEGACY"},
                "modulo_03_construir_grafo": {"id_field": "LEGACY", "pop_field": "POP_2025"},
                "modulo_04_generar_semillas": {"id_field": "LEGACY", "pop_field": "POP_2025", "province_field": "CPRO"},
                "modulo_05_optimizar_distritos": {"id_field": "LEGACY", "pop_field": "POP_2025", "province_field": "CPRO"},
                "modulo_06_consolidar_distritos": {"id_field": "LEGACY", "pop_field": "POP_2025", "province_field": "CPRO"},
            },
            "partitioning": {"population_field": "POP_{year}"},
            "validation": {},
        }
        _apply_source_contract(
            cfg,
            population_year=2019,
            section_year=2021,
            baseline={
                "package_sha256": "d" * 64,
                "compatibility_identity_sha256": "e" * 64,
            },
            source_inputs=self.source_inputs(),
            resolved_contract=self.resolved_contract(),
        )
        self.assertEqual(cfg["io"]["input"]["population_cip"]["paths"], ["inputs/weird_population.pkg"])
        self.assertEqual(cfg["io"]["input"]["population_cip"]["section_key_col"], "voting_zone_code")
        self.assertEqual(cfg["io"]["input"]["population_cip"]["pop_col"], "inhabitants_xyz")
        self.assertEqual(cfg["io"]["input"]["seccionado"]["path"], "inputs/boundaries.bundle")
        self.assertEqual(cfg["io"]["input"]["seccionado"]["section_key_col"], "ZONA_ID")
        self.assertEqual(cfg["modulos"]["modulo_03_construir_grafo"]["id_field"], "voting_zone_code_normalized")
        self.assertEqual(cfg["modulos"]["modulo_03_construir_grafo"]["pop_field"], "population_runtime")
        self.assertEqual(cfg["partitioning"]["population_field"], "population_runtime")

    def test_m01_outputs_are_contract_owned(self):
        module = load_m01()
        cfg = {"resolved_source_contract": {"runtime": self.resolved_contract()["runtime"]}}
        self.assertEqual(
            module.resolve_runtime_fields(cfg, 2019),
            ("voting_zone_code_normalized", "population_runtime"),
        )

    def test_internal_units_prefers_runtime_binding_over_legacy_year(self):
        with tempfile.TemporaryDirectory() as td:
            params = Path(td) / "params.yaml"
            cfg = {
                "meta": {
                    "run_name": "demo",
                    "year": 2025,
                    "source_population_year": 2019,
                    "source_section_year": 2021,
                },
                "resolved_source_contract": {
                    "runtime": self.resolved_contract()["runtime"],
                },
                "territory_contract": {"k_districts": 2},
                "modulos": {
                    "modulo_04_generar_semillas": {
                        "in_geojson": "out.geojson",
                        "id_field": "LEGACY_ID",
                        "pop_field": "POP_{year}",
                    }
                },
                "partitioning": {
                    "enabled": True,
                    "strategy": "connected_internal_units",
                    "input_geojson": "in.geojson",
                    "graph": "graph.json",
                    "output_geojson": "out.geojson",
                    "output_report": "report.json",
                    "id_field": "LEGACY_ID",
                    "municipality_field": "ADM2_CODE",
                    "population_field": "POP_{year}",
                    "partition_unit_field": "PART_UNIT",
                    "atomicity_ratio": 0.5,
                    "chunk_ratio": 0.8,
                },
            }
            params.write_text(yaml.safe_dump(cfg, sort_keys=False), encoding="utf-8")
            command = build_command(params, "run")
            self.assertIsNotNone(command)
            self.assertEqual(command[command.index("--id-field") + 1], "voting_zone_code_normalized")
            self.assertEqual(command[command.index("--population-field") + 1], "population_runtime")


if __name__ == "__main__":
    unittest.main()
