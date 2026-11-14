"""Versión 1.1.0; 2026-11-02; candidato. T-14/T-16: empaquetado y publicación del diagnóstico automático.
Cambios: linaje por rutas del contrato, PARTIAL, manifiesto con hashes, rebase y DIAG_PUBLISH_FAILED.
Anterior: legacy/tests/test_publicar_diagnostico_auto_v1.0.0_20261102.py
"""
from __future__ import annotations

import contextlib
import gzip
import hashlib
import io
import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import yaml

from herramientas import publicar_diagnostico_auto as pda

ROOT = Path(__file__).resolve().parents[1]
WF = ROOT / ".github/workflows/_reutilizable-generacion-territorial.yml"


def _contract(td: Path, run_name="t_2025") -> tuple[Path, Path]:
    cache = td / "cache" / run_name
    cache.mkdir(parents=True)
    cfg = {"meta": {"run_name": run_name, "year": 2025}, "modulos": {
        "modulo_01_preparar_base_territorial": {"out_geojson": f"{cache}/{{run_name}}_m01_secciones_poblacion.geojson.zip"},
        "modulo_03_construir_grafo": {"out_graph_json": f"{cache}/{{run_name}}_m03_grafo.json"},
        "modulo_05_optimizar_distritos": {"out_report": f"{cache}/{{run_name}}_m05_informe.json"}}}
    p = td / "t_2025.yaml"
    p.write_text(yaml.safe_dump(cfg), encoding="utf-8")
    return p, cache


def _fill(cache: Path, run_name="t_2025", skip=()):
    files = {"m01": (f"{run_name}_m01_secciones_poblacion.geojson.zip", b"zip"),
             "m03": (f"{run_name}_m03_grafo.json", b'{"a": 1}'),
             "m05": (f"{run_name}_m05_informe.json", b'{"status": "FAIL"}')}
    for k, (n, b) in files.items():
        if k not in skip:
            (cache / n).write_bytes(b)


