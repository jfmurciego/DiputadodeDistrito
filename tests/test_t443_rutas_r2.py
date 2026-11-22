# -*- coding: utf-8 -*-
"""T-443: árbol nuevo de R2 (D-188, D-190). Fija el árbol y la regla de nombres de herramientas/rutas_r2.py.

Los valores esperados son literales de docs/ESTUDIOS/T435_ESTRUCTURA_R2/CRUCE_claves.csv (cruce clave a clave del P74, run 44871986746),
salvo las dos decisiones del 22-11 (Coordinador, criterio técnico): nombre completo de la tabla maestra en todas las carpetas
(`principado-de-asturias`) y `congreso350_*` → `interno/competicion/<provincia>/` sin run en el nombre.
"""
import csv
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from herramientas import rutas_r2 as r  # noqa: E402

CRUCE = ROOT / "docs" / "ESTUDIOS" / "T435_ESTRUCTURA_R2" / "CRUCE_claves.csv"


class Arbol(unittest.TestCase):
    def test_paquete_p10_por_ambito(self):
        self.assertEqual(r.ruta_paquete_p10("nac47"), "fuentes/por-territorio/nacionales/valladolid/paquete.zip")
        self.assertEqual(r.ruta_paquete_p10("congreso_valladolid"), "fuentes/por-territorio/nacionales/valladolid/paquete.zip")
        self.assertEqual(r.ruta_paquete_p10("aut13"), "fuentes/por-territorio/autonomicas/comunidad-de-madrid/paquete.zip")
        self.assertEqual(r.ruta_paquete_p10("nac28"), "fuentes/por-territorio/nacionales/madrid/paquete.zip")
        self.assertEqual(r.ruta_paquete_p10("aut03"), "fuentes/por-territorio/autonomicas/principado-de-asturias/paquete.zip")
        self.assertEqual(r.ruta_paquete_p10("congreso350_valladolid"), "interno/competicion/valladolid/paquete.zip")

    def test_nombres_en_espanol_sin_tildes(self):
        self.assertEqual(r.ruta_paquete_p10("nac15"), "fuentes/por-territorio/nacionales/la-coruna/paquete.zip")
        self.assertEqual(r.ruta_paquete_p10("nac38"), "fuentes/por-territorio/nacionales/santa-cruz-de-tenerife/paquete.zip")
        self.assertEqual(r.ruta_paquete_p10("nac48"), "fuentes/por-territorio/nacionales/vizcaya/paquete.zip")
        self.assertEqual(r.ruta_paquete_p10("aut08"), "fuentes/por-territorio/autonomicas/castilla-la-mancha/paquete.zip")

    def test_toponimos_solo_en_espanol(self):
        """Topónimos de la tabla maestra en español, nunca en otras lenguas (regla del propietario, CLAUDE.md)."""
        esperado = {"nac48": "vizcaya", "nac20": "guipuzcoa", "nac03": "alicante", "nac12": "castellon", "nac01": "alava",
                    "nac17": "gerona", "nac25": "lerida", "nac32": "orense", "nac07": "baleares", "nac46": "valencia",
                    "aut04": "islas-baleares", "aut10": "comunidad-valenciana", "aut16": "pais-vasco"}
        for t, nombre in esperado.items():
            self.assertEqual(r.territorio_r2(t)[1], nombre, t)
        otras_lenguas = {"bizkaia", "gipuzkoa", "alacant", "castello", "araba", "girona", "lleida", "ourense", "illes-balears",
                         "balears", "valencia-valencia", "comunitat-valenciana", "euskadi", "a-coruna"}
        from ddd_core import territorio_ids as ti
        for t in ti.ids_nuevos():
            self.assertNotIn(r.territorio_r2(t)[1], otras_lenguas, t)

    def test_mapas(self):
        self.assertEqual(r.ruta_mapa("nac01", "doble-vuelta.zip"), "mapas/nacionales/congreso-2023/alava/doble-vuelta.zip")
        self.assertEqual(r.ruta_mapa("aut01", "doble-vuelta.zip"), "mapas/autonomicas/andalucia-2026/doble-vuelta.zip")
        self.assertEqual(r.ruta_mapa("aut12", "mapa.geojson"), "mapas/autonomicas/galicia-2024/mapa.geojson")
        self.assertEqual(r.ruta_mapa("nac22", "mapa.geojson", "2019-11"), "mapas/historicos/congreso-2019-11/huesca/mapa.geojson")
        self.assertEqual(r.ruta_mapa("nac22", "composicion.csv", "2011-11"), "mapas/historicos/congreso-2011/huesca/composicion.csv")
        self.assertEqual(r.ruta_informe_doble_vuelta("nac"), "mapas/nacionales/congreso-2023/informe-doble-vuelta.json")
        self.assertEqual(r.ruta_informe_doble_vuelta("aut"), "mapas/autonomicas/informe-doble-vuelta.json")
        with self.assertRaises(r.RutaInvalida):
            r.ruta_mapa("aut18", "mapa.geojson")  # Ceuta: sin autonómica vigente (CRUCE.md, hallazgo 5)
        with self.assertRaises(r.RutaInvalida):
            r.ruta_mapa("nac01", "otro.zip")

    def test_estados_sin_run(self):
        self.assertEqual(r.ruta_estado("nac01", "ddd-audit-43750441261"), "interno/estados/nacionales/alava/audit.zip")
        self.assertEqual(r.ruta_estado("aut01", "ddd-audit-electoral-43728682179"), "interno/estados/autonomicas/andalucia/audit-electoral.zip")
        self.assertEqual(r.ruta_estado("nac01", "ddd-minimo-43750441261-M08"), "interno/estados/nacionales/alava/minimo-m08.zip")
        self.assertEqual(r.ruta_estado("nac01", "ddd-state-43750441261-M06"), "interno/estados/nacionales/alava/minimo-m06.zip")
        self.assertEqual(r.ruta_estado("congreso350_soria", "ddd-audit-42601453125"), "interno/competicion/soria/audit.zip")
        with self.assertRaises(r.RutaInvalida):
            r.ruta_estado("nac01", "ddd-full-run-manifest-1")

    def test_fuentes_sin_sha12(self):
        self.assertEqual(r.ruta_fuente("interior", "2023", "02202307_MESA_e78fc231326a.zip"), "fuentes/interior/2023/02202307_MESA.zip")
        self.assertEqual(r.ruta_fuente("ine", "2021", "seccionado_2021_772ad76b84e1.zip"), "fuentes/ine/2021/seccionado_2021.zip")
        self.assertEqual(r.ruta_fuente("nazioenbehatokia", None, "data/201111/sekzioa/01_d4cd5dfba24c.json"),
                         "fuentes/gobierno-vasco/data/201111/sekzioa/01.json")
        with self.assertRaises(r.RutaInvalida):
            r.ruta_fuente("ine", "AAAA", "30832.csv")

    def test_manifiesto_en_la_carpeta(self):
        self.assertEqual(r.ruta_manifiesto("mapas/nacionales/congreso-2023/alava/doble-vuelta.zip"),
                         "mapas/nacionales/congreso-2023/alava/manifiesto.json")
        m = r.manifiesto({"paquete.zip": {"sha256": "ab" * 32, "bytes": 3}}, run="44575597009-1", huella="cd" * 32, fecha="2026-11-22")
        self.assertEqual(m["run"], "44575597009-1")
        self.assertEqual(m["ficheros"]["paquete.zip"], {"sha256": "ab" * 32, "bytes": 3})


