# -*- coding: utf-8 -*-
"""T-201b: el paso «Runs candidatos» de mantenimiento-programado.yml elige el M06 por elección.

PROYECTO: Diputado de Distrito · VERSIÓN: 1.0.0 · FECHA: 2026-11-10 · ESTADO: candidato · ANTERIOR: ninguna (fichero nuevo)
Se extrae el script Python del propio workflow y se ejecuta sobre un registro sintético (no se ejecuta el flujo).
"""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


def script() -> str:
    w = yaml.safe_load((ROOT / ".github/workflows/mantenimiento-programado.yml").read_text(encoding="utf-8"))
    for job in w["jobs"].values():
        for st in job.get("steps", []):
            r = st.get("run", "")
            if "candidatos.txt" in r and "<<'PY'" in r:
                return r.split("<<'PY'\n", 1)[1].split("\nPY", 1)[0]
    raise AssertionError("no se encontró el paso Runs candidatos")


class Candidatos(unittest.TestCase):
    def run_con(self, products, sel="todos"):
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "orchestracion").mkdir()
            (Path(d) / "orchestracion/publicaciones_visor.json").write_text(json.dumps({"products": products}))
            r = subprocess.run([sys.executable, "-c", script(), sel], cwd=d, capture_output=True, text=True, check=True)
            return r.stdout.split("\n")[:-1]

    def test_entrada_2026_con_run_mayor_no_cambia_los_candidatos_2023(self):
        p23 = [{"kind": "canonical_m06", "territory_id": "t1", "run_id": "10"},
               {"kind": "canonical_m06", "territory_id": "t2", "run_id": "7", "election_date": "2023-07-23"}]
        p26 = [{"kind": "canonical_m06", "territory_id": "t1", "run_id": "900", "election_date": "2026-11-29"},
               {"kind": "canonical_m06", "territory_id": "t3", "run_id": "901", "election_date": "2026-11-29"}]
        self.assertEqual(self.run_con(p23), ["10 t1", "7 t2"])
        self.assertEqual(self.run_con(p23 + p26), ["10 t1", "7 t2"])
        self.assertEqual(self.run_con(p23 + p26, "t1"), ["10 t1"])


if __name__ == "__main__":
    unittest.main()
