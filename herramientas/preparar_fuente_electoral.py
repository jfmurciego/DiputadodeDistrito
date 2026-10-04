#!/usr/bin/env python3
from __future__ import annotations
import argparse,csv,hashlib,io,json,re,shutil,unicodedata
from datetime import datetime,timezone
from pathlib import Path
import sys
import yaml
from herramientas.comprobar_fuente_electoral_oficial import check_declaration,load_declaration

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from ddd_core.electoral_contract import (
    STRUCTURAL_PROVENANCE_SCHEMA,
    validate_structural_provenance_document,
)


def _clean_header(value: object) -> str:
    text=unicodedata.normalize("NFKD",str(value or "")).encode("ascii","ignore").decode("ascii").strip().lower()
    return re.sub(r"[^a-z0-9]+","_",text).strip("_")


def _as_int(value: object) -> int:
    if value in (None,""): return 0
    if isinstance(value,(int,float)): return int(value)
    raw=str(value).strip().replace(".","").replace(",","")
    return int(float(raw or 0))


def _normalise_code(value: object,width:int) -> str:
    if value in (None,""): return ""
    raw=str(value).strip()
    try:
        raw=str(int(float(raw)))
    except Exception:
        raw=re.sub(r"\D","",raw)
    return raw.zfill(width)


def _raw_code(value: object) -> str:
    if value in (None, ""):
        return ""
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value).strip()


def _load_special_crosswalk(root:Path, transform:dict)->list[dict]:
    raw=str(transform.get("special_row_crosswalk") or "").strip()
    if not raw:
        return []
    path=(root/raw).resolve()
    data=json.loads(path.read_text(encoding="utf-8"))
    if data.get("schema")!="ddd-election-special-row-crosswalk/1.0":
        raise ValueError(f"Crosswalk especial con schema inválido: {path}")
    rows=data.get("rows") or []
    if not rows:
        raise ValueError(f"Crosswalk especial vacío: {path}")
    return rows


