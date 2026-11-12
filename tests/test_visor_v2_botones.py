# -*- coding: utf-8 -*-
"""T-119 PR-B: botones del visor v2 (rotación con datos reales; el resto «sin datos» con motivo) y generador de rotación.

PROYECTO: Diputado de Distrito · VERSIÓN: 1.0.0 · FECHA: 2026-11-09 · ESTADO: candidato · ANTERIOR: ninguna (fichero nuevo)
Valores esperados: literales de datos/resultados/historico/rotacion/congreso_alava.csv (T-110), no recalculados.
"""
import functools, http.server, json, os, shutil, sys, tempfile, threading, unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "herramientas"))
import generar_rotacion_visor as gr  # noqa: E402

try:
    from playwright.sync_api import sync_playwright
except ImportError:  # pragma: no cover
    sync_playwright = None

ALAVA_D2 = ["EAJ-PNV", "Podemos–Sumar", "Podemos–Sumar", "EAJ-PNV", "EAJ-PNV", "EH Bildu"]


class Generador(unittest.TestCase):
    def test_alava_distrito_3_publico(self):
        with tempfile.TemporaryDirectory() as t:
            out = Path(t) / "r.json"
            self.assertEqual(gr.generar(out, RAIZ / "datos/resultados/historico/rotacion", RAIZ / "datos/composicion"), 0)
            d = json.loads(out.read_text("utf-8"))
            a = d["provincias"]["01"]
            self.assertEqual(a["territorio"], "congreso_alava")
            self.assertEqual(a["distritos"][2], {"d": 3, "g": ALAVA_D2, "c": 3})
            self.assertEqual(len(a["sha256"]), 64)
            self.assertEqual(d["elecciones"][-1], "202307")

    def test_sin_datos_no_escribe(self):
        with tempfile.TemporaryDirectory() as t:
            self.assertEqual(gr.generar(Path(t) / "r.json", Path(t), Path(t)), 0)
            self.assertFalse((Path(t) / "r.json").exists())


