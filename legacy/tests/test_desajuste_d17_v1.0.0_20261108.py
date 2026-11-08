#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PROYECTO: Diputado de Distrito
COMPONENTE: prueba de la tolerancia D-17 del archivista (T-101)
VERSIÓN: 1.0.0 · FECHA: 2026-11-08 · ESTADO: candidato
ANTERIOR: ninguna (fichero nuevo)
FUNCIÓN: ZIP Infoelectoral sintético con una sección recodificada, como Málaga (2900701022 en el ZIP, 2908405001 en el
  M06): por debajo del 0,5 % de los votos de la provincia los votos se reparten con la tabla de equivalencia (1:1 y
  partida en dos distritos con peso de población, D-13) y queda la lista de desajustes en el informe, en el JSON del
  run y en el MANIFEST; por encima del tope, o sin tabla, falla como antes. Valores esperados escritos a mano.
"""
import io
import json
import shutil
import sys
import tempfile
import unittest
import unittest.mock
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "herramientas"))
sys.path.insert(0, str(ROOT / "tests"))
import archivo_origen as ao  # noqa: E402
import resultados_partidos as rp  # noqa: E402
import test_resultados_partidos as trp  # noqa: E402

# (muni, distrito, sección) → (distrito M06, votos, blancos, nulos, censo). La 003-01-009 del ZIP es la 003-01-001 del M06.
GRANDE = {("001", "01", "001"): (0, {"PP": 5000, "PSOE": 4000}, 2, 1, 10000),
          ("001", "01", "002"): (0, {"PP": 10, "PSOE": 20}, 1, 0, 60),
          ("002", "01", "001"): (1, {"PP": 5, "PSOE": 4000}, 0, 3, 5000),
          ("003", "01", "009"): (1, {"PP": 15, "PSOE": 5}, 1, 1, 50)}
COMP = {"2200101001": 0, "2200101002": 0, "2200201001": 1, "2200301001": 1}
POB = {"2200101001": 300, "2200101002": 50, "2200201001": 250, "2200301001": 150}
EQ_1A1 = {"2200301009": [{"seccion_m06": "2200301001", "tipo": "reparto", "peso_area": 1.0, "frac_m06": 0.7}]}
# partida: mitad del área de cada vigente; población 150 (distrito 1) frente a 50 (distrito 0) → 0,75 / 0,25
EQ_PARTIDA = {"2200301009": [{"seccion_m06": "2200301001", "tipo": "reparto", "peso_area": 0.5, "frac_m06": 0.5},
                             {"seccion_m06": "2200101002", "tipo": "reparto", "peso_area": 0.5, "frac_m06": 0.5}]}


def contrato(ruta_yaml: Path, sha: str, datos: dict) -> dict:
    cand = sum(sum(v.values()) for _, v, *_ in datos.values())
    bl = sum(x[2] for x in datos.values())
    nu = sum(x[3] for x in datos.values())
    ruta_yaml.write_text(f"""contracts:
  congreso_huesca_2023-07-23:
    territory_id: congreso_huesca
    election_date: '2023-07-23'
    source_sha256: {sha}
    election_prefix: '{trp.PRE}'
    files: {{mesas: 09022307.DAT, candidaturas_mesa: 10022307.DAT, candidaturas: 03022307.DAT}}
    province: '22'
    expected: {{ccaa: '02', sections: {len(datos)}, polling_stations: {len(datos)}, parties: 2, candidate_votes: {cand}, blank_votes: {bl}, null_votes: {nu}, voters: {cand + bl + nu}}}
