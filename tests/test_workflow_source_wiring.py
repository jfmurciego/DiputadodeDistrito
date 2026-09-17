from __future__ import annotations

import unittest
from pathlib import Path


class WorkflowSourceWiringTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = Path('.github/workflows/producir-territorio-por-contrato.yml').read_text(encoding='utf-8')

    def test_workflow_uses_durable_source_adapter(self):
        self.assertIn('ejecutar_fuentes_workflow.py', self.text)
        self.assertIn('--checkpoint-out', self.text)
        self.assertIn('.ddd-state/out/sources', self.text)

    def test_downloader_is_not_called_directly_by_workflow(self):
        self.assertNotIn('/app/herramientas/adquirir_fuentes_oficiales.py', self.text)

    def test_checkpoint_packaging_preserves_sources(self):
        self.assertIn('cp -a .ddd-source-package/. .ddd-state/out/sources/', self.text)

    def test_resume_exposes_checkpoint_sources_to_policy(self):
        self.assertIn('.ddd-state/in/sources', self.text)
        self.assertIn('--checkpoint-in', self.text)


if __name__ == '__main__':
    unittest.main()
