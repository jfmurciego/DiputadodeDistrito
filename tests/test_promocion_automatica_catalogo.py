from __future__ import annotations

import unittest
from pathlib import Path

import yaml

from herramientas.catalogo_preparacion import lookup
from herramientas.resolver_fuentes_territorio import territories
from herramientas.promover_catalogo_tras_preparacion import (
    contract_is_generation_complete,
)

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
        self.assertEqual(evidence["run_id"], 35475119597)
        self.assertEqual(
            evidence["artifact_name"],
            "ddd-source-package-extremadura-2025-35475119597",
        )
        self.assertEqual(
            evidence["artifact_sha256"],
            "f115ec74a9241e796fcef231a0400121d218b22dbeb8d22d467665c671d94c1a",
        )

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
        self.assertIn("Extremadura", options)
        promoter = (ROOT / "herramientas/promover_catalogo_tras_preparacion.py").read_text(encoding="utf-8")
        self.assertNotIn(".github/workflows/produccion-distritos.yml", promoter)

    def test_catalog_state_bounds_accept_current_catalog_indentation(self):
        from herramientas.promover_catalogo_tras_preparacion import _catalog_state_bounds

        lines = CAT.read_text(encoding="utf-8").splitlines()
        start, end = _catalog_state_bounds(lines, "galicia", "2025")
        block = lines[start:end]
        self.assertTrue(any(line.strip() == "preparation_status: READY" for line in block))
        self.assertTrue(any(line.strip() == "contract_path: territorios/galicia/config/galicia_2025.yaml" for line in block))

    def test_master_catalog_matches_extremadura_promotion(self):
        master = yaml.safe_load(MASTER.read_text(encoding="utf-8"))
        row = next(r for r in master["territories"] if r["territory_id"] == "extremadura")
        self.assertEqual(row["status"], "generation_ready")
        self.assertEqual(row["contract_level"], "production_m01_m06")
        self.assertEqual(row["production_authorization"], "AUTHORIZED")


if __name__ == "__main__":
    unittest.main()
