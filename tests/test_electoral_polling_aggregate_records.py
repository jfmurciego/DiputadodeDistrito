from __future__ import annotations

import copy
import importlib.util
import tempfile
import unittest
from pathlib import Path

from ddd_core.electoral_contract import (
    PartyDictionary,
    _validate_wide_polling_station_adapter,
    load_election_contract,
    validate_structural_provenance_document,
)
from herramientas.preparar_fuente_electoral import merge_delimited_sources


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


def scoped_adapter(*, require_aggregate: bool = True) -> dict:
    return {
        "kind": "wide_polling_station_csv",
        "separator": ";",
        "province_field": "province",
        "municipality_field": "municipality",
        "polling_station_field": "polling",
        "polling_station_regex": (
            r"^(?P<district>\d+)-(?P<section>\d+)-[A-Z]$"
        ),
        "party_columns": ["P", "Q"],
        "party_applicability": {
            "Q": {
                "field": "province",
                "equals": ["32"],
                "reason": "Q sólo concurre en la circunscripción 32",
            }
        },
        "record_classification": {
            "polling_station": {"mode": "locator_contract"},
            "aggregates": [
                {
                    "id": "provincial_total",
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
            "require_aggregate_for_each_block": require_aggregate,
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

    def _read_merged(
        self,
        raws: list[tuple[str, str]],
        adapter: dict,
        dictionary: PartyDictionary,
    ):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            paths = []
            source_ids = []
            for source_id, text in raws:
                path = root / f"{source_id}.csv"
                path.write_text(text, encoding="utf-8")
                paths.append(path)
                source_ids.append(source_id)
            merged = root / "merged.csv"
            info = merge_delimited_sources(
                paths,
                merged,
                source_ids=source_ids,
            )
            runtime_adapter = copy.deepcopy(adapter)
            runtime_adapter["structural_provenance"] = {
                "path": info["structural_provenance_path"],
                "sha256": info["structural_provenance_sha256"],
            }
            return M07.read_results(
                merged,
                runtime_adapter,
                "CUSEC_KEY",
                dictionary,
            )

    def test_contract_rejects_invalid_party_applicability(self):
        cases = []

        unknown = scoped_adapter()
        unknown["party_applicability"] = {
            "R": {
                "field": "province",
                "equals": ["32"],
                "reason": "fixture",
            }
        }
        cases.append((unknown, r"candidatura ajena a party_columns"))

        numeric_field = scoped_adapter()
        numeric_field["party_applicability"]["Q"]["field"] = 32
        cases.append((numeric_field, r"field debe ser texto no vacío"))

        duplicate_values = scoped_adapter()
        duplicate_values["party_applicability"]["Q"]["equals"] = [
            "32",
            " 32 ",
        ]
        cases.append((duplicate_values, r"equals contiene valores duplicados"))

        blank_reason = scoped_adapter()
        blank_reason["party_applicability"]["Q"]["reason"] = " "
        cases.append((blank_reason, r"reason debe ser texto no vacío"))

        missing_sidecar = scoped_adapter()
        cases.append((
            missing_sidecar,
            r"structural_provenance es obligatorio",
        ))

        for adapter, expected in cases:
            with self.subTest(expected=expected):
                with self.assertRaisesRegex(ValueError, expected):
                    _validate_wide_polling_station_adapter(
                        copy.deepcopy(adapter),
                        "fixture",
                    )

    def test_contract_load_rejects_scope_field_missing_in_any_raw(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            raw_a = root / "a.csv"
            raw_b = root / "b.csv"
            raw_a.write_text(
                "province;municipality;polling;P\n"
                "15;7;1-1-A;5\n"
                "SUM;;;5\n",
                encoding="utf-8",
            )
            raw_b.write_text(
                "province;municipality;polling;region;P;Q\n"
                "32;1;1-1-A;north;7;0\n"
                "SUM;;;north;7;0\n",
                encoding="utf-8",
            )
            merged = root / "merged.csv"
            info = merge_delimited_sources(
                [raw_a, raw_b],
                merged,
                source_ids=["a", "b"],
            )
            dictionary = root / "parties.json"
            dictionary.write_text(
                '{"schema_family":"ddd-party-dictionary",'
                '"schema_version":"1.0.0",'
                '"unknown_party_policy":"reject",'
                '"parties":[{"canonical_id":"P","display_name":"P"},'
                '{"canonical_id":"Q","display_name":"Q"}]}',
                encoding="utf-8",
            )
            import hashlib
            sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
            contract = root / "contract.json"
            adapter = scoped_adapter()
            adapter["party_applicability"]["Q"]["field"] = "region"
            adapter["party_applicability"]["Q"]["equals"] = ["north"]
            adapter["structural_provenance"] = {
                "path": Path(
                    info["structural_provenance_path"]
                ).name,
                "sha256": info["structural_provenance_sha256"],
            }
            contract.write_text(
                __import__("json").dumps({
                    "schema_family": "ddd-election",
                    "schema_version": "1.0.0",
                    "election_id": "demo_2026",
                    "territory_id": "demo",
                    "title": "Demo",
                    "election_date": "2026-01-01",
                    "input_mode": "verifiable_file",
                    "boundary_independence": True,
                    "sources": [{
                        "path": merged.name,
                        "sha256": sha(merged),
                        "publisher": "Official",
                        "source_url": "https://official.example/results",
                        "retrieved_at": "2026-01-02",
                        "adapter": adapter,
                    }],
                    "party_dictionary": {
                        "path": dictionary.name,
                        "sha256": sha(dictionary),
                    },
                    "reconciliation": {},
                }),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(
                ValueError,
                r"campo de ámbito 'region'.*ausente en raws: a",
            ):
                load_election_contract(
                    contract,
                    project_root=root,
                    expected_territory_id="demo",
                )

    def test_structural_document_rejects_impossible_metadata(self):
        base = {
            "schema": "ddd-electoral-structural-provenance/1.0",
            "merged_source": {
                "sha256": "a" * 64,
                "records": 1,
                "columns": ["province", "P"],
            },
            "sources": [{
                "source_id": "a",
                "raw_file": "a.csv",
                "raw_sha256": "b" * 64,
                "records": 1,
                "merged_row_index_start": 0,
                "merged_row_index_end_exclusive": 1,
                "original_columns": ["province", "P"],
            }],
        }
        invalid_name = copy.deepcopy(base)
        invalid_name["sources"][0]["raw_file"] = "../a.csv"
        with self.assertRaisesRegex(
            ValueError,
            r"raw_file debe ser un nombre de fichero",
        ):
            validate_structural_provenance_document(
                invalid_name,
                context="fixture",
            )

        invalid_union = copy.deepcopy(base)
        invalid_union["merged_source"]["columns"] = [
            "province", "P", "ghost",
        ]
        with self.assertRaisesRegex(
            ValueError,
            r"no coincide con la unión ordenada",
        ):
            validate_structural_provenance_document(
                invalid_union,
                context="fixture",
            )

    def test_party_scope_distinguishes_structural_absence_from_zero(self):
        adapter = scoped_adapter()
        raw_15 = (
            "province;municipality;polling;P\n"
            "15;7;1-1-A;5\n"
            "SUM;;;5\n"
        )
        raw_32 = (
            "province;municipality;polling;P;Q\n"
            "32;1;1-1-A;7;0\n"
            "SUM;;;7;0\n"
        )

        frame, sections = self._read_merged(
            [("province_15", raw_15), ("province_32", raw_32)],
            adapter,
            parties("P", "Q"),
        )

        self.assertEqual(
            sections,
            {"1500701001", "3200101001"},
        )
        self.assertEqual(
            frame.loc[frame["party"] == "Q", "votes"].tolist(),
            [0],
        )
        self.assertEqual(frame.attrs["not_applicable_party_cells"], 1)
        applicability = frame.attrs["party_applicability"]
        self.assertEqual(len(applicability), 1)
        self.assertEqual(applicability[0]["party_column"], "Q")
        self.assertEqual(applicability[0]["scope_value"], "15")
        self.assertEqual(applicability[0]["source_id"], "province_15")
        self.assertRegex(applicability[0]["raw_sha256"], r"^[0-9a-f]{64}$")

        first, second = frame.attrs["recognized_aggregates"]
        first_q = next(
            item
            for item in first["vote_reconciliation"]["comparisons"]
            if item.get("party_column") == "Q"
        )
        second_q = next(
            item
            for item in second["vote_reconciliation"]["comparisons"]
            if item.get("party_column") == "Q"
        )
        self.assertEqual(first_q["status"], "NOT_COMPARABLE")
        self.assertEqual(
            first["vote_reconciliation"]["status"],
            "MATCH_WITH_OUT_OF_SCOPE",
        )
        self.assertEqual(second_q["status"], "MATCH")
        self.assertEqual(second_q["aggregate_value"], 0)

    def test_blank_cell_in_physically_present_out_of_scope_column_blocks(self):
        raw_15 = (
            "province;municipality;polling;P;Q\n"
            "15;7;1-1-A;5;\n"
            "SUM;;;5;\n"
        )
        with self.assertRaisesRegex(
            ValueError,
            r"PARTY_COLUMN_PRESENT_OUTSIDE_DECLARED_SCOPE",
        ):
            self._read_merged(
                [("province_15", raw_15)],
                scoped_adapter(),
                parties("P", "Q"),
            )

    def test_party_column_missing_inside_declared_scope_blocks(self):
        raw_32 = (
            "province;municipality;polling;P\n"
            "32;1;1-1-A;7\n"
            "SUM;;;7\n"
        )
        with self.assertRaisesRegex(
            ValueError,
            r"PARTY_COLUMN_MISSING_IN_DECLARED_SCOPE",
        ):
            self._read_merged(
                [("province_32", raw_32)],
                scoped_adapter(),
                parties("P", "Q"),
            )

    def test_blank_party_value_inside_declared_scope_still_blocks(self):
        raw_32 = (
            "province;municipality;polling;P;Q\n"
            "32;1;1-1-A;10;\n"
            "SUM;;;10;\n"
        )
        with self.assertRaisesRegex(
            ValueError,
            r"ELECTORAL_VOTES_INVALID.*field=Q",
        ):
            self._read_merged(
                [("province_32", raw_32)],
                scoped_adapter(),
                parties("P", "Q"),
            )

    def test_scope_field_must_exist_and_have_value_in_original_raw(self):
        adapter = scoped_adapter()
        adapter["party_applicability"]["Q"] = {
            "field": "region",
            "equals": ["north"],
            "reason": "fixture",
        }
        missing_field = (
            "province;municipality;polling;P\n"
            "15;7;1-1-A;5\n"
            "SUM;;;5\n"
        )
        with self.assertRaisesRegex(
            ValueError,
            r"PARTY_SCOPE_FIELD_MISSING_IN_RAW",
        ):
            self._read_merged(
                [("missing_scope", missing_field)],
                adapter,
                parties("P", "Q"),
            )

        blank_value = (
            "province;municipality;polling;region;P\n"
            "15;7;1-1-A;;5\n"
            "SUM;;;;5\n"
        )
        with self.assertRaisesRegex(
            ValueError,
            r"PARTY_SCOPE_VALUE_MISSING",
        ):
            self._read_merged(
                [("blank_scope", blank_value)],
                adapter,
                parties("P", "Q"),
            )

    def test_raw_boundary_does_not_invent_business_block_boundary(self):
        adapter = scoped_adapter(require_aggregate=True)
        raw_a = (
            "province;municipality;polling;P;Q\n"
            "32;1;1-1-A;10;20\n"
        )
        raw_b = (
            "province;municipality;polling;P;Q\n"
            "32;2;1-1-A;5;7\n"
            "SUM;;;15;27\n"
        )

        frame, _ = self._read_merged(
            [("raw_a", raw_a), ("raw_b", raw_b)],
            adapter,
            parties("P", "Q"),
        )
        evidence = frame.attrs["recognized_aggregates"]
        self.assertEqual(len(evidence), 1)
        self.assertEqual(evidence[0]["scope"]["polling_station_rows"], 2)
        self.assertEqual(
            evidence[0]["vote_reconciliation"]["status"],
            "MATCH",
        )
        comparisons = {
            item["party_column"]: item
            for item in evidence[0]["vote_reconciliation"][
                "comparisons"
            ]
        }
        self.assertEqual(comparisons["P"]["polling_station_sum"], 15)
        self.assertEqual(comparisons["Q"]["polling_station_sum"], 27)

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
