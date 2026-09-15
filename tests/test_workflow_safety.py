"""
PROYECTO: Diputado de Distrito
PRUEBA: seguridad y gobierno de workflows
VERSIÓN: 1.1.0
FECHA: 2026-09-15
CAMBIO: mantiene obligatoria la ausencia de workflows sustituidos en la ruta
activa y comprueba su archivo histórico solo cuando legacy está materializado.
Dentro de la imagen reproducible sin legacy, la omisión solo se admite mediante
DDD_SKIP_LEGACY_CHECK=1, ya usado por la puerta CI tras auditar legacy en checkout.
ANTERIOR: legacy/tests/test_workflow_safety_pre_ci_container_fix_2026-09-15.py
"""
import os
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
        expected={
            "_reutilizable-promocion-m01-m03.yml":"_reutilizable-promocion-m01-m03_v1.0.0.yml",
            "exportar-aragon-flourish.yml":"exportar-aragon-flourish_v1.1.0.yml",
            "publicar-sitio.yml":"publicar-sitio_v2.2.0.yml",
        }
        for active in expected:
            self.assertFalse((WORKFLOWS/active).exists())

        if archived.is_dir():
            for historical in expected.values():
                self.assertTrue((archived/historical).is_file())
        else:
            self.assertEqual(
                os.environ.get("DDD_SKIP_LEGACY_CHECK"),
                "1",
                "legacy ausente fuera del entorno reproducible autorizado",
            )

if __name__=="__main__":unittest.main()
