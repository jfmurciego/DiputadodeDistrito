from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]

class PromotionMustNotMutateWorkflowTests(unittest.TestCase):
    def test_promoters_do_not_reference_workflow_files_as_mutation_targets(self):
        paths = [
            ROOT / "herramientas/promover_catalogo_operacional.py",
            ROOT / "herramientas/promover_catalogo_tras_preparacion.py",
            ROOT / ".github/workflows/_reutilizable-operacion-territorial.yml",
            ROOT / ".github/workflows/preparacion-resultados-electorales.yml",
            ROOT / ".github/workflows/preparacion-fuentes.yml",
        ]
        forbidden = (
            ".github/workflows/incorporacion-resultados-electorales.yml",
            ".github/workflows/produccion-distritos.yml",
            "DDD_WORKFLOW_TOKEN",
        )
        for path in paths:
            text = path.read_text(encoding="utf-8")
            for token in forbidden:
                self.assertNotIn(token, text, f"{path}: token prohibido {token}")

if __name__ == "__main__":
    unittest.main()
