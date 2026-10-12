import tempfile
import unittest
from pathlib import Path
import importlib.util
import json
import sys
from types import ModuleType
from unittest.mock import patch
import os
import yaml

from ddd_core.m05_atomic_output import CandidateRejected, run_staged_output


class AtomicOutputTests(unittest.TestCase):
    def test_private_noop_still_runs_official_gate_before_admission(self):
        import geopandas as gpd
        from shapely.geometry import Point

        source = Path(__file__).resolve().parents[1] / "modulos" / "05_optimizar_distritos.py"
        spec = importlib.util.spec_from_file_location("m05_noop_gate_test", source)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        original = gpd.GeoDataFrame({
            "CUSEC_KEY": ["s1", "s2"], "ddd_unit_id": ["u1", "u2"],
            "CPRO": ["28", "28"], "district_id": [0, 1],
            "ddd_closed_urban": [False, False], "POP_2023": [50, 50],
        }, geometry=[Point(0, 0), Point(1, 0)], crs="EPSG:4326")
        with tempfile.TemporaryDirectory() as raw:
            graph_path = Path(raw) / "graph.json"
            graph_path.write_text(json.dumps({
                "nodes": [{"id": "s1", "pop": 50}, {"id": "s2", "pop": 50}],
                "edges": [{"u": "s1", "v": "s2"}],
            }))
            s5 = {
                "in_graph_json": str(graph_path), "id_field": "CUSEC_KEY",
                "district_field": "district_id", "province_field": "CPRO",
                "population_repair": {"enabled": True, "strategy": "private_annealing", "seed": 4629},
            }
            cfg = {"validation": {
                "population_floor_ratio": 0.8, "population_cap_ratio": 1.75,
                "target_tolerance_ratio": 0.12,
            }}
            for gate_result, admitted in (({"passed": True, "m06": "PASS"}, True),
                                          ({"passed": False, "reason": "M06_FAIL"}, False)):
                with self.subTest(admitted=admitted):
                    gate = unittest.mock.Mock(return_value=gate_result)
                    with patch.object(module, "load_geo", return_value=original.copy()), \
                         patch.object(module, "_official_private_candidate_gate", gate):
                        meta = module._apply_population_repair(cfg, s5, Path(raw) / "staged.zip", None)
                    gate.assert_called_once()
                    self.assertEqual(meta["result"], "NOT_NEEDED" if admitted else "ATOMIC_REJECTION_OFFICIAL_VALIDATION")
                    self.assertEqual(meta["accepted"], admitted)
                    self.assertEqual(meta["official_atomic_gate"], gate_result)
                    self.assertEqual(original.district_id.tolist(), [0, 1])

    def test_official_gate_failure_and_timeout_never_replace_durable_candidate(self):
        source = Path(__file__).resolve().parents[1] / "modulos" / "05_optimizar_distritos.py"
        spec = importlib.util.spec_from_file_location("m05_official_gate_atomic_test", source)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        outcomes = (
            ("M06 failure", [1], "M06_FAIL"),
            ("validator failure", [0, 1], "VALIDAR_EJECUCION_FAIL"),
            ("validator timeout", [0, TimeoutError], "VALIDAR_EJECUCION_TIMEOUT"),
        )
        for label, statuses, expected_reason in outcomes:
            with self.subTest(outcome=label), tempfile.TemporaryDirectory() as raw:
                root = Path(raw); output = root / "durable-candidate.geojson.zip"
                graph = root / "graph.json"; graph.write_text("{}")
                output.write_bytes(b"original durable checkpoint")
                config = {
                    "meta": {"territory_id": "madrid", "run_name": "madrid_2025"},
                    "modulos": {
                        "modulo_05_optimizar_distritos": {"in_graph_json": str(graph)},
                        "modulo_03_construir_grafo": {"out_graph_json": str(graph)},
                        "modulo_06_consolidar_distritos": {
                            "id_field": "CUSEC_KEY", "district_field": "district_id",
                        "out_summary_csv": str(root / "summary.csv"), "out_catalog_csv": str(root / "catalog.csv"),
                            "out_composition_csv": "composition.csv", "out_geojson": "sections.zip",
                            "out_district_geojson": "districts.zip", "out_diagnostic_json": str(root / "diagnostic.json"),
                            "expected_districts": 135,
                        },
                    },
                }
                calls = []
                def fake_run(*_args, **_kwargs):
                    index = len(calls); calls.append(index)
                    status = statuses[min(index, len(statuses)-1)]
                    if status is TimeoutError:
                        raise module.subprocess.TimeoutExpired("official validator", 120)
                    return module.subprocess.CompletedProcess([], status, "", "injected gate result")
                with patch.object(module, "write_geo", side_effect=lambda _g, p: Path(p).write_bytes(b"private candidate")), \
                     patch.object(module.subprocess, "run", side_effect=fake_run):
                    result = module._official_private_candidate_gate(config, object(), output, 4629)
                self.assertFalse(result["passed"])
                self.assertEqual(result["reason"], expected_reason)
                self.assertEqual(output.read_bytes(), b"original durable checkpoint")
                self.assertEqual(list(root.glob("ddd_m05_private_gate_*")), [])

    def test_private_cli_runs_base_in_staging_before_rejection(self):
        source = Path(__file__).resolve().parents[1] / "modulos" / "05_optimizar_distritos.py"
        yaml_stub = ModuleType("yaml")
        yaml_stub.safe_load = lambda value: json.loads(value)
        yaml_stub.safe_dump = lambda value, **_kw: json.dumps(value)
        with tempfile.TemporaryDirectory() as raw:
            root=Path(raw); params=root/"params.yaml"; source_input=root/"input.zip"
            output=root/"existing-output.zip"; report=root/"existing-report.json"
            source_input.write_bytes(b"input"); output.write_bytes(b"previous durable result"); report.write_bytes(b"previous report")
            config={"modulos":{"modulo_05_optimizar_distritos":{
                "in_geojson":str(source_input),"out_geojson":str(output),"out_report":str(report),
                "population_repair":{"enabled":True,"strategy":"private_annealing"}}}}
            params.write_text(json.dumps(config))
            spec=importlib.util.spec_from_file_location("m05_atomic_cli_test",source)
            module=importlib.util.module_from_spec(spec)
            with patch.dict(sys.modules,{"yaml":yaml_stub,"geopandas":ModuleType("geopandas"),"pandas":ModuleType("pandas")}):
                spec.loader.exec_module(module)
                staged_paths=[]
                def fake_base(path):
                    staged_config=json.loads(Path(path).read_text())
                    staged=Path(staged_config["modulos"]["modulo_05_optimizar_distritos"]["out_geojson"])
                    staged_paths.append(staged); staged.write_bytes(b"baseline that must remain private")
                module._ogr_can_read_unit=lambda _path: True
                module._run_base=fake_base
                module._post=lambda *_args: ({}, {"accepted":False,"result":"NO_FEASIBLE_REPAIR_FOUND"})
                with patch.object(sys,"argv",[str(source),"--params",str(params)]):
                    with self.assertRaises(SystemExit) as caught:module.main()
                self.assertEqual(len(staged_paths),1,str(caught.exception))
                self.assertNotEqual(staged_paths[0],output)
                self.assertFalse(staged_paths[0].exists())
                self.assertEqual(output.read_bytes(),b"previous durable result")
                self.assertEqual(report.read_bytes(),b"previous report")

    def test_official_validation_rejection_and_timeout_preserve_durable_outputs(self):
        source = Path(__file__).resolve().parents[1] / "modulos" / "05_optimizar_distritos.py"
        yaml_stub = ModuleType("yaml")
        yaml_stub.safe_load = lambda value: json.loads(value)
        yaml_stub.safe_dump = lambda value, **_kw: json.dumps(value)
        outcomes = (
            ("validation rejection", lambda *_args: ({}, {
                "accepted": False,
                "result": "ATOMIC_REJECTION_OFFICIAL_VALIDATION",
                "official_atomic_gate": {"passed": False, "reason": "VALIDAR_EJECUCION_FAIL"},
            })),
            ("timeout", lambda *_args: (_ for _ in ()).throw(TimeoutError("official gate timeout"))),
        )
        for label, post in outcomes:
            with self.subTest(outcome=label), tempfile.TemporaryDirectory() as raw:
                root=Path(raw); params=root/"params.yaml"; source_input=root/"input.zip"
                output=root/"existing-output.zip"; report=root/"existing-report.json"
                source_input.write_bytes(b"input"); output.write_bytes(b"previous durable result"); report.write_bytes(b"previous report")
                config={"modulos":{"modulo_05_optimizar_distritos":{
                    "in_geojson":str(source_input),"out_geojson":str(output),"out_report":str(report),
                    "population_repair":{"enabled":True,"strategy":"private_annealing"}}}}
                params.write_text(json.dumps(config))
                spec=importlib.util.spec_from_file_location("m05_atomic_gate_test",source)
                module=importlib.util.module_from_spec(spec)
                with patch.dict(sys.modules,{"yaml":yaml_stub,"geopandas":ModuleType("geopandas"),"pandas":ModuleType("pandas")}):
                    spec.loader.exec_module(module)
                    def fake_base(path):
                        staged_config=json.loads(Path(path).read_text())
                        staged=Path(staged_config["modulos"]["modulo_05_optimizar_distritos"]["out_geojson"])
                        staged.write_bytes(b"baseline remains private")
                    module._ogr_can_read_unit=lambda _path: True
                    module._run_base=fake_base
                    module._post=post
                    with patch.object(sys,"argv",[str(source),"--params",str(params)]):
                        with self.assertRaises(SystemExit): module.main()
                self.assertEqual(output.read_bytes(),b"previous durable result")
                self.assertEqual(report.read_bytes(),b"previous report")

    def test_rejected_cli_run_preserves_existing_geojson_and_report(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw); output = root / "m05.zip"; report = root / "m05.json"
            output.write_bytes(b"original checkpoint"); report.write_bytes(b"original report")

            def execute(staged, staged_report):
                staged.write_bytes(b"invalid baseline produced before repair")
                staged_report.write_bytes(b"rejected run metadata")
                return False, {"accepted": False}

            with self.assertRaises(CandidateRejected):
                run_staged_output(output, report, execute)
            self.assertEqual(output.read_bytes(), b"original checkpoint")
            self.assertEqual(report.read_bytes(), b"original report")

    def test_admitted_cli_run_promotes_geojson_and_report(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw); output = root / "m05.zip"; report = root / "m05.json"
            output.write_bytes(b"original checkpoint")

            def execute(staged, staged_report):
                staged.write_bytes(b"officially admitted candidate")
                staged_report.write_bytes(b"accepted report")
                return True, {"accepted": True}

            result = run_staged_output(output, report, execute)
            self.assertTrue(result["accepted"])
            self.assertEqual(output.read_bytes(), b"officially admitted candidate")
            self.assertEqual(report.read_bytes(), b"accepted report")

    def test_rejection_diagnostic_reports_timeout_cause_without_assignments(self):
        source = Path(__file__).resolve().parents[1] / "modulos" / "05_optimizar_distritos.py"
        spec = importlib.util.spec_from_file_location("m05_rejection_diagnostic_test", source)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        meta = {
            "result": "NO_FEASIBLE_REPAIR_FOUND",
            "termination_reason": "TIME_BUDGET_EXHAUSTED",
            "elapsed_seconds": 65.01,
            "candidates": 600000,
            "expanded": 180000,
            "accepted_moves": 90000,
            "assignments": {"private-unit": 7},
        }
        from contextlib import redirect_stderr
        from io import StringIO
        captured = StringIO()
        with redirect_stderr(captured):
            module._emit_private_rejection_diagnostic(meta)
        output = captured.getvalue()
        self.assertIn('"wrapper_version": "7.8.4"', output)
        self.assertIn('"termination_reason": "TIME_BUDGET_EXHAUSTED"', output)
        self.assertIn('"candidates": 600000', output)
        self.assertNotIn("assignments", output)
        self.assertNotIn("private-unit", output)

    def test_report_write_failure_preserves_existing_products(self):
        with tempfile.TemporaryDirectory() as raw:
            root=Path(raw); output=root/"m05.zip"; report=root/"m05.json"
            output.write_bytes(b"original valid GeoJSON"); report.write_bytes(b"original valid report")
            def execute(staged, staged_report):
                staged.write_bytes(b"private candidate")
                original_write=Path.write_bytes
                def fail_report(path, data):
                    if path == staged_report:
                        raise OSError("injected staged report write failure")
                    return original_write(path, data)
                with patch.object(Path,"write_bytes",fail_report):
                    staged_report.write_bytes(b"candidate report")
                return True,{"accepted":True}
            with self.assertRaisesRegex(OSError,"staged report write failure"):
                run_staged_output(output,report,execute)
            self.assertEqual(output.read_bytes(),b"original valid GeoJSON")
            self.assertEqual(report.read_bytes(),b"original valid report")
            self.assertEqual(list(root.glob("ddd_m05_private_*")),[])

    def test_exception_during_run_preserves_existing_output(self):
        with tempfile.TemporaryDirectory() as raw:
            output = Path(raw) / "m05.zip"; output.write_bytes(b"original")

            def execute(staged, _report):
                staged.write_bytes(b"partial")
                raise TimeoutError("test timeout")

            with self.assertRaises(TimeoutError):
                run_staged_output(output, None, execute)
            self.assertEqual(output.read_bytes(), b"original")

    def test_missing_staged_report_rejects_before_promoting_geojson(self):
        with tempfile.TemporaryDirectory() as raw:
            root=Path(raw); output=root/"m05.zip"; report=(root/"m05.json").resolve()
            output.write_bytes(b"original"); report.write_bytes(b"old report")
            def execute(staged,_staged_report):
                staged.write_bytes(b"candidate")
                return True,{"accepted":True}
            with self.assertRaises(CandidateRejected):run_staged_output(output,report,execute)
            self.assertEqual(output.read_bytes(),b"original")
            self.assertEqual(report.read_bytes(),b"old report")

    def test_report_promotion_error_rolls_back_geojson(self):
        with tempfile.TemporaryDirectory() as raw:
            root=Path(raw); output=root/"m05.zip"; report=(root/"m05.json").resolve()
            output.write_bytes(b"original"); report.write_bytes(b"old report")
            def execute(staged,staged_report):
                staged.write_bytes(b"candidate"); staged_report.write_bytes(b"new report")
                return True,{"accepted":True}
            original_replace=os.replace
            def fail_report_replace(source,destination):
                if Path(destination)==report and not str(source).endswith(".previous"):
                    raise OSError("simulated report promotion failure")
                return original_replace(source,destination)
            with patch("ddd_core.m05_atomic_output.os.replace",side_effect=fail_report_replace):
                with self.assertRaises(OSError):run_staged_output(output,report,execute)
            self.assertEqual(output.read_bytes(),b"original")
            self.assertEqual(report.read_bytes(),b"old report")

    def test_explicit_m06_diagnostic_is_staged_and_rejection_preserves_all_durable_outputs(self):
        source = Path(__file__).resolve().parents[1] / "modulos" / "05_optimizar_distritos.py"
        spec=importlib.util.spec_from_file_location("m05_diagnostic_staging_test",source)
        module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
        with tempfile.TemporaryDirectory() as raw:
            root=Path(raw); module.ROOT=root
            contract_dir=root/"territorios"/"madrid"/"config"; contract_dir.mkdir(parents=True)
            (contract_dir/"madrid.yaml").write_text(yaml.safe_dump({"meta":{"run_name":"madrid_2025"}}))
            graph=root/"graph.json"; graph.write_text("{}")
            output_dir=root/"durable"; output_dir.mkdir()
            keys=("out_summary_csv","out_catalog_csv","out_composition_csv","out_geojson","out_district_geojson","out_diagnostic_json")
            durable={key:output_dir/f"{key}.out" for key in keys}
            originals={key:f"previous:{key}".encode() for key in keys}
            for key,path in durable.items():path.write_bytes(originals[key])
            cfg={"meta":{"territory_id":"madrid","run_name":"madrid_2025"},"modulos":{
                "modulo_05_optimizar_distritos":{"in_graph_json":str(graph)},
                "modulo_03_construir_grafo":{"out_graph_json":str(graph)},
                "modulo_06_consolidar_distritos":{
                    **{key:str(path) for key,path in durable.items()},
                    "id_field":"CUSEC_KEY","district_field":"district_id","expected_districts":135,
                },
            }}
            outcomes=(
                ("m06 failure","M06_FAIL"),("m06 timeout","M06_TIMEOUT"),
                ("validator failure","VALIDAR_EJECUCION_FAIL"),
                ("validator timeout","VALIDAR_EJECUCION_TIMEOUT"),
                ("validator exception","VALIDAR_EJECUCION_EXCEPTION"),
                ("audit failure","GEOMETRIC_AUDIT_FAIL"),("audit timeout","GEOMETRIC_AUDIT_TIMEOUT"),
                ("audit exception","GEOMETRIC_AUDIT_EXCEPTION"),
            )
            for mode,expected_reason in outcomes:
                with self.subTest(mode=mode):
                    observed={}
                    def fake_run(command,**kwargs):
                        program=Path(command[1]).name
                        if program=="06_consolidar_distritos.py":
                            staged=yaml.safe_load(Path(command[-1]).read_text())
                            staged_m6=staged["modulos"]["modulo_06_consolidar_distritos"]
                            observed.update({key:Path(staged_m6[key]) for key in keys})
                            self.assertTrue(all(path!=durable[key] and root in path.parents for key,path in observed.items()))
                            observed["out_diagnostic_json"].write_bytes(b"private diagnostic from rejected M06")
                            if mode=="m06 timeout":raise module.subprocess.TimeoutExpired(command,120)
                            if mode=="m06 failure":return module.subprocess.CompletedProcess(command,1,"","injected M06 rejection")
                        elif program=="validar_ejecucion.py":
                            run_id=command[command.index("--run-id")+1]
                            operational=root/"ejecuciones"/run_id/"VALIDACION.json"; operational.parent.mkdir(parents=True); operational.write_text("operational only")
                            if mode=="validator timeout":raise module.subprocess.TimeoutExpired(command,120)
                            if mode=="validator exception":raise OSError("injected validator exception")
                            if mode=="validator failure":return module.subprocess.CompletedProcess(command,1,"","injected validator rejection")
                        else:
                            if mode=="audit timeout":raise module.subprocess.TimeoutExpired(command,120)
                            if mode=="audit exception":raise OSError("injected audit exception")
                            if mode=="audit failure":return module.subprocess.CompletedProcess(command,1,"","injected audit rejection")
                            audit_path=Path(command[command.index("--output")+1])
                            audit_path.write_text(json.dumps({"decision":"PASS_WITH_EXCEPTIONS","gate_statement":"ok","contract_sha256":"test"}))
                        return module.subprocess.CompletedProcess(command,0,"","")
                    with patch.object(module,"write_geo",side_effect=lambda _g,p:Path(p).write_bytes(b"candidate")), \
                         patch.object(module.subprocess,"run",side_effect=fake_run):
                        result=module._official_private_candidate_gate(cfg,object(),output_dir/"candidate.zip",4629)
                    self.assertFalse(result["passed"]); self.assertEqual(result["reason"],expected_reason)
                    self.assertEqual(set(observed),set(keys))
                    for key,path in durable.items():self.assertEqual(path.read_bytes(),originals[key],key)
                    self.assertFalse(list(output_dir.glob("ddd_m05_private_gate_*")))
                    self.assertFalse((root/"ejecuciones").exists())

    def test_validator_operational_report_is_cleaned_after_private_gate_failure(self):
        source = Path(__file__).resolve().parents[1] / "modulos" / "05_optimizar_distritos.py"
        spec=importlib.util.spec_from_file_location("m05_private_operational_report_test",source)
        module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
        with tempfile.TemporaryDirectory() as raw:
            root=Path(raw); module.ROOT=root
            contract_dir=root/"territorios"/"madrid"/"config"; contract_dir.mkdir(parents=True)
            (contract_dir/"madrid.yaml").write_text(yaml.safe_dump({"meta":{"run_name":"madrid_2025"}}))
            graph=root/"graph.json"; graph.write_text("{}")
            cfg={"meta":{"territory_id":"madrid","run_name":"madrid_2025"},"modulos":{
                "modulo_05_optimizar_distritos":{"in_graph_json":str(graph)},
                "modulo_03_construir_grafo":{"out_graph_json":str(graph)},
                "modulo_06_consolidar_distritos":{"out_summary_csv":"s.csv","out_catalog_csv":"c.csv",
                    "out_composition_csv":"p.csv","out_geojson":"s.zip","out_district_geojson":"d.zip",
                    "id_field":"CUSEC_KEY","district_field":"district_id","expected_districts":135},
            }}
            calls=[]
            def fake_run(command,**kwargs):
                calls.append(command)
                if "validar_ejecucion.py" in command[1]:
                    run_id=command[command.index("--run-id")+1]
                    report=root/"ejecuciones"/run_id/"VALIDACION.json"; report.parent.mkdir(parents=True); report.write_text("operational report")
                    return module.subprocess.CompletedProcess(command,1,"","injected validator rejection")
                return module.subprocess.CompletedProcess(command,0,"","")
            with patch.object(module,"write_geo",side_effect=lambda _g,p:Path(p).write_bytes(b"candidate")), \
                 patch.object(module.subprocess,"run",side_effect=fake_run):
                result=module._official_private_candidate_gate(cfg,object(),root/"candidate.zip",4629)
            self.assertEqual(result["reason"],"VALIDAR_EJECUCION_FAIL")
            self.assertFalse((root/"ejecuciones").exists())


if __name__ == "__main__":
    unittest.main()
