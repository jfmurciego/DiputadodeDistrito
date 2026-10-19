"""Read-only proof that archived INE 2025 geometry is reconstructible.

This is a source-availability regression, NOT independent CNIG accreditation.
It never alters the original inputs or produces districts.
"""
from __future__ import annotations

import hashlib
import io
from pathlib import Path
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[1]
PARTS = ROOT / "inputs" / "partes"
ZIP_SHA = "55c9da7e34d3bb3cb725400c35b58e72f4db2ea8321ef91237a89e708d2dbcc4"
NAMES = tuple(f"seccionado_2025.zip.part{i:02d}" for i in range(3))


@unittest.skipUnless(
    (PARTS / "MANIFEST_PARTES.sha256").is_file(),
    "Original INE source parts are intentionally excluded from Docker; "
    "the dedicated GitHub checkout step verifies the actual source bytes.",
)
class NationalOriginalINEArchiveTests(unittest.TestCase):
    def test_reconstruct_2025_geometry_without_changing_source_files(self):
        expected = {}
        for line in (PARTS / "MANIFEST_PARTES.sha256").read_text().splitlines():
            digest, name = line.split()
            expected[name] = digest
        archive = io.BytesIO()
        final_sha = hashlib.sha256()
        for name in NAMES:
            self.assertIn(name, expected)
            source = PARTS / name
            self.assertTrue(source.is_file(), name)
            digest = hashlib.sha256()
            with source.open("rb") as stream:
                for block in iter(lambda: stream.read(1024 * 1024), b""):
                    digest.update(block)
                    final_sha.update(block)
                    archive.write(block)
            self.assertEqual(digest.hexdigest(), expected[name], name)
        self.assertEqual(final_sha.hexdigest(), ZIP_SHA)
        archive.seek(0)
        with zipfile.ZipFile(archive) as zf:
            bad_member = zf.testzip()
            self.assertIsNone(bad_member)
            members = [item for item in zf.namelist() if not item.endswith("/")]
            self.assertGreater(len(members), 0)
            shp = [name for name in members if name.lower().endswith(".shp")]
            self.assertTrue(shp, "Original archive should contain Shapefile geometry")
            print("N08_INE_ORIGINAL_ARCHIVE_SHA256=" + final_sha.hexdigest())
            print("N08_INE_SHP_MEMBERS=" + repr(shp[:12]))
            print("N08_INE_MEMBER_COUNT=" + str(len(members)))


if __name__ == "__main__":
    unittest.main()
