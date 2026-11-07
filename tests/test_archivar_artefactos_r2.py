"""
PROYECTO: Diputado de Distrito
PRUEBA: archivista R2 (T-47) con catálogo sintético y R2 simulado
VERSIÓN: 1.1.0
FECHA: 2026-11-07
CAMBIOS: 1.1.0 (T-72): solo productos finales M06/M08 y auditorías; M06 omitido si vive su M08.
ANTERIOR: ninguna (fichero nuevo; 1.0.0 sin copia en legacy)
"""
import importlib.util
import json
import tempfile
import unittest
import urllib.error
from unittest import mock
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("arc", ROOT / "herramientas/archivar_artefactos_r2.py")
arc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(arc)


def art(i, nombre, expira, expired=False):
    return {"id": i, "name": nombre, "expired": expired, "expires_at": expira, "size_in_bytes": 3,
            "workflow_run": {"id": int(nombre.split("-")[2]) if nombre.split("-")[2].isdigit() else 0}}


class R2Falso:
    def __init__(self):
        self.objs = {}
        self.subidas = 0

    def sha(self, k):
        return self.objs.get(k)

    def subir(self, k, ruta, h):
        self.subidas += 1
        self.objs[k] = h


class Archivista(unittest.TestCase):
    def setUp(self):
        self.td = tempfile.TemporaryDirectory()
        self.root = Path(self.td.name)
        (self.root / "orchestracion").mkdir()
        (self.root / arc.CATALOGO).write_text(json.dumps({"t": {"cantabria": {
            "territory_id": "cantabria",
            "x": {"artifact_name": "ddd-state-41037133327-M06"},
            "y": {"artifact_name": "ddd-audit-41037133327"}}}}))
        (self.root / arc.VISOR).write_text(json.dumps({"products": [
            {"id": "m", "run_id": "41037133327", "territory_id": "cantabria"},
            {"id": "s", "territory_id": "aragon"}]}))
        self.vivos = [
            art(2, "ddd-state-41037133327-M06", "2026-11-20T00:00:00Z"),
            art(1, "ddd-state-41037133327-M05", "2026-11-13T00:00:00Z"),
            art(3, "ddd-audit-41037133327", "2026-11-15T00:00:00Z"),
            art(4, "ddd-state-99999999999-M05", "2026-11-12T00:00:00Z"),  # no referenciado
            art(5, "ddd-state-41037133327-M08", "2026-11-01T00:00:00Z", expired=True),
        ]
        self.r2 = R2Falso()
        self.man = {"artefactos": {}}

    def tearDown(self):
        self.td.cleanup()

    def correr(self, **kw):
        n, r = arc.referencias(self.root)
        return arc.archivar(self.vivos, n, r, self.man, lambda a, p: p.write_bytes(b"zip" + str(a["id"]).encode()),
                            self.r2.sha, self.r2.subir, "bkt", ahora=lambda: "2026-11-07T00:00:00Z", **kw)

    def test_referencias_y_prioridad(self):
        n, r = arc.referencias(self.root)
        sel = arc.seleccionar(self.vivos, n, r)
        self.assertEqual([a["name"] for a in sel],
                         ["ddd-audit-41037133327", "ddd-state-41037133327-M06"])  # sin M05 (T-72)
        self.assertEqual(arc.clave(sel[1]), "cantabria/41037133327/ddd-state-41037133327-M06.zip")

    def test_archiva_y_manifiesto(self):
        res = self.correr()
        self.assertEqual(len(res["archivados"]), 2)
        e = self.man["artefactos"]["cantabria/41037133327/ddd-state-41037133327-M06.zip"]
        self.assertEqual(e["url"], "r2://bkt/cantabria/41037133327/ddd-state-41037133327-M06.zip")
        self.assertEqual(e["caducidad_original"], "2026-11-20T00:00:00Z")
        self.assertEqual(len(e["sha256"]), 64)
        self.assertEqual(e["tamano_bytes"], 4)
        self.assertEqual(set(self.r2.objs.values()), {x['sha256'] for x in self.man['artefactos'].values()})

    def test_idempotente(self):
        self.correr()
        res = self.correr()
        self.assertEqual(self.r2.subidas, 2)
        self.assertEqual(len(res["ya_archivados"]), 2)
        self.assertEqual(res["archivados"], [])

    def test_no_resube_mismo_sha(self):
        self.correr()
        self.man["artefactos"].clear()  # manifiesto perdido, R2 conserva los objetos
        res = self.correr()
        self.assertEqual(self.r2.subidas, 2)
        self.assertEqual(len(res["sin_cambios_r2"]), 2)

    def test_caduca_antes_y_maximo(self):
        res = self.correr(caduca_antes="2026-11-16")
        self.assertEqual(len(res["archivados"]), 1)
        res = self.correr(maximo=1)
        self.assertEqual(len(res["archivados"]), 1)

    def test_error_no_registra_y_perdidos(self):
        n, r = arc.referencias(self.root)
        n["ddd-state-41037133327-M04"] = "cantabria"
        n["ddd-state-41037133328-M06"] = "cantabria"

        def falla(a, p):
            raise RuntimeError("red")

        res = arc.archivar(self.vivos, n, r, self.man, falla, self.r2.sha, self.r2.subir, "bkt")
        self.assertEqual(len(res["errores"]), 2)
        self.assertEqual(self.man["artefactos"], {})
        self.assertIn("ddd-state-41037133328-M06", res["perdidos"])
        self.assertNotIn("ddd-state-41037133327-M04", res["perdidos"])  # intermedio: no se archiva

    def test_m06_omitido_si_vive_su_m08(self):
        self.vivos[4] = art(5, "ddd-state-41037133327-M08", "2026-11-21T00:00:00Z")
        n, r = arc.referencias(self.root)
        self.assertEqual([a["name"] for a in arc.seleccionar(self.vivos, n, r)],
                         ["ddd-audit-41037133327", "ddd-state-41037133327-M08"])
        self.assertTrue(arc.cubierto_por_m08("ddd-state-41037133327-M06",
                                             {"k": {"artefacto": "ddd-state-41037133327-M08"}}))
        self.assertTrue(arc.cubierto_por_m08("ddd-state-1111111111-M06",
                                             {"k": {"artefacto": "ddd-state-41037133327-M08", "incluye_m06_run": "1111111111"}}))

    def test_guardar_manifiesto_solo_si_cambia(self):
        ruta = self.root / arc.MANIFIESTO
        self.correr()
        self.assertTrue(arc.guardar_manifiesto(ruta, self.man))
        self.man["actualizado_en"] = "otra"
        self.assertFalse(arc.guardar_manifiesto(ruta, self.man))


