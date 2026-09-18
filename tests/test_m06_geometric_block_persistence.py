#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PROYECTO: Diputado de Distrito
COMPONENTE: regresión de persistencia de la puerta geométrica M06
VERSIÓN: 1.0.1
NOMBRE DE VERSIÓN: BLOCK sobre exit 2
FECHA: 2026-09-16
ESTADO: vigente
FUNCIÓN: garantizar que una auditoría que escribe decision=BLOCK y termina con código 2 conserva BLOCK como output antes de propagar el fallo.
CAMBIOS: acota la comprobación estática al tramo posterior a set +e del bloque geométrico, evitando capturar el set -euo pipefail previo.
MOTIVO: comprobar el orden operativo real del manejo del código de salida sin falsos positivos por directivas shell anteriores.
ANTERIOR: 1.0.0
"""
from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "produccion-distritos.yml"


class GeometricBlockPersistence(unittest.TestCase):
    def test_workflow_captures_decision_before_propagating_audit_failure(self):
        text = WORKFLOW.read_text(encoding="utf-8")
        start = text.index("      - id: geometric")
        end = text.index("      - name: Registrar estado verificable de producción", start)
        block = text[start:end]
        handling = block[block.index("set +e"):]

        required = [
            "set +e",
            "audit_rc=$?",
            "set -e",
            "decision=UNKNOWN",
            'if [[ -f "$output" ]]; then',
            'echo "decision=$decision" >> "$GITHUB_OUTPUT"',
            'echo "audit_path=$output" >> "$GITHUB_OUTPUT"',
            'exit "$audit_rc"',
        ]
        positions = [handling.index(token) for token in required]
        self.assertEqual(positions, sorted(positions))

    def test_synthetic_block_never_degrades_to_unknown_on_exit_2(self):
        with tempfile.TemporaryDirectory() as tmp:
            audit = Path(tmp) / "audit.json"
            audit.write_text(json.dumps({"decision": "BLOCK"}), encoding="utf-8")
            script = r'''
set -euo pipefail
output="$1"
set +e
bash -c 'exit 2'
audit_rc=$?
set -e
decision=UNKNOWN
if [[ -f "$output" ]]; then
  decision="$(python -c 'import json,sys; print(json.load(open(sys.argv[1],encoding="utf-8"))["decision"])' "$output")"
fi
printf '%s\n' "$decision"
exit "$audit_rc"
'''
            result = subprocess.run(
                ["bash", "-c", script, "bash", str(audit)],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(result.returncode, 2)
            self.assertEqual(result.stdout.strip(), "BLOCK")
            self.assertNotEqual(result.stdout.strip(), "UNKNOWN")


if __name__ == "__main__":
    unittest.main()
