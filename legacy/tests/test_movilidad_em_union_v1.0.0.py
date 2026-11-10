#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PROYECTO: Diputado de Distrito
COMPONENTE: prueba de la unión de movilidad INE EM-1 con las áreas (T-139, paso 1)
VERSIÓN: 1.0.0 · FECHA: 2026-11-10 · ESTADO: candidato
ANTERIOR: ninguna (fichero nuevo)
FUNCIÓN: valores esperados leídos a mano de los xlsx del INE (no recalculados por la herramienta).
"""
import sys
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


if __name__ == "__main__":
    unittest.main()
