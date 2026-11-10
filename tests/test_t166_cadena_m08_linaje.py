"""Versión 1.0.0; 2026-11-10; candidato. T-166: la 00 no encadena la hija «Reutilizar» si no podría planificar.
Cambios: fichero nuevo.
Anterior: ninguna (fichero nuevo)

Casos reales (fixtures congeladas con el catálogo y las evidencias del commit de cada run hija, sin artefactos):
  42651881625 y 42720255020 (Cantabria), 42737598841 (Extremadura): Planificar falló con
  `CONTINUE_DURABLE_BLOCK ... DURABLE_LINEAGE_INCOMPATIBLE: electoral_product` porque el catálogo conserva el M08 de una
  04 fallida (manifiesto sin digest de la fase 04).
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import yaml

from herramientas.resolver_ejecucion_completa import build_plan, chain_block_reason

ROOT = Path(__file__).resolve().parents[1]
FX = ROOT / "tests/fixtures/t166_encadenado_m08"
ORCH = ROOT / ".github/workflows/ejecucion-completa-proyecto.yml"
CASOS = {
    "cantabria_42651881625": "Cantabria",
    "cantabria_42720255020": "Cantabria",
    "extremadura_42737598841": "Extremadura",
}
CATALOGO = "configuracion/catalogo_preparacion.yaml"


class ChainGuardTests(unittest.TestCase):
    def test_los_tres_runs_hija_no_pueden_planificar_y_la_guarda_lo_detecta(self):
        for caso, territorio in CASOS.items():
            with self.subTest(caso=caso):
                root = FX / caso
                with self.assertRaisesRegex(ValueError, "DURABLE_LINEAGE_INCOMPATIBLE: electoral_product"):
                    build_plan(territory=territorio, edition="2025", execution_mode="reuse",
                               catalog=root / CATALOGO, root_dir=root)
                motivo = chain_block_reason(territory=territorio, edition="2025", catalog=root / CATALOGO, root_dir=root)
                self.assertIn("DURABLE_LINEAGE_INCOMPATIBLE: electoral_product", motivo or "")

    def test_cli_check_chain_dice_no_encadenar(self):
        for caso, territorio in CASOS.items():
            with self.subTest(caso=caso):
                out = subprocess.run(
                    [sys.executable, "-m", "herramientas.resolver_ejecucion_completa", "--territory", territorio,
                     "--edition", "2025", "--execution-mode", "reuse", "--check-chain", "--root-dir", str(FX / caso)],
                    cwd=ROOT, capture_output=True, text=True, check=True).stdout
                res = json.loads(out)
                self.assertFalse(res["chain"])
                self.assertIn("electoral_product", res["reason"])

    def test_sin_m08_en_catalogo_se_sigue_encadenando(self):
        # Sin producto electoral registrado (caso normal del encadenado) la guarda no bloquea.
        for caso, territorio in CASOS.items():
            with self.subTest(caso=caso), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp) / "raiz"
                shutil.copytree(FX / caso, root)
                cat = yaml.safe_load((root / CATALOGO).read_text(encoding="utf-8"))
                ed = cat["territories"][0]["editions"]["2025"]
                ed["electoral_product_available"] = False
                ed.get("evidence", {}).pop("electoral_product", None)
                (root / CATALOGO).write_text(yaml.safe_dump(cat, allow_unicode=True, sort_keys=False), encoding="utf-8")
                self.assertIsNone(chain_block_reason(territory=territorio, edition="2025",
                                                     catalog=root / CATALOGO, root_dir=root))

    def test_otros_errores_no_los_traga_la_guarda(self):
        # Territorio inexistente: error distinto, la hija lo informaría; la guarda no inventa un bloqueo.
        root = FX / "cantabria_42720255020"
        self.assertIsNone(chain_block_reason(territory="Atlantida", edition="2025", catalog=root / CATALOGO, root_dir=root))


class WorkflowTests(unittest.TestCase):
    def test_la_guarda_va_antes_de_activar_el_par_y_condiciona_el_dispatch(self):
        job = yaml.safe_load(ORCH.read_text(encoding="utf-8"))["jobs"]["encadenar_par_y_04"]
        nombres = [s.get("name", s.get("uses", "")) for s in job["steps"]]
        guarda = next(i for i, s in enumerate(job["steps"]) if s.get("id") == "guarda")
        activar = next(i for i, s in enumerate(job["steps"]) if s.get("name", "").startswith("Activar par"))
        self.assertLess(guarda, activar, nombres)
        self.assertIn("--check-chain", job["steps"][guarda]["run"])
        self.assertIn("steps.guarda.outputs.chain == 'true'", job["steps"][activar]["if"])
        self.assertTrue(any(str(s.get("uses", "")).startswith("actions/checkout@") for s in job["steps"][:guarda]))


if __name__ == "__main__":
    unittest.main()
