#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PROYECTO: Diputado de Distrito
COMPONENTE: prueba de composición M06 y votos por partido (T-67)
VERSIÓN: 1.0.0 · FECHA: 2026-11-07 · ESTADO: candidato
ANTERIOR: ninguna (fichero nuevo)
FUNCIÓN: ZIP Infoelectoral sintético (ancho fijo) + M06/M08 sintéticos: extracción y validación de la composición,
  votos por partido, porcentajes, blancos/nulos/censo, idempotencia y fallos (ganador distinto del M08, sección sin
  distrito, huella del ZIP, composición que no cuadra con el M06).
"""
import io
import json
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "herramientas"))
import composicion_m06 as cm  # noqa: E402
import resultados_ligeros as rl  # noqa: E402
import resultados_partidos as rp  # noqa: E402

PRE = "02202307"


def _put(buf, a, b, txt):
    buf[a - 1:b] = list(str(txt).rjust(b - a + 1)[-(b - a + 1):])


def l09(muni, dist, sec, mesa, censo, bl, nu, cand):
    s = list(" " * 90)
    s[0:8] = PRE
    s[9:11] = "02"
    s[11:13] = "22"
    s[13:16] = muni
    s[16:18] = dist
    s[18:22] = sec.rjust(4)
    s[22:23] = mesa
    _put(s, 24, 30, censo)
    _put(s, 66, 72, bl)
    _put(s, 73, 79, nu)
    _put(s, 80, 86, cand)
    return "".join(s)


def l10(muni, dist, sec, mesa, code, votos):
    s = list(" " * 40)
    s[0:8] = PRE
    s[11:13] = "22"
    s[13:16] = muni
    s[16:18] = dist
    s[18:22] = sec.rjust(4)
    s[22:23] = mesa
    s[23:29] = code
    _put(s, 30, 36, votos)
    return "".join(s)


def l03(code, name):
    return (PRE + code).ljust(14) + name.ljust(50)


# sección → (distrito del M06, {A: votos, B: votos}, blancos, nulos, censo)
SECC = {"2200101001": None}
DATOS = {("001", "01", "001"): (0, {"PP": 50, "PSOE": 30}, 2, 1, 100),
         ("001", "01", "002"): (0, {"PP": 10, "PSOE": 20}, 1, 0, 60),
         ("002", "01", "001"): (1, {"PP": 5, "PSOE": 40}, 0, 3, 80),
         ("003", "01", "001"): (1, {"PP": 15, "PSOE": 5}, 1, 1, 50)}


def hacer_zip(ruta, datos=DATOS):
    cod = {"PP": "000001", "PSOE": "000002"}
    f09, f10 = [], []
    for (muni, dist, sec), (_, v, bl, nu, censo) in datos.items():
        f09.append(l09(muni, dist, sec, "U", censo, bl, nu, sum(v.values())))
        f10.extend(l10(muni, dist, sec, "U", cod[p], n) for p, n in v.items())
    f09.append(l09("999", "99", "0", "U", 5, 0, 0, 0).replace("22", "22", 1))
    with zipfile.ZipFile(ruta, "w") as z:
        z.writestr("09022307.DAT", "\n".join(f09) + "\n")
        z.writestr("10022307.DAT", "\n".join(f10) + "\n")
        z.writestr("03022307.DAT", "\n".join(l03(c, p) for p, c in cod.items()) + "\n")
    return rp.sha256(ruta.read_bytes())


def m06_zip(dist_info):
    feats = [{"properties": {"district_id": str(d), "section_count": n, "district_pop": pop}} for d, (n, pop) in dist_info.items()]
    b = io.BytesIO()
    with zipfile.ZipFile(b, "w") as z:
        z.writestr("x_m06_distritos.geojson", json.dumps({"features": feats}))
    return b.getvalue()


def m08_zip(gan):
    feats = [{"properties": {"district_id": str(i), "district_pop": 1, "total_votes": 1, "winner_party": g,
                             "winner_votes": 1, "winner_share": 0.5}} for i, g in enumerate(gan)]
    b = io.BytesIO()
    with zipfile.ZipFile(b, "w") as z:
        z.writestr("x_m08_distritos_resultados.geojson", json.dumps({"features": feats}))
    return b.getvalue()


COMP = ("CUSEC_KEY,district_id,section_pop,extra\n2200101001,0,300,a\n2200101002,0,200,a\n"
        "2200201001,1,250,a\n2200301001,1,150,a\n")


class Base(unittest.TestCase):
    def setUp(self):
        self.d = Path(tempfile.mkdtemp())
        self.zip = self.d / "mesa.zip"
        self.sha = hacer_zip(self.zip)
        self.m06 = m06_zip({0: (2, 500), 1: (2, 400)})
        self.m08 = m08_zip(["PP", "PSOE"])
        self.reg = self.d / "reg.json"
        t = "nac22"
        prods = [{"kind": "canonical_m06", "territory_id": t, "run_id": "7", "blob_sha": "m6", "sha256": cm.sha256(self.m06)},
                 {"kind": "canonical_m08", "territory_id": t, "run_id": "7", "blob_sha": "m8", "sha256": rl.sha256(self.m08)}]
        self.reg.write_text(json.dumps({"products": prods}))
        self.m06dir, self.m08dir = self.d / "m06", self.d / "m08"
        self.m06dir.mkdir(), self.m08dir.mkdir()
        (self.m06dir / f"{t}_7.zip").write_bytes(self.m06)
        (self.m08dir / f"{t}_7.zip").write_bytes(self.m08)
        self.origen = self.d / "origen"
        self.origen.mkdir()
        with zipfile.ZipFile(self.origen / "estado.zip", "w") as z:  # ZIP anidado, como el estado de un run
            inner = io.BytesIO()
            with zipfile.ZipFile(inner, "w") as zi:
                zi.writestr("cache/congreso_huesca_2025_m06_composicion_distritos.csv", COMP)
            z.writestr("estado.zip", inner.getvalue())
        self.comp, self.out = self.d / "comp", self.d / "out"
        self.contratos = self.d / "c.yaml"
        self.escribir_contrato(self.sha)

    def escribir_contrato(self, sha, cand=None):
        cand = 175 if cand is None else cand
        self.contratos.write_text(f"""contracts:
  congreso_huesca_2023-07-23:
    territory_id: nac22
    election_date: '2023-07-23'
    source_sha256: {sha}
    election_prefix: '{PRE}'
    files: {{mesas: 09022307.DAT, candidaturas_mesa: 10022307.DAT, candidaturas: 03022307.DAT}}
    province: '22'
    expected: {{ccaa: '02', sections: 4, polling_stations: 4, parties: 2, candidate_votes: {cand}, blank_votes: 4, null_votes: 5, voters: {cand + 9}}}
