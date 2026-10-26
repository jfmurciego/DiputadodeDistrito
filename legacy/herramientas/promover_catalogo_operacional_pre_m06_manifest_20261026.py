#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

import yaml

try:
    from herramientas.catalogo_preparacion import validate_repository
    from herramientas.persistir_estado_operativo_compartido import persist_rederived_tree
    from herramientas.identidad_fuentes_legislatura import electoral_identity
except ModuleNotFoundError:  # ejecución directa: python herramientas/...
    from catalogo_preparacion import validate_repository
    from persistir_estado_operativo_compartido import persist_rederived_tree
    from identidad_fuentes_legislatura import electoral_identity

CATALOG = Path("configuracion/catalogo_preparacion.yaml")
ELECTION_REGISTRY = Path("configuracion/registro_electoral.yaml")

def _load_yaml(path: Path) -> dict:
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise ValueError(f"YAML inválido: {path}")
    return data


def _save_yaml(path: Path, data: dict) -> None:
    path.write_text(yaml.safe_dump(data, allow_unicode=True, sort_keys=False, width=120), encoding="utf-8")


def _state(catalog: dict, territory_id: str, edition: str) -> tuple[dict, str]:
    for row in catalog.get("territories") or []:
        if row.get("territory_id") != territory_id:
            continue
        state = (row.get("editions") or {}).get(str(edition))
        if not isinstance(state, dict):
            raise ValueError(f"Edición ausente: {territory_id}/{edition}")
        return state, str(row.get("name") or territory_id)
    raise ValueError(f"Territorio ausente: {territory_id}")


def _receipt_path(root: Path, territory_id: str, kind: str, edition: str) -> Path:
    return root / "territorios" / territory_id / "evidencia" / "catalogo" / f"{kind}_{edition}.json"


def _write_receipt(path: Path, payload: dict) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path.as_posix()


def _registered_election(root: Path, territory_id: str, election_id: str | None) -> dict | None:
    path=root/ELECTION_REGISTRY
    if not path.is_file() or not election_id:
        return None
    registry=_load_yaml(path)
    row=(registry.get("territories") or {}).get(territory_id)
    if not isinstance(row,dict) or str(row.get("election_id") or "") != str(election_id):
        return None
    return row


