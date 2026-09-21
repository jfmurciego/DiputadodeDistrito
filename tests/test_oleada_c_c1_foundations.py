from __future__ import annotations

import hashlib
import json
import shutil
import tempfile
import unittest
from pathlib import Path

import yaml

from herramientas.generar_read_model_plataforma import build

ROOT = Path(__file__).resolve().parents[1]


class OleadaCC1Foundations(unittest.TestCase):
    def test_campaign_example_is_declarative_and_inherits_territorial_method(self):
        data=yaml.safe_load((ROOT/"orchestracion/campanas/c1-ejemplo.yaml").read_text(encoding="utf-8"))
        self.assertEqual(data["schema"],"ddd-campaign/1.0")
        self.assertEqual(data["environment"],"test")
        self.assertFalse(data["publish_result"])
        self.assertEqual(data["max_parallel"],2)
        for row in data["territories"]:
            self.assertNotIn("optimization_algorithm",row)

    def test_aragon_candidate_only_adds_missing_semantics_and_metrics(self):
        data=yaml.safe_load((ROOT/"configuracion/oleada_c/comunidades_interes_candidatas.yaml").read_text(encoding="utf-8"))
        aragon=data["territories"]["aragon"]
        self.assertEqual(aragon["semantics"],"SOFT_OBJECTIVE")
        self.assertEqual(aragon["integration_status"],"DESIGN_ONLY")
        self.assertNotIn("source",aragon)
        self.assertNotIn("search_weight",aragon)
        self.assertIn("avoidable_split_communities",aragon["metrics"])
        self.assertIn("retention_over_structural_max",aragon["metrics"])
        self.assertEqual(aragon["structural_normalization"]["oversized_communities"],11)
        self.assertEqual(aragon["structural_normalization"]["total_communities"],33)
        self.assertAlmostEqual(aragon["structural_normalization"]["retention_max"],0.352)

    def test_aragon_read_model_reads_contract_and_pinned_source(self):
        payload=build(ROOT,"2025")
        aragon=next(x for x in payload["territories"] if x["territory_id"]=="aragon")
        coi=aragon["community_interest"]
        self.assertEqual(coi["source"],"inputs/COMARCAS.csv")
        self.assertEqual(coi["source_sha256"],"ac750499cc180c1241465a42b089044cd3095850b078113bc900b1a33538899a")
        self.assertAlmostEqual(coi["search_weight"],0.30)
        self.assertEqual(coi["semantics"],"SOFT_OBJECTIVE")

    def test_source_hash_matches_real_file_when_present(self):
        source=ROOT/"inputs/COMARCAS.csv"
        expected="ac750499cc180c1241465a42b089044cd3095850b078113bc900b1a33538899a"
        if source.is_file():
            self.assertEqual(hashlib.sha256(source.read_bytes()).hexdigest(),expected)
        manifest=(ROOT/"inputs/MANIFEST.sha256").read_text(encoding="utf-8")
        self.assertIn(f"{expected}  inputs/COMARCAS.csv",manifest)

    def test_read_model_has_lineage_and_publications(self):
        payload=build(ROOT,"2025")
        self.assertEqual(len(payload["territories"]),19)
        self.assertGreaterEqual(len(payload["publications"]),1)
        for row in payload["territories"]:
            for key in ("source_commit","artifact_sha256","release_tag","doi","attestation_verified","osf_registration"):
                self.assertIn(key,row)
        for row in payload["publications"]:
            for key in ("source_commit","artifact_sha256","release_tag","doi","attestation_verified","osf_registration"):
                self.assertIn(key,row)

    def test_side_effect_free_in_temporary_tree(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            (root/"configuracion/oleada_c").mkdir(parents=True)
            (root/"orchestracion/campanas").mkdir(parents=True)
            (root/"inputs").mkdir(parents=True)
            (root/"territorios/demo/config").mkdir(parents=True)
            (root/"configuracion/catalogo_preparacion.yaml").write_text(
                """schema: ddd-preparation-catalog/1.1
default_edition: '2025'
territories:
- territory_id: demo
  name: Demo
  editions:
    '2025':
      contract_path: territorios/demo/config/demo_2025.yaml
      territorial_sources_prepared: false
      territorial_product_available: false
      electoral_source_prepared: false
      electoral_product_available: false
      production_authorization: NONE
      territorial_certification: NOT_CERTIFIED
""",encoding="utf-8")
            (root/"territorios/demo/config/demo_2025.yaml").write_text(
                "io:\n  input: {}\nmodulos: {}\n",encoding="utf-8")
            (root/"configuracion/oleada_c/comunidades_interes_candidatas.yaml").write_text(
                "schema: ddd-community-interest-candidates/1.0\nterritories: {}\n",encoding="utf-8")
            (root/"configuracion/publicaciones.yaml").write_text(
                "schema: ddd-publication-catalog/1.0\npublications: []\n",encoding="utf-8")
            (root/"inputs/MANIFEST.sha256").write_text("",encoding="utf-8")
            def fingerprint():
                return {p.relative_to(root).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in root.rglob("*") if p.is_file()}
            before=fingerprint()
            payload=build(root,"2025")
            after=fingerprint()
            self.assertEqual(before,after)
            self.assertEqual(len(payload["territories"]),1)

    def test_foundation_schemas_are_versioned(self):
        expected={
            "schemas/ddd-platform-read-model.schema.json":"ddd-platform-read-model/1.0",
            "schemas/ddd-campaign.schema.json":"ddd-campaign/1.0",
            "schemas/ddd-community-interest-policy.schema.json":"ddd-community-interest-policy/1.0",
        }
        for rel,value in expected.items():
            data=json.loads((ROOT/rel).read_text(encoding="utf-8"))
            self.assertEqual(data["properties"]["schema"]["const"],value)


if __name__=="__main__":
    unittest.main()
