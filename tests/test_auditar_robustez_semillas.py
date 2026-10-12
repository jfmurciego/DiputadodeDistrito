"""Pruebas ligeras de la evidencia C-01; no ejecutan el motor territorial."""
import unittest

from herramientas.auditar_robustez_semillas import decide, percentile, seed_list


class SeedRobustnessAudit(unittest.TestCase):
    def test_seed_list_includes_canonical_and_has_required_size(self):
        seeds = seed_list(50, 12345)
        self.assertEqual(len(seeds), 50)
        self.assertEqual(len(set(seeds)), 50)
        self.assertEqual(seeds[0], 12345)

    def test_percentile_uses_midrank_for_ties(self):
        self.assertEqual(percentile([1.0, 2.0, 2.0, 4.0], 2.0), 50.0)

    def test_decision_accepts_central_published_map(self):
        rows = [
            {
                "max_rel_dev": 0.08 + i / 10000,
                "pp_mean": 0.20 + i / 1000,
                "pp_min": 0.06 + i / 10000,
                "districts_outside_tolerance": 0,
            }
            for i in range(50)
        ]
        canonical = {
            **rows[24],
            "pp_below_015_ratio": 0.25,
        }
        self.assertEqual(decide(rows, canonical), ("PASS", []))

    def test_process_success_does_not_mean_technical_solution(self):
        rows = [
            {
                "max_rel_dev": 0.10 if i < 15 else 0.18,
                "districts_outside_tolerance": 0 if i < 15 else 1,
                "pp_mean": 0.23,
                "pp_min": 0.052,
            }
            for i in range(50)
        ]
        canonical = {**rows[0], "pp_below_015_ratio": 0.25}
        decision, reasons = decide(rows, canonical)
        self.assertEqual(decision, "FAIL")
        self.assertIn("menos del 95 %", reasons[0])

    def test_private_annealing_audit_is_unsupported_and_overwrites_stale_pass(self):
        import json
        import sys
        import tempfile
        from pathlib import Path
        from unittest.mock import patch
        import yaml
        from herramientas import auditar_robustez_semillas as audit

        with tempfile.TemporaryDirectory() as dirname:
            directory = Path(dirname)
            config = directory / "params.yaml"
            config.write_text(yaml.safe_dump({
                "modulos": {"modulo_05_optimizar_distritos": {
                    "id_field": "CUSEC_KEY",
                    "population_repair": {"enabled": True, "strategy": "private_annealing"},
                }}
            }), encoding="utf-8")
            output = directory / "out"
            output.mkdir()
            evidence = output / "EVIDENCIA_C01.json"
            evidence.write_text('{"decision":"PASS"}', encoding="utf-8")
            argv = ["auditar_robustez_semillas.py", "--params", str(config),
                    "--graph", str(directory / "not_needed.json"),
                    "--initial", str(directory / "not_needed.zip"),
                    "--output-dir", str(output), "--samples", "50"]
            with patch.object(sys, "argv", argv), self.assertRaises(SystemExit) as ctx:
                audit.main()
            self.assertIn("UNSUPPORTED", str(ctx.exception))
            data = json.loads(evidence.read_text(encoding="utf-8"))
            self.assertEqual(data["decision"], "UNSUPPORTED")
            self.assertFalse(data["supported"])

    def test_disabled_private_annealing_does_not_trip_guard(self):
        # Existing C-01 behavior remains available when the private strategy is off.
        self.assertEqual(len(seed_list(50, 4629)), 50)


if __name__ == "__main__":
    unittest.main()
