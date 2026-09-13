#!/usr/bin/env python3
"""C-07 v1.0.0: adversarial end-to-end fixture with a unique known optimum."""

from __future__ import annotations

import csv
import json
import os
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
IDS = ["0100101001", "0100201001", "0100301001", "0100401001"]
POPS = [60, 40, 30, 70]
KNOWN_PARTITION = {frozenset(IDS[:2]), frozenset(IDS[2:])}


def partition_from_rows(rows):
    groups = {}
    for row in rows:
        groups.setdefault(int(row["district_id"]), set()).add(row["CUSEC_KEY"])
    return {frozenset(group) for group in groups.values()}


class AdversarialPipelineC07(unittest.TestCase):
    def assert_known_solution(self, rows):
        self.assertEqual(partition_from_rows(rows), KNOWN_PARTITION)
        populations = {}
        for row in rows:
            populations.setdefault(int(row["district_id"]), 0)
            populations[int(row["district_id"])] += int(row["section_pop"])
        self.assertEqual(sorted(populations.values()), [100, 100])

    def test_oracle_rejects_plausible_but_wrong_partition(self):
        wrong = [
            {"district_id": 0, "CUSEC_KEY": IDS[0], "section_pop": 60},
            {"district_id": 1, "CUSEC_KEY": IDS[1], "section_pop": 40},
            {"district_id": 1, "CUSEC_KEY": IDS[2], "section_pop": 30},
            {"district_id": 1, "CUSEC_KEY": IDS[3], "section_pop": 70},
        ]
        with self.assertRaises(AssertionError):
            self.assert_known_solution(wrong)

    def test_pipeline_finds_unique_known_partition(self):
        import geopandas as gpd
        import yaml
        from shapely.geometry import box

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source = root / "source"
            output = root / "output"
            source.mkdir()
            output.mkdir()
            frame = gpd.GeoDataFrame(
                {
                    "CUSEC": IDS,
                    "CPRO": ["01"] * 4,
                    "NPRO": ["Sintética"] * 4,
                    "CUMUN": ["01001", "01002", "01003", "01004"],
                    "NMUN": ["A", "B", "C", "D"],
                    "CUDIS": ["01"] * 4,
                },
                geometry=[box(i, 0, i + 1, 1) for i in range(4)],
                crs="EPSG:4326",
            )
            shapefile = source / "sections.shp"
            frame.to_file(shapefile)
            section_zip = root / "sections.zip"
            with zipfile.ZipFile(section_zip, "w", zipfile.ZIP_DEFLATED) as archive:
                for path in source.glob("sections.*"):
                    archive.write(path, path.name)
            population = root / "population.csv"
            with population.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.writer(handle)
                writer.writerow(["Secciones", "Total", "Periodo", "Sexo", "Edad"])
                for section_id, value in zip(IDS, POPS):
                    writer.writerow([section_id, value, 2025, "Total", "Todas las edades"])

            config = self._config(root, section_zip, population)
            params = root / "params.yaml"
            params.write_text(yaml.safe_dump(config, sort_keys=False), encoding="utf-8")
            environment = dict(os.environ, PYTHONHASHSEED="0")
            names = [
                "preparar_base_territorial",
                "construir_adyacencias",
                "construir_grafo",
                "generar_semillas",
                "optimizar_distritos",
                "consolidar_distritos",
            ]
            for number, name in enumerate(names, 1):
                completed = subprocess.run(
                    [sys.executable, str(ROOT / "modulos" / f"{number:02d}_{name}.py"), "--params", str(params)],
                    cwd=ROOT,
                    env=environment,
                    text=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                )
                self.assertEqual(completed.returncode, 0, f"M{number:02d}\n{completed.stdout}")
            with (output / "m06_composition.csv").open(encoding="utf-8", newline="") as handle:
                rows = list(csv.DictReader(handle))
            self.assert_known_solution(rows)
            graph = json.loads((output / "m03.json").read_text(encoding="utf-8"))
            self.assertEqual(len(graph["edges"]), 3)

    @staticmethod
    def _config(root, section_zip, population):
        return {
            "meta": {"run_name": "c07_adversarial", "year": 2025, "scope": "provincial"},
            "io": {
                "project_root": {"path": str(root)},
                "input": {
                    "seccionado": {"path": str(section_zip), "layer": "", "section_key_col": "CUSEC"},
                    "population_cip": {
                        "paths": [str(population)], "sep": ",", "section_key_col": "Secciones", "pop_col": "Total",
                        "filters": {"year_col": "Periodo", "sexo_col": "Sexo", "edad_col": "Edad", "sexo_total_values": ["Total"], "edad_total_values": ["Todas las edades"]},
                    },
                },
            },
            "modulos": {
                "modulo_01_preparar_base_territorial": {"province_codes": ["01"], "drop_missing_population": False, "out_geojson": "output/m01.geojson.zip", "out_report": "output/m01.json"},
                "modulo_02_construir_adyacencias": {"in_geojson": "output/m01.geojson.zip", "id_field": "CUSEC_KEY", "out_edges_jsonl": "output/m02.jsonl", "predicate": "touches", "working_crs": "EPSG:3035", "min_shared_border_m": 0.0, "buffer_m": 0.0, "simplify_m": 0.0, "max_candidates": 0, "log_every": 0},
                "modulo_03_construir_grafo": {"in_geojson": "output/m01.geojson.zip", "in_edges_jsonl": "output/m02.jsonl", "id_field": "CUSEC_KEY", "pop_field": "POP_{year}", "out_graph_json": "output/m03.json", "out_report": "output/m03_report.json"},
                "modulo_04_generar_semillas": {"in_graph_json": "output/m03.json", "in_geojson": "output/m01.geojson.zip", "id_field": "CUSEC_KEY", "pop_field": "POP_{year}", "province_field": "CPRO", "municipality_field": "CUMUN", "municipality_name_field": "NMUN", "district_apportionment": "hamilton", "k_districts": 2, "municipality_atomicity_limit_ratio": 0.70, "seed": 12345, "out_geojson": "output/m04.geojson.zip", "out_report": "output/m04.json"},
                "modulo_05_optimizar_distritos": {"in_graph_json": "output/m03.json", "in_geojson": "output/m04.geojson.zip", "id_field": "CUSEC_KEY", "pop_field": "POP_{year}", "district_field": "district_id", "province_field": "CPRO", "municipality_field": "CUMUN", "greedy_moves_limit": 20, "anneal_iters": 100, "seed": 12345, "anneal_seed_offset": 0, "anneal_outside_penalty": 0.01, "anneal_maxdev_weight": 0.05, "anneal_churn_weight": 0.0016, "anneal_temp_start": 0.02, "anneal_temp_end": 0.0005, "swap_polish_max": 0, "out_geojson": "output/m05.geojson.zip", "out_report": "output/m05.json"},
                "modulo_06_consolidar_distritos": {"in_geojson": "output/m05.geojson.zip", "id_field": "CUSEC_KEY", "district_field": "district_id", "pop_field": "POP_{year}", "province_field": "CPRO", "province_name_field": "NPRO", "municipality_field": "CUMUN", "municipality_name_field": "NMUN", "cudis_field": "CUDIS", "metric_crs": "EPSG:3035", "expected_districts": 2, "strict_expected_k": True, "out_summary_csv": "output/m06_summary.csv", "out_catalog_csv": "output/m06_catalog.csv", "out_composition_csv": "output/m06_composition.csv", "out_geojson": "output/m06_sections.geojson.zip", "out_district_geojson": "output/m06_districts.geojson.zip"},
            },
            "validation": {"expected_districts": 2, "population_floor_ratio": 0.50, "population_cap_ratio": 1.50, "target_tolerance_ratio": 0.05, "province_districts": {"01": 2}, "province_field": "CPRO", "municipality_field": "CUMUN", "municipality_name_field": "NMUN", "require_graph_contiguity": True, "require_one_graph_component_per_province": True, "require_connected_municipalities": True, "require_single_province_per_district": True, "require_municipality_discipline": True, "max_mixed_districts_per_split_municipality": 1},
        }


if __name__ == "__main__":
    unittest.main()
