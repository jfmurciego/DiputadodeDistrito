from __future__ import annotations
import json
import tempfile
import unittest
from pathlib import Path
import yaml

from herramientas.validar_elegibilidad_incorporacion_electoral import resolve_eligibility

ROOT=Path(__file__).resolve().parents[1]
ORCH=ROOT/".github/workflows/ejecucion-completa-proyecto.yml"
WF04=ROOT/".github/workflows/incorporacion-resultados-electorales.yml"

def fixture(prepared: bool):
    td=tempfile.TemporaryDirectory(); root=Path(td.name)
    (root/"configuracion").mkdir(parents=True)
    (root/"territorios/castilla_la_mancha/config").mkdir(parents=True)
    required={
      "territory_declared":True,"preparation_status":"READY",
      "contract_path":"territorios/castilla_la_mancha/config/castilla_la_mancha_2025.yaml",
      "territorial_source_declaration":"territorios/castilla_la_mancha/config/fuentes_oficiales.yaml",
      "electoral_source_declaration":None,"territorial_sources_prepared":True,
      "territorial_contract_complete":True,"territorial_product_available":True,
      "electoral_source_prepared":prepared,"electoral_product_available":False,
      "territorial_certification":"PASS_WITH_GOVERNED_EXCEPTIONS",
      "production_authorization":"AUTHORIZED",
      "last_valid_checkpoint":{"run_id":36402139263,"stage":"M06"},
    }
    catalog={"schema":"ddd-preparation-catalog/1.1","default_edition":"2025","territories":[
      {"territory_id":"castilla_la_mancha","name":"Castilla-La Mancha","editions":{"2025":required}}
    ]}
    (root/"configuracion/catalogo_preparacion.yaml").write_text(yaml.safe_dump(catalog,allow_unicode=True,sort_keys=False),encoding="utf-8")
    (root/"configuracion/registro_electoral.yaml").write_text(yaml.safe_dump({
      "schema":"ddd-election-registry/1.0","edition":"2025","territories":{"castilla_la_mancha":{
        "codauto":"08","name":"Castilla-La Mancha","election_id":"castilla_la_mancha_cortes_2023",
        "election_date":"2023-05-28","title":"Cortes de Castilla-La Mancha 2023"}}},allow_unicode=True,sort_keys=False),encoding="utf-8")
    (root/"territorios/castilla_la_mancha/config/castilla_la_mancha_2025.yaml").write_text(yaml.safe_dump({
      "meta":{"territory_id":"castilla_la_mancha","year":"2025","production_authorization":"AUTHORIZED","contract_level":"production_m01_m06"}
    },allow_unicode=True,sort_keys=False),encoding="utf-8")
    digest="24dab5f8ae7bcc4c2704ceb1deba6a2a0458a53151be6f1567232a8d1652302a"
    gate=root/"puerta.json"; manifest=root/"manifest.json"
    gate.write_text(json.dumps({"schema":"ddd.puerta-validacion/1.0","phase":"electoral_source","decision":"VALIDADO",
      "phase_decision":"ACQUIRE","territory_id":"castilla_la_mancha","edition":"2025","run_id":36402139263,
      "artifact_name":"ddd-electoral-package-castilla_la_mancha-2025-36402139263","artifact_digest":"sha256:"+digest,
      "expected_digest":None,"reasons":[]}),encoding="utf-8")
    manifest.write_text(json.dumps({"schema":"ddd-electoral-package/1.0","decision":"ACQUIRE","territory_id":"castilla_la_mancha",
      "edition":"2025","election_id":"castilla_la_mancha_cortes_2023","election_date":"2023-05-28"}),encoding="utf-8")
    return td,root,gate,manifest,digest

class ElectoralIncorporationEligibilityTests(unittest.TestCase):
    def test_same_run_gate_enables_04_even_if_frozen_catalog_says_false(self):
        td,root,gate,manifest,digest=fixture(False); self.addCleanup(td.cleanup)
        result=resolve_eligibility(root_dir=root,territory="Castilla-La Mancha",edition="2025",
          gate_evidence=gate,package_manifest=manifest,expected_run_id="36402139263",
          expected_artifact_name="ddd-electoral-package-castilla_la_mancha-2025-36402139263",
          expected_artifact_digest=digest)
        self.assertEqual(result["route"],"validated_gate_evidence")
        self.assertEqual(result["election_id"],"castilla_la_mancha_cortes_2023")

    def test_previously_accredited_source_keeps_catalog_route(self):
        td,root,_,_,_=fixture(True); self.addCleanup(td.cleanup)
        result=resolve_eligibility(root_dir=root,territory="Castilla-La Mancha",edition="2025")
        self.assertEqual(result["route"],"catalog_accredited")

    def test_missing_unvalidated_identity_or_digest_mismatch_blocks(self):
        td,root,gate,manifest,digest=fixture(False); self.addCleanup(td.cleanup)
        base=dict(root_dir=root,territory="Castilla-La Mancha",edition="2025",gate_evidence=gate,
          package_manifest=manifest,expected_run_id="36402139263",
          expected_artifact_name="ddd-electoral-package-castilla_la_mancha-2025-36402139263",
          expected_artifact_digest=digest)
        missing=dict(base); missing["gate_evidence"]=None
        with self.assertRaisesRegex(ValueError,"evidencia explícita incompleta"): resolve_eligibility(**missing)
        original_gate=json.loads(gate.read_text()); original_manifest=json.loads(manifest.read_text())
        cases=[
          ({**original_gate,"decision":"BLOQUEADO"},original_manifest,digest,"no validada"),
          ({**original_gate,"territory_id":"galicia"},original_manifest,digest,"territorio de la puerta"),
          (original_gate,{**original_manifest,"election_id":"otra_eleccion"},digest,"election_id"),
          (original_gate,original_manifest,"0"*64,"digest electoral de la puerta"),
        ]
        for gp,mp,ed,reason in cases:
            gate.write_text(json.dumps(gp)); manifest.write_text(json.dumps(mp))
            with self.assertRaisesRegex(ValueError,reason):
                resolve_eligibility(**{**base,"expected_artifact_digest":ed})
            gate.write_text(json.dumps(original_gate)); manifest.write_text(json.dumps(original_manifest))

    def test_workflow_carries_gate_digest_and_preserves_catalog_fallback(self):
        orch=ORCH.read_text(encoding="utf-8"); wf=WF04.read_text(encoding="utf-8")
        self.assertIn("needs.puerta_03.outputs.artifact_digest",orch)
        self.assertIn("electoral_package_artifact_digest:",wf)
        self.assertIn("ddd-puerta-electoral_source-$GITHUB_RUN_ID",wf)
        self.assertIn("validar_elegibilidad_incorporacion_electoral.py",wf)
        self.assertIn("catalogo_preparacion.py lookup",wf)
        self.assertIn("resolve --mode electoral_application",wf)

if __name__=="__main__":
    unittest.main()