#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

try:
    from herramientas.catalogo_preparacion import validate_repository
    from herramientas.persistir_estado_operativo_compartido import persist_rederived_tree
    from herramientas.identidad_fuentes_legislatura import (
        canonical_sha256,
        digest,
        electoral_identity,
        geometric_reuse_compatible,
        territorial_identity,
    )
    from herramientas.resolver_preparacion_legislatura import resolve
except ModuleNotFoundError:  # ejecución directa: python herramientas/...
    from catalogo_preparacion import validate_repository
    from persistir_estado_operativo_compartido import persist_rederived_tree
    from identidad_fuentes_legislatura import (
        canonical_sha256,
        digest,
        electoral_identity,
        geometric_reuse_compatible,
        territorial_identity,
    )
    from resolver_preparacion_legislatura import resolve

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


def _historical_product_reuse(root: Path, *, plan: dict, current_identity: str) -> dict:
    import yaml
    catalog = yaml.safe_load((root / "configuracion/catalogo_preparacion.yaml").read_text(encoding="utf-8")) or {}
    row = next(
        (r for r in catalog.get("territories") or [] if r.get("territory_id") == plan["territory_id"]),
        None,
    )
    state = ((row or {}).get("editions") or {}).get(str(plan["project_edition"])) or {}
    if not state.get("territorial_product_available"):
        return {"available": False, "geometric_reuse_compatible": False, "reason": "NO_TERRITORIAL_PRODUCT"}
    evidence = state.get("evidence") or {}
    product_rel = str(evidence.get("territorial_product") or "")
    lineage_rel = str(evidence.get("territorial_product_source_lineage") or "")
    if not product_rel or not (root / product_rel).is_file():
        return {"available": True, "geometric_reuse_compatible": False, "reason": "PRODUCT_RECEIPT_MISSING"}
    product = _json(root / product_rel)
    if not lineage_rel or not (root / lineage_rel).is_file():
        return {
            "available": True,
            "geometric_reuse_compatible": False,
            "reason": "PRODUCT_SOURCE_LINEAGE_MISSING",
            "product_receipt_path": product_rel,
        }
    lineage = _json(root / lineage_rel)
    if (
        lineage.get("schema") != "ddd.territorial-product-source-lineage/1.0"
        or str(lineage.get("territory_id") or "") != str(plan["territory_id"])
    ):
        return {
            "available": True,
            "geometric_reuse_compatible": False,
            "reason": "PRODUCT_SOURCE_LINEAGE_INVALID",
            "product_receipt_path": product_rel,
            "lineage_path": lineage_rel,
        }
    source_identity = str((lineage.get("territorial_source") or {}).get("territorial_identity_sha256") or "")
    try:
        compatible = geometric_reuse_compatible(
            product_territorial_identity_sha256=source_identity,
            current_territorial_identity_sha256=current_identity,
        )
    except Exception:
        compatible = False
    return {
        "available": True,
        "geometric_reuse_compatible": bool(compatible),
        "reason": "SOURCE_IDENTITY_MATCH" if compatible else "SOURCE_IDENTITY_MISMATCH",
        "product_receipt_path": product_rel,
        "lineage_path": lineage_rel,
        "product_run_id": product.get("run_id"),
        "product_artifact_name": product.get("artifact_name"),
        "product_artifact_sha256": product.get("artifact_sha256"),
        "product_source_territorial_identity_sha256": source_identity or None,
        "current_territorial_identity_sha256": current_identity,
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
        "territorial_run_id": int(territorial["run_id"]),
        "territorial_artifact_sha256": digest(
            territorial.get("artifact_sha256"),
            label="territorial.artifact_sha256",
        ),
        "compatibility_report_sha256": digest(
            territorial.get("compatibility_report_sha256"),
            label="territorial.compatibility_report_sha256",
        ),
        "compatibility_identity_sha256": digest(
            territorial.get("compatibility_identity_sha256"),
            label="territorial.compatibility_identity_sha256",
        ),
        "electoral_identity_sha256": electoral_identity_sha,
        "electoral_run_id": int(electoral["run_id"]),
        "electoral_artifact_sha256": digest(
            electoral.get("artifact_sha256"),
            label="electoral.artifact_sha256",
        ),
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
            "compatibility_report_member": territorial.get("compatibility_report_member"),
            "compatibility_report_sha256": digest(
                territorial.get("compatibility_report_sha256"),
                label="territorial.compatibility_report_sha256",
            ),
            "compatibility_identity_sha256": digest(
                territorial.get("compatibility_identity_sha256"),
                label="territorial.compatibility_identity_sha256",
            ),
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
        "territorial_product_reuse": _historical_product_reuse(
            root,
            plan=plan,
            current_identity=territorial_identity_sha,
        ),
        "pair_sha256": pair_sha,
    }