@unittest.skipIf(sync_playwright is None, "sin playwright")
class Botones(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.mkdtemp()
        v2 = Path(cls.tmp) / "v2"
        shutil.copytree(RAIZ / "visor" / "v2", v2, ignore=shutil.ignore_patterns("secciones", "rotacion.json", "territorial.json"))
        shutil.copy(RAIZ / "web" / "textos.md", v2 / "textos.md")
        cls.v2 = v2
        h = functools.partial(http.server.SimpleHTTPRequestHandler, directory=cls.tmp)
        h.log_message = lambda *a, **k: None
        cls.srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), h)
        threading.Thread(target=cls.srv.serve_forever, daemon=True).start()
        cls.url = f"http://127.0.0.1:{cls.srv.server_address[1]}/v2/index.html"

    @classmethod
    def tearDownClass(cls):
        cls.srv.shutdown(); shutil.rmtree(cls.tmp, ignore_errors=True)

    def _abrir(self, p, ancho=390, alto=844):
        b = p.chromium.launch(executable_path=os.environ.get("PW_CHROMIUM") or None, args=["--no-sandbox"])
        pg = b.new_page(viewport={"width": ancho, "height": alto})
        ml = os.environ.get("MAPLIBRE_DIR")
        if ml:
            def r(route):
                f = Path(ml) / route.request.url.rsplit("/", 1)[1]
                route.fulfill(path=str(f)) if f.exists() else route.abort()
            pg.route("https://unpkg.com/**", r)
        pg.route("**/nacional/**", lambda route: route.fulfill(body="<p>n</p>", content_type="text/html"))
        pg.goto(self.url)
        pg.wait_for_function("typeof map!=='undefined'&&map&&map.isStyleLoaded()", timeout=20000)
        return b, pg

    def test_sin_datos_con_motivo_y_407(self):
        (self.v2 / "datos" / "rotacion.json").unlink(missing_ok=True)
        with sync_playwright() as p:
            b, pg = self._abrir(p)
            try:
                for i, frag in [("s-350", "Madrid, Soria y Valladolid"), ("c-participacion", "no hay censo"), ("c-rotacion", "sin datos de rotación")]:
                    pg.click("#" + i, force=True)
                    self.assertIn(frag, pg.locator("#motivo").inner_text())
                    self.assertEqual(pg.locator("#" + i).get_attribute("aria-disabled"), "true")
                self.assertEqual(pg.locator("#c-ganador").get_attribute("aria-pressed"), "true")  # sin datos no cambia la capa
                pg.click("#s-407")
                self.assertTrue(pg.locator("#page-nacional").evaluate("e=>e.classList.contains('active')"))
                self.assertEqual(pg.locator("#s-real").get_attribute("aria-pressed"), "true")
            finally:
                b.close()

    def test_rotacion_real_en_alava(self):
        gr.generar(self.v2 / "datos" / "rotacion.json", RAIZ / "datos/resultados/historico/rotacion", RAIZ / "datos/composicion")
        with sync_playwright() as p:
            b, pg = self._abrir(p)
            try:
                pg.wait_for_function("document.querySelector('#c-rotacion').getAttribute('aria-disabled')!=='true'", timeout=10000)
                pg.click("#c-rotacion")
                self.assertEqual(pg.locator("#c-rotacion").get_attribute("aria-pressed"), "true")
                self.assertEqual(pg.locator("#c-ganador").get_attribute("aria-pressed"), "false")
                self.assertIn("cambios", pg.locator("#leyenda").inner_text())
                pt = pg.evaluate("(()=>{const q=map.project([-2.69,42.85]);const r=map.getCanvas().getBoundingClientRect();return[q.x+r.left,q.y+r.top]})()")
                for _ in range(4):
                    pg.wait_for_function("map.loaded()&&!map.isMoving()", timeout=10000)
                    pg.mouse.click(*pt)  # Álava
                    if "Álava" in pg.locator("#ruta").inner_text():
                        break
                    pg.wait_for_timeout(300)
                fila = pg.locator(".rot-tabla tr").nth(3)  # cabecera + distritos 1..3 → distrito 3 (d=2)
                self.assertEqual(fila.locator("td").first.inner_text(), "3")
                self.assertEqual(fila.locator("td").nth(6).get_attribute("title"), "EH Bildu")
                self.assertEqual(fila.locator("td").last.inner_text(), "3")
                self.assertFalse(pg.evaluate("document.documentElement.scrollWidth>innerWidth"))
                pg.click("#c-ganador")
                self.assertNotIn("rot-tabla", pg.locator("#ficha").inner_html())
            finally:
                b.close()

    def test_numero_mostrado_igual_al_csv_publico(self):
        """T-135: la tabla de rotación muestra los mismos números 1..K que el CSV público (sin doble +1)."""
        gr.generar(self.v2 / "datos" / "rotacion.json", RAIZ / "datos/resultados/historico/rotacion", RAIZ / "datos/composicion")
        with sync_playwright() as p:
            b, pg = self._abrir(p)
            try:
                pg.wait_for_function("document.querySelector('#c-rotacion').getAttribute('aria-disabled')!=='true'", timeout=10000)
                pg.click("#c-rotacion")
                for nombre, t, lonlat in (("Álava", "congreso_alava", (-2.69, 42.85)), ("Madrid", "congreso_madrid", (-3.70, 40.42))):
                    pg.evaluate(f"map.jumpTo({{center:[{lonlat[0]},{lonlat[1]}],zoom:7}})")
                    for _ in range(5):
                        pg.wait_for_function("map.loaded()&&!map.isMoving()", timeout=10000)
                        pt = pg.evaluate(f"(()=>{{const q=map.project([{lonlat[0]},{lonlat[1]}]);const r=map.getCanvas().getBoundingClientRect();return[q.x+r.left,q.y+r.top]}})()")
                        pg.mouse.click(*pt)
                        if nombre in pg.locator("#ruta").inner_text():
                            break
                        pg.wait_for_timeout(300)
                    self.assertIn(nombre, pg.locator("#ruta").inner_text())
                    vistos = [c.inner_text() for c in pg.locator(".rot-tabla tr td:first-child").all()]
                    csv_ = (RAIZ / "datos_abiertos" / t / "resultados.csv").read_text("utf-8").splitlines()[1:]
                    self.assertEqual(vistos, [l.split(",")[0] for l in csv_], nombre)
                    self.assertNotIn("0", vistos)
            finally:
                b.close()


if __name__ == "__main__":
    unittest.main()
