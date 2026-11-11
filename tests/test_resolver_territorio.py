#!/usr/bin/env python3
# PROYECTO: Diputado de Distrito
# VERSIÓN: 1.0.0
# FECHA: 2026-11-10
# QUÉ HACE: pruebas D y E de T-170 §4 (T-214): resolutor único, catálogo con notacion/id_legacy biyectivo con la tabla
#   maestra y admisión de contratos con el id viejo o el nuevo.
# CAMBIOS: fichero nuevo.
# MOTIVO: D-61; corte 5.0.0 pasos 1-2.
# ANTERIOR: ninguna (fichero nuevo)
import re
import sys
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from ddd_core import territorio_ids as T  # noqa: E402


class Resolutor(unittest.TestCase):
    def test_literales_en_ambos_sentidos(self):
        # Literales de la tabla maestra (INE CPRO 01 = Álava; CODAUTO 13 = Madrid; CPRO 28 = Madrid; CPRO 51 = Ceuta).
        casos = {
            "congreso_alava": ("nac01", "NAC01 · Álava"),
            "nac01": ("nac01", "NAC01 · Álava"),
            "NAC01": ("nac01", "NAC01 · Álava"),
            "madrid": ("aut13", "AUT13 · Comunidad de Madrid"),
            "congreso_madrid": ("nac28", "NAC28 · Madrid"),
            "illes_balears": ("aut04", "AUT04 · Islas Baleares"),
            "congreso_ceuta": ("nac51", "NAC51 · Ceuta"),
            "ceuta": ("aut18", "AUT18 · Ceuta"),
        }
        for x, (nuevo, etiqueta) in casos.items():
            self.assertEqual(T.resolver_id(x), nuevo, x)
            self.assertEqual(T.etiqueta(x), etiqueta, x)
            self.assertEqual(T.codigo_semilla(x), etiqueta.split(" · ")[0], x)
        self.assertEqual(T.id_legacy("nac01"), "congreso_alava")
        self.assertEqual(T.id_legacy("aut13"), "madrid")

    def test_71_ids_biyectivos_y_sin_colision(self):
        tabla = T.tabla()
        self.assertEqual(len(tabla), 71)
        self.assertEqual(sum(t.ambito == "AUT" for t in tabla.values()), 19)
        self.assertEqual(sum(t.ambito == "NAC" for t in tabla.values()), 52)
        legacy = {t.id_legacy for t in tabla.values()}
        self.assertEqual(len(legacy), 71)
        self.assertFalse(legacy & set(tabla), "un id viejo coincide con uno nuevo")
        for t in tabla.values():
            self.assertEqual(T.resolver_id(t.id_legacy), t.id)
            self.assertEqual(T.resolver_id(t.id), t.id)
            self.assertEqual(T.id_legacy(t.id), t.id_legacy)
            self.assertRegex(t.id, r"^(aut|nac)\d\d$")

    def test_duplicados_aut_nac_no_se_cruzan(self):
        for aut, nac in (("madrid", "nac28"), ("ceuta", "nac51"), ("melilla", "nac52"), ("illes_balears", "nac07"),
                         ("region_de_murcia", "nac30"), ("cantabria", "nac39"), ("la_rioja", "nac26")):
            self.assertFalse(T.mismo_territorio(aut, nac), (aut, nac))
        self.assertTrue(T.mismo_territorio("congreso_alava", "nac01"))
        self.assertTrue(T.mismo_territorio("x_sintetico", "x_sintetico"))
        self.assertFalse(T.mismo_territorio("x_sintetico", "nac01"))

    def test_desconocido_y_sufijo_350_reservado(self):
        with self.assertRaises(T.IdTerritorioDesconocido):
            T.resolver_id("congreso_illes")
        with self.assertRaises(T.IdTerritorioDesconocido):
            T.resolver_id("nac53")
        with self.assertRaises(T.IdReservado):
            T.resolver_id("nac01-350")
        # D-76: las 350 no se migran.
        self.assertEqual(T.resolver_id("congreso350_alava"), "congreso350_alava")

    def test_contador_de_lecturas_por_id_viejo(self):
        antes = T.LECTURAS_LEGACY["congreso_huesca"]
        T.resolver_id("congreso_huesca")
        T.resolver_id("nac22")
        self.assertEqual(T.LECTURAS_LEGACY["congreso_huesca"], antes + 1)

    def test_tabla_maestra_rechaza_duplicados(self):
        cab = "codigo,ambito,codigo_ine,literal_ine,nombre_es,id_interno\n"
        with self.assertRaises(ValueError):
            T._leer_tabla(cab + "NAC01,NAC,01,x,Álava,a\nNAC02,NAC,02,x,Albacete,a\n")
        with self.assertRaises(ValueError):
            T._leer_tabla(cab + "NAC01,NAC,01,x,Álava,nac02\nNAC02,NAC,02,x,Albacete,b\n")


