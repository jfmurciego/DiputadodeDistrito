# -*- coding: utf-8 -*-
"""T-462: imagen de cada distrito (P18 de Wikidata del municipio, licencia comprobada en Commons, WebP 800 px, R2).

PROYECTO: Diputado de Distrito
VERSIÓN: 1.2.0 · FECHA: 2026-11-26 · ESTADO: candidato
ANTERIOR: legacy/tests/test_t462_imagenes_distritos_v1.1.0_20261126.py
CAMBIOS: 1.2.0: T-508 (revisión de #1036): rechazo de fichas de otra versión, territorio o configuración, elección del artefacto previo con más de 100 artefactos (nombre, rama, caducidad, digest), `subir` se niega con catálogo incompleto y el paso de reanudar verifica el digest. 1.1.0: T-508: progreso, reanudación, presupuesto, plazo por petición y paso de reanudar del workflow. 1.0.0: fichero nuevo.
MOTIVO: sin red; la red se simula con respuestas sintéticas con la forma de las de Wikidata y Commons. Cifras de los distritos: T-458 §3.1.
"""
from __future__ import annotations

import importlib.util
import io
import json
import os
import re
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "herramientas"))
sys.path.insert(0, str(ROOT))
import imagenes_distritos as im  # noqa: E402

HAY_PIL = importlib.util.find_spec("PIL") is not None  # la imagen de CI no lo trae; el paso de P10 lo instala
SIN_PIL = unittest.skipUnless(HAY_PIL, "requiere Pillow")
import rutas_r2  # noqa: E402


def _png(ancho: int, alto: int, modo: str = "RGB") -> bytes:
    from PIL import Image

    b = io.BytesIO()
    Image.new(modo, (ancho, alto), (200, 30, 30, 128) if modo == "RGBA" else (200, 30, 30)).save(b, "PNG")
    return b.getvalue()


class Municipios(unittest.TestCase):
    def test_407_distritos_y_295_municipios(self):  # cifras del diseño T-458 §3.1
        d, m = im.leer_distritos()
        self.assertEqual((len(d), len(m)), (407, 295))
        self.assertEqual(m["22125"], "Huesca")

    def test_codigo_ine_mal_formado_falla(self):
        with tempfile.TemporaryDirectory() as t:
            (Path(t) / "nombres_congreso_x.csv").write_text(
                "territorio,district_id,municipio_principal_codigo,municipio_principal\nnac22,0,2215,Huesca\n", encoding="utf-8")
            with self.assertRaises(im.ErrorImagenes) as c:
                im.leer_distritos(Path(t))
            self.assertEqual(c.exception.codigo, "IMG_CODIGO_INE")


class Wikidata(unittest.TestCase):
    def test_nombre_de_fichero(self):
        self.assertEqual(im.nombre_fichero("http://commons.wikimedia.org/wiki/Special:FilePath/Vitoria%20-_Panor%C3%A1mica_01.jpg"),
                         "Vitoria - Panorámica 01.jpg")

    def test_rango_preferente_gana_y_desaprobado_se_ignora(self):
        def f(code, item, img=None, rank=None):
            d = {"code": {"value": code}, "item": {"value": "http://www.wikidata.org/entity/" + item}}
            if img:
                d["img"] = {"value": "http://commons.wikimedia.org/wiki/Special:FilePath/" + img}
                d["rank"] = {"value": "http://wikiba.se/ontology#" + rank}
            return d
        r = im.elegir_imagenes([f("22125", "Q1", "A.jpg", "NormalRank"), f("22125", "Q1", "B.jpg", "PreferredRank"),
                                f("22125", "Q1", "C.jpg", "DeprecatedRank"), f("01059", "Q2"), f("02003", "Q3", "D.jpg", "DeprecatedRank")])
        self.assertEqual(r["22125"], {"qid": "Q1", "fichero": "B.jpg"})
        self.assertEqual(r["01059"], {"qid": "Q2", "fichero": None})
        self.assertEqual(r["02003"]["fichero"], None)

    def test_consulta_lleva_los_codigos_entre_comillas(self):
        self.assertIn('VALUES ?code { "22125" "01059" }', im.consulta_sparql(["22125", "01059"]))


