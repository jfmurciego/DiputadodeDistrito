from pathlib import Path
import unittest
import yaml

ROOT=Path(__file__).resolve().parents[1]
UI=ROOT/".github/workflows/produccion-distritos.yml"
ROUTER=ROOT/".github/workflows/_reutilizable-operacion-territorial.yml"
ENGINE=ROOT/".github/workflows/producir-territorio-por-contrato.yml"

def load(path):
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}

class ProductRoutingDesignA(unittest.TestCase):
    def test_form_has_business_product_only(self):
        d=load(UI); t=d.get("on") or d.get(True); inputs=t["workflow_dispatch"]["inputs"]
        self.assertEqual(list(inputs),["territory_id","data_edition","product","publish_result","confirmar_ejecucion"])
        self.assertEqual(inputs["product"]["options"],["Distritos","Resultados electorales","Ambos"])
        forbidden={"from_stage","to_stage","checkpoint_run_id","run_id","operation","mode"}
        self.assertFalse(forbidden.intersection(inputs))

    def test_product_is_only_stage_selector(self):
        text=UI.read_text(encoding="utf-8")
        routes=(ROOT/"herramientas/resolver_producto_produccion.py").read_text(encoding="utf-8")
        self.assertIn("resolver_producto_produccion.py --product",text)
        self.assertIn('"Distritos":{"to_stage":"M06"',routes)
        self.assertIn('"Resultados electorales":{"to_stage":"M08","checkpoint_policy":"require_m06"',routes)
        self.assertIn('"Ambos":{"to_stage":"M08"',routes)
        self.assertNotIn("UI_PUBLISH",text)

    def test_electoral_is_fail_closed_on_missing_m06(self):
        text=UI.read_text(encoding="utf-8")
        self.assertIn("search_from=6",text)
        self.assertIn("search_to=6",text)
        self.assertIn("Resultados electorales requiere un checkpoint M06 válido",text)
        self.assertIn("exit 44",text)

    def test_publication_is_forwarded_after_product(self):
        ui=load(UI); router=load(ROUTER); engine=load(ENGINE)
        self.assertEqual(ui["jobs"]["ruta"]["with"]["publish_result"],"${{ inputs.publish_result }}")
        rt=(router.get("on") or router.get(True))["workflow_call"]["inputs"]
        en=(engine.get("on") or engine.get(True))["workflow_call"]["inputs"]
        self.assertIn("publish_result",rt); self.assertIn("publish_result",en)
        self.assertEqual(router["jobs"]["produccion"]["with"]["publish_result"],"${{ inputs.publish_result }}")
        visor=engine["jobs"]["visor"]
        self.assertIn("inputs.publish_result == true",visor["if"])
        self.assertIn("needs.m06.result == 'success'",visor["if"])
        self.assertIn("needs.m08.result == 'success'",visor["if"])

    def test_engine_remains_single_reusable_chain(self):
        ui=load(UI); router=load(ROUTER); engine=load(ENGINE)
        self.assertEqual(ui["jobs"]["ruta"]["uses"],"./.github/workflows/_reutilizable-operacion-territorial.yml")
        self.assertEqual(router["jobs"]["produccion"]["uses"],"./.github/workflows/producir-territorio-por-contrato.yml")
        self.assertIn("workflow_call",engine.get("on") or engine.get(True))
        for stage in range(1,9): self.assertIn(f"m{stage:02d}",engine["jobs"])

if __name__=="__main__": unittest.main()
