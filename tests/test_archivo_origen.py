#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PROYECTO: Diputado de Distrito
COMPONENTE: prueba del archivo en origen (T-72)
VERSIÓN: 1.0.0 · FECHA: 2026-11-07 · ESTADO: candidato
ANTERIOR: ninguna (fichero nuevo)
FUNCIÓN: subida simulada a R2 con sha256 y anotación en el manifiesto (y fallo claro); composición del run validada
  contra su GeoJSON M06 (y rechazo si no cuadra); votos por partido del run M08; check rojo/verde de los M06 publicados
  sin copia en R2 ni composición, y el check real sobre el repositorio con la lista de excepciones de T-71.
"""
import io
import json
import shutil
import sys
import tempfile
import unittest
import unittest.mock
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "herramientas"))
sys.path.insert(0, str(ROOT / "tests"))
import archivo_origen as ao  # noqa: E402
import archivar_artefactos_r2 as ar  # noqa: E402
import test_resultados_partidos as trp  # noqa: E402


def _estado(dirn: Path, comp: str, dist_info: dict) -> Path:
    """Estado M06 descomprimido como lo deja `gh run download`: cache/ con composición y GeoJSON."""
    (dirn / "cache").mkdir(parents=True)
    (dirn / "cache" / "t_m06_composicion_distritos.csv").write_text(comp)
    z = zipfile.ZipFile(io.BytesIO(trp.m06_zip(dist_info)))
    (dirn / "cache" / "t_m06_distritos.geojson").write_bytes(z.read(z.namelist()[0]))
    return dirn


class R2(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.root)
        self.subidas = {}
        self.art = {"id": 99, "name": "ddd-state-123456789-M06", "expires_at": "2026-11-21T00:00:00Z",
                    "workflow_run": {"id": 123456789}}

    def _desc(self, a, destino):
        destino.write_bytes(b"zip-bytes")

    def test_sube_y_anota_sha256(self):
        e = ao.archivar_uno(self.art, "nac22", self.root, self._desc, lambda k: None,
                            lambda k, p, h: self.subidas.__setitem__(k, h), "b")
        k = "congreso_huesca/123456789/ddd-state-123456789-M06.zip"
        self.assertEqual(self.subidas, {k: ar.hashlib.sha256(b"zip-bytes").hexdigest()})
        self.assertEqual(e["sha256"], self.subidas[k])
        man = json.loads((self.root / ar.MANIFIESTO).read_text())
        self.assertEqual(man["artefactos"][k]["url"], f"r2://b/{k}")
        self.assertEqual(man["artefactos"][k]["run_id"], "123456789")

    def test_fallo_de_subida_es_error(self):
        def falla(k, p, h):
            raise RuntimeError("R2 caído")
        with self.assertRaisesRegex(ValueError, "R2 caído"):
            ao.archivar_uno(self.art, "nac22", self.root, self._desc, lambda k: None, falla, "b")
        self.assertFalse((self.root / ar.MANIFIESTO).exists())

    def test_sin_credenciales_falla_claro(self):
        env = {k: "" for k in ("R2_BUCKET", "R2_ACCOUNT_ID", "AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY")}
        with unittest.mock.patch.dict(ao.os.environ, {"GITHUB_REPOSITORY": "r", "GITHUB_TOKEN": "t", **env}), \
                unittest.mock.patch("sys.stdout", new=io.StringIO()) as out:
            rc = ao.main(["--root-dir", str(self.root), "r2", "--run-id", "1", "--artefacto", "x", "--territorio", "t"])
        self.assertEqual(rc, 1)
        self.assertIn("ARCHIVO_R2_FAILED", out.getvalue())


class SustituyeM06(unittest.TestCase):
    def test_m08_retira_su_m06(self):
        root = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, root)
        d = lambda a, p: p.write_bytes(a["name"].encode())
        for n in ("ddd-state-555555555-M06", "ddd-state-666666666-M08"):
            ao.archivar_uno({"id": n, "name": n, "workflow_run": {"id": int(n.split("-")[2])}}, "t", root, d,
                            lambda k: None, lambda k, p, h: None, "b")
        borrados = []
        r = ao.retirar_m06("555555555", "t/666666666/ddd-state-666666666-M08.zip", root, borrados.append)
        self.assertEqual(r, borrados)
        self.assertEqual(borrados, ["t/555555555/ddd-state-555555555-M06.zip"])
        man = json.loads((root / ar.MANIFIESTO).read_text())["artefactos"]
        self.assertEqual(list(man), ["t/666666666/ddd-state-666666666-M08.zip"])
        self.assertEqual(man["t/666666666/ddd-state-666666666-M08.zip"]["incluye_m06_run"], "555555555")

    def test_fallo_al_retirar_conserva_entrada(self):
        root = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, root)
        d = lambda a, p: p.write_bytes(a["name"].encode())
        for n in ("ddd-state-555555555-M06", "ddd-state-666666666-M08"):
            ao.archivar_uno({"id": n, "name": n, "workflow_run": {"id": int(n.split("-")[2])}}, "t", root, d,
                            lambda k: None, lambda k, p, h: None, "b")

        def falla(k):
            raise RuntimeError("x")
        with unittest.mock.patch("sys.stdout", new=io.StringIO()):
            self.assertEqual(ao.retirar_m06("555555555", "t/666666666/ddd-state-666666666-M08.zip", root, falla), [])
        self.assertEqual(len(json.loads((root / ar.MANIFIESTO).read_text())["artefactos"]), 2)


class Composicion(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.root)

    def test_escribe_composicion_del_run(self):
        est = _estado(self.root / "est", trp.COMP, {0: (2, 500), 1: (2, 400)})
        e = ao.escribir_composicion(est, "nac22", "77", self.root)
        ruta = self.root / "datos/composicion/runs/congreso_huesca_77.csv"
        self.assertEqual(ruta.read_text().splitlines()[:2], ["seccion,distrito,poblacion", "2200101001,0,300"])
        man = json.loads((self.root / "datos/composicion/MANIFEST.json").read_text())
        self.assertEqual(man["runs"]["congreso_huesca/77"], e)
        self.assertEqual(e["secciones"], 4)
        self.assertEqual(e["sha256_csv"], ao.cm.sha256(ruta.read_bytes()))

    def _registro(self, run):
        reg = self.root / ao.cm.REGISTRO_VISOR.relative_to(ao.cm.ROOT)
        reg.parent.mkdir(parents=True, exist_ok=True)
        reg.write_text(json.dumps({"products": [{"kind": "canonical_m06", "territory_id": "nac22", "run_id": run,
                                                  "blob_sha": "b" * 40, "sha256": "c" * 64}]}))

    def test_run_vigente_se_promueve_a_canonico(self):
        self._registro("77")
        est = _estado(self.root / "est", trp.COMP, {0: (2, 500), 1: (2, 400)})
        e = ao.escribir_composicion(est, "nac22", "77", self.root)
        canon = self.root / "datos/composicion/congreso_huesca.csv"
        self.assertEqual(canon.read_bytes(), (self.root / e["ruta"]).read_bytes())
        t = json.loads((self.root / "datos/composicion/MANIFEST.json").read_text())["territorios"]["nac22"]
        self.assertEqual(t, {"run_id": "77", "blob_sha": "b" * 40, "sha256_m06": "c" * 64, "secciones": 4, "sha256_csv": e["sha256_csv"]})
        self.assertFalse(ao.promover_canonica("nac22", "77", self.root))  # idempotente

    def test_run_no_vigente_no_toca_el_canonico(self):
        self._registro("99")
        est = _estado(self.root / "est", trp.COMP, {0: (2, 500), 1: (2, 400)})
        ao.escribir_composicion(est, "nac22", "77", self.root)
        self.assertFalse((self.root / "datos/composicion/congreso_huesca.csv").exists())

    def test_csv_archivado_alterado_no_se_promueve(self):
        self._registro("77")
        est = _estado(self.root / "est", trp.COMP, {0: (2, 500), 1: (2, 400)})
        e = ao.escribir_composicion(est, "nac22", "77", self.root)
        (self.root / "datos/composicion/congreso_huesca.csv").unlink()
        (self.root / e["ruta"]).write_text("seccion,distrito,poblacion\n2200101001,0,1\n")
        with self.assertRaises(ValueError):
            ao.promover_canonica("nac22", "77", self.root)
        self.assertFalse((self.root / "datos/composicion/congreso_huesca.csv").exists())

    def test_no_cuadra_no_escribe(self):
        est = _estado(self.root / "est", trp.COMP, {0: (2, 500), 1: (3, 400)})
        with self.assertRaises(ValueError):
            ao.escribir_composicion(est, "nac22", "77", self.root)
        self.assertFalse((self.root / "datos/composicion").exists())


class Partidos(trp.Base):
    def test_votos_del_run_m08(self):
        root = self.d / "repo"
        ao.escribir_composicion(_estado(self.d / "est6", trp.COMP, {0: (2, 500), 1: (2, 400)}), "nac22", "77", root)
        est8 = self.d / "est8"
        est8.mkdir()
        z = zipfile.ZipFile(io.BytesIO(self.m08))
        (est8 / "m08.geojson").write_bytes(z.read(z.namelist()[0]))
        e = ao.escribir_partidos(est8, "nac22", "88", "77", root, self.zip, self.contratos)
        lineas = (root / e["ruta"]).read_text().splitlines()
        self.assertEqual(lineas[1], "0,PP,60,54.5455,3,1,160")
        man = json.loads((root / "datos/resultados/MANIFEST.json").read_text())
        self.assertEqual(man["partidos_runs"]["congreso_huesca/88"]["run_territorial"], "77")
        # T-90: el estado real trae el M08 como *.geojson.zip, sin .geojson suelto
        est8z = self.d / "est8z"
        est8z.mkdir()
        (est8z / "t_m08_distritos_resultados.geojson.zip").write_bytes(self.m08)
        self.assertEqual(ao.ganadores_m08(est8z), ao.ganadores_m08(est8))
        # sin composición del run territorial: se omite
        self.assertIsNone(ao.escribir_partidos(est8, "nac22", "88", "66", root, self.zip, self.contratos))


class Comprobar(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.root)
        (self.root / "orchestracion").mkdir()
        prods = [{"kind": "canonical_m06", "territory_id": t, "run_id": r, "blob_sha": "b", "sha256": "s"}
                 for t, r in (("a", "10"), ("b", "20"), ("c", "30"), ("c", "5"), ("d", "40"))]
        (self.root / "orchestracion/publicaciones_visor.json").write_text(json.dumps({"products": prods}))
        (self.root / "orchestracion/archivo_r2.json").write_text(json.dumps({"artefactos": {
            "a/10/ddd-state-10-M06.zip": {"artefacto": "ddd-state-10-M06", "territorio": "a", "run_id": "10"},
            "c/5/ddd-state-5-M06.zip": {"artefacto": "ddd-state-5-M06", "territorio": "c", "run_id": "5"},
            "d/41/ddd-state-41-M08.zip": {"artefacto": "ddd-state-41-M08", "territorio": "d", "run_id": "41",
                                          "incluye_m06_run": "40"}}}))
        (self.root / "datos/composicion/runs").mkdir(parents=True)
        (self.root / "datos/composicion/runs/b_20.csv").write_text("x")
        (self.root / "datos/composicion/MANIFEST.json").write_text(json.dumps({"territorios": {}, "runs": {
            "b/20": {"territorio": "b", "run_id": "20", "ruta": "datos/composicion/runs/b_20.csv"}}}))

    def test_rojo_si_falta_y_verde_con_excepcion(self):
        self.assertEqual(ao.comprobar(self.root)["faltan"], ["c"])  # c publica el run 30; R2 solo tiene el 5
        (self.root / "configuracion").mkdir()
        (self.root / ao.EXCEPCIONES).write_text(json.dumps({"territorios": ["c", "a"]}))
        r = ao.comprobar(self.root)
        self.assertEqual(r, {"faltan": [], "sobran_excepciones": ["a"]})


class RepositorioReal(unittest.TestCase):
    def test_m06_publicados_archivados_o_exceptuados(self):
        """Check de CI: todo M06 publicado tiene copia en R2 o composición en git, salvo las excepciones de T-71."""
        r = ao.comprobar(ROOT)
        self.assertEqual(r["faltan"], [], "M06 publicados sin R2 ni composición: " + ", ".join(r["faltan"]))


if __name__ == "__main__":
    unittest.main()
