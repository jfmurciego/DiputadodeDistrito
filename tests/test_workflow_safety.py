"""
PROYECTO: Diputado de Distrito
PRUEBA: seguridad y gobierno de workflows
VERSIÓN: 1.1.3
FECHA: 2026-09-16
CAMBIO: exige que los workflows G10 sean reutilizables sin botón manual,
manteniendo pull_request/push en g10-control.yml.
ANTERIOR: versión 1.1.2 en historial Git.
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

    def test_g10_no_expone_boton_manual_y_conserva_ci(self):
        control=yaml.safe_load((WORKFLOWS/"g10-control.yml").read_text(encoding="utf-8")) or {}
        control_triggers=control.get(True,control.get("on",{})) or {}
        self.assertEqual(set(control_triggers),{"pull_request","push","workflow_call"})
        self.assertNotIn("workflow_dispatch",control_triggers)
        self.assertIn("plan_path",control_triggers["workflow_call"]["inputs"])

        operate=yaml.safe_load((WORKFLOWS/"g10-operar-lote.yml").read_text(encoding="utf-8")) or {}
        operate_triggers=operate.get(True,operate.get("on",{})) or {}
        self.assertEqual(set(operate_triggers),{"workflow_call"})
        self.assertNotIn("workflow_dispatch",operate_triggers)
        self.assertIn("plan_path",operate_triggers["workflow_call"]["inputs"])

    def test_unica_ejecucion_territorial_manual_es_interfaz_institucional(self):
        production=(WORKFLOWS/"producir-territorio-por-contrato.yml").read_text(encoding="utf-8")
        self.assertIn("workflow_call",production)
        self.assertNotIn("workflow_dispatch",production)
        self.assertTrue((WORKFLOWS/"operacion-territorial.yml").is_file())

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
