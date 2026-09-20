#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

import yaml

CATALOG = Path("configuracion/catalogo_preparacion.yaml")

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


def promote(
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
) -> dict:
    root = root_dir.resolve()
    catalog_path = root / CATALOG
    catalog = _load_yaml(catalog_path)
    state, territory_name = _state(catalog, territory_id, edition)
    evidence = state.setdefault("evidence", {})
    digest = artifact_sha256.removeprefix("sha256:")

    common = {
        "schema": "ddd.catalog-evidence/1.0",
        "kind": kind,
        "territory_id": territory_id,
        "territory_name": territory_name,
        "edition": str(edition),
        "run_id": int(run_id),
        "artifact_name": artifact_name,
        "artifact_sha256": digest,
    }
    if source_commit:
        common["source_commit"] = source_commit

    if kind == "territorial_product":
        if decision not in {"PASS", "PASS_WITH_EXCEPTIONS"}:
            raise ValueError(f"Producto territorial no promovible: decision={decision!r}")
        receipt = _receipt_path(root, territory_id, kind, edition)
        rel = _write_receipt(receipt, {**common, "decision": decision, "stage": "M06"})
        state["territorial_product_available"] = True
        state["territorial_certification"] = "PASS" if decision == "PASS" else "PASS_WITH_GOVERNED_EXCEPTIONS"
        state["last_valid_checkpoint"] = {"run_id": int(run_id), "stage": "M06"}
        evidence["territorial_product"] = str(Path(rel).relative_to(root))

    elif kind == "electoral_source":
        if not declaration:
            raise ValueError("Fuente electoral sin declaración")
        declaration_path = root / declaration
        if not declaration_path.is_file():
            raise ValueError(f"Declaración electoral inexistente: {declaration}")
        receipt = _receipt_path(root, territory_id, kind, edition)
        rel = _write_receipt(receipt, {**common, "declaration": declaration, "election_id": election_id})
        state["electoral_source_declaration"] = declaration
        state["electoral_source_prepared"] = True
        evidence["electoral_source"] = str(Path(rel).relative_to(root))

    elif kind == "electoral_product":
        receipt = _receipt_path(root, territory_id, kind, edition)
        rel = _write_receipt(receipt, {**common, "stage": "M08"})
        state["electoral_product_available"] = True
        evidence["electoral_product"] = str(Path(rel).relative_to(root))
        state["last_valid_checkpoint"] = {"run_id": int(run_id), "stage": "M08"}

    else:
        raise ValueError(f"Tipo de promoción desconocido: {kind}")

    _save_yaml(catalog_path, catalog)
    return {
        "territory_id": territory_id,
        "edition": str(edition),
        "kind": kind,
        "run_id": int(run_id),
        "incorporation_enabled": bool(
            state.get("territorial_product_available")
            and state.get("electoral_source_prepared")
            and state.get("territorial_contract_complete")
            and state.get("production_authorization") == "AUTHORIZED"
        ),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root-dir", type=Path, default=Path("."))
    ap.add_argument("--kind", required=True, choices=["territorial_product", "electoral_source", "electoral_product"])
    ap.add_argument("--territory-id", required=True)
    ap.add_argument("--edition", required=True)
    ap.add_argument("--run-id", required=True, type=int)
    ap.add_argument("--artifact-name", required=True)
    ap.add_argument("--artifact-sha256", required=True)
    ap.add_argument("--declaration")
    ap.add_argument("--decision")
    ap.add_argument("--election-id")
    ap.add_argument("--source-commit")
    args = ap.parse_args()
    result = promote(
        root_dir=args.root_dir,
        kind=args.kind,
        territory_id=args.territory_id,
        edition=args.edition,
        run_id=args.run_id,
        artifact_name=args.artifact_name,
        artifact_sha256=args.artifact_sha256,
        declaration=args.declaration,
        decision=args.decision,
        election_id=args.election_id,
        source_commit=args.source_commit,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
