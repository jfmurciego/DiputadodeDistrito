import json
import csv
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "docs/AUDITORIAS/F10_CIERRE_VALENCIA_20261012/universo_2023.json"


class ValenciaUniverseEvidenceTests(unittest.TestCase):
    def test_ine_section_universe_matches_population_exactly(self):
        report = json.loads(REPORT.read_text(encoding="utf-8"))
        self.assertEqual("ddd.f10-valencia-2023-universe-audit/1.0", report["schema"])
        self.assertTrue(report["identity_exact"])
        self.assertEqual(3503, report["population_rows"])
        self.assertEqual(3503, report["geometry_sections"])
        self.assertEqual(0, report["invalid_population_rows_in_selected_table"])
        self.assertEqual(0, report["blank_population_rows_in_selected_table"])
        self.assertEqual(5216195, report["population_total"])
        self.assertEqual({"03": 1955268, "12": 604086, "46": 2656841}, report["province_totals"])

    def test_wfs_count_excess_is_district_features_not_sections(self):
        report = json.loads(REPORT.read_text(encoding="utf-8"))
        self.assertEqual(360, report["district_features_valencia"])
        self.assertEqual(2183, report["valencia_raw_features"])
        self.assertEqual({"SECCIONADO": 1823, "DISTRITO": 360}, report["province_features_by_type"]["46"])
        self.assertEqual(3503, sum(row["SECCIONADO"] for row in report["province_features_by_type"].values()))

    def test_evidence_binds_the_materialized_sources(self):
        report = json.loads(REPORT.read_text(encoding="utf-8"))
        self.assertEqual(64, len(report["section_identity_sha256"]))
        self.assertEqual({"population_tsv", "geometry_03", "geometry_12", "geometry_46"}, set(report["source_sha256"]))
        self.assertTrue(all(len(value) == 64 for value in report["source_sha256"].values()))

    def test_blank_rows_are_outside_2023_target_and_classified_by_municipality(self):
        crosswalk = ROOT / "docs/AUDITORIAS/F10_CIERRE_VALENCIA_20261012/46_cusec_sin_observacion.csv"
        with crosswalk.open(encoding="utf-8", newline="") as stream:
            rows = list(csv.DictReader(stream))
        self.assertEqual(46, len(rows))
        self.assertEqual(46, len({row["CUSEC"] for row in rows}))
        self.assertTrue(all(row["municipio"] and row["CUMUN"] for row in rows))
        self.assertTrue(all(row["observacion_65034_2023"] == "VACIA" for row in rows))
        self.assertTrue(all(row["geometria_2023_SECCIONADO"] == "NO" for row in rows))
        self.assertTrue(all(row["censo_2023_personas"] == "NO" for row in rows))
        self.assertEqual(35, sum(row["geometria_2025_SECCIONADO"] == "SI" for row in rows))
        self.assertEqual(11, sum(row["geometria_2025_SECCIONADO"] == "NO" for row in rows))

    def test_nineteen_consumers_keep_source_electoral_and_production_gates_separate(self):
        path = ROOT / "docs/AUDITORIAS/F10_CIERRE_VALENCIA_20261012/matriz_19_consumidores.json"
        matrix = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(19, len(matrix["rows"]))
        self.assertEqual(14, sum(row["source_accreditation"] == "PASS_HISTORICAL_RECEIPT" for row in matrix["rows"]))
        indexed = {row["territory_id"]: row for row in matrix["rows"]}
        for tid in ("extremadura", "aragon", "castilla_y_leon", "andalucia"):
            self.assertEqual("PASS_INDEPENDENT_RECEIPT", indexed[tid]["source_accreditation"])
            self.assertEqual("NOT_RUN_BY_MANDATE", indexed[tid]["production"])
        self.assertEqual("BLOCKED_TWO_OVERLAPS_EXCEED_1M2", indexed["comunidad_valenciana"]["territorial_consumption"])
        self.assertEqual("BLOCKED", matrix["overall_f10"])


if __name__ == "__main__":
    unittest.main()
