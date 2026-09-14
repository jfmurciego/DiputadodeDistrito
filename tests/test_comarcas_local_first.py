"""Pruebas sintéticas del adaptador comarcal local-first M01/M03/M06."""
from __future__ import annotations

import importlib.util
from pathlib import Path
import tempfile
import unittest

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]


def load_module(name: str, relative: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


COMARCAS = load_module("ddd_comarcas", "ddd_core/comarcas.py")


def sections():
    return pd.DataFrame({"CUSEC_KEY": ["2200101001", "2200101002", "2200201001"]})


def write_source(path: Path, rows):
    pd.DataFrame(rows).to_csv(path, index=False)


def config(path: Path, require_full_coverage=True):
    return {
        "enabled": True,
        "path": str(path),
        "sep": "auto",
        "require_full_coverage": require_full_coverage,
        "join": {
            "comarcas_key_col": "Municipio código",
            "comarca_code_col": "Comarca código",
            "comarca_name_col": "Comarca nombre",
        },
    }


class ComarcasLocalFirst(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.source = Path(self.tmp.name) / "COMARCAS.csv"

    def tearDown(self):
        self.tmp.cleanup()

    def test_union_por_codigo_municipal_y_cobertura_total(self):
        write_source(self.source, [
            {"Municipio código": "22001", "Comarca código": "C01", "Comarca nombre": "Norte"},
            {"Municipio código": "22002", "Comarca código": "C02", "Comarca nombre": "Sur"},
        ])
        out, report = COMARCAS.attach_comarcas(sections(), config(self.source))
        self.assertEqual(out["COMARCA_CODIGO"].tolist(), ["C01", "C01", "C02"])
        self.assertEqual(report["coverage_ratio"], 1.0)
        self.assertEqual(report["municipalities_missing"], [])

    def test_rechaza_duplicado_municipal_ambiguo(self):
        write_source(self.source, [
            {"Municipio código": "22001", "Comarca código": "C01", "Comarca nombre": "Norte"},
            {"Municipio código": "22001", "Comarca código": "C99", "Comarca nombre": "Otra"},
        ])
        with self.assertRaisesRegex(ValueError, "varias comarcas"):
            COMARCAS.attach_comarcas(sections(), config(self.source))

    def test_faltantes_bloquean_solo_si_el_contrato_lo_exige(self):
        write_source(self.source, [
            {"Municipio código": "22001", "Comarca código": "C01", "Comarca nombre": "Norte"},
        ])
        with self.assertRaisesRegex(ValueError, "sin cobertura"):
            COMARCAS.attach_comarcas(sections(), config(self.source))
        out, report = COMARCAS.attach_comarcas(sections(), config(self.source, False))
        self.assertTrue(pd.isna(out.loc[2, "COMARCA_CODIGO"]))
        self.assertEqual(report["municipalities_missing"], ["22002"])

    def test_m03_preserva_comarca_sin_usarla_como_arista(self):
        frame = pd.DataFrame({
            "CUSEC_KEY": ["2200101001", "2200201001"],
            "POP_2025": [10, 20],
            "COMARCA_CODIGO": ["C01", "C02"],
            "COMARCA_NOMBRE": ["Norte", "Sur"],
        })
        text = (ROOT / "modulos/03_construir_grafo.py").read_text(encoding="utf-8")
        self.assertIn('optional_fields=[c for c in ("COMARCA_CODIGO","COMARCA_NOMBRE")', text)
        self.assertIn("nodes=build_nodes", text)

    def test_m06_declara_comarcas_en_catalogo_y_composicion(self):
        text = (ROOT / "modulos/06_consolidar_distritos.py").read_text(encoding="utf-8")
        self.assertIn('row["community_codes"]', text)
        self.assertIn('row["community_names"]', text)
        self.assertIn("community_code_field, community_name_field", text)


if __name__ == "__main__":
    unittest.main()
