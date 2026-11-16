#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PROYECTO: Diputado de Distrito
COMPONENTE: prueba de la regla COMPOSICION_BOE del mapa espejo→sigla BOE (T-345)
VERSIÓN: 1.1.0 · FECHA: 2026-11-15 · ESTADO: candidato
ANTERIOR: legacy/tests/test_t345_composicion_boe_v1.0.0_20261115.py
CAMBIOS: 1.1.0 (D-121): casos de la regla DECISION_PROPIETARIO (solo las 13 provincias de la decisión; cualquier otra no acredita por esa vía).
FUNCIÓN: fixtures congelados (tests/fixtures/t345_composicion, sin estado vivo): la composición del rótulo del BOE de proclamadas acredita la sigla
  del espejo solo si contiene todas sus partes; rótulo ausente, ambiguo o sin las partes → no acreditada con motivo; el extractor aplica las
  correcciones de errores; la tabla versionada lleva fuente y sha256 literales del BOE y los alias nuevos validan por votos (tolerancia 0,10).
"""
import csv
import json
import os
import shutil
import sys
import tempfile
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


D121 = ["03", "04", "11", "12", "14", "18", "21", "23", "29", "38", "41", "46", "52"]  # literal del texto de D-121 (docs/PLAN.md), no leído del fichero


class DecisionPropietario(unittest.TestCase):
    def raiz(self, t, dec):
        raiz = Path(t) / "raiz"
        shutil.copytree(FX / "raiz", raiz)
        (raiz / ab.DECISION).parent.mkdir(parents=True)
        (raiz / ab.DECISION).write_text(json.dumps(dec), encoding="utf-8")
        return raiz

    DEC = {"id": "D-121", "fecha": "2026-11-15", "fuente": "docs/PLAN.md, D-121", "sha256_texto": "c" * 64, "eleccion": "201512",
           "sigla_boe": "COALICIÓN «ZZ POPULAR»", "sigla_espejo": "AA-BB", "provincias": ["02"]}

    def test_solo_acredita_las_provincias_de_la_decision(self):
        with tempfile.TemporaryDirectory() as t:
            ok, no = generado(self.raiz(t, self.DEC))
        dec = [f for f in ok if f[12] == "DECISION_PROPIETARIO"]
        self.assertEqual([(f[1], f[3], f[4], f[7], f[8]) for f in dec],
                         [("02", "AA-BB", "DECISION_PROPIETARIO:D-121", "decisión del propietario D-121, 2026-11-15", "c" * 64)])
        self.assertEqual([f[1] for f in ok if f[12] == "COMPOSICION_BOE"], ["01"])  # la de BOE sigue aparte y con su propia fuente
        self.assertEqual([r[1] for r in no], ["03"])  # la 03 no está en la decisión: sigue sin acreditar

    def test_otra_sigla_o_eleccion_no_acredita_por_esta_via(self):
        for cambio in ({"sigla_boe": "COALICIÓN «OTRA»"}, {"eleccion": "201606"}, {"sigla_espejo": "NO-EXISTE"}, {"provincias": []}):
            with tempfile.TemporaryDirectory() as t:
                ok, no = generado(self.raiz(t, {**self.DEC, **cambio}))
            self.assertEqual([f for f in ok if f[12] == "DECISION_PROPIETARIO"], [], cambio)

    def test_tabla_versionada_tiene_exactamente_las_13_filas_de_d121(self):
        self.assertEqual(ab.comprobar(), [])
        with (ROOT / ab.ACREDITADOS).open(encoding="utf-8", newline="") as fh:
            filas = [r for r in csv.DictReader(fh) if r["fuerza"] == "DECISION_PROPIETARIO"]
        self.assertEqual(sorted(f["provincia"] for f in filas), D121)
        self.assertEqual({(f["eleccion"], f["sigla_boe"], f["siglas_espejo"], f["fuente_boe"]) for f in filas},
                         {("201512", "COALICIÓN «UNIDAD POPULAR»", "IU-UPeC", "decisión del propietario D-121, 2026-11-15")})
        self.assertEqual(ab._decision(ROOT)["provincias"], D121)

    def test_comprobar_rechaza_filas_de_decision_fuera_de_la_lista(self):
        with tempfile.TemporaryDirectory() as t:
            raiz = Path(t)
            for rel in ("orchestracion/fuente_nazioenbehatokia.json", ab.DECISION, ab.ACREDITADOS):
                (raiz / rel).parent.mkdir(parents=True, exist_ok=True)
                shutil.copy(ROOT / rel, raiz / rel)
            for rel in list((ROOT / "configuracion").glob("resultados_oficiales_congreso_*")) + list((ROOT / ab.COMPOS).glob("*.json")):
                dest = raiz / rel.relative_to(ROOT)
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy(rel, dest)
            self.assertEqual(ab.comprobar(raiz), [])
            dec = json.loads((raiz / ab.DECISION).read_text(encoding="utf-8"))
            dec["provincias"] = dec["provincias"][:-1]  # una fila queda fuera de la decisión
            (raiz / ab.DECISION).write_text(json.dumps(dec), encoding="utf-8")
            err = ab.comprobar(raiz)
            self.assertTrue(any(e.startswith("DECISION_FUERA_DE_ALCANCE") for e in err) and any(e.startswith("DECISION_FILAS") for e in err), err)


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

    def test_alias_nuevos_y_no_acreditados_congelados_sin_decision(self):
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