class Licencias(unittest.TestCase):
    def _c(self, corta, **extra):
        return im.clasificar_licencia({"LicenseShortName": {"value": corta}, **{k: {"value": v} for k, v in extra.items()}})

    def test_permitidas_y_no(self):
        casos = {"CC0": "CC0 / dominio público", "Public domain": "CC0 / dominio público", "PD": "CC0 / dominio público",
                 "CC BY 4.0": "CC BY", "CC BY 2.0 de": "CC BY", "CC BY-SA 3.0": "CC BY-SA", "CC-BY-SA-4.0": "CC BY-SA",
                 "CC BY-NC 2.0": None, "CC BY-ND 2.0": None, "CC BY-NC-SA 3.0": None, "GFDL": None, "Copyrighted free use": None, "": None}
        for corta, esperado in casos.items():
            self.assertEqual(self._c(corta), esperado, corta)

    def test_nonfree_se_rechaza(self):
        self.assertIsNone(self._c("CC BY 4.0", NonFree="true"))

    def test_autor_solo_texto(self):  # T-325: el HTML de los metadatos no se conserva
        t = im.texto_plano('<a href="x">Ana</a> <img src=x onerror=alert(1)> &amp; Luis')
        self.assertEqual(t, "Ana & Luis")
        self.assertNotIn("<", t)

    def test_ficha_atribucion(self):
        info = {"mime": "image/jpeg", "titulo_final": "A.jpg", "descriptionurl": "https://commons.wikimedia.org/wiki/File:A.jpg",
                "sha1": "ab", "thumburl": "https://upload.wikimedia.org/x.jpg",
                "extmetadata": {"LicenseShortName": {"value": "CC BY 4.0"}, "Artist": {"value": "<b>Ana</b>"}, "LicenseUrl": {"value": "https://cc/by"}}}
        f = im.ficha(info)
        self.assertEqual((f["licencia"], f["autor"], f["atribucion_obligatoria"]), ("CC BY", "Ana", True))
        info["extmetadata"]["LicenseShortName"]["value"] = "CC0"
        self.assertFalse(im.ficha(info)["atribucion_obligatoria"])
        info["extmetadata"]["LicenseShortName"]["value"] = "CC BY-NC 4.0"
        self.assertIn("licencia no permitida", im.ficha(info))
        info["extmetadata"]["LicenseShortName"]["value"] = "CC0"
        info["mime"] = "application/pdf"
        self.assertIn("tipo no admitido", im.ficha(info))


@SIN_PIL
class Webp(unittest.TestCase):
    def test_reescala_a_800(self):
        b, w, h, cambios = im.a_webp(_png(1600, 900))
        self.assertEqual((w, h), (800, 450))
        self.assertEqual(b[:4] + b[8:12], b"RIFFWEBP")
        self.assertIn("reescalada a 800 px de ancho", cambios)

    def test_pequena_no_se_amplia_y_alfa_sobre_blanco(self):
        b, w, h, cambios = im.a_webp(_png(400, 200, "RGBA"))
        self.assertEqual((w, h), (400, 200))
        self.assertIn("transparencia sobre fondo blanco", cambios)

    def test_host_no_permitido(self):
        for u in ("https://example.com/x.jpg", "http://upload.wikimedia.org/x.jpg", "https://evil.upload.wikimedia.org.example.com/x"):
            with self.assertRaises(im.ErrorImagenes) as c:
                im._abrir(u)
            self.assertEqual(c.exception.codigo, "IMG_HOST")


