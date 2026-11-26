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


class Exacto(unittest.TestCase):
    """Sin skip: ortools es dependencia de Deslinde 1.1 (requirements-exacto.lock, imagen de CI con Dockerfile 1.3.0);
    si falta donde debe estar, estos tests fallan en vez de saltarse."""
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
        from unittest import mock
        # T-503: con K > 4 aplica si cabe (átomos × K ≤ TAMANO_MAX); si no, el motivo literal de la 1.0.0 (6 × 5 = 30)
        for cfg, funcion, motivo, tope in ((contrato(), "A", "función A", 2000), (contrato(5), "D8", "K=5", 29)):
            with mock.patch("deslinde.exacto.TAMANO_MAX", tope):
                plan, info = resolver(p, Reglas.desde_contrato(cfg, Criterio()), nat, None, funcion=funcion)
            self.assertIsNone(plan)
            self.assertEqual(info["estado"], "NO_APLICA")
            self.assertIn(motivo, info["motivo"])


class ExactoEnLaCompeticion(unittest.TestCase):
    """Integración con competir() (sintético de test_motor2_competicion_d8: K = 2, 5 unidades)."""

    def competir(self, canonico=None):
        from tests.test_motor2_competicion_d8 import Fijo, entrada, plan_corte
        from ddd_motor2.competicion import competir
        tmp = Path(tempfile.mkdtemp())
        return competir(entrada(tmp), canonico or Fijo("canonico", {None: plan_corte(2)}),
                        Fijo("cadena", {7: plan_corte(2)}), [7], tmp / "out", exhaustivo=False, funcion="D8")

    def test_gana_el_exacto_con_el_optimo(self):
        r = self.competir()
        self.assertEqual(r.exacto["estado"], "OPTIMO")
        self.assertEqual(r.ganador.id, "exacto")  # corta por la frontera corta (C-D), mejor que canónico y cadena
        self.assertIn("exacto", r.a_dict())

    def test_un_plan_del_exacto_rechazado_por_el_nucleo_no_gana(self):
        from unittest import mock
        from tests.test_motor2_competicion_d8 import UNIDADES
        malo = ({u: "X0" for u in UNIDADES}, {"version": "x", "aplicable": True, "estado": "OPTIMO", "etapas": []})
        with mock.patch("deslinde.exacto.resolver", return_value=malo):
            r = self.competir()
        x = next(c for c in r.candidatos if c.id == "exacto")
        self.assertEqual(x.estado, "INVALIDO")
        self.assertNotEqual(r.ganador.id, "exacto")
        self.assertEqual(r.ganador.estado, "VALIDO")

    def test_el_limite_no_depende_del_reloj(self):
        import itertools
        from unittest import mock
        base = self.competir().huella()
        reloj = itertools.count(0, 10_000.0)  # cada llamada al reloj avanza casi 3 horas
        with mock.patch("time.monotonic", side_effect=lambda: next(reloj)), \
                mock.patch("time.time", side_effect=lambda: next(reloj)):
            lento = self.competir().huella()
        self.assertEqual(base, lento)

    def test_sin_canonico_no_aplica_y_consta_en_la_huella(self):
        from ddd_motor2.competicion import Salida

        class Roto:
            nombre = "canonico"

            def generar(self, entrada, semilla, destino):
                return Salida(None, "FALLO", "roto")

        r = self.competir(Roto())
        self.assertEqual((r.exacto["estado"], r.exacto["motivo"]), ("NO_APLICA", "canónico FALLO_GENERADOR"))
        self.assertEqual(r.a_dict()["exacto"]["estado"], "NO_APLICA")
        h = r.huella()
        r.exacto = {**r.exacto, "motivo": "otro"}
        self.assertNotEqual(h, r.huella())

    def test_un_error_al_preparar_el_exacto_se_propaga(self):
        from unittest import mock
        from ddd_motor2.reglas import ErrorDatos
        with mock.patch("deslinde.exacto.resolver", side_effect=ErrorDatos("roto")):  # antes se volvía NO_APLICA mudo
            with self.assertRaises(ErrorDatos):
                self.competir()


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
        for f in (".github/workflows/p80-verificacion-motor.yml", ".github/workflows/p20-distritos.yml",
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
