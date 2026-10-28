"""Versión: 1.0.0; nombre: cabecera de gobernanza en contratos materializados; fecha: 2026-10-28.
Alcance: el materializador de 01 reescribe el contrato territorial sin borrar su cabecera.
Estado: candidato. Cambios/motivo: el registro del 28-10 dejó aragon_2025.yaml sin VERSIÓN/ANTERIOR.
Anterior: ninguno.
"""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import yaml

from herramientas.materializar_contrato_generacion import ywrite


class MaterializedContractHeaderTests(unittest.TestCase):
    def test_rewrite_keeps_leading_governance_comments(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "territorio_2025.yaml"
            path.write_text("# VERSIÓN: 1.0.0\n# ANTERIOR: legacy/x.yaml\nmeta:\n  year: 2025\n", encoding="utf-8")
            ywrite(path, {"meta": {"year": 2025, "status": "generation_ready"}})
            text = path.read_text(encoding="utf-8")
            self.assertTrue(text.startswith("# VERSIÓN: 1.0.0\n# ANTERIOR: legacy/x.yaml\n"))
            self.assertEqual({"meta": {"year": 2025, "status": "generation_ready"}}, yaml.safe_load(text))

    def test_new_contract_has_no_invented_header(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "nuevo" / "territorio_2025.yaml"
            ywrite(path, {"meta": {"year": 2025}})
            self.assertEqual("meta:\n  year: 2025\n", path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
