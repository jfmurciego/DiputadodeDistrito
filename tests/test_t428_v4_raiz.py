"""T-428 (D-184): la V4 es la versión oficial y se sirve en la raíz del sitio.

PROYECTO: Diputado de Distrito · VERSIÓN: 1.0.0 · FECHA: 2026-11-20 · ESTADO: candidato · ANTERIOR: ninguna (fichero nuevo)
Monta el sitio con las MISMAS líneas de copia de P40 (leídas del workflow) y los mismos pasos de portada (V2 → V3 → V4) sobre el visor real.
Esperados literales (rutas públicas), no recalculados como lo hace el código.
"""
import hashlib
import posixpath
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "herramientas"))
import preparar_portada_v2  # noqa: E402
import preparar_portada_v3  # noqa: E402
import preparar_portada_v4  # noqa: E402

WF = ROOT / ".github" / "workflows" / "p40-publicacion.yml"
HREF = re.compile(r'(?:href|src)="([^"]*)"')


def _pasos():
    return {s.get("name"): s for s in yaml.safe_load(WF.read_text(encoding="utf-8"))["jobs"]["publicar"]["steps"]}


def _sha_arbol(d: Path):
    return {str(p.relative_to(d)): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(d.rglob("*")) if p.is_file()}


def construir(site: Path, hasta_v3=False):
    """Copias del paso «Construir sitio candidato completo» (visor raíz, v2, v3, v4 y NO_PUBLICAR) y los pasos de portada."""
    run = _pasos()["Construir sitio candidato completo"]["run"]
    lineas = [l.split("  #")[0].strip() for l in run.splitlines()
              if l.strip().startswith(("rm -rf /tmp/site-candidate &&", "cp visor/", "cp -R visor/v2/", "mkdir -p /tmp/site-candidate/v4", "while IFS="))]
    assert len(lineas) == 7, lineas  # mkdir, raíz, nacional, v2, v3, v4 y NO_PUBLICAR: si cambian, este test se revisa
    for l in lineas:
        subprocess.run(["bash", "-eo", "pipefail", "-c", l.replace("/tmp/site-candidate", str(site))], cwd=ROOT, check=True)
    preparar_portada_v2.preparar_portada(site)
    preparar_portada_v3.preparar_portada_v3(site)
    if not hasta_v3:
        preparar_portada_v4.preparar_portada_v4(site)


def resolver(pagina: str, ref: str):
    """URL pública (ruta absoluta) de `ref` en la página `pagina`; None si sube por encima de la raíz del dominio."""
    if ref.startswith("/"):
        return ref
    base = posixpath.dirname("/" + pagina)
    partes = []
    for p in (base.strip("/").split("/") if base.strip("/") else []) + ref.split("/"):
        if p == "..":
            if not partes:
                return None
            partes.pop()
        elif p not in ("", "."):
            partes.append(p)
    dir_final = ref.endswith("/") or ref.split("/")[-1] in ("", ".", "..")
    return "/" + "/".join(partes) + ("/" if dir_final and partes else "")


