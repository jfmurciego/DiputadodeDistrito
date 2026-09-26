from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

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
            manifest = prepare(
                territory_id="castilla_y_leon",
                edition="2025",
                package_out=out,
                root=ROOT,
                params=PARAMS,
                declaration=None,
                previous=None,
            )
            self.assertEqual(manifest["decision"], "ACQUIRE")
            self.assertEqual(manifest["election_id"], "castilla_y_leon_cortes_2026-03-15")
            self.assertEqual(manifest["election_date"], "2026-03-15")
            self.assertEqual(
                manifest["selected_source"]["sha256"],
                contract["sources"][0]["sha256"],
            )
            self.assertTrue((out / "manifest.json").is_file())
            self.assertTrue((out / "contract/election_contract.json").is_file())


if __name__ == "__main__":
    unittest.main()
