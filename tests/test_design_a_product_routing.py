from pathlib import Path
import unittest
import yaml

ROOT=Path(__file__).resolve().parents[1]
GEN=ROOT/".github/workflows/p20-distritos.yml"
ELECTORAL=ROOT/".github/workflows/incorporacion-resultados-electorales.yml"

def load(path):
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}

def inputs(path):
    d=load(path); t=d.get("on") or d.get(True)
    return t["workflow_dispatch"]["inputs"]

class ProductRoutingDesignA(unittest.TestCase):
    def test_generation_form_has_functional_execution_mode(self):
        # T-377 (D-139): códigos y «empezar de cero» (desmarcado = reutilizar); la estrategia sale del botón (Canónico).
        self.assertEqual(list(inputs(GEN)),["territorio","empezar_de_cero"])  # D-148: uno por ejecución
        self.assertIs(inputs(GEN)["empezar_de_cero"]["default"],False)
        self.assertIn("execution_mode='Ejecutar desde el principio'; else execution_mode='Reutilizar progreso existente'",GEN.read_text(encoding="utf-8"))

    def test_electoral_incorporation_form_has_only_territory_and_edition(self):
        self.assertEqual(list(inputs(ELECTORAL)),["territory_id","data_edition"])

    def test_generation_is_fixed_to_districts_without_auto_publish(self):
        text=GEN.read_text(encoding="utf-8")
        self.assertIn("UI_PRODUCT: Distritos",text)
        self.assertIn("execution_authorization=EXECUTE_WITH_EXPLICIT_USER_AUTHORIZATION",text)  # T-377: job `entrada`
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

    def test_generation_and_electoral_paths_are_separate(self):
        generation=load(GEN); electoral=load(ELECTORAL)
        self.assertIn("resolve",generation["jobs"])  # T-377: el motor va dentro de P20
        self.assertEqual(electoral["jobs"]["incorporar"]["uses"],"./.github/workflows/_reutilizable-incorporacion-electoral.yml")



if __name__=="__main__": unittest.main()
