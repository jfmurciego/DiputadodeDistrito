# -*- coding: utf-8 -*-
"""T-119 PR-C: vista territorial del visor v2 (generador + navegador) y repaso completo del v2 en móvil y escritorio.

PROYECTO: Diputado de Distrito · VERSIÓN: 1.0.0 · FECHA: 2026-11-09 · ESTADO: candidato · ANTERIOR: ninguna (fichero nuevo)
El fixture reproduce propiedades reales del M06 de Baleares (distrito 9 de nac07, Baleares: 76.968 hab., −36,39 %, suelo 0).
"""
import functools, hashlib, http.server, json, os, shutil, sys, tempfile, threading, unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "herramientas"))
import generar_territorial_visor as gt  # noqa: E402
import generar_rotacion_visor as gr  # noqa: E402

try:
    from playwright.sync_api import sync_playwright
except ImportError:  # pragma: no cover
    sync_playwright = None


def _feat(i, pop, dev, suelo, tol, secs, cods, nombres):
    return {"type": "Feature", "geometry": {"type": "Polygon", "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 0]]]},
            "properties": {"distrito": i + 1, "district_pop": pop, "target": 120990.6, "relative_deviation": dev,
                           "population_floor": suelo, "population_cap": 154867.968, "within_target_tolerance": tol,
                           "within_hard_bounds": True, "section_count": secs, "municipality_codes": cods,
                           "municipality_names": nombres, "province_codes": "07-C01"}}


def _paquete(t: Path, corrupto=False):
    datos, dist = t / "datos", t / "distritos"
    (datos / "congreso_x").mkdir(parents=True); dist.mkdir()
    gj = json.dumps({"type": "FeatureCollection", "features": [
        _feat(8, 93601, -0.226, 0.0, True, 48, "07024:07-G01 | 07026:07-G01", "Eivissa | Formentera"),
        _feat(9, 76968, -0.3639, 0.0, False, 34, "07046:07-G01", "Sant Antoni de Portmany")]}).encode()
    (datos / "congreso_x" / "distritos.geojson").write_bytes(gj)
    h = hashlib.sha256(gj).hexdigest()
    (datos / "INDEX.json").write_text(json.dumps({"territorios": {"congreso_x": {
        "sha256_origen": "ab" * 32, "geojson": {"ruta": "congreso_x/distritos.geojson", "sha256": "0" * 64 if corrupto else h}}}}), "utf-8")
    (dist / "municipios_ine_2025.csv").write_text("codigo_ine,nombre_ine,poblacion_2025\n07024,Eivissa,50\n07026,Formentera,12\n07046,Sant Antoni de Portmany,29455\n", "utf-8")
    (dist / "toponimos_es.csv").write_text("codigo_ine,nombre_ine,nombre_es\n07024,Eivissa,Ibiza\n", "utf-8")
    (dist / "nombres_congreso_x.csv").write_text("territorio,district_id,nombre_distrito\ncongreso_x,8,Ibiza y entorno\ncongreso_x,9,Santa Eulalia\n", "utf-8")
    return datos, dist


class Generador(unittest.TestCase):
    def test_campos_y_toponimos(self):
        with tempfile.TemporaryDirectory() as t:
            datos, dist = _paquete(Path(t))
            out = Path(t) / "t.json"
            self.assertEqual(gt.generar(datos, out, dist), 0)
            p = json.loads(out.read_text("utf-8"))["provincias"]["07"]
            self.assertEqual(p["sha256_m06"], "ab" * 32)
            d9 = p["distritos"][1]
            self.assertEqual((d9["p"], d9["dev"], d9["suelo"], d9["exenta"], d9["tol"], d9["s"]), (76968, -0.3639, 0.0, True, False, 34))
            self.assertEqual((d9["d"], d9["n"]), (10, "Santa Eulalia"))  # público 10 = interno 9
            self.assertEqual(p["distritos"][0]["m"], ["Formentera", "Ibiza"])  # topónimo español, no «Eivissa»

    def test_sha_distinto_falla(self):
        with tempfile.TemporaryDirectory() as t:
            datos, dist = _paquete(Path(t), corrupto=True)
            with self.assertRaises(SystemExit):
                gt.generar(datos, Path(t) / "t.json", dist)


@unittest.skipIf(sync_playwright is None, "sin playwright")
class Repaso(unittest.TestCase):
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
        # Territorial de Álava (cod 01) con valores del fixture; secciones mínimas de Álava
        with tempfile.TemporaryDirectory() as t:
            datos, dist = _paquete(Path(t))
            gt.generar(datos, v2 / "datos" / "territorial.json", dist)
        d = json.loads((v2 / "datos" / "territorial.json").read_text("utf-8"))
        d["provincias"]["01"] = d["provincias"].pop("07")
        (v2 / "datos" / "territorial.json").write_text(json.dumps(d, ensure_ascii=False), "utf-8")
        gr.generar(v2 / "datos" / "rotacion.json", RAIZ / "datos/resultados/historico/rotacion", RAIZ / "datos/composicion")
        s = v2 / "datos" / "secciones"; s.mkdir()
        (s / "INDEX.json").write_text(json.dumps({"provincias": {"01": {"secciones": 1}}}), "utf-8")
        (s / "01.geojson").write_text(json.dumps({"type": "FeatureCollection", "features": [{"type": "Feature", "properties": {"s": "0100101001", "m": "Vitoria-Gasteiz", "p": 1390, "d": 1, "t": "nac01"},
            "geometry": {"type": "Polygon", "coordinates": [[[-2.72, 42.8], [-2.66, 42.8], [-2.66, 42.9], [-2.72, 42.9], [-2.72, 42.8]]]}}]}), "utf-8")

    @classmethod
    def tearDownClass(cls):
        cls.srv.shutdown(); shutil.rmtree(cls.tmp, ignore_errors=True)

    def _abrir(self, p, ancho, alto, errores):
        b = p.chromium.launch(executable_path=os.environ.get("PW_CHROMIUM") or None, args=["--no-sandbox"])
        pg = b.new_page(viewport={"width": ancho, "height": alto})
        pg.on("pageerror", lambda e: errores.append(str(e)))
        pg.on("console", lambda m: errores.append(m.text) if m.type == "error" and "404" not in m.text and "Failed to load resource" not in m.text else None)
        ml = os.environ.get("MAPLIBRE_DIR")
        if ml:
            def r(route):
                f = Path(ml) / route.request.url.rsplit("/", 1)[1]
                route.fulfill(path=str(f)) if f.exists() else route.abort()
            pg.route("https://unpkg.com/**", r)
        pg.route("**/nacional/**", lambda route: route.fulfill(body="<p>n</p>", content_type="text/html"))
        pg.goto(self.url)
        pg.wait_for_function("typeof map!=='undefined'&&map&&map.isStyleLoaded()", timeout=20000)
        pg.wait_for_function("document.querySelector('#m-territorial').getAttribute('aria-disabled')!=='true'", timeout=10000)
        return b, pg

    def _elegir_alava(self, pg):
        pt = pg.evaluate("(()=>{const q=map.project([-2.69,42.85]);const r=map.getCanvas().getBoundingClientRect();return[q.x+r.left,q.y+r.top]})()")
        for _ in range(4):
            pg.wait_for_function("map.loaded()&&!map.isMoving()", timeout=10000)
            pg.mouse.click(*pt)
            if "Álava" in pg.locator("#ruta").inner_text():
                return
            pg.wait_for_timeout(300)
        self.fail("no se pudo elegir Álava")

    def _repaso(self, ancho, alto, nombre):
        errores = []
        with sync_playwright() as p:
            b, pg = self._abrir(p, ancho, alto, errores)
            try:
                # selector visible y Electoral por defecto
                self.assertTrue(pg.locator("#modos").is_visible())
                self.assertEqual(pg.locator("#m-electoral").get_attribute("aria-pressed"), "true")
                # Territorial: sin chips electorales, con desviación; ficha nacional
                pg.click("#m-territorial")
                self.assertEqual(pg.locator("#m-territorial").get_attribute("aria-pressed"), "true")
                self.assertFalse(pg.locator("#c-rotacion").is_visible())
                self.assertFalse(pg.locator("#elecciones-barra").is_visible())  # la barra de elecciones es electoral
                self.assertTrue(pg.locator("#c-desviacion").is_visible())
                self.assertIn("territorial", pg.locator("#ficha").inner_text().lower())
                self.assertIn("40 %", pg.locator("#leyenda").inner_text())
                self._elegir_alava(pg)
                ficha = pg.locator("#ficha").inner_text()
                self.assertIn("Ibiza y entorno", ficha)
                self.assertIn("Santa Eulalia", ficha)
                self.assertIn("−36,4 %", ficha)
                self.assertIn("fuera de tolerancia", ficha)
                self.assertIn("suelo exento", ficha)
                self.assertIn("93.601", ficha)
                # secciones se activan solas al elegir provincia en Territorial
                pg.wait_for_function("map.getLayoutProperty('sec-fill','visibility')==='visible'", timeout=10000)
                self.assertEqual(pg.locator("#c-secciones").get_attribute("aria-pressed"), "true")
                # municipios con topónimo español (desplegable)
                pg.locator(".terr-dist summary").first.click()
                self.assertIn("Ibiza", pg.locator(".terr-dist p").first.inner_text())
                self.assertNotIn("Eivissa", pg.locator("#ficha").inner_text())
                # volver a Electoral restaura chips y ficha electoral
                pg.click("#m-electoral")
                self.assertTrue(pg.locator("#c-rotacion").is_visible())
                self.assertNotIn("terr-dist", pg.locator("#ficha").inner_html())
                # autonómico: sin selector; no hay botones muertos
                pg.click("#v-autonomico")
                self.assertFalse(pg.locator("#modos").is_visible())
                pg.click("#v-congreso")
                self.assertTrue(pg.locator("#modos").is_visible())
                # chips «sin datos»: ninguno sin motivo
                for c in pg.locator(".chip[aria-disabled=true]").all():
                    self.assertTrue(c.get_attribute("data-motivo"), c.inner_text())
                for c in pg.locator("button:disabled").all():
                    self.assertTrue(c.get_attribute("title") or c.inner_text(), "botón desactivado sin texto")
                # pestañas, enlaces y scroll horizontal
                for t in ["inicio", "nacional", "autonomico", "elecciones", "metodo"]:
                    pg.click(f'.tab[data-tab="{t}"]')
                    self.assertFalse(pg.evaluate("document.documentElement.scrollWidth>innerWidth"), f"scroll horizontal en {t} ({nombre})")
                hrefs = pg.evaluate("[...document.querySelectorAll('a[href]')].map(a=>a.getAttribute('href'))")
                self.assertTrue(all(h == "#" or h.startswith(("../nacional/", "https://github.com/")) for h in hrefs), hrefs)
                if os.environ.get("CAPTURAS_DIR"):
                    pg.click('.tab[data-tab="inicio"]')
                    pg.click("#m-territorial")
                    pg.screenshot(path=f'{os.environ["CAPTURAS_DIR"]}/terr_{nombre}.png', full_page=True)
            finally:
                b.close()
        self.assertEqual(errores, [])

    def test_repaso_movil_390(self):
        self._repaso(390, 844, "movil")

    def test_repaso_escritorio_1280(self):
        self._repaso(1280, 800, "escritorio")

    def test_sin_territorial_motivo_visible(self):
        f = self.v2 / "datos" / "territorial.json"
        guardado = f.read_text("utf-8"); f.unlink()
        try:
            with sync_playwright() as p:
                b = p.chromium.launch(executable_path=os.environ.get("PW_CHROMIUM") or None, args=["--no-sandbox"])
                pg = b.new_page(viewport={"width": 390, "height": 844})
                ml = os.environ.get("MAPLIBRE_DIR")
                if ml:
                    pg.route("https://unpkg.com/**", lambda r: r.fulfill(path=str(Path(ml) / r.request.url.rsplit("/", 1)[1])))
                pg.goto(self.url)
                pg.wait_for_function("typeof map!=='undefined'&&map&&map.isStyleLoaded()", timeout=20000)
                pg.wait_for_timeout(600)
                pg.click("#m-territorial", force=True)
                self.assertIn("sin datos territoriales", pg.locator("#motivo").inner_text())
                self.assertEqual(pg.locator("#m-electoral").get_attribute("aria-pressed"), "true")
                b.close()
        finally:
            f.write_text(guardado, "utf-8")


if __name__ == "__main__":
    unittest.main()
