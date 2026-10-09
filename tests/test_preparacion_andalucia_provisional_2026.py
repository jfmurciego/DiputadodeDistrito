from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

import yaml

from herramientas.preflight_preparacion_fuente import preflight
from herramientas.promover_catalogo_operacional import promote

ROOT = Path(__file__).resolve().parents[1]


class AndaluciaProvisionalWorkflowIntegrationTests(unittest.TestCase):
    def test_preparation_workflow_uses_common_governed_minsait_contracts(self):
        text = (ROOT / ".github/workflows/preparacion-resultados-electorales.yml").read_text(encoding="utf-8")
        contracts = yaml.safe_load(
            (ROOT / "configuracion/contratos_minsait_provisionales.yaml").read_text(encoding="utf-8")
        )["contracts"]
        self.assertIn("resolver_contrato_minsait_provisional.py", text)
        self.assertIn("adapter=minsait_provisional", text)
        self.assertIn("adaptador_minsait_csv.py", text)
        self.assertNotIn("ANDALUCIA_PROVISIONAL_SHA256", text)
        self.assertNotIn('ELECTION_ID" == "andalucia_parlamento_2026', text)
        self.assertEqual(contracts["andalucia_parlamento_2026"]["expected"]["provinces"], 8)
        self.assertEqual(contracts["andalucia_parlamento_2026"]["expected"]["polling_stations"], 10403)
        ext = contracts["extremadura_asamblea_2025-12-21"]
        self.assertEqual(ext["canonical_codauto"], "11")
        self.assertEqual(ext["expected"]["ccaa"], "10")
        self.assertEqual(ext["expected"]["provinces"], 2)
        self.assertEqual(ext["expected"]["sections"], 966)
        self.assertEqual(ext["expected"]["polling_stations"], 1400)
        self.assertEqual(ext["expected"]["candidate_votes"], 522418)
        self.assertEqual(ext["reconciliation"]["definitive"]["candidate_votes"], 524837)
        self.assertEqual(ext["reconciliation"]["delta_definitive_minus_provisional"], 2419)

    def test_provisional_package_cannot_register_in_production_path(self):
        text = (ROOT / ".github/workflows/preparacion-resultados-electorales.yml").read_text(encoding="utf-8")
        self.assertIn("production_eligible:", text)
        self.assertIn("needs.electorales.outputs.production_eligible == 'true'", text)
        self.assertIn("source_status:", text)

    def test_andalucia_can_register_package_in_working_copy_via_common_registry(self):
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
                artifact_name="ddd-electoral-package-andalucia-2025-provisional-147",
                artifact_sha256="a" * 64,
                declaration=None,
                election_id="andalucia_parlamento_2026",
                source_commit="1" * 40,
            )
            self.assertFalse(result["incorporation_enabled"])
            registered = preflight(root, "electoral", "Andalucía", "2025")
            self.assertTrue(registered["registered"])
            receipt = json.loads((root / registered["evidence_path"]).read_text(encoding="utf-8"))
            self.assertEqual(receipt["election_id"], "andalucia_parlamento_2026")
            self.assertEqual(receipt["election_date"], "2026-05-17")
            self.assertIsNone(receipt["declaration"])


if __name__ == "__main__":
    unittest.main()
