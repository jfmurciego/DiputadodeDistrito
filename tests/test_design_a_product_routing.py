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

    def test_generation_is_fixed_to_districts_without_auto_publish(self):
        text=GEN.read_text(encoding="utf-8")
        self.assertIn("UI_PRODUCT: Distritos",text)
        self.assertIn("execution_authorization: EXECUTE_WITH_EXPLICIT_USER_AUTHORIZATION",text)
        self.assertNotIn("publish_result:",text)
        self.assertNotIn("inputs.product",text)
        self.assertNotIn("inputs.publish_result",text)
        self.assertNotIn("inputs.confirmar_ejecucion",text)
        self.assertNotIn("Resolver paquete electoral preparado",text)
        self.assertIn("Resolver paquete territorial preparado",text)
        self.assertIn("source_package_run_id",text)

    def test_electoral_incorporation_uses_dedicated_reusable_without_publication(self):
        data=load(ELECTORAL)
        text=ELECTORAL.read_text(encoding="utf-8")
        self.assertEqual(data["jobs"]["incorporar"]["uses"],"./.github/workflows/_reutilizable-incorporacion-electoral.yml")
        self.assertNotIn("publish_result:",text)
        self.assertIn("Localizar producto territorial certificado",text)
        self.assertIn("Localizar resultados electorales preparados",text)

    def test_publication_still_targets_the_visor(self):
        router=load(ROUTER); engine=load(ENGINE)
        rt=(router.get("on") or router.get(True))["workflow_call"]["inputs"]
        en=(engine.get("on") or engine.get(True))["workflow_call"]["inputs"]
        self.assertIn("publish_result",rt); self.assertIn("publish_result",en)
        self.assertIn("source_package_run_id",rt); self.assertIn("source_package_run_id",en)
        visor=engine["jobs"]["visor"]
        self.assertIn("inputs.publish_result == true",visor["if"])
        self.assertIn("needs.m06.result == 'success'",visor["if"])
        self.assertIn("needs.m08.result == 'success'",visor["if"])

    def test_generation_and_electoral_paths_are_separate(self):
        generation=load(GEN); electoral=load(ELECTORAL)
        self.assertEqual(generation["jobs"]["ruta"]["uses"],"./.github/workflows/_reutilizable-generacion-territorial.yml")
        self.assertEqual(electoral["jobs"]["incorporar"]["uses"],"./.github/workflows/_reutilizable-incorporacion-electoral.yml")
        router=load(ROUTER); engine=load(ENGINE)
        self.assertEqual(router["jobs"]["produccion"]["uses"],"./.github/workflows/producir-territorio-por-contrato.yml")
        self.assertIn("workflow_call",engine.get("on") or engine.get(True))

if __name__=="__main__": unittest.main()
