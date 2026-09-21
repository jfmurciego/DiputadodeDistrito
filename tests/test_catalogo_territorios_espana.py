#!/usr/bin/env python3
import unittest
from pathlib import Path
import yaml

ROOT=Path(__file__).resolve().parents[1]
CAT=yaml.safe_load((ROOT/"configuracion/catalogo_territorios_espana_2025.yaml").read_text(encoding="utf-8"))["territories"]

class CatalogoTerritoriosEspana(unittest.TestCase):
    def test_catalogo_ids_y_codigos_unicos(self):
        ids=[x["territory_id"] for x in CAT]
        self.assertEqual(len(ids),len(set(ids)))
        self.assertEqual(len(ids),19)
        codes=[str(c).zfill(2) for x in CAT for c in x["province_codes"]]
        self.assertEqual(len(codes),len(set(codes)))
        self.assertEqual(len(codes),52)
        self.assertEqual(set(codes),{f"{i:02d}" for i in range(1,53)})

    def test_madrid_es_siguiente_y_arquipielagos_explicitos(self):
        madrid=next(x for x in CAT if x["territory_id"]=="madrid")
        self.assertEqual(madrid["batch"],"madrid")
        self.assertEqual(madrid["province_codes"],["28"])
        self.assertEqual({x["territory_id"] for x in CAT if x["batch"]=="insular"},{"illes_balears","canarias"})

    def test_niveles_y_gobierno_de_k(self):
        for territory in CAT:
            level=territory["contract_level"]
            self.assertIn(level,{"bootstrap_m01_m03","production_m01_m06"})
            governed=all(territory.get(key) not in (None,"") for key in ("k_districts","k_source","k_rationale"))
            if level=="production_m01_m06":
                self.assertTrue(governed,territory["territory_id"])
                self.assertIn(territory.get("production_authorization"),{"AUTHORIZED","PREFLIGHT"})
            else:
                self.assertFalse(governed,territory["territory_id"])

if __name__=="__main__":
    unittest.main()
