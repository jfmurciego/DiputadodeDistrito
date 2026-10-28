from __future__ import annotations

import json
import tempfile
from pathlib import Path
import unittest

from herramientas.resolver_ejecucion_completa import build_plan
from tests._linaje_historico import historical_catalog

ROOT = Path(__file__).resolve().parents[1]


class ReuseRealRegressionsTests(unittest.TestCase):
    def test_extremadura_36472516474_reuses_certified_m06_despite_historical_global_failure(self):
        historical = json.loads(
            (
                ROOT
                / "territorios/extremadura/evidencia/ejecuciones_completas/36472516474.json"
            ).read_text(encoding="utf-8")
        )
        self.assertEqual(historical["status"], "FAILED")
        self.assertEqual(historical["completion_status"], "INCOMPLETE")
        producer = next(p for p in historical["phases"] if p["name"].startswith("02 ·"))
        self.assertTrue(producer["executed"])
        self.assertEqual(producer["result"], "success")
        self.assertEqual(producer["validation_decision"], "VALIDADO")
        self.assertEqual(producer["phase_decision"], "PASS_WITH_EXCEPTIONS")

        # Extremadura adoptó el M06 40656175842; el caso histórico se ejercita con su linaje previo.
        catalog = historical_catalog(Path(tempfile.mkdtemp()) / "catalogo.yaml", "extremadura")
        plan = build_plan(
            territory="Extremadura",
            edition="2025",
            execution_mode="reuse",
            catalog=catalog,
            root_dir=ROOT,
            optimization_algorithm="Canónico",
            force_selected_algorithm=True,
        )

        self.assertFalse(plan["run_prepare_territorial"])
        self.assertFalse(plan["run_generate"])
        self.assertEqual(plan["existing"]["territorial_product"]["run_id"], 36472516474)
        self.assertEqual(
            plan["existing"]["territorial_product"]["artifact_name"],
            "ddd-state-36472516474-M06",
        )


if __name__ == "__main__":
    unittest.main()
