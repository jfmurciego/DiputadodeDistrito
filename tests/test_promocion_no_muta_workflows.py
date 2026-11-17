from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]

class PromotionMustNotMutateWorkflowTests(unittest.TestCase):
    def test_promoters_do_not_reference_workflow_files_as_mutation_targets(self):
        paths = [
            ROOT / "herramientas/promover_catalogo_operacional.py",
            ROOT / "herramientas/promover_catalogo_tras_preparacion.py",
            ROOT / "tests/fixtures/p10_vistas/_p12-electorales.yml",
            ROOT / "tests/fixtures/p10_vistas/_p11-territoriales.yml",
        ]
        forbidden = (
            ".github/workflows/p30-resultados-electorales.yml",
            ".github/workflows/p20-distritos.yml",
            "DDD_WORKFLOW_TOKEN",
        )
        for path in paths:
            text = path.read_text(encoding="utf-8")
            for token in forbidden:
                self.assertNotIn(token, text, f"{path}: token prohibido {token}")

if __name__ == "__main__":
    unittest.main()
