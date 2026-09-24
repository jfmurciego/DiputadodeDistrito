#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, re
from pathlib import Path
import yaml

try:\n    from herramientas.catalogo_territorios import load_master, normalize_territory_input\nexcept ModuleNotFoundError:  # ejecución directa como script\n    from catalogo_territorios import load_master, normalize_territory_input

CATALOG=Path("configuracion/catalogo_preparacion.yaml")
MASTER=Path("configuracion/catalogo_territorios_espana_2025.yaml")
REQUIRED=(
 "territory_declared","preparation_status","contract_path","territorial_source_declaration",
 "electoral_source_declaration","territorial_sources_prepared","territorial_contract_complete",
 "territorial_product_available","electoral_source_prepared","electoral_product_available",
 "territorial_certification","production_authorization","last_valid_checkpoint",
)
PREPARABLE={"READY","READY_INITIAL"}

def _sha256(path:Path)->str:
    h=hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda:f.read(1024*1024),b""): h.update(chunk)
    return h.hexdigest()

def _yaml(path:Path)->dict:
    data=yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(data,dict): raise ValueError(f"YAML inválido: {path}")
    return data

def load_catalog(path:Path=CATALOG)->dict:
    data=_yaml(path)
    if data.get("schema")!="ddd-preparation-catalog/1.1":
        raise ValueError("Esquema de catálogo de preparación no reconocido")
    rows=data.get("territories")
    if not isinstance(rows,list) or not rows: raise ValueError("Catálogo vacío")
    seen=set()
    for row in rows:
        tid=str(row.get("territory_id") or ""); name=str(row.get("name") or "")
        if not tid or not name or tid in seen: raise ValueError(f"Territorio inválido o duplicado: {tid!r}")
        seen.add(tid)
        editions=row.get("editions") or {}
        if not isinstance(editions,dict) or not editions: raise ValueError(f"{tid}: sin ediciones")
        for edition,state in editions.items():
            if not isinstance(state,dict): raise ValueError(f"{tid}/{edition}: estado inválido")
            missing=[k for k in REQUIRED if k not in state]
            if missing: raise ValueError(f"{tid}/{edition}: faltan {', '.join(missing)}")
            if state["preparation_status"] not in PREPARABLE|{"PENDING_INCORPORATION"}:
                raise ValueError(f"{tid}/{edition}: preparation_status inválido")
            cp=state.get("last_valid_checkpoint")
            if cp is not None and (not isinstance(cp,dict) or not isinstance(cp.get("run_id"),int) or not re.fullmatch(r"M0[1-8]",str(cp.get("stage") or ""))):
                raise ValueError(f"{tid}/{edition}: checkpoint inválido")
    return data

