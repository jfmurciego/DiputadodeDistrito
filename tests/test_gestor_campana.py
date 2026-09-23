from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

import yaml

from herramientas.gestor_campana import (
    CONFIRMATION,
    aggregate,
    assert_productive_launch,
    build_matrix,
    sha256,
    validate_manifest,
    validate_portfolio_contract,
    validate_reuse_metadata,
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
