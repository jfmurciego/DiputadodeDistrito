"""Trinquetes R038 v1.0.2: interfaz única dentro y fuera del contenedor."""
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
        text = (WORKFLOWS / "ejecucion-generacion-distritos.yml").read_text(encoding="utf-8")
        data = yaml.safe_load(text)
        raw_inputs = data[True]["workflow_dispatch"]["inputs"]
        operations = raw_inputs["operation"]["options"]
        self.assertEqual(operations, [
            "Admitir contrato", "Verificar contrato", "Preparar base M01–M03",
            "Diagnosticar topología", "Certificar territorio M01–M06",
            "Producir resultado M01–M08", "Generar alternativas GerryChain",
        ])
        self.assertNotIn("execution_authorization:", text)
        self.assertNotIn("ensemble_promotion_authorization:", text)
        self.assertIn("confirmar_ejecucion:", text)
        self.assertIn("confirmar_coste:", text)
        self.assertIn("${{ inputs.territory_id }}", text)
        self.assertIn("PUBLIC_PRODUCT_PUBLICATION", text)
        self.assertIn("admitir_contrato", text)
        self.assertIn("generar_alternativas_gerrychain", text)


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

    def test_operacion_general_publica_el_visor_con_el_componente_comun(self):
        operation = (WORKFLOWS / "ejecucion-generacion-distritos.yml").read_text(encoding="utf-8")
        viewer = (WORKFLOWS / "desplegar-visor-publico.yml").read_text(encoding="utf-8")
        self.assertIn("uses: ./.github/workflows/desplegar-visor-publico.yml", operation)
        self.assertIn("production_run_id: ${{ github.run_id }}", operation)
        self.assertIn("workflow_call:", viewer)
        self.assertIn("workflow_dispatch:", viewer)

    def test_no_queda_el_formulario_g10_sustituido(self):
        self.assertFalse((WORKFLOWS / "g10-ejecutar-tramo-certificado.yml").exists())
        if os.environ.get("DDD_SKIP_LEGACY_CHECK") != "1":
            self.assertTrue((ROOT / "legacy/workflows/local_first/g10-ejecutar-tramo-certificado_v1.1.0.yml").exists())


if __name__ == "__main__":
    unittest.main()
