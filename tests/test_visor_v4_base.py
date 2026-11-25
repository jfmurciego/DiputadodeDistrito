"""T-415 PR 1: base de visor/v4 (portada). Esperados literales, no recalculados."""
import hashlib
import json
import re
import unittest
from pathlib import Path

V4 = Path(__file__).resolve().parent.parent / "visor" / "v4"
DOCS = Path(__file__).resolve().parent.parent / "documentacion_publica" / "docs"
# T-423: páginas para el público general (Metodología y Comprender): ni jerga técnica ni códigos internos
JERGA = ["commit", "GerryChain", "GeoJSON", "ZIP", "sha256", "SHA-256", "R2", "workflow", "artefacto", "checkpoint", "ensemble",
         "CRS", "JSON", "CSV", "hash", "run", "grafo", "pipeline", "portfolio", "script", "repositorio", "legacy"]
PAGINAS = ["index.html", "comprender.html", "auditoria-registro.html"]
# sha256 de los WebP de la autora (final/SHA256SUMS y assets-manifest.json de la entrega)
SHA = {
    "congreso.webp": "ece374b9094acb48eb1ae0b1714440e4401a3154935bb444169bf211da8d13b6",
}


def _txt(p):
    return (V4 / p).read_text(encoding="utf-8")


class PortadaV4(unittest.TestCase):
    def test_enlaces_locales_y_anclas_resuelven(self):
        for pag in PAGINAS:
            h = _txt(pag)
            for ref in re.findall(r'(?:href|src)="([^"#:?]+)(?:[?#][^"]*)?"', h):
                if ref.startswith("docs/"):  # T-423: Datos, Metodología y Fuentes las genera P40 (Zensical) de documentacion_publica/docs/*.md (T-428: V4 en la raíz)
                    self.assertTrue((DOCS / ref[len("docs/"):].replace(".html", ".md")).is_file(), f"{pag}: {ref}")
                    continue
                destino = (V4 / ref).resolve()
                self.assertTrue(destino.exists(), f"{pag}: {ref}")
        for pag in PAGINAS:
            for r, a in re.findall(r'href="([^"#:]*)#([^"]+)"', _txt(pag)):
                self.assertIn(f'id="{a}"', _txt(r or pag), f"{pag}: ancla {a}")

    def test_sin_enlaces_a_ficheros_no_publicados(self):
        # NO_PUBLICAR.txt lista lo que P40 borra del sitio: ningún enlace interno de v4/ puede apuntar a ello (daría 404)
        excluidas = [l.strip() for l in _txt("NO_PUBLICAR.txt").splitlines() if l.strip() and not l.startswith("#")]
        self.assertIn("auditoria-registro.html", excluidas)  # guardia: el test comprueba algo real
        paginas = [p for p in PAGINAS + ["mapa/index.html"] if p not in excluidas]  # las páginas no publicadas no cuentan
        for pag in paginas:
            base = Path(pag).parent
            for ref in re.findall(r'(?:href|src)="([^"#:?]+)(?:[?#][^"]*)?"', _txt(pag)):
                destino = (V4 / (base / ref).as_posix()).resolve()
                if not destino.is_relative_to(V4.resolve()):
                    continue  # fuera de v4/ (v2/, datos/, docs/ del sitio): NO_PUBLICAR solo afecta a v4/
                destino = str(destino.relative_to(V4.resolve()))
                for e in excluidas:
                    self.assertFalse(destino == e or destino.startswith(e.rstrip("/") + "/"), f"{pag} enlaza a {ref}, que NO_PUBLICAR excluye")
        self.assertNotIn("auditoria-registro", "".join(_txt(p) for p in paginas))

    def test_explorar_va_al_mapa_v4_y_no_a_v3(self):
        for pag in PAGINAS:
            h = _txt(pag)
            self.assertNotIn("/v3/", h, pag)
            self.assertNotIn("diputadodedistrito.es", re.sub(r"<(?:link|meta)[^>]*diputadodedistrito\.es[^>]*>", "", h), pag)  # T-429: canonical y og son absolutos por norma
        self.assertIn('href="mapa/"', _txt("index.html"))

    def test_cabecera_identica_en_todas_las_paginas(self):
        # T-423: una sola plantilla (visor/v4/cabecera.html); cada página la copia con sus rutas; solo cambia aria-current
        plantilla = _txt("cabecera.html").split("-->\n", 1)[1].strip()
        self.assertEqual(plantilla.count("<a "), 5)  # marca + 4 del menú; sin botones a la derecha en ninguna página
        quitar = lambda h: re.sub(r'\{% if actual == "[^"]+" %\}|\{% endif %\}| aria-current="page"', "", h)
        # T-428: la V4 se sirve en la raíz del sitio (docs/ al lado); la documentación vive en /docs/ (V4 = ../)
        paginas = {"index.html": ("", "docs/", "./"), "comprender.html": ("", "docs/", "./"), "auditoria-registro.html": ("", "docs/", "./"),
                   "mapa/index.html": ("../", "../docs/", "../")}
        for pag, (v4, docs, inicio) in paginas.items():
            h = re.search(r'<header class="site-header[^"]*">.*?</header>', _txt(pag), re.S).group(0)
            self.assertEqual(quitar(h), plantilla.replace("{V4}", v4).replace("{DOCS}", docs).replace("{INICIO}", inicio), pag)
        zens = (DOCS.parent / "overrides/main.html").read_text(encoding="utf-8")
        h = re.search(r'<header class="site-header[^"]*">.*?</header>', zens, re.S).group(0)
        self.assertEqual(quitar(h), plantilla.replace("{V4}", "../").replace("{DOCS}", "").replace("{INICIO}", "../"), "Datos/Metodología/Fuentes")
        self.assertIn("cabecera.html", _txt("NO_PUBLICAR.txt").split())  # la plantilla no se publica

    def test_sin_nomenclatura_m_en_texto_visible(self):
        # T-423 (D-165): ningún «M01…M08» en lo que se lee; los ids de datos («M06» como clave exacta) y los ficheros no cuentan (T-313)
        m0 = re.compile(r"\bM0[1-8]\b")
        def html(t):
            t = re.sub(r"<!--.*?-->|<script\b.*?</script>|<style\b.*?</style>", " ", t, flags=re.S)
            return re.sub(r"<[^>]+>", " ", t) + " ".join(re.findall(r'(?:aria-label|title|alt|placeholder)="([^"]*)"', t))
        def js(t):
            t = re.sub(r"/\*.*?\*/|(?<![:\\])//[^\n]*", " ", t, flags=re.S)
            lits = re.findall(r'"((?:[^"\\\n]|\\.)*)"|\'((?:[^\'\\\n]|\\.)*)\'', t)
            return " ".join(a or b for a, b in lits if not re.fullmatch(r"M0[1-8]", a or b))
        def md(t):
            return re.sub(r"```.*?```|`[^`]*`|\]\([^)]*\)|https?://\S+", " ", t, flags=re.S)
        textos = {f: html(_txt(f)) for f in ("index.html", "comprender.html", "mapa/index.html")}
        textos.update({f: js(_txt(f)) for f in ("app.js", "mapa/explorar.js", "mapa/dv.js")})
        textos.update({d.name: md(d.read_text(encoding="utf-8")) for d in sorted(DOCS.glob("*.md"))})
        textos["overrides/main.html"] = html((DOCS.parent / "overrides/main.html").read_text(encoding="utf-8"))
        self.assertIn("metodo.md", textos)  # guardia: Metodología entra
        for f, t in textos.items():
            self.assertIsNone(m0.search(t), f"{f}: {m0.findall(t)[:5]}")
        self.assertIsNotNone(m0.search(js('const a="M06 publicado";')))  # guardia: el extractor sí ve literales con texto

    def test_menu_unico_e_investigacion(self):
        # T-423: un solo menú en portada, Comprender y Explorar; «Investigación» enlaza Datos, Metodología y Fuentes
        # opción A del propietario (19-11): Datos y Fuentes fuera del menú y de cualquier enlace visible de la V4
        menu = ["Inicio", "Comprender", "Explorar", "Metodología"]
        for pag in ("index.html", "comprender.html", "mapa/index.html"):
            nav = re.search(r'<nav class="main-nav"[^>]*>(.*?)</nav>', _txt(pag), re.S).group(1)
            self.assertEqual(re.findall(r">([^<]+)</a>", nav), menu, pag)
        inv = re.search(r'id="investigacion".*?</section>', _txt("index.html"), re.S).group(0)
        self.assertIn('href="docs/metodo.html"', inv)
        zens = (DOCS.parent / "overrides/main.html").read_text(encoding="utf-8")
        toml = (DOCS.parent / "zensical.toml").read_text(encoding="utf-8")
        for t in [_txt(p) for p in ("index.html", "comprender.html", "mapa/index.html", "cabecera.html", "app.js")] + [zens, toml, (DOCS / "index.md").read_text(encoding="utf-8")]:
            self.assertNotRegex(t, r"datos-abiertos\.(html|md)|fuentes\.(html|md)")

    def test_sin_nomenclatura_vieja(self):
        for pag in PAGINAS:
            self.assertIsNone(re.search(r"\bM0[1-8]\b", _txt(pag)), pag)

    def test_catalogo_doi_vacio(self):
        self.assertIn("window.DDD_MAPS = [];", _txt("catalogo-mapas.js"))

    def test_sin_recursos_externos_ni_rutas_privadas(self):
        malo = re.compile(r"/Users/|/home/|C:\\|chatgpt\.com|account_id|@[a-z0-9.-]+\.[a-z]{2,}", re.I)
        for f in PAGINAS + ["styles.css", "app.js", "catalogo-mapas.js", "assets-manifest.json", "NOTICE.md"]:
            self.assertIsNone(malo.search(_txt(f)), f)
        for pag in PAGINAS:
            for u in re.findall(r'(?:src|href)="(https?://[^"]+)"', re.sub(r'<link rel="canonical"[^>]*>', "", _txt(pag))):
                self.assertTrue(u.startswith(("https://orcid.org/", "https://www.linkedin.com/")), f"{pag}: {u}")
        self.assertNotRegex(_txt("styles.css"), r"url\(\s*['\"]?https?:|@import")

    def test_webp_coinciden_con_manifiesto(self):
        man = json.loads(_txt("assets-manifest.json"))
        self.assertEqual(len(man["assets"]), 9)  # 3 originales de la autora + 2 copias reducidas (T-442) + vista previa e iconos (T-451)
        for a in man["assets"]:
            if a["source_type"] == "derived":  # toda copia declara su original con el sha256 del manifiesto
                self.assertEqual(a["derived_from_sha256"], next(o["sha256"] for o in man["assets"] if o["file"] == a["derived_from"]), a["file"])
        for a in man["assets"]:
            h = hashlib.sha256((V4 / a["file"]).read_bytes()).hexdigest()
            self.assertEqual(h, a["sha256"], a["file"])
        h = hashlib.sha256((V4 / "assets/congreso.webp").read_bytes()).hexdigest()
        self.assertEqual(h, SHA["congreso.webp"])

    def test_copias_reducidas_para_movil(self):
        # T-442 (D-192): cada copia reducida declara su original con el sha256 de la autora y pesa menos; la portada la sirve solo en pantallas pequeñas
        man = {a["file"]: a for a in json.loads(_txt("assets-manifest.json"))["assets"]}
        portada = _txt("index.html")
        for copia, original, ancho in (("assets/congreso-760.webp", "assets/congreso.webp", 600), ("assets/mapa_espana-320.webp", "assets/mapa_espana.webp", 1000)):
            e = man[copia]
            self.assertEqual((e["source_type"], e["derived_from"], e["derived_from_sha256"]), ("derived", original, man[original]["sha256"]))
            self.assertLess((V4 / copia).stat().st_size, (V4 / original).stat().st_size)
            self.assertIn(f'<source media="(max-width:{ancho}px)" srcset="{copia}"', portada)
            self.assertIn(f'<img src="{original}"', portada)  # el original sigue para el resto de pantallas
        self.assertEqual(hashlib.sha256((V4 / "assets/congreso.webp").read_bytes()).hexdigest(), SHA["congreso.webp"])

    def test_video_configurable_y_vacio(self):
        cfg = json.loads(_txt("video.json"))
        self.assertEqual(set(cfg), {"base", "video", "poster", "subtitulos", "transcripcion"})
        # dominio propio de vídeos y fichero del propietario (19-11); sin póster, subtítulos ni transcripción por ahora
        self.assertEqual((cfg["base"], cfg["video"]), ("https://media.diputadodedistrito.es/", "Video_DDD.mp4"))
        for k in ("poster", "subtitulos", "transcripcion"):
            self.assertEqual(cfg[k], "", k)
        # la URL del bucket solo vive en video.json, nunca fija en el código
        for f in PAGINAS + ["app.js", "styles.css"]:
            self.assertNotIn("r2.dev", _txt(f), f)
        h = _txt("index.html")
        self.assertRegex(h, r'<section[^>]*data-video[^>]*\bhidden\b')
        self.assertNotIn("<video", h)  # el reproductor no se carga hasta pulsar
        self.assertNotRegex(_txt("app.js"), r"autoplay")

    def test_metodologia_en_lenguaje_llano(self):
        # T-423 (propietario, 19-11): la Metodología es para el público general: capítulos en español llano, sin jerga ni códigos internos
        md = (DOCS / "metodo.md").read_text(encoding="utf-8")
        texto = re.sub(r"<!--.*?-->|^---\n.*?\n---\n", " ", md, flags=re.S)
        titulos = re.findall(r"(?m)^#{1,6} (.+)$", texto) + re.findall(r"(?m)^title: (.+)$", md)
        self.assertGreaterEqual(len(titulos), 9)
        codigos = re.compile(r"\b[PM]\d{2}\b")
        for t in titulos:
            self.assertIsNone(codigos.search(t), t)
        self.assertIsNone(codigos.search(texto), codigos.findall(texto)[:5])
        for j in JERGA:
            self.assertIsNone(re.search(r"(?i)\b%s\b" % re.escape(j), texto), j)
        self.assertRegex(md, r"(?m)^hide:\n  - navigation$")  # sin el menú de la izquierda
        self.assertIn("Huesca", texto)  # ejemplo concreto con una provincia real
        self.assertIn("no tiene valor oficial", texto)

    def test_comprender_para_el_publico_general(self):
        # T-423: Comprender cuenta por qué importa y qué cambia (el cómo, en Metodología); sin jerga ni códigos; con cifras de la fuente
        h = _txt("comprender.html")
        visible = re.sub(r"<!--.*?-->|<script\b.*?</script>|<style\b.*?</style>|<head>.*?</head>", " ", h, flags=re.S)
        texto = re.sub(r"<[^>]+>", " ", visible)
        titulos = [re.sub(r"<[^>]+>", "", t) for t in re.findall(r"<h[1-3][^>]*>(.*?)</h[1-3]>", visible, re.S)]
        self.assertGreaterEqual(len(titulos), 6)
        codigos = re.compile(r"\b[PM]\d{2}\b")
        self.assertIsNone(codigos.search(texto), codigos.findall(texto)[:5])
        for j in JERGA:
            self.assertIsNone(re.search(r"(?i)\b%s\b" % re.escape(j), texto), j)
        self.assertNotIn("Publicaciones y datos", texto)
        for t in ("Qué cambia", "Tu distrito", "La doble vuelta", "Qué no es", "Para saber más"):
            self.assertIn(t, titulos)
        # 350 escaños y 407 distritos: suma de «escanos» y «k407» de visor/v2/datos/provincias.json (Huesca: 3 → 2)
        prov = json.loads((V4.parent / "v2/datos/provincias.json").read_text(encoding="utf-8"))["features"]
        self.assertEqual((sum(f["properties"]["escanos"] for f in prov), sum(f["properties"]["k407"] for f in prov)), (350, 407))
        hu = next(f["properties"] for f in prov if f["properties"]["nombre"] == "Huesca")
        self.assertEqual((hu["escanos"], hu["k407"]), (3, 2))
        for t in ("<strong>350</strong> escaños", "<strong>407</strong> distritos", "Hoy elige 3 diputados", "tendría 2 distritos"):
            self.assertIn(t, h)
        for ref in ('href="mapa/"', 'href="docs/metodo.html"'):
            self.assertIn(ref, re.search(r'class="routes saber-mas".*?</section>', h, re.S).group(0))

    def test_pie_identico_con_reserva_y_sin_auditoria(self):
        # T-423: un solo pie (visor/v4/pie.html) en todas las páginas, con la reserva de acciones legales visible y sin enlace a la auditoría
        pie = _txt("pie.html").split("-->\n", 1)[1].strip()
        self.assertIn("El autor se reserva el ejercicio de las acciones legales", pie)
        self.assertNotIn("<a ", pie)
        zens = (DOCS.parent / "overrides/main.html").read_text(encoding="utf-8")
        for nombre, t in [(p, _txt(p)) for p in ("index.html", "comprender.html", "auditoria-registro.html", "mapa/index.html")] + [("docs", zens)]:
            pies = re.findall(r'<footer class="footer[^"]*">.*?</footer>', t, re.S)
            self.assertEqual(pies, [pie], nombre)
        self.assertIn("pie.html", _txt("NO_PUBLICAR.txt").split())

    def test_video_desplegado_sin_autoplay(self):
        # T-423: reproductor visible sin pulsar nada, con su fotograma o póster; sin reproducción automática ni sonido
        import shutil, subprocess
        if not shutil.which("node"):
            self.skipTest("sin node")
        r = subprocess.run(["node", str(V4.parent.parent / "tests/test_visor_v4_video.js")], capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_doble_vuelta_en_comprender(self):
        h = _txt("comprender.html")
        self.assertIn('id="doble-vuelta"', h)
        for t in ("Izquierdas", "Nacionalistas", "Derecha nacional", "Simulación sin valor oficial", "mapa/?regla=tres"):
            self.assertIn(t, h)
        self.assertIn("tokens-bloques.css", h)
        # texto definitivo del propietario (19-11), con las correcciones ortográficas evidentes
        self.assertIn("La doble vuelta garantiza que el diputado sea elegido por la mayoría de su distrito. Si ningún candidato obtiene mayoría "
                      "absoluta de los votos a candidaturas en la primera votación, los dos más votados irán a la segunda. Así, las minorías pueden negociar apoyos y hacer "
                      "públicos sus acuerdos antes de la elección definitiva. Así aseguramos que el ciudadano tenga la última palabra, no los partidos.", h)
        for malo in ("artimetica", "irana", "Asi "):
            self.assertNotIn(malo, h)

    def test_contraste_de_tokens_de_bloques(self):
        css = _txt("tokens-bloques.css")

        def lum(hexc):
            c = [int(hexc[i:i + 2], 16) / 255 for i in (1, 3, 5)]
            c = [v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4 for v in c]
            return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]

        def ratio(a, b):
            la, lb = sorted((lum(a), lum(b)), reverse=True)
            return (la + 0.05) / (lb + 0.05)

        claro = dict(re.findall(r"--(izq|nac|pat|sin):(#[0-9a-f]{6})", css.split("@media")[0]))
        oscuro = dict(re.findall(r"--(izq|nac|pat|sin):(#[0-9a-f]{6})", css.split("[data-theme=dark]{")[1]))
        self.assertEqual(set(claro), {"izq", "nac", "pat", "sin"})
        self.assertEqual(set(oscuro), {"izq", "nac", "pat", "sin"})
        # texto/objetos: WCAG 2.1 ≥ 4,5 sobre #fffdf8 (claro) y sobre #14181a y #0b0d0e (oscuro)
        for k, v in claro.items():
            self.assertGreaterEqual(ratio(v, "#fffdf8"), 4.5, f"claro {k}")
        for k, v in oscuro.items():
            for fondo in ("#14181a", "#0b0d0e"):
                self.assertGreaterEqual(ratio(v, fondo), 4.5, f"oscuro {k} sobre {fondo}")
        # valores literales de T-413 §2 / D-172
        self.assertEqual((claro["izq"], oscuro["izq"]), ("#b3261e", "#ff8a80"))

    def test_lang_y_una_h1(self):
        for pag in PAGINAS:
            h = _txt(pag)
            self.assertIn('<html lang="es"', h, pag)
            self.assertEqual(len(re.findall(r"<h1[ >]", h)), 1, pag)


if __name__ == "__main__":
    unittest.main()