class Reintentos(unittest.TestCase):
    def setUp(self):
        self.esperas = []
        p = mock.patch.object(arc, "_dormir", self.esperas.append)
        p.start()
        self.addCleanup(p.stop)

    def e500(self):
        return urllib.error.HTTPError("u", 500, "Internal Server Error", {}, None)

    def test_500_transitorio_se_reintenta_con_backoff(self):
        llamadas = []

        def f():
            llamadas.append(1)
            if len(llamadas) < 4:
                raise self.e500()
            return "ok"

        self.assertEqual(arc.con_reintentos(f, "x"), "ok")
        self.assertEqual(self.esperas, [2, 4, 8])

    def test_agota_intentos(self):
        def f():
            raise self.e500()

        with self.assertRaises(urllib.error.HTTPError):
            arc.con_reintentos(f, "x")
        self.assertEqual(self.esperas, [2, 4, 8, 16, 32])

    def test_4xx_no_se_reintenta(self):
        def f():
            raise urllib.error.HTTPError("u", 404, "nf", {}, None)

        with self.assertRaises(urllib.error.HTTPError):
            arc.con_reintentos(f, "x")
        self.assertEqual(self.esperas, [])

    def test_listado_gh_sobrevive_a_un_500(self):
        respuestas = [self.e500(), mock.MagicMock()]
        resp = respuestas[1]
        resp.__enter__.return_value = resp
        resp.read.return_value = json.dumps({"artifacts": [{"id": 1}]}).encode()

        def abrir(req, timeout=0):
            r = respuestas.pop(0)
            if isinstance(r, Exception):
                raise r
            return r

        with mock.patch.object(arc.urllib.request, "urlopen", abrir):
            self.assertEqual(arc.listar_artefactos_gh("o/r", "t"), [{"id": 1}])
        self.assertEqual(self.esperas, [2])


if __name__ == "__main__":
    unittest.main()
