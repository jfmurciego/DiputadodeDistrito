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
        production={x["territory_id"] for x in CAT if x["contract_level"]=="production_m01_m06"}
        self.assertEqual(production,{"aragon","castilla_y_leon","extremadura"})
        for territory in CAT:
            self.assertIn(territory["contract_level"],{"bootstrap_m01_m03","production_m01_m06"})
            governed=all(territory.get(key) not in (None,"") for key in ("k_districts","k_source","k_rationale"))
            self.assertEqual(governed,territory["contract_level"]=="production_m01_m06")

if __name__=="__main__":
    unittest.main()
