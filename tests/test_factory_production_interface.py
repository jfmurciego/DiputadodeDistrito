#!/usr/bin/env python3
"""Pruebas R035.3: la línea común se deriva del contrato y no se activa sola."""
from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("resolver", ROOT / "herramientas" / "resolver_ejecucion_territorial.py")
RESOLVER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(RESOLVER)


class FactoryProductionInterface(unittest.TestCase):
    def test_dos_contratos_resuelven_la_misma_interfaz(self):
        for territory in ("aragon", "castilla_y_leon"):
            decision = RESOLVER.resolve(str(ROOT / "territorios" / territory / "config" / f"{territory}_2025.yaml"))
            self.assertEqual(decision["decision"], "ADMITTED", decision["contract"]["errors"])
            self.assertEqual(decision["territory_id"], territory)
            self.assertTrue(decision["params"].startswith("territorios/"))
            self.assertNotEqual(decision["cache_dir"], decision["runs_dir"])

    def test_interfaz_manual_unica_no_contiene_seleccion_codificada(self):
        text = (ROOT / ".github/workflows/produccion-distritos.yml").read_text(encoding="utf-8")
        self.assertIn("${{ inputs.territory_id }}", text)
        self.assertNotIn("aragon) params=", text)
        self.assertNotIn("castilla_y_leon) params=", text)

    def test_linea_comun_es_reutilizable_y_execute_esta_bloqueado(self):
        text = (ROOT / ".github/workflows/producir-territorio-por-contrato.yml").read_text(encoding="utf-8")
        self.assertNotIn("workflow_dispatch", text)
        self.assertIn("workflow_call", text)
        self.assertNotIn("push:", text)
        self.assertIn("EXECUTE_WITH_EXPLICIT_USER_AUTHORIZATION", text)
        self.assertIn("resolver_ejecucion_territorial.py", text)


if __name__ == "__main__":
    unittest.main()
