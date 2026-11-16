#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""T-358: población por sección con relleno (D-126). Fixtures mínimos construidos en un directorio temporal."""
from __future__ import annotations

import hashlib
import io
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from herramientas import poblacion_seccion_historica as ph  # noqa: E402

# Secciones: A = 0100101001 (provincia 01), B = 0100101002, C = 0200101001 (provincia 02)
A, B, C, D = "0100101001", "0100101002", "0200101001", "0200101002"


def fila(sec, anio, val):
    return f"X;Y;{sec} sección;Población;{anio};{val}\r\n"


def atlas_texto():
    f = ["Municipios;Distritos;Secciones;Indicadores demográficos;Periodo;Total\r\n"]
    # A: 2015 '.', 2016 '.', 2017 100, 2018 '.', 2019 '.', 2020 '..' , 2021 '.', 2022 50   → 2015 pide 2017 (dist 2); 2019 empate 2018? ver tests
    for a, v in zip(range(2015, 2023), [".", ".", "100", ".", ".", "..", ".", "50"]):
        f.append(fila(A, a, v))
    # B: valor en todos los años 2015-2022; en 2019 con miles
    for a in range(2015, 2023):
        f.append(fila(B, a, "1.200" if a == 2019 else "10"))
    # C: sin valor en 2015 y 2016 (vacío literal) pero existe en 2019/2020; en 2018 tiene 40 y en 2020 60 (empate para 2019)
    for a, v in zip(range(2015, 2023), ['""', '""', '""', "40", ".", "60", '""', '""']):
        f.append(fila(C, a, v))
    # D: «.» en todos los años (nunca hay dato)
    for a in range(2015, 2023):
        f.append(fila(D, a, "."))
    f.append("01001 Municipio;;;Población;2019;5.000\r\n")  # fila de municipio: se ignora
    return "".join(f)


def censo_zip_bytes():
    cab = "ccaa,cpro,cmun,dist,secc,t1_1\n"
    filas = "01,01,001,01,001,300\n01,01,001,01,002,\n01,02,001,01,001,.\n"
    b = io.BytesIO()
    with zipfile.ZipFile(b, "w") as z:
        z.writestr("C2011_ccaa01_Indicadores.csv", cab + filas)
    return b.getvalue()


def sha(b):
    return hashlib.sha256(b).hexdigest()


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)
        self.atlas = self.dir / "30832.csv"
        self.atlas.write_bytes(atlas_texto().encode("utf-8-sig"))
        self.censo = self.dir / "indicadores_seccion_censal_csv.zip"
        self.censo.write_bytes(censo_zip_bytes())
        self.sumas = self.dir / "SHA256SUMS.txt"
        self.escribe_sumas(sha(self.atlas.read_bytes()), sha(self.censo.read_bytes()))

    def tearDown(self):
        self.tmp.cleanup()

    def escribe_sumas(self, sa, sc):
        self.sumas.write_text(
            "# comentario\n"
            f"{sa}  10  https://www.ine.es/jaxiT3/files/t/es/csv_bdsc/30832.csv   (nota)\n"
            f"{sc}  10  https://www.ine.es/censos2011_datos/indicadores_seccion_censal_csv.zip\n",
            encoding="utf-8")

    def calcula(self):
        return ph.calcular(ph.leer_atlas(self.atlas), ph.leer_censo(self.censo))


class Relleno(Base):
    def fila(self, tabla, el, sec):
        return next(f for f in tabla if f[0] == el and f[1] == sec)

    def test_punto_se_rellena_con_el_anio_mas_cercano(self):
        tabla, _ = self.calcula()
        # A en 2015-12: años con valor 2017 (100) y 2022 (50) → 2017
        self.assertEqual(self.fila(tabla, "2015-12", A)[2:], (100, "relleno", 2017))
        # 2019-04: «.» en 2019; cercanos con valor: 2017 (dist 2), 2022 (dist 3) → 2017
        self.assertEqual(self.fila(tabla, "2019-04", A)[2:], (100, "relleno", 2017))

    def test_empate_toma_el_anterior(self):
        tabla, _ = self.calcula()
        # C en 2019-04: 2019 es «.»; 2018 = 40 y 2020 = 60 (empate a distancia 1) → el anterior (2018)
        self.assertEqual(self.fila(tabla, "2019-04", C)[2:], (40, "relleno", 2018))
        self.assertEqual(ph.anios_por_cercania(2019, [2020, 2018, 2022]), [2018, 2020, 2022])

    def test_dato_no_se_toca_y_miles_con_punto(self):
        tabla, _ = self.calcula()
        self.assertEqual(self.fila(tabla, "2019-04", B)[2:], (1200, "dato", None))

    def test_vacio_no_se_rellena_ni_aparece(self):
        tabla, _ = self.calcula()
        # C es vacío ("") en 2015 y 2016 → inexistente: ni aparece aunque otros años tengan valor
        self.assertFalse([f for f in tabla if f[0] in ("2015-12", "2016-06") and f[1] == C])
        # «..» (A en 2020) cuenta como no publicado: A aparece en 2019-11 y se rellena (2020 no tiene valor propio)
        f = self.fila(tabla, "2019-11", A)
        self.assertEqual(f[3], "relleno")

    def test_sin_ningun_dato(self):
        tabla, informe = self.calcula()
        self.assertEqual(self.fila(tabla, "2019-04", D)[2:], (None, "sin_dato", None))
        r = next(x for x in informe if x["elección"] == "2019-04" and x["provincia"] == "02")
        self.assertEqual(r["secciones_sin_dato"], 1)

    def test_censo_2011_vacio_y_relleno_con_atlas(self):
        tabla, _ = self.calcula()
        el = [f for f in tabla if f[0] == "2011-11"]
        # 0100101001 = 300 dato; 0100101002 vacío → no aparece; 0200101001 «.» → atlas más cercano a 2011 con valor (2018: 40)
        self.assertEqual([(f[1], f[2], f[3], f[4]) for f in el], [(A, 300, "dato", None), (C, 40, "relleno", 2018)])


