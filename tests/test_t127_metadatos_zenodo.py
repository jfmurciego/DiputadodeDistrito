"""T-127: coherencia de metadatos de citación (valores literales decididos por el propietario, 09-11)."""
import json
import re
import unittest
from pathlib import Path

R = Path(__file__).resolve().parents[1]
ORCID = "0009-0002-4434-959X"


class MetadatosZenodo(unittest.TestCase):
    def test_metadatos_de_la_herramienta_y_zenodo_json_archivado(self):
        # T-388 (D-146): los metadatos viven en la herramienta; `.zenodo.json` ya no está en la raíz (copia en legacy/)
        self.assertFalse((R / ".zenodo.json").exists())
        import sys
        sys.path.insert(0, str(R / "herramientas"))
        import zenodo_deposito as zd
        m = zd.metadatos("1.0.0", "mapas-v1.0.0", "o/r")
        c = m["creators"][0]
        self.assertEqual((c["name"], c["affiliation"], c["orcid"]), ("Murciego, Jesus", "Independent researcher", ORCID))
        self.assertEqual((m["license"], m["upload_type"]), ("cc-by-4.0", "dataset"))

    def test_citation_cff(self):
        t = (R / "CITATION.cff").read_text(encoding="utf-8")
        self.assertIn('family-names: "Murciego"', t)
        self.assertIn('given-names: "Jesus"', t)
        self.assertIn('affiliation: "Independent researcher"', t)
        self.assertIn(ORCID, t)
        self.assertIn('version: "4.9.0"', t)
        self.assertNotIn("license: Apache-2.0", t)  # T-280 (D-95)
        self.assertIn("license-url:", t)
        self.assertNotIn("rellenar", t)

    def test_doi_concepto_y_version_coherentes(self):
        concepto, version = "10.5281/zenodo.24093967", "10.5281/zenodo.24093968"
        cff = (R / "CITATION.cff").read_text(encoding="utf-8")
        readme = (R / "README.md").read_text(encoding="utf-8")
        guia = (R / "docs/PUBLICACION_ZENODO.md").read_text(encoding="utf-8")
        for doi in (concepto, version):
            self.assertIn(f'value: "{doi}"', cff)
            self.assertIn(doi, readme)
            self.assertIn(doi, guia)
        self.assertIn(f"zenodo.org/badge/DOI/{concepto}.svg", readme)

    def test_version_readme_y_paper(self):
        readme = (R / "README.md").read_text(encoding="utf-8")
        self.assertRegex(readme, r"\*\*README rev\. \d+\.\d+\.\d+-r\d+\*\*")
        paper = (R / "docs/ARTICULO_JOSS/paper.md").read_text(encoding="utf-8")
        self.assertIn("name: Jesus Murciego", paper)
        self.assertIn('name: "Independent researcher"', paper)
        self.assertNotIn("PENDIENTE", paper.split("# Summary")[0])


class LicenciaPropietaria(unittest.TestCase):
    """T-280 (D-95): LICENSE propietaria, nota de la Apache-2.0 anterior y excepciones de D-92."""

    def test_license(self):
        t = (R / "LICENSE").read_text(encoding="utf-8")
        self.assertIn("Copyright (c) 2026 Jesus Murciego. Todos los derechos reservados.", t)
        self.assertIn("Apache-2.0", t)
        self.assertIn("14 de noviembre de 2026", t)
        self.assertIn("CC BY 4.0", t)
        self.assertIn("CC BY-NC 4.0", t)
        self.assertNotIn("PENDIENTE", t)
        self.assertNotIn("PROPUESTA TÉCNICA", t)
        # La copia Apache en legacy/licencias/ no entra en la imagen de CI (.dockerignore excluye legacy/*): se comprueba en el árbol.
        if (R / "legacy").is_dir() and (R / ".git").exists():
            self.assertTrue((R / "legacy/licencias/LICENSE_apache-2.0_hasta_2026-11-14.txt").is_file())

    def test_readme_sin_apache_como_licencia_vigente(self):
        readme = (R / "README.md").read_text(encoding="utf-8")
        self.assertNotIn("**Código**: Apache-2.0", readme)
        self.assertIn("licencia propietaria", readme)


if __name__ == "__main__":
    unittest.main()