def validate_pair_receipt(
    *,
    root_dir: Path,
    pair_path: Path,
    expected_territory_id: str | None = None,
    expected_edition: str | None = None,
) -> dict:
    """Valida un receipt ya registrado sin reconstruirlo desde la matriz de preparación."""
    root = root_dir.resolve()
    path = pair_path if pair_path.is_absolute() else root / pair_path
    pair = _json(path)
    if pair.get("schema") != PAIR_SCHEMA:
        raise PreparedSourcePairBlock("PAIR_BLOCK: schema de par preparado no reconocido")

    territory_id = str(pair.get("territory_id") or "")
    edition = str(pair.get("edition") or "")
    if not territory_id or not edition:
        raise PreparedSourcePairBlock("PAIR_BLOCK: identidad territorial/edición incompleta")
    if expected_territory_id is not None and territory_id != str(expected_territory_id):
        raise PreparedSourcePairBlock("PAIR_BLOCK: territorio del par no coincide")
    if expected_edition is not None and edition != str(expected_edition):
        raise PreparedSourcePairBlock("PAIR_BLOCK: edición del par no coincide")

    election = pair.get("election") or {}
    references = pair.get("references") or {}
    population = references.get("population") or {}
    sectioning = references.get("sectioning") or {}
    temporal = pair.get("temporal_evidence") or {}
    territorial = pair.get("territorial_source") or {}
    electoral = pair.get("electoral_source") or {}

    temporal_rel = str(temporal.get("path") or "")
    temporal_path = root / temporal_rel if temporal_rel else None
    if temporal_path is None or not temporal_path.is_file():
        raise PreparedSourcePairBlock("PAIR_BLOCK: evidencia temporal durable ausente")
    temporal_sha = digest(temporal.get("sha256"), label="temporal_evidence.sha256")
    import hashlib
    if hashlib.sha256(temporal_path.read_bytes()).hexdigest() != temporal_sha:
        raise PreparedSourcePairBlock("PAIR_BLOCK: evidencia temporal durable no coincide con el receipt")

    territorial_id = territorial_identity(
        territory_id=territory_id,
        edition=edition,
        population_year=int(population.get("year")),
        section_year=int(sectioning.get("year")),
        package_sha256=str(territorial.get("package_sha256") or ""),
        compatibility_identity_sha256=str(territorial.get("compatibility_identity_sha256") or ""),
    )
    if territorial_id["territorial_identity_sha256"] != str(territorial.get("territorial_identity_sha256") or ""):
        raise PreparedSourcePairBlock("PAIR_BLOCK: identidad territorial del receipt no reconcilia")
    if str(pair.get("geometric_compatibility_key") or "") != territorial_id["territorial_identity_sha256"]:
        raise PreparedSourcePairBlock("PAIR_BLOCK: clave geométrica no coincide con la identidad territorial acreditada")

    electoral_id = electoral_identity(
        territory_id=territory_id,
        edition=edition,
        election_id=str(election.get("election_id") or ""),
        election_date=str(election.get("election_date") or ""),
        artifact_sha256=str(electoral.get("artifact_sha256") or ""),
    )
    if electoral_id["electoral_identity_sha256"] != str(electoral.get("electoral_identity_sha256") or ""):
        raise PreparedSourcePairBlock("PAIR_BLOCK: identidad electoral del receipt no reconcilia")
    if str(pair.get("electoral_compatibility_key") or "") != electoral_id["electoral_identity_sha256"]:
        raise PreparedSourcePairBlock("PAIR_BLOCK: clave electoral no coincide con la identidad acreditada")

    def verify_side_receipt(side: dict, *, label: str) -> dict:
        rel = str(side.get("receipt_path") or "")
        if not rel:
            raise PreparedSourcePairBlock(f"PAIR_BLOCK: falta receipt durable de {label}")
        side_path = root / rel
        receipt = _json(side_path)
        if str(receipt.get("territory_id") or "") != territory_id:
            raise PreparedSourcePairBlock(f"PAIR_BLOCK: receipt de {label} contradice territory_id")
        if str(receipt.get("edition") or "") != edition:
            raise PreparedSourcePairBlock(f"PAIR_BLOCK: receipt de {label} contradice edition")
        for key in ("run_id", "artifact_name", "artifact_sha256"):
            if str(receipt.get(key) or "") != str(side.get(key) or ""):
                raise PreparedSourcePairBlock(f"PAIR_BLOCK: receipt de {label} contradice {key}")
        remote = side.get("remote_verification") or {}
        if (
            int(remote.get("run_id") or 0) != int(side.get("run_id") or 0)
            or str(remote.get("artifact_name") or "") != str(side.get("artifact_name") or "")
            or digest(remote.get("artifact_sha256"), label=f"{label}.remote.artifact_sha256")
            != digest(side.get("artifact_sha256"), label=f"{label}.artifact_sha256")
            or remote.get("expired") is not False
            or not isinstance(remote.get("artifact_id"), int)
            or int(remote.get("artifact_id")) <= 0
        ):
            raise PreparedSourcePairBlock(f"PAIR_BLOCK: verificación remota durable de {label} no reconcilia")
        return receipt

    territorial_receipt = verify_side_receipt(territorial, label="territorial")
    if territorial_receipt.get("schema") != "ddd.territorial-source-receipt/1.0":
        raise PreparedSourcePairBlock("PAIR_BLOCK: schema de receipt territorial no reconocido")
    for key in ("package_sha256", "territorial_identity_sha256"):
        if str(territorial_receipt.get(key) or "") != str(territorial.get(key) or ""):
            raise PreparedSourcePairBlock(f"PAIR_BLOCK: receipt territorial contradice {key}")

    electoral_receipt = verify_side_receipt(electoral, label="electoral")
    if str(electoral_receipt.get("election_id") or "") != str(election.get("election_id") or ""):
        raise PreparedSourcePairBlock("PAIR_BLOCK: receipt electoral contradice election_id")
    receipt_date = str(electoral_receipt.get("election_date") or "")
    if receipt_date and receipt_date != str(election.get("election_date") or ""):
        raise PreparedSourcePairBlock("PAIR_BLOCK: receipt electoral contradice election_date")

    canonical = {
        "territory_id": territory_id,
        "edition": edition,
        "election_id": str(election.get("election_id") or ""),
        "election_date": str(election.get("election_date") or ""),
        "population_year": int(population.get("year")),
        "population_reference_date": str(population.get("reference_date") or ""),
        "section_year": int(sectioning.get("year")),
        "section_reference_label": str(sectioning.get("reference_label") or ""),
        "temporal_evidence_sha256": temporal_sha,
        "territorial_identity_sha256": territorial_id["territorial_identity_sha256"],
        "territorial_run_id": int(territorial.get("run_id")),
        "territorial_artifact_sha256": digest(
            territorial.get("artifact_sha256"), label="territorial.artifact_sha256"
        ),
        "compatibility_report_sha256": digest(
            territorial.get("compatibility_report_sha256"),
            label="territorial.compatibility_report_sha256",
        ),
        "compatibility_identity_sha256": digest(
            territorial.get("compatibility_identity_sha256"),
            label="territorial.compatibility_identity_sha256",
        ),
        "electoral_identity_sha256": electoral_id["electoral_identity_sha256"],
        "electoral_run_id": int(electoral.get("run_id")),
        "electoral_artifact_sha256": digest(
            electoral.get("artifact_sha256"), label="electoral.artifact_sha256"
        ),
    }
    if canonical_sha256(canonical) != str(pair.get("pair_sha256") or ""):
        raise PreparedSourcePairBlock("PAIR_BLOCK: pair_sha256 no reconcilia con el receipt")

    return pair


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




