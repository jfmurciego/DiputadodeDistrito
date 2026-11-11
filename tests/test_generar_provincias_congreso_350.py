"""Versión 1.0.0; 2026-11-08; candidato. Origen: nuevo, sin predecesor (T-102, decisión D-19).
Coherencia del producto paralelo «Congreso 350»: cada gemelo `congreso350_<prov>` toma K de los escaños reales
de 2023 (CSV oficial BOE-A-2023-18907), copia del 407 todo lo que gobierna M01–M03 y los límites de población,
no toca los 407 y nunca publica desde el Gestor (D-18).
"""
from __future__ import annotations

import csv
import hashlib
import sys
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
for p in (ROOT, ROOT / "herramientas"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from herramientas import generar_provincias_congreso_350 as g350  # noqa: E402
from herramientas.catalogo_territorios import load_pilot_territories, selector_labels  # noqa: E402
import clave_eleccion as ce  # noqa: E402
import legislatura_vigente as lv  # noqa: E402

M01_M03 = ("modulo_01_preparar_base_territorial", "modulo_02_construir_adyacencias", "modulo_03_construir_grafo")


def _al_2023(texto: str) -> str:
    """T-225 (D-65): el padre 407 pasó al par INE 2025/2025; el gemelo 350 queda fuera del corte (D-76) en 2023.
    Solo se deshacen los campos que dependen del año de la fuente, para comparar el resto."""
    return (texto.replace("POP_2025", "POP_2023").replace("inputs/seccionado_2025.zip", "inputs/seccionado_2023.zip")
            .replace("year_value: 2025", "year_value: 2023"))


def _load(rel: str) -> dict:
    return yaml.safe_load((ROOT / rel).read_text(encoding="utf-8")) or {}


class Congreso350Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.twins = {p["territory_id"]: p for p in g350.provinces(ROOT)}
        cls.pilots = {p["territory_id"]: p for p in load_pilot_territories()}
        cls.csv_sha = hashlib.sha256((ROOT / g350.SEATS).read_bytes()).hexdigest()

    def test_k_is_the_official_2023_seat_count(self):
        seats = {}
        with (ROOT / g350.SEATS).open(encoding="utf-8") as fh:
            for row in csv.DictReader(fh):
                seats[row["codigo"]] = int(row["escanos_circunscripcion"])
        self.assertEqual(350, sum(seats.values()))
        self.assertEqual(49, len(self.twins))
        self.assertEqual(set(seats) - g350.INSULAR, {p["code"] for p in self.twins.values()})
        for p in self.twins.values():
            self.assertEqual(seats[p["code"]], p["k"])
        self.assertEqual(37, self.twins["congreso350_madrid"]["k"])  # 2023, no los 38 de 2026
        self.assertEqual(2, self.twins["congreso350_soria"]["k"])
        self.assertEqual(1, self.twins["congreso350_ceuta"]["k"])

    def test_every_twin_is_declared_and_idempotent(self):
        self.assertEqual(set(self.twins), {t for t, r in self.pilots.items() if r.get("batch") == g350.VARIANT})
        self.assertEqual(set(), {p["territory_id"] for p in g350.provinces(ROOT)} - g350.declared(ROOT))

    def test_declarations_agree_and_407_untouched(self):
        policy = _load("configuracion/politica_generacion_territorial_2025.yaml")["territories"]
        matrix = {r["territory_id"]: r for r in _load("configuracion/preparacion_legislatura_vigente.yaml")["territories"]}
        registry = _load("configuracion/registro_electoral.yaml")["territories"]
        infoe = _load("configuracion/contratos_infoelectoral.yaml")["contracts"]
        labels = set(selector_labels())
        for tid, p in self.twins.items():
            with self.subTest(territory=tid):
                parent = p["source_id"]
                pilot = self.pilots[tid]
                self.assertEqual((p["k"], f"R{p['code']}", g350.VARIANT), (pilot["k_districts"], pilot["pilot_code"], pilot["scope"]))
                self.assertEqual(parent, pilot["parent_territory_id"])
                self.assertEqual(p["k_407"], self.pilots[parent]["k_districts"])  # el 407 no cambia
                self.assertEqual(p["k"], policy[tid]["k"])
                self.assertEqual("norma", policy[tid]["k_source"])
                self.assertIn(self.csv_sha, policy[tid]["rationale"])
                limits = dict(policy[tid]["population_limits"])
                parent_limits = dict(policy[parent]["population_limits"])
                for key in ("population_floor_ratio", "population_cap_ratio", "target_tolerance_ratio",
                            "municipality_atomicity_limit_ratio"):
                    self.assertEqual(parent_limits[key], limits[key], key)
                election_id = f"{tid}_2023-07-23"
                self.assertEqual(election_id, matrix[tid]["election_id"])
                self.assertEqual(election_id, registry[tid]["election_id"])
                twin_infoe = dict(infoe[election_id])
                parent_infoe = dict(infoe[f"{parent}_2023-07-23"])
                self.assertEqual(tid, twin_infoe.pop("territory_id"))
                parent_infoe.pop("territory_id")
                self.assertEqual(parent_infoe, twin_infoe)
                self.assertIn(pilot["name"], labels)

    def test_contract_changes_only_identity_paths_and_k(self):
        for tid, p in self.twins.items():
            with self.subTest(territory=tid):
                parent = p["source_id"]
                twin = _load(f"territorios/{tid}/config/{tid}_2025.yaml")
                ref = yaml.safe_load(_al_2023(g350._rename((ROOT / f"territorios/{parent}/config/{parent}_2025.yaml")
                                                           .read_text(encoding="utf-8"), p)))
                k = p["k"]
                self.assertEqual(k, twin["territory_contract"]["k_districts"])
                self.assertEqual(k, twin["modulos"]["modulo_04_generar_semillas"]["k_districts"])
                self.assertEqual(k, twin["modulos"]["modulo_06_consolidar_distritos"]["expected_districts"])
                self.assertEqual(k, twin["validation"]["expected_districts"])
                self.assertEqual({p["code"]: k}, twin["validation"]["province_districts"])
                self.assertIn(self.csv_sha, twin["territory_contract"]["k_reference_source"])
                # Lo que gobierna M01–M03 es idéntico al 407: mismo grafo (prueba local de Soria: sha igual).
                for mod in M01_M03:
                    a, b = dict(ref["modulos"][mod]), dict(twin["modulos"][mod])
                    # T-225: los puentes del padre son los del seccionado 2025 (Lérida, Valladolid); el gemelo sigue en 2023.
                    a.pop("topology_bridges", None), b.pop("topology_bridges", None)
                    self.assertEqual(a, b, mod)
                self.assertEqual(ref["io"]["input"], twin["io"]["input"])
                for key in ("population_floor_ratio", "population_cap_ratio", "municipality_atomicity_limit_ratio",
                            "population_floor_exempt_partitions"):
                    self.assertEqual(ref["validation"].get(key), twin["validation"].get(key), key)

    def test_election_key_and_whole_election_excludes_twins(self):
        units = ce.load_units(ROOT)
        self.assertEqual([], ce.validate(units))
        self.assertEqual(["congreso350_soria"], [u["territory_id"] for u in ce.expand("ES-NAC-R42-20230723", units)])
        whole = ce.expand("ES-NAC-20230723", units)
        self.assertEqual(52, len(whole))
        self.assertFalse(any(u["territory_id"].startswith(g350.PREFIX) for u in whole))

    def test_gestor_scope_and_no_publication(self):
        cfg = lv.build_config(ROOT)
        self.assertEqual(lv.load_config(ROOT), cfg)  # legislatura_vigente.yaml regenerado
        self.assertEqual(49, cfg["totales"][lv.VARIANT])
        sel = lv.select(cfg, "congreso 350", ["Soria", "47", "congreso350_madrid"])
        self.assertEqual({"congreso350_soria", "congreso350_valladolid", "congreso350_madrid"},
                         {r["territory_id"] for r in sel})
        self.assertEqual(71, len(lv.select(cfg, "legislatura completa", [])))
        self.assertEqual(52, len(lv.select(cfg, "nacional", [])))
        row = {**sel[0], "accion": "desde_el_principio"}
        self.assertFalse(lv.Territorio(row, "auto", print).publishes)
        self.assertTrue(lv.Territorio({**row, "ambito": "nacional"}, "auto", print).publishes)


if __name__ == "__main__":
    unittest.main()
