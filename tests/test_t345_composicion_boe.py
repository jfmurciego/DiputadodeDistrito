#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PROYECTO: Diputado de Distrito
COMPONENTE: prueba de la regla COMPOSICION_BOE del mapa espejo→sigla BOE (T-345)
VERSIÓN: 1.0.0 · FECHA: 2026-11-15 · ESTADO: candidato
ANTERIOR: ninguna (fichero nuevo)
FUNCIÓN: fixtures congelados (tests/fixtures/t345_composicion, sin estado vivo): la composición del rótulo del BOE de proclamadas acredita la sigla
  del espejo solo si contiene todas sus partes; rótulo ausente, ambiguo o sin las partes → no acreditada con motivo; el extractor aplica las
  correcciones de errores; la tabla versionada lleva fuente y sha256 literales del BOE y los alias nuevos validan por votos (tolerancia 0,10).
"""
import csv
import json
import os
import sys
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "herramientas"))
import alias_boe_espejo as ab  # noqa: E402

FX = ROOT / "tests/fixtures/t345_composicion"
ELEC = {"201512": "2015_12"}
PROCLAMADAS = {"201111": "BOE-A-2011-16745", "201512": "BOE-A-2015-12734"}  # ids localizados en el sumario del día de publicación


def generado(raiz=FX / "raiz"):
    man = json.loads((FX / "manifiesto.json").read_text(encoding="utf-8"))
    return ab.generar(FX / "espejo", raiz, man, ELEC)


class Composicion(unittest.TestCase):
    def test_acredita_solo_con_todas_las_partes_en_el_rotulo(self):
        ok, no = generado()
        self.assertEqual([(f[1], f[2], f[3], f[4].split(":")[0], f[12]) for f in ok if f[2] != "PSOE"],
                         [("01", "COALICIÓN «ZZ POPULAR»", "AA-BB", "COMPOSICION_BOE", "COMPOSICION_BOE")])
        f = next(f for f in ok if f[2].startswith("COALICIÓN"))
        self.assertEqual((f[7], f[8]), ("BOE-A-0000-2", "b" * 64))  # fuente y sha256 del documento de composición, no los del BOE de resultados
        self.assertIn("rótulo BOE: 7. ZZ POPULAR: ALFA ALIANZA, BETA BLOQUE (AA-BB)", f[5])
        motivos = {(r[1], r[2]): r[3] for r in no}
        self.assertIn("ninguna sigla del espejo con todas sus partes en el rótulo", motivos[("02", "COALICIÓN «ZZ POPULAR»")])
        self.assertIn("2 rótulos del BOE de proclamadas contienen la sigla", motivos[("03", "COALICIÓN «ZZ POPULAR»")])

    def test_sin_extracto_de_composicion_no_se_acredita(self):
        import shutil
        import tempfile
        with tempfile.TemporaryDirectory() as t:
            raiz = Path(t) / "raiz"
            shutil.copytree(FX / "raiz", raiz)
            shutil.rmtree(raiz / ab.COMPOS)
            ok, no = generado(raiz)
            self.assertEqual([f for f in ok if f[12] == "COMPOSICION_BOE"], [])  # sin extracto no hay acreditación por composición
            self.assertEqual(len([r for r in no if r[2].startswith("COALICIÓN")]), 3)

    def test_partes_de_la_sigla(self):
        segs, siglas = ab._rotulo("9. UNIDAD POPULAR EN ARAGÓN: IZQUIERDA UNIDA, CHUNTA ARAGONESISTA, UNIDAD POPULAR EN COMÚN (IU-CHA-UPeC)")
        self.assertEqual([ab.prueba_composicion(p, segs, siglas) for p in ("IU", "UPEC", "CHA")], ["SIGLA_EN_ROTULO"] * 3)
        segs, siglas = ab._rotulo("9. UNIDAD POPULAR: IZQUIERDA UNIDA, UNIDAD POPULAR EN COMÚN (UP-UPeC)")
        self.assertEqual(ab.prueba_composicion("IU", segs, siglas), "INICIALES_DE_PARTIDO")  # iniciales del segmento entero «IZQUIERDA UNIDA»
        self.assertIsNone(ab.prueba_composicion("PA", segs, siglas))  # «UNIDAD POPULAR…» no da «PA»: no vale un tramo suelto
        segs, siglas = ab._rotulo("11. UNIDAD POPULAR: IZQUIERDA UNIDA LOS VERDES-CONVOCATORIA POR ANDALUCÍA, UNIDAD POPULAR EN COMÚN (IULV-CA, UPeC)")
        self.assertIsNone(ab.prueba_composicion("IU", segs, siglas))  # «IU» no es «IULV-CA»: el BOE no lo dice, no se supone
        segs, siglas = ab._rotulo("3. CHUNTA ARAGONESISTA-IZQUIERDA UNIDA, LA IZQUIERDA DE ARAGÓN: LA IZQUIERDA PLURAL")
        self.assertEqual([ab.prueba_composicion(p, segs, siglas) for p in ("CHA", "IU")], ["INICIALES_DE_PARTIDO"] * 2)

    def test_extractor_aplica_correcciones_sin_red(self):
        docs = {f"https://www.boe.es/diario_boe/xml.php?id={i}": (FX / f"boe/{i}.xml").read_bytes() for i in ("BOE-A-0000-2", "BOE-A-0000-3")}
        spec = {"201512": {"proclamadas": ("BOE-A-0000-2", "2015-11-24"), "correcciones": [("BOE-A-0000-3", "2015-12-01")]}}
        with mock.patch.dict(ab.FUENTES_COMPOSICION, spec, clear=True):
            r = ab.extraer_composicion("201512", FX / "raiz", descargar=docs.__getitem__, fecha="2026-11-15")
        self.assertEqual(r["provincias"]["01"]["congreso"], ["1. PARTIDO SOCIALISTA OBRERO ESPAÑOL (PSOE)", "7. ZZ POPULAR: ALFA ALIANZA, BETA BLOQUE (AA-BB)"])
        self.assertEqual(r["provincias"]["02"]["congreso"], ["7. ZZ POPULAR: ALFA ALIANZA, BETA BLOQUE (AA-BB)"])  # corregido pese a los espacios
        self.assertEqual(r["provincias"]["03"]["junta"], "ALICANTE/ALACANT")
        self.assertEqual([x["papel"] for x in r["documentos"]], ["proclamadas", "correccion"])
        self.assertEqual(len(r["documentos"][0]["sha256"]), 64)


class TablaVersionada(unittest.TestCase):
    """La tabla viva solo se revalida con `comprobar` (estado vivo por diseño, como en T-343); los recuentos y la validación por votos
    leen copias congeladas de las filas COMPOSICION_BOE y de los no acreditados (fixtures), no `configuracion/`."""

    def leer(self, nombre):
        with (FX / nombre).open(encoding="utf-8", newline="") as fh:
            return list(csv.DictReader(fh))

    def test_comprobar_valida_fuente_y_sha256_de_la_ficha(self):
        self.assertEqual(ab.comprobar(), [])  # revalida cada fila COMPOSICION_BOE contra el sha256 de la ficha del extracto
        for k, ident in PROCLAMADAS.items():
            doc = next(d for d in ab._composicion(ROOT, k)["documentos"] if d["papel"] == "proclamadas")
            self.assertEqual(doc["boe"], ident)
            self.assertRegex(doc["sha256"], r"^[0-9a-f]{64}$")

    @unittest.skipUnless(os.environ.get("DDD_BOE_DESCARGA") == "1", "descarga de boe.es solo con DDD_BOE_DESCARGA=1")
    def test_extracto_se_reproduce_desde_boe_es(self):
        for k in ab.FUENTES_COMPOSICION:
            vivo = ab.extraer_composicion(k)
            ficha = ab._composicion(ROOT, k)
            self.assertEqual([(d["boe"], d["sha256"]) for d in vivo["documentos"]], [(d["boe"], d["sha256"]) for d in ficha["documentos"]])
            self.assertEqual(vivo["provincias"], ficha["provincias"])

    def test_alias_nuevos_y_no_acreditados_congelados(self):
        filas = self.leer("tabla_congelada_composicion.csv")
        self.assertEqual(len(filas), 35)
        self.assertEqual({(f["eleccion"], f["sigla_boe"], f["siglas_espejo"]) for f in filas}, {
            ("201111", "LA IZQUIERDA PLURAL", "CHA-IU"),
            ("201512", "COALICIÓN «PODEMOS - AHORA ALTO ARAGÓN EN COMÚN»", "PODEMOS"),
            ("201512", "COALICIÓN «UNIDAD POPULAR»", "IU-UPeC")})
        self.assertTrue(all(f["fuente_boe"] == PROCLAMADAS[f["eleccion"]] for f in filas))
        no = self.leer("no_acreditados_congelados.csv")
        self.assertEqual(len(no), 13)
        self.assertTrue(all("COMPOSICION_BOE:" in r["motivo"] for r in no))

    def test_validacion_independiente_por_votos(self):
        for f in self.leer("tabla_congelada_composicion.csv"):  # los votos validan, no prueban: defecto frente al BOE dentro de 0,10
            self.assertLessEqual(abs(float(f["validacion_votos"].split()[1])), 0.10, f)


if __name__ == "__main__":
    unittest.main()
