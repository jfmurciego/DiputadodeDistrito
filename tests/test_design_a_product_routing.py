from pathlib import Path
import unittest
import yaml

ROOT=Path(__file__).resolve().parents[1]
GEN=ROOT/".github/workflows/produccion-distritos.yml"
ELECTORAL=ROOT/".github/workflows/incorporacion-resultados-electorales.yml"
ROUTER=ROOT/".github/workflows/_reutilizable-operacion-territorial.yml"
ENGINE=ROOT/".github/workflows/producir-territorio-por-contrato.yml"

def load(path):
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}

def inputs(path):
    d=load(path); t=d.get("on") or d.get(True)
    return t["workflow_dispatch"]["inputs"]

class ProductRoutingDesignA(unittest.TestCase):
    def test_generation_form_has_only_territory_and_edition(self):
        self.assertEqual(list(inputs(GEN)),["territory_id","data_edition"])

    def test_electoral_incorporation_form_has_only_territory_and_edition(self):
        self.assertEqual(list(inputs(ELECTORAL)),["territory_id","data_edition"])

    def test_generation_is_fixed_to_districts_and_auto_publishes(self):
        text=GEN.read_text(encoding="utf-8")
        self.assertIn("UI_PRODUCT: Distritos",text)
        self.assertIn("execution_confirmed: true",text)
        self.assertIn("publish_result: true",text)
        self.assertNotIn("inputs.product",text)
        self.assertNotIn("inputs.publish_result",text)
        self.assertNotIn("inputs.confirmar_ejecucion",text)
        self.assertNotIn("Resolver paquete electoral preparado",text)

    def test_electoral_incorporation_is_fixed_to_results_and_auto_publishes(self):
        text=ELECTORAL.read_text(encoding="utf-8")
        self.assertIn("UI_PRODUCT: Resultados electorales",text)
        self.assertIn("execution_confirmed: true",text)
        self.assertIn("publish_result: true",text)
        self.assertIn("Resultados electorales requiere un checkpoint M06 válido",text)
        self.assertIn("Resolver paquete electoral preparado",text)

    def test_publication_still_targets_the_visor(self):
        router=load(ROUTER); engine=load(ENGINE)
        rt=(router.get("on") or router.get(True))["workflow_call"]["inputs"]
        en=(engine.get("on") or engine.get(True))["workflow_call"]["inputs"]
        self.assertIn("publish_result",rt); self.assertIn("publish_result",en)
        visor=engine["jobs"]["visor"]
        self.assertIn("inputs.publish_result == true",visor["if"])
        self.assertIn("needs.m06.result == 'success'",visor["if"])
        self.assertIn("needs.m08.result == 'success'",visor["if"])

    def test_engine_remains_single_reusable_chain(self):
        for ui_path in (GEN,ELECTORAL):
            ui=load(ui_path)
            self.assertEqual(ui["jobs"]["ruta"]["uses"],"./.github/workflows/_reutilizable-operacion-territorial.yml")
        router=load(ROUTER); engine=load(ENGINE)
        self.assertEqual(router["jobs"]["produccion"]["uses"],"./.github/workflows/producir-territorio-por-contrato.yml")
        self.assertIn("workflow_call",engine.get("on") or engine.get(True))
        for stage in range(1,9): self.assertIn(f"m{stage:02d}",engine["jobs"])

if __name__=="__main__": unittest.main()