class Sitio(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.antes = Path(cls.tmp.name) / "antes"
        cls.site = Path(cls.tmp.name) / "sitio"
        construir(cls.antes, hasta_v3=True)
        construir(cls.site)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def html(self, p):
        return (self.site / p).read_text(encoding="utf-8")

    def test_raiz_es_la_portada_v4(self):
        self.assertIn("url=v3/", (self.antes / "index.html").read_text(encoding="utf-8"))  # guardia: antes la raíz redirigía a la V3
        self.assertEqual((self.site / "index.html").read_bytes(), (ROOT / "visor/v4/index.html").read_bytes())
        for f in ("comprender.html", "mapa/index.html", "mapa/explorar.js", "app.js", "styles.css", "assets/logotipo_espana.webp"):
            self.assertEqual((self.site / f).read_bytes(), (ROOT / "visor/v4" / f).read_bytes(), f)
        for e in ("NO_PUBLICAR.txt", "cabecera.html", "auditoria-registro.html", "mapa/ejemplo"):
            self.assertFalse((self.site / e).exists(), e)  # lo no publicable tampoco llega a la raíz

    def test_v3_identica(self):
        self.assertEqual(_sha_arbol(self.site / "v3"), _sha_arbol(self.antes / "v3"))
        self.assertEqual(set(_sha_arbol(self.site / "v3")), {"index.html", "v3.css", "v3.js", "calendario.json"})
        self.assertEqual(_sha_arbol(self.site / "v2"), _sha_arbol(self.antes / "v2"))

    def test_ningun_href_visible_acaba_en_index_html(self):
        paginas = ["index.html", "comprender.html", "mapa/index.html", "v4/index.html", "v4/comprender.html", "v4/mapa/index.html"]
        textos = {p: self.html(p) for p in paginas}
        textos["docs (Zensical)"] = (ROOT / "documentacion_publica/overrides/main.html").read_text(encoding="utf-8")
        textos["docs/index.md"] = (ROOT / "documentacion_publica/docs/index.md").read_text(encoding="utf-8")
        mal = re.compile(r'(?:href="|\]\()[^")]*index\.html')
        self.assertIsNotNone(mal.search('<a href="../index.html">'))  # guardia
        for p, t in textos.items():
            self.assertIsNone(mal.search(t), p)
        for p in ("index.html", "comprender.html", "mapa/index.html"):
            nav = re.search(r'<nav class="main-nav"[^>]*>(.*?)</nav>', self.html(p), re.S).group(1)
            inicio = re.search(r'<a href="([^"]*)"[^>]*>Inicio</a>', nav).group(1)
            marca = re.search(r'class="brand" href="([^"]*)"', self.html(p)).group(1)
            self.assertEqual((resolver(p, inicio), resolver(p, marca)), ("/", "/"), p)  # «Inicio» y la marca llevan a «/»
            self.assertFalse(inicio.startswith("/"), p)  # relativo: vale en el dominio y en la ruta de proyecto de Pages

    def test_sin_rutas_absolutas_en_la_v4(self):
        # Planificador (20-11): solo rutas relativas, para que valga en el dominio propio, en github.io (ruta de proyecto) y en otro alojamiento
        abs_ = re.compile(r'(?:href|src|action)="/(?!/)')
        self.assertIsNotNone(abs_.search('<a href="/">'))  # guardia
        self.assertIsNone(abs_.search('<a href="//cdn.example">'))  # «//» es otra cosa (protocolo relativo) y aquí no lo hay
        fuentes = sorted((ROOT / "visor/v4").rglob("*.html")) + [ROOT / "documentacion_publica/overrides/main.html"]
        fuentes += [self.site / p for p in ("v4/index.html", "v4/comprender.html", "v4/mapa/index.html")]
        for p in fuentes:
            self.assertIsNone(abs_.search(p.read_text(encoding="utf-8")), p)

    def test_menu_resuelve_a_rutas_publicas(self):
        esperado = {"Inicio": "/", "Comprender": "/comprender.html", "Explorar": "/mapa/", "Metodología": "/docs/metodo.html"}
        for p in ("index.html", "comprender.html", "mapa/index.html"):
            nav = re.search(r'<nav class="main-nav"[^>]*>(.*?)</nav>', self.html(p), re.S).group(1)
            got = {t: resolver(p, h) for h, t in re.findall(r'<a href="([^"]*)"[^>]*>([^<]+)</a>', nav)}
            self.assertEqual(got, esperado, p)
        zens = (ROOT / "documentacion_publica/overrides/main.html").read_text(encoding="utf-8")
        nav = re.search(r'<nav class="main-nav"[^>]*>(.*?)</nav>', zens, re.S).group(1)
        got = {t: resolver("docs/metodo.html", h) for h, t in re.findall(r'<a href="([^"]*)"[^>]*>([^<]+)</a>', nav)}
        self.assertEqual(got, esperado)

    def test_recursos_locales_existen_en_el_sitio(self):
        for p in ("index.html", "comprender.html", "mapa/index.html"):
            for ref in HREF.findall(self.html(p)):
                ref = ref.split("#")[0].split("?")[0]
                if not ref or ref.startswith(("http", "mailto:", "docs/", "../docs/")):
                    continue  # docs/ la genera Zensical en P40 (lo comprueba test_visor_v4_base)
                url = resolver(p, ref)
                self.assertIsNotNone(url, f"{p}: {ref} sube por encima de la raíz")
                destino = self.site / url.lstrip("/")
                self.assertTrue(destino.is_file() or (destino / "index.html").is_file(), f"{p}: {ref} → {url}")

    def test_rutas_de_datos_de_explorar(self):
        js = self.html("mapa/explorar.js")
        rutas = set(re.findall(r'"((?:\.\./)+[^"]*)"', js))
        self.assertTrue(rutas, "Explorar sin rutas del sitio")  # guardia
        publicas = {r: resolver("mapa/index.html", r) for r in rutas}
        self.assertNotIn(None, publicas.values(), publicas)  # ninguna sube por encima de la raíz del dominio
        for esperado in ("/v2/datos/provincias.json", "/v2/datos/comunidades.json", "/datos/INDEX.json",
                         "/data/viewer-results.json", "/datos/catalogo_procedencia.json", "/v2/datos/territorial.json"):
            self.assertIn(esperado, publicas.values())
        for r in ("/v2/datos/provincias.json", "/v2/datos/comunidades.json"):
            self.assertTrue((self.site / r.lstrip("/")).is_file(), r)  # salen de visor/v2, copiado entero

    def test_v4_redirige_a_la_raiz(self):
        esperado = {"v4/index.html": "/", "v4/comprender.html": "/comprender.html", "v4/mapa/index.html": "/mapa/"}
        self.assertEqual({str(p.relative_to(self.site)) for p in (self.site / "v4").rglob("*") if p.is_file()}, set(esperado))
        for p, url in esperado.items():
            t = self.html(p)
            destino = re.search(r'url=([^"]+)"', t).group(1)
            self.assertEqual(resolver(p, destino), url, p)
            self.assertIn(f'new URL("{destino}" + window.location.search + window.location.hash', t)  # conserva ?regla=… y #ancla

    def test_rutas_publicas_conservadas(self):
        for f in ("v1/index.html", "v2/index.html", "v3/index.html", "nacional/index.html", "v2/datos/provincias.json"):
            self.assertTrue((self.site / f).is_file(), f)
        v1 = self.html("v1/index.html")
        self.assertIn('<base href="../">', v1)
        for n in ("app.js", "escenarios.js", "styles.css"):
            self.assertEqual((self.site / "v1" / n).read_bytes(), (ROOT / "visor" / n).read_bytes(), n)
            self.assertIn(f'"v1/{n}"', v1)  # con base ../ → /v1/<n>, sin chocar con los de la V4 en la raíz

    def test_no_se_promociona_dos_veces(self):
        with self.assertRaises((ValueError, FileNotFoundError)):
            preparar_portada_v4.preparar_portada_v4(self.site)


class Workflow(unittest.TestCase):
    def test_orden_y_destino(self):
        nombres = list(_pasos())
        v3, v4 = nombres.index("Promocionar portada pública V3"), nombres.index("Promocionar la V4 como portada oficial (T-428)")
        dv = nombres.index("Doble vuelta de los territorios del Congreso para la V4 (D-172)")
        self.assertLess(v3, v4)
        self.assertLess(v4, dv)  # los datos de la doble vuelta se escriben ya en la raíz
        self.assertIn("--destino /tmp/site-candidate/mapa/datos", _pasos()[nombres[dv]]["run"])
        validar = _pasos()["Validar sitio candidato completo"]["run"]
        self.assertNotIn("url=v3/", validar)
        self.assertIn("<title>Diputado de Distrito | Portada</title>", validar)
        self.assertEqual(preparar_portada_v4.MARCA_V4 in (ROOT / "visor/v4/index.html").read_text(encoding="utf-8"), True)

    def test_paso_nuevo_pasa_bash_n(self):
        subprocess.run(["bash", "-n", "-c", _pasos()["Promocionar la V4 como portada oficial (T-428)"]["run"]], check=True)


if __name__ == "__main__":
    unittest.main()
