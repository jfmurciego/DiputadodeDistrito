from __future__ import annotations

import importlib.util
from pathlib import Path
import unittest

import yaml

ROOT = Path(__file__).resolve().parents[1]
ADAPTER = ROOT / "herramientas/adaptador_eleccionesdb.py"


def load_adapter():
    spec = importlib.util.spec_from_file_location("ddd_eleccionesdb_guard", ADAPTER)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


class EleccionesDBProvisionalGuard(unittest.TestCase):
    def test_extremadura_provisional_is_not_promoted_as_verified_election(self):
        adapter = load_adapter()
        self.assertNotIn("extremadura_asamblea_2025-12-21", adapter.ELECTIONS)

    def test_extremadura_provisional_is_governed_but_not_selectable(self):
        declaration = yaml.safe_load(
            (ROOT / "territorios/extremadura/config/elecciones/fuentes_oficiales_2025.yaml").read_text(encoding="utf-8")
        )
        evidence = declaration["provisional_evidence"]
        self.assertEqual(evidence["status"], "PROVISIONAL")
        self.assertFalse(evidence["promotion_allowed"])
        self.assertEqual(evidence["sha256"], "d09a4ad4be094f230ed84e17160fbfc801f5d0c2f51e3d931073a06cc094003d")
        self.assertEqual(evidence["sections"], 966)
        self.assertEqual(evidence["candidate_votes"], 522418)
        self.assertEqual(evidence["definitive_reference"]["candidate_votes"], 524837)
        self.assertEqual(evidence["delta_definitive_minus_provisional"], 2419)
        selectable_urls = {str(x.get("url") or "") for x in declaration.get("sources") or []}
        self.assertNotIn(evidence["url"], selectable_urls)


if __name__ == "__main__":
    unittest.main()
