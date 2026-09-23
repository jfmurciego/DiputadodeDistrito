"""
PROYECTO: Diputado de Distrito
PRUEBA: seguridad y gobierno de workflows
VERSIÓN: 1.3.0
FECHA: 2026-09-16
CAMBIO: mantiene las puertas CI automáticas y permite un publicador web manual
separado de toda ejecución territorial.
ANTERIOR: versión 1.2.1 en historial Git.
"""
import os
from pathlib import Path
import unittest
import yaml

ROOT=Path(__file__).resolve().parents[1]
WORKFLOWS=ROOT/".github/workflows"

class WorkflowSafety(unittest.TestCase):
    ARCHIVED_MANUAL={
        "auditar-robustez-semillas-aragon.yml":"auditar-robustez-semillas-aragon_v1.1.0.yml",
        "regresion-m06-aragon.yml":"regresion-m06-aragon_v1.6.1.yml",
        "regresion-m06-castilla-y-leon.yml":"regresion-m06-castilla-y-leon_v1.3.0.yml",
    }
    AUTOMATIC_ONLY={
        "pruebas-plataforma.yml":{"push","pull_request"},
        "validar-contratos-territoriales.yml":{"push","pull_request"},
        "validar-productos-publicos.yml":{"push"},
    }

    def test_pesados_archivados_y_ci_sin_boton_manual(self):
        archived=ROOT/"legacy/workflows/consolidacion-interfaz"
        for active in self.ARCHIVED_MANUAL:
            self.assertFalse((WORKFLOWS/active).exists(),active)

        if archived.is_dir():
            for historical in self.ARCHIVED_MANUAL.values():
                self.assertTrue((archived/historical).is_file(),historical)
        else:
            self.assertEqual(
                os.environ.get("DDD_SKIP_LEGACY_CHECK"),
                "1",
                "legacy ausente fuera del entorno reproducible autorizado",
            )

        for name,required in self.AUTOMATIC_ONLY.items():
            data=yaml.safe_load((WORKFLOWS/name).read_text(encoding="utf-8")) or {}
            triggers=data.get(True,data.get("on",{})) or {}
            trigger_names=set(triggers)
            self.assertNotIn("workflow_dispatch",trigger_names,name)
            self.assertTrue(required.issubset(trigger_names),name)

        viewer=yaml.safe_load((WORKFLOWS/"desplegar-visor-publico.yml").read_text(encoding="utf-8")) or {}
        viewer_triggers=viewer.get(True,viewer.get("on",{})) or {}
        self.assertEqual(set(viewer_triggers),{"workflow_call","workflow_dispatch"})
        manual_inputs=viewer_triggers["workflow_dispatch"]["inputs"]
        self.assertEqual(set(manual_inputs),{"pagina_publicar","production_run_id"})
        self.assertEqual(manual_inputs["pagina_publicar"]["type"],"choice")
        self.assertEqual(manual_inputs["production_run_id"]["type"],"string")
        self.assertFalse(manual_inputs["production_run_id"]["required"])
        self.assertEqual(
            manual_inputs["pagina_publicar"]["options"],
            ["Dashboard operativo","Visor territorial","Sitio completo"],
        )
        reusable=yaml.safe_load((WORKFLOWS/"_reutilizable-publicar-sitio.yml").read_text(encoding="utf-8")) or {}
        reusable_triggers=reusable.get(True,reusable.get("on",{})) or {}
        self.assertEqual(set(reusable_triggers),{"workflow_call"})

    def test_orquestacion_no_expone_boton_manual_y_conserva_ci(self):
        self.assertFalse((WORKFLOWS/"g10-control.yml").exists())
        self.assertFalse((WORKFLOWS/"g10-operar-lote.yml").exists())

        control_path=WORKFLOWS/"orquestacion-control.yml"
        durable_path=WORKFLOWS/"orquestacion-durable.yml"
        self.assertTrue(control_path.is_file())
        self.assertTrue(durable_path.is_file())

        control=yaml.safe_load(control_path.read_text(encoding="utf-8")) or {}
        control_triggers=control.get(True,control.get("on",{})) or {}
        self.assertEqual(set(control_triggers),{"pull_request","push","workflow_call"})
        self.assertNotIn("workflow_dispatch",control_triggers)
        self.assertIn("plan_path",control_triggers["workflow_call"]["inputs"])
        self.assertEqual(control.get("name"),"Controlar Ejecución")

        durable=yaml.safe_load(durable_path.read_text(encoding="utf-8")) or {}
        durable_triggers=durable.get(True,durable.get("on",{})) or {}
        self.assertEqual(set(durable_triggers),{"workflow_call"})
        self.assertNotIn("workflow_dispatch",durable_triggers)
        self.assertIn("plan_path",durable_triggers["workflow_call"]["inputs"])
        self.assertEqual(durable.get("name"),"Resolver Reutilización y Estado Durable")

    def test_unica_ejecucion_territorial_manual_es_interfaz_institucional(self):
        production=(WORKFLOWS/"producir-territorio-por-contrato.yml").read_text(encoding="utf-8")
        self.assertIn("workflow_call",production)
        self.assertNotIn("workflow_dispatch",production)
        self.assertTrue((WORKFLOWS/"produccion-distritos.yml").is_file())

    def test_produccion_aplica_politica_geometrica_y_preserva_excepciones(self):
        production=(WORKFLOWS/"producir-territorio-por-contrato.yml").read_text(encoding="utf-8")
        state_builder=(ROOT/"herramientas/estado_produccion.py").read_text(encoding="utf-8")
        self.assertIn('continuidad_geometrica_{year}.json', production)
        self.assertIn('policy_args=(--policy "/app/$policy")', production)
        self.assertIn('GEOMETRIC_DECISION: ${{ steps.geometric.outputs.decision }}', production)
        self.assertIn('"PASS_WITH_EXCEPTIONS"', state_builder)
        self.assertIn("geometric_exceptions_causally_governed", state_builder)

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
                self.assertTrue((archived/historical).is_file(),historical)
        else:
            self.assertEqual(
                os.environ.get("DDD_SKIP_LEGACY_CHECK"),
                "1",
                "legacy ausente fuera del entorno reproducible autorizado",
            )

if __name__=="__main__":unittest.main()
