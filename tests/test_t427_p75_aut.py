#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PROYECTO: Diputado de Distrito
COMPONENTE: P75 de los aut (T-427): autonómica vigente sobre el mapa del run M08 vigente, con R2 simulado y repositorio sintético
VERSIÓN: 1.0.0 · FECHA: 2026-11-20 · ESTADO: candidato
ANTERIOR: ninguna (fichero nuevo)
FUNCIÓN: valores a mano: un aut OK con tabla y alias de SU comunidad; ningún aut en silencio (NO_APLICA con motivo, SIN_VOTOS_AUTONOMICOS,
  VOTOS_DE_OTRO_MAPA, DISTRITOS_NO_CASAN); nac y aut no se mezclan; los datos reales del repo cubren los 13 aut con votos y su MANIFEST casa
  con la composición del run vigente; las descripciones del botón de P70.
"""
import csv
import hashlib
import io
import json
import os
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest import mock

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "herramientas"))
import p75_doble_vuelta_r2 as p75  # noqa: E402

from ddd_core import territorio_ids  # noqa: E402

RUN = "2001"
COMP = "seccion,distrito,poblacion\n0100101001,0,10\n0100101002,1,10\n"
# distrito 0: PP 60, PSOE-A 40 → PP en 1.ª; distrito 1: PP 30, PSOE-A 28, AA 22 (Izquierdas en aut01), VOX 15, XX 5 (sin bloque)
VOTOS = "distrito,partido,votos,porcentaje\n0,PP,60,0\n0,PSOE-A,40,0\n1,PP,30,0\n1,PSOE-A,28,0\n1,AA,22,0\n1,VOX,15,0\n1,XX,5,0\n"
BLOQUES = ("comunidad,eleccion,siglas,denominacion,bloque_propuesto,motivo,votos,fuente_sha256\n"
           "aut01,2026-05,PP,PP,Patriotas,x,0,x\naut01,2026-05,PSOE,PSOE,Izquierdas,x,0,x\naut01,2026-05,AA,AA,Izquierdas,x,0,x\n"
           "aut01,2026-05,VOX,VOX,Patriotas,x,0,x\naut01,2026-05,XX,XX,,x,0,x\n"
           "aut02,2026-02,AA,AA,Patriotas,x,0,x\n")  # AA es de otro bloque en OTRA comunidad: no debe usarse
ALIAS = ("comunidad,eleccion,id_fuente,partido_homologado,origen,fuente\n"
         "aut01,202605,PP,PP,I,\naut01,202605,PSOE-A,PSOE,P,\naut01,202605,AA,AA,I,\naut01,202605,VOX,VOX,I,\naut01,202605,XX,XX,I,\n"
         "aut02,202602,AA,AA,I,\n")
CAL = ("comunidad,cod_ine,mes,en_alcance,vigente\naut01,01,2022-06,si,no\naut01,01,2026-05,si,si\naut02,02,2026-02,si,si\n")


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def paquete(ids=("0", "1")) -> bytes:
    b = io.BytesIO()
    with zipfile.ZipFile(b, "w") as z:  # votos de las GENERALES (lo que trae el M08 de un aut): solo se usan sus distritos
        z.writestr("estado/cache/run_m07_resultados_partido.csv", "district_id,party,votes\n" + "".join(f"{i}.0,PP-EU,1\n" for i in ids))
    return b.getvalue()


def montar(td: Path, paq: bytes, votos=True, run_manifiesto=RUN, comp_extra="") -> Path:
    for d in ("orchestracion", "configuracion", "datos/composicion/runs"):
        (td / d).mkdir(parents=True)
    leg = territorio_ids.id_legacy("aut01")
    prods = [{"kind": "canonical_m08", "territory_id": t, "run_id": r} for t, r in ((leg, RUN), ("aut02", "2002"), ("aut18", "2018"), ("nac01", "1"))]
    (td / "orchestracion/publicaciones_visor.json").write_text(json.dumps({"products": prods}), encoding="utf-8")
    arts = {f"{leg}/{RUN}/ddd-minimo-{RUN}-M08.zip": {"run_id": RUN, "artefacto": f"ddd-minimo-{RUN}-M08", "sha256": sha(paq)}}
    (td / "orchestracion/archivo_r2.json").write_text(json.dumps({"schema": "ddd.archivo-r2/1.0", "artefactos": arts}), encoding="utf-8")
    (td / "configuracion/bloques_partidos_autonomicas_2026-11-19.csv").write_text(BLOQUES, encoding="utf-8")
    (td / "configuracion/alias_partidos_autonomicas.csv").write_text(ALIAS, encoding="utf-8")
    (td / "configuracion/calendario_autonomicas.csv").write_text(CAL, encoding="utf-8")
    comp = (COMP + comp_extra).encode()
    (td / f"datos/composicion/runs/aut01_{RUN}.csv").write_bytes(comp)
    (td / "datos/composicion/MANIFEST_RUNS.json").write_text(json.dumps({"ficheros": {f"runs/aut01_{RUN}.csv": {
        "territorio": "aut01", "run_id": RUN, "sha256_csv": sha(COMP.encode())}}}), encoding="utf-8")
    if votos:
        c = td / "datos/resultados/doble_vuelta_autonomicas/aut01/202605"
        c.mkdir(parents=True)
        (c / "aut01_partidos.csv").write_text(VOTOS, encoding="utf-8")
        (c / "MANIFEST.json").write_text(json.dumps({"territorio": "aut01", "run_m08": run_manifiesto,
                                                     "composicion_ruta": f"datos/composicion/runs/aut01_{RUN}.csv",
                                                     "fuentes": {"composicion": sha(COMP.encode())},
                                                     "cuadre": {"ok": True, "aproximado_en_distrito": False, "nivel": "seccion"}}), encoding="utf-8")
    return td


def cp_de(paq: bytes):
    def cp(origen, destino, extra=None):
        Path(destino).write_bytes(paq)
    return cp


class P75Aut(unittest.TestCase):
    def correr(self, paq=None, cp_paq=None, pedidos="aut", ajuste=None, **kw):
        paq = paq or paquete()
        with tempfile.TemporaryDirectory() as t, tempfile.TemporaryDirectory() as w, mock.patch.dict(os.environ, {"R2_BUCKET": "b", "R2_ACCOUNT_ID": "a"}):
            r = montar(Path(t), paq, **kw)
            if ajuste:
                ajuste(r)
            inf = p75.ejecutar(r, pedidos, "", Path(w), cp_de(cp_paq or paq))
            zips = {p.parent.parent.name: p.read_bytes() for p in Path(w).rglob("ddd-doble-vuelta-*.zip")}
            return inf, {f["territorio"]: f for f in inf["territorios"]}, zips

    def test_aut_ok_con_la_tabla_de_su_comunidad(self):
        inf, f, zips = self.correr()
        self.assertEqual(inf["eleccion"], "autonomicas")
        self.assertEqual(inf["entradas"]["bloques"]["ruta"], "configuracion/bloques_partidos_autonomicas_2026-11-19.csv")
        a = f["aut01"]
        self.assertEqual((a["estado"], a["eleccion"], a["sin_casar_pct"], a["sin_bloque_pct"]), ("OK", "2026-05", 0.0, 2.5))  # XX: 5 de 200
        z = zipfile.ZipFile(io.BytesIO(zips["aut01"]))
        filas = {(r["district_id"], r["escenario"]): r for r in csv.DictReader(io.StringIO(z.read("doble_vuelta.csv").decode()))}
        self.assertEqual(filas[("0", "dv_base")]["candidatura_ganadora"], "PP")
        # distrito 1, dv_A: Izquierdas (PSOE 28 + AA 22 = 50) frente a Patriotas (PP 30 + VOX 15 = 45); XX se abstiene. Si se usara la fila de
        # aut02 (AA en Patriotas), ganaría Patriotas: prueba que la tabla va filtrada por comunidad.
        d = filas[("1", "dv_A")]
        self.assertEqual((d["candidatura_ganadora"], d["votos_a_2v"], d["votos_b_2v"], d["votos_abstencion"]), ("bloque:Izquierdas", "50", "45", "5"))
        self.assertEqual(json.loads(z.read("manifiesto.json"))["comunidad"], "aut01")

    def test_ninguno_en_silencio(self):
        inf, f, _ = self.correr()
        self.assertEqual(sorted(f), ["aut01", "aut02", "aut18"])  # todos los aut del registro; ningún nac
        self.assertEqual(f["aut18"]["estado"], "NO_APLICA")
        self.assertIn("Ceuta", f["aut18"]["motivo"])
        self.assertEqual(f["aut02"]["estado"], "SIN_VOTOS_AUTONOMICOS")  # tiene autonómica pero no votos en el mapa vigente
        self.assertIn("doble_vuelta_autonomicas/aut02/202602", f["aut02"]["motivo"])
        self.assertEqual((inf["ok"], inf["no_aplica"], inf["total"]), (1, 1, 3))
        for t in ("aut11", "aut18", "aut19"):
            self.assertIn(t, p75.NO_APLICA)

    def test_formato_de_t426(self):
        """MANIFEST de T-426 (#944): `composicion_sha256` arriba, sin `composicion_ruta`, `cuadre.exacto`; nivel y aproximado arriba."""
        def t426(td):
            m = td / "datos/resultados/doble_vuelta_autonomicas/aut01/202605/MANIFEST.json"
            m.write_text(json.dumps({"schema": "ddd.doble-vuelta-votos-aut/1.0", "territorio": "aut01", "eleccion": "202605", "run_m08": RUN,
                                     "composicion_sha256": sha(COMP.encode()), "aproximado_en_distrito": True, "nivel": "municipio",
                                     "cuadre": {"exacto": True, "votos_entrada": 200, "votos_salida": 200}}), encoding="utf-8")
        _, f, zips = self.correr(ajuste=t426)
        self.assertEqual((f["aut01"]["estado"], f["aut01"]["nivel"], f["aut01"]["aproximado_en_distrito"]), ("OK", "municipio", True))
        z = zipfile.ZipFile(io.BytesIO(zips["aut01"]))  # la entrada «distrito,partido,votos» llega a doble_vuelta.py como district_id,party,votes
        self.assertEqual(json.loads(z.read("manifiesto.json"))["entradas"]["votos"]["ruta"], "votos_autonomica.csv")
        self.assertEqual(sorted({r["district_id"] for r in csv.DictReader(io.StringIO(z.read("detalle.csv").decode()))}), ["0", "1"])

    def test_votos_de_otro_mapa(self):
        _, f, zips = self.correr(run_manifiesto="1999")  # MANIFEST de los votos con otro run
        self.assertEqual(f["aut01"]["estado"], "VOTOS_DE_OTRO_MAPA")
        _, f, zips = self.correr(comp_extra="0100101003,1,5\n")  # la composición del run ya no es la del MANIFEST_RUNS
        self.assertEqual(f["aut01"]["estado"], "VOTOS_DE_OTRO_MAPA")
        self.assertNotIn("aut01", zips)

    def test_distritos_del_m08_deben_ser_los_de_los_votos(self):
        p = paquete(ids=("0", "1", "2"))
        _, f, zips = self.correr(paq=p)
        self.assertEqual(f["aut01"]["estado"], "DISTRITOS_NO_CASAN")
        self.assertEqual(zips, {})

    def test_sha256_del_m08(self):
        _, f, _ = self.correr(cp_paq=paquete(ids=("0", "1", "9")))
        self.assertEqual(f["aut01"]["estado"], "SHA_DISTINTO")

    def test_nac_y_aut_no_se_mezclan(self):
        self.assertTrue(p75.es_aut("aut"))
        self.assertTrue(p75.es_aut("aut01,aut02"))
        self.assertFalse(p75.es_aut(""))
        self.assertFalse(p75.es_aut("nac01"))
        with self.assertRaisesRegex(ValueError, "P75_AMBITOS_MEZCLADOS"):
            p75.es_aut("nac01,aut01")

    def test_un_codigo_aut(self):
        _, f, _ = self.correr(pedidos=territorio_ids.id_legacy("aut01"))  # el id legacy vale
        self.assertEqual(list(f), ["aut01"])


class DatosReales(unittest.TestCase):
    """Los votos versionados casan con la composición del run M08 vigente y con el calendario (sin red ni R2)."""

    def test_trece_aut_con_votos_del_mapa_vigente(self):
        con = sorted(p.name for p in (ROOT / p75.VOTOS_AUT).iterdir() if p.is_dir())
        self.assertEqual(con, sorted(["aut01", "aut02", "aut04", "aut05", "aut06", "aut07", "aut09", "aut10", "aut12", "aut13", "aut15", "aut16", "aut17"]
                         + [t for t in ("aut03", "aut08", "aut14") if t in con]))  # T-426 añade aut03, aut08 y aut14
        vig = dict(p75.territorios_aut(ROOT))
        for t in con:
            ele = p75.eleccion_vigente_aut(ROOT, t)
            csvp, man, estado = p75.votos_aut(ROOT, t, vig[t], ele)
            self.assertEqual(estado, "", t)
            self.assertEqual(man["territorio"], t)
            self.assertTrue(man["cuadre"].get("ok") or man["cuadre"].get("exacto"), t)  # reagregación u T-426

    def test_reagregacion_usa_la_composicion_del_run_vigente(self):
        import reagregacion_autonomicas as ra
        ruta, run = ra.composicion_vigente("aut17")
        self.assertEqual(run, dict(p75.territorios_aut(ROOT))["aut17"])
        self.assertEqual(ruta, ROOT / f"datos/composicion/runs/aut17_{run}.csv")
        with self.assertRaises(SystemExit):
            ra.composicion_vigente("aut99")

    def test_no_aplica_no_tiene_votos(self):
        for t in p75.NO_APLICA:
            self.assertFalse((ROOT / p75.VOTOS_AUT / t).exists(), t)


class Boton(unittest.TestCase):
    def test_descripciones(self):
        w = yaml.safe_load((ROOT / ".github/workflows/p70-archivo.yml").read_text(encoding="utf-8"))
        ent = (w.get("on") or w.get(True))["workflow_dispatch"]["inputs"]
        self.assertIn("aut = los 19 autonómicos", ent["territorios"]["description"])
        self.assertIn("los aut usan su autonómica vigente", ent["eleccion"]["description"])


if __name__ == "__main__":
    unittest.main()
