#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from herramientas.identidad_fuentes_legislatura import (
    canonical_sha256,
    digest,
    electoral_identity,
)
from herramientas.resolver_preparacion_legislatura import resolve

PAIR_SCHEMA = "ddd.prepared-source-pair/1.0"
REMOTE_SCHEMA = "ddd.prepared-source-pair-artifact-verification/1.0"


class PreparedSourcePairBlock(ValueError):
    pass


def _json(path: Path) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise PreparedSourcePairBlock(f"PAIR_BLOCK: JSON ilegible: {path}") from exc
    if not isinstance(data, dict):
        raise PreparedSourcePairBlock(f"PAIR_BLOCK: JSON no objeto: {path}")
    return data


def _verify_remote(candidate: dict, observed: dict, *, label: str) -> dict:
    if not isinstance(observed, dict):
        raise PreparedSourcePairBlock(f"PAIR_BLOCK: falta verificación remota de {label}")
    expected_run = candidate.get("run_id")
    expected_name = str(candidate.get("artifact_name") or "")
    expected_digest = digest(candidate.get("artifact_sha256"), label=f"{label}.artifact_sha256")
    if (
        int(observed.get("run_id") or 0) != int(expected_run or 0)
        or str(observed.get("artifact_name") or "") != expected_name
        or digest(observed.get("artifact_sha256"), label=f"{label}.remote.artifact_sha256") != expected_digest
        or observed.get("expired") is not False
        or not isinstance(observed.get("artifact_id"), int)
        or int(observed.get("artifact_id")) <= 0
    ):
        raise PreparedSourcePairBlock(f"PAIR_BLOCK: verificación remota contradictoria de {label}")
    return {
        "run_id": int(expected_run),
        "artifact_id": int(observed["artifact_id"]),
        "artifact_name": expected_name,
        "artifact_sha256": expected_digest,
        "expired": False,
    }


