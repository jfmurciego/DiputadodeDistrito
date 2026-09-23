from __future__ import annotations

import json
import tempfile
import unittest
import zipfile
from pathlib import Path

import yaml

from herramientas.registro_publicaciones_visor import make_candidate
from herramientas.gestor_campana import (
    CONFIRMATION,
    aggregate,
    assert_productive_launch,
    build_matrix,
    sha256,
    validate_manifest,
    validate_portfolio_contract,
    validate_reuse_metadata,
    validate_campaign_summary_for_promotion,
    release_identity,
    publication_matrix,
    package_campaign_gallery,
)

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "configuracion/campanas/campana_cinco_territorios_v1.json"
WORKFLOW = ROOT / ".github/workflows/gestor-campanas.yml"
ORCH = ROOT / ".github/workflows/ejecucion-completa-proyecto.yml"


class CampaignManagerTests(unittest.TestCase):
    def manifest_copy(self) -> dict:
        return json.loads(MANIFEST.read_text(encoding="utf-8"))

    def write_manifest(self, data: dict, root: Path) -> Path:
        path = root / "manifest.json"
        path.write_text(json.dumps(data), encoding="utf-8")
        return path

    def test_manifest_is_strict_five_territory_contract(self):
        data = validate_manifest(MANIFEST)
        self.assertEqual(data["entrypoint"], "gerrychain_50")
        self.assertTrue(data["require_unique_hashes"])
        self.assertEqual(data["candidate_count"], 50)
        self.assertFalse(data["fail_fast"])
        self.assertEqual(data["max_parallel"], 5)
        self.assertFalse(data["retry_failed"])
        for row in data["territories"]:
            reuse = row["reuse"]
            self.assertEqual(reuse["checkpoint_stage"], "SOURCE_PACKAGE")
            self.assertEqual(len(reuse["source_sha"]), 40)
            self.assertEqual(len(reuse["artifact_sha256"]), 64)
            self.assertEqual(len(reuse["m01_artifact_sha256"]), 64)
            self.assertEqual(reuse["expected_certification"], "READY")

    def test_missing_or_wrong_entrypoint_is_rejected(self):
        for value in (None, "generic", "gerrychain"):
            with self.subTest(value=value), tempfile.TemporaryDirectory() as raw:
                data = self.manifest_copy()
                if value is None:
                    data.pop("entrypoint")
                else:
                    data["entrypoint"] = value
                with self.assertRaisesRegex(ValueError, "entrypoint"):
                    validate_manifest(self.write_manifest(data, Path(raw)))

    def test_unique_hashes_disabled_is_rejected(self):
        with tempfile.TemporaryDirectory() as raw:
            data = self.manifest_copy()
            data["require_unique_hashes"] = False
            with self.assertRaisesRegex(ValueError, "require_unique_hashes"):
                validate_manifest(self.write_manifest(data, Path(raw)))

    def test_matrix_propagates_strict_contract_and_fixed_reuse(self):
        source_sha = "a" * 40
        rows = build_matrix(
            MANIFEST,
            source_sha=source_sha,
            campaign_instance="campaign-123-1",
            confirmation=CONFIRMATION,
        )["include"]
        self.assertEqual(len(rows), 5)
        self.assertEqual(len({row["namespace"] for row in rows}), 5)
        self.assertEqual(len({row["artifact_namespace"] for row in rows}), 5)
        digest = sha256(MANIFEST)
        for row in rows:
            self.assertEqual(row["source_sha"], source_sha)
            self.assertEqual(row["manifest_sha256"], digest)
            self.assertEqual(row["entrypoint"], "gerrychain_50")
            self.assertTrue(row["require_unique_hashes"])
            self.assertEqual(row["candidate_count"], 50)
            self.assertGreater(row["reuse_run_id"], 0)
            self.assertEqual(len(row["reuse_artifact_sha256"]), 64)
            self.assertEqual(len(row["reuse_source_sha"]), 40)

    def test_wrong_confirmation_is_rejected(self):
        with self.assertRaises(ValueError):
            build_matrix(
                MANIFEST,
                source_sha="a" * 40,
                campaign_instance="campaign-x",
                confirmation="NO",
            )

    def test_productive_pull_request_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "workflow_dispatch"):
            assert_productive_launch("pull_request", "main", CONFIRMATION)

    def test_checkpoint_digest_or_provenance_mismatch_is_rejected(self):
        reuse = self.manifest_copy()["territories"][0]["reuse"]
        ok = dict(
            run_head_sha=reuse["source_sha"],
            artifact_name=reuse["artifact_name"],
            artifact_digest="sha256:" + reuse["artifact_sha256"],
            m01_artifact_name=reuse["m01_artifact_name"],
            m01_artifact_digest="sha256:" + reuse["m01_artifact_sha256"],
        )
        validate_reuse_metadata(reuse, **ok)
        bad = dict(ok)
        bad["run_head_sha"] = "f" * 40
        with self.assertRaisesRegex(ValueError, "procedencia"):
            validate_reuse_metadata(reuse, **bad)
        bad = dict(ok)
        bad["artifact_digest"] = "sha256:" + "0" * 64
        with self.assertRaisesRegex(ValueError, "Digest"):
            validate_reuse_metadata(reuse, **bad)

    def test_fifty_candidates_with_49_unique_hashes_is_invalid(self):
        candidates = [{"assignment_hash": f"{idx:064x}"} for idx in range(49)]
        candidates.append({"assignment_hash": candidates[0]["assignment_hash"]})
        result = validate_portfolio_contract(
            {"candidate_count": 50, "unique_candidate_count": 49, "candidates": candidates}
        )
        self.assertEqual(result["candidate_count_expected"], 50)
        self.assertEqual(result["candidate_count_valid"], 50)
        self.assertEqual(result["unique_candidate_hash_count"], 49)
        self.assertEqual(result["duplicate_candidate_hash_count"], 1)
        self.assertFalse(result["valid"])

    def test_valid_portfolio_requires_exactly_50_nonmissing_unique_hashes(self):
        candidates = [{"assignment_hash": f"{idx:064x}"} for idx in range(50)]
        result = validate_portfolio_contract(
            {"candidate_count": 50, "unique_candidate_count": 50, "candidates": candidates}
        )
        self.assertTrue(result["valid"])
        self.assertEqual(result["candidate_count_valid"], 50)
        self.assertEqual(result["unique_candidate_hash_count"], 50)
        self.assertEqual(result["missing_candidate_hash_count"], 0)
        self.assertEqual(result["duplicate_candidate_hash_count"], 0)

    def test_aggregate_rejects_any_non_strict_territorial_summary(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            rows = build_matrix(
                MANIFEST,
                source_sha="b" * 40,
                campaign_instance="campaign-x",
                confirmation=CONFIRMATION,
            )["include"]
            for row in rows:
                target = root / row["artifact_namespace"] / "summary"
                target.mkdir(parents=True)
                payload = {
                    **row,
                    "status": "PASS",
                    "candidate_count_expected": 50,
                    "candidate_count_valid": 50,
                    "unique_candidate_hash_count": 50,
                    "missing_candidate_hash_count": 0,
                    "duplicate_candidate_hash_count": 0,
                }
                if row["territory_id"] == "galicia":
                    payload["unique_candidate_hash_count"] = 49
                (target / "campaign_status.json").write_text(
                    json.dumps(payload), encoding="utf-8"
                )
            summary = aggregate(
                MANIFEST, root, campaign_instance="campaign-x", source_sha="b" * 40
            )
            self.assertEqual(summary["status"], "FAIL")
            self.assertEqual(summary["failed_territories"], ["galicia"])

    def test_pull_request_never_schedules_productive_campaign_or_pages(self):
        manager = WORKFLOW.read_text(encoding="utf-8")
        orchestration = ORCH.read_text(encoding="utf-8")
        self.assertIn("if: ${{ github.event_name == 'workflow_dispatch' }}", manager)
        self.assertIn("publish_result: false", manager)
        self.assertIn("E2E sintético de campaña sin ejecutar territorios", manager)
        self.assertIn("github.event_name != 'pull_request'", orchestration)
        self.assertIn("publish=false", orchestration)
        self.assertIn("needs.planificar.outputs.run_prepare_territorial == 'true'", orchestration)
        self.assertIn("needs.planificar.outputs.run_generate == 'true'", orchestration)
        self.assertIn("needs.planificar.outputs.run_incorporate == 'true'", orchestration)
        self.assertNotIn("repository_dispatch", manager)
        self.assertNotIn("gh workflow run", manager)
        self.assertNotIn("rerun", manager.lower())
        self.assertNotIn("sleep ", manager)

    def test_contract_is_propagated_to_runtime_runner(self):
        manager = WORKFLOW.read_text(encoding="utf-8")
        orchestration = ORCH.read_text(encoding="utf-8")
        production = (ROOT / ".github/workflows/produccion-distritos.yml").read_text(encoding="utf-8")
        reusable = (ROOT / ".github/workflows/_reutilizable-generacion-territorial.yml").read_text(encoding="utf-8")
        procedure = (ROOT / "procedimiento.sh").read_text(encoding="utf-8")
        for text in (manager, orchestration, production, reusable):
            self.assertIn("gerrychain_entrypoint", text)
            self.assertIn("require_unique_hashes", text)
        self.assertIn("DDD_GERRYCHAIN_ENTRYPOINT", reusable)
        self.assertIn("DDD_REQUIRE_UNIQUE_HASHES", reusable)
        self.assertIn('DDD_GERRYCHAIN_ENTRYPOINT:-}" == "gerrychain_50"', procedure)
        self.assertIn('DDD_REQUIRE_UNIQUE_HASHES:-}" == "true"', procedure)

    def test_no_implicit_latest_checkpoint_in_campaign_contract(self):
        manager = WORKFLOW.read_text(encoding="utf-8")
        orchestration = ORCH.read_text(encoding="utf-8")
        self.assertIn("reuse_run_id:", manager)
        self.assertIn("reuse_artifact_name:", manager)
        self.assertIn("reuse_artifact_sha256:", manager)
        self.assertIn("reuse_source_sha:", manager)
        self.assertIn('p["execution_mode"]="from_start"', orchestration)
        self.assertIn('p["run_prepare_territorial"]=False', orchestration)
        self.assertIn('p["run_generate"]=True', orchestration)

    def _strict_status(self, row: dict, *, status: str = "PASS") -> dict:
        return {
            **row,
            "status": status,
            "entrypoint": "gerrychain_50",
            "require_unique_hashes": True,
            "candidate_count_expected": 50,
            "candidate_count_valid": 50,
            "unique_candidate_hash_count": 50,
            "missing_candidate_hash_count": 0,
            "duplicate_candidate_hash_count": 0,
        }

    def test_promotion_requires_five_pass_and_one_failure_blocks_it(self):
        rows = build_matrix(
            MANIFEST,
            source_sha="d" * 40,
            campaign_instance="campaign-five",
            confirmation=CONFIRMATION,
        )["include"]
        summary = {
            "status": "PASS",
            "territories": [self._strict_status(row) for row in rows],
        }
        self.assertEqual(len(validate_campaign_summary_for_promotion(summary)), 5)
        summary["territories"][3]["status"] = "FAIL"
        with self.assertRaisesRegex(ValueError, "no promocionable"):
            validate_campaign_summary_for_promotion(summary)

    def test_five_releases_namespaces_and_galleries_are_distinct(self):
        rows = build_matrix(
            MANIFEST,
            source_sha="e" * 40,
            campaign_instance="campaign-five",
            confirmation=CONFIRMATION,
        )["include"]
        releases = []
        for index, row in enumerate(rows, start=1):
            release = release_identity(
                campaign_instance="campaign-five",
                slot=row["slot"],
                territory_id=row["territory_id"],
                asset_sha256=f"{index:064x}",
            )
            release["namespace"] = row["namespace"]
            release["gallery"] = f"{row['territory_id']}/{release['release_tag']}"
            releases.append(release)
        matrix = publication_matrix(releases)["include"]
        self.assertEqual(len(matrix), 5)
        self.assertEqual(len({row["release_tag"] for row in matrix}), 5)
        self.assertEqual(len({row["namespace"] for row in matrix}), 5)
        self.assertEqual(len({row["gallery"] for row in matrix}), 5)

    def test_publishing_one_ensemble_preserves_existing_territories(self):
        def entry(territory: str, ensemble: str, asset_id: int) -> dict:
            return {
                "id": f"ensemble-{territory}-{ensemble}",
                "asset_type": "ensemble_archive",
                "source_type": "release_asset",
                "immutable_location": f"github-release-asset://jfmurciego/DiputadodeDistrito/{asset_id}",
                "repository": "jfmurciego/DiputadodeDistrito",
                "asset_id": asset_id,
                "asset_name": f"{ensemble}.zip",
                "release_tag": ensemble,
                "sha256": f"{asset_id:064x}"[-64:],
                "kind": "ensemble",
                "territory_id": territory,
                "territory_label": territory,
                "ensemble_id": ensemble,
                "candidate_count_expected": 50,
                "candidate_count_valid": 50,
                "publication_status": "PUBLICABLE",
            }

        first = entry("aragon", "ensemble-aragon", 1001)
        second = entry("galicia", "ensemble-galicia", 1002)
        base = {
            "schema": "ddd.viewer-publication-registry/2.0",
            "products": [],
            "ensembles": [first],
        }
        candidate = make_candidate(base, [second])
        self.assertEqual(
            {row["territory_id"] for row in candidate["ensembles"]},
            {"aragon", "galicia"},
        )

    def test_synthetic_gallery_packages_in_existing_ensemble_format(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            bundle = root / "bundle"
            candidate_dir = bundle / "candidates"
            summary_dir = bundle / "summary"
            gallery_dir = bundle / "gallery"
            candidate_dir.mkdir(parents=True)
            summary_dir.mkdir(parents=True)
            gallery_dir.mkdir(parents=True)
            gallery_dir.joinpath("index.html").write_text(
                "<!doctype html><title>synthetic</title>", encoding="utf-8"
            )
            candidates = []
            for index in range(1, 51):
                seed = 1000 + index
                name = f"candidate_{index:03d}_seed_{seed}.geojson.zip"
                geo = {
                    "type": "FeatureCollection",
                    "features": [{
                        "type": "Feature",
                        "properties": {"district_id": "1"},
                        "geometry": {
                            "type": "Polygon",
                            "coordinates": [[[-3.0, 40.0], [-2.9, 40.0], [-2.9, 40.1], [-3.0, 40.0]]],
                        },
                    }],
                }
                with zipfile.ZipFile(candidate_dir / name, "w", zipfile.ZIP_DEFLATED) as archive:
                    archive.writestr("candidate.geojson", json.dumps(geo))
                candidates.append({
                    "index": index,
                    "seed": seed,
                    "assignment_hash": f"{index:064x}",
                    "geojson": name,
                })
            (candidate_dir / "portfolio.json").write_text(
                json.dumps({
                    "candidate_count": 50,
                    "unique_candidate_count": 50,
                    "candidates": candidates,
                }),
                encoding="utf-8",
            )
            (summary_dir / "campaign_status.json").write_text(
                json.dumps({
                    "campaign_instance": "campaign-synthetic",
                    "slot": "01",
                    "territory_id": "aragon",
                    "territory_name": "Aragón",
                    "status": "PASS",
                    "entrypoint": "gerrychain_50",
                    "require_unique_hashes": True,
                    "candidate_count_expected": 50,
                    "candidate_count_valid": 50,
                    "unique_candidate_hash_count": 50,
                    "missing_candidate_hash_count": 0,
                    "duplicate_candidate_hash_count": 0,
                }),
                encoding="utf-8",
            )
            output = root / "ensemble.zip"
            descriptor = package_campaign_gallery(
                bundle,
                output,
                campaign_instance="campaign-synthetic",
                expected_districts=67,
            )
            self.assertTrue(output.is_file())
            self.assertEqual(descriptor["candidate_count_valid"], 50)
            with zipfile.ZipFile(output) as archive:
                names = set(archive.namelist())
                self.assertIn("site/data/summary.json", names)
                self.assertIn("site/index.html", names)
                self.assertEqual(
                    len([name for name in names if name.startswith("site/assets/") and name.endswith(".geojson")]),
                    50,
                )
                summary = json.loads(archive.read("site/data/summary.json"))
                self.assertEqual(summary["territory_id"], "aragon")
                self.assertEqual(summary["candidate_count_valid"], 50)
                self.assertEqual(len(summary["candidates"]), 50)

    def test_publication_jobs_are_after_five_pass_and_skipped_on_pull_request(self):
        manager = WORKFLOW.read_text(encoding="utf-8")
        summary_pos = manager.index("  resumen:")
        promote_pos = manager.index("  promover_galerias:")
        publish_pos = manager.index("  publicar_galerias:")
        self.assertLess(summary_pos, promote_pos)
        self.assertLess(promote_pos, publish_pos)
        self.assertIn("needs: [preparar, resumen]", manager)
        self.assertIn("needs.resumen.result == 'success'", manager)
        self.assertIn("validate_campaign_summary_for_promotion", manager)
        self.assertIn("uses: ./.github/workflows/_reutilizable-publicar-sitio.yml", manager)
        self.assertIn("group: ddd-pages-prod", (ROOT / ".github/workflows/_reutilizable-publicar-sitio.yml").read_text(encoding="utf-8"))
        self.assertNotIn("actions/deploy-pages@", manager)
        self.assertIn("github.event_name == 'workflow_dispatch'", manager)
        self.assertIn("test \"${{ needs.publicar_galerias.result }}\" = success", manager)

    def test_campaign_propagates_accredited_ensemble_sha_to_common_publisher(self):
        manager = WORKFLOW.read_text(encoding="utf-8")
        publisher = (
            ROOT / ".github/workflows/_reutilizable-publicar-sitio.yml"
        ).read_text(encoding="utf-8")
        self.assertIn('expected_sha="$(jq -r .sha256 "$descriptor")"', manager)
        self.assertIn("ensemble_sha256: ${{ matrix.sha256 }}", manager)
        self.assertIn("ensemble_sha256:", publisher)
        self.assertIn("ENSEMBLE_SHA256: ${{ inputs.ensemble_sha256 || '' }}", publisher)

    def test_workflows_parse(self):
        for path in (
            WORKFLOW,
            ORCH,
            ROOT / ".github/workflows/produccion-distritos.yml",
            ROOT / ".github/workflows/incorporacion-resultados-electorales.yml",
            ROOT / ".github/workflows/_reutilizable-generacion-territorial.yml",
            ROOT / ".github/workflows/_reutilizable-incorporacion-electoral.yml",
            ROOT / ".github/workflows/_reutilizable-puerta-validacion.yml",
        ):
            parsed = yaml.load(path.read_text(encoding="utf-8"), Loader=yaml.BaseLoader)
            self.assertIsInstance(parsed, dict, path)


if __name__ == "__main__":
    unittest.main()