""")

    def extraer(self):
        return cm.extraer(self.origen, None, self.comp, self.reg, self.m06dir)

    def partidos(self, **kw):
        rl.generar(self.out, self.reg, m08_dir=self.m08dir)
        return rp.generar(self.out, self.reg, self.comp, self.zip, contratos_yaml=self.contratos, **kw)


class Composicion(Base):
    def test_extrae_y_valida(self):
        r = self.extraer()
        self.assertEqual(r["hechos"], ["nac22"])
        lineas = (self.comp / "congreso_huesca.csv").read_text().splitlines()
        self.assertEqual(lineas[0], "seccion,distrito,poblacion")
        self.assertEqual(lineas[1], "2200101001,0,300")
        man = json.loads((self.comp / "MANIFEST.json").read_text())["territorios"]["nac22"]
        self.assertEqual(man["secciones"], 4)

    def test_no_cuadra_con_m06(self):
        (self.m06dir / "congreso_huesca_7.zip").write_bytes(self.m06)
        reg = json.loads(self.reg.read_text())
        mal = m06_zip({0: (2, 500), 1: (3, 400)})
        (self.m06dir / "congreso_huesca_7.zip").write_bytes(mal)
        reg["products"][0]["sha256"] = cm.sha256(mal)
        self.reg.write_text(json.dumps(reg))
        self.assertEqual(self.extraer()["no_recuperados"], ["nac22"])
        self.assertFalse((self.comp / "congreso_huesca.csv").exists())

    def test_sha_m06_erroneo(self):
        reg = json.loads(self.reg.read_text())
        reg["products"][0]["sha256"] = "0" * 64
        self.reg.write_text(json.dumps(reg))
        with self.assertRaises(ValueError):
            self.extraer()


class Partidos(Base):
    def setUp(self):
        super().setUp()
        self.extraer()

    def test_csv_y_manifiesto(self):
        r = self.partidos()
        self.assertEqual(r["hechos"], ["nac22"])
        lineas = (self.out / "congreso_huesca_partidos.csv").read_text().splitlines()
        self.assertEqual(lineas[0], "distrito,partido,votos,porcentaje,blancos,nulos,censo")
        self.assertEqual(lineas[1], "0,PP,60,54.5455,3,1,160")
        self.assertEqual(lineas[2], "0,PSOE,50,45.4545,3,1,160")
        self.assertEqual(lineas[3], "1,PSOE,45,69.2308,1,4,130")
        man = json.loads((self.out / "MANIFEST.json").read_text())
        self.assertIn("nac22", man["partidos"])
        self.assertIn("nac22", man["territorios"])

    def test_idempotente_y_ligeros_conserva(self):
        self.partidos()
        a = (self.out / "congreso_huesca_partidos.csv").read_bytes()
        m = (self.out / "MANIFEST.json").read_bytes()
        self.partidos()
        self.assertEqual(a, (self.out / "congreso_huesca_partidos.csv").read_bytes())
        self.assertEqual(m, (self.out / "MANIFEST.json").read_bytes())

    def test_ganador_distinto_del_m08(self):
        mal = m08_zip(["PSOE", "PSOE"])
        (self.m08dir / "congreso_huesca_7.zip").write_bytes(mal)
        reg = json.loads(self.reg.read_text())
        reg["products"][1]["sha256"] = rl.sha256(mal)
        self.reg.write_text(json.dumps(reg))
        with self.assertRaisesRegex(ValueError, "ganador"):
            self.partidos()
        self.assertFalse((self.out / "congreso_huesca_partidos.csv").exists())

    def test_seccion_sin_distrito(self):
        (self.comp / "congreso_huesca.csv").write_text(
            "seccion,distrito,poblacion\n2200101001,0,300\n2200101002,0,200\n2200201001,1,250\n")
        man = json.loads((self.comp / "MANIFEST.json").read_text())
        man["territorios"]["nac22"]["sha256_csv"] = rp.sha256((self.comp / "congreso_huesca.csv").read_bytes())
        (self.comp / "MANIFEST.json").write_text(json.dumps(man))
        with self.assertRaisesRegex(ValueError, "sin distrito"):
            self.partidos()

    def test_huella_del_zip(self):
        self.escribir_contrato("f" * 64)
        with self.assertRaisesRegex(ValueError, "SHA-256"):
            self.partidos()

    def test_totales_del_contrato(self):
        self.escribir_contrato(self.sha, cand=999)
        with self.assertRaises(ValueError):
            self.partidos()

    def test_sin_composicion_se_omite(self):
        (self.comp / "MANIFEST.json").write_text(json.dumps({"territorios": {}}))
        self.assertEqual(self.partidos()["omitidos"], ["nac22"])


if __name__ == "__main__":
    unittest.main()
