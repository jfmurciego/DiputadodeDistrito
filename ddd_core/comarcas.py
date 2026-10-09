"""Unión declarativa de comunidades de interés por código municipal."""
from __future__ import annotations
import re
from pathlib import Path
import pandas as pd

def normalize_municipality_key(value):
    if value is None or (isinstance(value,float) and pd.isna(value)):return None
    digits=re.sub(r"\D+","",str(value).strip())
    return digits[:5].zfill(5) if digits else None

def _sniff_sep(sample):return "\t" if "\t" in sample and sample.count("\t")>=sample.count(",") else ","

def load_comarcas(cfg):
    raw=str(cfg.get("path") or "").strip()
    if not raw:raise ValueError("Falta io.input.comarcas.path")
    p=Path(raw).expanduser().resolve()
    if not p.exists():raise FileNotFoundError(f"Fuente comarcal no encontrada: {p}")
    with p.open("rb") as handle:sample=handle.read(4096).decode("utf-8",errors="replace")
    sep=cfg.get("sep","auto")
    source=pd.read_csv(p,sep=_sniff_sep(sample) if sep=="auto" else sep,dtype=str,encoding="utf-8-sig")
    join=cfg.get("join",{}) or {};key=join.get("comarcas_key_col","Municipio código");code=join.get("comarca_code_col","Comarca código");name=join.get("comarca_name_col","Comarca nombre")
    missing=[c for c in (key,code,name) if c not in source.columns]
    if missing:raise ValueError(f"Fuente comarcal sin columnas requeridas: {missing}")
    out=source[[key,code,name]].copy();out["MUN_KEY"]=out[key].map(normalize_municipality_key)
    if out["MUN_KEY"].isna().any():raise ValueError("Fuente comarcal contiene códigos municipales vacíos o inválidos")
    out=out.rename(columns={code:"COMARCA_CODIGO",name:"COMARCA_NOMBRE"})[["MUN_KEY","COMARCA_CODIGO","COMARCA_NOMBRE"]]
    for col in ("COMARCA_CODIGO","COMARCA_NOMBRE"):out[col]=out[col].astype(str).str.strip()
    conflicts=out.groupby("MUN_KEY")[["COMARCA_CODIGO","COMARCA_NOMBRE"]].nunique(dropna=False).max(axis=1);bad=sorted(conflicts[conflicts>1].index)
    if bad:raise ValueError(f"Fuente comarcal asigna varias comarcas al mismo municipio: {bad[:10]}")
    return out.drop_duplicates("MUN_KEY").reset_index(drop=True)

def attach_comarcas(frame, cfg):
    municipal=frame["CUSEC_KEY"].astype(str).str[:5]
    if not bool((cfg or {}).get("enabled",False)):
        return frame,{"enabled":False,"municipalities_total":int(municipal.nunique()),"municipalities_matched":0,"municipalities_missing":[],"coverage_ratio":None}
    out=frame.copy();out["MUN_KEY"]=municipal;out=out.merge(load_comarcas(cfg),on="MUN_KEY",how="left",validate="many_to_one")
    all_keys=sorted(out["MUN_KEY"].dropna().unique());matched=set(out.loc[out["COMARCA_CODIGO"].notna(),"MUN_KEY"]);missing=sorted(set(all_keys)-matched)
    if bool(cfg.get("require_full_coverage",True)) and missing:raise ValueError(f"Fuente comarcal sin cobertura para {len(missing)} municipios: {missing[:10]}")
    return out,{"enabled":True,"municipalities_total":len(all_keys),"municipalities_matched":len(matched),"municipalities_missing":missing,"coverage_ratio":len(matched)/len(all_keys) if all_keys else 1.0}
