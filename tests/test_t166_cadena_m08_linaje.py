"""Versión 1.0.0; 2026-11-10; candidato. T-166: la 00 hija «Reutilizar» planifica y completa la 04 con un M08 sin linaje.
Cambios: fichero nuevo.
Anterior: ninguna (fichero nuevo)

Casos reales (fixtures congeladas con el catálogo y las evidencias del commit de cada run hija, sin artefactos):
  42651881625 y 42720255020 (Cantabria), 42737598841 (Extremadura): Planificar falló con
  `CONTINUE_DURABLE_BLOCK ... DURABLE_LINEAGE_INCOMPATIBLE: electoral_product` porque el catálogo conserva el M08 de una
  04 fallida (fase 04 del manifiesto sin digest). Criterio: el plan ya no falla, no regenera el M06 y reincorpora el M08.
"""
from __future__ import annotations

import json
import shutil
import tempfile
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


CASO_BASE = "cantabria_42720255020"
EV = "territorios/cantabria/evidencia/"
M08_VIEJO = 41037133327
NUEVO_RUN = 99999999999


def _plan(root: Path) -> dict:
    return build_plan(territory="Cantabria", edition="2025", execution_mode="reuse",
                      catalog=root / CATALOGO, root_dir=root)


def _json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


class AcotadoYSustitucionTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name) / "raiz"
        shutil.copytree(FX / CASO_BASE, self.root)

    def _fase_04_vieja(self) -> tuple[Path, dict, dict]:
        ruta = self.root / EV / f"ejecuciones_completas/{M08_VIEJO}.json"
        manifiesto = _json(ruta)
        fase = next(f for f in manifiesto["phases"] if f["name"].startswith("04 ·"))
        return ruta, manifiesto, fase

    def test_fase_04_en_success_con_digest_ajeno_sigue_bloqueando(self):
        # Un M08 «legítimo» cuyo manifiesto enlaza otro artefacto no es el caso de la 04 fallida: bloquea.
        ruta, manifiesto, fase = self._fase_04_vieja()
        fase.update({"run_id": 1, "artifact": "otro", "artifact_digest": "sha256:" + "a" * 64,
                     "executed": True, "result": "success", "validation_decision": "VALIDADO"})
        ruta.write_text(json.dumps(manifiesto), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "CONTINUE_DURABLE_BLOCK.*DURABLE_LINEAGE_INCOMPATIBLE: electoral_product"):
            _plan(self.root)

    def test_fase_04_en_success_no_validada_sigue_bloqueando(self):
        ruta, manifiesto, fase = self._fase_04_vieja()
        receipt = _json(self.root / EV / "catalogo/electoral_product_2025.json")
        fase.update({"run_id": receipt["run_id"], "artifact": receipt["artifact_name"],
                     "artifact_digest": "sha256:" + receipt["artifact_sha256"],
                     "executed": True, "result": "success", "validation_decision": "BLOQUEADO"})
        ruta.write_text(json.dumps(manifiesto), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "CONTINUE_DURABLE_BLOCK.*DURABLE_PRODUCER_PHASE_INVALID"):
            _plan(self.root)

    def test_el_m08_rechazado_se_sustituye_al_registrarse_el_nuevo(self):
        self.assertIsNotNone(_plan(self.root)["catalog_state"]["rejected_electoral_product"])
        # Registro del M08 nuevo: manifiesto con la 04 en success enlazada al receipt, y receipt del catálogo.
        territorial = _json(self.root / EV / "ejecuciones_completas/42707820760.json")
        fuente = next(self.root.glob(EV + "fuentes_electorales/**/receipt.json"))
        fuente = _json(fuente)
        digest_m08 = "b" * 64
        manifiesto = json.loads(json.dumps(territorial))
        manifiesto["workflow_run_id"] = NUEVO_RUN
        for fase in manifiesto["phases"]:
            if fase["name"].startswith("03 ·"):
                fase.update({"run_id": fuente["run_id"], "artifact": fuente["artifact_name"],
                             "artifact_digest": "sha256:" + fuente["artifact_sha256"]})
            if fase["name"].startswith("04 ·"):
                fase.update({"run_id": NUEVO_RUN, "artifact": f"ddd-state-{NUEVO_RUN}-M08",
                             "artifact_digest": "sha256:" + digest_m08, "executed": True,
                             "result": "success", "validation_decision": "VALIDADO"})
        (self.root / EV / f"ejecuciones_completas/{NUEVO_RUN}.json").write_text(json.dumps(manifiesto), encoding="utf-8")
        ruta = self.root / EV / "catalogo/electoral_product_2025.json"
        receipt = _json(ruta)
        receipt.update({"run_id": NUEVO_RUN, "artifact_name": f"ddd-state-{NUEVO_RUN}-M08", "artifact_sha256": digest_m08})
        ruta.write_text(json.dumps(receipt), encoding="utf-8")
        plan = _plan(self.root)
        self.assertIsNone(plan["catalog_state"]["rejected_electoral_product"])
        self.assertEqual(NUEVO_RUN, plan["existing"]["electoral_product"]["run_id"])
        self.assertFalse(plan["run_incorporate"], "con el M08 nuevo registrado ya no se reincorpora")


if __name__ == "__main__":
    unittest.main()
