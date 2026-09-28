from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from herramientas.resolver_ejecucion_completa import build_plan
from herramientas.validar_puerta_ejecucion import validate_gate


ROOT = Path(__file__).resolve().parents[1]
PARAMS = ROOT / "territorios/galicia/config/galicia_2025.yaml"
CONTRACT = ROOT / "territorios/galicia/config/elecciones/galicia_parlamento_2024.json"
CATALOG = ROOT / "configuracion/catalogo_preparacion.yaml"
ORCHESTRATION = ROOT / ".github/workflows/ejecucion-completa-proyecto.yml"

DURABLE_RUN_ID = "36136559051"
DURABLE_ARTIFACT_NAME = "ddd-electoral-package-galicia-2025-36136559051"
DURABLE_ARTIFACT_DIGEST = "59392e194397ea965fde76a5a68fe97519d08e6c175f4328d3830fc72d102db2"
DURABLE_SOURCE_SHA256 = "7f9db16181962a1ef543fe0768c6822d19166e91b97e0a9d48b7c449c24aba96"


class GaliciaElectoralIdentityGateTests(unittest.TestCase):
    def _gate(self, *, election_id: str, election_date: str) -> dict:
        with tempfile.TemporaryDirectory() as td:
            package = Path(td)
            selected_source = {
                "path": "data/resultados_electorales_vigentes.csv",
                "sha256": DURABLE_SOURCE_SHA256,
                "bytes": 331227,
            }
            manifest = {
                "schema": "ddd-electoral-package/1.0",
                "decision": "ACQUIRE",
                "territory_id": "galicia",
                "edition": "2025",
                "election_id": election_id,
                "election_date": election_date,
                "selected_source": selected_source,
            }
            (package / "manifest.json").write_text(
                json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            # No se descargan ni se regeneran resultados: se reutiliza la huella
            # de procedencia ya certificada y la puerta real sigue comparándola
            # contra el contrato estático de Galicia.
            with patch(
                "herramientas.validar_paquete_electoral._validate_selected_source",
                return_value=(
                    selected_source,
                    package / selected_source["path"],
                    DURABLE_SOURCE_SHA256,
                ),
            ):
                return validate_gate(
                    phase="electoral_source",
                    artifact_root=package,
                    territory_id="galicia",
                    edition="2025",
                    run_id=DURABLE_RUN_ID,
                    artifact_name=DURABLE_ARTIFACT_NAME,
                    artifact_digest=DURABLE_ARTIFACT_DIGEST,
                    expected_digest=DURABLE_ARTIFACT_DIGEST,
                    params=PARAMS,
                    root_dir=ROOT,
                )

    def test_existing_durable_package_identity_passes_03_to_04_gate(self):
        contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
        self.assertEqual(contract["election_id"], "galicia_parlamento_2024")
        self.assertEqual(contract["election_date"], "2024-02-18")
        self.assertEqual(contract["sources"][0]["sha256"], DURABLE_SOURCE_SHA256)

        result = self._gate(
            election_id="galicia_parlamento_2024",
            election_date="2024-02-18",
        )

        self.assertEqual(result["decision"], "VALIDADO")
        self.assertEqual(result["phase_decision"], "ACQUIRE")
        self.assertEqual(result["reasons"], [])

    def test_not_certified_current_m06_forces_regeneration_and_new_incorporation(self):
        plan = build_plan(
            territory="Galicia",
            edition="2025",
            execution_mode="reuse",
            catalog=CATALOG,
            root_dir=ROOT,
            optimization_algorithm="Canónico",
            force_selected_algorithm=False,
        )

        self.assertEqual(plan["catalog_state"]["territorial_certification"], "NOT_CERTIFIED")
        self.assertFalse(plan["catalog_state"]["territorial_product_available"])
        self.assertEqual(
            plan["generation_gate"]["route"],
            "validated_pre_m04_topology",
        )
        self.assertFalse(plan["run_prepare_territorial"])
        self.assertTrue(plan["run_generate"])
        self.assertFalse(plan["run_prepare_electoral"])
        self.assertTrue(plan["run_incorporate"])

        self.assertEqual(
            plan["existing"]["electoral_source"]["election_id"],
            "galicia_parlamento_2024",
        )
        self.assertEqual(
            plan["existing"]["electoral_source"]["decision"],
            "VALIDADO",
        )
        self.assertEqual(
            plan["existing"]["electoral_product"]["run_id"],
            35716459467,
        )

    def test_historical_m08_cannot_enter_orphan_recovery_when_regeneration_is_required(self):
        plan = build_plan(
            territory="Galicia",
            edition="2025",
            execution_mode="reuse",
            catalog=CATALOG,
            root_dir=ROOT,
            optimization_algorithm="Canónico",
            force_selected_algorithm=False,
        )
        self.assertTrue(plan["run_generate"])

        orchestration = ORCHESTRATION.read_text(encoding="utf-8")
        self.assertIn(
            "needs.planificar.outputs.run_generate == 'false'",
            orchestration,
        )
        self.assertIn(
            "needs.planificar.outputs.run_prepare_electoral == 'false'",
            orchestration,
        )

    def test_gate_rejects_a_different_galicia_election(self):
        result = self._gate(
            election_id="galicia_parlamento_2020",
            election_date="2020-07-12",
        )

        self.assertEqual(result["decision"], "BLOQUEADO")
        self.assertTrue(
            any(reason.startswith("PAQUETE_ELECTORAL:") for reason in result["reasons"])
        )


if __name__ == "__main__":
    unittest.main()