class CatalogoConNotacion(unittest.TestCase):
    """Prueba D: catálogo 71 entradas AUT/NAC con notacion e id_legacy coherentes con la tabla maestra."""

    def test_catalogo(self):
        data = yaml.safe_load((ROOT / "configuracion/catalogo_territorios_espana_2025.yaml").read_text(encoding="utf-8"))
        filas = list(data["territories"]) + list(data["pilot_territories"])
        con = [r for r in filas if "notacion" in r]
        self.assertEqual(len(con), 71)
        tabla = T.tabla()
        vistos = set()
        for r in con:
            t = tabla[r["notacion"].lower()]
            self.assertEqual(r["id_legacy"], t.id_legacy)
            self.assertEqual(r["territory_id"], t.id_legacy)  # hasta el git mv
            if t.ambito == "AUT":
                self.assertEqual(r["autonomous_community_code_ine"], t.codigo[3:])
            else:
                self.assertEqual(r["province_codes"], [t.codigo[3:]])
            vistos.add(t.codigo)
        self.assertEqual(len(vistos), 71)
        # Las 49 de 350 quedan fuera del corte (D-76) y sin notación.
        r350 = [r for r in filas if r.get("scope") == "congreso_350"]
        self.assertEqual(len(r350), 49)
        self.assertFalse(any("notacion" in r or "id_legacy" in r for r in r350))


class ContratosLeenAmbosIds(unittest.TestCase):
    def test_contrato_territorial(self):
        from ddd_core.territory_contract import validate_production_contract

        path = ROOT / "territorios/congreso_huesca/config/congreso_huesca_2025.yaml"
        viejo = validate_production_contract(path, expected_territory="congreso_huesca")
        nuevo = validate_production_contract(path, expected_territory="nac22")
        self.assertEqual(viejo["status"], nuevo["status"])
        self.assertEqual(viejo["errors"], nuevo["errors"])
        otro = validate_production_contract(path, expected_territory="nac50")
        self.assertTrue(any("no coincide" in e for e in otro["errors"]))
        path = ROOT / "territorios/madrid/config/madrid_2025.yaml"
        cruce = validate_production_contract(path, expected_territory="nac28")
        self.assertTrue(any("no coincide" in e for e in cruce["errors"]))


class Gemelo350SinNotacion(unittest.TestCase):
    """Revisión T-214: el generador 350 deriva del padre (con notacion/id_legacy) la misma fila que ya hay."""

    def test_master_line_reproduce_la_fila_existente(self):
        sys.path.insert(0, str(ROOT / "herramientas"))
        import generar_provincias_congreso_350 as g

        csv_sha = g._sha(ROOT / "configuracion/resultados_oficiales_congreso_2023.csv")
        catalogo = (ROOT / "configuracion/catalogo_territorios_espana_2025.yaml").read_text(encoding="utf-8")
        for p in g.provinces(ROOT):
            if p["source_id"] not in ("congreso_alava", "congreso_madrid", "congreso_ceuta"):
                continue
            linea = g._master_line(ROOT, p, csv_sha)
            self.assertNotIn("notacion", linea)
            self.assertNotIn("id_legacy", linea)
            self.assertIn(f"parent_territory_id: {p['source_id']}}}", linea)
            # T-225: el padre pasó a source_prepared_pending_pre_m04 (par 2025/2025); el gemelo 350 conserva su estado.
            gemelo = next(x for x in catalogo.splitlines() if f"territory_id: {p['territory_id']}," in x)
            self.assertEqual(re.sub(r"status: \w+,", "", linea), re.sub(r"status: \w+,", "", gemelo))


if __name__ == "__main__":
    unittest.main()
