"""Version: 1.0.2; name: F10 Asturias/Galicia receipt candidate regressions; date: 2026-10-28.
Scope: validate preserved source packages and their canonical CI receipts.
Status: candidate. Change/reason: exact counts and receipts run on the frozen aee8215e root
(tests/_raiz_congelada.py), so new full runs do not change the historical case.
Previous: legacy/tests/test_f10_asturias_galicia_receipt_candidates_v1.0.1_20261028.py.
"""
import json
import shutil
import tempfile
import unittest
from pathlib import Path

from herramientas.validar_paquete_electoral import validate_package
from herramientas.estado_derivado_f10 import _electoral_identity


from tests._raiz_congelada import frozen_root  # noqa: E402

# Estado congelado en aee8215e: los recuentos y receipts exactos no dependen de las ejecuciones
# completas posteriores, que reescriben catálogo y productos en main.
ROOT = frozen_root()
PACKAGE_ROOT = ROOT / "docs/AUDITORIAS/F10_RECIBOS_ELECTORALES_ASTURIAS_GALICIA_20261026/paquetes"
CASES = {
    "principado_de_asturias": {
        "election_id": "asturias_jgpa_2023",
        "params": ROOT / "territorios/principado_de_asturias/config/principado_de_asturias_2025.yaml",
        "source": "data/resultados_electorales_normalizados.csv",
        "sha256": "f82dc1299c97da1d6857ddc7e05cefe34e0b931d8e131608f5c2c998a533cce9",
        "class": "verified_mirror",
        "receipt": "territorios/principado_de_asturias/evidencia/fuentes_electorales/2025/29fb6a23b9c2e9fa3f3c393c34b90c868983302ea5d8767f7be5d472fbd6536c/40389705458/receipt.json",
        "artifact_name": "ddd-electoral-package-principado_de_asturias-2025-40389705458",
        "artifact_sha256": "85e2d198db4216120dfacd46a6f5681dcf24f62ac8e68aacd634575f5e5eb037",
    },
    "galicia": {
        "election_id": "galicia_parlamento_2024",
        "params": ROOT / "territorios/galicia/config/galicia_2025.yaml",
        "source": "data/resultados_electorales_vigentes.csv",
        "sha256": "7f9db16181962a1ef543fe0768c6822d19166e91b97e0a9d48b7c449c24aba96",
        "class": "official",
        "receipt": "territorios/galicia/evidencia/fuentes_electorales/2025/af07c8d3bce5a45f63afd1c5d5eca0423a7713f71b4fbbb6c812f2509f51f230/40389705458/receipt.json",
        "artifact_name": "ddd-electoral-package-galicia-2025-40389705458",
        "artifact_sha256": "58b1d99c27cce39a55129484d9d2a3f8ebcd5748bb3a063c813440bc209e60e2",
    },
}


