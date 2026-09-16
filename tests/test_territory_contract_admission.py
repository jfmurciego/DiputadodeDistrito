#!/usr/bin/env python3
"""Pruebas R036 v1.2.0: admisión y autorización sin ejecutar M01-M06.

ANTERIOR: legacy/tests/test_territory_contract_admission_v1.1.0.py
"""
from __future__ import annotations
import copy
import tempfile
import unittest
from pathlib import Path
import yaml

from ddd_core.territory_contract import validate_production_contract

ROOT = Path(__file__).resolve().parents[1]
REPAIR_KEYS = {"enabled", "max_depth", "max_transfer_set", "max_candidates", "max_seconds", "seed"}


def population_repair_contract_errors(data):
    """Puerta CI declarativa: valida sólo la capacidad genérica M05, sin ejecutar territorio."""
    m05 = ((data.get("modulos") or {}).get("modulo_05_optimizar_distritos") or {})
    repair = m05.get("population_repair")
    if repair is None:
        return []
    errors = []
    if not isinstance(repair, dict):
        return ["population_repair debe ser objeto"]
    unknown = set(repair) - REPAIR_KEYS
    missing = REPAIR_KEYS - set(repair)
    if unknown:
        errors.append(f"parámetros desconocidos: {sorted(unknown)}")
    if missing:
        errors.append(f"parámetros ausentes: {sorted(missing)}")
    if repair.get("enabled") is not True and repair.get("enabled") is not False:
        errors.append("enabled debe ser booleano")
    for key in ("max_depth", "max_transfer_set", "max_candidates"):
        value = repair.get(key)
        if not isinstance(value, int) or isinstance(value, bool) or value < 1:
            errors.append(f"{key} debe ser entero >= 1")
    seconds = repair.get("max_seconds")
    if not isinstance(seconds, (int, float)) or isinstance(seconds, bool) or seconds <= 0:
        errors.append("max_seconds debe ser positivo")
    seed = repair.get("seed")
    if not isinstance(seed, int) or isinstance(seed, bool):
        errors.append("seed debe ser entero")
    if repair.get("enabled") is True:
        for key in ("in_graph_json", "province_field", "unit_id_field"):
            if not m05.get(key):
                errors.append(f"activación requiere {key}")
    return errors


class ProductionContractAdmission(unittest.TestCase):
    def test_contratos_validos_separan_autorizacion_de_produccion(self):
        expected = {"aragon": ("AUTHORIZED", True), "castilla_y_leon": ("AUTHORIZED", True), "la_rioja": ("PREFLIGHT", False)}
        for territory, (authorization, authorized) in expected.items():
            path = ROOT / "territorios" / territory / "config" / f"{territory}_2025.yaml"
            report = validate_production_contract(path, expected_territory=territory)
            self.assertEqual(report["status"], "ADMITTED", report["errors"])
            self.assertEqual(report["production_authorization"], authorization)
            self.assertEqual(report["production_authorized"], authorized)
            self.assertEqual(len(report["contract_sha256"]), 64)
            data = yaml.safe_load(path.read_text(encoding="utf-8"))
            self.assertEqual(population_repair_contract_errors(data), [])

    def test_extremadura_permanece_experimento_bloqueado_no_admisible(self):
        path = ROOT / "territorios/extremadura/config/extremadura_2025.yaml"
        report = validate_production_contract(path, expected_territory="extremadura")
        self.assertEqual(report["status"], "REJECTED"); self.assertFalse(report["production_authorized"])
        self.assertTrue(any("contract_level" in error for error in report["errors"]))

    def mutated(self, mutate):
        source = ROOT / "territorios" / "aragon" / "config" / "aragon_2025.yaml"
        data = yaml.safe_load(source.read_text(encoding="utf-8")); mutate(data)
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", suffix=".yaml", dir=source.parent, delete=False) as handle:
            yaml.safe_dump(data, handle, sort_keys=False, allow_unicode=True); path = Path(handle.name)
        try: return validate_production_contract(path, expected_territory="aragon")
        finally: path.unlink(missing_ok=True)

    def test_rechaza_restriccion_heredada_o_ausente(self):
        report=self.mutated(lambda data:data["territory_contract"].pop("population_cap_ratio")); self.assertEqual(report["status"],"REJECTED"); self.assertTrue(any("population_cap_ratio" in e for e in report["errors"]))
    def test_rechaza_cadena_m04_m05_rota(self):
        report=self.mutated(lambda data:data["modulos"]["modulo_05_optimizar_distritos"].__setitem__("in_geojson","otra_salida.zip")); self.assertEqual(report["status"],"REJECTED"); self.assertIn("cadena rota M04→M05 asignación",report["errors"])
    def test_rechaza_k_incoherente(self):
        report=self.mutated(lambda data:data["modulos"]["modulo_06_consolidar_distritos"].__setitem__("expected_districts",68)); self.assertEqual(report["status"],"REJECTED"); self.assertTrue(any("incoherencia K" in e for e in report["errors"]))
    def test_rechaza_k_sin_procedencia(self):
        report=self.mutated(lambda data:data["territory_contract"].pop("k_rationale")); self.assertEqual(report["status"],"REJECTED"); self.assertTrue(any("k_rationale" in e for e in report["errors"]))
    def test_rechaza_limites_excepcionales_sin_gobierno(self):
        def mutate(data): data["territory_contract"]["population_floor_ratio"]=0.85; data["validation"]["population_floor_ratio"]=0.85
        report=self.mutated(mutate); self.assertEqual(report["status"],"REJECTED"); self.assertTrue(any("limits_profile" in e for e in report["errors"]))
    def test_rechaza_esquema_ambiguo(self):
        report=self.mutated(lambda data:data["meta"].pop("contract_level")); self.assertEqual(report["status"],"REJECTED"); self.assertTrue(any("contract_level" in e for e in report["errors"]))
    def test_rechaza_autorizacion_ausente(self):
        report=self.mutated(lambda data:data["meta"].pop("production_authorization")); self.assertEqual(report["status"],"REJECTED"); self.assertTrue(any("production_authorization" in e for e in report["errors"]))
    def test_rechaza_autorizacion_distinta_del_catalogo(self):
        report=self.mutated(lambda data:data["meta"].__setitem__("production_authorization","BLOCKED")); self.assertEqual(report["status"],"REJECTED"); self.assertTrue(any("autorización de producción" in e for e in report["errors"]))
    def test_rechaza_salida_fuera_del_repositorio(self):
        report=self.mutated(lambda data:data["modulos"]["modulo_06_consolidar_distritos"].__setitem__("out_catalog_csv","/tmp/catalogo.csv")); self.assertEqual(report["status"],"REJECTED"); self.assertTrue(any("salida fuera" in e for e in report["errors"]))


