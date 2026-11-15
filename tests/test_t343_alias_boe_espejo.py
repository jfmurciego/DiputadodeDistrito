#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PROYECTO: Diputado de Distrito
COMPONENTE: prueba del mapa espejo→sigla BOE acreditado con ficheros y su uso en la puerta del histórico (T-343)
VERSIÓN: 1.0.0 · FECHA: 2026-11-15 · ESTADO: candidato
ANTERIOR: ninguna (fichero nuevo)
FUNCIÓN: fixtures congelados (tests/fixtures/t343_alias, sin estado vivo): el generador acredita por etiqueta y por familia y lista lo no
  acreditado; la puerta compara la sigla del BOE con la suma de las siglas del alias; sin alias, con sha256 de espejo distinto o sin
  prueba en fichero la provincia falla; el JSON lleva el aviso de coaliciones; la tabla versionada pasa `comprobar`.
"""
import csv
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "herramientas"))
import alias_boe_espejo as ab  # noqa: E402
import historico_campana as hc  # noqa: E402

FX = ROOT / "tests/fixtures/t343_alias"
ELEC = {"201911": "2019_11"}
SHA01 = "8c30c4757f72050ed6e1e51da270ec82565668eb2a882d806be88e64580526c8"  # sha256 literal de espejo/data/201911/sekzioa/01.json


def generado():
    man = json.loads((FX / "manifiesto.json").read_text(encoding="utf-8"))
    return ab.generar(FX / "espejo", FX / "raiz", man, ELEC)


class Generador(unittest.TestCase):
    def test_acredita_por_etiqueta_y_por_familia_y_lista_lo_demas(self):
        ok, no = generado()
        self.assertEqual([(f[1], f[2], f[3], f[4]) for f in ok], [
            ("01", "PSOE", "PSE-EE (PSOE)", "ETIQUETA:SIGLA_BOE_COMO_TOKEN"),
            ("01", "ZZZ-COALICION UNICA", "ZZZ-COALICI", "ETIQUETA:PREFIJO_TRUNCADO"),
            ("02", "ZZZ-COALICION UNICA", "OTRA ETIQUETA", "FAMILIA:f3"),
        ])
        self.assertEqual((ok[0][6], ok[0][12], ok[2][12]), (SHA01, "etiqueta", "familia"))  # fuerza visible
        self.assertEqual((ok[0][7], ok[0][8]), ("BOE-A-0000-0", "ab" * 32))
        self.assertIn("familia f3; semilla 01 ZZZ-COALICI", ok[2][5])  # la semilla de la familia es la etiqueta de otra provincia
        self.assertTrue(all(f[11] == "coaliciones: no comparables entre elecciones" for f in ok))
        self.assertEqual([(f[1], f[2], f[3].split(":")[0]) for f in no], [("03", "QQQ-NO PROBADO", "SIN_ETIQUETA_NI_FAMILIA")])

    def test_sha256_del_espejo_distinto_al_manifiesto_para(self):
        man = json.loads((FX / "manifiesto.json").read_text(encoding="utf-8"))
        man["ficheros"]["data/201911/sekzioa/01.json"]["sha256"] = "0" * 64
        with self.assertRaises(SystemExit) as c:
            ab.generar(FX / "espejo", FX / "raiz", man, ELEC)
        self.assertIn("ESPEJO_SHA256_DISTINTO", str(c.exception))

    def test_tabla_versionada_pasa_comprobar(self):
        self.assertEqual(ab.comprobar(), [])


class PuertaConAlias(unittest.TestCase):
    def raiz(self, t, filas=True, editar=None):
        raiz = Path(t) / "raiz"
        shutil.copytree(FX / "raiz", raiz)
        if filas:
            ok, _ = generado()
            if editar:
                editar(ok)
            with (raiz / hc.ALIAS_CSV).open("w", encoding="utf-8", newline="") as fh:
                w = csv.writer(fh, lineterminator="\n")
                w.writerow(ab.CAB)
                w.writerows(ok)
        return raiz

    def contraste(self, raiz, prov):
        return hc.contraste_boe("201911", prov, FX / f"espejo/data/201911/sekzioa/{prov}.json", raiz)

    def test_alias_aplicado_suma_las_siglas_del_espejo(self):
        with tempfile.TemporaryDirectory() as t:
            raiz = self.raiz(t)
            c = self.contraste(raiz, "01")
            self.assertEqual((c["ok"], c["sin_homologar"], c["comparados"]), (True, [], 3))
            self.assertEqual(c["diferencia"], 0.025)  # mayor defecto: BBB (400000 → 390000); PSOE 1,7 %, ZZZ 2 %
            self.assertEqual(c["alias"]["PSOE"]["siglas_espejo"], ["PSE-EE (PSOE)"])
            self.assertIn("NO son comparables entre elecciones", c["aviso"])
            self.assertTrue(self.contraste(raiz, "02")["ok"])  # alias por familia

    def test_sin_prueba_en_fichero_la_provincia_falla_y_se_lista(self):
        with tempfile.TemporaryDirectory() as t:
            c = self.contraste(self.raiz(t), "03")
            self.assertEqual((c["ok"], c["motivo"]), (False, "PARTIDOS_SIN_HOMOLOGAR"))
            self.assertEqual(c["no_acreditados"], {"QQQ-NO PROBADO": "SIN_ALIAS_ACREDITADO"})

    def test_sin_tabla_de_alias_falla_cerrado(self):
        with tempfile.TemporaryDirectory() as t:
            c = self.contraste(self.raiz(t, filas=False), "01")
            self.assertEqual((c["ok"], c["motivo"]), (False, "PARTIDOS_SIN_HOMOLOGAR"))
            self.assertEqual(set(c["no_acreditados"]), {"PSOE", "ZZZ-COALICION UNICA"})

    def test_alias_con_sha256_de_espejo_distinto_no_vale(self):
        def editar(ok):
            ok[0][6] = "f" * 64  # el alias de PSOE apunta a otra versión del espejo
        with tempfile.TemporaryDirectory() as t:
            c = self.contraste(self.raiz(t, editar=editar), "01")
            self.assertEqual((c["ok"], c["no_acreditados"]), (False, {"PSOE": "SHA256_ESPEJO_DISTINTO"}))

    def test_alias_que_apunta_a_una_sigla_ya_comparada_no_vale(self):
        def editar(ok):
            ok[0][3] = "BBB"  # alias mal escrito: PSOE ← BBB, y BBB ya está en el BOE
        with tempfile.TemporaryDirectory() as t:
            c = self.contraste(self.raiz(t, editar=editar), "01")
            self.assertFalse(c["ok"])
            self.assertEqual(c["no_acreditados"]["PSOE"], "SIGLAS_DEL_ALIAS_AUSENTES_EN_EL_ESPEJO")

    def test_alias_dudoso_con_votos_fuera_de_tolerancia_falla(self):
        with tempfile.TemporaryDirectory() as t:
            raiz = self.raiz(t)
            c = hc.contraste_boe("201911", "02", FX / "espejo/data/201911/sekzioa/02.json", raiz)
            self.assertTrue(c["ok"])  # control: la 02 pasa con el espejo congelado
            # votos fuera de tolerancia: se rebaja a mano el espejo de la 02 a 10 % del BOE en una copia con su sha256 recalculado
            esp = Path(t) / "esp02.json"
            doc = json.loads((FX / "espejo/data/201911/sekzioa/02.json").read_text(encoding="utf-8"))
            doc["r"]["0200100001"][3] = [[0, 295000], [1, 195000], [2, 2500]]
            esp.write_text(json.dumps(doc), encoding="utf-8")
            import hashlib
            with (raiz / hc.ALIAS_CSV).open(encoding="utf-8") as fh:
                fila = next(f for f in csv.reader(fh) if f[1] == "02")
            texto = (raiz / hc.ALIAS_CSV).read_text(encoding="utf-8").replace(fila[6], hashlib.sha256(esp.read_bytes()).hexdigest())
            (raiz / hc.ALIAS_CSV).write_text(texto, encoding="utf-8")
            c = hc.contraste_boe("201911", "02", esp, raiz)
            self.assertEqual((c["ok"], c["motivo"]), (False, "DEFECTO_SOBRE_TOLERANCIA"))  # ZZZ: 2.500 frente a 25.000 = 90 %

    def test_una_sigla_del_espejo_no_acredita_a_dos_del_boe(self):
        with tempfile.TemporaryDirectory() as t:
            raiz = Path(t) / "raiz"
            shutil.copytree(FX / "raiz", raiz)
            esp = Path(t) / "espejo"
            shutil.copytree(FX / "espejo", esp)
            # el BOE de la provincia 01 pasa a tener dos coaliciones de las que «ZZZ-COALICI» es prefijo de ambas (prefijo ambiguo)
            csvp = raiz / "configuracion/resultados_oficiales_congreso_2019_11.csv"
            csvp.write_text(csvp.read_text(encoding="utf-8") + "01,P01,4,ZZZ-COALICION DOS,100,0\n", encoding="utf-8")
            man = json.loads((FX / "manifiesto.json").read_text(encoding="utf-8"))
            ok, no = ab.generar(esp, raiz, man, ELEC)
            self.assertNotIn(("01", "ZZZ-COALICION UNICA"), [(f[1], f[2]) for f in ok])
            self.assertNotIn(("01", "ZZZ-COALICION DOS"), [(f[1], f[2]) for f in ok])
            motivos = {(f[1], f[2]): f[3].split(":")[0] for f in no}
            self.assertEqual(motivos[("01", "ZZZ-COALICION UNICA")], "SIGLA_ESPEJO_DUPLICADA")
            self.assertEqual(motivos[("01", "ZZZ-COALICION DOS")], "SIGLA_ESPEJO_DUPLICADA")

    def test_comprobar_detecta_sigla_de_espejo_duplicada(self):
        with tempfile.TemporaryDirectory() as t:
            raiz = Path(t)
            (raiz / "orchestracion").mkdir()
            (raiz / "configuracion").mkdir()
            shutil.copy(ROOT / ab.MANIFIESTO, raiz / ab.MANIFIESTO)
            for rel in ab.ELECCIONES.values():
                for ext in ("csv", "json"):
                    shutil.copy(ROOT / f"configuracion/resultados_oficiales_congreso_{rel}.{ext}", raiz / "configuracion")
            with (ROOT / ab.ACREDITADOS).open(encoding="utf-8") as fh:
                filas = list(csv.reader(fh))
            filas.append(list(filas[1][:2]) + ["OTRA SIGLA BOE"] + filas[1][3:])  # misma sigla del espejo, otra sigla del BOE
            with (raiz / ab.ACREDITADOS).open("w", encoding="utf-8", newline="") as fh:
                csv.writer(fh, lineterminator="\n").writerows(filas)
            self.assertTrue(any(e.startswith("SIGLA_ESPEJO_DUPLICADA") for e in ab.comprobar(raiz)))

    def test_la_puerta_lleva_el_aviso(self):
        with tempfile.TemporaryDirectory() as t:
            raiz = self.raiz(t)
            salida = Path(t) / "salida"
            (salida / "201911/nac01").mkdir(parents=True)
            (salida / "201911/nac01/reconciliacion.json").write_text(json.dumps(
                {"status": "PASS", "source_votes": 1000000, "ddd_unassigned_votes": 0}), encoding="utf-8")
            p = hc.puerta_json("nac01", "201911", "2023", 0, None, salida, None, "01", raiz, FX / "espejo/data/201911/sekzioa/01.json")
            self.assertEqual(p["estado"], "PASS")
            self.assertIn("NO son comparables entre elecciones", p["aviso"])


if __name__ == "__main__":
    unittest.main()
