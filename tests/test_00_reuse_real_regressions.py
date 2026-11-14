from __future__ import annotations

import json
import shutil
import tempfile
from pathlib import Path
import unittest

from herramientas.resolver_ejecucion_completa import build_plan
from tests._linaje_historico import historical_catalog
from tests._previo_r3 import raiz_previo_r3

ROOT = Path(__file__).resolve().parents[1]


class ReuseRealRegressionsTests(unittest.TestCase):
    def test_extremadura_36472516474_reuses_certified_m06_despite_historical_global_failure(self):
        # T-322: raíz congelada previa a r3 (aut11) y fixtures del linaje histórico; un P10 nuevo no la toca.
        root = raiz_previo_r3()
        shutil.copytree(ROOT / "tests/fixtures/linaje_historico", root / "tests/fixtures/linaje_historico")
        historical = json.loads(
            (
                root
                / "territorios/aut11/evidencia/ejecuciones_completas/36472516474.json"
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
        catalog = historical_catalog(root / "catalogo.yaml", "aut11")
        plan = build_plan(
            territory="Extremadura",
            edition="2025",
            execution_mode="reuse",
            catalog=catalog,
            root_dir=root,
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
