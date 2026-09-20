from __future__ import annotations

import unittest
from pathlib import Path


class WorkflowSourceWiringTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = Path('.github/workflows/producir-territorio-por-contrato.yml').read_text(encoding='utf-8')

    def test_workflow_uses_durable_source_adapter(self):
        self.assertIn('-m herramientas.ejecutar_fuentes_workflow', self.text)
        self.assertNotIn('/app/herramientas/ejecutar_fuentes_workflow.py', self.text)
        self.assertIn('--checkpoint-out', self.text)
        self.assertIn('.ddd-state/out/sources', self.text)

    def test_downloader_is_not_called_directly_by_workflow(self):
        self.assertNotIn('/app/herramientas/adquirir_fuentes_oficiales.py', self.text)

    def test_checkpoint_packaging_preserves_sources(self):
        self.assertIn('cp -a .ddd-source-package/. .ddd-state/out/sources/', self.text)

    def test_resume_exposes_checkpoint_sources_to_policy(self):
        self.assertIn('.ddd-state/in/sources', self.text)
        self.assertIn('--checkpoint-in', self.text)

    def test_prepared_source_identifiers_are_wired_into_official_sources_job(self):
        self.assertIn("SOURCE_PACKAGE_RUN_ID: ${{ inputs.source_package_run_id }}", self.text)
        self.assertIn("SOURCE_PACKAGE_ARTIFACT_NAME: ${{ inputs.source_package_artifact_name }}", self.text)
        recover = self.text.index("name: Recuperar datos territoriales preparados")
        run_ref = self.text.index('gh run download "$SOURCE_PACKAGE_RUN_ID"', recover)
        artifact_ref = self.text.index('"$SOURCE_PACKAGE_ARTIFACT_NAME"', recover)
        self.assertGreater(run_ref, recover)
        self.assertGreater(artifact_ref, recover)


if __name__ == '__main__':
    unittest.main()
