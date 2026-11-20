# -*- coding: utf-8 -*-
"""T-365 (D-125): contrato por elección del histórico por época, contrato M01-M06 por provincia y puerta M07/M08.

PROYECTO: Diputado de Distrito
VERSIÓN: 1.4.3 · FECHA: 2026-11-19 · ESTADO: candidato
ANTERIOR: legacy/tests/test_t365_historico_epoca_v1.4.2_20261119.py
CAMBIOS: 1.4.3: T-400 (D-180): clase RepartoParticiones. 1.4.2: T-400: clase PuentesDeEpoca. 1.4.1: T-405: clase TopologiaAdministrativa. 1.4.0: T-399: estado APARTADA_VOTOS admitido (D-158). 1.3.0: T-402: `materializar` normaliza la geometría (parche del seccionado en los tests con zip falso; clase NormalizacionGeometria con zip real). 1.2.0: T-396 (D-153): estado APARTADA admitido; contratos 1.2.0 con anterior 1.1.0. 1.1.0: T-389 (T-365b): contratos con la tabla de T-364b (1.2.0): provincias apartadas = BLOQUEADA_SIN_DATO sin filas, fallo cerrado con la tabla vieja.
MOTIVO: T-365. Sin red ni fuentes pesadas: el flujo M07/M08 usa un M06 sintético y los módulos reales.
"""
from __future__ import annotations

import csv
import hashlib
import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "herramientas"))
import contrato_historico_epoca as che  # noqa: E402

ELECCIONES = ("2011-11", "2015-12", "2016-06", "2019-04", "2019-11")


def _sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


class ContratosVersionados(unittest.TestCase):
    """Los cinco contratos versionados son coherentes con los ficheros acreditados que no cambian con la producción."""

    def test_k_y_huellas_de_cada_eleccion(self):
        fr2 = json.loads((ROOT / che.FUENTES_R2).read_text(encoding="utf-8"))["fuentes"]
        espejo = json.loads((ROOT / che.ESPEJO).read_text(encoding="utf-8"))["ficheros"]
        for e in ELECCIONES:
            with self.subTest(eleccion=e):
                c = json.loads(che.ruta_contrato(e).read_text(encoding="utf-8"))
                self.assertEqual((c["schema"], c["eleccion"], c["clave_espejo"]), (che.SCHEMA, e, che.ELECCIONES[e]))
                csv_boe = ROOT / c["escanos"]["csv"]
                self.assertEqual(_sha(csv_boe), c["escanos"]["sha256"])
                boe = che.escanos_boe(csv_boe)
                self.assertEqual(sorted(c["provincias"]), sorted(boe))
                self.assertEqual(sum(p["K"] for p in c["provincias"].values()), 350)
                self.assertEqual(c["seccionado"]["sha256"], fr2[c["seccionado"]["fichero"]]["sha256"])
                for cpro, p in c["provincias"].items():
                    self.assertEqual(p["K"], boe[cpro]["K"])
                    self.assertEqual(p["territorio"], f"nac{cpro}")  # id canónico, nunca uno viejo
                    self.assertEqual(p["votos"]["sha256"], espejo[p["votos"]["ruta"]]["sha256"])
                    self.assertIn(p["estado"], ("LISTA", "BLOQUEADA_RELLENO", "BLOQUEADA_SIN_DATO", "APARTADA", "APARTADA_VOTOS"))
                    # T-364b: BLOQUEADA_SIN_DATO = provincia sin filas en la tabla (apartada) o con secciones sin dato
                    self.assertEqual(p["estado"] == "BLOQUEADA_SIN_DATO",
                                     bool(p["poblacion"]["secciones_sin_dato"]) or p["poblacion"]["secciones"] == 0)
                    self.assertIsInstance(p["poblacion"]["secciones_sin_seccionado"], list)

    def test_huesca_2019_11_tres_escanos(self):
        c = json.loads(che.ruta_contrato("2019-11").read_text(encoding="utf-8"))
        self.assertEqual((c["provincias"]["22"]["K"], c["seccionado"]["anio"], c["poblacion"]["anio_referencia"]), (3, 2020, 2020))


