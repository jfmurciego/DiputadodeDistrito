"""Version: 1.0.3; name: F10 Valencian receipt regression; date: 2026-10-28.
Scope: Valencian independent-source receipt and fail-closed F10 projection.
Status: candidate. Change/reason: exact counts and receipts run on the frozen aee8215e root
(tests/_raiz_congelada.py), so new full runs do not change the historical case.
Previous: legacy/tests/test_f10_valencia_2023_durable_receipt_v1.0.2_20261028.py.
"""
from __future__ import annotations

import copy
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from herramientas import consumir_par_fuentes_legislatura as consumer
from herramientas.estado_derivado_f10 import _geometric_admissibility, derive_f10
from herramientas.identidad_fuentes_legislatura import territorial_identity
from herramientas.resolver_preparacion_legislatura import resolve

from tests._raiz_congelada import frozen_root  # noqa: E402

# Estado congelado en aee8215e: los recuentos y receipts exactos no dependen de las ejecuciones
# completas posteriores, que reescriben catálogo y productos en main.
ROOT = frozen_root()
VERSION = ROOT / (
    "territorios/comunidad_valenciana/evidencia/fuentes_territoriales/2025/"
    "94f094a23493448d9ee38f1b51fe6f73dd0f29b6b7a4410eae8bb5a170c38d62/39315133646"
)


