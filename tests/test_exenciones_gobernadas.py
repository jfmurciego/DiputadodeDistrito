"""DDD T-49 1.0.0, 2026-11-07: toda exención de suelo lleva decided_at, decided_by, reason y evidence."""
import copy
import unittest

from herramientas.comprobar_exenciones_gobernadas import check_all, check_contract, check_policy

OK = {"decided_at": "2026-11-01", "decided_by": "propietario", "reason": "r", "evidence": "PR #1"}


def contract(**val):
    return {"validation": val}


class ExencionesGobernadasTests(unittest.TestCase):
    def test_repositorio_sin_exenciones_sin_decision(self):
        self.assertEqual([], check_all())

    def test_municipal_sin_entrada_falla(self):
        errs = check_contract("x", contract(population_floor_exempt_municipalities=["30003"]))
        self.assertTrue(any("30003 sin entrada" in e for e in errs))

    def test_particion_completa_pasa(self):
        c = contract(population_floor_exempt_partitions=["07-C02"],
                     population_floor_exempt_partition_decisions={"07-C02": OK})
        self.assertEqual([], check_contract("x", c))

    def test_particion_solo_en_territory_contract_exige_decision(self):
        c = {"territory_contract": {"population_floor_exempt_partitions": ["35-C02"]}, "validation": {}}
        self.assertTrue(check_contract("x", c))

    def test_faltan_campos(self):
        for campo in ("decided_at", "decided_by", "reason", "evidence"):
            e = copy.deepcopy(OK)
            del e[campo]
            c = contract(population_floor_exempt_municipalities=["1"], population_floor_exempt_decisions={"1": e})
            self.assertTrue(check_contract("x", c), campo)

    def test_fecha_mal_formada_y_autor_distinto(self):
        for cambio in ({"decided_at": "02/11/2026"}, {"decided_by": "operador"}):
            c = contract(population_floor_exempt_municipalities=["1"], population_floor_exempt_decisions={"1": {**OK, **cambio}})
            self.assertTrue(check_contract("x", c))

    def test_decision_huerfana_falla(self):
        c = contract(population_floor_exempt_decisions={"9": OK})
        self.assertTrue(any("no corresponde" in e for e in check_contract("x", c)))

    def test_politica_sin_decided_at_falla(self):
        pol = {"territories": {"t": {"structural_floor_exemptions": {"07-C02": {"rationale": "x", "evidence": "y"}}}}}
        self.assertTrue(check_policy(pol))


if __name__ == "__main__":
    unittest.main()
