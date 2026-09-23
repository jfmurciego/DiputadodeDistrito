"""
PROYECTO: Diputado de Distrito
PRUEBA: contrato estructural GerryChain 50 multi-territorio
VERSIÓN: 1.0.0
FECHA: 2026-09-23
FUNCIÓN: demostrar que el motor ensemble no contiene excepciones territoriales y que
los contratos de Aragón, Principado de Asturias, Galicia, Castilla y León y
Extremadura exponen los campos necesarios para un binding externo genérico.
"""
from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

import yaml

from ddd_ensemble.runner import ensure_plan
from ddd_ensemble.ensemble_plan import (
    GERRYCHAIN50_ENTRYPOINT,
    build_gerrychain50_plan,
    gerrychain50_manager_contract,
)


ROOT = Path(__file__).resolve().parents[1]
TERRITORIES = {
    "aragon": ("territorios/aragon/config/aragon_2025.yaml", 67, "CUMUN"),
    "principado_de_asturias": (
        "territorios/principado_de_asturias/config/principado_de_asturias_2025.yaml",
        45,
        "M04_PARTITION_UNIT",
    ),
    "galicia": ("territorios/galicia/config/galicia_2025.yaml", 75, "CUMUN"),
    "castilla_y_leon": (
        "territorios/castilla_y_leon/config/castilla_y_leon_2025.yaml",
        82,
        "CUMUN",
    ),
    "extremadura": (
        "territorios/extremadura/config/extremadura_2025.yaml",
        65,
        "M04_PARTITION_UNIT",
    ),
}


def load_contract(path: str) -> dict:
    return yaml.safe_load((ROOT / path).read_text(encoding="utf-8")) or {}


def structural_binding(territory_id: str, cfg: dict) -> dict:
    modules = cfg["modulos"]
    m02 = modules["modulo_02_construir_adyacencias"]
    m03 = modules["modulo_03_construir_grafo"]
    m04 = modules["modulo_04_generar_semillas"]
    m05 = modules["modulo_05_optimizar_distritos"]
    validation = cfg["validation"]
    partitioning = cfg.get("partitioning") or {}
    discipline_field = str(validation.get("municipality_field") or m05.get("municipality_field") or "CUMUN")
    if (
        bool(partitioning.get("enabled"))
        and str(partitioning.get("strategy") or "") == "connected_internal_units"
    ):
        discipline_field = str(partitioning["partition_unit_field"])
    k = int(
        m05.get("expected_districts")
        or m04.get("k_districts")
        or validation["expected_districts"]
    )
    quotas = {str(key).zfill(2): int(value) for key, value in validation["province_districts"].items()}
    return {
        "territory_id": territory_id,
        "graph": str(m05.get("in_graph_json") or m04["in_graph_json"] or m03["out_graph_json"]),
        "initial": str(m05["in_geojson"]),
        "k": k,
        "population_field": str(m05["pop_field"]),
        "section_field": str(m05["id_field"]),
        "province_field": str(m05["province_field"]),
        "discipline_field": discipline_field,
        "atomic_unit_field": str(m05.get("unit_id_field") or "ddd_unit_id"),
        "province_districts": quotas,
        "min_shared_border_m": float(
            (m05.get("gerrychain") or {}).get(
                "min_shared_border_m",
                m02.get("min_shared_border_m", 1.0),
            )
        ),
        "gerrychain50": gerrychain50_manager_contract(seed=20260923),
    }


class MultiTerritoryEnsembleContractTests(unittest.TestCase):
    def test_engine_has_no_aragon_specific_branch(self):
        for relative in (
            "ddd_ensemble/ensemble_plan.py",
            "ddd_ensemble/runner.py",
            "ddd_ensemble/ensemble_assembler.py",
            "ddd_core/m05_gerrychain_engine.py",
        ):
            source = (ROOT / relative).read_text(encoding="utf-8").lower()
            self.assertNotIn('"aragon"', source, relative)
            self.assertNotIn("'aragon'", source, relative)

    def test_five_territories_expose_generic_binding(self):
        for territory_id, (path, expected_k, expected_discipline) in TERRITORIES.items():
            with self.subTest(territory=territory_id):
                binding = structural_binding(territory_id, load_contract(path))
                self.assertEqual(binding["territory_id"], territory_id)
                self.assertEqual(binding["k"], expected_k)
                self.assertEqual(sum(binding["province_districts"].values()), expected_k)
                self.assertEqual(binding["discipline_field"], expected_discipline)
                self.assertTrue(binding["graph"])
                self.assertTrue(binding["initial"])
                self.assertTrue(binding["population_field"])
                self.assertTrue(binding["section_field"])
                self.assertTrue(binding["province_field"])
                self.assertTrue(binding["atomic_unit_field"])
                self.assertGreater(binding["min_shared_border_m"], 0.0)
                self.assertEqual(
                    binding["gerrychain50"],
                    {
                        "schema": "ddd.gerrychain50-manager-contract/1.0",
                        "entrypoint": GERRYCHAIN50_ENTRYPOINT,
                        "candidate_count": 50,
                        "seed": 20260923,
                        "require_unique_hashes": True,
                    },
                )

    def test_fifty_candidate_plan_is_deterministic_for_each_territory(self):
        for territory_id in TERRITORIES:
            with self.subTest(territory=territory_id):
                first = build_gerrychain50_plan(
                    territory_id,
                    "fixture-bundle",
                    seed=20260923,
                )
                second = build_gerrychain50_plan(
                    territory_id,
                    "fixture-bundle",
                    seed=20260923,
                )
                self.assertEqual(first, second)
                self.assertEqual(first["candidate_count"], 50)
                self.assertEqual(len(first["candidates"]), 50)
                self.assertEqual(len({row["seed"] for row in first["candidates"]}), 50)
                self.assertTrue(first["requirements"]["unique_assignment_hashes"])


    def test_runner_rejects_fifty_candidates_without_strict_entrypoint(self):
        config = {
            "territory_id": "fixture",
            "prepared_bundle_id": "fixture-bundle",
            "ensemble": {
                "candidate_count": 50,
                "seed": 20260923,
                "require_unique_hashes": True,
            },
        }
        with TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(
                ValueError, "candidate_count=50 requiere ensemble.entrypoint=gerrychain_50"
            ):
                ensure_plan(config, Path(tmp))

    def test_gerrychain50_entrypoint_rejects_missing_seed(self):
        config = {
            "territory_id": "fixture",
            "prepared_bundle_id": "fixture-bundle",
            "ensemble": {
                "entrypoint": GERRYCHAIN50_ENTRYPOINT,
                "candidate_count": 50,
                "require_unique_hashes": True,
            },
        }
        with TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(ValueError, "requiere ensemble.seed"):
                ensure_plan(config, Path(tmp))


if __name__ == "__main__":
    unittest.main()
