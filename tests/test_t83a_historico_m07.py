#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PROYECTO: Diputado de Distrito
COMPONENTE: prueba del histórico por M07/M08 (T-83 paso A)
VERSIÓN: 1.0.0 · FECHA: 2026-11-08 · ESTADO: candidato
ANTERIOR: ninguna (fichero nuevo)
FUNCIÓN: provincia sintética de tres secciones vigentes (A y B → distrito 0, C → distrito 1) con valores esperados
  escritos a mano: reparto a escala de sección (una histórica partida 25/75), paquete M07 (CSV long, diccionario,
  contrato que carga `load_election_contract`) y ejecución real de M07 y M08 sobre él, sin total oficial completo (la oficial
  versionada es parcial), participación por distrito y rotación.
"""
import csv
import json
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "herramientas"))
sys.path.insert(0, str(ROOT))
try:
    import geopandas as gpd
    from shapely.geometry import box
    import reagregacion_historico as rh
    import historico_m07m08 as hm
    from ddd_core.electoral_contract import load_election_contract
except ImportError:  # pragma: no cover
    hm = None


def _s(cand, **votos):
    return {"censo": cand * 2, "votantes": cand, "votos_candidaturas": cand, "votos": votos}


@unittest.skipIf(hm is None, "faltan geopandas/shapely")
class HistoricoM07(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        # h1 = A; h2 partida 25 % A / 75 % B; h3 = C
        self.votos = {"h1": _s(40, PP=30, PSOE=10), "h2": _s(80, PP=20, PSOE=60), "h3": _s(20, PP=5, PSOE=15)}
        self.eq = {"h1": {"tipo": "1:1", "poblacion": {"2200101001": 1.0}},
                   "h2": {"tipo": "partida", "poblacion": {"2200101001": 0.25, "2200101002": 0.75}},
                   "h3": {"tipo": "1:1", "poblacion": {"2200201001": 1.0}}}

    def _secciones(self):
        return rh.redondear({"distritos": rh.reagregar_secciones(self.votos, self.eq)["distritos"]})

    def test_reparto_por_seccion(self):
        s = self._secciones()
        # A: h1 + 0,25·h2 = PP 30+5, PSOE 10+15; B: 0,75·h2 = PP 15, PSOE 45; C: h3
        self.assertEqual(s["2200101001"]["votos"], {"PP": 35, "PSOE": 25})
        self.assertEqual(s["2200101002"]["votos"], {"PP": 15, "PSOE": 45})
        self.assertEqual(s["2200201001"]["votos"], {"PP": 5, "PSOE": 15})
        self.assertEqual((s["2200101001"]["censo"], s["2200101002"]["votantes"]), (120, 60))

    def _paquete(self):
        return rh.escribir_paquete(self.tmp / "paq", "nac22", "201911", self._secciones(),
                                   {"PP": 56, "PSOE": 96}, {"path": "data/201911/sekzioa/22.json", "sha256": "x"})

    def test_paquete_carga_como_contrato(self):
        self._paquete()
        contrato, partidos = load_election_contract(self.tmp / "paq/contrato.json", project_root=ROOT,
                                                    expected_territory_id="nac22")
        self.assertEqual(contrato["election_id"], "congreso_huesca_2019-11-10")
        self.assertNotIn("official_candidate_votes", contrato["source_verification"])
        self.assertEqual(contrato["source_verification"]["official_party_votes_partial"], {"PP": 56, "PSOE": 96})
        self.assertEqual(partidos.canonicalize("psoe"), "PSOE")
        filas = (self.tmp / "paq/secciones.csv").read_text(encoding="utf-8").splitlines()
        self.assertEqual(filas[:3], ["section_id,party,votes", "2200101001,PP,35", "2200101001,PSOE,25"])

    def test_m07_m08_reales(self):
        self._paquete()
        comp = {"2200101001": ("0", 100), "2200101002": ("0", 300), "2200201001": ("1", 50)}
        geo = gpd.GeoDataFrame({"CUSEC": list(comp)}, geometry=[box(0, 0, 10, 10), box(10, 0, 20, 10),
                                                                box(20, 0, 30, 10)], crs=25830)
        shp = self.tmp / "secc"
        shp.mkdir()
        geo.to_file(shp / "secc.shp")
        zs = self.tmp / "seccionado.zip"
        with zipfile.ZipFile(zs, "w") as z:
            for f in shp.iterdir():
                z.write(f, arcname=f.name)
        dist = gpd.GeoDataFrame({"district_id": [0, 1]}, geometry=[box(0, 0, 20, 10), box(20, 0, 30, 10)],
                                crs=25830).to_crs(4326)
        dist.to_file(self.tmp / "distritos.geojson", driver="GeoJSON")
        zd = self.tmp / "distritos.zip"
        with zipfile.ZipFile(zd, "w") as z:
            z.write(self.tmp / "distritos.geojson", arcname="distritos.geojson")
        tr = self.tmp / "trabajo"
        secc, asign, inf = hm.secciones_m06(comp, zs, tr / "secciones.geojson.zip")
        self.assertEqual(inf["secciones_2025_por_solape"], {})
        p = hm.params("nac22", tr, secc, zd, self.tmp / "paq/contrato.json")
        hm.ejecutar("07_agregar_resultados_electorales.py", p)
        hm.ejecutar("08_integrar_resultados.py", p)
        rec = json.loads((tr / "m07_reconciliacion.json").read_text(encoding="utf-8"))
        self.assertEqual(rec["status"], "PASS")
        self.assertEqual((rec["source_votes"], rec["ddd_unassigned_votes"]), (140, 0))
        self.assertIsNone(rec["source_gap_to_definitive_votes"])  # sin total oficial completo
        res = hm.leer_resumen(tr / "m07_resumen_electoral.csv")
        self.assertEqual({d: (int(r["total_votes"]), r["winner_party"]) for d, r in res.items()},
                         {"0": (120, "PSOE"), "1": (20, "PSOE")})
        self.assertTrue((tr / "m08_distritos_resultados.geojson.zip").exists())
        part = hm.participacion(self.tmp / "paq/participacion.csv", asign)
        self.assertEqual((part["0"]["censo"], part["0"]["votantes"], part["1"]["censo"]), (240, 120, 40))

    def test_seccion_recodificada_por_solape(self):
        # composición con un código viejo (X) en lugar de C: C (2025) va al distrito de mayor solape (1)
        comp = {"2200101001": ("0", 100), "2200101002": ("0", 300), "2200299999": ("1", 50)}
        geo = gpd.GeoDataFrame({"CUSEC": ["2200101001", "2200101002", "2200201001"]},
                               geometry=[box(0, 0, 10, 10), box(10, 0, 20, 10), box(20, 0, 30, 10)], crs=25830)
        geo.to_file(self.tmp / "s.shp")
        zs = self.tmp / "s.zip"
        with zipfile.ZipFile(zs, "w") as z:
            for f in self.tmp.glob("s.*"):
                if f.suffix != ".zip":
                    z.write(f, arcname=f.name)
        dist = gpd.GeoDataFrame({"district_id": [0, 1]}, geometry=[box(0, 0, 22, 10), box(22, 0, 30, 10)],
                                crs=25830).to_crs(4326)
        dist.to_file(self.tmp / "d.geojson", driver="GeoJSON")
        _, asign, inf = hm.secciones_m06(comp, zs, self.tmp / "o.geojson.zip", self.tmp / "d.geojson",
                                         {"2200201001": 55})
        self.assertEqual(asign["2200201001"], "1")
        self.assertEqual(inf["composicion_sin_seccion_2025"], ["2200299999"])
        self.assertEqual(inf["composicion_exacta"], 2)

    def test_rotacion(self):
        out = self.tmp / "rot.csv"
        hm.escribir_rotacion(out, {"201904": {"0": "PSOE", "1": "PP"}, "201911": {"0": "PP", "1": "PP"},
                                   "202307": {"0": "PSOE", "1": "PP"}})
        with open(out, encoding="utf-8") as f:
            filas = list(csv.reader(f))
        self.assertEqual(filas, [["district_id", "201904", "201911", "202307", "cambios"],
                                 ["0", "PSOE", "PP", "PSOE", "2"], ["1", "PP", "PP", "PP", "0"]])


if __name__ == "__main__":
    unittest.main()
