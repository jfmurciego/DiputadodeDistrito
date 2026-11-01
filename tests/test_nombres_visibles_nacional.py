"""T-05: lo visible dice «nacional»; los identificadores y selectores internos («Congreso …») no cambian."""
import unittest

from herramientas.catalogo_territorios import format_territory_label, visible_label, visible_name


class NombresVisibles(unittest.TestCase):
    def test_congreso_se_muestra_como_nacional(self):
        row = {"territory_id": "congreso_huesca", "pilot_code": "C22", "scope": "congreso", "name": "Congreso Huesca"}
        self.assertEqual(visible_name(row), "Nacional Huesca")
        self.assertEqual(visible_label(row), "Nacional Huesca")
        self.assertEqual(format_territory_label(row), "Congreso Huesca")  # valor de los selectores

    def test_autonomicas_sin_cambios(self):
        row = {"territory_id": "aragon", "autonomous_community_code_ine": "02", "name": "Aragón"}
        self.assertEqual(visible_name(row), "Aragón")
        self.assertEqual(visible_label(row), "02 Aragón")


if __name__ == "__main__":
    unittest.main()
