#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PROYECTO: Diputado de Distrito
Módulo 07 — Agregar resultados electorales
VERSIÓN: 7.0.0
NOMBRE DE VERSIÓN: Agregación electoral desacoplada
FECHA: 2026-09-11
ESTADO: candidato
QUÉ HACE: agrega resultados electorales de sección a distrito y calcula ganador y bloque por distrito.
POR QUÉ ES SEPARADO: la elección analizada nunca debe condicionar la geometría de los distritos; puede sustituirse la elección sin redistritar.
VERSIÓN ANTERIOR: legacy/recuperado_2026-09-11_v6/scripts/ddd_step7_aggregate_election_results_v6_1_params.py
"""
from __future__ import annotations
import argparse,io,json,re,sys,zipfile
from pathlib import Path
import geopandas as gpd
import pandas as pd
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from ddd_core.config import load_params_yaml,module_cfg,require
def load_geo(path):
    p=Path(path)
    if p.suffix.lower()=='.zip':
        with zipfile.ZipFile(p) as z:
            member=next(n for n in z.namelist() if n.lower().endswith(('.geojson','.json')) and not n.endswith('/'));data=z.read(member)
        return gpd.read_file(io.BytesIO(data))
    return gpd.read_file(p)
def write_geo(gdf,path):
    out=Path(path);out.parent.mkdir(parents=True,exist_ok=True);tmp=out.parent/(out.stem.replace('.geojson','')+'.geojson');gdf.to_file(tmp,driver='GeoJSON')
    with zipfile.ZipFile(out,'w',compression=zipfile.ZIP_DEFLATED) as z:z.write(tmp,arcname=tmp.name)
    tmp.unlink(missing_ok=True)
def dotted(obj,path):
    cur=obj
    for part in path.split('.'):
        if not isinstance(cur,dict):return None
        cur=cur.get(part)
    return cur
def norm_party(x):return re.sub(r'\s+',' ',str(x or '').strip())
def read_results(path,s7,section_col):
    p=Path(path);txt=p.read_text(encoding='utf-8',errors='replace').lstrip()
    if txt.startswith(('{','[')):
        obj=json.loads(txt);zonas=dotted(obj,s7.get('json_rtve_zonas_path','mapa.zonas')) if isinstance(obj,dict) else None;rows=[]
        if isinstance(zonas,list):
            sf=s7.get('json_rtve_section_field','cod');lf=s7.get('json_rtve_party_list_field','lp');pf=s7.get('json_rtve_party_field','s');vf=s7.get('json_rtve_votes_field','v')
            for z in zonas:
                sec=z.get(sf)
                for item in z.get(lf,[]) or []:
                    try:v=int(float(item.get(vf,0)))
                    except Exception:continue
                    party=norm_party(item.get(pf))
                    if sec is not None and party:rows.append({section_col:str(sec),'party':party,'votes':v})
        if not rows:raise ValueError(f'No se pudieron extraer votos del JSON: {p}')
        return pd.DataFrame(rows)
    first=txt.splitlines()[0] if txt else '';sep=';' if first.count(';')>first.count(',') else ',';df=pd.read_csv(io.StringIO(txt),sep=sep,dtype=str);party_col=s7.get('party_col','PARTIDO');votes_col=s7.get('votes_col','VOTOS');sec_candidates=[section_col,'CUSEC_KEY','CUSEC','CESUC','SECCION'];sec_src=next((c for c in sec_candidates if c in df.columns),None)
    if not sec_src or party_col not in df.columns or votes_col not in df.columns:raise ValueError('CSV electoral no cumple contrato long section/party/votes')
    out=df[[sec_src,party_col,votes_col]].rename(columns={sec_src:section_col,party_col:'party',votes_col:'votes'});out[section_col]=out[section_col].astype(str);out['party']=out['party'].map(norm_party);out['votes']=pd.to_numeric(out['votes'],errors='coerce').fillna(0).astype('int64');return out
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--params',required=True);a=ap.parse_args();cfg=load_params_yaml(a.params);s7=module_cfg(cfg,'modulo_07_agregar_resultados_electorales','step7_elections');in_geo=require(s7.get('in_geojson'),'Falta M07 geometría');section=require(s7.get('section_id_field'),'Falta M07 section_id');district=require(s7.get('district_field'),'Falta M07 district_id');files=require(s7.get('results_files'),'Falta M07 resultados');out_party=require(s7.get('out_district_party_csv'),'Falta M07 salida partido');out_summary=require(s7.get('out_district_summary_csv'),'Falta M07 salida resumen');gdf=load_geo(in_geo);mapping=gdf[[section,district]].copy();mapping[section]=mapping[section].astype(str);mapping[district]=pd.to_numeric(mapping[district],errors='coerce').fillna(-1).astype('int64');frames=[read_results(f,s7,section) for f in files];res=pd.concat(frames,ignore_index=True);res[section]=res[section].astype(str);res['party']=res['party'].map(norm_party);res['votes']=pd.to_numeric(res['votes'],errors='coerce').fillna(0).astype('int64');sec_party=res.groupby([section,'party'],as_index=False)['votes'].sum();merged=sec_party.merge(mapping,on=section,how='inner');merged=merged[merged[district]>=0];dist_party=merged.groupby([district,'party'],as_index=False)['votes'].sum().rename(columns={district:'district_id'});blocs=s7.get('blocs',{}) or {};dist_party['bloc']=dist_party['party'].map(lambda p:blocs.get(p,''));totals=dist_party.groupby('district_id',as_index=False)['votes'].sum().rename(columns={'votes':'total_votes'});dp=dist_party.merge(totals,on='district_id');dp['vote_share']=dp['votes']/dp['total_votes'].replace({0:pd.NA});idx=dp.groupby('district_id')['votes'].idxmax();winners=dp.loc[idx,['district_id','party','votes','vote_share','bloc']].rename(columns={'party':'winner_party','votes':'winner_votes','vote_share':'winner_share','bloc':'winner_bloc'});summary=totals.merge(winners,on='district_id').sort_values('district_id');Path(out_party).parent.mkdir(parents=True,exist_ok=True);dist_party.sort_values(['district_id','votes'],ascending=[True,False]).to_csv(out_party,index=False);summary.to_csv(out_summary,index=False)
    out_enriched=s7.get('out_sections_enriched_geojson','')
    if out_enriched:
        sec_tot=sec_party.groupby(section,as_index=False)['votes'].sum().rename(columns={'votes':'section_total_votes'});sidx=sec_party.groupby(section)['votes'].idxmax();sec_win=sec_party.loc[sidx,[section,'party','votes']].rename(columns={'party':'section_winner_party','votes':'section_winner_votes'});gg=gdf.copy();gg[section]=gg[section].astype(str);write_geo(gg.merge(sec_tot,on=section,how='left').merge(sec_win,on=section,how='left'),out_enriched)
    print(f'[Módulo 7] OK districts={len(summary)} out_summary={out_summary}')
if __name__=='__main__':main()
