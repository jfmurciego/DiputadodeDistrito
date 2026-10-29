"""Version: 1.1.6; name: F10 derived doors regressions; date: 2026-10-29.
Scope: deterministic failure-closed validation of F10 receipts and task cards.
Status: candidate. Change/reason: a newer same-year re-download inherits the F10 closure
(estado_derivado_f10 1.1.4); another year still requires a new audit.
Previous: legacy/tests/test_f10_derived_doors_v1.1.5_20261029.py.
"""
from __future__ import annotations

import copy
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from herramientas.estado_derivado_f10 import (
    _validate_activity_cards,
    check_territorial_evidence,
    derive_f10,
    replay_snapshots,
    work_items_for,
)


from tests._raiz_congelada import frozen_root  # noqa: E402

# Estado congelado en aee8215e: los recuentos y receipts exactos no dependen de las ejecuciones
# completas posteriores, que reescriben catálogo y productos en main.
ROOT = frozen_root()
SNAPSHOTS = json.loads((ROOT / "tests/fixtures/f10_auto/snapshots.json").read_text())
PLAN_OVERLAY = json.loads((ROOT / "configuracion/puertas_f10.v1.json").read_text())
AUTHORIZATIONS = {
    "local_read_only": ["investigation", "diagnostics", "local_tests", "independent_review", "preserve_evidence"]
}


