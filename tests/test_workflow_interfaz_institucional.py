from pathlib import Path
import unittest
import yaml
from herramientas.catalogo_territorios import format_territory_label, load_master, selector_labels

ROOT=Path(__file__).resolve().parents[1]
WORKFLOWS=ROOT/".github"/"workflows"
GEN=WORKFLOWS/"p20-distritos.yml"
ELECTORAL=WORKFLOWS/"p30-resultados-electorales.yml"
ALL_TERRITORIES=selector_labels(ROOT/"configuracion/catalogo_territorios_espana_2025.yaml")

class WorkflowInterfaceInstitutional(unittest.TestCase):
    @staticmethod
    def _load(path):
        return yaml.safe_load(path.read_text(encoding="utf-8")) or {}

    @classmethod
    def _dispatch_inputs(cls,path):
        data=cls._load(path); triggers=data.get(True,data.get("on",{})) or {}
        return ((triggers.get("workflow_dispatch") or {}).get("inputs",{}) or {})

    def test_generation_interface_name_and_controls(self):
        self.assertEqual(self._load(GEN)["name"],"P20 Distritos")  # T-377 (D-139)
        inputs=self._dispatch_inputs(GEN)
        self.assertEqual(list(inputs),["territorio","empezar_de_cero"])  # D-148: uno por ejecución
        self.assertIn("data_edition=2025",self._load(GEN)["jobs"]["interfaz"]["steps"][-1]["run"])

    def test_electoral_incorporation_name_and_controls(self):
        self.assertEqual(self._load(ELECTORAL)["name"],"P30 Resultados electorales")
        inputs=self._dispatch_inputs(ELECTORAL)
        self.assertEqual(list(inputs),["territorio"])  # T-376/D-148: un código; la edición (2025) va en el código
        self.assertEqual(inputs["territorio"]["type"],"string")

    def test_no_redundant_human_confirmation_or_publish_switch(self):
        for path in (GEN,ELECTORAL):
            inputs=self._dispatch_inputs(path)
            self.assertNotIn("confirmar_ejecucion",inputs)
            self.assertNotIn("publish_result",inputs)
            self.assertNotIn("product",inputs)
        generation=GEN.read_text(encoding="utf-8")
        electoral=ELECTORAL.read_text(encoding="utf-8")
        self.assertIn("execution_authorization=EXECUTE_WITH_EXPLICIT_USER_AUTHORIZATION",generation)  # T-377: job `entrada`
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
        self.assertIn("resolve",generation["jobs"])  # T-377: el motor va dentro de P20
        electoral=self._load(ELECTORAL)
        self.assertNotIn("uses",electoral["jobs"]["incorporar"])  # T-376: la incorporación va dentro (P30), sin reutilizable

    def test_routes_inherit_standard_credentials(self):
        generation=self._load(GEN)
        electoral=self._load(ELECTORAL)
        self.assertFalse(any("uses" in j for j in generation["jobs"].values()))  # T-377: sin reutilizables; secretos del propio run
        self.assertNotIn("secrets",electoral["jobs"]["incorporar"])  # sin reutilizable no hay `secrets: inherit`: los pasos usan `secrets.*` directamente
        for reusable in ("p20-distritos.yml","p30-resultados-electorales.yml"):
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
        # T-377: la regla de `ruta` la aplica ahora el job `entrada`; la fila del botón pasa invocation_context=boton (persiste).
        self.assertIn('if [[ "$IN_INVOCATION_CONTEXT" != reusable || "$IN_PERSIST_STATE" == true ]]; then persist_state=true',text)
        self.assertNotIn("invocation_context",dispatch_inputs)  # el botón: vacío ≠ reusable ⇒ persiste, como la 02

    def test_checkpoint_selection_and_engine_are_preserved(self):
        self.assertIn("python -m herramientas.seleccionar_checkpoint_productivo",GEN.read_text(encoding="utf-8"))
        self.assertIn("python -m herramientas.seleccionar_checkpoint_productivo",ELECTORAL.read_text(encoding="utf-8"))


if __name__=="__main__": unittest.main()