def _red_falsa():
    """Wikidata/Commons sintéticos: 22125 CC0, 01059 CC BY-SA con autor malicioso, 02003 sin P18, 02081 con licencia NC."""
    def fila(code, item, img=None):
        d = {"code": {"value": code}, "item": {"value": "http://www.wikidata.org/entity/" + item}}
        if img:
            d["img"] = {"value": "http://commons.wikimedia.org/wiki/Special:FilePath/" + img}
            d["rank"] = {"value": "http://wikiba.se/ontology#NormalRank"}
        return d
    wd = {"results": {"bindings": [fila("22125", "Q1", "Huesca.jpg"), fila("01059", "Q2", "Vitoria.jpg"), fila("02003", "Q3"),
                                   fila("02081", "Q4", "Albacete.jpg")]}}

    def pag(t, lic, artista, url):
        return {"title": "File:" + t, "imageinfo": [{"mime": "image/png", "sha1": "s" + t, "thumburl": url, "url": url,
                "descriptionurl": "https://commons.wikimedia.org/wiki/File:" + t.replace(" ", "_"),
                "extmetadata": {"LicenseShortName": {"value": lic}, "Artist": {"value": artista}, "LicenseUrl": {"value": "https://cc/l"}}}]}
    cm = {"query": {"pages": [pag("Huesca.jpg", "CC0", "Ana", "https://upload.wikimedia.org/h.png"),
                              pag("Vitoria.jpg", "CC BY-SA 4.0", '<img src=x onerror=alert(1)>Luis', "https://upload.wikimedia.org/v.png"),
                              pag("Albacete.jpg", "CC BY-NC 2.0", "Eva", "https://upload.wikimedia.org/a.png")]}}
    img = {"https://upload.wikimedia.org/h.png": _png(1600, 900), "https://upload.wikimedia.org/v.png": _png(500, 300)}

    def abrir(url, datos=None, *a, **k):
        if "query.wikidata.org" in url:
            return json.dumps(wd).encode()
        if "commons.wikimedia.org" in url:
            return json.dumps(cm).encode()
        return img[url]
    return abrir


def _csv(d: Path):
    (d / "nombres_congreso_x.csv").write_text(
        "territorio,district_id,municipio_principal_codigo,municipio_principal\n"
        "nac22,0,22125,Huesca\nnac22,1,22125,Huesca\nnac01,0,01059,Vitoria\n"
        "nac02,0,02003,Albacete\nnac02,1,02081,Almansa\n", encoding="utf-8")


