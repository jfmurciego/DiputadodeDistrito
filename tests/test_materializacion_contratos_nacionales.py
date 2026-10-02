from __future__ import annotations

import ast
import csv
import hashlib
import copy
import io
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

import yaml
import geopandas as gpd
from shapely.geometry import box

from ddd_core.territory_contract import validate_production_contract
from herramientas.compatibilidad_poblacion_seccionado import build_materialized_report
from herramientas.materializar_contrato_generacion import (
    component_apportionment_audit,
    component_hamilton,
    hamilton,
    materialize,
)
from herramientas.resolver_ejecucion_completa import build_plan, generation_enablement
from herramientas.preparar_particiones_fisicas_m04 import prepare as prepare_physical_m04_input
from herramientas._resolver_ejecucion_completa_core import (
    _bridge_signature,
    _contract_generation_binding,
    _hard_partition_spec,
    _pre_m04_implementation_binding,
)

ROOT = Path(__file__).resolve().parents[1]
POLICY = ROOT / "configuracion/politica_generacion_territorial_2025.yaml"
MASTER = ROOT / "configuracion/catalogo_territorios_espana_2025.yaml"
PARTITIONS = ROOT / "configuracion/particiones_insulares_2025.json"


def population_package(
    root: Path,
    rows: list[tuple[str, int]],
    delimiter: str = "\t",
    *,
    population_year: int = 2025,
    section_year: int = 2025,
) -> Path:
    """Paquete sintético acreditado: población + seccionado + inventario + compatibilidad."""
    package = root / "package"
    package.mkdir(parents=True, exist_ok=True)

    payload = io.StringIO()
    writer = csv.writer(payload, delimiter=delimiter, lineterminator="\n")
    writer.writerow(["Total Nacional","Provincias","Municipios","Secciones","Sexo","Edad","Periodo","Total"])
    for section, population in rows:
        writer.writerow([
            "Total Nacional", section[:2], section[:5], section,
            "Total", "Todas las edades", str(population_year), f"{population:,}".replace(",", "."),
        ])
    population_zip = package / "65034.csv.zip"
    with zipfile.ZipFile(population_zip, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("65034.csv", payload.getvalue().encode("utf-8-sig"))

    master = yaml.safe_load(
        (root / "configuracion/catalogo_territorios_espana_2025.yaml").read_text(encoding="utf-8")
    )
    territory_id = master["territories"][0]["territory_id"]

    evidence = package / "evidence"
    materialized = evidence / "materialized" / "inputs"
    materialized.mkdir(parents=True)
    shutil.copy2(population_zip, materialized / "65034.csv.zip")

    section_zip = materialized / f"seccionado_{section_year}.zip"
    with tempfile.TemporaryDirectory() as geo_td:
        geo_root = Path(geo_td)
        shp = geo_root / "seccionado.shp"
        gdf = gpd.GeoDataFrame(
            {"CUSEC": [section for section, _ in rows]},
            geometry=[box(index, 0, index + 0.8, 0.8) for index, _ in enumerate(rows)],
            crs="EPSG:4326",
        )
        gdf.to_file(shp)
        with zipfile.ZipFile(section_zip, "w", zipfile.ZIP_DEFLATED) as zf:
            for path in sorted(geo_root.glob("seccionado.*")):
                zf.write(path, arcname=path.name)

    def sha(path: Path) -> str:
        return hashlib.sha256(path.read_bytes()).hexdigest()

    inventory = {
        "sources": [
            {
                "role": "population",
                "source_id": "synthetic_population",
                "path": "inputs/65034.csv.zip",
                "bytes": (materialized / "65034.csv.zip").stat().st_size,
                "sha256": sha(materialized / "65034.csv.zip"),
            },
            {
                "role": "target_sectioning",
                "source_id": "synthetic_sectioning",
                "path": f"inputs/seccionado_{section_year}.zip",
                "bytes": section_zip.stat().st_size,
                "sha256": sha(section_zip),
            },
        ]
    }
    (evidence / "inventario_fuentes.json").write_text(
        json.dumps(inventory, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    build_materialized_report(
        evidence_dir=evidence,
        territory_id=territory_id,
        edition="2025",
        population_year=population_year,
        section_year=section_year,
        inventory=inventory,
    )

    bundle = package / "prepared_sources.zip"
    with zipfile.ZipFile(bundle, "w", zipfile.ZIP_DEFLATED) as zf:
        for path in sorted(p for p in evidence.rglob("*") if p.is_file()):
            zf.write(path, arcname=path.relative_to(evidence).as_posix())
    manifest = {
        "territory_id": territory_id,
        "edition": 2025,
        "population_year": population_year,
        "section_year": section_year,
        "source_year": section_year,
        "path": bundle.name,
        "bytes": bundle.stat().st_size,
        "sha256": sha(bundle),
        "records": len(rows),
        "origin": "synthetic-test-fixture",
        "acquired_at": "2026-10-01T00:00:00+00:00",
    }
    (package / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
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
            result = materialize(root, "principado_de_asturias", "2025", package, population_year="2025", section_year="2025")
            self.assertEqual(result["status"], "SOURCE_PREPARED_PENDING_PRE_M04")
            cfg = yaml.safe_load((root / result["contract_path"]).read_text(encoding="utf-8"))
            self.assertEqual(cfg["validation"]["province_districts"], {"33": 45})
        finally:
            td.cleanup()

    def test_dynamic_source_manifest_admits_2023_2024_and_2026_inputs(self):
        cases = ((2023, 2023), (2024, 2024), (2025, 2026))
        for population_year, section_year in cases:
            with self.subTest(population_year=population_year, section_year=section_year):
                td = temp_root("principado_de_asturias", "Principado de Asturias", ["33"])
                try:
                    root = Path(td.name)
                    package = population_package(
                        root,
                        [("3300101001", 1_015_128)],
                        population_year=population_year,
                        section_year=section_year,
                    )
                    result = materialize(
                        root,
                        "principado_de_asturias",
                        "2025",
                        package,
                        population_year=str(population_year),
                        section_year=str(section_year),
                    )
                    contract_path = root / result["contract_path"]
                    cfg = yaml.safe_load(contract_path.read_text(encoding="utf-8"))
                    self.assertEqual(
                        cfg["io"]["input"]["seccionado"]["path"],
                        f"inputs/seccionado_{section_year}.zip",
                    )
                    source_inputs = cfg["generation_state"]["source_inputs"]
                    by_path = {row["path"]: row for row in source_inputs}
                    self.assertIn("inputs/65034.csv.zip", by_path)
                    self.assertIn(f"inputs/seccionado_{section_year}.zip", by_path)
                    self.assertRegex(
                        by_path[f"inputs/seccionado_{section_year}.zip"]["sha256"],
                        r"^[0-9a-f]{64}$",
                    )
                    admitted = validate_production_contract(
                        contract_path,
                        expected_territory="principado_de_asturias",
                    )
                    self.assertEqual("ADMITTED", admitted["status"], admitted["errors"])

                    if section_year != 2025:
                        broken = copy.deepcopy(cfg)
                        broken["generation_state"].pop("source_inputs", None)
                        contract_path.write_text(
                            yaml.safe_dump(broken, sort_keys=False, allow_unicode=True),
                            encoding="utf-8",
                        )
                        rejected = validate_production_contract(
                            contract_path,
                            expected_territory="principado_de_asturias",
                        )
                        self.assertEqual("REJECTED", rejected["status"])
                        self.assertTrue(
                            any(
                                f"seccionado_{section_year}.zip" in error
                                and "checksum" in error
                                for error in rejected["errors"]
                            ),
                            rejected["errors"],
                        )
                finally:
                    td.cleanup()

    def test_dynamic_source_manifest_rejects_invalid_digest(self):
        td = temp_root("principado_de_asturias", "Principado de Asturias", ["33"])
        try:
            root = Path(td.name)
            package = population_package(
                root,
                [("3300101001", 1_015_128)],
                population_year=2023,
                section_year=2023,
            )
            result = materialize(
                root,
                "principado_de_asturias",
                "2025",
                package,
                population_year="2023",
                section_year="2023",
            )
            contract_path = root / result["contract_path"]
            cfg = yaml.safe_load(contract_path.read_text(encoding="utf-8"))
            cfg["generation_state"]["source_inputs"][0]["sha256"] = "bad"
            contract_path.write_text(
                yaml.safe_dump(cfg, sort_keys=False, allow_unicode=True),
                encoding="utf-8",
            )
            rejected = validate_production_contract(
                contract_path,
                expected_territory="principado_de_asturias",
            )
            self.assertEqual("REJECTED", rejected["status"])
            self.assertTrue(
                any("source_inputs SHA-256 inválido" in error for error in rejected["errors"]),
                rejected["errors"],
            )
        finally:
            td.cleanup()

    def test_materializes_asturias_without_manual_contract_work(self):
        td = temp_root("principado_de_asturias", "Principado de Asturias", ["33"])
        try:
            root = Path(td.name)
            package = population_package(root, [("3300101001", 1_015_128)])
            result = materialize(root, "principado_de_asturias", "2025", package, population_year="2025", section_year="2025")
            self.assertEqual(result["status"], "SOURCE_PREPARED_PENDING_PRE_M04")
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
                result = materialize(root, territory_id, "2025", package, population_year="2025", section_year="2025")
                self.assertEqual(result["status"], "SOURCE_PREPARED_PENDING_PRE_M04", territory_id)
                self.assertEqual(result["k"], int(entry["k"]), territory_id)
                cfg = yaml.safe_load((root / result["contract_path"]).read_text(encoding="utf-8"))
                self.assertEqual(cfg["meta"]["production_authorization"], "AUTHORIZED", territory_id)
                self.assertEqual(sum(cfg["validation"]["province_districts"].values()), int(entry["k"]), territory_id)
            finally:
                td.cleanup()

    def test_archipelagos_plan_physical_input_then_require_durable_pre_m04_evidence(self):
        catalog = yaml.safe_load(
            (ROOT/"configuracion/catalogo_preparacion.yaml").read_text(encoding="utf-8")
        )
        rows = {row["territory_id"]: row for row in catalog["territories"]}
        expected = {
            "illes_balears": {"k": 59, "sections": 674, "components": 4},
            "canarias": {"k": 70, "sections": 1407, "components": 8},
        }
        for territory_id, target in expected.items():
            state = rows[territory_id]["editions"]["2025"]
            self.assertEqual("READY", state["preparation_status"], territory_id)
            self.assertTrue(state["territorial_sources_prepared"], territory_id)
            self.assertTrue(state["territorial_contract_complete"], territory_id)
            self.assertEqual("AUTHORIZED", state["production_authorization"], territory_id)
            self.assertFalse(state["territorial_product_available"], territory_id)
            self.assertEqual("NOT_CERTIFIED", state["territorial_certification"], territory_id)

            contract = yaml.safe_load((ROOT/state["contract_path"]).read_text(encoding="utf-8"))
            hard = _hard_partition_spec(contract, ROOT)
            self.assertEqual(target["k"], sum(hard["component_districts"].values()), territory_id)
            self.assertEqual(target["sections"], hard["expected_graph_nodes"], territory_id)
            self.assertEqual(target["components"], hard["expected_global_components"], territory_id)
            self.assertEqual(
                contract["modulos"]["modulo_04_generar_semillas"]["in_geojson"],
                hard["input_geojson"],
                territory_id,
            )

            gate = generation_enablement(
                root_dir=ROOT,
                contract_path=state["contract_path"],
                territory_id=territory_id,
                certified_product_ready=False,
                first_generation_evidence=None,
                preparation_evidence=state["preparation_evidence"],
                require_source=True,
            )
            self.assertFalse(gate["allowed"], territory_id)
            self.assertIn(gate["capability"], {"CAP_SOURCE", "CAP_PRE_M04_EVIDENCE"}, territory_id)

            plan = build_plan(
                territory=territory_id,
                edition="2025",
                execution_mode="reuse",
                catalog=ROOT/"configuracion/catalogo_preparacion.yaml",
                root_dir=ROOT,
            )
            durable_preflight = (state.get("evidence") or {}).get("generation_preflight")
            self.assertTrue(durable_preflight, territory_id)
            # La evidencia histórica no contiene la identidad de compatibilidad
            # exigida por el contrato nuevo: se conserva, pero no habilita.
            self.assertTrue(plan["pre_m04_accreditation_planned"], territory_id)
            self.assertTrue(plan["run_prepare_territorial"], territory_id)
            self.assertTrue(plan["run_generate"], territory_id)
            self.assertEqual("planned_pre_m04_accreditation", plan["generation_gate"]["route"], territory_id)
            self.assertFalse(plan["catalog_state"]["territorial_product_available"], territory_id)
            self.assertEqual("NOT_CERTIFIED", plan["catalog_state"]["territorial_certification"], territory_id)

    def test_historical_archipelago_preflight_does_not_bypass_new_source_identity(self):
        catalog = yaml.safe_load(
            (ROOT/"configuracion/catalogo_preparacion.yaml").read_text(encoding="utf-8")
        )
        rows = {row["territory_id"]: row for row in catalog["territories"]}
        for territory_id in ("illes_balears", "canarias"):
            state = rows[territory_id]["editions"]["2025"]
            contract = yaml.safe_load((ROOT/state["contract_path"]).read_text(encoding="utf-8"))
            hard = _hard_partition_spec(contract, ROOT)
            run_id = state["preparation_evidence"]["run_id"]
            m02 = contract["modulos"]["modulo_02_construir_adyacencias"]
            evidence = {
                "schema": "ddd.catalog-evidence/1.0",
                "kind": "generation_preflight",
                "territory_id": territory_id,
                "territory_name": rows[territory_id]["name"],
                "edition": "2025",
                "run_id": run_id,
                "source_commit": "1" * 40,
                "artifact_name": f"ddd-state-{run_id}-M03U",
                "artifact_sha256": "a" * 64,
                "decision": "READY_FOR_FIRST_GENERATION",
                "stage": "M03U",
                "source": dict(state["preparation_evidence"]),
                "implementation": _pre_m04_implementation_binding(ROOT, contract),
                "adjacency": {
                    "predicate": m02.get("predicate"),
                    "working_crs": m02.get("working_crs"),
                    "min_shared_border_m": m02.get("min_shared_border_m"),
                    "max_precision_overlap_area_m2": m02.get("max_precision_overlap_area_m2"),
                    "buffer_m": m02.get("buffer_m"),
                    "simplify_m": m02.get("simplify_m"),
                    "topology_bridges": _bridge_signature(m02.get("topology_bridges") or []),
                },
                "graph": {
                    "artifact_name": f"ddd-state-{run_id}-M03",
                    "artifact_sha256": "b" * 64,
                    "nodes": hard["expected_graph_nodes"],
                    "population": hard["expected_graph_population"],
                    "isolated": hard["expected_isolated"],
                    "global_components": hard["expected_global_components"],
                    "province_disconnected": hard["expected_province_disconnected"],
                    "municipality_disconnected": hard["expected_municipality_disconnected"],
                },
                "partitioning": {
                    "job_artifact_name": f"ddd-internal-units-{run_id}",
                    "job_artifact_sha256": "c" * 64,
                    "status": "PREPARED",
                    "strategy": "physical_components",
                    "contract_output_geojson": hard["input_geojson"],
                    "resolved_output_geojson": f"/tmp/{territory_id}_m03_particiones.geojson.zip",
                    "hard_partition_lookup": hard["lookup"],
                    "hard_partition_lookup_sha256": hard["lookup_sha256"],
                    "partition_field": hard["partition_field"],
                    "municipality_field": hard["municipality_field"],
                    "component_sections": hard["component_sections"],
                    "component_districts": hard["component_districts"],
                },
                "contract_binding": _contract_generation_binding(contract),
            }
            gate = generation_enablement(
                root_dir=ROOT,
                contract_path=state["contract_path"],
                territory_id=territory_id,
                certified_product_ready=False,
                first_generation_evidence=evidence,
                preparation_evidence=state["preparation_evidence"],
                require_source=True,
            )
            self.assertFalse(gate["allowed"], territory_id)
            self.assertIn(gate["capability"], {"CAP_SOURCE", "CAP_PRE_M04_EVIDENCE"}, territory_id)
            self.assertFalse(state["territorial_product_available"], territory_id)
            self.assertEqual("NOT_CERTIFIED", state["territorial_certification"], territory_id)

            bad_digest = copy.deepcopy(evidence)
            bad_digest["partitioning"]["hard_partition_lookup_sha256"] = "d" * 64
            blocked = generation_enablement(
                root_dir=ROOT,
                contract_path=state["contract_path"],
                territory_id=territory_id,
                certified_product_ready=False,
                first_generation_evidence=bad_digest,
                preparation_evidence=state["preparation_evidence"],
                require_source=True,
            )
            self.assertFalse(blocked["allowed"], territory_id)
            self.assertEqual("CAP_SOURCE", blocked["capability"], territory_id)
            self.assertIn("identidad completa", blocked["reason"], territory_id)

    def test_archipelago_physical_input_rejects_missing_lookup_and_inconsistent_apportionment(self):
        contract = yaml.safe_load(
            (ROOT/"territorios/illes_balears/config/illes_balears_2025.yaml").read_text(encoding="utf-8")
        )
        missing = copy.deepcopy(contract)
        missing["validation"]["hard_partition_lookup"] = "configuracion/no-existe.json"
        with self.assertRaisesRegex(ValueError, "lookup"):
            _hard_partition_spec(missing, ROOT)

        inconsistent = copy.deepcopy(contract)
        inconsistent["validation"]["province_districts"]["07-C01"] += 1
        with self.assertRaisesRegex(ValueError, "K"):
            _hard_partition_spec(inconsistent, ROOT)

        incomplete = copy.deepcopy(contract)
        incomplete["validation"]["partition_apportionment_audit"].pop("07-C04")
        with self.assertRaisesRegex(ValueError, "cubren exactamente"):
            _hard_partition_spec(incomplete, ROOT)

    def test_physical_preparer_materializes_verifiable_m04_input_without_running_seed_engine(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root/"modulos").mkdir()
            (root/"configuracion").mkdir()
            (root/"modulos/04_generar_semillas.py").symlink_to(
                ROOT/"modulos/04_generar_semillas.py"
            )

            source = root/"source.geojson.zip"
            geojson = {
                "type": "FeatureCollection",
                "features": [
                    {"type": "Feature", "properties": {"CUSEC_KEY": "0700101001", "CUMUN": "07001"}, "geometry": {"type": "Point", "coordinates": [1, 1]}},
                    {"type": "Feature", "properties": {"CUSEC_KEY": "0700201001", "CUMUN": "07002"}, "geometry": {"type": "Point", "coordinates": [2, 2]}},
                    {"type": "Feature", "properties": {"CUSEC_KEY": "0700201002", "CUMUN": "07002"}, "geometry": {"type": "Point", "coordinates": [2.1, 2.1]}},
                ],
            }
            with zipfile.ZipFile(source, "w", zipfile.ZIP_DEFLATED) as zf:
                zf.writestr("source.geojson", json.dumps(geojson))

            lookup = root/"configuracion/particiones.json"
            lookup.write_text(json.dumps({
                "schema": "ddd-archipelago-partitions/1.1",
                "edition": 2025,
                "territories": {
                    "demo": {
                        "partition_mode": "physical_components",
                        "components": {
                            "A": {"province_code": "07", "section_count": 1},
                            "B": {"province_code": "07", "section_count": 2},
                        },
                        "municipality_to_partition": {"07001": "A", "07002": "B"},
                        "section_overrides": {},
                    }
                },
            }), encoding="utf-8")
            target = root/"m03_particiones.geojson.zip"
            params = root/"demo.yaml"
            params.write_text(yaml.safe_dump({
                "meta": {"territory_id": "demo", "run_name": "demo_2025", "year": 2025},
                "territory_contract": {"k_districts": 2},
                "modulos": {
                    "modulo_01_preparar_base_territorial": {"out_geojson": str(source)},
                    "modulo_02_construir_adyacencias": {"topology_bridges": []},
                    "modulo_04_generar_semillas": {
                        "source_geojson": str(source),
                        "in_geojson": str(target),
                        "id_field": "CUSEC_KEY",
                        "province_field": "DDD_PARTITION",
                        "municipality_field": "DDD_MUNICIPALITY_PARTITION",
                        "district_apportionment": "hamilton_components",
                        "hard_partition_lookup": str(lookup),
                        "hard_partition_territory_id": "demo",
                    },
                },
                "validation": {
                    "hard_partition_mode": "physical_components",
                    "hard_partition_lookup": str(lookup),
                    "province_apportionment": "hamilton_components",
                    "province_field": "DDD_PARTITION",
                    "municipality_field": "DDD_MUNICIPALITY_PARTITION",
                    "province_districts": {"A": 1, "B": 1},
                    "partition_populations": {"A": 100, "B": 200},
                    "partition_apportionment_audit": {
                        "A": {"population": 100, "districts": 1, "floor_exception_required": False, "floor_exception_governed": True},
                        "B": {"population": 200, "districts": 1, "floor_exception_required": False, "floor_exception_governed": True},
                    },
                    "population_floor_exempt_partitions": [],
                },
            }, sort_keys=False), encoding="utf-8")

            source_properties = [feature["properties"] for feature in geojson["features"]]
            self.assertTrue(all("DDD_PARTITION" not in props for props in source_properties))
            self.assertTrue(all("DDD_MUNICIPALITY_PARTITION" not in props for props in source_properties))

            job = prepare_physical_m04_input(params, "123", root_dir=root)
            self.assertTrue(target.is_file())
            self.assertEqual("PREPARED", job["status"])
            self.assertEqual("physical_components", job["strategy"])
            self.assertEqual({"A": 1, "B": 2}, job["component_sections"])
            self.assertEqual({"A": 1, "B": 1}, job["component_districts"])
            self.assertEqual(hashlib.sha256(lookup.read_bytes()).hexdigest(), job["hard_partition_lookup_sha256"])

            with zipfile.ZipFile(target, "r") as zf:
                member = next(name for name in zf.namelist() if name.lower().endswith(".geojson"))
                materialized = json.loads(zf.read(member))
            materialized_properties = [feature["properties"] for feature in materialized["features"]]
            self.assertTrue(all("DDD_PARTITION" in props for props in materialized_properties))
            self.assertTrue(all("DDD_MUNICIPALITY_PARTITION" in props for props in materialized_properties))

    def test_physical_preparer_production_module_invocation_works_for_both_archipelagos(self):
        workflow = (ROOT/".github/workflows/_reutilizable-generacion-territorial.yml").read_text(
            encoding="utf-8"
        )
        self.assertIn(
            "-m herramientas.preparar_particiones_fisicas_m04",
            workflow,
        )
        self.assertNotIn(
            "/app/herramientas/preparar_particiones_fisicas_m04.py",
            workflow,
        )

        for territory_id in ("illes_balears", "canarias"):
            with self.subTest(territory=territory_id), tempfile.TemporaryDirectory() as td:
                root = Path(td)
                source = root/"source.geojson.zip"
                target = root/"m03_particiones.geojson.zip"
                lookup = root/"particiones.json"
                params = root/f"{territory_id}.yaml"
                report = root/"job.json"

                geojson = {
                    "type": "FeatureCollection",
                    "features": [
                        {
                            "type": "Feature",
                            "properties": {"CUSEC_KEY": "0700101001", "CUMUN": "07001"},
                            "geometry": {"type": "Point", "coordinates": [1, 1]},
                        },
                        {
                            "type": "Feature",
                            "properties": {"CUSEC_KEY": "0700201001", "CUMUN": "07002"},
                            "geometry": {"type": "Point", "coordinates": [2, 2]},
                        },
                        {
                            "type": "Feature",
                            "properties": {"CUSEC_KEY": "0700201002", "CUMUN": "07002"},
                            "geometry": {"type": "Point", "coordinates": [2.1, 2.1]},
                        },
                    ],
                }
                with zipfile.ZipFile(source, "w", zipfile.ZIP_DEFLATED) as zf:
                    zf.writestr("source.geojson", json.dumps(geojson))

                lookup.write_text(
                    json.dumps({
                        "schema": "ddd-archipelago-partitions/1.1",
                        "edition": 2025,
                        "territories": {
                            territory_id: {
                                "partition_mode": "physical_components",
                                "components": {
                                    "A": {"province_code": "07", "section_count": 1},
                                    "B": {"province_code": "07", "section_count": 2},
                                },
                                "municipality_to_partition": {
                                    "07001": "A",
                                    "07002": "B",
                                },
                                "section_overrides": {},
                            }
                        },
                    }),
                    encoding="utf-8",
                )
                params.write_text(
                    yaml.safe_dump({
                        "meta": {
                            "territory_id": territory_id,
                            "run_name": f"{territory_id}_2025",
                            "year": 2025,
                        },
                        "territory_contract": {"k_districts": 2},
                        "modulos": {
                            "modulo_01_preparar_base_territorial": {
                                "out_geojson": str(source),
                            },
                            "modulo_02_construir_adyacencias": {
                                "topology_bridges": [],
                            },
                            "modulo_04_generar_semillas": {
                                "source_geojson": str(source),
                                "in_geojson": str(target),
                                "id_field": "CUSEC_KEY",
                                "province_field": "DDD_PARTITION",
                                "municipality_field": "DDD_MUNICIPALITY_PARTITION",
                                "district_apportionment": "hamilton_components",
                                "hard_partition_lookup": str(lookup),
                                "hard_partition_territory_id": territory_id,
                            },
                        },
                        "validation": {
                            "hard_partition_mode": "physical_components",
                            "hard_partition_lookup": str(lookup),
                            "province_apportionment": "hamilton_components",
                            "province_field": "DDD_PARTITION",
                            "municipality_field": "DDD_MUNICIPALITY_PARTITION",
                            "province_districts": {"A": 1, "B": 1},
                            "partition_populations": {"A": 100, "B": 200},
                            "partition_apportionment_audit": {
                                "A": {
                                    "population": 100,
                                    "districts": 1,
                                    "floor_exception_required": False,
                                    "floor_exception_governed": True,
                                },
                                "B": {
                                    "population": 200,
                                    "districts": 1,
                                    "floor_exception_required": False,
                                    "floor_exception_governed": True,
                                },
                            },
                            "population_floor_exempt_partitions": [],
                        },
                    }, sort_keys=False),
                    encoding="utf-8",
                )

                result = subprocess.run(
                    [
                        sys.executable,
                        "-m",
                        "herramientas.preparar_particiones_fisicas_m04",
                        "--params",
                        str(params),
                        "--run-id",
                        f"test-{territory_id}",
                        "--job-report",
                        str(report),
                    ],
                    cwd=ROOT,
                    text=True,
                    capture_output=True,
                    check=False,
                )
                self.assertEqual(
                    0,
                    result.returncode,
                    f"{territory_id}: stdout={result.stdout}\nstderr={result.stderr}",
                )
                payload = json.loads(report.read_text(encoding="utf-8"))
                self.assertEqual("PREPARED", payload["status"], territory_id)
                self.assertEqual("physical_components", payload["strategy"], territory_id)
                self.assertTrue(target.is_file(), territory_id)

    def test_real_archipelago_contracts_separate_m02_source_fields_from_m04_partition_fields(self):
        for territory_id in ("illes_balears", "canarias"):
            with self.subTest(territory=territory_id):
                contract = yaml.safe_load(
                    (ROOT / f"territorios/{territory_id}/config/{territory_id}_2025.yaml").read_text(
                        encoding="utf-8"
                    )
                )
                hard = _hard_partition_spec(contract, ROOT)
                m01 = contract["modulos"]["modulo_01_preparar_base_territorial"]
                m04 = contract["modulos"]["modulo_04_generar_semillas"]
                self.assertEqual("DDD_PARTITION", hard["partition_field"])
                self.assertEqual("DDD_MUNICIPALITY_PARTITION", hard["municipality_field"])
                self.assertEqual(m04["in_geojson"], hard["input_geojson"])
                self.assertEqual(m01["out_geojson"], hard["source_geojson"])
                self.assertNotEqual(hard["source_geojson"], hard["input_geojson"])

    def test_m03_uses_source_admin_fields_before_physical_partitions_exist(self):
        source = (ROOT/"modulos/03_construir_grafo.py").read_text(encoding="utf-8")
        tree = ast.parse(source)
        function = next(
            node for node in tree.body
            if isinstance(node, ast.FunctionDef) and node.name == "graph_admin_fields"
        )
        namespace = {}
        exec(compile(ast.Module(body=[function], type_ignores=[]), "<graph_admin_fields>", "exec"), namespace)
        resolve = namespace["graph_admin_fields"]
        self.assertEqual(
            ("CPRO", "CUMUN", "NMUN"),
            resolve({
                "hard_partition_mode": "physical_components",
                "province_field": "DDD_PARTITION",
                "municipality_field": "DDD_MUNICIPALITY_PARTITION",
            }),
        )
        self.assertEqual(
            ("CPRO", "CUMUN", "NMUN"),
            resolve({"province_field": "CPRO", "municipality_field": "CUMUN"}),
        )

        workflow = (ROOT/".github/workflows/_reutilizable-generacion-territorial.yml").read_text(encoding="utf-8")
        self.assertIn("hard_partition_mode", workflow)
        self.assertIn("-m herramientas.preparar_particiones_fisicas_m04", workflow)
        self.assertIn("preparar_unidades_internas.py", workflow)

    def test_non_insular_preflight_behavior_is_unchanged(self):
        plan = build_plan(
            territory="cantabria",
            edition="2025",
            execution_mode="reuse",
            catalog=ROOT/"configuracion/catalogo_preparacion.yaml",
            root_dir=ROOT,
        )
        self.assertTrue(plan["pre_m04_accreditation_planned"])
        self.assertTrue(plan["run_prepare_territorial"])
        self.assertEqual("planned_pre_m04_accreditation", plan["generation_gate"]["route"])

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
            result = materialize(root, "canarias", "2025", package, population_year="2025", section_year="2025")
            self.assertEqual(result["status"], "SOURCE_PREPARED_PENDING_PRE_M04")
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
            self.assertEqual(cfg["modulos"]["modulo_02_construir_adyacencias"]["bridge_admin_level_1_field"], "CPRO")
            self.assertEqual(cfg["modulos"]["modulo_02_construir_adyacencias"]["bridge_admin_level_2_field"], "CUMUN")
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
            result = materialize(root, "illes_balears", "2025", package, population_year="2025", section_year="2025")
            self.assertEqual(result["status"], "SOURCE_PREPARED_PENDING_PRE_M04")
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
            self.assertEqual(cfg["modulos"]["modulo_02_construir_adyacencias"]["bridge_admin_level_1_field"], "CPRO")
            self.assertEqual(cfg["modulos"]["modulo_02_construir_adyacencias"]["bridge_admin_level_2_field"], "CUMUN")
        finally:
            td.cleanup()


if __name__ == "__main__":
    unittest.main()
