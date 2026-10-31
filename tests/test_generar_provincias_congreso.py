"""Versión 1.2.0; 2026-10-31; candidato. 1.2.0: Baleares y Las Palmas con reparto fijado. 1.1.0: provincias insulares con partición declarada. Coherencia del alta de las provincias del Congreso.
Origen: nuevo, sin predecesor. Cada provincia dada de alta por generar_provincias_congreso.py debe estar
declarada igual en catálogo, política, matriz, registro, contrato Infoelectoral y contrato M01–M06.
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from herramientas.catalogo_territorios import load_pilot_territories, selector_labels  # noqa: E402
from herramientas.generar_provincias_congreso import INSULAR, PROVINCES, _partition, provinces  # noqa: E402


def _load(rel: str) -> dict:
    return yaml.safe_load((ROOT / rel).read_text(encoding="utf-8")) or {}


class CongressProvincesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.reparto = {p["territory_id"]: p for p in provinces(ROOT)}
        cls.pilots = {p["territory_id"]: p for p in load_pilot_territories()}

    def test_reparto_is_n06_and_every_peninsular_province_is_declared(self):
        self.assertEqual(52, len(self.reparto))
        self.assertEqual(407, sum(p["k"] for p in self.reparto.values()))
        expected = {tid for tid, p in self.reparto.items() if p["code"] not in INSULAR or _partition(ROOT, tid)}
        self.assertEqual(expected, set(self.pilots))

    def test_number_and_plate_identify_each_province_once(self):
        plates = [plate for _, plate in PROVINCES.values()]
        self.assertEqual(len(plates), len(set(plates)))
        for tid, pilot in self.pilots.items():
            province = self.reparto[tid]
            self.assertEqual(f"C{province['code']}", pilot["pilot_code"])
            self.assertEqual([province["code"]], pilot["province_codes"])
            if tid != "congreso_huesca":
                self.assertEqual(province["plate"], pilot["plate_code"])

    def test_every_declaration_agrees_with_the_approved_k(self):
        policy = _load("configuracion/politica_generacion_territorial_2025.yaml")["territories"]
        matrix = {row["territory_id"]: row for row in _load("configuracion/preparacion_legislatura_vigente.yaml")["territories"]}
        registry = _load("configuracion/registro_electoral.yaml")["territories"]
        contracts = _load("configuracion/contratos_infoelectoral.yaml")["contracts"]
        labels = set(selector_labels())
        for tid, pilot in self.pilots.items():
            with self.subTest(territory=tid):
                k = self.reparto[tid]["k"]
                election_id = f"{tid}_2023-07-23"
                self.assertEqual(k, pilot["k_districts"])
                self.assertEqual(k, policy[tid]["k"])
                self.assertEqual(election_id, matrix[tid]["election_id"])
                self.assertEqual(election_id, registry[tid]["election_id"])
                self.assertEqual(self.reparto[tid]["code"], contracts[election_id]["province"])
                self.assertIn(pilot["name"], labels)
                contract = _load(f"territorios/{tid}/config/{tid}_2025.yaml")
                self.assertEqual(k, contract["validation"]["expected_districts"])
                if self.reparto[tid]["code"] in INSULAR:
                    self.assertEqual(k, sum(contract["validation"]["province_districts"].values()))
                else:
                    self.assertEqual({self.reparto[tid]["code"]: k}, contract["validation"]["province_districts"])

    def test_tenerife_groups_western_islands_in_one_district_joined_by_declared_bridges(self):
        partition = _partition(ROOT, "congreso_santa_cruz_de_tenerife")
        groups = partition["municipality_to_partition"]
        self.assertEqual({"38-C01", "38-G01"}, set(groups.values()))
        for bridge in partition["bridges"]:
            self.assertEqual("38-G01", groups[bridge["u"][:5]])
            self.assertEqual("38-G01", groups[bridge["v"][:5]])
        contract = _load("territorios/congreso_santa_cruz_de_tenerife/config/congreso_santa_cruz_de_tenerife_2025.yaml")
        self.assertEqual({"38-C01": 8, "38-G01": 1}, contract["validation"]["province_districts"])
        self.assertEqual(partition["bridges"], contract["modulos"]["modulo_02_construir_adyacencias"]["topology_bridges"])

    def test_owner_fixed_island_apportionment(self):
        # Decisión del propietario 31-10-2026: Mallorca 7, Menorca 1, Ibiza y Formentera 2; Lanzarote solo.
        expected = {"congreso_baleares": {"07-C01": 7, "07-C02": 1, "07-G01": 2},
                    "congreso_las_palmas": {"35-C01": 8, "35-C02": 1, "35-G01": 1}}
        for tid, quota in expected.items():
            contract = _load(f"territorios/{tid}/config/{tid}_2025.yaml")
            self.assertEqual(quota, contract["validation"]["province_districts"])
            bridges = _partition(ROOT, tid)["bridges"]
            self.assertEqual(bridges, contract["modulos"]["modulo_02_construir_adyacencias"]["topology_bridges"])
        baleares = _load("territorios/congreso_baleares/config/congreso_baleares_2025.yaml")["validation"]
        self.assertEqual(["07-C02", "07-G01"], baleares["population_floor_exempt_partitions"])
        self.assertEqual(1.4, _load("territorios/congreso_las_palmas/config/congreso_las_palmas_2025.yaml")["validation"]["population_cap_ratio"])

    def test_spanish_toponyms_only(self):
        names = {name for name, _ in PROVINCES.values()}
        for foreign in ("Girona", "Lleida", "Ourense", "Gipuzkoa", "Bizkaia", "Araba", "A Coruña", "Illes Balears"):
            self.assertNotIn(foreign, names)


if __name__ == "__main__":
    unittest.main()
