"""
PROYECTO: Diputado de Distrito
PRUEBA: seguridad y gobierno de workflows
VERSIÓN: 1.1.2
FECHA: 2026-09-15
CAMBIO: actualiza la referencia de la interfaz territorial principal tras su
renombrado institucional a ejecucion-generacion-distritos.yml, sin alterar el resto de
controles de seguridad y gobierno.
ANTERIOR: versión 1.1.1 en historial Git.
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
        "regresion-m06-aragon.yml",
        "regresion-m06-castilla-y-leon.yml",
    }

    def test_pesados_y_publicaciones_no_tienen_disparador_automatico(self):
        for name in self.MANUAL_ONLY:
            data=yaml.safe_load((WORKFLOWS/name).read_text(encoding="utf-8")) or {}
            triggers=data.get(True,data.get("on",{})) or {}
            self.assertEqual(set(triggers),{"workflow_dispatch"},name)

        viewer=yaml.safe_load((WORKFLOWS/"desplegar-visor-publico.yml").read_text(encoding="utf-8")) or {}
        viewer_triggers=viewer.get(True,viewer.get("on",{})) or {}
        self.assertEqual(set(viewer_triggers),{"workflow_call","workflow_dispatch"})

    def test_unica_ejecucion_territorial_manual_es_interfaz_institucional(self):
        production=(WORKFLOWS/"producir-territorio-por-contrato.yml").read_text(encoding="utf-8")
        self.assertIn("workflow_call",production)
        self.assertNotIn("workflow_dispatch",production)
        self.assertTrue((WORKFLOWS/"ejecucion-generacion-distritos.yml").is_file())

    def test_produccion_aplica_politica_geometrica_y_preserva_excepciones(self):
        production=(WORKFLOWS/"producir-territorio-por-contrato.yml").read_text(encoding="utf-8")
        self.assertIn('continuidad_geometrica_{year}.json', production)
        self.assertIn('policy_args=(--policy "/app/$policy")', production)
        self.assertIn('GEOMETRIC_DECISION: ${{ steps.geometric.outputs.decision }}', production)
        self.assertIn('"PASS_WITH_EXCEPTIONS"', production)

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
