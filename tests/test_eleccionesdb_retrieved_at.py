from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class EleccionesDBRetrievedAtContractTests(unittest.TestCase):
    def test_snapshot_carries_upstream_artifact_created_at(self):
        builder = (ROOT / "herramientas/construir_snapshot_eleccionesdb.py").read_text(encoding="utf-8")
        workflow = (ROOT / ".github/workflows/diagnostico-eleccionesdb-grupo-a.yml").read_text(encoding="utf-8")

        self.assertIn("ap.add_argument('--retrieved-at',required=True)", builder)
        self.assertIn("'retrieved_at':str(retrieved_at).strip()", builder)
        self.assertIn("artifact_created_at.txt", workflow)
        self.assertIn("--retrieved-at \"$(cat artifact_created_at.txt)\"", workflow)
        self.assertIn("retrieved_at=snapshot_meta['retrieved_at']", workflow)

    def test_production_preparation_resolves_retrieved_at_from_verified_snapshot_metadata(self):
        workflow = (ROOT / ".github/workflows/preparacion-resultados-electorales.yml").read_text(
            encoding="utf-8"
        )
        self.assertIn(
            "retrieved_at=\"$(jq -r '.retrieved_at // empty' snapshot/ddd-eleccionesdb-snapshot.json)\"",
            workflow,
        )
        self.assertIn("retrieved_at verificable ausente o inválido", workflow)
        self.assertIn("--retrieved-at \"$retrieved_at\"", workflow)

    def test_adapter_requires_and_embeds_retrieved_at(self):
        adapter = (ROOT / "herramientas/adaptador_eleccionesdb.py").read_text(encoding="utf-8")
        self.assertIn("def _verified_retrieved_at", adapter)
        self.assertIn("'retrieved_at':verified_retrieved_at", adapter)
        self.assertIn("ap.add_argument('--retrieved-at',required=True)", adapter)


if __name__ == "__main__":
    unittest.main()
