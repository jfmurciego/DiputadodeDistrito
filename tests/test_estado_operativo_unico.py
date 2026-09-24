from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

import yaml

from herramientas.generar_estado_operativo import START, END, build, update_readme
from herramientas.validar_puerta_ejecucion import validate_gate


class EstadoOperativoUnicoTests(unittest.TestCase):
    def test_build_requires_durable_receipts_for_green_chain(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            (root/"configuracion").mkdir()
            ev=root/"territorios/demo/evidencia/catalogo"; ev.mkdir(parents=True)
            digest="a"*64
            for kind,stage in (("territorial_product","M06"),("electoral_source",None),("electoral_product","M08")):
                payload={"territory_id":"demo","edition":"2025","run_id":123,"artifact_name":(
                    "ddd-electoral-package-demo-2025-123" if kind=="electoral_source" else f"ddd-state-123-{stage}"
                ),"artifact_sha256":digest}
                if kind=="territorial_product": payload["decision"]="PASS"
                (ev/f"{kind}_2025.json").write_text(json.dumps(payload),encoding="utf-8")
            catalog={"schema":"ddd-preparation-catalog/1.1","territories":[{
                "territory_id":"demo","name":"Demo","editions":{"2025":{
                    "contract_path":"territorios/demo/config/demo.yaml",
                    "territorial_sources_prepared":True,"electoral_source_prepared":True,
                    "territorial_product_available":True,"electoral_product_available":True,
                    "territorial_certification":"PASS","production_authorization":"AUTHORIZED",
                    "preparation_evidence":{"run_id":122,"artifact_name":"ddd-source-package-demo-2025-122","artifact_sha256":digest},
                    "evidence":{
                        "territorial_product":"territorios/demo/evidencia/catalogo/territorial_product_2025.json",
                        "electoral_source":"territorios/demo/evidencia/catalogo/electoral_source_2025.json",
                        "electoral_product":"territorios/demo/evidencia/catalogo/electoral_product_2025.json",
                    },
                    "last_valid_checkpoint":{"run_id":123,"stage":"M08"},
                }}
            },{
                "territory_id":"candidate","name":"Candidate","editions":{"2025":{
                    "contract_path":"territorios/candidate/config/candidate.yaml",
                    "territorial_sources_prepared":False,"electoral_source_prepared":False,
                    "territorial_product_available":False,"electoral_product_available":False,
                    "territorial_certification":"PREFLIGHT","production_authorization":"PREFLIGHT",
                }}
            }]}
            (root/"configuracion/catalogo_preparacion.yaml").write_text(yaml.safe_dump(catalog,allow_unicode=True,sort_keys=False),encoding="utf-8")
            state=build(root,"2025")
            self.assertEqual(state["schema"],"ddd-estado-operativo/2.1")
            self.assertEqual(state["kpis"]["complete_names"],["Demo"])
            demo=next(r for r in state["territories"] if r["territory_id"]=="demo")
            self.assertEqual((demo["ft"],demo["g"],demo["fe"],demo["re"]),("green","green","green","green"))
            candidate=next(r for r in state["territories"] if r["territory_id"]=="candidate")
            self.assertEqual(candidate["status"],"Puerta de validación pendiente")

    def test_catalog_flag_without_receipt_is_not_green(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); (root/"configuracion").mkdir()
            catalog={"territories":[{"territory_id":"demo","name":"Demo","editions":{"2025":{
                "contract_path":"territorios/demo/config/demo.yaml",
                "territorial_sources_prepared":True,"territorial_product_available":True,
                "electoral_source_prepared":True,"electoral_product_available":True,
                "territorial_certification":"PASS","production_authorization":"AUTHORIZED",
            }}}]}
            (root/"configuracion/catalogo_preparacion.yaml").write_text(yaml.safe_dump(catalog),encoding="utf-8")
            row=build(root,"2025")["territories"][0]
            self.assertNotEqual(row["g"],"green")
            self.assertNotEqual(row["re"],"green")

    def test_readme_updates_only_generated_block(self):
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/"README.md"
            path.write_text("cabecera\n"+START+"\nobsoleto\n"+END+"\ncola\n",encoding="utf-8")
            state={"generated_at":"2026-09-20T00:00:00+00:00","edition":"2025",
                   "kpis":{"complete":0,"complete_names":[],"territorial_validated":0,"territorial_validated_names":[],
                           "ready":0,"ready_names":[],"pending":0,"pending_names":[],"blocked":0,"blocked_names":[]},
                   "territories":[]}
            update_readme(path,state)
            text=path.read_text(encoding="utf-8")
            self.assertTrue(text.startswith("cabecera\n"+START))
            self.assertTrue(text.endswith(END+"\ncola\n"))
            self.assertIn("Cadena completa validada",text)


    def _synthetic_territorial_product_gate(
        self,
        root: Path,
        *,
        run_id: str = "123",
        territory_id: str = "demo",
        artifact_name: str,
        artifact_namespace: str | None = None,
        artifact_digest: str | None = None,
        expected_digest: str | None = None,
    ) -> dict:
        state=root/"state"; audit=root/"audit"
        for name in ("cache","run","sources"):
            (state/name).mkdir(parents=True,exist_ok=True)
        audit.mkdir(parents=True,exist_ok=True)
        (state/"run/CHAIN_STATE.json").write_text(
            json.dumps({"completed_stage":6}),encoding="utf-8"
        )
        (audit/"production_status.json").write_text(json.dumps({
            "territory_id":territory_id,
            "decision":"PASS",
            "scope_through_stage":"M06",
        }),encoding="utf-8")
        params=root/"demo.yaml"
        params.write_text(yaml.safe_dump({"meta":{"year":2025}}),encoding="utf-8")
        digest=artifact_digest or ("a"*64)
        return validate_gate(
            phase="territorial_product",
            artifact_root=state,
            audit_root=audit,
            params=params,
            territory_id=territory_id,
            edition="2025",
            run_id=run_id,
            artifact_name=artifact_name,
            artifact_digest=digest,
            expected_digest=expected_digest,
            artifact_namespace=artifact_namespace,
        )

    def test_territorial_product_gate_accepts_canonical_and_declared_campaign_namespace(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            canonical=self._synthetic_territorial_product_gate(
                root/"canonical",
                artifact_name="ddd-state-123-M06",
            )
            self.assertEqual(canonical["decision"],"VALIDADO")

            namespace="campaign-123-1--04--demo"
            namespaced=self._synthetic_territorial_product_gate(
                root/"campaign",
                artifact_name=f"ddd-state-123-M06-{namespace}",
                artifact_namespace=namespace,
            )
            self.assertEqual(namespaced["decision"],"VALIDADO")

    def test_territorial_product_gate_rejects_unbound_or_arbitrary_campaign_names(self):
        cases=(
            (
                "run-distinto",
                "ddd-state-123-M06-campaign-999-1--04--demo",
                "campaign-999-1--04--demo",
            ),
            (
                "territorio-distinto",
                "ddd-state-123-M06-campaign-123-1--04--otro",
                "campaign-123-1--04--otro",
            ),
            (
                "slot-invalido",
                "ddd-state-123-M06-campaign-123-1--00--demo",
                "campaign-123-1--00--demo",
            ),
            (
                "namespace-no-declarado",
                "ddd-state-123-M06-campaign-123-1--04--demo",
                None,
            ),
            (
                "sufijo-arbitrario",
                "ddd-state-123-M06-campaign-123-1--04--demo-extra",
                "campaign-123-1--04--demo",
            ),
        )
        with tempfile.TemporaryDirectory() as td:
            base=Path(td)
            for label,artifact_name,artifact_namespace in cases:
                with self.subTest(case=label):
                    result=self._synthetic_territorial_product_gate(
                        base/label,
                        artifact_name=artifact_name,
                        artifact_namespace=artifact_namespace,
                    )
                    self.assertEqual(result["decision"],"BLOQUEADO")
                    self.assertIn(
                        "NOMBRE_ARTEFACTO_NO_COINCIDE_CON_RUN",
                        result["reasons"],
                    )

    def test_territorial_product_gate_keeps_digest_mismatch_blocking_for_campaign_name(self):
        with tempfile.TemporaryDirectory() as td:
            namespace="campaign-123-2--04--demo"
            result=self._synthetic_territorial_product_gate(
                Path(td),
                artifact_name=f"ddd-state-123-M06-{namespace}",
                artifact_namespace=namespace,
                artifact_digest="a"*64,
                expected_digest="b"*64,
            )
            self.assertEqual(result["decision"],"BLOQUEADO")
            self.assertIn(
                "DIGEST_NO_COINCIDE_CON_EVIDENCIA_DURABLE",
                result["reasons"],
            )

    def test_reusable_gate_passes_declared_artifact_namespace_to_validator(self):
        root=Path(__file__).resolve().parents[1]
        gate=(root/".github/workflows/_reutilizable-puerta-validacion.yml").read_text(
            encoding="utf-8"
        )
        self.assertIn(
            "ARTIFACT_NAMESPACE: ${{ inputs.artifact_namespace }}".replace("\\$","$"),
            gate,
        )
        self.assertIn(
            '--artifact-namespace "$ARTIFACT_NAMESPACE"',
            gate,
        )

    def test_gate_rejects_artifact_name_from_another_run(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)/"artifact"; root.mkdir()
            (root/"manifest.json").write_text("{}",encoding="utf-8")
            result=validate_gate(phase="electoral_source",artifact_root=root,territory_id="demo",edition="2025",
                run_id="123",artifact_name="ddd-electoral-package-demo-2025-999",artifact_digest="a"*64)
            self.assertEqual(result["decision"],"BLOQUEADO")
            self.assertIn("NOMBRE_ARTEFACTO_NO_COINCIDE_CON_RUN",result["reasons"])

    def test_gate_rejects_digest_different_from_durable_evidence(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)/"artifact"; root.mkdir()
            (root/"manifest.json").write_text("{}",encoding="utf-8")
            result=validate_gate(phase="territorial_source",artifact_root=root,territory_id="demo",edition="2025",
                run_id="123",artifact_name="ddd-source-package-demo-2025-123",
                artifact_digest="a"*64,expected_digest="b"*64)
            self.assertEqual(result["decision"],"BLOQUEADO")
            self.assertIn("DIGEST_NO_COINCIDE_CON_EVIDENCIA_DURABLE",result["reasons"])

    def test_electoral_product_requires_application_evidence_and_m08_state(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)/"state"; audit=Path(td)/"audit"
            for name in ("cache","run","sources"): (root/name).mkdir(parents=True,exist_ok=True)
            audit.mkdir()
            (root/"run/CHAIN_STATE.json").write_text(json.dumps({"completed_stage":8}),encoding="utf-8")
            (audit/"production_status.json").write_text(json.dumps({
                "territory_id":"demo","decision":"PASS","scope_through_stage":"M06","electoral_application":True
            }),encoding="utf-8")
            params=Path(td)/"demo.yaml"
            params.write_text(yaml.safe_dump({"meta":{"year":2025}}),encoding="utf-8")
            result=validate_gate(phase="electoral_product",artifact_root=root,audit_root=audit,params=params,
                territory_id="demo",edition="2025",run_id="123",artifact_name="ddd-state-123-M08",artifact_digest="b"*64)
            self.assertEqual(result["decision"],"VALIDADO")

    def test_electoral_product_without_application_flag_requires_durable_legacy_digest(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)/"state"; audit=Path(td)/"audit"
            for name in ("cache","run","sources"): (root/name).mkdir(parents=True,exist_ok=True)
            audit.mkdir()
            (root/"run/CHAIN_STATE.json").write_text(json.dumps({"completed_stage":8}),encoding="utf-8")
            (audit/"production_status.json").write_text(json.dumps({
                "territory_id":"demo","decision":"PASS_WITH_EXCEPTIONS"
            }),encoding="utf-8")
            params=Path(td)/"demo.yaml"
            params.write_text(yaml.safe_dump({"meta":{"year":2025}}),encoding="utf-8")
            digest="c"*64
            current=validate_gate(phase="electoral_product",artifact_root=root,audit_root=audit,params=params,
                territory_id="demo",edition="2025",run_id="123",artifact_name="ddd-state-123-M08",artifact_digest=digest)
            self.assertEqual(current["decision"],"BLOQUEADO")
            self.assertIn("INCORPORACION_ELECTORAL_NO_ACREDITADA",current["reasons"])
            legacy=validate_gate(phase="electoral_product",artifact_root=root,audit_root=audit,params=params,
                territory_id="demo",edition="2025",run_id="123",artifact_name="ddd-state-123-M08",
                artifact_digest=digest,expected_digest=digest)
            self.assertEqual(legacy["decision"],"VALIDADO")

    def test_electoral_audit_progression_requires_final_accreditation(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)/"state"; initial=Path(td)/"audit-initial"; final=Path(td)/"audit-final"
            for name in ("cache","run","sources"): (root/name).mkdir(parents=True,exist_ok=True)
            initial.mkdir(); final.mkdir()
            (root/"run/CHAIN_STATE.json").write_text(json.dumps({"completed_stage":8}),encoding="utf-8")
            base={"territory_id":"demo","decision":"PASS_WITH_EXCEPTIONS","scope_through_stage":"M06"}
            (initial/"production_status.json").write_text(json.dumps(base),encoding="utf-8")
            accredited=dict(base)
            accredited["electoral_application"]=True
            (final/"production_status.json").write_text(json.dumps(accredited),encoding="utf-8")
            params=Path(td)/"demo.yaml"
            params.write_text(yaml.safe_dump({"meta":{"year":2025}}),encoding="utf-8")
            initial_result=validate_gate(
                phase="electoral_product",artifact_root=root,audit_root=initial,params=params,
                territory_id="demo",edition="2025",run_id="123",
                artifact_name="ddd-state-123-M08",artifact_digest="a"*64)
            self.assertEqual(initial_result["decision"],"BLOQUEADO")
            self.assertIn("INCORPORACION_ELECTORAL_NO_ACREDITADA",initial_result["reasons"])
            final_result=validate_gate(
                phase="electoral_product",artifact_root=root,audit_root=final,params=params,
                territory_id="demo",edition="2025",run_id="123",
                artifact_name="ddd-state-123-M08",artifact_digest="a"*64)
            self.assertEqual(final_result["decision"],"VALIDADO")

    def test_electoral_audit_artifact_cardinality_zero_one_two(self):
        root=Path(__file__).resolve().parents[1]
        gate_path=root/".github/workflows/_reutilizable-puerta-validacion.yml"
        incorporation_path=root/".github/workflows/_reutilizable-incorporacion-electoral.yml"
        gate_text=gate_path.read_text(encoding="utf-8")
        incorporation_text=incorporation_path.read_text(encoding="utf-8")
        for path in (gate_path,incorporation_path):
            parsed=yaml.load(path.read_text(encoding="utf-8"),Loader=yaml.BaseLoader)
            self.assertIsInstance(parsed,dict)
        self.assertIn('audit_name="ddd-audit-electoral-$resolved_run_id"',gate_text)
        self.assertIn('audit_name="ddd-audit-$resolved_run_id"',gate_text)
        self.assertIn("name: ddd-audit-electoral-${{ github.run_id }}".replace("\\$","$"),incorporation_text)
        self.assertNotIn("name: ddd-audit-${{ github.run_id }}\n          path: .ddd-audit".replace("\\$","$"),incorporation_text)
        jq_filter='[.artifacts[]|select(.name==$n and (.expired|not))]|length'
        self.assertIn(jq_filter,gate_text)
        audit_name="ddd-audit-electoral-123"
        historical_only={"artifacts":[{"name":"ddd-audit-123","expired":False,"id":99}]}
        historical_count=len([
            row for row in historical_only["artifacts"]
            if row.get("name")==audit_name and not row.get("expired",False)
        ])
        self.assertEqual(historical_count,0)
        for count in (0,1,2):
            payload={"artifacts":[
                {"name":audit_name,"expired":False,"id":idx+1}
                for idx in range(count)
            ]}
            observed=len([
                row for row in payload["artifacts"]
                if row.get("name")==audit_name and not row.get("expired",False)
            ])
            self.assertEqual(observed,count)
            self.assertEqual(observed==1,count==1)

    def test_product_gate_rejects_contract_from_other_edition(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)/"state"; audit=Path(td)/"audit"
            for name in ("cache","run","sources"): (root/name).mkdir(parents=True,exist_ok=True)
            audit.mkdir()
            (root/"run/CHAIN_STATE.json").write_text(json.dumps({"completed_stage":6}),encoding="utf-8")
            (audit/"production_status.json").write_text(json.dumps({
                "territory_id":"demo","decision":"PASS"
            }),encoding="utf-8")
            params=Path(td)/"demo.yaml"
            params.write_text(yaml.safe_dump({"meta":{"year":2024}}),encoding="utf-8")
            result=validate_gate(phase="territorial_product",artifact_root=root,audit_root=audit,params=params,
                territory_id="demo",edition="2025",run_id="123",artifact_name="ddd-state-123-M06",artifact_digest="d"*64)
            self.assertEqual(result["decision"],"BLOQUEADO")
            self.assertIn("EDICION_CONTRATO_NO_COINCIDE",result["reasons"])


if __name__=="__main__":
    unittest.main()
