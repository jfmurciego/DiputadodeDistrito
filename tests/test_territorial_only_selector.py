from pathlib import Path
import unittest
import yaml

ROOT = Path(__file__).resolve().parents[1]
ORCH = ROOT / ".github" / "workflows" / "ejecucion-completa-proyecto.yml"


class TerritorialOnlyManualSelectorRegression(unittest.TestCase):
    def test_manual_selector_drives_existing_territorial_only_path(self):
        text = ORCH.read_text(encoding="utf-8")
        data = yaml.load(text, Loader=yaml.BaseLoader)
        selector = data["on"]["workflow_dispatch"]["inputs"]["publication_mode"]

        self.assertEqual(selector["type"], "choice")
        self.assertEqual(selector["default"], "electoral")
        self.assertEqual(selector["options"], ["electoral", "territorial_only"])
        self.assertIn(
            "PUBLICATION_MODE: ${{ github.event_name == 'pull_request' && 'electoral' || inputs.publication_mode || 'electoral' }}",
            text,
        )
        self.assertIn('if effective_mode=="territorial_only":', text)
        self.assertIn('p["run_prepare_electoral"]=False', text)
        self.assertIn('p["run_incorporate"]=False', text)

        jobs = data["jobs"]
        self.assertEqual(jobs["preparar_electoral"]["if"], "${{ false }}")
        self.assertEqual(jobs["preparar_territorial"]["if"], "${{ false }}")
        self.assertEqual(jobs["generar"]["needs"], ["planificar", "preparar_territorial", "puerta_01"])
        self.assertNotIn("puerta_03", jobs["generar"]["needs"])
        self.assertIn("puerta_02", jobs["publicar"]["needs"])
        self.assertEqual(
            jobs["publicar"]["with"]["production_run_id"],
            "${{ needs.puerta_04.result == 'success' && needs.puerta_04.outputs.run_id || needs.puerta_02.outputs.run_id }}",
        )

    def test_electoral_mode_is_resolved_before_electoral_jobs(self):
        text = ORCH.read_text(encoding="utf-8")
        data = yaml.load(text, Loader=yaml.BaseLoader)
        self.assertIn("effective=resolve_publication_mode(plan,requested,root_dir=Path(\".\"))", text)
        self.assertLess(
            text.index("effective=resolve_publication_mode(plan,requested,root_dir=Path(\".\"))"),
            text.index("resolve-territorial"),
        )
        self.assertIn('p["publication_mode_requested"]=publication_mode', text)
        self.assertIn('p["publication_mode_effective"]=effective_mode', text)
        self.assertIn('p["publication_mode"]=effective_mode', text)
        outputs = data["jobs"]["planificar"]["outputs"]
        self.assertIn("publication_mode_requested", outputs)
        self.assertIn("publication_mode_effective", outputs)
        for job_name in ("puerta_03", "puerta_04"):
            condition = data["jobs"][job_name]["if"]
            self.assertIn("needs.planificar.outputs.publication_mode_effective == 'electoral'", condition)
            self.assertNotIn("inputs.publication_mode", condition)
        self.assertEqual(
            data["jobs"]["campaign_status"]["env"]["PUBLICATION_MODE"],
            "${{ needs.planificar.outputs.publication_mode_effective }}",
        )

    def test_all_19_registered_identities_preserve_requested_electoral_mode(self):
        from herramientas.resolver_ejecucion_completa import resolve_publication_mode
        registry = yaml.safe_load((ROOT / "configuracion/registro_electoral.yaml").read_text(encoding="utf-8"))
        self.assertEqual(len(registry["territories"]), 19)
        for territory_id, entry in registry["territories"].items():
            with self.subTest(territory=territory_id):
                plan = {
                    "territory_id": territory_id,
                    "territory_name": entry["name"],
                    "edition": "2025",
                    "run_prepare_electoral": True,
                }
                self.assertEqual(resolve_publication_mode(plan, "electoral", root_dir=ROOT), "electoral")

    def test_registered_identity_without_declaration_enters_03_instead_of_downgrading(self):
        from herramientas.resolver_ejecucion_completa import resolve_publication_mode
        from herramientas.resolver_eleccion_vigente import resolve_for_preparation
        row = resolve_for_preparation("Andalucía", root_dir=ROOT, edition="2025")
        self.assertEqual(row["resolution_mode"], "registered_identity_pending_source")
        plan = {"territory_name": "Andalucía", "edition": "2025", "run_prepare_electoral": True}
        self.assertEqual(resolve_publication_mode(plan, "electoral", root_dir=ROOT), "electoral")

    def test_materialized_election_contract_keeps_electoral_mode(self):
        from herramientas.resolver_ejecucion_completa import resolve_publication_mode
        from herramientas.resolver_eleccion_vigente import resolve_for_preparation
        row = resolve_for_preparation("Castilla y León", root_dir=ROOT, edition="2025")
        self.assertEqual(row["resolution_mode"], "materialized_election_contract")
        plan = {"territory_name": "Castilla y León", "edition": "2025", "run_prepare_electoral": True}
        self.assertEqual(resolve_publication_mode(plan, "electoral", root_dir=ROOT), "electoral")

    def test_reusable_electoral_product_keeps_requested_mode_without_repreparing(self):
        from herramientas.resolver_ejecucion_completa import resolve_publication_mode
        plan = {
            "territory_id": "principado_de_asturias",
            "territory_name": "Principado de Asturias",
            "edition": "2025",
            "run_prepare_electoral": False,
        }
        self.assertEqual(resolve_publication_mode(plan, "electoral", root_dir=ROOT), "electoral")

    def test_provisional_non_promotable_source_does_not_downgrade_scope(self):
        from herramientas.resolver_ejecucion_completa import resolve_publication_mode
        adapter = (ROOT / "herramientas/adaptador_minsait_csv.py").read_text(encoding="utf-8")
        workflow = (ROOT / ".github/workflows/preparacion-resultados-electorales.yml").read_text(encoding="utf-8")
        self.assertIn('"production_eligible": False', adapter)
        self.assertIn("needs.electorales.outputs.production_eligible == 'true'", workflow)
        plan = {"territory_name": "Andalucía", "edition": "2025", "run_prepare_electoral": True}
        self.assertEqual(resolve_publication_mode(plan, "electoral", root_dir=ROOT), "electoral")

    def test_extremadura_real_block_remains_explicitly_electoral(self):
        from herramientas.resolver_ejecucion_completa import resolve_publication_mode
        declaration = yaml.safe_load(
            (ROOT / "territorios/extremadura/config/elecciones/fuentes_oficiales_2025.yaml").read_text(encoding="utf-8")
        )
        candidate = next(row for row in declaration["sources"] if row.get("role") == "candidate_data_source")
        self.assertEqual(candidate["data_status"], "provisional_only")
        self.assertFalse(candidate["promotion_allowed"])
        self.assertEqual(declaration["provisional_evidence"]["blocker"], "BLOCKED_FINAL_GRANULAR_SOURCE")
        plan = {"territory_name": "Extremadura", "edition": "2025", "run_prepare_electoral": True}
        self.assertEqual(resolve_publication_mode(plan, "electoral", root_dir=ROOT), "electoral")

    def test_only_explicit_territorial_only_omits_electoral_scope(self):
        from herramientas.resolver_ejecucion_completa import resolve_publication_mode
        plan = {"territory_name": "Andalucía", "edition": "2025", "run_prepare_electoral": True}
        self.assertEqual(resolve_publication_mode(plan, "territorial_only", root_dir=ROOT), "territorial_only")
        text = ORCH.read_text(encoding="utf-8")
        self.assertIn('if effective_mode=="territorial_only":', text)
        self.assertIn('p["run_prepare_electoral"]=False', text)
        self.assertIn('p["run_incorporate"]=False', text)

    def test_electoral_block_does_not_update_or_publish_territorial_success(self):
        data = yaml.load(ORCH.read_text(encoding="utf-8"), Loader=yaml.BaseLoader)
        state_condition = data["jobs"]["actualizar_estado"]["if"]
        publish_condition = data["jobs"]["publicar"]["if"]
        for condition in (state_condition, publish_condition):
            self.assertIn("publication_mode_effective == 'territorial_only'", condition)
            self.assertIn("publication_mode_effective == 'electoral'", condition)
            self.assertIn("needs.puerta_04.result == 'success'", condition)


if __name__ == "__main__":
    unittest.main()
