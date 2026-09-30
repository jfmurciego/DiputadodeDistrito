from __future__ import annotations

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
    validate_effective_packages,
)
from herramientas.identidad_fuentes_legislatura import (
    canonical_sha256,
    electoral_identity,
    territorial_identity,
)
from herramientas.registrar_par_fuentes_legislatura import validate_pair_receipt

ROOT = Path(__file__).resolve().parents[1]


def build_pair_fixture(root: Path) -> tuple[Path, dict]:
    (root / "configuracion").mkdir(parents=True, exist_ok=True)
    (root / "evidence").mkdir(parents=True, exist_ok=True)
    temporal = root / "evidence/temporal.json"
    temporal.write_text('{"provider":"demo"}\n', encoding="utf-8")
    import hashlib
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
    elect_id = electoral_identity(
        territory_id="demo",
        edition="2025",
        election_id="demo_2026",
        election_date="2026-05-17",
        artifact_sha256=electoral_artifact_sha,
    )

    terr_receipt_rel = "evidence/territorial.json"
    electoral_receipt_rel = "evidence/electoral.json"
    (root / terr_receipt_rel).write_text(
        json.dumps(
            {
                "schema": "ddd.territorial-source-receipt/1.0",
                "territory_id": "demo",
                "edition": "2025",
                "population_year": 2025,
                "section_year": 2026,
                "run_id": 101,
                "artifact_name": "ddd-source-package-demo-2025-101",
                "artifact_sha256": territorial_artifact_sha,
                "package_sha256": package_sha,
                "territorial_identity_sha256": terr_id["territorial_identity_sha256"],
            }
        ),
        encoding="utf-8",
    )
    (root / electoral_receipt_rel).write_text(
        json.dumps(
            {
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
        ),
        encoding="utf-8",
    )

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
        "electoral_identity_sha256": elect_id["electoral_identity_sha256"],
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
            "run_id": 101,
            "artifact_name": "ddd-source-package-demo-2025-101",
            "artifact_sha256": territorial_artifact_sha,
            "package_sha256": package_sha,
            "receipt_path": terr_receipt_rel,
            "population_year": 2025,
            "section_year": 2026,
            "territorial_identity_sha256": terr_id["territorial_identity_sha256"],
            "compatibility_report_member": "compatibilidad_poblacion_seccionado.json",
            "compatibility_report_sha256": compatibility_report_sha,
            "compatibility_identity_sha256": compatibility_identity,
            "remote_verification": {
                "run_id": 101,
                "artifact_id": 1001,
                "artifact_name": "ddd-source-package-demo-2025-101",
                "artifact_sha256": territorial_artifact_sha,
                "expired": False,
            },
        },
        "electoral_source": {
            "run_id": 202,
            "artifact_name": "ddd-electoral-package-demo-2025-202",
            "artifact_sha256": electoral_artifact_sha,
            "receipt_path": electoral_receipt_rel,
            "election_id": "demo_2026",
            "election_date": "2026-05-17",
            "electoral_identity_sha256": elect_id["electoral_identity_sha256"],
            "remote_verification": {
                "run_id": 202,
                "artifact_id": 2002,
                "artifact_name": "ddd-electoral-package-demo-2025-202",
                "artifact_sha256": electoral_artifact_sha,
                "expired": False,
            },
        },
        "geometric_compatibility_key": terr_id["territorial_identity_sha256"],
        "electoral_compatibility_key": elect_id["electoral_identity_sha256"],
        "territorial_product_reuse": {
            "available": False,
            "geometric_reuse_compatible": False,
            "reason": "NO_TERRITORIAL_PRODUCT",
        },
        "pair_sha256": canonical_sha256(canonical),
    }
    pair_path = root / "evidence/pair.json"
    pair_path.write_text(json.dumps(pair, indent=2) + "\n", encoding="utf-8")
    return pair_path, pair


