#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""T-163 · competidor como sustituto de M05: lógica de semilla inicial de GerryChain (sin ejecutar M05 real)."""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ddd_motor2.competicion import Salida  # noqa: E402
from ddd_motor2.competidor import CanonicoM05, GerryChainM05, referencia_m04  # noqa: E402


class PasoFalso:
    params, run_id = "p.yaml", "r"
    s5 = {"out_geojson": "/x/t_m05_distritos_optimizados.geojson.zip"}

    def __init__(self, baseline_rc):
        self.baseline_rc, self.ordenes = baseline_rc, []

    def run(self, cmd):
        self.ordenes.append(cmd)
        return self.baseline_rc

    def m05_y_m06(self, cmd, destino, extra):
        self.ordenes.append(cmd)
        return Salida(Path(destino) / "comp.csv", extra=extra)


class Competidor(unittest.TestCase):
    def test_m04_admisible_sin_initial(self):
        p = PasoFalso(0)
        gc = GerryChainM05(p, CanonicoM05(p))
        gc.generar(None, 11, Path("/d1"))
        gc.generar(None, 12, Path("/d2"))
        self.assertEqual(sum("--validate-baseline-only" in c for c in p.ordenes), 1)  # una vez por territorio
        cadenas = [c for c in p.ordenes if "--seed-base" in c]
        self.assertEqual([c[c.index("--seed-base") + 1] for c in cadenas], ["11", "12"])
        self.assertFalse(any("--initial" in c for c in cadenas))

    def test_m04_no_admisible_parte_del_canonico(self):
        p = PasoFalso(1)
        can = CanonicoM05(p)
        gc = GerryChainM05(p, can)
        self.assertEqual(gc.generar(None, 5, Path("/d")).estado, "SIN_SEMILLA")
        can.generar(None, None, Path("/c"))
        s = gc.generar(None, 5, Path("/d"))
        self.assertEqual(s.extra["semilla_inicial"], "canonica")
        self.assertIn(str(Path("/c/t_m05_distritos_optimizados.geojson.zip")), p.ordenes[-1])


