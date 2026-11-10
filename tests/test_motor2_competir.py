#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""T-163 · resumen de aceptación de la competición para la batería (solo stdlib)."""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import json  # noqa: E402

from ddd_motor2.competicion import EntradaTerritorio  # noqa: E402
from ddd_motor2.competir import competir_territorio, escribir_resumen, resumen  # noqa: E402
from tests.test_motor2_competicion import POB, Fijo  # noqa: E402
from tests.test_motor2_semilla import cfg as cfg_con_ancla  # noqa: E402


def fila(t, estado="VALIDO", frente="empata", s=10.0):
    return {"territorio": t, "estado": estado, "ganador": "canonico", "frente_al_canonico": frente,
            "canonico": "VALIDO", "candidatos_validos": 6, "candidatos": 6, "desvio_max": 0.1,
            "desvio_max_canonico": 0.1, "fuera_tolerancia": 0, "huella_resultado": "x", "tiempo_s": s}


class Resumen(unittest.TestCase):
    def test_aceptacion(self):
        self.assertTrue(resumen([fila("a"), fila("b", frente="mejora")])["aceptacion"])
        self.assertFalse(resumen([fila("a"), fila("b", estado="INVALIDO")])["aceptacion"])
        self.assertFalse(resumen([fila("a"), {"territorio": "b", "estado": "ERROR", "detalle": "x"}])["aceptacion"])
        self.assertFalse(resumen([])["aceptacion"])

    def test_peor_que_el_vigente(self):  # T-217: no debería pasar nunca (el vigente válido compite)
        r = resumen([fila("a"), {**fila("b"), "vigente_compite": True, "frente_al_vigente": "empeora"}])
        self.assertEqual((r["peor_que_el_vigente"], r["vigente_compite"], r["aceptacion"]), (["b"], 1, False))
        r = resumen([{**fila("c"), "fuera_tolerancia": 38, "fuera_vigente_publicado": 33}])  # Cataluña sin reparar
        self.assertEqual(r["peor_que_el_vigente"], ["c"])

    def test_ficheros(self):
        tmp = Path(tempfile.mkdtemp())
        tot = escribir_resumen([fila("a", s=3), fila("b", frente="mejora", s=5),
                                {"territorio": "c", "estado": "ERROR", "detalle": "x"}], tmp)
        self.assertEqual((tot["validos"], tot["mejora"], tot["empata"], tot["errores"]), (2, 1, 1, ["c"]))
        md = (tmp / "RESUMEN.md").read_text(encoding="utf-8")
        self.assertIn("Válidos: 2/3", md)
        self.assertIn("| c | — | ERROR |", md)


class Territorio(unittest.TestCase):
    def test_competir_territorio_con_composicion_real(self):
        tmp = Path(tempfile.mkdtemp())
        secc = {u: f"220010100{i}" for i, u in enumerate(sorted(POB))}
        grafo = tmp / "grafo.json"
        grafo.write_text(json.dumps({"nodes": list(secc.values()), "edges": [
            {"u": secc[a], "v": secc[b]} for a, b in (("A", "B"), ("B", "C"), ("C", "D"))]}))
        e = EntradaTerritorio("prueba", cfg_con_ancla(), grafo)
        bueno = {"A": "1", "B": "1", "C": "2", "D": "2"}
        from ddd_motor2.semilla import semillas
        cad = Fijo("gerrychain", {x: bueno for x in semillas(e.cfg, "prueba", 3)})
        f = competir_territorio("prueba", tmp, 3, generadores=(Fijo("canonico", {None: bueno}), cad), entrada=e)
        self.assertEqual((f["estado"], f["valido"], f["ganador"], f["frente_al_canonico"]),
                         ("VALIDO", True, "canonico", "empata"))
        self.assertEqual(f["candidatos"], 5)  # canónico + 3 cadenas + exhaustivo (territorio pequeño)
        self.assertTrue((tmp / "competicion" / "prueba" / "COMPETICION.json").is_file())
        from ddd_motor2.competir import fila_guardada
        g = fila_guardada("prueba", tmp, 3, cfg=e.cfg)
        self.assertTrue(g.pop("reanudado"))
        self.assertEqual({k: g[k] for k in f if k != "tiempo_s"}, {k: f[k] for k in f if k != "tiempo_s"})
        self.assertIsNone(fila_guardada("otro", tmp, 3, cfg=e.cfg))
        # Otra competición: otro número de cadenas, otra ancla u otras reglas → se recalcula.
        self.assertIsNone(fila_guardada("prueba", tmp, 4, cfg=e.cfg))
        self.assertIsNone(fila_guardada("prueba", tmp, 3, cfg=cfg_con_ancla(p="c" * 64)))
        otra = cfg_con_ancla()
        otra["validation"]["target_tolerance_ratio"] = 0.2
        self.assertIsNone(fila_guardada("prueba", tmp, 3, cfg=otra))

    def test_fallo_al_escribir_deja_error(self):
        from unittest import mock
        tmp = Path(tempfile.mkdtemp())
        e = EntradaTerritorio("prueba", cfg_con_ancla(), tmp / "g.json")
        with mock.patch("ddd_motor2.competir.competir_publico", return_value=object()), \
                mock.patch("ddd_motor2.competir.escribir", side_effect=OSError("disco lleno")):
            f = competir_territorio("prueba", tmp, 2, generadores=(None, None), entrada=e)
        self.assertEqual(f["estado"], "ERROR")
        self.assertIn("disco lleno", f["detalle"])

    def test_sin_ancla_es_error_explicito(self):
        tmp = Path(tempfile.mkdtemp())
        from tests.test_motor2_competicion import CFG
        e = EntradaTerritorio("prueba", CFG, tmp / "g.json")
        f = competir_territorio("prueba", tmp, 2, generadores=(Fijo("canonico", {}), Fijo("gerrychain", {})), entrada=e)
        self.assertEqual(f["estado"], "ERROR")
        self.assertIn("ErrorContrato", f["detalle"])


class FirmaBanco(unittest.TestCase):
    """La orden que ejecuta el banco T-132 (#623): python -m ddd_motor2.competidor --params … --run-id … --semilla n."""

    def test_firma(self):
        import importlib.util
        from ddd_motor2.competidor import parser, territorio_de
        self.assertIsNotNone(importlib.util.find_spec("ddd_motor2.competidor"))
        a = parser().parse_args(["--params", "territorios/huesca/config/huesca_2025.yaml", "--run-id", "banco-x",
                                 "--semilla", "3"])
        self.assertEqual((a.run_id, a.semilla, a.cadenas), ("banco-x", 3, 5))
        self.assertEqual(territorio_de(Path(a.params)), "huesca")


if __name__ == "__main__":
    unittest.main()
