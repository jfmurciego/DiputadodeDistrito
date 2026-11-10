"""Versión 1.0.0; 2026-11-10; candidato. T-166: la 00 hija «Reutilizar» planifica y completa la 04 con un M08 sin linaje.
Cambios: fichero nuevo.
Anterior: ninguna (fichero nuevo)

Casos reales (fixtures congeladas con el catálogo y las evidencias del commit de cada run hija, sin artefactos):
  42651881625 y 42720255020 (Cantabria), 42737598841 (Extremadura): Planificar falló con
  `CONTINUE_DURABLE_BLOCK ... DURABLE_LINEAGE_INCOMPATIBLE: electoral_product` porque el catálogo conserva el M08 de una
  04 fallida (fase 04 del manifiesto sin digest). Criterio: el plan ya no falla, no regenera el M06 y reincorpora el M08.
"""
from __future__ import annotations

import unittest
from pathlib import Path

from herramientas.resolver_ejecucion_completa import build_plan

ROOT = Path(__file__).resolve().parents[1]
FX = ROOT / "tests/fixtures/t166_encadenado_m08"
CATALOGO = "configuracion/catalogo_preparacion.yaml"
CASOS = {
    "cantabria_42651881625": "Cantabria",
    "cantabria_42720255020": "Cantabria",
    "extremadura_42737598841": "Extremadura",
}


class HijaReutilizarPlanificaTests(unittest.TestCase):
    def test_los_tres_runs_planifican_y_reincorporan_el_m08(self):
        for caso, territorio in CASOS.items():
            with self.subTest(caso=caso):
                root = FX / caso
                plan = build_plan(territory=territorio, edition="2025", execution_mode="reuse",
                                  catalog=root / CATALOGO, root_dir=root)
                self.assertTrue(plan["run_incorporate"], "la 04 debe ejecutarse")
                self.assertFalse(plan["run_generate"], "el M06 vigente se reutiliza")
                m08 = plan["existing"]["electoral_product"]
                self.assertIsNone(m08["run_id"])
                self.assertIsNone(m08["decision"])
                rechazado = plan["catalog_state"]["rejected_electoral_product"]
                self.assertFalse(rechazado["reusable"])
                self.assertIn("DURABLE_LINEAGE_INCOMPATIBLE: electoral_product", rechazado["reason"])


if __name__ == "__main__":
    unittest.main()
