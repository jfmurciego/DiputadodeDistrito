from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "herramientas/escribir_manifest_ejecucion_completa.py"


def test_manifest_v11_conserva_digest_y_decision_de_cada_puerta():
    with tempfile.TemporaryDirectory() as td:
        out = Path(td) / "manifest.json"
        cmd = [
            sys.executable, str(SCRIPT),
            "--territory-id", "demo",
            "--territory-name", "Demo",
            "--edition", "2025",
            "--execution-mode", "reuse",
            "--optimization-algorithm", "Canónico",
            "--workflow-run-id", "999",
            "--source-sha", "abc",
            "--publish-requested", "false",
            "--prepare-territorial-result", "skipped",
            "--generate-result", "skipped",
            "--prepare-electoral-result", "skipped",
            "--incorporate-result", "skipped",
            "--publish-result", "skipped",
            "--prepare-territorial-executed", "false",
            "--generate-executed", "false",
            "--prepare-electoral-executed", "false",
            "--incorporate-executed", "false",
            "--territorial-source-run-id", "101",
            "--territorial-source-artifact", "source",
            "--territorial-source-digest", "sha256:" + "a" * 64,
            "--territorial-source-decision", "VALIDADO",
            "--territorial-product-run-id", "102",
            "--territorial-product-artifact", "m06",
            "--territorial-product-digest", "sha256:" + "b" * 64,
            "--territorial-product-decision", "VALIDADO",
            "--electoral-source-run-id", "103",
            "--electoral-source-artifact", "electoral-source",
            "--electoral-source-digest", "sha256:" + "c" * 64,
            "--electoral-source-decision", "VALIDADO",
            "--electoral-product-run-id", "104",
            "--electoral-product-artifact", "m08",
            "--electoral-product-digest", "sha256:" + "d" * 64,
            "--electoral-product-decision", "VALIDADO",
            "--operational-state-result", "success",
            "--output", str(out),
        ]
        subprocess.run(cmd, cwd=ROOT, check=True, capture_output=True, text=True)
        payload = json.loads(out.read_text(encoding="utf-8"))
        assert payload["schema"] == "ddd.full-run-manifest/1.1"
        assert payload["status"] == "SUCCESS"
        assert payload["blocked_validation_gates"] == []
        for phase in payload["phases"][:4]:
            assert phase["validation_decision"] == "VALIDADO"
            assert phase["digest"].startswith("sha256:")


def test_manifest_bloquea_si_una_puerta_no_valida():
    with tempfile.TemporaryDirectory() as td:
        out = Path(td) / "manifest.json"
        common = [
            sys.executable, str(SCRIPT),
            "--territory-id", "demo",
            "--territory-name", "Demo",
            "--edition", "2025",
            "--execution-mode", "reuse",
            "--optimization-algorithm", "Canónico",
            "--workflow-run-id", "999",
            "--source-sha", "abc",
            "--publish-requested", "false",
            "--prepare-territorial-result", "skipped",
            "--generate-result", "skipped",
            "--prepare-electoral-result", "skipped",
            "--incorporate-result", "skipped",
            "--publish-result", "skipped",
            "--prepare-territorial-executed", "false",
            "--generate-executed", "false",
            "--prepare-electoral-executed", "false",
            "--incorporate-executed", "false",
        ]
        for prefix, run_id in (
            ("territorial-source", "101"),
            ("territorial-product", "102"),
            ("electoral-source", "103"),
            ("electoral-product", "104"),
        ):
            common += [
                f"--{prefix}-run-id", run_id,
                f"--{prefix}-artifact", prefix,
                f"--{prefix}-digest", "sha256:" + "a" * 64,
                f"--{prefix}-decision", "BLOQUEADO" if prefix == "electoral-source" else "VALIDADO",
            ]
        common += ["--operational-state-result", "success", "--output", str(out)]
        subprocess.run(common, cwd=ROOT, check=True, capture_output=True, text=True)
        payload = json.loads(out.read_text(encoding="utf-8"))
        assert payload["status"] == "FAILED"
        assert "03 · Preparación de Resultados Electorales" in payload["blocked_validation_gates"]