class PreparedSourcePairExecutionTests(unittest.TestCase):
    def test_final_179_receipt_contract_is_consumed_from_catalog_pointer(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            pair_path, pair = build_pair_fixture(root)
            catalog = {
                "schema": "ddd-preparation-catalog/1.1",
                "default_edition": "2025",
                "territories": [
                    {
                        "territory_id": "demo",
                        "name": "Demo",
                        "editions": {
                            "2025": {
                                "territory_declared": True,
                                "preparation_status": "READY",
                                "contract_path": "demo.yaml",
                                "territorial_source_declaration": "demo_sources.yaml",
                                "electoral_source_declaration": None,
                                "territorial_sources_prepared": True,
                                "territorial_contract_complete": True,
                                "territorial_product_available": False,
                                "electoral_source_prepared": True,
                                "electoral_product_available": False,
                                "territorial_certification": "NOT_CERTIFIED",
                                "production_authorization": "AUTHORIZED",
                                "last_valid_checkpoint": None,
                                "evidence": {
                                    "prepared_source_pair": pair_path.relative_to(root).as_posix()
                                },
                            }
                        },
                    }
                ],
            }
            (root / "configuracion/catalogo_preparacion.yaml").write_text(
                yaml.safe_dump(catalog, sort_keys=False), encoding="utf-8"
            )
            resolved = resolve_pair(root_dir=root, territory="Demo", edition="2025")
            self.assertEqual(resolved["pair"]["pair_sha256"], pair["pair_sha256"])
            self.assertEqual(
                resolved["pair"]["territorial_source"]["territorial_identity_sha256"],
                pair["geometric_compatibility_key"],
            )

    def test_missing_pair_pointer_blocks_instead_of_reconstructing_from_flags(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "configuracion").mkdir()
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
                        "territorial_source_declaration": "demo_sources.yaml",
                        "electoral_source_declaration": None,
                        "territorial_sources_prepared": True,
                        "territorial_contract_complete": True,
                        "territorial_product_available": True,
                        "electoral_source_prepared": True,
                        "electoral_product_available": True,
                        "territorial_certification": "PASS",
                        "production_authorization": "AUTHORIZED",
                        "last_valid_checkpoint": {"run_id": 1, "stage": "M08"},
                        "evidence": {},
                    }},
                }],
            }
            (root / "configuracion/catalogo_preparacion.yaml").write_text(
                yaml.safe_dump(catalog, sort_keys=False), encoding="utf-8"
            )
            with self.assertRaisesRegex(PreparedPairExecutionBlock, "prepared_source_pair"):
                resolve_pair(root_dir=root, territory="Demo", edition="2025")

    def test_effective_bytes_delegate_to_validate_compatibility_package(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            pair_path, pair = build_pair_fixture(root)
            territorial_package = root / "territorial"
            electoral_package = root / "electoral"
            territorial_package.mkdir()
            electoral_package.mkdir()
            params = root / "params.yaml"
            params.write_text("{}\n", encoding="utf-8")
            report = {
                "compatibility_identity_sha256":
                    pair["territorial_source"]["compatibility_identity_sha256"]
            }
            with mock.patch(
                "herramientas.consumir_par_fuentes_legislatura.validate_compatibility_package",
                return_value=(
                    report,
                    pair["territorial_source"]["compatibility_report_sha256"],
                    [],
                ),
            ) as compat, mock.patch(
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
            compat.assert_called_once()
            self.assertTrue(compat.call_args.kwargs["require_ready"])

    def test_effective_compatibility_digest_mismatch_blocks(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            pair_path, pair = build_pair_fixture(root)
            territorial_package = root / "territorial"
            electoral_package = root / "electoral"
            territorial_package.mkdir()
            electoral_package.mkdir()
            params = root / "params.yaml"
            params.write_text("{}\n", encoding="utf-8")
            with mock.patch(
                "herramientas.consumir_par_fuentes_legislatura.validate_compatibility_package",
                return_value=(
                    {"compatibility_identity_sha256": pair["territorial_source"]["compatibility_identity_sha256"]},
                    "9" * 64,
                    [],
                ),
            ):
                with self.assertRaisesRegex(PreparedPairExecutionBlock, "digest del informe"):
                    validate_effective_packages(
                        root_dir=root,
                        pair_path=pair_path,
                        territorial_package=territorial_package,
                        electoral_package=electoral_package,
                        params=params,
                    )

    def test_historical_aragon_and_castilla_y_leon_reuse_only_matching_territorial_identity(self):
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
            pair = {
                "territory_id": territory_id,
                "edition": "2025",
                "territorial_source": {
                    "territorial_identity_sha256": receipt["territorial_identity_sha256"]
                },
            }
            with self.subTest(territory=territory_id, source="compatible"):
                reuse = resolve_geometric_reuse(root_dir=ROOT, pair=pair)
                self.assertTrue(reuse["compatible"])
                self.assertEqual(reuse["product_run_id"], product_run)
                self.assertEqual(
                    reuse["reason"], "SOURCE_IDENTITY_MATCH"
                )

            different = {
                **pair,
                "territorial_source": {"territorial_identity_sha256": "f" * 64},
            }
            with self.subTest(territory=territory_id, source="different"):
                reuse = resolve_geometric_reuse(root_dir=ROOT, pair=different)
                self.assertFalse(reuse["compatible"])
                self.assertEqual(reuse["reason"], "SOURCE_IDENTITY_MISMATCH")

    def test_00_has_no_source_preparation_fallback_and_verifies_bytes_before_calculation(self):
        workflow = (ROOT / ".github/workflows/ejecucion-completa-proyecto.yml").read_text(
            encoding="utf-8"
        )
        self.assertIn("consumir_par_fuentes_legislatura", workflow)
        self.assertIn("Verificar bytes del par preparado", workflow)
        self.assertIn("compatibilidad_poblacion_seccionado.py", workflow)
        self.assertIn('p["run_prepare_territorial"]=False', workflow)
        self.assertIn('p["run_prepare_electoral"]=False', workflow)
        self.assertIn("needs.verificar_par_preparado.result == 'success'", workflow)


if __name__ == "__main__":
    unittest.main()
