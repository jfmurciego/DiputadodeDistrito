from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import yaml

from herramientas.materializar_evidencia_pre_m04 import build_evidence
from herramientas.resolver_ejecucion_completa import build_plan, generation_enablement


SHA_A = "a" * 64
SHA_B = "b" * 64
SHA_C = "c" * 64
SHA_D = "d" * 64
COMMIT = "1" * 40
ROOT = Path(__file__).resolve().parents[1]
REAL_TARGETS = ("cataluna", "comunidad_valenciana", "madrid", "region_de_murcia", "ceuta", "melilla")


def contract(*, partitioned: bool) -> dict:
    base = "territorios/demo/.cache/ddd/preparacion/{run_name}"
    m01_out = f"{base}/demo_2025_m01.geojson.zip"
    m03_graph = f"{base}/demo_2025_m03.json"
    m04_in = f"{base}/demo_2025_m03u.geojson.zip" if partitioned else m01_out
    cfg = {
        "meta": {
            "territory_id": "demo",
            "territory": "Demo",
            "run_name": "demo_2025",
            "year": 2025,
            "contract_level": "production_m01_m06",
            "production_authorization": "AUTHORIZED",
            "status": "production_ready_auto_materialized",
        },
        "territory_contract": {
            "k_districts": 2,
            "population_floor_ratio": 0.8,
            "population_cap_ratio": 1.75,
            "target_tolerance_ratio": 0.12,
            "oversized_municipality_rule": "split_only_above_hard_cap",
            "municipality_atomicity_limit_ratio": 1.75,
            "status": "topology_contract_candidate",
        },
        "modulos": {
            "modulo_01_preparar_base_territorial": {"out_geojson": m01_out},
            "modulo_02_construir_adyacencias": {
                "predicate": "contact",
                "working_crs": "EPSG:3035",
                "min_shared_border_m": 1,
                "max_precision_overlap_area_m2": 1,
                "buffer_m": 0,
                "simplify_m": 0,
                "topology_bridges": [],
            },
            "modulo_03_construir_grafo": {"out_graph_json": m03_graph},
            "modulo_04_generar_semillas": {
                "in_graph_json": m03_graph,
                "in_geojson": m04_in,
                "out_geojson": f"{base}/m04.geojson.zip",
                "municipality_field": "CUMUN",
                "k_districts": 2,
            },
            "modulo_05_optimizar_distritos": {
                "in_graph_json": m03_graph,
                "in_geojson": f"{base}/m04.geojson.zip",
                "out_geojson": f"{base}/m05.geojson.zip",
                "municipality_field": "CUMUN",
            },
            "modulo_06_consolidar_distritos": {
                "in_geojson": f"{base}/m05.geojson.zip",
                "municipality_field": "CUMUN",
                "expected_districts": 2,
            },
        },
        "validation": {
            "expected_districts": 2,
            "expected_sections_geometry": 4,
            "expected_population_total_2025": 400,
            "municipality_field": "CUMUN",
            "require_graph_contiguity": True,
            "require_municipality_discipline": True,
        },
    }
    if partitioned:
        cfg["partitioning"] = {
            "enabled": True,
            "strategy": "connected_internal_units",
            "input_geojson": m01_out,
            "graph": m03_graph,
            "output_geojson": m04_in,
            "output_report": f"{base}/partition.json",
            "partition_unit_field": "CUMUN",
            "municipality_field": "CUMUN",
            "atomicity_ratio": 1.75,
            "chunk_ratio": 0.25,
        }
    return cfg


