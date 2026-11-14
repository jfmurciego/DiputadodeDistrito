"""T-291 · la 03 pasa la tabla 2026→2023 al adaptador solo en las generales 2026 sobre los mapas vigentes."""
from __future__ import annotations

import re
import subprocess
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github/workflows/preparacion-resultados-electorales.yml"


def _prepare_script() -> str:
    wf = yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))
    for job in wf["jobs"].values():
        for step in job.get("steps", []):
            if step.get("id") == "prepare":
                return step["run"]
    raise AssertionError("sin paso prepare")


def _equivalence_args(election_date: str, edition: str) -> str:
    script = _prepare_script()
    inicio = script.index("equivalence_args=()")
    fin = re.compile(r"(?m)^fi$").search(script, inicio).end()
    bloque = script[inicio:fin]
    out = subprocess.run(
        ["bash", "-euo", "pipefail", "-c", bloque + '\nprintf "%s|" "${equivalence_args[@]}"'],
        cwd=ROOT, env={"PATH": "/usr/bin:/bin:/usr/local/bin", "ELECTION_DATE": election_date, "EDITION": edition},
        capture_output=True, text=True, check=True,
    )
    return out.stdout


class Paso03Equivalencia(unittest.TestCase):
    def test_generales_2026_en_mapas_vigentes(self):
        self.assertEqual(_equivalence_args("2026-11-29", "2025"),
                         "--section-equivalence|configuracion/equivalencia_seccionado_ine_2026_a_2023.csv|")

    def test_2023_no_cambia(self):
        self.assertEqual(_equivalence_args("2023-07-23", "2025"), "|")

    def test_otra_edicion_no_cambia(self):
        self.assertEqual(_equivalence_args("2026-11-29", "2026"), "|")

    def test_las_dos_ramas_del_adaptador_pasan_el_argumento(self):
        script = _prepare_script()
        self.assertEqual(script.count('"${equivalence_args[@]}"'), 2)
        for etiqueta in ("--adapter-label infoelectoral_mesas/1.0", '"${eligible_args[@]}"'):
            i = script.index(etiqueta)
            self.assertIn('"${equivalence_args[@]}"', script[i:i + 120], etiqueta)


if __name__ == "__main__":
    unittest.main()
