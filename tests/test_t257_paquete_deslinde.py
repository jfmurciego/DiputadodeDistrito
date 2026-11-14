#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""T-257 (D-88) · paquete independiente Deslinde (paquetes/deslinde): fuente única, aislamiento y equivalencia.
VERSIÓN: 1.0.0
ANTERIOR: ninguna (fichero nuevo)
(a) ddd_motor2.<módulo movido> ES deslinde.<módulo> (mismo objeto) y no queda copia en ddd_motor2/;
(b) el paquete no importa ddd_core, ddd_motor2 ni herramientas (salvo la lectura de contrato del repo, en diferido) y
    se carga sin el repo en sys.path;
(c) deslinde/exenciones.py es copia literal de ddd_core/population_cap_exemptions.py (desde «from __future__»);
(d) equivalencia en 3 territorios (Soria, Álava, La Rioja como aut19 de prueba): el paquete solo, sin repo (código
    oficial dado y tablas de naturalidad desde ficheros), da los mismos candidatos, planes, composiciones y ganador
    que ddd_motor2 con la tabla maestra del repo. Las huellas fijas de la competición siguen en
    test_motor2_aceptacion (HUELLAS_FIJAS): no cambian con T-257.
Solo stdlib (fixture sintético con generador determinista por semilla, como test_motor2_aceptacion).
"""
from __future__ import annotations

import ast
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "paquetes" / "deslinde" / "src"
PAQ = SRC / "deslinde"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import ddd_motor2  # noqa: E402  (registra en Deslinde la tabla maestra y las tablas del repo)

TABLAS = (ROOT / "configuracion/partidos_judiciales.csv", ROOT / "docs/ESTUDIOS/T64_comarcas_partidos/comarcas_agrarias.csv",
          ROOT / "datos/movilidad/areas_movilidad_2019.csv")

# Fixture compartido (lo ejecutan el test y el subproceso sin repo): solo importa deslinde y stdlib.
FIXTURE = r'''
import csv, json, random
from pathlib import Path
from deslinde.competicion import EntradaTerritorio, Salida, competir_publico
from deslinde.reglas import Criterio

TERRITORIOS = {"soria": (4, 2), "alava": (6, 3), "aut19": (8, 2)}
CERRADAS = {"soria": ("U0", "U1")}
CFG = {"validation": {"expected_districts": 2, "population_floor_ratio": 0.8, "population_cap_ratio": 1.2,
                      "target_tolerance_ratio": 0.1, "require_single_province_per_district": True,
                      "require_municipality_discipline": True},
       "generation_state": {"source_inputs": [{"path": "inputs/65034.csv.zip", "sha256": "a" * 64, "role": "population"},
                                              {"path": "inputs/seccionado_2025.zip", "sha256": "b" * 64,
                                               "role": "target_sectioning"}]}}

def unidades(t):
    return [f"U{i}" for i in range(TERRITORIOS[t][0])]

def escribir_comp(ruta, plan, pob, cerradas=()):
    ruta.parent.mkdir(parents=True, exist_ok=True)
    with open(ruta, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["CUSEC_KEY", "district_id", "section_pop", "CPRO", "CUMUN", "ddd_unit_id", "ddd_closed_urban"])
        for i, (u, d) in enumerate(sorted(plan.items())):
            w.writerow([f"220010100{i}", d, pob[u], "22", f"2200{i}", u, "1" if u in cerradas else "0"])
    return ruta

class Generador:
    def __init__(self, nombre, t):
        self.nombre, self.t = nombre, t
    def generar(self, entrada, semilla, destino):
        us, k = unidades(self.t), TERRITORIOS[self.t][1]
        n = len(us)
        cortes = {n * j // k for j in range(1, k)} if semilla is None else set(random.Random(semilla).sample(range(1, n), k - 1))
        d, plan = 1, {}
        for i, u in enumerate(us):
            if i in cortes:
                d += 1
            plan[u] = str(d)
        return Salida(escribir_comp(Path(destino) / "comp.csv", plan, {u: 100 for u in us}, CERRADAS.get(self.t, ())))

def competir_t(t, ident, tmp, funcion="D8"):
    us = unidades(t)
    secc = {u: f"220010100{i}" for i, u in enumerate(us)}
    g = tmp / f"grafo_{t}.json"
    g.write_text(json.dumps({"nodes": list(secc.values()), "edges": [
        {"u": secc[a], "v": secc[b], "edge_type": "geometric"} for a, b in zip(us, us[1:])]}))
    cfg = json.loads(json.dumps(CFG))
    cfg["validation"]["expected_districts"] = TERRITORIOS[t][1]
    r = competir_publico(EntradaTerritorio(ident, cfg, g), Generador("canonico", t), Generador("gerrychain", t),
                         tmp / f"out_{t}", n_cadenas=5, criterio=Criterio(), funcion=funcion)
    return {"ganador": r.ganador.id, "semillas": r.semilla_publica["semillas"], "codigo": r.semilla_publica["codigo"],
            "candidatos": [[c.id, c.semilla, c.estado, c.huella_plan, c.composicion_sha256]
                           for c in sorted(r.candidatos, key=lambda c: c.orden)]}
'''
IDS = {"soria": ("nac42", "NAC42"), "alava": ("nac01", "NAC01"), "aut19": ("aut19", "AUT19")}


def _sin_repo(codigo: str) -> subprocess.CompletedProcess:
    env = {k: v for k, v in os.environ.items() if k != "PYTHONPATH"}
    env["PYTHONHASHSEED"] = "0"
    return subprocess.run([sys.executable, "-P", "-s", "-c", codigo], cwd=tempfile.mkdtemp(), env=env,
                          capture_output=True, text=True, timeout=300)


class FuenteUnica(unittest.TestCase):
    def test_modulos_movidos_son_los_de_deslinde(self):
        import importlib
        for n in ddd_motor2.MOVIDOS:
            with self.subTest(n=n):
                self.assertIs(importlib.import_module(f"ddd_motor2.{n}"), importlib.import_module(f"deslinde.{n}"))
                self.assertFalse((ROOT / "ddd_motor2" / (n.replace(".", "/") + ".py")).exists(), f"copia de {n}")
        from ddd_motor2.reglas import ErrorContrato
        from deslinde.reglas.modelo import ErrorContrato as E2
        self.assertIs(ErrorContrato, E2)

    def test_produccion_y_bateria_usan_los_candidatos_de_deslinde(self):
        from deslinde import candidatos
        from ddd_motor2 import generadores, produccion
        self.assertIs(generadores.Ponderado, candidatos.Ponderado)
        self.assertIs(generadores.piezas_finas, candidatos.piezas_finas)
        self.assertTrue(issubclass(generadores.Vigente, candidatos.Vigente))
        self.assertIs(produccion.CanonicoDelRun, candidatos.CanonicoDelRun)
        from ddd_motor2.naturalidad_competicion import cadena
        from deslinde.ponderado import cadena as c2
        self.assertIs(cadena, c2)

    def test_la_huella_motor2_incluye_el_paquete(self):
        from ddd_motor2.produccion import huella_motor
        files = huella_motor()["engine_files"]
        self.assertIn("paquetes/deslinde/src/deslinde/competicion.py", files)
        self.assertIn("paquetes/deslinde/src/deslinde/reglas/evaluar.py", files)


class Aislamiento(unittest.TestCase):
    PROHIBIDOS = ("ddd_core", "ddd_motor2", "herramientas", "modulos", "ddd_ensemble")

    def test_sin_imports_del_repo(self):
        for f in sorted(PAQ.rglob("*.py")):
            arbol = ast.parse(f.read_text(encoding="utf-8"))
            for nodo in ast.walk(arbol):
                nombres = ([a.name for a in nodo.names] if isinstance(nodo, ast.Import) else
                           [nodo.module or ""] if isinstance(nodo, ast.ImportFrom) and not nodo.level else [])
                for n in nombres:
                    if n.split(".")[0] in self.PROHIBIDOS:
                        # única excepción: el contrato se lee con ddd_core dentro del repo (try/except ImportError)
                        self.assertEqual((f.name, n), ("contrato.py", "ddd_core.config"), f"{f.relative_to(ROOT)}: {n}")

    def test_se_carga_sin_el_repo(self):
        mods = sorted(p.relative_to(SRC).with_suffix("").as_posix().replace("/", ".")
                      for p in PAQ.rglob("*.py") if p.name not in ("__init__.py", "__main__.py"))
        r = _sin_repo(f"import sys; sys.path.insert(0, {str(SRC)!r}); import importlib\n"
                      f"for m in {mods!r}: importlib.import_module(m)\n"
                      f"print(sorted(m for m in sys.modules if m.split('.')[0] in {self.PROHIBIDOS!r}))")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(r.stdout.strip(), "[]")

    def test_cli_exige_hashseed_efectivo(self):
        args = ["competir", "--contrato", "x", "--grafo", "x", "--composicion", "x", "--territorio", "NAC22", "--out", "x"]
        r = subprocess.run([sys.executable, "-I", "-c", f"import sys; sys.path.insert(0, {str(SRC)!r}); "
                            f"from deslinde.__main__ import main; sys.exit(main({args!r}))"],
                           env={**os.environ, "PYTHONHASHSEED": "0"}, capture_output=True, text=True, timeout=60)
        self.assertEqual(r.returncode, 6, r.stderr)  # -I ignora PYTHONHASHSEED: se niega


class CopiaVigiladaExenciones(unittest.TestCase):
    def test_identica_a_ddd_core(self):
        def cuerpo(p):
            t = p.read_text(encoding="utf-8")
            return t[t.index("from __future__ import annotations"):]
        self.assertEqual(cuerpo(PAQ / "exenciones.py"), cuerpo(ROOT / "ddd_core" / "population_cap_exemptions.py"),
                         "la regla común de exención de techo cambió en ddd_core: copia el cambio a deslinde/exenciones.py")


class Equivalencia(unittest.TestCase):
    """(d) mismo resultado con el paquete solo (sin repo) que con ddd_motor2 (tabla maestra del repo)."""

    def test_tres_territorios(self):
        ns: dict = {}
        exec(FIXTURE, ns)  # noqa: S102  (fixture propio del test)
        prog = (f"import sys, json; from pathlib import Path; import tempfile; sys.path.insert(0, {str(SRC)!r})\n"
                f"from deslinde import tablas\n"
                f"tablas.registrar(tablas.desde_ficheros(*{[str(p) for p in TABLAS]!r}))\n" + FIXTURE +
                f"\nprint(json.dumps({{t: competir_t(t, c, Path(tempfile.mkdtemp())) for t, (_, c) in {IDS!r}.items()}}))")
        r = _sin_repo(prog)
        self.assertEqual(r.returncode, 0, r.stderr)
        solo = json.loads(r.stdout.strip().splitlines()[-1])
        for t, (ident, cod) in IDS.items():
            with self.subTest(t=t):
                repo = ns["competir_t"](t, ident, Path(tempfile.mkdtemp()))
                self.assertEqual(repo["codigo"], cod)
                self.assertEqual(solo[t], repo)


if __name__ == "__main__":
    unittest.main()
