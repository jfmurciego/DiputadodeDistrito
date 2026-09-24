#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from datetime import date
from pathlib import Path

import yaml

try:\n    from herramientas.catalogo_territorios import normalize_territory_input\nexcept ModuleNotFoundError:  # ejecución directa como script\n    from catalogo_territorios import normalize_territory_input

DEFAULT = Path("configuracion/elecciones_vigentes.yaml")
PREPARATION_CATALOG = Path("configuracion/catalogo_preparacion.yaml")
DECLARATION_SCHEMA = "ddd-election-official-source-declaration/1.0"


def load_catalog(path: Path) -> dict:
    if not path.is_file():
        return {"territories": []}
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    rows = data.get("territories")
    if not isinstance(rows, list):
        raise ValueError("Catálogo de elecciones vigentes sin territories")
    return data


def _load_yaml(path: Path) -> dict:
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return data if isinstance(data, dict) else {}


def _catalog_preparation_row(root_dir: Path, territory: str, edition: str | None) -> tuple[str, str, dict] | None:
    path = root_dir / PREPARATION_CATALOG
    if not path.is_file():
        return None
    data = _load_yaml(path)
    token = normalize_territory_input(territory)
    rows = [
        row for row in (data.get("territories") or [])
        if token in {str(row.get("territory_id") or ""), str(row.get("name") or "")}
    ]
    if len(rows) != 1:
        return None
    row = rows[0]
    tid = str(row.get("territory_id") or "")
    name = str(row.get("name") or "")
    editions = row.get("editions") or {}
    selected_edition = str(edition or data.get("default_edition") or "")
    state = editions.get(selected_edition)
    if not tid or not name or not isinstance(state, dict):
        return None
    return tid, name, state


def _declaration_candidates(root_dir: Path, territory_id: str, state: dict) -> list[Path]:
    result: list[Path] = []
    explicit = state.get("electoral_source_declaration")
    if explicit:
        path = root_dir / str(explicit)
        if path.is_file():
            result.append(path)
    folder = root_dir / "territorios" / territory_id / "config" / "elecciones"
    if folder.is_dir():
        for path in sorted(folder.glob("*.yaml")):
            if path not in result:
                data = _load_yaml(path)
                if data.get("schema") == DECLARATION_SCHEMA:
                    result.append(path)
    return result


def _row_from_materialized_contract(
    *,
    territory_id: str,
    name: str,
    territorial_edition: str,
    state: dict,
    root_dir: Path,
) -> dict | None:
    contract_raw = state.get("contract_path")
    if not contract_raw:
        return None
    params_path = root_dir / str(contract_raw)
    if not params_path.is_file():
        return None
    params = _load_yaml(params_path)
    m07 = (params.get("modulos") or {}).get("modulo_07_agregar_resultados_electorales") or {}
    election_contract_raw = m07.get("election_contract")
    if not election_contract_raw:
        return None
    election_contract = root_dir / str(election_contract_raw)
    if not election_contract.is_file():
        return None
    try:
        data = json.loads(election_contract.read_text(encoding="utf-8"))
    except Exception:
        return None
    for key in ("territory_id", "election_id", "election_date"):
        if data.get(key) in (None, ""):
            return None
    if str(data.get("territory_id")) != territory_id:
        raise SystemExit(f"Contrato electoral de otro territorio: {election_contract}")
    return {
        "territory_id": territory_id,
        "name": name,
        "territorial_edition": territorial_edition,
        "election_id": str(data["election_id"]),
        "election_date": str(data["election_date"]),
        "declaration": "",
        "election_contract": election_contract.relative_to(root_dir).as_posix(),
        "resolution_mode": "materialized_election_contract",
    }


