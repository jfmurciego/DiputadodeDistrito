#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""T-160 · adaptador composición M06 + grafo M03 → núcleo de reglas (solo stdlib; ficheros sintéticos)."""
from __future__ import annotations

import csv
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ddd_motor2.adaptadores import problema_y_plan  # noqa: E402
from ddd_motor2.reglas import ErrorDatos, Reglas, evaluar  # noqa: E402

CAB = ["CUSEC_KEY", "district_id", "section_pop", "CPRO", "CUMUN", "ddd_unit_id", "ddd_closed_urban"]


def cfg(**val):
    base = {"expected_districts": 2, "population_floor_ratio": 0.8, "population_cap_ratio": 1.2,
            "target_tolerance_ratio": 0.1, "require_single_province_per_district": True,
            "require_municipality_discipline": True}
    base.update(val)
    return {"validation": base}


class Adaptador(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())

    def escribir(self, filas, aristas, nombre="m06.csv", cab=CAB, tipos=None):
        with open(self.tmp / nombre, "w", newline="", encoding="utf-8") as fh:
            w = csv.writer(fh)
            w.writerow(cab)
            w.writerows(filas)
        edges = [{"u": u, "v": v, "edge_type": (tipos or {}).get((u, v), "geometric")} for u, v in aristas]
        (self.tmp / "grafo.json").write_text(json.dumps({"nodes": [{"id": f[0]} for f in filas], "edges": edges}))
        return self.tmp / nombre, self.tmp / "grafo.json"

    def test_agrega_secciones_por_unidad_y_evalua(self):
        filas = [["s1", "1", "60", "22", "22001", "A", "0"], ["s2", "1", "40", "22", "22001", "A", "0"],
                 ["s3", "2", "100", "22", "22002", "B", "0"]]
        comp, grafo = self.escribir(filas, [("s1", "s2"), ("s2", "s3")])
        p, plan, avisos = problema_y_plan(comp, grafo, cfg())
        self.assertEqual({u.id: u.poblacion for u in p.unidades}, {"A": 100, "B": 100})
        self.assertEqual(p.aristas, (("A", "B"),))
        self.assertEqual(plan, {"A": "1", "B": "2"})
        self.assertEqual(avisos, [])
        self.assertTrue(evaluar(p, Reglas.desde_contrato(cfg()), plan).valido)

    def test_municipio_es_campo_y_unidad_multimunicipal_se_desglosa(self):
        # Id con «formato» 22:22009:M que no se interpreta; la unidad mezcla dos CUMUN (grupo atómico).
        filas = [["s1", "1", "60", "22", "22001", "22:22009:M", "0"], ["s2", "1", "40", "22", "22003", "22:22009:M", "0"],
                 ["s3", "2", "100", "22", "22002", "B", "0"]]
        comp, grafo = self.escribir(filas, [("s1", "s2"), ("s2", "s3")])
        p, plan, avisos = problema_y_plan(comp, grafo, cfg())
        u = p.por_id["22:22009:M"]
        self.assertIsNone(u.municipio)
        self.assertEqual(u.desglose, (("22001", 60), ("22003", 40)))
        self.assertIn("1 unidades con varios municipios: desglose por municipio", avisos)
        self.assertTrue(evaluar(p, Reglas.desde_contrato(cfg()), plan).valido)

    def test_provincia_mezclada_o_municipio_incompleto_fallan(self):
        filas = [["s1", "1", "60", "22", "22001", "A", "0"], ["s2", "1", "40", "44", "", "A", "0"],
                 ["s3", "2", "100", "22", "22002", "B", "0"]]
        comp, grafo = self.escribir(filas, [("s1", "s2"), ("s2", "s3")])
        p, plan, avisos = problema_y_plan(comp, grafo, cfg())
        self.assertIsNone(p.por_id["A"].provincia)
        with self.assertRaisesRegex(ErrorDatos, "provincia"):
            evaluar(p, Reglas.desde_contrato(cfg()), plan)

    def test_mezcla_de_vacio_y_valor_avisa_y_deja_el_campo_vacio(self):
        filas = [["s1", "1", "60", "22", "22001", "A", "0"], ["s2", "1", "40", "22", "", "A", "0"],
                 ["s3", "2", "100", "22", "22002", "B", "0"]]
        comp, grafo = self.escribir(filas, [("s1", "s2"), ("s2", "s3")])
        p, plan, avisos = problema_y_plan(comp, grafo, cfg())
        self.assertIsNone(p.por_id["A"].municipio)
        self.assertEqual(p.por_id["A"].desglose, ())
        self.assertIn("1 unidades mezclan secciones con y sin municipio: el campo queda vacío", avisos)
        with self.assertRaisesRegex(ErrorDatos, "municipio"):
            evaluar(p, Reglas.desde_contrato(cfg()), plan)

    def test_respaldo_cusec_solo_si_se_pide(self):
        cab = ["CUSEC_KEY", "district_id", "section_pop", "CPRO", "ddd_unit_id"]
        comp, grafo = self.escribir([["2200101001", "1", "100", "22", "A"], ["2200201001", "2", "100", "22", "B"]],
                                    [("2200101001", "2200201001")], cab=cab)
        p, plan, _ = problema_y_plan(comp, grafo, cfg())
        with self.assertRaisesRegex(ErrorDatos, "municipio"):
            evaluar(p, Reglas.desde_contrato(cfg()), plan)
        p, plan, avisos = problema_y_plan(comp, grafo, cfg(), respaldo_municipio_cusec=True)
        self.assertEqual(p.por_id["A"].municipio, "22001")
        self.assertIn("2 secciones sin municipio: CUSEC[:5] (respaldo de compatibilidad)", avisos)
        self.assertTrue(evaluar(p, Reglas.desde_contrato(cfg()), plan).valido)

    def test_columnas_del_contrato_islas_y_atributos_geojson(self):
        cab = ["CUSEC_KEY", "district_id", "section_pop", "DDD_PARTITION", "DDD_MUNICIPALITY_PARTITION", "ddd_unit_id"]
        filas = [["s1", "1", "100", "35-C01", "35016:35-C01", "U1"], ["s2", "2", "100", "35-C01", "35001:35-C01", "U2"]]
        comp, grafo = self.escribir(filas, [("s1", "s2")], cab=cab)
        c = cfg(province_field="DDD_PARTITION", municipality_field="DDD_MUNICIPALITY_PARTITION",
                province_districts={"35-C01": 2})
        c["partitioning"] = {"enabled": True, "strategy": "connected_internal_units",
                             "partition_unit_field": "M04_PARTITION_UNIT"}
        p, plan, _ = problema_y_plan(comp, grafo, c)
        self.assertEqual((p.por_id["U1"].provincia, p.por_id["U1"].municipio), ("35-C01", "35016:35-C01"))
        with self.assertRaisesRegex(ErrorDatos, "unidad_r012"):
            evaluar(p, Reglas.desde_contrato(c), plan)
        geo = {"type": "FeatureCollection", "features": [
            {"type": "Feature", "geometry": None, "properties": {"CUSEC_KEY": "s1", "M04_PARTITION_UNIT": "P1"}},
            {"type": "Feature", "geometry": None, "properties": {"CUSEC_KEY": "s2", "M04_PARTITION_UNIT": "P2"}}]}
        (self.tmp / "m06.geojson").write_text(json.dumps(geo))
        p, plan, _ = problema_y_plan(comp, grafo, c, atributos_secciones=self.tmp / "m06.geojson")
        self.assertEqual(p.por_id["U1"].unidad_r012, "P1")
        self.assertTrue(evaluar(p, Reglas.desde_contrato(c), plan).valido)

    def test_unidad_partida_y_poblacion_no_entera_fallan(self):
        comp, grafo = self.escribir([["s1", "1", "60", "22", "22001", "A", "0"],
                                     ["s2", "2", "40", "22", "22001", "A", "0"]], [("s1", "s2")])
        with self.assertRaisesRegex(ErrorDatos, "atomicidad"):
            problema_y_plan(comp, grafo, cfg())
        comp, grafo = self.escribir([["s1", "1", "60.5", "22", "22001", "A", "0"]], [])
        with self.assertRaisesRegex(ErrorDatos, "no entera"):
            problema_y_plan(comp, grafo, cfg())

    def test_puentes_del_contrato_y_del_tipo_de_arista(self):
        filas = [["s1", "1", "50", "22", "22001", "A", "0"], ["s2", "1", "50", "22", "22001", "B", "0"],
                 ["s3", "2", "50", "22", "22002", "C", "0"], ["s4", "2", "50", "22", "22002", "D", "0"]]
        comp, grafo = self.escribir(filas, [("s1", "s2"), ("s3", "s4"), ("s2", "s3")],
                                    tipos={("s3", "s4"): "administrative_bridge"})
        c = cfg()
        c["modulo_02_construir_adyacencias"] = {"step2": {"topology_bridges": [{"u": "s2", "v": "s1"}]}}
        p, _, _ = problema_y_plan(comp, grafo, c)
        self.assertEqual(p.aristas, (("B", "C"),))
        self.assertEqual(p.puentes, (("A", "B"), ("C", "D")))

    def test_nucleos_desde_referencia(self):
        filas = [["s1", "1", "100", "22", "22001", "A", "1"], ["s2", "2", "60", "22", "22002", "B", "0"],
                 ["s3", "2", "40", "22", "22002", "C", "0"]]
        comp, grafo = self.escribir(filas, [("s1", "s2"), ("s2", "s3")])
        p, plan, avisos = problema_y_plan(comp, grafo, cfg())
        self.assertEqual(p.por_id["A"].nucleo_cerrado, "nucleo:1")
        self.assertTrue(any("por construcción" in a for a in avisos))
        # Plan alternativo que mete B en el distrito del núcleo: R-NUCLEO frente a la referencia.
        alt = [["s1", "1", "100", "22", "22001", "A", "1"], ["s2", "1", "60", "22", "22002", "B", "0"],
               ["s3", "2", "40", "22", "22002", "C", "0"]]
        comp_alt, grafo = self.escribir(alt, [("s1", "s2"), ("s2", "s3")], nombre="alt.csv")
        p2, plan2, _ = problema_y_plan(comp_alt, grafo, cfg(), referencia_nucleos=comp)
        c = cfg(require_municipality_discipline=False, population_floor_ratio=0.1, population_cap_ratio=1.9)
        self.assertIn("R-NUCLEO", evaluar(p2, Reglas.desde_contrato(c), plan2).codigos())

    def test_sin_columna_de_unidad_cada_seccion_es_unidad(self):
        cab = ["CUSEC_KEY", "district_id", "section_pop", "CPRO", "CUMUN"]
        comp, grafo = self.escribir([["s1", "1", "100", "22", "22001"], ["s2", "2", "100", "22", "22002"]],
                                    [("s1", "s2")], cab=cab)
        p, plan, avisos = problema_y_plan(comp, grafo, cfg())
        self.assertEqual(sorted(p.por_id), ["s1", "s2"])
        self.assertIn("sin columna ddd_unit_id: cada sección es su unidad", avisos)


if __name__ == "__main__":
    unittest.main()