def promote(
    *, root_dir: Path, kind: str, territory_id: str, edition: str, run_id: int,
    artifact_name: str, artifact_sha256: str, declaration: str | None = None,
    decision: str | None = None, election_id: str | None = None, source_commit: str | None = None,
) -> dict:
    root = root_dir.resolve(); catalog_path = root / CATALOG; catalog = _load_yaml(catalog_path)
    state, territory_name = _state(catalog, territory_id, edition); evidence = state.setdefault("evidence", {})
    digest = artifact_sha256.removeprefix("sha256:")
    common = {"schema":"ddd.catalog-evidence/1.0","kind":kind,"territory_id":territory_id,"territory_name":territory_name,"edition":str(edition),"run_id":int(run_id),"artifact_name":artifact_name,"artifact_sha256":digest}
    if source_commit: common["source_commit"] = source_commit

    if kind == "territorial_product":
        if decision not in {"PASS", "PASS_WITH_EXCEPTIONS"}: raise ValueError(f"Producto territorial no promovible: decision={decision!r}")
        receipt = _receipt_path(root, territory_id, kind, edition); rel = _write_receipt(receipt, {**common, "decision": decision, "stage": "M06"})
        state["territorial_product_available"] = True; state["territorial_certification"] = "PASS" if decision == "PASS" else "PASS_WITH_GOVERNED_EXCEPTIONS"; state["last_valid_checkpoint"] = {"run_id": int(run_id), "stage": "M06"}; evidence["territorial_product"] = str(Path(rel).relative_to(root))

    elif kind == "electoral_source":
        receipt_payload = {**common, "election_id": election_id}
        election_date = ""
        if declaration:
            declaration_path = root / declaration
            if not declaration_path.is_file(): raise ValueError(f"Declaración electoral inexistente: {declaration}")
            declared = _load_yaml(declaration_path)
            if str(declared.get("territory_id") or "") != territory_id:
                raise ValueError("Declaración electoral pertenece a otro territorio")
            declared_election_id = str(declared.get("election_id") or "")
            if not declared_election_id or (election_id and declared_election_id != election_id):
                raise ValueError(
                    f"Declaración electoral no corresponde a la elección promovida: "
                    f"{declared_election_id!r} != {election_id!r}"
                )
            election_date = str(declared.get("election_date") or "")
            receipt_payload["declaration"] = declaration; state["electoral_source_declaration"] = declaration
        else:
            contract_raw = state.get("contract_path")
            election_contract_raw = None
            if contract_raw:
                params_path = root / str(contract_raw)
                if not params_path.is_file():
                    raise ValueError(f"Contrato territorial inexistente: {contract_raw}")
                params = _load_yaml(params_path)
                m07 = (params.get("modulos") or {}).get("modulo_07_agregar_resultados_electorales") or {}
                election_contract_raw = m07.get("election_contract")
            if election_contract_raw:
                election_contract_path = root / str(election_contract_raw)
                if not election_contract_path.is_file():
                    raise ValueError(f"Contrato electoral inexistente: {election_contract_raw}")
                election_contract = json.loads(election_contract_path.read_text(encoding="utf-8"))
                if str(election_contract.get("territory_id") or "") != territory_id:
                    raise ValueError("Contrato electoral pertenece a otro territorio")
                contract_election_id = str(election_contract.get("election_id") or "")
                if not contract_election_id or (election_id and contract_election_id != election_id):
                    raise ValueError(
                        f"Contrato electoral no corresponde a la elección promovida: "
                        f"{contract_election_id!r} != {election_id!r}"
                    )
                election_date = str(election_contract.get("election_date") or "")
                receipt_payload.update({
                    "declaration": None,
                    "election_contract": str(election_contract_raw),
                    "election_contract_sha256": __import__("hashlib").sha256(
                        election_contract_path.read_bytes()
                    ).hexdigest(),
                })
                state["electoral_source_declaration"] = None
            else:
                registered = _registered_election(root, territory_id, election_id)
                if registered is None:
                    raise ValueError("Fuente electoral sin declaración, registro común ni election_contract materializado")
                election_date = str(registered.get("election_date") or "")
                receipt_payload.update({
                    "declaration": None,
                    "election_registry": ELECTION_REGISTRY.as_posix(),
                    "election_date": election_date,
                })
                state["electoral_source_declaration"] = None
        if not election_date:
            registered = _registered_election(root, territory_id, election_id)
            election_date = str((registered or {}).get("election_date") or "")
        if not election_date:
            raise ValueError("Fuente electoral sin fecha de elección verificable")
        identity = electoral_identity(
            territory_id=territory_id,
            edition=str(edition),
            election_id=str(election_id),
            election_date=election_date,
            artifact_sha256=digest,
        )
        receipt_payload["election_date"] = election_date
        receipt_payload["electoral_identity_sha256"] = identity["electoral_identity_sha256"]
        receipt = (
            root / "territorios" / territory_id / "evidencia" / "fuentes_electorales"
            / str(edition) / identity["electoral_identity_sha256"] / str(run_id) / "receipt.json"
        )
        rendered = json.dumps(receipt_payload, ensure_ascii=False, indent=2) + "\n"
        receipt.parent.mkdir(parents=True, exist_ok=True)
        if receipt.exists() and receipt.read_text(encoding="utf-8") != rendered:
            raise ValueError("Receipt electoral versionado ya existe con contenido contradictorio")
        receipt.write_text(rendered, encoding="utf-8")
        rel = receipt.as_posix()
        state["electoral_source_prepared"] = True
        evidence["electoral_source"] = str(Path(rel).relative_to(root))

    elif kind == "electoral_product":
        receipt = _receipt_path(root, territory_id, kind, edition); rel = _write_receipt(receipt, {**common, "stage": "M08"}); state["electoral_product_available"] = True; evidence["electoral_product"] = str(Path(rel).relative_to(root)); state["last_valid_checkpoint"] = {"run_id": int(run_id), "stage": "M08"}
    else: raise ValueError(f"Tipo de promoción desconocido: {kind}")

    _save_yaml(catalog_path, catalog)
    return {"territory_id":territory_id,"edition":str(edition),"kind":kind,"run_id":int(run_id),"incorporation_enabled":bool(state.get("territorial_product_available") and state.get("electoral_source_prepared") and state.get("territorial_contract_complete") and state.get("production_authorization") == "AUTHORIZED")}




