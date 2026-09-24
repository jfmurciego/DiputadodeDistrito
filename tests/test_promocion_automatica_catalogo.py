from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

import yaml

from herramientas.catalogo_preparacion import lookup
from herramientas.resolver_fuentes_territorio import territories
from herramientas.promover_catalogo_tras_preparacion import (
    _set_catalog_state,
    contract_is_generation_complete,
)
from herramientas.promover_catalogo_operacional import promote
from herramientas.catalogo_preparacion import validate_repository

ROOT = Path(__file__).resolve().parents[1]
PREP = ROOT / ".github/workflows/preparacion-fuentes.yml"
GEN = ROOT / ".github/workflows/produccion-distritos.yml"
CAT = ROOT / "configuracion/catalogo_preparacion.yaml"
MASTER = ROOT / "configuracion/catalogo_territorios_espana_2025.yaml"
EXT = ROOT / "territorios/extremadura/config/extremadura_2025.yaml"


class AutomaticCatalogPromotionTests(unittest.TestCase):
    def test_preparation_workflow_promotes_in_serialized_lightweight_job(self):
        text = PREP.read_text(encoding="utf-8")
        data = yaml.safe_load(text)
        self.assertEqual(data["permissions"]["contents"], "write")
        self.assertIn("registrar",data["jobs"])
        register=data["jobs"]["registrar"]
        self.assertEqual(register["concurrency"]["group"],"ddd-catalog-promotion")
        self.assertFalse(register["concurrency"]["cancel-in-progress"])
        run="\n".join(step.get("run","") for step in register["steps"])
        self.assertIn("python -m herramientas.promover_catalogo_tras_preparacion", run)
        self.assertNotIn("python herramientas/promover_catalogo_tras_preparacion.py", run)
        self.assertIn("--run-id",run)
        self.assertIn("--artifact-name",run)
        self.assertIn("--artifact-sha256",run)
        self.assertIn("git push origin",run)
        upload_steps=data["jobs"]["territoriales"]["steps"]
        self.assertTrue(any(step.get("id")=="upload" for step in upload_steps))

    def test_preparation_uses_standard_github_token_for_catalog_promotion(self):
        text = PREP.read_text(encoding="utf-8")
        self.assertIn("github.token", text)
        self.assertNotIn("DDD_WORKFLOW_TOKEN", text)
        self.assertNotIn(".github/workflows/produccion-distritos.yml", text)

    def test_extremadura_preparation_evidence_is_durable(self):
        row = lookup("Extremadura", "2025", CAT)
        self.assertTrue(row["territorial_sources_prepared"])
        self.assertTrue(row["territorial_contract_complete"])
        self.assertEqual(row["production_authorization"], "AUTHORIZED")
        evidence = row["preparation_evidence"]
        self.assertEqual(evidence["run_id"], 35755043806)
        self.assertEqual(
            evidence["artifact_name"],
            "ddd-source-package-extremadura-2025-35755043806",
        )
        self.assertEqual(
            evidence["artifact_sha256"],
            "fd7632e9af10d0584c5d5a9b8d1e3c173f5b0002695e95242566710fe61b9347",
        )
        self.assertEqual(
            evidence["package_sha256"],
            "edd43c6e3589825100d73dd9ecb5af054cf65b3013987616afe5b901f1affb07",
        )
        self.assertNotIn("stage", evidence)

    def test_extremadura_contract_is_generation_complete(self):
        complete, reasons = contract_is_generation_complete(EXT)
        self.assertTrue(complete, reasons)
        contract = yaml.safe_load(EXT.read_text(encoding="utf-8"))
        self.assertEqual(contract["meta"]["contract_level"], "production_m01_m06")
        self.assertEqual(contract["meta"]["production_authorization"], "AUTHORIZED")

    def test_generation_selector_is_stable_and_catalog_gates_readiness(self):
        data = yaml.safe_load(GEN.read_text(encoding="utf-8"))
        triggers = data.get("on") or data.get(True)
        options = triggers["workflow_dispatch"]["inputs"]["territory_id"]["options"]
        expected = [r["name"] for r in territories()]
        self.assertEqual(options, expected)
        self.assertIn("11 · Extremadura", options)
        promoter = (ROOT / "herramientas/promover_catalogo_tras_preparacion.py").read_text(encoding="utf-8")
        self.assertNotIn(".github/workflows/produccion-distritos.yml", promoter)

    def test_catalog_state_bounds_accept_current_catalog_indentation(self):
        from herramientas.promover_catalogo_tras_preparacion import _catalog_state_bounds

        lines = CAT.read_text(encoding="utf-8").splitlines()
        start, end = _catalog_state_bounds(lines, "galicia", "2025")
        block = lines[start:end]
        self.assertTrue(any(line.strip() == "preparation_status: READY" for line in block))
        self.assertTrue(any(line.strip() == "contract_path: territorios/galicia/config/galicia_2025.yaml" for line in block))

    def test_preparation_evidence_is_inserted_after_complete_checkpoint_block(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "catalogo.yaml"
            path.write_text(
                """schema: ddd-preparation-catalog/1.1
territories:
- territory_id: demo
  name: Demo
  editions:
    '2025':
      territory_declared: true
      preparation_status: READY
      contract_path: territorios/demo/config/demo_2025.yaml
      territorial_source_declaration: territorios/demo/config/fuentes_oficiales.yaml
      electoral_source_declaration: null
      territorial_sources_prepared: true
      territorial_contract_complete: true
      territorial_product_available: true
      electoral_source_prepared: false
      electoral_product_available: false
      territorial_certification: PASS_WITH_GOVERNED_EXCEPTIONS
      production_authorization: AUTHORIZED
      last_valid_checkpoint:
        run_id: 111
        stage: M06
""",
                encoding="utf-8",
            )
            _set_catalog_state(
                path,
                territory_id="demo",
                edition="2025",
                source_declaration="territorios/demo/config/fuentes_oficiales.yaml",
                contract_complete=True,
                run_id=222,
                artifact_name="ddd-source-package-demo-2025-222",
                artifact_sha256="a" * 64,
                package_sha256="b" * 64,
                contract_path="territorios/demo/config/demo_2025.yaml",
            )
            state = yaml.safe_load(path.read_text(encoding="utf-8"))["territories"][0]["editions"]["2025"]
            self.assertEqual(state["last_valid_checkpoint"], {"run_id": 111, "stage": "M06"})
            self.assertEqual(
                state["preparation_evidence"],
                {
                    "run_id": 222,
                    "artifact_name": "ddd-source-package-demo-2025-222",
                    "artifact_sha256": "a" * 64,
                    "package_sha256": "b" * 64,
                },
            )

    def test_electoral_source_can_be_promoted_from_materialized_contract_without_declaration(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            (root/"configuracion").mkdir()
            (root/"territorios/demo/config/elecciones").mkdir(parents=True)
            (root/"territorios/demo/evidencia/catalogo").mkdir(parents=True)
            election_contract=root/"territorios/demo/config/elecciones/demo_2026.json"
            election_contract.write_text(json.dumps({
                "schema_family":"ddd-election","schema_version":"1.0.0",
                "territory_id":"demo","election_id":"demo_2026","election_date":"2026-02-08",
                "sources":[{"path":"inputs/results.json","sha256":"0"*64}],
            }),encoding="utf-8")
            params=root/"territorios/demo/config/demo_2025.yaml"
            params.write_text(yaml.safe_dump({
                "meta":{"territory_id":"demo","year":2025,"contract_level":"production_m01_m06","production_authorization":"AUTHORIZED"},
                "modulos":{"modulo_07_agregar_resultados_electorales":{
                    "election_contract":"territorios/demo/config/elecciones/demo_2026.json"
                }},
            },sort_keys=False),encoding="utf-8")
            catalog={
                "schema":"ddd-preparation-catalog/1.1",
                "territories":[{
                    "territory_id":"demo","name":"Demo",
                    "editions":{"2025":{
                        "territory_declared":True,"preparation_status":"READY",
                        "contract_path":"territorios/demo/config/demo_2025.yaml",
                        "territorial_source_declaration":"territorios/demo/config/fuentes.yaml",
                        "electoral_source_declaration":None,
                        "territorial_sources_prepared":True,"territorial_contract_complete":True,
                        "territorial_product_available":False,"electoral_source_prepared":False,
                        "electoral_product_available":False,"territorial_certification":"NOT_CERTIFIED",
                        "production_authorization":"AUTHORIZED","last_valid_checkpoint":None,
                    }}
                }]
            }
            (root/"configuracion/catalogo_preparacion.yaml").write_text(
                yaml.safe_dump(catalog,sort_keys=False),encoding="utf-8"
            )
            result=promote(
                root_dir=root,kind="electoral_source",territory_id="demo",edition="2025",
                run_id=123,artifact_name="ddd-electoral-package-demo-2025-123",
                artifact_sha256="1"*64,declaration=None,election_id="demo_2026",source_commit="abc",
            )
            self.assertTrue(result["incorporation_enabled"] is False)
            receipt=json.loads((root/"territorios/demo/evidencia/catalogo/electoral_source_2025.json").read_text(encoding="utf-8"))
            self.assertIsNone(receipt["declaration"])
            self.assertEqual(receipt["election_contract"],"territorios/demo/config/elecciones/demo_2026.json")
            self.assertEqual(receipt["election_id"],"demo_2026")
            self.assertEqual(
                receipt["election_contract_sha256"],
                hashlib.sha256(election_contract.read_bytes()).hexdigest(),
            )

    def test_master_catalog_matches_extremadura_promotion(self):
        master = yaml.safe_load(MASTER.read_text(encoding="utf-8"))
        row = next(r for r in master["territories"] if r["territory_id"] == "extremadura")
        self.assertEqual(row["status"], "generation_ready")
        self.assertEqual(row["contract_level"], "production_m01_m06")
        self.assertEqual(row["production_authorization"], "AUTHORIZED")


if __name__ == "__main__":
    unittest.main()
