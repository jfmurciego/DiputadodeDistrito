from __future__ import annotations

import csv
import io
import json
import shutil
import tempfile
import unittest
import zipfile
from pathlib import Path

import yaml

from herramientas.materializar_contrato_generacion import (
    component_apportionment_audit,
    component_hamilton,
    hamilton,
    materialize,
)

ROOT = Path(__file__).resolve().parents[1]
POLICY = ROOT / "configuracion/politica_generacion_territorial_2025.yaml"
MASTER = ROOT / "configuracion/catalogo_territorios_espana_2025.yaml"
PARTITIONS = ROOT / "configuracion/particiones_insulares_2025.json"


def population_package(root: Path, rows: list[tuple[str, int]], delimiter: str = "\t") -> Path:
    package = root / "package"
    package.mkdir(parents=True)
    payload = io.StringIO()
    writer = csv.writer(payload, delimiter=delimiter, lineterminator="\n")
    writer.writerow(["Total Nacional","Provincias","Municipios","Secciones","Sexo","Edad","Periodo","Total"])
    for section, population in rows:
        writer.writerow([
            "Total Nacional", section[:2], section[:5], section,
            "Total", "Todas las edades", "2025", f"{population:,}".replace(",", "."),
        ])
    zpath = package / "65034.csv.zip"
    with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("65034.csv", payload.getvalue().encode("utf-8-sig"))
    return package


def temp_root(territory_id: str, name: str, provinces: list[str]) -> tempfile.TemporaryDirectory:
    td = tempfile.TemporaryDirectory()
    root = Path(td.name)
    (root / "configuracion").mkdir(parents=True)
    (root / "inputs").mkdir(parents=True)
    shutil.copy2(POLICY, root / "configuracion/politica_generacion_territorial_2025.yaml")
    shutil.copy2(PARTITIONS, root / "configuracion/particiones_insulares_2025.json")
    (root / "configuracion/catalogo_territorios_espana_2025.yaml").write_text(
        "territories:\n"
        f"  - {{territory_id: {territory_id}, name: {name}, province_codes: {provinces!r}, batch: test, status: bootstrap, contract_level: bootstrap_m01_m03}}\n",
        encoding="utf-8",
    )
    (root / "inputs/MANIFEST.sha256").write_text(
        "0"*64 + "  inputs/seccionado_2025.zip\n" +
        "1"*64 + "  inputs/65034.csv.zip\n",
        encoding="utf-8",
    )
    return td


