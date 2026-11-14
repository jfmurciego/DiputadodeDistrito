#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PROYECTO: Diputado de Distrito
COMPONENTE: tests de Deslinde 1.1 (T-297): frontera medida (M02 7.4.0 / M03 7.6.0) y candidato exacto (exacto.py)
VERSIÓN: 1.0.0
FECHA: 2026-11-14
ANTERIOR: ninguna (fichero nuevo)
Sintéticos; las partes de CP-SAT se saltan sin ortools y las de M02 sin shapely.
"""
from __future__ import annotations

import importlib.util
import json
import runpy
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ddd_motor2.reglas import Criterio, Problema, Reglas, Unidad, evaluar  # noqa: E402

TIENE_ORTOOLS = importlib.util.find_spec("ortools") is not None
TIENE_GEO = importlib.util.find_spec("shapely") is not None and importlib.util.find_spec("geopandas") is not None


def contrato(k=2):
    return {"validation": {"expected_districts": k, "population_floor_ratio": 0.85, "population_cap_ratio": 1.15,
                           "target_tolerance_ratio": 0.10, "require_single_province_per_district": True,
                           "require_municipality_discipline": False, "province_districts": {}}}


class _Natural:
    """Lo que usa exacto.py de naturalidad_clave.Natural: partidos (pj), comarcas (ca) y frontera (largo)."""

    def __init__(self, pj, ca, largo):
        self.pj, self.ca, self.largo = pj, ca, largo


def rejilla():
    """2×3: u0 u1 u2 / u3 u4 u5, población 100 cada una (objetivo 300 con K=2)."""
    us = tuple(Unidad(f"u{i}", 100, municipio=f"30{i:03d}", provincia="30") for i in range(6))
    aristas = (("u0", "u1"), ("u1", "u2"), ("u3", "u4"), ("u4", "u5"), ("u0", "u3"), ("u1", "u4"), ("u2", "u5"))
    return Problema(us, aristas)


@unittest.skipUnless(TIENE_ORTOOLS, "sin ortools")
class Exacto(unittest.TestCase):
    def _resolver(self, nat, **kw):
        from deslinde.exacto import resolver
        p = rejilla()
        r = Reglas.desde_contrato(contrato(), Criterio())
        return p, r, resolver(p, r, nat, None, **kw)

    def test_optimo_por_demarcacion_y_valido(self):
        # partido A = fila de arriba, B = fila de abajo: el óptimo D8 corta entre filas (0 partidos partidos)
        pj = {f"u{i}": ("A" if i < 3 else "B") for i in range(6)}
        nat = _Natural(pj, {u: None for u in pj}, {})
        p, r, (plan, info) = self._resolver(nat)
        self.assertEqual(info["estado"], "OPTIMO")
        self.assertTrue(evaluar(p, r, plan).valido)
        self.assertEqual(len({plan["u0"], plan["u1"], plan["u2"]}), 1)
        self.assertNotEqual(plan["u0"], plan["u3"])
        self.assertEqual([e[2] for e in info["etapas"] if e[0] == "partidas"], [0])

    def test_frontera_decide_a_igualdad_de_demarcaciones(self):
        # sin demarcaciones; aristas entre filas de 1 m y dentro de cada fila de 100 m: el único reparto 3+3 que no
        # corta ninguna de 100 m es fila contra fila (corta las 3 de 1 m = 3000 mm)
        largo = {("u0", "u1"): 100.0, ("u1", "u2"): 100.0, ("u3", "u4"): 100.0, ("u4", "u5"): 100.0,
                 ("u0", "u3"): 1.0, ("u1", "u4"): 1.0, ("u2", "u5"): 1.0}
        nat = _Natural({f"u{i}": None for i in range(6)}, {f"u{i}": None for i in range(6)}, largo)
        _, _, (plan, info) = self._resolver(nat)
        self.assertEqual(info["estado"], "OPTIMO")
        self.assertEqual([e[2] for e in info["etapas"] if e[0] == "frontera_mm"], [3000])
        self.assertNotEqual(plan["u0"], plan["u3"])

    def test_determinista(self):
        nat = _Natural({f"u{i}": None for i in range(6)}, {f"u{i}": None for i in range(6)}, {})
        _, _, (a, ia) = self._resolver(nat)
        _, _, (b, ib) = self._resolver(nat)
        self.assertEqual(a, b)
        self.assertEqual(ia["etapas"], ib["etapas"])

    def test_no_aplica(self):
        from deslinde.exacto import resolver
        nat = _Natural({}, {}, {})
        p = rejilla()
        for cfg, funcion, motivo in ((contrato(), "A", "función A"), (contrato(5), "D8", "K=5")):
            plan, info = resolver(p, Reglas.desde_contrato(cfg, Criterio()), nat, None, funcion=funcion)
            self.assertIsNone(plan)
            self.assertEqual(info["estado"], "NO_APLICA")
            self.assertIn(motivo, info["motivo"])


class RecuentoBateria(unittest.TestCase):
    def test_exacto_no_es_cadena_y_cuenta_en_el_esperado(self):
        bm = runpy.run_path(str(ROOT / "herramientas/bateria_motor.py"))
        with tempfile.TemporaryDirectory() as d:
            cands = [{"id": "canonico", "generador": "canonico", "estado": "VALIDO"},
                     {"id": "ponderado-s1", "generador": "ponderado", "estado": "VALIDO"},
                     {"id": "exacto", "generador": "exacto", "estado": "VALIDO"}]
            Path(d, "COMPETICION.json").write_text(json.dumps({"candidatos": cands, "canonico": "canonico"}))
            c = bm["cadenas_de"](Path(d))
        self.assertEqual((c["cadenas"], c["exacto"], c["candidatos"]), (1, True, 3))


class InstalacionOrtools(unittest.TestCase):
    def test_lock_con_hashes_y_mismos_pines_que_el_paquete(self):
        import re
        exacto = (ROOT / "requirements-exacto.lock").read_text()
        pines = dict(re.findall(r"(?m)^([A-Za-z0-9_.-]+)==(\S+)", exacto))
        self.assertEqual(sorted(pines), ["absl-py", "immutabledict", "ortools", "protobuf", "typing_extensions"])
        for nombre in pines:  # cada pin con al menos un --hash
            self.assertRegex(exacto, rf"(?s){re.escape(nombre)}=={re.escape(pines[nombre])} \\\n\s+--hash=sha256:[0-9a-f]{{64}}")
        paquete = dict(re.findall(r"(?m)^([A-Za-z0-9_.-]+)==(\S+)",
                                  (ROOT / "paquetes/deslinde/requirements-deslinde.lock").read_text()))
        self.assertEqual({k: paquete[k] for k in pines}, pines)

    def test_workflows_y_dockerfile_lo_instalan_sin_dependencias_y_con_hashes(self):
        for f in (".github/workflows/bateria-motor.yml", ".github/workflows/_reutilizable-generacion-territorial.yml",
                  "Dockerfile"):
            texto = (ROOT / f).read_text()
            self.assertRegex(texto, r"pip install (--no-cache-dir )?--no-deps --require-hashes (--requirement|-r) "
                                    r"(/app/)?requirements-exacto\.lock", f)

    def test_sin_ortools_falla_con_error_claro(self):
        from unittest import mock
        from deslinde.exacto import resolver
        with mock.patch.dict(sys.modules, {"ortools": None}):
            with self.assertRaisesRegex(RuntimeError, "EXACTO_SIN_ORTOOLS"):
                resolver(rejilla(), Reglas.desde_contrato(contrato(), Criterio()), _Natural({}, {}, {}), None)


@unittest.skipUnless(TIENE_GEO, "sin shapely/geopandas")
class FronteraM02M03(unittest.TestCase):
    def test_m02_escribe_y_m03_conserva_shared_border_m(self):
        from shapely.geometry import box
        m02 = runpy.run_path(str(ROOT / "modulos/02_construir_adyacencias.py"))
        m03 = runpy.run_path(str(ROOT / "modulos/03_construir_grafo.py"))
        self.assertEqual(m02["_shared_if_ok"](box(0, 0, 2, 1), box(2, 0, 3, 1), "contact", 0.5, 1.0), 1.0)
        self.assertIsNone(m02["_shared_if_ok"](box(0, 0, 1, 1), box(2, 0, 3, 1), "contact", 0.5, 1.0))
        with tempfile.TemporaryDirectory() as d:
            out = Path(d, "e.jsonl")
            puente = {"u": "c", "v": "d", "edge_type": "topology_bridge", "admin_scope": "province:30"}
            m02["write_edges_jsonl"]([("a", "b")], [puente], out, {("a", "b"): 12.345})
            filas = [json.loads(x) for x in out.read_text().splitlines()]
            self.assertEqual(filas[0], {"u": "a", "v": "b", "edge_type": "geometric", "shared_border_m": 12.345})
            self.assertNotIn("shared_border_m", filas[1])
            aristas = m03["load_edges_jsonl"](str(out))
        self.assertEqual(aristas[0]["shared_border_m"], 12.345)
        self.assertNotIn("shared_border_m", aristas[1])


if __name__ == "__main__":
    unittest.main()