def _row_from_declaration(
    *,
    territory_id: str,
    name: str,
    territorial_edition: str,
    declaration: Path,
    root_dir: Path,
) -> dict:
    data = _load_yaml(declaration)
    for key in ("territory_id", "election_id", "election_date"):
        if data.get(key) in (None, ""):
            raise SystemExit(f"Declaración electoral incompleta: {declaration}; falta {key}")
    if str(data.get("territory_id")) != territory_id:
        raise SystemExit(f"Declaración electoral de otro territorio: {declaration}")
    return {
        "territory_id": territory_id,
        "name": name,
        "territorial_edition": territorial_edition,
        "election_id": str(data["election_id"]),
        "election_date": str(data["election_date"]),
        "declaration": declaration.relative_to(root_dir).as_posix(),
        "resolution_mode": "auto_discovered_declaration",
    }


def resolve(
    territory: str,
    path: Path = DEFAULT,
    root_dir: Path = Path("."),
    edition: str | None = None,
) -> dict:
    root = root_dir.resolve()
    token = normalize_territory_input(territory)

    # 1) Override gobernado: conserva compatibilidad con elecciones_vigentes.yaml.
    override_path = path if path.is_absolute() else root / path
    rows = [
        row for row in load_catalog(override_path)["territories"]
        if token in {str(row.get("territory_id") or ""), str(row.get("name") or "")}
    ]
    if len(rows) > 1:
        raise SystemExit(f"Elección vigente ambigua para territorio={territory!r}")
    if len(rows) == 1:
        row = dict(rows[0])
        for key in ("territory_id", "name", "territorial_edition", "election_id", "election_date", "declaration"):
            if row.get(key) in (None, ""):
                raise SystemExit(f"Elección vigente incompleta: falta {key}")
        declaration = root / str(row["declaration"])
        if not declaration.is_file():
            raise SystemExit(f"Declaración electoral vigente inexistente: {declaration}")
        declared = _load_yaml(declaration)
        if declared.get("territory_id") != row["territory_id"]:
            raise SystemExit("territory_id de declaración vigente no coincide")
        if declared.get("election_id") != row["election_id"]:
            raise SystemExit("election_id de declaración vigente no coincide")
        if str(declared.get("election_date")) != str(row["election_date"]):
            raise SystemExit("election_date de declaración vigente no coincide")
        row["resolution_mode"] = "governed_override"
        return row

    # 2) Resolución industrial: catálogo territorial + declaraciones existentes.
    found = _catalog_preparation_row(root, token, edition)
    if found is None:
        raise SystemExit(f"Territorio o edición no declarados: territorio={territory!r}, edición={edition!r}")
    territory_id, name, state = found
    territorial_edition = str(edition or _load_yaml(root / PREPARATION_CATALOG).get("default_edition") or "")
    candidates = _declaration_candidates(root, territory_id, state)
    resolved = []
    for declaration in candidates:
        try:
            resolved.append(_row_from_declaration(
                territory_id=territory_id,
                name=name,
                territorial_edition=territorial_edition,
                declaration=declaration,
                root_dir=root,
            ))
        except SystemExit:
            raise
        except Exception:
            continue
    if not resolved:
        materialized = _row_from_materialized_contract(
            territory_id=territory_id,
            name=name,
            territorial_edition=territorial_edition,
            state=state,
            root_dir=root,
        )
        if materialized is not None:
            return materialized
        raise SystemExit(
            f"No existe elección resoluble para territorio={territory!r}: "
            "no hay declaración de adquisición ni contrato electoral materializado."
        )

    # La elección más reciente declarada es la vigente. Empate de fecha = ambigüedad.
    def parsed(row: dict) -> date:
        return date.fromisoformat(str(row["election_date"]))
    resolved.sort(key=parsed, reverse=True)
    if len(resolved) > 1 and resolved[0]["election_date"] == resolved[1]["election_date"]:
        raise SystemExit(
            f"Elección vigente ambigua para territorio={territory!r}: "
            f"{resolved[0]['election_id']} / {resolved[1]['election_id']}"
        )
    return resolved[0]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--territory", required=True)
    ap.add_argument("--edition")
    ap.add_argument("--catalog", type=Path, default=DEFAULT)
    ap.add_argument("--root-dir", type=Path, default=Path("."))
    a = ap.parse_args()
    print(json.dumps(resolve(a.territory, a.catalog, a.root_dir, a.edition), ensure_ascii=False))


if __name__ == "__main__":
    main()
