"""T-429: textos de la V4 (regla «Mayoría simple», doble vuelta), etiquetas para compartir y línea de hipótesis."""
import re, unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
V4 = ROOT / "visor/v4"
PAGINAS = {"index.html": "/", "comprender.html": "/comprender.html", "mapa/index.html": "/mapa/", "auditoria-registro.html": "/auditoria-registro.html"}
DOM = "https://diputadodedistrito.es"


class TextosV4(unittest.TestCase):
    def test_ninguna_regla_de_hoy_con_mayoria_simple(self):
        for p in list(V4.rglob("*.html")) + list(V4.rglob("*.js")) + [ROOT / "documentacion_publica/docs/metodo.md"]:
            t = p.read_text(encoding="utf-8")
            self.assertNotIn("regla de hoy", t.lower(), p.name)
            self.assertNotIn(">Más votado<", t, p.name)
            self.assertNotIn("mayoría aritmética", t, p.name)
        dv = (V4 / "mapa/dv.js").read_text(encoding="utf-8")
        self.assertIn("No es el sistema actual", dv)
        self.assertIn("Mayoría simple en el distrito", (V4 / "mapa/index.html").read_text(encoding="utf-8"))
        self.assertIn("No es el sistema actual", (ROOT / "documentacion_publica/docs/metodo.md").read_text(encoding="utf-8"))

    def test_frase_del_propietario_intacta(self):
        self.assertIn("No sabes qué diputado es el tuyo.", (V4 / "comprender.html").read_text(encoding="utf-8"))
        self.assertIn("mayoría absoluta de los votos a candidaturas", (V4 / "comprender.html").read_text(encoding="utf-8"))

    def test_etiquetas_para_compartir(self):
        for rel, ruta in PAGINAS.items():
            t = (V4 / rel).read_text(encoding="utf-8")
            for k in ("og:title", "og:description", "og:url", "og:image"):
                self.assertRegex(t, rf'<meta property="{k}" content="[^"]+"', f"{rel}: {k}")
            self.assertIn(f'<meta property="og:url" content="{DOM}{ruta}">', t, rel)
            self.assertIn(f'<link rel="canonical" href="{DOM}{ruta}">', t, rel)
            self.assertIn('<meta name="twitter:card" content="summary_large_image">', t, rel)
            self.assertIn(f'content="{DOM}/assets/compartir-1200x630.jpg"', t, rel)
        d = (ROOT / "documentacion_publica/overrides/main.html").read_text(encoding="utf-8")
        for k in ('rel="canonical"', 'property="og:title"', 'property="og:description"', 'property="og:url"', 'property="og:image"', 'twitter:card'):
            self.assertIn(k, d)

    def test_linea_de_hipotesis_en_la_ficha(self):
        js = (V4 / "mapa/explorar.js").read_text(encoding="utf-8")
        self.assertIn("El trasvase de votos entre partidos del mismo bloque es una hipótesis de simulación, no un comportamiento observado.", js)


if __name__ == "__main__":
    unittest.main()
