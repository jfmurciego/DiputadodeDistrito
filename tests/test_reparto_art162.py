"""Oráculo del reparto art. 162 (T-129). Valores esperados: anexo del RD 806/2026 transcrito en
configuracion/escanos_oficiales_congreso_2026.csv (sha256 9c9b48c1…); población INE 1-1-2025 en
docs/ESTUDIOS/modelo_nacional_2025_120000/fuente_poblacion.json (sha256 6a5f16d1…)."""
import csv
import hashlib
import json
import unittest
from pathlib import Path

from herramientas.reparto_art162 import repartir

R = Path(__file__).resolve().parents[1]
POB = R / "docs/ESTUDIOS/modelo_nacional_2025_120000/fuente_poblacion.json"
CSV26 = R / "configuracion/escanos_oficiales_congreso_2026.csv"
POB23 = R / "configuracion/poblacion_provincial_2022.json"  # pendiente de acreditar (fuente + sha256)
RES23 = R / "configuracion/resultados_oficiales_congreso_2023.csv"


def _sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def _poblacion(p):
    return {r["province_code"]: r["population"] for r in json.loads(p.read_text("utf-8"))["rows"]}


class Reparto(unittest.TestCase):
    def test_fuentes_con_huella(self):
        self.assertEqual(_sha(POB), "6a5f16d1bf354bebb1d05ad0f9afc350d8dc1c7ea251aac3ce6002e392b16a7c")
        self.assertEqual(_sha(CSV26), "9c9b48c1dcefe1aac327aa0211fc5f7c57130f83e5929dab25cbac352d182b8f")

    def test_padron_2025_frente_a_rd_2026(self):
        oficial = {r["codigo"]: int(r["escanos_2026"]) for r in
                   csv.DictReader(l for l in CSV26.open(encoding="utf-8") if not l.startswith("#"))}
        calc = repartir(_poblacion(POB))
        self.assertEqual(sum(calc.values()), 350)
        dif = {k for k in oficial if calc[k] != oficial[k]}
        # Pendiente de acreditar la cifra de población del RD; hoy solo difieren estas dos (241 hab. de margen).
        self.assertEqual(dif, {"13", "38"})
        self.assertEqual((calc["28"], calc["11"]), (38, 8))

    @unittest.skipUnless(POB23.exists(), "falta población provincial acreditada para 2023 (fuente + sha256)")
    def test_2023_reproduce_escanos_oficiales(self):
        oficial = {}
        for r in csv.DictReader(RES23.open(encoding="utf-8")):
            oficial[r["codigo"]] = int(r["escanos_circunscripcion"])
        self.assertEqual(repartir(_poblacion(POB23)), oficial)


if __name__ == "__main__":
    unittest.main()
