from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

import yaml

from herramientas.resolver_ejecucion_completa import build_plan

ROOT = Path(__file__).resolve().parents[1]
DIGESTS = {
    "source": "1" * 64,
    "source_package": "2" * 64,
    "m06": "3" * 64,
    "electoral_source": "4" * 64,
    "m08": "5" * 64,
}


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def phase(name: str, run_id: int, artifact: str, digest: str, *, result: str = "success") -> dict:
    return {
        "name": name,
        "executed": result == "success",
        "result": result,
        "run_id": run_id,
        "artifact": artifact,
        "artifact_digest": f"sha256:{digest}",
        "validation_decision": "VALIDADO",
        "phase_decision": "PASS",
    }


def write_manifest(root: Path, run_id: int, phases: list[dict]) -> None:
    write_json(
        root / f"territorios/demo/evidencia/ejecuciones_completas/{run_id}.json",
        {
            "schema": "ddd.full-run-manifest/2.1",
            "territory_id": "demo",
            "territory_name": "Demo",
            "edition": "2025",
            "workflow_run_id": run_id,
            "status": "SUCCESS",
            "completion_status": "COMPLETE",
            "phases": phases,
        },
    )


def prepare_root(
    root: Path,
    *,
    source: bool = False,
    m06: bool = False,
    electoral_source: bool = False,
    m08: bool = False,
    invalid: bool = False,
    incompatible: bool = False,
) -> Path:
    contract = root / "territorios/demo/config/demo_2025.yaml"
    contract.parent.mkdir(parents=True, exist_ok=True)
    contract.write_text(
        yaml.safe_dump(
            {
                "meta": {
                    "territory_id": "demo",
                    "status": "generation_ready",
                    "contract_level": "production_m01_m06",
                },
                "territory_contract": {
                    "status": "generation_ready",
                    "k_districts": 3,
                    "population_floor_ratio": 0.8,
                    "population_cap_ratio": 1.75,
                    "target_tolerance_ratio": 0.12,
                },
                "modulos": {
                    "modulo_01_preparar_base_territorial": {"out_geojson": "source.geojson"},
                    "modulo_02_construir_adyacencias": {"out_edges_jsonl": "edges.jsonl"},
                    "modulo_03_construir_grafo": {"out_graph_json": "graph.json"},
                    "modulo_04_generar_semillas": {
                        "in_graph_json": "graph.json",
                        "in_geojson": "source.geojson",
                        "out_geojson": "seeds.geojson",
                        "municipality_field": "CUMUN",
                        "k_districts": 3,
                    },
                    "modulo_05_optimizar_distritos": {
                        "in_graph_json": "graph.json",
                        "in_geojson": "seeds.geojson",
                        "out_geojson": "optimized.geojson",
                        "municipality_field": "CUMUN",
                    },
                    "modulo_06_consolidar_distritos": {
                        "in_geojson": "optimized.geojson",
                        "municipality_field": "CUMUN",
                        "expected_districts": 3,
                    },
                },
                "validation": {
                    "municipality_field": "CUMUN",
                    "require_municipality_discipline": True,
                    "require_graph_contiguity": True,
                },
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    declaration = root / "territorios/demo/config/fuentes_oficiales.yaml"
    declaration.write_text(
        yaml.safe_dump(
            {
                "schema": "ddd-territory-sources/1.0",
                "territory": {"id": "demo", "edition": "2025"},
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    registry = root / "configuracion/registro_electoral.yaml"
    registry.parent.mkdir(parents=True, exist_ok=True)
    registry.write_text(
        yaml.safe_dump(
            {"territories": {"demo": {"election_id": "demo_election_2025", "election_date": "2025-01-01"}}},
            sort_keys=False,
        ),
        encoding="utf-8",
    )

    evidence: dict[str, str] = {}
    prep = {}
    source_run = 101
    source_artifact = f"ddd-source-package-demo-2025-{source_run}"
    if source:
        prep = {
            "run_id": source_run,
            "artifact_name": source_artifact,
            "artifact_sha256": DIGESTS["source"],
            "package_sha256": DIGESTS["source_package"],
            "source_commit": "a" * 40,
        }

    m06_run = 201
    m06_artifact = f"ddd-state-{m06_run}-M06"
    if m06:
        rel = "territorios/demo/evidencia/catalogo/territorial_product_2025.json"
        evidence["territorial_product"] = rel
        write_json(
            root / rel,
            {
                "schema": "ddd.catalog-evidence/1.0",
                "kind": "territorial_product",
                "territory_id": "demo",
                "territory_name": "Demo",
                "edition": "2025",
                "run_id": m06_run,
                "artifact_name": m06_artifact,
                "artifact_sha256": ("x" * 64 if invalid else DIGESTS["m06"]),
                "source_commit": "b" * 40,
                "decision": "PASS",
                "stage": "M06",
            },
        )
        manifest_source = (
            phase("01 · Preparación de Datos Territoriales", source_run, source_artifact, DIGESTS["source"], result="skipped")
            if source
            else phase("01 · Preparación de Datos Territoriales", 91, "ddd-source-package-demo-2025-91", "9" * 64, result="skipped")
        )
        write_manifest(
            root,
            m06_run,
            [
                manifest_source,
                phase("02 · Generación de Distritos Autonómicos", m06_run, m06_artifact, DIGESTS["m06"]),
            ],
        )

    electoral_run = 301
    electoral_artifact = f"ddd-electoral-package-demo-2025-{electoral_run}"
    if electoral_source:
        rel = "territorios/demo/evidencia/catalogo/electoral_source_2025.json"
        evidence["electoral_source"] = rel
        write_json(
            root / rel,
            {
                "schema": "ddd.catalog-evidence/1.0",
                "kind": "electoral_source",
                "territory_id": "demo",
                "territory_name": "Demo",
                "edition": "2025",
                "run_id": electoral_run,
                "artifact_name": electoral_artifact,
                "artifact_sha256": DIGESTS["electoral_source"],
                "source_commit": "c" * 40,
                "election_id": "demo_election_2025",
            },
        )

    m08_run = 401
    m08_artifact = f"ddd-state-{m08_run}-M08"
    if m08:
        rel = "territorios/demo/evidencia/catalogo/electoral_product_2025.json"
        evidence["electoral_product"] = rel
        write_json(
            root / rel,
            {
                "schema": "ddd.catalog-evidence/1.0",
                "kind": "electoral_product",
                "territory_id": "demo",
                "territory_name": "Demo",
                "edition": "2025",
                "run_id": m08_run,
                "artifact_name": m08_artifact,
                "artifact_sha256": DIGESTS["m08"],
                "source_commit": "d" * 40,
                "stage": "M08",
            },
        )
        used_m06_digest = "8" * 64 if incompatible else DIGESTS["m06"]
        write_manifest(
            root,
            m08_run,
            [
                phase("01 · Preparación de Datos Territoriales", source_run, source_artifact, DIGESTS["source"], result="skipped"),
                phase("02 · Generación de Distritos Autonómicos", m06_run, m06_artifact, used_m06_digest, result="skipped"),
                phase("03 · Preparación de Resultados Electorales", electoral_run, electoral_artifact, DIGESTS["electoral_source"], result="skipped"),
                phase("04 · Incorporación de Resultados Electorales", m08_run, m08_artifact, DIGESTS["m08"]),
            ],
        )

    state = {
        "territory_declared": True,
        "preparation_status": "READY",
        "contract_path": "territorios/demo/config/demo_2025.yaml",
        "territorial_source_declaration": "territorios/demo/config/fuentes_oficiales.yaml",
        "electoral_source_declaration": None,
        "territorial_sources_prepared": source,
        "territorial_contract_complete": True,
        "territorial_product_available": m06,
        "electoral_source_prepared": electoral_source,
        "electoral_product_available": m08,
        "territorial_certification": "PASS" if m06 else "NOT_CERTIFIED",
        "production_authorization": "AUTHORIZED",
        "last_valid_checkpoint": None,
        "preparation_evidence": prep,
        "evidence": evidence,
    }
    if m08:
        state["last_valid_checkpoint"] = {"run_id": m08_run, "stage": "M08"}
    elif m06:
        state["last_valid_checkpoint"] = {"run_id": m06_run, "stage": "M06"}

    catalog = root / "configuracion/catalogo_preparacion.yaml"
    catalog.write_text(
        yaml.safe_dump(
            {
                "schema": "ddd-preparation-catalog/1.1",
                "default_edition": "2025",
                "territories": [
                    {"territory_id": "demo", "name": "Demo", "editions": {"2025": state}}
                ],
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    return catalog


def plan(root: Path, **kwargs) -> dict:
    catalog = prepare_root(root, **kwargs)
    return build_plan(
        territory="Demo",
        edition="2025",
        execution_mode="reuse",
        catalog=catalog,
        root_dir=root,
        optimization_algorithm="Canónico",
        force_selected_algorithm=False,
    )


class ContinueFromLastValidTests(unittest.TestCase):
    def assert_phases(self, p: dict, expected: tuple[bool, bool, bool, bool]) -> None:
        self.assertEqual(
            (
                p["run_prepare_territorial"],
                p["run_generate"],
                p["run_prepare_electoral"],
                p["run_incorporate"],
            ),
            expected,
        )

    def case(self, **kwargs) -> dict:
        td = tempfile.TemporaryDirectory()
        self.addCleanup(td.cleanup)
        return plan(Path(td.name), **kwargs)

    def test_no_assets_runs_01_02_03_04(self):
        self.assert_phases(self.case(), (True, True, True, True))

    def test_only_territorial_source_runs_02_03_04(self):
        self.assert_phases(self.case(source=True), (True, True, True, True))

    def test_certified_territorial_product_runs_03_04(self):
        self.assert_phases(self.case(m06=True), (False, False, True, True))

    def test_territorial_and_electoral_sources_without_product_run_02_and_04(self):
        self.assert_phases(
            self.case(source=True, electoral_source=True),
            (True, True, False, True),
        )

    def test_territorial_product_and_electoral_source_run_only_04(self):
        self.assert_phases(
            self.case(m06=True, electoral_source=True),
            (False, False, False, True),
        )

    def test_complete_electoral_product_runs_nothing(self):
        self.assert_phases(
            self.case(source=True, m06=True, electoral_source=True, m08=True),
            (False, False, False, False),
        )

    def test_invalid_evidence_blocks(self):
        with self.assertRaisesRegex(ValueError, "CONTINUE_DURABLE_BLOCK.*DIGEST"):
            self.case(m06=True, invalid=True)

    def test_incompatible_lineage_blocks(self):
        with self.assertRaisesRegex(ValueError, "CONTINUE_DURABLE_BLOCK.*LINEAGE_INCOMPATIBLE"):
            self.case(source=True, m06=True, electoral_source=True, m08=True, incompatible=True)

    def test_failed_m06_producer_phase_blocks_reuse(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            catalog = prepare_root(root, m06=True)
            manifest_path = root / "territorios/demo/evidencia/ejecuciones_completas/201.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            producer = next(p for p in manifest["phases"] if p["name"].startswith("02 ·"))
            producer["result"] = "failure"
            producer["executed"] = True
            write_json(manifest_path, manifest)
            with self.assertRaisesRegex(ValueError, "CONTINUE_DURABLE_BLOCK.*PRODUCER_PHASE_INVALID"):
                build_plan(
                    territory="Demo",
                    edition="2025",
                    execution_mode="reuse",
                    catalog=catalog,
                    root_dir=root,
                    optimization_algorithm="Canónico",
                    force_selected_algorithm=False,
                )

    def test_contradictory_m06_producer_validation_blocks_reuse(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            catalog = prepare_root(root, m06=True)
            manifest_path = root / "territorios/demo/evidencia/ejecuciones_completas/201.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            producer = next(p for p in manifest["phases"] if p["name"].startswith("02 ·"))
            producer["validation_decision"] = "BLOQUEADO"
            write_json(manifest_path, manifest)
            with self.assertRaisesRegex(ValueError, "CONTINUE_DURABLE_BLOCK.*PRODUCER_PHASE_INVALID"):
                build_plan(
                    territory="Demo",
                    edition="2025",
                    execution_mode="reuse",
                    catalog=catalog,
                    root_dir=root,
                    optimization_algorithm="Canónico",
                    force_selected_algorithm=False,
                )

    def test_castilla_la_mancha_current_complete_product_is_reused_without_work(self):
        plan = build_plan(
            territory="Castilla-La Mancha",
            edition="2025",
            execution_mode="reuse",
            catalog=ROOT / "configuracion/catalogo_preparacion.yaml",
            root_dir=ROOT,
            optimization_algorithm="Canónico",
            force_selected_algorithm=True,
        )
        self.assertFalse(plan["run_prepare_territorial"])
        self.assertFalse(plan["run_generate"])
        self.assertFalse(plan["run_prepare_electoral"])
        self.assertFalse(plan["run_incorporate"])
        self.assertTrue(plan["catalog_state"]["territorial_product_available"])
        self.assertTrue(plan["catalog_state"]["electoral_product_available"])
        territorial_run = plan["existing"]["territorial_product"]["run_id"]
        electoral_run = plan["existing"]["electoral_product"]["run_id"]
        self.assertIsInstance(territorial_run, int)
        self.assertEqual(electoral_run, territorial_run)

    def test_workflow_accepts_future_label_without_exposing_interface_yet(self):
        workflow = (ROOT / ".github/workflows/ejecucion-completa-proyecto.yml").read_text(encoding="utf-8")
        self.assertIn('"Continuar desde el último resultado válido") mode=reuse', workflow)
        self.assertIn('if [[ "$mode" == "reuse" ]]', workflow)
        dispatch = workflow.split("workflow_dispatch:", 1)[1].split("permissions:", 1)[0]
        self.assertNotIn("Continuar desde el último resultado válido\n", dispatch)


if __name__ == "__main__":
    unittest.main()
