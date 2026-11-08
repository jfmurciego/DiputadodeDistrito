#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PROYECTO: Diputado de Distrito
COMPONENTE: prueba de la tolerancia D-17 del archivista (T-101)
<<<<<<< HEAD
VERSIÓN: 1.2.0 · FECHA: 2026-11-08 · ESTADO: candidato
CAMBIOS: 1.2.0 (T-104): partida con todas sus secciones M06 en un mismo distrito = «contenida_distrito», fuera del
  tope (caso sintético y Valencia/Bétera con la composición versionada); caso negativo: partida entre dos distritos.
  1.1.0 (T-103): recodificada (1:1), contenida y partida; solo las partidas cuentan para el tope; cifras de
  Badajoz, Albacete, Almería y Valencia con la tabla versionada (Valencia sigue por encima del tope).
ANTERIOR: legacy/tests/test_desajuste_d17_v1.1.0_20261108.py
=======
VERSIÓN: 1.1.0 · FECHA: 2026-11-08 · ESTADO: candidato
CAMBIOS: 1.1.0 (T-103): recodificada (1:1), contenida y partida; solo las partidas cuentan para el tope; cifras de
  Badajoz, Albacete, Almería y Valencia con la tabla versionada (Valencia sigue por encima del tope).
ANTERIOR: legacy/tests/test_desajuste_d17_v1.0.0_20261108.py
>>>>>>> origin/main
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
EQ_RECOD = {"2200301009": [{"seccion_m06": "2200301001", "tipo": "1:1", "peso_area": 1.0, "frac_m06": 1.0}]}
EQ_1A1 = {"2200301009": [{"seccion_m06": "2200301001", "tipo": "reparto", "peso_area": 1.0, "frac_m06": 0.7}]}
# partida: mitad del área de cada vigente; población 150 (distrito 1) frente a 50 (distrito 0) → 0,75 / 0,25
EQ_PARTIDA = {"2200301009": [{"seccion_m06": "2200301001", "tipo": "reparto", "peso_area": 0.5, "frac_m06": 0.5},
                             {"seccion_m06": "2200101002", "tipo": "reparto", "peso_area": 0.5, "frac_m06": 0.5}]}
# T-104: partida entre dos secciones del mismo distrito (1): población 250 y 150 → 0,625 / 0,375, distrito 1 exacto
EQ_MISMO_DISTRITO = {"2200301009": [{"seccion_m06": "2200201001", "tipo": "reparto", "peso_area": 0.5, "frac_m06": 0.5},
                                    {"seccion_m06": "2200301001", "tipo": "reparto", "peso_area": 0.5, "frac_m06": 0.5}]}


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
        self.assertEqual(inf["desajustes"][0]["clase"], "contenida")
        self.assertEqual((inf["votos_partidos"], inf["pct_partido"]), (0, 0.0))

    def test_recodificada_1a1_fuera_del_tope(self):
        cuerpo, inf = rp.agregar_informe(self.zip, self.ctr, COMP, ["PP", "PSOE"], equivalencia=EQ_RECOD, poblacion=POB)
        self.assertIn("1,PP,20,0.4969,1,4,5050", cuerpo.decode().splitlines())
        self.assertEqual((inf["desajustes"][0]["clase"], inf["votos_partidos"]), ("recodificada", 0))

    def test_seccion_partida_peso_poblacion(self):
        cuerpo, inf = rp.agregar_informe(self.zip, self.ctr, COMP, ["PP", "PSOE"], equivalencia=EQ_PARTIDA, poblacion=POB)
        # PP 15 → 11,25 / 3,75 → 11 / 4 ; PSOE 5 → 3,75 / 1,25 → 4 / 1 (restos mayores)
        filas = {(r.split(",")[0], r.split(",")[1]): int(r.split(",")[2]) for r in cuerpo.decode().splitlines()[1:]}
        self.assertEqual(filas, {("0", "PP"): 5014, ("0", "PSOE"): 4021, ("1", "PSOE"): 4004, ("1", "PP"): 16})
        self.assertEqual(inf["desajustes"][0]["distritos"], {"0": 0.25, "1": 0.75})
        self.assertEqual((inf["desajustes"][0]["clase"], inf["votos_partidos"]), ("partida", 20))
        self.assertIn("población", inf["desajustes"][0]["regla"])
