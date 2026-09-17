from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from herramientas.gestionar_fuentes_checkpoint import execute_source_policy


class SourceCheckpointIntegrationTests(unittest.TestCase):
    def package(self, checkpoint: Path, *, edition=2025, payload=b"id,value\n1,x\n", records=1):
        root = checkpoint / "sources"
        frozen = root / "frozen/source.csv"
        frozen.parent.mkdir(parents=True, exist_ok=True)
        frozen.write_bytes(payload)
        manifest = {
            "source_id": "official", "edition": edition,
            "origin": "https://official.example/source.csv",
            "path": "frozen/source.csv", "bytes": len(payload),
            "sha256": hashlib.sha256(payload).hexdigest(),
            "records": records, "acquired_at": "2026-09-17T18:00:00Z",
        }
        (root / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
        return manifest

    def test_resume_restores_checkpoint_and_never_calls_downloader(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); old = root / "checkpoint-in"; new = root / "checkpoint-out"; work = root / "work"
            manifest = self.package(old)
            calls = []

            def downloader(_):
                calls.append("CALLED")
                raise AssertionError("el descargador no debe ejecutarse en REUSE")

            evidence = execute_source_policy(requested_edition=2025, working=work, checkpoint_in=old,
                checkpoint_out=new, official_available=True, downloader=downloader, expected_records=1)
            self.assertEqual(evidence["decision"], "REUSE")
            self.assertTrue(evidence["restored_from_checkpoint"])
            self.assertEqual(calls, [])
            self.assertEqual((new / "sources/frozen/source.csv").read_bytes(), b"id,value\n1,x\n")
            self.assertEqual(json.loads((new / "sources/manifest.json").read_text())["sha256"], manifest["sha256"])
            self.assertEqual(json.loads((new / "source_execution.json").read_text())["decision"], "REUSE")

    def test_first_run_acquires_once_then_same_edition_reuses_without_download(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            first_work = root / "work-first"
            first_checkpoint = root / "checkpoint-first"
            second_work = root / "work-second"
            second_checkpoint = root / "checkpoint-second"
            calls = []
            payload = b"id,value\n1,new\n"

            def downloader(target):
                calls.append("ACQUIRE")
                p = target / "frozen/source.csv"
                p.parent.mkdir(parents=True)
                p.write_bytes(payload)
                return {
                    "source_id": "official", "edition": 2026,
                    "origin": "https://official.example/source.csv",
                    "path": "frozen/source.csv", "bytes": len(payload),
                    "sha256": hashlib.sha256(payload).hexdigest(),
                    "records": 1, "acquired_at": "2026-09-17T19:00:00Z",
                }

            acquired = execute_source_policy(requested_edition=2026, working=first_work, checkpoint_in=None,
                checkpoint_out=first_checkpoint, official_available=True, downloader=downloader, expected_records=1)
            self.assertEqual(acquired["decision"], "ACQUIRE")
            self.assertEqual(calls, ["ACQUIRE"])
            self.assertTrue((first_checkpoint / "sources/frozen/source.csv").is_file())
            self.assertEqual(json.loads((first_checkpoint / "source_execution.json").read_text())["decision"], "ACQUIRE")

            reused = execute_source_policy(requested_edition=2026, working=second_work, checkpoint_in=first_checkpoint,
                checkpoint_out=second_checkpoint, official_available=True, downloader=downloader, expected_records=1)
            self.assertEqual(reused["decision"], "REUSE")
            self.assertTrue(reused["restored_from_checkpoint"])
            self.assertEqual(calls, ["ACQUIRE"])
            self.assertEqual((second_checkpoint / "sources/frozen/source.csv").read_bytes(), payload)
            self.assertEqual(json.loads((second_checkpoint / "source_execution.json").read_text())["decision"], "REUSE")

    def test_damaged_checkpoint_blocks_without_fallback_download(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); old = root / "old"; self.package(old)
            (old / "sources/frozen/source.csv").write_bytes(b"tampered")
            calls=[]

            def downloader(_):
                calls.append(1)
                return {}

            with self.assertRaisesRegex(RuntimeError, "BLOQUEADAS.*tamaño incorrecto.*checksum incorrecto"):
                execute_source_policy(requested_edition=2025, working=root/"work", checkpoint_in=old,
                    checkpoint_out=root/"out", official_available=True, downloader=downloader, expected_records=1)
            self.assertEqual(calls, [])

    def test_checkpoint_output_keeps_sources_manifest_and_payload(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); old = root / "in"; out = root / "out"; work = root / "work"
            manifest = self.package(old, edition=2027, payload=b"id,value\n1,kept\n")

            def forbidden(_):
                raise AssertionError("no debe adquirir al conservar la copia")

            execute_source_policy(requested_edition=2027, working=work, checkpoint_in=old,
                checkpoint_out=out, official_available=True, downloader=forbidden, expected_records=1)
            self.assertTrue((out / "sources/manifest.json").is_file())
            self.assertTrue((out / "sources/frozen/source.csv").is_file())
            self.assertEqual(json.loads((out / "sources/manifest.json").read_text())["sha256"], manifest["sha256"])


if __name__ == "__main__":
    unittest.main()