def build_pair(
    *,
    root_dir: Path,
    territory: str,
    remote_verification: dict,
) -> dict:
    root = root_dir.resolve()
    plan_doc = resolve(root, territory)
    plans = plan_doc.get("plans") or []
    if len(plans) != 1:
        raise PreparedSourcePairBlock("PAIR_BLOCK: el registro exige un territorio único")
    plan = plans[0]
    if plan.get("territorial_action") not in {"REUSE", "REUSE_TEMPORAL_SUBSTITUTION"}:
        raise PreparedSourcePairBlock(
            f"PAIR_BLOCK: fuente territorial efectiva no acreditada: {plan.get('territorial_action')}"
        )
    if plan.get("electoral_action") != "REUSE":
        raise PreparedSourcePairBlock(
            f"PAIR_BLOCK: fuente electoral efectiva no acreditada: {plan.get('electoral_action')}"
        )

    territorial = plan.get("territorial_candidate") or {}
    electoral = plan.get("electoral_candidate") or {}
    territorial_identity_sha = digest(
        territorial.get("territorial_identity_sha256"),
        label="territorial.territorial_identity_sha256",
    )
    election_id = str(plan.get("election_id") or "")
    election_date = str(plan.get("election_date") or "")
    electoral_id = electoral_identity(
        territory_id=str(plan["territory_id"]),
        edition=str(plan["project_edition"]),
        election_id=election_id,
        election_date=election_date,
        artifact_sha256=str(electoral.get("artifact_sha256") or ""),
    )
    electoral_identity_sha = electoral_id["electoral_identity_sha256"]

    if remote_verification.get("schema") != REMOTE_SCHEMA:
        raise PreparedSourcePairBlock("PAIR_BLOCK: schema de verificación remota no reconocido")
    remote_territorial = _verify_remote(
        territorial,
        remote_verification.get("territorial"),
        label="territorial",
    )
    remote_electoral = _verify_remote(
        electoral,
        remote_verification.get("electoral"),
        label="electoral",
    )

    temporal = plan.get("temporal_evidence") or {}
    temporal_path = root / str(temporal.get("path") or "")
    if not temporal_path.is_file():
        raise PreparedSourcePairBlock("PAIR_BLOCK: evidencia temporal durable ausente")
    temporal_sha = digest(temporal.get("sha256"), label="temporal_evidence.sha256")
    import hashlib
    actual_temporal_sha = hashlib.sha256(temporal_path.read_bytes()).hexdigest()
    if actual_temporal_sha != temporal_sha:
        raise PreparedSourcePairBlock("PAIR_BLOCK: evidencia temporal cambió después de planificar")

    canonical = {
        "territory_id": str(plan["territory_id"]),
        "edition": str(plan["project_edition"]),
        "election_id": election_id,
        "election_date": election_date,
        "population_year": int(plan["population_year_selected"]),
        "population_reference_date": str(plan["population_reference_date"]),
        "section_year": int(plan["section_year_selected"]),
        "section_reference_label": str(plan["section_reference_label"]),
        "temporal_evidence_sha256": temporal_sha,
        "territorial_identity_sha256": territorial_identity_sha,
        "electoral_identity_sha256": electoral_identity_sha,
    }
    pair_sha = canonical_sha256(canonical)
    return {
        "schema": PAIR_SCHEMA,
        "territory_id": str(plan["territory_id"]),
        "territory_name": str(plan["name"]),
        "edition": str(plan["project_edition"]),
        "election": {
            "election_id": election_id,
            "election_date": election_date,
        },
        "references": {
            "population": {
                "required_year": int(plan["population_year_required"]),
                "year": int(plan["population_year_selected"]),
                "reference_date": str(plan["population_reference_date"]),
            },
            "sectioning": {
                "required_year": int(plan["section_year_required"]),
                "year": int(plan["section_year_selected"]),
                "reference_label": str(plan["section_reference_label"]),
            },
        },
        "temporal_evidence": {
            "path": str(temporal["path"]),
            "sha256": temporal_sha,
            "provider": str(temporal.get("provider") or ""),
            "checked_at": str(temporal.get("checked_at") or ""),
        },
        "territorial_source": {
            "run_id": int(territorial["run_id"]),
            "artifact_name": str(territorial["artifact_name"]),
            "artifact_sha256": digest(
                territorial.get("artifact_sha256"),
                label="territorial.artifact_sha256",
            ),
            "package_sha256": digest(
                territorial.get("package_sha256"),
                label="territorial.package_sha256",
            ),
            "source_commit": territorial.get("source_commit"),
            "source_declaration": territorial.get("declaration"),
            "receipt_path": territorial.get("receipt_path"),
            "population_year": int(plan["population_year_selected"]),
            "section_year": int(plan["section_year_selected"]),
            "territorial_identity_sha256": territorial_identity_sha,
            "remote_verification": remote_territorial,
        },
        "electoral_source": {
            "run_id": int(electoral["run_id"]),
            "artifact_name": str(electoral["artifact_name"]),
            "artifact_sha256": digest(
                electoral.get("artifact_sha256"),
                label="electoral.artifact_sha256",
            ),
            "source_commit": electoral.get("source_commit"),
            "receipt_path": electoral.get("receipt"),
            "provenance_reference": electoral.get("provenance_reference"),
            "election_id": election_id,
            "election_date": election_date,
            "electoral_identity_sha256": electoral_identity_sha,
            "remote_verification": remote_electoral,
        },
        "geometric_compatibility_key": territorial_identity_sha,
        "electoral_compatibility_key": electoral_identity_sha,
        "pair_sha256": pair_sha,
    }


