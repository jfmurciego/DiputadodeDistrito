#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

import yaml

MATRIX = Path("configuracion/preparacion_legislatura_vigente.yaml")
CATALOG = Path("configuracion/catalogo_preparacion.yaml")
REGISTRY = Path("configuracion/registro_electoral.yaml")
SHA256 = re.compile(r"^[0-9a-f]{64}$")
GIT_SHA = re.compile(r"^[0-9a-f]{40}$")


def _yaml(path: Path) -> dict:
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise ValueError(f"YAML inválido: {path}")
    return data


def _json(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"JSON inválido: {path}")
    return data


def _digest(value: object) -> str | None:
    text = str(value or "").removeprefix("sha256:").strip().lower()
    return text if SHA256.fullmatch(text) else None


def _catalog_state(root: Path, territory_id: str, edition: str) -> tuple[dict, dict]:
    data = _yaml(root / CATALOG)
    rows = [r for r in data.get("territories") or [] if r.get("territory_id") == territory_id]
    if len(rows) != 1:
        raise ValueError(f"Territorio ausente/duplicado en catálogo: {territory_id}")
    state = (rows[0].get("editions") or {}).get(str(edition))
    if not isinstance(state, dict):
        raise ValueError(f"Edición operativa ausente: {territory_id}/{edition}")
    return rows[0], state


def _territorial_candidate(root: Path, territory_id: str, state: dict, selected_year: int) -> dict:
    prep = state.get("preparation_evidence")
    declaration_rel = state.get("territorial_source_declaration")
    if not state.get("territorial_sources_prepared") or not isinstance(prep, dict) or not declaration_rel:
        return {"reusable": False, "reason": "TERRITORIAL_PACKAGE_MISSING"}
    declaration_path = root / str(declaration_rel)
    if not declaration_path.is_file():
        return {"reusable": False, "reason": "TERRITORIAL_DECLARATION_MISSING"}
    declaration = _yaml(declaration_path)
    territory = declaration.get("territory") or {}
    if str(territory.get("id") or "") != territory_id:
        return {"reusable": False, "reason": "TERRITORIAL_IDENTITY_MISMATCH"}
    observed_year = int(territory.get("source_year", territory.get("edition", 0)) or 0)
    if observed_year != selected_year:
        return {
            "reusable": False,
            "reason": "TERRITORIAL_SOURCE_YEAR_MISMATCH",
            "observed_source_year": observed_year,
        }
    run_id = prep.get("run_id")
    artifact_name = str(prep.get("artifact_name") or "")
    artifact_sha256 = _digest(prep.get("artifact_sha256"))
    package_sha256 = _digest(prep.get("package_sha256"))
    if not isinstance(run_id, int) or run_id <= 0:
        return {"reusable": False, "reason": "TERRITORIAL_RUN_INVALID"}
    if artifact_name != f"ddd-source-package-{territory_id}-2025-{run_id}":
        return {"reusable": False, "reason": "TERRITORIAL_ARTIFACT_IDENTITY_MISMATCH"}
    if not artifact_sha256 or not package_sha256:
        return {"reusable": False, "reason": "TERRITORIAL_DIGEST_MISSING"}
    return {
        "reusable": True,
        "reason": "TERRITORIAL_DURABLE_CANDIDATE",
        "run_id": run_id,
        "artifact_name": artifact_name,
        "artifact_sha256": artifact_sha256,
        "package_sha256": package_sha256,
        "source_year": observed_year,
        "declaration": str(declaration_rel),
    }


def _electoral_candidate(root: Path, territory_id: str, state: dict, election_id: str) -> dict:
    evidence = state.get("evidence") or {}
    rel = evidence.get("electoral_source") if isinstance(evidence, dict) else None
    if not state.get("electoral_source_prepared") or not rel:
        return {"reusable": False, "reason": "ELECTORAL_PACKAGE_MISSING"}
    path = root / str(rel)
    if not path.is_file():
        return {"reusable": False, "reason": "ELECTORAL_RECEIPT_MISSING"}
    data = _json(path)
    schema = data.get("schema")
    if str(data.get("territory_id") or "") != territory_id:
        return {"reusable": False, "reason": "ELECTORAL_IDENTITY_MISMATCH"}
    if str(data.get("election_id") or "") != election_id:
        return {"reusable": False, "reason": "ELECTORAL_ELECTION_MISMATCH"}

    if schema == "ddd.catalog-evidence/1.0":
        if data.get("kind") != "electoral_source":
            return {"reusable": False, "reason": "ELECTORAL_RECEIPT_KIND"}
        run_id = data.get("run_id")
        artifact_name = str(data.get("artifact_name") or "")
        artifact_sha256 = _digest(data.get("artifact_sha256"))
        source_commit = str(data.get("source_commit") or "")
        if not isinstance(run_id, int) or run_id <= 0:
            return {"reusable": False, "reason": "ELECTORAL_RUN_INVALID"}
        if artifact_name != f"ddd-electoral-package-{territory_id}-2025-{run_id}":
            return {"reusable": False, "reason": "ELECTORAL_ARTIFACT_IDENTITY_MISMATCH"}
        if not artifact_sha256:
            return {"reusable": False, "reason": "ELECTORAL_DIGEST_MISSING"}
        if not GIT_SHA.fullmatch(source_commit):
            return {"reusable": False, "reason": "ELECTORAL_PROVENANCE_MISSING"}
        return {
            "reusable": True,
            "reason": "ELECTORAL_DURABLE_CANDIDATE",
            "run_id": run_id,
            "artifact_name": artifact_name,
            "artifact_sha256": artifact_sha256,
            "receipt": str(rel),
        }

    if schema == "ddd-election-source-provenance/1.0":
        digest = _digest(data.get("normalized_sha256")) or _digest(data.get("source_sha256"))
        if not digest or not data.get("publisher") or not data.get("source_url") or not data.get("retrieved_at"):
            return {"reusable": False, "reason": "ELECTORAL_LEGACY_PROVENANCE_INCOMPLETE"}
        return {
            "reusable": False,
            "legacy": True,
            "reason": "ELECTORAL_PACKAGE_IDENTITY_NOT_DURABLE",
            "artifact_sha256": digest,
            "receipt": str(rel),
        }
    return {"reusable": False, "reason": "ELECTORAL_RECEIPT_SCHEMA"}