def _largest_remainder(total:int, weights:list[tuple[str,float]])->dict[str,int]:
    if total < 0:
        raise ValueError("No se pueden repartir votos negativos")
    denom=sum(max(0.0,float(w)) for _,w in weights)
    if denom <= 0:
        raise ValueError("Pesos de reconciliación sin masa positiva")
    raw=[(key,total*max(0.0,float(w))/denom) for key,w in weights]
    base={key:int(value//1) for key,value in raw}
    remaining=total-sum(base.values())
    order=sorted(raw,key=lambda kv:(-(kv[1]-int(kv[1]//1)),kv[0]))
    for key,_ in order[:remaining]:
        base[key]+=1
    return base


def transform_gipeyop_polling_xlsx(source:Path,out_dir:Path,declaration:dict,source_decl:dict,root:Path)->dict:
    try:
        import openpyxl
    except Exception as exc:
        raise RuntimeError("La transformación XLSX electoral requiere openpyxl") from exc
    sheet_name=str((source_decl.get("transform") or {}).get("sheet") or "MESAS")
    wb=openpyxl.load_workbook(source,read_only=True,data_only=True)
    if sheet_name not in wb.sheetnames:
        raise ValueError(f"XLSX sin hoja {sheet_name!r}: {source}")
    ws=wb[sheet_name]
    rows=ws.iter_rows(values_only=True)
    try: headers_raw=next(rows)
    except StopIteration: raise ValueError("XLSX electoral vacío")
    headers=[_clean_header(x) for x in headers_raw]
    aliases={
        "year":{"year","anyo","ano"}, "province":{"cod_prov","codigo_provincia","provincia"},
        "municipality":{"cod_mun","codigo_municipio","municipio"}, "district":{"distrito","codigo_distrito"},
        "section":{"seccion","codigo_seccion"}, "polling":{"mesa","codigo_mesa"},
        "census":{"censo_total","censo","censo_ine"},
        "total_votes":{"votos","votos_totales"}, "blank":{"blancos","votos_blancos"}, "null":{"nulos","votos_nulos"},
    }
    positions={}
    for key,names in aliases.items():
        for idx,name in enumerate(headers):
            if name in names:
                positions[key]=idx; break
    required={"province","municipality","district","section","census","total_votes","blank","null"}
    missing=sorted(required-set(positions))
    if missing: raise ValueError(f"XLSX electoral sin columnas estructurales: {missing}; cabecera={headers}")
    party_start=max(positions["total_votes"],positions["blank"],positions["null"])+1
    party_headers=[]
    for idx in range(party_start,len(headers_raw)):
        raw=str(headers_raw[idx] or "").strip()
        if raw: party_headers.append((idx,raw))
    if not party_headers: raise ValueError("XLSX electoral sin columnas de candidaturas")
    transform=source_decl.get("transform") or {}
    expected_year=str(transform.get("election_year") or str(declaration.get("election_date") or "")[:4])
    special_crosswalk=_load_special_crosswalk(root,transform)
    special_pos=0
    aliases={str(x["from"]):str(x["to"]) for x in ((declaration.get("section_reconciliation") or {}).get("aliases") or [])}
    all_party_totals={}
    cera_party_totals={}
    out_dir.mkdir(parents=True,exist_ok=True)
    normalized=out_dir/"resultados_electorales_normalizados.csv"
    parties=set(); records=0; sections=set()
    with normalized.open("w",encoding="utf-8",newline="") as fh:
        writer=csv.DictWriter(fh,fieldnames=["CUSEC_KEY","party","votes"],delimiter=";")
        writer.writeheader()
        for values in rows:
            if not values: continue
            if "year" in positions and expected_year:
                y=str(values[positions["year"]] or "").strip()
                try: y=str(int(float(y)))
                except Exception: pass
                if y and y!=expected_year: continue
            prov=_normalise_code(values[positions["province"]],2)
            mun=_normalise_code(values[positions["municipality"]],3)
            dist=_normalise_code(values[positions["district"]],2)
            sec_raw=_raw_code(values[positions["section"]])
            sec=_normalise_code(values[positions["section"]],3)
            if not (prov and mun and dist and sec_raw): continue

            row_party_votes={}
            for idx,party in party_headers:
                votes=_as_int(values[idx] if idx < len(values) else 0)
                row_party_votes[party]=votes
                all_party_totals[party]=all_party_totals.get(party,0)+votes

            # CERA se verifica contra el escrutinio oficial pero no se geocodifica.
            if mun in {"991","992","993","999"}:
                for party,votes in row_party_votes.items():
                    cera_party_totals[party]=cera_party_totals.get(party,0)+votes
                continue

            special_section=(not re.fullmatch(r"\d+",sec_raw) or int(sec_raw)<=0)
            if special_section:
                if not special_crosswalk:
                    raise ValueError(f"Registro especial sin crosswalk gobernado: {prov}/{mun}/{dist}/{sec_raw}")
                if special_pos >= len(special_crosswalk):
                    raise ValueError("Hay más registros especiales que filas declaradas en el crosswalk")
                expected=special_crosswalk[special_pos]
                special_pos+=1
                if str(expected.get("special_code")) != sec_raw:
                    raise ValueError(
                        f"Crosswalk especial fuera de secuencia ordinal={special_pos}: "
                        f"esperado={expected.get('special_code')} observado={sec_raw}"
                    )
                census_value=_as_int(values[positions["census"]])
                if census_value != int(expected.get("expected_autonomic_census") or -1):
                    raise ValueError(
                        f"Crosswalk especial no reproduce censo ordinal={special_pos}: "
                        f"esperado={expected.get('expected_autonomic_census')} observado={census_value}"
                    )
                cusec=str(expected["target_cusec"])
                evidence=(json.loads((root/str(transform.get("special_row_crosswalk"))).read_text(encoding="utf-8")).get("evidence") or {})
                source_identity=evidence.get("source_identity") or {}
                if (
                    str(source_identity.get("province") or "") != prov
                    or str(source_identity.get("municipality") or "") != mun
                    or str(source_identity.get("district") or "") != dist
                ):
                    raise ValueError(
                        f"Crosswalk especial no reproduce identidad de la fila fuente ordinal={special_pos}: "
                        f"observado={prov}/{mun}/{dist}/{sec_raw} esperado="
                        f"{source_identity.get('province')}/{source_identity.get('municipality')}/{source_identity.get('district')}"
                    )
                target_district=cusec[5:7] if len(cusec)==10 else ""
                allowed_target_districts={str(x) for x in (evidence.get("target_districts") or [])}
                if (
                    len(cusec) != 10
                    or cusec[:2] != prov
                    or cusec[2:5] != mun
                    or target_district not in allowed_target_districts
                ):
                    raise ValueError(
                        f"Crosswalk especial no reproduce identidad territorial de destino ordinal={special_pos}: "
                        f"fuente={prov}/{mun}/{dist}/{sec_raw} destino={cusec}"
                    )
            else:
                cusec=f"{prov}{mun}{dist}{sec}"

            cusec=aliases.get(cusec,cusec)
            sections.add(cusec)
            for party,votes in row_party_votes.items():
                parties.add(party)
                writer.writerow({"CUSEC_KEY":cusec,"party":party,"votes":votes})
                records+=1
    wb.close()
    if special_crosswalk and special_pos != len(special_crosswalk):
        raise ValueError(f"Crosswalk especial incompleto: usados={special_pos} declarados={len(special_crosswalk)}")
    verification=declaration.get("verification") or {}
    official={str(k):int(v) for k,v in (verification.get("official_party_totals") or {}).items()}
    if official:
        observed={str(k):int(all_party_totals.get(k,0)) for k in official}
        delta={k:observed[k]-official[k] for k in official}
        extras={k:v for k,v in all_party_totals.items() if k not in official and int(v)!=0}
        if any(delta.values()) or extras:
            raise ValueError(
                "Mirror electoral no coincide con totales oficiales por candidatura: "
                f"delta={delta}; extras={extras}"
            )
    official_total=int(verification.get("official_candidate_votes") or sum(official.values()) or sum(all_party_totals.values()))
    cera_total=sum(cera_party_totals.values())
    expected_cera=verification.get("expected_cera_candidate_votes")
    if expected_cera is not None and cera_total != int(expected_cera):
        raise ValueError(
            f"CERA no coincide con total esperado: observado={cera_total} esperado={int(expected_cera)}"
        )
    excluded_pct=(100.0*cera_total/official_total) if official_total else 0.0
    if not records or not sections: raise ValueError("La transformación electoral no produjo registros censales")
    dictionary=out_dir/"party_dictionary.json"
    dictionary_payload={
        "schema_family":"ddd-party-dictionary","schema_version":"1.0.0","unknown_party_policy":"reject",
        "parties":[{"canonical_id":p,"display_name":p,"aliases":[],"classification":""} for p in sorted(parties)],
    }
    dictionary.write_text(json.dumps(dictionary_payload,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    contract=out_dir/"election_contract.json"
    contract_payload={
        "schema_family":"ddd-election","schema_version":"1.0.0",
        "election_id":str(declaration["election_id"]),"territory_id":str(declaration["territory_id"]),
        "title":str(declaration.get("title") or declaration["election_id"]),
        "election_date":str(declaration["election_date"]),"input_mode":"verifiable_file","boundary_independence":True,
        "sources":[{
            "path":normalized.as_posix(),"sha256":sha(normalized),
            "publisher":str(source_decl.get("publisher") or ""),"source_url":str(source_decl.get("url") or ""),
            "retrieved_at":datetime.now(timezone.utc).date().isoformat(),
            "adapter":{"kind":"long_csv","separator":";","section_field":"CUSEC_KEY","party_field":"party","votes_field":"votes"},
        }],
        "party_dictionary":{"path":dictionary.as_posix(),"sha256":sha(dictionary)},
        "reconciliation":declaration.get("reconciliation") or {"policy":"fail_unless_declared","allowed_result_only_sections":[],"allowed_map_only_sections":[]},
        "section_reconciliation":declaration.get("section_reconciliation") or {},
        "source_verification":{
            "status":"VERIFIED_EXACT" if official else "NOT_CONFIGURED",
            "official_candidate_votes":official_total,
            "observed_candidate_votes":sum(all_party_totals.values()),
            "party_totals_match":bool(official),
        },
        "non_geocodable_votes":{
            "policy":"exclude_from_geographic_district_allocation",
            "kind":"CERA",
            "candidate_votes":cera_total,
            "official_candidate_votes":official_total,
            "percentage_of_candidate_votes":excluded_pct,
            "party_totals":cera_party_totals,
        },
    }
    contract.write_text(json.dumps(contract_payload,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    return {
        "source":normalized,"contract":contract,"dictionary":dictionary,
        "records":records,"sections":len(sections),"parties":len(parties),
        "source_verification_status":"VERIFIED_EXACT" if official else "NOT_CONFIGURED",
        "official_candidate_votes":official_total,
        "cera_candidate_votes":cera_total,
        "cera_percentage":excluded_pct,
        "special_rows_reconciled":special_pos,
    }


def transform_gencat_polling_csv(source:Path,out_dir:Path,declaration:dict,source_decl:dict,root:Path)->dict:
    fields,rows=_read_delimited(source)
    required={"Nivell","Codi circumscripció","Codi municipi","Districte","Secció","Mesa","Votants","Vots a candidatures"}
    missing=sorted(required-set(fields))
    if missing: raise ValueError(f"CSV Generalitat sin columnas estructurales: {missing}")
    excluded={"Vots nuls","Vots en blanc","Vots a candidatures","Vots vàlids"}
    party_fields=[f for f in fields if f.startswith("Vots ") and f not in excluded]
    if not party_fields: raise ValueError("CSV Generalitat sin columnas de candidaturas")
    geo_sections=set(); geo_polling=set(); aggregates={}
    all_party_totals={p.replace("Vots ","",1).strip():0 for p in party_fields}
    cera_party_totals={p.replace("Vots ","",1).strip():0 for p in party_fields}
    total_candidate_votes=0; total_voters=0; geo_mesa_rows=0; cera_rows=0; cera_candidate_votes=0
    for row in rows:
        if str(row.get("Nivell") or "").strip()!="ME": continue
        prov=_normalise_code(row.get("Codi circumscripció"),2); mun=_normalise_code(row.get("Codi municipi"),3)
        dist=_normalise_code(row.get("Districte"),2); sec=_normalise_code(row.get("Secció"),3); mesa=str(row.get("Mesa") or "").strip()
        if not (prov and mun and dist and sec and mesa): raise ValueError(f"Mesa no identificable en CSV Generalitat: {row}")
        row_candidate=_as_int(row.get("Vots a candidatures")); row_party=0; party_values={}
        for field in party_fields:
            party=field.replace("Vots ","",1).strip(); n=_as_int(row.get(field))
            if n<0: raise ValueError("Votos negativos en CSV Generalitat")
            party_values[party]=n; all_party_totals[party]=all_party_totals.get(party,0)+n; row_party+=n
        if row_party!=row_candidate: raise ValueError(f"Votos por candidatura no cuadran en mesa {prov}/{mun}/{dist}/{sec}-{mesa}: partidos={row_party} candidaturas={row_candidate}")
        total_candidate_votes+=row_candidate; total_voters+=_as_int(row.get("Votants"))
        if mun=="998":
            cera_rows+=1; cera_candidate_votes+=row_candidate
            for party,n in party_values.items(): cera_party_totals[party]=cera_party_totals.get(party,0)+n
            continue
        cusec=prov+mun+dist+sec
        if len(cusec)!=10: raise ValueError(f"CUSEC inválido en CSV Generalitat: {cusec}")
        geo_sections.add(cusec); geo_polling.add(cusec+"-"+mesa); geo_mesa_rows+=1
        for party,n in party_values.items(): aggregates[(cusec,party)]=aggregates.get((cusec,party),0)+n
    if not geo_mesa_rows or not geo_sections or not total_candidate_votes: raise ValueError("CSV Generalitat no produjo mesas/secciones/votos")
    verification=declaration.get("verification") or {}
    checks={
        "official_candidate_votes":total_candidate_votes==int(verification.get("official_candidate_votes") or total_candidate_votes),
        "official_voters":total_voters==int(verification.get("official_voters") or total_voters),
        "expected_polling_stations":geo_mesa_rows==int(verification.get("expected_polling_stations") or geo_mesa_rows),
        "expected_sections":len(geo_sections)==int(verification.get("expected_sections") or len(geo_sections)),
        "expected_cera_rows":cera_rows==int(verification.get("expected_cera_rows") or cera_rows),
        "expected_cera_candidate_votes":cera_candidate_votes==int(verification.get("expected_cera_candidate_votes") or cera_candidate_votes),
    }
    official_party={str(k):int(v) for k,v in (verification.get("official_party_totals") or {}).items()}
    if official_party:
        checks["official_party_totals"]=all(all_party_totals.get(k,0)==v for k,v in official_party.items()) and not any(v for k,v in all_party_totals.items() if k not in official_party)
    if not all(checks.values()): raise ValueError(f"CSV Generalitat no reconcilia con controles oficiales: {checks}; votos={total_candidate_votes}; votantes={total_voters}; mesas_geo={geo_mesa_rows}; secciones_geo={len(geo_sections)}; cera_rows={cera_rows}; cera_votos={cera_candidate_votes}")
    out_dir.mkdir(parents=True,exist_ok=True); normalized=out_dir/"resultados_electorales_normalizados.csv"
    with normalized.open("w",encoding="utf-8",newline="") as fh:
        writer=csv.DictWriter(fh,fieldnames=["CUSEC_KEY","party","votes"],delimiter=";"); writer.writeheader()
        for (cusec,party),votes in sorted(aggregates.items()): writer.writerow({"CUSEC_KEY":cusec,"party":party,"votes":votes})
    dictionary=out_dir/"party_dictionary.json"
    dictionary.write_text(json.dumps({"schema_family":"ddd-party-dictionary","schema_version":"1.0.0","unknown_party_policy":"reject","parties":[{"canonical_id":p,"display_name":p,"aliases":[],"classification":""} for p in sorted(all_party_totals)]},ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    geographic_candidate_votes=sum(aggregates.values())
    if geographic_candidate_votes!=total_candidate_votes-cera_candidate_votes: raise ValueError(f"Descuadre geográfico/CERA: geo={geographic_candidate_votes} total={total_candidate_votes} cera={cera_candidate_votes}")
    contract=out_dir/"election_contract.json"
    contract_payload={
        "schema_family":"ddd-election","schema_version":"1.0.0","election_id":str(declaration["election_id"]),"territory_id":str(declaration["territory_id"]),"title":str(declaration.get("title") or declaration["election_id"]),"election_date":str(declaration["election_date"]),"input_mode":"verifiable_file","boundary_independence":True,
        "sources":[{"path":normalized.as_posix(),"sha256":sha(normalized),"publisher":str(source_decl.get("publisher") or ""),"source_url":str(source_decl.get("url") or ""),"retrieved_at":datetime.now(timezone.utc).date().isoformat(),"adapter":{"kind":"long_csv","separator":";","section_field":"CUSEC_KEY","party_field":"party","votes_field":"votes"}}],
        "party_dictionary":{"path":dictionary.as_posix(),"sha256":sha(dictionary)},"reconciliation":declaration.get("reconciliation") or {"policy":"fail_unless_declared","allowed_result_only_sections":[],"allowed_map_only_sections":[]},
        "source_verification":{"status":"VERIFIED_EXACT","official_candidate_votes":int(verification.get("official_candidate_votes") or total_candidate_votes),"observed_candidate_votes":total_candidate_votes,"official_voters":int(verification.get("official_voters") or total_voters),"observed_voters":total_voters,"geographic_polling_stations":geo_mesa_rows,"geographic_sections":len(geo_sections),"party_totals_match":checks.get("official_party_totals",True)},
        "non_geocodable_votes":{"policy":"exclude_from_geographic_district_allocation","kind":"CERA","rows":cera_rows,"candidate_votes":cera_candidate_votes,"party_totals":cera_party_totals},
    }
    contract.write_text(json.dumps(contract_payload,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    return {"source":normalized,"contract":contract,"dictionary":dictionary,"records":len(aggregates),"sections":len(geo_sections),"parties":len(all_party_totals),"source_verification_status":"VERIFIED_EXACT","official_candidate_votes":total_candidate_votes,"geographic_candidate_votes":geographic_candidate_votes,"cera_candidate_votes":cera_candidate_votes,"cera_percentage":(100.0*cera_candidate_votes/total_candidate_votes) if total_candidate_votes else 0.0,"special_rows_reconciled":cera_rows,"polling_stations":geo_mesa_rows,"voters":total_voters}

def _transform_selected_source(src:Path,tmp:Path,declaration:dict,source_decl:dict,root:Path)->dict|None:
    transform=source_decl.get("transform") or {}
    kind=str(transform.get("kind") or "")
    if not kind: return None
    if kind=="gipeyop_polling_xlsx":
        return transform_gipeyop_polling_xlsx(src,tmp/"normalized",declaration,source_decl,root)
    if kind=="gencat_polling_csv":
        return transform_gencat_polling_csv(src,tmp/"normalized",declaration,source_decl,root)
    raise ValueError(f"Transformación electoral no soportada: {kind}")

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
    if text is None:
        raise ValueError(f"No se puede decodificar {path}")
    first_line=text.splitlines()[0] if text.splitlines() else ""
    if not first_line:
        raise ValueError(f"Fuente vacía: {path}")
    delimiter=max((";",",","\t"),key=lambda d:first_line.count(d))
    try:
        records=list(
            csv.reader(
                io.StringIO(text),
                delimiter=delimiter,
                strict=True,
            )
        )
    except csv.Error as exc:
        raise ValueError(f"CSV malformado: {path}: {exc}") from exc
    if not records or not records[0]:
        raise ValueError(f"CSV sin cabecera: {path}")
    fields=[str(value or "").strip() for value in records[0]]
    if (
        any(not field for field in fields)
        or len(set(fields))!=len(fields)
    ):
        raise ValueError(f"CSV con cabecera vacía o duplicada: {path}")
    rows=[]
    for index,record in enumerate(records[1:],start=2):
        if len(record)!=len(fields):
            raise ValueError(
                f"CSV con anchura inválida: {path} row={index} "
                f"esperadas={len(fields)} observadas={len(record)}"
            )
        rows.append(dict(zip(fields,record,strict=True)))
    if not rows:
        raise ValueError(f"Fuente sin registros: {path}")
    return fields,rows


def merge_delimited_sources(
    paths:list[Path],
    out:Path,
    *,
    source_ids:list[str]|None=None,
)->dict:
    if not paths:
        raise ValueError("No hay fuentes electorales para fusionar")
    if source_ids is not None and len(source_ids)!=len(paths):
        raise ValueError("source_ids no coincide con las fuentes a fusionar")
    all_fields=[]; all_rows=[]; provenance_sources=[]; cursor=0
    for index,path in enumerate(paths):
        fields,rows=_read_delimited(path)
        if source_ids is not None:
            raw_source_id=source_ids[index]
            if not isinstance(raw_source_id,str) or not raw_source_id.strip():
                raise ValueError(
                    "source_id debe ser texto no vacío "
                    "en procedencia estructural"
                )
            source_id=raw_source_id.strip()
        else:
            source_id=path.name
        for field in fields:
            if field not in all_fields:
                all_fields.append(field)
        start=cursor
        cursor+=len(rows)
        provenance_sources.append({
            "source_id":source_id,
            "raw_file":path.name,
            "raw_sha256":sha(path),
            "records":len(rows),
            "merged_row_index_start":start,
            "merged_row_index_end_exclusive":cursor,
            "original_columns":fields,
        })
        all_rows.extend(rows)
    if len({row["source_id"] for row in provenance_sources})!=len(provenance_sources):
        raise ValueError("source_id duplicado en procedencia estructural")
    out.parent.mkdir(parents=True,exist_ok=True)
    with out.open("w",encoding="utf-8",newline="") as f:
        writer=csv.DictWriter(
            f,
            fieldnames=all_fields,
            delimiter=";",
            extrasaction="ignore",
        )
        writer.writeheader()
        for row in all_rows:
            writer.writerow({field:row.get(field,"") for field in all_fields})
    sidecar=out.with_name(out.name+".structural_provenance.json")
    provenance={
        "schema":STRUCTURAL_PROVENANCE_SCHEMA,
        "merged_source":{
            "sha256":sha(out),
            "records":len(all_rows),
            "columns":all_fields,
        },
        "sources":provenance_sources,
    }
    validate_structural_provenance_document(
        provenance,
        context="procedencia estructural generada",
        expected_source_sha256=sha(out),
    )
    sidecar.write_text(
        json.dumps(
            provenance,
            ensure_ascii=False,
            sort_keys=True,
            indent=2,
        )+"\n",
        encoding="utf-8",
    )
    return {
        "records":len(all_rows),
        "columns":all_fields,
        "structural_provenance_path":str(sidecar),
        "structural_provenance_sha256":sha(sidecar),
        "structural_provenance_schema":STRUCTURAL_PROVENANCE_SCHEMA,
    }


def _load_structural_provenance(
    path:Path,
    *,
    expected_sha256:str,
    expected_source_sha256:str,
    context:str,
)->dict:
    expected=str(expected_sha256 or "").lower()
    if (
        not path.is_file()
        or not re.fullmatch(r"[0-9a-f]{64}",expected)
        or sha(path).lower()!=expected
    ):
        raise ValueError(f"{context}: sidecar ausente o con SHA inválido")
    document=json.loads(path.read_text(encoding="utf-8"))
    validate_structural_provenance_document(
        document,
        context=context,
        expected_source_sha256=expected_source_sha256,
    )
    return document


def _copy_raw_sources(
    *,
    package_out:Path,
    selected_sources:list[dict],
    source_paths:list[Path],
)->list[dict]:
    if len(selected_sources)!=len(source_paths):
        raise ValueError("raw_sources no coincide con selected_sources")
    raw_dir=package_out/"raw"
    raw_dir.mkdir(parents=True,exist_ok=True)
    result=[]
    seen_ids=set()
    for index,(selected,source) in enumerate(
        zip(selected_sources,source_paths,strict=True)
    ):
        raw_source_id=selected.get("id")
        if (
            not isinstance(raw_source_id,str)
            or not raw_source_id.strip()
        ):
            raise ValueError(
                "raw_sources contiene source.id no textual o vacío"
            )
        source_id=raw_source_id.strip()
        if source_id in seen_ids:
            raise ValueError("raw_sources contiene source.id duplicado")
        seen_ids.add(source_id)
        declared_sha=str(selected.get("sha256") or "").lower()
        actual_sha=sha(source).lower()
        if not declared_sha or declared_sha!=actual_sha:
            raise ValueError(
                f"raw source {source_id}: SHA no coincide con adquisición"
            )
        declared_bytes=selected.get("bytes")
        if declared_bytes is not None and (
            not isinstance(declared_bytes,int)
            or isinstance(declared_bytes,bool)
            or declared_bytes<0
            or source.stat().st_size!=declared_bytes
        ):
            raise ValueError(
                f"raw source {source_id}: bytes no coinciden con adquisición"
            )
        target=raw_dir/f"{index:03d}_{source.name}"
        shutil.copy2(source,target)
        result.append({
            "id":source_id,
            "path":target.relative_to(package_out).as_posix(),
            "original_name":source.name,
            "sha256":actual_sha,
            "bytes":target.stat().st_size,
            "url":selected.get("url"),
            "publisher":selected.get("publisher"),
        })
    return result


def _validate_raw_sources_against_structural(
    *,
    package:Path,
    raw_sources:list[dict],
    document:dict,
    context:str,
    required:bool=True,
)->None:
    if not isinstance(raw_sources,list):
        raise ValueError(f"{context}: raw_sources inválido")
    if not raw_sources:
        if required:
            raise ValueError(f"{context}: raw_sources ausentes")
        return
    structural_sources=document.get("sources") or []
    if len(raw_sources)!=len(structural_sources):
        raise ValueError(f"{context}: raw_sources no coincide con sidecar")
    for index,(raw,structural) in enumerate(
        zip(raw_sources,structural_sources,strict=True)
    ):
        raw_context=f"{context}.raw_sources[{index}]"
        if not isinstance(raw,dict):
            raise ValueError(f"{raw_context} inválido")
        raw_id=str(raw.get("id") or "").strip()
        if raw_id!=str(structural.get("source_id") or "").strip():
            raise ValueError(f"{raw_context}: source_id no coincide")
        if (
            str(raw.get("original_name") or "")
            != str(structural.get("raw_file") or "")
        ):
            raise ValueError(f"{raw_context}: nombre raw no coincide")
        raw_path=package/str(raw.get("path") or "")
        expected_sha=str(raw.get("sha256") or "").lower()
        if (
            not raw_path.is_file()
            or not re.fullmatch(r"[0-9a-f]{64}",expected_sha)
            or sha(raw_path).lower()!=expected_sha
            or expected_sha!=str(structural.get("raw_sha256") or "").lower()
        ):
            raise ValueError(f"{raw_context}: raw no acredita el sidecar")
        declared_bytes=raw.get("bytes")
        if (
            not isinstance(declared_bytes,int)
            or isinstance(declared_bytes,bool)
            or declared_bytes<0
            or raw_path.stat().st_size!=declared_bytes
        ):
            raise ValueError(f"{raw_context}: bytes no coinciden")
        fields,rows=_read_delimited(raw_path)
        if fields!=list(structural.get("original_columns") or []):
            raise ValueError(
                f"{raw_context}: cabecera raw no coincide con sidecar"
            )
        if len(rows)!=int(structural.get("records") or -1):
            raise ValueError(
                f"{raw_context}: número de registros no coincide con sidecar"
            )


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

def _expected_election_identity(root:Path,cfg:dict,declaration:Path|None)->tuple[str|None,str|None]:
    decl=declaration
    if decl is None:
        raw=(cfg.get("meta") or {}).get("electoral_sources_declaration")
        if raw:
            decl=root/str(raw)
    if decl and decl.is_file():
        data=load_declaration(decl)
        return (
            str(data.get("election_id") or "") or None,
            str(data.get("election_date") or "") or None,
        )
    m07=(cfg.get("modulos") or {}).get("modulo_07_agregar_resultados_electorales") or {}
    contract_raw=m07.get("election_contract")
    if contract_raw:
        contract_path=root/str(contract_raw)
        if contract_path.is_file():
            data=json.loads(contract_path.read_text(encoding="utf-8"))
            return (
                str(data.get("election_id") or "") or None,
                str(data.get("election_date") or "") or None,
            )
    return None,None


def _materialize_embedded_contract(*,root:Path,package_out:Path,source_contract:Path,manifest:dict)->dict|None:
    contract=json.loads(source_contract.read_text(encoding="utf-8"))
    sources=contract.get("sources") or []
    if len(sources)!=1:
        raise ValueError("Contrato electoral materializado sin fuente única")
    selected=manifest.get("selected_source") or {}
    selected_sha=str(selected.get("sha256") or "").lower()
    if not selected_sha or str(sources[0].get("sha256") or "").lower()!=selected_sha:
        raise ValueError("Contrato electoral embebido no coincide con la fuente seleccionada")

    dictionary_decl=contract.get("party_dictionary") or {}
    dictionary_raw=str(dictionary_decl.get("path") or "")
    if not dictionary_raw:
        return None
    dictionary_expected=str(dictionary_decl.get("sha256") or "").lower()
    dictionary_src=(root/dictionary_raw).resolve()
    if not dictionary_src.is_file():
        raise ValueError("Contrato electoral materializado perdió su diccionario de partidos")
    if not dictionary_expected or sha(dictionary_src).lower()!=dictionary_expected:
        raise ValueError("SHA-256 del diccionario de partidos no coincide con el contrato")

    contract_dir=package_out/"contract"; contract_dir.mkdir(exist_ok=True)
    contract_target=contract_dir/"election_contract.json"
    dictionary_target=contract_dir/"party_dictionary.json"
    shutil.copy2(dictionary_src,dictionary_target)

    structural_info=None
    adapter=dict((sources[0].get("adapter") or {}))
    structural_decl=adapter.get("structural_provenance")
    if structural_decl:
        structural_raw=str(structural_decl.get("path") or "").strip()
        structural_expected=str(
            structural_decl.get("sha256") or ""
        ).lower()
        structural_src=(root/structural_raw).resolve()
        structural_doc=_load_structural_provenance(
            structural_src,
            expected_sha256=structural_expected,
            expected_source_sha256=selected_sha,
            context="procedencia estructural del contrato materializado",
        )
        evidence_dir=package_out/"evidence"; evidence_dir.mkdir(exist_ok=True)
        structural_target=evidence_dir/"structural_provenance.json"
        shutil.copy2(structural_src,structural_target)
        structural_info={
            "schema":STRUCTURAL_PROVENANCE_SCHEMA,
            "path":"evidence/structural_provenance.json",
            "sha256":sha(structural_target),
            "merged_source_sha256":selected_sha,
            "raw_sources_embedded":bool(
                manifest.get("raw_sources")
            ),
        }
        adapter["structural_provenance"]={
            "path":"evidence/structural_provenance.json",
            "sha256":structural_info["sha256"],
        }
        contract["sources"][0]["adapter"]=adapter
        manifest["structural_provenance"]=structural_info
        raw_sources=manifest.get("raw_sources") or []
        if raw_sources:
            _validate_raw_sources_against_structural(
                package=package_out,
                raw_sources=raw_sources,
                document=structural_doc,
                context="contrato materializado",
                required=False,
            )

    contract["sources"][0]["path"]=str(selected["path"])
    contract["party_dictionary"]["path"]="contract/party_dictionary.json"
    contract["party_dictionary"]["sha256"]=sha(dictionary_target)
    contract_target.write_text(
        json.dumps(contract,ensure_ascii=False,indent=2)+"\n",
        encoding="utf-8",
    )

    embedded={
        "election_contract":"contract/election_contract.json",
        "party_dictionary":"contract/party_dictionary.json",
        "contract_sha256":sha(contract_target),
        "party_dictionary_sha256":sha(dictionary_target),
    }
    if structural_info:
        embedded["structural_provenance"]="evidence/structural_provenance.json"
        embedded["structural_provenance_sha256"]=structural_info["sha256"]
    return embedded


def validate_previous(package:Path,territory_id:str,edition:str,expected_election_id:str|None=None,expected_election_date:str|None=None)->dict|None:
    try:
        m=json.loads((package/"manifest.json").read_text(encoding="utf-8"))
        if m.get("schema")!="ddd-electoral-package/1.0" or m.get("decision") not in {"REUSE","ACQUIRE"}: return None
        if m.get("territory_id")!=territory_id or str(m.get("edition"))!=str(edition): return None
        if expected_election_id is not None and str(m.get("election_id") or "")!=str(expected_election_id): return None
        if expected_election_date is not None and str(m.get("election_date") or "")!=str(expected_election_date): return None
        s=m.get("selected_source") or {}; p=package/str(s.get("path") or "")
        if not p.is_file() or sha(p)!=str(s.get("sha256") or "") or p.stat().st_size!=int(s.get("bytes") or -1): return None
        records,_=count_records(p)
        if "records" in s and int(s.get("records") or 0)!=records: return None

        structural=m.get("structural_provenance")
        if structural is not None:
            if not isinstance(structural,dict): return None
            sidecar=package/str(structural.get("path") or "")
            document=_load_structural_provenance(
                sidecar,
                expected_sha256=str(structural.get("sha256") or ""),
                expected_source_sha256=str(s.get("sha256") or ""),
                context="paquete electoral reutilizable",
            )
            if (
                str(structural.get("merged_source_sha256") or "").lower()
                != str(s.get("sha256") or "").lower()
            ):
                return None
            raw_required=structural.get("raw_sources_embedded")
            if not isinstance(raw_required,bool):
                return None
            if structural.get("schema")!=STRUCTURAL_PROVENANCE_SCHEMA:
                return None
            _validate_raw_sources_against_structural(
                package=package,
                raw_sources=m.get("raw_sources") or [],
                document=document,
                context="paquete electoral reutilizable",
                required=raw_required,
            )
        return m
    except Exception: return None

def prepare(*,territory_id:str,edition:str,package_out:Path,root:Path,params:Path|None=None,declaration:Path|None=None,previous:Path|None=None,previous_run_id:str|None=None,previous_artifact_name:str|None=None)->dict:
    root=root.resolve()
    cfg={}
    if params and params.is_file(): cfg=yaml.safe_load(params.read_text(encoding="utf-8")) or {}
    expected_election_id,expected_election_date=_expected_election_identity(root,cfg,declaration)
    if previous and previous.is_dir():
        m=validate_previous(
            previous,territory_id,edition,
            expected_election_id=expected_election_id,
            expected_election_date=expected_election_date,
        )
        if m and previous_run_id and previous_artifact_name:
            source=previous/m["selected_source"]["path"]
            meta={k:v for k,v in m["selected_source"].items() if k not in {"path","sha256","bytes","records","record_count_method"}}
            manifest=_write_package(package_out,"REUSE",territory_id,edition,source,meta,{
                "reuse_provenance":{
                    "run_id":str(previous_run_id),
                    "artifact_name":str(previous_artifact_name),
                },
                "election_id":m.get("election_id"),
                "election_date":m.get("election_date"),
            })
            raw_sources=m.get("raw_sources") or []
            if raw_sources:
                copied_raw=[]
                for index,raw in enumerate(raw_sources):
                    raw_src=previous/str(raw.get("path") or "")
                    expected_raw_sha=str(raw.get("sha256") or "").lower()
                    if (
                        not raw_src.is_file()
                        or sha(raw_src).lower()!=expected_raw_sha
                    ):
                        raise ValueError(
                            "Paquete electoral reutilizable perdió un raw"
                        )
                    raw_dir=package_out/"raw"; raw_dir.mkdir(exist_ok=True)
                    raw_target=raw_dir/f"{index:03d}_{raw_src.name}"
                    shutil.copy2(raw_src,raw_target)
                    copied_raw.append({
                        **raw,
                        "path":raw_target.relative_to(package_out).as_posix(),
                        "sha256":sha(raw_target),
                        "bytes":raw_target.stat().st_size,
                    })
                manifest["raw_sources"]=copied_raw

            structural=m.get("structural_provenance")
            if structural is not None:
                structural_src=previous/str(structural.get("path") or "")
                structural_doc=_load_structural_provenance(
                    structural_src,
                    expected_sha256=str(structural.get("sha256") or ""),
                    expected_source_sha256=str(
                        (m.get("selected_source") or {}).get("sha256") or ""
                    ),
                    context="paquete electoral reutilizable",
                )
                evidence_dir=package_out/"evidence"; evidence_dir.mkdir(exist_ok=True)
                structural_target=evidence_dir/"structural_provenance.json"
                shutil.copy2(structural_src,structural_target)
                manifest["structural_provenance"]={
                    **structural,
                    "path":"evidence/structural_provenance.json",
                    "sha256":sha(structural_target),
                }
                _validate_raw_sources_against_structural(
                    package=package_out,
                    raw_sources=manifest.get("raw_sources") or [],
                    document=structural_doc,
                    context="paquete electoral reutilizado",
                    required=(
                        structural.get("raw_sources_embedded") is True
                    ),
                )

            embedded=m.get("embedded_contract") or {}
            if embedded:
                contract_src=previous/str(embedded.get("election_contract") or "")
                dictionary_src=previous/str(embedded.get("party_dictionary") or "")
                if not contract_src.is_file() or not dictionary_src.is_file():
                    raise ValueError("Paquete electoral reutilizable perdió su contrato embebido")
                contract_dir=package_out/"contract"; contract_dir.mkdir(exist_ok=True)
                shutil.copy2(contract_src,contract_dir/"election_contract.json")
                shutil.copy2(dictionary_src,contract_dir/"party_dictionary.json")
                manifest["embedded_contract"]={
                    "election_contract":"contract/election_contract.json",
                    "party_dictionary":"contract/party_dictionary.json",
                    "contract_sha256":sha(contract_dir/"election_contract.json"),
                    "party_dictionary_sha256":sha(contract_dir/"party_dictionary.json"),
                }
                if manifest.get("structural_provenance"):
                    manifest["embedded_contract"].update({
                        "structural_provenance":"evidence/structural_provenance.json",
                        "structural_provenance_sha256":manifest[
                            "structural_provenance"
                        ]["sha256"],
                    })
            (package_out/"manifest.json").write_text(
                json.dumps(manifest,ensure_ascii=False,indent=2)+"\n",
                encoding="utf-8",
            )
            return manifest
    m07=(cfg.get("modulos") or {}).get("modulo_07_agregar_resultados_electorales") or {}
    contract_raw=m07.get("election_contract")
    if contract_raw:
        contract_path=root/str(contract_raw)
        if contract_path.is_file():
            contract=json.loads(contract_path.read_text(encoding="utf-8"))
            contract_tid=str(contract.get("territory_id") or "")
            contract_election_id=str(contract.get("election_id") or "")
            contract_election_date=str(contract.get("election_date") or "")
            identity_matches=(
                contract_tid == territory_id
                and bool(contract_election_id)
                and bool(contract_election_date)
                and (expected_election_id is None or contract_election_id == expected_election_id)
                and (expected_election_date is None or contract_election_date == expected_election_date)
            )
            sources=contract.get("sources") or []
            if identity_matches and len(sources)==1:
                s=sources[0]; src=root/str(s.get("path") or "")
                expected=str(s.get("sha256") or "").lower()
                if src.is_file() and expected and sha(src).lower()==expected:
                    meta={"origin_url":s.get("source_url"),"publisher":s.get("publisher"),"acquired_at":s.get("retrieved_at"),"source_mode":"existing_contract","contract":str(contract_raw)}
                    manifest=_write_package(
                        package_out,"REUSE",territory_id,edition,src,meta,{
                            "election_id":contract_election_id,
                            "election_date":contract_election_date,
                        },
                    )
                    embedded=_materialize_embedded_contract(
                        root=root,
                        package_out=package_out,
                        source_contract=contract_path,
                        manifest=manifest,
                    )
                    if embedded:
                        manifest["embedded_contract"]=embedded
                        (package_out/"manifest.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
                    return manifest
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
                composition=d.get("composition") or {}
                if str(composition.get("kind") or "")=="electoral_gap_filler":
                    from ddd_core.electoral_gap_filler import compose_delimited_sources
                    declared_rows=d.get("sources") or []
                    declared_ids=[str(row.get("id") or "").strip() for row in declared_rows]
                    if any(not sid for sid in declared_ids):
                        raise ValueError("source.id obligatorio y no vacío antes de composición")
                    if len(set(declared_ids)) != len(declared_ids):
                        raise ValueError("source.id duplicado antes de composición electoral")
                    selected_ids=[str(sel.get("id") or "").strip() for sel in selected_sources]
                    if any(not sid for sid in selected_ids):
                        raise ValueError("selected_sources.id obligatorio y no vacío")
                    if len(set(selected_ids)) != len(selected_ids):
                        raise ValueError("selected_sources contiene IDs duplicados")
                    declared_by_id={sid:row for sid,row in zip(declared_ids,declared_rows,strict=True)}
                    source_declarations=[]
                    for sel,sid in zip(selected_sources,selected_ids,strict=True):
                        declared=declared_by_id.get(sid)
                        if not declared:
                            raise ValueError(f"Fuente seleccionada sin declaración para composición: {sid}")
                        source_declarations.append(declared)
                    runtime=dict(composition)
                    runtime.setdefault("election_id",str(d.get("election_id") or ""))
                    runtime.setdefault("election_date",str(d.get("election_date") or ""))
                    runtime.setdefault("scope",territory_id)
                    merge_info=compose_delimited_sources(
                        source_paths,source_declarations,selected_sources,runtime,merged,
                        repository_root=root,
                        acquisition_root=tmp,
                    )
                else:
                    merge_info=merge_delimited_sources(
                        source_paths,
                        merged,
                        source_ids=[
                            str(sel.get("id") or "")
                            for sel in selected_sources
                        ],
                    )
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
                    "merge":{
                        key:value
                        for key,value in merge_info.items()
                        if key!="structural_provenance_path"
                    },
                    "declaration":str(decl),
                }
                composition_blocked=(
                    merge_info.get("composition")=="electoral_gap_filler"
                    and str(merge_info.get("status") or "")!="PASS"
                )
                if composition_blocked:
                    block_extra={
                        **election_extra,
                        "reason":"La composición electoral no supera validación/admisibilidad",
                        "composition_status":merge_info.get("status"),
                        "source_status":"BLOCKED",
                        "production_eligible":False,
                    }
                    manifest=_write_package(
                        package_out,"BLOCK",territory_id,edition,None,{},block_extra
                    )
                else:
                    manifest=_write_package(
                        package_out,"ACQUIRE",territory_id,edition,merged,meta,election_extra
                    )
                structural_path=str(
                    merge_info.get("structural_provenance_path") or ""
                ).strip()
                if structural_path:
                    manifest["raw_sources"]=_copy_raw_sources(
                        package_out=package_out,
                        selected_sources=selected_sources,
                        source_paths=source_paths,
                    )
                else:
                    raw_dir=package_out/"raw"; raw_dir.mkdir(exist_ok=True)
                    manifest["raw_sources"]=[]
                    for sel,src in zip(
                        selected_sources,
                        source_paths,
                        strict=True,
                    ):
                        raw_target=raw_dir/src.name
                        shutil.copy2(src,raw_target)
                        manifest["raw_sources"].append({
                            "id":sel.get("id"),
                            "path":raw_target.relative_to(
                                package_out
                            ).as_posix(),
                            "sha256":sel.get("sha256"),
                            "bytes":sel.get("bytes"),
                            "url":sel.get("url"),
                            "publisher":sel.get("publisher"),
                        })

                if structural_path:
                    structural_src=Path(structural_path)
                    structural_doc=_load_structural_provenance(
                        structural_src,
                        expected_sha256=str(
                            merge_info.get(
                                "structural_provenance_sha256"
                            ) or ""
                        ),
                        expected_source_sha256=sha(merged),
                        context="procedencia estructural del merge electoral",
                    )
                    _validate_raw_sources_against_structural(
                        package=package_out,
                        raw_sources=manifest["raw_sources"],
                        document=structural_doc,
                        context="paquete electoral adquirido",
                    )
                    evidence_dir=package_out/"evidence"; evidence_dir.mkdir(exist_ok=True)
                    structural_target=evidence_dir/"structural_provenance.json"
                    shutil.copy2(structural_src,structural_target)
                    manifest["structural_provenance"]={
                        "schema":STRUCTURAL_PROVENANCE_SCHEMA,
                        "path":"evidence/structural_provenance.json",
                        "sha256":sha(structural_target),
                        "merged_source_sha256":sha(merged),
                        "raw_sources_embedded":True,
                    }

                if merge_info.get("composition")=="electoral_gap_filler":
                    evidence_src=Path(str(merge_info["evidence_path"]))
                    evidence_dir=package_out/"evidence"; evidence_dir.mkdir(exist_ok=True)
                    evidence_target=evidence_dir/"electoral_gap_fill.json"
                    shutil.copy2(evidence_src,evidence_target)
                    universe_meta=merge_info.get("expected_universe") or {}
                    universe_rel=Path(str(universe_meta.get("path") or ""))
                    universe_src=(root/universe_rel).resolve()
                    if not universe_src.is_file() or sha(universe_src)!=str(universe_meta.get("sha256") or ""):
                        raise ValueError("Expected universe perdió su artefacto gobernado antes de empaquetar evidencia")
                    universe_target=evidence_dir/("expected_universe"+universe_src.suffix)
                    shutil.copy2(universe_src,universe_target)
                    manifest["composition_evidence"]={
                        "kind":"electoral_gap_filler",
                        "path":"evidence/electoral_gap_fill.json",
                        "sha256":sha(evidence_target),
                        "logical_digest":merge_info.get("logical_digest"),
                        "expected_universe":{
                            **universe_meta,
                            "package_path":f"evidence/{universe_target.name}",
                            "package_sha256":sha(universe_target),
                        },
                    }
                (package_out/"manifest.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
                shutil.rmtree(tmp,ignore_errors=True); return manifest
            sel=result.get("selected_source") or (selected_sources[0] if selected_sources else None)
            if not sel:
                raise ValueError("READY sin fuente electoral seleccionada")
            src=tmp/str(sel["artifact_path"])
            declared_source=next((s for s in (d.get("sources") or []) if str(s.get("id") or "")==str(sel.get("id") or "")),{})
            transformed=_transform_selected_source(src,tmp,d,declared_source,root)
            selected_src=transformed["source"] if transformed else src
            source_mode="verified_mirror_transformed" if transformed and str(declared_source.get("source_class") or "")=="verified_mirror" else ("official_acquisition_transformed" if transformed else "official_acquisition")
            meta={"origin_url":sel.get("url"),"publisher":sel.get("publisher"),"acquired_at":datetime.now(timezone.utc).isoformat(),"source_mode":source_mode,"declaration":str(decl),"source_class":declared_source.get("source_class","official")}
            if transformed:
                meta["transform"]={
                    "kind":str((declared_source.get("transform") or {}).get("kind") or ""),
                    "records":transformed["records"],"sections":transformed["sections"],"parties":transformed["parties"],
                    "source_verification_status":transformed.get("source_verification_status"),
                    "official_candidate_votes":transformed.get("official_candidate_votes"),
                    "cera_candidate_votes":transformed.get("cera_candidate_votes"),
                    "cera_percentage":transformed.get("cera_percentage"),
                    "special_rows_reconciled":transformed.get("special_rows_reconciled"),
                }
            manifest=_write_package(package_out,"ACQUIRE",territory_id,edition,selected_src,meta,election_extra)
            if transformed:
                contract_dir=package_out/"contract"; contract_dir.mkdir(exist_ok=True)
                shutil.copy2(transformed["contract"],contract_dir/"election_contract.json")
                shutil.copy2(transformed["dictionary"],contract_dir/"party_dictionary.json")
                embedded={
                    "election_contract":"contract/election_contract.json",
                    "party_dictionary":"contract/party_dictionary.json",
                    "contract_sha256":sha(contract_dir/"election_contract.json"),
                    "party_dictionary_sha256":sha(contract_dir/"party_dictionary.json"),
                }
                manifest["embedded_contract"]=embedded
                # Reescribir paths internos del contrato a rutas portables dentro del paquete.
                ep=json.loads((contract_dir/"election_contract.json").read_text(encoding="utf-8"))
                ep["sources"][0]["path"]="data/"+selected_src.name
                ep["party_dictionary"]["path"]="contract/party_dictionary.json"
                (contract_dir/"election_contract.json").write_text(json.dumps(ep,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
                embedded["contract_sha256"]=sha(contract_dir/"election_contract.json")
                manifest["embedded_contract"]=embedded
                (package_out/"manifest.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
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
