import unittest
from pathlib import Path

from ddd_core.m06_schema import inspect_catalog


ROOT = Path(__file__).resolve().parents[1]
CATALOGS = {
    "aragon": ROOT / "territorios/aragon/resultados/ejecuciones/gh-34599224954-1/M06/catalogo_distritos.csv",
    "castilla_y_leon": ROOT / "territorios/castilla_y_leon/resultados/ejecuciones/gh-34701897922-1/M06/catalogo_distritos.csv",
    "extremadura": ROOT / "territorios/extremadura/resultados/ejecuciones/gh-34703213474-1/M06/catalogo_distritos.csv",
}


class M06SchemaContractTest(unittest.TestCase):
    def test_all_certified_catalogues_resolve_same_metric_name(self):
        reports = {name: inspect_catalog(path) for name, path in CATALOGS.items()}
        for report in reports.values():
            self.assertIn("polsby_popper", report["canonical_fields"])
            self.assertNotIn("compactness_polsby_popper", report["canonical_fields"])
        self.assertEqual(reports["aragon"]["schema_status"], "PASS_LEGACY_ADAPTED")
        self.assertEqual(reports["castilla_y_leon"]["schema_status"], "PASS_LEGACY_ADAPTED")

    def test_active_m06_producer_uses_canonical_metric(self):
        source = (ROOT / "modulos/06_consolidar_distritos.py").read_text(encoding="utf-8")
        self.assertIn('"polsby_popper": compactness', source)
        self.assertNotIn('"compactness_polsby_popper": compactness', source)


if __name__ == "__main__":
    unittest.main()
