"""
PROYECTO: Diputado de Distrito
PRUEBA: interfaz productiva empresarial de GitHub Actions
VERSIÓN: 2.1.0
FECHA: 2026-09-17
OBJETIVO: exigir cuatro controles humanos, resolución automática del recorrido y
encadenamiento hacia la producción modular sin exponer parámetros técnicos.
CAMBIO: el checkpoint automático debe superar la puerta común de reutilización,
registrar descartes y conservar los identificadores internos resolver_interfaz/ruta.
"""
from pathlib import Path
import unittest

import yaml

ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS = ROOT / ".github" / "workflows"
INTERFACE = WORKFLOWS / "produccion-distritos.yml"
ROUTER = WORKFLOWS / "_reutilizable-operacion-territorial.yml"
PRODUCTION = WORKFLOWS / "producir-territorio-por-contrato.yml"

VISIBLE_TERRITORIES = ["Aragón", "Castilla y León"]

TECHNICAL_IDS = {"Aragón": "aragon", "Castilla y León": "castilla_y_leon"}


class WorkflowInterfaceInstitutional(unittest.TestCase):
    @staticmethod
    def _load(path: Path):
        return yaml.safe_load(path.read_text(encoding="utf-8")) or {}

    @classmethod
    def _dispatch_inputs(cls, path=INTERFACE):
        data = cls._load(path)
        triggers = data.get(True, data.get("on", {})) or {}
        dispatch = triggers.get("workflow_dispatch")
        if dispatch is None:
            return None
        return (dispatch or {}).get("inputs", {}) or {}

    def test_unica_interfaz_territorial_general(self):
        self.assertTrue(INTERFACE.is_file())
        self.assertFalse((WORKFLOWS / "picadora-territorial.yml").exists())
        self.assertFalse((WORKFLOWS / "aragon-ejecucion-integral.yml").exists())
        general = []
        for path in sorted(WORKFLOWS.glob("*.yml")):
            inputs = self._dispatch_inputs(path)
            if inputs is None:
                continue
            territory = inputs.get("territory_id", {}) or {}
            if territory.get("options", []) == VISIBLE_TERRITORIES:
                general.append(path.name)
        self.assertEqual(general, ["ejecucion-generacion-distritos.yml"])

    def test_formulario_productivo_tiene_exactamente_cuatro_controles(self):
        inputs = self._dispatch_inputs()
        self.assertEqual(list(inputs), [
            "territory_id", "data_edition", "publish_result", "confirmar_ejecucion"
        ])
        self.assertEqual(inputs["territory_id"]["description"], "Territorio")
        self.assertEqual(inputs["data_edition"]["description"], "Edición de datos")
        self.assertEqual(inputs["publish_result"]["description"], "Publicar resultado")
        self.assertEqual(inputs["confirmar_ejecucion"]["description"], "Confirmar ejecución")
        self.assertEqual(inputs["territory_id"]["options"], VISIBLE_TERRITORIES)
        self.assertEqual(inputs["data_edition"]["options"], ["2025"])
        self.assertEqual(inputs["publish_result"]["type"], "boolean")
        self.assertEqual(inputs["confirmar_ejecucion"]["type"], "boolean")
        forbidden = {
            "operation", "from_stage", "to_stage", "execution_origin", "checkpoint_run_id",
            "ensemble_stage", "confirmar_coste", "ensemble_origin", "orchestration_plan",
            "execution_authorization", "ensemble_promotion_authorization",
        }
        self.assertFalse(forbidden.intersection(inputs))
        self.assertEqual(self._load(INTERFACE)["name"], "Producción de distritos")

    def test_resolucion_territorial_y_contrato_dependen_solo_de_configuracion(self):
        text = INTERFACE.read_text(encoding="utf-8")
        self.assertIn("herramientas/catalogo_preparacion.py resolve --mode production", text)
        self.assertIn("contract_path", text)
        self.assertNotIn("case \"$UI_TERRITORY\"", text)


    def test_publicacion_resuelve_el_recorrido_sin_control_tecnico(self):
        text = INTERFACE.read_text(encoding="utf-8")
        self.assertIn('if [[ "$UI_PUBLISH" == true ]]; then to_stage=M08; else to_stage=M07; fi', text)
        self.assertIn('from_stage=M01', text)
        self.assertIn('target_num="$((10#${TO_STAGE#M}))"', text)
        self.assertIn('from_stage="M$(printf \'%02d\' "$((stage_num+1))")"', text)

    def test_checkpoint_automatico_valida_paquete_completo_y_registra_descartes(self):
        text = INTERFACE.read_text(encoding="utf-8")
        self.assertIn('ddd-decision-$run_id', text)
        self.assertIn('ddd-state-$run_id-$stage', text)
        self.assertIn("'.territory_id // empty'", text)
        self.assertIn("'.params // empty'", text)
        self.assertIn("*/sources/manifest.json", text)
        self.assertIn("python -m herramientas.seleccionar_checkpoint_productivo", text)
        self.assertIn("checkpoints_descartados.json", text)
        self.assertIn("ddd-checkpoint-selection-${{ github.run_id }}", text)
        self.assertIn("sort_by(.created_at) | reverse", text)
        self.assertNotIn("adquirir_fuentes_oficiales", text)
        self.assertNotIn("inputs.checkpoint_run_id", text)

    def test_encadenamiento_productivo_es_automatico_y_mantiene_confirmacion_humana(self):
        data = self._load(INTERFACE)
        self.assertEqual(list(data["jobs"]), ["resolver_interfaz", "ruta"])
        job = data["jobs"]["ruta"]
        self.assertEqual(job["name"], "Procesar territorio")
        self.assertEqual(job["uses"], "./.github/workflows/_reutilizable-operacion-territorial.yml")
        values = job["with"]
        self.assertEqual(values["operation"], "producir_resultado_m01_m08")
        self.assertIn("needs.resolver_interfaz.outputs.params", values["params"])
        self.assertIn("needs.resolver_interfaz.outputs.from_stage", values["from_stage"])
        self.assertIn("needs.resolver_interfaz.outputs.to_stage", values["to_stage"])
        self.assertIn("needs.resolver_interfaz.outputs.checkpoint_run_id", values["checkpoint_run_id"])
        self.assertIn("inputs.confirmar_ejecucion", values["execution_confirmed"])

    def test_secuencia_visible_usa_nombres_de_negocio_y_conserva_m01_m08(self):
        router = self._load(ROUTER)
        self.assertEqual(
            router["jobs"]["produccion"]["name"],
            "Fuentes, procesamiento, controles, distritos, resultados y publicación",
        )
        self.assertEqual(router["jobs"]["informe_ejecucion"]["name"], "Informe de ejecución")
        production_text = PRODUCTION.read_text(encoding="utf-8")
        for stage in ("m01:", "m02:", "m03:", "m04:", "m05:", "m06:", "m07:", "m08:"):
            self.assertIn(stage, production_text)
        self.assertIn("official_sources:", production_text)
        self.assertIn("auditoria:", production_text)
        self.assertIn("electoral_source:", production_text)
        self.assertIn("visor:", production_text)
        self.assertEqual(
            ROUTER.read_text(encoding="utf-8").count(
                "uses: ./.github/workflows/producir-territorio-por-contrato.yml"
            ),
            1,
        )


if __name__ == "__main__":
    unittest.main()
