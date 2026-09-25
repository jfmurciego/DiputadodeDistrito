import unittest
from pathlib import Path

import yaml

from herramientas.resolver_eleccion_vigente import resolve

ROOT = Path(__file__).resolve().parents[1]


class TestRegistroElectoralComun(unittest.TestCase):
    def test_registry_has_exactly_19_registered_territories(self):
        data = yaml.safe_load(
            (ROOT / "configuracion/registro_electoral.yaml").read_text(encoding="utf-8")
        )
        self.assertEqual(data["schema"], "ddd-election-registry/1.0")
        self.assertEqual(len(data["territories"]), 19)
        for row in data["territories"].values():
            self.assertTrue(row["election_id"])
            self.assertTrue(row["election_date"])
            self.assertTrue(row["name"])

    def test_early_abort_territory_now_resolves_without_source_declaration(self):
        row = resolve("Cantabria", root_dir=ROOT, edition="2025")
        self.assertEqual(row["territory_id"], "cantabria")
        self.assertEqual(row["election_id"], "cantabria_parlamento_2023")
        self.assertEqual(row["resolution_mode"], "common_election_registry")
        self.assertEqual(row["declaration"], "")

    def test_ceuta_melilla_are_their_own_assembly_elections(self):
        ceuta = resolve("Ceuta", root_dir=ROOT, edition="2025")
        melilla = resolve("Melilla", root_dir=ROOT, edition="2025")
        self.assertEqual(ceuta["election_id"], "ceuta_asamblea_local_2023")
        self.assertEqual(melilla["election_id"], "melilla_asamblea_local_2023")


if __name__ == "__main__":
    unittest.main()
