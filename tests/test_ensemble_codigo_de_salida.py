"""Versión 1.0.0; 2026-11-02; candidato. T-32: el runner del ensemble no sale en verde con candidatos fallidos o 0 válidos."""
from __future__ import annotations

import io
import contextlib
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from ddd_ensemble import runner


def run_main(result_run=None, summary=None, argv_extra=()):
    argv = ["runner", "--config", "x.json", "--mode", "all", "--output", tempfile.mkdtemp(), *argv_extra]
    plan = {"plan_sha256": "abc", "candidates": []}
    with mock.patch("sys.argv", argv), \
         mock.patch.object(runner, "load_config", return_value=({"ensemble": {"shortlist_size": 10}}, Path("."))), \
         mock.patch.object(runner, "validate_inputs"), mock.patch.object(runner, "resolve_prepared_bundle_id"), \
         mock.patch.object(runner, "ensure_plan", return_value=plan), \
         mock.patch.object(runner, "run_candidates", return_value=result_run or {"executed": 0, "skipped": 0, "failed": 0}), \
         mock.patch.object(runner, "finish", return_value=summary or {"complete": True, "candidate_count_valid": 10}), \
         contextlib.redirect_stdout(io.StringIO()):
        try:
            runner.main()
        except SystemExit as exc:
            return exc.code
    return 0


class CodigoDeSalidaTests(unittest.TestCase):
    def test_rojo_candidatos_fallidos_ya_no_salen_en_verde(self):
        self.assertEqual(run_main({"executed": 0, "skipped": 0, "failed": 2}), 3)

    def test_rojo_cero_validos_falla_aunque_se_permita_lo_parcial(self):
        self.assertEqual(run_main(summary={"complete": False, "candidate_count_valid": 0}, argv_extra=("--allow-partial",)), 4)

    def test_verde_todo_correcto_sale_con_cero(self):
        self.assertEqual(run_main(), 0)

    def test_parcial_con_validos_sigue_siendo_reanudable(self):
        # Con --allow-partial y algún candidato válido, el ensamblado parcial (matriz de reintento) no es un error.
        self.assertEqual(run_main(summary={"complete": False, "candidate_count_valid": 4}, argv_extra=("--allow-partial",)), 0)
        self.assertEqual(run_main(summary={"complete": False, "candidate_count_valid": 4}), 2)

    def test_exit_code_for_directo(self):
        self.assertEqual(runner.exit_code_for({"run": {"failed": 1}}, True), 3)
        self.assertEqual(runner.exit_code_for({"summary": {"candidate_count_valid": 0}}, True), 4)
        self.assertEqual(runner.exit_code_for({"run": {"failed": 0}, "summary": {"candidate_count_valid": 10, "complete": True}}, False), 0)


if __name__ == "__main__":
    unittest.main()
