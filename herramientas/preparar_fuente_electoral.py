#!/usr/bin/env python3
from __future__ import annotations
import argparse,csv,hashlib,json,shutil
from datetime import datetime,timezone
from pathlib import Path
import yaml
from herramientas.comprobar_fuente_electoral_oficial import check_declaration,load_declaration

def sha(path:Path)->str:
    h=hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda:f.read(1024*1024),b""): h.update(chunk)
    return h.hexdigest()

def count_records(path:Path)->tuple[int,str]:
    try:
        if path.suffix.lower() in {".csv",".tsv",".txt"}:
            text=path.read_text(encoding="utf-8-sig",errors="strict")
            delim="\t" if path.suffix.lower()==".tsv" else ("," if text.splitlines() and text.splitlines()[0].count(",")>=text.splitlines()[0].count(";") else ";")
            rows=list(csv.reader(text.splitlines(),delimiter=delim))
            return max(0,len(rows)-1),"delimited_rows_excluding_header"
        if path.suffix.lower()==".json":
            obj=json.loads(path.read_text(encoding="utf-8"))
            if isinstance(obj,list): return len(obj),"json_top_level_list"
            cur=obj
            for key in ("mapa","zonas"):
                if isinstance(cur,dict) and key in cur: cur=cur[key]
            if isinstance(cur,list): return len(cur),"json_mapa_zonas"
            if isinstance(obj,dict) and isinstance(obj.get("features"),list): return len(obj["features"]),"geojson_features"
    except Exception:
        pass
    return 0,"not_countable"

def _read_delimited(path:Path)->tuple[list[str],list[dict]]:
    raw=path.read_bytes()
    text=None
    for encoding in ("utf-8-sig","utf-8","latin-1"):
        try:
            text=raw.decode(encoding); break
        except UnicodeDecodeError:
            continue
    if text is None: raise ValueError(f"No se puede decodificar {path}")
    lines=text.splitlines()
    if not lines: raise ValueError(f"Fuente vacía: {path}")
    delimiter=max((";",",","\t"),key=lambda d:lines[0].count(d))
    reader=csv.DictReader(lines,delimiter=delimiter)
    fields=[str(x or "").strip() for x in (reader.fieldnames or [])]
    if not fields: raise ValueError(f"CSV sin cabecera: {path}")
    rows=[]
    for row in reader:
        rows.append({fields[i]: row.get(reader.fieldnames[i],"") for i in range(len(fields))})
    return fields,rows

def merge_delimited_sources(paths:list[Path],out:Path)->dict:
    all_fields=[]; all_rows=[]
    for path in paths:
        fields,rows=_read_delimited(path)
        for field in fields:
            if field not in all_fields: all_fields.append(field)
        all_rows.extend(rows)
    if not all_rows: raise ValueError("Las fuentes electorales no contienen registros")
    out.parent.mkdir(parents=True,exist_ok=True)
    with out.open("w",encoding="utf-8",newline="") as f:
        writer=csv.DictWriter(f,fieldnames=all_fields,delimiter=";",extrasaction="ignore")
        writer.writeheader()
        for row in all_rows: writer.writerow({field:row.get(field,"") for field in all_fields})
    return {"records":len(all_rows),"columns":all_fields}

