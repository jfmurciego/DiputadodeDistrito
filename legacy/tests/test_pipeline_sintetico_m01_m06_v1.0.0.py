#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PROYECTO: Diputado de Distrito
COMPONENTE: smoke sintético M01-M06
VERSIÓN: 1.0.0
FECHA: 2026-09-12
FUNCIÓN: ejecutar los seis módulos sobre cuatro secciones artificiales contiguas y verificar conservación, K, cuotas, contigüidad y tolerancia.
ESTADO: vigente F1.5
ANTERIOR: ninguno — prueba nueva.
"""
from __future__ import annotations
import csv, json, os, subprocess, sys, tempfile, unittest, zipfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

class PipelineSinteticoM01M06(unittest.TestCase):
    def test_pipeline_completo(self):
        import geopandas as gpd
        import yaml
        from shapely.geometry import box
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);src=root/"src";src.mkdir();out=root/"out";out.mkdir()
            ids=["0100101001","0100201001","0100301001","0100401001"]
            g=gpd.GeoDataFrame({
                "CUSEC":ids,"CPRO":["01"]*4,"NPRO":["Sintética"]*4,
                "CUMUN":["01001","01002","01003","01004"],
                "NMUN":["A","B","C","D"],"CUDIS":["01"]*4,
            },geometry=[box(i,0,i+1,1) for i in range(4)],crs="EPSG:4326")
            shp=src/"secciones.shp";g.to_file(shp)
            secc=root/"seccionado.zip"
            with zipfile.ZipFile(secc,"w",zipfile.ZIP_DEFLATED) as z:
                for p in src.glob("secciones.*"):z.write(p,p.name)
            pop=root/"poblacion.csv"
            with pop.open("w",encoding="utf-8",newline="") as f:
                w=csv.writer(f);w.writerow(["Secciones","Total","Periodo","Sexo","Edad"])
                for sid in ids:w.writerow([sid,100,2025,"Total","Todas las edades"])
            cfg={
                "meta":{"run_name":"sintetico","year":2025,"scope":"provincial"},
                "io":{"project_root":{"path":str(root)},"input":{"seccionado":{"path":str(secc),"layer":"","section_key_col":"CUSEC"},"population_cip":{"paths":[str(pop)],"sep":",","section_key_col":"Secciones","pop_col":"Total","filters":{"year_col":"Periodo","sexo_col":"Sexo","edad_col":"Edad","sexo_total_values":["Total"],"edad_total_values":["Todas las edades"]}}}},
                "modulos":{
                    "modulo_01_preparar_base_territorial":{"province_codes":["01"],"drop_missing_population":False,"out_geojson":"out/m01.geojson.zip","out_report":"out/m01.json"},
                    "modulo_02_construir_adyacencias":{"in_geojson":"out/m01.geojson.zip","id_field":"CUSEC_KEY","out_edges_jsonl":"out/m02.jsonl","predicate":"touches","working_crs":"EPSG:3035","min_shared_border_m":0.0,"buffer_m":0.0,"simplify_m":0.0,"max_candidates":0,"log_every":0},
                    "modulo_03_construir_grafo":{"in_geojson":"out/m01.geojson.zip","in_edges_jsonl":"out/m02.jsonl","id_field":"CUSEC_KEY","pop_field":"POP_{year}","out_graph_json":"out/m03.json","out_report":"out/m03_report.json"},
                    "modulo_04_generar_semillas":{"in_graph_json":"out/m03.json","in_geojson":"out/m01.geojson.zip","id_field":"CUSEC_KEY","pop_field":"POP_{year}","province_field":"CPRO","municipality_field":"CUMUN","municipality_name_field":"NMUN","district_apportionment":"hamilton","k_districts":2,"municipality_atomicity_limit_ratio":1.5,"seed":12345,"out_geojson":"out/m04.geojson.zip","out_report":"out/m04.json"},
                    "modulo_05_optimizar_distritos":{"in_graph_json":"out/m03.json","in_geojson":"out/m04.geojson.zip","id_field":"CUSEC_KEY","pop_field":"POP_{year}","district_field":"district_id","province_field":"CPRO","municipality_field":"CUMUN","greedy_moves_limit":20,"anneal_iters":100,"seed":12345,"anneal_seed_offset":0,"anneal_outside_penalty":0.01,"anneal_maxdev_weight":0.05,"anneal_churn_weight":0.0016,"anneal_temp_start":0.02,"anneal_temp_end":0.0005,"swap_polish_max":0,"out_geojson":"out/m05.geojson.zip","out_report":"out/m05.json"},
                    "modulo_06_consolidar_distritos":{"in_geojson":"out/m05.geojson.zip","id_field":"CUSEC_KEY","district_field":"district_id","pop_field":"POP_{year}","province_field":"CPRO","province_name_field":"NPRO","municipality_field":"CUMUN","municipality_name_field":"NMUN","cudis_field":"CUDIS","metric_crs":"EPSG:3035","expected_districts":2,"strict_expected_k":True,"out_summary_csv":"out/m06_summary.csv","out_catalog_csv":"out/m06_catalog.csv","out_composition_csv":"out/m06_composition.csv","out_geojson":"out/m06_sections.geojson.zip","out_district_geojson":"out/m06_districts.geojson.zip"},
                },
                "validation":{"expected_districts":2,"population_floor_ratio":0.50,"population_cap_ratio":1.50,"target_tolerance_ratio":0.50,"province_districts":{"01":2},"province_field":"CPRO","municipality_field":"CUMUN","municipality_name_field":"NMUN","require_graph_contiguity":True,"require_one_graph_component_per_province":True,"require_connected_municipalities":True,"require_single_province_per_district":True,"require_municipality_discipline":True,"max_mixed_districts_per_split_municipality":1},
            }
            params=root/"params.yaml";params.write_text(yaml.safe_dump(cfg,sort_keys=False),encoding="utf-8")
            env=dict(os.environ);env["PYTHONHASHSEED"]="0"
            for n in range(1,7):
                script=ROOT/"modulos"/f"{n:02d}_"+["preparar_base_territorial","construir_adyacencias","construir_grafo","generar_semillas","optimizar_distritos","consolidar_distritos"][n-1]+".py"
                p=subprocess.run([sys.executable,str(script),"--params",str(params)],cwd=ROOT,env=env,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
                self.assertEqual(p.returncode,0,f"M{n:02d}\n{p.stdout}")
            with (out/"m06_summary.csv").open(encoding="utf-8",newline="") as f:summary=list(csv.DictReader(f))
            with (out/"m06_composition.csv").open(encoding="utf-8",newline="") as f:comp=list(csv.DictReader(f))
            self.assertEqual(len(summary),2);self.assertEqual(len(comp),4)
            self.assertEqual(sum(int(r["section_pop"]) for r in comp),400)
            self.assertTrue(all(r["within_hard_bounds"].lower()=="true" for r in summary))
            self.assertTrue(all(r["within_target_tolerance"].lower()=="true" for r in summary))
            graph=json.loads((out/"m03.json").read_text())
            self.assertEqual(len(graph["nodes"]),4);self.assertEqual(len(graph["edges"]),3)

if __name__=="__main__":unittest.main()