@SIN_PIL
class Descarga(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.t = tempfile.TemporaryDirectory()
        cls.d, cls.s = Path(cls.t.name) / "datos", Path(cls.t.name) / "salida"
        cls.d.mkdir()
        _csv(cls.d)
        cls.cat = im.descargar(cls.s, abrir=_red_falsa(), directorio=cls.d, pausa=0)

    @classmethod
    def tearDownClass(cls):
        cls.t.cleanup()

    def test_totales_y_motivos(self):
        self.assertEqual({k: self.cat["totales"][k] for k in ("distritos", "municipios", "con_imagen", "sin_imagen", "errores_descarga")},
                         {"distritos": 5, "municipios": 4, "con_imagen": 2, "sin_imagen": 2, "errores_descarga": 0})
        motivos = {s["municipio_codigo"]: s["motivo"] for s in self.cat["sin_imagen"]}
        self.assertEqual(motivos["02003"], "sin imagen P18 en Wikidata")
        self.assertTrue(motivos["02081"].startswith("licencia no permitida"))

    def test_imagen_guardada_y_catalogo(self):
        hu = next(i for i in self.cat["imagenes"] if i["municipio_codigo"] == "22125")
        b = (self.s / "img" / "22125.webp").read_bytes()
        self.assertEqual((hu["ancho"], hu["alto"], hu["bytes"], hu["sha256"], hu["licencia"], hu["atribucion_obligatoria"]),
                         (800, 450, len(b), im.sha256(b), "CC0 / dominio público", False))
        vi = next(i for i in self.cat["imagenes"] if i["municipio_codigo"] == "01059")
        self.assertEqual((vi["autor"], vi["licencia"], vi["atribucion_obligatoria"], vi["ancho"]), ("Luis", "CC BY-SA", True, 500))
        self.assertNotIn("url_imagen", vi)
        self.assertEqual(json.loads((self.s / "catalogo.json").read_text(encoding="utf-8")), self.cat)

    def test_hoja_de_contactos(self):
        h = (self.s / "hoja_contactos.html").read_text(encoding="utf-8")
        self.assertIn("img/22125.webp", h)
        self.assertIn("2 distrito(s)", h)  # Huesca sirve a dos distritos
        self.assertNotIn("<img src=x", h)  # el HTML del autor no entra
        self.assertIn("Sin imagen (2)", h)
        self.assertNotIn("http://", h.replace("https://", ""))  # sin recursos de terceros


class _Aws:
    def __init__(self, existentes=None):
        self.puestas, self.ex = [], dict(existentes or {})

    def __call__(self, args, capturar=False):
        clave = args[args.index("--key") + 1]
        if args[1] == "head-object":
            if clave not in self.ex:
                return subprocess.CompletedProcess(args, 254, "", "An error occurred (404) when calling the HeadObject: Not Found")
            return subprocess.CompletedProcess(args, 0, json.dumps({"Metadata": self.ex[clave]}), "")
        meta = dict(p.split("=") for p in args[args.index("--metadata") + 1].split(","))
        self.puestas.append((clave, meta))
        self.ex[clave] = meta
        return subprocess.CompletedProcess(args, 0, "", "")


@SIN_PIL
class Subida(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.env = mock.patch.dict(os.environ, {"R2_BUCKET": "prueba", "R2_ACCOUNT_ID": "x"})
        cls.env.start()
        cls.t = tempfile.TemporaryDirectory()
        cls.d, cls.s = Path(cls.t.name) / "datos", Path(cls.t.name) / "salida"
        cls.d.mkdir()
        _csv(cls.d)
        im.descargar(cls.s, abrir=_red_falsa(), directorio=cls.d, pausa=0)

    @classmethod
    def tearDownClass(cls):
        cls.env.stop()
        cls.t.cleanup()

    def test_claves_en_prefijo_propio_validas_y_manifiesto_ultimo(self):
        aws = _Aws()
        r = im.subir(self.s, aws=aws, run=50)
        claves = [c for c, _ in aws.puestas]
        self.assertEqual(claves, ["interno/imagenes-distritos/img/01059.webp", "interno/imagenes-distritos/img/22125.webp",
                                  "interno/imagenes-distritos/catalogo.json", "interno/imagenes-distritos/manifiesto.json"])
        for c in claves:
            self.assertEqual(rutas_r2.validar(c), [], c)
            self.assertFalse(c.startswith(("fuentes/", "mapas/")))
        self.assertTrue(all(m["run"] == "50" and len(m["sha256"]) == 64 for _, m in aws.puestas))
        self.assertEqual({p["r2"] for p in r["piezas"]}, {"subido"})

    def test_misma_huella_no_reescribe_y_run_mayor_falla(self):
        aws = _Aws()
        im.subir(self.s, aws=aws, run=50)
        n = len(aws.puestas)
        r = im.subir(self.s, aws=aws, run=51)
        self.assertEqual(len(aws.puestas), n + 1)  # solo el manifiesto cambia (lleva el run)
        self.assertEqual([p["r2"] for p in r["piezas"]].count("ya_estaba"), 3)
        otro = _Aws({"interno/imagenes-distritos/img/22125.webp": {"sha256": "0" * 64, "run": "99"}})
        with self.assertRaises(im.ErrorImagenes) as c:
            im.subir(self.s, aws=otro, run=50)
        self.assertEqual(c.exception.codigo, "IMG_RUN_MAYOR")
        self.assertFalse(any(k.endswith("manifiesto.json") for k, _ in otro.puestas))

    def test_huella_del_catalogo_se_comprueba(self):
        (self.s / "img" / "22125.webp").write_bytes(b"corrupto")
        try:
            with self.assertRaises(im.ErrorImagenes) as c:
                im.subir(self.s, aws=_Aws(), run=1)
            self.assertEqual(c.exception.codigo, "IMG_HUELLA")
        finally:
            im.descargar(self.s, abrir=_red_falsa(), directorio=self.d, pausa=0)


@SIN_PIL
class Reanudable(unittest.TestCase):  # T-508
    def setUp(self):
        self.t = tempfile.TemporaryDirectory()
        self.d, self.s = Path(self.t.name) / "datos", Path(self.t.name) / "salida"
        self.d.mkdir()
        _csv(self.d)

    def tearDown(self):
        self.t.cleanup()

    def test_progreso_con_recuento_y_tiempo(self):
        import contextlib

        b = io.StringIO()
        with contextlib.redirect_stdout(b):
            im.descargar(self.s, abrir=_red_falsa(), directorio=self.d, pausa=0, cada=2)
        lineas = [x for x in b.getvalue().splitlines() if x.startswith("IMAGENES_PROGRESO")]
        self.assertEqual([x.split()[1] for x in lineas], ["2/4", "4/4"])
        self.assertRegex(lineas[0], r"\d+s$")

    def test_presupuesto_agotado_deja_parcial_y_el_siguiente_run_continua(self):
        reloj = iter([0, 0, 0, 99, 99, 99, 99, 99, 99, 99, 99])  # t0, y luego pasado el presupuesto
        c1 = im.descargar(self.s, abrir=_red_falsa(), directorio=self.d, pausa=0, presupuesto_s=10, reloj=lambda: next(reloj))
        self.assertFalse(c1["completo"])
        self.assertTrue(c1["pendientes"])
        self.assertEqual(len(c1["imagenes"]) + len(c1["sin_imagen"]) + len(c1["pendientes"]), 4)
        hechos = {i["municipio_codigo"] for i in c1["imagenes"]}
        pedidas: list[str] = []
        base = _red_falsa()

        def espia(url, *a, **k):
            pedidas.append(url)
            return base(url, *a, **k)
        c2 = im.descargar(self.s, abrir=espia, directorio=self.d, pausa=0)
        self.assertTrue(c2["completo"])
        self.assertEqual(c2["totales"]["reanudados"], len(hechos))
        self.assertEqual((c2["totales"]["con_imagen"], c2["totales"]["sin_imagen"]), (2, 2))
        self.assertEqual(len([u for u in pedidas if "upload.wikimedia.org" in u]), 2 - len(hechos))  # lo ya bajado no se pide

    def test_webp_corrupto_se_vuelve_a_bajar(self):
        im.descargar(self.s, abrir=_red_falsa(), directorio=self.d, pausa=0)
        (self.s / "img" / "22125.webp").write_bytes(b"roto")
        c = im.descargar(self.s, abrir=_red_falsa(), directorio=self.d, pausa=0)
        self.assertEqual(c["totales"]["reanudados"], 1)
        self.assertEqual(im.sha256((self.s / "img" / "22125.webp").read_bytes()), next(i["sha256"] for i in c["imagenes"] if i["municipio_codigo"] == "22125"))

    def test_cuerpo_que_gotea_vence_por_plazo_total(self):
        class Gota:
            def read(self, n):
                return b"x"
        with self.assertRaises(TimeoutError):
            im._leer(Gota(), 10**9, time.monotonic() - 1)

    def test_user_agent_generico_y_reintentos_acotados(self):
        self.assertNotRegex(im.USER_AGENT, r"@|jfmurciego|DiputadodeDistrito|http")
        self.assertLessEqual(im.INTENTOS, 3)
        self.assertLessEqual(im.ESPERA_MAX, 30)


@SIN_PIL
class ReanudarValida(unittest.TestCase):  # T-508, revisión de #1036
    def setUp(self):
        self.t = tempfile.TemporaryDirectory()
        self.d, self.s = Path(self.t.name) / "datos", Path(self.t.name) / "salida"
        self.d.mkdir()
        _csv(self.d)
        im.descargar(self.s, abrir=_red_falsa(), directorio=self.d, pausa=0)

    def tearDown(self):
        self.t.cleanup()

    def _reanudar(self):
        import contextlib

        b = io.StringIO()
        with contextlib.redirect_stdout(b):
            c = im.descargar(self.s, abrir=_red_falsa(), directorio=self.d, pausa=0)
        return c, b.getvalue()

    def _tocar(self, clave, valor):
        j = self.s / "img" / "22125.json"
        r = json.loads(j.read_text(encoding="utf-8"))
        r[clave] = valor
        j.write_text(json.dumps(r), encoding="utf-8")

    def test_ficha_valida_se_reutiliza(self):
        c, _ = self._reanudar()
        self.assertEqual(c["totales"]["reanudados"], 2)

    def test_ficha_de_otra_version_o_configuracion_se_descarta_y_se_dice(self):
        self._tocar("huella", "0" * 64)
        c, log = self._reanudar()
        self.assertEqual(c["totales"]["reanudados"], 1)
        self.assertIn("IMAGENES_REANUDAR_DESCARTA 1 fichas previas: otra versión, territorio o configuración", log)
        self.assertEqual(c["totales"]["con_imagen"], 2)  # se bajó de nuevo

    def test_ficha_de_otro_territorio_se_descarta(self):
        self._tocar("territorio_catalogo", "aut08")
        c, _ = self._reanudar()
        self.assertEqual(c["totales"]["reanudados"], 1)

    def test_huella_cambia_con_el_criterio(self):
        h = im.huella_config()
        with mock.patch.object(im, "ANCHO", 400):
            self.assertNotEqual(im.huella_config(), h)
        with mock.patch.object(im, "VERSION", "9.9.9"):
            self.assertNotEqual(im.huella_config(), h)

    def test_subir_se_niega_con_catalogo_incompleto(self):
        c = json.loads((self.s / "catalogo.json").read_text(encoding="utf-8"))
        for marca in (False, None):
            c["completo"] = marca
            if marca is None:
                del c["completo"]
            (self.s / "catalogo.json").write_text(json.dumps(c), encoding="utf-8")
            with self.assertRaises(im.ErrorImagenes) as e:
                im.subir(self.s, aws=mock.Mock(), run=1)
            self.assertEqual(e.exception.codigo, "IMG_INCOMPLETO")


class ElegirPrevio(unittest.TestCase):  # T-508
    @staticmethod
    def _a(i, nombre=None, rama="main", exp=False, digest=True, dia=1):
        return json.dumps({"id": i, "name": nombre or f"imagenes-distritos-{i}", "expired": exp, "created_at": f"2026-11-{dia:02d}T00:00:00Z",
                           "digest": ("sha256:" + "a" * 64) if digest else None, "workflow_run": {"head_branch": rama}})

    def test_mas_de_100_artefactos_aparece_el_de_imagenes(self):
        lineas = [self._a(1000 + i, nombre=f"otra-cosa-{i}", dia=20) for i in range(150)] + [self._a(7, dia=3)]
        self.assertEqual(im.elegir_previo(lineas)["id"], 7)  # estaba tras 150 artefactos de otros

    def test_gana_el_mas_reciente(self):
        self.assertEqual(im.elegir_previo([self._a(1, dia=2), self._a(2, dia=9), self._a(3, dia=5)])["id"], 2)

    def test_rechaza_otra_rama_caducado_sin_digest_y_nombre_ajeno(self):
        malos = [self._a(1, rama="t508"), self._a(2, exp=True), self._a(3, digest=False), self._a(4, nombre="imagenes-distritos-x"),
                 self._a(5, nombre="imagenes-distritos-1-extra")]
        self.assertIsNone(im.elegir_previo(malos))

    def test_cli_elegir_previo(self):
        r = subprocess.run([sys.executable, str(ROOT / "herramientas" / "imagenes_distritos.py"), "elegir-previo"],
                           input="\n".join([self._a(5, dia=4), self._a(6, rama="x", dia=9)]), capture_output=True, text=True)
        self.assertEqual((r.returncode, r.stdout.strip()), (0, "5 sha256:" + "a" * 64))


class Workflow(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import yaml

        cls.w = yaml.safe_load((ROOT / ".github" / "workflows" / "p10-fuentes.yml").read_text(encoding="utf-8"))
        cls.j = cls.w["jobs"]["p14_imagenes"]

    def test_opcion_condicion_y_grupo(self):
        d = (self.w.get("on") or self.w[True])["workflow_dispatch"]["inputs"]
        self.assertEqual(d["tipo"]["options"][-2:], ["Imágenes de distritos (hoja de contactos)", "Imágenes de distritos y subir a R2"])
        self.assertEqual(list(d), ["tipo", "territorio", "eleccion", "regenerar"])  # sin entradas técnicas nuevas (D-129)
        self.assertEqual(self.j["if"], "${{ startsWith(inputs.tipo, 'Imágenes de distritos') && github.ref == 'refs/heads/main' && !inputs.campana }}")
        self.assertIn("startsWith(inputs.tipo, 'Imágenes de distritos') && 'ddd-imagenes-distritos'", self.w["concurrency"]["group"])
        self.assertEqual(self.j["needs"], "entrada")

    def test_solo_un_paso_con_secretos_y_condicionado(self):
        con = [s for s in self.j["steps"] if "secrets." in json.dumps(s)]
        self.assertEqual(len(con), 1)
        self.assertEqual(con[0]["if"], "${{ inputs.tipo == 'Imágenes de distritos y subir a R2' }}")
        self.assertIn("imagenes_distritos.py subir", con[0]["run"])
        bajar = next(s for s in self.j["steps"] if s.get("name") == "Bajar y preparar (sin secretos)")
        self.assertIn("imagenes_distritos.py descargar", bajar["run"])
        self.assertLess(self.j["steps"].index(bajar), self.j["steps"].index(con[0]))
        texto = json.dumps(self.j)
        for prohibido in ("git push", "DDD_REGISTRO_APP", "contents: write", "fuentes/", "mapas/"):
            self.assertNotIn(prohibido, texto)

    def test_t508_plazo_reanudar_y_presupuesto(self):
        self.assertLessEqual(self.j["timeout-minutes"], 30)
        nombres = [s.get("name") for s in self.j["steps"]]
        rec = self.j["steps"][nombres.index("Recuperar lo ya bajado (reanudar)")]
        self.assertLess(nombres.index("Recuperar lo ya bajado (reanudar)"), nombres.index("Bajar y preparar (sin secretos)"))
        self.assertNotIn("secrets.", json.dumps(rec))
        self.assertIn("--paginate", rec["run"])
        self.assertIn("elegir-previo", rec["run"])
        self.assertIn("sha256sum", rec["run"])  # digest del zip verificado antes de extraer
        self.assertIn("'img/*'", rec["run"])  # solo img/: catálogo y hoja no vienen del artefacto previo
        self.assertIn("se empieza de cero", rec["run"])
        self.assertEqual(self.j["permissions"], {"contents": "read", "actions": "read"})
        bajar = next(s for s in self.j["steps"] if s.get("name") == "Bajar y preparar (sin secretos)")
        self.assertIn("python -u", bajar["run"])
        m = re.search(r"--presupuesto-min (\d+)", bajar["run"])
        self.assertTrue(m and int(m.group(1)) < self.j["timeout-minutes"] - 5)
        self.assertEqual(self.j["steps"][-1]["if"], "${{ always() }}")  # el artefacto parcial se conserva

    def test_entrada(self):
        paso = next(s for s in self.w["jobs"]["entrada"]["steps"] if s.get("name") == "Comprobar tipo, territorio y elección")
        for tipo, terr, rc in (("Imágenes de distritos (hoja de contactos)", "congreso", 0), ("Imágenes de distritos y subir a R2", "congreso", 0),
                               ("Imágenes de distritos y subir a R2", "aut08", 2), ("Imágenes de distritos (hoja de contactos)", "", 2)):
            with tempfile.TemporaryDirectory() as t:
                env = {**os.environ, "TIPO": tipo, "TERRITORIO": terr, "TERRITORIO_LLAMADA": "",
                       "ELECCION": "vigente", "GITHUB_STEP_SUMMARY": str(Path(t) / "s")}
                r = subprocess.run(["bash", "-eo", "pipefail", "-c", paso["run"]], env=env, capture_output=True, text=True)
            self.assertEqual(r.returncode, rc, ((tipo, terr), r.stdout + r.stderr))


if __name__ == "__main__":
    unittest.main()