class PublicarDiagnosticoAutoTests(unittest.TestCase):
    def test_territory_of(self):
        self.assertEqual(pda.territory_of("territorios/nac22/config/nac22_2025.yaml"), "nac22")

    def test_collect_uses_declared_paths_not_mtime(self):
        # T14-01: un fichero más nuevo de otra ejecución en la misma carpeta no se elige.
        with tempfile.TemporaryDirectory() as t:
            td = Path(t)
            params, cache = _contract(td)
            _fill(cache)
            (cache / "otro_m03_grafo.json").write_text('{"otro": 1}')
            out = pda.collect(pda.declared_paths(str(params), "9"), td / "out")
            self.assertEqual(gzip.open(td / "out/t_2025_m03_grafo.json.gz").read(), b'{"a": 1}')
            self.assertEqual(sorted(p.name for p in out), [
                "MANIFEST.json", "t_2025_m01_secciones_poblacion.geojson.zip", "t_2025_m03_grafo.json.gz", "t_2025_m05_informe.json"])

    def test_manifest_has_hashes_and_lineage(self):
        # T14-03
        with tempfile.TemporaryDirectory() as t:
            td = Path(t)
            params, cache = _contract(td)
            _fill(cache)
            pda.collect(pda.declared_paths(str(params), "9"), td / "out", meta={"run_id": "9", "checkpoint_run_id": "7", "stage": "M05"})
            m = json.loads((td / "out/MANIFEST.json").read_text())
            self.assertEqual((m["status"], m["run_id"], m["checkpoint_run_id"], m["stage"]), ("COMPLETE", "9", "7", "M05"))
            for e in m["files"]:
                self.assertEqual(e["sha256"], hashlib.sha256((td / "out" / e["file"]).read_bytes()).hexdigest())

    def test_missing_file_marks_partial(self):
        # T14-02
        with tempfile.TemporaryDirectory() as t:
            td = Path(t)
            params, cache = _contract(td)
            _fill(cache, skip=("m05",))
            with contextlib.redirect_stdout(io.StringIO()):
                pda.collect(pda.declared_paths(str(params), "9"), td / "out")
            m = json.loads((td / "out/MANIFEST.json").read_text())
            self.assertEqual((m["status"], m["missing"]), ("PARTIAL", ["m05"]))

    def test_collect_rejects_oversize(self):
        with tempfile.TemporaryDirectory() as t:
            td = Path(t)
            params, cache = _contract(td)
            _fill(cache)
            with mock.patch.object(pda, "MAX_BYTES", 2):
                with self.assertRaises(RuntimeError):
                    pda.collect(pda.declared_paths(str(params), "9"), td / "out")
            self.assertEqual(list((td / "out").iterdir()), [])

    def _publish_to_bare(self, td: Path, bare: Path, files, run_id="123"):
        orig = subprocess.run

        def fake(cmd, *a, **k):
            cmd = [str(bare) if (isinstance(x, str) and x.startswith("https://github.com/")) else x for x in cmd]
            return orig(cmd, *a, **k)
        with mock.patch.object(pda.subprocess, "run", fake):
            pda.publish(files, "t", run_id, "o/r", "diagnostico/auto", "tok")

    def test_publish_pushes_to_branch_layout(self):
        with tempfile.TemporaryDirectory() as t:
            td = Path(t)
            bare = td / "r.git"
            subprocess.run(["git", "init", "-q", "--bare", str(bare)], check=True)
            params, cache = _contract(td)
            _fill(cache)
            files = pda.collect(pda.declared_paths(str(params), "123"), td / "out")
            self._publish_to_bare(td, bare, files)
            ls = subprocess.run(["git", "ls-tree", "-r", "--name-only", "diagnostico/auto"], cwd=bare,
                                capture_output=True, text=True).stdout.split()
            self.assertIn("t/123/t_2025_m03_grafo.json.gz", ls)
            self.assertIn("t/123/MANIFEST.json", ls)
            msg = subprocess.run(["git", "log", "-1", "--format=%s", "diagnostico/auto"], cwd=bare, capture_output=True, text=True).stdout
            self.assertIn("COMPLETE", msg)

    def test_rebase_failure_is_reported(self):
        # T14-04: un rebase que falla no se ignora ni se reintenta a ciegas.
        real = subprocess.run

        def fake(cmd, *a, **k):
            if cmd[:2] == ["git", "rebase"] and "--abort" not in cmd:
                return subprocess.CompletedProcess(cmd, 1, "", "conflicto")
            return real(cmd, *a, **k)
        with tempfile.TemporaryDirectory() as t:
            td = Path(t)
            bare = td / "r.git"
            subprocess.run(["git", "init", "-q", "--bare", str(bare)], check=True)
            params, cache = _contract(td)
            _fill(cache)
            files = pda.collect(pda.declared_paths(str(params), "1"), td / "out")
            real_git = pda._git
            calls = {"push": 0}

            def git(args, cwd, token):
                if args[0] == "push":
                    calls["push"] += 1
                    return subprocess.CompletedProcess(args, 1, "", "rechazado")
                return subprocess.CompletedProcess(args, 0, "", "") if args[0] == "fetch" and calls["push"] else real_git(args, cwd, token)
            with mock.patch.object(pda, "_git", git), mock.patch.object(pda.subprocess, "run", fake):
                with self.assertRaisesRegex(RuntimeError, "rebase fallido"):
                    pda.publish(files, "t", "1", "o/r", "diagnostico/auto", "tok")

    def test_publish_failure_is_visible_and_not_fatal(self):
        # T14-05
        with tempfile.TemporaryDirectory() as t:
            td = Path(t)
            params, cache = _contract(td)
            _fill(cache)
            summary = td / "summary.md"
            buf = io.StringIO()
            with mock.patch.object(pda, "publish", side_effect=RuntimeError("push fallido")), \
                 mock.patch.dict("os.environ", {"GITHUB_STEP_SUMMARY": str(summary)}), \
                 mock.patch("sys.argv", ["x", "--params", str(params), "--run-id", "5"]), \
                 contextlib.redirect_stdout(buf):
                self.assertEqual(pda.main(), 0)
            self.assertIn("::error title=DIAG_PUBLISH_FAILED::", buf.getvalue())
            self.assertIn("DIAG_PUBLISH_FAILED", summary.read_text())

    def test_workflow_wires_failure_steps_only(self):
        text = WF.read_text(encoding="utf-8")
        self.assertIn("herramientas/publicar_diagnostico_auto.py", text)
        self.assertGreaterEqual(text.count("Publicar diagnóstico automático"), 2)
        for block in text.split("- name: Publicar diagnóstico automático")[1:]:
            head = block.split("run:")[0]
            self.assertIn("if: ${{ failure()", head)
            self.assertIn("--checkpoint-run-id", block[:900])


if __name__ == "__main__":
    unittest.main()
