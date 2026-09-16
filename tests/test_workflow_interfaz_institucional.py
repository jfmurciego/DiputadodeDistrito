"""
PROYECTO: Diputado de Distrito
PRUEBA: interfaz institucional de GitHub Actions
VERSIÓN: 1.0.2
FECHA: 2026-09-15
OBJETIVO: exigir una única interfaz territorial general, ruta institucional,
etiquetas públicas españolas y compatibilidad con los IDs técnicos vigentes.
CAMBIO: comprueba mecánicamente todos los workflow_dispatch activos para que
solo ejecucion-generacion-distritos.yml pueda exponer el formulario territorial general;
formularios manuales de diagnóstico, regresión o publicación no se confunden
con la interfaz general.
"""
from pathlib import Path
import unittest

import yaml

ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS = ROOT / ".github" / "workflows"
INTERFACE = WORKFLOWS / "ejecucion-generacion-distritos.yml"

VISIBLE_TERRITORIES = [
    "Andalucía",
    "Aragón",
    "Principado de Asturias",
    "Islas Baleares",
    "Canarias",
    "Cantabria",
    "Castilla-La Mancha",
    "Castilla y León",
    "Cataluña",
    "Comunidad Valenciana",
    "Extremadura",
    "Galicia",
    "Comunidad de Madrid",
    "Región de Murcia",
    "Comunidad Foral de Navarra",
    "País Vasco",
    "La Rioja",
    "Ceuta",
    "Melilla",
]

TECHNICAL_IDS = {
    "Andalucía": "andalucia",
    "Aragón": "aragon",
    "Principado de Asturias": "principado_de_asturias",
    "Islas Baleares": "illes_balears",
    "Canarias": "canarias",
    "Cantabria": "cantabria",
    "Castilla-La Mancha": "castilla_la_mancha",
    "Castilla y León": "castilla_y_leon",
    "Cataluña": "cataluna",
    "Comunidad Valenciana": "comunidad_valenciana",
    "Extremadura": "extremadura",
    "Galicia": "galicia",
    "Comunidad de Madrid": "madrid",
    "Región de Murcia": "region_de_murcia",
    "Comunidad Foral de Navarra": "comunidad_foral_de_navarra",
    "País Vasco": "pais_vasco",
    "La Rioja": "la_rioja",
    "Ceuta": "ceuta",
    "Melilla": "melilla",
}

VISIBLE_OPERATIONS = [
    "Admitir contrato",
    "Verificar contrato",
    "Preparar base M01–M03",
    "Diagnosticar topología",
    "Certificar territorio M01–M06",
    "Producir resultado M01–M08",
    "Generar alternativas GerryChain",
    "Publicar visor actual",
    "Controlar ejecución",
    "Resolver reutilización y estado durable",
]

VISIBLE_ENSEMBLE_STAGES = [
    "Prueba sintética",
    "Piloto Aragón — 10 alternativas",
    "Lote Aragón — 50 alternativas",
]

VISIBLE_ORCHESTRATION_PLANS = ["Prueba de orquestación", "Cierre Fase 1"]
VISIBLE_EXECUTION_ORIGINS = ["Nueva cadena desde M01", "Último checkpoint compatible"]
VISIBLE_ENSEMBLE_ORIGINS = [
    "Generar nuevas alternativas",
    "Republicar último Aragón-10 válido",
]


