"""Reparto de la suite en grupos (T-50): partición completa, disjunta, determinista y equilibrada."""
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "herramientas"))

import repartir_tests as rt  # noqa: E402


class Reparto(unittest.TestCase):
    def test_particion_completa_y_disjunta(self):
        pesos = {f"m{i}": float((i * 37) % 23 + 1) for i in range(60)}
        for n in (1, 2, 5, 8):
            grupos = rt.repartir(pesos, n)
            self.assertEqual(len(grupos), n)
            todos = [m for g in grupos for m in g]
            self.assertEqual(sorted(todos), sorted(pesos))
            self.assertEqual(len(todos), len(set(todos)))

    def test_determinista_y_equilibrado(self):
        tiempos = json.loads((ROOT / "tests/tiempos_ci.json").read_text(encoding="utf-8"))["modulos"]
        a = rt.repartir(tiempos, 5)
        self.assertEqual(a, rt.repartir(dict(reversed(list(tiempos.items()))), 5))
        cargas = [sum(tiempos[m] for m in g) for g in a]
        self.assertLess(max(cargas) - min(cargas), max(tiempos.values()))
        self.assertLess(max(cargas), sum(tiempos.values()) / 5 * 1.15)

    def test_desconocidos_pesan_la_mediana(self):
        pesos = rt.pesos_de(["a", "b#3", "nuevo"], {"a": 10.0, "b": 2.0, "c": 4.0})
        self.assertEqual(pesos, {"a": 10.0, "b#3": 2.0, "nuevo": 4.0})

    def test_grupo_fuera_de_rango(self):
        with self.assertRaises(ValueError):
            rt.repartir({"a": 1.0}, 0)


if __name__ == "__main__":
    unittest.main()
