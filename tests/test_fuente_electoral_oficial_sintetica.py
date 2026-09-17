from __future__ import annotations

import hashlib
import importlib.util
import json
import tempfile
import unittest
from email.message import Message
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "herramientas/comprobar_fuente_electoral_oficial.py"


def load_checker():
    spec = importlib.util.spec_from_file_location("ddd_election_source_checker", SCRIPT)
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
        self.checker = load_checker()

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
            self.assertEqual(selected["sha256"], hashlib.sha256(data).hexdigest())
            self.assertEqual(selected["bytes"], len(data))
            frozen = Path(selected["downloaded_path"])
            self.assertTrue(frozen.is_file())
            self.assertEqual(frozen.read_bytes(), data)
            persisted = json.loads((Path(td) / "decision_fuente_electoral.json").read_text(encoding="utf-8"))
            self.assertFalse(persisted["rtve_allowed_as_substitute"])

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


if __name__ == "__main__":
    unittest.main()