class Valencia2023DurableReceiptTests(unittest.TestCase):
    def test_receipt_is_consumed_at_exact_2023_years_without_promoting_old_lineage(self):
        row, receipt = consumer.validate_territorial_receipt(
            root_dir=ROOT, territory="comunidad_valenciana", edition="2025"
        )
        self.assertEqual("ddd.territorial-source-receipt/1.0", receipt["schema"])
        self.assertEqual((2025, 2023, 2023),
                         (int(receipt["edition"]), receipt["population_year"], receipt["section_year"]))
        self.assertEqual(39315133646, receipt["run_id"])
        self.assertEqual(36273981926, row["preparation_evidence"]["run_id"])
        self.assertIs(row["independent_source_evidence"]["promoted"], False)
        self.assertEqual("AUTHENTIC_EVIDENCE_ONLY_HISTORICAL_PRODUCT_LINEAGE_PRESERVED",
                         row["independent_source_evidence"]["status"])
        self.assertIs(row["territorial_product_available"], False)
        self.assertIsNone(row["last_valid_checkpoint"])

        plan = resolve(ROOT, "Comunidad Valenciana")["plans"][0]
        self.assertEqual((2023, 2023), (plan["population_year_selected"], plan["section_year_selected"]))
        self.assertEqual("REUSE", plan["territorial_action"])
        self.assertEqual("ADMISSIBLE", plan["territorial_admissibility"])
        self.assertEqual("ADMISSIBLE", plan["electoral_admissibility"])
        self.assertIs(plan["blocked"], False)

    def test_f10_closes_acquisition_but_keeps_geometry_admissibility_blocked(self):
        projection = derive_f10(ROOT)
        cv = next(row for row in projection["territories"]
                  if row["territory_id"] == "comunidad_valenciana")
        self.assertEqual("CLOSED", cv["territorial_acquisition"])
        self.assertEqual("BLOCKED", cv["territorial_admissibility"])
        self.assertIn("M02_CONTRACT_NOT_BOUND_TO_2023", cv["territorial_admissibility_reason"][0])
        self.assertEqual({"PASS": 18, "BLOCKED": 1},
                         projection["counts"]["territorial_admissibility"])
        self.assertEqual({"CLOSED": 19},
                         projection["counts"]["territorial_acquisition"])
        self.assertFalse(projection["production_authorized"])

        state, receipt = consumer.validate_territorial_receipt(
            root_dir=ROOT, territory="comunidad_valenciana", edition="2025"
        )
        state["independent_source_evidence"]["geometry_assessment_sha256"] = "0" * 64
        status, reasons, _ = _geometric_admissibility(ROOT, state, receipt, "PASS")
        self.assertEqual("BLOCKED", status)
        self.assertEqual(["GEOMETRY_ASSESSMENT_HASH_MISMATCH"], reasons)

    def test_wrong_edition_package_hash_or_identity_is_rejected_by_receipt_consumer(self):
        row, receipt = consumer.validate_territorial_receipt(
            root_dir=ROOT, territory="comunidad_valenciana", edition="2025"
        )
        for field, value, message in (
            ("edition", "2024", "identidad"),
            ("package_sha256", "0" * 64, "contradice"),
            ("territorial_identity_sha256", "0" * 64, "contradice"),
        ):
            with tempfile.TemporaryDirectory() as tmp:
                tampered = copy.deepcopy(receipt)
                tampered[field] = value
                path = Path(tmp) / "receipt.json"
                path.write_text(json.dumps(tampered), encoding="utf-8")
                state = copy.deepcopy(row)
                state["independent_source_evidence"]["receipt_path"] = str(path)
                with mock.patch.object(consumer, "_catalog_row", return_value=state):
                    with self.subTest(field=field), self.assertRaisesRegex(
                        consumer.PreparedPairExecutionBlock, message
                    ):
                        consumer.validate_territorial_receipt(
                            root_dir=ROOT, territory="comunidad_valenciana", edition="2025"
                        )

    def test_full_original_input_hashes_and_geometry_results_are_pinned(self):
        expected_hashes = {
            "03": "fc0e20f94d6e54dc35885977c053212d1ff5bbe6250101d9b2acf4ca1215fe46",
            "12": "dcb5f4f0a872f86ca20ed80e10028ed32d259e8bef70f890746e4f007c87f24b",
            "46": "07c84a0eb2b570cb43b975fe7d3eccdd842f7b4e56bef23c837271f1aab1358c",
        }
        for province, expected in expected_hashes.items():
            path = VERSION / "originales" / f"{province}.geojson"
            self.assertEqual(expected, hashlib.sha256(path.read_bytes()).hexdigest())

        evidence = json.loads((VERSION / "evidencia_geometrica.json").read_text(encoding="utf-8"))
        m02 = evidence["m02"]
        # This result is reproducible under the 2025 operational configuration,
        # but it cannot be transferred to source edition 2023 without binding.
        self.assertEqual("EPSG:25830", m02["working_crs"])
        self.assertEqual(1.0, m02["max_precision_overlap_area_m2"])
        self.assertEqual(0.0, m02["buffer_m"])
        self.assertEqual(0.0, m02["simplify_m"])
        self.assertEqual(0, m02["pairs_over_1m2"])
        self.assertEqual(148, m02["total_positive_area_pairs_in_full_universe"])
        self.assertLess(m02["target_pairs"]["4617201001/4619401008"]["intersection_area_m2"], 1.0)
        self.assertLess(m02["target_pairs"]["4617201001/4619401013"]["intersection_area_m2"], 1.0)
        self.assertEqual(3503, evidence["m03"]["nodes"])
        self.assertEqual(5216195, evidence["m03"]["total_pop"])
        self.assertEqual(0, evidence["m03"]["isolated"])

        assessment = json.loads((VERSION / "m02_contract_assessment_2023.json").read_text())
        self.assertEqual("BLOCKED", assessment["decision"])
        self.assertEqual("UNBOUND_TO_SOURCE_EDITION", assessment["contract_binding"])
        self.assertEqual("EPSG:3035", assessment["execution"]["working_crs"])
        self.assertEqual(2, assessment["execution"]["pairs_over_threshold"])
        self.assertAlmostEqual(11.827709239674732,
                               assessment["execution"]["target_pairs"]["4617201001/4619401008"]["overlap_area_m2"])
        self.assertAlmostEqual(12.111237796381374,
                               assessment["execution"]["target_pairs"]["4617201001/4619401013"]["overlap_area_m2"])

    def test_national_doors_update_only_territorial_cv_and_keep_other_gates_blocked(self):
        projection = derive_f10(ROOT)
        self.assertEqual({"CLOSED": 19}, projection["counts"]["territorial_acquisition"])
        self.assertEqual({"ADMISSIBLE": 15, "BLOCKED": 4}, projection["counts"]["electoral_admissibility"])
        self.assertEqual({"BLOCKED": 5, "PASS": 14}, projection["counts"]["joint_admissibility"])
        self.assertFalse(projection["production_authorized"])
        cv = next(row for row in projection["territories"] if row["territory_id"] == "comunidad_valenciana")
        self.assertEqual("CLOSED", cv["territorial_acquisition"])
        self.assertEqual("ADMISSIBLE", cv["electoral_admissibility"])
        self.assertEqual("BLOCKED", cv["joint_admissibility"])


if __name__ == "__main__":
    unittest.main()
