"""Localización de artefactos acreditados en Actions o en su release draft durable."""
from __future__ import annotations

import hashlib
import io
import json
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

    def test_without_accredited_sha_the_recorded_digest_is_adopted(self):
        live = locate(REPO, RUN, NAME, None, api=_api(
            [{"id": 1, "name": NAME, "expired": False, "digest": f"sha256:{SHA}"}]))
        self.assertEqual(SHA, live["artifact_sha256"])
        stored = locate(REPO, RUN, NAME, "", api=_api([], [_release()]))
        self.assertEqual((SHA, "release"), (stored["artifact_sha256"], stored["source"]))

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


class R2PrimeroTests(unittest.TestCase):
    """T-302: R2 se lee primero (índice con sha256); alterado se rechaza; ausente cae al release."""
    CLAVE = f"arc-p/m06/{NAME}-12779789644_{SHA[:12]}.zip"
    INDICE = {CLAVE: {"run_id": str(RUN), "artifact_name": NAME, "artifact_id": 12779789644, "sha256": SHA}}

    def _loc(self, indice=None, releases=None):
        return locate(REPO, RUN, NAME, SHA, api=_api([], [_release()] if releases is None else releases),
                      r2_index=self.INDICE if indice is None else indice)

    def test_reads_from_r2_first_with_release_as_fallback(self):
        loc = self._loc()
        self.assertEqual(("r2", self.CLAVE), (loc["source"], loc["r2_key"]))
        self.assertEqual("release", loc["fallback"]["source"])
        with tempfile.TemporaryDirectory() as tmp:
            usado = []
            def r2(k, t): usado.append(k); t.write_bytes(PAYLOAD)
            def release(*a): raise AssertionError("no debe tocar el release")
            res = fetch(loc, Path(tmp) / "in", extract=True, download=release, r2=r2)
            self.assertEqual([self.CLAVE], usado)
            self.assertTrue((Path(tmp) / "in/run/CHAIN_STATE.json").is_file())
            self.assertEqual("r2", res["source"])

    def test_tampered_r2_is_rejected_and_never_extracted(self):
        loc = self._loc(releases=[])
        self.assertIsNone(loc["fallback"])
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "in"
            with self.assertRaises(LocationError) as ctx:
                fetch(loc, out, extract=True, r2=lambda k, t: t.write_bytes(PAYLOAD + b"!"))
            self.assertEqual(EXIT_DIGEST, ctx.exception.code)
            self.assertEqual([], list(out.iterdir()))

    def test_tampered_r2_with_valid_release_uses_the_verified_release(self):
        with tempfile.TemporaryDirectory() as tmp:
            res = fetch(self._loc(), Path(tmp) / "in", extract=False,
                        download=lambda p, t, r: t.write_bytes(PAYLOAD),
                        r2=lambda k, t: t.write_bytes(b"alterado"))
            self.assertEqual("release", res["source"])

    def test_absent_in_r2_falls_back_to_release(self):
        loc = self._loc(indice={})
        self.assertEqual("release", loc["source"])
        loc = self._loc(indice={"otra": {"run_id": "1", "artifact_name": NAME, "sha256": SHA}})
        self.assertEqual("release", loc["source"])

    def test_missing_r2_object_falls_back_and_other_digest_is_ignored(self):
        def falta(k, t): raise OSError("404")
        with tempfile.TemporaryDirectory() as tmp:
            res = fetch(self._loc(), Path(tmp) / "in", extract=False,
                        download=lambda p, t, r: t.write_bytes(PAYLOAD), r2=falta)
            self.assertEqual("release", res["source"])
        ajeno = {self.CLAVE: dict(self.INDICE[self.CLAVE], sha256="2" * 64)}
        self.assertEqual("release", self._loc(indice=ajeno)["source"])

    def test_default_index_is_valid_and_well_formed(self):
        raw = (Path(__file__).resolve().parents[1] / "orchestracion/almacen_m06_r2.json").read_text(encoding="utf-8")
        idx = json.loads(raw)
        self.assertEqual("ddd.almacen-m06-r2/1.0", idx["schema"])
        for k, e in idx["objetos"].items():
            self.assertTrue(k.startswith("arc-p/m06/"), k)
            self.assertRegex(e["sha256"], r"^[0-9a-f]{64}$")
        # los ids viejos de territorio los vigila tests.test_t220_renombrado sobre todo el repositorio
        self.assertEqual({}, {k: e for k, e in idx["objetos"].items() if not e.get("run_id") or not e.get("artifact_name")})


