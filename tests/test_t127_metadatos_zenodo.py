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
        self.assertIn('version: "4.9.0"', t)
        self.assertIn("license: Apache-2.0", t)
        self.assertNotIn("rellenar", t)

    def test_doi_concepto_y_version_coherentes(self):
        concepto, version = "10.5281/zenodo.24093967", "10.5281/zenodo.24093968"
        cff = (R / "CITATION.cff").read_text(encoding="utf-8")
        readme = (R / "README.md").read_text(encoding="utf-8")
        guia = (R / "docs/PUBLICACION_ZENODO.md").read_text(encoding="utf-8")
        z = json.loads((R / ".zenodo.json").read_text(encoding="utf-8"))
        for doi in (concepto, version):
            self.assertIn(f'value: "{doi}"', cff)
            self.assertIn(doi, readme)
            self.assertIn(doi, guia)
        self.assertIn(f"zenodo.org/badge/DOI/{concepto}.svg", readme)
        self.assertIn(concepto, [r["identifier"] for r in z["related_identifiers"]])

    def test_version_readme_y_paper(self):
        readme = (R / "README.md").read_text(encoding="utf-8")
        self.assertRegex(readme, r"\*\*README rev\. 4\.9\.0-r1\*\*")
        paper = (R / "docs/ARTICULO_JOSS/paper.md").read_text(encoding="utf-8")
        self.assertIn("name: Jesus Murciego", paper)
        self.assertIn('name: "Independent researcher"', paper)
        self.assertNotIn("PENDIENTE", paper.split("# Summary")[0])


if __name__ == "__main__":
    unittest.main()
