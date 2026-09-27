from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from herramientas.preparar_fuente_electoral import prepare
from herramientas.resolver_eleccion_vigente import resolve_for_preparation

ROOT = Path(__file__).resolve().parents[1]
PARAMS = ROOT / "territorios/castilla_y_leon/config/castilla_y_leon_2025.yaml"
CONTRACT = ROOT / "territorios/castilla_y_leon/config/elecciones/castilla_y_leon_cortes_2026.json"


class CastillaYLeonMaterializedElectionTests(unittest.TestCase):
    def test_resolves_current_2026_identity_without_acquisition_declaration(self):
        row = resolve_for_preparation("Castilla y León", root_dir=ROOT, edition="2025")
        self.assertEqual(row["territory_id"], "castilla_y_leon")
        self.assertEqual(row["election_id"], "castilla_y_leon_cortes_2026-03-15")
        self.assertEqual(row["election_date"], "2026-03-15")
        self.assertEqual(row["resolution_mode"], "materialized_election_contract")
        self.assertEqual(row["declaration"], "")

    def test_prepares_from_materialized_contract_without_external_acquisition(self):
        contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
        self.assertEqual(contract["election_id"], "castilla_y_leon_cortes_2026-03-15")
        self.assertEqual(contract["territory_id"], "castilla_y_leon")
        self.assertEqual(contract["sources"][0]["publisher"], "Junta de Castilla y León — Datos Abiertos")
        with tempfile.TemporaryDirectory() as td:
            out = Path(td) / "package"
            with patch(
                "herramientas.preparar_fuente_electoral.check_declaration",
                side_effect=AssertionError("Castilla y León no debe adquirir datos externos"),
            ):
                manifest = prepare(
                    territory_id="castilla_y_leon",
                    edition="2025",
                    package_out=out,
                    root=ROOT,
                    params=PARAMS,
                    declaration=None,
                    previous=None,
                )
            self.assertEqual(manifest["decision"], "REUSE")
            self.assertEqual(manifest["election_id"], "castilla_y_leon_cortes_2026-03-15")
            self.assertEqual(manifest["election_date"], "2026-03-15")
            self.assertEqual(
                contract["sources"][0]["sha256"],
                "603e0261adc11871cdc8345a847da9f9161894050a51dd334f9928a4e6d01d30",
            )
            self.assertEqual(
                manifest["selected_source"]["sha256"],
                contract["sources"][0]["sha256"],
            )

            embedded = manifest["embedded_contract"]
            contract_path = out / embedded["election_contract"]
            dictionary_path = out / embedded["party_dictionary"]
            self.assertTrue((out / "manifest.json").is_file())
            self.assertTrue(contract_path.is_file())
            self.assertTrue(dictionary_path.is_file())

            sha256 = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
            self.assertEqual(embedded["contract_sha256"], sha256(contract_path))
            self.assertEqual(embedded["party_dictionary_sha256"], sha256(dictionary_path))
            self.assertEqual(
                embedded["party_dictionary_sha256"],
                contract["party_dictionary"]["sha256"],
            )

            portable = json.loads(contract_path.read_text(encoding="utf-8"))
            self.assertEqual(portable["territory_id"], "castilla_y_leon")
            self.assertEqual(portable["election_id"], "castilla_y_leon_cortes_2026-03-15")
            self.assertEqual(portable["election_date"], "2026-03-15")
            self.assertEqual(
                portable["sources"][0]["path"],
                manifest["selected_source"]["path"],
            )
            self.assertEqual(
                portable["sources"][0]["sha256"],
                manifest["selected_source"]["sha256"],
            )
            self.assertEqual(
                portable["party_dictionary"]["path"],
                "contract/party_dictionary.json",
            )
            self.assertEqual(
                portable["party_dictionary"]["sha256"],
                embedded["party_dictionary_sha256"],
            )


if __name__ == "__main__":
    unittest.main()
