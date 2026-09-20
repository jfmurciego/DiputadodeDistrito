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
