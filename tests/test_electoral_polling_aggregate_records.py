from __future__ import annotations

import copy
import importlib.util
import tempfile
import unittest
from pathlib import Path

from ddd_core.electoral_contract import (
    PartyDictionary,
    _validate_wide_polling_station_adapter,
)


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "m07_polling_aggregate_records",
    ROOT / "modulos/07_agregar_resultados_electorales.py",
)
M07 = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(M07)


def parties(*names: str) -> PartyDictionary:
    return PartyDictionary({
        "schema_family": "ddd-party-dictionary",
        "schema_version": "1.0.0",
        "unknown_party_policy": "reject",
        "parties": [
            {"canonical_id": name, "display_name": name}
            for name in names
        ],
    })


def galicia_style_adapter() -> dict:
    return {
        "kind": "wide_polling_station_csv",
        "separator": ";",
        "province_field": "Cód Cir",
        "municipality_field": "Cód Con",
        "polling_station_field": "Mesa",
        "polling_station_regex": (
            r"^(?P<district>\d{2})-(?P<section>\d{3})-[A-Z0-9]+$"
        ),
        "party_columns": ["BNG", "PP"],
        "record_classification": {
            "polling_station": {"mode": "locator_contract"},
            "aggregates": [
                {
                    "id": "provincial_total",
                    "match": {
                        "field": "Cód Cir",
                        "equals": "Total",
                        "required_empty_fields": ["Cód Con", "Mesa"],
                    },
                    "scope": {
                        "kind": "preceding_polling_station_block",
                        "partition_field": "Cód Cir",
                    },
                    "vote_reconciliation": {
                        "kind": "party_columns_exact_sum",
                        "empty_aggregate_value": "reject",
                    },
                }
            ],
            "require_aggregate_for_each_block": True,
        },
    }