def persist_promotion(
    *,
    root_dir: Path,
    kind: str,
    territory_id: str,
    edition: str,
    run_id: int,
    artifact_name: str,
    artifact_sha256: str,
    declaration: str | None = None,
    decision: str | None = None,
    election_id: str | None = None,
    source_commit: str | None = None,
    target_branch: str,
    max_attempts: int = 4,
) -> dict:
    """Persiste una promoción operacional rederivándola desde el HEAD remoto."""
    root = root_dir.resolve()
    result_box: dict[str, dict] = {}

    def apply(current_root: Path, _attempt: int) -> None:
        result_box["promotion"] = promote(
            root_dir=current_root,
            kind=kind,
            territory_id=territory_id,
            edition=str(edition),
            run_id=int(run_id),
            artifact_name=artifact_name,
            artifact_sha256=artifact_sha256,
            declaration=declaration,
            decision=decision,
            election_id=election_id,
            source_commit=source_commit,
        )

    def validate(current_root: Path) -> None:
        errors = validate_repository(root_dir=current_root)
        if errors:
            raise ValueError(
                "Promoción operacional deja repositorio inválido: "
                + "; ".join(errors[:8])
            )

    evidence_dir = {
        "electoral_source": f"territorios/{territory_id}/evidencia/fuentes_electorales",
        "territorial_product": f"territorios/{territory_id}/evidencia/catalogo",
        "electoral_product": f"territorios/{territory_id}/evidencia/catalogo",
    }[kind]
    persisted = persist_rederived_tree(
        root_dir=root,
        target_branch=target_branch,
        paths=(CATALOG.as_posix(), evidence_dir),
        commit_message=f"chore: registrar {kind} de {territory_id}",
        apply=apply,
        validate=validate,
        max_attempts=max_attempts,
        exhausted_message=(
            f"No se pudo registrar {kind} de {territory_id} tras "
            f"{max_attempts} rederivaciones desde el HEAD vigente"
        ),
    )
    result = dict(result_box.get("promotion") or {})
    result["promotion_sha"] = persisted.head_sha
    result["persistence_attempt"] = persisted.attempt
    result["persistence_changed"] = persisted.changed
    return result

def main() -> int:
    ap=argparse.ArgumentParser(); ap.add_argument("--root-dir",type=Path,default=Path(".")); ap.add_argument("--kind",required=True,choices=["territorial_product","electoral_source","electoral_product"]); ap.add_argument("--territory-id",required=True); ap.add_argument("--edition",required=True); ap.add_argument("--run-id",required=True,type=int); ap.add_argument("--artifact-name",required=True); ap.add_argument("--artifact-sha256",required=True); ap.add_argument("--declaration"); ap.add_argument("--decision"); ap.add_argument("--election-id"); ap.add_argument("--source-commit"); ap.add_argument("--persist",action="store_true"); ap.add_argument("--target-branch",default="main"); ap.add_argument("--max-attempts",type=int,default=4)
    args=ap.parse_args()
    common=dict(root_dir=args.root_dir,kind=args.kind,territory_id=args.territory_id,edition=args.edition,run_id=args.run_id,artifact_name=args.artifact_name,artifact_sha256=args.artifact_sha256,declaration=args.declaration,decision=args.decision,election_id=args.election_id,source_commit=args.source_commit)
    result=(persist_promotion(**common,target_branch=args.target_branch,max_attempts=args.max_attempts) if args.persist else promote(**common))
    print(json.dumps(result,ensure_ascii=False,indent=2)); return 0
if __name__ == "__main__": raise SystemExit(main())
