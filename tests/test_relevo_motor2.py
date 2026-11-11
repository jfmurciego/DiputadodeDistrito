"""T-234 (D-82, D-84): relevo formal. motor2 («Deslinde 1.0») por defecto en la 00, P30 y el Gestor; m05 solo expreso y con aviso.

Solo stdlib + PyYAML: ejecuta con bash la comprobación del interruptor del paso «Resolver fases necesarias» de la 00."""
from __future__ import annotations

import subprocess
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
WF = ROOT / ".github" / "workflows"


def _wf(nombre):
    return yaml.safe_load((WF / nombre).read_text(encoding="utf-8"))


class InterruptorDeLa00(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pasos = _wf("ejecucion-completa-proyecto.yml")["jobs"]["planificar"]["steps"]
        cls.paso = next(s for s in pasos if s.get("name") == "Resolver fases necesarias")
        run = cls.paso["run"]
        ini = run.index("# T-234")
        cls.guion = "set -euo pipefail\n" + run[ini:run.index("esac", ini) + 4] + "\n"

    def _correr(self, motor, algoritmo="Canónico"):
        r = subprocess.run(["bash", "-c", self.guion], capture_output=True, text=True,
                           env={"UI_MOTOR": motor, "UI_ALGORITHM": algoritmo, "PATH": "/usr/bin:/bin"})
        return r.returncode, r.stdout

    def test_el_paso_recibe_el_motor_con_motor2_por_defecto(self):
        self.assertEqual(self.paso["env"]["UI_MOTOR"], "${{ inputs.motor || 'motor2' }}")

    def test_motor2_canonico_pasa_sin_aviso(self):
        rc, out = self._correr("motor2")
        self.assertEqual(rc, 0)
        self.assertNotIn("::warning::", out)

    def test_m05_explicito_sigue_funcionando_y_avisa(self):
        for alg in ("Canónico", "GerryChain 50"):
            rc, out = self._correr("m05", alg)
            self.assertEqual(rc, 0, alg)
            self.assertIn("::warning::motor=m05: ruta autónoma del canónico RETIRADA", out)

    def test_motor2_con_gerrychain_y_motor_desconocido_fallan_cerrado(self):
        self.assertEqual(self._correr("motor2", "GerryChain 50")[0], 20)
        self.assertEqual(self._correr("motor3")[0], 20)
        self.assertEqual(self._correr("")[0], 20)


class DefectosYCallers(unittest.TestCase):
    def test_la_cadena_electoral_hereda_motor2(self):
        texto = (WF / "ejecucion-completa-proyecto.yml").read_text(encoding="utf-8")
        self.assertNotIn("inputs.motor || 'm05'", texto)
        self.assertEqual(texto.count("inputs.motor || 'motor2'"), 3)  # 02, cadena electoral, interruptor

    def test_la_02_pasa_motor2_al_reutilizable_y_a_la_seleccion(self):
        texto = (WF / "produccion-distritos.yml").read_text(encoding="utf-8")
        self.assertNotIn("inputs.motor || 'm05'", texto)
        self.assertIn("DDD_MOTOR: ${{ inputs.motor || 'motor2' }}", texto)

    def test_el_modo_matriz_del_gestor_pasa_el_motor_de_forma_expresa(self):
        w = _wf("gestor-campanas.yml")["jobs"]["territorios"]["with"]
        self.assertEqual(w["motor"], "${{ matrix.optimization_algorithm == 'Canónico' && 'motor2' || 'm05' }}")

    def test_el_gestor_2_lanza_la_00_con_motor2(self):
        from herramientas import legislatura_vigente as lv  # noqa: PLC0415
        enviados = []
        orig = lv.dispatch
        lv.dispatch = lambda wf, inputs: enviados.append((wf, inputs))
        try:
            t = lv.Territorio({"territory_id": "huesca", "selector_00": "Huesca", "accion": "reutilizar"},
                              "Canónico", lambda *_: None)
            t.start()
        finally:
            lv.dispatch = orig
        self.assertEqual(enviados[0][0], "ejecucion-completa-proyecto.yml")
        self.assertEqual(enviados[0][1]["motor"], "motor2")


if __name__ == "__main__":
    unittest.main()