def validate_repository(path:Path=CATALOG,root_dir:Path=Path("."))->list[str]:
    root=root_dir.resolve(); data=load_catalog(path if path.is_absolute() else root/path)
    master_rows={str(r.get("territory_id")):r for r in load_master(root/MASTER)}
    errors=[]
    for row in data["territories"]:
        tid=row["territory_id"]; name=row["name"]
        m=master_rows.get(tid)
        if not m: errors.append(f"{tid}: ausente del catálogo territorial maestro")
        elif str(m.get("name"))!=name: errors.append(f"{tid}: nombre no coincide con catálogo maestro")
        for edition,state in row["editions"].items():
            contract_raw=state.get("contract_path")
            contract=(root/contract_raw) if contract_raw else None
            cfg=None
            if contract_raw:
                if not contract.is_file(): errors.append(f"{tid}/{edition}: contract_path inexistente: {contract_raw}")
                else:
                    try: cfg=_yaml(contract)
                    except Exception as exc: errors.append(f"{tid}/{edition}: contrato ilegible: {exc}")
            if cfg is not None:
                meta=cfg.get("meta") or {}
                if str(meta.get("territory_id") or "")!=tid: errors.append(f"{tid}/{edition}: meta.territory_id no coincide")
                if str(meta.get("year") or "")!=str(edition): errors.append(f"{tid}/{edition}: meta.year no coincide")
                actual_auth=str(meta.get("production_authorization") or "NONE")
                if actual_auth!=str(state.get("production_authorization")):
                    errors.append(f"{tid}/{edition}: production_authorization catálogo={state.get('production_authorization')} contrato={actual_auth}")
                if state.get("territorial_contract_complete") and str(meta.get("contract_level"))!="production_m01_m06":
                    errors.append(f"{tid}/{edition}: contrato marcado completo pero contract_level={meta.get('contract_level')}")
            elif state.get("territorial_contract_complete"):
                errors.append(f"{tid}/{edition}: contrato completo sin fichero materializado")
            src_raw=state.get("territorial_source_declaration")
            if src_raw:
                src=root/src_raw
                if not src.is_file(): errors.append(f"{tid}/{edition}: declaración territorial inexistente: {src_raw}")
                else:
                    d=_yaml(src); tr=d.get("territory") or {}
                    if str(tr.get("id") or "")!=tid or str(tr.get("edition") or "")!=str(edition):
                        errors.append(f"{tid}/{edition}: declaración territorial no corresponde al catálogo")
            if state.get("preparation_status") in PREPARABLE and not src_raw:
                errors.append(f"{tid}/{edition}: preparable sin declaración territorial inicial")
            if state.get("preparation_status")=="PENDING_INCORPORATION" and src_raw:
                errors.append(f"{tid}/{edition}: pendiente pese a tener declaración territorial")
            if state.get("territorial_sources_prepared") and not src_raw:
                errors.append(f"{tid}/{edition}: fuentes preparadas sin declaración")
            ed_raw=state.get("electoral_source_declaration")
            if ed_raw and not (root/ed_raw).is_file():
                errors.append(f"{tid}/{edition}: declaración electoral inexistente: {ed_raw}")

            evidence=state.get("evidence") or {}
            def require_evidence(kind:str,flag:str)->Path|None:
                if not state.get(flag): return None
                raw=evidence.get(kind)
                if not raw:
                    errors.append(f"{tid}/{edition}: {flag}=true sin evidence.{kind}")
                    return None
                p=root/str(raw)
                if not p.is_file() or p.stat().st_size<=0:
                    errors.append(f"{tid}/{edition}: evidencia inexistente o vacía: {raw}")
                    return None
                return p

            require_evidence("territorial_product","territorial_product_available")
            require_evidence("electoral_product","electoral_product_available")
            electoral_evidence=require_evidence("electoral_source","electoral_source_prepared")
            if state.get("electoral_source_prepared") and electoral_evidence is not None:
                receipt=None
                try:
                    receipt=json.loads(electoral_evidence.read_text(encoding="utf-8"))
                except Exception:
                    receipt=None
                if isinstance(receipt,dict) and receipt.get("schema")=="ddd.catalog-evidence/1.0":
                    if receipt.get("kind")!="electoral_source":
                        errors.append(f"{tid}/{edition}: evidencia electoral con tipo inválido")
                    if str(receipt.get("territory_id") or "")!=tid or str(receipt.get("edition") or "")!=str(edition):
                        errors.append(f"{tid}/{edition}: evidencia electoral no corresponde al territorio/edición")
                    if not isinstance(receipt.get("run_id"),int) or not str(receipt.get("artifact_name") or "").startswith(f"ddd-electoral-package-{tid}-{edition}-"):
                        errors.append(f"{tid}/{edition}: evidencia electoral sin run/artefacto durable")
                    if not re.fullmatch(r"[0-9a-f]{64}",str(receipt.get("artifact_sha256") or "")):
                        errors.append(f"{tid}/{edition}: evidencia electoral sin SHA-256 de artefacto")
                    if str(receipt.get("declaration") or "")!=str(ed_raw or ""):
                        errors.append(f"{tid}/{edition}: evidencia electoral y declaración no coinciden")
                    if not ed_raw:
                        election_contract_raw=str(receipt.get("election_contract") or "")
                        election_contract_hash=str(receipt.get("election_contract_sha256") or "").lower()
                        if not election_contract_raw or not re.fullmatch(r"[0-9a-f]{64}",election_contract_hash):
                            errors.append(f"{tid}/{edition}: evidencia electoral sin contrato materializado verificable")
                        else:
                            election_contract_path=root/election_contract_raw
                            if not election_contract_path.is_file():
                                errors.append(f"{tid}/{edition}: contrato electoral de evidencia inexistente: {election_contract_raw}")
                            elif _sha256(election_contract_path).lower()!=election_contract_hash:
                                errors.append(f"{tid}/{edition}: SHA-256 del contrato electoral de evidencia no coincide")
                            else:
                                try:
                                    election_contract=json.loads(election_contract_path.read_text(encoding="utf-8"))
                                    if str(election_contract.get("territory_id") or "")!=tid:
                                        errors.append(f"{tid}/{edition}: contrato electoral de evidencia pertenece a otro territorio")
                                    if str(election_contract.get("election_id") or "")!=str(receipt.get("election_id") or ""):
                                        errors.append(f"{tid}/{edition}: election_id de evidencia no coincide con contrato electoral")
                                except Exception as exc:
                                    errors.append(f"{tid}/{edition}: contrato electoral de evidencia inválido: {exc}")
                else:
                    # Compatibilidad con evidencias históricas ya certificadas de Aragón/Castilla y León.
                    if cfg is None:
                        errors.append(f"{tid}/{edition}: fuente electoral preparada sin contrato territorial legible")
                    else:
                        m07=(cfg.get("modulos") or {}).get("modulo_07_agregar_resultados_electorales") or {}
                        contract_raw=m07.get("election_contract")
                        contract_path=(root/str(contract_raw)) if contract_raw else None
                        if contract_path is None or not contract_path.is_file():
                            errors.append(f"{tid}/{edition}: fuente electoral preparada sin election_contract real")
                        else:
                            try:
                                contract=json.loads(contract_path.read_text(encoding="utf-8"))
                                sources=contract.get("sources") or []
                                if not sources:
                                    errors.append(f"{tid}/{edition}: election_contract sin fuentes")
                                for source in sources:
                                    src_raw=source.get("path"); expected=str(source.get("sha256") or "").lower()
                                    src=(root/str(src_raw)) if src_raw else None
                                    if not src_raw or not expected:
                                        errors.append(f"{tid}/{edition}: fuente electoral sin path/sha256 contractual")
                                    elif src is not None and src.is_file() and _sha256(src).lower()!=expected:
                                        errors.append(f"{tid}/{edition}: SHA-256 electoral no coincide: {src_raw}")
                            except Exception as exc:
                                errors.append(f"{tid}/{edition}: election_contract inválido: {exc}")
    if errors: raise ValueError("\n".join(errors))
    return []

