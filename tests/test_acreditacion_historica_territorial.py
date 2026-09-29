from __future__ import annotations

import copy
import hashlib
import json
import shutil
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest import mock

import yaml

import herramientas.acreditar_producto_territorial_historico as historical
from herramientas.acreditar_producto_territorial_historico import (
    HistoricalTerritorialAccreditationBlock,
    derive_historical_territorial_producer,
    materialization_seal_sha256,
    materialize_actions_evidence,
)
from herramientas.resolver_activos_durables import DurableAssetBlock, validate_durable_assets
from herramientas.resolver_ejecucion_completa import build_plan

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "configuracion/catalogo_preparacion.yaml"
EXPECTED = {
    "aragon": {
        "run_id": 36321736287,
        "mode": "missing_durable_manifest",
        "gate_sha": "d044c70efc260c6a1646838fcf07cf95df5b433c1a6dca44dacd6a54ffb0d1ad",
        "audit_sha": "849a15644bae4cd7b3137b2ee96874cbd1a289c8187b3b40709709a28d8af163",
        "gate_artifact_id": 10933030770,
        "gate_archive_sha": "f885e8b325c782badd693fe2174789807fdf678a499ea5ec5c4068c8afca6710",
        "audit_artifact_id": 10933135052,
        "audit_archive_sha": "b8e668142f7801cf5c73ec01cd81811e92151266a86f41ba21f5584e34891c4d",
    },
    "castilla_y_leon": {
        "run_id": 35889595424,
        "mode": "legacy_campaign_namespace_false_rejection",
        "gate_sha": "f375aa583b98902ba68bf7c1bd45b8db8f1104af71962aad801872990f2e81b7",
        "audit_sha": "74dfefb61c81e43515751718321515e2489222d5bb807ba2653159480ffe8b47",
        "gate_artifact_id": 10773961795,
        "gate_archive_sha": "4d130b6a12494adf5fc5bca2a0bb46fdce2e253a561ebc831bfab4e650f60fca",
        "audit_artifact_id": 10772863961,
        "audit_archive_sha": "1a155e24fafe6e948b36673cc68b99099f231297e94f1f36337cfd1614d7af2d",
    },
}


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _catalog_row(territory_id: str) -> tuple[dict, dict]:
    data = yaml.safe_load(CATALOG.read_text(encoding="utf-8")) or {}
    row = next(row for row in data["territories"] if row["territory_id"] == territory_id)
    return row, row["editions"]["2025"]


def _receipt_rel(territory_id: str) -> str:
    _, state = _catalog_row(territory_id)
    return str((state.get("evidence") or {})["territorial_product"])


def _receipt(territory_id: str, root: Path = ROOT) -> dict:
    return json.loads((root / _receipt_rel(territory_id)).read_text(encoding="utf-8"))


def _accreditation_rel(territory_id: str, run_id: int) -> str:
    return f"territorios/{territory_id}/evidencia/acreditaciones_historicas/{run_id}.json"


def _copy_file(root: Path, rel: str) -> None:
    src = ROOT / rel
    dst = root / rel
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)


def _record(root: Path, territory_id: str, run_id: int) -> tuple[Path, dict]:
    path = root / _accreditation_rel(territory_id, run_id)
    return path, json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _reseal_record(path: Path, record: dict) -> None:
    record["materialization"]["seal_sha256"] = materialization_seal_sha256(record)
    _write_json(path, record)


def _sealed_path(root: Path, record: dict, name: str) -> Path:
    return root / record["sealed_evidence"][name]["path"]


def _mutate_sealed_json(
    root: Path,
    territory_id: str,
    run_id: int,
    name: str,
    mutate,
    *,
    update_hash_and_seal: bool,
) -> None:
    record_path, record = _record(root, territory_id, run_id)
    evidence_path = _sealed_path(root, record, name)
    payload = json.loads(evidence_path.read_text(encoding="utf-8"))
    mutate(payload)
    _write_json(evidence_path, payload)
    if update_hash_and_seal:
        record["sealed_evidence"][name]["content_sha256"] = _sha256(evidence_path)
        _reseal_record(record_path, record)


