import io
import json
import unittest
from pathlib import Path

from herramientas.auditar_filas_vacias_ine_65034 import selected_rows, verify_hash


class Ine65034EmptyRowsTests(unittest.TestCase):
    def test_preserved_source_audit_reproduces_all_46_classifications(self):
        root = Path(__file__).resolve().parents[1]
        evidence = json.loads((root / "docs/AUDITORIAS/F10_CIERRE_VALENCIA_20261012/filas_vacias_65034_reproducidas.json").read_text(encoding="utf-8"))
        self.assertEqual("ddd.f10-ine-65034-empty-rows-audit/1.0", evidence["schema"])
        self.assertEqual(4048, evidence["numeric_rows"])
        self.assertEqual(46, evidence["empty_rows"])
        self.assertTrue(evidence["empty_rows_match_reference_exactly"])
        self.assertEqual({"absent_from_census_2023": 46, "present_in_geometry_2025": 35, "absent_from_geometry_2025": 11}, evidence["counts"])
        self.assertTrue(all(not row["geometria_2023_SECCIONADO"] for row in evidence["classifications_recomputed_from_official_inputs"].values()))
        self.assertEqual(46, len(evidence["rows"]))

    def test_reconstructs_empty_ids_only_for_requested_selection(self):
        source = (
            "Total Nacional\tProvincias\tMunicipios\tSecciones\tSexo\tEdad\tPeriodo\tTotal\n"
            "España\t03 Alicante\t03014 Alacant/Alicante\t0301401017 Sección 1017\tTotal\tTodas las edades\t2023\t\n"
            "España\t03 Alicante\t03014 Alacant/Alicante\t0301401018 Sección 1018\tTotal\tTodas las edades\t2023\t123\n"
            "España\t03 Alicante\t03014 Alacant/Alicante\t0301401019 Sección 1019\tTotal\tTodas las edades\t2022\t\n"
            "España\t03 Alicante\t03014 Alacant/Alicante\t0301401020 Sección 1020\tHombres\tTodas las edades\t2023\t\n"
            "España\t08 Barcelona\t08001 Barcelona\t0800101001 Sección 1\tTotal\tTodas las edades\t2023\t\n"
        )
        numeric, empty = selected_rows(io.StringIO(source))
        self.assertEqual(["0301401018"], [row["CUSEC"] for row in numeric])
        self.assertEqual(["0301401017"], [row["CUSEC"] for row in empty])
        self.assertEqual("03014", empty[0]["CUMUN"])
        self.assertEqual("Alacant/Alicante", empty[0]["municipio"])

    def test_rejects_incompatible_csv_schema(self):
        with self.assertRaises(ValueError):
            selected_rows(io.StringIO("a\tb\n1\t2\n"))

    def test_hash_mismatch_is_a_hard_failure(self):
        verify_hash("abc", "abc", "fixture")
        with self.assertRaisesRegex(ValueError, "fixture"):
            verify_hash("abc", "def", "fixture")


if __name__ == "__main__":
    unittest.main()
