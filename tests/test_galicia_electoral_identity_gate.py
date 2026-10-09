from __future__ import annotations

import json
import re
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import yaml

from herramientas.detectar_producto_electoral_huerfano import (
    RecoveryBlocked,
    validate_candidate,
)
from herramientas.resolver_ejecucion_completa import build_plan
from herramientas.validar_puerta_ejecucion import validate_gate


ROOT = Path(__file__).resolve().parents[1]
PARAMS = ROOT / "territorios/galicia/config/galicia_2025.yaml"
CONTRACT = ROOT / "territorios/galicia/config/elecciones/galicia_parlamento_2024.json"
CATALOG = ROOT / "configuracion/catalogo_preparacion.yaml"
REGISTRY = ROOT / "configuracion/registro_electoral.yaml"
ORCHESTRATION = ROOT / ".github/workflows/ejecucion-completa-proyecto.yml"
PASS_CERTIFICATIONS = {"PASS", "PASS_WITH_EXCEPTIONS", "PASS_WITH_GOVERNED_EXCEPTIONS"}


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


class GaliciaElectoralIdentityGateTests(unittest.TestCase):
    def _catalog_and_state(self) -> tuple[dict, dict]:
        catalog = yaml.safe_load(CATALOG.read_text(encoding="utf-8"))
        galicia = next(
            row for row in catalog["territories"] if row["territory_id"] == "galicia"
        )
        return catalog, galicia["editions"]["2025"]

    def _receipt(self, state: dict, kind: str) -> dict:
        rel = (state.get("evidence") or {}).get(kind)
        self.assertTrue(rel, f"falta receipt {kind}")
        path = ROOT / rel
        self.assertTrue(path.is_file(), f"receipt ausente: {path}")
        payload = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(payload["territory_id"], "galicia")
        self.assertEqual(str(payload["edition"]), "2025")
        digest = str(payload["artifact_sha256"]).removeprefix("sha256:").lower()
        self.assertRegex(digest, r"^[0-9a-f]{64}$")
        self.assertTrue(payload["run_id"])
        self.assertTrue(payload["artifact_name"])
        return payload

    def _current_identities(self) -> tuple[dict, dict, dict, dict]:
        _, state = self._catalog_and_state()
        territorial = self._receipt(state, "territorial_product")
        electoral_source = self._receipt(state, "electoral_source")
        electoral_product = self._receipt(state, "electoral_product")

        contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
        registry = yaml.safe_load(REGISTRY.read_text(encoding="utf-8"))
        registered = registry["territories"]["galicia"]

        self.assertEqual(electoral_source["election_id"], registered["election_id"])
        self.assertEqual(contract["election_id"], registered["election_id"])
        self.assertEqual(contract["election_date"], registered["election_date"])

        checkpoint = state.get("last_valid_checkpoint") or {}
        if checkpoint.get("stage") == "M08":
            self.assertEqual(checkpoint.get("run_id"), electoral_product["run_id"])
        if state.get("territorial_product_available"):
            self.assertIn(territorial.get("decision"), PASS_CERTIFICATIONS)

        return state, territorial, electoral_source, electoral_product

    def _gate(self, *, election_id: str, election_date: str) -> dict:
        _, _, electoral_source, _ = self._current_identities()
        contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
        selected_source = {
            "path": "data/resultados_electorales_vigentes.csv",
            "sha256": contract["sources"][0]["sha256"],
            "bytes": 331227,
        }
        with tempfile.TemporaryDirectory() as td:
            package = Path(td)
            manifest = {
                "schema": "ddd-electoral-package/1.0",
                "decision": "ACQUIRE",
                "territory_id": "galicia",
                "edition": "2025",
                "election_id": election_id,
                "election_date": election_date,
                "selected_source": selected_source,
            }
            (package / "manifest.json").write_text(
                json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            with patch(
                "herramientas.validar_paquete_electoral._validate_selected_source",
                return_value=(
                    selected_source,
                    package / selected_source["path"],
                    selected_source["sha256"],
                ),
            ):
                return validate_gate(
                    phase="electoral_source",
                    artifact_root=package,
                    territory_id="galicia",
                    edition="2025",
                    run_id=str(electoral_source["run_id"]),
                    artifact_name=electoral_source["artifact_name"],
                    artifact_digest=electoral_source["artifact_sha256"],
                    expected_digest=electoral_source["artifact_sha256"],
                    params=PARAMS,
                    root_dir=ROOT,
                )

    def _isolated_plan(self, *, certified: bool) -> dict:
        catalog, state = self._catalog_and_state()
        # Copia profunda para que la prueba no altere el catálogo leído.
        catalog = json.loads(json.dumps(catalog))
        galicia = next(
            row for row in catalog["territories"] if row["territory_id"] == "galicia"
        )
        state = galicia["editions"]["2025"]

        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            territorial_run = 91001
            electoral_run = 91002
            territorial = tmp / "territorial_product_2025.json"
            electoral = tmp / "electoral_product_2025.json"

            _write_json(
                territorial,
                {
                    "schema": "ddd.catalog-evidence/1.0",
                    "kind": "territorial_product",
                    "territory_id": "galicia",
                    "edition": "2025",
                    "run_id": territorial_run,
                    "artifact_name": f"ddd-state-{territorial_run}-M06",
                    "artifact_sha256": "6" * 64,
                    "source_commit": "6" * 40,
                    "decision": "PASS_WITH_EXCEPTIONS",
                    "stage": "M06",
                },
            )
            _write_json(
                electoral,
                {
                    "schema": "ddd.catalog-evidence/1.0",
                    "kind": "electoral_product",
                    "territory_id": "galicia",
                    "edition": "2025",
                    "run_id": electoral_run,
                    "artifact_name": f"ddd-state-{electoral_run}-M08",
                    "artifact_sha256": "7" * 64,
                    "source_commit": "7" * 40,
                    "stage": "M08",
                },
            )

            if not certified:
                state.setdefault("evidence", {}).pop("generation_preflight", None)

            state["territorial_product_available"] = certified
            state["territorial_certification"] = (
                "PASS_WITH_EXCEPTIONS" if certified else "NOT_CERTIFIED"
            )
            state["electoral_product_available"] = certified
            state["last_valid_checkpoint"] = {
                "run_id": electoral_run if certified else territorial_run,
                "stage": "M08" if certified else "M06",
            }
            state["evidence"]["territorial_product"] = str(territorial)
            state["evidence"]["electoral_product"] = str(electoral)

            isolated_catalog = tmp / "catalog.yaml"
            isolated_catalog.write_text(
                yaml.safe_dump(catalog, allow_unicode=True, sort_keys=False),
                encoding="utf-8",
            )
            electoral_source_path = ROOT / state["evidence"]["electoral_source"]
            electoral_source = json.loads(electoral_source_path.read_text(encoding="utf-8"))
            durable = {
                "territorial_source": state.get("preparation_evidence") or None,
                "territorial_product": (
                    json.loads(territorial.read_text(encoding="utf-8")) if certified else None
                ),
                "electoral_source": electoral_source,
                "electoral_product": (
                    json.loads(electoral.read_text(encoding="utf-8")) if certified else None
                ),
            }
            with patch(
                "herramientas.resolver_ejecucion_completa.validate_durable_assets",
                return_value=durable,
            ):
                plan = build_plan(
                    territory="Galicia",
                    edition="2025",
                    execution_mode="reuse",
                    catalog=isolated_catalog,
                    root_dir=ROOT,
                    optimization_algorithm="Canónico",
                    force_selected_algorithm=False,
                )
            plan["_fixture"] = {
                "territorial_run": territorial_run,
                "electoral_run": electoral_run,
            }
            return plan

    def test_existing_durable_package_identity_passes_03_to_04_gate(self):
        _, _, electoral_source, _ = self._current_identities()
        contract = json.loads(CONTRACT.read_text(encoding="utf-8"))

        result = self._gate(
            election_id=electoral_source["election_id"],
            election_date=contract["election_date"],
        )

        self.assertEqual(result["decision"], "VALIDADO")
        self.assertEqual(result["phase_decision"], "ACQUIRE")
        self.assertEqual(result["reasons"], [])

    def _assert_active_certification(self, state: dict, receipt: dict) -> None:
        self.assertTrue(state["territorial_product_available"])
        self.assertIn(state["territorial_certification"], PASS_CERTIFICATIONS)
        self.assertIn(receipt["decision"], PASS_CERTIFICATIONS)

    def _assert_manifest_phase_matches_receipt(self, manifest: dict, receipt: dict, name: str) -> None:
        phases = [phase for phase in manifest["phases"] if phase["name"].startswith(name)]
        self.assertEqual(len(phases), 1)
        phase = phases[0]
        self.assertEqual(phase["run_id"], receipt["run_id"])
        self.assertEqual(phase["artifact"], receipt["artifact_name"])
        self.assertEqual(
            str(phase["artifact_digest"]).removeprefix("sha256:"),
            str(receipt["artifact_sha256"]).removeprefix("sha256:"),
        )
        if receipt.get("stage") in {"M06", "M08"}:
            self.assertEqual(manifest["source_sha"], receipt["source_commit"])
            self.assertEqual(phase["validation_decision"], "VALIDADO")
        if receipt.get("decision"):
            self.assertEqual(phase["phase_decision"], receipt["decision"])

    def test_current_catalog_and_receipts_are_identity_and_digest_coherent(self):
        state, territorial, _, electoral_product = self._current_identities()
        self._assert_active_certification(state, territorial)
        checkpoint = state.get("last_valid_checkpoint") or {}
        self.assertIn(checkpoint.get("stage"), {"M06", "M08"})
        expected_run = (
            electoral_product["run_id"]
            if checkpoint.get("stage") == "M08"
            else territorial["run_id"]
        )
        self.assertEqual(checkpoint.get("run_id"), expected_run)

        # El snapshot vivo puede avanzar legítimamente entre M06 y M08.
        # Aquí sólo exigimos receipts e identidad actual coherentes; la relación
        # manifiesto↔receipt se prueba abajo con un escenario controlado.
        self.assertTrue(state.get("territorial_sources_prepared"))
        self.assertTrue(state.get("electoral_source_prepared"))

    def test_manifest_receipt_mismatches_are_detected(self):
        territorial = {
            "territory_id": "galicia",
            "edition": "2025",
            "run_id": 92001,
            "artifact_name": "ddd-state-92001-M06",
            "artifact_sha256": "a" * 64,
            "source_commit": "b" * 40,
            "decision": "PASS",
            "stage": "M06",
        }
        state = {
            "territorial_product_available": True,
            "territorial_certification": "PASS",
        }
        manifest = {
            "territory_id": "galicia",
            "edition": "2025",
            "source_sha": territorial["source_commit"],
            "phases": [
                {
                    "name": "02 · Generación de Distritos Autonómicos",
                    "run_id": territorial["run_id"],
                    "artifact": territorial["artifact_name"],
                    "artifact_digest": territorial["artifact_sha256"],
                    "validation_decision": "VALIDADO",
                    "phase_decision": territorial["decision"],
                }
            ],
        }
        self._assert_manifest_phase_matches_receipt(
            manifest, territorial, "02 · Generación de Distritos"
        )
        for field, bad_value in (
            ("run_id", -1),
            ("artifact_name", "ddd-state-other-M06"),
            ("artifact_sha256", "0" * 64),
            ("source_commit", "0" * 40),
            ("decision", "BLOCKED"),
        ):
            with self.subTest(field=field):
                corrupted = {**territorial, field: bad_value}
                with self.assertRaises(AssertionError):
                    self._assert_manifest_phase_matches_receipt(
                        manifest, corrupted, "02 · Generación de Distritos"
                    )
        self._assert_active_certification(state, territorial)
        for bad_state, bad_receipt in (
            ({**state, "territorial_certification": "NOT_CERTIFIED"}, territorial),
            (state, {**territorial, "decision": "BLOCKED"}),
        ):
            with self.assertRaises(AssertionError):
                self._assert_active_certification(bad_state, bad_receipt)

    def test_isolated_certified_product_reuses_without_generation_or_incorporation(self):
        plan = self._isolated_plan(certified=True)
        self.assertEqual(
            plan["generation_gate"]["route"],
            "certified_product_lineage",
        )
        self.assertFalse(plan["run_prepare_territorial"])
        self.assertFalse(plan["run_generate"])
        self.assertFalse(plan["run_prepare_electoral"])
        self.assertFalse(plan["run_incorporate"])
        self.assertEqual(
            plan["existing"]["territorial_product"]["run_id"],
            plan["_fixture"]["territorial_run"],
        )
        self.assertEqual(
            plan["existing"]["electoral_product"]["run_id"],
            plan["_fixture"]["electoral_run"],
        )

    def test_isolated_not_certified_preparation_requires_generation_and_incorporation(self):
        plan = self._isolated_plan(certified=False)
        self.assertEqual(plan["catalog_state"]["territorial_certification"], "NOT_CERTIFIED")
        self.assertFalse(plan["catalog_state"]["territorial_product_available"])
        self.assertEqual(
            plan["generation_gate"]["route"],
            "planned_pre_m04_accreditation",
        )
        self.assertTrue(plan["pre_m04_accreditation_planned"])
        self.assertTrue(plan["run_prepare_territorial"])
        self.assertTrue(plan["run_generate"])
        self.assertFalse(plan["run_prepare_electoral"])
        self.assertTrue(plan["run_incorporate"])

        orchestration = ORCHESTRATION.read_text(encoding="utf-8")
        self.assertIn(
            "needs.planificar.outputs.run_generate == 'false'",
            orchestration,
        )
        self.assertIn(
            "needs.planificar.outputs.run_prepare_electoral == 'false'",
            orchestration,
        )

    def test_incompatible_historical_m08_is_rejected_by_recovery_validation(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            evidence = root / "evidence"
            run_id = 93001
            current_territorial_run = 92001
            incompatible_territorial_run = 91999
            electoral_source_run = 92501
            source_commit = "c" * 40
            digest = "a" * 64

            registry = root / "configuracion/registro_electoral.yaml"
            registry.parent.mkdir(parents=True)
            registry.write_text(
                yaml.safe_dump(
                    {
                        "schema": "ddd-election-registry/1.0",
                        "edition": "2025",
                        "territories": {
                            "galicia": {
                                "name": "Galicia",
                                "election_id": "galicia_parlamento_2024",
                            }
                        },
                    },
                    sort_keys=False,
                ),
                encoding="utf-8",
            )
            base = root / "territorios/galicia/evidencia/catalogo"
            _write_json(
                base / "territorial_product_2025.json",
                {
                    "territory_id": "galicia",
                    "edition": "2025",
                    "run_id": current_territorial_run,
                    "artifact_name": f"ddd-state-{current_territorial_run}-M06",
                    "artifact_sha256": "1" * 64,
                },
            )
            _write_json(
                base / "electoral_source_2025.json",
                {
                    "territory_id": "galicia",
                    "edition": "2025",
                    "run_id": electoral_source_run,
                    "artifact_name": f"ddd-electoral-package-galicia-2025-{electoral_source_run}",
                    "artifact_sha256": "2" * 64,
                    "election_id": "galicia_parlamento_2024",
                },
            )

            _write_json(
                evidence / "run.json",
                {"id": run_id, "status": "completed", "head_sha": source_commit},
            )
            artifacts = {
                "artifacts": [
                    {
                        "id": 1,
                        "name": f"ddd-state-{run_id}-M08",
                        "expired": False,
                        "digest": f"sha256:{digest}",
                    },
                    {
                        "id": 2,
                        "name": f"ddd-audit-electoral-{run_id}",
                        "expired": False,
                        "digest": "sha256:" + "4" * 64,
                    },
                    {
                        "id": 3,
                        "name": f"ddd-electoral-application-report-{run_id}",
                        "expired": False,
                        "digest": "sha256:" + "5" * 64,
                    },
                ]
            }
            _write_json(evidence / "artifacts.initial.json", artifacts)
            _write_json(evidence / "artifacts.confirm.json", artifacts)
            _write_json(
                evidence / "audit/production_status.json",
                {
                    "decision": "PASS_WITH_EXCEPTIONS",
                    "territory_id": "galicia",
                    "workflow_run_id": run_id,
                    "source_territorial_run_id": incompatible_territorial_run,
                    "electoral_application": True,
                },
            )
            _write_json(
                evidence / "report/report.json",
                {
                    "status": "SUCCESS",
                    "territory_id": "galicia",
                    "workflow_run_id": run_id,
                    "territorial_source_run_id": incompatible_territorial_run,
                    "electoral_package_run_id": electoral_source_run,
                },
            )
            _write_json(
                evidence / "report/validacion_paquete_electoral.json",
                {
                    "decision": "READY_PACKAGE",
                    "territory_id": "galicia",
                    "edition": "2025",
                    "election_id": "galicia_parlamento_2024",
                },
            )

            with self.assertRaisesRegex(
                RecoveryBlocked,
                "RECOVERY_TERRITORIAL_PRODUCT_INCOMPATIBLE",
            ):
                validate_candidate(
                    root_dir=root,
                    territory_id="galicia",
                    edition="2025",
                    candidate={
                        "run_id": run_id,
                        "source_commit": source_commit,
                        "manifest_path": "synthetic/failed.json",
                    },
                    evidence_root=evidence,
                )

    def test_gate_rejects_a_different_galicia_election(self):
        result = self._gate(
            election_id="galicia_parlamento_2020",
            election_date="2020-07-12",
        )

        self.assertEqual(result["decision"], "BLOQUEADO")
        self.assertTrue(
            any(reason.startswith("PAQUETE_ELECTORAL:") for reason in result["reasons"])
        )


if __name__ == "__main__":
    unittest.main()