def write_fixture(root: Path, *, partitioned: bool):
    contract_path = root / "territorios/demo/config/demo_2025.yaml"
    contract_path.parent.mkdir(parents=True, exist_ok=True)
    contract_path.write_text(yaml.safe_dump(contract(partitioned=partitioned), sort_keys=False), encoding="utf-8")

    catalog_path = root / "configuracion/catalogo_preparacion.yaml"
    catalog_path.parent.mkdir(parents=True, exist_ok=True)
    catalog_path.write_text(
        yaml.safe_dump(
            {
                "schema": "ddd-preparation-catalog/1.1",
                "default_edition": "2025",
                "territories": [{
                    "territory_id": "demo",
                    "name": "Demo",
                    "editions": {
                        "2025": {
                            "territory_declared": True,
                            "preparation_status": "READY",
                            "territorial_source_declaration": "territorios/demo/config/fuentes_oficiales.yaml",
                            "electoral_source_declaration": None,
                            "territorial_sources_prepared": True,
                            "contract_path": "territorios/demo/config/demo_2025.yaml",
                            "territorial_contract_complete": True,
                            "production_authorization": "AUTHORIZED",
                            "territorial_product_available": False,
                            "territorial_certification": "NOT_CERTIFIED",
                            "electoral_source_prepared": False,
                            "electoral_product_available": False,
                            "last_valid_checkpoint": {"stage": "M03", "run_id": 123},
                            "preparation_evidence": {
                                "run_id": 123,
                                "artifact_name": "ddd-source-package-demo-2025-123",
                                "artifact_sha256": SHA_A,
                                "package_sha256": SHA_B,
                            },
                        }
                    },
                }],
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )

    m03 = root / "m03-state"
    m03.mkdir()
    (m03 / "report.json").write_text(
        json.dumps({
            "module": "03",
            "version": "7.4.1",
            "nodes": 4,
            "edges": 3,
            "isolated": 0,
            "total_pop": 400,
            "global_component_audit": {"components": 1},
            "province_component_audit": {"disconnected": 0},
            "municipality_component_audit": {"disconnected": 0},
        }),
        encoding="utf-8",
    )
    job = root / "job.json"
    if partitioned:
        job_data = {
            "schema": "ddd.internal-units-job/1.0",
            "status": "PREPARED",
            "strategy": "connected_internal_units",
            "output_geojson": "territorios/demo/.cache/ddd/preparacion/demo_2025/demo_2025_m03u.geojson.zip",
        }
    else:
        job_data = {
            "schema": "ddd.internal-units-job/1.0",
            "status": "NOOP",
            "strategy": None,
        }
    job.write_text(json.dumps(job_data), encoding="utf-8")
    return contract_path, m03, job


class PreM04EntrypointTests(unittest.TestCase):
    def test_materializer_module_entrypoint_is_importable_from_repository_root(self):
        completed = subprocess.run(
            [sys.executable, "-m", "herramientas.materializar_evidencia_pre_m04", "--help"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)

    def test_workflow_invokes_materializer_as_module(self):
        workflow = (ROOT / ".github/workflows/_reutilizable-generacion-territorial.yml").read_text(encoding="utf-8")
        self.assertIn("python -m herramientas.materializar_evidencia_pre_m04", workflow)
        self.assertNotIn("python herramientas/materializar_evidencia_pre_m04.py", workflow)


class DurablePreM04EvidenceTests(unittest.TestCase):
    def build(self, root: Path, *, partitioned: bool):
        contract_path, m03, job = write_fixture(root, partitioned=partitioned)
        with patch("herramientas.materializar_evidencia_pre_m04._git_head", return_value=COMMIT):
            evidence = build_evidence(
                root_dir=root,
                territory_id="demo",
                edition="2025",
                run_id=123,
                contract_path="territorios/demo/config/demo_2025.yaml",
                m03_state_dir=m03,
                partition_job=job,
                m03_artifact_sha256=SHA_C,
                m03u_artifact_sha256=SHA_D,
                partition_artifact_sha256=SHA_A,
            )
        return contract_path, evidence

    def gate(self, root: Path, evidence):
        return generation_enablement(
            root_dir=root,
            contract_path="territorios/demo/config/demo_2025.yaml",
            territory_id="demo",
            certified_product_ready=False,
            first_generation_evidence=evidence,
            preparation_evidence={
                "run_id": 123,
                "artifact_name": "ddd-source-package-demo-2025-123",
                "artifact_sha256": SHA_A,
                "package_sha256": SHA_B,
            },
            require_source=True,
        )

    def test_single_province_complete_evidence_enables_effective_gate(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            _, evidence = self.build(root, partitioned=False)
            self.assertEqual(evidence["partitioning"]["status"], "NOOP")
            self.assertEqual(self.gate(root, evidence), {
                "allowed": True,
                "route": "validated_pre_m04_topology",
            })

    def test_island_partition_complete_evidence_enables_effective_gate(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            _, evidence = self.build(root, partitioned=True)
            self.assertEqual(evidence["partitioning"]["status"], "PREPARED")
            self.assertEqual(evidence["partitioning"]["strategy"], "connected_internal_units")
            self.assertEqual(self.gate(root, evidence), {
                "allowed": True,
                "route": "validated_pre_m04_topology",
            })

    def test_absent_evidence_is_precisely_blocked(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            write_fixture(root, partitioned=False)
            gate = self.gate(root, None)
            self.assertFalse(gate["allowed"])
            self.assertEqual(gate["capability"], "CAP_PRE_M04_EVIDENCE")

    def test_contradictory_graph_evidence_is_precisely_blocked(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            _, evidence = self.build(root, partitioned=False)
            evidence["graph"]["nodes"] = 5
            gate = self.gate(root, evidence)
            self.assertFalse(gate["allowed"])
            self.assertEqual(gate["capability"], "CAP_PRE_M04_EVIDENCE")
            self.assertIn("número de secciones", gate["reason"])

    def test_incomplete_partition_evidence_is_precisely_blocked(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            _, evidence = self.build(root, partitioned=True)
            evidence["partitioning"]["job_artifact_sha256"] = ""
            gate = self.gate(root, evidence)
            self.assertFalse(gate["allowed"])
            self.assertEqual(gate["capability"], "CAP_PRE_M04_EVIDENCE")
            self.assertIn("particionado", gate["reason"])


class RealTerritoryPreM04ContractTests(unittest.TestCase):
    def _state_and_contract(self, territory_id: str):
        catalog = yaml.safe_load((ROOT / "configuracion/catalogo_preparacion.yaml").read_text(encoding="utf-8")) or {}
        row = next(r for r in catalog.get("territories") or [] if r.get("territory_id") == territory_id)
        state = (row.get("editions") or {}).get("2025") or {}
        contract_path = state.get("contract_path")
        self.assertTrue(contract_path, territory_id)
        contract = yaml.safe_load((ROOT / contract_path).read_text(encoding="utf-8")) or {}
        return state, contract_path, contract

    def _build_real_evidence(self, territory_id: str):
        state, contract_path, contract = self._state_and_contract(territory_id)
        prep = state.get("preparation_evidence") or {}
        run_id = int(prep["run_id"])
        validation = contract.get("validation") or {}
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            m03 = tmp / "m03"
            m03.mkdir()
            (m03 / "report.json").write_text(
                json.dumps({
                    "module": "03",
                    "version": "7.4.1",
                    "nodes": validation.get("expected_sections_geometry"),
                    "edges": max(0, int(validation.get("expected_sections_geometry") or 1) - 1),
                    "isolated": 0,
                    "total_pop": validation.get("expected_population_total_2025"),
                    "global_component_audit": {"components": 1},
                    "province_component_audit": {"disconnected": 0},
                    "municipality_component_audit": {"disconnected": 0},
                }),
                encoding="utf-8",
            )
            job = tmp / "job.json"
            job.write_text(json.dumps({
                "schema": "ddd.internal-units-job/1.0",
                "status": "NOOP",
                "strategy": None,
            }), encoding="utf-8")
            with patch("herramientas.materializar_evidencia_pre_m04._git_head", return_value=COMMIT):
                evidence = build_evidence(
                    root_dir=ROOT,
                    territory_id=territory_id,
                    edition="2025",
                    run_id=run_id,
                    contract_path=contract_path,
                    m03_state_dir=m03,
                    partition_job=job,
                    m03_artifact_sha256=SHA_C,
                    m03u_artifact_sha256=SHA_D,
                    partition_artifact_sha256=SHA_A,
                )
        return state, contract_path, prep, evidence

    def test_real_pending_territories_receive_pre_m04_accreditation_before_generation_gate(self):
        for territory_id in REAL_TARGETS:
            with self.subTest(territory=territory_id):
                state, contract_path, prep, evidence = self._build_real_evidence(territory_id)
                self.assertFalse(state.get("territorial_product_available"))
                self.assertEqual(evidence["decision"], "READY_FOR_FIRST_GENERATION")
                self.assertEqual(evidence["stage"], "M03U")
                self.assertEqual(evidence["source"]["artifact_name"], prep["artifact_name"])
                self.assertEqual(evidence["source"]["artifact_sha256"], str(prep["artifact_sha256"]).removeprefix("sha256:"))
                self.assertEqual(evidence["source"]["package_sha256"], str(prep["package_sha256"]).removeprefix("sha256:"))
                gate = generation_enablement(
                    root_dir=ROOT,
                    contract_path=contract_path,
                    territory_id=territory_id,
                    certified_product_ready=False,
                    first_generation_evidence=evidence,
                    preparation_evidence=prep,
                    require_source=True,
                )
                self.assertEqual(gate, {"allowed": True, "route": "validated_pre_m04_topology"})

    def test_missing_or_contradictory_pre_m04_accreditation_still_blocks_real_targets(self):
        for territory_id in REAL_TARGETS:
            with self.subTest(territory=territory_id, case="missing"):
                state, contract_path, prep, evidence = self._build_real_evidence(territory_id)
                missing = generation_enablement(
                    root_dir=ROOT,
                    contract_path=contract_path,
                    territory_id=territory_id,
                    certified_product_ready=False,
                    first_generation_evidence=None,
                    preparation_evidence=prep,
                    require_source=True,
                )
                self.assertFalse(missing["allowed"])
                self.assertEqual(missing["capability"], "CAP_PRE_M04_EVIDENCE")
            with self.subTest(territory=territory_id, case="contradictory"):
                evidence["graph"]["nodes"] = int(evidence["graph"]["nodes"]) + 1
                contradictory = generation_enablement(
                    root_dir=ROOT,
                    contract_path=contract_path,
                    territory_id=territory_id,
                    certified_product_ready=False,
                    first_generation_evidence=evidence,
                    preparation_evidence=prep,
                    require_source=True,
                )
                self.assertFalse(contradictory["allowed"])
                self.assertEqual(contradictory["capability"], "CAP_PRE_M04_EVIDENCE")

    def test_00_reuse_plan_schedules_pre_m04_before_first_generation_for_real_targets(self):
        catalog = ROOT / "configuracion/catalogo_preparacion.yaml"
        for territory_id in REAL_TARGETS:
            with self.subTest(territory=territory_id):
                state, _, _ = self._state_and_contract(territory_id)
                self.assertTrue(state.get("territorial_sources_prepared"))
                self.assertFalse(state.get("territorial_product_available"))
                self.assertFalse((state.get("evidence") or {}).get("generation_preflight"))
                plan = build_plan(
                    territory=territory_id,
                    edition="2025",
                    execution_mode="reuse",
                    catalog=catalog,
                    root_dir=ROOT,
                    optimization_algorithm="Canónico",
                    force_selected_algorithm=False,
                )
                self.assertTrue(plan["pre_m04_accreditation_planned"])
                self.assertTrue(plan["run_prepare_territorial"])
                self.assertTrue(plan["run_generate"])
                self.assertEqual(
                    plan["generation_gate"],
                    {"allowed": True, "route": "planned_pre_m04_accreditation"},
                )
                self.assertEqual(plan["existing"]["territorial_source"]["decision"], "VALIDADO")

    def test_00_wiring_waits_for_validated_pre_m04_before_generation(self):
        full = yaml.safe_load((ROOT / ".github/workflows/ejecucion-completa-proyecto.yml").read_text(encoding="utf-8"))
        preparation = yaml.safe_load((ROOT / ".github/workflows/preparacion-fuentes.yml").read_text(encoding="utf-8"))
        reusable = yaml.safe_load((ROOT / ".github/workflows/_reutilizable-generacion-territorial.yml").read_text(encoding="utf-8"))
        full_jobs = full["jobs"]
        prep_jobs = preparation["jobs"]

        self.assertEqual(full_jobs["preparar_territorial"]["uses"], "./.github/workflows/preparacion-fuentes.yml")
        self.assertIn("preparar_territorial", full_jobs["puerta_01"]["needs"])
        self.assertIn("puerta_01", full_jobs["generar"]["needs"])
        self.assertIn("needs.puerta_01.result == 'success'", full_jobs["generar"]["if"])

        self.assertIn("pre_m04", prep_jobs["resultado"]["needs"])
        terminal = prep_jobs["resultado"]["steps"][-1]
        self.assertIn("PRE_M04_RESULT", terminal["env"])
        self.assertIn('[[ "$PERSIST_STATE" == true && "$PRE_M04_RESULT" != success ]]', terminal["run"])
        self.assertTrue(prep_jobs["pre_m04"]["with"]["preflight_only"])

        self.assertIn("!inputs.preflight_only", reusable["jobs"]["m04"]["if"])
        self.assertIn("inputs.preflight_only", reusable["jobs"]["pre_m04_evidence"]["if"])

    def test_00_generation_handoff_reloads_durable_pre_m04_and_blocks_nonpersistent_plan(self):
        full_text = (ROOT / ".github/workflows/ejecucion-completa-proyecto.yml").read_text(encoding="utf-8")
        full = yaml.safe_load(full_text)
        production_text = (ROOT / ".github/workflows/produccion-distritos.yml").read_text(encoding="utf-8")
        production = yaml.safe_load(production_text)

        plan_outputs = full["jobs"]["planificar"]["outputs"]
        self.assertIn("pre_m04_accreditation_planned", plan_outputs)
        self.assertIn(
            "La acreditación pre-M04 planificada exige persist_state=true antes de habilitar generación.",
            full_text,
        )

        generate = full["jobs"]["generar"]
        self.assertEqual(generate["with"]["require_generation_gate"], True)
        self.assertIn("pre_m04_accreditation_planned == 'true'", generate["with"]["source_ref"])
        self.assertIn("'main'", generate["with"]["source_ref"])

        triggers = production.get("on") or production.get(True) or {}
        call_inputs = (triggers.get("workflow_call") or {}).get("inputs") or {}
        self.assertIn("require_generation_gate", call_inputs)
        resolver_steps = production["jobs"]["resolver_interfaz"]["steps"]
        gate = next(step for step in resolver_steps if step.get("name") == "Validar puerta efectiva antes de Formación inicial")
        self.assertEqual(gate["if"], "${{ inputs.require_generation_gate }}")
        body = gate["run"]
        self.assertIn("generation_enablement(", body)
        self.assertIn("GENERATION_CONTRACT_BLOCK:", body)

        names = [step.get("name") for step in resolver_steps]
        self.assertLess(
            names.index("Validar puerta efectiva antes de Formación inicial"),
            names.index("Resolver paquete territorial preparado"),
        )

    def test_preparation_workflow_persists_pre_m04_before_terminal_success_and_never_runs_m04(self):
        preparation = yaml.safe_load((ROOT / ".github/workflows/preparacion-fuentes.yml").read_text(encoding="utf-8"))
        reusable = yaml.safe_load((ROOT / ".github/workflows/_reutilizable-generacion-territorial.yml").read_text(encoding="utf-8"))
        jobs = preparation["jobs"]
        self.assertEqual(jobs["pre_m04"]["needs"], ["resolver", "territoriales", "registrar"])
        self.assertTrue(jobs["pre_m04"]["with"]["preflight_only"])
        self.assertIn("pre_m04", jobs["resultado"]["needs"])
        self.assertIn("PRE_M04_RESULT", jobs["resultado"]["steps"][-1]["env"])
        self.assertIn("!inputs.preflight_only", reusable["jobs"]["m04"]["if"])
        self.assertIn("inputs.preflight_only", reusable["jobs"]["pre_m04_evidence"]["if"])


if __name__ == "__main__":
    unittest.main()
