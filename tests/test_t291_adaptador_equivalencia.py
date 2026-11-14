"""T-291 · el adaptador común declara en el contrato la tabla de equivalencia de seccionados (D-65)."""
from __future__ import annotations

import csv
import hashlib
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("ddd_minsait_csv_t291", ROOT / "herramientas/adaptador_minsait_csv.py")
adapter = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(adapter)

TABLA = "configuracion/equivalencia_seccionado_ine_2026_a_2025.csv"


def _build(root: Path, **extra) -> dict:
    source = root / "source.csv"
    with source.open("w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["codigo_ccaa", "codigo_provincia", "codigo_municipio", "codigo_distrito",
                    "codigo_seccion", "codigo_mesa", "partido", "votos"])
        w.writerow(["16", "20", "69", "1", "1", "A", "P1", "7"])
    out = root / "package"
    adapter.build(source, out, territory_id="congreso_guipuzcoa", election_id="congreso_guipuzcoa_2026-11-29",
                  election_date="2026-11-29", edition="2023", expected_sha256=adapter.sha256(source),
                  expected_ccaa="16", expected_provinces=1, expected_sections=1, expected_polling_stations=1,
                  expected_candidate_votes=7, source_url="https://example.invalid/s.csv", publisher="Minsait", **extra)
    return json.loads((out / "contract/election_contract.json").read_text(encoding="utf-8"))


class AdaptadorEquivalencia(unittest.TestCase):
    def test_declara_la_tabla_con_su_huella(self):
        with tempfile.TemporaryDirectory() as td:
            contract = _build(Path(td), section_equivalence=Path(TABLA))
        record = contract["section_reconciliation"]["equivalence_table"]
        self.assertEqual(record, {
            "path": TABLA,
            "sha256": hashlib.sha256((ROOT / TABLA).read_bytes()).hexdigest(),
            "source_column": "seccion_2026",
            "target_column": "seccion_2025",
            "decision": "D-65",
        })

    def test_sin_argumento_el_contrato_no_cambia(self):
        with tempfile.TemporaryDirectory() as td:
            contract = _build(Path(td))
        self.assertNotIn("section_reconciliation", contract)

    def test_tabla_fuera_del_repositorio_bloquea(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "eq.csv"
            p.write_text("a,b,tipo,peso_poblacion\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "versionada en el repositorio"):
                adapter.section_equivalence_record(p)

    def test_tabla_sin_columnas_bloquea(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "eq.csv").write_text("a,b\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "sin columnas"):
                adapter.section_equivalence_record(Path("eq.csv"), root=root)


if __name__ == "__main__":
    unittest.main()
