"""Composición conservadora de huecos electorales acreditados."""
from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
import csv
import hashlib
import json
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

IDENTITY_FIELDS=("election_id","election_date","election_type","scope")


@dataclass(frozen=True)
class SourceMeta:
    source_id:str; election_id:str; election_date:str; election_type:str; scope:str
    granularity:str; result_status:str; artifact_sha256:str; artifact:str; table:str

    @classmethod
    def from_mapping(cls,value:Mapping[str,Any])->"SourceMeta":
        fields=tuple(cls.__dataclass_fields__)
        missing=[k for k in fields if str(value.get(k) or "").strip()==""]
        if missing: raise ValueError(f"metadatos de fuente incompletos: {missing}")
        digest=str(value["artifact_sha256"]).lower()
        if len(digest)!=64 or any(c not in "0123456789abcdef" for c in digest):
            raise ValueError("artifact_sha256 inválido")
        return cls(**{k:str(value[k]) for k in fields})


def _identity(meta:SourceMeta)->tuple[str,str,str,str]:
    return tuple(getattr(meta,k) for k in IDENTITY_FIELDS)


def _row(raw:Mapping[str,Any],meta:SourceMeta,fallback_row:int)->dict[str,Any]:
    missing=[k for k in ("unit_id","party","votes") if k not in raw or raw[k] is None]
    if missing: raise ValueError(f"registro sin campos obligatorios {missing}")
    unit,party=str(raw["unit_id"]),str(raw["party"])
    if not unit or not party: raise ValueError("unit_id/party vacíos")
    value=raw["votes"]
    if isinstance(value,bool): raise ValueError("votes booleano no permitido")
    try: votes=int(value)
    except (TypeError,ValueError) as exc: raise ValueError(f"votes no entero: {value!r}") from exc
    if str(value).strip() not in {str(votes),f"{votes}.0"} and not isinstance(value,int):
        raise ValueError(f"votes no entero: {value!r}")
    if votes<0: raise ValueError("votes negativo")
    provenance={
        "source_id":meta.source_id,"election_id":meta.election_id,"artifact":meta.artifact,
        "artifact_sha256":meta.artifact_sha256,"table":str(raw.get("source_table") or meta.table),
        "source_row":int(raw.get("source_row") or fallback_row),"result_status":meta.result_status,
    }
    if isinstance(raw.get("provenance"),Mapping): provenance.update(deepcopy(raw["provenance"]))
    defaults={"source_id":meta.source_id,"election_id":meta.election_id,"artifact":meta.artifact,
              "artifact_sha256":meta.artifact_sha256,"table":str(raw.get("source_table") or meta.table),
              "result_status":meta.result_status}
    for key,default in defaults.items():
        if str(provenance.get(key) or "").strip()=="": provenance[key]=default
    if provenance.get("source_row") in (None,""): provenance["source_row"]=int(raw.get("source_row") or fallback_row)
    return {"unit_id":unit,"party":party,"votes":votes,
            "unit_kind":str(raw.get("unit_kind") or "geographic"),"provenance":provenance}


def _dedupe(rows:Sequence[Mapping[str,Any]],meta:SourceMeta):
    index={}; conflicts=[]
    for number,raw in enumerate(rows,1):
        item=_row(raw,meta,number); key=(item["unit_kind"],item["unit_id"],item["party"])
        previous=index.get(key)
        if previous is None: index[key]=item
        elif previous["votes"]!=item["votes"]:
            conflicts.append({"code":"CONTRADICTORY_DUPLICATE","unit_kind":key[0],"unit_id":key[1],
                              "party":key[2],"values":sorted({previous["votes"],item["votes"]}),
                              "source_id":meta.source_id})
    return index,conflicts


def _logical(row):
    p=row.get("provenance") if isinstance(row.get("provenance"),Mapping) else {}
    return {"unit_kind":row["unit_kind"],"unit_id":row["unit_id"],"party":row["party"],"votes":row["votes"],
            "source_id":p.get("source_id"),"artifact_sha256":p.get("artifact_sha256"),
            "table":p.get("table"),"result_status":p.get("result_status")}


def _digest(rows,special):
    key=lambda r:(r["unit_kind"],r["unit_id"],r["party"])
    payload={"rows":[_logical(r) for r in sorted(rows,key=key)],
             "special_units":[_logical(r) for r in sorted(special,key=key)]}
    raw=json.dumps(payload,ensure_ascii=False,sort_keys=True,separators=(",",":")).encode()
    return hashlib.sha256(raw).hexdigest()


