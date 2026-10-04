from __future__ import annotations

import copy
import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import pandas as pd
import yaml

from ddd_core import m04_seed_engine as canonical
from ddd_core.config import hard_limits

ROOT = Path(__file__).resolve().parents[1]
ENTRYPOINT_PATH = ROOT / "modulos" / "04_generar_semillas.py"

spec = importlib.util.spec_from_file_location("ddd_m04_entrypoint_default_regression", ENTRYPOINT_PATH)
entrypoint = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(entrypoint)


CASES = {
    "aragon": {
        "params": ROOT / "territorios/aragon/config/aragon_2025.yaml",
        "graph": ROOT / "territorios/aragon/resultados/ejecuciones/gh-34599224954-1/M03/grafo.json",
        "composition": ROOT / "territorios/aragon/resultados/ejecuciones/gh-34599224954-1/M06/composicion_distritos.csv",
        "k": 67,
        "province_districts": {"22": 11, "44": 7, "50": 49},
    },
    "castilla_y_leon": {
        "params": ROOT / "territorios/castilla_y_leon/config/castilla_y_leon_2025.yaml",
        "graph": ROOT / "territorios/castilla_y_leon/resultados/ejecuciones/gh-34701897922-1/M03/grafo.json",
        "composition": ROOT / "territorios/castilla_y_leon/resultados/ejecuciones/gh-34701897922-1/M06/composicion_distritos.csv",
        "k": 82,
        "province_districts": {
            "05": 6, "09": 12, "24": 15, "34": 6, "37": 11,
            "40": 5, "42": 3, "47": 18, "49": 6,
        },
    },
}


def connected(nodes, adjacency):
    nodes = set(nodes)
    if not nodes:
        return False
    seen = {next(iter(nodes))}
    stack = list(seen)
    while stack:
        node = stack.pop()
        for neighbor in adjacency.get(node, set()):
            if neighbor in nodes and neighbor not in seen:
                seen.add(neighbor)
                stack.append(neighbor)
    return seen == nodes


