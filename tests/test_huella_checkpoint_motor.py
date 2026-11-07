"""T-51: huella de motor, contrato y política en los checkpoints reutilizables."""
from __future__ import annotations

import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path

from herramientas import huella_checkpoint_motor as motor
from herramientas.seleccionar_checkpoint_productivo import select_latest_valid
from tests import test_checkpoint_productivo_selector as base_selector

POLITICA = "territories:\n  demo:\n    population_limits:\n      population_cap_ratio: 1.15\n"


class Base(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.h = base_selector.ProductiveCheckpointSelectorTests()
        self.params = self.h.prepare_root(self.root)
        for rel, txt in (("modulos/04_generar_semillas.py", "m04 v1\n"), ("ddd_core/m04_seed_engine.py", "motor v1\n"),
                         ("configuracion/m04_engine.json", "{}\n"), (motor.POLITICA, POLITICA)):
            f = self.root / rel
            f.parent.mkdir(parents=True, exist_ok=True)
            f.write_text(txt, encoding="utf-8")
        self.antigua = motor.build_fingerprint(params=self.params, root_dir=self.root)

    def tearDown(self):
        self._tmp.cleanup()

    def actual(self):
        return motor.build_fingerprint(params=self.params, root_dir=self.root)

    def escribir(self, rel, txt):
        (self.root / rel).write_text(txt, encoding="utf-8")


class Comparacion(Base):
    def test_misma_huella(self):
        self.assertEqual(motor.comparar(self.antigua, self.actual(), 6)["status"], motor.MATCH)

    def test_motor_m04_distinto_rehace_desde_m04(self):
        self.escribir("ddd_core/m04_seed_engine.py", "motor v2\n")
        r = motor.comparar(self.antigua, self.actual(), 4)
        self.assertEqual((r["status"], r["invalidate_from"]), (motor.MISMATCH, "M04"))
        self.assertIn("ddd_core/m04_seed_engine.py", r["differences"][0])

    def test_politica_y_contrato_distintos(self):
        self.escribir(motor.POLITICA, POLITICA.replace("1.15", "1.16"))
        r = motor.comparar(self.antigua, self.actual(), 5)
        self.assertEqual(r["invalidate_from"], "M04")
        self.assertIn("population_limits de la política", r["differences"])
        self.escribir(motor.POLITICA, POLITICA)
        self.params.write_text(self.params.read_text(encoding="utf-8") + "territory_contract:\n  k_districts: 3\n",
                               encoding="utf-8")
        self.assertIn("contrato materializado", motor.comparar(self.antigua, self.actual(), 4)["differences"])

    def test_motor_m05_distinto_solo_invalida_desde_m05(self):
        self.escribir("ddd_core/m05_population_repair.py", "otra reparación\n")
        self.assertEqual(motor.comparar(self.antigua, self.actual(), 4)["status"], motor.MATCH)
        r = motor.comparar(self.antigua, self.actual(), 6)
        self.assertEqual((r["status"], r["invalidate_from"]), (motor.MISMATCH, "M05"))

    def test_sin_huella_es_no_verificable(self):
        self.assertEqual(motor.comparar(None, self.actual(), 6)["status"], motor.UNVERIFIED)
        self.assertEqual(motor.comparar(None, self.actual(), 3)["status"], motor.MATCH)


class Seleccion(Base):
    def estado(self, nombre, huella):
        st = self.h.accumulated_state(self.root, nombre, self.params, fingerprint=True)
        out = st / "compatibility" / "motor.json"
        out.write_text(json.dumps(huella), encoding="utf-8")
        return st

    def seleccionar(self, candidatos):
        with contextlib.redirect_stderr(io.StringIO()) as err:
            r = select_latest_valid(params=self.params, candidates=candidatos, root_dir=self.root)
        return r, err.getvalue()

    def test_checkpoint_de_huella_antigua_rehace_desde_m04(self):
        st = self.estado("state_old", self.antigua)
        pkg = self.h.package(self.root, "pkg")
        self.escribir("ddd_core/m04_seed_engine.py", "motor v2\n")
        cands = [{"run_id": 41432561787, "stage": s, "package": pkg, "state_root": st} for s in ("M06", "M05", "M04")]
        cands.append({"run_id": 41432561787, "stage": "M03", "package": pkg, "state_root": st})
        r, err = self.seleccionar(cands)
        self.assertEqual(r["selected"]["stage"], "M03")
        self.assertEqual(r["from_stage"], "M04")
        self.assertEqual(len(r["discarded"]), 3)
        self.assertTrue(all(d["reason"].startswith(motor.MISMATCH) for d in r["discarded"]))
        self.assertIn("::warning::CHECKPOINT_ENGINE_MISMATCH", err)

    def test_solo_m05_distinto_deriva_m04_y_rehace_desde_m05(self):
        st = self.estado("state_m05", self.antigua)
        self.escribir("ddd_core/m05_swap_polish.py", "otro pulido\n")
        # m05.json del checkpoint se rehace con el motor nuevo para aislar el efecto de motor.json
        (st / "compatibility" / "m05.json").write_text(json.dumps(
            motor.build_m05_fingerprint(params=self.params, root_dir=self.root)), encoding="utf-8")
        pkg = self.h.package(self.root, "pkg2")
        r, _ = self.seleccionar([{"run_id": 7, "stage": "M06", "package": pkg, "state_root": st}])
        self.assertEqual(r["selected"]["derivation_cause"], motor.MISMATCH)
        self.assertEqual((r["selected"]["effective_stage"], r["from_stage"]), ("M04", "M05"))

    def test_misma_huella_reutiliza_m06(self):
        st = self.estado("state_ok", self.antigua)
        pkg = self.h.package(self.root, "pkg3")
        r, err = self.seleccionar([{"run_id": 8, "stage": "M06", "from_stage": "M07", "package": pkg, "state_root": st}])
        self.assertEqual(r["from_stage"], "M07")
        self.assertEqual(r["selected"]["engine_fingerprint"]["status"], motor.MATCH)
        self.assertNotIn("::warning::", err)


if __name__ == "__main__":
    unittest.main()
