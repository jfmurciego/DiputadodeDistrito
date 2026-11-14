"""T-291 · votos por partido de 2026 con la regla de M07 (partida entera al distrito de mayor población, D-65)."""
from __future__ import annotations

import csv
import importlib.util
import io
import sys
import tempfile
import unittest
from collections import defaultdict
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "herramientas"))
sys.path.insert(0, str(ROOT / "tests"))
import resultados_ligeros as rl  # noqa: E402
import resultados_partidos as rp  # noqa: E402
from test_resultados_partidos import PRE, hacer_zip  # noqa: E402

spec = importlib.util.spec_from_file_location("m07_t291_partidos", ROOT / "modulos/07_agregar_resultados_electorales.py")
m07 = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(m07)

# Composición 2023: 2200101002 no existe (es una sección 2026 nueva); 2200401001 no tiene mesas en el ZIP.
COMP = {"2200101001": 0, "2200201001": 1, "2200301001": 1, "2200401001": 1}
# 2200101002 es partida: 0,4 en el distrito 0 y 0,6 en el 1 → entera al 1 (a 2200201001, su sección de más peso).
TABLA = {"2200101002": {"tipo": "partida", "pesos": [("2200101001", 0.4), ("2200201001", 0.35), ("2200301001", 0.25)]}}


def _contrato(sha: str) -> dict:
    return {"election_id": "nac22_2026-11-29", "territory_id": "nac22", "election_date": "2026-11-29", "source_sha256": sha, "election_prefix": PRE,
            "files": {"mesas": "09022307.DAT", "candidaturas_mesa": "10022307.DAT", "candidaturas": "03022307.DAT"},
            "province": "22",
            "expected": {"ccaa": "02", "sections": 4, "polling_stations": 4, "parties": 2, "candidate_votes": 175,
                         "blank_votes": 4, "null_votes": 5, "voters": 184}}


