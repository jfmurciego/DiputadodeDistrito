"""Versión 1.0.0; 2026-11-09; candidato. T-128: el runner imprime en el log el motivo del fallo de cada candidato."""
from __future__ import annotations

import io
import json
import tempfile
import unittest
from contextlib import redirect_stderr
from pathlib import Path
from unittest import mock

from ddd_ensemble import runner


class FalloEnLog(unittest.TestCase):
    def test_message_del_fallo_sale_por_stderr_y_en_failure_json(self):
        out = Path(tempfile.mkdtemp())
        plan = {"candidates": [{"candidate_id": "c1", "profile": "shape", "seed": 1, "parameters": {"comarca_surcharge": 0, "population": 1, "shape": 1, "comarca": 0}}]}
        config = {"fields": {}, "engine": {}, "territory_id": "t"}
        err = io.StringIO()
        with mock.patch.object(runner, "adapt", return_value=object()), \
             mock.patch.object(runner, "contract", return_value=object()), \
             mock.patch.object(runner, "_degeneracy_policy", return_value=None), \
             mock.patch.object(runner, "_sampling_policy", return_value=None), \
             mock.patch.object(runner, "run_statistical_gerrychain", side_effect=ValueError("CRS incompatible 3035")), \
             redirect_stderr(err):
            res = runner.run_candidates(config, out, out, plan, None)
        self.assertEqual(res["failed"], 1)
        self.assertIn("CANDIDATE_FAILED c1 profile=shape ValueError: CRS incompatible 3035", err.getvalue())
        data = json.loads((out / "results" / "c1" / "failure.json").read_text())
        self.assertEqual(data["message"], "CRS incompatible 3035")


if __name__ == "__main__":
    unittest.main()
