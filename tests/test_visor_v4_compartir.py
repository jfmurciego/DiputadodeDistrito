"""T-451: vista previa al compartir de la V4 (og:image, twitter:*, iconos). Falla si una página publicada apunta a una imagen o un icono
que no existe, o si faltan las etiquetas que leen WhatsApp, X y similares."""
import re
import struct
import unittest
from pathlib import Path

V4 = Path(__file__).resolve().parents[1] / "visor" / "v4"
DOM = "https://diputadodedistrito.es/"
PUBLICAS = ("index.html", "comprender.html", "mapa/index.html")  # las páginas públicas de la V4 (las demás no se publican)
META = re.compile(r'<meta (?:property|name)="([^"]+)" content="([^"]*)">')
ENLACE = re.compile(r'<link rel="(icon|apple-touch-icon)"[^>]*?href="([^"]+)"')


def no_publicar():
    return {l.strip() for l in (V4 / "NO_PUBLICAR.txt").read_text(encoding="utf-8").splitlines() if l.strip() and not l.startswith("#")}


def paginas_publicadas():
    fuera = no_publicar()
    return sorted(p.relative_to(V4).as_posix() for p in V4.rglob("*.html")
                  if not any(p.relative_to(V4).as_posix() == f or p.relative_to(V4).as_posix().startswith(f + "/") for f in fuera))


def metas(texto):
    return dict(META.findall(texto))


def referencias_rotas(texto: str, rel: str, raiz: Path = V4) -> list[str]:
    """Imágenes de vista previa (og:image, twitter:image) e iconos que no existen en `raiz` (la V4 se publica en la raíz del sitio)."""
    rotas = []
    for clave, valor in META.findall(texto):
        if clave in ("og:image", "twitter:image"):
            if not valor.startswith(DOM) or not (raiz / valor[len(DOM):]).is_file():
                rotas.append(f"{clave}={valor}")
    for tipo, href in ENLACE.findall(texto):
        destino = (raiz / rel).parent / href
        if "://" in href or href.startswith("/") or not destino.resolve().is_file() or raiz.resolve() not in destino.resolve().parents:
            rotas.append(f"{tipo}={href}")
    return rotas


def medidas_jpeg(datos: bytes) -> tuple[int, int]:
    i = 2
    while i < len(datos):
        marca, largo = datos[i + 1], struct.unpack(">H", datos[i + 2:i + 4])[0]
        if marca in (0xC0, 0xC1, 0xC2):
            alto, ancho = struct.unpack(">HH", datos[i + 5:i + 9])
            return ancho, alto
        i += 2 + largo
    raise ValueError("sin SOF")


class VistaPrevia(unittest.TestCase):
    def test_ninguna_pagina_publicada_apunta_a_un_fichero_que_no_existe(self):
        paginas = paginas_publicadas()
        self.assertTrue(set(PUBLICAS) <= set(paginas), paginas)
        for rel in paginas:
            with self.subTest(rel):
                self.assertEqual(referencias_rotas((V4 / rel).read_text(encoding="utf-8"), rel), [])

    def test_control_negativo(self):
        malo = ('<meta property="og:image" content="https://diputadodedistrito.es/assets/no-existe.jpg">'
                '<meta name="twitter:image" content="https://otro.ejemplo/x.jpg">'
                '<link rel="icon" href="assets/no-existe.ico"><link rel="apple-touch-icon" href="../../fuera.png">')
        self.assertEqual(len(referencias_rotas(malo, "index.html")), 4)

    def test_etiquetas_de_cada_pagina_publica(self):
        for rel in PUBLICAS:
            with self.subTest(rel):
                t = (V4 / rel).read_text(encoding="utf-8")
                m = metas(t)
                canonica = re.search(r'<link rel="canonical" href="([^"]+)">', t).group(1)
                self.assertEqual(m["og:url"], canonica)
                self.assertEqual(m["twitter:card"], "summary_large_image")
                self.assertEqual(m["twitter:title"], m["og:title"])
                self.assertEqual(m["twitter:description"], m["og:description"])
                self.assertEqual(m["twitter:image"], m["og:image"])
                self.assertEqual(m["og:image"], DOM + "assets/compartir-1200x630.jpg")
                self.assertTrue(m["og:image:alt"] and m["twitter:image:alt"])
                self.assertEqual(m["theme-color"], "#0b0d0e")
                self.assertEqual(sorted(tipo for tipo, _ in ENLACE.findall(t)), ["apple-touch-icon", "icon", "icon"])
                self.assertNotIn("OG-IMAGEN-PENDIENTE", t)

    def test_imagen_e_iconos(self):
        jpg = (V4 / "assets/compartir-1200x630.jpg").read_bytes()
        self.assertEqual(jpg[:2], b"\xff\xd8")
        m = metas((V4 / "index.html").read_text(encoding="utf-8"))
        self.assertEqual(medidas_jpeg(jpg), (int(m["og:image:width"]), int(m["og:image:height"])))
        self.assertEqual(medidas_jpeg(jpg), (1200, 630))
        self.assertLess(len(jpg), 300_000)  # peso razonable para WhatsApp y X
        for nombre, lado in (("icono-32.png", 32), ("apple-touch-icon.png", 180)):
            png = (V4 / "assets" / nombre).read_bytes()
            self.assertEqual(png[:8], b"\x89PNG\r\n\x1a\n")
            self.assertEqual(struct.unpack(">II", png[16:24]), (lado, lado), nombre)
        ico = (V4 / "assets/favicon.ico").read_bytes()
        self.assertEqual(ico[:4], b"\x00\x00\x01\x00")
        self.assertEqual(struct.unpack("<H", ico[4:6])[0], 3)  # 16, 32 y 48 px

    def test_la_tarjeta_fuente_no_se_publica(self):
        self.assertIn("compartir-tarjeta.html", no_publicar())
        self.assertNotIn("compartir-tarjeta.html", paginas_publicadas())


if __name__ == "__main__":
    unittest.main()
