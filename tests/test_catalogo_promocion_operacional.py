"""Regresión de promoción automática del catálogo operativo."""
import json
import tempfile
import unittest
from pathlib import Path

import yaml

from herramientas.promover_catalogo_operacional import promote


class CatalogOperationalPromotionTests(unittest.TestCase):
    def fixture(self, root: Path):
        (root / "configuracion").mkdir()
        (root / "territorios/demo/config/elecciones").mkdir(parents=True)
        (root / "configuracion/catalogo_preparacion.yaml").write_text(yaml.safe_dump({
            "schema": "ddd-preparation-catalog/1.1",
            "default_edition": "2025",
            "territories": [{
                "territory_id": "demo",
                "name": "Demo",
                "editions": {"2025": {
                    "territory_declared": True,
                    "preparation_status": "READY",
                    "contract_path": "territorios/demo/config/demo_2025.yaml",
                    "territorial_source_declaration": "territorios/demo/config/fuentes_oficiales.yaml",
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
        }, sort_keys=False), encoding="utf-8")
        decl = root / "territorios/demo/config/elecciones/demo.yaml"
        decl.write_text("schema: ddd-election-official-source-declaration/1.0\n", encoding="utf-8")
        return decl

    def test_territorial_plus_electoral_source_enables_incorporation(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            decl = self.fixture(root)
            first = promote(
                root_dir=root, kind="territorial_product", territory_id="demo", edition="2025",
                run_id=100, artifact_name="ddd-state-100-M06", artifact_sha256="a" * 64,
                decision="PASS_WITH_EXCEPTIONS", source_commit="1" * 40,
            )
            self.assertFalse(first["incorporation_enabled"])
            second = promote(
                root_dir=root, kind="electoral_source", territory_id="demo", edition="2025",
                run_id=101, artifact_name="ddd-electoral-package-demo-2025-101", artifact_sha256="b" * 64,
                declaration=str(decl.relative_to(root)), election_id="demo_2025", source_commit="2" * 40,
            )
            self.assertTrue(second["incorporation_enabled"])
            catalog = yaml.safe_load((root / "configuracion/catalogo_preparacion.yaml").read_text(encoding="utf-8"))
            state = catalog["territories"][0]["editions"]["2025"]
            self.assertTrue(state["territorial_product_available"])
            self.assertTrue(state["electoral_source_prepared"])
            self.assertEqual(state["last_valid_checkpoint"], {"run_id": 100, "stage": "M06"})
            receipt = root / state["evidence"]["electoral_source"]
            payload = json.loads(receipt.read_text(encoding="utf-8"))
            self.assertEqual(payload["artifact_name"], "ddd-electoral-package-demo-2025-101")
            self.assertFalse((root / ".github").exists())

    def test_electoral_source_alone_does_not_enable_incorporation(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            decl = self.fixture(root)
            result = promote(
                root_dir=root, kind="electoral_source", territory_id="demo", edition="2025",
                run_id=101, artifact_name="ddd-electoral-package-demo-2025-101", artifact_sha256="b" * 64,
                declaration=str(decl.relative_to(root)), election_id="demo_2025", source_commit="2" * 40,
            )
            self.assertFalse(result["incorporation_enabled"])
            catalog = yaml.safe_load((root / "configuracion/catalogo_preparacion.yaml").read_text(encoding="utf-8"))
            state = catalog["territories"][0]["editions"]["2025"]
            self.assertTrue(state["electoral_source_prepared"])
            self.assertFalse(state["territorial_product_available"])
            self.assertFalse((root / ".github").exists())

    def test_territorial_product_plus_electoral_source_enables_incorporation(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            decl = self.fixture(root)
            promote(
                root_dir=root, kind="electoral_source", territory_id="demo", edition="2025",
                run_id=101, artifact_name="ddd-electoral-package-demo-2025-101", artifact_sha256="b" * 64,
                declaration=str(decl.relative_to(root)), election_id="demo_2025", source_commit="2" * 40,
            )
            result = promote(
                root_dir=root, kind="territorial_product", territory_id="demo", edition="2025",
                run_id=100, artifact_name="ddd-state-100-M06", artifact_sha256="a" * 64,
                decision="PASS_WITH_EXCEPTIONS", source_commit="1" * 40,
            )
            self.assertTrue(result["incorporation_enabled"])
            catalog = yaml.safe_load((root / "configuracion/catalogo_preparacion.yaml").read_text(encoding="utf-8"))
            state = catalog["territories"][0]["editions"]["2025"]
            self.assertTrue(state["electoral_source_prepared"])
            self.assertTrue(state["territorial_product_available"])
            self.assertFalse((root / ".github").exists())

    def test_electoral_product_closes_catalog_state(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            self.fixture(root)
            promote(
                root_dir=root, kind="electoral_product", territory_id="demo", edition="2025",
                run_id=200, artifact_name="ddd-state-200-M08", artifact_sha256="c" * 64,
                source_commit="3" * 40,
            )
            catalog = yaml.safe_load((root / "configuracion/catalogo_preparacion.yaml").read_text(encoding="utf-8"))
            state = catalog["territories"][0]["editions"]["2025"]
            self.assertTrue(state["electoral_product_available"])
            self.assertEqual(state["last_valid_checkpoint"], {"run_id": 200, "stage": "M08"})


if __name__ == "__main__":
    unittest.main()
