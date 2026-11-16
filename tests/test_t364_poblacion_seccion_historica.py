#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""T-364 (D-128): población por sección con interpolación y ajuste municipal. Fixtures mínimos con sha256 propio.

Los valores esperados están calculados a mano (no con el código): ver el comentario de cada caso."""
from __future__ import annotations

import hashlib
import io
import struct
import sys
import tempfile
import unittest
import zipfile
from unittest import mock
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from herramientas import poblacion_seccion_historica as ph  # noqa: E402

S1, S2, S3 = "0100100001", "0100100002", "0100100003"   # municipio 01001
S4, S5 = "0200200001", "0200200002"                      # municipio 02002
S6 = "0300300001"                                        # municipio 03003
S8, S9 = "0500500001", "0500500002"                      # municipio 05005: S8 NO LISTADA en el Atlas 2016, 2019 y 2020
S10 = "0600600001"                                       # solo en el seccionado 2016, sin ningún dato en el Atlas
S11, S12 = "0700700001", "0700700002"                    # municipio 07007: S12 vacía «""» en el Atlas 2016-2017 y SÍ está en el seccionado
S13 = "0800800001"                                       # vacía «""» en el Atlas y NO está en ningún seccionado: inexistente
S7 = "0400400001"                                        # municipio 04004: miles con punto, sin estimadas


def fila(sec, anio, val):
    return f"X;Y;{sec} sección;Población;{anio};{val}\r\n"


def serie(sec, valores):
    """valores: dict año → valor; años 2015-2022 que falten = valor del último dado."""
    return "".join(fila(sec, a, valores[a]) for a in range(2015, 2023))


def atlas_texto():
    f = ["Municipios;Distritos;Secciones;Indicadores demográficos;Periodo;Total\r\n"]
    f.append(serie(S1, {a: "500" for a in range(2015, 2023)}))
    # S2: 2016 y 2017 «.»; 2016 → interpola 2015 (100) y 2018 (200) en 1/3: 133
    f.append(serie(S2, {2015: "100", 2016: ".", 2017: ".", **{a: "200" for a in range(2018, 2023)}}))
    # S3: 2016 «.»; 2015 = 200, 2018 = 500 → 300
    f.append(serie(S3, {2015: "200", 2016: ".", 2017: "..", **{a: "500" for a in range(2018, 2023)}}))
    # S4: dato 800 siempre
    f.append(serie(S4, {a: "800" for a in range(2015, 2023)}))
    # S5: 2016 «.» con 50 (2015) y 70 (2017) → 60; desde 2017 = 70
    f.append(serie(S5, {2015: "50", 2016: ".", **{a: "70" for a in range(2017, 2023)}}))
    # S6: 2015 y 2016 «.»; solo hay dato después (2017: 90) → más cercana (2017)
    f.append(serie(S6, {2015: ".", 2016: ".", **{a: "90" for a in range(2017, 2023)}}))
    # S8: el Atlas solo la lista en 2015 (100) y 2018 (200): en 2016, 2019 y 2020 no figura (ni «.» ni valor)
    f.append(fila(S8, 2015, "100") + fila(S8, 2018, "200"))
    f.append(serie(S9, {a: "400" for a in range(2015, 2023)}))
    f.append(serie(S11, {a: "300" for a in range(2015, 2023)}))
    f.append(serie(S12, {2015: "100", 2016: '""', 2017: '""', **{a: "200" for a in range(2018, 2023)}}))
    f.append(serie(S13, {a: '""' for a in range(2015, 2023)}))
    f.append(serie(S7, {a: "1.200" for a in range(2015, 2023)}))  # «1.200» = 1200 (separador de miles)
    f.append("01001 Municipio;;;Población;2019;5.000\r\n")  # fila de municipio: se ignora
    return "".join(f)


def censo_zip_bytes():
    cab = "ccaa,cpro,cmun,dist,secc,t1_1\n"
    filas = "01,01,001,00,001,300\n01,01,001,00,002,\n01,03,003,00,001,.\n"
    b = io.BytesIO()
    with zipfile.ZipFile(b, "w") as z:
        z.writestr("C2011_ccaa01_Indicadores.csv", cab + filas)
    return b.getvalue()


def oficial_texto(extra=""):
    oficial = {  # municipio → {año: oficial}; solo importan 2015, 2016, 2019 y 2020
        "01001 Uno": {2015: 800, 2016: 1500, 2019: 1200, 2020: 1200},
        "02002 Dos": {2015: 850, 2016: 700, 2019: 870, 2020: 870},
        "03003 Tres": {2015: 90, 2016: 90, 2019: 90, 2020: 90},
        "05005 Cinco": {2015: 500, 2016: 1000, 2019: 650, 2020: 600},
        "06006 Seis": {2015: 1, 2016: 1, 2019: 1, 2020: 1},
        "07007 Siete": {2015: 400, 2016: 700, 2019: 500, 2020: 500},
    }
    f = ["Municipios;Sexo;Periodo;Total\r\n"]
    for mun, d in oficial.items():
        for anio in (2025, 2020, 2019, 2016, 2015, 2014):
            v = d.get(anio, 1)
            f.append(f"{mun};Total;{anio};{v:,}\r\n".replace(",", "."))
            f.append(f"{mun};Hombres;{anio};7\r\n")
    return "".join(f) + extra


def sha(b):
    return hashlib.sha256(b).hexdigest()


def dbf_zip_bytes(codigos, campo="CUSEC", ancho=10):
    """ZIP con un .dbf mínimo (cabecera, un campo de texto, registros con byte de borrado)."""
    desc = campo.encode().ljust(11, b"\0") + b"C" + b"\0" * 4 + bytes([ancho]) + b"\0" * 15
    rl = 1 + ancho
    cab = bytearray(32)
    cab[0] = 3
    cab[4:12] = struct.pack("<IHH", len(codigos), 32 + len(desc) + 1, rl)
    cuerpo = b"".join(b" " + c.encode().ljust(ancho) for c in sorted(codigos))
    b = io.BytesIO()
    with zipfile.ZipFile(b, "w") as z:
        z.writestr("secciones.dbf", bytes(cab) + desc + b"\r" + cuerpo)
    return b.getvalue()


SECC = {2012: {S1, S2, S6},  # = secciones que lista el Censo 2011 (S2 vacía: existe en la fuente, no se estima)
        **{a: {S1, S2, S3, S4, S5, S6, S7, S8, S9, S11, S12} for a in (2015, 2016, 2019, 2020)}}
SECC[2016] = SECC[2016] | {S10}


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)
        self.atlas = self.dir / "30832.csv"
        self.atlas.write_bytes(atlas_texto().encode("utf-8-sig"))
        self.censo = self.dir / "indicadores_seccion_censal_csv.zip"
        self.censo.write_bytes(censo_zip_bytes())
        self.oficial = self.dir / "29005.csv"
        self.oficial.write_bytes(oficial_texto().encode("utf-8-sig"))
        self.secc = self.dir / "secc"
        self.secc.mkdir()
        for anio, cods in SECC.items():
            (self.secc / f"seccionado_{anio}.zip").write_bytes(dbf_zip_bytes(cods))
        self.sumas = self.dir / "SHA256SUMS.txt"
        self.escribe_sumas()
        p = mock.patch.object(ph, "TOPE_DESCUADRE_PCT", 50)  # fixtures de 9 secciones: el tope real (1 %) se prueba aparte
        p.start()
        self.addCleanup(p.stop)

    def tearDown(self):
        self.tmp.cleanup()

    def escribe_sumas(self, sa=None, sc=None, so=None):
        self.sumas.write_text(
            "# comentario\n"
            f"{sa or sha(self.atlas.read_bytes())}  10  https://www.ine.es/jaxiT3/files/t/es/csv_bdsc/30832.csv   (nota)\n"
            f"{sc or sha(self.censo.read_bytes())}  10  https://www.ine.es/censos2011_datos/indicadores_seccion_censal_csv.zip\n"
            f"{so or sha(self.oficial.read_bytes())}  10  https://www.ine.es/jaxiT3/files/t/es/csv_bdsc/29005.csv\n"
            + "".join(f"{sha(p.read_bytes())}  10  https://www.ine.es/prodyser/cartografia/{p.name}\n"
                      for p in sorted(self.secc.glob("seccionado_*.zip"))),
            encoding="utf-8")

    def calcula(self):
        of = ph.leer_oficial(self.oficial, {2015, 2016, 2019, 2020})
        secc = {a: ph.leer_seccionado(self.secc / f"seccionado_{a}.zip") for a in SECC}
        return ph.calcular(ph.leer_atlas(self.atlas), ph.leer_censo(self.censo), of, secc)

    def run_main(self, salida="out", *extra):
        return ph.main(["--atlas", str(self.atlas), "--censo", str(self.censo), "--oficial", str(self.oficial),
                        "--seccionados", str(self.secc), "--sumas", str(self.sumas), "--salida", str(self.dir / salida), *extra])


def buscar(filas, sec):
    return next(f for f in filas if f[0] == sec)


class Interpolacion(Base):
    def test_interpola_entre_anterior_y_siguiente_de_la_misma_seccion(self):
        tablas, _, _ = self.calcula()
        # S2 en 2016: (2015=100, 2018=200) → 100 + 100·1/3 = 133,33 → 133; sin ajuste posible (ver S3: sí ajusta el municipio)
        antes = ph.poblacion_eleccion(ph.leer_atlas(self.atlas)[2016], 2016, ph.leer_atlas(self.atlas))
        self.assertEqual(buscar(antes, S2)[1:], (133, "interpolada", "no", "2015-2018"))
        self.assertEqual(buscar(antes, S3)[1:], (300, "interpolada", "no", "2015-2018"))  # «..» en 2017 = no publicado

    def test_redondeo_half_up(self):
        atlas = {2015: {S1: 10}, 2016: {S1: "."}, 2017: {S1: 11}}
        self.assertEqual(ph.estimar(S1, 2016, atlas), (11, "interpolada", "2015-2017"))  # 10,5 → 11

    def test_un_solo_lado_es_mas_cercana_no_interpolada(self):
        atlas = ph.leer_atlas(self.atlas)
        # S6 en 2015: sin dato antes; el más cercano con dato es 2017 (90). Control negativo: no es «interpolada».
        self.assertEqual(ph.estimar(S6, 2015, atlas), (90, "mas_cercana", "2017"))
        # solo lado anterior: S5 en 2022 simulado «.» → último dato 2021 (70)
        atlas[2022][S5] = "."
        self.assertEqual(ph.estimar(S5, 2022, atlas), (70, "mas_cercana", "2021"))

    def test_dato_no_se_toca_y_miles_con_punto(self):
        tablas, _, _ = self.calcula()
        self.assertEqual(buscar(tablas["2019-04"], S7)[1:], (1200, "dato", "no", "2019"))

    def test_censo_2011_vacio_y_estimado_con_atlas(self):
        tablas, _, _ = self.calcula()
        # S1 = 300 (dato del censo); S2 vacío en el censo → no aparece; S6 «.» en el censo → Atlas (solo lado posterior: 2017 = 90)
        self.assertEqual([(f[0], f[1], f[2]) for f in tablas["2011-11"]], [(S1, 300, "dato"), (S6, 90, "mas_cercana")])

    def test_sin_ningun_dato(self):
        atlas = {2015: {S1: "."}, 2016: {S1: "."}}
        self.assertEqual(ph.estimar(S1, 2016, atlas), (None, "sin_dato", ""))

    def test_vacio_no_aparece_y_punto_punto_es_no_publicado(self):
        tablas, _, _ = self.calcula()
        self.assertNotIn(S2, [f[0] for f in tablas["2011-11"]])  # vacío en el censo: inexistente, no se estima
        self.assertEqual(buscar(tablas["2011-11"], S6)[1:], (90, "mas_cercana", "no", "2017"))  # «.» del censo


class NoListada(Base):
    def test_seccion_del_seccionado_que_el_atlas_no_lista_se_estima_y_ajusta(self):
        tablas, _, _ = self.calcula()
        # S8 existe en el seccionado y el Atlas no la lista en 2016/2019/2020 (solo 2015 = 100 y 2018 = 200).
        # 2015-12: listada, dato. 2016-06: interpola 2015-2018 → 133; municipio 05005 oficial 1000 − S9 400 = 600 → ajustada a 600.
        self.assertEqual(buscar(tablas["2015-12"], S8)[1:], (100, "dato", "no", "2015"))
        self.assertEqual(buscar(tablas["2016-06"], S8)[1:], (600, "no_listada", "sí", "2015-2018"))
        # 2019-04: solo hay dato anterior (2018 = 200) → más cercana; oficial 650 − 400 = 250
        self.assertEqual(buscar(tablas["2019-04"], S8)[1:], (250, "no_listada", "sí", "2018"))
        # 2019-11 (Atlas 2020): 200 = residuo 600 − 400 → cuadra, sin marca de ajuste
        self.assertEqual(buscar(tablas["2019-11"], S8)[1:], (200, "no_listada", "no", "2018"))
        # 2011-11: seccionado 2012 = lo que lista el Censo: S8 no entra
        self.assertNotIn(S8, [f[0] for f in tablas["2011-11"]])

    def test_vacio_con_seccion_en_el_seccionado_se_estima_y_sin_ella_no_aparece(self):
        tablas, _, _ = self.calcula()
        # S12: «""» en el Atlas 2016 pero existe en el seccionado 2016 → no_listada; 2015-2018: 100→200 = 133; oficial 700 − S11 300 = 400
        self.assertEqual(buscar(tablas["2016-06"], S12)[1:], (400, "no_listada", "sí", "2015-2018"))
        self.assertEqual(buscar(tablas["2015-12"], S12)[1:], (100, "dato", "no", "2015"))
        # control negativo: S13 vacía en el Atlas y sin sección en el seccionado = inexistente, no aparece en ninguna elección
        for el, filas in tablas.items():
            self.assertNotIn(S13, [f[0] for f in filas])

    def test_informe_cuenta_secciones_sin_seccionado(self):
        atlas = {2016: {S1: 5, S2: 5, S4: 5}}
        filas = ph.poblacion_eleccion(atlas[2016], 2016, atlas, {S1, S2})  # S4 (provincia 02) no está en el seccionado: se mantiene
        self.assertEqual(len(filas), 3)
        r = {x["provincia"]: x for x in ph.informe_provincias("X", filas, (), {S1, S2})}
        self.assertEqual((r["01"]["secciones_sin_seccionado"], r["02"]["secciones_sin_seccionado"]), (0, 1))
        self.assertEqual(ph.informe_provincias("X", filas)[0]["secciones_sin_seccionado"], "")  # sin seccionado: no aplica

    def test_cuenta_en_el_porcentaje_estimado(self):
        _, inf, _ = self.calcula()
        r = next(x for x in inf if x["elección"] == "2016-06" and x["provincia"] == "05")
        # provincia 05: S8 600 (no listada, ajustada) + S9 400 → 1000; estimada 600 → 60 %
        self.assertEqual((r["secciones"], r["secciones_no_listadas"], r["población"], r["población_estimada"], r["pct_estimada"], r["marca"]),
                         (2, 1, 1000, 600, "60.0000", "MARCA"))

    def test_sin_dato_en_ningun_anio_no_es_cero_y_avisa(self):
        tablas, _, mun = self.calcula()
        # S10 (solo en el seccionado 2016, sin ninguna fila del Atlas): sin_dato, nunca población 0
        self.assertEqual(buscar(tablas["2016-06"], S10)[1:], (None, "sin_dato", "no", ""))
        m = next(x for x in mun if x["elección"] == "2016-06" and x["municipio"] == "06006")
        self.assertEqual(m["estado"], "aviso_sin_dato")  # municipio sin estimadas pero con sin_dato: no se silencia

    def test_sin_dato_fuerza_estricto(self):
        filas = ph.poblacion_eleccion({S1: 500}, 2016, {2016: {S1: 500}}, {S1, S10})
        self.assertEqual(buscar(filas, S10)[1:3], (None, "sin_dato"))
        _, inf = ph.ajustar("X", filas, {"01001": 500, "06006": 1})
        self.assertEqual([m["estado"] for m in inf], ["aviso_sin_dato"])

    def test_falla_cerrado(self):
        atlas = {2016: {S1: 5, S2: 5}}
        with mock.patch.object(ph, "TOPE_DESCUADRE_PCT", 1):
            # seccionado con una sección más que la fuente (1 de 2 = 50 % > 1 %)
            with self.assertRaises(ph.ErrorFuente):
                ph.poblacion_eleccion(atlas[2016], 2016, atlas, {S1, S2, S3})
            # fuente con una sección que el seccionado no tiene
            with self.assertRaises(ph.ErrorFuente):
                ph.poblacion_eleccion(atlas[2016], 2016, atlas, {S1})
            # control: casan exactamente → sin error
            self.assertEqual(len(ph.poblacion_eleccion(atlas[2016], 2016, atlas, {S1, S2})), 2)
        with self.assertRaises(ph.ErrorFuente):  # falta el seccionado de una elección
            ph.calcular(ph.leer_atlas(self.atlas), ph.leer_censo(self.censo),
                        ph.leer_oficial(self.oficial, {2015, 2016, 2019, 2020}), {2015: SECC[2015]})

    def test_seccionado_ilegible(self):
        p = self.dir / "x.zip"
        for contenido in (b"basura", dbf_zip_bytes({S1}, campo="OTRO"), dbf_zip_bytes({S1}, ancho=9), dbf_zip_bytes({"ABC"}, ancho=10)):
            p.write_bytes(contenido)
            with self.assertRaises((ph.ErrorFuente, zipfile.BadZipFile)):
                ph.leer_seccionado(p)
        b = io.BytesIO()
        with zipfile.ZipFile(b, "w") as z:
            z.writestr("a.txt", "x")
        p.write_bytes(b.getvalue())
        with self.assertRaises(ph.ErrorFuente):
            ph.leer_seccionado(p)

    def test_seccionado_alterado_falla_con_sha256(self):
        (self.secc / "seccionado_2016.zip").write_bytes(dbf_zip_bytes({S1}))
        self.assertEqual(self.run_main(), 1)
        self.assertFalse((self.dir / "out").exists() and any((self.dir / "out").iterdir()))


class Ajuste(Base):
    def test_reparto_exacto_y_solo_estimadas(self):
        tablas, _, mun = self.calcula()
        t = tablas["2016-06"]
        # Municipio 01001, oficial 1500; dato S1 = 500 → residuo 1000 para S2 (133) y S3 (300), suma 433.
        # 133·1000/433 = 307,16 (resto 69) ; 300·1000/433 = 692,84 (resto 364): base 307+692 = 999 → el resto mayor (S3) recibe +1.
        self.assertEqual(buscar(t, S1)[1:], (500, "dato", "no", "2016"))
        self.assertEqual(buscar(t, S2)[1:], (307, "interpolada", "sí", "2015-2018"))
        self.assertEqual(buscar(t, S3)[1:], (693, "interpolada", "sí", "2015-2018"))
        m = next(x for x in mun if x["elección"] == "2016-06" and x["municipio"] == "01001")
        self.assertEqual((m["estado"], m["oficial"], m["publicada"], m["estimada_antes"], m["estimada_despues"], m["desajuste_pct"]),
                         ("ajustado", 1500, 500, 433, 1000, "37.8000"))  # 567/1500 = 37,8 %

    def test_reparto_empate_desempata_por_orden(self):
        self.assertEqual(ph.reparto([1, 1], 3), [2, 1])  # restos iguales (1 y 1): el primero
        self.assertEqual(sum(ph.reparto([133, 300, 7], 1000)), 1000)

    def test_municipio_que_cuadra_no_marca_ajustada(self):
        tablas, _, mun = self.calcula()
        # S6 en 2015: estimada 90 (2017), oficial 03003 = 90 → residuo 90 = estimada: «cuadra», ajustada = no
        self.assertEqual(buscar(tablas["2015-12"], S6)[1:], (90, "mas_cercana", "no", "2017"))
        m = next(x for x in mun if x["elección"] == "2015-12" and x["municipio"] == "03003")
        self.assertEqual(m["estado"], "cuadra")

    def test_residuo_negativo_avisa_y_no_ajusta(self):
        tablas, _, mun = self.calcula()
        # Municipio 02002 en 2016: oficial 700 < publicada 800 (S4) → residuo −100: aviso, S5 queda con la estimación (60)
        self.assertEqual(buscar(tablas["2016-06"], S5)[1:], (60, "interpolada", "no", "2015-2017"))
        m = next(x for x in mun if x["elección"] == "2016-06" and x["municipio"] == "02002")
        self.assertEqual(m["estado"], "aviso_residuo_no_positivo")

    def test_residuo_cero_con_estimadas_avisa(self):
        filas = [("0100100001", 800, "dato", "no", "2016"), ("0100100002", 60, "interpolada", "no", "2015-2017")]
        nuevas, inf = ph.ajustar("X", filas, {"01001": 800})  # residuo 0: no se anulan secciones
        self.assertEqual(nuevas, filas)
        self.assertEqual(inf[0]["estado"], "aviso_residuo_no_positivo")

    def test_municipio_ausente_en_oficial_o_con_sin_dato_avisa(self):
        filas = [("0100100001", 800, "dato", "no", "2016"), ("0100100002", 60, "interpolada", "no", "2015-2017")]
        self.assertEqual(ph.ajustar("X", filas, {})[1][0]["estado"], "aviso_sin_oficial")
        filas.append(("0100100003", None, "sin_dato", "no", ""))
        nuevas, inf = ph.ajustar("X", filas, {"01001": 2000})
        self.assertEqual((nuevas, inf[0]["estado"]), (filas, "aviso_sin_dato"))

    def test_2011_no_se_ajusta(self):
        _, _, mun = self.calcula()
        self.assertEqual([m["estado"] for m in mun if m["elección"] == "2011-11"], ["sin_ajuste_fuente"])

    def test_dato_nunca_cambia(self):
        tablas, _, _ = self.calcula()
        for el, filas in tablas.items():
            for f in filas:
                if f[2] == "dato":
                    self.assertEqual(f[3], "no")


class Informe(Base):
    def test_informe_sobre_poblacion_estimada(self):
        _, inf, _ = self.calcula()
        r = next(x for x in inf if x["elección"] == "2016-06" and x["provincia"] == "01")
        # provincia 01 en 2016: S1 500 + S2 307 + S3 693 = 1500; estimada 1000 → 66,6667 %; 1 municipio ajustado; desajuste 37,8 %
        self.assertEqual((r["secciones"], r["secciones_interpoladas"], r["secciones_mas_cercanas"], r["secciones_ajustadas"],
                          r["población"], r["población_estimada"], r["pct_estimada"], r["municipios_ajustados"],
                          r["desajuste_medio_pct"], r["marca"]),
                         (3, 2, 0, 2, 1500, 1000, "66.6667", 1, "37.8000", "MARCA"))
        r2 = next(x for x in inf if x["elección"] == "2016-06" and x["provincia"] == "02")
        self.assertEqual((r2["municipios_aviso"], r2["municipios_ajustados"], r2["desajuste_medio_pct"]), (1, 0, "0.0000"))

    def test_umbral_estricto_sobre_estimada(self):
        filas = [("0100100001", 9900, "dato", "no", "2016"), ("0100100002", 100, "mas_cercana", "no", "2015")]
        self.assertEqual(ph.informe_provincias("X", filas)[0]["marca"], "")  # exactamente 1 % → sin marca
        filas[1] = ("0100100002", 101, "mas_cercana", "no", "2015")
        self.assertEqual(ph.informe_provincias("X", filas)[0]["marca"], "MARCA")

    def test_marca_si_hay_sin_dato(self):
        filas = [("0100100001", 1000, "dato", "no", "2016"), ("0100100002", None, "sin_dato", "no", "")]
        r = ph.informe_provincias("X", filas)[0]
        self.assertEqual((r["secciones_sin_dato"], r["pct_estimada"], r["marca"]), (1, "0.0000", "MARCA"))

    def test_pct_redondeo_entero(self):
        self.assertEqual(ph.pct(1, 3), "33.3333")
        self.assertEqual(ph.pct(0, 0), "0.0000")


class Fuentes(Base):
    def test_falla_con_sha256_distinto(self):
        for cual in ("sa", "sc", "so"):
            self.escribe_sumas(**{cual: "0" * 64})
            self.assertEqual(self.run_main(), 1, cual)
            self.assertFalse((self.dir / "out" / "informe_provincias.csv").exists(), cual)

    def test_falla_con_oficial_alterado(self):
        self.oficial.write_bytes(self.oficial.read_bytes() + b"x")
        self.assertEqual(self.run_main(), 1)

    def test_falla_sin_sha_en_sumas(self):
        self.sumas.write_text("# vacío\n", encoding="utf-8")
        with self.assertRaises(ph.ErrorFuente):
            ph.verificar(self.oficial, ph.NOMBRE_OFICIAL, ph.leer_sumas(self.sumas))

    def test_oficial_mal_formado_falla(self):
        for texto in ("Otra;Cabecera\r\n",
                      oficial_texto("01001 Uno;Total;2016;1.000\r\n"),   # municipio repetido
                      oficial_texto("04004 Cuatro;Total;2016;abc\r\n"),  # no numérico
                      oficial_texto("04004 Cuatro;Total;2016\r\n")):     # campos de menos
            self.oficial.write_bytes(texto.encode("utf-8-sig"))
            with self.assertRaises(ph.ErrorFuente):
                ph.leer_oficial(self.oficial, {2016})

    def test_oficial_municipio_inexistente_se_omite(self):
        self.oficial.write_bytes(oficial_texto('04004 Cuatro;Total;2016;""\r\n').encode("utf-8-sig"))
        self.assertNotIn("04004", ph.leer_oficial(self.oficial, {2016})[2016])
        self.assertIn("01001", ph.leer_oficial(self.oficial, {2016})[2016])

    def test_falta_oficial_de_un_anio(self):
        with self.assertRaises(ph.ErrorFuente):
            ph.calcular(ph.leer_atlas(self.atlas), ph.leer_censo(self.censo), {2015: {}})

    def test_linea_mal_formada_de_seccion_falla(self):
        base = atlas_texto()
        for mala in (f"X;Y;{S1} sección;Población;2019\r\n", "X;Y;ABC sección;Población;2019;100\r\n",
                     f"X;Y;{S1} sección;Población;20x9;100\r\n"):
            self.atlas.write_bytes((base + mala).encode("utf-8-sig"))
            with self.assertRaises(ph.ErrorFuente):
                ph.leer_atlas(self.atlas)

    def test_valor_no_numerico_falla(self):
        with self.assertRaises(ph.ErrorFuente):
            ph._num("abc")


class Salida(Base):
    def test_interfaz_estable_y_determinista_byte_a_byte(self):
        self.assertEqual(self.run_main("a"), 0)
        self.assertEqual(self.run_main("b"), 0)
        nombres = sorted(p.name for p in (self.dir / "a").iterdir())
        self.assertEqual(nombres, ["informe_municipios.csv", "informe_provincias.csv"]
                         + [f"poblacion_seccion_{e}.csv" for e in sorted(ph.ELECCIONES)])
        for n in nombres:
            self.assertEqual((self.dir / "a" / n).read_bytes(), (self.dir / "b" / n).read_bytes())
        txt = (self.dir / "a" / "poblacion_seccion_2016-06.csv").read_text(encoding="utf-8")
        self.assertNotIn("\r", txt)
        self.assertEqual(txt.splitlines()[0], "sección,población,origen,ajustada,años_fuente")
        self.assertIn(f"{S2},307,interpolada,sí,2015-2018", txt.splitlines())
        self.assertIn(f"{S1},500,dato,no,2016", txt.splitlines())
        secciones = [l.split(",")[0] for l in txt.splitlines()[1:]]
        self.assertEqual(secciones, sorted(secciones))

    def test_estricto_sale_con_2_si_hay_avisos(self):
        self.assertEqual(self.run_main("c"), 0)   # avisos (02002) sin --estricto: no falla
        self.assertEqual(self.run_main("d", "--estricto"), 2)
        # control: con --estricto y avisos no hay tablas por elección (el consumidor no puede usarlas); sí los informes
        self.assertEqual(sorted(p.name for p in (self.dir / "d").iterdir()), ["informe_municipios.csv", "informe_provincias.csv"])
        self.assertTrue(any((self.dir / "c").glob("poblacion_seccion_*.csv")))


if __name__ == "__main__":
    unittest.main()
