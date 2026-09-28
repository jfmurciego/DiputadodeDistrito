from __future__ import annotations

import json
from pathlib import Path
import unittest
import yaml

from herramientas.resolver_ejecucion_completa import (
    _territorial_product_reuse_validation,
    build_plan,
)

ROOT = Path(__file__).resolve().parents[1]


class ReuseRealRegressionsTests(unittest.TestCase):
    def test_extremadura_36472516474_is_reused_instead_of_regenerated(self):
        receipt = json.loads(
            (ROOT / "territorios/extremadura/evidencia/catalogo/territorial_product_2025.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(receipt["run_id"], 36472516474)

        plan = build_plan(
            territory="Extremadura",
            edition="2025",
            execution_mode="reuse",
            catalog=ROOT / "configuracion/catalogo_preparacion.yaml",
            root_dir=ROOT,
            optimization_algorithm="Canónico",
            # Reproduce the flag that manual workflow_dispatch used when run 36472516474
            # incorrectly regenerated a compatible M06.
            force_selected_algorithm=True,
        )

        self.assertFalse(plan["run_prepare_territorial"])
        self.assertFalse(plan["run_generate"])
        self.assertEqual(plan["existing"]["territorial_product"]["run_id"], 36472516474)
        self.assertEqual(
            plan["existing"]["territorial_product"]["artifact_name"],
            "ddd-state-36472516474-M06",
        )
        self.assertTrue(plan["catalog_state"]["territorial_product_reuse_validation"]["valid"])
        self.assertEqual(
            plan["catalog_state"]["territorial_product_reuse_validation"]["reason"],
            "VALIDATED_M06_RECEIPT",
        )

    def test_extremadura_receipt_validation_requires_identity_digest_certification_and_lineage(self):
        catalog = yaml.safe_load((ROOT / "configuracion/catalogo_preparacion.yaml").read_text(encoding="utf-8"))
        row = next(r for r in catalog["territories"] if r["territory_id"] == "extremadura")
        state = row["editions"]["2025"]
        receipt = json.loads(
            (ROOT / state["evidence"]["territorial_product"]).read_text(encoding="utf-8")
        )

        ok = _territorial_product_reuse_validation(
            row=row,
            state=state,
            edition="2025",
            evidence=receipt,
        )
        self.assertTrue(ok["valid"])

        cases = {}

        wrong_identity = dict(receipt)
        wrong_identity["territory_id"] = "castilla_la_mancha"
        cases["identity"] = (state, wrong_identity, "RECEIPT_IDENTITY")

        bad_digest = dict(receipt)
        bad_digest["artifact_sha256"] = "bad"
        cases["digest"] = (state, bad_digest, "RECEIPT_DIGEST")

        bad_certification = dict(receipt)
        bad_certification["decision"] = "FAIL"
        cases["certification"] = (state, bad_certification, "RECEIPT_CERTIFICATION")

        bad_lineage = dict(receipt)
        bad_lineage["source_commit"] = "not-a-commit"
        cases["source_commit_lineage"] = (state, bad_lineage, "RECEIPT_SOURCE_COMMIT")

        checkpoint_state = json.loads(json.dumps(state))
        checkpoint_state["last_valid_checkpoint"] = {"run_id": receipt["run_id"] + 1, "stage": "M06"}
        cases["checkpoint_lineage"] = (
            checkpoint_state,
            receipt,
            "CHECKPOINT_RECEIPT_LINEAGE",
        )

        for name, (case_state, case_receipt, reason) in cases.items():
            with self.subTest(case=name):
                result = _territorial_product_reuse_validation(
                    row=row,
                    state=case_state,
                    edition="2025",
                    evidence=case_receipt,
                )
                self.assertFalse(result["valid"])
                self.assertEqual(result["reason"], reason)

    def test_noncanonical_strategy_still_requests_generation(self):
        plan = build_plan(
            territory="Extremadura",
            edition="2025",
            execution_mode="reuse",
            catalog=ROOT / "configuracion/catalogo_preparacion.yaml",
            root_dir=ROOT,
            optimization_algorithm="GerryChain 50",
            force_selected_algorithm=True,
        )
        self.assertTrue(plan["run_generate"])


if __name__ == "__main__":
    unittest.main()
