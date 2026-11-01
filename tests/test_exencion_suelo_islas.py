"""T-13: la exención municipal de suelo vale también con el campo «municipio:partición» de los contratos con islas."""
import unittest

import pandas as pd

from ddd_core.population_floor_exemptions import municipalities_touch_exempt
from herramientas.validar_ejecucion import floor_exempt_districts


class ExencionSueloIslas(unittest.TestCase):
    def test_municipio_con_particion(self):
        self.assertTrue(municipalities_touch_exempt(["35016:35-C01", "35012:35-C01"], {"35012"}))
        self.assertTrue(municipalities_touch_exempt(["30009"], {"30009"}))  # Beniel (CUMUN) sigue igual
        self.assertFalse(municipalities_touch_exempt(["35016:35-C01"], {"35012"}))

    def test_validador_recalcula_exenciones_desde_las_secciones(self):
        sec = pd.DataFrame({
            "district_id": [1, 1, 2, 3],
            "DDD_MUNICIPALITY_PARTITION": ["35012:35-C01", "35016:35-C01", "35016:35-C01", "35003:35-C02"],
            "DDD_PARTITION": ["35-C01", "35-C01", "35-C01", "35-C02"],
        })
        cfg = {"validation": {"population_floor_exempt_municipalities": ["35012"],
                              "population_floor_exempt_partitions": ["35-C02"]}}
        s6 = {"municipality_field": "DDD_MUNICIPALITY_PARTITION", "province_field": "DDD_PARTITION"}
        self.assertEqual(floor_exempt_districts(cfg, s6, cfg["validation"], sec, "district_id"), {"1", "3"})
        self.assertEqual(floor_exempt_districts({"validation": {}}, s6, {}, sec, "district_id"), set())


if __name__ == "__main__":
    unittest.main()