def compose_records(primary_rows:Sequence[Mapping[str,Any]],primary_source:Mapping[str,Any],
                    fragments:Sequence[tuple[Mapping[str,Any],Sequence[Mapping[str,Any]]]],*,
                    expected_keys:Iterable[tuple[str,str]],allowed_parties:Iterable[str]|None=None,
                    allowed_status_pairs:Iterable[tuple[str,str]]=(),official_geographic_candidate_votes:int|None=None,
                    official_total_candidate_votes:int|None=None)->dict[str,Any]:
    pmeta=SourceMeta.from_mapping(primary_source); pindex,conflicts=_dedupe(primary_rows,pmeta)
    expected={(str(u),str(p)) for u,p in expected_keys}; parties=None if allowed_parties is None else {str(p) for p in allowed_parties}
    status_pairs={(str(a),str(b)) for a,b in allowed_status_pairs}
    primary={k:v for k,v in pindex.items() if k[0]=="geographic"}; snapshot=deepcopy(list(primary.values()))
    additions={}; special={}; identical=[]; blocked=set()
    for raw_meta,rows in fragments:
        meta=SourceMeta.from_mapping(raw_meta)
        if _identity(meta)!=_identity(pmeta):
            conflicts.append({"code":"ELECTION_IDENTITY_MISMATCH","source_id":meta.source_id,
                              "primary_identity":dict(zip(IDENTITY_FIELDS,_identity(pmeta))),
                              "fragment_identity":dict(zip(IDENTITY_FIELDS,_identity(meta)))})
            continue
        if meta.granularity!=pmeta.granularity:
            conflicts.append({"code":"GRANULARITY_MISMATCH","source_id":meta.source_id,
                              "primary_granularity":pmeta.granularity,"fragment_granularity":meta.granularity})
            continue
        findex,local=_dedupe(rows,meta); conflicts.extend(local); blocked.update(c["unit_id"] for c in local if c.get("unit_id"))
        for key,item in sorted(findex.items()):
            kind,unit,party=key
            if parties is not None and party not in parties:
                conflicts.append({"code":"UNRESOLVED_PARTY","source_id":meta.source_id,"unit_id":unit,"party":party}); blocked.add(unit); continue
            if kind!="geographic":
                old=special.get(key)
                if old is None: special[key]=item
                elif old["votes"]!=item["votes"]: conflicts.append({"code":"SPECIAL_UNIT_CONFLICT","unit_id":unit,"party":party,"values":[old["votes"],item["votes"]]})
                continue
            pair=(unit,party); old=primary.get(key)
            if old is not None:
                if old["votes"]==item["votes"]: identical.append({"unit_id":unit,"party":party,"source_id":meta.source_id})
                else:
                    conflicts.append({"code":"PRIMARY_OVERLAP_CONFLICT","unit_id":unit,"party":party,
                                      "primary_votes":old["votes"],"fragment_votes":item["votes"],"source_id":meta.source_id}); blocked.add(unit)
                continue
            if pair not in expected:
                conflicts.append({"code":"OUTSIDE_ACCREDITED_UNIVERSE","unit_id":unit,"party":party,"source_id":meta.source_id}); blocked.add(unit); continue
            if meta.result_status!=pmeta.result_status and (pmeta.result_status,meta.result_status) not in status_pairs:
                conflicts.append({"code":"RESULT_STATUS_MISMATCH","unit_id":unit,"party":party,
                                  "primary_status":pmeta.result_status,"fragment_status":meta.result_status,"source_id":meta.source_id}); blocked.add(unit); continue
            old=additions.get(key)
            if old is not None and old["votes"]!=item["votes"]:
                conflicts.append({"code":"FRAGMENT_CONFLICT","unit_id":unit,"party":party,"values":[old["votes"],item["votes"]]}); blocked.add(unit)
            elif old is None: additions[key]=item
    additions={k:v for k,v in additions.items() if k[1] not in blocked}
    composed=dict(primary); composed.update(additions)
    missing=sorted(expected-{(k[1],k[2]) for k in composed}); rows=[composed[k] for k in sorted(composed)]; specials=[special[k] for k in sorted(special)]
    geo_votes=sum(r["votes"] for r in rows); special_votes=sum(r["votes"] for r in specials); total=geo_votes+special_votes
    reconciliation=[]
    if official_geographic_candidate_votes is not None and geo_votes!=int(official_geographic_candidate_votes):
        reconciliation.append({"code":"GEOGRAPHIC_TOTAL_MISMATCH","actual":geo_votes,"expected":int(official_geographic_candidate_votes)})
    if official_total_candidate_votes is not None and total!=int(official_total_candidate_votes):
        reconciliation.append({"code":"TOTAL_WITH_SPECIAL_MISMATCH","actual":total,"expected":int(official_total_candidate_votes)})
    status="BLOCK" if conflicts or reconciliation else "BLOCK_INCOMPLETE" if missing else "PASS"
    after={(r["unit_kind"],r["unit_id"],r["party"],r["votes"]) for r in rows}
    for r in snapshot: assert (r["unit_kind"],r["unit_id"],r["party"],r["votes"]) in after
    report={"schema":"ddd-electoral-gap-fill/1.0","status":status,"identity":dict(zip(IDENTITY_FIELDS,_identity(pmeta))),
            "granularity":pmeta.granularity,"primary_source_id":pmeta.source_id,"expected_keys":len(expected),
            "primary_present_keys":len({(k[1],k[2]) for k in primary}),"added_keys":len(additions),
            "remaining_missing_keys":[{"unit_id":u,"party":p} for u,p in missing],"blocked_units":sorted(blocked),
            "conflicts":conflicts,"ignored_identical_duplicates":identical,"geographic_candidate_votes":geo_votes,
            "special_candidate_votes":special_votes,"candidate_votes_with_special":total,"reconciliation_errors":reconciliation,
            "logical_digest":_digest(rows,specials),"production_eligible":False}
    return {"rows":rows,"special_units":specials,"report":report}


