"""T-268: la 00 rechaza al principio de «Planificar» los territorios del mapa de 350 (D-76)."""
from __future__ import annotations

import os
import subprocess
import unittest
from pathlib import Path

import yaml

from herramientas.guarda_territorio_350 import es_territorio_350

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github/workflows/ejecucion-completa-proyecto.yml"
PASO = "Rechazar territorios del mapa de 350"


def _pasos():
    wf = yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))
    return wf["jobs"]["planificar"]["steps"]


class GuardaTerritorio350(unittest.TestCase):
    def _ejecutar_paso(self, territorio: str):
        paso = next(p for p in _pasos() if p.get("name") == PASO)
        env = {**os.environ, "TERRITORY": territorio}
        return subprocess.run(["bash", "-eo", "pipefail", "-c", paso["run"]], cwd=ROOT, env=env,
                              capture_output=True, text=True)

    def test_paso_rechaza_congreso_350_con_mensaje_accionable(self):
        r = self._ejecutar_paso("Congreso 350 Álava")
        self.assertEqual(r.returncode, 3, r.stdout + r.stderr)
        self.assertIn("::error::TERRITORIO_350_FUERA_DEL_MOTOR", r.stdout)
        self.assertIn("D-76", r.stdout)
        self.assertIn("Usa «Congreso Álava»", r.stdout)

    def test_paso_rechaza_id_congreso350(self):
        r = self._ejecutar_paso("congreso350_soria")
        self.assertEqual(r.returncode, 3, r.stdout + r.stderr)
        self.assertIn("::error::", r.stdout)

    def test_paso_admite_territorios_del_motor(self):
        for t in ("Congreso Álava", "Castilla-La Mancha", "congreso_soria", "Región de Murcia"):
            with self.subTest(t=t):
                r = self._ejecutar_paso(t)
                self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
                self.assertNotIn("::error::", r.stdout)

    def test_todas_las_opciones_350_del_selector_se_rechazan_y_las_demas_no(self):
        wf = yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))
        opciones = wf[True]["workflow_dispatch"]["inputs"]["territory_id"]["options"]
        de_350 = [o for o in opciones if o.startswith("Congreso 350 ")]
        self.assertEqual(len(de_350), 49)
        for o in opciones:
            self.assertEqual(es_territorio_350(o), o in de_350, o)

    def test_guarda_es_el_primer_paso_tras_el_checkout_y_sin_condicion(self):
        pasos = _pasos()
        self.assertTrue(pasos[0]["uses"].startswith("actions/checkout@"))
        self.assertEqual(pasos[1]["name"], PASO)
        self.assertNotIn("if", pasos[1])
        nombres = [p.get("name") for p in pasos]
        self.assertLess(nombres.index(PASO), nombres.index("Resolver fases necesarias"))
        self.assertLess(nombres.index("Resolver fases necesarias"),
                        nombres.index("Comprobar que el paquete electoral sigue descargable"))


if __name__ == "__main__":
    unittest.main()
