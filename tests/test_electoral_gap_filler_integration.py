import csv
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from ddd_core.electoral_gap_filler import compose_delimited_sources
from herramientas.preparar_fuente_electoral import prepare


def write_csv(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=["CUSEC_KEY", "party", "votes"], delimiter=";")
        writer.writeheader()
        writer.writerows(rows)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


ELECTION_IDENTITY = {
    "election_id": "demo_2026",
    "election_date": "2026-01-01",
    "election_type": "regional",
    "scope": "demo",
}


def source_decl(source_id, *, eligible=True, source_class="official", identity=None):
    return {
        "id": source_id,
        "result_status": "FINAL",
        "source_class": source_class,
        "granularity": "section_party",
        "promotion_allowed": eligible,
        "identity_evidence": f"evidence://{source_id}",
        "election_identity": identity or ELECTION_IDENTITY,
    }


def governed_universe(root, path, *, identity=None, source_id="independent-universe", derived=None):
    return {
        "path": path.relative_to(root).as_posix(),
        "sha256": sha(path),
        "source_id": source_id,
        "source_class": "independent_electoral_universe",
        "identity_evidence": "official://independent-universe",
        "election_identity": identity or ELECTION_IDENTITY,
        "granularity": "section_party",
        "derived_from_source_ids": list(derived or []),
    }


def composition(root, universe, *, identity=None, **extra):
    ident = dict(identity or ELECTION_IDENTITY)
    value = {
        "primary_source_id": "primary",
        "expected_universe": governed_universe(root, universe, identity=ident),
        **ident,
        "granularity": "section_party",
    }
    value.update(extra)
    return value