class AlmacenArchivoTests(unittest.TestCase):
    def test_sin_assets_falla(self):
        from herramientas.almacen_m06_r2 import archivar
        with tempfile.TemporaryDirectory() as tmp:
            objs, fallos = archivar(REPO, Path(tmp), api=lambda p: [], r2_sha=lambda k: None, r2_subir=lambda *a: None)
        self.assertEqual(({}, 1), (objs, fallos))

    def test_archiva_verifica_y_es_idempotente(self):
        from herramientas.almacen_m06_r2 import archivar, indexar, clave
        rel = [_release(), {"tag_name": "viewer-x-1", "assets": [{"id": 9, "name": "a-1.zip", "digest": "sha256:" + "3" * 64}]}]
        subidos, remoto = [], {}
        def subir(k, z, h): subidos.append(k); remoto[k] = h
        with tempfile.TemporaryDirectory() as tmp:
            kw = dict(api=lambda p: rel, download=lambda p, t, r: t.write_bytes(PAYLOAD),
                      r2_sha=remoto.get, r2_subir=subir, ahora=lambda: "2026-11-14T00:00:00Z")
            objs, fallos = archivar(REPO, Path(tmp), **kw)
            k = clave(f"{NAME}-12779789644.zip", SHA)
            self.assertEqual(([k], 0), (subidos, fallos))
            self.assertEqual(SHA, objs[k]["sha256"])
            self.assertEqual(str(RUN), objs[k]["run_id"])
            archivar(REPO, Path(tmp), **kw)
            self.assertEqual([k], subidos)  # sin resubida
            idx = Path(tmp) / "idx.json"
            self.assertEqual(1, indexar(Path(tmp) / "ARCHIVO_ALMACEN_M06.json", idx))
            self.assertEqual({k}, set(json.loads(idx.read_text())["objetos"]))

    def test_bytes_distintos_del_digest_no_se_suben(self):
        from herramientas.almacen_m06_r2 import archivar
        subidos = []
        with tempfile.TemporaryDirectory() as tmp:
            objs, fallos = archivar(REPO, Path(tmp), api=lambda p: [_release()],
                                    download=lambda p, t, r: t.write_bytes(b"otro"), r2_sha=lambda k: None,
                                    r2_subir=lambda *a: subidos.append(a))
        self.assertEqual(({}, 1, []), (objs, fallos, subidos))


if __name__ == "__main__":
    unittest.main()


class PuertaValidacionWorkflowTests(unittest.TestCase):
    def test_gate_falls_back_to_release_only_with_accredited_digest(self):
        import yaml
        wf = yaml.safe_load((Path(__file__).resolve().parents[1]
                             / ".github/workflows/_reutilizable-puerta-validacion.yml").read_text(encoding="utf-8"))
        run = next(step["run"] for job in wf["jobs"].values() for step in job["steps"]
                   if "herramientas.validar_puerta_ejecucion" in str(step.get("run", "")))
        fallback = run.index("herramientas.localizar_artefacto_durable")
        guard = run.rindex('"$expected" =~ ^[0-9a-f]{64}$', 0, fallback)
        self.assertLess(guard, fallback)
        self.assertIn('--sha256 "$expected"', run)
        self.assertIn('[[ "$from_release" == true ]] || emit_blocked "Falta certificación $audit_name" 43', run)
        self.assertIn("ni en Actions ni en su release durable", run)
