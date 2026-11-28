"""T-430 paso 2 (D-193/D-194): `herramientas/publicar_sitio_r2.py` sube la web (sin datos) al bucket del sitio, páginas al final, índice
al final y borrado con guarda."""
import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import yaml

from herramientas import publicar_sitio_r2 as s
from herramientas.publicar_datos_web import DatosWebError


class R2Falso:
    def __init__(self, corromper=None):
        self.obj, self.escritos, self.borrados, self.corromper = {}, [], [], corromper

    def leer(self, clave):
        return self.obj.get(clave)

    def escribir(self, clave, origen, cache):
        b = Path(origen).read_bytes()
        self.obj[clave] = b"X" if clave == self.corromper else b
        self.escritos.append(clave)

    def borrar(self, clave):
        self.borrados.append(clave)
        self.obj.pop(clave, None)


FICHEROS = {"index.html": b"<html>portada", "comprender.html": b"<html>c", "styles.css": b"body{}", "app.js": b"1",
            "assets/congreso.webp": b"img", "mapa/index.html": b"<html>m", "mapa/explorar.js": b"2", "mapa/datos.json": b'{"actual":""}',
            "docs/metodo.html": b"<html>d", "v4/index.html": b"<html>r", "congreso/data/24.geojson": b"{}",  # piloto opt-in: web
            # datos: no van al sitio (los sirve datos.)
            "datos/INDEX.json": b"{}", "datos/nac01/distritos.geojson": b"{}", "mapa/datos/INDEX.json": b"{}", "v2/datos/provincias.json": b"[]",
            "data/viewer-results.json": b"{}"}


