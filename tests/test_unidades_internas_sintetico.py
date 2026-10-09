from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "herramientas/preparar_unidades_internas.py"


class InternalUnitsSyntheticExecution(unittest.TestCase):
    def _fixture(self, base: Path) -> tuple[Path, Path]:
        features = []
        for i in range(1, 7):
            features.append({
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [float(i), 0.0]},
                "properties": {"CUSEC_KEY": f"s{i}", "CUMUN": "m1", "POP_2025": 50},
            })
        geo = {"type": "FeatureCollection", "features": features}
        geo_path = base / "input.geojson"
        geo_path.write_text(json.dumps(geo), encoding="utf-8")
        graph = {
            "nodes": [{"id": f"s{i}", "pop": 50} for i in range(1, 7)],
            "edges": [{"u": f"s{i}", "v": f"s{i+1}"} for i in range(1, 6)],
        }
        graph_path = base / "graph.json"
        graph_path.write_text(json.dumps(graph), encoding="utf-8")
        return geo_path, graph_path

    def _params(self, path: Path, geo: Path, graph: Path, output: Path, report: Path, *, policy=True, invalid=False) -> None:
        cfg = {
            "meta": {"run_name": "synthetic", "year": 2025},
            "territory_contract": {"k_districts": 2},
            "modulos": {"modulo_04_generar_semillas": {"in_geojson": str(output), "id_field": "CUSEC_KEY", "pop_field": "POP_2025"}},
        }
        if policy:
            cfg["partitioning"] = {
                "enabled": True,
                "strategy": "invalid_strategy" if invalid else "connected_internal_units",
                "input_geojson": str(geo),
                "graph": str(graph),
                "output_geojson": str(output),
                "output_report": str(report),
                "id_field": "CUSEC_KEY",
                "municipality_field": "CUMUN",
                "population_field": "POP_2025",
                "partition_unit_field": "M04_PARTITION_UNIT",
                "atomicity_ratio": 0.5,
                "chunk_ratio": 0.8,
            }
        path.write_text(yaml.safe_dump(cfg, sort_keys=False), encoding="utf-8")

    def _run(self, params: Path, job_report: Path) -> subprocess.CompletedProcess:
        return subprocess.run(
            [sys.executable, str(SCRIPT), "--params", str(params), "--run-id", "synthetic-run", "--job-report", str(job_report)],
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

    @staticmethod
    def _properties(path: Path) -> list[dict]:
        data = json.loads(path.read_text(encoding="utf-8"))
        return [feature["properties"] for feature in data["features"]]

    @staticmethod
    def _connected(nodes: set[str], edges: list[tuple[str, str]]) -> bool:
        if not nodes:
            return False
        adj = {n: set() for n in nodes}
        for u, v in edges:
            if u in nodes and v in nodes:
                adj[u].add(v)
                adj[v].add(u)
        seen = {next(iter(nodes))}
        stack = list(seen)
        while stack:
            u = stack.pop()
            for v in adj[u]:
                if v not in seen:
                    seen.add(v)
                    stack.append(v)
        return seen == nodes

    def test_real_preparer_preserves_population_sections_connectivity_and_is_deterministic(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            geo, graph = self._fixture(base)
            mappings = []
            for run in (1, 2):
                params = base / f"params{run}.yaml"
                output = base / f"out{run}.geojson"
                report = base / f"out{run}.json"
                job = base / f"job{run}.json"
                self._params(params, geo, graph, output, report)
                proc = self._run(params, job)
                self.assertEqual(proc.returncode, 0, proc.stderr)
                props = self._properties(output)
                ids = [str(p["CUSEC_KEY"]) for p in props]
                self.assertEqual(set(ids), {f"s{i}" for i in range(1, 7)})
                self.assertEqual(len(ids), len(set(ids)))
                self.assertEqual(sum(int(p["POP_2025"]) for p in props), 300)
                units: dict[str, set[str]] = {}
                for p in props:
                    units.setdefault(str(p["M04_PARTITION_UNIT"]), set()).add(str(p["CUSEC_KEY"]))
                edges = [(f"s{i}", f"s{i+1}") for i in range(1, 6)]
                self.assertTrue(all(self._connected(nodes, edges) for nodes in units.values()))
                mappings.append(sorted((str(p["CUSEC_KEY"]), str(p["M04_PARTITION_UNIT"])) for p in props))
                job_data = json.loads(job.read_text(encoding="utf-8"))
                self.assertEqual(job_data["status"], "PREPARED")
                self.assertEqual(job_data["input_geojson"], str(geo))
                self.assertEqual(job_data["output_geojson"], str(output))
                self.assertGreaterEqual(job_data["duration_seconds"], 0)
            self.assertEqual(mappings[0], mappings[1])

    def test_no_policy_is_neutral_noop(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            geo, graph = self._fixture(base)
            params = base / "params.yaml"
            output = base / "unused.geojson"
            self._params(params, geo, graph, output, base / "unused.json", policy=False)
            job = base / "job.json"
            proc = self._run(params, job)
            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertFalse(output.exists())
            self.assertEqual(json.loads(job.read_text(encoding="utf-8"))["status"], "NOOP")

    def test_invalid_policy_blocks(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            geo, graph = self._fixture(base)
            params = base / "params.yaml"
            output = base / "out.geojson"
            self._params(params, geo, graph, output, base / "out.json", invalid=True)
            job = base / "job.json"
            proc = self._run(params, job)
            self.assertEqual(proc.returncode, 2)
            self.assertFalse(output.exists())
            payload = json.loads(job.read_text(encoding="utf-8"))
            self.assertEqual(payload["status"], "BLOCKED")
            self.assertIn("no soportada", payload["error"])


if __name__ == "__main__":
    unittest.main()
