"""Integración ligera del encadenamiento modular sin datos territoriales."""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]


class ModularChainIntegrationTests(unittest.TestCase):
    def fixture(self, raw: str) -> tuple[Path, Path, Path]:
        root = Path(raw)
        shutil.copy2(ROOT / "procedimiento.sh", root / "procedimiento.sh")
        (root / "modulos").mkdir()
        (root / "herramientas").mkdir()
        shutil.copy2(ROOT / "herramientas/validar_fuentes_reanudacion.py", root / "herramientas/validar_fuentes_reanudacion.py")
        shutil.copy2(ROOT / "herramientas/politica_reutilizacion_fuentes.py", root / "herramientas/politica_reutilizacion_fuentes.py")
        for stage in range(1, 9):
            script = root / "modulos" / {
                1: "01_preparar_base_territorial.py",
                2: "02_construir_adyacencias.py",
                3: "03_construir_grafo.py",
                4: "04_generar_semillas.py",
                5: "05_optimizar_distritos.py",
                6: "06_consolidar_distritos.py",
                7: "07_agregar_resultados_electorales.py",
                8: "08_integrar_resultados.py",
            }[stage]
            script.write_text(
                "import argparse\n"
                "p=argparse.ArgumentParser(); p.add_argument('--params'); p.parse_args()\n",
                encoding="utf-8",
            )
        (root / "herramientas/registrar_ejecucion.py").write_text(
            "import argparse\n"
            "p=argparse.ArgumentParser(); p.add_argument('--params'); p.add_argument('--phase'); p.add_argument('--run-id'); p.parse_args()\n",
            encoding="utf-8",
        )
        (root / "herramientas/validar_ejecucion.py").write_text(
            "import argparse\n"
            "p=argparse.ArgumentParser(); p.add_argument('--params'); p.add_argument('--run-id'); p.parse_args()\n",
            encoding="utf-8",
        )
        params = root / "territory.yaml"
        params.write_text(yaml.safe_dump({
            "meta": {"run_name": "synthetic", "year": 2025, "territory_id": "synthetic"},
            "io": {
                "cache": {"dir": str(root / "cache")},
                "runs": {"dir": str(root / "runs/{run_id}")},
            },
        }), encoding="utf-8")

        declaration = root / "territorios/synthetic/config/fuentes_oficiales.yaml"
        declaration.parent.mkdir(parents=True)
        declaration.write_text(yaml.safe_dump({
            "territory": {"id": "synthetic", "edition": 2025},
            "coverage_checks": {"expected_sections": 1},
        }), encoding="utf-8")
        package = root / ".ddd-source-package"
        frozen = package / "frozen/source.csv"
        frozen.parent.mkdir(parents=True)
        payload = b"id,value\n1,x\n"
        frozen.write_bytes(payload)
        (package / "manifest.json").write_text(json.dumps({
            "source_id": "synthetic-official",
            "edition": 2025,
            "origin": "https://official.example/source.csv",
            "path": "frozen/source.csv",
            "bytes": len(payload),
            "sha256": hashlib.sha256(payload).hexdigest(),
            "records": 1,
            "acquired_at": "2026-09-17T19:00:00Z",
        }), encoding="utf-8")
        return root, params, root / "chain.json"

    def run_stage(self, root: Path, params: Path, chain: Path, stage: str) -> subprocess.CompletedProcess[str]:
        env = os.environ.copy()
        env.update({
            "DDD_PARAMS": str(params),
            "DDD_RUN_ID": "synthetic-run",
            "DDD_FROM_STAGE": stage,
            "DDD_TO_STAGE": stage,
            "DDD_CHAIN_STATE": str(chain),
        })
        return subprocess.run(
            ["bash", "procedimiento.sh"], cwd=root, env=env,
            text=True, capture_output=True, check=False,
        )

    def test_m01_y_m02_encadenan_estado(self):
        with tempfile.TemporaryDirectory() as raw:
            root, params, chain = self.fixture(raw)
            first = self.run_stage(root, params, chain, "M01")
            self.assertEqual(first.returncode, 0, first.stderr)
            self.assertEqual(json.loads(chain.read_text(encoding="utf-8"))["completed_stage"], 1)
            second = self.run_stage(root, params, chain, "M02")
            self.assertEqual(second.returncode, 0, second.stderr)
            self.assertEqual(json.loads(chain.read_text(encoding="utf-8"))["completed_stage"], 2)
            evidence = json.loads((root / ".ddd-source-package/source_execution.json").read_text(encoding="utf-8"))
            self.assertEqual(evidence["decision"], "REUSE")

    def test_rechaza_checkpoint_de_otro_contrato(self):
        with tempfile.TemporaryDirectory() as raw:
            root, params, chain = self.fixture(raw)
            chain.write_text(json.dumps({"params": "otro.yaml", "completed_stage": 1}), encoding="utf-8")
            result = self.run_stage(root, params, chain, "M02")
            self.assertEqual(result.returncode, 1)
            self.assertIn("pertenece a otro contrato", result.stderr)


if __name__ == "__main__":
    unittest.main()