class Informe(Base):
    def test_porcentaje_y_marca_mayor_que_1_por_ciento(self):
        _, informe = self.calcula()
        # 2019-04, provincia 01: A rellena 100 + B dato 1200 → 100/1300 = 7,6923 % → MARCA
        r = next(x for x in informe if x["elección"] == "2019-04" and x["provincia"] == "01")
        self.assertEqual((r["secciones"], r["población"], r["población_rellena"], r["pct_relleno"], r["marca"]),
                         (2, 1300, 100, "7.6923", "MARCA"))
        # 2016-06 provincia 01: A rellena 100 (2017) + B 10 → 100/110; provincia 02 solo D sin dato → 0 y sin marca
        r2 = next(x for x in informe if x["elección"] == "2016-06" and x["provincia"] == "02")
        self.assertEqual((r2["población"], r2["pct_relleno"], r2["marca"]), (0, "0.0000", "MARCA"))  # sin_dato → MARCA

    def test_umbral_estricto(self):
        filas = [("0100100001", 9900, "dato", None), ("0100100002", 100, "relleno", 2019)]
        self.assertEqual(ph.informe_provincias("X", filas)[0]["marca"], "")  # exactamente 1 % → sin marca
        filas[1] = ("0100100002", 101, "relleno", 2019)
        self.assertEqual(ph.informe_provincias("X", filas)[0]["marca"], "MARCA")

    def test_pct_redondeo_entero(self):
        self.assertEqual(ph.pct(1, 3), "33.3333")
        self.assertEqual(ph.pct(0, 0), "0.0000")


class Fuentes(Base):
    def run_main(self, tabla="t.csv", informe="i.csv"):
        return ph.main(["--atlas", str(self.atlas), "--censo", str(self.censo), "--sumas", str(self.sumas),
                        "--tabla", str(self.dir / tabla), "--informe", str(self.dir / informe)])

    def test_falla_con_sha256_distinto(self):
        self.escribe_sumas("0" * 64, sha(self.censo.read_bytes()))
        with self.assertRaises(ph.ErrorFuente):
            ph.verificar(self.atlas, ph.NOMBRE_ATLAS, ph.leer_sumas(self.sumas))
        self.assertEqual(self.run_main(), 1)
        self.assertFalse((self.dir / "t.csv").exists())

    def test_falla_con_censo_alterado(self):
        self.censo.write_bytes(self.censo.read_bytes() + b"x")
        self.assertEqual(self.run_main(), 1)

    def test_determinista_byte_a_byte(self):
        self.assertEqual(self.run_main("t1.csv", "i1.csv"), 0)
        self.assertEqual(self.run_main("t2.csv", "i2.csv"), 0)
        for a, b in (("t1.csv", "t2.csv"), ("i1.csv", "i2.csv")):
            self.assertEqual((self.dir / a).read_bytes(), (self.dir / b).read_bytes())
        txt = (self.dir / "t1.csv").read_text(encoding="utf-8")
        self.assertNotIn("\r", txt)
        self.assertTrue(txt.startswith("elección,sección,población,origen,año_fuente_relleno\n"))
        filas = [l.split(",")[:2] for l in txt.splitlines()[1:]]
        self.assertEqual(filas, sorted(filas, key=lambda x: (x[0], x[1])))

    def test_linea_mal_formada_de_seccion_falla(self):
        base = atlas_texto()
        for mala in (f"X;Y;{A} sección;Población;2019\r\n",               # campos de menos
                     "X;Y;ABC sección;Población;2019;100\r\n",           # sección no numérica
                     f"X;Y;{A} sección;Población;20x9;100\r\n"):        # periodo no numérico
            self.atlas.write_bytes((base + mala).encode("utf-8-sig"))
            with self.assertRaises(ph.ErrorFuente):
                ph.leer_atlas(self.atlas)

    def test_marca_si_hay_sin_dato_aunque_no_haya_relleno(self):
        filas = [("0100100001", 1000, "dato", None), ("0100100002", None, "sin_dato", None)]
        r = ph.informe_provincias("X", filas)[0]
        self.assertEqual((r["secciones_sin_dato"], r["población"], r["pct_relleno"], r["marca"]), (1, 1000, "0.0000", "MARCA"))

    def test_valor_no_numerico_falla(self):
        with self.assertRaises(ph.ErrorFuente):
            ph._num("abc")


if __name__ == "__main__":
    unittest.main()