class Main(unittest.TestCase):
    """main() con rutas y generadores falsos: rc 3 sin ancla, rc 2 sin evaluable, copia del ganador en out_*."""

    def preparar(self, con_ancla=True):
        import json
        import tempfile
        from tests.test_motor2_competicion import CFG, POB
        from tests.test_motor2_semilla import cfg as cfg_ancla
        tmp = Path(tempfile.mkdtemp())
        secc = {u: f"220010100{i}" for i, u in enumerate(sorted(POB))}
        grafo = tmp / "grafo.json"
        grafo.write_text(json.dumps({"nodes": list(secc.values()), "edges": [
            {"u": secc[a], "v": secc[b]} for a, b in (("A", "B"), ("B", "C"), ("C", "D"))]}))
        run = tmp / "ejecuciones" / "r"
        run.mkdir(parents=True)
        s5 = {"in_graph_json": str(grafo), "out_geojson": str(run / "t_m05.geojson.zip"),
              "out_report": str(run / "t_m05_informe.json")}
        return tmp, (cfg_ancla() if con_ancla else CFG), s5

    def ejecutar(self, cfg, s5, planes_can, planes_gc, informe=lambda nombre: True):
        from unittest import mock

        from ddd_motor2 import competidor as m
        from tests.test_motor2_competicion import escribir_comp

        def fabrica(nombre, planes):
            class Falso:
                def __init__(self, *a, **k):
                    self.nombre = nombre

                def generar(self, entrada, semilla, destino):
                    plan = planes(semilla)
                    destino = Path(destino)
                    destino.mkdir(parents=True, exist_ok=True)
                    (destino / Path(s5["out_geojson"]).name).write_text(f"M05 {nombre} {semilla}")
                    if informe(nombre):
                        (destino / Path(s5["out_report"]).name).write_text("{}")
                    Path(s5["out_geojson"]).write_text("último candidato")  # como el M05 real
                    Path(s5["out_report"]).write_text("informe del último candidato")
                    if plan is None:
                        return Salida(None, "FALLO")
                    return Salida(escribir_comp(destino / "comp.csv", plan))
            return Falso
        with mock.patch.object(m, "rutas", return_value=(cfg, s5, {})), \
                mock.patch.object(m, "CanonicoM05", fabrica("canonico", planes_can)), \
                mock.patch.object(m, "GerryChainM05", fabrica("gerrychain", planes_gc)):
            return m.main(["--params", "territorios/la_rioja/config/la_rioja_2025.yaml", "--run-id", "r", "--semilla", "1",
                           "--cadenas", "2"])

    def test_sin_ancla_rc3(self):
        _, cfg, s5 = self.preparar(con_ancla=False)
        self.assertEqual(self.ejecutar(cfg, s5, lambda s: None, lambda s: None), 3)

    def test_sin_evaluable_rc2_y_borra_salida(self):
        _, cfg, s5 = self.preparar()
        self.assertEqual(self.ejecutar(cfg, s5, lambda s: None, lambda s: None), 2)
        self.assertFalse(Path(s5["out_geojson"]).exists())
        self.assertFalse(Path(s5["out_report"]).exists())

    def test_copia_el_ganador(self):
        bueno = {"A": "1", "B": "1", "C": "2", "D": "2"}
        malo = {"A": "1", "B": "2", "C": "2", "D": "2"}
        _, cfg, s5 = self.preparar()
        self.assertEqual(self.ejecutar(cfg, s5, lambda s: malo, lambda s: bueno), 0)
        texto = Path(s5["out_geojson"]).read_text()
        self.assertTrue(texto.startswith("M05 gerrychain "), texto)
        self.assertTrue(Path(s5["out_report"]).is_file())
        self.assertTrue((Path(s5["out_geojson"]).parent / "competicion" / "COMPETICION.json").is_file())

    def test_ganador_sin_informe_borra_el_del_ultimo(self):
        bueno = {"A": "1", "B": "1", "C": "2", "D": "2"}
        malo = {"A": "1", "B": "2", "C": "2", "D": "2"}
        _, cfg, s5 = self.preparar()
        rc = self.ejecutar(cfg, s5, lambda s: bueno, lambda s: malo, informe=lambda nombre: nombre != "canonico")
        self.assertEqual(rc, 0)
        self.assertTrue(Path(s5["out_geojson"]).read_text().startswith("M05 canonico"))
        self.assertFalse(Path(s5["out_report"]).exists())




class ReferenciaM04(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())

    def _m04(self, props):
        f = self.tmp / "m04.geojson"
        f.write_text(json.dumps({"features": [{"properties": p} for p in props]}))
        return {"in_geojson": str(f)}

    def test_completo_usa_el_m04(self):
        ref, motivo = referencia_m04(self._m04([{"CUSEC_KEY": "1", "district_id": 1},
                                                {"CUSEC_KEY": "2", "district_id": 2}]), {}, self.tmp)
        self.assertTrue(ref.is_file())
        self.assertIn("M04", motivo)

    def test_respaldo_si_no_hay_m04_o_ningun_district_id(self):
        ref, motivo = referencia_m04({"in_geojson": str(self.tmp / "no.geojson")}, {}, self.tmp)
        self.assertEqual((ref, "ausente" in motivo), (None, True))
        ref, motivo = referencia_m04(self._m04([{"CUSEC_KEY": "1"}]), {}, self.tmp)
        self.assertEqual((ref, "no trae" in motivo), (None, True))

    def test_parcial_o_corrupto_falla(self):
        from ddd_motor2.reglas import ErrorDatos
        with self.assertRaises(ErrorDatos):
            referencia_m04(self._m04([{"CUSEC_KEY": "1", "district_id": 1}, {"CUSEC_KEY": "2"}]), {}, self.tmp)
        malo = self.tmp / "malo.geojson"
        malo.write_text("{no json")
        with self.assertRaises(ErrorDatos):
            referencia_m04({"in_geojson": str(malo)}, {}, self.tmp)
        zip_malo = self.tmp / "malo.geojson.zip"
        zip_malo.write_bytes(b"no es un zip")
        with self.assertRaises(ErrorDatos):
            referencia_m04({"in_geojson": str(zip_malo)}, {}, self.tmp)


if __name__ == "__main__":
    unittest.main()
