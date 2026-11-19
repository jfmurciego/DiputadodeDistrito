#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PROYECTO: Diputado de Distrito
COMPONENTE: pruebas de la doble vuelta con coaliciones (T-409, D-167) sobre casos sintéticos
VERSIÓN: 1.1.0 · FECHA: 2026-11-18 · ESTADO: candidato
ANTERIOR: legacy/tests/test_t409_doble_vuelta_v1.0.0_20261117.py
FUNCIÓN: valores esperados calculados a mano (docs/ESTUDIOS/T409_DOBLE_VUELTA/DISENO.md §7), no recalculados con el código.
"""
import csv
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "herramientas"))
import doble_vuelta as dv  # noqa: E402

BL = {"A": "Izquierdas", "B": "Izquierdas", "C": "Patriotas", "D": "Patriotas", "E": "Nacionalistas"}
V = {"A": 30, "B": 15, "C": 28, "D": 12, "E": 15}


class Resolver(unittest.TestCase):
    def test_mayoria_en_primera_vuelta(self):
        r = dv.resolver({"A": 60, "C": 40}, BL, "dv_base")
        self.assertEqual((r["vuelta_decisiva"], r["candidatura_ganadora"], r["votos_abstencion"]), (1, "A", 0))

    def test_exactamente_50_no_gana_en_primera(self):
        r = dv.resolver({"A": 50, "C": 30, "D": 20}, BL, "dv_base")
        self.assertEqual(r["vuelta_decisiva"], 2)

    def test_transferencia_por_bloque_y_abstencion(self):
        r = dv.resolver(V, BL, "dv_base")
        self.assertEqual((r["vuelta_decisiva"], r["candidatura_ganadora"]), (2, "A"))
        self.assertEqual((r["finalista_a"], r["finalista_b"], r["votos_a_2v"], r["votos_b_2v"]), ("A", "C", 45, 40))
        self.assertEqual(r["votos_abstencion"], 15)  # E: sin finalista nacionalista
        self.assertEqual(r["cuota_ganador_2v"], f"{45 / 85:.6f}")
        self.assertEqual(r["empate"], "false")

    def test_conserva_votos(self):
        for esc in dv.ESCENARIOS:
            r = dv.resolver(V, BL, esc)
            self.assertEqual(r["votos_a_2v"] + r["votos_b_2v"] + r["votos_abstencion"], 100, esc)

    def test_coalicion_total_y_dos_bloques(self):
        a = dv.resolver(V, BL, "dv_A")
        self.assertEqual((a["candidatura_ganadora"], a["votos_a_2v"], a["votos_b_2v"], a["votos_abstencion"]),
                         ("bloque:Izquierdas", 45, 40, 15))
        b = dv.resolver(V, BL, "dv_B")
        self.assertEqual((b["candidatura_ganadora"], b["votos_abstencion"]), ("bloque:Izquierdas", 15))

    def test_dv_B_nacionalistas_por_partido_transfieren_al_finalista_nacionalista(self):
        # I 45, N1 25, N2 20, P 10 (dv_B: I y P coaligados; los nacionalistas, por partido): finalistas I y N1;
        # N2 va a N1 (45 − 45) y P eliminado (Patriotas sin finalista) se abstiene.
        bl = {"A": "Izquierdas", "N1": "Nacionalistas", "N2": "Nacionalistas", "C": "Patriotas"}
        r = dv.resolver({"A": 45, "N1": 25, "N2": 20, "C": 10}, bl, "dv_B")
        self.assertEqual((r["finalista_a"], r["finalista_b"]), ("bloque:Izquierdas", "N1"))
        self.assertEqual((r["votos_a_2v"], r["votos_b_2v"], r["votos_abstencion"]), (45, 45, 10))
        self.assertEqual((r["candidatura_ganadora"], r["empate"]), ("N1", "true"))  # 45-45: alfabético, marcado

    def test_empate_por_segundo_puesto_es_alfabetico_y_marcado(self):
        r = dv.resolver({"X": 40, "Y": 20, "Z": 20}, {}, "dv_base")
        self.assertEqual((r["finalista_b"], r["candidatura_ganadora"], r["empate"]), ("Y", "X", "true"))

    def test_dos_finalistas_del_mismo_bloque(self):
        bl = {"A": "Izquierdas", "B": "Izquierdas", "D": "Izquierdas", "C": "Patriotas", "E": "Patriotas"}
        r = dv.resolver({"A": 30, "B": 25, "C": 20, "D": 10, "E": 15}, bl, "dv_base")
        self.assertEqual((r["finalista_a"], r["finalista_b"]), ("A", "B"))
        self.assertEqual((r["votos_a_2v"], r["votos_b_2v"], r["votos_abstencion"]), (40, 25, 35))
        self.assertEqual(r["candidatura_ganadora"], "A")

    def test_sin_bloque_se_abstiene(self):
        r = dv.resolver({"A": 40, "C": 30, "Z": 30}, {"A": "Izquierdas", "C": "Patriotas"}, "dv_base")
        self.assertEqual((r["votos_a_2v"], r["votos_b_2v"], r["votos_abstencion"]), (40, 30, 30))

    def test_distrito_sin_votos(self):
        r = dv.resolver({"A": 0}, BL, "dv_base")
        self.assertEqual((r["candidatura_ganadora"], r["votos_1v"]), ("", 0))


class Detalle(unittest.TestCase):
    def test_dv_A_lleva_bloque_y_votos_por_partido(self):
        d = dv.detalle(V, BL, "dv_A")
        # Izquierdas 30+15=45, Patriotas 28+12=40, Nacionalistas 15 (valores a mano, DISENO §7)
        self.assertEqual([(f["partido"], f["candidatura"], f["bloque"], f["votos_1v"], f["votos_candidatura"]) for f in d], [
            ("A", "bloque:Izquierdas", "Izquierdas", 30, 45), ("B", "bloque:Izquierdas", "Izquierdas", 15, 45),
            ("C", "bloque:Patriotas", "Patriotas", 28, 40), ("D", "bloque:Patriotas", "Patriotas", 12, 40),
            ("E", "bloque:Nacionalistas", "Nacionalistas", 15, 15)])

    def test_dv_base_y_dv_B(self):
        base = dv.detalle(V, BL, "dv_base")
        self.assertEqual([f["candidatura"] for f in base], ["A", "C", "B", "E", "D"])
        b = {f["partido"]: f["candidatura"] for f in dv.detalle(V, BL, "dv_B")}
        self.assertEqual((b["A"], b["C"], b["E"]), ("bloque:Izquierdas", "bloque:Patriotas", "E"))

    def test_sin_bloque_y_votos_cero(self):
        d = dv.detalle({"A": 10, "Z": 5, "Q": 0}, {"A": "Izquierdas"}, "dv_A")
        self.assertEqual([(f["partido"], f["bloque"], f["candidatura"]) for f in d],
                         [("A", "Izquierdas", "bloque:Izquierdas"), ("Z", "", "Z")])

    def test_cli_escribe_detalle_con_sha256(self):
        with tempfile.TemporaryDirectory() as d:
            d = Path(d)
            (d / "v.csv").write_text("district_id,party,votes,bloc\n" + "".join(f"1,{p},{v},\n" for p, v in V.items()), encoding="utf-8")
            (d / "b.csv").write_text("eleccion,siglas,denominacion,bloque_propuesto,motivo\n" + "".join(
                f"2023-07,{p},{p},{b},x\n" for p, b in BL.items()), encoding="utf-8")
            dv.generar(d / "v.csv", d / "b.csv", "2023-07", d / "s.csv", d / "m.json", d / "det.csv")
            filas = list(csv.DictReader(open(d / "det.csv", encoding="utf-8")))
            self.assertEqual(len(filas), 15)  # 5 partidos × 3 escenarios
            self.assertEqual(list(filas[0]), dv.DETALLE_COLUMNAS)
            self.assertEqual(json.loads((d / "m.json").read_text())["detalle"]["sha256"], dv.sha256(d / "det.csv"))


class Tabla(unittest.TestCase):
    @unittest.skipUnless((ROOT / "configuracion/bloques_partidos_2026-11-17.csv").exists(), "la tabla llega con #901")
    def test_tabla_versionada_un_partido_un_bloque(self):
        p = ROOT / "configuracion/bloques_partidos_2026-11-17.csv"
        por = {}
        for f in csv.DictReader(open(p, encoding="utf-8")):
            por.setdefault(f["siglas"], set()).add(f["bloque_propuesto"])
        self.assertEqual([s for s, b in por.items() if len(b) > 1], [])
        dv.cargar_bloques(p, "2023-07")

    def test_cli_determinista_con_manifiesto(self):
        with tempfile.TemporaryDirectory() as d:
            d = Path(d)
            (d / "v.csv").write_text("district_id,party,votes,bloc\n" + "".join(f"1,{p},{v},\n" for p, v in V.items()), encoding="utf-8")
            (d / "b.csv").write_text("eleccion,siglas,denominacion,bloque_propuesto,motivo\n" + "".join(
                f"2023-07,{p},{p},{b},x\n" for p, b in BL.items()), encoding="utf-8")
            args = (d / "v.csv", d / "b.csv", "2023-07")
            dv.generar(*args, d / "s1.csv", d / "m.json")
            dv.generar(*args, d / "s2.csv")
            self.assertEqual((d / "s1.csv").read_bytes(), (d / "s2.csv").read_bytes())
            m = json.loads((d / "m.json").read_text())
            self.assertEqual(m["salida"]["sha256"], dv.sha256(d / "s1.csv"))
            self.assertEqual(m["filas"], 3)


if __name__ == "__main__":
    unittest.main()
