#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PROYECTO: Diputado de Distrito
COMPONENTE: publicador de la doble vuelta con los aut (T-427), con el montaje de test_t419 (R2 simulado)
VERSIÓN: 1.0.0 · FECHA: 2026-11-20 · ESTADO: candidato
ANTERIOR: ninguna (fichero nuevo)
FUNCIÓN: con `autonomicas` en el fijado, los aut OK llegan al sitio con su sha256, sin geometría y con `clave_visor`; los declarados sin doble vuelta van a
  `sin_doble_vuelta` con su motivo; un estado no declarado, sin motivo, un informe de otro P75 o ningún OK rechazan todo; sin `autonomicas`, nada cambia.
"""
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tests"))
sys.path.insert(0, str(ROOT / "herramientas"))
import publicar_doble_vuelta as pdv  # noqa: E402
from test_t419_publicar_doble_vuelta import Montaje, detalle, resultados, sha, zip_de, zips_buenos  # noqa: E402

# id del visor de aut01 desde la tabla maestra (fuente independiente del publicador; T-220: sin literales viejos)
LEG = next(l.strip().split(",")[-1] for l in (ROOT / "configuracion/notacion_territorial.csv").read_text(encoding="utf-8").splitlines()
           if l.startswith("AUT01,"))
CLAVE = f"{LEG}/3001/ddd-doble-vuelta-3001-p75-88-1.zip"
ZA = zip_de(resultados(ids=(0, 1, 2)), detalle(ids=(0, 1, 2)))


def con_aut(filas=None, eleccion="autonomicas", run="88-1", pin_run="88-1", motivo=True):
    def mod(m):
        m.objetos[CLAVE] = ZA
        fs = filas if filas is not None else [
            {"territorio": "aut01", "run": "3001", "estado": "OK", "eleccion": "2026-05", "sin_casar_pct": 0.0, "aproximado_en_distrito": False,
             "nivel": "seccion", "sha256_salida": sha(ZA), "clave_r2": CLAVE},
            {"territorio": "aut03", "run": "3003", "estado": "SIN_VOTOS_AUTONOMICOS", "motivo": "sin votos" if motivo else None},
            {"territorio": "aut18", "run": "3018", "estado": "NO_APLICA", "motivo": "Ceuta no elige parlamento autonómico"}]
        inf = (json.dumps({"schema": "ddd.p75-informe/1.0", "eleccion": eleccion, "run_p75": run,
                           "entradas": {"bloques": {"sha256": "c" * 64}, "alias": {"sha256": "d" * 64}},
                           "territorios": fs, "ok": sum(f["estado"] == "OK" for f in fs), "total": len(fs)}) + "\n").encode()
        m.objetos["doble_vuelta/autonomicas/88-1/INFORME.json"] = inf
        m.pin["autonomicas"] = {"run_p75": pin_run, "informe_clave": "doble_vuelta/autonomicas/88-1/INFORME.json", "informe_sha256": sha(inf)}
        m.escribir_pin()
    return mod


class PublicarAut(unittest.TestCase):
    def setUp(self):
        p = mock.patch.object(pdv, "ESPERADOS", 2)
        p.start()
        self.addCleanup(p.stop)

    def correr(self, mod=None):
        with tempfile.TemporaryDirectory() as t, tempfile.TemporaryDirectory() as d:
            m = Montaje(Path(t), zips_buenos())
            if mod:
                mod(m)
            try:
                ind = pdv.publicar(Path(t), Path(d), m.cp, "b", "2026-11-20", sitio=Path(t) / "sitio")
            except pdv.DobleVueltaError as exc:
                return None, str(exc), {}
            return ind, "", {str(p.relative_to(d)): p.read_bytes() for p in Path(d).rglob("*") if p.is_file()}

    def test_aut_en_el_sitio_con_motivos(self):
        ind, err, s = self.correr(con_aut())
        self.assertEqual(err, "")
        self.assertEqual(ind["schema"], "ddd.v4-doble-vuelta/1.1")
        self.assertIn("aut01/resultados_doble_vuelta.csv", s)
        self.assertNotIn("aut01/distritos.geojson", s)  # el visor pinta el M08 del registro
        a = next(t for t in ind["territorios"] if t["id"] == "aut01")
        self.assertEqual((a["ambito"], a["clave_visor"], a["eleccion"], a["distritos"], a["run_m08"]), ("AUT", LEG, "2026-05", 3, "3001"))
        # ids: internos 0..2 en el ZIP de P75 → públicos 1..3 en el sitio (T-135), igual que los nac
        self.assertEqual(sorted({l.split(",")[0] for l in s["aut01/resultados_doble_vuelta.csv"].decode().splitlines()[1:]}), ["1", "2", "3"])
        self.assertEqual(a["resultados"]["sha256"], sha(s["aut01/resultados_doble_vuelta.csv"]))
        self.assertEqual([t["ambito"] for t in ind["territorios"]], ["NAC", "NAC", "AUT"])
        self.assertEqual([(x["id"], x["estado"], x["motivo"]) for x in ind["sin_doble_vuelta"]],
                         [("aut03", "SIN_VOTOS_AUTONOMICOS", "sin votos"), ("aut18", "NO_APLICA", "Ceuta no elige parlamento autonómico")])
        self.assertEqual(ind["autonomicas"]["bloques_sha256"], "c" * 64)
        self.assertEqual(json.loads(s["INDEX.json"]), ind)

    def test_sin_autonomicas_nada_cambia(self):
        ind, err, s = self.correr()
        # índice 1.1: los nac llevan EXACTAMENTE las claves de la 1.0.1 más `ambito` (literal de la 1.0.1, revisor de #946)
        claves_101 = {"id", "nombre", "etiqueta", "distritos", "run_m08", "sin_casar_pct", "sha256_paquete_p75", "resultados", "detalle", "geometria"}
        for t in ind["territorios"]:
            self.assertEqual(set(t), claves_101 | {"ambito"})
            self.assertEqual(t["ambito"], "NAC")
        self.assertEqual(ind["schema"], "ddd.v4-doble-vuelta/1.1")
        self.assertEqual(err, "")
        self.assertNotIn("autonomicas", ind)
        self.assertFalse(any(k.startswith("aut") for k in s))

    def test_rechazos(self):
        malo = [{"territorio": "aut01", "run": "1", "estado": "SHA_DISTINTO", "motivo": "x"}]
        for mod, causa in ((con_aut(filas=malo), "INFORME_INCOMPLETO"),
                           (con_aut(motivo=False), "INFORME_INCOMPLETO"),
                           (con_aut(filas=[{"territorio": "aut18", "run": "1", "estado": "NO_APLICA", "motivo": "x"}]), "ningún aut OK"),
                           (con_aut(eleccion="2023-07"), "INFORME_NO_ES_EL_FIJADO"),
                           (con_aut(pin_run="99-1"), "INFORME_NO_ES_EL_FIJADO"),
                           (con_aut(filas=[{"territorio": "nac01", "run": "1", "estado": "OK"}]), "TERRITORIO_INVALIDO")):
            ind, err, s = self.correr(mod)
            self.assertIn(causa, err)
            self.assertEqual(s, {})  # nada escrito


class FijadoAut(unittest.TestCase):
    """`autonomicas` del fijado: literales de la huella verificada en el log del job de P75 (run 45382110179, intento 1, 16/19 OK; aut11, aut18 y aut19 NO_APLICA)."""

    def setUp(self):
        self.pin = json.loads((ROOT / pdv.FIJADO).read_text(encoding="utf-8"))["autonomicas"]

    def test_valores_fijados(self):
        self.assertEqual(sorted(self.pin), ["informe_clave", "informe_sha256", "run_p75"])
        self.assertEqual(self.pin["run_p75"], "45382110179-1")
        self.assertEqual(self.pin["informe_clave"], "interno/doble-vuelta/autonomicas/informe-doble-vuelta.json")
        self.assertEqual(self.pin["informe_sha256"], "d684a089137fc94cef64395577e653764e1dc449685d9a98628cce41eaf62b44")

    def test_otro_informe_con_ese_nombre_falla_cerrado(self):
        with tempfile.TemporaryDirectory() as t, tempfile.TemporaryDirectory() as d:
            m = Montaje(Path(t), zips_buenos())
            con_aut()(m)  # informe sintético de los aut con su propia huella
            m.objetos[self.pin["informe_clave"]] = m.objetos.pop("doble_vuelta/autonomicas/88-1/INFORME.json")
            m.pin["autonomicas"] = dict(self.pin)  # el fijado real: su sha256 no es el del informe servido
            m.escribir_pin()
            with mock.patch.object(pdv, "ESPERADOS", 2), self.assertRaisesRegex(pdv.DobleVueltaError, "INFORME_SHA256_DISTINTO"):
                pdv.publicar(Path(t), Path(d), m.cp, "b", "2026-11-20", sitio=Path(t) / "sitio")
            self.assertEqual(list(Path(d).iterdir()), [])  # nada escrito


if __name__ == "__main__":
    unittest.main()
