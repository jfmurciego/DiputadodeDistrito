from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
WF = ROOT / ".github" / "workflows"
FULL = WF / "ejecucion-completa-proyecto.yml"


def load(path: Path) -> dict:
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return data


class FullRunSourceShaPinningTests(unittest.TestCase):
    def test_00_pins_checkout_sha_and_propagates_it_to_validation_and_business_reusables(self):
        text = FULL.read_text(encoding="utf-8")
        full = load(FULL)
        jobs = full["jobs"]

        outputs = jobs["planificar"]["outputs"]
        self.assertEqual(outputs["source_sha"], "${{ steps.plan.outputs.source_sha }}")
        self.assertEqual(outputs["source_ref"], "${{ steps.plan.outputs.source_sha }}")
        self.assertIn('source_sha="$(git rev-parse HEAD)"', text)
        self.assertIn('echo "source_sha=$source_sha"', text)
        self.assertIn('echo "source_ref=$source_sha"', text)

        for name in (
            "preparar_territorial",
            "puerta_01",
            "generar",
            "puerta_02",
            "preparar_electoral",
            "puerta_03",
            "incorporar",
            "puerta_04",
        ):
            with self.subTest(job=name):
                self.assertEqual(
                    jobs[name]["with"]["source_ref"],
                    "${{ needs.planificar.outputs.source_sha }}",
                )

        self.assertNotIn(
            "pre_m04_accreditation_planned == 'true' && 'main'",
            jobs["generar"]["with"]["source_ref"],
        )
        self.assertIn(
            '--source-sha "${{ needs.planificar.outputs.source_sha }}"',
            jobs["manifestar"]["steps"][2]["run"],
        )

        for name in ("campaign_status", "manifestar"):
            checkout = next(
                step for step in jobs[name]["steps"]
                if str(step.get("uses", "")).startswith("actions/checkout@")
            )
            self.assertEqual(
                checkout["with"]["ref"],
                "${{ needs.planificar.outputs.source_sha }}",
            )

        # El estado operativo compartido es una escritura deliberada contra main;
        # no participa en las puertas que validan código/contratos del run.
        state_checkout = next(
            step for step in jobs["actualizar_estado"]["steps"]
            if str(step.get("uses", "")).startswith("actions/checkout@")
        )
        self.assertIn("'main'", state_checkout["with"]["ref"])
        self.assertIn("needs.planificar.outputs.source_sha", state_checkout["with"]["ref"])

    def test_nested_reusables_receive_the_same_pinned_ref(self):
        production = load(WF / "produccion-distritos.yml")
        incorporation = load(WF / "incorporacion-resultados-electorales.yml")
        preparation = load(WF / "preparacion-fuentes.yml")
        gate = load(WF / "_reutilizable-puerta-validacion.yml")

        self.assertEqual(
            production["jobs"]["ruta"]["with"]["source_ref"],
            "${{ inputs.source_ref }}",
        )
        self.assertEqual(
            incorporation["jobs"]["incorporar"]["with"]["source_ref"],
            "${{ inputs.source_ref }}",
        )
        self.assertEqual(
            preparation["jobs"]["pre_m04"]["with"]["source_ref"],
            "${{ inputs.source_ref || github.sha }}",
        )

        gate_checkout = next(
            step for step in gate["jobs"]["validar"]["steps"]
            if str(step.get("uses", "")).startswith("actions/checkout@")
        )
        self.assertEqual(
            gate_checkout["with"]["ref"],
            "${{ inputs.source_ref || github.sha }}",
        )

    def test_advancing_main_does_not_change_a_checkout_pinned_to_the_initial_sha(self):
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)

            def git(*args: str) -> str:
                completed = subprocess.run(
                    ["git", *args],
                    cwd=repo,
                    text=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    check=True,
                )
                return completed.stdout.strip()

            git("init", "-b", "main")
            git("config", "user.name", "DDD Test")
            git("config", "user.email", "ddd-test@example.invalid")

            contract = repo / "contract.txt"
            contract.write_text("contract-A\n", encoding="utf-8")
            git("add", "contract.txt")
            git("commit", "-m", "A")
            source_sha = git("rev-parse", "HEAD")

            contract.write_text("contract-B\n", encoding="utf-8")
            git("add", "contract.txt")
            git("commit", "-m", "B")
            main_after_advance = git("rev-parse", "main")
            self.assertNotEqual(main_after_advance, source_sha)

            git("checkout", "--detach", source_sha)
            self.assertEqual(git("rev-parse", "HEAD"), source_sha)
            self.assertEqual(contract.read_text(encoding="utf-8"), "contract-A\n")
            self.assertEqual(git("rev-parse", "main"), main_after_advance)


if __name__ == "__main__":
    unittest.main()