class EscanosBoe(unittest.TestCase):
    def test_k_ambiguo_o_que_no_suma_falla(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "boe.csv"
            p.write_text("codigo,provincia,escanos_circunscripcion,partido,votos,escanos\n22,Huesca,3,A,10,2\n22,Huesca,3,B,5,1\n",
                         encoding="utf-8")
            self.assertEqual(che.escanos_boe(p)["22"]["K"], 3)  # control positivo
            p.write_text("codigo,provincia,escanos_circunscripcion,partido,votos,escanos\n22,Huesca,3,A,10,2\n", encoding="utf-8")
            with self.assertRaises(SystemExit):
                che.escanos_boe(p)
            p.write_text("codigo,provincia,escanos_circunscripcion,partido,votos,escanos\n22,Huesca,3,A,10,2\n22,Huesca,2,B,5,1\n",
                         encoding="utf-8")
            with self.assertRaises(SystemExit):
                che.escanos_boe(p)


def _contrato_sintetico(tabla_sha: str, base_sha: str, secc_sha: str, votos_sha: str) -> dict:
    return {"eleccion": "2019-11", "fecha": "2019-11-10", "clave_espejo": "201911",
            "seccionado": {"anio": 2020, "fichero": "seccionado_2020.zip", "sha256": secc_sha},
            "poblacion": {"fichero": "tabla.csv", "sha256": tabla_sha, "anio_referencia": 2020},
            "escanos": {"csv": "configuracion/x.csv", "sha256": "e" * 64, "boe": "BOE-A-2019-18147"},
            "provincias": {"22": {"territorio": "nac22", "K": 3, "estado": "LISTA", "k_source": "norma", "k_rationale": "D-125: K BOE",
                                  "contrato_base": {"ruta": "territorios/nac22/config/nac22_2025.yaml", "sha256": base_sha},
                                  "votos": {"ruta": "data/201911/sekzioa/22.json", "sha256": votos_sha},
                                  "poblacion": {"secciones": 2, "total": 30}}}}


BASE = {"meta": {"territory_id": "nac22", "run_name": "nac22_2025", "year": 2025, "source_population_year": 2023,
                 "source_section_year": 2023},
        "io": {"input": {"seccionado": {"path": "inputs/seccionado_2023.zip"}, "population_cip": {"paths": ["inputs/65034.csv.zip"]}}},
        "territory_contract": {"k_districts": 2, "k_source": "formula"},
        "modulos": {"modulo_02_construir_adyacencias": {"topology_bridges": []},
                    "modulo_04_generar_semillas": {"k_districts": 2, "pop_field": "POP_2023",
                                                   "out_geojson": "x/nac22_2025_m04_semillas.geojson.zip"},
                    "modulo_06_consolidar_distritos": {"expected_districts": 2, "pop_field": "POP_2023"}},
        "validation": {"expected_districts": 2, "province_districts": {"22": 2}, "population_floor_ratio": 0.85},
        "resolved_source_contract": {"runtime": {"population_field": "POP_2023"}},
        "generation_state": {"pre_m04_run_id": 1}}


class TablaPoblacion(unittest.TestCase):
    """Las dos interfaces: T-358 (columna elección) y T-364 (un CSV por elección; sin_dato con población vacía falla)."""

    def test_interfaz_t364(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "poblacion_seccion_2019-11.csv"
            p.write_text("sección,población,origen,ajustada,años_fuente\n2200101001,10,dato,no,2020\n"
                         "2200101002,7,interpolada,sí,2019-2021\n", encoding="utf-8")
            t = che.leer_tabla(p, "2019-11")
            self.assertEqual((t["2200101001"]["poblacion"], t["2200101002"]["origen"]), (10, "interpolada"))
            with self.assertRaises(SystemExit):
                che.leer_tabla(p, "2019-04")  # fichero de otra elección
            p.write_text("sección,población,origen,ajustada,años_fuente\n2200101001,,sin_dato,no,\n"
                         "2200101002,7,no_listada,sí,2019-2021\n", encoding="utf-8")
            t = che.leer_tabla(p, "2019-11")
            self.assertIsNone(t["2200101001"]["poblacion"])  # nunca 0: la provincia queda BLOQUEADA_SIN_DATO
            self.assertEqual(t["2200101002"]["origen"], "no_listada")
            p.write_text("sección,población,origen,ajustada,años_fuente\n2200101001,,dato,no,2020\n", encoding="utf-8")
            with self.assertRaises(SystemExit):
                che.leer_tabla(p, "2019-11")  # vacío sin sin_dato: tabla inválida


class ContratoProvincia(unittest.TestCase):
    def test_cambia_fuentes_anios_y_k_y_nada_mas(self):
        c = _contrato_sintetico("a" * 64, "b" * 64, "c" * 64, "d" * 64)
        cfg = che.contrato_provincia(BASE, c, "22", "2019-11", "s.zip", "p.csv", {"seccionado": "c" * 64, "poblacion": "f" * 64},
                                     "9" * 64)
        self.assertEqual(cfg["meta"]["run_name"], "nac22_h2019_11")
        self.assertEqual((cfg["meta"]["source_population_year"], cfg["meta"]["source_section_year"]), (2020, 2020))
        self.assertEqual(cfg["meta"]["historico_epoca"]["election_id"], "nac22_2019-11-10")
        self.assertEqual((cfg["territory_contract"]["k_districts"], cfg["modulos"]["modulo_04_generar_semillas"]["k_districts"],
                          cfg["modulos"]["modulo_06_consolidar_distritos"]["expected_districts"],
                          cfg["validation"]["expected_districts"], cfg["validation"]["province_districts"]), (3, 3, 3, 3, {"22": 3}))
        self.assertEqual(cfg["modulos"]["modulo_04_generar_semillas"]["pop_field"], "POP_2020")
        self.assertIn("nac22_h2019_11_m04", cfg["modulos"]["modulo_04_generar_semillas"]["out_geojson"])
        self.assertNotIn("resolved_source_contract", cfg)
        self.assertNotIn("pre_m04_run_id", cfg["generation_state"])
        self.assertEqual(cfg["validation"]["population_floor_ratio"], 0.85)  # límites del contrato base intactos
        self.assertEqual(BASE["territory_contract"]["k_districts"], 2)  # la base no se toca

    def test_topologia_acreditada_falla(self):
        base = json.loads(json.dumps(BASE))
        base["validation"]["topology_accreditation"] = {"package_sha256": "x"}
        with self.assertRaises(SystemExit):
            che.contrato_provincia(base, _contrato_sintetico("a" * 64, "b" * 64, "c" * 64, "d" * 64), "22", "2019-11",
                                   "s.zip", "p.csv", {"seccionado": "c", "poblacion": "f"}, "9" * 64)


class Materializar(unittest.TestCase):
    """Fallo cerrado ante huellas distintas o casado incompleto; control positivo con todo cuadrado."""

    def _arbol(self, d: Path, secciones_geo: set):
        import yaml
        root, fuentes = d / "root", d / "fuentes"
        (root / "territorios/nac22/config").mkdir(parents=True)
        fuentes.mkdir()
        base = root / "territorios/nac22/config/nac22_2025.yaml"
        base.write_text(yaml.safe_dump(BASE), encoding="utf-8")
        (fuentes / "seccionado_2020.zip").write_bytes(b"zip")
        (fuentes / "tabla.csv").write_text("elección,sección,población,origen,año_fuente_relleno\n"
                                           "2019-11,2200101001,10,dato,\n2019-11,2200101002,20,dato,\n"
                                           "2015-12,2200101003,5,dato,\n", encoding="utf-8")
        c = _contrato_sintetico(_sha(fuentes / "tabla.csv"), _sha(base), _sha(fuentes / "seccionado_2020.zip"), "d" * 64)
        cpath = root / "contrato.json"
        cpath.write_text(json.dumps(c), encoding="utf-8")
        def falso(secc, cpro, cache, sha):  # zip de mentira: la normalización real se prueba en NormalizacionGeometria
            dest = cache / "seccionado_normalizado.zip"
            dest.write_bytes(secc.read_bytes())
            return dest, {"normalizado_sha256": _sha(dest), "corregidas": []}
        parche = mock.patch.multiple(che, _secciones_seccionado=mock.Mock(return_value=secciones_geo), _normalizar_seccionado=falso)
        return root, fuentes, cpath, parche

    def test_casado_completo_escribe_el_contrato(self):
        import yaml
        with tempfile.TemporaryDirectory() as d:
            root, fuentes, cpath, parche = self._arbol(Path(d), {"2200101001", "2200101002"})
            with parche:
                out = che.materializar("2019-11", "nac22", fuentes, root, cpath)
            cfg = yaml.safe_load(out.read_text(encoding="utf-8"))
            self.assertEqual(out.name, "nac22_h2019_11.yaml")
            self.assertEqual(cfg["territory_contract"]["k_districts"], 3)
            pob = root / cfg["io"]["input"]["population_cip"]["paths"][0]
            self.assertEqual(pob.read_text(encoding="utf-8").splitlines()[1:], ["2020,2200101001,10,dato", "2020,2200101002,20,dato"])
            self.assertEqual({x["role"] for x in cfg["generation_state"]["source_inputs"]}, {"population", "target_sectioning"})

    def test_casado_incompleto_falla(self):
        for geo in ({"2200101001"}, {"2200101001", "2200101002", "2200101009"}):
            with self.subTest(geo=sorted(geo)), tempfile.TemporaryDirectory() as d:
                root, fuentes, cpath, parche = self._arbol(Path(d), geo)
                with parche, self.assertRaises(SystemExit) as cm:
                    che.materializar("2019-11", "nac22", fuentes, root, cpath)
                self.assertIn("CASADO_POBLACION_SECCIONADO", str(cm.exception))

    def test_puente_fuera_del_seccionado_falla(self):
        import yaml
        with tempfile.TemporaryDirectory() as d:
            geo = {"2200101001", "2200101002"}
            root, fuentes, cpath, parche = self._arbol(Path(d), geo)
            base = root / "territorios/nac22/config/nac22_2025.yaml"
            cfg = yaml.safe_load(base.read_text(encoding="utf-8"))
            for v, falla in ((2200101002, False), ("2200101099", True)):  # entero sin cero inicial (zfill) y extremo inexistente
                cfg["modulos"]["modulo_02_construir_adyacencias"]["topology_bridges"] = [{"u": "2200101001", "v": v}]
                base.write_text(yaml.safe_dump(cfg), encoding="utf-8")
                c = json.loads(cpath.read_text(encoding="utf-8"))
                c["provincias"]["22"]["contrato_base"]["sha256"] = _sha(base)
                cpath.write_text(json.dumps(c), encoding="utf-8")
                with self.subTest(v=v), parche:
                    if falla:
                        with self.assertRaises(SystemExit) as cm:
                            che.materializar("2019-11", "nac22", fuentes, root, cpath)
                        self.assertIn("PUENTE_FUERA_DEL_SECCIONADO", str(cm.exception))
                    else:
                        che.materializar("2019-11", "nac22", fuentes, root, cpath)

    def test_sin_seccionado_distinto_del_declarado_falla(self):
        with tempfile.TemporaryDirectory() as d:
            root, fuentes, cpath, parche = self._arbol(Path(d), {"2200101001", "2200101002"})
            c = json.loads(cpath.read_text(encoding="utf-8"))
            c["provincias"]["22"]["poblacion"]["secciones_sin_seccionado"] = ["2200101009"]
            cpath.write_text(json.dumps(c), encoding="utf-8")
            with parche, self.assertRaises(SystemExit) as cm:
                che.materializar("2019-11", "nac22", fuentes, root, cpath)
            self.assertIn("SIN_SECCIONADO_DISTINTO_DEL_CONTRATO", str(cm.exception))

    def test_provincia_bloqueada_por_relleno_falla(self):
        with tempfile.TemporaryDirectory() as d:
            root, fuentes, cpath, parche = self._arbol(Path(d), {"2200101001", "2200101002"})
            c = json.loads(cpath.read_text(encoding="utf-8"))
            c["provincias"]["22"]["estado"] = "BLOQUEADA_RELLENO"
            cpath.write_text(json.dumps(c), encoding="utf-8")
            with parche, self.assertRaises(SystemExit) as cm:
                che.materializar("2019-11", "nac22", fuentes, root, cpath)
            self.assertIn("PROVINCIA_NO_LISTA", str(cm.exception))

    def test_huella_distinta_falla(self):
        with tempfile.TemporaryDirectory() as d:
            root, fuentes, cpath, parche = self._arbol(Path(d), {"2200101001", "2200101002"})
            (fuentes / "seccionado_2020.zip").write_bytes(b"otro")
            with parche, self.assertRaises(SystemExit) as cm:
                che.materializar("2019-11", "nac22", fuentes, root, cpath)
            self.assertIn("FUENTE_HUELLA_DISTINTA", str(cm.exception))


class NormalizacionGeometria(unittest.TestCase):
    """T-402: la misma normalización auditada de la adquisición; válida intacta, inválida válida con área conservada."""

    BOW = "POLYGON((0 0, 2 2, 2 0, 0 2, 0 0))"  # corbata: anillo autointersectante, 2 triángulos de 1 unidad² cada uno
    OK = "POLYGON((10 0, 12 0, 12 2, 10 2, 10 0))"

    def _gdf(self, wkts):
        import geopandas as gpd
        from shapely import wkt
        return gpd.GeoDataFrame({"CUSEC": [f"22001{i:05d}" for i in range(len(wkts))]}, geometry=[wkt.loads(w) for w in wkts],
                                crs="EPSG:25830")

    def test_invalida_pasa_a_valida_con_area_y_valida_no_cambia(self):
        g = self._gdf([self.OK, self.BOW])
        self.assertFalse(g.geometry.is_valid.all())  # control negativo: la entrada es realmente inválida
        out, corr, pol = che.normalizar_geometrias(g)
        self.assertTrue(out.geometry.is_valid.all())
        self.assertEqual([x["seccion"] for x in corr], ["2200100001"])
        self.assertEqual(out.geometry.iloc[0].wkb, g.geometry.iloc[0].wkb)  # la válida, byte a byte
        self.assertAlmostEqual(out.geometry.iloc[1].area, 2.0, places=9)  # valor literal: dos triángulos de 1
        self.assertEqual(len(pol["sha256"]), 64)

    def test_solo_validas_no_cambia_nada(self):
        g = self._gdf([self.OK])
        out, corr, _ = che.normalizar_geometrias(g)
        self.assertEqual((corr, out.geometry.iloc[0].wkb), ([], g.geometry.iloc[0].wkb))

    def test_no_normalizable_falla_cerrado(self):
        g = self._gdf(["POLYGON EMPTY"])
        with self.assertRaises(SystemExit):
            che.normalizar_geometrias(g)

    def test_zip_normalizado_reproducible_con_huella(self):
        import zipfile
        with tempfile.TemporaryDirectory() as d:
            d = Path(d)
            g = self._gdf([self.OK, self.BOW])
            g.to_file(d / "s.shp")
            zp = d / "origen.zip"
            with zipfile.ZipFile(zp, "w") as z:
                for f in sorted(d.glob("s.*")):
                    z.write(f, f.name)
            r = []
            for n in ("a", "b"):
                (d / n).mkdir()
                r.append(che._normalizar_seccionado(zp, "22", d / n, _sha(zp)))
            self.assertEqual(r[0][1]["normalizado_sha256"], r[1][1]["normalizado_sha256"])
            self.assertEqual(r[0][1]["huella_geometrias_sha256"], r[1][1]["huella_geometrias_sha256"])
            self.assertEqual(len(r[0][1]["corregidas"]), 1)
            self.assertTrue(che._leer_seccionado(r[0][0], "22").geometry.is_valid.all())
            self.assertEqual(che._leer_seccionado(r[0][0], "22")["CUSEC"].tolist(), g["CUSEC"].tolist())


class MaterializarZipReal(unittest.TestCase):
    """T-402: `materializar` de punta a punta con un seccionado REAL (zip de shapefile con una sección inválida), sin parches."""

    def test_camino_completo_normaliza_y_deja_huellas(self):
        import zipfile
        import geopandas as gpd
        import yaml
        from shapely import wkt
        with tempfile.TemporaryDirectory() as d:
            d = Path(d)
            root, fuentes = d / "root", d / "fuentes"
            (root / "territorios/nac22/config").mkdir(parents=True)
            fuentes.mkdir()
            base = root / "territorios/nac22/config/nac22_2025.yaml"
            base.write_text(yaml.safe_dump(BASE), encoding="utf-8")
            ok, bow = NormalizacionGeometria.OK, NormalizacionGeometria.BOW
            g = gpd.GeoDataFrame({"CUSEC": ["2200101001", "2200101002", "2300101001"]},
                                 geometry=[wkt.loads(ok), wkt.loads(bow), wkt.loads(ok)], crs="EPSG:25830")  # la 23 es de otra provincia
            (d / "crudo").mkdir()
            g.to_file(d / "crudo" / "s.shp")
            with zipfile.ZipFile(fuentes / "seccionado_2020.zip", "w") as z:
                for f in sorted((d / "crudo").glob("s.*")):
                    z.write(f, f.name)
            (fuentes / "tabla.csv").write_text("elección,sección,población,origen,año_fuente_relleno\n"
                                               "2019-11,2200101001,10,dato,\n2019-11,2200101002,20,dato,\n", encoding="utf-8")
            c = _contrato_sintetico(_sha(fuentes / "tabla.csv"), _sha(base), _sha(fuentes / "seccionado_2020.zip"), "d" * 64)
            cpath = root / "contrato.json"
            cpath.write_text(json.dumps(c), encoding="utf-8")
            out = che.materializar("2019-11", "nac22", fuentes, root, cpath)
            cfg = yaml.safe_load(out.read_text(encoding="utf-8"))
            geo = cfg["meta"]["historico_epoca"]["geometria"]
            zip_n = root / next(x["path"] for x in cfg["generation_state"]["source_inputs"] if x["role"] == "target_sectioning")
            sha_n = next(x["sha256"] for x in cfg["generation_state"]["source_inputs"] if x["role"] == "target_sectioning")
            self.assertEqual(_sha(zip_n), sha_n)  # la huella de source_inputs es la del zip normalizado, no la del crudo
            self.assertEqual((geo["normalizado_sha256"], geo["origen_sha256"]), (sha_n, c["seccionado"]["sha256"]))
            self.assertNotEqual(sha_n, c["seccionado"]["sha256"])
            self.assertEqual([x["seccion"] for x in geo["corregidas"]], ["2200101002"])
            self.assertEqual(geo["secciones"], 2)  # solo la provincia 22
            leido = che._leer_seccionado(zip_n, None)
            self.assertTrue(leido.geometry.is_valid.all())
            self.assertEqual(leido["CUSEC"].tolist(), ["2200101001", "2200101002"])
            self.assertTrue(leido.geometry.iloc[0].equals(wkt.loads(ok)))  # la válida, intacta (el shapefile reordena el anillo: se compara por conjunto)
            self.assertEqual(geo["huella_geometrias_sha256"], che._huella_geometrias(leido))


class PuentesDeEpoca(unittest.TestCase):
    """T-400: La Graciosa (3502401010) no existe en el seccionado 2012; está dentro de 3502401005 (contenida al 100 % en el donante 2019): el puente se omite."""
    BASE = {"modulos": {"modulo_02_construir_adyacencias": {"topology_bridges": [
        {"u": "3502401010", "v": "3502401001", "admin_scope": "province:35", "edge_type": "maritime_group"}]}}}
    GEO = {"3502401001", "3502401005"}

    def _c(self):
        return json.loads((ROOT / "configuracion/historico_epoca/contrato_2011_11.json").read_text(encoding="utf-8"))

    def test_extremo_ausente_declarado_omite_el_puente(self):
        out = che._puentes_de_epoca(ROOT, self._c(), "2011-11", "35", self.BASE, self.GEO, None)
        self.assertEqual(out, [])  # la 3502401005 ya contiene La Graciosa: M02 rechaza un puente sin desconexión
        self.assertEqual(self.BASE["modulos"]["modulo_02_construir_adyacencias"]["topology_bridges"][0]["u"], "3502401010")

    def test_sin_declaracion_o_con_otra_huella_falla_cerrado(self):
        with self.assertRaises(che.ErrorContrato):
            che._puentes_de_epoca(ROOT, self._c(), "2011-11", "35", self.BASE, {"3502401001"}, None)  # destino ausente
        with self.assertRaises(che.ErrorContrato):
            che._puentes_de_epoca(ROOT, self._c(), "2011-11", "14", self.BASE, self.GEO, None)  # sin declaración en esa provincia
        c = self._c()
        c["seccionado"]["sha256"] = "0" * 64
        with self.assertRaises(che.ErrorContrato):
            che._puentes_de_epoca(ROOT, c, "2011-11", "35", self.BASE, self.GEO, None)

    def test_puente_con_extremos_presentes_pasa_tal_cual(self):
        geo = self.GEO | {"3502401010"}
        out = che._puentes_de_epoca(ROOT, self._c(), "2011-11", "35", self.BASE, geo, None)
        self.assertEqual(out[0]["u"], "3502401010")


class RepartoParticiones(unittest.TestCase):
    """T-400 (D-180): K por partición insular con la población de la época. Poblaciones medidas con poblacion_seccion_2011-11.csv
    (sha256 45aa3552…) y el lookup de particiones; cuotas esperadas escritas a mano (Hamilton por componentes, ≥ 1 por partición)."""

    def _pob(self, territorio, por_particion):
        d = json.loads((ROOT / "configuracion/particiones_insulares_2025.json").read_text(encoding="utf-8"))["territories"][territorio]
        pob = {}
        for comp, n in por_particion.items():
            mun = next(m for m, c in d["municipality_to_partition"].items() if c == comp)
            pob[mun + "01001"] = {"poblacion": n, "origen": "dato"}
        return pob

    def _base(self, territorio):
        import yaml
        return yaml.safe_load((ROOT / f"territorios/{territorio}/config/{territorio}_2025.yaml").read_text(encoding="utf-8"))

    def test_las_palmas_2011_seis_uno_uno_y_fuerteventura_exenta(self):
        pob = self._pob("nac35", {"35-C01": 846485, "35-C02": 102810, "35-G01": 137980})
        r = che._reparto_particiones(ROOT, self._base("nac35"), "nac35", 8, pob)
        self.assertEqual(r["cuota"], {"35-C01": 6, "35-C02": 1, "35-G01": 1})
        self.assertEqual(r["exentas"], ["35-C02"])  # 102.810 < 0,85 · 1.087.275 / 8 = 115.523
        self.assertTrue(r["auditoria"]["35-C02"]["floor_exception_governed"])

    def test_cuota_de_contrato_provincial_para_un_territorio_sin_particiones(self):
        base = {"validation": {}, "territory_contract": {}}
        self.assertIsNone(che._reparto_particiones(ROOT, base, "nac22", 3, {}))

    def test_santa_cruz_2011_falla_cerrado_sin_politica_de_excepcion(self):
        pob = self._pob("nac38", {"38-C01": 877740, "38-G01": 115715})  # 38-G01 < suelo 120.634 y la política de nac38 no gobierna la excepción
        with self.assertRaises(ValueError):
            che._reparto_particiones(ROOT, self._base("nac38"), "nac38", 7, pob)


class TopologiaAdministrativa(unittest.TestCase):
    """T-405: municipio no conexo del seccionado de la época (Fuente Palmera, 14030, 2011-11) acreditado para M04."""
    FP = ["1403001001", "1403001002", "1403001003", "1403001004", "1403001005", "1403002002", "1403002001"]

    def _decl(self):
        return json.loads((ROOT / "configuracion/historico_epoca/topologia_administrativa.json").read_text(encoding="utf-8"))["elecciones"]["2011-11"]

    def test_atada_al_seccionado_del_contrato(self):
        c = json.loads((ROOT / "configuracion/historico_epoca/contrato_2011_11.json").read_text(encoding="utf-8"))
        self.assertEqual(self._decl()["seccionado_sha256"], c["seccionado"]["sha256"])

    def test_la_validacion_del_motor_acepta_dos_componentes_6_y_1(self):
        from ddd_core.topology_preflight import validate_administrative_components
        d = self._decl()["provincias"]["14"][0]
        ids = [x for comp in d["components"] for x in comp]
        units = {u: {"province": "14", "municipality": "14030"} for u in ids}
        resto = [u for u in ids if u != "1403002001"]
        aristas = list(zip(resto, resto[1:]))  # el resto, conexo; la 1403002001, aislada (hecho medido en el seccionado 2012)
        ok, mal = validate_administrative_components(units=units, declarations=[{k: v for k, v in d.items() if k != "municipio"}],
                                                     operational_edges=aristas)
        self.assertEqual((len(mal), sorted((len(x) for x in ok[0]["components"]), reverse=True)), (0, [6, 1]))
        _, mal = validate_administrative_components(units=units, declarations=[{k: v for k, v in d.items() if k != "municipio"}],
                                                    operational_edges=aristas + [("1403002001", "1403001001")])
        self.assertEqual(len(mal), 1)  # si el seccionado cambia y la sección se conecta, la acreditación ya no vale

    def _con_seccionado(self, mun):
        import pandas as pd
        return mock.patch.object(che, "_leer_seccionado", return_value=pd.DataFrame({"CUSEC": self.FP, "CUMUN": mun}))

    def test_materializar_la_emite_y_falla_si_no_cubre_el_municipio(self):
        c = json.loads((ROOT / "configuracion/historico_epoca/contrato_2011_11.json").read_text(encoding="utf-8"))
        with self._con_seccionado(["14030"] * 7):
            decl = che._topologia_declarada(ROOT, c, "2011-11", "14", Path("x"))
        self.assertEqual([d["admin_scope"] for d in decl], ["municipality:14030"])
        self.assertNotIn("municipio", decl[0])
        with self._con_seccionado(["14030"] * 6 + ["14031"]), self.assertRaises(SystemExit) as cm:
            che._topologia_declarada(ROOT, c, "2011-11", "14", Path("x"))
        self.assertIn("TOPOLOGIA_NO_CUBRE_EL_MUNICIPIO", str(cm.exception))

    def test_otro_seccionado_falla_y_sin_declaracion_es_vacio(self):
        c = json.loads((ROOT / "configuracion/historico_epoca/contrato_2011_11.json").read_text(encoding="utf-8"))
        c["seccionado"]["sha256"] = "0" * 64
        with self.assertRaises(SystemExit) as cm:
            che._topologia_declarada(ROOT, c, "2011-11", "14", Path("x"))
        self.assertIn("TOPOLOGIA_DE_OTRO_SECCIONADO", str(cm.exception))
        self.assertEqual(che._topologia_declarada(ROOT, c, "2011-11", "23", Path("x")), [])
        self.assertEqual(che._topologia_declarada(ROOT, c, "2019-11", "14", Path("x")), [])

    def test_contrato_provincia_lleva_la_acreditacion_con_el_binding_exacto(self):
        from ddd_core.topology_preflight import topology_source_binding, validate_topology_accreditation_binding
        c = _contrato_sintetico("a" * 64, "b" * 64, "c" * 64, "d" * 64)
        decl = [{"admin_scope": "municipality:22001", "components": [["a"], ["b"]], "reason": "r", "source": "s", "evidence": {}}]
        cfg = che.contrato_provincia(BASE, c, "22", "2019-11", "s.zip", "p.csv", {"seccionado": "c", "poblacion": "f"}, "9" * 64, None, decl)
        b = validate_topology_accreditation_binding(cfg)
        self.assertEqual((b["present"], b["valid"]), (True, True))
        self.assertEqual(cfg["validation"]["topology_accreditation"]["source_binding"], topology_source_binding(cfg))
        sin = che.contrato_provincia(BASE, c, "22", "2019-11", "s.zip", "p.csv", {"seccionado": "c", "poblacion": "f"}, "9" * 64)
        self.assertNotIn("topology_accreditation", sin["validation"])


class AdmisionPorEleccion(unittest.TestCase):
    """territory_contract 1.5.0: con `meta.historico_epoca` K se compara con el contrato de SU elección; sin él, como 1.4.1."""

    def _contrato(self, mutar=None, nombre="nac22_h2019_11.yaml"):
        import yaml
        base = yaml.safe_load((ROOT / "territorios/nac22/config/nac22_2025.yaml").read_text(encoding="utf-8"))
        cpath = che.ruta_contrato("2019-11")
        c = json.loads(cpath.read_text(encoding="utf-8"))
        cfg = che.contrato_provincia(base, c, "22", "2019-11", "s.zip", "p.csv", {"seccionado": "c" * 64, "poblacion": "f" * 64},
                                     _sha(cpath))
        cfg["io"]["project_root"]["path"] = str(ROOT)  # contrato en un temporal: no se escribe en territorios/
        if mutar:
            mutar(cfg)
        d = tempfile.TemporaryDirectory()
        self.addCleanup(d.cleanup)
        out = Path(d.name) / nombre
        out.write_text(yaml.safe_dump(cfg, allow_unicode=True), encoding="utf-8")
        from ddd_core.territory_contract import validate_production_contract
        return validate_production_contract(out, expected_territory="nac22")

    def test_k_de_la_eleccion_admite(self):
        self.assertEqual(self._contrato()["errors"], [])

    def test_k_distinto_del_de_la_eleccion_falla(self):
        def k2(cfg):
            cfg["territory_contract"]["k_districts"] = 2  # el K del catálogo 2025: ya no vale para 2019-11
        self.assertTrue(any("K catálogo/contrato" in e for e in self._contrato(k2)["errors"]))

    def test_huella_del_contrato_de_eleccion_distinta_falla(self):
        def otra(cfg):
            cfg["meta"]["historico_epoca"]["contrato_sha256"] = "0" * 64
        self.assertTrue(any("contrato_sha256" in e for e in self._contrato(otra)["errors"]))

    def test_sin_historico_compara_con_el_catalogo_maestro(self):
        def sin(cfg):
            cfg["meta"].pop("historico_epoca")  # control negativo: K=3 contra el catálogo 2025 (K=2) falla como siempre
        self.assertTrue(any("K catálogo/contrato" in e for e in self._contrato(sin)["errors"]))

    def test_rama_acotada_al_contrato_de_epoca(self):
        def anio(cfg):
            cfg["meta"]["year"] = 2025
        self.assertTrue(any("meta.year" in e for e in self._contrato(anio)["errors"]))
        # un contrato con nombre de vigente no puede usar la rama histórica
        self.assertTrue(any("run_name y fichero" in e for e in self._contrato(nombre="nac22_2025.yaml")["errors"]))

        def rn(cfg):
            cfg["meta"]["run_name"] = "nac22_2025"
        self.assertTrue(any("run_name y fichero" in e for e in self._contrato(rn)["errors"]))

    def test_eleccion_inexistente_mal_formada_o_sin_provincia(self):
        import ddd_core.territory_contract as tc
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / "configuracion/historico_epoca").mkdir(parents=True)
            cpath = root / "configuracion/historico_epoca/contrato_2019_11.json"
            cpath.write_text(json.dumps({"provincias": {"01": {"territorio": "nac01", "K": 4}}}), encoding="utf-8")
            sha = _sha(cpath)

            def juzgar(eleccion, territorio="nac22"):
                cfg = {"meta": {"run_name": f"{territorio}_h{eleccion.replace('-', '_')}", "year": eleccion[:4],
                                "historico_epoca": {"eleccion": eleccion, "contrato_sha256": sha}},
                       "_internal": {"params_path": f"/x/{territorio}_h{eleccion.replace('-', '_')}.yaml"}}
                errores: list = []
                r = tc._catalogo_eleccion(root, cfg, territorio, {"k_districts": 2}, errores)
                return r, errores
            self.assertEqual(juzgar("2019-11", "nac01")[0]["k_districts"], 4)  # control positivo
            self.assertIn("exactamente una provincia", juzgar("2019-11")[1][0])
            self.assertIn("falta el contrato", juzgar("2099-01")[1][0])
            self.assertIn("AAAA-MM", juzgar("2019-1")[1][0])

    def test_vigentes_iguales_sin_la_rama_nueva(self):
        import ddd_core.territory_contract as tc
        contratos = sorted((ROOT / "territorios").glob("*/config/*_20[0-9][0-9].yaml"))
        self.assertGreater(len(contratos), 100)
        for f in contratos:
            a = tc.validate_production_contract(f)
            with mock.patch.object(tc, "_catalogo_eleccion", lambda root, cfg, t, cat, err: cat):
                b = tc.validate_production_contract(f)
            self.assertEqual(a, b, f.name)


class Puerta(unittest.TestCase):
    C = {"eleccion": "2019-11", "fecha": "2019-11-10", "clave_espejo": "201911",
         "provincias": {"22": {"territorio": "nac22", "K": 3, "estado": "LISTA"}}}
    REC = {"status": "PASS", "ddd_unassigned_votes": 0, "source_votes": 1000}

    def test_pasa_solo_con_las_tres_condiciones(self):
        self.assertEqual(che.puerta(self.C, "22", self.REC, {"ok": True}, 3)["estado"], "PASS")
        self.assertEqual(che.puerta(self.C, "22", self.REC, {"ok": False}, 3)["estado"], "FAIL")
        self.assertEqual(che.puerta(self.C, "22", self.REC, {"ok": True}, 2)["estado"], "FAIL")
        self.assertEqual(che.puerta(self.C, "22", {**self.REC, "ddd_unassigned_votes": 2}, {"ok": True}, 3)["estado"], "FAIL")
        self.assertEqual(che.puerta(self.C, "22", {**self.REC, "status": "FAIL"}, {"ok": True}, 3)["estado"], "FAIL")
        self.assertEqual(che.puerta(self.C, "22", {"status": "PASS"}, {"ok": True}, 3)["estado"], "FAIL")  # sin source_votes


@unittest.skipUnless(importlib.util.find_spec("geopandas"), "sin geopandas")
class FlujoElectoral(unittest.TestCase):
    """M07 y M08 reales sobre un M06 sintético de 4 secciones y 2 distritos; votos del Observatorio y BOE sintéticos."""

    def test_flujo_pasa_y_un_escano_de_mas_falla(self):
        import geopandas as gpd
        import yaml
        from shapely.geometry import box
        with tempfile.TemporaryDirectory() as d:
            d = Path(d)
            root, fuentes, m06d = d / "root", d / "fuentes", d / "m06"
            secs = ["2200101001", "2200101002", "2200101003", "2200101004"]
            distr = {"2200101001": 0, "2200101002": 0, "2200101003": 1, "2200101004": 1}
            m06d.mkdir()
            g = gpd.GeoDataFrame({"CUSEC_KEY": secs, "district_id": [distr[s] for s in secs], "POP_2020": [10, 10, 10, 10],
                                  "CPRO": "22"}, geometry=[box(i, 0, i + 1, 1) for i in range(4)], crs=4326)
            g.to_file(m06d / "secciones.geojson", driver="GeoJSON")
            g.dissolve("district_id").reset_index()[["district_id", "geometry"]].to_file(m06d / "distritos.geojson", driver="GeoJSON")
            with open(m06d / "composicion.csv", "w", encoding="utf-8", newline="") as f:
                w = csv.writer(f)
                w.writerow(["CUSEC_KEY", "district_id", "section_pop"])
                w.writerows([s, distr[s], 10] for s in secs)
            espejo = {"s": ["A", "B"], "k": [], "f": [], "b": [],
                      "r": {s: [100, 50, 40, [[0, 30], [1, 10]]] for s in secs}}
            ruta = fuentes / "nazioenbehatokia/data/201911/sekzioa/22.json"
            ruta.parent.mkdir(parents=True)
            ruta.write_text(json.dumps(espejo), encoding="utf-8")
            (root / "configuracion/historico_epoca").mkdir(parents=True)
            (root / "configuracion/resultados_oficiales_congreso_2019_11.csv").write_text(
                "codigo,provincia,escanos_circunscripcion,partido,votos,escanos\n22,Huesca,2,A,125,2\n22,Huesca,2,B,42,0\n",
                encoding="utf-8")
            c = {"eleccion": "2019-11", "fecha": "2019-11-10", "clave_espejo": "201911",
                 "provincias": {"22": {"territorio": "nac22", "K": 2, "estado": "LISTA",
                                       "votos": {"ruta": "data/201911/sekzioa/22.json", "sha256": _sha(ruta)}}}}
            che.ruta_contrato("2019-11", root).write_text(json.dumps(c), encoding="utf-8")
            (root / "territorios/nac22/config").mkdir(parents=True)
            params = {"meta": {"run_name": "nac22_h2019_11"}, "io": {"project_root": {"path": str(root)}},
                      "modulos": {"modulo_06_consolidar_distritos": {
                          "out_geojson": str(m06d / "secciones.geojson"), "out_district_geojson": str(m06d / "distritos.geojson"),
                          "out_composition_csv": str(m06d / "composicion.csv"), "id_field": "CUSEC_KEY",
                          "district_field": "district_id", "pop_field": "POP_2020"}}}
            (root / "territorios/nac22/config/nac22_h2019_11.yaml").write_text(yaml.safe_dump(params), encoding="utf-8")
            salida = d / "salida"
            self.assertEqual(che.electoral("2019-11", "nac22", fuentes, salida, root), 0)
            pu = json.loads((salida / "PUERTA_nac22_2019_11.json").read_text(encoding="utf-8"))
            self.assertEqual((pu["estado"], pu["m07"], pu["perdidos"], pu["distritos_m08"]), ("PASS", "PASS", 0, 2))
            man = json.loads((salida / "2019-11/nac22/MANIFEST.json").read_text(encoding="utf-8"))
            self.assertEqual((man["election_date"], man["election_id"], man["ganadores"]),
                             ("2019-11-10", "nac22_2019-11-10", {"0": "A", "1": "A"}))
            c["provincias"]["22"]["estado"] = "BLOQUEADA_RELLENO"
            che.ruta_contrato("2019-11", root).write_text(json.dumps(c), encoding="utf-8")
            with self.assertRaises(SystemExit):
                che.electoral("2019-11", "nac22", fuentes, salida, root)
            c["provincias"]["22"]["estado"] = "LISTA"
            c["provincias"]["22"]["K"] = 3  # control negativo: K distinto del número de distritos
            che.ruta_contrato("2019-11", root).write_text(json.dumps(c), encoding="utf-8")
            self.assertEqual(che.electoral("2019-11", "nac22", fuentes, salida, root), 1)


class TablaT364b(unittest.TestCase):
    """T-389: los contratos anclan las tablas de T-364b (1.2.0) y fallan cerrado con las anteriores (sin red ni tablas en el repo)."""

    # sha256 de las tablas: literal de T-364b (README de T-364, ejecución del 16-11, 2 corridas idénticas) y de la corrida de T-389
    NUEVAS = {"2011-11": "45aa3552592a8819beab26b2a885551fbe1e8ccba0ec68ac3ccbb7621f0496a3",
              "2015-12": "7d8a67dccaca7dd87fbde6bec8b4a13abed808dd8c028a6a429e00324c7909b3",
              "2016-06": "6941ae4af6b8b58ef31dfd7e1aca56d10632b864d59b8b92c55e3838100cd9a5",
              "2019-04": "55048fe207e6ddc97653aa237f700bfa42800846848682aa59d17119f60677e7",
              "2019-11": "aef26748a31f9500efa8d9c30f9cf7b2e3a7312c41d214906a96141454acf56d"}
    VIEJAS = {"2015-12": "34c0a1dd1407288a9219d78ccdaf15a69cdb0b023b88cd123718174726df0b34",
              "2016-06": "2654f579cd23f26c882b62fade93606b76d3652c922bfe685fd413ffe7c99f82",
              "2019-04": "270061aea7f41f040657674d6b725811cf61e304e3d4a4e14100340fff06ed11",
              "2019-11": "c6eb6f8a839e2af650ee6d28cc0f69d38c05b2dd84305566f371b22684281555"}
    APARTADAS = {"2011-11": 0, "2015-12": 13, "2016-06": 2, "2019-04": 0, "2019-11": 0}  # corrida real de T-364b

    @staticmethod
    def _anterior_valido(ruta: str, eleccion: str) -> bool:
        return ruta == f"legacy/contrato_historico_epoca_{eleccion.replace('-', '_')}_v1.2.0_20261117.json"

    def test_anterior_se_valida_por_forma(self):  # control negativo: ruta mal formada o de otra elección falla
        self.assertTrue(self._anterior_valido("legacy/contrato_historico_epoca_2019_11_v1.2.0_20261117.json", "2019-11"))
        for mala in ("", "ninguna (fichero nuevo)", "configuracion/historico_epoca/contrato_2019_11.json",
                     "legacy/contrato_historico_epoca_2019_04_v1.2.0_20261117.json",
                     "legacy/contrato_historico_epoca_2019_11_v1.0.0_20261116.json"):
            self.assertFalse(self._anterior_valido(mala, "2019-11"), mala)

    def test_contratos_anclan_las_tablas_nuevas(self):
        for e in ELECCIONES:
            with self.subTest(eleccion=e):
                c = json.loads(che.ruta_contrato(e).read_text(encoding="utf-8"))
                self.assertEqual(c["poblacion"]["sha256"], self.NUEVAS[e])
                self.assertNotEqual(c["poblacion"]["sha256"], self.VIEJAS.get(e))
                self.assertIn("1.2.0", c["poblacion"]["origen"])
                self.assertEqual(c["version"], "1.3.0")  # T-399
                self.assertTrue(self._anterior_valido(c["anterior"], e), c["anterior"])  # forma; la imagen de CI no trae legacy/
                if (ROOT / ".git").exists() and (ROOT / "legacy").is_dir():  # existencia solo con árbol completo
                    self.assertTrue((ROOT / c["anterior"]).is_file())
                self.assertIn(self.NUEVAS[e], (ROOT / "docs/ESTUDIOS/T364_POBLACION_SECCION_INTERPOLADA/README.md").read_text(encoding="utf-8"))

    def test_provincias_apartadas_son_bloqueada_sin_dato(self):
        for e, n in self.APARTADAS.items():
            with self.subTest(eleccion=e):
                c = json.loads(che.ruta_contrato(e).read_text(encoding="utf-8"))
                sin_filas = sorted(k for k, p in c["provincias"].items() if p["poblacion"]["secciones"] == 0)
                self.assertEqual(len(sin_filas), n)
                self.assertTrue(all(c["provincias"][k]["estado"] == "BLOQUEADA_SIN_DATO" for k in sin_filas))
        c = json.loads(che.ruta_contrato("2016-06").read_text(encoding="utf-8"))
        self.assertEqual(sorted(k for k, p in c["provincias"].items() if p["estado"] == "BLOQUEADA_SIN_DATO"), ["36", "48"])

    def test_informe_t365b_coincide_con_los_contratos(self):
        filas = list(csv.DictReader(open(ROOT / "docs/ESTUDIOS/T365_HISTORICO_POR_EPOCA/informe_t365b.csv", encoding="utf-8", newline="")))
        for e in ELECCIONES:
            c = json.loads(che.ruta_contrato(e).read_text(encoding="utf-8"))
            ap = sorted(f["provincia"] for f in filas if f["elección"] == e and f["estado_contrato"] == "BLOQUEADA_SIN_DATO"
                        and f["apartada"] == "sí")
            self.assertEqual(ap, sorted(k for k, p in c["provincias"].items() if p["poblacion"]["secciones"] == 0), e)
            for f in filas:
                if f["elección"] == e:
                    self.assertEqual(f["estado_contrato"], c["provincias"][f["provincia"]]["estado"])

    def _tabla(self, d: Path, extra: str = "") -> Path:
        p = Path(d) / "fuentes" / "poblacion_seccion_2019-11.csv"
        p.parent.mkdir(exist_ok=True)
        p.write_text("sección,población,origen,ajustada,años_fuente\n2200101001,10,dato,no,2020\n"
                     "2200101002,7,reasignada,sin_ajuste_municipal,2019\n" + extra, encoding="utf-8")
        return p

    def _materializar(self, d: Path, tabla: Path, sha_contrato: str, estado: str = "LISTA"):
        import yaml
        root, fuentes = Path(d) / "root", tabla.parent
        (root / "territorios/nac22/config").mkdir(parents=True)
        base = root / "territorios/nac22/config/nac22_2025.yaml"
        base.write_text(yaml.safe_dump(BASE), encoding="utf-8")
        (fuentes / "seccionado_2020.zip").write_bytes(b"zip")
        c = _contrato_sintetico(sha_contrato, _sha(base), _sha(fuentes / "seccionado_2020.zip"), "d" * 64)
        c["poblacion"]["fichero"] = tabla.name
        c["provincias"]["22"]["estado"] = estado
        cpath = root / "contrato.json"
        cpath.write_text(json.dumps(c), encoding="utf-8")
        def falso(secc, cpro, cache, sha):
            dest = cache / "seccionado_normalizado.zip"
            dest.write_bytes(secc.read_bytes())
            return dest, {"normalizado_sha256": _sha(dest), "corregidas": []}
        with mock.patch.multiple(che, _secciones_seccionado=mock.Mock(return_value={"2200101001", "2200101002"}),
                                 _normalizar_seccionado=falso):
            return che.materializar("2019-11", "nac22", fuentes, root, cpath)

    def test_tabla_nueva_pasa_y_la_vieja_falla_cerrado(self):
        with tempfile.TemporaryDirectory() as d:
            nueva = self._tabla(d)
            self.assertTrue(self._materializar(d, nueva, _sha(nueva)).is_file())  # interfaz 1.2.0: reasignada + sin_ajuste_municipal
        with tempfile.TemporaryDirectory() as d:
            vieja = self._tabla(d)
            with self.assertRaises(SystemExit) as cm:  # el contrato ancla otra tabla (la anterior): falla cerrado
                self._materializar(d, vieja, "a" * 64)
            self.assertIn("FUENTE_HUELLA_DISTINTA", str(cm.exception))

    def test_provincia_apartada_sin_filas_falla_cerrado(self):
        with tempfile.TemporaryDirectory() as d:
            tabla = self._tabla(d)
            with self.assertRaises(SystemExit) as cm:
                self._materializar(d, tabla, _sha(tabla), estado="BLOQUEADA_SIN_DATO")
            self.assertIn("PROVINCIA_NO_LISTA", str(cm.exception))


if __name__ == "__main__":
    unittest.main()
