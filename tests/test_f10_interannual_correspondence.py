"""Regresiones F10, versión 1.0.0, fecha 2026-10-12, estado candidato.
Alcance: correspondencias interanuales, sin redistribución ni promoción.
Cambios/motivo: contactos no son contribuciones; conservar contabilidad completa.
Origen: diagnóstico F10 de adquisiciones oficiales 2026-10-11.
"""
import unittest

from shapely.geometry import box

from herramientas.compatibilidad_poblacion_seccionado import (
    _intersects, reconcile_population_sectioning,
)


def reconcile(population, target, origin):
    return reconcile_population_sectioning(
        territory_id="regression", edition="2025", population_year=2025,
        section_year=2026, population_rows=population,
        target_geometry_rows=target, origin_geometry_rows=origin)


class InterannualCorrespondenceTests(unittest.TestCase):
    def test_boundary_and_point_contacts_are_not_contributions(self):
        self.assertFalse(_intersects(box(0, 0, 1, 1), box(1, 0, 2, 1)))
        self.assertFalse(_intersects(box(0, 0, 1, 1), box(1, 1, 2, 2)))
        self.assertTrue(_intersects(box(0, 0, 1, 1), box(.5, 0, 1.5, 1)))

    def test_splits_with_unmapped_touching_neighbours_are_detected_and_blocked(self):
        report = reconcile(
            [("0100101001", 100), ("0100101002", 200)],
            [("0100101001", box(0, 0, 1, 1)),
             ("0100101003", box(1, 0, 2, 1)),
             ("0100101002", box(2, 0, 3, 1)),
             ("0100101004", box(3, 0, 4, 1))],
            [("0100101001", box(0, 0, 2, 1)),
             ("0100101002", box(2, 0, 4, 1))])
        self.assertEqual(sum(r["kind"] == "SPLIT" for r in report["correspondences"]), 2)
        self.assertEqual(report["decision"], "BLOCKED")
        self.assertFalse(report["population"]["exact_conservation"])
        self.assertEqual(report["population"]["unassigned_total"], 300)
        self.assertTrue(report["population"]["accounting_exact"])

    def test_exact_code_permutation_does_not_leave_stale_boundary_change(self):
        report = reconcile(
            [("0100101001", 100), ("0100101002", 200)],
            [("0100101001", box(1, 0, 2, 1)), ("0100101002", box(0, 0, 1, 1))],
            [("0100101001", box(0, 0, 1, 1)), ("0100101002", box(1, 0, 2, 1))])
        self.assertEqual(report["geometric_changes"], [])
        self.assertNotIn("SAME_CODE_BOUNDARY_CHANGED", report["causes"])
        self.assertTrue(report["population"]["exact_conservation"])
        self.assertEqual(report["population"]["unassigned_total"], 0)

    def test_unassigned_population_keeps_real_section_values(self):
        report = reconcile(
            [("0100101001", 100), ("0100101002", 200)],
            [("0100101001", box(0, 0, 1, 1)), ("0100101002", box(2, 0, 4, 1))],
            [("0100101001", box(0, 0, 1, 1)), ("0100101002", box(2, 0, 3, 1))])
        self.assertEqual(report["population"]["unassigned_by_section"],
                         [{"section_id": "0100101002", "population": 200}])
        self.assertEqual(report["population"]["input_total"], 300)
        self.assertEqual(report["population"]["assigned_total"], 100)
        self.assertFalse(report["population"]["exact_conservation"])


class F10RealEvidenceTests(unittest.TestCase):
    def test_real_unassigned_population_is_retained_and_blocked_in_three_territories(self):
        import gzip
        import json
        from pathlib import Path
        from shapely.geometry import shape
        for territory, deficit in (("aragon", 31024), ("andalucia", 319989),
                                   ("castilla_y_leon", 84197)):
            with self.subTest(territory=territory):
                fixture = json.loads(gzip.decompress((Path(__file__).parent /
                    "fixtures" / "f10_interannual" / f"{territory}.json.gz").read_bytes()))
                self.assertEqual(fixture["expected_unassigned_total"], deficit)
                report = reconcile(fixture["population_rows"],
                    [(k, shape(g)) for k, g in fixture["target_geometry_rows"]],
                    [(k, shape(g)) for k, g in fixture["origin_geometry_rows"]])
                self.assertEqual(report["population"]["unassigned_total"], deficit)
                self.assertTrue(report["population"]["accounting_exact"])
                self.assertFalse(report["population"]["exact_conservation"])
                self.assertEqual(report["decision"], "BLOCKED")
                self.assertEqual(sum(c["source_population_total"] for c in
                    report["unresolved_components"]), deficit)
                self.assertTrue(all(c["population_assignment"] == "NOT_ACCREDITED"
                    for c in report["unresolved_components"]))
                self.assertIn("UNACCREDITED_SECTIONING_CHANGE", report["causes"])
                if territory == "aragon":
                    self.assertIn({"source_keys": ["2221301002", "2221301003"],
                        "target_keys": ["2221301002"], "kind": "FUSION",
                        "evidence": "geometric_union_after_crs_normalization"},
                        report["correspondences"])


