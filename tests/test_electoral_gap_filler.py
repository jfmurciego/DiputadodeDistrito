import copy
import unittest

from ddd_core.electoral_gap_filler import compose_records

IDENTITY = dict(election_id="x_2025", election_date="2025-12-21", election_type="regional", scope="x")
SHA = "a" * 64


def meta(source_id="main", status="FINAL", granularity="section_party", eligible=True, **kw):
    x = dict(
        source_id=source_id, granularity=granularity, result_status=status,
        artifact_sha256=SHA, artifact=f"{source_id}.csv", table="data",
        source_class="official", identity_evidence="contract:test",
        production_eligible=eligible, **IDENTITY,
    )
    x.update(kw)
    return x


def row(unit, party, votes, **kw):
    return dict(unit_id=unit, party=party, votes=votes, **kw)


class GapFillTests(unittest.TestCase):
    def test_same_election_fills_only_accredited_gap_and_provenance(self):
        p = [row("01001", "A", 10), row("01001", "B", 0)]
        f = [row("01002", "A", 7, source_row=8), row("01002", "B", 2, source_row=9)]
        out = compose_records(
            p, meta(), [(meta("frag"), f)],
            expected_keys={("01001", "A"), ("01001", "B"), ("01002", "A"), ("01002", "B")},
            allowed_parties={"A", "B"},
        )
        self.assertEqual(out["report"]["status"], "PASS")
        self.assertEqual(out["report"]["added_keys"], 2)
        added = [r for r in out["rows"] if r["unit_id"] == "01002"][0]
        self.assertEqual(added["provenance"]["source_id"], "frag")
        self.assertEqual(added["provenance"]["source_row"], 8)

    def test_clm_2023_plus_europe_2024_is_hard_block(self):
        pmeta = meta(election_id="castilla_la_mancha_cortes_2023", election_date="2023-05-28")
        emeta = meta("eu", election_id="europeas_2024", election_date="2024-06-09")
        out = compose_records([], pmeta, [(emeta, [row("16001", "A", 1)])], expected_keys={("16001", "A")})
        self.assertEqual(out["report"]["status"], "BLOCK")
        self.assertEqual(out["report"]["conflicts"][0]["code"], "ELECTION_IDENTITY_MISMATCH")

    def test_explicit_zero_is_present_and_never_a_gap(self):
        out = compose_records(
            [row("01001", "A", 0)], meta(), [(meta("f"), [row("01001", "A", 5)])],
            expected_keys={("01001", "A")},
        )
        self.assertEqual(out["rows"][0]["votes"], 0)
        self.assertEqual(out["report"]["conflicts"][0]["code"], "PRIMARY_VALUE_CONFLICT")
        self.assertTrue(out["report"]["conflicts"][0]["primary_was_explicit_zero"])

    def test_identical_duplicate_no_double_count_and_contradiction_blocks_unit(self):
        ok = compose_records(
            [row("01001", "A", 3)], meta(), [(meta("f"), [row("01001", "A", 3)])],
            expected_keys={("01001", "A")},
        )
        self.assertEqual(ok["report"]["geographic_candidate_votes"], 3)
        bad = compose_records(
            [], meta(), [(meta("f"), [row("01002", "A", 1), row("01002", "A", 2), row("01002", "B", 4)])],
            expected_keys={("01002", "A"), ("01002", "B")},
        )
        self.assertEqual(bad["report"]["status"], "BLOCK")
        self.assertEqual(bad["report"]["added_keys"], 0)

    def test_polling_section_and_aggregate_overlap_is_blocked(self):
        for granularity in ("polling_station_party", "municipality_party", "constituency_party"):
            with self.subTest(granularity=granularity):
                out = compose_records(
                    [], meta(), [(meta("f", granularity=granularity), [row("x", "A", 1)])],
                    expected_keys={("x", "A")},
                )
                self.assertEqual(out["report"]["conflicts"][0]["code"], "GRANULARITY_MISMATCH")

    def test_primary_outside_independent_universe_blocks_without_deleting_primary(self):
        out = compose_records(
            [row("001", "A", 5), row("999", "A", 2)],
            meta(),
            [],
            expected_keys={("001", "A")},
            allowed_parties={"A"},
        )
        self.assertEqual(out["report"]["status"], "BLOCK")
        self.assertEqual(out["report"]["conflicts"][0]["code"], "PRIMARY_OUTSIDE_ACCREDITED_UNIVERSE")
        self.assertEqual(
            {(r["unit_id"], r["party"], r["votes"]) for r in out["rows"]},
            {("001", "A", 5), ("999", "A", 2)},
        )

    def test_unresolved_party_is_blocked(self):
        out = compose_records(
            [], meta(), [(meta("f"), [row("x", "UNKNOWN", 1)])],
            expected_keys={("x", "UNKNOWN")}, allowed_parties={"A"},
        )
        self.assertEqual(out["report"]["conflicts"][0]["code"], "UNRESOLVED_PARTY")

    def test_provisional_final_mismatch_blocks_unless_explicitly_declared(self):
        args = dict(
            primary_rows=[], primary_source=meta(status="PROVISIONAL"),
            fragments=[(meta("f", status="DEFINITIVE"), [row("x", "A", 1)])],
            expected_keys={("x", "A")},
        )
        blocked = compose_records(**args)
        self.assertEqual(blocked["report"]["conflicts"][0]["code"], "RESULT_STATUS_MISMATCH")
        explicit = compose_records(**args, allowed_status_pairs={("PROVISIONAL", "DEFINITIVE")})
        self.assertEqual(explicit["report"]["status"], "BLOCK_ADMISSIBILITY")
        self.assertFalse(explicit["report"]["production_eligible"])

    def test_incomplete_coverage_and_totals_do_not_claim_complete(self):
        out = compose_records(
            [row("x", "A", 1)], meta(), [], expected_keys={("x", "A"), ("y", "A")},
            official_geographic_candidate_votes=9,
        )
        self.assertEqual(out["report"]["status"], "BLOCK")
        self.assertTrue(out["report"]["remaining_missing_keys"])
        self.assertEqual(out["report"]["reconciliation_errors"][0]["code"], "GEOGRAPHIC_TOTAL_MISMATCH")

    def test_special_external_unit_is_separate_never_geocoded(self):
        p = [row("01001", "A", 10)]
        f = [row("CERA-01", "A", 2, unit_kind="external")]
        out = compose_records(
            p, meta(), [(meta("f"), f)], expected_keys={("01001", "A")},
            official_geographic_candidate_votes=10, official_total_candidate_votes=12,
        )
        self.assertEqual(out["report"]["status"], "PASS")
        self.assertEqual(len(out["rows"]), 1)
        self.assertEqual(out["report"]["special_candidate_votes"], 2)

    def test_non_admissible_secondary_can_be_evaluated_but_not_promoted(self):
        out = compose_records(
            [row("01001", "A", 10)], meta(),
            [(meta("copy", eligible=False, source_class="third_party_copy"), [row("CERA-01", "A", 2, unit_kind="external")])],
            expected_keys={("01001", "A")}, official_total_candidate_votes=12,
        )
        self.assertEqual(out["report"]["status"], "BLOCK_ADMISSIBILITY")
        self.assertEqual(out["report"]["special_candidate_votes"], 2)
        self.assertFalse(out["report"]["production_eligible"])

    def test_caller_provenance_cannot_spoof_checked_source_identity(self):
        fragment = row(
            "002", "A", 2,
            provenance={
                "source_id": "spoof",
                "artifact_sha256": "f" * 64,
                "table": "original-sheet",
                "source_row": 77,
                "source_locator": "mesa-77",
            },
        )
        out = compose_records(
            [], meta(), [(meta("checked"), [fragment])],
            expected_keys={("002", "A")}, allowed_parties={"A"},
        )
        prov = out["report"]["incorporated_records"][0]["provenance"]
        self.assertEqual(prov["source_id"], "checked")
        self.assertEqual(prov["artifact_sha256"], SHA)
        self.assertEqual(prov["table"], "original-sheet")
        self.assertEqual(prov["source_row"], 77)
        self.assertEqual(prov["source_locator"], "mesa-77")
        self.assertEqual(prov["gap_completed"], {"unit_id": "002", "party": "A"})

    def test_determinism_idempotence_and_primary_conservation(self):
        p = [row("001", "A", 1), row("001", "B", 0)]
        f = [row("002", "A", 2), row("002", "B", 3)]
        expected = {("001", "A"), ("001", "B"), ("002", "A"), ("002", "B")}
        original = copy.deepcopy(p)
        a = compose_records(p, meta(), [(meta("f"), f)], expected_keys=expected)
        b = compose_records(p, meta(), [(meta("f"), list(reversed(f)))], expected_keys=expected)
        self.assertEqual(a["report"]["logical_digest"], b["report"]["logical_digest"])
        self.assertEqual(p, original)
        idem = compose_records(a["rows"], meta(), [(meta("f"), f)], expected_keys=expected)
        self.assertEqual(a["report"]["logical_digest"], idem["report"]["logical_digest"])
        fail = compose_records(a["rows"], meta(), [(meta("bad", election_id="wrong"), f)], expected_keys=expected)
        self.assertEqual(
            {(r["unit_id"], r["party"], r["votes"]) for r in a["rows"]},
            {(r["unit_id"], r["party"], r["votes"]) for r in fail["rows"]},
        )


if __name__ == "__main__":
    unittest.main()