class PollingStationAggregateRecordTests(unittest.TestCase):
    def _read(self, text: str, adapter: dict, dictionary: PartyDictionary):
        with tempfile.TemporaryDirectory() as td:
            source = Path(td) / "mesas.csv"
            source.write_text(text, encoding="utf-8")
            return M07.read_results(
                source,
                adapter,
                "CUSEC_KEY",
                dictionary,
            )

    def test_contract_rejects_permissive_aggregate_semantics(self):
        cases = []

        not_applicable = galicia_style_adapter()
        not_applicable["record_classification"]["aggregates"][0][
            "vote_reconciliation"
        ]["empty_aggregate_value"] = "not_applicable"
        cases.append((
            not_applicable,
            r"empty_aggregate_value debe ser reject",
        ))

        not_comparable = galicia_style_adapter()
        not_comparable["record_classification"]["aggregates"][0][
            "vote_reconciliation"
        ] = {
            "kind": "not_comparable",
            "reason": "fixture",
        }
        cases.append((
            not_comparable,
            r"vote_reconciliation.kind debe ser party_columns_exact_sum",
        ))

        non_boolean = galicia_style_adapter()
        non_boolean["record_classification"][
            "require_aggregate_for_each_block"
        ] = 1
        cases.append((
            non_boolean,
            r"require_aggregate_for_each_block debe ser booleano",
        ))

        duplicate_parties = galicia_style_adapter()
        duplicate_parties["party_columns"] = ["BNG", "BNG"]
        cases.append((
            duplicate_parties,
            r"party_columns debe ser una lista no vacía de nombres únicos",
        ))

        for adapter, expected in cases:
            with self.subTest(expected=expected):
                with self.assertRaisesRegex(ValueError, expected):
                    _validate_wide_polling_station_adapter(
                        copy.deepcopy(adapter),
                        "fixture",
                    )

    def test_wide_contract_can_declare_no_aggregate_rows(self):
        adapter = galicia_style_adapter()
        adapter["record_classification"]["aggregates"] = []
        adapter["record_classification"][
            "require_aggregate_for_each_block"
        ] = False

        _validate_wide_polling_station_adapter(
            adapter,
            "fixture",
        )

        text = (
            "Cód Cir;Cód Con;Mesa;BNG;PP\n"
            "15;007;01-001-A;10;20\n"
        )
        frame, sections = self._read(
            text,
            adapter,
            parties("BNG", "PP"),
        )
        self.assertEqual(sections, {"1500701001"})
        self.assertEqual(frame.attrs["recognized_aggregate_rows"], 0)

    def test_wide_contract_cannot_require_undeclared_aggregate(self):
        adapter = galicia_style_adapter()
        adapter["record_classification"]["aggregates"] = []
        adapter["record_classification"][
            "require_aggregate_for_each_block"
        ] = True
        with self.assertRaisesRegex(
            ValueError,
            r"no puede exigir agregados sin declarar reglas",
        ):
            _validate_wide_polling_station_adapter(
                adapter,
                "fixture",
            )

    def test_two_raw_columns_cannot_map_to_same_canonical_party(self):
        adapter = galicia_style_adapter()
        adapter["party_columns"] = ["A", "ALIAS_A"]
        dictionary = PartyDictionary({
            "schema_family": "ddd-party-dictionary",
            "schema_version": "1.0.0",
            "unknown_party_policy": "reject",
            "parties": [{
                "canonical_id": "A",
                "display_name": "A",
                "aliases": ["ALIAS_A"],
            }],
        })
        text = (
            "Cód Cir;Cód Con;Mesa;A;ALIAS_A\n"
            "15;007;01-001-A;10;10\n"
            "Total;;;10;10\n"
        )
        with self.assertRaisesRegex(
            ValueError,
            r"PARTY_COLUMNS_CANONICAL_DUPLICATE",
        ):
            self._read(text, adapter, dictionary)

    def test_optional_aggregate_reconciles_only_immediately_preceding_block(self):
        adapter = galicia_style_adapter()
        adapter["record_classification"][
            "require_aggregate_for_each_block"
        ] = False
        text = (
            "Cód Cir;Cód Con;Mesa;BNG;PP\n"
            "15;007;01-001-A;10;20\n"
            "27;001;01-001-A;5;7\n"
            "Total;;;5;7\n"
        )

        frame, sections = self._read(
            text,
            adapter,
            parties("BNG", "PP"),
        )

        self.assertEqual(
            sections,
            {"1500701001", "2700101001"},
        )
        evidence = frame.attrs["recognized_aggregates"]
        self.assertEqual(len(evidence), 1)
        self.assertEqual(
            evidence[0]["scope"]["partition_value"],
            "27",
        )
        self.assertEqual(
            evidence[0]["scope"]["polling_station_rows"],
            1,
        )

    def test_required_aggregate_blocks_before_partition_transition(self):
        text = (
            "Cód Cir;Cód Con;Mesa;BNG;PP\n"
            "15;007;01-001-A;10;20\n"
            "27;001;01-001-A;5;7\n"
            "Total;;;5;7\n"
        )

        with self.assertRaisesRegex(
            ValueError,
            r"MISSING_EXPECTED_AGGREGATE",
        ):
            self._read(
                text,
                galicia_style_adapter(),
                parties("BNG", "PP"),
            )

    def test_contract_rejects_mixed_partition_fields_for_aggregate_rules(self):
        adapter = galicia_style_adapter()
        second = copy.deepcopy(
            adapter["record_classification"]["aggregates"][0]
        )
        second["id"] = "other_total"
        second["match"]["equals"] = "GrandTotal"
        second["scope"]["partition_field"] = "Cód Con"
        adapter["record_classification"]["aggregates"].append(second)

        with self.assertRaisesRegex(
            ValueError,
            r"debe usar un único scope.partition_field",
        ):
            _validate_wide_polling_station_adapter(
                adapter,
                "fixture",
            )

    def test_four_real_provincial_totals_are_recognized_and_not_counted(self):
        # Totales oficiales observados en el artefacto del run 37159898924.
        text = (
            "Cód Cir;Cód Con;Mesa;BNG;PP\n"
            "15;007;01-001-A;199462;292651\n"
            "Total;;;199462;292651\n"
            "27;001;01-001-A;46940;100123\n"
            "Total;;;46940;100123\n"
            "32;001;01-001-A;44222;88694\n"
            "Total;;;44222;88694\n"
            "36;001;01-001-A;180068;230245\n"
            "Total;;;180068;230245\n"
        )

        frame, sections = self._read(
            text,
            galicia_style_adapter(),
            parties("BNG", "PP"),
        )

        self.assertEqual(
            sections,
            {
                "1500701001",
                "2700101001",
                "3200101001",
                "3600101001",
            },
        )
        self.assertEqual(frame.attrs["recognized_aggregate_rows"], 4)
        self.assertEqual(frame.attrs["polling_station_rows"], 4)
        evidence = frame.attrs["recognized_aggregates"]
        self.assertEqual(
            [item["scope"]["partition_value"] for item in evidence],
            ["15", "27", "32", "36"],
        )
        self.assertTrue(
            all(
                item["vote_reconciliation"]["status"] == "MATCH"
                for item in evidence
            )
        )
        self.assertTrue(
            all(item["included_in_vote_rows"] is False for item in evidence)
        )
        self.assertTrue(
            all(item["source"]["name"] == "mesas.csv" for item in evidence)
        )
        self.assertTrue(
            all(
                len(item["source"]["sha256"]) == 64
                for item in evidence
            )
        )
        self.assertTrue(
            all(
                "/" not in item["source"]["name"]
                and "\\" not in item["source"]["name"]
                for item in evidence
            )
        )

        observed = {
            (row.CUSEC_KEY, row.party): int(row.votes)
            for row in frame.itertuples()
        }
        self.assertEqual(observed[("1500701001", "BNG")], 199462)
        self.assertEqual(observed[("1500701001", "PP")], 292651)
        self.assertEqual(
            int(frame["votes"].sum()),
            199462 + 292651
            + 46940 + 100123
            + 44222 + 88694
            + 180068 + 230245,
        )

    def test_empty_polling_locator_is_not_silently_treated_as_aggregate(self):
        text = (
            "Cód Cir;Cód Con;Mesa;BNG;PP\n"
            "15;007;01-001-A;10;20\n"
            "15;007;;5;7\n"
            "Total;;;15;27\n"
        )
        with self.assertRaisesRegex(
            ValueError,
            r"ELECTORAL_INPUT_INVALID.*row=csv\[3\].*field=Mesa"
            r".*cause=RECORD_CLASS_INVALID",
        ):
            self._read(
                text,
                galicia_style_adapter(),
                parties("BNG", "PP"),
            )

    def test_discordant_recognized_aggregate_blocks_with_scope(self):
        text = (
            "Cód Cir;Cód Con;Mesa;BNG;PP\n"
            "15;007;01-001-A;10;20\n"
            "Total;;;11;20\n"
        )
        with self.assertRaisesRegex(
            ValueError,
            r"ELECTORAL_AGGREGATE_MISMATCH.*aggregate_id=provincial_total"
            r".*scope=Cód Cir:15",
        ):
            self._read(
                text,
                galicia_style_adapter(),
                parties("BNG", "PP"),
            )

    def test_blank_aggregate_value_blocks_even_when_polling_sum_exists(self):
        adapter = {
            "kind": "wide_polling_station_csv",
            "separator": ";",
            "province_field": "province",
            "municipality_field": "municipality",
            "polling_station_field": "polling",
            "polling_station_regex": (
                r"^(?P<district>\d+)-(?P<section>\d+)-[A-Z]$"
            ),
            "party_columns": ["P", "Q"],
            "record_classification": {
                "polling_station": {"mode": "locator_contract"},
                "aggregates": [
                    {
                        "id": "regional_summary",
                        "match": {
                            "field": "province",
                            "equals": "SUM",
                            "required_empty_fields": [
                                "municipality",
                                "polling",
                            ],
                        },
                        "scope": {
                            "kind": "preceding_polling_station_block",
                            "partition_field": "province",
                        },
                        "vote_reconciliation": {
                            "kind": "party_columns_exact_sum",
                            "empty_aggregate_value": "reject",
                        },
                    }
                ],
                "require_aggregate_for_each_block": True,
            },
        }
        text = (
            "province;municipality;polling;P;Q\n"
            "7;42;3-12-A;5;37\n"
            "SUM;;;5;\n"
        )

        with self.assertRaisesRegex(
            ValueError,
            r"ELECTORAL_VOTES_INVALID.*row=csv\[3\].*field=Q",
        ):
            self._read(
                text,
                adapter,
                parties("P", "Q"),
            )

    def test_second_format_with_other_identifiers_reconciles_exactly(self):
        adapter = {
            "kind": "wide_polling_station_csv",
            "separator": ";",
            "province_field": "province",
            "municipality_field": "municipality",
            "polling_station_field": "polling",
            "polling_station_regex": (
                r"^(?P<district>\d+)-(?P<section>\d+)-[A-Z]$"
            ),
            "party_columns": ["P", "Q"],
            "record_classification": {
                "polling_station": {"mode": "locator_contract"},
                "aggregates": [
                    {
                        "id": "regional_summary",
                        "match": {
                            "field": "province",
                            "equals": "SUM",
                            "required_empty_fields": [
                                "municipality",
                                "polling",
                            ],
                        },
                        "scope": {
                            "kind": "preceding_polling_station_block",
                            "partition_field": "province",
                        },
                        "vote_reconciliation": {
                            "kind": "party_columns_exact_sum",
                            "empty_aggregate_value": "reject",
                        },
                    }
                ],
                "require_aggregate_for_each_block": True,
            },
        }
        text = (
            "province;municipality;polling;P;Q\n"
            "7;42;3-12-A;5;0\n"
            "SUM;;;5;0\n"
        )

        frame, sections = self._read(
            text,
            adapter,
            parties("P", "Q"),
        )

        self.assertEqual(sections, {"0704203012"})
        self.assertEqual(
            frame.loc[frame["party"] == "Q", "votes"].tolist(),
            [0],
        )
        comparisons = {
            item.get("party_column"): item
            for item in frame.attrs["recognized_aggregates"][0][
                "vote_reconciliation"
            ]["comparisons"]
        }
        self.assertEqual(comparisons["P"]["status"], "MATCH")
        self.assertEqual(comparisons["Q"]["status"], "MATCH")
        self.assertEqual(comparisons["Q"]["aggregate_value"], 0)


if __name__ == "__main__":
    unittest.main()