class PopulationRepairDeclarativeContract(unittest.TestCase):
    def setUp(self):
        self.path=ROOT/"territorios/castilla_y_leon/config/castilla_y_leon_2025.yaml"; self.data=yaml.safe_load(self.path.read_text(encoding="utf-8"))
    def errors_after(self, mutate):
        data=copy.deepcopy(self.data); mutate(data["modulos"]["modulo_05_optimizar_distritos"]); return population_repair_contract_errors(data)
    def test_perfil_generico_exacto_y_declarativo(self):
        m05=self.data["modulos"]["modulo_05_optimizar_distritos"]
        self.assertEqual(m05["population_repair"],{"enabled":True,"max_depth":4,"max_transfer_set":2,"max_candidates":20000,"max_seconds":120,"seed":0})
        self.assertEqual(m05["unit_id_field"],"ddd_unit_id")
        source=(ROOT/"modulos/05_optimizar_distritos.py").read_text(encoding="utf-8"); self.assertNotIn("castilla_y_leon",source.lower())
    def test_limites_invalidos_y_parametros_desconocidos_se_rechazan(self):
        mutations=[lambda m:m["population_repair"].__setitem__("max_depth",0),lambda m:m["population_repair"].__setitem__("max_transfer_set",0),lambda m:m["population_repair"].__setitem__("max_candidates",0),lambda m:m["population_repair"].__setitem__("max_seconds",0),lambda m:m["population_repair"].__setitem__("territorial_override",1)]
        for mutate in mutations: self.assertTrue(self.errors_after(mutate))
    def test_activacion_exige_grafo_provincia_y_unidad_indivisible(self):
        for key in ("in_graph_json","province_field","unit_id_field"): self.assertTrue(self.errors_after(lambda m,key=key:m.pop(key)))
    def test_desactivado_conserva_el_camino_anterior(self):
        source=(ROOT/"modulos/05_optimizar_distritos.py").read_text(encoding="utf-8")
        start=source.index("def _apply_population_repair")
        disabled=source.index('if not rcfg.get("enabled",False):',start)
        graph=source.index("graph=json.loads",disabled)
        prefix=source[disabled:graph]
        self.assertIn('meta={"enabled":False',prefix)
        self.assertIn("return meta",prefix)
        self.assertNotIn("write_geo",prefix)
        self.assertNotIn("repair(",prefix)
    def test_aragon_no_activa_ni_declara_esta_capacidad(self):
        data=yaml.safe_load((ROOT/"territorios/aragon/config/aragon_2025.yaml").read_text(encoding="utf-8")); m05=data["modulos"]["modulo_05_optimizar_distritos"]
        self.assertNotIn("population_repair",m05); self.assertNotIn("unit_id_field",m05)


if __name__ == "__main__": unittest.main()
