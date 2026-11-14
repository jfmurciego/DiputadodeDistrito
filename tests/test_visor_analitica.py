# -*- coding: utf-8 -*-
"""T-294: contador propio sin datos personales en los visores (sustituye al bloque Cloudflare Web Analytics de T-174).

PROYECTO: Diputado de Distrito · VERSIÓN: 2.0.0 · FECHA: 2026-11-14 · ESTADO: candidato
ANTERIOR: legacy/tests/test_visor_analitica_v1.0.0_20261114.py
CAMBIOS: el beacon es un único sendBeacon con la ruta al subdominio propio; V1, V2 y V3 lo llevan, nacional no; sin cookies ni almacenamiento.
"""
import re, unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
CON = ["visor/index.html", "visor/v2/index.html", "visor/v3/index.html"]
SIN = ["visor/nacional/index.html"]
SCRIPT = re.compile(r"(?s)<script>(.*?)</script>")
PROHIBIDO = re.compile(r"cookie|localStorage|sessionStorage|credentials|fetch\(|XMLHttpRequest|cloudflareinsights", re.I)
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

    def test_rutas_servidas_estan_en_la_lista_blanca(self):
        rutas = re.search(r"RUTAS = \[(.*?)\]", (RAIZ / "herramientas/contador_worker/worker.js").read_text(encoding="utf-8")).group(1)
        for r in ('"/v1/"', '"/v2/"', '"/v3/"'):
            self.assertIn(r, rutas)


if __name__ == "__main__":
    unittest.main()
