from __future__ import annotations

import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from herramientas.auditar_componentes_geometricos import audit

CRS = {"type": "name", "properties": {"name": "urn:ogc:def:crs:EPSG::25830"}}


def polygon(section: str, district: int, x0: float, x1: float):
    return {"type": "Feature", "properties": {"CUSEC_KEY": section, "district_id": district},
            "geometry": {"type": "Polygon", "coordinates": [[[x0,0],[x1,0],[x1,1],[x0,1],[x0,0]]]}}


def multipart(section: str, district: int, spans: list[tuple[float,float]]):
    return {"type": "Feature", "properties": {"CUSEC_KEY": section, "district_id": district},
            "geometry": {"type": "MultiPolygon", "coordinates": [[[[a,0],[b,0],[b,1],[a,1],[a,0]]] for a,b in spans]}}


class CausalGeometryTests(unittest.TestCase):
    def files(self, root: Path, features: list[dict], bridges: list[dict] | None = None):
        sections = root / "synthetic_m06_secciones.geojson"
        sections.write_text(json.dumps({"type":"FeatureCollection","crs":CRS,"features":features}), encoding="utf-8")
        contract = root / "contract.yaml"
        import yaml
        contract.write_text(yaml.safe_dump({"modulos":{"modulo_02_construir_adyacencias":{"topology_bridges":bridges or []}}}), encoding="utf-8")
        return sections, contract

    def run(self, sections: Path, contract: Path, expected: int = 1):
        return audit(sections, section_field="CUSEC_KEY", district_field="district_id",
                     working_crs="EPSG:25830", contract_path=contract, expected_districts=expected)

    def test_valid_atomic_multipart(self):
        with tempfile.TemporaryDirectory() as raw:
            s,c=self.files(Path(raw), [multipart("a",1,[(0,1),(3,4)])])
            r=self.run(s,c); d=r["districts"][0]
            self.assertEqual(r["decision"], "PASS_WITH_EXCEPTIONS")
            self.assertEqual(d["causal_exceptions"][0]["type"], "ATOMIC_MULTIPART")
            self.assertEqual(d["causal_exceptions"][0]["sections"], ["a"])
            self.assertTrue(d["causal_exceptions"][0]["geometry_sha256"])
            self.assertTrue(d["causal_exceptions"][0]["contract_sha256"])

    def test_valid_governed_bridge(self):
        with tempfile.TemporaryDirectory() as raw:
            bridge={"u":"a","v":"b","edge_type":"administrative_exclave","source":"synthetic"}
            s,c=self.files(Path(raw), [polygon("a",1,0,1),polygon("b",1,3,4)], [bridge])
            r=self.run(s,c); e=r["districts"][0]["causal_exceptions"][0]
            self.assertEqual(r["decision"], "PASS_WITH_EXCEPTIONS")
            self.assertEqual(e["type"], "GOVERNED_BRIDGE"); self.assertEqual(e["endpoints"],["a","b"])
            self.assertIn("topology_bridges[0]", e["source"])

    def test_combination_multipart_and_bridge(self):
        with tempfile.TemporaryDirectory() as raw:
            bridge={"u":"a","v":"b","edge_type":"cartographic_gap"}
            s,c=self.files(Path(raw), [multipart("a",1,[(0,1),(3,4)]),polygon("b",1,6,7)], [bridge])
            r=self.run(s,c); kinds={e["type"] for e in r["districts"][0]["causal_exceptions"]}
            self.assertEqual(r["decision"], "PASS_WITH_EXCEPTIONS")
            self.assertEqual(kinds,{"ATOMIC_MULTIPART","GOVERNED_BRIDGE"})

    def test_bridge_endpoints_in_different_districts_is_not_causal(self):
        with tempfile.TemporaryDirectory() as raw:
            bridge={"u":"a","v":"b","edge_type":"synthetic"}
            features=[polygon("a",1,0,1),polygon("c",1,3,4),polygon("b",2,6,7)]
            s,c=self.files(Path(raw),features,[bridge]); r=self.run(s,c,2)
            d1=next(d for d in r["districts"] if d["district_id"]=="1")
            self.assertEqual(d1["decision"],"BLOCK"); self.assertEqual(d1["causal_exceptions"],[])

    def test_declared_but_unused_bridge_does_not_excuse_component(self):
        with tempfile.TemporaryDirectory() as raw:
            bridge={"u":"a","v":"b","edge_type":"synthetic"}
            features=[polygon("a",1,0,1),polygon("b",1,1,2),polygon("c",1,5,6)]
            s,c=self.files(Path(raw),features,[bridge]); r=self.run(s,c)
            self.assertEqual(r["decision"],"BLOCK")
            self.assertEqual(r["districts"][0]["causal_exceptions"],[])

    def test_unexplained_component_blocks(self):
        with tempfile.TemporaryDirectory() as raw:
            s,c=self.files(Path(raw),[polygon("a",1,0,1),polygon("b",1,3,4)])
            r=self.run(s,c)
            self.assertEqual(r["decision"],"BLOCK"); self.assertTrue(r["districts"][0]["unexplained_components"])

    def test_district_renumbering_does_not_change_causal_result(self):
        with tempfile.TemporaryDirectory() as raw:
            root=Path(raw); bridge={"u":"a","v":"b","edge_type":"synthetic"}
            s1,c1=self.files(root,[polygon("a",1,0,1),polygon("b",1,3,4)],[bridge]); r1=self.run(s1,c1)
            s2=root/"renumbered.geojson"; s2.write_text(json.dumps({"type":"FeatureCollection","crs":CRS,"features":[polygon("a",999,0,1),polygon("b",999,3,4)]}),encoding="utf-8")
            r2=self.run(s2,c1)
            self.assertEqual(r1["decision"],r2["decision"])
            e1=r1["districts"][0]["causal_exceptions"][0]; e2=r2["districts"][0]["causal_exceptions"][0]
            for key in ("type","endpoints","components","contract_sha256"):
                self.assertEqual(e1[key],e2[key])

    def test_district_based_policy_is_rejected(self):
        with tempfile.TemporaryDirectory() as raw:
            root=Path(raw); s,c=self.files(root,[polygon("a",1,0,1)])
            policy=root/"policy.json"; policy.write_text('{"district_id": 1}',encoding="utf-8")
            with self.assertRaisesRegex(ValueError,"prohibidas"):
                audit(s,section_field="CUSEC_KEY",district_field="district_id",working_crs="EPSG:25830",contract_path=c,policy_path=policy)


if __name__ == "__main__": unittest.main()
