from pathlib import Path
import unittest
import yaml

ROOT=Path(__file__).resolve().parents[1]
GEN=ROOT/".github/workflows/produccion-distritos.yml"
ELECTORAL=ROOT/".github/workflows/incorporacion-resultados-electorales.yml"

def load(path):
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}

def inputs(path):
    d=load(path); t=d.get("on") or d.get(True)
    return t["workflow_dispatch"]["inputs"]

class ProductRoutingDesignA(unittest.TestCase):
    def test_generation_form_has_functional_execution_mode(self):
        self.assertEqual(list(inputs(GEN)),["territory_id","data_edition","execution_mode","optimization_algorithm"])
        self.assertEqual(inputs(GEN)["execution_mode"]["options"],["Reutilizar progreso existente","Ejecutar desde el principio"])
        self.assertEqual(inputs(GEN)["optimization_algorithm"]["options"],["Canónico","GerryChain","GerryChain 25","GerryChain 50"])

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



if __name__=="__main__": unittest.main()
