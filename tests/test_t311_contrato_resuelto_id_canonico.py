"""T-311: el contrato resuelto que la preparación copia a autNN_2025.yaml lleva el id canónico.

VERSIÓN: 1.0.0
ANTERIOR: ninguna (fichero nuevo)
"""
from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
import zipfile
from pathlib import Path

from ddd_core.territorio_ids import id_legacy
from herramientas.materializar_contrato_generacion import resolved_source_contract


def _sha(contract: dict) -> str:
    c = dict(contract)
    c.pop("contract_sha256", None)
    return hashlib.sha256(json.dumps(c, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def _package(root: Path, territory_id: str) -> Path:
    contract = {"schema": "ddd.resolved-source-contract/1.0",
                "territory": {"territory_id": territory_id, "territory_name": "X", "project_edition": "2025"},
                "sources": {}, "runtime": {}}
    contract["contract_sha256"] = _sha(contract)
    with zipfile.ZipFile(root / "prepared_sources.zip", "w") as z:
        z.writestr("resolved_source_contract.json", json.dumps(contract))
    return root


class ContratoResueltoIdCanonico(unittest.TestCase):
    def test_paquete_reutilizado_con_id_legacy_sale_canonico(self):
        legacy = id_legacy("aut02")
        with tempfile.TemporaryDirectory() as d:
            out = resolved_source_contract(_package(Path(d), legacy))
        self.assertEqual(out["territory"]["territory_id"], "aut02")
        self.assertEqual(out["contract_sha256"], _sha(out))
        self.assertTrue(out["package_contract_sha256"])
        self.assertNotEqual(out["package_contract_sha256"], out["contract_sha256"])

    def test_id_canonico_no_cambia_el_contrato(self):
        with tempfile.TemporaryDirectory() as d:
            out = resolved_source_contract(_package(Path(d), "aut11"))
        self.assertEqual(out["territory"]["territory_id"], "aut11")
        self.assertNotIn("package_contract_sha256", out)

    def test_id_fuera_de_tabla_se_conserva(self):
        with tempfile.TemporaryDirectory() as d:
            out = resolved_source_contract(_package(Path(d), "piloto_x"))
        self.assertEqual(out["territory"]["territory_id"], "piloto_x")


if __name__ == "__main__":
    unittest.main()
