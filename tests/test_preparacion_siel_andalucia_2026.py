from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class SielAndaluciaWorkflowIntegrationTests(unittest.TestCase):
    def test_acquisition_workflow_is_internal_not_product_menu(self):
        text = (ROOT / ".github/workflows/adquirir-siel-andalucia-2026.yml").read_text(encoding="utf-8")
        self.assertIn("workflow_call:", text)
        self.assertNotIn("workflow_dispatch:", text)
        self.assertNotIn("pull_request:", text)

    def test_preparation_workflow_consumes_verified_siel_snapshot(self):
        text = (ROOT / ".github/workflows/preparacion-resultados-electorales.yml").read_text(encoding="utf-8")
        self.assertIn('adapter=siel_andalucia', text)
        self.assertIn('ddd-siel-andalucia-2026-snapshot', text)
        self.assertIn('candidate_votes_official":4157539', text)
        self.assertIn('province_controls', text)
        self.assertIn('adaptador_siel_andalucia_2026.py', text)
        self.assertIn('--sections-sha256 "$sections_sha"', text)
        self.assertIn('--cera-sha256 "$cera_sha"', text)
        self.assertIn('--edition "$EDITION"', text)


if __name__ == "__main__":
    unittest.main()
