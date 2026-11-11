"""VERSIÓN: 1.0.0
FECHA: 2026-11-11
CAMBIOS: T-244 — con el catálogo vivo, Andalucía 2025 resuelve el receipt territorial
253f…/40946875467 (preparation_evidence) y no el independiente 057a…/38082966768, cuyo
paquete está purgado; el resto de filas del catálogo no cambia respecto a la base.
MOTIVO: la 00 de Andalucía (run 43011608060) falló con exit 72 «Artefacto territorial
ausente o ambiguo» porque el resolver prefería el receipt independiente purgado.
ANTERIOR: ninguna (fichero nuevo)
"""
from __future__ import annotations

import subprocess
import unittest
from pathlib import Path

import yaml

from herramientas.consumir_par_fuentes_legislatura import (
    _territorial_receipt_evidence,
    validate_territorial_receipt,
)

ROOT = Path(__file__).resolve().parents[1]
CATALOG_REL = "configuracion/catalogo_preparacion.yaml"
# Base de main antes de T-244 (origin/main al abrir la PR).
BASE_COMMIT = "6ad5b525a72328c916f98ca06ee6c6035293e440"
RECEIPT_253F = (
    "territorios/andalucia/evidencia/fuentes_territoriales/2025/"
    "253f7c0dc82793977197c5dad117d30f1cd96ceaf0d8cab696c0c36bb6111b09/40946875467/receipt.json"
)


def _rows(catalog: dict) -> dict:
    return {row["territory_id"]: row for row in catalog["territories"]}


class AndaluciaReceiptVigenteTests(unittest.TestCase):
    def test_resolver_elige_receipt_253f(self):
        state, receipt = validate_territorial_receipt(root_dir=ROOT, territory="andalucia", edition="2025")
        self.assertNotIn("independent_source_evidence", state)
        evidence = _territorial_receipt_evidence(state)
        self.assertEqual(RECEIPT_253F, evidence["receipt_path"])
        self.assertEqual(40946875467, receipt["run_id"])
        self.assertEqual(
            "253f7c0dc82793977197c5dad117d30f1cd96ceaf0d8cab696c0c36bb6111b09",
            receipt["territorial_identity_sha256"],
        )
        self.assertEqual("ddd-source-package-andalucia-2025-40946875467", receipt["artifact_name"])

    def test_otras_filas_conservan_su_receipt_independiente(self):
        """La comparación completa antes/después se hizo en la PR (solo difería Andalucía);
        aquí se fija lo estable: sólo Andalucía pierde el receipt independiente."""
        try:
            old_text = subprocess.run(
                ["git", "show", f"{BASE_COMMIT}:{CATALOG_REL}"],
                cwd=ROOT, check=True, capture_output=True, text=True,
            ).stdout
        except (OSError, subprocess.CalledProcessError):
            self.skipTest("base del catálogo no disponible en este clon (clon superficial)")
        old_rows = _rows(yaml.safe_load(old_text))
        new_rows = _rows(yaml.safe_load((ROOT / CATALOG_REL).read_text(encoding="utf-8")))

        def independents(rows: dict) -> dict:
            return {
                (tid, ed): state["independent_source_evidence"]
                for tid, row in rows.items()
                for ed, state in (row.get("editions") or {}).items()
                if state.get("independent_source_evidence") is not None
            }

        expected = independents(old_rows)
        self.assertIn(("andalucia", "2025"), expected)
        expected.pop(("andalucia", "2025"))
        self.assertEqual(expected, independents(new_rows))


if __name__ == "__main__":
    unittest.main()