class NationalGenerationMaterializationTests(unittest.TestCase):
    def test_policy_covers_exactly_the_national_registry(self):
        policy = yaml.safe_load(POLICY.read_text(encoding="utf-8"))
        master = yaml.safe_load(MASTER.read_text(encoding="utf-8"))
        self.assertEqual(
            set(policy["territories"]),
            {row["territory_id"] for row in master["territories"]},
        )
        self.assertTrue(all(int(v["k"]) > 0 for v in policy["territories"].values()))

    def test_archipelago_registry_is_explicit_and_has_no_marine_edges(self):
        data = json.loads(PARTITIONS.read_text(encoding="utf-8"))
        self.assertEqual(set(data["territories"]), {"illes_balears", "canarias"})
        self.assertEqual(len(data["territories"]["illes_balears"]["components"]), 4)
        self.assertEqual(len(data["territories"]["canarias"]["components"]), 8)
        self.assertEqual(
            data["territories"]["canarias"]["section_overrides"]["3502401010"],
            "35-C04",
        )

    def test_hamilton_conserves_k(self):
        self.assertEqual(hamilton({"22":230087,"44":136091,"50":998443},67), {"22":11,"44":7,"50":49})

    def test_component_hamilton_keeps_one_small_component_and_declares_exception(self):
        quota, exempt = component_hamilton(
            {"A":971068,"B":102821,"C":11690,"D":164265}, 59, 0.80
        )
        self.assertEqual(sum(quota.values()), 59)
        self.assertEqual(quota["C"], 1)
        self.assertEqual(exempt, ["C"])

    def test_population_parser_accepts_semicolon_official_subset(self):
        td = temp_root("principado_de_asturias", "Principado de Asturias", ["33"])
        try:
            root = Path(td.name)
            package = population_package(
                root,
                [("3300101001", 1507), ("3300201001", 1905), ("3300201002", 0)],
                delimiter=";",
            )
            result = materialize(root, "principado_de_asturias", "2025", package)
            self.assertEqual(result["status"], "READY")
            cfg = yaml.safe_load((root / result["contract_path"]).read_text(encoding="utf-8"))
            self.assertEqual(cfg["validation"]["province_districts"], {"33": 45})
        finally:
            td.cleanup()

    def test_materializes_asturias_without_manual_contract_work(self):
        td = temp_root("principado_de_asturias", "Principado de Asturias", ["33"])
        try:
            root = Path(td.name)
            package = population_package(root, [("3300101001", 1_015_128)])
            result = materialize(root, "principado_de_asturias", "2025", package)
            self.assertEqual(result["status"], "READY")
            self.assertEqual(result["k"], 45)
            cfg = yaml.safe_load((root / result["contract_path"]).read_text(encoding="utf-8"))
            self.assertEqual(cfg["meta"]["contract_level"], "production_m01_m06")
            self.assertEqual(cfg["meta"]["production_authorization"], "AUTHORIZED")
            self.assertEqual(cfg["validation"]["province_districts"], {"33":45})
            self.assertTrue(all(
                key in cfg["modulos"] for key in (
                    "modulo_01_preparar_base_territorial","modulo_02_construir_adyacencias",
                    "modulo_03_construir_grafo","modulo_04_generar_semillas",
                    "modulo_05_optimizar_distritos","modulo_06_consolidar_distritos",
                )
            ))
        finally:
            td.cleanup()

    def test_every_non_insular_territory_materializes_without_manual_promotion(self):
        policy = yaml.safe_load(POLICY.read_text(encoding="utf-8"))
        master = yaml.safe_load(MASTER.read_text(encoding="utf-8"))
        by_id = {row["territory_id"]: row for row in master["territories"]}
        for territory_id, entry in policy["territories"].items():
            if entry["partition_mode"] == "physical_components_hamilton":
                continue
            row = by_id[territory_id]
            provinces = [str(x).zfill(2) for x in row["province_codes"]]
            td = temp_root(territory_id, row["name"], provinces)
            try:
                root = Path(td.name)
                rows = [(f"{province}00101001", 100000 + index * 1000) for index, province in enumerate(provinces)]
                package = population_package(root, rows)
                result = materialize(root, territory_id, "2025", package)
                self.assertEqual(result["status"], "READY", territory_id)
                self.assertEqual(result["k"], int(entry["k"]), territory_id)
                cfg = yaml.safe_load((root / result["contract_path"]).read_text(encoding="utf-8"))
                self.assertEqual(cfg["meta"]["production_authorization"], "AUTHORIZED", territory_id)
                self.assertEqual(sum(cfg["validation"]["province_districts"].values()), int(entry["k"]), territory_id)
            finally:
                td.cleanup()

    def test_archipelagos_live_catalog_reflects_durable_preparation_without_claiming_product(self):
        catalog = yaml.safe_load(
            (ROOT/"configuracion/catalogo_preparacion.yaml").read_text(encoding="utf-8")
        )
        rows = {row["territory_id"]: row for row in catalog["territories"]}
        for territory_id in ("illes_balears", "canarias"):
            state = rows[territory_id]["editions"]["2025"]
            self.assertEqual("READY", state["preparation_status"])
            self.assertTrue(state["territorial_sources_prepared"])
            self.assertTrue(state["territorial_contract_complete"])
            self.assertEqual("AUTHORIZED", state["production_authorization"])
            self.assertTrue(state["contract_path"])
            self.assertTrue(state["territorial_source_declaration"])
            self.assertFalse(state["territorial_product_available"])
            self.assertEqual("NOT_CERTIFIED", state["territorial_certification"])
            evidence = state["preparation_evidence"]
            self.assertTrue(evidence["run_id"])
            self.assertTrue(evidence["artifact_name"])
            self.assertEqual(64, len(evidence["artifact_sha256"]))
            self.assertEqual(64, len(evidence["package_sha256"]))

    def test_archipelago_policy_separates_institutional_k_from_ddd_apportionment(self):
        policy = yaml.safe_load(POLICY.read_text(encoding="utf-8"))
        for territory_id, expected_k in (("illes_balears", 59), ("canarias", 70)):
            entry = policy["territories"][territory_id]
            self.assertEqual(expected_k, entry["k"])
            self.assertEqual("norma", entry["k_source"])
            self.assertEqual("institutional_chamber_size_only", entry["k_reference_scope"])
            self.assertEqual("ddd_design_policy", entry["apportionment_source"])
            self.assertFalse(entry["legal_apportionment_reused"])
            self.assertIn("Contexto solamente", entry["legal_context"]["note"])
        self.assertEqual(
            {"Mallorca":33,"Menorca":13,"Ibiza":12,"Formentera":1},
            policy["territories"]["illes_balears"]["legal_context"]["constituencies"],
        )
        canary = policy["territories"]["canarias"]["legal_context"]
        self.assertEqual(9, canary["autonomous_constituency"])
        self.assertEqual(61, sum(canary["island_constituencies"].values()))

    def test_r026_component_inventories_match_partition_registry_and_ddd_audit(self):
        partitions = json.loads(PARTITIONS.read_text(encoding="utf-8"))
        cases = {
            "illes_balears": {
                "k": 59,
                "r026": ROOT/"resultados/archipielagos/gh-34688874092/illes_balears.json",
                "population_by_partition": {
                    "07-C01":971068,"07-C02":102821,"07-C03":11690,"07-C04":164265,
                },
                "quota": {"07-C01":44,"07-C02":6,"07-C03":1,"07-C04":8},
                "exempt": ["07-C03"],
            },
            "canarias": {
                "k": 70,
                "r026": ROOT/"resultados/archipielagos/gh-34688874092/canarias.json",
                "population_by_partition": {
                    "35-C01":875589,"35-C02":129080,"35-C03":166146,"35-C04":732,
                    "38-C01":966469,"38-C02":22560,"38-C03":86297,"38-C04":11993,
                },
                "quota": {
                    "35-C01":25,"35-C02":5,"35-C03":6,"35-C04":1,
                    "38-C01":28,"38-C02":1,"38-C03":3,"38-C04":1,
                },
                "exempt": ["35-C04","38-C02","38-C04"],
            },
        }
        policy = yaml.safe_load(POLICY.read_text(encoding="utf-8"))
        for territory_id, case in cases.items():
            r026 = json.loads(case["r026"].read_text(encoding="utf-8"))
            registry = partitions["territories"][territory_id]["components"]
            self.assertEqual(r026["sections"], sum(x["section_count"] for x in registry.values()))
            self.assertEqual(r026["population"], sum(case["population_by_partition"].values()))
            quota, exempt = component_hamilton(case["population_by_partition"], case["k"], 0.80)
            self.assertEqual(case["quota"], quota)
            self.assertEqual(case["exempt"], exempt)
            audit = component_apportionment_audit(
                case["population_by_partition"], quota, case["k"], 0.80, exempt,
                exception_policy=policy["archipelago"]["small_component_policy"],
            )
            self.assertTrue(all(row["floor_exception_governed"] for row in audit.values()))
            self.assertEqual(
                set(exempt),
                {key for key,row in audit.items() if row["floor_exception_required"]},
            )

    def test_ungoverned_archipelago_floor_exception_blocks(self):
        with self.assertRaisesRegex(ValueError, "no gobernada"):
            component_apportionment_audit(
                {"A": 100000, "B": 1000},
                {"A": 4, "B": 1},
                5,
                0.80,
                ["B"],
                exception_policy="different_policy",
            )

    def test_materializes_canary_archipelago_without_marine_bridge(self):
        td = temp_root("canarias", "Canarias", ["35", "38"])
        try:
            root = Path(td.name)
            package = population_package(root, [
                ("3500101001", 875589),
                ("3500301001", 129080),
                ("3500401001", 166146),
                ("3502401010", 732),
                ("3800101001", 966469),
                ("3800201001", 22560),
                ("3800701001", 86297),
                ("3801301001", 11993),
            ])
            result = materialize(root, "canarias", "2025", package)
            self.assertEqual(result["status"], "READY")
            self.assertEqual(result["partition_mode"], "physical_components_hamilton")
            self.assertEqual(
                {"35-C01":25,"35-C02":5,"35-C03":6,"35-C04":1,
                 "38-C01":28,"38-C02":1,"38-C03":3,"38-C04":1},
                result["partition_districts"],
            )
            self.assertEqual("institutional_chamber_size_only", result["k_reference_scope"])
            self.assertEqual("ddd_design_policy", result["apportionment_source"])
            self.assertFalse(result["legal_apportionment_reused"])
            self.assertEqual(["35-C04","38-C02","38-C04"], result["population_floor_exempt_partitions"])
            self.assertTrue(all(x["floor_exception_governed"] for x in result["partition_apportionment_audit"].values()))
            self.assertIn("38-C04", result["population_floor_exempt_partitions"])
            cfg = yaml.safe_load((root / result["contract_path"]).read_text(encoding="utf-8"))
            self.assertEqual(cfg["validation"]["hard_partition_mode"], "physical_components")
            self.assertEqual(cfg["modulos"]["modulo_02_construir_adyacencias"]["topology_bridges"], [])
        finally:
            td.cleanup()

    def test_materializes_balearic_archipelago_with_explicit_partition_exception(self):
        td = temp_root("illes_balears", "Islas Baleares", ["07"])
        try:
            root = Path(td.name)
            package = population_package(root, [
                ("0700101001", 971068),
                ("0700201001", 102821),
                ("0702401001", 11690),
                ("0702601001", 164265),
            ])
            result = materialize(root, "illes_balears", "2025", package)
            self.assertEqual(result["status"], "READY")
            self.assertEqual(result["partition_mode"], "physical_components_hamilton")
            self.assertEqual(
                {"07-C01":44,"07-C02":6,"07-C03":1,"07-C04":8},
                result["partition_districts"],
            )
            self.assertEqual("institutional_chamber_size_only", result["k_reference_scope"])
            self.assertEqual("ddd_design_policy", result["apportionment_source"])
            self.assertFalse(result["legal_apportionment_reused"])
            self.assertEqual(["07-C03"], result["population_floor_exempt_partitions"])
            self.assertTrue(all(x["floor_exception_governed"] for x in result["partition_apportionment_audit"].values()))
            cfg = yaml.safe_load((root / result["contract_path"]).read_text(encoding="utf-8"))
            self.assertEqual(cfg["modulos"]["modulo_04_generar_semillas"]["province_field"], "DDD_PARTITION")
            self.assertEqual(cfg["validation"]["hard_partition_mode"], "physical_components")
        finally:
            td.cleanup()


if __name__ == "__main__":
    unittest.main()
