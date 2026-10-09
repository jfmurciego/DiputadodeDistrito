from __future__ import annotations

import copy
import unittest
from pathlib import Path

import yaml

from herramientas.auditar_lineage_bindings import (
    ContractDerivationBlock,
    audit_binding_lineage,
)
from herramientas.materializar_contrato_generacion import _apply_source_contract
from herramientas.resolver_preparacion_legislatura import resolve

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "configuracion/catalogo_preparacion.yaml"


def final_contract_from_plan(plan: dict) -> tuple[dict, list[dict]]:
    source_plan = plan["resolved_source_plan"]
    assert source_plan["status"] == "RESOLVED"
    population = source_plan["sources"]["population"]
    sectioning = source_plan["sources"]["sectioning"]

    pop_path = population["artifact"]["planned_path"]
    sec_path = sectioning["artifact"]["planned_path"]
    pop_source_id = population["source_id"]
    sec_source_id = sectioning["source_id"]

    resolved = {
        "schema": "ddd.resolved-source-contract/1.0",
        "contract_sha256": "f" * 64,
        "territory": copy.deepcopy(source_plan["territory"]),
        "temporal": copy.deepcopy(source_plan["temporal"]),
        "sources": {
            "population": {
                "schema": "ddd.resolved-source-binding/1.0",
                "source_id": pop_source_id,
                "role": "population",
                "path": pop_path,
                "artifact": {
                    "path": pop_path,
                    "sha256": "a" * 64,
                    "bytes": 1,
                },
                "container": "zip" if str(pop_path).endswith(".zip") else "file",
                "materialized_format": "csv",
                "archive_member": population["artifact"].get("planned_archive_member") or "",
                "encoding": "utf-8-sig",
                "delimiter": "auto",
                "fields": copy.deepcopy(population["fields"]),
                "filters": copy.deepcopy(population["filters"]),
            },
            "sectioning": {
                "schema": "ddd.resolved-source-binding/1.0",
                "source_id": sec_source_id,
                "role": "target_sectioning",
                "path": sec_path,
                "artifact": {
                    "path": sec_path,
                    "sha256": "b" * 64,
                    "bytes": 1,
                },
                "container": "zip" if str(sec_path).endswith(".zip") else "file",
                "materialized_format": "shapefile",
                "archive_member": "",
                "layer": "",
                "fields": copy.deepcopy(sectioning["fields"]),
            },
        },
        "runtime": copy.deepcopy(source_plan["runtime"]),
        "transformations": [
            {
                "kind": "normalize_section_identifier",
                "from": "sources.sectioning.fields.section_id",
                "to": "runtime.section_id_field",
            },
            {
                "kind": "attach_population",
                "source_field": "sources.population.fields.population",
                "to": "runtime.population_field",
            },
        ],
    }
    source_inputs = [
        {
            "source_id": pop_source_id,
            "role": "population",
            "path": pop_path,
            "sha256": "a" * 64,
        },
        {
            "source_id": sec_source_id,
            "role": "target_sectioning",
            "path": sec_path,
            "sha256": "b" * 64,
        },
    ]
    return resolved, source_inputs


