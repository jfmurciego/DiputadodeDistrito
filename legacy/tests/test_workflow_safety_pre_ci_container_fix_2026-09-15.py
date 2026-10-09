"""Contrato: cálculo pesado y publicación solo bajo orden manual."""
from pathlib import Path
import unittest
import yaml

ROOT=Path(__file__).resolve().parents[1]
WORKFLOWS=ROOT/".github/workflows"

class WorkflowSafety(unittest.TestCase):
    MANUAL_ONLY={
        "auditar-robustez-semillas-aragon.yml",
        "desplegar-visor-publico.yml",
        "regresion-m06-aragon.yml",
        "regresion-m06-castilla-y-leon.yml",
    }

    def test_pesados_y_publicaciones_no_tienen_disparador_automatico(self):
        for name in self.MANUAL_ONLY:
            data=yaml.safe_load((WORKFLOWS/name).read_text(encoding="utf-8")) or {}
            triggers=data.get(True,data.get("on",{})) or {}
            self.assertEqual(set(triggers),{"workflow_dispatch"},name)

    def test_unica_ejecucion_territorial_manual_es_interfaz_institucional(self):
        production=(WORKFLOWS/"producir-territorio-por-contrato.yml").read_text(encoding="utf-8")
        self.assertIn("workflow_call",production)
        self.assertNotIn("workflow_dispatch",production)
        self.assertTrue((WORKFLOWS/"picadora-territorial.yml").is_file())

    def test_workflows_sustituidos_estan_archivados(self):
        archived=ROOT/"legacy/workflows/cleanup_2026-09-14"
        for active, historical in {
            "_reutilizable-promocion-m01-m03.yml":"_reutilizable-promocion-m01-m03_v1.0.0.yml",
            "exportar-aragon-flourish.yml":"exportar-aragon-flourish_v1.1.0.yml",
            "publicar-sitio.yml":"publicar-sitio_v2.2.0.yml",
        }.items():
            self.assertFalse((WORKFLOWS/active).exists())
            self.assertTrue((archived/historical).is_file())

if __name__=="__main__":unittest.main()
