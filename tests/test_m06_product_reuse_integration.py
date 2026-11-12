"""Versión: 1.0.2; nombre: reutilización de los M06 registrados; fecha: 2026-10-28.
Cambios/motivo: se adoptan los M06 de Aragón (40656036271) y Extremadura (40656175842) del 28-10, los
únicos con bytes vivos (conservados en los releases draft almacen-m06-*).
Anterior: legacy/tests/test_m06_product_reuse_integration_v1.0.1_20261028.py.
"""
from __future__ import annotations

import json
import unittest
from pathlib import Path

import yaml

from herramientas.resolver_activos_durables import DurableAssetBlock, validate_durable_assets
from herramientas.resolver_ejecucion_completa import build_plan

from tests._raiz_congelada import frozen_root  # noqa: E402

# Los M06 registrados se evalúan sobre el estado congelado en aee8215e: un relanzamiento en curso
# registra fuente nueva antes que su M06 y deja el linaje vivo transitoriamente incompatible.
ROOT = frozen_root()
CATALOG = ROOT / "configuracion/catalogo_preparacion.yaml"
# Territorios con M06 registrado. Los run_id no se fijan: cada ejecución completa registra uno
# nuevo; la regla es que el resolver durable devuelva exactamente el producto del catálogo.
PRODUCTS = (
    "aragon", "principado_de_asturias", "cantabria", "castilla_y_leon",
    "castilla_la_mancha", "extremadura", "galicia",
)


def catalogued_product(row):
    evidence = row["editions"]["2025"]["evidence"]["territorial_product"]
    return json.loads((ROOT / evidence).read_text(encoding="utf-8"))


class M06ProductReuseIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog = yaml.safe_load(CATALOG.read_text(encoding="utf-8"))
        cls.rows = {row["territory_id"]: row for row in cls.catalog["territories"]}

    def test_all_seven_registered_m06_products_validate_independently_of_m08(self):
        for territory_id in PRODUCTS:
            with self.subTest(territory=territory_id):
                expected = catalogued_product(self.rows[territory_id])
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
                self.assertEqual(product["run_id"], expected["run_id"])
                self.assertEqual(product["artifact_name"], expected["artifact_name"])
                self.assertEqual(product["artifact_sha256"], expected["artifact_sha256"])
                self.assertTrue(product["artifact_name"].startswith(f"ddd-state-{product['run_id']}-M06"))
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
