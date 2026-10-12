"""F10 v1.0.0 — receipts auténticos INE 2025/2025; 2026 electoral sigue bloqueada.
Fecha: 2026-10-12. Alcance: evidencia territorial independiente; sin promoción ni producción.
Origen: ZIP protegido DDD_F10_5_ARTEFACTOS_AUTENTICOS_20261011 y receipts #179 ya versionados.
"""
import json
import unittest
from pathlib import Path

import yaml
from herramientas.consumir_par_fuentes_legislatura import validate_territorial_receipt
from herramientas.resolver_preparacion_legislatura import resolve

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "docs/AUDITORIAS/F10_RECIBOS_2025_20261012/VERIFICACION.json"
CATALOG = ROOT / "configuracion/catalogo_preparacion.yaml"


class F10Receipts2025Tests(unittest.TestCase):
    def test_real_receipts_match_catalogue_and_preserve_historical_preparation(self):
        evidence = json.loads(MANIFEST.read_text(encoding="utf-8"))
        for item in evidence["rows"]:
            tid = item["territory_id"]
            with self.subTest(territory=tid):
                state, receipt = validate_territorial_receipt(root_dir=ROOT, territory=tid, edition="2025")
                self.assertEqual(item["run_id"], receipt["run_id"])
                self.assertEqual(item["artifact_sha256"], receipt["artifact_sha256"])
                self.assertEqual(item["package_sha256"], receipt["package_sha256"])
                self.assertEqual(item["compatibility_report_sha256"], receipt["compatibility_report_sha256"])
                self.assertEqual(item["compatibility_identity_sha256"], receipt["compatibility_identity_sha256"])
                self.assertEqual((2025, 2025), (receipt["population_year"], receipt["section_year"]))
                self.assertEqual(item["historic_preparation_run"], state["preparation_evidence"]["run_id"])
                self.assertIs(state["independent_source_evidence"]["promoted"], False)
                self.assertEqual("AUTHENTIC_EVIDENCE_ONLY_HISTORICAL_PRODUCT_LINEAGE_PRESERVED", state["independent_source_evidence"]["status"])

    def test_2026_electoral_compatibility_is_not_certified_by_2025_receipt(self):
        for tid in ("andalucia", "aragon", "castilla_y_leon"):
            with self.subTest(territory=tid):
                plan = resolve(ROOT, tid)["plans"][0]
                self.assertEqual(plan["population_year_selected"], 2025)
                self.assertEqual(plan["section_year_selected"], 2025)
                self.assertEqual(plan["electoral_2026_crosswalk_status"], "BLOCKED_PENDING_OFFICIAL_EVIDENCE")
                self.assertEqual(plan["territorial_action"], "REUSE_TEMPORAL_SUBSTITUTION")
                self.assertEqual(plan["territorial_admissibility"], "ADMISSIBLE_TEMPORAL_SUBSTITUTION")
                self.assertEqual(plan["electoral_admissibility"], "BLOCKED")
                self.assertEqual(plan["sources_status"], "BLOCKED")
                self.assertIs(plan["generation_authorized_by_reference_decision"], False)

    def test_corrupted_independent_receipt_fails_closed_in_planner(self):
        from unittest import mock
        from herramientas import resolver_preparacion_legislatura as planner
        for promoted, status in ((True, "AUTHENTIC_EVIDENCE_ONLY_HISTORICAL_PRODUCT_LINEAGE_PRESERVED"), (False, "READY")):
            state = next(r for r in yaml.safe_load(CATALOG.read_text())["territories"] if r["territory_id"] == "aragon")["editions"]["2025"]
            import copy
            mutated = copy.deepcopy(state)
            mutated["independent_source_evidence"]["promoted"] = promoted
            mutated["independent_source_evidence"]["status"] = status
            with self.subTest(promoted=promoted, status=status), mock.patch.object(
                planner, "_catalog_state", return_value=({"territory_id":"aragon"}, mutated)
            ):
                plan = resolve(ROOT, "Aragón")["plans"][0]
                self.assertEqual(plan["territorial_action"], "ACQUIRE")
                self.assertEqual(plan["territorial_candidate"]["reason"], "TERRITORIAL_RECEIPT_CONTRADICTORY")

    def test_original_product_source_runs_remain_unchanged(self):
        records = yaml.safe_load(CATALOG.read_text(encoding="utf-8"))["territories"]
        indexed = {x["territory_id"]:x["editions"]["2025"] for x in records}
        self.assertEqual(indexed["aragon"]["last_valid_checkpoint"]["run_id"], 36321736287)
        self.assertEqual(indexed["castilla_y_leon"]["last_valid_checkpoint"]["run_id"], 35889595424)
        self.assertIsNone(indexed["andalucia"]["last_valid_checkpoint"])
        self.assertNotIn("independent_source_evidence",indexed["comunidad_valenciana"])
