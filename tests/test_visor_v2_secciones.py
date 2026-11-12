# -*- coding: utf-8 -*-
"""T-119: capa de secciones del visor v2 (generador + navegador, móvil 390 px).

PROYECTO: Diputado de Distrito · VERSIÓN: 1.0.0 · FECHA: 2026-11-09 · ESTADO: candidato · ANTERIOR: ninguna (fichero nuevo)
Los valores esperados son literales del fixture (no se recalculan con el código bajo prueba).
El navegador necesita playwright y MapLibre: con MAPLIBRE_DIR (carpeta con maplibre-gl.js/css) no usa la red.
"""
import functools
import http.server
import json
import os
import shutil
import tempfile
import threading
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
MANIFEST_SHA = "0" * 64

try:
    import geopandas as gpd
    from shapely.geometry import box
except ImportError:  # pragma: no cover
    gpd = None


@unittest.skipIf(gpd is None, "sin geopandas")
class GeneradorSecciones(unittest.TestCase):
    def test_une_seccionado_y_composicion(self):
        import sys
        sys.path.insert(0, str(RAIZ / "herramientas"))
        import generar_secciones_visor as g
        with tempfile.TemporaryDirectory() as t:
            t = Path(t)
            df = gpd.GeoDataFrame(
                {"CUSEC": ["0100101001", "0100101002", "2800101001"], "NMUN": ["Alegría-Dulantzi", "Alegría-Dulantzi", "Madrid"]},
                geometry=[box(500000, 4740000, 500500, 4740500), box(500500, 4740000, 501000, 4740500), box(440000, 4470000, 440500, 4470500)],
                crs=25830)
            shp = t / "s"; shp.mkdir()
            df.to_file(shp / "s.shp")
            zp = t / "seccionado.zip"
            shutil.make_archive(str(zp.with_suffix("")), "zip", shp)
            comp = t / "comp"; comp.mkdir()
            (comp / "congreso_alava.csv").write_text("seccion,distrito,poblacion\n0100101001,2,1390\n0100101002,0,1579\n", "utf-8")
            out = t / "out"
            self.assertEqual(g.generar(zp, out, comp), 0)
            idx = json.loads((out / "INDEX.json").read_text("utf-8"))
            self.assertEqual(sorted(idx["provincias"]), ["01"])  # Madrid no está en la composición
            self.assertEqual(idx["provincias"]["01"]["secciones"], 2)
            raw = (out / "01.geojson").read_bytes()
            self.assertEqual(idx["provincias"]["01"]["sha256"], g.sha(raw))
            props = {f["properties"]["s"]: f["properties"] for f in json.loads(raw)["features"]}
            self.assertEqual(props["0100101001"], {"s": "0100101001", "m": "Alegría-Dulantzi", "p": 1390, "d": 3, "t": "nac01"})
            self.assertEqual(props["0100101002"]["d"], 1)
            x = json.loads(raw)["features"][0]["geometry"]["coordinates"][0][0]
            self.assertTrue(-3.0 < x[0] < -2.0 and 42.0 < x[1] < 43.5, x)  # WGS84 en Álava

    def test_provincia_solo_en_runs(self):
        import sys, hashlib
        sys.path.insert(0, str(RAIZ / "herramientas"))
        import generar_secciones_visor as g
        with tempfile.TemporaryDirectory() as t:
            c = Path(t); (c / "runs").mkdir()
            for run, fila in (("111", "0100101001,0,5"), ("222", "0100101001,1,7")):
                b = f"seccion,distrito,poblacion\n{fila}\n".encode()
                (c / "runs" / f"congreso_y_{run}.csv").write_bytes(b)
            man = {"runs": {f"congreso_y/{r}": {"territorio": "congreso_y", "run_id": r, "ruta": str(c / "runs" / f"congreso_y_{r}.csv"),
                   "sha256_csv": hashlib.sha256((c / "runs" / f"congreso_y_{r}.csv").read_bytes()).hexdigest()} for r in ("111", "222")}}
            (c / "MANIFEST.json").write_text(json.dumps(man), "utf-8")
            idx = c / "INDEX.json"; idx.write_text(json.dumps({"territorios": {"congreso_y": {"run_id": 111}}}), "utf-8")
            sec, h = g.leer_composicion(c, indice=idx)
            self.assertEqual(sec["0100101001"], {"d": 1, "p": 5, "t": "congreso_y"})  # el run publicado (111), no el más reciente
            self.assertEqual(list(h), ["congreso_y"])

    def test_sin_seccionado_no_falla(self):
        import sys
        sys.path.insert(0, str(RAIZ / "herramientas"))
        import generar_secciones_visor as g
        with tempfile.TemporaryDirectory() as t:
            self.assertEqual(g.generar(Path(t) / "no.zip", Path(t) / "out", RAIZ / "datos" / "composicion"), 0)
            self.assertFalse((Path(t) / "out").exists())

    def test_composicion_con_sha_distinto_falla(self):
        import sys
        sys.path.insert(0, str(RAIZ / "herramientas"))
        import generar_secciones_visor as g
        with tempfile.TemporaryDirectory() as t:
            c = Path(t)
            (c / "congreso_x.csv").write_text("seccion,distrito,poblacion\n0100101001,0,1\n", "utf-8")
            (c / "MANIFEST.json").write_text(json.dumps({"territorios": {"congreso_x": {"sha256_csv": MANIFEST_SHA}}}), "utf-8")
            with self.assertRaises(SystemExit):
                g.leer_composicion(c)


