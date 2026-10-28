"""Versión: 1.0.1; nombre: reutilización de los M06 registrados; fecha: 2026-10-28.
Cambios/motivo: Cantabria, Castilla-La Mancha y Galicia registraron M06 nuevos (runs 40604431189,
40604483629 y 40604535110) con su manifiesto durable; se fijan esos productos.
Anterior: legacy/tests/test_m06_product_reuse_integration_v1.0.0_20261028.py.
"""
from __future__ import annotations

import unittest
from pathlib import Path

import yaml

from herramientas.resolver_activos_durables import DurableAssetBlock, validate_durable_assets
from herramientas.resolver_ejecucion_completa import build_plan

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "configuracion/catalogo_preparacion.yaml"
PRODUCTS = {
    "aragon": (36321736287, "ddd-state-36321736287-M06", "1aa6889ae4e49e49ce2a6b469b6cfbc325d040b30639d5adb8326afde9c89394"),
    "principado_de_asturias": (40241852045, "ddd-state-40241852045-M06", "9e8a8aa21962dea749fd4db1b0c357216a4ac901dab8351cc6be294e74676cdd"),
    "cantabria": (40604431189, "ddd-state-40604431189-M06", "232a101d11467d89c3be9e3a359c64f1e78305e57b4def7cfcd0de82b60891fa"),
    "castilla_y_leon": (35889595424, "ddd-state-35889595424-M06-campaign-35889595424-1--04--castilla_y_leon", "cfb818ef94bfcf35b64b78dc620a0eadd859c6f95aba1234b2d54898d556016b"),
    "castilla_la_mancha": (40604483629, "ddd-state-40604483629-M06", "ea98d1cef0153f1f5201756a8dca0e8943637e843b37702d64ca6f851b7a8a8d"),
    "extremadura": (36472516474, "ddd-state-36472516474-M06", "1a491b8ae90a1051989cca29ffa712ade781adb81d622ac0607cc6fac15d26dd"),
    "galicia": (40604535110, "ddd-state-40604535110-M06", "b734e29e58f7a2f4af3161058971508c356f783832d5212535d9ab7bd5b0fe4d"),
}


class M06ProductReuseIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog = yaml.safe_load(CATALOG.read_text(encoding="utf-8"))
        cls.rows = {row["territory_id"]: row for row in cls.catalog["territories"]}

    def test_all_seven_registered_m06_products_validate_independently_of_m08(self):
        for territory_id, (run_id, artifact_name, artifact_sha256) in PRODUCTS.items():
            with self.subTest(territory=territory_id):
                state = dict(self.rows[territory_id]["editions"]["2025"])
                state["electoral_source_prepared"] = False
                state["electoral_product_available"] = False
                result = validate_durable_assets(
                    root_dir=ROOT,
                    state=state,
                    territory_id=territory_id,
                    edition="2025",
                    territorial_source=state.get("preparation_evidence"),
                    expected_election_id=None,
                )
                product = result["territorial_product"]
                self.assertEqual(product["run_id"], run_id)
                self.assertEqual(product["artifact_name"], artifact_name)
                self.assertEqual(product["artifact_sha256"], artifact_sha256)
                self.assertEqual(product["decision"], "PASS_WITH_EXCEPTIONS")
                self.assertIsNone(result["electoral_product"])

    def test_reuse_plans_skip_generation_and_unaccredited_m08_stays_blocked(self):
        for territory_id in PRODUCTS:
            with self.subTest(territory=territory_id):
                if territory_id == "castilla_y_leon":
                    with self.assertRaisesRegex(
                        ValueError,
                        "DURABLE_ASSET_INVALID: electoral_product: receipt durable ilegible",
                    ):
                        build_plan(
                            territory=territory_id,
                            edition="2025",
                            execution_mode="reuse",
                            catalog=CATALOG,
                            root_dir=ROOT,
                        )
                    continue
                plan = build_plan(
                    territory=territory_id,
                    edition="2025",
                    execution_mode="reuse",
                    catalog=CATALOG,
                    root_dir=ROOT,
                )
                self.assertFalse(plan["run_generate"])
                self.assertEqual(plan["generation_execution_mode"], "reuse")
                self.assertTrue(plan["existing"]["territorial_product"]["artifact_name"])

    def test_invalid_m08_receipt_is_not_swallowed_by_m06_reuse(self):
        row = self.rows["castilla_y_leon"]["editions"]["2025"]
        state = dict(row)
        with self.assertRaisesRegex(DurableAssetBlock, "DURABLE_ASSET_INVALID: electoral_product"):
            validate_durable_assets(
                root_dir=ROOT,
                state=state,
                territory_id="castilla_y_leon",
                edition="2025",
                territorial_source=state.get("preparation_evidence"),
                expected_election_id=None,
            )


if __name__ == "__main__":
    unittest.main()
