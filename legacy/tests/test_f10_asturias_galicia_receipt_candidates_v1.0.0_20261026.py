"""Integridad de los candidatos electorales F10 preservados en esta PR."""
import json
import shutil
import tempfile
import unittest
from pathlib import Path

from herramientas.validar_paquete_electoral import validate_package


ROOT = Path(__file__).resolve().parents[1]
PACKAGE_ROOT = ROOT / "docs/AUDITORIAS/F10_RECIBOS_ELECTORALES_ASTURIAS_GALICIA_20261026/paquetes"
CASES = {
    "principado_de_asturias": {
        "election_id": "asturias_jgpa_2023",
        "params": ROOT / "territorios/principado_de_asturias/config/principado_de_asturias_2025.yaml",
        "source": "data/resultados_electorales_normalizados.csv",
        "sha256": "f82dc1299c97da1d6857ddc7e05cefe34e0b931d8e131608f5c2c998a533cce9",
        "class": "verified_mirror",
    },
    "galicia": {
        "election_id": "galicia_parlamento_2024",
        "params": ROOT / "territorios/galicia/config/galicia_2025.yaml",
        "source": "data/resultados_electorales_vigentes.csv",
        "sha256": "7f9db16181962a1ef543fe0768c6822d19166e91b97e0a9d48b7c449c24aba96",
        "class": "official",
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

    def test_wrong_territory_and_edition_are_rejected(self):
        for territory_id in CASES:
            with self.subTest(territory=territory_id), tempfile.TemporaryDirectory() as raw:
                clone = Path(raw) / "package"
                shutil.copytree(PACKAGE_ROOT / territory_id, clone)
                manifest_path = clone / "manifest.json"
                manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
                manifest["territory_id"] = "galicia" if territory_id != "galicia" else "principado_de_asturias"
                manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
                with self.assertRaisesRegex(ValueError, "territorio o edición del paquete electoral no coincide"):
                    self.validate(territory_id, clone)


if __name__ == "__main__":
    unittest.main()
