from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import yaml

from herramientas.resolver_adquisicion_electoral_especial import resolve
from herramientas import preparar_snapshot_electoral_oficial as special
from herramientas import adquirir_siel_andalucia_2026 as siel
from herramientas.validar_paquete_electoral import validate_package

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "preparacion-resultados-electorales.yml"
REGISTRY = ROOT / "configuracion" / "adquisiciones_electorales_especiales.yaml"

SECTIONS_SHA = "6ef7fd1efb04ea3623b401b6fd73c1ed3895005384306c75b5953a97ddafa70e"
CERA_SHA = "1a8de1e3e43623f677f5142fc300d70692837b30ffc5aa65e57ece3f6e7e9e7c"


class OfficialSnapshotEntrypointTests(unittest.TestCase):
    def test_direct_script_entrypoint_can_import_repository_package(self):
        proc = subprocess.run(
            [
                sys.executable,
                "herramientas/preparar_snapshot_electoral_oficial.py",
                "--help",
            ],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertNotIn("ModuleNotFoundError", proc.stderr)


class SpecialElectoralAcquisitionContractTests(unittest.TestCase):
    def test_andalucia_resolves_to_reusable_official_snapshot_strategy(self):
        row = resolve(
            root_dir=ROOT,
            election_id="andalucia_parlamento_2026",
            territory_id="andalucia",
            election_date="2026-05-17",
        )
        self.assertIsNotNone(row)
        self.assertEqual(row["kind"], "official_api_snapshot")
        self.assertEqual(row["provider"], "siel")
        self.assertEqual(row["source_status"], "VERIFIED_OFFICIAL_FINAL")
        self.assertTrue(row["promotion_allowed"])
        cfg = row["provider_config"]
        self.assertEqual(cfg["expected_sections"], 6044)
        self.assertEqual(cfg["official_candidate_votes"], 4157539)
        self.assertEqual(cfg["expected_snapshot"]["sections_sha256"], SECTIONS_SHA)
        self.assertEqual(cfg["expected_snapshot"]["cera_sha256"], CERA_SHA)
        self.assertEqual(cfg["locator"]["sha256"], siel.SECTION_LOCATOR_SHA256)

    def test_unknown_election_has_no_special_strategy(self):
        self.assertIsNone(resolve(
            root_dir=ROOT,
            election_id="fixture_unknown",
            territory_id="fixture",
            election_date="2025-01-01",
        ))

    def test_registry_is_not_a_workflow_specific_andalucia_switch(self):
        data = yaml.safe_load(REGISTRY.read_text(encoding="utf-8"))
        self.assertEqual(data["schema"], "ddd-special-electoral-acquisitions/1.0")
        self.assertIn("andalucia_parlamento_2026", data["acquisitions"])
        text = WORKFLOW.read_text(encoding="utf-8")
        self.assertNotIn('ELECTION_ID" == "andalucia_parlamento_2026', text)
        self.assertNotIn("if: andalucia", text.lower())


class CommonWorkflowRoutingTests(unittest.TestCase):
    def test_common_03_resolves_official_snapshot_before_fallbacks(self):
        text = WORKFLOW.read_text(encoding="utf-8")
        special_pos = text.index("resolver_adquisicion_electoral_especial.py")
        eleccionesdb_pos = text.index("from herramientas.adaptador_eleccionesdb import ELECTIONS")
        minsait_pos = text.index("resolver_contrato_minsait_provisional.py")
        self.assertLess(special_pos, eleccionesdb_pos)
        self.assertLess(eleccionesdb_pos, minsait_pos)
        self.assertIn("adapter=official_snapshot", text)
        self.assertIn("preparar_snapshot_electoral_oficial.py", text)

    def test_common_validation_precedes_policy_upload_and_registration(self):
        text = WORKFLOW.read_text(encoding="utf-8")
        prepare_pos = text.index("Preparar paquete electoral con contrato común")
        validate_pos = text.index("Validar paquete consumible antes de promoción")
        policy_pos = text.index("Leer política de promoción del paquete")
        upload_pos = text.index("id: upload", validate_pos)
        register_pos = text.index("Registrar resultados electorales preparados")
        self.assertLess(prepare_pos, validate_pos)
        self.assertLess(validate_pos, policy_pos)
        self.assertLess(policy_pos, upload_pos)
        self.assertLess(upload_pos, register_pos)
        self.assertIn('"$decision" == "REUSE" || "$decision" == "ACQUIRE"', text)
        self.assertIn("validar_paquete_electoral.py", text)
        self.assertIn("READY_PACKAGE", text)
        self.assertIn("se conserva para evidencia y bloqueo durable", text)

    def test_common_03_preserves_checkpoint_and_snapshot_as_artifacts(self):
        data = yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))
        steps = data["jobs"]["electorales"]["steps"]
        names = [str(step.get("name") or "") for step in steps if isinstance(step, dict)]
        self.assertIn("Adquirir snapshot oficial especializado", names)
        self.assertIn("Conservar checkpoint de adquisición oficial si existe", names)
        self.assertIn("Conservar snapshot oficial adquirido", names)
        checkpoint = next(s for s in steps if s.get("name") == "Conservar checkpoint de adquisición oficial si existe")
        self.assertIn("always()", checkpoint["if"])
        self.assertEqual(checkpoint["with"]["retention-days"], 7)
        snapshot = next(s for s in steps if s.get("name") == "Conservar snapshot oficial adquirido")
        self.assertEqual(snapshot["with"]["retention-days"], 90)