class F10DerivedDoorsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.projection = derive_f10(ROOT, activity_authorizations=AUTHORIZATIONS)

    def test_real_receipts_rederive_four_independent_counts(self):
        self.assertEqual({"CLOSED": 19}, self.projection["counts"]["territorial_acquisition"])
        self.assertEqual({"PASS": 18, "BLOCKED": 1}, self.projection["counts"]["territorial_admissibility"])
        self.assertEqual({"ADMISSIBLE": 15, "BLOCKED": 4}, self.projection["counts"]["electoral_admissibility"])
        self.assertEqual({"BLOCKED": 5, "PASS": 14}, self.projection["counts"]["joint_admissibility"])
        self.assertEqual({"NOT_AUTHORIZED_BY_F10": 19}, self.projection["counts"]["production"])
        self.assertEqual("PENDING", self.projection["f10_global"])
        self.assertIn("adquisición territorial CLOSED 19/19", self.projection["f10_global_reason"])
        self.assertIn("admisibilidad electoral ADMISSIBLE 15/19", self.projection["f10_global_reason"])
        self.assertEqual([], self.projection["catalog_validation_errors"])

    def test_independent_receipts_are_not_promoted_or_used_as_historical_products(self):
        rows = {row["territory_id"]: row for row in self.projection["territories"]}
        for territory_id, run_id in (("andalucia", 38082966768), ("aragon", 38093067883),
                                     ("castilla_y_leon", 38091055890), ("extremadura", 38091144559)):
            with self.subTest(territory=territory_id):
                self.assertEqual("CLOSED", rows[territory_id]["territorial_acquisition"])
                self.assertEqual(run_id, rows[territory_id]["territorial_run_id"])
        self.assertEqual("CLOSED", rows["comunidad_valenciana"]["territorial_acquisition"])
        self.assertEqual(39315133646, rows["comunidad_valenciana"]["territorial_run_id"])
        self.assertEqual("BLOCKED", rows["comunidad_valenciana"]["territorial_admissibility"])

    def test_historical_receipt_arrivals_replay_A_through_D(self):
        stages = {
            "A": SNAPSHOTS["A"],
            "B": SNAPSHOTS["A"] + SNAPSHOTS["B_add"],
            "C": SNAPSHOTS["A"] + SNAPSHOTS["B_add"] + SNAPSHOTS["C_add"],
            "D": SNAPSHOTS["A"] + SNAPSHOTS["B_add"] + SNAPSHOTS["C_add"] + SNAPSHOTS["D_add"],
        }
        replay = replay_snapshots(self.projection["territories"], stages, AUTHORIZATIONS, PLAN_OVERLAY["activities"])
        self.assertEqual({"BLOCKED": 5, "CLOSED": 14}, replay["A"]["counts"]["territorial_acquisition"])
        self.assertEqual({"BLOCKED": 4, "CLOSED": 15}, replay["B"]["counts"]["territorial_acquisition"])
        self.assertEqual({"BLOCKED": 1, "CLOSED": 18}, replay["C"]["counts"]["territorial_acquisition"])
        self.assertEqual(replay["C"]["counts"], replay["D"]["counts"])
        self.assertEqual({"BLOCKED": 5, "PASS": 14}, replay["D"]["counts"]["joint_admissibility"])
        ready_a = {x["territory_id"] for x in replay["A"]["work_items"] if x["state"] == "READY_LOCAL"}
        ready_b = {x["territory_id"] for x in replay["B"]["work_items"] if x["state"] == "READY_LOCAL"}
        ready_c = {x["territory_id"] for x in replay["C"]["work_items"] if x["state"] == "READY_LOCAL"}
        self.assertEqual(set(), ready_a)
        self.assertIn("extremadura", ready_b)
        self.assertTrue({"andalucia", "aragon", "castilla_y_leon"} <= ready_c)
        cv = next(x for x in replay["C"]["work_items"] if x["territory_id"] == "comunidad_valenciana")
        self.assertFalse(cv["selectable"])
        self.assertEqual("CLOSED", next(x for x in self.projection["territories"] if x["territory_id"] == "comunidad_valenciana")["territorial_acquisition"])

    def test_valencia_2023_receipt_is_temporally_selected_and_not_promoted(self):
        from herramientas.consumir_par_fuentes_legislatura import validate_territorial_receipt
        from herramientas.resolver_preparacion_legislatura import resolve

        state, receipt = validate_territorial_receipt(
            root_dir=ROOT, territory="comunidad_valenciana", edition="2025"
        )
        self.assertEqual((2023, 2023), (receipt["population_year"], receipt["section_year"]))
        self.assertEqual("AUTHENTIC_EVIDENCE_ONLY_HISTORICAL_PRODUCT_LINEAGE_PRESERVED",
                         state["independent_source_evidence"]["status"])
        self.assertIs(state["independent_source_evidence"]["promoted"], False)
        self.assertEqual(36273981926, state["preparation_evidence"]["run_id"])
        self.assertIs(state["territorial_product_available"], False)

        plan = resolve(ROOT, "Comunidad Valenciana")["plans"][0]
        self.assertEqual((2023, 2023), (plan["population_year_selected"], plan["section_year_selected"]))
        self.assertEqual("ADMISSIBLE", plan["territorial_admissibility"])
        self.assertEqual("ADMISSIBLE", plan["electoral_admissibility"])
        self.assertIs(plan["blocked"], False)

    def test_valencia_2023_geometry_evidence_records_full_m02_contract(self):
        evidence = next(
            ROOT.glob("territorios/comunidad_valenciana/evidencia/fuentes_territoriales/2025/94f094a23493448d9ee38f1b51fe6f73dd0f29b6b7a4410eae8bb5a170c38d62/39315133646/evidencia_geometrica.json")
        )
        data = json.loads(evidence.read_text(encoding="utf-8"))
        m02 = data["m02"]
        self.assertEqual("EPSG:25830", m02["working_crs"])
        self.assertEqual(1.0, m02["max_precision_overlap_area_m2"])
        self.assertEqual(0.0, m02["buffer_m"])
        self.assertEqual(0.0, m02["simplify_m"])
        self.assertEqual(0, m02["pairs_over_1m2"])
        self.assertEqual(148, m02["total_positive_area_pairs_in_full_universe"])
        self.assertAlmostEqual(0.18890051866037538,
                               m02["target_pairs"]["4617201001/4619401008"]["intersection_area_m2"])
        self.assertAlmostEqual(0.19342763282640657,
                               m02["target_pairs"]["4617201001/4619401013"]["intersection_area_m2"])
        self.assertEqual(3503, data["m03"]["nodes"])
        self.assertEqual(5216195, data["m03"]["total_pop"])
        self.assertEqual(0, data["m03"]["isolated"])

    def test_corrupt_hash_wrong_identity_time_and_contradictory_dossier_fail_closed(self):
        canonical = next(x for x in self.projection["territories"] if x["territory_id"] == "extremadura")
        receipt = json.loads((ROOT / canonical["territorial_receipt_path"]).read_text())
        dossier_row = json.loads((ROOT / "docs/AUDITORIAS/F10_CIERRE_TERRITORIAL_20261012/matriz_nacional_19.json").read_text())["rows"]
        dossier_row = next(x for x in dossier_row if x["territory_id"] == "extremadura")
        args = dict(territory_id="extremadura", receipt_path=canonical["territorial_receipt_path"],
                    receipt_sha256=canonical["territorial_receipt_sha256"], dossier_row=dossier_row)
        with self.assertRaisesRegex(ValueError, "receipt_sha256"):
            check_territorial_evidence(receipt, **{**args, "receipt_sha256": "0" * 64})
        wrong_edition = copy.deepcopy(receipt); wrong_edition["edition"] = "2024"
        with self.assertRaisesRegex(ValueError, "identidad/edición"):
            check_territorial_evidence(wrong_edition, **args)
        wrong_identity = copy.deepcopy(receipt); wrong_identity["territory_id"] = "aragon"
        with self.assertRaisesRegex(ValueError, "identidad/edición"):
            check_territorial_evidence(wrong_identity, **args)
        wrong_hash = copy.deepcopy(receipt); wrong_hash["artifact_sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "artifact_sha256"):
            check_territorial_evidence(wrong_hash, **args)
        wrong_time = copy.deepcopy(receipt); wrong_time["section_year"] = "2025"
        with self.assertRaisesRegex(ValueError, "años"):
            check_territorial_evidence(wrong_time, **args)
        contradictory = copy.deepcopy(dossier_row); contradictory["territorial_acquisition"] = "BLOCKED"
        with self.assertRaisesRegex(ValueError, "contradice receipt territorial"):
            check_territorial_evidence(receipt, **{**args, "dossier_row": contradictory})

    def test_reregistration_is_accepted_only_if_newer_and_same_years(self):
        canonical = next(x for x in self.projection["territories"] if x["territory_id"] == "extremadura")
        receipt = json.loads((ROOT / canonical["territorial_receipt_path"]).read_text())
        dossier_row = json.loads((ROOT / "docs/AUDITORIAS/F10_CIERRE_TERRITORIAL_20261012/matriz_nacional_19.json").read_text())["rows"]
        dossier_row = next(x for x in dossier_row if x["territory_id"] == "extremadura")
        # Mismo paquete reutilizado por un run posterior: run, artefacto y receipt nuevos.
        rereg = copy.deepcopy(receipt)
        rereg["run_id"] = int(receipt["run_id"]) + 1
        rereg["artifact_sha256"] = "1" * 64
        args = dict(territory_id="extremadura", receipt_path="territorios/extremadura/otro/receipt.json",
                    receipt_sha256="2" * 64, dossier_row=dossier_row)
        check_territorial_evidence(rereg, **args)
        older = copy.deepcopy(rereg); older["run_id"] = int(receipt["run_id"]) - 1
        with self.assertRaisesRegex(ValueError, "receipt_path"):
            check_territorial_evidence(older, **args)
        # 1.1.4: una re-descarga del mismo año con otra huella de paquete o compatibilidad hereda
        # el cierre; otro año de seccionado o población exige nueva auditoría F10.
        other_package = copy.deepcopy(rereg); other_package["package_sha256"] = "3" * 64
        other_package["compatibility_identity_sha256"] = "4" * 64
        check_territorial_evidence(other_package, **args)
        other_year = copy.deepcopy(rereg); other_year["section_year"] = int(receipt["section_year"]) + 1
        with self.assertRaisesRegex(ValueError, "section_year"):
            check_territorial_evidence(other_year, **args)

    def test_corrupt_receipt_bytes_fail_in_the_canonical_consumer(self):
        from herramientas import consumir_par_fuentes_legislatura as consumer

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "receipt.json").write_text("{broken", encoding="utf-8")
            state = {
                "territory_id": "demo", "name": "Demo", "territorial_sources_prepared": True,
                "preparation_evidence": {"receipt_path": "receipt.json"},
            }
            with mock.patch.object(consumer, "_catalog_row", return_value=state):
                with self.assertRaisesRegex(consumer.PreparedPairExecutionBlock, "receipt territorial ilegible"):
                    consumer.validate_territorial_receipt(root_dir=root, territory="demo", edition="2025")

    def test_plan_overlay_does_not_reopen_formal_f10_or_production(self):
        self.assertEqual({"id": "F10", "status": "PENDING", "authority_class": "owner_reserved",
                          "reserved": True, "depends_on": ["F09"]}, PLAN_OVERLAY["formal_task_preserved"])
        self.assertFalse(PLAN_OVERLAY["production"]["authorized"])
        self.assertTrue(all(row["does_not_require_global_f10_closed"] for row in PLAN_OVERLAY["activities"]))
        registered = [row for row in PLAN_OVERLAY["activities"] if row["task_spec_registered"]]
        self.assertEqual(4, len(registered))
        self.assertTrue(all(row["task_spec_path"].startswith("configuracion/f10_auto_tareas.json#")
                            for row in registered))
        self.assertEqual(64, len({row["task_spec_sha256"] for row in registered}.pop()))
        self.assertFalse(PLAN_OVERLAY["activities"][-1]["task_spec_registered"])

    def test_registered_cards_are_hash_pinned_and_bad_reference_blocks_only_that_activity(self):
        checked = _validate_activity_cards(ROOT, PLAN_OVERLAY["activities"])
        self.assertEqual([], [row for row in checked if row.get("task_spec_error")])
        broken = copy.deepcopy(PLAN_OVERLAY["activities"])
        broken[0]["task_spec_sha256"] = "0" * 64
        checked = _validate_activity_cards(ROOT, broken)
        self.assertIn("hash de ficha distinto", checked[0]["task_spec_error"])
        rows = copy.deepcopy(self.projection["territories"])
        work = {row["territory_id"]: row for row in work_items_for(rows, AUTHORIZATIONS, checked)}
        self.assertEqual("WAIT_OWNER", work["andalucia"]["state"])
        self.assertEqual("READY_LOCAL", work["aragon"]["state"])

    def test_card_without_complete_validator_coverage_is_not_selectable(self):
        registry = json.loads((ROOT / "configuracion/f10_auto_tareas.json").read_text())
        registry["cards"][0]["spec"]["validators"][0]["covers"] = [0]
        with tempfile.TemporaryDirectory(dir=ROOT / "tests") as directory:
            card_path = Path(directory) / "broken-card.json"
            content = json.dumps(registry, ensure_ascii=False).encode()
            card_path.write_bytes(content)
            activities = copy.deepcopy(PLAN_OVERLAY["activities"])
            activities[0]["task_spec_path"] = f"{card_path.relative_to(ROOT).as_posix()}#F10-AND-CROSSWALK-2025-2026"
            activities[0]["task_spec_sha256"] = hashlib.sha256(content).hexdigest()
            checked = _validate_activity_cards(ROOT, activities)
            self.assertIn("ficha excede alcance", checked[0]["task_spec_error"])

    def test_blocked_territory_does_not_block_independent_work_item(self):
        rows = copy.deepcopy(self.projection["territories"])
        rows_by_id = {row["territory_id"]: row for row in rows}
        rows_by_id["aragon"]["territorial_acquisition"] = "BLOCKED"
        work = {row["territory_id"]: row for row in work_items_for(rows, AUTHORIZATIONS, PLAN_OVERLAY["activities"])}
        self.assertEqual("WAIT_OWNER", work["aragon"]["state"])
        self.assertEqual("READY_LOCAL", work["andalucia"]["state"])
        self.assertEqual("READY_LOCAL", work["castilla_y_leon"]["state"])

    def test_without_local_investigation_grant_no_work_is_unlocked(self):
        work = work_items_for(self.projection["territories"], {"local_read_only": ["local_tests"]}, PLAN_OVERLAY["activities"])
        self.assertTrue(all(row["state"] == "WAIT_OWNER" for row in work))


