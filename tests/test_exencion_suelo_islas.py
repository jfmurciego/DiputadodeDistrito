"""T-13: la exención municipal de suelo vale también con el campo «municipio:partición» de los contratos con islas."""
import unittest

import pandas as pd

from ddd_core.population_floor_exemptions import municipalities_touch_exempt
from herramientas.validar_ejecucion import districts_below_floor, floor_exempt_districts


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

    def test_sin_campo_municipal_usa_cumun_o_cusec(self):
        cfg = {"validation": {"population_floor_exempt_municipalities": ["35012"]}}
        s6 = {"municipality_field": "DDD_MUNICIPALITY_PARTITION", "id_field": "CUSEC_KEY"}
        by_cusec = pd.DataFrame({"district_id": [1, 2], "CUSEC_KEY": ["3501201001", "3501601001"]})
        self.assertEqual(floor_exempt_districts(cfg, s6, cfg["validation"], by_cusec, "district_id"), {"1"})
        by_cumun = by_cusec.assign(CUMUN=["35012", "35016"])
        self.assertEqual(floor_exempt_districts(cfg, s6, cfg["validation"], by_cumun, "district_id"), {"1"})

    def _resumen(self):
        return pd.DataFrame({"district_id": [5, 6, 7], "district_pop": [66538, 70000, 120000],
                             "population_floor": [97396.655] * 3})

    def test_negativo_distrito_exento_pasa_y_no_exento_bajo_suelo_bloquea(self):
        # T-24 (Las Palmas): Mogán 35012 exento (formato «35012:35-C01» o CUMUN/CUSEC); otro municipio bajo suelo bloquea.
        cfg = {"validation": {"population_floor_exempt_municipalities": ["35012"]}}
        s6 = {"municipality_field": "DDD_MUNICIPALITY_PARTITION", "province_field": "DDD_PARTITION"}
        sec = pd.DataFrame({"district_id": [5, 6, 7],
                            "DDD_MUNICIPALITY_PARTITION": ["35012:35-C01", "35016:35-C01", "35003:35-C01"],
                            "DDD_PARTITION": ["35-C01"] * 3})
        exempt = floor_exempt_districts(cfg, s6, cfg["validation"], sec, "district_id")
        self.assertEqual(exempt, {"5"})
        below = districts_below_floor(self._resumen(), "district_pop", 97396.655, exempt)
        self.assertEqual([r["district_id"] for r in below], [6])  # el 6 (35016) no está exento y sigue bloqueando
        # sin ninguna exención, ambos bajo suelo bloquean
        self.assertEqual([r["district_id"] for r in districts_below_floor(self._resumen(), "district_pop", 97396.655, set())], [5, 6])

    def test_negativo_con_cumun_y_cusec_sin_campo_municipal(self):
        cfg = {"validation": {"population_floor_exempt_municipalities": ["35012"]}}
        s6 = {"municipality_field": "DDD_MUNICIPALITY_PARTITION", "id_field": "CUSEC_KEY"}
        for sec in (pd.DataFrame({"district_id": [5, 6, 7], "CUSEC_KEY": ["3501201001", "3501601001", "3500301001"]}),
                    pd.DataFrame({"district_id": [5, 6, 7], "CUSEC_KEY": ["x", "y", "z"], "CUMUN": ["35012", "35016", "35003"]})):
            exempt = floor_exempt_districts(cfg, s6, cfg["validation"], sec, "district_id")
            below = districts_below_floor(self._resumen(), "district_pop", 97396.655, exempt)
            self.assertEqual([r["district_id"] for r in below], [6])


if __name__ == "__main__":
    unittest.main()