def _read_delimited_records(path,*,source_decl,composition):
    path=Path(path); raw=path.read_bytes(); text=None
    for encoding in ("utf-8-sig","utf-8","latin-1"):
        try: text=raw.decode(encoding); break
        except UnicodeDecodeError: pass
    if text is None: raise ValueError(f"fuente electoral no decodificable: {path}")
    reader=csv.DictReader(text.splitlines(),delimiter=str((source_decl.get("composition_fields") or {}).get("delimiter") or composition.get("delimiter") or ";"))
    fields=source_decl.get("composition_fields") or composition.get("fields") or {}
    unit,party,votes,kind=(str(fields.get(k) or "") for k in ("unit","party","votes","unit_kind"))
    if not (unit and party and votes): raise ValueError("electoral_gap_filler requiere fields unit/party/votes")
    missing=[x for x in (unit,party,votes) if x not in (reader.fieldnames or [])]
    if missing: raise ValueError(f"fuente sin columnas declaradas: {missing}")
    default=str(source_decl.get("unit_kind_default") or composition.get("unit_kind_default") or "geographic")
    return [{"unit_id":str(r.get(unit) or ""),"party":str(r.get(party) or ""),"votes":r.get(votes),
             "unit_kind":str(r.get(kind) or default) if kind else default,"source_row":n,
             "source_table":str(source_decl.get("source_table") or source_decl.get("id") or path.name)}
            for n,r in enumerate(reader,2) if r is not None]


def _load_expected_keys(path):
    data=json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data,list) or not data: raise ValueError("expected_keys debe ser una lista JSON no vacía")
    out=set()
    for i,row in enumerate(data,1):
        if not isinstance(row,Mapping): raise ValueError(f"expected_keys[{i}] no es objeto")
        unit,party=str(row.get("unit_id") or ""),str(row.get("party") or "")
        if not unit or not party: raise ValueError(f"expected_keys[{i}] sin unit_id/party")
        out.add((unit,party))
    return out


def _source_meta(source,selected,composition):
    evidence=source.get("election_evidence")
    if not isinstance(evidence,Mapping): raise ValueError(f"fuente {source.get('id')!r} sin election_evidence")
    refs=evidence.get("references")
    if not isinstance(refs,list) or not [r for r in refs if str(r).strip()]: raise ValueError(f"fuente {source.get('id')!r} sin referencias de identidad electoral")
    meta={"source_id":str(source.get("id") or ""),"election_id":str(evidence.get("election_id") or ""),
          "election_date":str(evidence.get("election_date") or ""),"election_type":str(evidence.get("election_type") or ""),
          "scope":str(evidence.get("scope") or ""),"granularity":str(source.get("composition_granularity") or composition.get("granularity") or ""),
          "result_status":str(source.get("result_status") or ""),"artifact_sha256":str(selected.get("sha256") or ""),
          "artifact":str(selected.get("artifact_path") or selected.get("downloaded_path") or source.get("url") or ""),
          "table":str(source.get("source_table") or source.get("id") or "")}
    expected={k:str((composition.get("election_identity") or {}).get(k) or "") for k in IDENTITY_FIELDS}
    actual={k:meta[k] for k in IDENTITY_FIELDS}
    if any(not expected[k] for k in IDENTITY_FIELDS): raise ValueError("composition.election_identity debe declarar id, fecha, tipo y ámbito")
    if actual!=expected: raise ValueError(f"evidencia de identidad incompatible para {meta['source_id']}: {actual} != {expected}")
    return meta


