"""Version: 1.0.1; candidate durable M06 manifest, source lineage, and M08 isolation.
Previous: legacy/tests/m06-durable-manifest_20261026/test_m06_durable_manifest_pre_source_inputs.py.
"""
from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
import zipfile
from pathlib import Path

import yaml

from herramientas.manifest_generacion_territorial import (
    GenerationManifestError,
    build_manifest,
    manifest_sha256,
    write_idempotent,
)
from herramientas.resolver_activos_durables import (
    DurableAssetBlock,
    validate_durable_assets,
)
from herramientas.promover_catalogo_operacional import promote


def write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, sort_keys=True, indent=2) + "\n", encoding="utf-8")


class DurableM06ManifestTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.contract = self.root / "contratos/demo.yaml"
        self.contract.parent.mkdir(parents=True)
        self.contract.write_text(yaml.safe_dump({"meta": {"territory_id": "demo", "year": 2025}}), encoding="utf-8")
        self.state = self.root / "state"
        (self.state / "sources").mkdir(parents=True)
        (self.state / "sources/manifest.json").write_text('{"source":"verified"}\n', encoding="utf-8")
        write_json(self.state / "run/OPTIMIZATION_EXECUTION.json", {
            "requested_algorithm": "Canónico", "effective_algorithm": "Canónico",
            "fallback": False, "candidate_count": 0, "execution_status": "M05_SUCCESS",
        })
        self.audit = self.root / "audit"
        write_json(self.audit / "production_status.json", {"decision": "PASS"})
        self.index_path = self.root / "artifact-index.json"
        self.roles_path = self.root / "artifact-roles.json"
        entries = []
        for run_id, artifact_id, name in (
            (100, 1001, "ddd-state-100-M06"),
            (100, 1002, "ddd-state-100-M05"),
            (100, 1003, "ddd-audit-100"),
            (100, 1004, "ddd-state-100-M04"),
            (90, 1090, "ddd-source-package-demo-2025-90"),
        ):
            entries.append({"workflow_run_id": run_id, "id": artifact_id, "name": name,
                            "digest": "sha256:" + hashlib.sha256(name.encode()).hexdigest(),
                            "size_in_bytes": 10, "expired": False})
        write_json(self.index_path, {"artifacts": entries})
        write_json(self.roles_path, {
            "m04": {"run_id": 100, "name": "ddd-state-100-M04"},
            "m05": {"run_id": 100, "name": "ddd-state-100-M05"},
            "m06": {"run_id": 100, "name": "ddd-state-100-M06"},
            "audit": {"run_id": 100, "name": "ddd-audit-100"},
            "source_package": {"run_id": 90, "name": "ddd-source-package-demo-2025-90"},
        })

    def tearDown(self):
        self.tmp.cleanup()

    def build(self):
        return build_manifest(
            root_dir=self.root, state_dir=self.state, audit_dir=self.audit,
            artifact_index_path=self.index_path, artifact_roles_path=self.roles_path,
            territory_id="demo", territory_name="Demo", edition="2025",
            contract_path="contratos/demo.yaml", workflow_run_id=100,
            workflow_run_attempt=1, workflow_sha="a" * 40, checkout_sha="b" * 40,
            workflow_name="02 Generación", execution_mode="execute",
            from_stage="M01", to_stage="M06", checkpoint_run_id=None,
            optimization_algorithm="Canónico", gerrychain_entrypoint="",
            require_unique_hashes=False,
        )

    def receipt(self, payload):
        ref = payload["artifacts"]["m06"]
        return {"schema": "ddd.catalog-evidence/1.0", "kind": "territorial_product",
                "territory_id": "demo", "edition": "2025", "run_id": 100,
                "artifact_name": ref["artifact_name"], "artifact_sha256": ref["artifact_sha256"],
                "decision": "PASS", "stage": "M06", "producer_manifest_path": "territorios/demo/evidencia/generaciones_m06/100.json"}

    def source(self):
        return {"run_id": 90, "artifact_name": "ddd-source-package-demo-2025-90",
                "artifact_sha256": hashlib.sha256(b"ddd-source-package-demo-2025-90").hexdigest(),
                "package_sha256": "e" * 64}

    def test_valid_02_manifest_and_recovery_are_idempotent(self):
        payload = self.build()
        self.assertEqual(payload["schema"], "ddd.territorial-generation-manifest/1.0")
        self.assertEqual(payload["identity"]["workflow_run_id"], 100)
        path = self.root / "territorios/demo/evidencia/generaciones_m06/100.json"
        self.assertTrue(write_idempotent(path, payload))
        self.assertFalse(write_idempotent(path, payload))

    def test_checkpoint_source_is_recovered_only_with_matching_durable_package(self):
        from herramientas.manifest_generacion_territorial import resolve_checkpoint_source_package

        source = self.source()
        package_sha = "e" * 64
        (self.state / "sources/manifest.json").write_text(
            json.dumps({"territory_id": "demo", "edition": "2025", "sha256": package_sha}),
            encoding="utf-8",
        )
        catalog = self.root / "configuracion/catalogo_preparacion.yaml"
        catalog.parent.mkdir(parents=True, exist_ok=True)
        catalog.write_text(yaml.safe_dump({"territories": [
            {"territory_id": "demo", "editions": {"2025": {
                "preparation_evidence": {**source, "package_sha256": package_sha},
            }}},
        ]}), encoding="utf-8")
        args = {"root_dir": self.root, "state_dir": self.state,
                "territory_id": "demo", "edition": "2025"}
        recovered = resolve_checkpoint_source_package(**args)
        self.assertEqual(recovered, {
            "run_id": 90,
            "artifact_name": source["artifact_name"],
            "artifact_sha256": source["artifact_sha256"],
        })

        # El nombre del checkpoint no acredita el contenido; nunca reutilizar
        # por semejanza de nombre ni forzar una referencia del catálogo.
        (self.state / "sources/manifest.json").write_text(
            json.dumps({"territory_id": "demo", "edition": "2025", "sha256": "f" * 64}),
            encoding="utf-8",
        )
        with self.assertRaisesRegex(GenerationManifestError, "CHECKPOINT_SOURCE_UNPROVEN"):
            resolve_checkpoint_source_package(**args)

    def test_workflow_records_real_checkout_sha_and_requires_source_lineage(self):
        root = Path(__file__).resolve().parents[1]
        workflow = (root / ".github/workflows/_reutilizable-generacion-territorial.yml").read_text(encoding="utf-8")
        self.assertIn('checkout_sha="$(git rev-parse HEAD)"', workflow)
        self.assertIn('--checkout-sha "$checkout_sha"', workflow)
        self.assertIn('--source-commit "$checkout_sha"', workflow)
        self.assertNotIn('--checkout-sha "$GITHUB_SHA"', workflow)
        self.assertIn('resolve_checkpoint_source_package(', workflow)
        self.assertIn('CHECKPOINT_SOURCE_UNPROVEN', workflow)
        self.assertIn('source_ref inmutable', workflow)
        self.assertIn('"$checkout_sha" == "$expected_checkout"', workflow)

    def test_promotion_links_the_exact_verified_manifest(self):
        payload = self.build()
        manifest_path = self.root / "territorios/demo/evidencia/generaciones_m06/100.json"
        write_idempotent(manifest_path, payload)
        catalog = self.root / "configuracion/catalogo_preparacion.yaml"
        catalog.parent.mkdir(parents=True, exist_ok=True)
        catalog.write_text(yaml.safe_dump({"territories": [{"territory_id": "demo", "name": "Demo",
            "editions": {"2025": {"contract_path": "contratos/demo.yaml", "evidence": {}}}}]}), encoding="utf-8")
        ref = payload["artifacts"]["m06"]
        promote(root_dir=self.root, kind="territorial_product", territory_id="demo", edition="2025",
                run_id=100, artifact_name=ref["artifact_name"], artifact_sha256=ref["artifact_sha256"],
                decision="PASS", producer_manifest_path="territorios/demo/evidencia/generaciones_m06/100.json")
        receipt = json.loads((self.root / "territorios/demo/evidencia/catalogo/territorial_product_2025.json").read_text())
        self.assertEqual(receipt["producer_manifest_path"], "territorios/demo/evidencia/generaciones_m06/100.json")

    def test_changed_artifact_receipt_is_rejected(self):
        from herramientas.resolver_activos_durables import _validate_m06_manifest
        payload = self.build()
        receipt = self.receipt(payload)
        receipt["artifact_sha256"] = "f" * 64
        with self.assertRaisesRegex(DurableAssetBlock, "artefacto M06 distinto"):
            _validate_m06_manifest(root=self.root, payload=payload, territory_id="demo", edition="2025",
                                    run_id=100, receipt=receipt, contract_path="contratos/demo.yaml")

    def test_cross_identity_is_rejected_even_with_recomputed_manifest_hash(self):
        from herramientas.resolver_activos_durables import _validate_m06_manifest
        payload = self.build()
        payload["identity"]["territory_id"] = "otro"
        payload["manifest_sha256"] = manifest_sha256(payload)
        with self.assertRaisesRegex(DurableAssetBlock, "identidad M06 incompleta o cruzada"):
            _validate_m06_manifest(root=self.root, payload=payload, territory_id="demo", edition="2025",
                                    run_id=100, receipt=self.receipt(payload), contract_path="contratos/demo.yaml")

    def test_incomplete_audit_evidence_does_not_build(self):
        (self.audit / "production_status.json").unlink()
        with self.assertRaisesRegex(GenerationManifestError, "production_status.json ausente"):
            self.build()

    def test_gerrychain50_manifest_binds_all_candidates_to_selected_m05_output(self):
        portfolio_dir = self.state / "run/portfolio"
        portfolio_dir.mkdir(parents=True)
        rows = []
        for index in range(1, 51):
            candidate = portfolio_dir / f"candidate_{index:03}.zip"
            with zipfile.ZipFile(candidate, "w", compression=zipfile.ZIP_DEFLATED) as archive:
                archive.writestr("assignment.json", f'{{"candidate":{index}}}')
            assignment_hash = f"{index:064x}"
            rows.append({"index": index, "assignment_hash": assignment_hash,
                         "sha256": hashlib.sha256(candidate.read_bytes()).hexdigest(),
                         "geojson": str(candidate), "selected": index == 1})
        selected_output = self.state / "run/selected_m05.zip"
        selected_output.write_bytes((portfolio_dir / "candidate_001.zip").read_bytes())
        report = {"schema": "ddd.m05-gerrychain-strategy/2.0",
                  "search": {"selected_assignment_hash": rows[0]["assignment_hash"]},
                  "portfolio": {"candidate_count": 50, "unique_candidate_count": 50,
                                "selected_assignment_hash": rows[0]["assignment_hash"], "candidates": rows},
                  "output": {"geojson": str(selected_output), "sha256": hashlib.sha256(selected_output.read_bytes()).hexdigest()}}
        report_path = self.state / "run/portfolio_report.json"
        write_json(report_path, report)
        write_json(self.state / "run/OPTIMIZATION_EXECUTION.json", {
            "requested_algorithm": "GerryChain 50", "effective_algorithm": "GerryChain 50",
            "fallback": False, "candidate_count": 50, "execution_status": "M05_SUCCESS",
        })
        payload = build_manifest(
            root_dir=self.root, state_dir=self.state, audit_dir=self.audit,
            artifact_index_path=self.index_path, artifact_roles_path=self.roles_path,
            territory_id="demo", territory_name="Demo", edition="2025",
            contract_path="contratos/demo.yaml", workflow_run_id=100, workflow_run_attempt=1,
            workflow_sha="a" * 40, checkout_sha="b" * 40, workflow_name="02 Generación",
            execution_mode="execute", from_stage="M01", to_stage="M06", checkpoint_run_id=None,
            optimization_algorithm="GerryChain 50", gerrychain_entrypoint="gerrychain_50",
            require_unique_hashes=True,
        )
        proof = payload["execution"]["portfolio_proof"]
        self.assertEqual(proof["candidate_count"], 50)
        self.assertEqual(proof["unique_assignment_hash_count"], 50)
        self.assertEqual(proof["selected_artifact_sha256"], proof["selected_output_sha256"])

    def test_old_m08_lineage_is_rejected_without_blocking_valid_m06(self):
        payload = self.build()
        m06_manifest = self.root / "territorios/demo/evidencia/generaciones_m06/100.json"
        write_idempotent(m06_manifest, payload)
        m06_receipt_path = self.root / "territorios/demo/evidencia/catalogo/territorial_product_2025.json"
        m06_receipt = self.receipt(payload)
        write_json(m06_receipt_path, m06_receipt)

        m08_receipt_path = self.root / "territorios/demo/evidencia/catalogo/electoral_product_2025.json"
        write_json(m08_receipt_path, {
            "schema": "ddd.catalog-evidence/1.0", "kind": "electoral_product",
            "territory_id": "demo", "edition": "2025", "run_id": 200,
            "artifact_name": "ddd-state-200-M08", "artifact_sha256": "c" * 64, "stage": "M08",
        })
        old_m06 = {"run_id": 99, "artifact": "old-M06", "artifact_digest": "d" * 64,
                   "executed": True, "result": "success", "validation_decision": "VALIDADO",
                   "phase_decision": "PASS"}
        m08 = {"schema": "ddd.full-run-manifest/2.1", "territory_id": "demo", "edition": "2025",
               "workflow_run_id": 200, "phases": [
                   {"name": "01 · Fuente", "run_id": 90, "artifact": "ddd-source-package-demo-2025-90",
                    "artifact_digest": self.source()["artifact_sha256"], "executed": False,
                    "result": "skipped", "validation_decision": "VALIDADO"},
                   {"name": "02 · M06", **old_m06},
                   {"name": "04 · M08", "run_id": 200, "artifact": "ddd-state-200-M08",
                    "artifact_digest": "c" * 64, "executed": True, "result": "success",
                    "validation_decision": "VALIDADO"},
               ]}
        write_json(self.root / "territorios/demo/evidencia/ejecuciones_completas/200.json", m08)
        result = validate_durable_assets(
            root_dir=self.root,
            state={"contract_path": "contratos/demo.yaml", "evidence": {
                "territorial_product": m06_receipt_path.relative_to(self.root).as_posix(),
                "electoral_product": m08_receipt_path.relative_to(self.root).as_posix()},
                "territorial_sources_prepared": True, "preparation_evidence": self.source(),
                "territorial_product_available": True, "territorial_certification": "PASS",
                "electoral_product_available": True},
            territory_id="demo", edition="2025", territorial_source=self.source(), expected_election_id=None,
        )
        self.assertIsNotNone(result["territorial_product"])
        self.assertIsNone(result["electoral_product"])
        self.assertFalse(result["rejected_electoral_product"]["reusable"])

        # Sólo se descarta un M08 válido ligado a otro M06. Un recibo M08
        # corrupto debe seguir bloqueando, aunque M06 territorial sea válido.
        bad_receipt = json.loads(m08_receipt_path.read_text(encoding="utf-8"))
        bad_receipt["artifact_sha256"] = "INVALID_DIGEST"
        write_json(m08_receipt_path, bad_receipt)
        with self.assertRaisesRegex(DurableAssetBlock, "DURABLE_ASSET_DIGEST_INVALID"):
            validate_durable_assets(
                root_dir=self.root,
                state={"contract_path": "contratos/demo.yaml", "evidence": {
                    "territorial_product": m06_receipt_path.relative_to(self.root).as_posix(),
                    "electoral_product": m08_receipt_path.relative_to(self.root).as_posix()},
                    "territorial_sources_prepared": True, "preparation_evidence": self.source(),
                    "territorial_product_available": True, "territorial_certification": "PASS",
                    "electoral_product_available": True},
                territory_id="demo", edition="2025", territorial_source=self.source(),
                expected_election_id=None,
            )

    def test_standalone_m06_rejects_source_package_from_another_run(self):
        payload = self.build()
        manifest_path = self.root / "territorios/demo/evidencia/generaciones_m06/100.json"
        write_idempotent(manifest_path, payload)
        receipt_path = self.root / "territorios/demo/evidencia/catalogo/territorial_product_2025.json"
        write_json(receipt_path, self.receipt(payload))
        common = {"contract_path": "contratos/demo.yaml", "evidence": {
            "territorial_product": receipt_path.relative_to(self.root).as_posix()},
            "territorial_sources_prepared": True, "territorial_product_available": True,
            "territorial_certification": "PASS"}
        validate_durable_assets(root_dir=self.root, state=common, territory_id="demo", edition="2025",
                                territorial_source=self.source(), expected_election_id=None)
        payload["inputs"]["source_package_artifact"]["run_id"] = 91
        payload["manifest_sha256"] = manifest_sha256(payload)
        write_json(manifest_path, payload)
        with self.assertRaisesRegex(DurableAssetBlock, "contradice las entradas M06"):
            validate_durable_assets(root_dir=self.root, state=common, territory_id="demo", edition="2025",
                                    territorial_source=self.source(), expected_election_id=None)


if __name__ == "__main__":
    unittest.main()
