#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""T-511 (D-217): el presupuesto de la ventana de 5 horas acepta o rechaza un plan de flota.

PROYECTO: Diputado de Distrito
VERSIÓN: 1.0.0
FECHA: 2026-11-28
CAMBIOS: 1.0.0: fichero nuevo.
MOTIVO: fija que 26 sesiones Fable a esfuerzo máximo se rechazan (salida ≠ 0), que una ola dentro del reparto 30/15/55
  se acepta y que las skills ya no mandan crear la sucesora con «mismo modelo».
ANTERIOR: ninguna (fichero nuevo)
"""
from __future__ import annotations

import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIX = ROOT / "tests" / "fixtures" / "presupuesto_ventana"
HERRAMIENTA = ROOT / "herramientas" / "presupuesto_ventana.py"
CONFIG = ROOT / "configuracion" / "presupuesto_ventana.json"


def ejecutar(plan: Path, config: Path | None = None) -> subprocess.CompletedProcess:
    cmd = [sys.executable, str(HERRAMIENTA), "--plan", str(plan)]
    if config is not None:
        cmd += ["--config", str(config)]
    return subprocess.run(cmd, capture_output=True, text=True, cwd=ROOT)


class CriterioDeAceptacion(unittest.TestCase):
    def test_flota_de_26_sesiones_a_esfuerzo_maximo_se_rechaza(self):
        plan = json.loads((FIX / "flota_26_fable_max.json").read_text(encoding="utf-8"))
        self.assertEqual(sum(s.get("cantidad", 1) for s in plan["sesiones"]), 26)
        r = ejecutar(FIX / "flota_26_fable_max.json")
        self.assertNotEqual(r.returncode, 0, r.stdout)
        self.assertIn("::error::", r.stdout)

    def test_ola_dentro_del_reparto_se_acepta(self):
        r = ejecutar(FIX / "ola_dentro_del_reparto.json")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("PLAN ACEPTADO", r.stdout)


class Reglas(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.dir = Path(self.tmp.name)

    def plan(self, sesiones, **extra) -> Path:
        p = self.dir / "plan.json"
        p.write_text(json.dumps({"sesiones": sesiones, **extra}), encoding="utf-8")
        return p

    def test_con_autorizacion_el_tope_del_reparto_sigue_rechazando(self):
        sesiones = [{"rol": "implementador", "cantidad": 26, "modelo": "fable", "esfuerzo": "max",
                     "autorizado_propietario": True}]
        r = ejecutar(self.plan(sesiones))
        self.assertEqual(r.returncode, 1)
        self.assertIn("trabajo:", r.stdout)
        self.assertNotIn("supera la tabla", r.stdout)

    def test_subir_modelo_sin_frase_del_propietario_se_rechaza_aunque_quepa(self):
        r = ejecutar(self.plan([{"rol": "revisor", "modelo": "fable", "esfuerzo": "medium"}]))
        self.assertEqual(r.returncode, 1)
        self.assertIn("supera la tabla", r.stdout)
        r = ejecutar(self.plan([{"rol": "revisor", "modelo": "fable", "esfuerzo": "medium",
                                 "autorizado_propietario": True}]))
        self.assertEqual(r.returncode, 0, r.stdout)

    def test_bajar_de_la_tabla_no_necesita_autorizacion(self):
        r = ejecutar(self.plan([{"rol": "ingeniero_motor", "modelo": "sonnet", "esfuerzo": "low"}]))
        self.assertEqual(r.returncode, 0, r.stdout)

    def test_limite_exacto_de_trabajo(self):
        # 55 % de 90 USD = 49,5; implementador sonnet/high cuesta 4,5: 11 sesiones = 49,5 USD caben, 12 no.
        self.assertEqual(ejecutar(self.plan([{"rol": "implementador", "cantidad": 11}])).returncode, 0)
        self.assertEqual(ejecutar(self.plan([{"rol": "implementador", "cantidad": 12}])).returncode, 1)

    def test_coordinacion_tiene_su_propio_tope(self):
        # 15 % de 90 USD = 13,5; coordinador sonnet/medium cuesta 2,95: 4 sesiones = 11,8 caben, 5 = 14,75 no.
        self.assertEqual(ejecutar(self.plan([{"rol": "coordinador", "cantidad": 4}])).returncode, 0)
        r = ejecutar(self.plan([{"rol": "coordinador", "cantidad": 5}]))
        self.assertEqual(r.returncode, 1)
        self.assertIn("coordinacion:", r.stdout)

    def test_lo_ya_gastado_en_la_ventana_se_descuenta(self):
        s = [{"rol": "implementador", "cantidad": 10}]  # 45 USD
        self.assertEqual(ejecutar(self.plan(s)).returncode, 0)
        self.assertEqual(ejecutar(self.plan(s, ya_gastado_usd=10)).returncode, 1)

    def test_las_cifras_se_cambian_en_la_configuracion_sin_tocar_codigo(self):
        cfg = json.loads(CONFIG.read_text(encoding="utf-8"))
        cfg["ventana_usd"] = 180
        cfg_path = self.dir / "cfg.json"
        cfg_path.write_text(json.dumps(cfg), encoding="utf-8")
        p = self.plan([{"rol": "implementador", "cantidad": 12}])
        self.assertEqual(ejecutar(p).returncode, 1)
        self.assertEqual(ejecutar(p, cfg_path).returncode, 0)

    def test_entradas_invalidas(self):
        self.assertEqual(ejecutar(self.plan([{"rol": "inventado"}])).returncode, 1)
        self.assertEqual(ejecutar(self.plan([{"rol": "revisor", "cantidad": 0}])).returncode, 1)
        self.assertEqual(ejecutar(self.plan([{"rol": "revisor", "modelo": "gpt"}])).returncode, 1)
        self.assertEqual(ejecutar(self.plan([])).returncode, 2)
        self.assertEqual(ejecutar(self.dir / "no_existe.json").returncode, 2)

    def test_reparto_que_no_suma_uno_es_error_de_configuracion(self):
        cfg = copy.deepcopy(json.loads(CONFIG.read_text(encoding="utf-8")))
        cfg["reparto"]["trabajo"] = 0.60
        cfg_path = self.dir / "cfg.json"
        cfg_path.write_text(json.dumps(cfg), encoding="utf-8")
        self.assertEqual(ejecutar(FIX / "ola_dentro_del_reparto.json", cfg_path).returncode, 2)

    def test_configuracion_del_repositorio_fija_el_reparto_del_propietario(self):
        cfg = json.loads(CONFIG.read_text(encoding="utf-8"))
        self.assertEqual(cfg["ventana_usd"], 90)
        self.assertEqual(cfg["reparto"], {"reserva_propietario": 0.30, "coordinacion": 0.15, "trabajo": 0.55})
        for rol, v in cfg["roles"].items():
            self.assertIn(v["modelo"], cfg["orden_modelos"], rol)
            self.assertIn(v["esfuerzo"], cfg["orden_esfuerzo"], rol)
            self.assertIn(v["categoria"], ("coordinacion", "trabajo"), rol)


class SkillsSinHerenciaDelModelo(unittest.TestCase):
    def test_ninguna_skill_manda_crear_la_sucesora_con_el_mismo_modelo(self):
        skills = sorted((ROOT / ".claude" / "skills").glob("*/SKILL.md"))
        self.assertGreaterEqual(len(skills), 10)
        for s in skills:
            self.assertNotIn("mismo modelo", s.read_text(encoding="utf-8"), str(s))

    def test_las_tres_skills_de_relevo_citan_la_tabla(self):
        for nombre in ("planificador", "coordinador", "operador"):
            t = (ROOT / ".claude" / "skills" / nombre / "SKILL.md").read_text(encoding="utf-8")
            self.assertIn("configuracion/presupuesto_ventana.json", t, nombre)


if __name__ == "__main__":
    unittest.main()
