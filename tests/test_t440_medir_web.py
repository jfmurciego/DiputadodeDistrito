"""T-440: medición de la web a petición en P90 (repository_dispatch «medir-web»), solo lectura y sin secretos."""
import unittest
from pathlib import Path

import yaml

from herramientas import medir_web as m

WF = Path(__file__).resolve().parents[1] / ".github/workflows/p90-automatico.yml"


class Falso:
    def __init__(self, salida):
        self.stdout = salida


class MedirWeb(unittest.TestCase):
    def test_compresion_y_valores(self):
        vistos = []

        def ejecutar(args, **_):
            vistos.append(args)
            return Falso("200 0.120 0.450 12345" if "--compressed" in args else "200 0.100 0.900 54321")

        self.assertEqual(m.medir("https://x/", True, ejecutar), {"codigo": 200, "ttfb": 0.12, "total": 0.45, "bytes": 12345})
        self.assertEqual(m.medir("https://x/", False, ejecutar)["bytes"], 54321)
        self.assertIn("Accept-Encoding: identity", vistos[1])
        self.assertNotIn("--compressed", vistos[1])

    def test_tabla_tres_intentos_por_fila_y_fallo_visible(self):
        texto, ok = m.tabla("https://x", 3, lambda a, **_: Falso("404 0.01 0.02 10" if a[-1].endswith("/") else "200 0.1 0.2 1000"))
        filas = [l for l in texto.splitlines() if l.startswith("| ") and "Compresión" not in l]
        self.assertEqual(len(filas), 2 * len(m.URLS))
        self.assertIn("| Portada | sí | 404 | 10 (10/10/10) | 20 (20/20/20) | 10 |", filas)
        self.assertIn("1.000", texto)
        self.assertEqual(ok, 3 * (2 * len(m.URLS) - 4))  # la portada (/) y el mapa (/mapa/) dan 404 en el doble

    def test_salida_vacia_de_curl_no_rompe(self):
        self.assertEqual(m.medir("https://x", True, lambda a, **_: Falso(""))["codigo"], 0)

    def test_job_a_peticion_solo_lectura_sin_secretos(self):
        texto = WF.read_text(encoding="utf-8")
        wf = yaml.safe_load(texto)
        on = wf.get(True, wf.get("on"))
        self.assertEqual(on["repository_dispatch"], {"types": ["medir-web"]})
        self.assertNotIn("workflow_dispatch", on)
        j = wf["jobs"]["medir_web"]
        self.assertEqual(j["if"], "${{ github.event_name == 'repository_dispatch' && github.event.action == 'medir-web' }}")
        self.assertEqual(j["permissions"], {"contents": "read"})
        bloque = yaml.safe_dump(j)
        self.assertNotIn("secrets.", bloque)
        self.assertIn("herramientas/medir_web.py", bloque)
        # ningún otro job sin `if` propio ni dependencia corre con este evento
        for nombre, otro in wf["jobs"].items():
            if nombre != "medir_web":
                self.assertTrue(otro.get("if") or otro.get("needs"), nombre)
                self.assertNotIn("repository_dispatch", str(otro.get("if", "")), nombre)


if __name__ == "__main__":
    unittest.main()
