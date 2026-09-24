from pathlib import Path
import unittest
import yaml

ROOT=Path(__file__).resolve().parents[1]
WORKFLOWS=ROOT/".github"/"workflows"
GEN=WORKFLOWS/"produccion-distritos.yml"
ELECTORAL=WORKFLOWS/"incorporacion-resultados-electorales.yml"
PRODUCTION=WORKFLOWS/"producir-territorio-por-contrato.yml"
ALL_TERRITORIES=["01 · Andalucía","02 · Aragón","03 · Principado de Asturias","04 · Islas Baleares","05 · Canarias","06 · Cantabria","07 · Castilla y León","08 · Castilla-La Mancha","09 · Cataluña","10 · Comunidad Valenciana","11 · Extremadura","12 · Galicia","13 · Comunidad de Madrid","14 · Región de Murcia","15 · Comunidad Foral de Navarra","16 · País Vasco","17 · La Rioja","18 · Ceuta","19 · Melilla"]

class WorkflowInterfaceInstitutional(unittest.TestCase):
    @staticmethod
    def _load(path):
        return yaml.safe_load(path.read_text(encoding="utf-8")) or {}

    @classmethod
    def _dispatch_inputs(cls,path):
        data=cls._load(path); triggers=data.get(True,data.get("on",{})) or {}
        return ((triggers.get("workflow_dispatch") or {}).get("inputs",{}) or {})

    def test_generation_interface_name_and_controls(self):
        self.assertEqual(self._load(GEN)["name"],"02 · Generación de Distritos Autonómicos")
        inputs=self._dispatch_inputs(GEN)
        self.assertEqual(list(inputs),["territory_id","data_edition","execution_mode","optimization_algorithm"])
        self.assertEqual(inputs["territory_id"]["options"],ALL_TERRITORIES)
        self.assertEqual(inputs["data_edition"]["options"],["2025"])
        self.assertEqual(inputs["execution_mode"]["options"],["Reutilizar progreso existente","Ejecutar desde el principio"])
        self.assertEqual(inputs["optimization_algorithm"]["options"],["Canónico","GerryChain","GerryChain 25","GerryChain 50"])

    def test_electoral_incorporation_name_and_controls(self):
        self.assertEqual(self._load(ELECTORAL)["name"],"04 · Incorporación de Resultados Electorales")
        inputs=self._dispatch_inputs(ELECTORAL)
        self.assertEqual(list(inputs),["territory_id","data_edition"])
        self.assertEqual(inputs["territory_id"]["options"],ALL_TERRITORIES)
        self.assertEqual(inputs["data_edition"]["options"],["2025"])

    def test_no_redundant_human_confirmation_or_publish_switch(self):
        for path in (GEN,ELECTORAL):
            inputs=self._dispatch_inputs(path)
            self.assertNotIn("confirmar_ejecucion",inputs)
            self.assertNotIn("publish_result",inputs)
            self.assertNotIn("product",inputs)
        generation=GEN.read_text(encoding="utf-8")
        electoral=ELECTORAL.read_text(encoding="utf-8")
        self.assertIn("execution_authorization: EXECUTE_WITH_EXPLICIT_USER_AUTHORIZATION",generation)
        self.assertNotIn("publish_result:",generation)
        self.assertNotIn("publish_result:",electoral)

    def test_generation_uses_district_route_only(self):
        text=GEN.read_text(encoding="utf-8")
        self.assertIn("UI_PRODUCT: Distritos",text)
        self.assertNotIn("Resolver paquete electoral preparado",text)
        self.assertIn("resolver_producto_produccion.py --product",text)
        self.assertIn("Resolver paquete territorial preparado",text)
        self.assertIn("source_package_run_id",text)
        self.assertIn("prepared_source_run_id",text)
        self.assertIn("prepared_source_artifact_name",text)
        self.assertIn("preparation_evidence.run_id",text)
        self.assertIn("preparation_evidence.artifact_name",text)
        self.assertIn('gh api --paginate "repos/$GITHUB_REPOSITORY/actions/artifacts?per_page=100"',text)

    def test_electoral_requires_existing_certified_product_and_prepared_package(self):
        text=ELECTORAL.read_text(encoding="utf-8")
        self.assertIn("Localizar producto territorial certificado",text)
        self.assertIn("Localizar resultados electorales preparados",text)
        self.assertIn("seleccionar_checkpoint_productivo",text)
        self.assertIn("production_status.json",text)
        self.assertIn("exit 44",text)
        self.assertIn("exit 45",text)

    def test_electoral_rejects_m06_that_selector_only_allows_to_derive(self):
        text=ELECTORAL.read_text(encoding="utf-8")
        self.assertIn('selection="$tmp/checkpoint_selection.json"',text)
        self.assertIn('"$selection"',text)
        self.assertIn(
            "(.valid == true) and ((.requires_derivation // false) == false) and (.effective_stage == \"M06\")",
            text,
        )
        self.assertIn('if [[ "$direct_reuse" != true ]]',text)
        self.assertIn("continue",text)

    def test_interfaces_delegate_to_separate_reusable_chains(self):
        generation=self._load(GEN)
        self.assertEqual(generation["jobs"]["ruta"]["uses"],"./.github/workflows/_reutilizable-generacion-territorial.yml")
        electoral=self._load(ELECTORAL)
        self.assertEqual(electoral["jobs"]["incorporar"]["uses"],"./.github/workflows/_reutilizable-incorporacion-electoral.yml")

    def test_routes_inherit_standard_credentials(self):
        generation=self._load(GEN)
        electoral=self._load(ELECTORAL)
        self.assertEqual(generation["jobs"]["ruta"]["secrets"],"inherit")
        self.assertEqual(electoral["jobs"]["incorporar"]["secrets"],"inherit")
        for reusable in ("_reutilizable-generacion-territorial.yml","_reutilizable-incorporacion-electoral.yml"):
            text=(WORKFLOWS/reusable).read_text(encoding="utf-8")
            self.assertNotIn("DDD_WORKFLOW_TOKEN",text)

    def test_manual_generation_persists_state_by_default_without_overriding_reusable_calls(self):
        data=self._load(GEN)
        triggers=data.get(True,data.get("on",{})) or {}
        call_inputs=((triggers.get("workflow_call") or {}).get("inputs",{}) or {})
        dispatch_inputs=((triggers.get("workflow_dispatch") or {}).get("inputs",{}) or {})
        self.assertEqual(call_inputs["invocation_context"]["default"],"reusable")
        self.assertNotIn("invocation_context",dispatch_inputs)
        self.assertNotIn("persist_state",dispatch_inputs)
        text=GEN.read_text(encoding="utf-8")
        self.assertIn("persist_state: ${{ inputs.invocation_context != 'reusable' || inputs.persist_state }}",text)

    def test_checkpoint_selection_and_engine_are_preserved(self):
        self.assertIn("python -m herramientas.seleccionar_checkpoint_productivo",GEN.read_text(encoding="utf-8"))
        self.assertIn("python -m herramientas.seleccionar_checkpoint_productivo",ELECTORAL.read_text(encoding="utf-8"))
        production_text=PRODUCTION.read_text(encoding="utf-8")
        for stage in ("m01:","m02:","m03:","m04:","m05:","m06:","m07:","m08:"):
            self.assertIn(stage,production_text)
        self.assertIn("visor:",production_text)

if __name__=="__main__": unittest.main()
