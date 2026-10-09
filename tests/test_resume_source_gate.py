from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from herramientas.validar_fuentes_reanudacion import validate_resume_sources


class ResumeSourceGateTests(unittest.TestCase):
    def prepare(self, root: Path, *, payload: bytes = b"id,value\n1,x\n", edition: int = 2025, records: int = 1):
        (root / "territorios/demo/config").mkdir(parents=True)
        (root / "territorios/demo/config/fuentes_oficiales.yaml").write_text(
            "territory:\n  id: demo\n  edition: 2025\ncoverage_checks:\n  expected_sections: 1\n",
            encoding="utf-8",
        )
        params = root / "params.yaml"
        params.write_text("meta:\n  territory_id: demo\n", encoding="utf-8")
        package = root / ".ddd-source-package"
        frozen = package / "frozen/source.csv"
        frozen.parent.mkdir(parents=True)
        frozen.write_bytes(payload)
        manifest = {
            "source_id": "official",
            "edition": edition,
            "origin": "https://official.example/source.csv",
            "path": "frozen/source.csv",
            "bytes": len(payload),
            "sha256": hashlib.sha256(payload).hexdigest(),
            "records": records,
            "acquired_at": "2026-09-17T19:00:00Z",
        }
        (package / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
        return params, package

    def test_valid_checkpoint_is_reuse_and_writes_evidence(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            params, package = self.prepare(root)
            evidence = validate_resume_sources(params=params, package=package, root_dir=root)
            self.assertEqual(evidence["decision"], "REUSE")
            self.assertTrue(evidence["restored_from_checkpoint"])
            recorded = json.loads((package / "source_execution.json").read_text(encoding="utf-8"))
            self.assertEqual(recorded["decision"], "REUSE")
            self.assertEqual(recorded["edition"], "2025")

    def test_corrupt_checkpoint_blocks_before_module_execution(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            params, package = self.prepare(root)
            (package / "frozen/source.csv").write_bytes(b"tampered")
            with self.assertRaisesRegex(RuntimeError, "Fuentes BLOQUEADAS: copia preparada dañada"):
                validate_resume_sources(params=params, package=package, root_dir=root)
            self.assertFalse((package / "source_execution.json").exists())

    def test_wrong_edition_blocks_without_acquire_path(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            params, package = self.prepare(root, edition=2024)
            with self.assertRaisesRegex(RuntimeError, "Fuentes BLOQUEADAS"):
                validate_resume_sources(params=params, package=package, root_dir=root)

    def test_missing_package_blocks(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            params, package = self.prepare(root)
            (package / "manifest.json").unlink()
            with self.assertRaisesRegex(RuntimeError, "checkpoint sin sources/manifest.json"):
                validate_resume_sources(params=params, package=package, root_dir=root)

    def test_procedure_wires_gate_before_restarted_modules(self):
        text = Path("procedimiento.sh").read_text(encoding="utf-8")
        gate = "python herramientas/validar_fuentes_reanudacion.py"
        self.assertIn(gate, text)
        self.assertLess(text.index(gate), text.index('python herramientas/registrar_ejecucion.py --params "$PARAMS" --phase start'))
        helper = Path("herramientas/validar_fuentes_reanudacion.py").read_text(encoding="utf-8")
        self.assertNotIn("adquirir_fuentes_oficiales", helper)
        self.assertIn("official_available=False", helper)


if __name__ == "__main__":
    unittest.main()
