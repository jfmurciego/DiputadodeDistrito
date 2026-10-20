"""Regression tests for exact, time-aware parsing of official INE variation archives."""
from __future__ import annotations

import unittest
import zipfile
from pathlib import Path

from herramientas.inspeccionar_variaciones_callejero_f10 import (
    ALLOWED_URLS,
    EXPECTED_SHA256,
    decode_tram_change,
    inspect,
    validate_archive_hash,
)


ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "docs/AUDITORIAS/F10_CROSSWALK_INE_20261020/originales"
TARGETS = (
    "5002501003", "2221301003", "2408904017", "2408906020",
    "3702301002", "4217302016", "4701001012", "3412004006",
    "3710701002", "4109110025", "4109110027", "2102502001",
    "2102502002",
)
ARCHIVES = {
    "0125_0725": ("Var_Callejero_0125_0725.zip", "https://ine.es/prodyser/callejero/Var_Callejero_0125_0725.zip"),
    "0725_0126": ("Var_Callejero_0725_0126.zip", "https://ine.es/prodyser/callejero/Var_Callejero_0725_0126.zip"),
    "0126_0726": ("Var_Callejero_0126_0726.zip", "https://ine.es/prodyser/callejero/Var_Callejero_0126_0726.zip"),
}


class INEVariationArchiveTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.reports = {}
        for period, (name, url) in ARCHIVES.items():
            data = (RAW / name).read_bytes()
            validate_archive_hash(data, url)
            with zipfile.ZipFile(RAW / name) as archive:
                if archive.testzip() is not None:
                    raise AssertionError(f"ZIP_CRC_FAIL:{name}")
            cls.reports[period] = inspect(data, TARGETS)

    def test_all_three_zip_hashes_match_the_official_manifest(self):
        self.assertEqual(set(EXPECTED_SHA256), set(ALLOWED_URLS))
        for _, (name, url) in ARCHIVES.items():
            with self.subTest(name=name):
                self.assertEqual(validate_archive_hash((RAW / name).read_bytes(), url), EXPECTED_SHA256[url])

    def test_altered_zip_is_rejected_before_use(self):
        name, url = ARCHIVES["0125_0725"]
        data = bytearray((RAW / name).read_bytes())
        data[len(data) // 2] ^= 1
        with self.assertRaisesRegex(ValueError, "OFFICIAL_ARCHIVE_SHA256_MISMATCH"):
            validate_archive_hash(bytes(data), url)

    def test_add_modify_delete_records_are_decoded_without_invented_opposites(self):
        first = self.reports["0125_0725"]["change_records_involving_targets"]
        added = [r for r in first if r["change_code"] == "A" and r["other_section"] == "2221301003"]
        deleted = [r for r in first if r["change_code"] == "B" and r["source_section"] == "2102502002"]
        moved = [r for r in self.reports["0725_0126"]["change_records_involving_targets"]
                 if r["source_section"] == "2221301003" and r["other_section"] == "2221301002"]
        self.assertEqual([(r["source_section"], r["date"]) for r in added], [(None, "20250101")])
        self.assertEqual(len(deleted), 21)
        self.assertTrue(all(r["other_section"] is None for r in deleted))
        self.assertEqual(len(moved), 364)
        self.assertTrue(all(r["effective_on_or_before_election"] for r in moved))

    def test_tram_accepts_only_the_variation_causes_defined_for_that_family(self):
        def row_with_cause(cause: str) -> bytes:
            row = bytearray(b" " * 79)
            row[0:10] = b"2102502002"
            row[61:69] = b"20260129"
            row[73:74] = cause.encode("ascii")
            row[74:79] = b"02001"
            return bytes(row)

        self.assertIsNone(decode_tram_change(row_with_cause("R")))
        self.assertEqual(decode_tram_change(row_with_cause("F"))["change_code"], "F")
        self.assertEqual(decode_tram_change(row_with_cause("S"))["change_code"], "S")

    def test_post_election_change_is_not_treated_as_election_day_evidence(self):
        events = self.reports["0126_0726"]["change_records_involving_targets"]
        later = [r for r in events if r["other_section"] == "3702301002" and r["date"] == "20260501"]
        prior = [r for r in events if r["other_section"] == "3702301002" and r["date"] == "20260101"]
        self.assertEqual(len(later), 1)
        self.assertFalse(later[0]["effective_on_or_before_election"])
        self.assertEqual(len(prior), 1)
        self.assertTrue(prior[0]["effective_on_or_before_election"])

    def test_partial_transfers_are_not_promoted_to_whole_section_crosswalks(self):
        for period, report in self.reports.items():
            with self.subTest(period=period):
                self.assertFalse(report["crosswalk_accredited"])
                self.assertIn("not a whole-section or vote crosswalk", report["change_record_scope"])
                self.assertTrue(all("whole_section_equivalence_accredited" not in r
                                    for r in report["change_records_involving_targets"]))

    def test_sevilla_geometry_cases_have_no_section_level_tram_link(self):
        all_events = [r for report in self.reports.values() for r in report["change_records_involving_targets"]]
        for code in ("4109110025", "4109110027"):
            self.assertTrue(any(code in r["section_event_status"] for r in self.reports.values()))
            self.assertFalse(any(code in (r["source_section"], r["other_section"]) for r in all_events))
        self.assertTrue(any(r["municipality"] == "41091" and r["section_link"] == "NOT_PROVIDED_BY_THIS_FAMILY"
                            for report in self.reports.values() for r in report["municipal_variations"]))

    def test_cortegana_partial_move_and_section_persistence_remain_distinct(self):
        events = self.reports["0126_0726"]["change_records_involving_targets"]
        moved = [r for r in events if r["source_section"] == "2102502002" and r["other_section"] == "2102502001"]
        deleted = [r for r in events if r["source_section"] == "2102502001" and r["change_code"] == "B"]
        self.assertEqual(len(moved), 15)
        self.assertEqual(len(deleted), 3)
        self.assertTrue(all(r["effective_on_or_before_election"] for r in moved + deleted))

    def test_all_required_cases_are_reported_even_when_no_tram_record_exists(self):
        for report in self.reports.values():
            self.assertEqual(set(report["section_event_status"]), set(TARGETS))
            self.assertFalse(report["crosswalk_accredited"])
        for report in self.reports.values():
            self.assertEqual(
                report["section_event_status"]["5002501003"]["status"],
                "NO_TRAM_RECORD_IN_PERIOD",
            )

    def test_post_election_records_are_not_counted_as_effective(self):
        report = self.reports["0126_0726"]
        status = report["section_event_status"]["3702301002"]
        self.assertEqual(status["records_on_or_before_election"], 1)
        self.assertEqual(status["records_after_election"], 1)

    def test_archives_do_not_contain_a_secc_family(self):
        for period, report in self.reports.items():
            with self.subTest(period=period):
                self.assertEqual(set(report["families_present"]), {"PSEU", "TRAM", "UP", "VIAS"})
                self.assertFalse(report["section_family_present"])


if __name__ == "__main__":
    unittest.main()
