"""Trinquetes R038 v1.1.0: interfaz productiva única dentro y fuera del contenedor."""
import os
from pathlib import Path
import subprocess
import unittest

import yaml


ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS = ROOT / ".github" / "workflows"


class R038OperacionLimpia(unittest.TestCase):
    def test_workflows_territoriales_sustituidos_no_siguen_activos(self):
        retired = {
            "preparar-territorio.yml", "optimizar-territorio.yml",
            "consolidar-territorio.yml", "inventario-extremadura.yml",
            "auditar-topologia-extremadura.yml", "f104-extremadura-canonica.yml",
            "procedimiento-ddd.yml", "auditoria-integral-f1-40-controles.yml",
            "lote-autonomo-f1-auditoria-geojson.yml",
            "f106-cierre-complementario-f1.yml",
        }
        self.assertFalse(retired & {path.name for path in WORKFLOWS.glob("*.yml")})
        if os.environ.get("DDD_SKIP_LEGACY_CHECK") != "1":
            for name in retired:
                self.assertTrue((ROOT / "legacy" / "workflows" / "r038" / name).is_file())

    def test_interfaz_productiva_cubre_m01_m08_y_protege_ejecucion(self):
        text = (WORKFLOWS / "produccion-distritos.yml").read_text(encoding="utf-8")
        data = yaml.safe_load(text)
        raw_inputs = data[True]["workflow_dispatch"]["inputs"]
        self.assertEqual(list(raw_inputs), ["territory_id", "data_edition"])
        self.assertEqual(raw_inputs["territory_id"]["description"], "Territorio")
        self.assertEqual(raw_inputs["data_edition"]["description"], "Edición de datos")
        self.assertNotIn("product", raw_inputs)
        self.assertNotIn("publish_result", raw_inputs)
        self.assertNotIn("confirmar_ejecucion", raw_inputs)
        self.assertNotIn("execution_authorization:", text)
        self.assertNotIn("ensemble_promotion_authorization:", text)
        self.assertNotIn("operation:", raw_inputs)
        self.assertNotIn("from_stage:", raw_inputs)
        self.assertNotIn("to_stage:", raw_inputs)
        self.assertNotIn("checkpoint_run_id:", raw_inputs)
        self.assertIn("${{ inputs.territory_id }}", text)
        self.assertIn("producir_resultado_m01_m08", text)
        routes = (ROOT / "herramientas" / "resolver_producto_produccion.py").read_text(encoding="utf-8")
        self.assertIn('"Distritos":{"to_stage":"M06"', routes)
        self.assertIn('"Resultados electorales":{"to_stage":"M08","checkpoint_policy":"require_m06"', routes)
        self.assertIn('"Ambos":{"to_stage":"M08"', routes)
        self.assertIn("execution_confirmed: true", text)
        self.assertIn("publish_result: false", text)

    def test_lanzador_shell_compila(self):
        result = subprocess.run(
            ["bash", "-n", str(ROOT / "procedimiento.sh")],
            text=True, capture_output=True, check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_linea_comun_publica_productos_del_run(self):
        text = (WORKFLOWS / "producir-territorio-por-contrato.yml").read_text(encoding="utf-8")
        self.assertIn("steps.resolve.outputs.runs_dir", text)
        self.assertIn("--run-id \"$DDD_RUN_ID\"", text)
        self.assertIn("bash -n procedimiento.sh", text)
        self.assertIn("workflow_call", text)
        self.assertNotIn("workflow_dispatch", text)

    def test_publicacion_es_un_proceso_independiente(self):
        generation = (WORKFLOWS / "produccion-distritos.yml").read_text(encoding="utf-8")
        electoral = (WORKFLOWS / "incorporacion-resultados-electorales.yml").read_text(encoding="utf-8")
        viewer = (WORKFLOWS / "_reutilizable-publicar-sitio.yml").read_text(encoding="utf-8")
        manual = (WORKFLOWS / "desplegar-visor-publico.yml").read_text(encoding="utf-8")
        self.assertIn('publish_result: false', generation)
        self.assertNotIn('publish_result:', electoral)
        self.assertNotIn("_reutilizable-publicar-sitio.yml", electoral)
        self.assertIn("workflow_call:", viewer)
        self.assertNotIn("workflow_dispatch:", viewer)
        self.assertIn("group: ddd-pages-prod", viewer)
        self.assertIn("cancel-in-progress: false", viewer)
        self.assertIn("workflow_dispatch:", manual)
        self.assertNotIn("workflow_call:", manual)

    def test_no_queda_el_formulario_g10_sustituido(self):
        self.assertFalse((WORKFLOWS / "g10-ejecutar-tramo-certificado.yml").exists())
        if os.environ.get("DDD_SKIP_LEGACY_CHECK") != "1":
            self.assertTrue((ROOT / "legacy/workflows/local_first/g10-ejecutar-tramo-certificado_v1.1.0.yml").exists())


if __name__ == "__main__":
    unittest.main()
