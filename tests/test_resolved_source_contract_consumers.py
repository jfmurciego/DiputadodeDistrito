from __future__ import annotations

import copy
import importlib.util
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

import yaml

from ddd_core.territory_contract import validate_production_contract
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
                    "container": "zip",
                    "materialized_format": "shapefile",
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
                "modulo_04_generar_semillas": {
                    "id_field": "LEGACY",
                    "pop_field": "POP_2025",
                    "province_field": "CPRO",
                    "municipality_field": "M04_PARTITION_UNIT",
                    "source_municipality_field": "CUMUN",
                },
                "modulo_05_optimizar_distritos": {
                    "id_field": "LEGACY",
                    "pop_field": "POP_2025",
                    "province_field": "CPRO",
                    "municipality_field": "CUMUN",
                },
                "modulo_06_consolidar_distritos": {
                    "id_field": "LEGACY",
                    "pop_field": "POP_2025",
                    "province_field": "CPRO",
                    "municipality_field": "CUMUN",
                },
            },
            "partitioning": {
                "enabled": True,
                "strategy": "connected_internal_units",
                "partition_unit_field": "M04_PARTITION_UNIT",
                "municipality_field": "CUMUN",
                "population_field": "POP_{year}",
            },
            "validation": {
                "province_field": "CPRO",
                "municipality_field": "CUMUN",
            },
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
        self.assertEqual(cfg["io"]["input"]["population_cip"]["container"], "zip")
        self.assertEqual(cfg["io"]["input"]["population_cip"]["materialized_format"], "csv")
        self.assertEqual(cfg["io"]["input"]["population_cip"]["archive_member"], "population.dat")
        self.assertEqual(cfg["io"]["input"]["population_cip"]["encoding"], "utf-8")
        self.assertEqual(cfg["io"]["input"]["seccionado"]["path"], "inputs/boundaries.bundle")
        self.assertEqual(cfg["io"]["input"]["seccionado"]["container"], "zip")
        self.assertEqual(cfg["io"]["input"]["seccionado"]["materialized_format"], "shapefile")
        self.assertEqual(cfg["io"]["input"]["seccionado"]["section_key_col"], "ZONA_ID")
        self.assertEqual(cfg["modulos"]["modulo_03_construir_grafo"]["id_field"], "voting_zone_code_normalized")
        self.assertEqual(cfg["modulos"]["modulo_03_construir_grafo"]["pop_field"], "population_runtime")
        self.assertEqual(cfg["partitioning"]["population_field"], "population_runtime")
        self.assertEqual(cfg["validation"]["province_field"], "PROV_CODE")
        self.assertEqual(cfg["validation"]["municipality_field"], "ADM2_CODE")
        self.assertEqual(cfg["partitioning"]["municipality_field"], "ADM2_CODE")
        self.assertEqual(
            cfg["modulos"]["modulo_04_generar_semillas"]["province_field"],
            "PROV_CODE",
        )
        self.assertEqual(
            cfg["modulos"]["modulo_04_generar_semillas"]["municipality_field"],
            "M04_PARTITION_UNIT",
        )
        self.assertEqual(
            cfg["modulos"]["modulo_04_generar_semillas"]["source_municipality_field"],
            "ADM2_CODE",
        )
        for module_name in (
            "modulo_05_optimizar_distritos",
            "modulo_06_consolidar_distritos",
        ):
            self.assertEqual(
                cfg["modulos"][module_name]["province_field"],
                "PROV_CODE",
            )
            self.assertEqual(
                cfg["modulos"][module_name]["municipality_field"],
                "ADM2_CODE",
            )

    def test_runtime_admin_bindings_keep_production_contract_coherent(self):
        source = (
            ROOT
            / "territorios/principado_de_asturias/config/principado_de_asturias_2025.yaml"
        )
        cfg = yaml.safe_load(source.read_text(encoding="utf-8"))
        resolved = copy.deepcopy(self.resolved_contract())

        population = resolved["sources"]["population"]
        population["path"] = "inputs/65034.csv.zip"
        population["artifact"]["path"] = "inputs/65034.csv.zip"
        population["archive_member"] = "65034.csv"
        population["fields"] = {
            "section_id": "Secciones",
            "population": "Total",
            "year": "Periodo",
            "sex": "Sexo",
            "age": "Edad",
        }
        population["filters"] = {
            "year_value": 2023,
            "sex_total_values": ["Total"],
            "age_total_values": ["Todas las edades"],
        }

        sectioning = resolved["sources"]["sectioning"]
        sectioning["path"] = "inputs/seccionado_2023.zip"
        sectioning["artifact"]["path"] = "inputs/seccionado_2023.zip"
        sectioning["fields"]["section_id"] = "CUSEC"

        resolved["temporal"] = {
            "population_year": 2023,
            "section_year": 2023,
        }
        resolved["runtime"] = {
            "section_id_field": "CUSEC_KEY",
            "population_field": "POP_2023",
            "province_field": "PROV_CODE",
            "municipality_field": "ADM2_CODE",
        }

        source_inputs = [
            {
                "source_id": "demo-pop",
                "role": "population",
                "path": "inputs/65034.csv.zip",
                "sha256": "b" * 64,
            },
            {
                "source_id": "demo-geo",
                "role": "target_sectioning",
                "path": "inputs/seccionado_2023.zip",
                "sha256": "c" * 64,
            },
        ]
        _apply_source_contract(
            cfg,
            population_year=2023,
            section_year=2023,
            baseline={
                "package_sha256": "d" * 64,
                "compatibility_identity_sha256": "e" * 64,
            },
            source_inputs=source_inputs,
            resolved_contract=resolved,
        )

        self.assertEqual(cfg["validation"]["province_field"], "PROV_CODE")
        self.assertEqual(cfg["validation"]["municipality_field"], "ADM2_CODE")
        self.assertEqual(cfg["partitioning"]["municipality_field"], "ADM2_CODE")
        self.assertEqual(
            cfg["modulos"]["modulo_04_generar_semillas"]["municipality_field"],
            "M04_PARTITION_UNIT",
        )
        self.assertEqual(
            cfg["modulos"]["modulo_05_optimizar_distritos"]["municipality_field"],
            "ADM2_CODE",
        )
        self.assertEqual(
            cfg["modulos"]["modulo_06_consolidar_distritos"]["municipality_field"],
            "ADM2_CODE",
        )

        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            suffix=".yaml",
            dir=source.parent,
            delete=False,
        ) as handle:
            yaml.safe_dump(cfg, handle, sort_keys=False, allow_unicode=True)
            path = Path(handle.name)
        try:
            report = validate_production_contract(
                path,
                expected_territory="principado_de_asturias",
            )
        finally:
            path.unlink(missing_ok=True)

        self.assertEqual(report["status"], "ADMITTED", report["errors"])
        self.assertTrue(report["production_authorized"], report["errors"])

    def test_m01_outputs_are_contract_owned(self):
        module = load_m01()
        cfg = {"resolved_source_contract": {"runtime": self.resolved_contract()["runtime"]}}
        self.assertEqual(
            module.resolve_runtime_fields(cfg, 2019),
            ("voting_zone_code_normalized", "population_runtime"),
        )

    def test_m01_real_io_obeys_container_member_encoding_and_delimiter(self):
        import geopandas as gpd
        from shapely.geometry import Polygon

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            inputs = root / "inputs"
            inputs.mkdir(parents=True)

            population_path = inputs / "population.pkg"
            misleading = (
                "wrong,columns\n"
                "this,would_fail\n"
            ).encode("utf-8")
            real_population = (
                "Año|Sexo|Edad|Sección|Habitantes\n"
                "2019|Todos|Todas|3300101001|1234\n"
                "2019|Todos|Todas|3300101002|567\n"
            ).encode("latin-1")
            with zipfile.ZipFile(population_path, "w", zipfile.ZIP_DEFLATED) as archive:
                # El señuelo aparece primero para que cualquier autodetección falle.
                archive.writestr("README.csv", misleading)
                archive.writestr("real_data.dat", real_population)

            shape_dir = root / "shape"
            shape_dir.mkdir()
            shp = shape_dir / "sections.shp"
            gdf = gpd.GeoDataFrame(
                {
                    "ZONA_ID": ["3300101001", "3300101002"],
                    "CPRO": ["33", "33"],
                },
                geometry=[
                    Polygon([(0, 0), (1, 0), (1, 1), (0, 1)]),
                    Polygon([(1, 0), (2, 0), (2, 1), (1, 1)]),
                ],
                crs="EPSG:4326",
            )
            gdf.to_file(shp, driver="ESRI Shapefile", index=False)
            section_path = inputs / "boundaries.bundle"
            with zipfile.ZipFile(section_path, "w", zipfile.ZIP_DEFLATED) as archive:
                for sidecar in sorted(shape_dir.glob("sections.*")):
                    archive.write(sidecar, arcname=sidecar.name)

            resolved = copy.deepcopy(self.resolved_contract())
            population = resolved["sources"]["population"]
            population["path"] = "inputs/population.pkg"
            population["artifact"]["path"] = "inputs/population.pkg"
            population["archive_member"] = "real_data.dat"
            population["encoding"] = "latin-1"
            population["delimiter"] = "|"
            population["fields"] = {
                "section_id": "Sección",
                "population": "Habitantes",
                "year": "Año",
                "sex": "Sexo",
                "age": "Edad",
            }
            population["filters"] = {
                "year_value": 2019,
                "sex_total_values": ["Todos"],
                "age_total_values": ["Todas"],
            }

            sectioning = resolved["sources"]["sectioning"]
            sectioning["path"] = "inputs/boundaries.bundle"
            sectioning["artifact"]["path"] = "inputs/boundaries.bundle"
            sectioning["container"] = "zip"
            sectioning["materialized_format"] = "shapefile"
            sectioning["archive_member"] = "sections.shp"
            sectioning["layer"] = ""
            sectioning["fields"]["section_id"] = "ZONA_ID"

            source_inputs = [
                {
                    "source_id": "demo-pop",
                    "role": "population",
                    "path": "inputs/population.pkg",
                    "sha256": "b" * 64,
                },
                {
                    "source_id": "demo-geo",
                    "role": "target_sectioning",
                    "path": "inputs/boundaries.bundle",
                    "sha256": "c" * 64,
                },
            ]
            cfg = {
                "meta": {"year": 2025},
                "io": {"input": {"seccionado": {}, "population_cip": {}}},
                "validation": {"require_non_null_population": True},
                "modulos": {
                    "modulo_01_preparar_base_territorial": {
                        "province_codes": ["33"],
                        "out_geojson": "outputs/m01.zip",
                        "out_report": "outputs/m01_report.json",
                    },
                },
            }
            _apply_source_contract(
                cfg,
                population_year=2019,
                section_year=2021,
                baseline={
                    "package_sha256": "d" * 64,
                    "compatibility_identity_sha256": "e" * 64,
                },
                source_inputs=source_inputs,
                resolved_contract=resolved,
            )
            params = root / "params.yaml"
            params.write_text(yaml.safe_dump(cfg, sort_keys=False), encoding="utf-8")

            completed = subprocess.run(
                [sys.executable, str(M01_PATH), "--params", str(params)],
                cwd=root,
                text=True,
                capture_output=True,
            )
            self.assertEqual(
                completed.returncode,
                0,
                completed.stdout + "\n" + completed.stderr,
            )
            report = yaml.safe_load(
                (root / "outputs/m01_report.json").read_text(encoding="utf-8")
            )
            self.assertEqual(report["population_field"], "population_runtime")
            self.assertEqual(
                report["section_id_field"],
                "voting_zone_code_normalized",
            )
            self.assertEqual(report["rows_out"], 2)

            with zipfile.ZipFile(root / "outputs/m01.zip") as archive:
                geojson_name = next(
                    name for name in archive.namelist()
                    if name.endswith(".geojson")
                )
                extracted = root / "m01.geojson"
                extracted.write_bytes(archive.read(geojson_name))
            output = gpd.read_file(extracted)
            self.assertEqual(
                output["population_runtime"].astype(int).tolist(),
                [1234, 567],
            )
            self.assertIn("voting_zone_code_normalized", output.columns)
            self.assertNotIn("CUSEC_KEY", output.columns)

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
                    "municipality_field": "CUMUN",
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
            self.assertEqual(command[command.index("--municipality-field") + 1], "ADM2_CODE")


if __name__ == "__main__":
    unittest.main()
