"""T-127: coherencia de metadatos de citación (valores literales decididos por el propietario, 09-11)."""
import json
import re
import unittest
from pathlib import Path

R = Path(__file__).resolve().parents[1]
ORCID = "0009-0002-4434-959X"


class MetadatosZenodo(unittest.TestCase):
    def test_zenodo_json(self):
        z = json.loads((R / ".zenodo.json").read_text(encoding="utf-8"))
        c = z["creators"][0]
        self.assertEqual(c["name"], "Murciego, Jesus")
        self.assertEqual(c["affiliation"], "Independent researcher")
        self.assertEqual(c["orcid"], ORCID)
        self.assertEqual(z["license"], "apache-2.0")

    def test_citation_cff(self):
        t = (R / "CITATION.cff").read_text(encoding="utf-8")
        self.assertIn('family-names: "Murciego"', t)
        self.assertIn('given-names: "Jesus"', t)
        self.assertIn('affiliation: "Independent researcher"', t)
        self.assertIn(ORCID, t)
        self.assertIn('version: "4.10.0"', t)
        self.assertIn("license: Apache-2.0", t)
        self.assertNotIn("rellenar", t)

    def test_version_readme_y_paper(self):
        readme = (R / "README.md").read_text(encoding="utf-8")
        self.assertRegex(readme, r"\*\*README v4\.10\.0\*\*")
        paper = (R / "docs/ARTICULO_JOSS/paper.md").read_text(encoding="utf-8")
        self.assertIn("name: Jesus Murciego", paper)
        self.assertIn('name: "Independent researcher"', paper)
        self.assertNotIn("PENDIENTE", paper.split("# Summary")[0])


if __name__ == "__main__":
    unittest.main()
