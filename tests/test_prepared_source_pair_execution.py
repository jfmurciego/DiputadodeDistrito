from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import yaml

from herramientas.consumir_par_fuentes_legislatura import (
    PreparedPairExecutionBlock,
    resolve_geometric_reuse,
    resolve_pair,
    resolve_territorial_source,
    validate_effective_packages,
    validate_effective_territorial_package,
)
from herramientas.identidad_fuentes_legislatura import (
    canonical_sha256,
    electoral_identity,
    territorial_identity,
)

ROOT = Path(__file__).resolve().parents[1]


def build_source_fixture(
    root: Path,
    *,
    include_pair: bool,
    include_electoral: bool,
) -> tuple[Path, dict | None, dict]:
    (root / "configuracion").mkdir(parents=True, exist_ok=True)
    (root / "evidence").mkdir(parents=True, exist_ok=True)
    temporal = root / "evidence/temporal.json"
    temporal.write_text('{"provider":"demo"}\n', encoding="utf-8")
    temporal_sha = hashlib.sha256(temporal.read_bytes()).hexdigest()

    compatibility_identity = "c" * 64
    compatibility_report_sha = "d" * 64
    package_sha = "a" * 64
    territorial_artifact_sha = "b" * 64
    electoral_artifact_sha = "e" * 64

    terr_id = territorial_identity(
        territory_id="demo",
        edition="2025",
        population_year=2025,
        section_year=2026,
        package_sha256=package_sha,
        compatibility_identity_sha256=compatibility_identity,
    )
    territorial_receipt = {
        "schema": "ddd.territorial-source-receipt/1.0",
        "kind": "territorial_source",
        "territory_id": "demo",
        "edition": "2025",
        "population_year": 2025,
        "section_year": 2026,
        "run_id": 101,
        "artifact_name": "ddd-source-package-demo-2025-101",
        "artifact_sha256": territorial_artifact_sha,
        "package_sha256": package_sha,
        "source_commit": "1" * 40,
        "source_declaration": "evidence/sources.yaml",
        "territorial_identity_sha256": terr_id["territorial_identity_sha256"],
        "compatibility_report_member": "compatibilidad_poblacion_seccionado.json",
        "compatibility_report_sha256": compatibility_report_sha,
        "compatibility_identity_sha256": compatibility_identity,
    }
    territorial_rel = "evidence/territorial.json"
    (root / territorial_rel).write_text(
        json.dumps(territorial_receipt, indent=2) + "\n", encoding="utf-8"
    )

    electoral_rel = "evidence/electoral.json"
    electoral_receipt = None
    electoral_id = None
    if include_electoral:
        electoral_id = electoral_identity(
            territory_id="demo",
            edition="2025",
            election_id="demo_2026",
            election_date="2026-05-17",
            artifact_sha256=electoral_artifact_sha,
        )
        electoral_receipt = {
            "schema": "ddd.catalog-evidence/1.0",
            "kind": "electoral_source",
            "territory_id": "demo",
            "edition": "2025",
            "run_id": 202,
            "artifact_name": "ddd-electoral-package-demo-2025-202",
            "artifact_sha256": electoral_artifact_sha,
            "election_id": "demo_2026",
            "election_date": "2026-05-17",
        }
        (root / electoral_rel).write_text(
            json.dumps(electoral_receipt, indent=2) + "\n", encoding="utf-8"
        )

    pair = None
    pair_rel = None
    if include_pair:
        if not include_electoral:
            raise AssertionError("pair fixture requires electoral receipt")
        canonical = {
            "territory_id": "demo",
            "edition": "2025",
            "election_id": "demo_2026",
            "election_date": "2026-05-17",
            "population_year": 2025,
            "population_reference_date": "2025-01-01",
            "section_year": 2026,
            "section_reference_label": "Secciones_2026",
            "temporal_evidence_sha256": temporal_sha,
            "territorial_identity_sha256": terr_id["territorial_identity_sha256"],
            "territorial_run_id": 101,
            "territorial_artifact_sha256": territorial_artifact_sha,
            "compatibility_report_sha256": compatibility_report_sha,
            "compatibility_identity_sha256": compatibility_identity,
            "electoral_identity_sha256": electoral_id["electoral_identity_sha256"],
            "electoral_run_id": 202,
            "electoral_artifact_sha256": electoral_artifact_sha,
        }
        pair = {
            "schema": "ddd.prepared-source-pair/1.0",
            "territory_id": "demo",
            "territory_name": "Demo",
            "edition": "2025",
            "election": {
                "election_id": "demo_2026",
                "election_date": "2026-05-17",
            },
            "references": {
                "population": {
                    "required_year": 2026,
                    "year": 2025,
                    "reference_date": "2025-01-01",
                },
                "sectioning": {
                    "required_year": 2026,
                    "year": 2026,
                    "reference_label": "Secciones_2026",
                },
            },
            "temporal_evidence": {
                "path": "evidence/temporal.json",
                "sha256": temporal_sha,
                "provider": "demo",
                "checked_at": "2026-09-30",
            },
            "territorial_source": {
                **territorial_receipt,
                "receipt_path": territorial_rel,
                "remote_verification": {
                    "run_id": 101,
                    "artifact_id": 1001,
                    "artifact_name": territorial_receipt["artifact_name"],
                    "artifact_sha256": territorial_artifact_sha,
                    "expired": False,
                },
            },
            "electoral_source": {
                **electoral_receipt,
                "receipt_path": electoral_rel,
                "electoral_identity_sha256": electoral_id["electoral_identity_sha256"],
                "remote_verification": {
                    "run_id": 202,
                    "artifact_id": 2002,
                    "artifact_name": electoral_receipt["artifact_name"],
                    "artifact_sha256": electoral_artifact_sha,
                    "expired": False,
                },
            },
            "geometric_compatibility_key": terr_id["territorial_identity_sha256"],
            "electoral_compatibility_key": electoral_id["electoral_identity_sha256"],
            "territorial_product_reuse": {
                "available": False,
                "geometric_reuse_compatible": False,
                "reason": "NO_TERRITORIAL_PRODUCT",
            },
            "pair_sha256": canonical_sha256(canonical),
        }
        pair_rel = "evidence/pair.json"
        (root / pair_rel).write_text(
            json.dumps(pair, indent=2) + "\n", encoding="utf-8"
        )

    prep = {
        key: territorial_receipt[key]
        for key in (
            "run_id",
            "artifact_name",
            "artifact_sha256",
            "package_sha256",
            "source_commit",
            "population_year",
            "section_year",
            "territorial_identity_sha256",
            "compatibility_report_member",
            "compatibility_report_sha256",
            "compatibility_identity_sha256",
        )
    }
    prep["receipt_path"] = territorial_rel
    evidence = {}
    if pair_rel:
        evidence["prepared_source_pair"] = pair_rel
    if include_electoral:
        evidence["electoral_source"] = electoral_rel

    catalog = {
        "schema": "ddd-preparation-catalog/1.1",
        "default_edition": "2025",
        "territories": [{
            "territory_id": "demo",
            "name": "Demo",
            "editions": {"2025": {
                "territory_declared": True,
                "preparation_status": "READY",
                "contract_path": "demo.yaml",
                "territorial_source_declaration": "evidence/sources.yaml",
                "electoral_source_declaration": None,
                "territorial_sources_prepared": True,
                "territorial_contract_complete": True,
                "territorial_product_available": False,
                "electoral_source_prepared": include_electoral,
                "electoral_product_available": False,
                "territorial_certification": "NOT_CERTIFIED",
                "production_authorization": "AUTHORIZED",
                "last_valid_checkpoint": None,
                "preparation_evidence": prep,
                "evidence": evidence,
            }},
        }],
    }
    (root / "configuracion/catalogo_preparacion.yaml").write_text(
        yaml.safe_dump(catalog, sort_keys=False), encoding="utf-8"
    )
    return root / territorial_rel, pair, territorial_receipt


