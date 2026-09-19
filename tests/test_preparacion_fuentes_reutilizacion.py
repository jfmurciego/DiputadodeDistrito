from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
import zipfile
from pathlib import Path

import yaml

from herramientas.seleccionar_paquete_fuentes import select_first_valid, validate_prepared_package

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github/workflows/preparacion-fuentes.yml"


def build_package(root: Path, *, territory="la_rioja", edition=2025, corrupt=False) -> Path:
    package = root
    package.mkdir(parents=True, exist_ok=True)
    source = b"official-source-bytes"
    source_sha = hashlib.sha256(source).hexdigest()
    docs = {
        "declaracion_materializacion.json": {
            "territory_id": territory, "territory": "La Rioja", "edition": edition,
            "sources": [{"source_id": "population"}],
        },
        "inventario_fuentes.json": {
            "territory_id": territory, "territory": "La Rioja", "edition": edition,
            "sources": [{
                "source_id": "population", "path": "inputs/population.zip",
                "bytes": len(source), "sha256": source_sha,
            }],
        },
        "manifiesto_procedencia.json": {
            "territory_id": territory, "territory": "La Rioja", "edition": edition,
            "sources": [{"source_id": "population"}],
        },
        "decision_adquisicion.json": {
            "territory_id": territory, "territory": "La Rioja", "edition": edition,
            "decision": "READY",
        },
    }
    bundle = package / "prepared_sources.zip"
    with zipfile.ZipFile(bundle, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for name, data in docs.items():
            zf.writestr(name, json.dumps(data))
        zf.writestr("materialized/inputs/population.zip", source if not corrupt else source + b"corrupt")
    manifest = {
        "source_id": "prepared-territorial-sources:population",
        "territory_id": territory,
        "edition": edition,
        "origin": "https://official.example/population",
        "path": "prepared_sources.zip",
        "bytes": bundle.stat().st_size,
        "sha256": hashlib.sha256(bundle.read_bytes()).hexdigest(),
        "records": 1,
        "acquired_at": "2026-09-19T00:00:00Z",
    }
    (package / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    return package


class PreparedSourceReuseTests(unittest.TestCase):
    def test_valid_previous_package_is_reused(self):
        with tempfile.TemporaryDirectory() as td:
            package = build_package(Path(td) / "valid")
            selected, diagnostics = select_first_valid(
                [package], territory_id="la_rioja", edition=2025, reuse_enabled=True
            )
            self.assertEqual(selected, package)
            self.assertTrue(diagnostics[0]["valid"])
            self.assertEqual(validate_prepared_package(package, territory_id="la_rioja", edition=2025), (True, []))

    def test_reuse_disabled_selects_nothing(self):
        with tempfile.TemporaryDirectory() as td:
            package = build_package(Path(td) / "valid")
            selected, diagnostics = select_first_valid(
                [package], territory_id="la_rioja", edition=2025, reuse_enabled=False
            )
            self.assertIsNone(selected)
            self.assertEqual(diagnostics, [])

    def test_corrupt_newest_falls_back_to_older_valid_package(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            newest = build_package(root / "newest", corrupt=True)
            older = build_package(root / "older")
            selected, diagnostics = select_first_valid(
                [newest, older], territory_id="la_rioja", edition=2025, reuse_enabled=True
            )
            self.assertEqual(selected, older)
            self.assertFalse(diagnostics[0]["valid"])
            self.assertTrue(diagnostics[1]["valid"])
            self.assertTrue(any("tamaño incorrecto" in r or "checksum incorrecto" in r for r in diagnostics[0]["reasons"]))

    def test_workflow_declares_runner_dependency_and_reuse_switch_controls_both_packages(self):
        data = yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))
        jobs = data["jobs"]
        territorial_steps = jobs["territoriales"]["steps"]
        install_index = next(i for i, s in enumerate(territorial_steps) if s.get("name") == "Instalar dependencias de resolución territorial")
        generate_index = next(i for i, s in enumerate(territorial_steps) if s.get("name") == "Generar declaración territorial desde fuentes oficiales")
        self.assertLess(install_index, generate_index)
        self.assertIn("PyYAML==6.0.2", territorial_steps[install_index]["run"])

        territorial_previous = next(s for s in territorial_steps if s.get("id") == "previous")
        electoral_previous = next(s for s in jobs["electorales"]["steps"] if s.get("id") == "previous")
        expected = "${{ inputs.reutilizar_si_ya_preparada }}"
        self.assertEqual(territorial_previous["if"], expected)
        self.assertEqual(electoral_previous["if"], expected)

        script = territorial_previous["run"]
        self.assertIn("herramientas.seleccionar_paquete_fuentes", script)
        self.assertIn("se busca uno anterior", script)
        self.assertIn("break 2", script)


if __name__ == "__main__":
    unittest.main()