class CommonPackageValidationRegressionTests(unittest.TestCase):
    def test_special_package_with_correct_identity_but_broken_source_hash_is_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            package = root / "package"
            (package / "data").mkdir(parents=True)
            source = package / "data" / "resultados_electorales_normalizados.csv"
            source.write_text("CUSEC_KEY;party;votes\n4100101001;A;10\n", encoding="utf-8")
            manifest = {
                "schema": "ddd-electoral-package/1.0",
                "decision": "ACQUIRE",
                "territory_id": "andalucia",
                "edition": "2025",
                "election_id": "andalucia_parlamento_2026",
                "election_date": "2026-05-17",
                "source_status": "VERIFIED_OFFICIAL_FINAL",
                "production_eligible": True,
                "acquisition": {
                    "kind": "official_api_snapshot",
                    "provider": "siel",
                },
                "selected_source": {
                    "path": "data/resultados_electorales_normalizados.csv",
                    "sha256": "0" * 64,
                    "bytes": source.stat().st_size,
                },
            }
            (package / "manifest.json").write_text(
                json.dumps(manifest, ensure_ascii=False),
                encoding="utf-8",
            )
            params = root / "params.yaml"
            params.write_text(
                yaml.safe_dump({
                    "meta": {"territory_id": "andalucia", "year": 2025},
                    "modulos": {},
                }, sort_keys=False),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "hash interno del paquete electoral no coincide"):
                validate_package(
                    package=package,
                    params=params,
                    territory_id="andalucia",
                    edition="2025",
                    root=root,
                    materialize=False,
                )


class OfficialSnapshotExecutorTests(unittest.TestCase):
    def test_siel_provider_requires_exact_validated_snapshot_and_marks_package_eligible(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "configuracion").mkdir()
            (root / "configuracion" / "adquisiciones_electorales_especiales.yaml").write_text(
                REGISTRY.read_text(encoding="utf-8"),
                encoding="utf-8",
            )
            snapshot_out = root / "snapshot"
            package_out = root / "package"

            def fake_download(_url: str, target: Path) -> None:
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(b"locator")

            fake_snapshot = {
                "sections": 6044,
                "candidate_votes_official": 4157539,
                "sections_sha256": SECTIONS_SHA,
                "cera_sha256": CERA_SHA,
            }

            def fake_adapter(_snapshot, out, **_kwargs):
                out.mkdir(parents=True, exist_ok=True)
                manifest = {
                    "schema": "ddd-electoral-package/1.0",
                    "decision": "ACQUIRE",
                    "territory_id": "andalucia",
                    "edition": "2025",
                    "election_id": "andalucia_parlamento_2026",
                    "election_date": "2026-05-17",
                    "source_status": "VERIFIED_OFFICIAL_FINAL",
                }
                (out / "manifest.json").write_text(
                    json.dumps(manifest, ensure_ascii=False) + "\n",
                    encoding="utf-8",
                )
                return manifest

            with mock.patch.object(special, "download", side_effect=fake_download), \
                 mock.patch.object(special, "sha256", return_value=siel.SECTION_LOCATOR_SHA256), \
                 mock.patch("herramientas.adquirir_siel_andalucia_2026.build", return_value=fake_snapshot), \
                 mock.patch("herramientas.adaptador_siel_andalucia_2026.build", side_effect=fake_adapter):
                result = special.prepare(
                    root_dir=root,
                    election_id="andalucia_parlamento_2026",
                    territory_id="andalucia",
                    election_date="2026-05-17",
                    edition="2025",
                    snapshot_out=snapshot_out,
                    package_out=package_out,
                    workers=4,
                )

            self.assertTrue(result["production_eligible"])
            self.assertEqual(result["source_status"], "VERIFIED_OFFICIAL_FINAL")
            self.assertEqual(result["acquisition"]["kind"], "official_api_snapshot")
            self.assertEqual(result["acquisition"]["provider"], "siel")
            persisted = json.loads((package_out / "manifest.json").read_text(encoding="utf-8"))
            self.assertTrue(persisted["production_eligible"])
            self.assertEqual(persisted["acquisition"]["provider"], "siel")

    def test_snapshot_hash_drift_blocks_before_adapter(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "configuracion").mkdir()
            (root / "configuracion" / "adquisiciones_electorales_especiales.yaml").write_text(
                REGISTRY.read_text(encoding="utf-8"),
                encoding="utf-8",
            )
            drift = {
                "sections": 6044,
                "candidate_votes_official": 4157539,
                "sections_sha256": "0" * 64,
                "cera_sha256": CERA_SHA,
            }
            with mock.patch.object(special, "download", side_effect=lambda _u, p: p.write_bytes(b"x")), \
                 mock.patch.object(special, "sha256", return_value=siel.SECTION_LOCATOR_SHA256), \
                 mock.patch("herramientas.adquirir_siel_andalucia_2026.build", return_value=drift), \
                 mock.patch("herramientas.adaptador_siel_andalucia_2026.build") as adapter:
                with self.assertRaisesRegex(ValueError, "difiere de la copia validada"):
                    special.prepare(
                        root_dir=root,
                        election_id="andalucia_parlamento_2026",
                        territory_id="andalucia",
                        election_date="2026-05-17",
                        edition="2025",
                        snapshot_out=root / "snapshot",
                        package_out=root / "package",
                    )
                adapter.assert_not_called()


if __name__ == "__main__":
    unittest.main()