class F10SameYearRedownloadTests(unittest.TestCase):
    ROW = {"receipt_path": "old/receipt.json", "receipt_sha256": "a" * 64, "run_id": 100,
           "package_sha256": "b" * 64, "population_year": 2023, "section_year": 2023,
           "territorial_identity_sha256": "c" * 64, "compatibility_report_sha256": "d" * 64,
           "compatibility_identity_sha256": "e" * 64, "territorial_acquisition": "CLOSED"}

    def receipt(self, **over):
        base = {"territory_id": "demo", "edition": "2025", "run_id": 200, "population_year": 2023,
                "section_year": 2023, "package_sha256": "f" * 64, "territorial_identity_sha256": "9" * 64,
                "compatibility_report_sha256": "8" * 64, "compatibility_identity_sha256": "7" * 64}
        return {**base, **over}

    def test_newer_same_year_redownload_inherits_closure(self):
        check_territorial_evidence(self.receipt(), territory_id="demo", receipt_path="new/receipt.json",
                                   receipt_sha256="1" * 64, dossier_row=self.ROW)

    def test_other_year_or_older_receipt_still_blocks(self):
        with self.assertRaisesRegex(ValueError, "section_year"):
            check_territorial_evidence(self.receipt(section_year=2025), territory_id="demo",
                                       receipt_path="new/receipt.json", receipt_sha256="1" * 64,
                                       dossier_row=self.ROW)
        with self.assertRaisesRegex(ValueError, "receipt_path"):
            check_territorial_evidence(self.receipt(run_id=50), territory_id="demo",
                                       receipt_path="new/receipt.json", receipt_sha256="1" * 64,
                                       dossier_row=self.ROW)


class F10LiveRepositoryRuleTests(unittest.TestCase):
    """Sobre el repositorio vivo sólo se exige la regla, no un recuento."""

    def test_live_projection_is_consistent_and_new_packages_await_f10_audit(self):
        live = derive_f10(Path(__file__).resolve().parents[1], activity_authorizations=AUTHORIZATIONS)
        self.assertEqual([], live["catalog_validation_errors"])
        self.assertEqual(19, len(live["territories"]))
        for row in live["territories"]:
            if row["territorial_acquisition"] == "CLOSED":
                continue
            with self.subTest(territory=row["territory_id"]):
                # Un paquete re-descargado con bytes nuevos no hereda el cierre F10: queda
                # bloqueado hasta una auditoría nueva, nunca aceptado en silencio.
                self.assertTrue(any("matriz de seguimiento contradice" in reason
                                    for reason in row["territorial_reason"]), row["territorial_reason"])


if __name__ == "__main__":
    unittest.main()
