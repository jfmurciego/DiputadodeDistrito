from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
WRITER = ROOT / "herramientas/escribir_manifest_ejecucion_completa.py"


def write_manifest(*, publication_mode: str, territorial_source_validation: str,
                   territorial_product_validation: str, prepare_electoral_result: str = "skipped",
                   incorporate_result: str = "skipped", prepare_electoral_executed: bool = False,
                   incorporate_executed: bool = False, electoral_source_validation: str = "BLOQUEADO",
                   electoral_product_validation: str = "BLOQUEADO") -> dict:
    with tempfile.TemporaryDirectory() as td:
        output = Path(td) / "manifest.json"
        cmd = [
            sys.executable,
            str(WRITER),
            "--territory-id", "demo",
            "--territory-name", "Demo",
            "--edition", "2025",
            "--execution-mode", "reuse",
            "--optimization-algorithm", "Canónico",
            "--workflow-run-id", "999",
            "--source-sha", "a" * 40,
            "--publication-mode-requested", publication_mode,
            "--publication-mode-effective", publication_mode,
            "--publish-requested", "false",
            "--prepare-territorial-result", "skipped",
            "--generate-result", "skipped",
            "--prepare-electoral-result", prepare_electoral_result,
            "--incorporate-result", incorporate_result,
            "--publish-result", "skipped",
            "--prepare-territorial-executed", "false",
            "--generate-executed", "false",
            "--prepare-electoral-executed", str(prepare_electoral_executed).lower(),
            "--incorporate-executed", str(incorporate_executed).lower(),
            "--territorial-source-run-id", "100",
            "--territorial-source-artifact", "ddd-source-package-demo-2025-100",
            "--territorial-source-digest", "sha256:" + "1" * 64,
            "--territorial-product-run-id", "200",
            "--territorial-product-artifact", "ddd-state-200-M06",
            "--territorial-product-digest", "sha256:" + "2" * 64,
            "--territorial-source-validation", territorial_source_validation,
            "--territorial-product-validation", territorial_product_validation,
            "--electoral-source-validation", electoral_source_validation,
            "--electoral-product-validation", electoral_product_validation,
            "--output", str(output),
        ]
        completed = subprocess.run(cmd, capture_output=True, text=True)
        if completed.returncode != 0:
            raise AssertionError(completed.stderr or completed.stdout)
        return json.loads(output.read_text(encoding="utf-8"))


class FullRunManifestScopeTests(unittest.TestCase):
    def test_territorial_only_success_marks_electoral_phases_out_of_scope(self):
        manifest = write_manifest(
            publication_mode="territorial_only",
            territorial_source_validation="VALIDADO",
            territorial_product_validation="VALIDADO",
        )
        self.assertEqual(manifest["status"], "SUCCESS")
        self.assertEqual(manifest["completion_status"], "COMPLETE")
        self.assertEqual(manifest["blocked_phases"], [])
        self.assertEqual(
            manifest["out_of_scope_phases"],
            [
                "03 · Preparación de Resultados Electorales",
                "04 · Incorporación de Resultados Electorales",
            ],
        )
        phase03 = next(p for p in manifest["phases"] if p["name"].startswith("03 ·"))
        phase04 = next(p for p in manifest["phases"] if p["name"].startswith("04 ·"))
        for phase in (phase03, phase04):
            self.assertEqual(phase["scope"], "OUT_OF_SCOPE")
            self.assertIsNone(phase["validation_decision"])

    def test_real_territorial_block_still_fails_territorial_only_scope(self):
        manifest = write_manifest(
            publication_mode="territorial_only",
            territorial_source_validation="VALIDADO",
            territorial_product_validation="BLOQUEADO",
        )
        self.assertEqual(manifest["status"], "FAILED")
        self.assertEqual(manifest["completion_status"], "INCOMPLETE")
        self.assertEqual(
            manifest["blocked_phases"],
            ["02 · Generación de Distritos Autonómicos"],
        )
        self.assertNotIn(
            "03 · Preparación de Resultados Electorales",
            manifest["blocked_phases"],
        )
        self.assertIn(
            "03 · Preparación de Resultados Electorales",
            manifest["out_of_scope_phases"],
        )

    def test_electoral_incomplete_remains_failed_and_blocked(self):
        manifest = write_manifest(
            publication_mode="electoral",
            territorial_source_validation="VALIDADO",
            territorial_product_validation="VALIDADO",
            prepare_electoral_result="failure",
            incorporate_result="skipped",
            prepare_electoral_executed=True,
            incorporate_executed=False,
            electoral_source_validation="BLOQUEADO",
            electoral_product_validation="BLOQUEADO",
        )
        self.assertEqual(manifest["status"], "FAILED")
        self.assertEqual(manifest["completion_status"], "INCOMPLETE")
        self.assertIn(
            "03 · Preparación de Resultados Electorales",
            manifest["failed_phases"],
        )
        self.assertIn(
            "03 · Preparación de Resultados Electorales",
            manifest["blocked_phases"],
        )
        self.assertIn(
            "04 · Incorporación de Resultados Electorales",
            manifest["blocked_phases"],
        )
        self.assertEqual(manifest["out_of_scope_phases"], [])

    def test_historical_extremadura_36472516474_is_not_rewritten(self):
        historical = json.loads(
            (
                ROOT
                / "territorios/extremadura/evidencia/ejecuciones_completas/36472516474.json"
            ).read_text(encoding="utf-8")
        )
        self.assertEqual(historical["status"], "FAILED")
        self.assertEqual(historical["completion_status"], "INCOMPLETE")
        self.assertEqual(historical["publication_mode_effective"], "territorial_only")
        self.assertIn(
            "03 · Preparación de Resultados Electorales",
            historical["blocked_phases"],
        )
        self.assertIn(
            "04 · Incorporación de Resultados Electorales",
            historical["blocked_phases"],
        )


if __name__ == "__main__":
    unittest.main()