def compose_declared_gap_csv(*,source_paths,selected_sources,source_declarations,declaration,root,out_dir):
    root,out_dir=Path(root),Path(out_dir); composition=declaration.get("composition") or {}
    if str(composition.get("kind") or "")!="electoral_gap_filler": raise ValueError("composition.kind no es electoral_gap_filler")
    if len(source_paths)!=len(selected_sources): raise ValueError("paths/selected_sources desalineados")
    by_id={str(s.get("id") or ""):s for s in source_declarations}
    selected={str(s.get("id") or ""):(p,s) for p,s in zip(source_paths,selected_sources)}
    primary_id=str(composition.get("primary_source_id") or "")
    if not primary_id or primary_id not in selected: raise ValueError("primary_source_id no está entre las fuentes READY")
    expected_path=Path(str(composition.get("expected_keys") or ""))
    if not str(expected_path): raise ValueError("electoral_gap_filler requiere expected_keys")
    if not expected_path.is_absolute(): expected_path=root/expected_path
    primary_path,primary_selected=selected[primary_id]; primary_decl=by_id.get(primary_id)
    if primary_decl is None: raise ValueError(f"fuente primaria {primary_id!r} no declarada")
    primary_meta=_source_meta(primary_decl,primary_selected,composition)
    primary_rows=_read_delimited_records(primary_path,source_decl=primary_decl,composition=composition)
    evidence=[{"source_id":primary_id,"references":list((primary_decl.get("election_evidence") or {}).get("references") or []),"artifact_sha256":primary_meta["artifact_sha256"]}]
    fragments=[]
    for sid,(path,sel) in sorted(selected.items()):
        if sid==primary_id: continue
        decl=by_id.get(sid)
        if decl is None: raise ValueError(f"fuente {sid!r} READY pero no declarada")
        meta=_source_meta(decl,sel,composition); fragments.append((meta,_read_delimited_records(path,source_decl=decl,composition=composition)))
        evidence.append({"source_id":sid,"references":list((decl.get("election_evidence") or {}).get("references") or []),"artifact_sha256":meta["artifact_sha256"]})
    result=compose_records(primary_rows,primary_meta,fragments,expected_keys=_load_expected_keys(expected_path),
        allowed_parties=composition.get("allowed_parties"),
        allowed_status_pairs={tuple(x) for x in (composition.get("allowed_status_pairs") or []) if isinstance(x,(list,tuple)) and len(x)==2},
        official_geographic_candidate_votes=composition.get("official_geographic_candidate_votes"),
        official_total_candidate_votes=composition.get("official_total_candidate_votes"))
    result["report"]["identity_evidence"]=evidence; result["report"]["expected_keys_path"]=str(expected_path)
    out_dir.mkdir(parents=True,exist_ok=True); composed=out_dir/"resultados_electorales_compuestos.csv"
    with composed.open("w",encoding="utf-8",newline="") as fh:
        writer=csv.DictWriter(fh,fieldnames=["CUSEC_KEY","party","votes"],delimiter=";"); writer.writeheader()
        for row in result["rows"]: writer.writerow({"CUSEC_KEY":row["unit_id"],"party":row["party"],"votes":row["votes"]})
    lineage=out_dir/"electoral_gap_lineage.jsonl"
    with lineage.open("w",encoding="utf-8") as fh:
        for row in result["rows"]+result["special_units"]:
            fh.write(json.dumps({"unit_kind":row["unit_kind"],"unit_id":row["unit_id"],"party":row["party"],"votes":row["votes"],"provenance":row["provenance"]},ensure_ascii=False,sort_keys=True)+"\n")
    report=out_dir/"electoral_gap_report.json"; report.write_text(json.dumps(result["report"],ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    return {**result,"composed_path":composed,"lineage_path":lineage,"report_path":report}
