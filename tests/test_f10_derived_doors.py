"""Read-only F10 door projection, historical replay and fail-closed regressions."""
from __future__ import annotations

import copy
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


ROOT = Path(__file__).resolve().parents[1]
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
        self.assertEqual({"BLOCKED": 1, "CLOSED": 18}, self.projection["counts"]["territorial_acquisition"])
        self.assertEqual({"ADMISSIBLE": 15, "BLOCKED": 4}, self.projection["counts"]["electoral_admissibility"])
        self.assertEqual({"PASS": 14, "BLOCKED": 5}, self.projection["counts"]["joint_admissibility"])
        self.assertEqual({"NOT_AUTHORIZED_BY_F10": 19}, self.projection["counts"]["production"])
        self.assertEqual("PENDING", self.projection["f10_global"])
        self.assertEqual([], self.projection["catalog_validation_errors"])

    def test_independent_receipts_are_not_promoted_or_used_as_historical_products(self):
        rows = {row["territory_id"]: row for row in self.projection["territories"]}
        for territory_id, run_id in (("andalucia", 38082966768), ("aragon", 38093067883),
                                     ("castilla_y_leon", 38091055890), ("extremadura", 38091144559)):
            with self.subTest(territory=territory_id):
                self.assertEqual("CLOSED", rows[territory_id]["territorial_acquisition"])
                self.assertEqual(run_id, rows[territory_id]["territorial_run_id"])
        self.assertEqual("BLOCKED", rows["comunidad_valenciana"]["territorial_acquisition"])
        self.assertIn("receipt territorial versionado", " ".join(rows["comunidad_valenciana"]["territorial_reason"]))

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
        self.assertEqual({"PASS": 14, "BLOCKED": 5}, replay["D"]["counts"]["joint_admissibility"])
        ready_a = {x["territory_id"] for x in replay["A"]["work_items"] if x["state"] == "READY_LOCAL"}
        ready_b = {x["territory_id"] for x in replay["B"]["work_items"] if x["state"] == "READY_LOCAL"}
        ready_c = {x["territory_id"] for x in replay["C"]["work_items"] if x["state"] == "READY_LOCAL"}
        self.assertNotIn("extremadura", ready_a)
        self.assertIn("extremadura", ready_b)
        self.assertTrue({"andalucia", "aragon", "castilla_y_leon"} <= ready_c)
        self.assertNotIn("comunidad_valenciana", ready_c)
        self.assertEqual("BLOCKED", next(x for x in self.projection["territories"] if x["territory_id"] == "comunidad_valenciana")["territorial_acquisition"])

    def test_corrupt_hash_wrong_identity_time_and_contradictory_dossier_fail_closed(self):
        canonical = next(x for x in self.projection["territories"] if x["territory_id"] == "extremadura")
        receipt = json.loads((ROOT / canonical["territorial_receipt_path"]).read_text())
        dossier_row = json.loads((ROOT / "docs/AUDITORIAS/F10_CIERRE_TERRITORIAL_20261012/matriz_nacional_19.json").read_text())["rows"]
        dossier_row = next(x for x in dossier_row if x["territory_id"] == "extremadura")
        args = dict(territory_id="extremadura", receipt_path=canonical["territorial_receipt_path"],
                    receipt_sha256=canonical["territorial_receipt_sha256"], dossier_row=dossier_row)
        with self.assertRaisesRegex(ValueError, "receipt_sha256"):
            check_territorial_evidence(receipt, **{**args, "receipt_sha256": "0" * 64})
        wrong_identity = copy.deepcopy(receipt); wrong_identity["territory_id"] = "aragon"
        with self.assertRaisesRegex(ValueError, "identidad/edición"):
            check_territorial_evidence(wrong_identity, **args)
        wrong_time = copy.deepcopy(receipt); wrong_time["section_year"] = "2025"
        with self.assertRaisesRegex(ValueError, "años"):
            check_territorial_evidence(wrong_time, **args)
        contradictory = copy.deepcopy(dossier_row); contradictory["territorial_acquisition"] = "BLOCKED"
        with self.assertRaisesRegex(ValueError, "contradice receipt territorial"):
            check_territorial_evidence(receipt, **{**args, "dossier_row": contradictory})

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


if __name__ == "__main__":
    unittest.main()
