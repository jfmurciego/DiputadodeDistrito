"""Trinquetes R038 v1.0.1: interfaz única dentro y fuera del contenedor."""
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


    def test_interfaz_institucional_cubre_m01_m08_y_protege_ejecucion(self):
        text = (WORKFLOWS / "picadora-territorial.yml").read_text(encoding="utf-8")
        data = yaml.safe_load(text)
        raw_inputs = data[True]["workflow_dispatch"]["inputs"]
        operations = raw_inputs["operation"]["options"]
        self.assertEqual(operations, [
            "admitir_contrato", "verificar_contrato", "preparar_base_m01_m03",
            "diagnosticar_topologia", "certificar_territorio_m01_m06",
            "producir_resultado_m01_m08", "generar_alternativas_gerrychain",
        ])
        self.assertIn("EXECUTE_WITH_EXPLICIT_USER_AUTHORIZATION", text)
        self.assertIn("${{ inputs.territory_id }}", text)
        self.assertIn("PUBLIC_PRODUCT_PUBLICATION", text)


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

    def test_no_queda_el_formulario_g10_sustituido(self):
        self.assertFalse((WORKFLOWS / "g10-ejecutar-tramo-certificado.yml").exists())
        if os.environ.get("DDD_SKIP_LEGACY_CHECK") != "1":
            self.assertTrue((ROOT / "legacy/workflows/local_first/g10-ejecutar-tramo-certificado_v1.1.0.yml").exists())


if __name__ == "__main__":
    unittest.main()