class EffectiveModeSourceTests(unittest.TestCase):
    def test_territorial_only_valid_source_without_pair_or_electoral_continues(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            receipt_path, pair, receipt = build_source_fixture(
                root, include_pair=False, include_electoral=False
            )
            self.assertIsNone(pair)
            resolved = resolve_territorial_source(
                root_dir=root, territory="Demo", edition="2025"
            )
            self.assertEqual(
                resolved["territorial_source"]["territorial_identity_sha256"],
                receipt["territorial_identity_sha256"],
            )

            package = root / "territorial"
            package.mkdir()
            (package / "manifest.json").write_text(
                json.dumps({"sha256": receipt["package_sha256"]}) + "\n",
                encoding="utf-8",
            )
            with mock.patch(
                "herramientas.consumir_par_fuentes_legislatura.validate_prepared_package",
                return_value=(True, []),
            ), mock.patch(
                "herramientas.consumir_par_fuentes_legislatura.validate_compatibility_package",
                return_value=(
                    {
                        "compatibility_identity_sha256":
                            receipt["compatibility_identity_sha256"]
                    },
                    receipt["compatibility_report_sha256"],
                    [],
                ),
            ):
                validation = validate_effective_territorial_package(
                    root_dir=root,
                    territorial_receipt_path=receipt_path,
                    territorial_package=package,
                )
            self.assertEqual(validation["decision"], "READY")

    def test_territorial_only_invalid_territorial_bytes_blocks(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            receipt_path, _, receipt = build_source_fixture(
                root, include_pair=False, include_electoral=False
            )
            package = root / "territorial"
            package.mkdir()
            (package / "manifest.json").write_text(
                json.dumps({"sha256": receipt["package_sha256"]}) + "\n",
                encoding="utf-8",
            )
            with mock.patch(
                "herramientas.consumir_par_fuentes_legislatura.validate_prepared_package",
                return_value=(False, ["checksum incorrecto"]),
            ):
                with self.assertRaisesRegex(
                    PreparedPairExecutionBlock, "paquete territorial efectivo inválido"
                ):
                    validate_effective_territorial_package(
                        root_dir=root,
                        territorial_receipt_path=receipt_path,
                        territorial_package=package,
                    )

    def test_electoral_without_pair_blocks_even_if_individual_flags_exist(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            build_source_fixture(root, include_pair=False, include_electoral=True)
            with self.assertRaisesRegex(PreparedPairExecutionBlock, "prepared_source_pair"):
                resolve_pair(root_dir=root, territory="Demo", edition="2025")

    def test_electoral_with_pair_and_valid_bytes_continues(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            _, pair, receipt = build_source_fixture(
                root, include_pair=True, include_electoral=True
            )
            resolved = resolve_pair(root_dir=root, territory="Demo", edition="2025")
            pair_path = root / resolved["receipt_path"]
            territorial_package = root / "territorial"
            electoral_package = root / "electoral"
            territorial_package.mkdir()
            electoral_package.mkdir()
            (territorial_package / "manifest.json").write_text(
                json.dumps({"sha256": receipt["package_sha256"]}) + "\n",
                encoding="utf-8",
            )
            params = root / "demo.yaml"
            params.write_text("{}\n", encoding="utf-8")
            with mock.patch(
                "herramientas.consumir_par_fuentes_legislatura.validate_prepared_package",
                return_value=(True, []),
            ), mock.patch(
                "herramientas.consumir_par_fuentes_legislatura.validate_compatibility_package",
                return_value=(
                    {
                        "compatibility_identity_sha256":
                            receipt["compatibility_identity_sha256"]
                    },
                    receipt["compatibility_report_sha256"],
                    [],
                ),
            ), mock.patch(
                "herramientas.consumir_par_fuentes_legislatura.validate_electoral_package",
                return_value={
                    "decision": "READY_PACKAGE",
                    "election_id": pair["election"]["election_id"],
                    "package_sha256": "1" * 64,
                },
            ):
                result = validate_effective_packages(
                    root_dir=root,
                    pair_path=pair_path,
                    territorial_package=territorial_package,
                    electoral_package=electoral_package,
                    params=params,
                )
            self.assertEqual(result["decision"], "READY")
            self.assertEqual(result["pair_sha256"], pair["pair_sha256"])


class GeometricReuseTests(unittest.TestCase):
    def test_historical_aragon_and_castilla_y_leon_reuse_only_matching_identity(self):
        cases = {
            "aragon": (
                "territorios/aragon/evidencia/fuentes_territoriales/2025/"
                "4ec21d6470c2dd934d4785e1a6e906d49a230a82dc7078218f224c91159afce0/"
                "35728613828/receipt.json",
                36321736287,
            ),
            "castilla_y_leon": (
                "territorios/castilla_y_leon/evidencia/fuentes_territoriales/2025/"
                "380dc48849ae078bf6c51144eb98e295be3306d9e66098f82a6b4e61cffa825c/"
                "35610439734/receipt.json",
                35889595424,
            ),
        }
        for territory_id, (receipt_rel, product_run) in cases.items():
            receipt = json.loads((ROOT / receipt_rel).read_text(encoding="utf-8"))
            current = receipt["territorial_identity_sha256"]
            with self.subTest(territory=territory_id, source="compatible"):
                reuse = resolve_geometric_reuse(
                    root_dir=ROOT,
                    territory_id=territory_id,
                    edition="2025",
                    current_identity=current,
                )
                self.assertTrue(reuse["compatible"])
                self.assertEqual(reuse["product_run_id"], product_run)

            with self.subTest(territory=territory_id, source="different"):
                reuse = resolve_geometric_reuse(
                    root_dir=ROOT,
                    territory_id=territory_id,
                    edition="2025",
                    current_identity="f" * 64,
                )
                self.assertFalse(reuse["compatible"])
                self.assertEqual(reuse["reason"], "SOURCE_IDENTITY_MISMATCH")


class OrchestrationModeTests(unittest.TestCase):
    def test_manual_and_campaign_paths_share_mode_sensitive_source_gate(self):
        workflow_path = ROOT / ".github/workflows/ejecucion-completa-proyecto.yml"
        workflow = workflow_path.read_text(encoding="utf-8")
        data = yaml.load(workflow, Loader=yaml.BaseLoader)
        jobs = data["jobs"]
        triggers = data.get("on") or data.get(True)

        self.assertIn("workflow_dispatch", triggers)
        self.assertIn("workflow_call", triggers)
        self.assertIn("publication_mode", triggers["workflow_dispatch"]["inputs"])
        self.assertIn("publication_mode", triggers["workflow_call"]["inputs"])

        source_gate = jobs["verificar_fuentes_preparadas"]
        self.assertEqual(source_gate["needs"], "planificar")
        self.assertNotIn("publication_mode_effective == 'electoral'", source_gate["if"])

        self.assertEqual(
            jobs["puerta_01"]["needs"],
            ["planificar", "verificar_fuentes_preparadas", "preparar_territorial"],
        )
        self.assertEqual(jobs["generar"]["needs"], ["planificar", "preparar_territorial", "puerta_01", "acreditar_generacion"])
        self.assertNotIn("puerta_03", jobs["generar"]["needs"])
        self.assertIn(
            "publication_mode_effective == 'electoral'",
            jobs["puerta_03"]["if"],
        )
        self.assertIn("run_prepare_territorial == 'true'", jobs["preparar_territorial"]["if"])
        self.assertIn("github.event_name != 'pull_request'", jobs["preparar_territorial"]["if"])
        self.assertIn("run_prepare_electoral == 'true'", jobs["preparar_electoral"]["if"])
        self.assertIn("publication_mode_effective == 'electoral'", jobs["preparar_electoral"]["if"])
        self.assertIn("run_prepare_territorial == 'false'", source_gate["if"])

        campaign = yaml.load(
            (ROOT / ".github/workflows/gestor-campanas.yml").read_text(encoding="utf-8"),
            Loader=yaml.BaseLoader,
        )
        self.assertEqual(
            campaign["jobs"]["territorios"]["with"]["publication_mode"],
            "${{ matrix.publication_mode }}",
        )

    def test_mode_is_resolved_before_source_requirement(self):
        workflow = (ROOT / ".github/workflows/ejecucion-completa-proyecto.yml").read_text(
            encoding="utf-8"
        )
        mode_pos = workflow.index("publication_mode.json")
        territorial_pos = workflow.index("resolve-territorial")
        pair_pos = workflow.index("--root-dir . resolve \\")
        self.assertLess(mode_pos, territorial_pos)
        self.assertLess(mode_pos, pair_pos)
        self.assertIn("Verificar bytes de la fuente territorial acreditada", workflow)


if __name__ == "__main__":
    unittest.main()
