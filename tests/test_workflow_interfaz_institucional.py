"""
PROYECTO: Diputado de Distrito
PRUEBA: interfaz institucional de GitHub Actions
VERSIÓN: 1.1.0
FECHA: 2026-09-15
OBJETIVO: exigir una única interfaz territorial general, etiquetas públicas españolas,
compatibilidad con IDs técnicos y publicación explícita de evidencia visual M06.
"""
from pathlib import Path
import unittest

import yaml

ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS = ROOT / ".github" / "workflows"
INTERFACE = WORKFLOWS / "operacion-territorial.yml"

VISIBLE_TERRITORIES = [
    "Andalucía", "Aragón", "Principado de Asturias", "Islas Baleares",
    "Canarias", "Cantabria", "Castilla-La Mancha", "Castilla y León",
    "Cataluña", "Comunidad Valenciana", "Extremadura", "Galicia",
    "Comunidad de Madrid", "Región de Murcia", "Comunidad Foral de Navarra",
    "País Vasco", "La Rioja", "Ceuta", "Melilla",
]

TECHNICAL_IDS = {
    "Andalucía": "andalucia", "Aragón": "aragon",
    "Principado de Asturias": "principado_de_asturias", "Islas Baleares": "illes_balears",
    "Canarias": "canarias", "Cantabria": "cantabria",
    "Castilla-La Mancha": "castilla_la_mancha", "Castilla y León": "castilla_y_leon",
    "Cataluña": "cataluna", "Comunidad Valenciana": "comunidad_valenciana",
    "Extremadura": "extremadura", "Galicia": "galicia", "Comunidad de Madrid": "madrid",
    "Región de Murcia": "region_de_murcia", "Comunidad Foral de Navarra": "comunidad_foral_de_navarra",
    "País Vasco": "pais_vasco", "La Rioja": "la_rioja", "Ceuta": "ceuta", "Melilla": "melilla",
}

VISIBLE_OPERATIONS = [
    "Admitir contrato", "Verificar contrato", "Preparar base M01–M03",
    "Diagnosticar topología", "Certificar territorio M01–M06",
    "Producir resultado M01–M08", "Publicar evidencia M06 existente",
    "Generar alternativas GerryChain",
]

VISIBLE_ENSEMBLE_STAGES = [
    "Prueba sintética", "Piloto Aragón — 10 alternativas", "Lote Aragón — 50 alternativas",
]


class WorkflowInterfaceInstitutional(unittest.TestCase):
    def _data(self):
        return yaml.safe_load(INTERFACE.read_text(encoding="utf-8")) or {}

    def _dispatch_inputs(self):
        data = self._data()
        triggers = data.get(True, data.get("on", {})) or {}
        return triggers["workflow_dispatch"]["inputs"]

    def test_unica_interfaz_territorial_general_y_sin_picadora_activa(self):
        self.assertTrue(INTERFACE.is_file())
        self.assertFalse((WORKFLOWS / "picadora-territorial.yml").exists())
        self.assertTrue(all("picadora" not in path.name.lower() for path in WORKFLOWS.glob("*.yml")))
        production = (WORKFLOWS / "producir-territorio-por-contrato.yml").read_text(encoding="utf-8")
        self.assertIn("workflow_call", production)
        self.assertNotIn("workflow_dispatch", production)

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
        self.assertEqual(inputs["ensemble_stage"]["default"], "Prueba sintética")
        self.assertIn("source_run_id", inputs)

    def test_resolvedor_preserva_ids_tecnicos_territoriales(self):
        text = INTERFACE.read_text(encoding="utf-8")
        for label, technical_id in TECHNICAL_IDS.items():
            expected = f'"{label}"|{technical_id}) territory_id={technical_id} ;;'
            self.assertIn(expected, text)
        self.assertIn("territorios/${{ needs.resolver_interfaz.outputs.territory_id }}/config/", text)
        self.assertIn("territory_id: ${{ needs.resolver_interfaz.outputs.territory_id }}", text)

    def test_resolvedor_preserva_ids_tecnicos_de_operacion_y_ensemble(self):
        text = INTERFACE.read_text(encoding="utf-8")
        for technical_operation in (
            "admitir_contrato", "verificar_contrato", "preparar_base_m01_m03",
            "diagnosticar_topologia", "certificar_territorio_m01_m06",
            "producir_resultado_m01_m08", "publicar_evidencia_m06",
            "generar_alternativas_gerrychain",
        ):
            self.assertIn(f"|{technical_operation}) operation={technical_operation} ;;", text)
        for technical_stage in ("synthetic", "aragon_10", "aragon_50"):
            self.assertIn(f"|{technical_stage}) ensemble_stage={technical_stage} ;;", text)

    def test_publicacion_m06_usa_workflow_reutilizable(self):
        text = INTERFACE.read_text(encoding="utf-8")
        self.assertIn("_reutilizable-publicar-evidencia-m06.yml", text)
        self.assertIn("source_run_id: ${{ inputs.source_run_id }}", text)
        self.assertIn("source_run_id: ${{ github.run_id }}", text)


if __name__ == "__main__":
    unittest.main()
