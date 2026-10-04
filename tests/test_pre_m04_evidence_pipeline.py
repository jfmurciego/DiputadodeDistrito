from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import yaml

from herramientas.handoff_evidencia_pre_m04 import (
    PreM04HandoffError,
    stage_handoff,
    verify_handoff,
)
from herramientas.materializar_evidencia_pre_m04 import build_evidence
from herramientas.resolver_ejecucion_completa import build_plan, generation_enablement, generation_ready_contract
from herramientas.resolver_preparacion_legislatura import resolve as resolve_current_legislature


SHA_A = "a" * 64
SHA_B = "b" * 64
SHA_C = "c" * 64
SHA_D = "d" * 64
COMMIT = "1" * 40
ROOT = Path(__file__).resolve().parents[1]
# Madrid y Ceuta dejaron de ser especímenes históricos tras la renovación
# de fuente/preflight ya presente en main. Este conjunto conserva sólo casos
# que aún deben atravesar reacreditación pre-M04 en el catálogo vivo.
REAL_TARGETS = ("cataluna", "comunidad_valenciana", "region_de_murcia")
FROM_START_PRE_M04_TARGETS = {
    "andalucia", "aragon", "principado_de_asturias", "illes_balears", "canarias",
    "cantabria", "castilla_y_leon", "castilla_la_mancha", "cataluna",
    "comunidad_valenciana", "extremadura", "galicia", "madrid", "region_de_murcia",
    "comunidad_foral_de_navarra", "pais_vasco", "la_rioja", "ceuta", "melilla",
}


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
            "source_population_year": 2025,
            "source_section_year": 2025,
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
        "generation_state": {
            "source_prepared": True,
            "generation_enabled": False,
            "package_sha256": SHA_B,
            "compatibility_identity_sha256": SHA_C,
        },
        "validation": {
            "expected_districts": 2,
            "expected_sections_geometry": 4,
            "expected_population_total_2025": 400,
            "source_baseline": {
                "schema": "ddd.source-baseline/1.0",
                "edition": "2025",
                "population_year": 2025,
                "section_year": 2025,
                "population_total": 400,
                "target_section_count": 4,
                "package_sha256": SHA_B,
                "compatibility_report_sha256": SHA_D,
                "compatibility_identity_sha256": SHA_C,
            },
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
                                "compatibility_identity_sha256": SHA_C,
                                "population_year": 2025,
                                "section_year": 2025,
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
                "compatibility_identity_sha256": SHA_C,
                "population_year": 2025,
                "section_year": 2025,
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

    def test_explicit_preparation_evidence_overrides_stale_catalog_without_changing_contract(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            contract_path, m03, job = write_fixture(root, partitioned=False)
            override = {
                "run_id": 124,
                "artifact_name": "ddd-source-package-demo-2025-124",
                "artifact_sha256": SHA_A,
                "package_sha256": SHA_B,
                "compatibility_identity_sha256": SHA_C,
                "population_year": 2025,
                "section_year": 2025,
            }
            with patch("herramientas.materializar_evidencia_pre_m04._git_head", return_value=COMMIT):
                evidence = build_evidence(
                    root_dir=root,
                    territory_id="demo",
                    edition="2025",
                    run_id=124,
                    contract_path=str(contract_path.relative_to(root)),
                    m03_state_dir=m03,
                    partition_job=job,
                    m03_artifact_sha256=SHA_C,
                    m03u_artifact_sha256=SHA_D,
                    partition_artifact_sha256=SHA_A,
                    preparation_evidence=override,
                )
            catalog = yaml.safe_load((root / "configuracion/catalogo_preparacion.yaml").read_text(encoding="utf-8"))
            stale = catalog["territories"][0]["editions"]["2025"]["preparation_evidence"]
            self.assertEqual(stale["run_id"], 123)
            self.assertEqual(evidence["run_id"], 124)
            self.assertEqual(evidence["source"]["artifact_name"], override["artifact_name"])
            self.assertEqual(evidence["effective_gate"], {
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

    def test_generation_ready_contract_delegates_to_definitive_pre_m04_validation(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            contract_path, evidence = self.build(root, partitioned=False)
            evidence_rel = "territorios/demo/evidencia/catalogo/generation_preflight_2025.json"
            evidence_path = root / evidence_rel
            evidence_path.parent.mkdir(parents=True, exist_ok=True)
            evidence_path.write_text(
                json.dumps(evidence, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )

            catalog = yaml.safe_load(
                (root / "configuracion/catalogo_preparacion.yaml").read_text(encoding="utf-8")
            )
            state = catalog["territories"][0]["editions"]["2025"]
            state["generation_enabled"] = True
            state.setdefault("evidence", {})["generation_preflight"] = evidence_rel

            effective = yaml.safe_load(contract_path.read_text(encoding="utf-8"))
            effective["generation_state"].update({
                "generation_enabled": True,
                "pre_m04_run_id": evidence["run_id"],
                "pre_m04_source_commit": evidence["source_commit"],
                "pre_m04_artifact_sha256": evidence["artifact_sha256"],
            })
            contract_path.write_text(
                yaml.safe_dump(effective, sort_keys=False),
                encoding="utf-8",
            )

            result = generation_ready_contract(
                root_dir=root,
                state=state,
                territory_id="demo",
            )
            self.assertTrue(result["allowed"])
            self.assertEqual(result["status"], "GENERATION_READY")
            self.assertEqual(result["route"], "validated_pre_m04_topology")
            self.assertEqual(result["source"]["run_id"], 123)
            self.assertEqual(result["source"]["package_sha256"], SHA_B)
            self.assertEqual(result["source"]["compatibility_identity_sha256"], SHA_C)
            self.assertEqual(result["source"]["population_year"], 2025)
            self.assertEqual(result["source"]["section_year"], 2025)
            self.assertEqual(len(result["contract_sha256"]), 64)
            self.assertEqual(len(result["generation_evidence_sha256"]), 64)

            drift = json.loads(json.dumps(state))
            drift["preparation_evidence"]["artifact_sha256"] = "0" * 64
            blocked = generation_ready_contract(
                root_dir=root,
                state=drift,
                territory_id="demo",
            )
            self.assertFalse(blocked["allowed"])
            self.assertEqual(blocked["capability"], "CAP_PRE_M04_EVIDENCE")

            not_registered = json.loads(json.dumps(state))
            not_registered["generation_enabled"] = False
            blocked_flag = generation_ready_contract(
                root_dir=root,
                state=not_registered,
                territory_id="demo",
            )
            self.assertFalse(blocked_flag["allowed"])
            self.assertEqual(blocked_flag["capability"], "CAP_PRE_M04_EVIDENCE")



    def test_generation_enablement_has_single_material_validation_chain(self):
        public = (ROOT / "herramientas/resolver_ejecucion_completa.py").read_text(encoding="utf-8")
        core = (ROOT / "herramientas/_resolver_ejecucion_completa_core.py").read_text(encoding="utf-8")
        public_block = public[
            public.index("def generation_enablement"):
            public.index("def generation_ready_contract")
        ]
        self.assertIn("return _core.generation_enablement(", public_block)
        self.assertNotIn("_core.generation_enablement = generation_enablement", public)
        self.assertEqual(core.count("def generation_enablement("), 1)
        ready_block = public[
            public.index("def generation_ready_contract"):
            public.index("def _explicit_source")
        ]
        self.assertIn("_core.generation_enablement(", ready_block)


class PreM04EvidenceHandoffRegressionTests(unittest.TestCase):
    REAL_CASES = {
        "illes_balears": {
            "run_id": 36529385760,
            "source_commit": "afe1ed53c6968e5abf7b8b2ca3726d3cc2cbca97",
            "m03u_sha256": "4a13e0b169f02c1f323937bbc9fc9cbfe01ae9660cce668d26d37e8eef7abfc2",
            "m03_sha256": "6e36edf7767522a5125e12a1b97f0da504f24866161649c708391ea4d73d0ee0",
            "partition_sha256": "8344300cc7d7e2fc2d659f6a2cb20203ca7d5a6c53a5d95e6a2a3e347f9143ea",
        },
        "canarias": {
            "run_id": 36529404391,
            "source_commit": "afe1ed53c6968e5abf7b8b2ca3726d3cc2cbca97",
            "m03u_sha256": "76b75f7bcb5016ce23e239f893240b4670a9254c67aa9111014fa8ebd40c2a31",
            "m03_sha256": "f875c59f8e890ccdf60d2a7d2a1eb0a7bc1a6511d34e9d38f98bbec1dc419cf3",
            "partition_sha256": "84e5134f8050ecbeb9b620bbb02900ebff05b3d41351ad0720cf2658e9866b94",
        },
    }

    def _real_evidence(self, territory_id: str) -> Path:
        return (
            ROOT
            / "territorios"
            / territory_id
            / "evidencia"
            / "catalogo"
            / "generation_preflight_2025.json"
        )

    def test_real_archipelago_handoff_survives_workspace_evidence_disappearance(self):
        for territory_id, expected in self.REAL_CASES.items():
            with self.subTest(territory=territory_id), tempfile.TemporaryDirectory() as td:
                temp = Path(td)
                workspace = temp / "workspace"
                persisted = (
                    workspace
                    / "territorios"
                    / territory_id
                    / "evidencia"
                    / "catalogo"
                    / "generation_preflight_2025.json"
                )
                persisted.parent.mkdir(parents=True, exist_ok=True)
                original = self._real_evidence(territory_id).read_bytes()
                persisted.write_bytes(original)

                # Este era el handoff antiguo dentro del worktree: los runs reales
                # 36529385760 y 36529404391 demostraron que desaparecía durante el rebase.
                old_workspace_handoff = workspace / ".ddd-pre-m04-evidence.json"
                old_workspace_handoff.write_bytes(original)

                runner_temp = temp / "runner-temp"
                handoff = runner_temp / f"ddd-pre-m04-evidence-{expected['run_id']}.json"
                metadata = runner_temp / f"ddd-pre-m04-handoff-{expected['run_id']}.json"
                meta = stage_handoff(
                    persisted_evidence=persisted,
                    handoff=handoff,
                    metadata=metadata,
                    territory_id=territory_id,
                    edition="2025",
                    run_id=expected["run_id"],
                    source_commit=expected["source_commit"],
                )

                payload = json.loads(handoff.read_text(encoding="utf-8"))
                self.assertEqual(payload["artifact_sha256"], expected["m03u_sha256"])
                self.assertEqual(payload["graph"]["artifact_sha256"], expected["m03_sha256"])
                self.assertEqual(
                    payload["partitioning"]["job_artifact_sha256"],
                    expected["partition_sha256"],
                )
                self.assertEqual(payload["source_commit"], expected["source_commit"])
                self.assertEqual(payload["run_id"], expected["run_id"])

                # Reproduce el límite destructivo observado: el temporal del workspace
                # desaparece, pero RUNNER_TEMP está fuera del checkout mutable.
                old_workspace_handoff.unlink()
                self.assertFalse(old_workspace_handoff.exists())
                self.assertTrue(handoff.is_file())

                verified = verify_handoff(
                    persisted_evidence=persisted,
                    handoff=handoff,
                    metadata=metadata,
                    territory_id=territory_id,
                    edition="2025",
                    run_id=expected["run_id"],
                    source_commit=expected["source_commit"],
                )
                self.assertEqual(verified["evidence_sha256"], meta["evidence_sha256"])
                self.assertEqual(handoff.read_bytes(), persisted.read_bytes())

    def test_handoff_blocks_if_preserved_bytes_do_not_match_persisted_evidence(self):
        for territory_id, expected in self.REAL_CASES.items():
            with self.subTest(territory=territory_id), tempfile.TemporaryDirectory() as td:
                temp = Path(td)
                persisted = temp / "generation_preflight_2025.json"
                persisted.write_bytes(self._real_evidence(territory_id).read_bytes())
                handoff = temp / "runner-temp" / "evidence.json"
                metadata = temp / "runner-temp" / "handoff.json"
                stage_handoff(
                    persisted_evidence=persisted,
                    handoff=handoff,
                    metadata=metadata,
                    territory_id=territory_id,
                    edition="2025",
                    run_id=expected["run_id"],
                    source_commit=expected["source_commit"],
                )

                payload = json.loads(persisted.read_text(encoding="utf-8"))
                payload["artifact_sha256"] = "0" * 64
                persisted.write_text(
                    json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
                    encoding="utf-8",
                )
                with self.assertRaisesRegex(
                    PreM04HandoffError,
                    "PRE_M04_HANDOFF_DIGEST_MISMATCH",
                ):
                    verify_handoff(
                        persisted_evidence=persisted,
                        handoff=handoff,
                        metadata=metadata,
                        territory_id=territory_id,
                        edition="2025",
                        run_id=expected["run_id"],
                        source_commit=expected["source_commit"],
                    )

    def test_workflow_stages_before_rebase_verifies_before_push_and_uploads_runner_temp(self):
        workflow_path = ROOT / ".github/workflows/_reutilizable-generacion-territorial.yml"
        workflow_text = workflow_path.read_text(encoding="utf-8")
        workflow = yaml.safe_load(workflow_text)
        job = workflow["jobs"]["pre_m04_evidence"]
        bind = next(
            step
            for step in job["steps"]
            if step.get("name") == "Vincular fuente, contrato, implementación, grafo y particionado"
        )
        body = bind["run"]
        self.assertNotIn("> .ddd-pre-m04-evidence.json", body)
        self.assertIn('handoff="$RUNNER_TEMP/ddd-pre-m04-evidence-$GITHUB_RUN_ID.json"', body)
        self.assertIn("handoff_evidencia_pre_m04 stage", body)
        self.assertIn("handoff_evidencia_pre_m04 verify", body)
        self.assertLess(body.index("handoff_evidencia_pre_m04 stage"), body.index("git commit"))
        self.assertLess(body.index("git pull --rebase"), body.index("handoff_evidencia_pre_m04 verify"))
        self.assertLess(body.index("handoff_evidencia_pre_m04 verify"), body.index('git push origin "HEAD:$target_branch"'))
        self.assertIn(
            "no coincide con la evidencia persistida; no se publicará acreditación",
            body,
        )

        upload = next(
            step
            for step in job["steps"]
            if step.get("name") == "Publicar evidencia pre-M04 inmutable"
        )
        self.assertEqual(
            upload["with"]["path"],
            "${{ runner.temp }}/ddd-pre-m04-evidence-${{ github.run_id }}.json",
        )


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

    def test_historical_real_targets_require_reaccreditation_before_generation(self):
        catalog = ROOT / "configuracion/catalogo_preparacion.yaml"
        for territory_id in REAL_TARGETS:
            with self.subTest(territory=territory_id):
                state, contract_path, _ = self._state_and_contract(territory_id)
                prep = state.get("preparation_evidence") or {}
                gate = generation_enablement(
                    root_dir=ROOT,
                    contract_path=contract_path,
                    territory_id=territory_id,
                    certified_product_ready=False,
                    first_generation_evidence=None,
                    preparation_evidence=prep,
                    require_source=True,
                )
                self.assertFalse(gate["allowed"])
                self.assertIn(gate["capability"], {"CAP_SOURCE", "CAP_PRE_M04_EVIDENCE"})

                plan = build_plan(
                    territory=territory_id,
                    edition="2025",
                    execution_mode="reuse",
                    catalog=catalog,
                    root_dir=ROOT,
                    optimization_algorithm="GerryChain 50",
                    force_selected_algorithm=True,
                )
                self.assertTrue(plan["run_prepare_territorial"])
                self.assertTrue(plan["pre_m04_accreditation_planned"])
                self.assertTrue(plan["run_generate"])
                self.assertEqual(
                    {"allowed": True, "route": "planned_pre_m04_accreditation"},
                    plan["generation_gate"],
                )

    def test_00_reuse_plan_reaccredits_historical_real_targets(self):
        catalog = ROOT / "configuracion/catalogo_preparacion.yaml"
        for territory_id in REAL_TARGETS:
            with self.subTest(territory=territory_id):
                plan = build_plan(
                    territory=territory_id,
                    edition="2025",
                    execution_mode="reuse",
                    catalog=catalog,
                    root_dir=ROOT,
                    optimization_algorithm="GerryChain 50",
                    force_selected_algorithm=True,
                )
                self.assertTrue(plan["run_prepare_territorial"])
                self.assertTrue(plan["pre_m04_accreditation_planned"])
                self.assertTrue(plan["run_generate"])
                decision = plan["existing"]["territorial_source"].get("decision")
                if decision is not None:
                    self.assertEqual(decision, "VALIDADO")
                self.assertEqual(
                    {"allowed": True, "route": "planned_pre_m04_accreditation"},
                    plan["generation_gate"],
                )

    def test_00_reuse_reaccredits_present_but_stale_pre_m04_without_reacquiring_source(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            contract_path, m03, job = write_fixture(root, partitioned=False)

            # Fingerprint de implementación real dentro del fixture para poder
            # demostrar una evidencia presente que queda obsoleta después.
            implementation_files = {
                "modulos/01_preparar_base_territorial.py": "m01-current\n",
                "modulos/02_construir_adyacencias.py": "m02-current\n",
                "modulos/03_construir_grafo.py": "m03-current\n",
                "herramientas/preparar_unidades_internas.py": "partition-current\n",
                "herramientas/construir_unidades_internas_m04.py": "builder-current\n",
            }
            for rel, payload in implementation_files.items():
                path = root / rel
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(payload, encoding="utf-8")

            with patch(
                "herramientas.materializar_evidencia_pre_m04._git_head",
                return_value=COMMIT,
            ):
                evidence = build_evidence(
                    root_dir=root,
                    territory_id="demo",
                    edition="2025",
                    run_id=123,
                    contract_path=str(contract_path.relative_to(root)),
                    m03_state_dir=m03,
                    partition_job=job,
                    m03_artifact_sha256=SHA_C,
                    m03u_artifact_sha256=SHA_D,
                    partition_artifact_sha256=SHA_A,
                )

            self.assertEqual(
                evidence["effective_gate"],
                {"allowed": True, "route": "validated_pre_m04_topology"},
            )

            # Simula exactamente el caso Melilla: la evidencia existe y está
            # ligada a la fuente correcta, pero M01 cambió desde que se emitió.
            evidence_rel = (
                "territorios/demo/evidencia/catalogo/"
                "generation_preflight_2025.json"
            )
            evidence_path = root / evidence_rel
            evidence_path.parent.mkdir(parents=True, exist_ok=True)
            evidence_path.write_text(
                json.dumps(evidence, indent=2),
                encoding="utf-8",
            )

            catalog_path = root / "configuracion/catalogo_preparacion.yaml"
            catalog = yaml.safe_load(catalog_path.read_text(encoding="utf-8")) or {}
            state = catalog["territories"][0]["editions"]["2025"]
            state["generation_enabled"] = True
            state.setdefault("evidence", {})["generation_preflight"] = evidence_rel
            catalog_path.write_text(
                yaml.safe_dump(catalog, sort_keys=False, allow_unicode=True),
                encoding="utf-8",
            )

            valid_plan = build_plan(
                territory="demo",
                edition="2025",
                execution_mode="reuse",
                catalog=catalog_path,
                root_dir=root,
                optimization_algorithm="Canónico",
            )
            self.assertFalse(valid_plan["run_prepare_territorial"])
            self.assertFalse(valid_plan["pre_m04_accreditation_planned"])
            self.assertEqual(
                valid_plan["generation_gate"],
                {"allowed": True, "route": "validated_pre_m04_topology"},
            )

            stale = json.loads(json.dumps(evidence))
            stale["implementation"]["m01_git_blob_sha1"] = "0" * 40
            evidence_path.write_text(
                json.dumps(stale, indent=2),
                encoding="utf-8",
            )

            direct = generation_enablement(
                root_dir=root,
                contract_path=str(contract_path.relative_to(root)),
                territory_id="demo",
                certified_product_ready=False,
                first_generation_evidence=stale,
                preparation_evidence=state["preparation_evidence"],
                require_source=True,
            )
            self.assertFalse(direct["allowed"])
            self.assertEqual(direct["capability"], "CAP_PRE_M04_EVIDENCE")
            self.assertIn("implementación pre-M04 cambió", direct["reason"])

            plan = build_plan(
                territory="demo",
                edition="2025",
                execution_mode="reuse",
                catalog=catalog_path,
                root_dir=root,
                optimization_algorithm="Canónico",
            )

        self.assertEqual(
            plan["existing"]["territorial_source"]["decision"],
            "VALIDADO",
        )
        self.assertEqual(plan["existing"]["territorial_source"]["run_id"], 123)
        self.assertEqual(plan["execution_mode"], "reuse")
        self.assertTrue(plan["run_prepare_territorial"])
        self.assertTrue(plan["pre_m04_accreditation_planned"])
        self.assertTrue(plan["run_generate"])
        self.assertEqual(
            plan["generation_gate"],
            {"allowed": True, "route": "planned_pre_m04_accreditation"},
        )

        # En reuse, 01 debe recuperar el paquete ya acreditado; no volver a
        # descargarlo. La reacreditación es M01→pre-M04, no adquisición.
        workflow = yaml.safe_load(
            (ROOT / ".github/workflows/ejecucion-completa-proyecto.yml").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(
            workflow["jobs"]["preparar_territorial"]["with"][
                "reutilizar_si_ya_preparada"
            ],
            "${{ needs.planificar.outputs.execution_mode_internal != 'from_start' }}",
        )

    def test_00_reuse_reaccredits_valid_source_when_pre_m04_is_unreadable(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            write_fixture(root, partitioned=False)

            evidence_rel = (
                "territorios/demo/evidencia/catalogo/"
                "generation_preflight_2025.json"
            )
            evidence_path = root / evidence_rel
            evidence_path.parent.mkdir(parents=True, exist_ok=True)
            evidence_path.write_text("{not-json", encoding="utf-8")

            catalog_path = root / "configuracion/catalogo_preparacion.yaml"
            catalog = yaml.safe_load(catalog_path.read_text(encoding="utf-8")) or {}
            state = catalog["territories"][0]["editions"]["2025"]
            state["generation_enabled"] = True
            state.setdefault("evidence", {})["generation_preflight"] = evidence_rel
            catalog_path.write_text(
                yaml.safe_dump(catalog, sort_keys=False, allow_unicode=True),
                encoding="utf-8",
            )

            plan = build_plan(
                territory="demo",
                edition="2025",
                execution_mode="reuse",
                catalog=catalog_path,
                root_dir=root,
                optimization_algorithm="Canónico",
            )

        self.assertEqual(
            plan["existing"]["territorial_source"]["decision"],
            "VALIDADO",
        )
        self.assertTrue(plan["run_prepare_territorial"])
        self.assertTrue(plan["pre_m04_accreditation_planned"])
        self.assertTrue(plan["run_generate"])
        self.assertEqual(
            plan["generation_gate"],
            {"allowed": True, "route": "planned_pre_m04_accreditation"},
        )

    def test_00_reuse_reaccredits_valid_source_when_pre_m04_is_missing(self):
        source_catalog = ROOT / "configuracion/catalogo_preparacion.yaml"
        data = yaml.safe_load(source_catalog.read_text(encoding="utf-8")) or {}
        row = next(
            item for item in data["territories"]
            if item["territory_id"] == "melilla"
        )
        state = row["editions"]["2025"]
        self.assertTrue(state["territorial_sources_prepared"])
        self.assertTrue(state["generation_enabled"])
        self.assertIn("generation_preflight", state["evidence"])

        # Reproduce de forma sintética el estado parcial que existía antes del
        # run 37063207747: fuente territorial válida, pre-M04 aún no acreditado.
        state["generation_enabled"] = False
        state["evidence"].pop("generation_preflight", None)

        with tempfile.TemporaryDirectory() as td:
            catalog = Path(td) / "catalog.yaml"
            catalog.write_text(
                yaml.safe_dump(data, allow_unicode=True, sort_keys=False),
                encoding="utf-8",
            )
            plan = build_plan(
                territory="melilla",
                edition="2025",
                execution_mode="reuse",
                catalog=catalog,
                root_dir=ROOT,
                optimization_algorithm="GerryChain 50",
                force_selected_algorithm=True,
            )

        self.assertEqual(
            "VALIDADO",
            plan["existing"]["territorial_source"]["decision"],
        )
        self.assertTrue(plan["run_prepare_territorial"])
        self.assertTrue(plan["pre_m04_accreditation_planned"])
        self.assertTrue(plan["run_generate"])
        self.assertEqual(
            {"allowed": True, "route": "planned_pre_m04_accreditation"},
            plan["generation_gate"],
        )

    def test_00_from_start_national_matrix_plans_required_pre_m04_accreditation(self):
        catalog_path = ROOT / "configuracion/catalogo_preparacion.yaml"
        catalog = yaml.safe_load(catalog_path.read_text(encoding="utf-8")) or {}
        rows = {
            row["territory_id"]: (row.get("editions") or {}).get("2025") or {}
            for row in catalog.get("territories") or []
        }
        self.assertEqual(19, len(rows))
        authoritative = {
            item["territory_id"]: item
            for item in resolve_current_legislature(ROOT, "Todos")["plans"]
        }
        self.assertEqual(set(rows), set(authoritative))

        planned = set()
        for territory_id, state in rows.items():
            with self.subTest(territory=territory_id):
                plan = build_plan(
                    territory=territory_id,
                    edition="2025",
                    execution_mode="from_start",
                    catalog=catalog_path,
                    root_dir=ROOT,
                    optimization_algorithm="Canónico",
                    force_selected_algorithm=False,
                )
                self.assertTrue(plan["run_prepare_territorial"])
                self.assertTrue(plan["run_generate"])
                self.assertEqual(
                    plan["population_year"],
                    authoritative[territory_id]["population_year_selected"],
                )
                self.assertEqual(
                    plan["section_year"],
                    authoritative[territory_id]["section_year_selected"],
                )
                self.assertEqual("from_start", plan["generation_execution_mode"])
                self.assertTrue(plan["generation_gate"]["allowed"])
                if plan["pre_m04_accreditation_planned"]:
                    planned.add(territory_id)
                    self.assertEqual(
                        {"allowed": True, "route": "planned_pre_m04_accreditation"},
                        plan["generation_gate"],
                    )

        self.assertEqual(FROM_START_PRE_M04_TARGETS, planned)

    def test_00_from_start_archipelagos_and_continental_pre_m04_family_use_01_then_generation(self):
        catalog = ROOT / "configuracion/catalogo_preparacion.yaml"
        families = {
            "physical_components": ("illes_balears", "canarias"),
            "continental_pre_m04": (
                "cataluna",
                "comunidad_valenciana",
                "madrid",
                "region_de_murcia",
                "comunidad_foral_de_navarra",
                "pais_vasco",
                "la_rioja",
                "melilla",
            ),
        }
        for family, territories in families.items():
            for territory_id in territories:
                with self.subTest(family=family, territory=territory_id):
                    plan = build_plan(
                        territory=territory_id,
                        edition="2025",
                        execution_mode="from_start",
                        catalog=catalog,
                        root_dir=ROOT,
                    )
                    self.assertTrue(plan["run_prepare_territorial"])
                    self.assertTrue(plan["pre_m04_accreditation_planned"])
                    self.assertTrue(plan["run_generate"])
                    self.assertEqual(
                        {"allowed": True, "route": "planned_pre_m04_accreditation"},
                        plan["generation_gate"],
                    )

    def test_00_from_start_does_not_authorize_contract_without_resolvable_m04_input(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            contract_path, _, _ = write_fixture(root, partitioned=False)
            broken = yaml.safe_load(contract_path.read_text(encoding="utf-8"))
            broken["modulos"]["modulo_04_generar_semillas"]["in_geojson"] = "unreachable.geojson"
            contract_path.write_text(
                yaml.safe_dump(broken, sort_keys=False, allow_unicode=True),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(
                ValueError,
                r"GENERATION_CONTRACT_BLOCK: Demo: CAP_M04_INPUT:",
            ):
                build_plan(
                    territory="demo",
                    edition="2025",
                    execution_mode="from_start",
                    catalog=root / "configuracion/catalogo_preparacion.yaml",
                    root_dir=root,
                )

    def test_historical_source_and_flags_do_not_bypass_reaccreditation(self):
        catalog = ROOT / "configuracion/catalogo_preparacion.yaml"

        reuse = build_plan(
            territory="illes_balears",
            edition="2025",
            execution_mode="reuse",
            catalog=catalog,
            root_dir=ROOT,
        )
        self.assertTrue(reuse["run_prepare_territorial"])
        self.assertTrue(reuse["pre_m04_accreditation_planned"])
        self.assertEqual(
            {"allowed": True, "route": "planned_pre_m04_accreditation"},
            reuse["generation_gate"],
        )

        with self.assertRaisesRegex(ValueError, "CATALOG_SOURCE_BLOCK"):
            build_plan(
                territory="illes_balears",
                edition="2025",
                execution_mode="catalog_source",
                catalog=catalog,
                root_dir=ROOT,
            )

        continental = build_plan(
            territory="andalucia",
            edition="2025",
            execution_mode="from_start",
            catalog=catalog,
            root_dir=ROOT,
        )
        self.assertTrue(continental["run_prepare_territorial"])
        self.assertTrue(continental["pre_m04_accreditation_planned"])
        self.assertTrue(continental["run_generate"])
        self.assertEqual(
            {"allowed": True, "route": "planned_pre_m04_accreditation"},
            continental["generation_gate"],
        )

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

    def test_00_generation_handoff_keeps_source_sha_and_transports_pre_m04_evidence(self):
        full_text = (ROOT / ".github/workflows/ejecucion-completa-proyecto.yml").read_text(encoding="utf-8")
        full = yaml.safe_load(full_text)
        preparation = yaml.safe_load((ROOT / ".github/workflows/preparacion-fuentes.yml").read_text(encoding="utf-8"))
        reusable = yaml.safe_load((ROOT / ".github/workflows/_reutilizable-generacion-territorial.yml").read_text(encoding="utf-8"))
        production_text = (ROOT / ".github/workflows/produccion-distritos.yml").read_text(encoding="utf-8")
        production = yaml.safe_load(production_text)

        plan_outputs = full["jobs"]["planificar"]["outputs"]
        self.assertIn("pre_m04_accreditation_planned", plan_outputs)
        self.assertEqual(plan_outputs["source_sha"], "${{ steps.plan.outputs.source_sha }}")
        self.assertEqual(plan_outputs["source_ref"], "${{ steps.plan.outputs.source_sha }}")
        self.assertIn('source_sha="$(git rev-parse HEAD)"', full_text)
        self.assertIn(
            "La acreditación pre-M04 planificada exige persist_state=true antes de habilitar generación.",
            full_text,
        )

        generate = full["jobs"]["generar"]
        self.assertEqual(generate["with"]["require_generation_gate"], True)
        enabled_ref = "${{ needs.preparar_territorial.result == 'success' && needs.preparar_territorial.outputs.enabled_source_ref || needs.planificar.outputs.source_sha }}"
        self.assertIn("preparar_territorial", generate["needs"])
        self.assertEqual(generate["with"]["source_ref"], enabled_ref)
        self.assertNotIn("'main'", generate["with"]["source_ref"])
        self.assertEqual(full["jobs"]["puerta_01"]["with"]["source_ref"], enabled_ref)
        self.assertIn("preparar_territorial", full["jobs"]["puerta_02"]["needs"])
        self.assertEqual(full["jobs"]["puerta_02"]["with"]["source_ref"], enabled_ref)
        prep_outputs = ((preparation.get("on") or preparation.get(True) or {}).get("workflow_call") or {}).get("outputs") or {}
        self.assertEqual(
            prep_outputs["enabled_source_ref"]["value"],
            "${{ jobs.pre_m04.outputs.enabled_source_ref }}",
        )
        self.assertIn(
            "run_prepare_territorial == 'true'",
            generate["with"]["generation_preflight_artifact_name"],
        )
        self.assertIn(
            "persist_state == 'true'",
            generate["with"]["generation_preflight_artifact_name"],
        )
        self.assertEqual(
            generate["with"]["source_package_artifact_sha256"],
            "${{ needs.puerta_01.outputs.artifact_digest }}",
        )

        pre_m04 = preparation["jobs"]["pre_m04"]["with"]
        self.assertEqual(pre_m04["source_ref"], "${{ needs.registrar.outputs.promotion_sha }}")
        self.assertEqual(pre_m04["source_evidence_run_id"], "${{ github.run_id }}")
        self.assertIn("needs.registrar.outputs.artifact_sha256", pre_m04["source_evidence_artifact_sha256"])
        self.assertIn("needs.registrar.outputs.package_sha256", pre_m04["source_evidence_package_sha256"])

        reusable_inputs = ((reusable.get("on") or reusable.get(True) or {}).get("workflow_call") or {}).get("inputs") or {}
        for key in (
            "source_evidence_run_id",
            "source_evidence_artifact_name",
            "source_evidence_artifact_sha256",
            "source_evidence_package_sha256",
        ):
            self.assertIn(key, reusable_inputs)
        reusable_call = (reusable.get("on") or reusable.get(True) or {}).get("workflow_call") or {}
        self.assertEqual(
            (reusable_call.get("outputs") or {})["enabled_source_ref"]["value"],
            "${{ jobs.pre_m04_evidence.outputs.enabled_source_ref }}",
        )
        pre_m04_job = reusable["jobs"]["pre_m04_evidence"]
        self.assertEqual(
            pre_m04_job["outputs"]["enabled_source_ref"],
            "${{ steps.persist.outputs.enabled_source_ref }}",
        )
        checkout = next(step for step in pre_m04_job["steps"] if step.get("uses", "").startswith("actions/checkout@"))
        self.assertEqual(checkout["with"]["ref"], "${{ inputs.source_ref || github.sha }}")
        self.assertIn("--preparation-evidence-json", pre_m04_job["steps"][3]["run"])
        self.assertTrue(any(
            step.get("with", {}).get("name") == "ddd-generation-preflight-${{ needs.resolve.outputs.territory_id }}-${{ github.run_id }}"
            for step in pre_m04_job["steps"]
        ))

        triggers = production.get("on") or production.get(True) or {}
        call_inputs = (triggers.get("workflow_call") or {}).get("inputs") or {}
        self.assertIn("require_generation_gate", call_inputs)
        self.assertIn("generation_preflight_artifact_name", call_inputs)
        self.assertIn("source_package_artifact_sha256", call_inputs)
        resolver_steps = production["jobs"]["resolver_interfaz"]["steps"]
        download = next(step for step in resolver_steps if step.get("name") == "Recuperar evidencia pre-M04 explícita")
        self.assertEqual(download["if"], "${{ inputs.generation_preflight_artifact_name != '' }}")
        gate = next(step for step in resolver_steps if step.get("name") == "Validar puerta efectiva antes de Formación inicial")
        self.assertEqual(gate["if"], "${{ inputs.require_generation_gate }}")
        body = gate["run"]
        self.assertIn("generation_enablement(", body)
        self.assertIn("GENERATION_CONTRACT_BLOCK:", body)
        self.assertIn("GENERATION_PREFLIGHT_ARTIFACT_NAME", body)
        self.assertIn("SOURCE_PACKAGE_ARTIFACT_SHA256", body)

        names = [step.get("name") for step in resolver_steps]
        self.assertLess(
            names.index("Recuperar evidencia pre-M04 explícita"),
            names.index("Validar puerta efectiva antes de Formación inicial"),
        )
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
