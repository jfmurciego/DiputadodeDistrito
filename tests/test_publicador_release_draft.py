from __future__ import annotations

import unittest
from pathlib import Path

import yaml

from herramientas.resolver_release_asset import (
    decide_asset_action,
    decide_release_action,
    require_asset,
    require_release,
    resolve_release,
    validate_downloaded_sha,
)

ROOT = Path(__file__).resolve().parents[1]
PUBLISHER = ROOT / ".github/workflows/p40-publicacion.yml"
MANUAL = ROOT / ".github/workflows/p40-publicacion.yml"


def release(release_id: int, tag: str, *, draft: bool, assets: list[dict] | None = None) -> dict:
    return {
        "id": release_id,
        "tag_name": tag,
        "draft": draft,
        "assets": list(assets or []),
    }


class DraftReleasePromotionTests(unittest.TestCase):
    def test_missing_release_means_create(self):
        self.assertEqual(decide_release_action([], "viewer-extremadura-1-m06-deadbeef"), "create")
        self.assertIsNone(resolve_release([], "viewer-extremadura-1-m06-deadbeef"))

    def test_existing_draft_same_tag_is_reused(self):
        row = release(101, "viewer-extremadura-1-m06-deadbeef", draft=True)
        self.assertEqual(decide_release_action([row], row["tag_name"]), "reuse")
        observed = require_release([row], row["tag_name"])
        self.assertEqual(observed["id"], 101)
        self.assertTrue(observed["draft"])

    def test_unique_active_asset_with_correct_hash_promotes(self):
        asset = {"id": 501, "name": "extremadura-1-m06.geojson.zip"}
        row = release(101, "viewer-extremadura-1-m06-deadbeef", draft=False, assets=[asset])
        observed_release = require_release([row], row["tag_name"])
        observed_asset = require_asset(observed_release, asset["name"])
        self.assertEqual(observed_asset["id"], 501)
        validate_downloaded_sha("a" * 64, "a" * 64)

    def test_zero_or_multiple_final_assets_block(self):
        empty = release(101, "tag", draft=True, assets=[])
        with self.assertRaisesRegex(ValueError, "activo inexistente"):
            require_asset(empty, "asset.zip")

        duplicated = release(
            101,
            "tag",
            draft=True,
            assets=[
                {"id": 1, "name": "asset.zip"},
                {"id": 2, "name": "asset.zip"},
            ],
        )
        with self.assertRaisesRegex(ValueError, "encontrados=2"):
            require_asset(duplicated, "asset.zip")

    def test_wrong_downloaded_hash_blocks(self):
        with self.assertRaisesRegex(ValueError, "SHA-256 distinto"):
            validate_downloaded_sha("a" * 64, "b" * 64)

    def test_republication_is_idempotent_without_clobber(self):
        asset = {"id": 501, "name": "extremadura-1-m06.geojson.zip"}
        row = release(101, "tag", draft=True, assets=[asset])
        self.assertEqual(decide_release_action([row], "tag"), "reuse")
        self.assertEqual(decide_asset_action(row, asset["name"]), "reuse")
        publisher = PUBLISHER.read_text(encoding="utf-8")
        self.assertNotIn("--clobber", publisher)
        self.assertNotIn("gh release upload", publisher)

    def test_multiple_releases_with_same_tag_block(self):
        rows = [
            release(101, "tag", draft=True),
            release(102, "tag", draft=False),
        ]
        with self.assertRaisesRegex(ValueError, "encontrados=2"):
            require_release(rows, "tag")

    def test_publisher_resolves_drafts_by_release_id_and_never_tags_endpoint(self):
        text = PUBLISHER.read_text(encoding="utf-8")
        # T-377 (D-138): la resolución de la Release del ensemble se fue con P28; queda la subida del M08 por asset_id.
        self.assertIn("uploads.github.com", text)
        self.assertIn('repos/$GITHUB_REPOSITORY/releases/assets/$asset_id', text)
        self.assertIn('persisted_sha="$(sha256sum "$persisted"', text)
        self.assertNotIn("releases/tags/$tag", text)

    def test_publication_only_path_accepts_exact_certified_run(self):
        text = MANUAL.read_text(encoding="utf-8")
        parsed = yaml.load(text, Loader=yaml.BaseLoader)
        dispatch = parsed["on"]["workflow_dispatch"]["inputs"]
        self.assertEqual(set(dispatch), {"que_publicar", "territorios", "simular"})  # T-372: el run sale del registro durable
        self.assertIn("PRODUCTION_RUN_ID_OVERRIDE: ${{ needs.resolver.outputs.production_run_id }}", text)
        self.assertIn("herramientas/p40_resolver.py territorios", text)
        self.assertNotIn("p20-distritos.yml", text)
        self.assertNotIn("preparacion-fuentes.yml", text)
        self.assertNotIn("p30-resultados-electorales.yml", text)


    def test_p40_ya_no_publica_ensembles(self):  # T-377 (D-138): P28 retirada sin sustituto
        text = "\n".join(l for l in PUBLISHER.read_text(encoding="utf-8").splitlines() if not l.lstrip().startswith("#"))
        for s in ("ensemble_sha256", "ENSEMBLE_SHA256", "describe-ensemble", "Resolver ensemble persistente solicitado"):
            self.assertNotIn(s, text)

    def test_correct_ensemble_hash_is_accepted(self):
        expected = "a" * 64
        validate_downloaded_sha(expected, expected)

    def test_external_ensemble_asset_substitution_is_blocked(self):
        accredited = "a" * 64
        substituted = "b" * 64
        with self.assertRaisesRegex(ValueError, "SHA-256 distinto"):
            validate_downloaded_sha(accredited, substituted)

    def test_ensemble_zero_or_multiple_assets_remain_blocked(self):
        empty = release(201, "ensemble-tag", draft=True, assets=[])
        with self.assertRaisesRegex(ValueError, "activo inexistente"):
            require_asset(empty, "ensemble-tag.zip")
        duplicate = release(
            201,
            "ensemble-tag",
            draft=True,
            assets=[
                {"id": 301, "name": "ensemble-tag.zip"},
                {"id": 302, "name": "ensemble-tag.zip"},
            ],
        )
        with self.assertRaisesRegex(ValueError, "encontrados=2"):
            require_asset(duplicate, "ensemble-tag.zip")

    def test_workflows_parse(self):
        for path in (PUBLISHER, MANUAL):
            parsed = yaml.load(path.read_text(encoding="utf-8"), Loader=yaml.BaseLoader)
            self.assertIsInstance(parsed, dict)


if __name__ == "__main__":
    unittest.main()
