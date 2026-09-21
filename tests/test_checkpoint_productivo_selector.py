from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from herramientas.seleccionar_checkpoint_productivo import select_latest_valid
from herramientas.huella_checkpoint_m05 import ENGINE_FILES, build_fingerprint
from herramientas.derivar_checkpoint_acumulado import derive_checkpoint, inspect_derivable_checkpoint

ROOT = Path(__file__).resolve().parents[1]


class ProductiveCheckpointSelectorTests(unittest.TestCase):
    def prepare_root(self, root: Path):
        (root / "territorios/demo/config").mkdir(parents=True)
        (root / "territorios/demo/config/fuentes_oficiales.yaml").write_text(
            "territory:\n  id: demo\n  edition: 2025\ncoverage_checks:\n  expected_sections: 1\n",
            encoding="utf-8",
        )
        for rel in ENGINE_FILES:
            path=root / rel; path.parent.mkdir(parents=True,exist_ok=True)
            path.write_text(f"synthetic {rel}\n",encoding="utf-8")
        params = root / "params.yaml"
        params.write_text(
            "meta:\n  territory_id: demo\n  run_name: demo_2025\n  year: 2025\n"
            "modulos:\n"
            "  modulo_01_preparar_base_territorial:\n    out_geojson: cache/demo_2025_m01.geojson.zip\n"
            "  modulo_02_construir_adyacencias:\n    out_edges_jsonl: cache/demo_2025_m02.jsonl\n"
            "  modulo_03_construir_grafo:\n    out_graph_json: cache/demo_2025_m03.json\n"
            "  modulo_04_generar_semillas:\n    out_geojson: cache/demo_2025_m04.geojson.zip\n"
            "  modulo_05_optimizar_distritos:\n"
            "    seed: 1\n    population_repair:\n      enabled: true\n"
            "    out_geojson: cache/demo_2025_m05.geojson.zip\n"
            "    out_report: cache/demo_2025_m05_informe.json\n"
            "  modulo_06_consolidar_distritos:\n    out_geojson: cache/demo_2025_m06.geojson.zip\n",
            encoding="utf-8",
        )
        return params

    def package(self, root: Path, name: str, *, payload: bytes = b"id,value\n1,x\n",
                edition: int = 2025, corrupt_hash: bool = False) -> Path:
        package = root / name
        frozen = package / "prepared_sources.zip"
        frozen.parent.mkdir(parents=True, exist_ok=True)
        frozen.write_bytes(payload)
        digest = hashlib.sha256(payload).hexdigest()
        if corrupt_hash:
            digest = "0" * 64
        manifest = {
            "source_id": "prepared-territorial-sources:official",
            "edition": edition,
            "origin": "https://official.example/source.csv",
            "path": "prepared_sources.zip",
            "bytes": len(payload),
            "sha256": digest,
            "records": 1,
            "acquired_at": "2026-09-17T19:00:00Z",
        }
        (package / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
        return package

    def state(self, root: Path, name: str, params: Path, *, fingerprint: bool = True,
              outliers: int = 0, hard: int = 0) -> Path:
        state=root / name
        if fingerprint:
            out=state / "compatibility" / "m05.json"; out.parent.mkdir(parents=True,exist_ok=True)
            out.write_text(json.dumps(build_fingerprint(params=params,root_dir=root)),encoding="utf-8")
        report=state / "cache" / "demo_2025_m05_informe.json"
        report.parent.mkdir(parents=True,exist_ok=True)
        report.write_text(json.dumps({
            "objective_start": [hard, 0, max(outliers, 1), 0.20, 1.0],
            "objective_final": [hard, 0, outliers, 0.10 if outliers == 0 else 0.13, 0.5],
        }),encoding="utf-8")
        return state

    def accumulated_state(self, root: Path, name: str, params: Path) -> Path:
        state=self.state(root,name,params,fingerprint=False)
        cache=state/"cache"; cache.mkdir(parents=True,exist_ok=True)
        for fname in ("demo_2025_m01.geojson.zip","demo_2025_m02.jsonl","demo_2025_m03.json","demo_2025_m04.geojson.zip",
                      "demo_2025_m05.geojson.zip","demo_2025_m06.geojson.zip"):
            (cache/fname).write_text(fname,encoding="utf-8")
        (state/"sources").mkdir(parents=True,exist_ok=True)
        run=state/"run"; run.mkdir(parents=True,exist_ok=True)
        (run/"CHAIN_STATE.json").write_text(json.dumps({"completed_stage":6,"completed_stage_label":"M06"}),encoding="utf-8")
        return state

    def test_manifest_present_and_valid_copy_is_selected(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); params = self.prepare_root(root)
            valid = self.package(root, "valid")
            state = self.state(root, "state-valid", params)
            result = select_latest_valid(
                params=params,
                candidates=[{"run_id": 200, "stage": "M06", "from_stage": "M07", "package": valid, "state_root": state}],
                root_dir=root,
            )
            self.assertEqual(result["selected"]["run_id"], "200")
            self.assertEqual(result["from_stage"], "M07")
            self.assertEqual(result["discarded"], [])

    def test_manifest_present_but_wrong_checksum_is_discarded(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); params = self.prepare_root(root)
            bad = self.package(root, "bad", corrupt_hash=True)
            state = self.state(root, "state-bad", params)
            result = select_latest_valid(
                params=params,
                candidates=[{"run_id": 201, "stage": "M06", "from_stage": "M07", "package": bad, "state_root": state}],
                root_dir=root,
            )
            self.assertIsNone(result["selected"])
            self.assertIn("checksum incorrecto", result["discarded"][0]["reason"])
            self.assertEqual(result["from_stage"], "M01")

    def test_wrong_edition_is_discarded(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); params = self.prepare_root(root)
            bad = self.package(root, "bad-edition", edition=2024)
            state = self.state(root, "state-edition", params)
            result = select_latest_valid(
                params=params,
                candidates=[{"run_id": 202, "stage": "M05", "from_stage": "M06", "package": bad, "state_root": state}],
                root_dir=root,
            )
            self.assertIsNone(result["selected"])
            self.assertIn("Fuentes BLOQUEADAS", result["discarded"][0]["reason"])

    def test_newest_invalid_falls_back_to_previous_valid(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); params = self.prepare_root(root)
            newest = self.package(root, "newest", corrupt_hash=True)
            newest_state = self.state(root, "newest-state", params)
            older = self.package(root, "older")
            older_state = self.state(root, "older-state", params)
            result = select_latest_valid(
                params=params,
                candidates=[
                    {"run_id": 300, "stage": "M06", "from_stage": "M07", "package": newest, "state_root": newest_state},
                    {"run_id": 250, "stage": "M05", "from_stage": "M06", "package": older, "state_root": older_state},
                ],
                root_dir=root,
            )
            self.assertEqual(result["selected"]["run_id"], "250")
            self.assertEqual([d["run_id"] for d in result["discarded"]], ["300"])
            self.assertEqual(result["from_stage"], "M06")

    def test_compatible_m06_with_population_block_is_not_reused(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); params=self.prepare_root(root)
            package=self.package(root,"valid")
            state=self.state(root,"state-blocked",params,outliers=3)
            result=select_latest_valid(
                params=params,
                candidates=[{"run_id":35319351944,"stage":"M06","from_stage":"M07","package":package,"state_root":state}],
                root_dir=root,
            )
            self.assertIsNone(result["selected"])
            self.assertIn("checkpoint poblacionalmente no certificado",result["discarded"][0]["reason"])
            self.assertIn("outliers=3",result["discarded"][0]["reason"])
            self.assertEqual(result["from_stage"],"M01")

    def test_compatible_m06_with_target_met_is_reused_directly(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); params=self.prepare_root(root)
            package=self.package(root,"valid")
            state=self.state(root,"state-certified",params,outliers=0)
            result=select_latest_valid(
                params=params,
                candidates=[{"run_id":200,"stage":"M06","from_stage":"M07","package":package,"state_root":state}],
                root_dir=root,
            )
            self.assertEqual(result["selected"]["run_id"],"200")
            self.assertFalse(result["selected"]["requires_derivation"])
            self.assertEqual(result["selected"]["population_evidence"]["population_decision"],"TARGET_MET")
            self.assertEqual(result["from_stage"],"M07")

    def test_old_m06_without_m05_fingerprint_derives_m04_and_resumes_m05(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); params=self.prepare_root(root)
            package=self.package(root,"valid")
            old_state=self.accumulated_state(root,"old-state",params)
            result=select_latest_valid(
                params=params,
                candidates=[{"run_id":35319351944,"stage":"M06","from_stage":"M07","package":package,"state_root":old_state}],
                root_dir=root,
            )
            self.assertEqual(result["selected"]["run_id"],"35319351944")
            self.assertTrue(result["selected"]["requires_derivation"])
            self.assertEqual(result["selected"]["effective_stage"],"M04")
            self.assertEqual(result["from_stage"],"M05")
            derived=root/"derived-m04"
            evidence=derive_checkpoint(params=params,state_root=old_state,output=derived,target_stage=4)
            self.assertEqual(evidence["derived_stage"],"M04")
            chain=json.loads((derived/"run"/"CHAIN_STATE.json").read_text(encoding="utf-8"))
            self.assertEqual(chain["completed_stage"],4)
            self.assertTrue((derived/"cache"/"demo_2025_m04.geojson.zip").is_file())
            self.assertFalse((derived/"cache"/"demo_2025_m05.geojson.zip").exists())
            self.assertFalse((derived/"cache"/"demo_2025_m06.geojson.zip").exists())

    def test_real_checkpoint_35319351944_inventory_contains_derivable_m04(self):
        fixture=ROOT / "tests" / "fixtures" / "checkpoint_35319351944_inventory.json"
        inventory=json.loads(fixture.read_text(encoding="utf-8"))
        self.assertEqual(inventory["run_id"],35319351944)
        self.assertEqual(inventory["chain_state"]["completed_stage"],6)
        self.assertEqual(
            inventory["sha256"]["cache/castilla_y_leon_2025_m04_semillas.geojson.zip"],
            "3791a1c5aee011b1972cfb13f0193929b3421a13b3d354bad67f7d638e777da4",
        )
        params=ROOT / "territorios" / "castilla_y_leon" / "config" / "castilla_y_leon_2025.yaml"
        cfg=__import__("yaml").safe_load(params.read_text(encoding="utf-8")) or {}
        required=[]
        for module_name,module_cfg in (cfg.get("modulos") or {}).items():
            try: stage=int(str(module_name).split("_")[1])
            except Exception: continue
            if stage>4: continue
            for key,value in (module_cfg or {}).items():
                if str(key).startswith("out_") and isinstance(value,str):
                    required.append(Path(value.format(
                        year=(cfg.get("meta") or {}).get("year"),
                        run_name=(cfg.get("meta") or {}).get("run_name"),
                        run_id="",
                    )).name)
        available={Path(p).name for p in inventory["files"] if p.startswith("cache/")}
        self.assertTrue(set(required) <= available)
        self.assertIn("sources/manifest.json",inventory["files"])
        self.assertIn("run/CHAIN_STATE.json",inventory["files"])


    def test_changed_m05_config_invalidates_m06(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); params=self.prepare_root(root)
            package=self.package(root,"valid")
            state=self.accumulated_state(root,"state",params)
            fingerprint=state/"compatibility"/"m05.json"; fingerprint.parent.mkdir(parents=True,exist_ok=True)
            fingerprint.write_text(json.dumps(build_fingerprint(params=params,root_dir=root)),encoding="utf-8")
            params.write_text(
                params.read_text(encoding="utf-8").replace("seed: 1","seed: 2"),
                encoding="utf-8",
            )
            result=select_latest_valid(
                params=params,
                candidates=[{"run_id":200,"stage":"M06","from_stage":"M07","package":package,"state_root":state}],
                root_dir=root,
            )
            self.assertIsNotNone(result["selected"])
            self.assertTrue(result["selected"]["requires_derivation"])
            self.assertEqual(result["from_stage"],"M05")
            self.assertIn("checkpoint incompatible con M05 actual",result["selected"]["compatibility_error"])

    def test_no_compatible_checkpoint_starts_from_m01(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); params = self.prepare_root(root)
            result = select_latest_valid(params=params, candidates=[], root_dir=root)
            self.assertIsNone(result["selected"])
            self.assertEqual(result["discarded"], [])
            self.assertEqual(result["from_stage"], "M01")


if __name__ == "__main__":
    unittest.main()
