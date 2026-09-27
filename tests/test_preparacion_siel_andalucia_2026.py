from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

import yaml

from herramientas.preflight_preparacion_fuente import preflight
from herramientas.promover_catalogo_operacional import promote

ROOT = Path(__file__).resolve().parents[1]


class SielAndaluciaWorkflowIntegrationTests(unittest.TestCase):
    def test_acquisition_workflow_is_internal_not_product_menu(self):
        text = (ROOT / ".github/workflows/adquirir-siel-andalucia-2026.yml").read_text(encoding="utf-8")
        self.assertIn("workflow_call:", text)
        self.assertNotIn("workflow_dispatch:", text)
        self.assertNotIn("pull_request:", text)
        self.assertIn("contents: read", text)
        self.assertNotIn("contents: write", text)
        self.assertNotIn("promover_catalogo_operacional", text)
        self.assertNotIn("git push", text)
        self.assertIn("include-hidden-files: true", text)

    def test_preparation_workflow_consumes_verified_siel_snapshot(self):
        text = (ROOT / ".github/workflows/preparacion-resultados-electorales.yml").read_text(encoding="utf-8")
        self.assertIn("codauto: {value: '${{ jobs.resolver.outputs.codauto }}'}", text)
        self.assertIn('adapter=siel_andalucia', text)
        self.assertIn('ddd-siel-andalucia-2026-snapshot', text)
        self.assertIn('candidate_votes_official":4157539', text)
        self.assertIn('"siel_election_key":202605', text)
        self.assertIn('"sections":6044', text)
        self.assertIn('"votes_consumed":False', text)
        self.assertIn('province_controls', text)
        self.assertIn('adaptador_siel_andalucia_2026.py', text)
        self.assertIn('--sections-sha256 "$sections_sha"', text)
        self.assertIn('--cera-sha256 "$cera_sha"', text)
        self.assertIn('--edition "$EDITION"', text)

    def test_andalucia_can_register_verified_package_in_working_copy_via_common_registry(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "configuracion").mkdir()
            (root / "territorios/andalucia/evidencia/catalogo").mkdir(parents=True)
            (root / "territorios/andalucia/config").mkdir(parents=True)
            (root / "territorios/andalucia/config/andalucia_2025.yaml").write_text(
                yaml.safe_dump({"modulos": {}}, sort_keys=False),
                encoding="utf-8",
            )
            catalog = {
                "schema": "ddd-preparation-catalog/1.1",
                "default_edition": "2025",
                "territories": [{
                    "territory_id": "andalucia",
                    "name": "Andalucía",
                    "editions": {"2025": {
                        "territory_declared": True,
                        "preparation_status": "READY",
                        "contract_path": "territorios/andalucia/config/andalucia_2025.yaml",
                        "territorial_source_declaration": "territorios/andalucia/config/fuentes_oficiales.yaml",
                        "electoral_source_declaration": None,
                        "territorial_sources_prepared": True,
                        "territorial_contract_complete": True,
                        "territorial_product_available": False,
                        "electoral_source_prepared": False,
                        "electoral_product_available": False,
                        "territorial_certification": "NOT_CERTIFIED",
                        "production_authorization": "AUTHORIZED",
                        "last_valid_checkpoint": None,
                    }},
                }],
            }
            registry = {
                "schema": "ddd-election-registry/1.0",
                "edition": "2025",
                "territories": {
                    "andalucia": {
                        "name": "Andalucía",
                        "election_id": "andalucia_parlamento_2026",
                        "election_date": "2026-05-17",
                        "title": "Parlamento de Andalucía 2026",
                    }
                },
            }
            (root / "configuracion/catalogo_preparacion.yaml").write_text(
                yaml.safe_dump(catalog, allow_unicode=True, sort_keys=False), encoding="utf-8"
            )
            (root / "configuracion/registro_electoral.yaml").write_text(
                yaml.safe_dump(registry, allow_unicode=True, sort_keys=False), encoding="utf-8"
            )
            result = promote(
                root_dir=root,
                kind="electoral_source",
                territory_id="andalucia",
                edition="2025",
                run_id=1472026,
                artifact_name="ddd-electoral-package-andalucia-2025-1472026",
                artifact_sha256="a" * 64,
                declaration=None,
                election_id="andalucia_parlamento_2026",
                source_commit="1" * 40,
            )
            self.assertFalse(result["incorporation_enabled"])
            registered = preflight(root, "electoral", "Andalucía", "2025")
            self.assertTrue(registered["registered"])
            self.assertEqual(registered["run_id"], 1472026)
            self.assertEqual(
                registered["artifact_name"],
                "ddd-electoral-package-andalucia-2025-1472026",
            )
            receipt = json.loads((root / registered["evidence_path"]).read_text(encoding="utf-8"))
            self.assertEqual(receipt["election_id"], "andalucia_parlamento_2026")
            self.assertEqual(receipt["election_date"], "2026-05-17")
            self.assertEqual(receipt["election_registry"], "configuracion/registro_electoral.yaml")
            self.assertIsNone(receipt["declaration"])


if __name__ == "__main__":
    unittest.main()
