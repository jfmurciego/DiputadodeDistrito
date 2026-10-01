#!/usr/bin/env python3
import importlib.util
import json
import re
import tempfile
import unittest
from pathlib import Path

from ddd_core.electoral_contract import PartyDictionary

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "m07_strict_votes",
    ROOT / "modulos/07_agregar_resultados_electorales.py",
)
M07 = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(M07)


def parties():
    return PartyDictionary({
        "schema_family": "ddd-party-dictionary",
        "schema_version": "1.0.0",
        "unknown_party_policy": "reject",
        "parties": [
            {"canonical_id": "P", "display_name": "P", "aliases": [], "classification": ""}
        ],
    })


class StrictElectoralVoteBoundary(unittest.TestCase):
    def _read(self, text, suffix, adapter):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / ("source" + suffix)
            path.write_text(text, encoding="utf-8")
            return M07.read_results(path, adapter, "CUSEC_KEY", parties())

    @staticmethod
    def _long_adapter():
        return {
            "kind": "long_csv",
            "separator": ";",
            "section_field": "section",
            "party_field": "party",
            "votes_field": "votes",
        }

    @staticmethod
    def _nested_adapter():
        return {
            "kind": "nested_json",
            "records_path": "zones",
            "section_field": "section",
            "party_records_field": "results",
            "party_field": "party",
            "votes_field": "votes",
        }

    @staticmethod
    def _wide_adapter(party_columns=None):
        return {
            "kind": "wide_polling_station_csv",
            "separator": ";",
            "province_field": "province",
            "municipality_field": "municipality",
            "polling_station_field": "polling",
            "polling_station_regex": r"(?P<district>\d+)-(?P<section>\d+)-[A-Z]",
            "party_columns": party_columns or ["P"],
        }

    def test_long_csv_accepts_zero_and_explicit_decimal_integers(self):
        frame, sections = self._read(
            "section;party;votes\n"
            "0100101001;P;0\n"
            "0100101002;P;1\n"
            "0100101003;P;17\n",
            ".csv",
            self._long_adapter(),
        )
        self.assertEqual(list(frame["votes"]), [0, 1, 17])
        self.assertEqual(
            sections,
            {"0100101001", "0100101002", "0100101003"},
        )
        self.assertEqual(frame.attrs["rejected_rows"], 0)

    def test_decimal_policy_rejects_dot_zero_and_exponent_without_truncation(self):
        for raw in ("1.0", "1e0"):
            with self.subTest(raw=raw), self.assertRaisesRegex(
                ValueError,
                rf"ELECTORAL_VOTES_INVALID.*adapter=long_csv.*value='{re.escape(raw)}'.*entero decimal exacto",
            ):
                self._read(
                    f"section;party;votes\n0100101001;P;{raw}\n",
                    ".csv",
                    self._long_adapter(),
                )

    def test_long_csv_missing_vote_blocks_instead_of_becoming_zero(self):
        with self.assertRaisesRegex(
            ValueError,
            r"ELECTORAL_VOTES_INVALID.*adapter=long_csv.*row=csv\[2\].*field=votes",
        ):
            self._read(
                "section;party;votes\n0100101001;P;\n",
                ".csv",
                self._long_adapter(),
            )

    def test_long_csv_fraction_is_not_truncated(self):
        with self.assertRaisesRegex(ValueError, r"ELECTORAL_VOTES_INVALID.*value='1\.5'"):
            self._read(
                "section;party;votes\n0100101001;P;1.5\n",
                ".csv",
                self._long_adapter(),
            )

    def test_long_csv_missing_section_and_unknown_party_block_instead_of_disappearing(self):
        with self.assertRaisesRegex(
            ValueError,
            r"ELECTORAL_INPUT_INVALID.*row=csv\[2\].*field=section.*cause=SECTION_ID_MISSING",
        ):
            self._read(
                "section;party;votes\n;P;1\n",
                ".csv",
                self._long_adapter(),
            )
        with self.assertRaisesRegex(
            ValueError,
            r"ELECTORAL_INPUT_INVALID.*row=csv\[2\].*field=party.*cause=PARTY_NOT_RECOGNIZED",
        ):
            self._read(
                "section;party;votes\n0100101001;UNKNOWN;1\n",
                ".csv",
                self._long_adapter(),
            )

    def test_nested_json_accepts_integer_and_rejects_negative_with_location(self):
        frame, _ = self._read(
            json.dumps({
                "zones": [{
                    "section": "0100101001",
                    "results": [{"party": "P", "votes": 3}],
                }]
            }),
            ".json",
            self._nested_adapter(),
        )
        self.assertEqual(frame["votes"].tolist(), [3])
        self.assertEqual(frame.attrs["rejected_rows"], 0)
        with self.assertRaisesRegex(
            ValueError,
            r"ELECTORAL_VOTES_INVALID.*adapter=nested_json.*zone\[1\].results\[1\].*votos negativos",
        ):
            self._read(
                json.dumps({
                    "zones": [{
                        "section": "0100101001",
                        "results": [{"party": "P", "votes": -1}],
                    }]
                }),
                ".json",
                self._nested_adapter(),
            )

    def test_nested_json_float_even_integral_is_not_coerced(self):
        with self.assertRaisesRegex(
            ValueError,
            r"ELECTORAL_VOTES_INVALID.*value=1\.0.*sin truncamiento",
        ):
            self._read(
                json.dumps({
                    "zones": [{
                        "section": "0100101001",
                        "results": [{"party": "P", "votes": 1.0}],
                    }]
                }),
                ".json",
                self._nested_adapter(),
            )

    def test_nested_json_mixed_valid_zone_and_results_without_section_blocks(self):
        payload = {
            "zones": [
                {
                    "section": "0100101001",
                    "results": [{"party": "P", "votes": 4}],
                },
                {
                    "results": [{"party": "P", "votes": 2}],
                },
            ]
        }
        with self.assertRaisesRegex(
            ValueError,
            r"ELECTORAL_INPUT_INVALID.*adapter=nested_json.*row=zone\[2\].*field=section.*cause=SECTION_ID_MISSING_WITH_RESULTS",
        ):
            self._read(json.dumps(payload), ".json", self._nested_adapter())

    def test_nested_json_unknown_party_blocks_instead_of_disappearing(self):
        with self.assertRaisesRegex(
            ValueError,
            r"ELECTORAL_INPUT_INVALID.*zone\[1\].results\[1\].*field=party.*cause=PARTY_NOT_RECOGNIZED",
        ):
            self._read(
                json.dumps({
                    "zones": [{
                        "section": "0100101001",
                        "results": [{"party": "UNKNOWN", "votes": 1}],
                    }]
                }),
                ".json",
                self._nested_adapter(),
            )

    def test_wide_csv_accepts_zero_and_integer_votes(self):
        frame, sections = self._read(
            "province;municipality;polling;P\n"
            "1;1;1-1-A;0\n"
            "1;2;1-2-A;9\n",
            ".csv",
            self._wide_adapter(),
        )
        self.assertEqual(frame["votes"].tolist(), [0, 9])
        self.assertEqual(sections, {"0100101001", "0100201002"})
        self.assertEqual(frame.attrs["rejected_rows"], 0)

    def test_wide_csv_invalid_vote_blocks_with_location(self):
        with self.assertRaisesRegex(
            ValueError,
            r"ELECTORAL_VOTES_INVALID.*adapter=wide_polling_station_csv.*row=csv\[2\].*field=P",
        ):
            self._read(
                "province;municipality;polling;P\n1;1;1-1-A;bad\n",
                ".csv",
                self._wide_adapter(),
            )

    def test_wide_csv_mixed_valid_and_invalid_locator_blocks_instead_of_filtering_row(self):
        with self.assertRaisesRegex(
            ValueError,
            r"ELECTORAL_INPUT_INVALID.*adapter=wide_polling_station_csv.*row=csv\[3\].*field=polling.*cause=POLLING_STATION_LOCATOR_INVALID",
        ):
            self._read(
                "province;municipality;polling;P\n"
                "1;1;1-1-A;7\n"
                "1;2;INVALID;3\n",
                ".csv",
                self._wide_adapter(),
            )

    def test_wide_csv_partial_locator_match_is_rejected(self):
        with self.assertRaisesRegex(
            ValueError,
            r"ELECTORAL_INPUT_INVALID.*row=csv\[2\].*field=polling.*cause=POLLING_STATION_LOCATOR_INVALID",
        ):
            self._read(
                "province;municipality;polling;P\n1;1;1-1-A-extra;7\n",
                ".csv",
                self._wide_adapter(),
            )

    def test_wide_csv_invalid_province_and_municipality_codes_block_with_field_and_cause(self):
        with self.assertRaisesRegex(
            ValueError,
            r"ELECTORAL_INPUT_INVALID.*row=csv\[2\].*field=province.*cause=PROVINCE_CODE_INVALID",
        ):
            self._read(
                "province;municipality;polling;P\nX;1;1-1-A;7\n",
                ".csv",
                self._wide_adapter(),
            )
        with self.assertRaisesRegex(
            ValueError,
            r"ELECTORAL_INPUT_INVALID.*row=csv\[2\].*field=municipality.*cause=MUNICIPALITY_CODE_INVALID",
        ):
            self._read(
                "province;municipality;polling;P\n1;X;1-1-A;7\n",
                ".csv",
                self._wide_adapter(),
            )

    def test_wide_csv_overwidth_codes_are_invalid_even_when_numeric(self):
        with self.assertRaisesRegex(
            ValueError,
            r"ELECTORAL_INPUT_INVALID.*field=province.*cause=PROVINCE_CODE_INVALID",
        ):
            self._read(
                "province;municipality;polling;P\n123;1;1-1-A;7\n",
                ".csv",
                self._wide_adapter(),
            )
        with self.assertRaisesRegex(
            ValueError,
            r"ELECTORAL_INPUT_INVALID.*field=municipality.*cause=MUNICIPALITY_CODE_INVALID",
        ):
            self._read(
                "province;municipality;polling;P\n1;1234;1-1-A;7\n",
                ".csv",
                self._wide_adapter(),
            )
        with self.assertRaisesRegex(
            ValueError,
            r"ELECTORAL_INPUT_INVALID.*field=polling.*cause=POLLING_STATION_LOCATOR_INVALID",
        ):
            self._read(
                "province;municipality;polling;P\n1;1;123-1-A;7\n",
                ".csv",
                self._wide_adapter(),
            )

    def test_wide_csv_unknown_party_column_blocks_instead_of_accepting_empty_party(self):
        with self.assertRaisesRegex(
            ValueError,
            r"ELECTORAL_INPUT_INVALID.*row=header.*field=party_columns.*cause=PARTY_NOT_RECOGNIZED",
        ):
            self._read(
                "province;municipality;polling;UNKNOWN\n1;1;1-1-A;7\n",
                ".csv",
                self._wide_adapter(["UNKNOWN"]),
            )


if __name__ == "__main__":
    unittest.main()
