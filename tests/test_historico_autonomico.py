"""T-133: paso A del histórico autonómico del Gestor 2.0 (plan por comunidad con su propio calendario).

VERSIÓN: 1.0.0 · FECHA: 2026-11-09
ANTERIOR: ninguna (fichero nuevo)
Valores esperados de fuentes independientes: fechas de las autonómicas de cada comunidad (calendario con fuente y
sha256: CyL 2011-05, 2015-05, 2019-05, 2022-02 y 2026-03 vigente; Galicia 2012-10, 2016-09, 2020-07 y 2024-02 vigente;
Madrid 2011-05, 2015-05, 2019-05, 2021-05 y 2023-05 vigente). No se fija qué comunidades están soportadas (cambia con
cada paso B): lo no soportado se prueba con una comunidad inexistente.
"""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "herramientas"))
import historico_autonomico as ha  # noqa: E402

ESPERADAS = {"galicia": ["201210", "201609", "202007"],
             "madrid": ["201105", "201505", "201905", "202105"],
             "castilla_y_leon": ["201105", "201505", "201905", "202202"]}


class Plan(unittest.TestCase):
    def test_cada_comunidad_con_sus_fechas_sin_la_vigente(self):
        for c, esperado in ESPERADAS.items():
            with self.subTest(c=c):
                self.assertEqual([e["eleccion"] for e in ha.elecciones(c)], esperado)

    def test_plan_de_las_tres_comunidades_con_paso_b(self):
        p = ha.plan(list(ESPERADAS), True)
        self.assertEqual({r["comunidad"]: r["elecciones"] for r in p["include"]}, ESPERADAS)
        self.assertEqual(p["prueba"]["comunidad"], "galicia")
        self.assertIn("| madrid | 201105, 201505, 201905, 202105 |", ha.plan_markdown(p))

    def test_sin_requisitos_se_omite_con_todas_y_falla_si_se_pide(self):
        p = ha.plan(["galicia", "narnia"], False)
        self.assertEqual([r["comunidad"] for r in p["include"]], ["galicia"])
        self.assertIn("sin composición", p["omitidos"]["narnia"])
        with self.assertRaisesRegex(ha.NoDisponible, "narnia: sin composición"):
            ha.plan(["galicia", "narnia"], True)
        with self.assertRaisesRegex(ha.NoDisponible, "Ninguna comunidad"):
            ha.plan(["narnia"], False)

    def test_comunidad_sin_dato_por_seccion_no_se_planifica(self):
        # Cantabria 2011-2019 y Asturias solo tienen dato por municipio en el Observatorio (calendario: «sin datos»/«por municipio»).
        self.assertEqual(ha.elecciones("principado_de_asturias"), [])


if __name__ == "__main__":
    unittest.main()
