from __future__ import annotations

import hashlib
import importlib.util
import json
import shutil
import tempfile
import unittest
from email.message import Message
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
CHECKER = ROOT / "herramientas/comprobar_fuente_electoral_oficial.py"
INSTALLER = ROOT / "herramientas/instalar_fuente_electoral_oficial.py"
WORKFLOW = ROOT / ".github/workflows/produccion-distritos.yml"


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


class FakeResponse:
    def __init__(self, data: bytes, content_type: str = "text/csv", status: int = 200):
        self._data = data
        self.status = status
        self.headers = Message()
        self.headers["Content-Type"] = content_type

    def read(self, n: int = -1) -> bytes:
        return self._data if n < 0 else self._data[:n]

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


class OfficialElectionSourceSynthetic(unittest.TestCase):
    def setUp(self):
        self.checker = load_module(CHECKER, "ddd_election_source_checker")
        self.installer = load_module(INSTALLER, "ddd_election_source_installer")

    @staticmethod
    def _base(sources: list[dict]) -> dict:
        return {
            "schema": "ddd-election-official-source-declaration/1.0",
            "territory_id": "synthetic",
            "election_id": "synthetic-2025",
            "minimum_resolution": "section",
            "allowed_official_hosts": ["official.example"],
            "forbidden_substitutes": ["rtve.es", "Corporación RTVE"],
            "max_download_bytes": 1000000,
            "sources": sources,
        }

    @staticmethod
    def _write_contract(root: Path, sha: str) -> Path:
        contract = root / "config/election.json"
        contract.parent.mkdir(parents=True, exist_ok=True)
        contract.write_text(json.dumps({
            "schema_family": "ddd-election",
            "schema_version": "1.0.0",
            "election_id": "synthetic-2025",
            "territory_id": "synthetic",
            "sources": [{
                "id": "official_csv",
                "path": "runtime/elections/results.csv",
                "sha256": sha,
                "publisher": "Official Authority",
                "source_url": "https://official.example/results.csv",
            }],
        }), encoding="utf-8")
        params = root / "params.yaml"
        params.write_text(yaml.safe_dump({
            "meta": {"territory_id": "synthetic", "run_name": "synthetic", "year": 2025},
            "modulos": {"modulo_07_agregar_resultados_electorales": {"election_contract": "config/election.json"}},
        }, sort_keys=False), encoding="utf-8")
        return params

    def test_public_granular_file_is_frozen_with_checksum(self):
        data = b"seccion,mesa,candidatura,votos\n001,01,A,10\n"
        declaration = self._base([{
            "id": "official_csv",
            "publisher": "Official Authority",
            "url": "https://official.example/results.csv",
            "access": "public",
            "declared_resolution": "section",
            "granularity_markers": ["seccion", "mesa"],
        }])

        def opener(request, timeout=0):
            self.assertEqual(request.full_url, "https://official.example/results.csv")
            return FakeResponse(data)

        with tempfile.TemporaryDirectory() as td:
            decision = self.checker.check_declaration(declaration, td, opener=opener)
            self.assertEqual(decision["decision"], "READY")
            selected = decision["selected_source"]
            expected = hashlib.sha256(data).hexdigest()
            self.assertEqual(selected["sha256"], expected)
            self.assertEqual(selected["bytes"], len(data))
            frozen = Path(td) / selected["artifact_path"]
            checksum = Path(td) / selected["checksum_path"]
            self.assertEqual(frozen.read_bytes(), data)
            self.assertEqual(checksum.read_text(encoding="utf-8").split()[0], expected)
            persisted = json.loads((Path(td) / "decision_fuente_electoral.json").read_text(encoding="utf-8"))
            self.assertFalse(persisted["rtve_allowed_as_substitute"])

    def test_end_to_end_download_artifact_recovery_contract_path_and_processing_enabled(self):
        data = b"seccion,mesa,candidatura,votos\n001,01,A,10\n002,01,B,20\n"
        expected = hashlib.sha256(data).hexdigest()
        declaration = self._base([{
            "id": "official_csv",
            "publisher": "Official Authority",
            "url": "https://official.example/results.csv",
            "access": "public",
            "declared_resolution": "section",
            "granularity_markers": ["seccion", "mesa"],
        }])

        def opener(request, timeout=0):
            return FakeResponse(data)

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            produced = root / "produced-artifact"
            recovered = root / "recovered-artifact"
            decision = self.checker.check_declaration(declaration, produced, opener=opener)
            self.assertEqual(decision["decision"], "READY")
            shutil.copytree(produced, recovered)
            params = self._write_contract(root, expected)
            report = root / "install-report.json"
            result = self.installer.install_from_artifact(params, recovered, root_dir=root, report_path=report)
            self.assertEqual(result["decision"], "READY")
            self.assertTrue(result["processing_enabled"])
            destination = root / "runtime/elections/results.csv"
            self.assertEqual(destination.read_bytes(), data)
            self.assertEqual(self.installer.sha256_file(destination), expected)
            self.assertEqual(json.loads(report.read_text(encoding="utf-8"))["processing_enabled"], True)

    def test_blocked_source_prevents_processing(self):
        declaration = self._base([{
            "id": "blocked",
            "publisher": "Official Authority",
            "url": "https://official.example/summary",
            "access": "public",
            "declared_resolution": "municipality",
        }])

        def opener(request, timeout=0):
            return FakeResponse(b"municipio,votos\n001,10\n")

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            artifact = root / "artifact"
            decision = self.checker.check_declaration(declaration, artifact, opener=opener)
            self.assertEqual(decision["decision"], "BLOCK")
            params = self._write_contract(root, hashlib.sha256(b"x").hexdigest())
            with self.assertRaises(ValueError):
                self.installer.install_from_artifact(params, artifact, root_dir=root, report_path=root / "report.json")
            self.assertFalse((root / "runtime/elections/results.csv").exists())

    def test_credentials_and_insufficient_granularity_block(self):
        declaration = self._base([
            {
                "id": "credential_repo",
                "publisher": "Official Authority",
                "url": "https://official.example/private",
                "access": "credentials_required",
                "declared_resolution": "section",
                "granularity_markers": ["seccion"],
            },
            {
                "id": "public_summary",
                "publisher": "Official Authority",
                "url": "https://official.example/summary",
                "access": "public",
                "declared_resolution": "municipality",
            },
        ])

        def opener(request, timeout=0):
            if request.full_url.endswith("/private"):
                return FakeResponse(b"login", "text/html")
            return FakeResponse(b"<html>summary</html>", "text/html")

        with tempfile.TemporaryDirectory() as td:
            decision = self.checker.check_declaration(declaration, td, opener=opener)
            self.assertEqual(decision["decision"], "BLOCK")
            statuses = {row["id"]: row["status"] for row in decision["checks"]}
            self.assertEqual(statuses["credential_repo"], "BLOCK_CREDENTIALS")
            self.assertEqual(statuses["public_summary"], "BLOCK_GRANULARITY")
            self.assertIsNone(decision["selected_source"])

    def test_forbidden_substitute_cannot_be_selected(self):
        declaration = self._base([{
            "id": "forbidden",
            "publisher": "Corporación RTVE",
            "url": "https://official.example/results.csv",
            "access": "public",
            "declared_resolution": "section",
            "granularity_markers": ["seccion"],
        }])
        called = False

        def opener(request, timeout=0):
            nonlocal called
            called = True
            return FakeResponse(b"seccion,votos\n001,10\n")

        with tempfile.TemporaryDirectory() as td:
            decision = self.checker.check_declaration(declaration, td, opener=opener)
            self.assertEqual(decision["decision"], "BLOCK")
            self.assertEqual(decision["checks"][0]["status"], "BLOCK_FORBIDDEN_SUBSTITUTE")
            self.assertFalse(called)

    def test_workflow_recovers_and_installs_artifact_before_m07(self):
        text = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("name: ddd-electoral-source-${{ github.run_id }}", text)
        self.assertIn("Recuperar fuente electoral oficial aprobada", text)
        self.assertIn("instalar_fuente_electoral_oficial.py", text)
        self.assertIn("--artifact-dir /app/.ddd-electoral-source", text)
        self.assertNotIn("extremadura", (ROOT / "herramientas/instalar_fuente_electoral_oficial.py").read_text(encoding="utf-8").lower())


if __name__ == "__main__":
    unittest.main()
