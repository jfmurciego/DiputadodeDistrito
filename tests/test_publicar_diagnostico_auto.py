"""Versión 1.0.0; 2026-11-01; candidato. T-14: empaquetado y publicación del diagnóstico automático."""
from __future__ import annotations

import gzip
import subprocess
import tempfile
import unittest
from pathlib import Path

from herramientas import publicar_diagnostico_auto as pda

ROOT = Path(__file__).resolve().parents[1]
WF = ROOT / ".github/workflows/_reutilizable-generacion-territorial.yml"


class PublicarDiagnosticoAutoTests(unittest.TestCase):
    def _cache(self, td: Path) -> Path:
        c = td / "cache" / "x"
        c.mkdir(parents=True)
        (c / "t_2025_m01_secciones_poblacion.geojson.zip").write_bytes(b"zip")
        (c / "t_2025_m03_grafo.json").write_text('{"a": 1}')
        (c / "t_2025_m05_informe.json").write_text('{"status": "FAIL"}')
        return td / "cache"

    def test_territory_of(self):
        self.assertEqual(pda.territory_of("territorios/congreso_huesca/config/congreso_huesca_2025.yaml"), "congreso_huesca")

    def test_collect_gzips_graph_and_keeps_three_files(self):
        with tempfile.TemporaryDirectory() as t:
            td = Path(t)
            out = pda.collect(self._cache(td), td / "out")
            self.assertEqual(sorted(p.name for p in out), [
                "t_2025_m01_secciones_poblacion.geojson.zip", "t_2025_m03_grafo.json.gz", "t_2025_m05_informe.json"])
            self.assertEqual(gzip.open(td / "out/t_2025_m03_grafo.json.gz").read(), b'{"a": 1}')

    def test_collect_rejects_oversize(self):
        with tempfile.TemporaryDirectory() as t:
            td = Path(t)
            cache = self._cache(td)
            old = pda.MAX_BYTES
            pda.MAX_BYTES = 2
            try:
                with self.assertRaises(RuntimeError):
                    pda.collect(cache, td / "out")
            finally:
                pda.MAX_BYTES = old
            self.assertEqual(list((td / "out").iterdir()), [])

    def test_publish_pushes_to_branch_layout(self):
        # Remoto local simulado con repositorio bare; el token no se usa con file://.
        with tempfile.TemporaryDirectory() as t:
            td = Path(t)
            bare = td / "r.git"
            subprocess.run(["git", "init", "-q", "--bare", str(bare)], check=True)
            files = pda.collect(self._cache(td), td / "out")
            orig = pda.publish.__globals__["subprocess"].run
            # Redirige la URL https a la bare local sustituyendo el remoto.
            def fake(cmd, *a, **k):
                cmd = [str(bare) if (isinstance(x, str) and x.startswith("https://github.com/")) else x for x in cmd]
                return orig(cmd, *a, **k)
            pda.subprocess.run = fake
            try:
                pda.publish(files, "t", "123", "o/r", "diagnostico/auto", "tok")
            finally:
                pda.subprocess.run = orig
            ls = subprocess.run(["git", "ls-tree", "-r", "--name-only", "diagnostico/auto"], cwd=bare,
                                capture_output=True, text=True).stdout.split()
            self.assertIn("t/123/t_2025_m03_grafo.json.gz", ls)
            self.assertIn("t/123/ORIGEN.txt", ls)

    def test_workflow_wires_failure_steps_only(self):
        text = WF.read_text(encoding="utf-8")
        self.assertIn("herramientas/publicar_diagnostico_auto.py", text)
        self.assertGreaterEqual(text.count("Publicar diagnóstico automático"), 2)
        for block in text.split("- name: Publicar diagnóstico automático")[1:]:
            self.assertIn("if: ${{ failure()", block.split("run:")[0])


if __name__ == "__main__":
    unittest.main()
