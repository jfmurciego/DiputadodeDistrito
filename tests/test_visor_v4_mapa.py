"""V4 · Explorar (T-423): la V3 completa dentro de la V4 con la capa «Doble vuelta».

VERSIÓN: 2.0.0 · FECHA: 2026-11-19 · ESTADO: candidato
CAMBIOS: 2.0.0 (T-423): el mapa simple de T-413 (SVG, un territorio cada vez) se retira; se prueba que la V4 contiene todas las capas,
  niveles, controles y paneles de la V3 (incluida la sección censal), que la capa de doble vuelta cubre los 52 nac (prueba JS), que la V3
  publicada no cambia (sha256 literales de main) y que los datos de ejemplo siguen saliendo igual de la herramienta.
ANTERIOR: legacy/visor/v4/mapa_simple_t413_20261119/ (código retirado); 1.0.0 en el historial de git.
"""
import json
import hashlib, re, shutil, subprocess, sys, tempfile, unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
V3 = RAIZ / "visor/v3"
MAPA = RAIZ / "visor/v4/mapa"
# Huellas de visor/v3 en main antes de T-423 (git show origin/main:visor/v3/<f> | sha256sum). La V3 publicada no se toca.
V3_SHA256 = {
    "index.html": "9719c3c95f0601ba6918ebffeb1fc077d697333b222edff9ea78b7e485e19f90",
    "v3.css": "4a8ab8e6f51d45f49cc0eca95d13f4254d6d9e2d4cad4faff3727899aec1a7e0",
    "v3.js": "16fbbefbbf305392287fefa08e32448795ff59e29dd06a63d87d5c3928b7365f",
    "calendario.json": "254e79295e402fbf5d66308c5f2aaeebdb15a39f03441a37c0a3fc8318387d79",
    "README.md": "6dac3e6ebb1b471f208c5020ba41579a4e3c99022c9d9fdf4d4608694ece7216",
}
# Lo que la V3 ofrece y la V4 debe conservar (literal, leído de visor/v3/index.html y v3.js a mano).
CAPAS_V3 = ["ganador", "unidades", "poblacion", "desviacion"]
NIVELES_V3 = ["comunidad", "provincia", "distrito", "municipio", "seccion"]
CAPAS_MAPLIBRE_V3 = ["ccaa-fill", "ccaa-line", "prov-fill", "prov-line", "prov-label", "dist-fill", "dist-line", "sec-fill", "sec-line"]


def _txt(p):
    return Path(p).read_text(encoding="utf-8")


def _opciones(html, select_id):
    m = re.search(r'<select id="%s">(.*?)</select>' % select_id, html, re.S)
    return re.findall(r'<option value="([^"]+)"', m.group(1))


class V3NoCambia(unittest.TestCase):
    def test_v3_identica_a_main(self):
        self.assertEqual(sorted(p.name for p in V3.iterdir()), sorted(V3_SHA256))
        for f, h in V3_SHA256.items():
            self.assertEqual(hashlib.sha256((V3 / f).read_bytes()).hexdigest(), h, f"visor/v3/{f} ha cambiado")


class V4ContieneV3(unittest.TestCase):
    def setUp(self):
        self.h3, self.h4 = _txt(V3 / "index.html"), _txt(MAPA / "index.html")
        self.j3, self.j4 = _txt(V3 / "v3.js"), _txt(MAPA / "explorar.js")

    def test_capas_y_niveles_de_la_v3_incluida_la_seccion(self):
        self.assertEqual(_opciones(self.h3, "layer"), CAPAS_V3)  # guardia: la lista literal es la de la V3
        self.assertEqual(_opciones(self.h3, "level"), NIVELES_V3)
        self.assertEqual(_opciones(self.h4, "layer"), ["doblevuelta"] + CAPAS_V3)
        self.assertEqual(_opciones(self.h4, "level"), NIVELES_V3)
        self.assertIn('<option value="seccion">Sección censal</option>', self.h4)
        for capa in CAPAS_MAPLIBRE_V3:
            self.assertIn('map.addLayer({id:"%s"' % capa, self.j3)
            self.assertIn('map.addLayer({id:"%s"' % capa, self.j4)

    def test_todos_los_controles_y_paneles_de_la_v3(self):
        ids_v3 = set(re.findall(r'\bid="([^"]+)"', self.h3))
        self.assertGreater(len(ids_v3), 40)
        self.assertEqual(ids_v3 - set(re.findall(r'\bid="([^"]+)"', self.h4)), set())
        for marca in ('data-panel="territorio"', 'data-panel="resultados"', 'data-panel="comparar"', 'data-panel="evolucion"',
                      'data-value="nacional"', 'data-value="autonomico"', 'data-value="proporcional"', 'data-value="mayoritario"',
                      'data-value="territorial"', 'data-value="electoral"'):
            self.assertIn(marca, self.h4)

    def test_mismo_motor_y_mismas_fuentes(self):
        # MapLibre con la misma integridad SRI; mismas fuentes de datos y a la misma profundidad (/mapa/ en la raíz, como /v3/; T-428)
        for sri in re.findall(r'integrity="(sha384-[^"]+)"', self.h3):
            self.assertIn(sri, self.h4)
        for ruta in ("v2/datos/provincias.json", "v2/datos/comunidades.json", "datos/INDEX.json", "v2/datos/secciones/",
                     "v2/datos/territorial.json", "data/viewer-results.json", "datos/catalogo_procedencia.json"):
            self.assertIn('"../' + ruta, self.j3)
            self.assertIn('"../' + ruta, self.j4)
            self.assertNotIn('"../../' + ruta, self.j4)
        self.assertEqual(_txt(MAPA / "calendario.json"), _txt(V3 / "calendario.json"))
        # funciones de la V3 que siguen en la V4 (vista nacional, provincia, distrito, sección, calendario, paletas, paneles)
        for fn in re.findall(r"\n  (?:async )?function (\w+)\(", self.j3):
            self.assertRegex(self.j4, r"\n  (?:async )?function %s\(" % fn, fn)
        self.assertIn(re.search(r"const PALETA=\{.*?\};", self.j3, re.S).group(0), self.j4)


