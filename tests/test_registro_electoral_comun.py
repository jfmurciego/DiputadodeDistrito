import unittest
from pathlib import Path

import yaml

from herramientas.resolver_eleccion_vigente import resolve

ROOT = Path(__file__).resolve().parents[1]


class TestRegistroElectoralComun(unittest.TestCase):
    def setUp(self):
        self.registry = yaml.safe_load(
            (ROOT / "configuracion/registro_electoral.yaml").read_text(encoding="utf-8")
        )

    def test_registry_has_exactly_19_identified_elections(self):
        self.assertEqual(self.registry["schema"], "ddd-election-registry/1.0")
        self.assertEqual(len(self.registry["territories"]), 19)
        for row in self.registry["territories"].values():
            self.assertTrue(row["election_id"])
            self.assertTrue(row["election_date"])
            self.assertTrue(row["name"])

    def test_identified_election_without_acquirable_source_is_not_resolvable(self):
        cantabria = self.registry["territories"]["cantabria"]
        self.assertEqual(cantabria["election_id"], "cantabria_parlamento_2023")
        self.assertFalse(cantabria.get("declaration"))
        with self.assertRaisesRegex(SystemExit, "No existe elección resoluble"):
            resolve("Cantabria", root_dir=ROOT, edition="2025")

    def test_acquirable_source_is_resolvable(self):
        asturias = self.registry["territories"]["principado_de_asturias"]
        self.assertTrue(asturias.get("declaration"))
        row = resolve("Principado de Asturias", root_dir=ROOT, edition="2025")
        self.assertEqual(row["election_id"], "asturias_jgpa_2023")
        self.assertTrue(row["declaration"])

    def test_ceuta_melilla_keep_their_own_identified_assembly_elections(self):
        self.assertEqual(self.registry["territories"]["ceuta"]["election_id"], "ceuta_asamblea_local_2023")
        self.assertEqual(self.registry["territories"]["melilla"]["election_id"], "melilla_asamblea_local_2023")


if __name__ == "__main__":
    unittest.main()
