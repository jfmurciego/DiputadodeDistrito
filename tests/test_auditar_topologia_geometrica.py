from __future__ import annotations

import json
from pathlib import Path
import sys
import tempfile
import unittest
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from herramientas.auditar_topologia_geometrica import _read_geojson, audit


class GeometricTopologyAuditTests(unittest.TestCase):
    def fixture(self, root: Path, diagonal: bool) -> tuple[Path, Path, Path]:
        features = []
        positions = [(0, 0), (1, 0), (0, 1), (1, 1)]
        districts = [0, 1, 1, 0] if diagonal else [0, 0, 1, 1]
        for index, ((x, y), district) in enumerate(zip(positions, districts)):
            features.append({
                "type": "Feature",
                "properties": {"CUSEC_KEY": str(index), "district_id": district},
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[[x, y], [x + 1, y], [x + 1, y + 1], [x, y + 1], [x, y]]],
                },
            })
        payload = {
            "type": "FeatureCollection",
            "crs": {"type": "name", "properties": {"name": "urn:ogc:def:crs:EPSG::25830"}},
            "features": features,
        }
        sections = root / "sections.geojson"
        assignment = root / "assignment.geojson"
        sections.write_text(json.dumps(payload), encoding="utf-8")
        assignment.write_text(json.dumps(payload), encoding="utf-8")
        graph = root / "graph.json"
        graph.write_text(json.dumps({
            "nodes": [{"id": str(i), "pop": 10} for i in range(4)],
            "edges": [
                {"u": "0", "v": "1"}, {"u": "0", "v": "2"}, {"u": "0", "v": "3"},
                {"u": "1", "v": "2"}, {"u": "1", "v": "3"}, {"u": "2", "v": "3"},
            ],
        }), encoding="utf-8")
        return sections, graph, assignment

    def test_corner_contacts_do_not_certify_district_contiguity(self):
        with tempfile.TemporaryDirectory() as raw:
            paths = self.fixture(Path(raw), diagonal=True)
            report = audit(*paths, section_field="CUSEC_KEY", district_field="district_id", min_shared_border_m=0.5, working_crs="EPSG:25830")
            self.assertEqual(report["decision"], "BLOCK")
            self.assertEqual(report["point_only_edges"], 2)
            self.assertEqual(report["territory_component_sizes"], [4])
            self.assertEqual(report["disconnected_districts"], {"0": [1, 1], "1": [1, 1]})

    def test_shared_line_partition_passes(self):
        with tempfile.TemporaryDirectory() as raw:
            paths = self.fixture(Path(raw), diagonal=False)
            report = audit(*paths, section_field="CUSEC_KEY", district_field="district_id", min_shared_border_m=0.5, working_crs="EPSG:25830")
            self.assertEqual(report["decision"], "PASS")

    def test_reads_geojson_zip_used_by_production(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            sections, _, _ = self.fixture(root, diagonal=False)
            archive_path = root / "sections.geojson.zip"
            with zipfile.ZipFile(archive_path, "w") as archive:
                archive.write(sections, arcname="sections.geojson")
            self.assertEqual(len(_read_geojson(archive_path)), 4)


if __name__ == "__main__":
    unittest.main()