class ElectoralGapFillerPreparationIntegrationTests(unittest.TestCase):
    def _basic_files(self, root):
        primary = root / "primary.csv"
        fragment = root / "fragment.csv"
        universe = root / "universe.csv"
        out = root / "composed.csv"
        write_csv(primary, [
            {"CUSEC_KEY": "0100101001", "party": "A", "votes": "10"},
            {"CUSEC_KEY": "0100101001", "party": "B", "votes": "0"},
        ])
        write_csv(fragment, [
            {"CUSEC_KEY": "0100101002", "party": "A", "votes": "7"},
            {"CUSEC_KEY": "0100101002", "party": "B", "votes": "2"},
        ])
        write_csv(universe, [
            {"CUSEC_KEY": "0100101001", "party": "A", "votes": "0"},
            {"CUSEC_KEY": "0100101001", "party": "B", "votes": "0"},
            {"CUSEC_KEY": "0100101002", "party": "A", "votes": "0"},
            {"CUSEC_KEY": "0100101002", "party": "B", "votes": "0"},
        ])
        return primary, fragment, universe, out

    def _compose(self, root, primary, fragment, universe, out, *, declarations=None, comp=None):
        declarations = declarations or [source_decl("primary"), source_decl("fragment")]
        selected = [
            {"id": "primary", "sha256": sha(primary), "artifact_path": primary.name},
            {"id": "fragment", "sha256": sha(fragment), "artifact_path": fragment.name},
        ]
        return compose_delimited_sources(
            [primary, fragment], declarations, selected,
            comp or composition(root, universe),
            out,
            repository_root=root,
        )

    def test_checked_multisource_composition_writes_geographic_product_and_universe_evidence(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            primary, fragment, universe, out = self._basic_files(root)
            info = self._compose(
                root, primary, fragment, universe, out,
                comp=composition(
                    root, universe,
                    official_geographic_candidate_votes=19,
                    official_total_candidate_votes=19,
                ),
            )
            self.assertEqual(info["composition"], "electoral_gap_filler")
            with out.open(encoding="utf-8") as fh:
                rows = list(csv.DictReader(fh, delimiter=";"))
            self.assertEqual(sum(int(r["votes"]) for r in rows), 19)
            report = json.loads(Path(info["evidence_path"]).read_text(encoding="utf-8"))
            self.assertEqual(report["status"], "PASS")
            self.assertEqual(report["added_keys"], 2)
            self.assertEqual(len(report["incorporated_records"]), 2)
            self.assertTrue(report["production_eligible"])
            self.assertEqual(report["expected_universe"]["sha256"], sha(universe))
            self.assertEqual(report["expected_universe"]["source_id"], "independent-universe")
            self.assertEqual(report["expected_universe"]["derived_from_source_ids"], [])

    def test_universe_cannot_be_downloaded_fragment(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            acquire = root / ".ddd-electoral-package-acquire"
            primary = acquire / "primary.csv"
            fragment = acquire / "fragment.csv"
            out = root / "out.csv"
            write_csv(primary, [{"CUSEC_KEY": "001", "party": "A", "votes": "1"}])
            write_csv(fragment, [{"CUSEC_KEY": "002", "party": "A", "votes": "2"}])
            comp = {
                "primary_source_id": "primary",
                "expected_universe": {
                    "path": ".ddd-electoral-package-acquire/fragment.csv",
                    "sha256": sha(fragment),
                    "source_id": "independent-universe",
                    "source_class": "independent_electoral_universe",
                    "identity_evidence": "official://universe",
                    "election_identity": ELECTION_IDENTITY,
                    "granularity": "section_party",
                    "derived_from_source_ids": [],
                },
                **ELECTION_IDENTITY,
                "granularity": "section_party",
            }
            with self.assertRaisesRegex(ValueError, "temporal|\\.ddd"):
                compose_delimited_sources(
                    [primary, fragment],
                    [source_decl("primary"), source_decl("fragment")],
                    [
                        {"id": "primary", "sha256": sha(primary), "artifact_path": primary.name},
                        {"id": "fragment", "sha256": sha(fragment), "artifact_path": fragment.name},
                    ],
                    comp, out, repository_root=root, acquisition_root=acquire,
                )

    def test_universe_absolute_or_missing_governance_is_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            primary, fragment, universe, out = self._basic_files(root)
            selected = [
                {"id": "primary", "sha256": sha(primary), "artifact_path": primary.name},
                {"id": "fragment", "sha256": sha(fragment), "artifact_path": fragment.name},
            ]
            absolute = composition(root, universe)
            absolute["expected_universe"]["path"] = universe.resolve().as_posix()
            with self.assertRaisesRegex(ValueError, "relativo"):
                compose_delimited_sources(
                    [primary, fragment], [source_decl("primary"), source_decl("fragment")],
                    selected, absolute, out, repository_root=root,
                )
            incomplete = composition(root, universe)
            del incomplete["expected_universe"]["sha256"]
            with self.assertRaisesRegex(ValueError, "expected_universe incompleto"):
                compose_delimited_sources(
                    [primary, fragment], [source_decl("primary"), source_decl("fragment")],
                    selected, incomplete, out, repository_root=root,
                )

    def test_universe_path_cannot_escape_repository_with_parent_segments(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            root = base / "repo"
            root.mkdir()
            primary = root / "primary.csv"
            fragment = root / "fragment.csv"
            outside = base / "outside.csv"
            out = root / "out.csv"
            write_csv(primary, [{"CUSEC_KEY": "001", "party": "A", "votes": "1"}])
            write_csv(fragment, [{"CUSEC_KEY": "002", "party": "A", "votes": "2"}])
            write_csv(outside, [
                {"CUSEC_KEY": "001", "party": "A", "votes": "0"},
                {"CUSEC_KEY": "002", "party": "A", "votes": "0"},
            ])
            comp = {
                "primary_source_id": "primary",
                "expected_universe": {
                    "path": "../outside.csv",
                    "sha256": sha(outside),
                    "source_id": "independent-universe",
                    "source_class": "independent_electoral_universe",
                    "identity_evidence": "official://universe",
                    "election_identity": ELECTION_IDENTITY,
                    "granularity": "section_party",
                    "derived_from_source_ids": [],
                },
                **ELECTION_IDENTITY,
                "granularity": "section_party",
            }
            with self.assertRaisesRegex(ValueError, "escapa"):
                compose_delimited_sources(
                    [primary, fragment],
                    [source_decl("primary"), source_decl("fragment")],
                    [
                        {"id": "primary", "sha256": sha(primary), "artifact_path": primary.name},
                        {"id": "fragment", "sha256": sha(fragment), "artifact_path": fragment.name},
                    ],
                    comp, out, repository_root=root,
                )

    def test_universe_cannot_be_same_file_as_vote_source_even_outside_acquisition_dir(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            primary, fragment, _universe, out = self._basic_files(root)
            comp = {
                "primary_source_id": "primary",
                "expected_universe": {
                    "path": "fragment.csv",
                    "sha256": sha(fragment),
                    "source_id": "independent-universe",
                    "source_class": "independent_electoral_universe",
                    "identity_evidence": "official://universe",
                    "election_identity": ELECTION_IDENTITY,
                    "granularity": "section_party",
                    "derived_from_source_ids": [],
                },
                **ELECTION_IDENTITY,
                "granularity": "section_party",
            }
            with self.assertRaisesRegex(ValueError, "fragmentos consumidos"):
                self._compose(root, primary, fragment, fragment, out, comp=comp)

    def test_universe_source_id_or_derivation_cannot_overlap_vote_sources(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            primary, fragment, universe, out = self._basic_files(root)
            for mutation, pattern in (
                ({"source_id": "fragment"}, "source_id"),
                ({"derived_from_source_ids": ["primary"]}, "derivación"),
            ):
                with self.subTest(mutation=mutation):
                    comp = composition(root, universe)
                    comp["expected_universe"].update(mutation)
                    with self.assertRaisesRegex(ValueError, pattern):
                        self._compose(root, primary, fragment, universe, out, comp=comp)

    def test_universe_empty_and_duplicate_are_rejected_in_integration(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            primary = root / "primary.csv"
            fragment = root / "fragment.csv"
            write_csv(primary, [{"CUSEC_KEY": "001", "party": "A", "votes": "1"}])
            write_csv(fragment, [{"CUSEC_KEY": "002", "party": "A", "votes": "2"}])
            for name, rows, pattern in (
                ("empty.csv", [], "vacío"),
                ("duplicate.csv", [
                    {"CUSEC_KEY": "001", "party": "A", "votes": "0"},
                    {"CUSEC_KEY": "001", "party": "A", "votes": "0"},
                ], "duplicadas"),
            ):
                with self.subTest(name=name):
                    universe = root / name
                    write_csv(universe, rows)
                    with self.assertRaisesRegex(ValueError, pattern):
                        self._compose(root, primary, fragment, universe, root / f"{name}.out")

    def test_fragment_valid_party_outside_universe_is_blocked(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            primary = root / "primary.csv"
            fragment = root / "fragment.csv"
            universe = root / "universe.csv"
            out = root / "out.csv"
            write_csv(primary, [{"CUSEC_KEY": "001", "party": "A", "votes": "1"}])
            write_csv(fragment, [{"CUSEC_KEY": "999", "party": "A", "votes": "2"}])
            write_csv(universe, [
                {"CUSEC_KEY": "001", "party": "A", "votes": "0"},
                {"CUSEC_KEY": "002", "party": "A", "votes": "0"},
            ])
            info = self._compose(root, primary, fragment, universe, out)
            self.assertEqual(info["status"], "BLOCK")
            self.assertFalse(out.exists())
            report = json.loads(Path(info["evidence_path"]).read_text(encoding="utf-8"))
            self.assertEqual(report["conflicts"][0]["code"], "OUTSIDE_ACCREDITED_UNIVERSE")

    def test_artifact_bytes_changed_after_selected_sha_are_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            primary, fragment, universe, out = self._basic_files(root)
            selected = [
                {"id": "primary", "sha256": sha(primary), "artifact_path": primary.name},
                {"id": "fragment", "sha256": sha(fragment), "artifact_path": fragment.name},
            ]
            with fragment.open("a", encoding="utf-8") as fh:
                fh.write("\n")
            with self.assertRaisesRegex(ValueError, "SHA-256 de artefacto"):
                compose_delimited_sources(
                    [primary, fragment], [source_decl("primary"), source_decl("fragment")],
                    selected, composition(root, universe), out, repository_root=root,
                )

    def test_conflict_in_one_party_blocks_other_missing_party_in_same_unit(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            primary = root / "primary.csv"
            fragment = root / "fragment.csv"
            universe = root / "universe.csv"
            out = root / "out.csv"
            write_csv(primary, [{"CUSEC_KEY": "001", "party": "A", "votes": "0"}])
            write_csv(fragment, [
                {"CUSEC_KEY": "001", "party": "A", "votes": "5"},
                {"CUSEC_KEY": "001", "party": "B", "votes": "3"},
            ])
            write_csv(universe, [
                {"CUSEC_KEY": "001", "party": "A", "votes": "0"},
                {"CUSEC_KEY": "001", "party": "B", "votes": "0"},
            ])
            info = self._compose(root, primary, fragment, universe, out)
            report = json.loads(Path(info["evidence_path"]).read_text(encoding="utf-8"))
            self.assertEqual(info["status"], "BLOCK")
            self.assertEqual(report["added_keys"], 0)
            self.assertEqual(report["blocked_units"], ["001"])
            self.assertIn({"unit_id": "001", "party": "B"}, report["remaining_missing_keys"])

    def test_missing_promotion_allowance_is_not_production_eligible(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            primary, fragment, universe, out = self._basic_files(root)
            fragment_decl = source_decl("fragment", source_class="third_party_copy")
            fragment_decl.pop("promotion_allowed")
            declarations = [
                source_decl("primary"),
                fragment_decl,
            ]
            info = self._compose(root, primary, fragment, universe, out, declarations=declarations)
            self.assertEqual(info["status"], "BLOCK_ADMISSIBILITY")
            self.assertFalse(info["production_eligible"])
            self.assertFalse(out.exists())

    def test_prepare_rejects_duplicate_source_ids_even_with_distinct_artifacts(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            declaration = root / "decl.yaml"
            declaration.write_text("schema: test\n", encoding="utf-8")
            package = root / "package"
            universe = root / "universe.csv"
            write_csv(universe, [
                {"CUSEC_KEY": "1600101001", "party": "A", "votes": "0"},
                {"CUSEC_KEY": "1600101002", "party": "A", "votes": "0"},
            ])
            european_identity = {
                "election_id": "europeas_2024",
                "election_date": "2024-06-09",
                "election_type": "european",
                "scope": "spain",
            }
            clm_identity = {
                "election_id": "castilla_la_mancha_cortes_2023",
                "election_date": "2023-05-28",
                "election_type": "regional",
                "scope": "castilla_la_mancha",
            }
            declared = {
                "election_id": clm_identity["election_id"],
                "election_date": clm_identity["election_date"],
                "composition": {
                    "kind": "electoral_gap_filler",
                    "primary_source_id": "fragment",
                    "expected_universe": governed_universe(root, universe, identity=clm_identity),
                    "election_type": clm_identity["election_type"],
                    "scope": clm_identity["scope"],
                    "granularity": "section_party",
                },
                "sources": [
                    {
                        **source_decl("fragment", identity=european_identity),
                        "url": "https://official.example/europeas.txt",
                    },
                    {
                        **source_decl("fragment", identity=clm_identity),
                        "url": "https://official.example/clm.csv",
                    },
                ],
            }

            def fake_check(_decl, tmp):
                tmp.mkdir(parents=True, exist_ok=True)
                europeas = tmp / "fragment.txt"
                clm = tmp / "fragment.csv"
                europeas.write_text("CUSEC_KEY;party;votes\n1600101001;A;10\n", encoding="utf-8")
                clm.write_text("CUSEC_KEY;party;votes\n1600101002;A;2\n", encoding="utf-8")
                return {
                    "decision": "READY",
                    "selected_sources": [
                        {
                            "id": "fragment", "artifact_path": "fragment.txt",
                            "sha256": sha(europeas), "bytes": europeas.stat().st_size,
                            "url": "https://official.example/europeas.txt", "publisher": "Official A",
                        },
                        {
                            "id": "fragment", "artifact_path": "fragment.csv",
                            "sha256": sha(clm), "bytes": clm.stat().st_size,
                            "url": "https://official.example/clm.csv", "publisher": "Official B",
                        },
                    ],
                }

            with patch("herramientas.preparar_fuente_electoral.load_declaration", return_value=declared), \
                 patch("herramientas.preparar_fuente_electoral.check_declaration", side_effect=fake_check):
                with self.assertRaisesRegex(ValueError, "source.id duplicado"):
                    prepare(
                        territory_id="castilla_la_mancha",
                        edition="2025",
                        package_out=package,
                        root=root,
                        declaration=declaration,
                    )
            self.assertFalse((package / "data").exists())

    def test_composer_rejects_selected_duplicate_ids_and_declared_selected_mismatch(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            primary, fragment, universe, out = self._basic_files(root)
            declarations = [source_decl("primary"), source_decl("fragment")]
            duplicated_selected = [
                {"id": "same", "sha256": sha(primary), "artifact_path": primary.name},
                {"id": "same", "sha256": sha(fragment), "artifact_path": fragment.name},
            ]
            with self.assertRaisesRegex(ValueError, "selected_sources contiene id duplicado"):
                compose_delimited_sources(
                    [primary, fragment], declarations, duplicated_selected,
                    composition(root, universe), out, repository_root=root,
                )

            mismatched_selected = [
                {"id": "primary", "sha256": sha(primary), "artifact_path": primary.name},
                {"id": "other", "sha256": sha(fragment), "artifact_path": fragment.name},
            ]
            with self.assertRaisesRegex(ValueError, "Asociación fuente/artefacto inconsistente"):
                compose_delimited_sources(
                    [primary, fragment], declarations, mismatched_selected,
                    composition(root, universe), out, repository_root=root,
                )

    def test_integration_blocks_different_election_even_if_outer_composition_is_renamed(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            primary = root / "primary.csv"
            fragment = root / "fragment.csv"
            universe = root / "universe.csv"
            out = root / "composed.csv"
            write_csv(primary, [{"CUSEC_KEY": "1600101001", "party": "A", "votes": "10"}])
            write_csv(fragment, [{"CUSEC_KEY": "1600101002", "party": "A", "votes": "2"}])
            write_csv(universe, [
                {"CUSEC_KEY": "1600101001", "party": "A", "votes": "0"},
                {"CUSEC_KEY": "1600101002", "party": "A", "votes": "0"},
            ])
            primary_identity = {
                "election_id": "castilla_la_mancha_cortes_2023",
                "election_date": "2023-05-28",
                "election_type": "regional",
                "scope": "castilla_la_mancha",
            }
            european_identity = {
                "election_id": "europeas_2024",
                "election_date": "2024-06-09",
                "election_type": "european",
                "scope": "spain",
            }
            declarations = [
                source_decl("primary", identity=primary_identity),
                source_decl("fragment", identity=european_identity),
            ]
            comp = composition(root, universe, identity=primary_identity)
            info = self._compose(
                root, primary, fragment, universe, out,
                declarations=declarations, comp=comp,
            )
            self.assertEqual(info["status"], "BLOCK")
            report = json.loads(Path(info["evidence_path"]).read_text(encoding="utf-8"))
            self.assertEqual(report["conflicts"][0]["code"], "ELECTION_IDENTITY_MISMATCH")

    def test_prepare_persists_block_package_raw_sources_and_evidence(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            declaration = root / "decl.yaml"
            declaration.write_text("schema: test\n", encoding="utf-8")
            universe = root / "universe.csv"
            package = root / "package"
            write_csv(universe, [
                {"CUSEC_KEY": "0100101001", "party": "A", "votes": "0"},
                {"CUSEC_KEY": "0100101002", "party": "A", "votes": "0"},
            ])
            declared = {
                "election_id": "demo_2026",
                "election_date": "2026-01-01",
                "composition": {
                    "kind": "electoral_gap_filler",
                    "primary_source_id": "primary",
                    "expected_universe": governed_universe(root, universe),
                    "election_type": "regional",
                    "granularity": "section_party",
                },
                "sources": [
                    source_decl("primary"),
                    source_decl("fragment", eligible=False, source_class="third_party_copy"),
                ],
            }

            def fake_check(_decl, tmp):
                tmp.mkdir(parents=True, exist_ok=True)
                primary = tmp / "primary.csv"
                fragment = tmp / "fragment.csv"
                write_csv(primary, [{"CUSEC_KEY": "0100101001", "party": "A", "votes": "10"}])
                write_csv(fragment, [{"CUSEC_KEY": "0100101002", "party": "A", "votes": "2"}])
                return {
                    "decision": "READY",
                    "selected_sources": [
                        {"id": "primary", "artifact_path": "primary.csv", "sha256": sha(primary),
                         "bytes": primary.stat().st_size, "url": "official://primary", "publisher": "Official"},
                        {"id": "fragment", "artifact_path": "fragment.csv", "sha256": sha(fragment),
                         "bytes": fragment.stat().st_size, "url": "copy://fragment", "publisher": "Copy"},
                    ],
                }

            with patch("herramientas.preparar_fuente_electoral.load_declaration", return_value=declared), \
                 patch("herramientas.preparar_fuente_electoral.check_declaration", side_effect=fake_check):
                manifest = prepare(
                    territory_id="demo", edition="2026", package_out=package,
                    root=root, declaration=declaration,
                )

            self.assertEqual(manifest["decision"], "BLOCK")
            self.assertEqual(manifest["composition_status"], "BLOCK_ADMISSIBILITY")
            self.assertFalse(manifest["production_eligible"])
            self.assertIsNone(manifest["selected_source"])
            self.assertEqual(len(manifest["raw_sources"]), 2)
            self.assertTrue((package / "raw" / "primary.csv").is_file())
            self.assertTrue((package / "raw" / "fragment.csv").is_file())
            evidence = package / manifest["composition_evidence"]["path"]
            self.assertTrue(evidence.is_file())
            report = json.loads(evidence.read_text(encoding="utf-8"))
            self.assertEqual(report["status"], "BLOCK_ADMISSIBILITY")
            self.assertEqual(report["expected_universe"]["sha256"], sha(universe))
            universe_pkg = package / manifest["composition_evidence"]["expected_universe"]["package_path"]
            self.assertTrue(universe_pkg.is_file())
            self.assertEqual(sha(universe_pkg), sha(universe))
            self.assertFalse((package / "data").exists())

    def test_failed_composition_does_not_materialize_output(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            primary = root / "primary.csv"
            fragment = root / "fragment.csv"
            universe = root / "universe.csv"
            out = root / "composed.csv"
            write_csv(primary, [{"CUSEC_KEY": "0100101001", "party": "A", "votes": "0"}])
            write_csv(fragment, [{"CUSEC_KEY": "0100101001", "party": "A", "votes": "5"}])
            write_csv(universe, [{"CUSEC_KEY": "0100101001", "party": "A", "votes": "0"}])
            info = self._compose(root, primary, fragment, universe, out)
            self.assertEqual(info["status"], "BLOCK")
            self.assertFalse(out.exists())
            report = json.loads(Path(info["evidence_path"]).read_text(encoding="utf-8"))
            self.assertEqual(report["conflicts"][0]["code"], "PRIMARY_VALUE_CONFLICT")


class ElectoralGapFillerWorkflowDurabilityTests(unittest.TestCase):
    def test_workflow_accepts_only_cli_block_code_then_uploads_before_terminal_failure(self):
        root = Path(__file__).resolve().parents[1]
        workflow = (root / ".github/workflows/preparacion-resultados-electorales.yml").read_text(encoding="utf-8")
        generic_literal = 'python -m herramientas.preparar_fuente_electoral "' + '$' + '{args[@]}"'
        generic = workflow.index(generic_literal)
        accepts_block = workflow.index('[[ "$prepare_rc" != 0 && "$prepare_rc" != 2 ]]', generic)
        verifies_manifest = workflow.index('"BLOCK" ]]', accepts_block)
        upload = workflow.index("actions/upload-artifact@", verifies_manifest)
        terminal = workflow.index('Preparación electoral BLOQUEADA', upload)
        self.assertLess(generic, accepts_block)
        self.assertLess(accepts_block, verifies_manifest)
        self.assertLess(verifies_manifest, upload)
        self.assertLess(upload, terminal)


if __name__ == "__main__":
    unittest.main()
