from __future__ import annotations

import json

import yaml

from tests import _test_gestor_campana_core as _core
from tests._test_gestor_campana_core import *  # noqa: F401,F403

ROOT = _core.ROOT
build_plan = _core.build_plan
generation_enablement = _core.generation_enablement
apply_explicit_territorial_source = _core.apply_explicit_territorial_source


def _test_generation_gate_real_territories_and_both_entry_paths(self):
    catalog_path = ROOT / "configuracion/catalogo_preparacion.yaml"
    catalog = yaml.safe_load(catalog_path.read_text(encoding="utf-8"))
    rows = {row["territory_id"]: row["editions"]["2025"] for row in catalog["territories"]}

    # Un producto territorial certificado es la procedencia más fuerte y, por tanto,
    # prevalece sobre declaraciones generation_ready o sobre la mera ruta de particionado.
    for name, territory_id, route in (
        ("Galicia", "galicia", "certified_product_lineage"),
        ("Principado de Asturias", "principado_de_asturias", "certified_product_lineage"),
        ("Aragón", "aragon", "certified_product_lineage"),
        ("Castilla y León", "castilla_y_leon", "certified_product_lineage"),
        ("Andalucía", "andalucia", "declared_generation_ready"),
    ):
        with self.subTest(territory=name):
            plan = build_plan(
                territory=name,
                edition="2025",
                execution_mode="reuse",
                catalog=catalog_path,
                root_dir=ROOT,
                force_selected_algorithm=True,
            )
            self.assertEqual(plan["generation_gate"], {"allowed": True, "route": route})

    for name, territory_id in (
        ("La Rioja", "la_rioja"),
        ("Cantabria", "cantabria"),
        ("Comunidad Foral de Navarra", "comunidad_foral_de_navarra"),
        ("País Vasco", "pais_vasco"),
    ):
        with self.subTest(first_product=territory_id):
            row = rows[territory_id]
            self.assertFalse(row["territorial_product_available"])
            self.assertEqual(row["territorial_certification"], "NOT_CERTIFIED")
            self.assertEqual(row["production_authorization"], "AUTHORIZED")
            evidence_path = row["evidence"]["generation_preflight"]
            evidence = json.loads((ROOT / evidence_path).read_text(encoding="utf-8"))
            bare_gate = generation_enablement(
                root_dir=ROOT,
                contract_path=row["contract_path"],
                territory_id=territory_id,
                certified_product_ready=False,
            )
            self.assertFalse(bare_gate["allowed"])
            plan = build_plan(
                territory=name,
                edition="2025",
                execution_mode="reuse",
                catalog=catalog_path,
                root_dir=ROOT,
                force_selected_algorithm=True,
            )
            self.assertEqual(
                plan["generation_gate"],
                {"allowed": True, "route": "validated_pre_m04_topology"},
            )
            prep = row["preparation_evidence"]
            apply_explicit_territorial_source(
                plan,
                root_dir=ROOT,
                reuse_run_id=str(prep["run_id"]),
                reuse_artifact_name=prep["artifact_name"],
                reuse_artifact_sha256=prep["artifact_sha256"],
                reuse_source_sha=evidence["source_commit"],
            )
            self.assertTrue(plan["run_generate"])
            self.assertEqual(
                plan["existing"]["territorial_source"]["run_id"],
                prep["run_id"],
            )

    for name, territory_id in (
        ("Comunidad de Madrid", "madrid"),
        ("Comunidad Valenciana", "comunidad_valenciana"),
        ("Cataluña", "cataluna"),
    ):
        with self.subTest(still_blocked=territory_id):
            row = rows[territory_id]
            self.assertEqual(row["production_authorization"], "AUTHORIZED")
            self.assertFalse(row["territorial_product_available"])
            self.assertFalse((row.get("evidence") or {}).get("generation_preflight"))
            with self.assertRaisesRegex(ValueError, "GENERATION_CONTRACT_BLOCK"):
                build_plan(
                    territory=name,
                    edition="2025",
                    execution_mode="reuse",
                    catalog=catalog_path,
                    root_dir=ROOT,
                    force_selected_algorithm=True,
                )
            plan = {
                "territory_id": territory_id,
                "contract_path": row["contract_path"],
                "execution_mode": "reuse",
                "run_generate": False,
                "run_prepare_territorial": False,
                "catalog_state": {
                    "territorial_product_available": False,
                    "preparation_evidence": row["preparation_evidence"],
                    "generation_preflight_evidence": {},
                },
                "existing": {
                    "territorial_source": {
                        "run_id": row["preparation_evidence"]["run_id"],
                        "artifact_name": row["preparation_evidence"]["artifact_name"],
                    }
                },
            }
            with self.assertRaisesRegex(ValueError, "GENERATION_CONTRACT_BLOCK"):
                apply_explicit_territorial_source(
                    plan,
                    root_dir=ROOT,
                    reuse_run_id=str(row["preparation_evidence"]["run_id"]),
                    reuse_artifact_name=row["preparation_evidence"]["artifact_name"],
                    reuse_artifact_sha256=row["preparation_evidence"]["artifact_sha256"],
                    reuse_source_sha="0" * 40,
                )


def _test_authorized_is_not_generation_grant(self):
    catalog = yaml.safe_load((ROOT / "configuracion/catalogo_preparacion.yaml").read_text(encoding="utf-8"))
    rows = {row["territory_id"]: row["editions"]["2025"] for row in catalog["territories"]}
    row = rows["madrid"]
    self.assertEqual(row["production_authorization"], "AUTHORIZED")
    gate = generation_enablement(
        root_dir=ROOT,
        contract_path=row["contract_path"],
        territory_id="madrid",
        certified_product_ready=False,
    )
    self.assertFalse(gate["allowed"])
    self.assertEqual(gate["capability"], "CAP_PRE_M04_EVIDENCE")


_core.CampaignManagerTests.test_generation_gate_real_territories_and_both_entry_paths = (
    _test_generation_gate_real_territories_and_both_entry_paths
)
_core.CampaignManagerTests.test_authorized_is_not_generation_grant = _test_authorized_is_not_generation_grant
CampaignManagerTests = _core.CampaignManagerTests
