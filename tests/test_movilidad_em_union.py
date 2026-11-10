#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PROYECTO: Diputado de Distrito
COMPONENTE: prueba de la unión de movilidad INE EM-1 con las áreas (T-139, paso 1)
VERSIÓN: 1.2.0 · FECHA: 2026-11-10 · ESTADO: candidato
ANTERIOR: legacy/tests/test_movilidad_em_union_v1.1.0.py
FUNCIÓN: valores esperados leídos a mano de los xlsx del INE (no recalculados por la herramienta).
"""
import csv
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "herramientas"))
import movilidad_em_union as m  # noqa: E402


class Union(unittest.TestCase):
    def setUp(self):
        self.areas = m.leer_csv(m.AREAS_CSV)
        self.codigos = m.leer_csv(m.CODIGOS_CSV)

    def test_conteos_del_ine(self):
        self.assertEqual(len(self.areas), 9864)  # filas de NACIONAL_MOVILES
        self.assertEqual(len({a["id_grupo"] for a in self.areas}), 3214)  # «3.214 áreas»
        self.assertEqual(len([c for c in self.codigos if c["codigo"] != "OTRO"]), 3214)
        self.assertEqual(len(m.leer_csv(m.FLUJOS_CSV)), 82296)  # 82297 filas del xlsx con cabecera

    def test_biyeccion_nombre_normalizado(self):
        mapa = m.unir(self.areas, self.codigos)
        self.assertEqual(len(mapa), 3214)
        self.assertEqual(len(set(mapa.values())), 3214)
        self.assertEqual(mapa["001A"], next(a["id_grupo"] for a in self.areas
                                            if a["literal_grupo"].startswith("Montesinos, Los y Algorfa")))

    def test_primer_flujo_del_xlsx(self):
        f = m.leer_csv(m.FLUJOS_CSV)[0]
        self.assertEqual((f["cod_origen"], f["cod_destino"], f["flujo"]), ("001A", "001A", "2218"))

    def test_nombre_distinto_falla(self):
        malos = self.codigos + [{"codigo": "999X", "nombre": "No existe", "provincia": ""}]
        with self.assertRaises(ValueError):
            m.unir(self.areas, malos)


class Estadisticas(unittest.TestCase):
    def test_cadiz_sin_municipio_sin_area_partido(self):
        ind = m.indice_secciones(m.leer_csv(m.AREAS_CSV))
        e = m.estadisticas_provincia(m.COMPOSICION / "congreso_cadiz.csv", ind)
        self.assertEqual(e["K"], 11)
        self.assertEqual(e["municipios"], 45)
        self.assertEqual(e["pob_sin_area_en_municipios_partidos"], 0)


class Indicador(unittest.TestCase):
    """Valores calculados a mano sobre un territorio de juguete."""

    def _montar(self, secciones):
        d = Path(tempfile.mkdtemp()) / "t.csv"
        with open(d, "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["seccion", "distrito", "poblacion"])
            w.writerows(secciones)
        return d

    AREAS = [{"cumun": c, "tipo": "MUNICIPIO", "id_area_geo": c, "id_grupo": g} for c, g in
             (("01001", "A"), ("01002", "B"), ("01003", "C"))]
    MAPA = {"fa": "A", "fb": "B", "fc": "C"}

    def _fl(self, *t):
        return [{"cod_origen": o, "cod_destino": d, "flujo": str(n)} for o, d, n in t]

    def test_areas_enteras(self):
        p = self._montar([("0100100001", "1", 100), ("0100200001", "1", 100), ("0100300001", "2", 100)])
        r = m.indicador_plan(p, self.AREAS, self._fl(("fa", "fb", 10), ("fa", "fc", 30), ("fb", "fa", 5)), self.MAPA)
        self.assertAlmostEqual(r["distritos"]["1"][0], 15 / 45)
        self.assertNotIn("2", r["distritos"])  # C no tiene flujos de salida
        self.assertAlmostEqual(r["plan"], 15 / 45)

    def test_area_partida_reparte_por_poblacion(self):
        p = self._montar([("0100100001", "1", 50), ("0100100002", "2", 50), ("0100200001", "1", 100),
                          ("0100300001", "2", 100)])
        r = m.indicador_plan(p, self.AREAS, self._fl(("fa", "fb", 10)), self.MAPA)
        self.assertAlmostEqual(r["distritos"]["1"][0], 1.0)
        self.assertAlmostEqual(r["distritos"]["2"][0], 0.0)

    def test_sin_capital(self):
        p = self._montar([("0100100001", "1", 100), ("0100200001", "1", 100), ("0100300001", "2", 100)])
        r = m.indicador_plan(p, self.AREAS, self._fl(("fa", "fb", 10), ("fa", "fc", 30), ("fb", "fa", 5)),
                             self.MAPA, capital="01003")  # C fuera: queda 15/15
        self.assertAlmostEqual(r["plan"], 1.0)

    def test_hacia_fuera_no_cuenta_en_la_fraccion(self):
        p = self._montar([("0100100001", "1", 100), ("0100200001", "1", 100)])
        r = m.indicador_plan(p, self.AREAS, self._fl(("fa", "fb", 10), ("fa", "fc", 30)), self.MAPA)
        self.assertAlmostEqual(r["plan"], 1.0)
        self.assertEqual(r["flujo_hacia_fuera"], 30)


class Correlacion(unittest.TestCase):
    def test_spearman_valores_conocidos(self):
        self.assertAlmostEqual(m.spearman([1, 2, 3], [10, 20, 30]), 1.0)
        self.assertAlmostEqual(m.spearman([1, 2, 3], [3, 2, 1]), -1.0)
        self.assertAlmostEqual(m.spearman([1, 2, 3, 4], [1, 3, 2, 4]), 0.8)  # 1 - 6*2/(4*15)

    def test_empates_con_rango_medio(self):
        self.assertEqual(m.rangos([5, 5, 7]), [1.5, 1.5, 3.0])


class CompacidadM06(unittest.TestCase):
    def test_poblacion_m06_igual_a_composicion(self):
        # poblaciones por distrito del M06 == suma de la composición vigente (comprobado a mano para Cádiz: 1.254.866)
        filas = [r for r in m.leer_csv(m.COMPACIDAD_CSV) if r["territorio"] == "congreso_cadiz"]
        self.assertEqual(len(filas), 11)
        self.assertEqual(sum(int(r["poblacion_m06"]) for r in filas), 1254866)
        self.assertTrue(all(0 < float(r["polsby_popper_m06"]) <= 1 for r in m.leer_csv(m.COMPACIDAD_CSV)))


if __name__ == "__main__":
    unittest.main()
