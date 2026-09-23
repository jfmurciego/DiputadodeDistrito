from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

import yaml

from herramientas.gestor_campana import (
    CONFIRMATION,
    aggregate,
    build_matrix,
    sha256,
    validate_manifest,
)

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "configuracion/campanas/campana_cinco_territorios_v1.json"
WORKFLOW = ROOT / ".github/workflows/gestor-campanas.yml"


class CampaignManagerTests(unittest.TestCase):
    def test_manifest_is_exact_versioned_five_territory_campaign(self):
        data = validate_manifest(MANIFEST)
        self.assertEqual(data["optimization_algorithm"], "GerryChain 50")
        self.assertEqual(data["candidate_count"], 50)
        self.assertFalse(data["fail_fast"])
        self.assertEqual(data["max_parallel"], 5)
        self.assertFalse(data["retry_failed"])
        self.assertEqual(
            [
                (row["slot"], row["territory_id"], row["publication_mode"])
                for row in data["territories"]
            ],
            [
                ("01", "aragon", "electoral"),
                ("02", "principado_de_asturias", "electoral"),
                ("03", "galicia", "electoral"),
                ("04", "castilla_y_leon", "electoral"),
                ("05", "extremadura", "territorial_only"),
            ],
        )

    def test_matrix_propagates_identity_and_isolates_namespaces(self):
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
        expected_hash = sha256(MANIFEST)
        for row in rows:
            self.assertEqual(row["source_sha"], source_sha)
            self.assertEqual(row["manifest_sha256"], expected_hash)
            self.assertEqual(row["optimization_algorithm"], "GerryChain 50")
            self.assertEqual(row["candidate_count"], 50)
            self.assertFalse(row["retry_failed"])
            self.assertEqual(
                row["namespace"],
                f"campaign-123-1/{row['slot']}/{row['territory_id']}",
            )

    def test_wrong_confirmation_is_rejected(self):
        with self.assertRaises(ValueError):
            build_matrix(
                MANIFEST,
                source_sha="a" * 40,
                campaign_instance="campaign-x",
                confirmation="NO",
            )

    def test_aggregate_preserves_individual_failure(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
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
                    "status": "FAIL" if row["territory_id"] == "galicia" else "PASS",
                    "candidate_count_expected": 50,
                }
                (target / "campaign_status.json").write_text(
                    json.dumps(payload), encoding="utf-8"
                )
            summary = aggregate(
                MANIFEST,
                root,
                campaign_instance="campaign-x",
                source_sha="b" * 40,
            )
            self.assertEqual(summary["status"], "FAIL")
            self.assertEqual(summary["failed_territories"], ["galicia"])
            self.assertEqual(len(summary["territories"]), 5)

    def test_aggregate_marks_missing_report(self):
        with tempfile.TemporaryDirectory() as td:
            summary = aggregate(
                MANIFEST,
                Path(td),
                campaign_instance="campaign-x",
                source_sha="c" * 40,
            )
            self.assertEqual(summary["status"], "FAIL")
            self.assertEqual(len(summary["failed_territories"]), 5)

    def test_workflow_is_direct_minimal_and_never_runs_territories_on_pr(self):
        text = WORKFLOW.read_text(encoding="utf-8")
        data = yaml.load(text, Loader=yaml.BaseLoader)
        self.assertEqual(data["name"], "Gestor de campañas")
        dispatch = data["on"]["workflow_dispatch"]["inputs"]
        self.assertEqual(set(dispatch), {"manifest", "confirmacion"})
        self.assertIn("fail-fast: false", text)
        self.assertIn("max-parallel: 5", text)
        self.assertIn(
            "uses: ./.github/workflows/ejecucion-completa-proyecto.yml", text
        )
        self.assertIn("if: ${{ github.event_name == 'workflow_dispatch' }}", text)
        self.assertIn(
            "optimization_algorithm: ${{ matrix.optimization_algorithm }}", text
        )
        self.assertIn("source_ref: ${{ matrix.source_sha }}", text)
        self.assertIn("publication_mode: ${{ matrix.publication_mode }}", text)
        self.assertIn("artifact_namespace: ${{ matrix.artifact_namespace }}", text)
        self.assertIn("candidate_count: ${{ matrix.candidate_count }}", text)
        self.assertIn("publish_result: false", text)
        self.assertNotIn("repository_dispatch", text)
        self.assertNotIn("gh workflow run", text)
        self.assertNotIn("rerun", text.lower())

    def test_full_execution_exposes_campaign_contract_and_namespaces_products(self):
        text = (
            ROOT / ".github/workflows/ejecucion-completa-proyecto.yml"
        ).read_text(encoding="utf-8")
        for token in (
            "publication_mode:",
            "artifact_namespace:",
            "campaign_instance:",
            "campaign_slot:",
            "campaign_namespace:",
            "campaign_manifest_sha256:",
            "candidate_count:",
        ):
            self.assertIn(token, text)
        self.assertIn(
            "ddd-campaign-territory-${{ inputs.artifact_namespace }}", text
        )
        self.assertIn("format('ddd-state-{0}-M06{1}'", text)
        self.assertIn("format('ddd-state-{0}-M08{1}'", text)

    def test_namespace_is_propagated_through_existing_reusables(self):
        generation = (
            ROOT / ".github/workflows/_reutilizable-generacion-territorial.yml"
        ).read_text(encoding="utf-8")
        production = (
            ROOT / ".github/workflows/produccion-distritos.yml"
        ).read_text(encoding="utf-8")
        incorporation = (
            ROOT / ".github/workflows/_reutilizable-incorporacion-electoral.yml"
        ).read_text(encoding="utf-8")
        gate = (
            ROOT / ".github/workflows/_reutilizable-puerta-validacion.yml"
        ).read_text(encoding="utf-8")
        self.assertIn("artifact_namespace:", generation)
        self.assertIn("artifact_namespace:", production)
        self.assertIn("artifact_namespace:", incorporation)
        self.assertIn("audit_artifact_name:", gate)
        self.assertIn(
            "La puerta electoral exige acreditación electoral final, nunca certificación territorial",
            gate,
        )

    def test_workflows_parse(self):
        for path in (
            WORKFLOW,
            ROOT / ".github/workflows/ejecucion-completa-proyecto.yml",
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
