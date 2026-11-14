"""T-291 · M07 consume la equivalencia de seccionados 2026→2023 (D-65) con todas sus clases."""
from __future__ import annotations

import csv
import hashlib
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "modulos/07_agregar_resultados_electorales.py"
spec = importlib.util.spec_from_file_location("m07_t291", MODULE)
m07 = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(m07)

TABLA = ROOT / "configuracion/equivalencia_seccionado_ine_2026_a_2023.csv"
META = ROOT / "configuracion/equivalencia_seccionado_ine_2026_a_2023.json"

CSV_LITERAL = (
    "seccion_2026,seccion_2023,tipo,peso_area,peso_poblacion\n"
    "A,T1,partida,0.700000,0.750000\n"
    "A,T2,partida,0.300000,0.250000\n"
    "B,T1,contenida,1.000000,1.000000\n"
    "U,T3,1:1,1.000000,1.000000\n"
    "S,,sin_vigente,,\n"
)


def _tabla(tmp: Path, texto: str = CSV_LITERAL) -> tuple[dict, dict]:
    p = tmp / "eq.csv"
    p.write_text(texto, encoding="utf-8")
    record = {"path": str(p), "sha256": hashlib.sha256(texto.encode()).hexdigest(),
              "source_column": "seccion_2026", "target_column": "seccion_2023"}
    return m07.load_section_equivalence(record, project_root=tmp)


class EquivalenciaM07(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)
        self.mapa = pd.DataFrame({"section": ["T1", "T2", "T3", "C"], "district": ["D1", "D2", "D2", "D1"]})

    def tearDown(self):
        self.tmp.cleanup()

    def test_todas_las_clases_con_literal(self):
        tabla, _ = _tabla(self.dir)
        votos = pd.DataFrame({
            "section": ["A", "A", "B", "U", "C", "S"],
            "party": ["P", "Q", "P", "P", "P", "P"],
            "votes": [10, 3, 5, 4, 6, 2],
        })
        out, ev = m07.apply_section_equivalence(votos, self.mapa, section_field="section",
                                                district_field="district", table=tabla)
        got = {(r["section"], r["party"]): r["votes"] for r in out.to_dict("records")}
        # P de A: 7,5/2,5 → empate de restos, gana T1 por orden: 8/2. Q de A: 2,25/0,75 → 2/1.
        self.assertEqual(got, {("T1", "P"): 8 + 5, ("T2", "P"): 2, ("T1", "Q"): 2, ("T2", "Q"): 1,
                               ("T3", "P"): 4, ("C", "P"): 6, ("S", "P"): 2})
        self.assertEqual(ev["votes_before"], 30)
        self.assertEqual(ev["votes_after"], 30)
        self.assertEqual(ev["by_class"]["partida"], {"sections": 1, "votes": 13})
        self.assertEqual(ev["by_class"]["contenida"], {"sections": 1, "votes": 5})
        self.assertEqual(ev["by_class"]["1:1"], {"sections": 1, "votes": 4})
        self.assertEqual(ev["by_class"]["sin_vigente"], {"sections": 1, "votes": 2})
        self.assertEqual(ev["votes_split_across_districts"], 13)
        self.assertEqual(ev["sections_split_across_districts"], ["A"])

    def test_cusec_conservado_con_limite_cambiado_se_reasigna(self):
        # La sección 2026 «T1» conserva el código pero su territorio cae en T2: la tabla manda.
        texto = "seccion_2026,seccion_2023,tipo,peso_area,peso_poblacion\nT1,T2,contenida,1,1\n"
        tabla, _ = _tabla(self.dir, texto)
        votos = pd.DataFrame({"section": ["T1", "T2"], "party": ["P", "P"], "votes": [5, 1]})
        out, _ = m07.apply_section_equivalence(votos, self.mapa, section_field="section",
                                               district_field="district", table=tabla)
        self.assertEqual(out.to_dict("records"), [{"section": "T2", "party": "P", "votes": 6}])

    def test_destino_ausente_del_mapa_se_informa_y_se_renormaliza(self):
        texto = ("seccion_2026,seccion_2023,tipo,peso_area,peso_poblacion\n"
                 "A,T1,partida,0.5,0.5\nA,X9,partida,0.5,0.5\n")
        tabla, _ = _tabla(self.dir, texto)
        votos = pd.DataFrame({"section": ["A"], "party": ["P"], "votes": [7]})
        out, ev = m07.apply_section_equivalence(votos, self.mapa, section_field="section",
                                                district_field="district", table=tabla)
        self.assertEqual(out.to_dict("records"), [{"section": "T1", "party": "P", "votes": 7}])
        self.assertEqual(ev["targets_missing_in_map"], [{"source": "A", "missing": ["X9"]}])

    def test_huella_incorrecta_bloquea(self):
        p = self.dir / "eq.csv"
        p.write_text(CSV_LITERAL, encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "SECTION_EQUIVALENCE_SHA256_MISMATCH"):
            m07.load_section_equivalence({"path": str(p), "sha256": "0" * 64, "source_column": "seccion_2026",
                                          "target_column": "seccion_2023"}, project_root=self.dir)

    def test_contenida_con_dos_destinos_bloquea(self):
        texto = ("seccion_2026,seccion_2023,tipo,peso_area,peso_poblacion\n"
                 "B,T1,contenida,1,0.5\nB,T2,contenida,1,0.5\n")
        with self.assertRaisesRegex(ValueError, "SECTION_EQUIVALENCE_EXACT_NOT_UNIQUE"):
            _tabla(self.dir, texto)


class TablaVersionada(unittest.TestCase):
    def test_huella_y_clases_de_la_tabla_2026_2023(self):
        meta = json.loads(META.read_text(encoding="utf-8"))
        self.assertEqual(hashlib.sha256(TABLA.read_bytes()).hexdigest(), meta["csv"]["sha256"])
        self.assertEqual(meta["fuentes"]["seccionado_2023"]["sha256"],
                         "7a15e700a4592d793230441cfcb4b72e40979998aef019ca644389271886bf1f")
        self.assertEqual(meta["fuentes"]["padron_65034"]["periodo"], "2023")
        tabla, _ = m07.load_section_equivalence(
            {"path": "configuracion/equivalencia_seccionado_ine_2026_a_2023.csv", "sha256": meta["csv"]["sha256"],
             "source_column": "seccion_2026", "target_column": "seccion_2023"}, project_root=ROOT)
        for s, e in tabla.items():
            if e["tipo"] == "partida":
                self.assertAlmostEqual(sum(w for _, w in e["pesos"]), 1.0, places=4, msg=s)
            for t, _ in e["pesos"]:
                self.assertEqual(t[:2], s[:2], f"{s} → {t} cambia de provincia")
        with TABLA.open(encoding="utf-8") as fh:
            tipos = {r["tipo"] for r in csv.DictReader(fh)}
        self.assertLessEqual(tipos, set(m07.EQUIVALENCE_CLASSES))
        # Ceuta y Melilla (distrito único) tienen secciones en la tabla: deben quedar al 0 % sin asignar.
        self.assertTrue(any(s.startswith("51") for s in tabla))
        self.assertTrue(any(s.startswith("52") for s in tabla))


if __name__ == "__main__":
    unittest.main()
