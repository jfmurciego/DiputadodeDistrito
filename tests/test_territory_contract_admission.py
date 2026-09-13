#!/usr/bin/env python3
"""Pruebas R034 v1.0.0: admisión de contratos sin ejecutar M01-M06."""
from __future__ import annotations
import tempfile
import unittest
from pathlib import Path
import yaml

from ddd_core.territory_contract import validate_production_contract

ROOT = Path(__file__).resolve().parents[1]


class ProductionContractAdmission(unittest.TestCase):
    def test_baselines_certificados_son_admitidos(self):
        for territory in ("aragon", "castilla_y_leon"):
            report = validate_production_contract(ROOT / "territorios" / territory / "config" / f"{territory}_2025.yaml", expected_territory=territory)
            self.assertEqual(report["status"], "ADMITTED", report["errors"])
            self.assertEqual(len(report["contract_sha256"]), 64)

    def mutated(self, mutate):
        source = ROOT / "territorios" / "aragon" / "config" / "aragon_2025.yaml"
        data = yaml.safe_load(source.read_text(encoding="utf-8"))
        mutate(data)
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", suffix=".yaml", dir=source.parent, delete=False) as handle:
            yaml.safe_dump(data, handle, sort_keys=False, allow_unicode=True)
            path = Path(handle.name)
        try:
            return validate_production_contract(path, expected_territory="aragon")
        finally:
            path.unlink(missing_ok=True)

    def test_rechaza_restriccion_heredada_o_ausente(self):
        report = self.mutated(lambda data: data["territory_contract"].pop("population_cap_ratio"))
        self.assertEqual(report["status"], "REJECTED")
        self.assertTrue(any("population_cap_ratio" in error for error in report["errors"]))

    def test_rechaza_cadena_m04_m05_rota(self):
        report = self.mutated(lambda data: data["modulos"]["modulo_05_optimizar_distritos"].__setitem__("in_geojson", "otra_salida.zip"))
        self.assertEqual(report["status"], "REJECTED")
        self.assertIn("cadena rota M04→M05 asignación", report["errors"])

    def test_rechaza_k_incoherente(self):
        report = self.mutated(lambda data: data["modulos"]["modulo_06_consolidar_distritos"].__setitem__("expected_districts", 68))
        self.assertEqual(report["status"], "REJECTED")
        self.assertTrue(any("incoherencia K" in error for error in report["errors"]))

    def test_rechaza_salida_fuera_del_repositorio(self):
        report = self.mutated(lambda data: data["modulos"]["modulo_06_consolidar_distritos"].__setitem__("out_catalog_csv", "/tmp/catalogo.csv"))
        self.assertEqual(report["status"], "REJECTED")
        self.assertTrue(any("salida fuera" in error for error in report["errors"]))


if __name__ == "__main__":
    unittest.main()