def persist_pair(
    *,
    root_dir: Path,
    territory: str,
    remote_verification_path: Path,
    target_branch: str,
    max_attempts: int = 4,
) -> dict:
    """Persiste el par preparado rederivándolo desde el HEAD remoto vigente."""
    root = root_dir.resolve()
    frozen_remote = (
        remote_verification_path
        if remote_verification_path.is_absolute()
        else root / remote_verification_path
    )
    initial = build_pair(
        root_dir=root,
        territory=territory,
        remote_verification=_json(frozen_remote),
    )
    territory_id = str(initial["territory_id"])
    result_box: dict[str, dict] = {}

    def apply(current_root: Path, _attempt: int) -> None:
        result_box["pair"] = register_pair(
            root_dir=current_root,
            territory=territory,
            remote_verification_path=frozen_remote,
            verify_only=False,
        )

    def validate(current_root: Path) -> None:
        errors = validate_repository(root_dir=current_root)
        if errors:
            raise PreparedSourcePairBlock(
                "PAIR_BLOCK: registro deja repositorio inválido: "
                + "; ".join(errors[:8])
            )

    persisted = persist_rederived_tree(
        root_dir=root,
        target_branch=target_branch,
        paths=(
            "configuracion/catalogo_preparacion.yaml",
            f"territorios/{territory_id}/evidencia/pares_fuentes",
        ),
        commit_message=f"chore: registrar par preparado de {territory_id}",
        apply=apply,
        validate=validate,
        max_attempts=max_attempts,
        exhausted_message=(
            f"No se pudo registrar el par preparado de {territory_id} tras "
            f"{max_attempts} rederivaciones desde el HEAD vigente"
        ),
    )
    pair = dict(result_box.get("pair") or {})
    pair["promotion_sha"] = persisted.head_sha
    pair["persistence_attempt"] = persisted.attempt
    pair["persistence_changed"] = persisted.changed
    return pair

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root-dir", type=Path, default=Path("."))
    ap.add_argument("--territory", required=True)
    ap.add_argument("--remote-verification", required=True, type=Path)
    ap.add_argument("--verify-only", action="store_true")
    ap.add_argument("--persist", action="store_true")
    ap.add_argument("--target-branch", default="main")
    ap.add_argument("--max-attempts", type=int, default=4)
    ap.add_argument("--output", type=Path)
    args = ap.parse_args()
    try:
        if args.persist and args.verify_only:
            raise PreparedSourcePairBlock("PAIR_BLOCK: --persist y --verify-only son incompatibles")
        result = (
            persist_pair(
                root_dir=args.root_dir,
                territory=args.territory,
                remote_verification_path=args.remote_verification,
                target_branch=args.target_branch,
                max_attempts=args.max_attempts,
            )
            if args.persist
            else register_pair(
                root_dir=args.root_dir,
                territory=args.territory,
                remote_verification_path=args.remote_verification,
                verify_only=args.verify_only,
            )
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
