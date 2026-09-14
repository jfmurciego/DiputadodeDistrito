#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PROYECTO: Diputado de Distrito
HERRAMIENTA: Generador de configuración bootstrap territorial
VERSIÓN: 1.0.0
NOMBRE DE VERSIÓN: Bootstrap M01-M03 observable
FECHA: 2026-09-12
ESTADO: vigente — R022
QUÉ HACE: genera un YAML efímero M01-M03 para un territorio del catálogo nacional, con auditorías topológicas activas y enforcement desactivado.
POR QUÉ ES SEPARADA: el catálogo planifica territorios; esta herramienta transforma esa declaración en un contrato ejecutable sin duplicar YAML ni lógica en Actions.
CAMBIOS: primera versión.
MOTIVO: ejecutar Madrid y el resto de España con el mismo motor y medir antes de fijar cardinalidades, puentes, K o tolerancias.
ANTERIOR: ninguno — herramienta nueva.
"""
from __future__ import annotations
import argparse
from pathlib import Path
import yaml

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--catalog",default="configuracion/catalogo_territorios_espana_2025.yaml")
    ap.add_argument("--territory",required=True)
    ap.add_argument("--out",required=True)
    a=ap.parse_args()
    cat=yaml.safe_load(Path(a.catalog).read_text(encoding="utf-8"))
    matches=[x for x in cat["territories"] if x["territory_id"]==a.territory]
    if len(matches)!=1: raise SystemExit(f"Territorio no único/no encontrado: {a.territory}")
    t=matches[0];tid=t["territory_id"];run=f"{tid}_2025";base=f"territorios/{tid}/.cache/ddd/preparacion/{{run_name}}"
    cfg={
      "meta":{"procedure_name":"Diputado de Distrito","territory_id":tid,"territory":t["name"],"run_name":run,"year":2025,"scope":"provincial","schema_version":"bootstrap-1.0.0","status":"observation_m01_m03"},
      "io":{"project_root":{"path":"../../.."},"input":{"seccionado":{"path":"inputs/seccionado_2025.zip","layer":"","section_key_col":"CUSEC"},"population_cip":{"paths":["inputs/65034.csv.zip"],"sep":"auto","section_key_col":"Secciones","pop_col":"Total","filters":{"year_col":"Periodo","sexo_col":"Sexo","edad_col":"Edad","sexo_total_values":["Total"],"edad_total_values":["Todas las edades"]}}},"cache":{"dir":base}},
      "territory_contract":{"unit_id_role":"census_section","admin_level_1_role":"province","admin_level_2_role":"municipality","province_codes":t["province_codes"],"status":"bootstrap_observation","topology_mode":"archipelago" if t["batch"]=="insular" else "land"},
      "modulos":{
        "modulo_01_preparar_base_territorial":{"province_codes":t["province_codes"],"drop_missing_population":False,"out_geojson":base+f"/{run}_m01_secciones_poblacion.geojson.zip","out_report":base+f"/{run}_m01_informe.json"},
        "modulo_02_construir_adyacencias":{"in_geojson":base+f"/{run}_m01_secciones_poblacion.geojson.zip","id_field":"CUSEC_KEY","out_edges_jsonl":base+f"/{run}_m02_adyacencias.jsonl","predicate":"contact","working_crs":"EPSG:3035","min_shared_border_m":1.0,"max_precision_overlap_area_m2":1.0,"buffer_m":0.0,"simplify_m":0.0,"max_candidates":0,"log_every":10000,"topology_bridges":[]},
        "modulo_03_construir_grafo":{"in_geojson":base+f"/{run}_m01_secciones_poblacion.geojson.zip","in_edges_jsonl":base+f"/{run}_m02_adyacencias.jsonl","id_field":"CUSEC_KEY","pop_field":"POP_{year}","out_graph_json":base+f"/{run}_m03_grafo.json","out_report":base+f"/{run}_m03_informe.json"}},
      "validation":{"expected_province_codes":t["province_codes"],"require_unique_section_id":True,"require_non_null_population":True,"province_field":"CPRO","municipality_field":"CUMUN","municipality_name_field":"NMUN","audit_graph_components":True,"audit_admin_level_1_components":True,"audit_admin_level_2_components":True,"require_one_graph_component_per_province":False,"require_connected_municipalities":False}
    }
    out=Path(a.out);out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(yaml.safe_dump(cfg,sort_keys=False,allow_unicode=True),encoding="utf-8")
    print(out)

if __name__=="__main__":main()