class PopulationInputPreservationTests(unittest.TestCase):
    def test_acquisition_keeps_original_bytes_when_valencia_coverage_blocks(self):
        import copy
        import hashlib
        import json
        import tempfile
        from pathlib import Path
        from herramientas.adquirir_fuentes_oficiales import acquire
        from tests.test_fuentes_oficiales_preparacion import CATALOG, SimulatedINE, declaration
        dec = copy.deepcopy(declaration("comunidad_valenciana"))
        dec["territory"]["population_year"] = dec["territory"]["section_year"] = 2023
        dec["environment_policy"]["test"] = ["simulated"]
        fetcher = SimulatedINE(dec, expected_sections=3, edition=2023,
                               omit_population_province="46")
        original = fetcher("https://www.ine.es/jaxiT3/files/t/csv_bdsc/65034.csv")
        with tempfile.TemporaryDirectory() as td:
            evidence = Path(td) / "evidence"
            _, _, _, decision = acquire(catalog=CATALOG, declaration=dec,
                evidence_dir=evidence, environment="test", acquisition_mode="simulated",
                fetcher=fetcher, root_dir=Path(td))
            self.assertEqual(decision["decision"], "BLOCKED")
            record = json.loads((evidence / "raw_population_input.json").read_text())
            self.assertEqual((evidence / record["path"]).read_bytes(), original)
            self.assertEqual(record["sha256"], hashlib.sha256(original).hexdigest())
            self.assertEqual(record["source_year"], 2023)
            self.assertTrue(any("Cobertura provincial" in r["reason"]
                                for r in decision["reasons"]))

    def test_snapshot_origin_is_preserved_and_collision_does_not_replace_evidence(self):
        import json
        import tempfile
        from pathlib import Path
        from herramientas.adquirir_fuentes_oficiales import _persist_population_payload
        identity = {"snapshot_path": "cache/ine.zip", "snapshot_sha256": "a" * 64,
                    "snapshot_official_origin_url": "https://www.ine.es/historic.csv",
                    "snapshot_acquired_at": "2023-01-01", "snapshot_edition": 2023}
        with tempfile.TemporaryDirectory() as td:
            args = dict(source_id="population", source_year=2023,
                        url="https://www.ine.es/current.csv", mode="verified_snapshot",
                        payload=b"population", snapshot_identity=identity)
            record = _persist_population_payload(Path(td), **args)
            self.assertEqual(record["url"], identity["snapshot_official_origin_url"])
            self.assertEqual(record["snapshot_identity"], identity)
            with self.assertRaisesRegex(ValueError, "IDENTITY_COLLISION"):
                _persist_population_payload(Path(td), **{**args, "payload": b"different"})
            self.assertEqual(json.loads((Path(td) / "raw_population_input.json").read_text()), record)
            self.assertEqual((Path(td) / record["path"]).read_bytes(), b"population")


class ValenciaHistoricalSnapshotTests(unittest.TestCase):
    def test_historical_official_rows_cover_valencia_without_promoting_snapshot(self):
        import csv
        import io
        import json
        from pathlib import Path
        from herramientas.adquirir_fuentes_oficiales import _filter_population
        from tests.test_fuentes_oficiales_preparacion import declaration
        fixture = json.loads((Path(__file__).parent / "fixtures" /
            "f10_interannual" / "comunidad_valenciana_population.json").read_text())
        stream = io.StringIO()
        writer = csv.DictWriter(stream, fieldnames=fixture["sample_rows"][0].keys(), delimiter="\t")
        writer.writeheader()
        writer.writerows(fixture["sample_rows"])
        filtered, checks = _filter_population(stream.getvalue().encode(),
            declaration("comunidad_valenciana"), 2023, ["03", "12", "46"])
        self.assertEqual(checks["provinces"], ["03", "12", "46"])
        self.assertEqual(checks["rows"], 3)
        self.assertIn(b"4600101001", filtered)
        self.assertEqual(fixture["observed_rows_by_province"], {"03": 1236, "12": 444, "46": 1823})
        self.assertEqual(fixture["status"], "independent_not_promoted")
        self.assertEqual(fixture["original_F10_payload"], "NOT_PRESERVED")
