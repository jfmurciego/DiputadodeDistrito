"""T-132 / D-48: interfaz del generador competidor del banco (herramientas/banco_generadores.py)."""
import unittest

from herramientas import banco_generadores as bg


class BancoGeneradores(unittest.TestCase):
    def test_competidor_es_un_generador_y_su_orden_por_defecto_es_ddd_motor2(self):
        self.assertIn("competidor", bg.GENERADORES)
        self.assertEqual(bg.COMPETIDOR[-2:], ["-m", "ddd_motor2.competidor"])

    def test_reproducibilidad_y_calidad_son_subcomandos(self):
        for cmd in ("reproducibilidad", "calidad", "matriz", "ejecutar"):
            with self.assertRaises(SystemExit) as cm:
                bg.main([cmd, "--help"])
            self.assertEqual(cm.exception.code, 0)


if __name__ == "__main__":
    unittest.main()
