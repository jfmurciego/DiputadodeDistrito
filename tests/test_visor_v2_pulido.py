# -*- coding: utf-8 -*-
"""T-119 pulido del visor v2: un solo iframe del visor nacional, pestañas accesibles, sin scroll horizontal a 390 px.

PROYECTO: Diputado de Distrito · VERSIÓN: 1.0.0 · FECHA: 2026-11-09 · ESTADO: candidato · ANTERIOR: ninguna (fichero nuevo)
Con MAPLIBRE_DIR (maplibre-gl.js/css) no usa la red; PW_CHROMIUM fija el ejecutable; CAPTURAS_DIR guarda capturas.
"""
import functools, http.server, os, shutil, tempfile, threading, unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
try:
    from playwright.sync_api import sync_playwright
except ImportError:  # pragma: no cover
    sync_playwright = None


@unittest.skipIf(sync_playwright is None, "sin playwright")
class Pulido(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.mkdtemp()
        shutil.copytree(RAIZ / "visor" / "v2", Path(cls.tmp) / "v2", ignore=shutil.ignore_patterns("secciones", "rotacion.json", "territorial.json"))
        shutil.copy(RAIZ / "web" / "textos.md", Path(cls.tmp) / "v2" / "textos.md")
        h = functools.partial(http.server.SimpleHTTPRequestHandler, directory=cls.tmp)
        h.log_message = lambda *a, **k: None
        cls.srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), h)
        threading.Thread(target=cls.srv.serve_forever, daemon=True).start()
        cls.url = f"http://127.0.0.1:{cls.srv.server_address[1]}/v2/index.html"

    @classmethod
    def tearDownClass(cls):
        cls.srv.shutdown(); shutil.rmtree(cls.tmp, ignore_errors=True)

    def _abrir(self, p, ancho, alto):
        b = p.chromium.launch(executable_path=os.environ.get("PW_CHROMIUM") or None, args=["--no-sandbox"])
        pg = b.new_page(viewport={"width": ancho, "height": alto})
        ml = os.environ.get("MAPLIBRE_DIR")
        if ml:
            def r(route):
                f = Path(ml) / route.request.url.rsplit("/", 1)[1]
                route.fulfill(path=str(f)) if f.exists() else route.abort()
            pg.route("https://unpkg.com/**", r)
        pg.route("**/nacional/**", lambda route: route.fulfill(body="<p>nacional</p>", content_type="text/html"))
        pg.goto(self.url)
        pg.wait_for_function("typeof map!=='undefined'&&map&&map.isStyleLoaded()", timeout=20000)
        return b, pg

    def _recorrer(self, ancho, alto, nombre):
        with sync_playwright() as p:
            b, pg = self._abrir(p, ancho, alto)
            try:
                self.assertFalse(pg.locator(".barra-edit").is_visible())  # los botones de edición solo con ?edit=1
                self.assertEqual(pg.locator("iframe").count(), 1)  # un solo visor nacional embebido
                for t in ["inicio", "nacional", "autonomico", "elecciones", "metodo"]:
                    pg.click(f'.tab[data-tab="{t}"]')
                    self.assertEqual(pg.locator(".tab[aria-current=page]").get_attribute("data-tab"), t)
                    self.assertEqual(pg.locator(".tab[aria-current=page]").count(), 1)
                    self.assertFalse(pg.evaluate("document.documentElement.scrollWidth>innerWidth"), f"scroll horizontal en {t}")
                    if os.environ.get("CAPTURAS_DIR"):
                        pg.screenshot(path=f'{os.environ["CAPTURAS_DIR"]}/v2_{nombre}_{t}.png')
                pg.click('.tab[data-tab="elecciones"]')
                self.assertEqual(pg.locator("#page-elecciones iframe").count(), 0)
                pg.click("#page-elecciones [data-tab-go=nacional]")
                self.assertTrue(pg.locator("#page-nacional").evaluate("e=>e.classList.contains('active')"))
                m = pg.locator(".model").nth(1)
                m.focus(); pg.keyboard.press("Enter")  # teclado
                self.assertEqual(m.get_attribute("aria-pressed"), "true")
                self.assertEqual(pg.locator(".model").first.get_attribute("aria-pressed"), "false")
            finally:
                b.close()

    def test_movil_390(self):
        self._recorrer(390, 844, "movil")

    def test_escritorio_1280(self):
        self._recorrer(1280, 800, "escritorio")


if __name__ == "__main__":
    unittest.main()