""")
    return rp.contratos(ruta_yaml)["congreso_huesca"]


class Tolerancia(unittest.TestCase):
    def setUp(self):
        self.d = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.d)
        self.zip = self.d / "mesa.zip"
        self.ctr = contrato(self.d / "c.yaml", trp.hacer_zip(self.zip, GRANDE), GRANDE)

    def test_malaga_recodificada_dentro_del_tope(self):
        cuerpo, inf = rp.agregar_informe(self.zip, self.ctr, COMP, ["PP", "PSOE"], equivalencia=EQ_1A1, poblacion=POB)
        self.assertEqual(cuerpo.decode().splitlines()[1:], [
            "0,PP,5010,55.4817,3,1,10060", "0,PSOE,4020,44.5183,3,1,10060",
            "1,PSOE,4005,99.5031,1,4,5050", "1,PP,20,0.4969,1,4,5050"])
        self.assertEqual(inf["votos_desajustados"], 20)
        self.assertEqual(inf["pct_desajuste"], 0.1532)  # 20 / 13055
        self.assertEqual([(x["seccion"], x["origen"], x["votos"], x["distritos"]) for x in inf["desajustes"]],
                         [("2200301009", "zip_sin_m06", 20, {"1": 1.0}), ("2200301001", "m06_sin_zip", 0, {"1": 1.0})])
        self.assertIn("población", inf["desajustes"][0]["regla"])

    def test_seccion_partida_peso_poblacion(self):
        cuerpo, inf = rp.agregar_informe(self.zip, self.ctr, COMP, ["PP", "PSOE"], equivalencia=EQ_PARTIDA, poblacion=POB)
        # PP 15 → 11,25 / 3,75 → 11 / 4 ; PSOE 5 → 3,75 / 1,25 → 4 / 1 (restos mayores)
        filas = {(r.split(",")[0], r.split(",")[1]): int(r.split(",")[2]) for r in cuerpo.decode().splitlines()[1:]}
        self.assertEqual(filas, {("0", "PP"): 5014, ("0", "PSOE"): 4021, ("1", "PSOE"): 4004, ("1", "PP"): 16})
        self.assertEqual(inf["desajustes"][0]["distritos"], {"0": 0.25, "1": 0.75})

    def test_por_encima_del_tope_falla(self):
        d = self.d / "chico"
        d.mkdir()
        z = d / "mesa.zip"
        datos = {k: v for k, v in trp.DATOS.items() if k[0] != "003"} | {("003", "01", "009"): (1, {"PP": 15, "PSOE": 5}, 1, 1, 50)}
        ctr = contrato(d / "c.yaml", trp.hacer_zip(z, datos), datos)  # 20 de 175 votos = 11,4 %
        with self.assertRaisesRegex(ValueError, r"tope 0.5 % \(D-17\)"):
            rp.agregar_informe(z, ctr, COMP, ["PP", "PSOE"], equivalencia=EQ_1A1, poblacion=POB)

    def test_sin_tabla_o_sin_equivalencia_falla(self):
        with self.assertRaisesRegex(ValueError, "secciones del ZIP sin distrito 1"):
            rp.agregar(self.zip, self.ctr, COMP, ["PP", "PSOE"])
        with self.assertRaisesRegex(ValueError, "no tiene equivalencia"):
            rp.agregar_informe(self.zip, self.ctr, COMP, ["PP", "PSOE"], equivalencia={}, poblacion=POB)

    def test_archivista_deja_evidencia(self):
        root = self.d / "repo"
        rc = root / "datos/composicion/runs/congreso_huesca_77.csv"
        rc.parent.mkdir(parents=True)
        rc.write_text("seccion,distrito,poblacion\n" + "".join(f"{s},{d},{POB[s]}\n" for s, d in COMP.items()))
        (root / "datos/composicion/MANIFEST.json").write_text(json.dumps({"runs": {"congreso_huesca/77": {
            "ruta": "datos/composicion/runs/congreso_huesca_77.csv", "sha256_csv": ao.cm.sha256(rc.read_bytes())}}}))
        eq = self.d / "eq.csv"
        eq.write_text("seccion_zip,seccion_m06,tipo,peso_area,frac_m06\n2200301009,2200301001,reparto,1.000000,0.700000\n")
        est8 = self.d / "est8"
        est8.mkdir()
        (est8 / "m08.geojson").write_bytes(zipfile.ZipFile(io.BytesIO(trp.m08_zip(["PP", "PSOE"]))).read("x_m08_distritos_resultados.geojson"))
        with unittest.mock.patch("sys.stdout", new=io.StringIO()):
            e = ao.escribir_partidos(est8, "congreso_huesca", "88", "77", root, self.zip, self.d / "c.yaml", eq)
        self.assertEqual(e["desajustes"]["secciones"], 2)
        self.assertEqual(e["desajustes"]["ruta"], "datos/resultados/runs/congreso_huesca_88_desajustes.json")
        j = json.loads((root / e["desajustes"]["ruta"]).read_text())
        self.assertEqual(j["desajustes"][0]["seccion"], "2200301009")
        self.assertEqual(j["tope_pct"], 0.5)
        man = json.loads((root / "datos/resultados/MANIFEST.json").read_text())["partidos_runs"]["congreso_huesca/88"]
        self.assertEqual(man["desajustes"]["sha256"], ao.cm.sha256((root / e["desajustes"]["ruta"]).read_bytes()))


class TablaVersionada(unittest.TestCase):
    def test_sha256_y_malaga(self):
        eq = rp.leer_equivalencia()  # comprueba el sha256 del CSV contra su JSON
        self.assertEqual([x["seccion_m06"] for x in eq["2900701022"]], ["2900701003"])
        meta = json.loads(rp.EQUIVALENCIA_META.read_text(encoding="utf-8"))
        self.assertEqual(meta["fuentes"]["zip_mesa_2023"]["sha256"],
                         "e78fc231326a03cf67bbec87b7100ea0c8c46859daa1b2a631c06daaaf1717f8")


if __name__ == "__main__":
    unittest.main()
