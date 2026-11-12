"""Regresiones del revisor de PR: no silenciar fallos de OAuth ni falsear GO.
PROYECTO: Diputado de Distrito
VERSIÓN: 1.0.0
FECHA: 2026-11-12
ESTADO: candidato
CAMBIOS: prueba JSON, SHA, proveedor bloqueado y configuración de autenticación.
MOTIVO: el action de Claude puede devolver is_error=true, subtype=success, sin revisar nada.
ANTERIOR: ninguna (fichero nuevo)
"""
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from herramientas.diagnosticar_revisor_pr import (
    RevisionInvalida,
    _read_execution,
    clasificar_fallo,
    main,
    validar_resultado,
)

ROOT = Path(__file__).resolve().parents[1]
HEAD = "a" * 40


class TestReviewerDiagnostics(unittest.TestCase):
    def test_validar_veredicto_real_sha_exacto(self):
        expected = {"caso": "PR-741", "sha": HEAD, "veredicto": "PASS_WITH_EXCEPTIONS",
                    "defectos": [], "ci": "no_aplica", "siguiente": "owner merge"}
        self.assertEqual(validar_resultado(json.dumps(expected), HEAD, []), expected)

    def test_rechazar_sha_corto_o_ajeno(self):
        data = {"sha": HEAD[:10], "veredicto": "PASS", "defectos": [], "siguiente": "merge"}
        with self.assertRaisesRegex(RevisionInvalida, "SHA"):
            validar_resultado(json.dumps(data), HEAD, [])

    def test_no_convertir_error_oauth_en_aprobacion(self):
        event = [{"type": "system", "subtype": "init", "model": "claude-sonnet-5-5"},
                 {"type": "result", "subtype": "success", "is_error": True,
                  "num_turns": 1, "total_cost_usd": 0, "api_error_status": 401}]
        self.assertIn("401", clasificar_fallo(event))
        with self.assertRaisesRegex(RevisionInvalida, "401"):
            validar_resultado("", HEAD, event)

    def test_rechazo_429_y_error_sin_diagnostico(self):
        self.assertIn("429", clasificar_fallo([{"api_error_status": 429}]))
        self.assertIn("primera llamada", clasificar_fallo([
            {"is_error": True, "num_turns": 1, "subtype": "success"}]))
        self.assertIn("archivo de diagnóstico", clasificar_fallo([]))

    def test_blocked_no_satisface_puerta(self):
        v = {"sha": HEAD, "veredicto": "BLOCKED", "defectos": [], "siguiente": "investigar"}
        env = {"EXPECTED_HEAD_SHA": HEAD, "CLAUDE_STRUCTURED_OUTPUT": json.dumps(v),
               "CLAUDE_EXECUTION_FILE": ""}
        with patch.dict(os.environ, env):
            self.assertEqual(main(), 1)

    def test_archivo_json_y_jsonl(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "out.json"
            p.write_text(json.dumps([{"type": "result", "api_error_status": 401}]))
            self.assertEqual(len(_read_execution(str(p))), 1)
            p.write_text('{"type":"system"}\n{"type":"result","api_error_status":429}\n')
            self.assertEqual(len(_read_execution(str(p))), 2)

    def test_workflow_no_permite_pass_falso_y_tiene_alternativa_api_key(self):
        workflow = (ROOT / ".github/workflows/revisor-pr.yml").read_text(encoding="utf-8")
        self.assertIn("ANTHROPIC_API_KEY", workflow)
        self.assertIn("CLAUDE_CODE_OAUTH_TOKEN", workflow)
        self.assertIn("continue-on-error: true", workflow)
        self.assertIn("python herramientas/diagnosticar_revisor_pr.py", workflow)
        self.assertIn('[[ "$HEAD_SHA" == "$sha" ]]', workflow)
        self.assertIn('"BLOCKED"', workflow)
        self.assertIn("git diff --no-ext-diff", workflow)
        self.assertIn("--allowedTools Read,Grep,Glob", workflow)
        self.assertNotIn("Bash(gh pr", workflow)


if __name__ == "__main__":
    unittest.main()