<<<<<<< HEAD

    def test_contenida_en_distrito_fuera_del_tope(self):
        cuerpo, inf = rp.agregar_informe(self.zip, self.ctr, COMP, ["PP", "PSOE"], equivalencia=EQ_MISMO_DISTRITO,
                                         poblacion=POB)
        self.assertIn("1,PP,20,0.4969,1,4,5050", cuerpo.decode().splitlines())
        x = inf["desajustes"][0]
        self.assertEqual((x["clase"], x["distritos"], inf["votos_partidos"]), ("contenida_distrito", {"1": 1.0}, 0))
        self.assertEqual(x["secciones_m06"], {"2200201001": 0.625, "2200301001": 0.375})
        self.assertIn("T-104", x["regla"])
        # caso negativo: candidatas en dos distritos → sigue partida
        self.assertEqual(rp.clasificar(EQ_PARTIDA["2200301009"], COMP), "partida")
=======
>>>>>>> origin/main

    def test_por_encima_del_tope_falla(self):
        d = self.d / "chico"
        d.mkdir()
        z = d / "mesa.zip"
        datos = {k: v for k, v in trp.DATOS.items() if k[0] != "003"} | {("003", "01", "009"): (1, {"PP": 15, "PSOE": 5}, 1, 1, 50)}
        ctr = contrato(d / "c.yaml", trp.hacer_zip(z, datos), datos)  # 20 de 175 votos = 11,4 %
        with self.assertRaisesRegex(ValueError, r"tope 0.5 % \(D-17\) \[secciones partidas: 2200301009=20\]"):
            rp.agregar_informe(z, ctr, COMP, ["PP", "PSOE"], equivalencia=EQ_PARTIDA, poblacion=POB)
<<<<<<< HEAD
        # la misma sección contenida, recodificada o contenida en un distrito no cuenta: pasa aunque sea el 11,4 %
        for eq in (EQ_1A1, EQ_RECOD, EQ_MISMO_DISTRITO):
=======
        # la misma sección contenida o recodificada no cuenta: pasa aunque sea el 11,4 % de la provincia
        for eq in (EQ_1A1, EQ_RECOD):
>>>>>>> origin/main
            self.assertEqual(rp.agregar_informe(z, ctr, COMP, ["PP", "PSOE"], equivalencia=eq, poblacion=POB)[1]["votos_partidos"], 0)

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


class CuatroProvincias(unittest.TestCase):
    """T-103: % partido con la tabla versionada (cifras de la clasificación enviada al propietario el 08-11)."""
    def test_pct_partido(self):
        eq = rp.leer_equivalencia()
        prov = json.loads(rp.EQUIVALENCIA_META.read_text(encoding="utf-8"))["provincias"]
        esperado = {"congreso_badajoz": (386842, 693), "congreso_albacete": (218503, 0),
                    "congreso_almeria": (316006, 0), "congreso_valencia": (1419017, 8511)}
        for terr, (total, partidos) in esperado.items():
            p = prov[terr]
            self.assertEqual(p["votos_candidaturas"], total)
            v = sum(s["votos"] for s in p["secciones_zip_sin_m06"] if rp.clasificar(eq[s["seccion"]]) == "partida")
            self.assertEqual(v, partidos, terr)
            self.assertEqual(v / total > rp.TOPE_DESAJUSTE, terr == "congreso_valencia", terr)
        self.assertEqual(rp.clasificar(eq["0608304014"]), "recodificada")
<<<<<<< HEAD
        self.assertFalse(hasattr(rp, "CASOS_APARTE"))

    def test_valencia_betera_en_un_distrito(self):
        """T-104: con la composición versionada, las 10 partidas de Bétera (46070) caen todas en el distrito 22."""
        eq = rp.leer_equivalencia()
        comp = rp.leer_composicion(rp.COMPOSICION / "congreso_valencia.csv")
        p = json.loads(rp.EQUIVALENCIA_META.read_text(encoding="utf-8"))["provincias"]["congreso_valencia"]
        clases = {s["seccion"]: rp.clasificar([e for e in eq[s["seccion"]] if e["seccion_m06"] in comp], comp)
                  for s in p["secciones_zip_sin_m06"]}
        self.assertNotIn("partida", clases.values())
        betera = [s for s, c in clases.items() if c == "contenida_distrito"]
        self.assertEqual(len(betera), 10)
        self.assertTrue(all(s.startswith("46070") for s in betera))
        self.assertEqual({comp[e["seccion_m06"]] for s in betera for e in eq[s]}, {22})
=======
        self.assertIn("46", rp.CASOS_APARTE)
>>>>>>> origin/main


if __name__ == "__main__":
    unittest.main()