def rows_for(mode:str,path:Path=CATALOG)->list[dict]:
    data=load_catalog(path)
    out=[]
    for row in data["territories"]:
        for edition,state in (row.get("editions") or {}).items():
            if not state.get("territory_declared"): continue
            if mode=="preparation":
                eligible=state.get("preparation_status") in PREPARABLE
            elif mode in {"production","generation"}:
                eligible=bool(
                    state.get("territorial_sources_prepared")
                    and state.get("territorial_contract_complete")
                    and state.get("production_authorization")=="AUTHORIZED"
                )
            elif mode=="electoral_application":
                eligible=bool(
                    state.get("territorial_product_available")
                    and state.get("electoral_source_prepared")
                    and state.get("territorial_contract_complete")
                    and state.get("production_authorization")=="AUTHORIZED"
                )
            else:
                raise ValueError(f"Modo de catálogo desconocido: {mode}")
            if eligible: out.append({"territory_id":row["territory_id"],"name":row["name"],"edition":str(edition),**state})
    return out

def resolve(mode:str,territory:str,edition:str,path:Path=CATALOG)->dict:
    territory=normalize_territory_input(territory)
    matches=[r for r in rows_for(mode,path) if r["edition"]==str(edition) and territory in {r["name"],r["territory_id"]}]
    if len(matches)!=1: raise SystemExit(f"No existe opción {mode} única para territorio={territory!r}, edición={edition!r}")
    return matches[0]

def lookup(territory:str,edition:str,path:Path=CATALOG)->dict:
    territory=normalize_territory_input(territory)
    matches=[]
    for row in load_catalog(path)["territories"]:
        if territory not in {row["name"],row["territory_id"]}: continue
        state=(row.get("editions") or {}).get(str(edition))
        if state is not None:
            matches.append({"territory_id":row["territory_id"],"name":row["name"],"edition":str(edition),**state})
    if len(matches)!=1:
        raise SystemExit(f"No existe territorio/edición único para territorio={territory!r}, edición={edition!r}")
    return matches[0]

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--catalog",type=Path,default=CATALOG); ap.add_argument("--root-dir",type=Path,default=Path("."))
    sub=ap.add_subparsers(dest="cmd",required=True)
    sub.add_parser("validate")
    modes=["preparation","production","generation","electoral_application"]
    op=sub.add_parser("options"); op.add_argument("--mode",choices=modes,required=True)
    rs=sub.add_parser("resolve"); rs.add_argument("--mode",choices=modes,required=True); rs.add_argument("--territory",required=True); rs.add_argument("--edition",required=True)
    lk=sub.add_parser("lookup"); lk.add_argument("--territory",required=True); lk.add_argument("--edition",required=True)
    a=ap.parse_args()
    path=a.catalog if a.catalog.is_absolute() else a.root_dir/a.catalog
    if a.cmd=="validate": validate_repository(path,a.root_dir); print("OK"); return
    if a.cmd=="options": print(json.dumps(rows_for(a.mode,path),ensure_ascii=False)); return
    if a.cmd=="lookup": print(json.dumps(lookup(a.territory,a.edition,path),ensure_ascii=False)); return
    print(json.dumps(resolve(a.mode,a.territory,a.edition,path),ensure_ascii=False))
if __name__=="__main__": main()