class F10AsturiasGaliciaReceiptCandidateTests(unittest.TestCase):
    def validate(self, territory_id: str, package: Path | None = None):
        case = CASES[territory_id]
        return validate_package(
            package=package or PACKAGE_ROOT / territory_id,
            params=case["params"],
            territory_id=territory_id,
            edition="2025",
            root=ROOT,
            materialize=False,
        )

    def test_both_packages_pass_the_canonical_validator_with_exact_identity(self):
        for territory_id, case in CASES.items():
            with self.subTest(territory=territory_id):
                result = self.validate(territory_id)
                self.assertEqual(result["decision"], "READY_PACKAGE")
                self.assertEqual(result["election_id"], case["election_id"])
                self.assertEqual(result["package_sha256"], case["sha256"])
                self.assertTrue(result["provenance_hash_matches_contract"])

    def test_manifest_pins_publisher_and_declared_source_class(self):
        for territory_id, case in CASES.items():
            with self.subTest(territory=territory_id):
                manifest = json.loads((PACKAGE_ROOT / territory_id / "manifest.json").read_text(encoding="utf-8"))
                self.assertEqual(manifest["territory_id"], territory_id)
                self.assertEqual(manifest["edition"], "2025")
                self.assertEqual(manifest["election_id"], case["election_id"])
                selected = manifest["selected_source"]
                self.assertEqual(selected["sha256"], case["sha256"])
                if territory_id == "galicia":
                    self.assertEqual(selected["publisher"], "Xunta de Galicia")
                else:
                    self.assertEqual(selected["source_class"], case["class"])

    def test_modified_payload_is_rejected(self):
        for territory_id, case in CASES.items():
            with self.subTest(territory=territory_id), tempfile.TemporaryDirectory() as raw:
                clone = Path(raw) / "package"
                shutil.copytree(PACKAGE_ROOT / territory_id, clone)
                payload = clone / case["source"]
                payload.write_bytes(payload.read_bytes() + b"\n")
                with self.assertRaisesRegex(ValueError, "hash interno del paquete electoral no coincide"):
                    self.validate(territory_id, clone)

    def test_wrong_territory_edition_and_election_identity_are_rejected(self):
        for territory_id in CASES:
            for field, value, message in (
                ("territory_id", "other", "territorio o edición del paquete electoral no coincide"),
                ("edition", "2024", "territorio o edición del paquete electoral no coincide"),
                ("election_id", "other_election", "election_id del contrato electoral"),
            ):
                with self.subTest(territory=territory_id, field=field), tempfile.TemporaryDirectory() as raw:
                    clone = Path(raw) / "package"
                    shutil.copytree(PACKAGE_ROOT / territory_id, clone)
                    manifest_path = clone / "manifest.json"
                    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
                    manifest[field] = value
                    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
                    with self.assertRaisesRegex(ValueError, message):
                        self.validate(territory_id, clone)

    def test_canonical_receipts_pin_real_ci_run_artifact_and_election_identity(self):
        for territory_id, case in CASES.items():
            with self.subTest(territory=territory_id):
                # The durable catalog is YAML; use the loader already required by the source validator.
                import yaml
                state = yaml.safe_load((ROOT / "configuracion/catalogo_preparacion.yaml").read_text(encoding="utf-8"))
                territory = next(row for row in state["territories"] if row["territory_id"] == territory_id)
                receipt_rel = territory["editions"]["2025"]["evidence"]["electoral_source"]
                self.assertEqual(case["receipt"], receipt_rel)
                receipt = json.loads((ROOT / receipt_rel).read_text(encoding="utf-8"))
                self.assertEqual("ddd.catalog-evidence/1.0", receipt["schema"])
                self.assertEqual("electoral_source", receipt["kind"])
                self.assertEqual(territory_id, receipt["territory_id"])
                self.assertEqual("2025", receipt["edition"])
                self.assertEqual(case["election_id"], receipt["election_id"])
                self.assertEqual(40389705458, receipt["run_id"])
                self.assertEqual(case["artifact_name"], receipt["artifact_name"])
                self.assertEqual(case["artifact_sha256"], receipt["artifact_sha256"])
                self.assertEqual("164a2d6044282f01702046596b087b8d688af71d", receipt["source_commit"])
                _electoral_identity(
                    receipt,
                    election_id=case["election_id"],
                    election_date=receipt["election_date"],
                )
                wrong_election = case["election_id"] + "_other"
                with self.subTest(field="election_id"), self.assertRaisesRegex(
                    ValueError, "electoral_identity_sha256 no reconcilia"
                ):
                    _electoral_identity(
                        receipt, election_id=wrong_election,
                        election_date=receipt["election_date"],
                    )
                for field, replacement in (("artifact_sha256", "0" * 64),
                                           ("electoral_identity_sha256", "f" * 64)):
                    tampered = dict(receipt)
                    tampered[field] = replacement
                    with self.subTest(field=field), self.assertRaisesRegex(
                        ValueError, "electoral_identity_sha256 no reconcilia"
                    ):
                        _electoral_identity(
                            tampered,
                            election_id=case["election_id"],
                            election_date=receipt["election_date"],
                        )


if __name__ == "__main__":
    unittest.main()
