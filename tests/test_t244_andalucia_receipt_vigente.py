"""VERSIÓN: 1.0.2
FECHA: 2026-11-14
CAMBIOS: T-244 — con el catálogo vivo, Andalucía 2025 resuelve el receipt territorial
253f…/40946875467 (preparation_evidence) y no el independiente 057a…/38082966768, cuyo
paquete está purgado. La comparación completa del catálogo antes/después (solo difiere
Andalucía) se hizo en la PR y consta en el registro: un test contra un commit fijo se
salta en clon superficial y falla con cualquier cambio legítimo posterior.
MOTIVO: la 00 de Andalucía (run 43011608060) falló con exit 72 «Artefacto territorial
ausente o ambiguo» porque el resolver prefería el receipt independiente purgado.
CAMBIOS 1.0.2 (T-322): lee el receipt de la raíz congelada tests/fixtures/previo_r3 (un P10 nuevo de aut01 cambia el estado vivo); la regla de elegir el 253f/40946875467 queda ligada a ese estado.
CAMBIOS 1.0.1 (T-220): ids de territorio nuevos de la tabla maestra (aut01…nac52, D-61); el id viejo se lee vía ddd_core.territorio_ids.
ANTERIOR: legacy/tests/test_t244_andalucia_receipt_vigente_v1.0.1.py
"""
from __future__ import annotations

import unittest
from pathlib import Path

from tests._previo_r3 import raiz_previo_r3
from herramientas.consumir_par_fuentes_legislatura import (
    _territorial_receipt_evidence,
    validate_territorial_receipt,
)

ROOT = Path(__file__).resolve().parents[1]
RECEIPT_253F = (
    "territorios/aut01/evidencia/fuentes_territoriales/2025/"
    "253f7c0dc82793977197c5dad117d30f1cd96ceaf0d8cab696c0c36bb6111b09/40946875467/receipt.json"
)


class AndaluciaReceiptVigenteTests(unittest.TestCase):
    def test_resolver_elige_receipt_253f(self):
        state, receipt = validate_territorial_receipt(root_dir=raiz_previo_r3(canonico=True), territory="aut01", edition="2025")
        self.assertNotIn("independent_source_evidence", state)
        evidence = _territorial_receipt_evidence(state)
        self.assertEqual(RECEIPT_253F, evidence["receipt_path"])
        self.assertEqual(40946875467, receipt["run_id"])
        self.assertEqual(
            "253f7c0dc82793977197c5dad117d30f1cd96ceaf0d8cab696c0c36bb6111b09",
            receipt["territorial_identity_sha256"],
        )
        self.assertEqual("ddd-source-package-aut01-2025-40946875467", receipt["artifact_name"])


if __name__ == "__main__":
    unittest.main()