def validate_matrix(root: Path) -> list[dict]:
    matrix = _yaml(root / MATRIX)
    registry = _yaml(root / REGISTRY)
    rows = matrix.get("territories") or []
    registered = registry.get("territories") or {}
    if len(rows) != 19 or len(registered) != 19:
        raise ValueError(f"La matriz y el registro deben contener 19 territorios: {len(rows)}/{len(registered)}")
    ids = [str(r.get("territory_id") or "") for r in rows]
    if len(set(ids)) != 19 or set(ids) != set(registered):
        raise ValueError("La matriz no coincide exactamente con los 19 territorios del registro electoral")

    latest = int((matrix.get("population_section_policy") or {}).get("latest_official_population_section_year"))
    for row in rows:
        tid = row["territory_id"]
        reg = registered[tid]
        if row.get("election_id") != reg.get("election_id") or str(row.get("election_date")) != str(reg.get("election_date")):
            raise ValueError(f"{tid}: identidad electoral de matriz no coincide con registro")
        election_year = int(str(row["election_date"])[:4])
        terr = row.get("territorial") or {}
        required = int(terr.get("required_year"))
        selected = int(terr.get("selected_source_year"))
        lag = int(terr.get("lag_years", 0))
        if required != election_year:
            raise ValueError(f"{tid}: año territorial requerido debe ser el año de la elección")
        if required <= latest:
            if selected != required or lag != 0:
                raise ValueError(f"{tid}: existe fuente oficial del año electoral y no admite sustitución")
        else:
            if selected != latest or lag != required - latest or not str(terr.get("reason") or "").strip():
                raise ValueError(f"{tid}: sustitución temporal no declarada correctamente")
        if selected > latest:
            raise ValueError(f"{tid}: source_year {selected} aún no publicado")
    return rows


def resolve(root: Path, territory: str = "Todos") -> dict:
    root = root.resolve()
    rows = validate_matrix(root)
    matrix = _yaml(root / MATRIX)
    edition = str(matrix.get("project_edition") or "2025")
    wanted = territory.strip().casefold()
    selected_rows = rows if wanted in {"todos", "all"} else [
        r for r in rows
        if wanted in {str(r["territory_id"]).casefold(), str(r["name"]).casefold()}
    ]
    if not selected_rows:
        raise ValueError(f"Territorio no encontrado: {territory}")

    plans = []
    for row in selected_rows:
        tid = row["territory_id"]
        _, state = _catalog_state(root, tid, edition)
        terr = row["territorial"]
        electoral = row["electoral"]
        selected_year = int(terr["selected_source_year"])
        t_candidate = _territorial_candidate(root, tid, state, selected_year)
        if t_candidate.get("reusable"):
            t_action = "REUSE_TEMPORAL_SUBSTITUTION" if int(terr["required_year"]) != selected_year else "REUSE"
        else:
            t_action = "ACQUIRE"

        if electoral.get("action") == "BLOCKED_PROVISIONAL":
            e_candidate = {"reusable": False, "reason": "PROVISIONAL_NOT_PRODUCTION_ELIGIBLE"}
            e_action = "BLOCKED_PROVISIONAL"
        else:
            e_candidate = _electoral_candidate(root, tid, state, row["election_id"])
            e_action = "REUSE" if e_candidate.get("reusable") else "ACQUIRE"

        plans.append({
            "territory_id": tid,
            "name": row["name"],
            "election_id": row["election_id"],
            "election_date": str(row["election_date"]),
            "project_edition": edition,
            "population_year_required": int(terr["required_year"]),
            "population_year_current": int(terr["current_package_year"]),
            "population_year_selected": selected_year,
            "section_year_required": int(terr["required_year"]),
            "section_year_current": int(terr["current_package_year"]),
            "section_year_selected": selected_year,
            "temporal_lag_years": int(terr.get("lag_years", 0)),
            "temporal_reason": terr.get("reason"),
            "territorial_action": t_action,
            "territorial_candidate": t_candidate,
            "electoral_source": electoral.get("source"),
            "electoral_granularity": electoral.get("granularity"),
            "electoral_action": e_action,
            "electoral_candidate": e_candidate,
            "definitive_gap": {
                k: v for k, v in electoral.items()
                if k.startswith("definitive_") or k.endswith("_candidate_votes")
            },
            "blocked": e_action.startswith("BLOCKED"),
            "block_reason": e_candidate.get("reason") if e_action.startswith("BLOCKED") else None,
        })
    return {
        "schema": "ddd-current-legislature-preparation-plan/1.0",
        "project_edition": edition,
        "as_of": matrix.get("as_of"),
        "plans": plans,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root-dir", type=Path, default=Path("."))
    ap.add_argument("--territory", default="Todos")
    ap.add_argument("--output", type=Path)
    args = ap.parse_args()
    try:
        result = resolve(args.root_dir, args.territory)
    except Exception as exc:
        print(json.dumps({"ok": False, "error": f"{type(exc).__name__}: {exc}"}, ensure_ascii=False))
        return 2
    payload = json.dumps({"ok": True, **result}, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload, encoding="utf-8")
    else:
        print(payload, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