def _write_package(out:Path,decision:str,territory_id:str,edition:str,source:Path|None,meta:dict,extra:dict|None=None)->dict:
    if out.exists(): shutil.rmtree(out)
    out.mkdir(parents=True)
    selected=None
    if source is not None:
        data_dir=out/"data"; data_dir.mkdir()
        target=data_dir/source.name; shutil.copy2(source,target)
        records,method=count_records(target)
        selected={"path":target.relative_to(out).as_posix(),"sha256":sha(target),"bytes":target.stat().st_size,"records":records,"record_count_method":method,**meta}
    manifest={"schema":"ddd-electoral-package/1.0","decision":decision,"territory_id":territory_id,"edition":str(edition),"frozen_at":datetime.now(timezone.utc).isoformat(),"selected_source":selected}
    if extra: manifest.update(extra)
    (out/"manifest.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    (out/"decision.json").write_text(json.dumps({"decision":decision,"territory_id":territory_id,"edition":str(edition),"selected_source":selected},ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    return manifest

def validate_previous(package:Path,territory_id:str,edition:str)->dict|None:
    try:
        m=json.loads((package/"manifest.json").read_text(encoding="utf-8"))
        if m.get("schema")!="ddd-electoral-package/1.0" or m.get("decision") not in {"REUSE","ACQUIRE"}: return None
        if m.get("territory_id")!=territory_id or str(m.get("edition"))!=str(edition): return None
        s=m.get("selected_source") or {}; p=package/str(s.get("path") or "")
        if not p.is_file() or sha(p)!=str(s.get("sha256") or "") or p.stat().st_size!=int(s.get("bytes") or -1): return None
        records,_=count_records(p)
        if "records" in s and int(s.get("records") or 0)!=records: return None
        return m
    except Exception: return None

def prepare(*,territory_id:str,edition:str,package_out:Path,root:Path,params:Path|None=None,declaration:Path|None=None,previous:Path|None=None,previous_run_id:str|None=None,previous_artifact_name:str|None=None)->dict:
    root=root.resolve()
    if previous and previous.is_dir():
        m=validate_previous(previous,territory_id,edition)
        if m and previous_run_id and previous_artifact_name:
            source=previous/m["selected_source"]["path"]
            meta={k:v for k,v in m["selected_source"].items() if k not in {"path","sha256","bytes","records","record_count_method"}}
            return _write_package(package_out,"REUSE",territory_id,edition,source,meta,{
                "reuse_provenance":{
                    "run_id":str(previous_run_id),
                    "artifact_name":str(previous_artifact_name),
                }
            })
    cfg={}
    if params and params.is_file(): cfg=yaml.safe_load(params.read_text(encoding="utf-8")) or {}
    m07=(cfg.get("modulos") or {}).get("modulo_07_agregar_resultados_electorales") or {}
    contract_raw=m07.get("election_contract")
    if contract_raw:
        contract_path=root/str(contract_raw)
        if contract_path.is_file():
            contract=json.loads(contract_path.read_text(encoding="utf-8"))
            sources=contract.get("sources") or []
            if len(sources)==1:
                s=sources[0]; src=root/str(s.get("path") or "")
                expected=str(s.get("sha256") or "").lower()
                if src.is_file() and expected and sha(src).lower()==expected:
                    meta={"origin_url":s.get("source_url"),"publisher":s.get("publisher"),"acquired_at":s.get("retrieved_at"),"source_mode":"existing_contract","contract":str(contract_raw)}
                    return _write_package(package_out,"REUSE",territory_id,edition,src,meta)
    decl=declaration
    if decl is None:
        raw=(cfg.get("meta") or {}).get("electoral_sources_declaration")
        if raw: decl=root/str(raw)
    if decl and decl.is_file():
        tmp=package_out.parent/(package_out.name+"-acquire")
        if tmp.exists(): shutil.rmtree(tmp)
        d=load_declaration(decl); result=check_declaration(d,tmp)
        if result.get("decision")=="READY":
            selected_sources=result.get("selected_sources") or []
            election_extra={"checker_decision":result,"election_id":d.get("election_id"),"election_date":d.get("election_date")}
            if len(selected_sources)>1:
                source_paths=[tmp/str(sel["artifact_path"]) for sel in selected_sources]
                merged=tmp/"resultados_electorales_vigentes.csv"
                merge_info=merge_delimited_sources(source_paths,merged)
                provenance=[{
                    "id":sel.get("id"),"url":sel.get("url"),"publisher":sel.get("publisher"),
                    "sha256":sel.get("sha256"),"bytes":sel.get("bytes")
                } for sel in selected_sources]
                meta={
                    "publisher":"; ".join(sorted({str(sel.get("publisher") or "") for sel in selected_sources if sel.get("publisher")})),
                    "acquired_at":datetime.now(timezone.utc).isoformat(),
                    "source_mode":"official_acquisition_multisource",
                    "source_count":len(selected_sources),
                    "sources":provenance,
                    "merge":merge_info,
                    "declaration":str(decl),
                }
                manifest=_write_package(package_out,"ACQUIRE",territory_id,edition,merged,meta,election_extra)
                raw_dir=package_out/"raw"; raw_dir.mkdir(exist_ok=True)
                for sel,src in zip(selected_sources,source_paths):
                    raw_target=raw_dir/src.name
                    shutil.copy2(src,raw_target)
                manifest["raw_sources"]=[{
                    "id":sel.get("id"),
                    "path":f"raw/{(tmp/str(sel['artifact_path'])).name}",
                    "sha256":sel.get("sha256"),
                    "bytes":sel.get("bytes"),
                    "url":sel.get("url"),
                    "publisher":sel.get("publisher"),
                } for sel in selected_sources]
                (package_out/"manifest.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
                shutil.rmtree(tmp,ignore_errors=True); return manifest
            sel=result.get("selected_source") or (selected_sources[0] if selected_sources else None)
            if not sel:
                raise ValueError("READY sin fuente electoral seleccionada")
            src=tmp/str(sel["artifact_path"])
            meta={"origin_url":sel.get("url"),"publisher":sel.get("publisher"),"acquired_at":datetime.now(timezone.utc).isoformat(),"source_mode":"official_acquisition","declaration":str(decl)}
            manifest=_write_package(package_out,"ACQUIRE",territory_id,edition,src,meta,election_extra)
            shutil.rmtree(tmp,ignore_errors=True); return manifest
        manifest=_write_package(package_out,"BLOCK",territory_id,edition,None,{},{"reason":"No existe fuente electoral oficial reutilizable o adquirible","checker_decision":result})
        shutil.copytree(tmp,package_out/"checker",dirs_exist_ok=True)
        shutil.rmtree(tmp,ignore_errors=True)
        return manifest
    return _write_package(package_out,"BLOCK",territory_id,edition,None,{},{"reason":"Sin paquete reutilizable, contrato materializado ni declaración electoral oficial"})

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--territory-id",required=True); ap.add_argument("--edition",required=True)
    ap.add_argument("--package-out",type=Path,required=True); ap.add_argument("--root-dir",type=Path,default=Path("."))
    ap.add_argument("--params",type=Path); ap.add_argument("--declaration",type=Path); ap.add_argument("--previous-package",type=Path)
    ap.add_argument("--previous-run-id"); ap.add_argument("--previous-artifact-name")
    a=ap.parse_args()
    m=prepare(territory_id=a.territory_id,edition=a.edition,package_out=a.package_out,root=a.root_dir,params=a.params,declaration=a.declaration,previous=a.previous_package,previous_run_id=a.previous_run_id,previous_artifact_name=a.previous_artifact_name)
    print(json.dumps(m,ensure_ascii=False))
    if m["decision"]=="BLOCK": raise SystemExit(2)
if __name__=="__main__": main()
