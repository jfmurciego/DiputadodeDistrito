# -*- coding: utf-8 -*-
"""T-294: contador propio sin datos personales en los visores (sustituye al bloque Cloudflare Web Analytics de T-174).

PROYECTO: Diputado de Distrito · VERSIÓN: 2.2.0 · FECHA: 2026-11-15 · ESTADO: candidato
ANTERIOR: legacy/tests/test_visor_analitica_v2.1.0_20261115.py
CAMBIOS 2.2.0: T-348, la frase de Cloudflare/NEL también en nacional y Congreso. 2.1.0: T-346, línea de Cloudflare/NEL en V1, V3 y textos.md. 2.0.0: el beacon es un único sendBeacon con la ruta al subdominio propio; V1, V2 y V3 lo llevan, nacional no; sin cookies ni almacenamiento.
"""
import re, unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
CON = ["visor/index.html", "visor/v2/index.html", "visor/v3/index.html"]
SIN = ["visor/nacional/index.html"]
SCRIPT = re.compile(r"(?s)<script>(.*?)</script>")
PROHIBIDO = re.compile(r"cookie|localStorage|sessionStorage|credentials|fetch\(|XMLHttpRequest|cloudflareinsights", re.I)
OSM_TXT = "el mapa de fondo lo sirve OpenStreetMap, que ve la dirección IP"
OSM_VISORES = {"visor/app.js", "visor/nacional/nacional.js", "visor/congreso/congreso.js"}
TEXTO = "No usa cookies ni guarda nada en tu dispositivo, no registra tu dirección IP"


class Contador(unittest.TestCase):
    def test_visores_con_contador_un_solo_beacon_limpio(self):
        for p in CON:
            html = (RAIZ / p).read_text(encoding="utf-8")
            propios = [s for s in SCRIPT.findall(html) if "contador." in s]
            self.assertEqual(len(propios), 1, p)
            self.assertIsNone(PROHIBIDO.search(propios[0]), p)
            self.assertNotIn("cloudflareinsights", html, p)

    def test_visores_sin_contador(self):
        for p in SIN:
            html = (RAIZ / p).read_text(encoding="utf-8")
            self.assertNotIn("contador.", html, p)
            self.assertNotIn("cloudflareinsights", html, p)

    def test_texto_de_transparencia_en_cada_visor(self):
        for p in ("visor/index.html", "visor/v3/index.html", "web/textos.md"):
            self.assertIn(TEXTO, (RAIZ / p).read_text(encoding="utf-8"), p)

    def test_linea_cloudflare_nel_en_cada_texto(self):
        # T-346: el sitio lo sirve Cloudflare; los informes NEL/Report-To del navegador incluyen la IP.
        for p in ("visor/index.html", "visor/v3/index.html", "web/textos.md"):
            tx = (RAIZ / p).read_text(encoding="utf-8")
            self.assertIn("el sitio lo sirve Cloudflare", tx, p)
            self.assertIn("NEL/Report-To, hacia a.nel.cloudflare.com", tx, p)
            self.assertIn("incluyen tu dirección IP", tx, p)
        for p in ("visor/nacional/index.html", "visor/congreso/index.html"):  # T-348: sin párrafo de contador
            tx = (RAIZ / p).read_text(encoding="utf-8")
            self.assertIn("el sitio lo sirve Cloudflare", tx, p)
            self.assertIn("NEL/Report-To, hacia a.nel.cloudflare.com", tx, p)
            self.assertNotIn("Medición de visitas", tx, p)

    def test_osm_declarado_solo_donde_se_cargan_teselas(self):
        cargan = {str(p.relative_to(RAIZ)) for p in (RAIZ / "visor").rglob("*.js")
                  if "vendor" not in p.parts and "tile.openstreetmap.org" in p.read_text(encoding="utf-8")}
        self.assertEqual(cargan, OSM_VISORES)  # V2 y V3 no cargan teselas: no lo declaran
        self.assertIn(OSM_TXT, (RAIZ / "visor/index.html").read_text(encoding="utf-8"))
        nota = "El mapa de fondo lo sirve OpenStreetMap, que ve la dirección IP de quien lo consulta."
        for p in ("visor/nacional/index.html", "visor/congreso/index.html"):
            self.assertIn(nota, (RAIZ / p).read_text(encoding="utf-8"), p)
        for p in ("visor/v2/index.html", "visor/v3/index.html", "web/textos.md"):
            self.assertNotIn("OpenStreetMap", (RAIZ / p).read_text(encoding="utf-8"), p)

    def test_rutas_servidas_estan_en_la_lista_blanca(self):
        rutas = re.search(r"RUTAS = \[(.*?)\]", (RAIZ / "herramientas/contador_worker/worker.js").read_text(encoding="utf-8")).group(1)
        for r in ('"/v1/"', '"/v2/"', '"/v3/"'):
            self.assertIn(r, rutas)


if __name__ == "__main__":
    unittest.main()