class CanonicalDefaultRegressionTests(unittest.TestCase):
    maxDiff = None

    def _run_case(self, case):
        cfg = yaml.safe_load(case["params"].read_text(encoding="utf-8"))
        step = cfg["modulos"]["modulo_04_generar_semillas"]
        self.assertNotIn(
            "gateway_policy",
            step,
            "La regresión debe cubrir exactamente el nuevo default nacional, no un opt-in.",
        )

        graph = json.loads(case["graph"].read_text(encoding="utf-8"))
        weights = {str(node["id"]): int(node["pop"]) for node in graph["nodes"]}
        adjacency = {node: set() for node in weights}
        for edge in graph["edges"]:
            left, right = str(edge["u"]), str(edge["v"])
            if left in adjacency and right in adjacency:
                adjacency[left].add(right)
                adjacency[right].add(left)

        composition = pd.read_csv(
            case["composition"],
            dtype={"CUSEC_KEY": str, "CPRO": str, "CUMUN": str},
        )
        composition["CUSEC_KEY"] = composition["CUSEC_KEY"].astype(str).str.zfill(10)
        composition["CPRO"] = composition["CPRO"].astype(str).str.zfill(2)
        composition["CUMUN"] = composition["CUMUN"].astype(str).str.zfill(5)

        # El grafo M03 y la composición M06 certificados deben describir
        # exactamente el mismo universo de secciones. Normalizamos CUSEC a su
        # representación canónica de 10 dígitos antes de comparar.
        graph_ids = sorted(weights)
        self.assertTrue(
            all(len(section) == 10 and section.isdigit() for section in graph_ids)
        )
        certified = (
            composition[["CUSEC_KEY", "CPRO", "CUMUN"]]
            .drop_duplicates("CUSEC_KEY")
            .set_index("CUSEC_KEY")
        )
        self.assertEqual(set(certified.index), set(graph_ids))
        for section in graph_ids:
            self.assertEqual(certified.loc[section, "CPRO"], section[:2])
            self.assertEqual(certified.loc[section, "CUMUN"], section[:5])

        frame = certified.reset_index().copy()

        with tempfile.TemporaryDirectory() as td:
            temp = Path(td)
            params_path = temp / "params.yaml"
            params_path.write_text("{}\n", encoding="utf-8")
            output_path = temp / "m04.geojson.zip"
            report_path = temp / "m04_report.json"

            cfg = copy.deepcopy(cfg)
            step = cfg["modulos"]["modulo_04_generar_semillas"]
            step["in_graph_json"] = str(case["graph"])
            step["in_geojson"] = str(temp / "certified-input.geojson.zip")
            step["out_geojson"] = str(output_path)
            step["out_report"] = str(report_path)

            captured = {"frame": None}

            def load_geo(path):
                if str(path) == str(output_path) and captured["frame"] is not None:
                    return captured["frame"].copy()
                return frame.copy()

            def write_geo(gdf, _path):
                captured["frame"] = gdf.copy()

            def load_cfg(_path):
                return copy.deepcopy(cfg)

            patches = [
                patch.object(entrypoint, "load_params_yaml", side_effect=load_cfg),
                patch.object(entrypoint, "load_geo", side_effect=load_geo),
                patch.object(entrypoint, "write_geo", side_effect=write_geo),
                patch.object(entrypoint, "normalize_unit_property_for_ogr", return_value=0),
                patch.object(canonical, "load_params_yaml", side_effect=load_cfg),
                patch.object(canonical, "_normalize_unit_property_for_ogr", return_value=0),
                patch.object(canonical.core, "load_params_yaml", side_effect=load_cfg),
                patch.object(canonical.core, "load_geo", side_effect=load_geo),
                patch.object(canonical.core.previous, "load_params_yaml", side_effect=load_cfg),
                patch.object(canonical.core.previous, "load_geo", side_effect=load_geo),
                patch.object(canonical.core.previous, "write_geo", side_effect=write_geo),
                patch.object(canonical.postprocess_engine, "load_params_yaml", side_effect=load_cfg),
                patch.object(canonical.postprocess_engine, "load_geo", side_effect=load_geo),
                patch.object(canonical.postprocess_engine, "write_geo", side_effect=write_geo),
            ]
            old_argv = sys.argv
            self.assertIs(
                canonical.core.partition_oversized_municipality,
                canonical.partition_oversized_municipality,
                "M04 no debe heredar un monkey-patch de una ejecución anterior",
            )
            try:
                for item in patches:
                    item.start()
                sys.argv = [str(ENTRYPOINT_PATH), "--params", str(params_path)]
                entrypoint.main()
            finally:
                sys.argv = old_argv
                for item in reversed(patches):
                    item.stop()
            self.assertIs(
                canonical.core.partition_oversized_municipality,
                canonical.partition_oversized_municipality,
                "M04 debe restaurar el motor de particionado tras la ejecución",
            )

            result = captured["frame"]
            self.assertIsNotNone(result)
            result["CUSEC_KEY"] = result["CUSEC_KEY"].astype(str)
            result["CPRO"] = result["CPRO"].astype(str).str.zfill(2)

            self.assertEqual(result["district_id"].nunique(), case["k"])
            counts = (
                result.groupby("CPRO")["district_id"]
                .nunique()
                .astype(int)
                .to_dict()
            )
            self.assertEqual(counts, case["province_districts"])

            district_nodes = {
                int(district): set(group["CUSEC_KEY"].astype(str))
                for district, group in result.groupby("district_id")
            }
            for district, nodes in district_nodes.items():
                self.assertTrue(
                    connected(nodes, adjacency),
                    f"{case['params'].stem}: distrito {district} desconectado",
                )
                provinces = set(
                    result.loc[
                        result["district_id"] == district, "CPRO"
                    ].astype(str).str.zfill(2)
                )
                self.assertEqual(len(provinces), 1)

            total = sum(weights.values())
            _, floor, cap, _ = hard_limits(cfg, k=case["k"], total_pop=total)
            floor_exempt = {
                str(value).zfill(2)
                for value in (
                    (cfg.get("validation") or {}).get(
                        "population_floor_exempt_partitions"
                    )
                    or []
                )
            }
            for district, nodes in district_nodes.items():
                population = sum(weights[node] for node in nodes)
                province = str(
                    result.loc[
                        result["district_id"] == district, "CPRO"
                    ].iloc[0]
                ).zfill(2)
                if province not in floor_exempt:
                    self.assertGreaterEqual(population, floor)
                self.assertLessEqual(population, cap)

            report = json.loads(report_path.read_text(encoding="utf-8"))
            self.assertEqual(report.get("version"), entrypoint.ENTRYPOINT_VERSION)
            self.assertEqual(report.get("engine_version"), canonical.ENGINE_VERSION)
            self.assertEqual(
                report.get("gateway_policy"),
                "preserve_dependent_component_gateways",
            )

    def test_aragon_certified_inputs_preserve_hard_baseline_through_current_entrypoint(self):
        self._run_case(CASES["aragon"])

    def test_castilla_y_leon_certified_inputs_preserve_hard_baseline_through_current_entrypoint(self):
        self._run_case(CASES["castilla_y_leon"])


if __name__ == "__main__":
    unittest.main()