def _copy_case(territory_id: str) -> tuple[Path, tempfile.TemporaryDirectory, str, dict]:
    td = tempfile.TemporaryDirectory()
    root = Path(td.name)
    receipt_rel = _receipt_rel(territory_id)
    asset = _receipt(territory_id)
    run_id = int(asset["run_id"])
    acc_rel = _accreditation_rel(territory_id, run_id)
    _copy_file(root, receipt_rel)
    _copy_file(root, acc_rel)
    record = json.loads((root / acc_rel).read_text(encoding="utf-8"))
    for name in ("gate", "audit"):
        _copy_file(root, record["sealed_evidence"][name]["path"])
    manifest_rel = f"territorios/{territory_id}/evidencia/ejecuciones_completas/{run_id}.json"
    if (ROOT / manifest_rel).is_file():
        _copy_file(root, manifest_rel)
    return root, td, receipt_rel, json.loads((root / receipt_rel).read_text(encoding="utf-8"))


def _planner_catalog(territory_id: str, output: Path) -> tuple[str, dict]:
    row, state = _catalog_row(territory_id)
    row = copy.deepcopy(row)
    state = row["editions"]["2025"]
    state["electoral_source_prepared"] = False
    state["electoral_product_available"] = False
    state["evidence"] = {
        "territorial_product": str((state.get("evidence") or {})["territorial_product"])
    }
    state["last_valid_checkpoint"] = {
        "run_id": int(_receipt(territory_id)["run_id"]),
        "stage": "M06",
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        yaml.safe_dump(
            {
                "schema": "ddd-preparation-catalog/1.1",
                "default_edition": "2025",
                "territories": [row],
            },
            sort_keys=False,
            allow_unicode=True,
        ),
        encoding="utf-8",
    )
    return row["name"], state


