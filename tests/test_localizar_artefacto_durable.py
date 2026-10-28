"""Localización de artefactos acreditados en Actions o en su release draft durable."""
from __future__ import annotations

import hashlib
import io
import tempfile
import unittest
import zipfile
from pathlib import Path

from herramientas.localizar_artefacto_durable import (
    EXIT_DIGEST,
    EXIT_NOT_FOUND,
    LocationError,
    fetch,
    locate,
)

REPO = "o/r"
RUN = 40604431189
NAME = f"ddd-state-{RUN}-M06"


def _zip(members: dict[str, bytes]) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        for path, data in members.items():
            zf.writestr(path, data)
    return buf.getvalue()


PAYLOAD = _zip({"run/CHAIN_STATE.json": b"{}", "cache/m06.geojson": b"x"})
SHA = hashlib.sha256(PAYLOAD).hexdigest()


def _api(artifacts, releases=()):
    def api(path: str):
        if path.startswith(f"repos/{REPO}/actions/runs/{RUN}/artifacts"):
            return {"artifacts": list(artifacts)}
        if path.startswith(f"repos/{REPO}/releases"):
            return list(releases)
        raise AssertionError(path)
    return api


def _release(asset_name=f"{NAME}-12779789644.zip", digest=SHA, tag=f"almacen-m06-cantabria-{RUN}"):
    return {"tag_name": tag, "assets": [{"id": 7, "name": asset_name, "digest": f"sha256:{digest}"}]}


class LocateTests(unittest.TestCase):
    def test_live_actions_artifact_is_used_first(self):
        loc = locate(REPO, RUN, NAME, SHA, api=_api(
            [{"id": 1, "name": NAME, "expired": False, "digest": f"sha256:{SHA}"}], [_release()]))
        self.assertEqual("actions", loc["source"])
        self.assertEqual(f"repos/{REPO}/actions/artifacts/1/zip", loc["download_path"])

    def test_expired_artifact_falls_back_to_verified_release(self):
        loc = locate(REPO, RUN, NAME, SHA, api=_api(
            [{"id": 1, "name": NAME, "expired": True, "digest": f"sha256:{SHA}"}], [_release()]))
        self.assertEqual("release", loc["source"])
        self.assertEqual(12779789644, loc["artifact_id"])
        self.assertEqual(f"repos/{REPO}/releases/assets/7", loc["download_path"])

    def test_live_artifact_with_other_digest_blocks_without_release_fallback(self):
        with self.assertRaises(LocationError) as ctx:
            locate(REPO, RUN, NAME, SHA, api=_api(
                [{"id": 1, "name": NAME, "expired": False, "digest": "sha256:" + "0" * 64}], [_release()]))
        self.assertEqual(EXIT_DIGEST, ctx.exception.code)

    def test_release_with_other_digest_or_outside_store_is_rejected(self):
        with self.assertRaises(LocationError) as ctx:
            locate(REPO, RUN, NAME, SHA, api=_api([], [_release(digest="1" * 64)]))
        self.assertEqual(EXIT_DIGEST, ctx.exception.code)
        with self.assertRaises(LocationError) as ctx:
            locate(REPO, RUN, NAME, SHA, api=_api([], [_release(tag=f"ensemble-aragon-{RUN}")]))
        self.assertEqual(EXIT_NOT_FOUND, ctx.exception.code)

    def test_source_package_of_other_run_is_found_in_the_consuming_release(self):
        source = "ddd-source-package-cantabria-2025-40241638106"
        rel = _release(asset_name=f"{source}-12617190596.zip")
        loc = locate(REPO, 40241638106, source, SHA, api=lambda p: (
            {"artifacts": []} if "/actions/runs/" in p else [rel]))
        self.assertEqual(("release", 12617190596), (loc["source"], loc["artifact_id"]))

    def test_similar_asset_name_is_not_confused(self):
        other = _release(asset_name=f"{NAME}U-12779789644.zip")
        with self.assertRaises(LocationError) as ctx:
            locate(REPO, RUN, NAME, SHA, api=_api([], [other]))
        self.assertEqual(EXIT_NOT_FOUND, ctx.exception.code)

    def test_nothing_available_blocks(self):
        with self.assertRaises(LocationError) as ctx:
            locate(REPO, RUN, NAME, SHA, api=_api([], []))
        self.assertEqual(EXIT_NOT_FOUND, ctx.exception.code)


class FetchTests(unittest.TestCase):
    def _location(self):
        return locate(REPO, RUN, NAME, SHA, api=_api([], [_release()]))

    def test_download_is_verified_and_extracted_like_gh_run_download(self):
        with tempfile.TemporaryDirectory() as tmp:
            seen = []
            def download(path, target, release_asset):
                seen.append((path, release_asset)); target.write_bytes(PAYLOAD)
            result = fetch(self._location(), Path(tmp) / "in", extract=True, download=download)
            self.assertEqual([(f"repos/{REPO}/releases/assets/7", True)], seen)
            self.assertTrue((Path(tmp) / "in/run/CHAIN_STATE.json").is_file())
            self.assertFalse((Path(tmp) / f"in/{NAME}.zip").exists())
            self.assertEqual(str(Path(tmp) / "in"), result["extracted_to"])

    def test_tampered_bytes_are_rejected_and_removed(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "in"
            with self.assertRaises(LocationError) as ctx:
                fetch(self._location(), out, extract=True,
                      download=lambda p, t, r: t.write_bytes(PAYLOAD + b"!"))
            self.assertEqual(EXIT_DIGEST, ctx.exception.code)
            self.assertEqual([], list(out.iterdir()))

    def test_unsafe_zip_paths_are_rejected(self):
        evil = _zip({"../fuera.txt": b"x"})
        loc = dict(self._location(), artifact_sha256=hashlib.sha256(evil).hexdigest())
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(LocationError):
                fetch(loc, Path(tmp) / "in", extract=True, download=lambda p, t, r: t.write_bytes(evil))
            self.assertFalse((Path(tmp) / "fuera.txt").exists())


if __name__ == "__main__":
    unittest.main()