def _feat(s, d, p, x0):
    return {"type": "Feature", "properties": {"s": s, "m": "Vitoria-Gasteiz", "p": p, "d": d, "t": "nac01"},
            "geometry": {"type": "Polygon", "coordinates": [[[x0, 42.80], [x0 + .06, 42.80], [x0 + .06, 42.90], [x0, 42.90], [x0, 42.80]]]}}


try:
    from playwright.sync_api import sync_playwright
except ImportError:  # pragma: no cover
    sync_playwright = None


@unittest.skipIf(sync_playwright is None, "sin playwright")
class NavegadorSecciones(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.mkdtemp()
        cls.v2 = Path(cls.tmp) / "v2"
        shutil.copytree(RAIZ / "visor" / "v2", cls.v2, ignore=shutil.ignore_patterns("secciones", "rotacion.json", "territorial.json"))
        shutil.copy(RAIZ / "web" / "textos.md", cls.v2 / "textos.md")
        d = cls.v2 / "datos" / "secciones"; d.mkdir()
        (d / "INDEX.json").write_text(json.dumps({"provincias": {"01": {"secciones": 2}}}), "utf-8")
        (d / "01.geojson").write_text(json.dumps({"type": "FeatureCollection", "features": [
            _feat("0100101001", 1, 1390, -2.72), _feat("0100101002", 2, 1579, -2.66)]}), "utf-8")
        h = functools.partial(http.server.SimpleHTTPRequestHandler, directory=cls.tmp)
        h.log_message = lambda *a, **k: None
        cls.srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), h)
        threading.Thread(target=cls.srv.serve_forever, daemon=True).start()
        cls.url = f"http://127.0.0.1:{cls.srv.server_address[1]}/v2/index.html"

    @classmethod
    def tearDownClass(cls):
        cls.srv.shutdown(); shutil.rmtree(cls.tmp, ignore_errors=True)

    def _pagina(self, p, ml):
        b = p.chromium.launch(executable_path=os.environ.get("PW_CHROMIUM") or None, args=["--no-sandbox"])
        pg = b.new_page(viewport={"width": 390, "height": 844})
        if ml:
            def r(route):
                u = route.request.url
                f = Path(ml) / u.rsplit("/", 1)[1]
                route.fulfill(path=str(f)) if f.exists() else route.abort()
            pg.route("https://unpkg.com/**", r)
        pg.goto(self.url)
        pg.wait_for_function("typeof maplibregl!=='undefined'&&typeof map!=='undefined'&&map&&map.isStyleLoaded()", timeout=20000)
        return b, pg

    def test_capa_secciones_movil(self):
        with sync_playwright() as p:
            b, pg = self._pagina(p, os.environ.get("MAPLIBRE_DIR"))
            try:
                chip = pg.locator("#c-secciones")
                pg.wait_for_function("document.querySelector('#c-secciones').getAttribute('aria-disabled')!=='true'", timeout=10000)
                self.assertEqual(chip.get_attribute("aria-pressed"), "false")
                self.assertFalse(pg.evaluate("document.documentElement.scrollWidth>innerWidth"))  # sin scroll horizontal
                chip.click()
                pt = pg.evaluate("(()=>{const q=map.project([-2.69,42.85]);const r=map.getCanvas().getBoundingClientRect();return[q.x+r.left,q.y+r.top]})()")
                for _ in range(4):  # el mapa puede seguir cargando teselas: reintenta hasta que la provincia quede elegida
                    pg.wait_for_function("map.loaded()&&!map.isMoving()", timeout=10000)
                    pg.mouse.click(*pt)  # provincia de Álava
                    if "Álava" in pg.locator("#ruta").inner_text():
                        break
                    pg.wait_for_timeout(300)
                self.assertIn("Álava", pg.locator("#ruta").inner_text())
                pg.wait_for_function("map.getSource('sec')&&map.getSource('sec')._data.features&&map.getSource('sec')._data.features.length===2", timeout=10000)
                self.assertEqual(pg.evaluate("map.getLayoutProperty('sec-fill','visibility')"), "visible")
                pg.evaluate("map.jumpTo({center:[-2.69,42.85],zoom:9.5})")
                pg.wait_for_function("map.queryRenderedFeatures({layers:['sec-fill']}).length>0", timeout=10000)
                pt = pg.evaluate("(()=>{const q=map.project([-2.69,42.85]);const r=map.getCanvas().getBoundingClientRect();return[q.x+r.left-20,q.y+r.top]})()")
                pg.mouse.click(*pt)
                self.assertIn("Cada color es un distrito (2)", pg.locator("#leyenda").inner_text())
                ficha = pg.locator("#ficha").inner_text()
                self.assertIn("0100101001", ficha)
                self.assertIn("Vitoria-Gasteiz", ficha)
                self.assertIn("1390 habitantes", ficha)
                self.assertIn("Distrito 1", ficha)
                chip.click()
                self.assertEqual(pg.evaluate("map.getLayoutProperty('sec-fill','visibility')"), "none")
            finally:
                b.close()

    def test_sin_capa_el_chip_sigue_desactivado(self):
        shutil.rmtree(self.v2 / "datos" / "secciones")
        try:
            with sync_playwright() as p:
                b, pg = self._pagina(p, os.environ.get("MAPLIBRE_DIR"))
                try:
                    pg.wait_for_timeout(800)
                    self.assertEqual(pg.locator("#c-secciones").get_attribute("aria-disabled"), "true")
                finally:
                    b.close()
        finally:
            d = self.v2 / "datos" / "secciones"; d.mkdir()
            (d / "INDEX.json").write_text(json.dumps({"provincias": {"01": {"secciones": 2}}}), "utf-8")


if __name__ == "__main__":
    unittest.main()