class ReglaDeNombres(unittest.TestCase):
    def test_prohibidos(self):
        for mala in ("nac01/43750441261/ddd-audit-43750441261.zip", "interno/estados/nacionales/nac01/audit.zip",
                     "interno/estados/nacionales/alava/audit-43750441261.zip", "fuentes/ine/2021/seccionado_2021_772ad76b84e1.zip",
                     "mapas/nacionales/congreso-2023/Álava/mapa.geojson", "interno/estados/nacionales/congreso_alava/audit.zip",
                     "interno/estados/nacionales/alava/audit-v1.2.zip", "web/actual/actual.json"):
            self.assertTrue(r.validar(mala), mala)

    def test_las_rutas_nuevas_del_cruce_valen(self):
        """Toda ruta nueva concreta del cruce cumple la regla, salvo las conocidas: año INE por fijar (AAAA) y la competición con run
        en el nombre (sustituida por `interno/competicion/<provincia>/<tipo>.zip`)."""
        malas = []
        with CRUCE.open(encoding="utf-8") as fh:
            for fila in csv.DictReader(fh):
                n = fila["ruta_nueva"]
                if not r.es_nueva(n) or "…" in n or n.endswith("/") or "/AAAA/" in n or n.startswith("interno/competicion/"):
                    continue
                if r.validar(n):
                    malas.append(n)
        self.assertEqual(malas, [])

    def test_candidatas(self):
        self.assertEqual(r.candidatas("fuentes/x/2023/a.zip", "arc-e/a.zip"), ["fuentes/x/2023/a.zip", "arc-e/a.zip"])
        self.assertEqual(r.candidatas(None, "arc-e/a.zip"), ["arc-e/a.zip"])
        self.assertEqual(r.candidatas("arc-e/a.zip", "arc-e/a.zip"), ["arc-e/a.zip"])


if __name__ == "__main__":
    unittest.main()
