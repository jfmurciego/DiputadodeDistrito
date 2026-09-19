from pathlib import Path
import unittest
import yaml

ROOT=Path(__file__).resolve().parents[1]
WORKFLOWS=ROOT/".github"/"workflows"
GEN=WORKFLOWS/"produccion-distritos.yml"
ELECTORAL=WORKFLOWS/"incorporacion-resultados-electorales.yml"
PRODUCTION=WORKFLOWS/"producir-territorio-por-contrato.yml"
VISIBLE_TERRITORIES=["Aragón","Castilla y León"]

class WorkflowInterfaceInstitutional(unittest.TestCase):
    @staticmethod
    def _load(path):
        return yaml.safe_load(path.read_text(encoding="utf-8")) or {}

    @classmethod
    def _dispatch_inputs(cls,path):
        data=cls._load(path); triggers=data.get(True,data.get("on",{})) or {}
        return ((triggers.get("workflow_dispatch") or {}).get("inputs",{}) or {})

    def test_generation_interface_name_and_controls(self):
        self.assertEqual(self._load(GEN)["name"],"Generación de distritos autonómicos")
        inputs=self._dispatch_inputs(GEN)
        self.assertEqual(list(inputs),["territory_id","data_edition"])
        self.assertEqual(inputs["territory_id"]["options"],VISIBLE_TERRITORIES)
        self.assertEqual(inputs["data_edition"]["options"],["2025"])

    def test_electoral_incorporation_name_and_controls(self):
        self.assertEqual(self._load(ELECTORAL)["name"],"Incorporación de resultados electorales")
        inputs=self._dispatch_inputs(ELECTORAL)
        self.assertEqual(list(inputs),["territory_id","data_edition"])
        self.assertEqual(inputs["territory_id"]["options"],VISIBLE_TERRITORIES)
        self.assertEqual(inputs["data_edition"]["options"],["2025"])

    def test_no_redundant_human_confirmation_or_publish_switch(self):
        for path in (GEN,ELECTORAL):
            inputs=self._dispatch_inputs(path)
            self.assertNotIn("confirmar_ejecucion",inputs)
            self.assertNotIn("publish_result",inputs)
            self.assertNotIn("product",inputs)
            text=path.read_text(encoding="utf-8")
            self.assertIn("execution_confirmed: true",text)
            self.assertIn("publish_result: true",text)

    def test_generation_uses_district_route_only(self):
        text=GEN.read_text(encoding="utf-8")
        self.assertIn("UI_PRODUCT: Distritos",text)
        self.assertNotIn("Resolver paquete electoral preparado",text)
        self.assertIn("resolver_producto_produccion.py --product",text)

    def test_electoral_requires_existing_m06_and_prepared_package(self):
        text=ELECTORAL.read_text(encoding="utf-8")
        self.assertIn("UI_PRODUCT: Resultados electorales",text)
        self.assertIn("search_from=6",text)
        self.assertIn("search_to=6",text)
        self.assertIn("Resultados electorales requiere un checkpoint M06 válido",text)
        self.assertIn("Resolver paquete electoral preparado",text)
        self.assertIn("exit 44",text)
        self.assertIn("exit 45",text)

    def test_both_interfaces_delegate_to_same_reusable_chain(self):
        for path in (GEN,ELECTORAL):
            data=self._load(path)
            self.assertEqual(list(data["jobs"]),["resolver_interfaz","ruta"])
            route=data["jobs"]["ruta"]
            self.assertEqual(route["uses"],"./.github/workflows/_reutilizable-operacion-territorial.yml")
            self.assertEqual(route["with"]["operation"],"producir_resultado_m01_m08")

    def test_checkpoint_selection_and_engine_are_preserved(self):
        for path in (GEN,ELECTORAL):
            text=path.read_text(encoding="utf-8")
            self.assertIn("python -m herramientas.seleccionar_checkpoint_productivo",text)
            self.assertIn("ddd-checkpoint-selection-${{ github.run_id }}",text)
        production_text=PRODUCTION.read_text(encoding="utf-8")
        for stage in ("m01:","m02:","m03:","m04:","m05:","m06:","m07:","m08:"):
            self.assertIn(stage,production_text)
        self.assertIn("visor:",production_text)

if __name__=="__main__": unittest.main()
