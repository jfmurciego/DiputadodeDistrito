import unittest
from pathlib import Path

from ddd_core.m06_schema import inspect_catalog


ROOT = Path(__file__).resolve().parents[1]
CATALOGS = {
    "aut02": ROOT / "territorios/aut02/resultados/ejecuciones/gh-34599224954-1/M06/catalogo_distritos.csv",
    "aut07": ROOT / "territorios/aut07/resultados/ejecuciones/gh-34701897922-1/M06/catalogo_distritos.csv",
    "aut11": ROOT / "territorios/aut11/resultados/ejecuciones/gh-34703213474-1/M06/catalogo_distritos.csv",
}


class M06SchemaContractTest(unittest.TestCase):
    def test_all_certified_catalogues_resolve_same_metric_name(self):
        reports = {name: inspect_catalog(path) for name, path in CATALOGS.items()}
        for report in reports.values():
            self.assertIn("polsby_popper", report["canonical_fields"])
            self.assertNotIn("compactness_polsby_popper", report["canonical_fields"])
        self.assertEqual(reports["aut02"]["schema_status"], "PASS_LEGACY_ADAPTED")
        self.assertEqual(reports["aut07"]["schema_status"], "PASS_LEGACY_ADAPTED")

    def test_active_m06_producer_uses_canonical_metric(self):
        source = (ROOT / "modulos/06_consolidar_distritos.py").read_text(encoding="utf-8")
        self.assertIn('"polsby_popper": compactness', source)
        self.assertNotIn('"compactness_polsby_popper": compactness', source)


if __name__ == "__main__":
    unittest.main()
