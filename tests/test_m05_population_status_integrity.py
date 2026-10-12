"""Final M05 population labels must match section-derived totals."""
import csv
import importlib.util
import json
import os
import tempfile
import unittest
from pathlib import Path

import geopandas as gpd
from shapely.geometry import Point

from ddd_core.m05_swap_polish import load_geo


MODULE_PATH = Path(__file__).resolve().parents[1] / "modulos" / "05_optimizar_distritos.py"
SPEC = importlib.util.spec_from_file_location("m05_population_status_integrity", MODULE_PATH)
M05 = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(M05)


class PopulationStatusIntegrityTests(unittest.TestCase):
    def test_refresh_changes_obsolete_below_floor_to_pass_and_rebuilds_report(self):
        frame = gpd.GeoDataFrame({
            "CUSEC_KEY": ["s1", "s2", "s3"],
            "district_id": [1, 1, 2],
            "ddd_population_status": ["BELOW_FLOOR"] * 3,
        }, geometry=[Point(0, 0), Point(1, 0), Point(2, 0)], crs="EPSG:4326")
        with tempfile.TemporaryDirectory() as raw:
            report = Path(raw) / "m05_report.json"
            report.write_text(json.dumps({"population_status_by_district": {
                "1": {"population": 17, "floor": 40, "cap": 100, "population_status": "BELOW_FLOOR"},
            }}))
            refreshed = M05._refresh_population_report(
                report, frame, "district_id", {"s1": 20, "s2": 25, "s3": 50},
                "CUSEC_KEY", 50, 40, 100, 6, {},
            )
            saved = json.loads(report.read_text())
        self.assertEqual(refreshed["ddd_population_status"].tolist(), ["PASS", "PASS", "PASS"])
        self.assertEqual(saved["population_status_by_district"]["1"]["population"], 45)
        self.assertEqual(saved["population_status_by_district"]["1"]["population_status"], "PASS")
        self.assertEqual(saved["population_status_by_district"]["2"]["population"], 50)

    def test_private_repair_refreshes_section_status_and_report_before_official_admission(self):
        from unittest.mock import patch

        frame=gpd.GeoDataFrame({
            "CUSEC_KEY":["s1","s2","s3","s4"],"ddd_unit_id":["u1","u2","u3","u4"],
            "CPRO":["28"]*4,"district_id":[1,1,2,2],"ddd_closed_urban":[False]*4,
            "POP_2023":[20,10,30,40],"ddd_population_status":["BELOW_FLOOR"]*4,
        },geometry=[Point(0,0),Point(1,0),Point(2,0),Point(3,0)],crs="EPSG:4326")
        with tempfile.TemporaryDirectory() as raw:
            root=Path(raw); graph=root/"graph.json"
            graph.write_text(json.dumps({"nodes":[{"id":f"s{i}","pop":p} for i,p in enumerate([20,10,30,40],1)],
                "edges":[{"u":"s1","v":"s2"},{"u":"s3","v":"s4"},{"u":"s1","v":"s3"},{"u":"s2","v":"s4"}]}))
            output=root/"candidate.geojson.zip"; report=root/"report.json"
            report.write_text(json.dumps({"population_status_by_district":{"1":{"population":30,"floor":40,"cap":87.5,"population_status":"BELOW_FLOOR"}}}))
            cfg={"validation":{"population_floor_ratio":0.8,"population_cap_ratio":1.75,"target_tolerance_ratio":0.12}}
            s5={"in_graph_json":str(graph),"id_field":"CUSEC_KEY","district_field":"district_id","province_field":"CPRO",
                "pop_field":"POP_2023","population_repair":{"enabled":True,"strategy":"private_annealing","seed":4629}}
            candidate={"u1":1,"u2":2,"u3":1,"u4":2}
            meta={"accepted":True,"assignments":candidate,"seed":4629,"result":"REPAIRED"}
            def pass_gate(_cfg,geo,out_path,_seed):
                M05.write_geo(geo,out_path)
                return {"passed":True,"m06":"PASS"}
            with patch.object(M05,"load_geo",return_value=frame.copy()), \
                 patch.object(M05,"repair_private",return_value=meta), \
                 patch.object(M05,"_official_private_candidate_gate",side_effect=pass_gate):
                result=M05._apply_population_repair(cfg,s5,output,report)
            saved=json.loads(report.read_text()); product=load_geo(output)
        self.assertTrue(result["accepted"])
        self.assertEqual(product["ddd_population_status"].tolist(),["PASS"]*4)
        self.assertEqual(saved["population_status_by_district"]["1"]["population"],50)
        self.assertEqual(saved["population_status_by_district"]["2"]["population"],50)
        self.assertEqual(saved["population_status_by_district"]["1"]["population_status"],"PASS")

    @unittest.skipUnless(os.environ.get("DDD_M05_MADRID_RUN_DIR"), "set DDD_M05_MADRID_RUN_DIR to a frozen official run")
    def test_madrid_all_district_populations_and_statuses_match_m05_m06_products(self):
        run = Path(os.environ["DDD_M05_MADRID_RUN_DIR"])
        m05_geo = load_geo(run / "m05_candidate.geojson.zip")
        m06_geo = load_geo(run / "official" / "madrid_2025_m06_secciones.geojson.zip")
        report = json.loads((run / "m05_report.json").read_text())
        diagnostic = json.loads((run / "official" / "madrid_2025_m06_resumen_distritos_diagnostico.json").read_text())
        summary_path = run / "official" / "madrid_2025_m06_resumen_distritos.csv"
        with summary_path.open(newline="") as stream:
            summary = {str(row["district_id"]): row for row in csv.DictReader(stream)}

        self.assertEqual(len(report["population_status_by_district"]), 135)
        self.assertEqual(len(summary), 135)
        self.assertEqual(diagnostic["observed_districts"], 135)
        self.assertEqual(int(m05_geo["CUSEC_KEY"].nunique()), 4479)
        self.assertEqual(int(m06_geo["CUSEC_KEY"].nunique()), 4479)
        for label, frame in (("M05", m05_geo), ("M06 sections", m06_geo)):
            pops = frame.groupby(frame["district_id"].astype(str))["POP_2023"].sum().astype(int).to_dict()
            status = frame.groupby(frame["district_id"].astype(str))["ddd_population_status"].first().to_dict()
            self.assertEqual(set(pops), set(report["population_status_by_district"]), label)
            for district, population in pops.items():
                with self.subTest(product=label, district=district):
                    m05row = report["population_status_by_district"][district]
                    m06row = summary[district]
                    self.assertEqual(population, int(m05row["population"]))
                    self.assertEqual(population, int(float(m06row["district_pop"])))
                    self.assertEqual(status[district], m05row["population_status"])
                    self.assertEqual(status[district], m06row["population_status"])
        self.assertEqual(diagnostic["total_population"], 6871903)
        self.assertEqual(sum(int(v["population"]) for v in report["population_status_by_district"].values()), 6871903)


if __name__ == "__main__":
    unittest.main()
