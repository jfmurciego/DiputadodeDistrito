"""Clave de elección: INE ↔ matrícula, expansión elección → territorios y simulación en seco (T-03)."""
from pathlib import Path
import copy
import unittest

import yaml

from herramientas import clave_eleccion as ce

ROOT = Path(__file__).resolve().parents[1]
WF = ROOT / ".github/workflows"


def _options(workflow: str, field: str) -> list[str]:
    data = yaml.safe_load((WF / workflow).read_text(encoding="utf-8"))
    return data.get(True, data.get("on"))["workflow_dispatch"]["inputs"][field]["options"]


class ClaveEleccion(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.units = ce.load_units(ROOT)

    def test_registro_sin_colisiones(self):
        self.assertEqual(ce.validate(self.units), [])

    def test_ine_y_matricula_resuelven_al_mismo_canonico(self):
        for key in ("ES-NAC-22-20230723", "ES-NAC-HU-20230723", "es/nac/hu/2023-07-23", "ES NAC 22 20230723"):
            self.assertEqual(ce.canonical(key, self.units), "ES-NAC-22-20230723")
        self.assertEqual(ce.canonical("ES-NAC-PM-20230723", self.units), "ES-NAC-07-20230723")
        self.assertEqual(ce.canonical("ES-NAC-GE-20230723", self.units), "ES-NAC-17-20230723")
        self.assertEqual(ce.canonical("ES-NAC-OR-20230723", self.units), "ES-NAC-32-20230723")
        for foreign in ("IB", "GI", "OU"):
            with self.assertRaises(ce.ClaveError):
                ce.canonical(f"ES-NAC-{foreign}-20230723", self.units)
        self.assertEqual(ce.canonical("ES-NAC-BI-20230723", self.units), "ES-NAC-48-20230723")
        self.assertEqual(ce.canonical("ES-NAC-9-20230723", self.units), "ES-NAC-09-20230723")
        rows = ce.expand("ES-NAC-HU-20230723", self.units)
        self.assertEqual([r["territory_id"] for r in rows], ["congreso_huesca"])

    def test_claves_invalidas(self):
        for key in ("ES-NAC-22-20231399", "ES-XX-22-20230723", "nac-22-20230723", ""):
            with self.assertRaises(ce.ClaveError):
                ce.parse(key)
        with self.assertRaises(ce.ClaveError):
            ce.canonical("ES-NAC-QQ-20230723", self.units)

    def test_eleccion_nacional_expande_a_52_provincias(self):
        rows = ce.expand("ES-NAC-20230723", self.units)
        self.assertEqual(len(rows), 52)
        self.assertEqual(len({r["territory_id"] for r in rows}), 52)
        self.assertEqual([r["code"] for r in rows], [f"{i:02d}" for i in range(1, 53)])
        self.assertTrue(all(r["territory_id"].startswith("congreso_") for r in rows))

    def test_autonomicas_con_la_misma_clave(self):
        self.assertEqual([r["territory_id"] for r in ce.expand("ES-AUT-02-20260208", self.units)], ["aragon"])
        same_day = ce.expand("ES-AUT-20230528", self.units)
        self.assertGreater(len(same_day), 1)
        self.assertTrue(all(r["scope"] == "AUT" for r in same_day))
        with self.assertRaises(ce.ClaveError):
            ce.expand("ES-AUT-02-20230528", self.units)

    def test_fecha_distinta_no_resuelve_a_la_eleccion_vigente(self):
        with self.assertRaises(ce.ClaveError):
            ce.expand("ES-NAC-22-20190428", self.units)
        with self.assertRaises(ce.ClaveError):
            ce.expand("ES-NAC-20190428", self.units)

    def test_dos_elecciones_no_colisionan(self):
        huesca = next(u for u in self.units if u["territory_id"] == "congreso_huesca")
        old = copy.deepcopy(huesca)
        old.update(territory_id="congreso_huesca_20190428", election_date="2019-04-28",
                   key="ES-NAC-22-20190428", aliases=["ES-NAC-HU-20190428"])
        units = self.units + [old]
        self.assertEqual(ce.validate(units), [])
        self.assertEqual([r["territory_id"] for r in ce.expand("ES-NAC-HU-20190428", units)],
                         ["congreso_huesca_20190428"])
        self.assertEqual(len(ce.expand("ES-NAC-20230723", units)), 52)
        self.assertEqual(len(ce.expand("ES-NAC-20190428", units)), 1)
        # Reutilizar el mismo territory_id o la misma clave para otra elección sí colisiona.
        clash = copy.deepcopy(old); clash["territory_id"] = "congreso_huesca"
        self.assertTrue(ce.validate(self.units + [clash]))
        dup = copy.deepcopy(huesca); dup["territory_id"] = "otro"
        self.assertTrue(ce.validate(self.units + [dup]))

    def test_filtro_solo(self):
        rows = ce.expand("ES-NAC-20230723", self.units, ["HU", "08", "Vizcaya", "La Coruña"])
        self.assertEqual([r["code"] for r in rows], ["08", "15", "22", "48"])
        with self.assertRaises(ce.ClaveError):
            ce.expand("ES-NAC-20230723", self.units, ["Aragón"])

    def test_simulacion_en_seco_del_00_por_eleccion(self):
        p = ce.plan("ES-NAC-20230723", "completa", self.units, inputs={"execution_mode": "Reutilizar progreso existente"})
        self.assertEqual((p["election"], p["count"]), ("ES-NAC-20230723", 52))
        names = set(_options("ejecucion-completa-proyecto.yml", "territory_id"))
        for d in p["dispatches"]:
            self.assertEqual(d["workflow"], "ejecucion-completa-proyecto.yml")
            self.assertIn(d["inputs"]["territory_id"], names)
            self.assertEqual(d["inputs"]["lanzado_por_eleccion"], "true")
            self.assertIn(d["inputs"]["data_edition"], _options("ejecucion-completa-proyecto.yml", "data_edition"))

    def test_todos_los_territorios_son_lanzables_en_cada_fase(self):
        for phase, (workflow, field, _fixed) in ce.PHASES.items():
            options = set(_options(workflow, field))
            for u in self.units:
                self.assertIn(u["dispatch_name"], options, f"{phase}: {u['dispatch_name']}")

    def test_workflow_de_activacion_por_eleccion(self):
        data = yaml.safe_load((WF / "activacion-por-eleccion.yml").read_text(encoding="utf-8"))
        inputs = data.get(True, data.get("on"))["workflow_dispatch"]["inputs"]
        self.assertEqual(inputs["fase"]["options"], ["plan", "activar", "electoral", "completa"])
        self.assertEqual(inputs["fase"]["default"], "plan")
        self.assertEqual(data["permissions"]["actions"], "write")
        full = (WF / "ejecucion-completa-proyecto.yml").read_text(encoding="utf-8")
        self.assertIn("(github.actor != 'github-actions[bot]' || inputs.lanzado_por_eleccion)", full)
        # El relanzamiento interno del 00 no pasa la entrada: el encadenado ocurre como mucho una vez.
        relaunch = full.split("encadenar_par_y_04:", 1)[1]
        self.assertNotIn("lanzado_por_eleccion]", relaunch)


if __name__ == "__main__":
    unittest.main()
