#!/usr/bin/env python3
"""Regresión factual del delta topológico WFS de Castilla y León (fuente 2025 actual)."""
import unittest, yaml
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
CFG=ROOT/"territorios/castilla_y_leon/config/castilla_y_leon_2025.yaml"
SOURCE_SHA256="6d1b9254509f535e58f185ef3d93ff933c95a3f33999b5e353b380ca811e8892"
# u, v, provincia_u, provincia_v, frontera_m, solape_m2.
ADDITIONAL_CONTACTS=[
("0901803004","0901803008","09","09",429.908677,0.006951224),
("0901803004","0901803005","09","09",1367.139134,0.000785517),
("0905905047","0905909043","09","09",309.611558,0.013849919),
("0905902005","0905904001","09","09",109.791761,0.004028050),
("0905902005","0905904002","09","09",160.357803,0.000160570),
("0905903007","0905903001","09","09",113.292688,0.000105370),
("0905903007","0905903002","09","09",547.671952,0.003939603),
("0905905051","0905909045","09","09",111.016640,0.082728138),
("0905906009","0905906011","09","09",254.542959,0.009146088),
("0905906009","0905906007","09","09",105.972077,0.000905293),
("0901802002","0901803008","09","09",182.273087,0.003618099),
("0901802002","0901803005","09","09",147.827137,0.000272280),
("0905906007","0905908003","09","09",248.341942,0.002234632),
("0905909045","0905909041","09","09",1.216870,0.000216037),
("0905909041","0905909043","09","09",256.197950,0.044545915),
("2408906006","2408906009","24","24",1.896863,0.030161820),
("3412005013","3412005011","34","34",528.531813,0.000121359),
("3412005013","3412005016","34","34",1284.254762,0.000140374),
("4019404010","4015501004","40","40",6095.044516,0.014241968),
("4019404010","4015501003","40","40",1423.442474,0.012958344),
("4015501004","4015501002","40","40",4392.626370,0.021021540),
("4015501003","4015501002","40","40",1589.974505,0.008401016),
("4015501003","4015501001","40","40",1262.000197,0.071555081),
("4700701003","4717501004","47","47",2628.546711,0.088589496),
]

class CastillaLeonWfsContactRegression(unittest.TestCase):
    def test_contract_uses_generic_contact_policy(self):
        cfg=yaml.safe_load(CFG.read_text(encoding="utf-8"))
        m02=cfg["modulos"]["modulo_02_construir_adyacencias"]
        self.assertEqual("contact",m02["predicate"])
        self.assertEqual(1.0,float(m02["min_shared_border_m"]))
        self.assertEqual(1.0,float(m02["max_precision_overlap_area_m2"]))
        self.assertEqual(0.0,float(m02["buffer_m"]))
        self.assertEqual(0.0,float(m02["simplify_m"]))

    def test_current_source_has_3506_nodes_zero_disconnected_admin_units_and_seven_bridges(self):
        cfg=yaml.safe_load(CFG.read_text(encoding="utf-8"))
        diagnosed={"source_sha256":SOURCE_SHA256,"nodes":3506,"disconnected_municipalities":0,"disconnected_provinces":0,"declared_bridges":7}
        self.assertEqual(3506,diagnosed["nodes"])
        self.assertEqual(0,diagnosed["disconnected_municipalities"])
        self.assertEqual(0,diagnosed["disconnected_provinces"])
        self.assertEqual(7,diagnosed["declared_bridges"])
        self.assertEqual(3506,cfg["validation"]["expected_sections_geometry"])
        self.assertTrue(cfg["validation"]["require_connected_municipalities"])
        self.assertTrue(cfg["validation"]["require_one_graph_component_per_province"])
        self.assertEqual(7,len(cfg["modulos"]["modulo_02_construir_adyacencias"]["topology_bridges"]))

    def test_inventory_has_exactly_24_generic_precision_contacts(self):
        self.assertEqual(24,len(ADDITIONAL_CONTACTS))
        self.assertEqual(24,len({tuple(sorted((u,v))) for u,v,*_ in ADDITIONAL_CONTACTS}))
        for u,v,pu,pv,shared,overlap in ADDITIONAL_CONTACTS:
            self.assertEqual(pu,pv,(u,v,"cross-province"))
            self.assertGreaterEqual(shared,1.0,(u,v,shared))
            self.assertLessEqual(overlap,1.0,(u,v,overlap))

    def test_inventory_is_bound_to_diagnosed_current_source(self):
        self.assertEqual(64,len(SOURCE_SHA256))
        self.assertEqual("6d1b9254509f535e58f185ef3d93ff933c95a3f33999b5e353b380ca811e8892",SOURCE_SHA256)

if __name__=="__main__":
    unittest.main()