def _state_bounds(lines: list[str], territory_id: str, edition: str) -> tuple[int, int, str]:
    territory_re = re.compile(rf"^(?P<indent>\s*)-\s+territory_id:\s*{re.escape(territory_id)}\s*$")
    found = next(((i, m) for i, line in enumerate(lines) if (m := territory_re.match(line))), None)
    if found is None:
        raise PreparedSourcePairBlock(f"PAIR_BLOCK: territorio no registrado: {territory_id}")
    t0, match = found
    territory_indent = match.group("indent")
    next_territory = re.compile(rf"^{re.escape(territory_indent)}-\s+territory_id:")
    t1 = next((i for i in range(t0 + 1, len(lines)) if next_territory.match(lines[i])), len(lines))
    edition_re = re.compile(rf"^(?P<indent>\s*)['\"]?{re.escape(edition)}['\"]?:\s*$")
    found_edition = next(
        ((i, m) for i in range(t0, t1) if (m := edition_re.match(lines[i]))),
        None,
    )
    if found_edition is None:
        raise PreparedSourcePairBlock(f"PAIR_BLOCK: edición no registrada: {territory_id}/{edition}")
    e0, em = found_edition
    edition_indent = em.group("indent")
    next_edition = re.compile(rf"^{re.escape(edition_indent)}['\"]?\d{{4}}['\"]?:\s*$")
    e1 = next((i for i in range(e0 + 1, t1) if next_edition.match(lines[i])), t1)
    state_indent = edition_indent + "  "
    return e0 + 1, e1, state_indent


def _set_pair_pointer(catalog_path: Path, *, territory_id: str, edition: str, pair_rel: str) -> None:
    lines = catalog_path.read_text(encoding="utf-8").splitlines()
    start, end, state_indent = _state_bounds(lines, territory_id, edition)
    evidence_line = next(
        (i for i in range(start, end) if lines[i].startswith(state_indent + "evidence:")),
        None,
    )
    child_indent = state_indent + "  "
    if evidence_line is None:
        evidence_line = end
        lines.insert(evidence_line, state_indent + "evidence:")
        end += 1
    ev_end = evidence_line + 1
    while ev_end < len(lines) and (
        lines[ev_end].startswith(child_indent) or not lines[ev_end].strip()
    ):
        ev_end += 1
    prefix = child_indent + "prepared_source_pair:"
    existing = next((i for i in range(evidence_line + 1, ev_end) if lines[i].startswith(prefix)), None)
    if existing is None:
        lines.insert(ev_end, f"{prefix} {pair_rel}")
    else:
        lines[existing] = f"{prefix} {pair_rel}"
    catalog_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def register_pair(
    *,
    root_dir: Path,
    territory: str,
    remote_verification_path: Path,
    verify_only: bool = False,
) -> dict:
    root = root_dir.resolve()
    remote = _json(remote_verification_path)
    pair = build_pair(root_dir=root, territory=territory, remote_verification=remote)
    pair_path = (
        root
        / "territorios"
        / pair["territory_id"]
        / "evidencia"
        / "pares_fuentes"
        / pair["edition"]
        / f"{pair['pair_sha256']}.json"
    )
    rendered = json.dumps(pair, ensure_ascii=False, indent=2) + "\n"
    if verify_only:
        if not pair_path.is_file() or pair_path.read_text(encoding="utf-8") != rendered:
            raise PreparedSourcePairBlock("PAIR_BLOCK: par durable efectivo ausente o contradictorio")
        return {**pair, "receipt_path": pair_path.relative_to(root).as_posix()}

    pair_path.parent.mkdir(parents=True, exist_ok=True)
    if pair_path.exists() and pair_path.read_text(encoding="utf-8") != rendered:
        raise PreparedSourcePairBlock("PAIR_BLOCK: hash de par existente con contenido contradictorio")
    pair_path.write_text(rendered, encoding="utf-8")
    pair_rel = pair_path.relative_to(root).as_posix()
    _set_pair_pointer(
        root / "configuracion/catalogo_preparacion.yaml",
        territory_id=pair["territory_id"],
        edition=pair["edition"],
        pair_rel=pair_rel,
    )
    return {**pair, "receipt_path": pair_rel}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root-dir", type=Path, default=Path("."))
    ap.add_argument("--territory", required=True)
    ap.add_argument("--remote-verification", required=True, type=Path)
    ap.add_argument("--verify-only", action="store_true")
    ap.add_argument("--output", type=Path)
    args = ap.parse_args()
    try:
        result = register_pair(
            root_dir=args.root_dir,
            territory=args.territory,
            remote_verification_path=args.remote_verification,
            verify_only=args.verify_only,
        )
    except Exception as exc:
        payload = {"decision": "BLOCKED", "reason": str(exc)}
        print(json.dumps(payload, ensure_ascii=False))
        return 2
    payload = {"decision": "READY", **result}
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