class WorkflowInterfaceInstitutional(unittest.TestCase):
    def _data(self):
        return yaml.safe_load(INTERFACE.read_text(encoding="utf-8")) or {}

    @staticmethod
    def _workflow_dispatch_inputs(path: Path):
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        triggers = data.get(True, data.get("on", {})) or {}
        dispatch = triggers.get("workflow_dispatch")
        if dispatch is None:
            return None
        return (dispatch or {}).get("inputs", {}) or {}

    def _dispatch_inputs(self):
        inputs = self._workflow_dispatch_inputs(INTERFACE)
        self.assertIsNotNone(inputs)
        return inputs

    def test_unica_interfaz_territorial_general_y_sin_picadora_activa(self):
        self.assertTrue(INTERFACE.is_file())
        self.assertFalse((WORKFLOWS / "picadora-territorial.yml").exists())
        self.assertFalse((WORKFLOWS / "aragon-ejecucion-integral.yml").exists())
        self.assertTrue(
            all("picadora" not in path.name.lower() for path in WORKFLOWS.glob("*.yml"))
        )

        production = (WORKFLOWS / "producir-territorio-por-contrato.yml").read_text(
            encoding="utf-8"
        )
        self.assertIn("workflow_call", production)
        self.assertNotIn("workflow_dispatch", production)

        general_interfaces = []
        for path in sorted(WORKFLOWS.glob("*.yml")):
            inputs = self._workflow_dispatch_inputs(path)
            if inputs is None:
                continue
            territory = inputs.get("territory_id", {}) or {}
            operation = inputs.get("operation", {}) or {}
            territory_options = territory.get("options", []) or []
            operation_options = operation.get("options", []) or []
            if (
                territory_options == VISIBLE_TERRITORIES
                and "Producir resultado M01–M08" in operation_options
            ):
                general_interfaces.append(path.name)

        self.assertEqual(general_interfaces, ["ejecucion-generacion-distritos.yml"])

    def test_nombres_visibles_territoriales_son_espanoles_y_canonicos(self):
        inputs = self._dispatch_inputs()
        self.assertEqual(inputs["territory_id"]["options"], VISIBLE_TERRITORIES)
        self.assertEqual(inputs["territory_id"]["default"], "La Rioja")
        self.assertIn("Islas Baleares", inputs["territory_id"]["options"])
        self.assertNotIn("illes_balears", inputs["territory_id"]["options"])

    def test_operaciones_y_fases_no_exponen_ids_tecnicos_en_el_formulario(self):
        inputs = self._dispatch_inputs()
        self.assertEqual(inputs["operation"]["options"], VISIBLE_OPERATIONS)
        self.assertEqual(inputs["operation"]["default"], "Admitir contrato")
        self.assertEqual(inputs["ensemble_stage"]["options"], VISIBLE_ENSEMBLE_STAGES)
        self.assertEqual(inputs["orchestration_plan"]["options"], VISIBLE_ORCHESTRATION_PLANS)
        self.assertEqual(inputs["execution_origin"]["options"], VISIBLE_EXECUTION_ORIGINS)
        self.assertEqual(inputs["ensemble_origin"]["options"], VISIBLE_ENSEMBLE_ORIGINS)
        self.assertLessEqual(len(inputs), 10)
        self.assertFalse(
            [name for name, definition in inputs.items() if definition.get("type") == "string"]
        )
        self.assertEqual(self._data()["name"], "Ejecucion de Generacion de Distritos")
        self.assertEqual(inputs["ensemble_stage"]["default"], "Prueba sintética")
        self.assertEqual(inputs["confirmar_ejecucion"]["type"], "boolean")
        self.assertEqual(inputs["confirmar_coste"]["type"], "boolean")
        self.assertNotIn("execution_authorization", inputs)
        self.assertNotIn("ensemble_promotion_authorization", inputs)
        self.assertNotIn("checkpoint_run_id", inputs)
        self.assertNotIn("ensemble_republish_source_run_id", inputs)

    def test_resolvedor_preserva_ids_tecnicos_territoriales(self):
        text = INTERFACE.read_text(encoding="utf-8")
        for label, technical_id in TECHNICAL_IDS.items():
            expected = f'"{label}"|{technical_id}) territory_id={technical_id} ;;'
            self.assertIn(expected, text)

        self.assertIn(
            "territorios/${{ needs.resolver_interfaz.outputs.territory_id }}/config/",
            text,
        )
        self.assertIn(
            "territory_id: ${{ needs.resolver_interfaz.outputs.territory_id }}",
            text,
        )

    def test_resolvedor_preserva_ids_tecnicos_de_operacion_y_ensemble(self):
        text = INTERFACE.read_text(encoding="utf-8")
        for technical_operation in (
            "admitir_contrato",
            "verificar_contrato",
            "preparar_base_m01_m03",
            "diagnosticar_topologia",
            "certificar_territorio_m01_m06",
            "producir_resultado_m01_m08",
            "generar_alternativas_gerrychain",
            "publicar_visor_actual",
            "controlar_ejecucion",
            "resolver_reutilizacion",
        ):
            self.assertIn(
                f"|{technical_operation}) operation={technical_operation} ;;",
                text,
            )
        for technical_stage in ("synthetic", "aragon_10", "aragon_50"):
            self.assertIn(
                f"|{technical_stage}) ensemble_stage={technical_stage} ;;",
                text,
            )

    def test_orquestacion_se_resuelve_sin_texto_y_delega_en_reutilizables(self):
        interface = INTERFACE.read_text(encoding="utf-8")
        router = (WORKFLOWS / "_reutilizable-operacion-territorial.yml").read_text(
            encoding="utf-8"
        )
        self.assertIn(
            '"Prueba de orquestación") orchestration_plan_path=orchestracion/plan_lote_g10_smoke.json',
            interface,
        )
        self.assertIn(
            '"Cierre Fase 1") orchestration_plan_path=orchestracion/plan_lote_g10_fase1_cierre.json',
            interface,
        )
        self.assertIn("uses: ./.github/workflows/orquestacion-control.yml", router)
        self.assertIn("uses: ./.github/workflows/orquestacion-durable.yml", router)
        self.assertEqual(
            router.count("uses: ./.github/workflows/producir-territorio-por-contrato.yml"),
            1,
        )

if __name__ == "__main__":
    unittest.main()