class HistoricalTerritorialAccreditationTests(unittest.TestCase):
    def test_real_sealed_evidence_reconstructs_both_accredited_views(self):
        for territory_id, expected in EXPECTED.items():
            with self.subTest(territory=territory_id):
                asset = _receipt(territory_id)
                run_id = expected["run_id"]
                record = json.loads(
                    (ROOT / _accreditation_rel(territory_id, run_id)).read_text(encoding="utf-8")
                )
                gate_path = ROOT / record["sealed_evidence"]["gate"]["path"]
                audit_path = ROOT / record["sealed_evidence"]["audit"]["path"]
                self.assertEqual(expected["gate_sha"], _sha256(gate_path))
                self.assertEqual(expected["audit_sha"], _sha256(audit_path))
                self.assertEqual(
                    expected["gate_artifact_id"],
                    record["sealed_evidence"]["gate"]["source"]["artifact_id"],
                )
                self.assertEqual(
                    expected["gate_archive_sha"],
                    record["sealed_evidence"]["gate"]["source"]["archive_sha256"],
                )
                self.assertEqual(
                    expected["audit_artifact_id"],
                    record["sealed_evidence"]["audit"]["source"]["artifact_id"],
                )
                self.assertEqual(
                    expected["audit_archive_sha"],
                    record["sealed_evidence"]["audit"]["source"]["archive_sha256"],
                )
                self.assertEqual(
                    record["materialization"]["seal_sha256"],
                    materialization_seal_sha256(record),
                )

                result = derive_historical_territorial_producer(
                    root_dir=ROOT,
                    territory_id=territory_id,
                    edition="2025",
                    receipt_rel=_receipt_rel(territory_id),
                    asset=asset,
                )
                self.assertIsNotNone(result)
                self.assertEqual(expected["mode"], result["mode"])
                self.assertEqual(run_id, result["phase"]["run_id"])
                self.assertEqual(asset["artifact_name"], result["phase"]["artifact"])
                self.assertEqual(
                    f"sha256:{asset['artifact_sha256']}",
                    result["phase"]["artifact_digest"],
                )
                self.assertEqual("VALIDADO", result["phase"]["validation_decision"])
                self.assertEqual("PASS_WITH_EXCEPTIONS", result["phase"]["phase_decision"])
                self.assertEqual("PASS_WITH_EXCEPTIONS", result["audit"]["decision"])

        cyl = derive_historical_territorial_producer(
            root_dir=ROOT,
            territory_id="castilla_y_leon",
            edition="2025",
            receipt_rel=_receipt_rel("castilla_y_leon"),
            asset=_receipt("castilla_y_leon"),
        )
        self.assertEqual("BLOQUEADO", cyl["phase"]["historical_validation_decision"])
        self.assertEqual(
            "NOMBRE_ARTEFACTO_NO_COINCIDE_CON_RUN",
            cyl["phase"]["historical_block_reason"],
        )

    def test_planner_reuses_both_real_m06_from_durable_sealed_evidence(self):
        for territory_id in ("aragon", "castilla_y_leon"):
            with self.subTest(territory=territory_id), tempfile.TemporaryDirectory() as td:
                catalog = Path(td) / "catalogo.yaml"
                territory_name, _ = _planner_catalog(territory_id, catalog)
                plan = build_plan(
                    territory=territory_name,
                    edition="2025",
                    execution_mode="reuse",
                    catalog=catalog,
                    root_dir=ROOT,
                    optimization_algorithm="Canónico",
                    force_selected_algorithm=False,
                )
                self.assertFalse(plan["run_generate"])
                receipt = _receipt(territory_id)
                self.assertEqual(
                    int(receipt["run_id"]),
                    plan["existing"]["territorial_product"]["run_id"],
                )
                self.assertEqual(
                    receipt["artifact_name"],
                    plan["existing"]["territorial_product"]["artifact_name"],
                )
                self.assertEqual(
                    receipt["artifact_sha256"],
                    plan["existing"]["territorial_product"]["artifact_sha256"],
                )

    def test_missing_original_gate_or_audit_blocks(self):
        for evidence_name in ("gate", "audit"):
            root, td, receipt_rel, asset = _copy_case("aragon")
            self.addCleanup(td.cleanup)
            _, record = _record(root, "aragon", int(asset["run_id"]))
            _sealed_path(root, record, evidence_name).unlink()
            with self.subTest(evidence=evidence_name), self.assertRaisesRegex(
                HistoricalTerritorialAccreditationBlock,
                "MISSING",
            ):
                derive_historical_territorial_producer(
                    root_dir=root,
                    territory_id="aragon",
                    edition="2025",
                    receipt_rel=receipt_rel,
                    asset=asset,
                )

    def test_altering_one_byte_of_gate_or_audit_blocks(self):
        for evidence_name in ("gate", "audit"):
            root, td, receipt_rel, asset = _copy_case("aragon")
            self.addCleanup(td.cleanup)
            _, record = _record(root, "aragon", int(asset["run_id"]))
            path = _sealed_path(root, record, evidence_name)
            raw = bytearray(path.read_bytes())
            raw[max(0, len(raw) // 2)] ^= 1
            path.write_bytes(bytes(raw))
            with self.subTest(evidence=evidence_name), self.assertRaisesRegex(
                HistoricalTerritorialAccreditationBlock,
                "EVIDENCE_TAMPERED",
            ):
                derive_historical_territorial_producer(
                    root_dir=root,
                    territory_id="aragon",
                    edition="2025",
                    receipt_rel=receipt_rel,
                    asset=asset,
                )

    def test_identity_or_product_digest_substitution_blocks_even_if_resealed(self):
        cases = {
            "run": lambda row: row.update({"run_id": 36321736288}),
            "territory": lambda row: row.update({"territory_id": "otro"}),
            "digest": lambda row: row.update({"artifact_digest": "sha256:" + "0" * 64}),
            "name": lambda row: row.update({"artifact_name": "ddd-state-36321736287-M06-inventado"}),
        }
        for label, mutate in cases.items():
            root, td, receipt_rel, asset = _copy_case("aragon")
            self.addCleanup(td.cleanup)
            _mutate_sealed_json(
                root,
                "aragon",
                int(asset["run_id"]),
                "gate",
                mutate,
                update_hash_and_seal=True,
            )
            with self.subTest(case=label), self.assertRaisesRegex(
                HistoricalTerritorialAccreditationBlock,
                "TRUST_ANCHOR_MISMATCH",
            ):
                derive_historical_territorial_producer(
                    root_dir=root,
                    territory_id="aragon",
                    edition="2025",
                    receipt_rel=receipt_rel,
                    asset=asset,
                )

    def test_audit_substitution_blocks_even_if_resealed(self):
        root, td, receipt_rel, asset = _copy_case("aragon")
        self.addCleanup(td.cleanup)
        _mutate_sealed_json(
            root,
            "aragon",
            int(asset["run_id"]),
            "audit",
            lambda row: row.update(
                {"decision": "PASS", "territorial_certification_status": "PASS"}
            ),
            update_hash_and_seal=True,
        )
        with self.assertRaisesRegex(
            HistoricalTerritorialAccreditationBlock,
            "TRUST_ANCHOR_MISMATCH",
        ):
            derive_historical_territorial_producer(
                root_dir=root,
                territory_id="aragon",
                edition="2025",
                receipt_rel=receipt_rel,
                asset=asset,
            )

    def test_semantically_coherent_original_substitution_still_blocks_when_resealed(self):
        for evidence_name, mutate in (
            ("gate", lambda row: row.update({"materialized_note": "invented-but-semantically-neutral"})),
            ("audit", lambda row: row.update({"materialized_note": "invented-but-semantically-neutral"})),
        ):
            root, td, receipt_rel, asset = _copy_case("aragon")
            self.addCleanup(td.cleanup)
            _mutate_sealed_json(
                root,
                "aragon",
                int(asset["run_id"]),
                evidence_name,
                mutate,
                update_hash_and_seal=True,
            )
            with self.subTest(evidence=evidence_name), self.assertRaisesRegex(
                HistoricalTerritorialAccreditationBlock,
                "TRUST_ANCHOR_MISMATCH",
            ):
                derive_historical_territorial_producer(
                    root_dir=root,
                    territory_id="aragon",
                    edition="2025",
                    receipt_rel=receipt_rel,
                    asset=asset,
                )

    def test_materialization_verifies_actions_archive_identity_and_exact_member_bytes(self):
        source_bytes = (
            ROOT
            / "territorios/aragon/evidencia/acreditaciones_historicas/36321736287/originales/puerta.json"
        ).read_bytes()
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            archive_path = root / "artifact.zip"
            with zipfile.ZipFile(archive_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
                archive.writestr("puerta.json", source_bytes)
            archive_sha = _sha256(archive_path)
            metadata = {
                "workflow_run_id": 36321736287,
                "artifact_id": 9001,
                "name": "ddd-puerta-test",
                "head_sha": "2d4ab0f40e6461f9455155246a3238922179146f",
                "archive_sha256": archive_sha,
            }
            destination = root / "sealed" / "puerta.json"
            sealed = materialize_actions_evidence(
                archive_path=archive_path,
                destination=destination,
                member_name="puerta.json",
                artifact_metadata=metadata,
                run_id=36321736287,
                source_commit="2d4ab0f40e6461f9455155246a3238922179146f",
                expected_artifact_id=9001,
                expected_artifact_name="ddd-puerta-test",
                expected_archive_sha256=archive_sha,
            )
            self.assertEqual(source_bytes, destination.read_bytes())
            self.assertEqual(hashlib.sha256(source_bytes).hexdigest(), sealed["content_sha256"])

            with self.assertRaisesRegex(
                HistoricalTerritorialAccreditationBlock,
                "DIGEST_MISMATCH",
            ):
                materialize_actions_evidence(
                    archive_path=archive_path,
                    destination=root / "bad.json",
                    member_name="puerta.json",
                    artifact_metadata=metadata,
                    run_id=36321736287,
                    source_commit="2d4ab0f40e6461f9455155246a3238922179146f",
                    expected_artifact_id=9001,
                    expected_artifact_name="ddd-puerta-test",
                    expected_archive_sha256="0" * 64,
                )

            with self.assertRaisesRegex(
                HistoricalTerritorialAccreditationBlock,
                "IDENTITY_INVALID",
            ):
                materialize_actions_evidence(
                    archive_path=archive_path,
                    destination=root / "bad-id.json",
                    member_name="puerta.json",
                    artifact_metadata=metadata,
                    run_id=36321736287,
                    source_commit="2d4ab0f40e6461f9455155246a3238922179146f",
                    expected_artifact_id=9002,
                    expected_artifact_name="ddd-puerta-test",
                    expected_archive_sha256=archive_sha,
                )

    def test_actions_expiration_after_materialization_does_not_change_planning(self):
        for territory_id in ("aragon", "castilla_y_leon"):
            with self.subTest(territory=territory_id), mock.patch.object(
                historical,
                "materialize_actions_evidence",
                side_effect=AssertionError("planning must not consult Actions materialization"),
            ):
                result = derive_historical_territorial_producer(
                    root_dir=ROOT,
                    territory_id=territory_id,
                    edition="2025",
                    receipt_rel=_receipt_rel(territory_id),
                    asset=_receipt(territory_id),
                )
                self.assertEqual("VALIDADO", result["phase"]["validation_decision"])

    def _rewrite_cyl_namespace_case(
        self,
        namespace: str,
        *,
        arbitrary_suffix: bool = False,
    ) -> tuple[Path, tempfile.TemporaryDirectory, str, dict]:
        root, td, receipt_rel, asset = _copy_case("castilla_y_leon")
        run_id = int(asset["run_id"])
        canonical = f"ddd-state-{run_id}-M06"
        artifact_name = f"{canonical}-{namespace}"
        if arbitrary_suffix:
            artifact_name += "-extra"
        asset["artifact_name"] = artifact_name
        _write_json(root / receipt_rel, asset)

        record_path, record = _record(root, "castilla_y_leon", run_id)
        record["original_artifact"]["name"] = artifact_name
        record["historical_manifest"]["artifact_namespace"] = namespace
        _reseal_record(record_path, record)

        _mutate_sealed_json(
            root,
            "castilla_y_leon",
            run_id,
            "gate",
            lambda row: row.update({"artifact_name": artifact_name}),
            update_hash_and_seal=True,
        )

        manifest_path = (
            root
            / "territorios/castilla_y_leon/evidencia/ejecuciones_completas"
            / f"{run_id}.json"
        )
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        producer = next(row for row in manifest["phases"] if row["name"].startswith("02 ·"))
        producer["artifact"] = artifact_name
        _write_json(manifest_path, manifest)
        return root, td, receipt_rel, asset

    def test_castilla_y_leon_slot_00_and_arbitrary_suffix_block(self):
        run_id = 35889595424
        for label, namespace, arbitrary in (
            ("slot00", f"campaign-{run_id}-1--00--castilla_y_leon", False),
            ("suffix", f"campaign-{run_id}-1--04--castilla_y_leon", True),
        ):
            root, td, receipt_rel, asset = self._rewrite_cyl_namespace_case(
                namespace,
                arbitrary_suffix=arbitrary,
            )
            self.addCleanup(td.cleanup)
            with self.subTest(case=label), self.assertRaisesRegex(
                HistoricalTerritorialAccreditationBlock,
                "NAMESPACE_INVALID",
            ):
                derive_historical_territorial_producer(
                    root_dir=root,
                    territory_id="castilla_y_leon",
                    edition="2025",
                    receipt_rel=receipt_rel,
                    asset=asset,
                )

    def test_castilla_y_leon_any_other_gate_block_reason_is_rejected(self):
        root, td, receipt_rel, asset = _copy_case("castilla_y_leon")
        self.addCleanup(td.cleanup)
        _mutate_sealed_json(
            root,
            "castilla_y_leon",
            int(asset["run_id"]),
            "gate",
            lambda row: row.update(
                {"reasons": ["DIGEST_NO_COINCIDE_CON_EVIDENCIA_DURABLE"]}
            ),
            update_hash_and_seal=True,
        )
        with self.assertRaisesRegex(
            HistoricalTerritorialAccreditationBlock,
            "TRUST_ANCHOR_MISMATCH",
        ):
            derive_historical_territorial_producer(
                root_dir=root,
                territory_id="castilla_y_leon",
                edition="2025",
                receipt_rel=receipt_rel,
                asset=asset,
            )

    def test_modern_blocked_producer_without_explicit_historical_record_stays_blocked(self):
        root, td, receipt_rel, asset = _copy_case("castilla_y_leon")
        self.addCleanup(td.cleanup)
        (root / _accreditation_rel("castilla_y_leon", int(asset["run_id"]))).unlink()
        _, state = _catalog_row("castilla_y_leon")
        state = copy.deepcopy(state)
        state["electoral_source_prepared"] = False
        state["electoral_product_available"] = False
        state["evidence"] = {"territorial_product": receipt_rel}
        with self.assertRaisesRegex(
            DurableAssetBlock,
            "DURABLE_PRODUCER_PHASE_INVALID",
        ):
            validate_durable_assets(
                root_dir=root,
                state=state,
                territory_id="castilla_y_leon",
                edition="2025",
                territorial_source=state["preparation_evidence"],
                expected_election_id=None,
            )

    def test_planner_blocks_when_materialization_identity_is_contradictory(self):
        territory_id = "aragon"
        root, td, receipt_rel, asset = _copy_case(territory_id)
        self.addCleanup(td.cleanup)
        row, state = _catalog_row(territory_id)
        _copy_file(root, state["contract_path"])
        _copy_file(root, state["territorial_source_declaration"])
        bad_state = copy.deepcopy(state)
        bad_state["electoral_source_prepared"] = False
        bad_state["electoral_product_available"] = False
        bad_state["evidence"] = {"territorial_product": receipt_rel}
        bad_state["last_valid_checkpoint"] = {"run_id": int(asset["run_id"]), "stage": "M06"}
        catalog = root / "configuracion/catalogo_preparacion.yaml"
        catalog.parent.mkdir(parents=True, exist_ok=True)
        catalog.write_text(
            yaml.safe_dump(
                {
                    "schema": "ddd-preparation-catalog/1.1",
                    "default_edition": "2025",
                    "territories": [
                        {
                            "territory_id": territory_id,
                            "name": row["name"],
                            "editions": {"2025": bad_state},
                        }
                    ],
                },
                sort_keys=False,
                allow_unicode=True,
            ),
            encoding="utf-8",
        )
        record_path, record = _record(root, territory_id, int(asset["run_id"]))
        record["original_artifact"]["archive_sha256"] = "0" * 64
        _reseal_record(record_path, record)

        with self.assertRaisesRegex(
            ValueError,
            "CONTINUE_DURABLE_BLOCK.*HISTORICAL",
        ):
            build_plan(
                territory=row["name"],
                edition="2025",
                execution_mode="reuse",
                catalog=catalog,
                root_dir=root,
                optimization_algorithm="Canónico",
                force_selected_algorithm=False,
            )

    def test_materialization_seal_detects_provenance_identity_change(self):
        root, td, receipt_rel, asset = _copy_case("aragon")
        self.addCleanup(td.cleanup)
        record_path, record = _record(root, "aragon", int(asset["run_id"]))
        record["sealed_evidence"]["gate"]["source"]["artifact_id"] += 1
        _write_json(record_path, record)
        with self.assertRaisesRegex(
            HistoricalTerritorialAccreditationBlock,
            "SEAL_INVALID",
        ):
            derive_historical_territorial_producer(
                root_dir=root,
                territory_id="aragon",
                edition="2025",
                receipt_rel=receipt_rel,
                asset=asset,
            )


if __name__ == "__main__":
    unittest.main()