class SitioR2(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.TemporaryDirectory()
        self.s = Path(self.d.name)
        for r, b in FICHEROS.items():
            (self.s / r).parent.mkdir(parents=True, exist_ok=True)
            (self.s / r).write_bytes(b)

    def tearDown(self):
        self.d.cleanup()

    def test_sin_datos_paginas_al_final_e_indice_ultimo(self):
        r2 = R2Falso()
        idx = s.publicar(self.s, r2, "7")
        self.assertEqual(set(idx["ficheros"]), {r for r in FICHEROS if not s.es_dato(r)})
        self.assertNotIn("mapa/datos.json", [r for r in FICHEROS if s.es_dato(r)])  # el fichero de configuración sí es de la web
        self.assertEqual(r2.escritos[-1], "_sitio/actual.json")
        html = [i for i, k in enumerate(r2.escritos[:-1]) if k.endswith(".html")]
        otros = [i for i, k in enumerate(r2.escritos[:-1]) if not k.endswith(".html")]
        self.assertLess(max(otros), min(html), "las páginas HTML se suben al final")
        self.assertFalse(any(s.es_dato(k) for k in r2.obj))

    def test_solo_sube_lo_que_cambia_y_borra_lo_que_sale(self):
        r2 = R2Falso()
        s.publicar(self.s, r2, "1")
        n = len(r2.escritos)
        (self.s / "comprender.html").write_bytes(b"<html>c2")
        (self.s / "app.js").unlink()
        s.publicar(self.s, r2, "2")
        self.assertEqual(r2.escritos[n:], ["comprender.html", "_sitio/actual.json"])
        self.assertEqual(r2.borrados, ["app.js"])

    def test_sin_portada_no_publica(self):
        (self.s / "index.html").unlink()
        r2 = R2Falso()
        with self.assertRaises(DatosWebError):
            s.publicar(self.s, r2, "1")
        self.assertEqual(r2.escritos, [])

    def test_borrado_masivo_y_claves_no_validas_abortan_sin_tocar_nada(self):
        r2 = R2Falso()
        idx = s.publicar(self.s, r2, "1")
        previo = dict(r2.obj)
        idx["ficheros"].update({f"viejo/{i}.html": "0" * 64 for i in range(60)})
        r2.obj["_sitio/actual.json"] = previo["_sitio/actual.json"] = json.dumps(idx).encode()
        with self.assertRaises(DatosWebError):
            s.publicar(self.s, r2, "2")
        self.assertEqual(r2.obj, previo)
        for mala in ("../x", "/x", "", "datos/INDEX.json", "v2/datos/x.json", "_sitio/actual.json", "a//b"):
            self.assertFalse(s.clave_valida(mala), mala)

    def test_borrado_a_medias_se_reintenta(self):
        r2 = R2Falso()
        s.publicar(self.s, r2, "1")
        (self.s / "app.js").unlink()
        (self.s / "styles.css").unlink()
        falla = {"styles.css"}

        def borrar(k):
            if k in falla:
                raise DatosWebError("R2_BORRADO: " + k)
            r2.obj.pop(k, None)
        r2.borrar = borrar
        with self.assertRaises(DatosWebError):
            s.publicar(self.s, r2, "2")
        self.assertIn("styles.css", json.loads(r2.obj["_sitio/actual.json"])["ficheros"])  # el índice viejo lo sigue listando
        falla.clear()
        s.publicar(self.s, r2, "3")
        self.assertNotIn("styles.css", r2.obj)

    def test_sha256_distinto_no_toca_indice_ni_borra(self):
        r2 = R2Falso()
        s.publicar(self.s, r2, "1")
        previo = r2.obj["_sitio/actual.json"]
        (self.s / "styles.css").write_bytes(b"body{color:red}")
        (self.s / "app.js").unlink()
        r2.corromper = "styles.css"
        with self.assertRaises(DatosWebError):
            s.publicar(self.s, r2, "2")
        self.assertEqual((r2.obj["_sitio/actual.json"], r2.borrados), (previo, []))

    def test_simular_no_escribe(self):
        r2 = R2Falso()
        s.publicar(self.s, r2, "1", simular=True)
        self.assertEqual(r2.escritos, [])

    def test_sin_bucket_nada_y_buckets_ajenos_rechazados(self):
        self.assertEqual(s.main(["--sitio", str(self.s), "--bucket", ""]), 0)
        with mock.patch.dict(os.environ, {"R2_BUCKET": "trabajo", "R2_WEB_BUCKET": "datos"}):
            self.assertEqual(s.main(["--sitio", str(self.s), "--bucket", "trabajo"]), 1)
            self.assertEqual(s.main(["--sitio", str(self.s), "--bucket", "datos"]), 1)


class PasoP40(unittest.TestCase):
    def test_paso_solo_main_con_secretos_propios(self):
        wf = yaml.safe_load((Path(__file__).resolve().parents[1] / ".github/workflows/p40-publicacion.yml").read_text(encoding="utf-8"))
        self.assertIn("github.ref == 'refs/heads/main'", wf["jobs"]["subir_r2"]["if"])  # T-510 (P40 1.8.0): job propio, solo main
        pasos = wf["jobs"]["subir_r2"]["steps"]
        nombres = [p.get("name") for p in pasos]
        p = pasos[nombres.index("Web en R2 (T-430)")]
        self.assertGreater(nombres.index("Web en R2 (T-430)"), nombres.index("Datos de la web en R2 (T-430)"))  # datos antes que la web
        self.assertIs(p.get("continue-on-error"), True)
        self.assertEqual(p["env"]["AWS_ACCESS_KEY_ID"], "${{ secrets.R2_SITIO_ACCESS_KEY_ID }}")
        self.assertEqual(p["env"]["R2_SITIO_BUCKET"], "${{ vars.R2_SITIO_BUCKET }}")
        self.assertEqual((p["env"]["R2_BUCKET"], p["env"]["R2_WEB_BUCKET"]), ("${{ vars.R2_BUCKET }}", "${{ vars.R2_WEB_BUCKET }}"))
        self.assertIn("publicar_sitio_r2.py --sitio /tmp/site-candidate", p["run"])
        datos = pasos[nombres.index("Datos de la web en R2 (T-430)")]
        self.assertEqual(datos.get("id"), "datos_web")
        self.assertEqual(p.get("if"), "${{ steps.datos_web.outcome == 'success' }}")  # sin datos, no se sube la web
        self.assertNotIn("--permitir-borrado", p["run"])


if __name__ == "__main__":
    unittest.main()