class BindingLineageArchitectureTests(unittest.TestCase):
    def test_all_19_current_territories_have_explicit_binding_lineage(self):
        plans = resolve(ROOT, "Todos")["plans"]
        self.assertEqual(len(plans), 19)
        catalog = yaml.safe_load(CATALOG.read_text(encoding="utf-8"))
        states = {
            row["territory_id"]: row["editions"]["2025"]
            for row in catalog["territories"]
        }

        audited = {}
        for plan in plans:
            territory_id = plan["territory_id"]
            with self.subTest(territory_id=territory_id):
                cfg = yaml.safe_load(
                    (ROOT / states[territory_id]["contract_path"]).read_text(
                        encoding="utf-8"
                    )
                )
                resolved, source_inputs = final_contract_from_plan(plan)
                _apply_source_contract(
                    cfg,
                    population_year=int(plan["population_year_selected"]),
                    section_year=int(plan["section_year_selected"]),
                    baseline={
                        "package_sha256": "c" * 64,
                        "compatibility_identity_sha256": "d" * 64,
                    },
                    source_inputs=source_inputs,
                    resolved_contract=resolved,
                )
                lineage = audit_binding_lineage(cfg)
                self.assertTrue(lineage)
                audited[territory_id] = {
                    row["binding"]: row["upstream"]
                    for row in lineage
                }

        self.assertEqual(len(audited), 19)
        for territory_id, lineage in audited.items():
            self.assertEqual(
                lineage["modulos.modulo_03_construir_grafo.pop_field"],
                "resolved_source_contract.runtime.population_field",
                territory_id,
            )
            self.assertEqual(
                lineage["io.input.seccionado.path"],
                "resolved_source_contract.sources.sectioning.artifact.path",
                territory_id,
            )
            self.assertEqual(
                lineage["io.input.population_cip.archive_member"],
                "resolved_source_contract.sources.population.archive_member",
                territory_id,
            )
            self.assertEqual(
                lineage["io.input.population_cip.filters.year_col"],
                "resolved_source_contract.sources.population.fields.year",
                territory_id,
            )
            self.assertEqual(
                lineage["io.input.population_cip.filters.year_value"],
                "resolved_source_contract.sources.population.filters.year_value",
                territory_id,
            )
            self.assertEqual(
                lineage["validation.province_field"],
                "resolved_source_contract.runtime.province_field",
                territory_id,
            )
            self.assertEqual(
                lineage["validation.municipality_field"],
                "resolved_source_contract.runtime.municipality_field",
                territory_id,
            )
            self.assertEqual(
                lineage["generation_state.source_inputs[population].sha256"],
                "resolved_source_contract.sources.population.artifact.sha256",
                territory_id,
            )
            self.assertEqual(
                lineage["generation_state.source_inputs[target_sectioning].sha256"],
                "resolved_source_contract.sources.sectioning.artifact.sha256",
                territory_id,
            )

    def test_hostile_non_spanish_contract_crosses_binding_route_without_invention(self):
        cfg = {
            "meta": {
                "year": 2025,
                "source_population_year": 2019,
                "source_section_year": 2021,
            },
            "io": {"input": {"seccionado": {}, "population_cip": {}}},
            "modulos": {
                "modulo_02_construir_adyacencias": {"id_field": "legacy"},
                "modulo_03_construir_grafo": {"id_field": "legacy", "pop_field": "legacy"},
                "modulo_04_generar_semillas": {
                    "id_field": "legacy",
                    "pop_field": "legacy",
                    "province_field": "legacy",
                    "municipality_field": "PART_UNIT",
                    "source_municipality_field": "legacy",
                },
                "modulo_05_optimizar_distritos": {
                    "id_field": "legacy",
                    "pop_field": "legacy",
                    "province_field": "legacy",
                    "municipality_field": "legacy",
                },
                "modulo_06_consolidar_distritos": {
                    "id_field": "legacy",
                    "pop_field": "legacy",
                    "province_field": "legacy",
                    "municipality_field": "legacy",
                },
            },
            "partitioning": {
                "enabled": True,
                "strategy": "connected_internal_units",
                "partition_unit_field": "PART_UNIT",
                "municipality_field": "legacy",
                "population_field": "POP_{year}",
            },
            "validation": {
                "province_field": "legacy",
                "municipality_field": "legacy",
            },
        }
        resolved = {
            "schema": "ddd.resolved-source-contract/1.0",
            "contract_sha256": "e" * 64,
            "territory": {
                "territory_id": "ecuador_demo",
                "territory_name": "Ecuador demo",
                "project_edition": "2025",
            },
            "temporal": {
                "population_year": 2019,
                "section_year": 2021,
                "election_year": 2022,
            },
            "sources": {
                "population": {
                    "schema": "ddd.resolved-source-binding/1.0",
                    "source_id": "ecuador_population",
                    "role": "population",
                    "path": "inputs/weird_population_file.parquet",
                    "artifact": {
                        "path": "inputs/weird_population_file.parquet",
                        "sha256": "a" * 64,
                        "bytes": 10,
                    },
                    "container": "file",
                    "materialized_format": "parquet",
                    "archive_member": "",
                    "encoding": "utf-8-sig",
                    "delimiter": "auto",
                    "fields": {
                        "section_id": "voting_zone_code",
                        "population": "inhabitants_xyz",
                        "year": "reference_year",
                        "sex": "sex_scope",
                        "age": "age_scope",
                    },
                    "filters": {
                        "year_value": 2019,
                        "sex_total_values": ["ALL"],
                        "age_total_values": ["ALL"],
                    },
                },
                "sectioning": {
                    "schema": "ddd.resolved-source-binding/1.0",
                    "source_id": "ecuador_boundaries",
                    "role": "target_sectioning",
                    "path": "inputs/boundaries.gpkg",
                    "artifact": {
                        "path": "inputs/boundaries.gpkg",
                        "sha256": "b" * 64,
                        "bytes": 10,
                    },
                    "container": "file",
                    "materialized_format": "geopackage",
                    "archive_member": "",
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
        source_inputs = [
            {
                "source_id": "ecuador_population",
                "role": "population",
                "path": "inputs/weird_population_file.parquet",
                "sha256": "a" * 64,
            },
            {
                "source_id": "ecuador_boundaries",
                "role": "target_sectioning",
                "path": "inputs/boundaries.gpkg",
                "sha256": "b" * 64,
            },
        ]
        _apply_source_contract(
            cfg,
            population_year=2019,
            section_year=2021,
            baseline={
                "package_sha256": "c" * 64,
                "compatibility_identity_sha256": "d" * 64,
            },
            source_inputs=source_inputs,
            resolved_contract=resolved,
        )
        lineage = audit_binding_lineage(cfg)
        lineage_map = {
            row["binding"]: row["upstream"]
            for row in lineage
        }
        self.assertEqual(
            lineage_map["io.input.population_cip.filters.year_col"],
            "resolved_source_contract.sources.population.fields.year",
        )
        self.assertEqual(
            lineage_map["io.input.population_cip.filters.year_value"],
            "resolved_source_contract.sources.population.filters.year_value",
        )
        self.assertEqual(
            lineage_map["generation_state.source_inputs[population].sha256"],
            "resolved_source_contract.sources.population.artifact.sha256",
        )
        values = "\n".join(str(row["value"]) for row in lineage)
        for invented in (
            "65034.csv",
            "CUSEC",
            "CUSEC_KEY",
            "CPRO",
            "CUMUN",
            "POP_2025",
            "seccionado_2025.zip",
        ):
            self.assertNotIn(invented, values)

        corrupted = copy.deepcopy(cfg)
        corrupted["modulos"]["modulo_03_construir_grafo"]["pop_field"] = "POP_2025"
        with self.assertRaisesRegex(
            ContractDerivationBlock,
            "CONTRACT_DERIVATION_BLOCK",
        ):
            audit_binding_lineage(corrupted)

        corrupted_physical = copy.deepcopy(cfg)
        corrupted_physical["io"]["input"]["population_cip"]["archive_member"] = "README.csv"
        with self.assertRaisesRegex(
            ContractDerivationBlock,
            "CONTRACT_DERIVATION_BLOCK",
        ):
            audit_binding_lineage(corrupted_physical)

        corrupted_admin = copy.deepcopy(cfg)
        corrupted_admin["modulos"]["modulo_05_optimizar_distritos"][
            "municipality_field"
        ] = "CUMUN"
        corrupted_admin["validation"]["municipality_field"] = "CUMUN"
        with self.assertRaisesRegex(
            ContractDerivationBlock,
            "CONTRACT_DERIVATION_BLOCK",
        ):
            audit_binding_lineage(corrupted_admin)

        corrupted_durable = copy.deepcopy(cfg)
        durable_population = next(
            row
            for row in corrupted_durable["generation_state"]["source_inputs"]
            if row["role"] == "population"
        )
        durable_population["sha256"] = "9" * 64
        with self.assertRaisesRegex(
            ContractDerivationBlock,
            "CONTRACT_DERIVATION_BLOCK",
        ):
            audit_binding_lineage(corrupted_durable)

        corrupted_filter = copy.deepcopy(cfg)
        corrupted_filter["io"]["input"]["population_cip"]["filters"][
            "year_value"
        ] = 2025
        with self.assertRaisesRegex(
            ContractDerivationBlock,
            "CONTRACT_DERIVATION_BLOCK",
        ):
            audit_binding_lineage(corrupted_filter)

        external_mismatch = copy.deepcopy(source_inputs)
        external_mismatch[0]["sha256"] = "8" * 64
        with self.assertRaisesRegex(
            ContractDerivationBlock,
            "CONTRACT_DERIVATION_BLOCK",
        ):
            audit_binding_lineage(
                cfg,
                source_inputs=external_mismatch,
            )


if __name__ == "__main__":
    unittest.main()