class CapaDobleVuelta(unittest.TestCase):
    @unittest.skipUnless(shutil.which("node"), "sin node")
    def test_explorar_52_nac_reglas_ficha_y_seccion(self):
        r = subprocess.run(["node", str(RAIZ / "tests/test_visor_v4_explorar.js")], capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    @unittest.skipUnless(shutil.which("node"), "sin node")
    def test_explorar_autonomico_t427(self):
        r = subprocess.run(["node", str(RAIZ / "tests/test_visor_v4_explorar_aut.js")], capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    @unittest.skipUnless(shutil.which("node"), "sin node")
    def test_explorar_datos_remotos_t430(self):
        r = subprocess.run(["node", str(RAIZ / "tests/test_visor_v4_explorar_actual.js")], capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_origen_de_datos_inerte_hasta_configurarlo_t430(self):
        # T-430 paso 1: mientras los datos no estén en datos.diputadodedistrito.es, Explorar usa las rutas relativas de hoy
        self.assertEqual(json.loads((RAIZ / "visor/v4/mapa/datos.json").read_text(encoding="utf-8")), {"actual": ""})

    @unittest.skipUnless(shutil.which("node"), "sin node")
    def test_lector_dv(self):
        r = subprocess.run(["node", str(RAIZ / "tests/test_visor_v4_mapa.js")], capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_reglas_aviso_y_datos_de_p40(self):
        h, js = _txt(MAPA / "index.html"), _txt(MAPA / "explorar.js")
        reglas = re.search(r'<div class="segment segment-4" id="regla">(.*?)</div>', h, re.S).group(1)
        self.assertEqual(re.findall(r">([^<]+)</button>", reglas), ["Tres bloques", "Dos bloques", "Sin coaliciones", "Mayoría simple en el distrito"])
        self.assertEqual(re.findall(r'data-value="(\w+)"', reglas), ["tres", "dos", "base", "primero"])
        self.assertIn('<option value="doblevuelta" selected>', h)
        self.assertIn("Simulación sin valor oficial.", h)
        self.assertIn('dv:"datos/"', js)  # lo que deja herramientas/publicar_doble_vuelta.py en v4/mapa/datos/ (P40)
        self.assertIn("crypto", js)
        self.assertIn("subtle.digest", js)  # verifica el sha256 antes de mostrar nada
        for s in ('src="dv.js"', 'src="explorar.js"', 'href="../tokens-bloques.css"', 'href="../styles.css"'):
            self.assertIn(s, h)
        self.assertLess(h.index('src="dv.js"'), h.index('src="explorar.js"'))

    def test_mapa_simple_retirado(self):
        for f in ("mapa.js", "geo.js", "mapa.css"):
            self.assertFalse((MAPA / f).exists(), f)
        self.assertNotIn("<svg id=\"mapa\"", _txt(MAPA / "index.html"))

    def test_sin_enlaces_a_v3_ni_externos(self):
        for f in ("index.html", "explorar.js", "dv.js"):
            t = _txt(MAPA / f)
            self.assertNotIn("/v3/", t)
            self.assertIsNone(re.search(r"(src|href)=\"https?://", re.sub(r'<link rel="canonical"[^>]*>', "", t)), f)

    def test_ejemplos_coinciden_con_la_herramienta(self):
        with tempfile.TemporaryDirectory() as d:
            sal, det = Path(d) / "r.csv", Path(d) / "d.csv"
            subprocess.run([sys.executable, str(RAIZ / "herramientas/doble_vuelta.py"), "--votos", str(MAPA / "ejemplo/votos.csv"),
                            "--bloques", str(RAIZ / "configuracion/bloques_partidos_2026-11-17.csv"), "--eleccion", "2023-07",
                            "--salida", str(sal), "--detalle", str(det)], check=True, capture_output=True)
            self.assertEqual(sal.read_bytes(), (MAPA / "ejemplo/resultados_doble_vuelta.csv").read_bytes())
            self.assertEqual(det.read_bytes(), (MAPA / "ejemplo/detalle.csv").read_bytes())


if __name__ == "__main__":
    unittest.main()
