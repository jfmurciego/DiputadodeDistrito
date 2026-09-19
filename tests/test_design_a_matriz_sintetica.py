from __future__ import annotations
import hashlib,json,tempfile,unittest
from pathlib import Path
import yaml

from herramientas.catalogo_preparacion import lookup,rows_for
from herramientas.resolver_fuentes_territorio import territories
from herramientas.resolver_producto_produccion import ROUTES,resolve_product,synthetic_matrix_decision
from herramientas.validar_paquete_electoral import validate_package

ROOT=Path(__file__).resolve().parents[1]
WF=ROOT/".github/workflows"
PREP=WF/"preparacion-fuentes.yml"
ELECTORAL_PREP=WF/"preparacion-resultados-electorales.yml"
GEN=WF/"produccion-distritos.yml"
ELECTORAL_APPLY=WF/"incorporacion-resultados-electorales.yml"
ENGINE=WF/"producir-territorio-por-contrato.yml"
ROUTER=WF/"_reutilizable-operacion-territorial.yml"
CAT=ROOT/"configuracion/catalogo_preparacion.yaml"

def load(path:Path):
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}

def triggers(path:Path):
    d=load(path); return d.get("on") or d.get(True) or {}

class MandatorySyntheticDesignATests(unittest.TestCase):
    def test_visible_workflows(self):
        visible={
            "Preparación de datos territoriales":PREP,
            "Preparación de resultados electorales":ELECTORAL_PREP,
            "Generación de distritos autonómicos":GEN,
            "Incorporación de resultados electorales":ELECTORAL_APPLY,
            "Pruebas de la plataforma":WF/"pruebas-plataforma.yml",
        }
        self.assertEqual({load(p)["name"] for p in visible.values()},set(visible))
        dispatch=[p.name for p in WF.glob("*.yml") if "workflow_dispatch" in triggers(p)]
        self.assertEqual(sorted(dispatch),["incorporacion-resultados-electorales.yml","preparacion-fuentes.yml","preparacion-resultados-electorales.yml","produccion-distritos.yml","prueba-fuentes-oficiales.yml","prueba-openai.yml"])

    def test_preparation_supports_every_registered_territory_without_making_it_producible(self):
        prep_options=triggers(PREP)["workflow_dispatch"]["inputs"]["territory_id"]["options"]
        expected=[r["name"] for r in territories()]
        prod=[r["name"] for r in rows_for("production",CAT)]
        self.assertEqual(prep_options,expected)
        self.assertIn("La Rioja",prep_options)
        self.assertIn("Ceuta",prep_options)
        self.assertIn("Melilla",prep_options)
        self.assertNotIn("La Rioja",prod)
        self.assertEqual(triggers(GEN)["workflow_dispatch"]["inputs"]["territory_id"]["options"],prod)
        self.assertEqual(triggers(ELECTORAL_APPLY)["workflow_dispatch"]["inputs"]["territory_id"]["options"],prod)

    def test_preparation_generates_sources_and_reuses_existing_package_by_default(self):
        inputs=triggers(PREP)["workflow_dispatch"]["inputs"]
        self.assertNotIn("source_scope",inputs)
        self.assertTrue(inputs["reutilizar_si_ya_preparada"]["default"])
        text=PREP.read_text(encoding="utf-8")
        self.assertIn("resolver_fuentes_territorio.py declaration",text)
        self.assertIn("Recuperar fuente territorial ya preparada",text)
        self.assertIn("gh run download",text)
        self.assertIn("ddd-source-package-$TERRITORY_ID-$EDITION-",text)
        self.assertNotIn("Territorio pendiente de incorporación: falta declaración de fuentes territoriales.",text)

    def test_catalog_lookup_does_not_require_preparation_status_ready(self):
        row=lookup("La Rioja","2025",CAT)
        self.assertEqual(row["territory_id"],"la_rioja")
        self.assertEqual(row["preparation_status"],"PENDING_INCORPORATION")

    def test_preparations_are_separate_and_never_execute_m01_m08(self):
        territorial=load(PREP)
        electoral=load(ELECTORAL_PREP)
        self.assertEqual(set(territorial["jobs"]),{"resolver","territoriales"})
        self.assertEqual(set(electoral["jobs"]),{"resolver","electorales"})
        territorial_text=PREP.read_text(encoding="utf-8")
        electoral_text=ELECTORAL_PREP.read_text(encoding="utf-8")
        self.assertNotIn("preparar_fuente_electoral",territorial_text)
        self.assertNotIn("ddd-electoral-package",territorial_text)
        for text in (territorial_text,electoral_text):
            self.assertNotIn("procedimiento.sh",text)
            self.assertNotIn("producir-territorio-por-contrato.yml",text)
        electoral_job=yaml.safe_dump(electoral["jobs"]["electorales"],allow_unicode=True)
        self.assertNotIn("auditar_componentes_geometricos",electoral_job)
        self.assertNotIn("M06",electoral_job)
        self.assertNotIn("geometry",electoral_job.lower())

    def test_three_products_route_without_publish_changing_stage(self):
        self.assertEqual(resolve_product("Distritos"),{
            "product":"Distritos","to_stage":"M06","checkpoint_policy":"latest_before_target","requires_electoral_package":False})
        self.assertEqual(resolve_product("Resultados electorales"),{
            "product":"Resultados electorales","to_stage":"M08","checkpoint_policy":"require_m06","requires_electoral_package":True})
        self.assertEqual(resolve_product("Ambos"),{
            "product":"Ambos","to_stage":"M08","checkpoint_policy":"latest_through_m06","requires_electoral_package":True})
        gen=GEN.read_text(encoding="utf-8")
        electoral=ELECTORAL_APPLY.read_text(encoding="utf-8")
        self.assertIn("UI_PRODUCT: Distritos",gen)
        self.assertIn("UI_PRODUCT: Resultados electorales",electoral)
        self.assertIn("publish_result: true",gen)
        self.assertIn("publish_result: true",electoral)

    def test_territorial_product_has_no_electoral_dependency(self):
        route=resolve_product("Distritos")
        self.assertFalse(route["requires_electoral_package"])
        self.assertEqual(route["to_stage"],"M06")
        engine=load(ENGINE)
        self.assertIn("fromJSON(needs.resolve.outputs.to_num) >= 7",engine["jobs"]["electoral_source"]["if"])

    def test_electoral_requires_package_and_valid_m06_without_recalculation(self):
        text=ELECTORAL_APPLY.read_text(encoding="utf-8")
        self.assertIn("checkpoint_policy",text)
        self.assertIn("require_m06",text)
        self.assertIn("search_from=6",text); self.assertIn("search_to=6",text)
        self.assertIn("Resultados electorales requiere un checkpoint M06 válido; no se recalculará M01–M06.",text)
        self.assertIn("Producción electoral requiere un paquete electoral preparado, íntegro y coincidente con el contrato.",text)
        self.assertIn("exit 44",text); self.assertIn("exit 45",text)
        self.assertIn('from_stage="M$(printf \'%02d\' "$((stage_num+1))")"',text)
        self.assertEqual(resolve_product("Resultados electorales")["checkpoint_policy"],"require_m06")

    def test_checkpoint_is_automatic_and_corrupt_candidates_are_discarded(self):
        text=GEN.read_text(encoding="utf-8")
        self.assertIn("sort_by(.created_at) | reverse",text)
        self.assertIn("seleccionar_checkpoint_productivo",text)
        self.assertIn("validation_rc == 2",text)
        self.assertIn("record_discard",text)
        self.assertIn("search_from=$target_num",text)
        self.assertIn("requires_derivation",text)
        inputs=triggers(GEN)["workflow_dispatch"]["inputs"]
        self.assertNotIn("checkpoint_run_id",inputs)
        self.assertNotIn("from_stage",inputs)

    def test_publication_and_certification_contracts_are_independent(self):
        pub=(ROOT/"herramientas/evaluar_publicacion_visor.py").read_text(encoding="utf-8")
        territorial=(ROOT/"herramientas/estado_produccion.py").read_text(encoding="utf-8")
        self.assertIn('"deployment_status": status',pub)
        self.assertIn('"territorial_certification_status": decision',territorial)
        self.assertIn('"status": status',pub)
        self.assertIn('"decision": decision',territorial)

    def test_contractual_artifacts_and_internal_workflows_are_preserved(self):
        engine=ENGINE.read_text(encoding="utf-8")
        ui=GEN.read_text(encoding="utf-8")
        prep=PREP.read_text(encoding="utf-8")
        electoral_prep=ELECTORAL_PREP.read_text(encoding="utf-8")
        for token in [
            "ddd-state-${{ github.run_id }}-${{ env.STAGE }}",
            "ddd-audit-${{ github.run_id }}",
            "ddd-electoral-source-${{ github.run_id }}",
        ]: self.assertIn(token,engine)
        self.assertIn("ddd-checkpoint-selection-${{ github.run_id }}",ui)
        self.assertIn("ddd-electoral-package-${{ needs.resolver.outputs.territory_id }}-${{ needs.resolver.outputs.edition }}-${{ github.run_id }}",electoral_prep)
        self.assertIn("ddd-source-package-${{ needs.resolver.outputs.territory_id }}-${{ inputs.data_edition }}-${{ github.run_id }}",prep)
        for name in [
            "_reutilizable-auditoria-topologica.yml","_reutilizable-operacion-territorial.yml",
            "generar-alternativas-territoriales.yml","orquestacion-control.yml","orquestacion-durable.yml",
            "notificar-finalizacion-orquestacion.yml","desplegar-visor-publico.yml",
            "producir-territorio-por-contrato.yml",
        ]: self.assertTrue((WF/name).is_file(),name)
        router=ROUTER.read_text(encoding="utf-8")
        self.assertIn("generar-alternativas-territoriales.yml",router)
        self.assertIn("orquestacion-control.yml",router)
        self.assertIn("orquestacion-durable.yml",router)
        self.assertIn("desplegar-visor-publico.yml",router)

    def test_complete_54_case_matrix(self):
        cases=0
        for product in ROUTES:
            for publish in (False,True):
                for m06 in ("existing","absent","corrupt"):
                    for electoral in ("existing","absent","corrupt"):
                        cases+=1
                        plan=synthetic_matrix_decision(product,m06,electoral)
                        if product=="Resultados electorales" and m06!="existing":
                            self.assertFalse(plan["runnable"]); self.assertEqual(plan["block_reason"],"M06_REQUIRED")
                        elif product!="Distritos" and electoral!="existing":
                            self.assertFalse(plan["runnable"]); self.assertEqual(plan["block_reason"],"ELECTORAL_PACKAGE_REQUIRED")
                        else:
                            self.assertTrue(plan["runnable"])
                        self.assertEqual(resolve_product(product)["to_stage"],plan["to_stage"])
                        self.assertIsInstance(publish,bool)
        self.assertEqual(cases,54)

    def test_electoral_package_hash_equals_contract_and_corruption_blocks(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); data=b"mesa;votos\n1;10\n"; digest=hashlib.sha256(data).hexdigest()
            contract=root/"election.json"; contract.write_text(json.dumps({"sources":[{"path":"inputs/election.csv","sha256":digest}]}),encoding="utf-8")
            params=root/"params.yaml"; params.write_text(yaml.safe_dump({
                "meta":{"territory_id":"fixture","year":2025},
                "modulos":{"modulo_07_agregar_resultados_electorales":{"election_contract":"election.json"}}
            }),encoding="utf-8")
            package=root/"package"; (package/"data").mkdir(parents=True)
            source=package/"data/election.csv"; source.write_bytes(data)
            manifest={"schema":"ddd-electoral-package/1.0","decision":"ACQUIRE","territory_id":"fixture","edition":"2025",
                      "selected_source":{"path":"data/election.csv","sha256":digest,"bytes":len(data)}}
            (package/"manifest.json").write_text(json.dumps(manifest),encoding="utf-8")
            ok=validate_package(package=package,params=params,territory_id="fixture",edition="2025",root=root)
            self.assertTrue(ok["provenance_hash_matches_contract"])
            self.assertEqual(ok["package_sha256"],ok["contract_sha256"])
            source.write_bytes(data+b"corrupt")
            with self.assertRaisesRegex(ValueError,"hash interno"):
                validate_package(package=package,params=params,territory_id="fixture",edition="2025",root=root)

    def test_new_election_uses_m06_checkpoint_and_m07_m08_only(self):
        plan=synthetic_matrix_decision("Resultados electorales","existing","existing")
        self.assertTrue(plan["runnable"]); self.assertEqual(plan["to_stage"],"M08")
        self.assertEqual(plan["checkpoint_policy"],"require_m06")
        text=ELECTORAL_APPLY.read_text(encoding="utf-8")
        self.assertIn("search_from=6",text); self.assertIn("search_to=6",text)
        self.assertIn("latest_through_m06",text)
        self.assertIn('from_stage="M$(printf \'%02d\' "$((stage_num+1))")"',text)

if __name__=="__main__": unittest.main()
