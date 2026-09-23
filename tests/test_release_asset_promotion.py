import hashlib
import tempfile
import unittest
from pathlib import Path

from herramientas.promover_release_asset import PromotionError, promote


class FakeApi:
    def __init__(self, releases=None, downloaded=None):
        self.releases = releases or []
        self.downloaded = downloaded
        self.created = 0
        self.uploaded = 0

    def list_releases(self, repo):
        return self.releases

    def create_draft(self, repo, tag, target):
        self.created += 1
        release = {"id": 101, "tag_name": tag, "draft": True, "assets": []}
        self.releases.append(release)
        return release

    def release_by_id(self, repo, release_id):
        return next(r for r in self.releases if r["id"] == release_id)

    def upload_asset(self, repo, release_id, asset_name, source):
        self.uploaded += 1
        release = self.release_by_id(repo, release_id)
        asset = {"id": 501 + self.uploaded, "name": asset_name}
        release.setdefault("assets", []).append(asset)
        return asset

    def download_asset(self, repo, asset_id, target):
        target.write_bytes(self.downloaded)


class ReleasePromotionTests(unittest.TestCase):
    def run_promotion(self, api, source_bytes=b"certified"):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source = root / "product.zip"
            source.write_bytes(source_bytes)
            result = promote(
                api,
                repo="o/r",
                tag="viewer-extremadura-35859241320-m06-deadbeef",
                target_commit="abc123",
                asset_name="extremadura-35859241320-m06.geojson.zip",
                source=source,
                verify_path=root / "verify",
            )
            return result

    def test_release_inexistente_se_crea_y_se_resuelve_como_draft(self):
        api = FakeApi(downloaded=b"certified")
        result = self.run_promotion(api)
        self.assertEqual(api.created, 1)
        self.assertTrue(result["release_draft"])
        self.assertEqual(result["release_id"], 101)

    def test_draft_existente_con_mismo_tag_se_reutiliza(self):
        tag = "viewer-extremadura-35859241320-m06-deadbeef"
        api = FakeApi(
            releases=[{"id": 77, "tag_name": tag, "draft": True, "assets": []}],
            downloaded=b"certified",
        )
        result = self.run_promotion(api)
        self.assertEqual(api.created, 0)
        self.assertEqual(result["release_id"], 77)

    def test_activo_unico_y_hash_correcto_promueve(self):
        tag = "viewer-extremadura-35859241320-m06-deadbeef"
        name = "extremadura-35859241320-m06.geojson.zip"
        api = FakeApi(
            releases=[{"id": 77, "tag_name": tag, "draft": True,
                       "assets": [{"id": 9, "name": name}]}],
            downloaded=b"certified",
        )
        result = self.run_promotion(api)
        self.assertEqual(result["asset_id"], 9)
        self.assertEqual(result["sha256"], hashlib.sha256(b"certified").hexdigest())

    def test_cero_o_varios_activos_finales_bloquean(self):
        tag = "viewer-extremadura-35859241320-m06-deadbeef"
        name = "extremadura-35859241320-m06.geojson.zip"

        class UploadLost(FakeApi):
            def upload_asset(self, repo, release_id, asset_name, source):
                self.uploaded += 1
                return {"id": 501, "name": asset_name}

        zero = UploadLost(
            releases=[{"id": 77, "tag_name": tag, "draft": True, "assets": []}],
            downloaded=b"certified",
        )
        with self.assertRaises(PromotionError):
            self.run_promotion(zero)
        self.assertEqual(zero.uploaded, 1)

        many = FakeApi(
            releases=[{"id": 77, "tag_name": tag, "draft": True,
                       "assets": [{"id": 1, "name": name}, {"id": 2, "name": name}]}],
            downloaded=b"certified",
        )
        with self.assertRaises(PromotionError):
            self.run_promotion(many)

    def test_hash_distinto_bloquea(self):
        tag = "viewer-extremadura-35859241320-m06-deadbeef"
        name = "extremadura-35859241320-m06.geojson.zip"
        api = FakeApi(
            releases=[{"id": 77, "tag_name": tag, "draft": True,
                       "assets": [{"id": 9, "name": name}]}],
            downloaded=b"different",
        )
        with self.assertRaises(PromotionError):
            self.run_promotion(api)

    def test_republicacion_idempotente_no_sube_ni_clobber(self):
        tag = "viewer-extremadura-35859241320-m06-deadbeef"
        name = "extremadura-35859241320-m06.geojson.zip"
        api = FakeApi(
            releases=[{"id": 77, "tag_name": tag, "draft": True,
                       "assets": [{"id": 9, "name": name}]}],
            downloaded=b"certified",
        )
        first = self.run_promotion(api)
        second = self.run_promotion(api)
        self.assertEqual(api.uploaded, 0)
        self.assertEqual(first["asset_id"], second["asset_id"])
        source = (Path(__file__).parents[1] / "herramientas/promover_release_asset.py").read_text()
        self.assertNotIn("--clobber", source)

    def test_publicador_no_depende_del_endpoint_tags_y_expone_publicacion_por_run(self):
        root = Path(__file__).parents[1]
        reusable = (root / ".github/workflows/_reutilizable-publicar-sitio.yml").read_text()
        manual = (root / ".github/workflows/desplegar-visor-publico.yml").read_text()
        promotion = reusable.split("- name: Promover productos a release persistente", 1)[1].split(
            "- name: Resolver ensemble persistente solicitado", 1
        )[0]
        self.assertNotIn("/releases/tags/", promotion)
        self.assertIn("promover_release_asset.py", promotion)
        self.assertIn("production_run_id:", manual)
        self.assertIn("PRODUCTION_RUN_ID_OVERRIDE: ${{ inputs.production_run_id }}", manual)

    def test_release_duplicado_con_mismo_tag_bloquea(self):
        tag = "viewer-extremadura-35859241320-m06-deadbeef"
        api = FakeApi(
            releases=[
                {"id": 1, "tag_name": tag, "draft": True, "assets": []},
                {"id": 2, "tag_name": tag, "draft": True, "assets": []},
            ],
            downloaded=b"certified",
        )
        with self.assertRaises(PromotionError):
            self.run_promotion(api)


if __name__ == "__main__":
    unittest.main()