class Partidos2026(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.zip = Path(self.tmp.name) / "mesa.zip"
        self.contrato = _contrato(hacer_zip(self.zip))

    def tearDown(self):
        self.tmp.cleanup()

    def _filas(self, tabla=TABLA, ganadores=("PP", "PSOE")):
        cuerpo, informe = rp.agregar_informe(self.zip, self.contrato, COMP, list(ganadores), mayoria=tabla)
        return list(csv.DictReader(io.StringIO(cuerpo.decode("utf-8")))), informe

    def test_literal_partida_entera_al_distrito_de_mayor_poblacion(self):
        filas, informe = self._filas()
        got = [(r["distrito"], r["partido"], r["votos"], r["blancos"], r["nulos"], r["censo"]) for r in filas]
        # Distrito 0: 2200101001 (PP 50, PSOE 30). Distrito 1: el resto, con 2200101002 entera (PP 10, PSOE 20).
        self.assertEqual(got, [("0", "PP", "50", "2", "1", "100"), ("0", "PSOE", "30", "2", "1", "100"),
                               ("1", "PSOE", "65", "2", "4", "190"), ("1", "PP", "30", "2", "4", "190")])
        self.assertEqual(informe["votos_por_mayoria_entre_distritos"], 30)
        self.assertEqual(informe["asignaciones"][0]["destino"], "2200201001")

    def test_suma_por_distrito_igual_al_total_de_m07(self):
        filas, _ = self._filas()
        partidos = defaultdict(int)
        for r in filas:
            partidos[int(r["distrito"])] += int(r["votos"])
        # El mismo reparto por sección pasado por M07 7.4.0 (apply_section_equivalence) y agregado por distrito.
        votos = pd.DataFrame([("2200101001", "PP", 50), ("2200101001", "PSOE", 30), ("2200101002", "PP", 10),
                              ("2200101002", "PSOE", 20), ("2200201001", "PP", 5), ("2200201001", "PSOE", 40),
                              ("2200301001", "PP", 15), ("2200301001", "PSOE", 5)],
                             columns=["section", "party", "votes"])
        mapa = pd.DataFrame({"section": list(COMP), "district": [str(d) for d in COMP.values()]})
        out, _ = m07.apply_section_equivalence(votos, mapa, section_field="section", district_field="district",
                                               table=TABLA)
        m07_tot = out.merge(mapa, on="section").groupby("district")["votes"].sum()
        self.assertEqual(dict(partidos), {int(d): int(v) for d, v in m07_tot.items()})

    def test_seccion_sin_destino_falla(self):
        with self.assertRaisesRegex(ValueError, "sin distrito tras la equivalencia"):
            self._filas(tabla={})

    def test_salida_2026_aparte(self):
        self.assertEqual(rl.salida_de("2023-07-23"), rl.SALIDA)
        self.assertEqual(rl.salida_de("2026-11-29"), rl.SALIDA / "2026-11-29")
        self.assertEqual(rl.salida_de("2026-11-29", Path("x")), Path("x"))

    def test_destino_igual_a_m07_con_desempate_por_cadena_y_bloque_ausente(self):
        # Distritos 10 y 2 empatados: como M07, gana la cadena menor («10» < «2»). X no está en el mapa.
        comp = {"A": 10, "B": 2, "C": 2}
        casos = {"S1": [("A", 0.5), ("B", 0.5)], "S2": [("A", 0.3), ("X", 0.7)], "S3": [("A", 0.5), ("X", 0.5)],
                 "S4": [("B", 0.2), ("C", 0.2), ("A", 0.3), ("X", 0.3)]}
        tabla = {s: {"tipo": "partida", "pesos": p} for s, p in casos.items()}
        mapa = pd.DataFrame({"section": list(comp), "district": [str(d) for d in comp.values()]})
        votos = pd.DataFrame({"section": list(casos), "party": list(casos), "votes": [1, 1, 1, 1]})
        out, _ = m07.apply_section_equivalence(votos, mapa, section_field="section", district_field="district",
                                               table=tabla)
        m07_destino = dict(zip(out["party"], out["section"]))  # cada caso lleva su propio «partido»
        for s in casos:
            self.assertEqual(rp.destino_por_mayoria(tabla[s], comp) or s, m07_destino[s], s)
        self.assertEqual(rp.destino_por_mayoria(tabla["S1"], comp), "A")

    def test_tabla_versionada_y_regla_igual_a_m07(self):
        tabla = rp.leer_equivalencia_mayoria()
        self.assertGreater(len(tabla), 1000)
        comp = {"T1": 1, "T2": 2, "T3": 2}
        for pesos, esperado in (([("T1", 0.4), ("T2", 0.3), ("T3", 0.3)], "T2"), ([("T1", 0.5), ("X", 0.5)], "T1"),
                                ([("T1", 0.2), ("X", 0.8)], None)):
            self.assertEqual(rp.destino_por_mayoria({"tipo": "partida", "pesos": pesos}, comp), esperado)


class Mantenimiento(unittest.TestCase):
    def test_entrada_eleccion_por_defecto_2023_y_se_pasa_a_las_dos_herramientas(self):
        import yaml
        wf = yaml.safe_load((ROOT / ".github/workflows/mantenimiento-programado.yml").read_text(encoding="utf-8"))
        entradas = wf[True]["workflow_dispatch"]["inputs"] if True in wf else wf["on"]["workflow_dispatch"]["inputs"]
        self.assertEqual(entradas["eleccion"]["default"], "2023-07-23")
        job = wf["jobs"]["extraer_m06"]
        self.assertEqual(job["env"]["ELECCION"], "${{ inputs.eleccion || '2023-07-23' }}")
        run = "\n".join(st.get("run", "") for st in job["steps"])
        self.assertIn('python herramientas/resultados_ligeros.py --eleccion "$ELECCION"', run)
        self.assertIn('python herramientas/resultados_partidos.py --fecha "$ELECCION"', run)


if __name__ == "__main__":
    unittest.main()
