#!/usr/bin/env python3
# Versión: 1.1.4; nombre: Puertas derivadas F10; fecha: 2026-10-29.
# Alcance: validar fichas READ_ONLY y evidencias de actividades F10.
# Estado: candidato. Cambios/motivo: un receipt territorial posterior hereda el cierre F10 si
# conserva los años de población y seccionado; la re-descarga INE del mismo año desde el principio
# trae otra huella de paquete y dejaba la adquisición en BLOCKED sin cambiar de fuente.
# Anterior: legacy/herramientas/estado_derivado_f10_v1.1.3_20261029.py.
"""Read-only F10 door projection from current receipts and canonical consumers.

The closure dossier is cross-checked as a tracking record; it never grants PASS.
Territorial receipt and joint-pair decisions come from the source consumers.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
from typing import Any

import yaml


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"JSON no es objeto: {path}")
    return value


def _yaml(path: Path) -> dict[str, Any]:
    value = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(value, dict):
        raise ValueError(f"YAML no es objeto: {path}")
    return value


def _receipt_reference(state: dict[str, Any]) -> str | None:
    independent = state.get("independent_source_evidence") or {}
    historical = state.get("preparation_evidence") or {}
    # Independent receipts stay independent; never rewrite historical lineage.
    return independent.get("receipt_path") or historical.get("receipt_path")


def _geometric_admissibility(
    root: Path, state: dict[str, Any], receipt: dict[str, Any], fallback: str
) -> tuple[str, list[str], str | None]:
    """Validate optional F10 geometry evidence separately from source acquisition.

    A valid #179 receipt closes acquisition. It does not, by itself, prove that
    an M02 contract was applicable to the receipt's source edition.
    """
    independent = state.get("independent_source_evidence") or {}
    path_value = independent.get("geometry_assessment_path")
    digest_value = independent.get("geometry_assessment_sha256")
    declared_status = independent.get("geometry_admissibility")
    if path_value is None and digest_value is None and declared_status is None:
        return fallback, [], None
    rel = str(path_value or "")
    if not rel or Path(rel).is_absolute():
        return "BLOCKED", ["GEOMETRY_ASSESSMENT_PATH_INVALID"], rel or None
    path = root / rel
    if not path.is_file() or sha256(path) != str(digest_value or ""):
        return "BLOCKED", ["GEOMETRY_ASSESSMENT_HASH_MISMATCH"], rel
    try:
        report = _json(path)
    except Exception:
        return "BLOCKED", ["GEOMETRY_ASSESSMENT_UNREADABLE"], rel
    expected = {
        "schema": "ddd.f10-valencia-2023-m02-contract-applicability/1.0",
        "territory_id": "comunidad_valenciana",
        "population_year": receipt.get("population_year"),
        "section_year": receipt.get("section_year"),
        "package_sha256": receipt.get("package_sha256"),
    }
    if any(report.get(key) != value for key, value in expected.items()):
        return "BLOCKED", ["GEOMETRY_ASSESSMENT_IDENTITY_MISMATCH"], rel
    if (
        receipt.get("geometry_assessment_path") != rel
        or receipt.get("geometry_assessment_sha256") != str(digest_value)
        or receipt.get("geometry_admissibility") != declared_status
    ):
        return "BLOCKED", ["GEOMETRY_ASSESSMENT_RECEIPT_MISMATCH"], rel
    decision = str(report.get("decision") or "")
    reason = str(report.get("reason") or "")
    if (
        decision == "PASS"
        and declared_status == "PASS"
        and report.get("contract_binding") == "BOUND_TO_SOURCE_EDITION"
        and (report.get("execution") or {}).get("pairs_over_threshold") == 0
    ):
        return "PASS", [], rel
    if decision == "BLOCKED" and declared_status == "BLOCKED" and reason:
        return "BLOCKED", [reason], rel
    return "BLOCKED", ["GEOMETRY_ASSESSMENT_NOT_ADMISSIBLE"], rel


def check_territorial_evidence(receipt: dict[str, Any], *, territory_id: str,
                               receipt_path: str, receipt_sha256: str,
                               dossier_row: dict[str, Any]) -> None:
    """Reject receipt/hash/identity/temporal contradictions with the tracking record."""
    if receipt.get("territory_id") != territory_id or str(receipt.get("edition")) != "2025":
        raise ValueError("receipt territorial con identidad/edición errónea")
    if type(receipt.get("population_year")) is not int or type(receipt.get("section_year")) is not int:
        raise ValueError("receipt territorial sin años poblacionales/seccionales íntegros")
    package_keys = (
        "package_sha256", "population_year", "section_year",
        "territorial_identity_sha256", "compatibility_report_sha256", "compatibility_identity_sha256",
    )
    if dossier_row.get("receipt_path") == receipt_path:
        if dossier_row.get("receipt_sha256") != receipt_sha256:
            raise ValueError("matriz de seguimiento contradice receipt_sha256")
        keys = ("run_id", "artifact_sha256", *package_keys)
    else:
        # Cada reutilización o re-descarga registra el paquete con su run y artefacto propios.
        # Un receipt posterior hereda el cierre F10 si conserva la edición y los años de
        # población y seccionado: la re-descarga INE del mismo año puede traer otra huella
        # (paquete, identidad, compatibilidad) sin cambiar de fuente. Otro año exige auditoría.
        if not all(dossier_row.get(key) not in (None, "") for key in package_keys):
            raise ValueError("matriz de seguimiento contradice receipt_path")
        try:
            newer = int(receipt.get("run_id")) > int(dossier_row.get("run_id"))
        except (TypeError, ValueError):
            newer = False
        if not newer:
            raise ValueError("matriz de seguimiento contradice receipt_path")
        keys = ("population_year", "section_year")
    for key in keys:
        expected = dossier_row.get(key)
        if expected not in (None, "") and str(receipt.get(key)) != str(expected):
            raise ValueError(f"matriz de seguimiento contradice receipt.{key}")
    if dossier_row.get("territorial_acquisition") != "CLOSED":
        raise ValueError("matriz de seguimiento contradice receipt territorial válido")


def _electoral_identity(receipt: dict[str, Any], *, election_id: str, election_date: str) -> str:
    from herramientas.identidad_fuentes_legislatura import electoral_identity

    expected = electoral_identity(
        territory_id=str(receipt.get("territory_id") or ""),
        edition=str(receipt.get("edition") or ""),
        election_id=election_id,
        election_date=election_date,
        artifact_sha256=str(receipt.get("artifact_sha256") or ""),
    )
    recorded = str(receipt.get("electoral_identity_sha256") or "")
    if recorded and expected["electoral_identity_sha256"] != recorded:
        raise ValueError("electoral_identity_sha256 no reconcilia")
    return expected["electoral_identity_sha256"]


def _status_counts(rows: list[dict[str, Any]], key: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        status = str(row[key])
        counts[status] = counts.get(status, 0) + 1
    return dict(sorted(counts.items()))


DEFAULT_ACTIVITIES = (
    ("F10-AND-CROSSWALK-2025-2026", "andalucia", "research_official_2025_2026_crosswalk", "CLOSED"),
    ("F10-ARA-CROSSWALK-2025-2026", "aragon", "research_official_2025_2026_crosswalk", "CLOSED"),
    ("F10-CYL-CROSSWALK-2025-2026", "castilla_y_leon", "research_official_2025_2026_crosswalk", "CLOSED"),
    ("F10-EXT-ELECTORAL-SOURCE", "extremadura", "research_definitive_granular_election_source", "CLOSED"),
    ("F10-CV-2023-SOURCE-RESOLUTION", "comunidad_valenciana", "resolve_2023_population_geometry_blocker", "BLOCKED"),
)


def work_items_for(rows: list[dict[str, Any]], activity_authorizations: dict[str, list[str]],
                   activities: list[dict[str, Any]] | None = None) -> list[dict[str, Any]]:
    """Compute independent local work readiness; this does not grant execution authority."""
    authorized = set(activity_authorizations.get("local_read_only", []))
    definitions = activities or [
        {"id": item_id, "territory_id": territory_id, "action": action,
         "requires": [{"door": "territorial_acquisition", "state": required_state}],
         "required_actions": ["investigation"], "task_spec_registered": False}
        for item_id, territory_id, action, required_state in DEFAULT_ACTIVITIES
    ]
    by_id = {row["territory_id"]: row for row in rows}
    work_items = []
    for activity in definitions:
        territory_id = str(activity["territory_id"])
        requirements = activity.get("requires") or []
        door_states = {str(req["door"]): str(req["state"]) for req in requirements}
        actual_states = {"territorial_acquisition": by_id[territory_id]["territorial_acquisition"]}
        dependencies_met = bool(door_states) and all(actual_states.get(door) == state for door, state in door_states.items())
        permitted = set(activity.get("required_actions") or []) <= authorized
        # Valencia's already-exhausted local research remains parked until genuinely new evidence arrives.
        spec_error = activity.get("task_spec_error")
        owner_wait = bool(activity.get("wait_reason")) or bool(spec_error)
        ready = dependencies_met and permitted and not owner_wait
        work_items.append({
            "activity_id": activity["id"],
            "territory_id": territory_id,
            "action": activity["action"],
            "state": "READY_LOCAL" if ready else "WAIT_OWNER",
            "requires_doors": door_states,
            "door_states": actual_states,
            "authorization_class": activity.get("authorization_class", "local_read_only"),
            "authorized_actions": sorted(authorized),
            "execution_engine": "ddd auto",
            "task_spec_registered": bool(activity.get("task_spec_registered")),
            "selectable": bool(activity.get("task_spec_registered")) and ready,
            "reason": (
                str(spec_error) if spec_error else
                "Puertas independientes satisfechas; la actividad puede continuar aunque F10 global siga PENDING"
                if ready else str(activity.get("wait_reason") or "La puerta de entrada no está acreditada o la clase local no cubre la acción")
            ),
            "task_spec_error": spec_error,
        })
    return work_items


def replay_snapshots(validated_rows: list[dict[str, Any]], snapshots: dict[str, list[str]],
                     activity_authorizations: dict[str, list[str]],
                     activities: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    """Replay receipt arrivals against already validated facts, for local regression fixtures."""
    result = {}
    for name, included in snapshots.items():
        included_ids = set(included)
        rows = []
        for original in validated_rows:
            row = dict(original)
            if row["territorial_acquisition"] == "CLOSED" and row["territory_id"] not in included_ids:
                row["territorial_acquisition"] = "BLOCKED"
            row["joint_admissibility"] = (
                "PASS" if row["territorial_acquisition"] == "CLOSED" and original["joint_admissibility"] == "PASS" else "BLOCKED"
            )
            rows.append(row)
        result[name] = {
            "counts": {
                "territorial_acquisition": _status_counts(rows, "territorial_acquisition"),
                "electoral_admissibility": _status_counts(rows, "electoral_admissibility"),
                "joint_admissibility": _status_counts(rows, "joint_admissibility"),
                "production": {"NOT_AUTHORIZED_BY_F10": len(rows)},
            },
            "work_items": work_items_for(rows, activity_authorizations, activities),
        }
    return result


def derive_f10(root_dir: Path, *, activity_authorizations: dict[str, list[str]] | None = None,
               plan_root: Path | None = None) -> dict[str, Any]:
    """Derive independent F10 doors; performs reads and canonical local validation only."""
    root = root_dir.resolve()
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    from herramientas import catalogo_preparacion
    from herramientas.consumir_par_fuentes_legislatura import (
        resolve_pair,
        validate_territorial_receipt,
    )
    from herramientas.identidad_fuentes_legislatura import electoral_identity

    catalog_path = root / "configuracion/catalogo_preparacion.yaml"
    prep_path = root / "configuracion/preparacion_legislatura_vigente.yaml"
    matrix_path = root / "docs/AUDITORIAS/F10_CIERRE_TERRITORIAL_20261012/matriz_nacional_19.json"
    if not all(path.is_file() for path in (catalog_path, prep_path, matrix_path)):
        raise ValueError("Faltan catálogo, preparación vigente o matriz de seguimiento F10")

    # The canonical catalog validator verifies receipt schemas, territorial/election
    # identities, contracts and election registry. Errors are attributed per territory.
    catalog_errors = catalogo_preparacion.validate_repository(catalog_path, root)
    config = _yaml(prep_path)
    catalog = _yaml(catalog_path)
    dossier = _json(matrix_path)
    plan_inputs: dict[str, str] = {}
    activities = None
    if plan_root is not None:
        plan_root = plan_root.resolve()
        overlay_path = plan_root / "puertas_f10.v1.json"
        plan_state_path = plan_root / "estado.json"
        plan_catalog_path = plan_root / "catalogo.json"
        overlay = _json(overlay_path)
        plan_state = _json(plan_state_path)
        if overlay.get("schema") != "ddd.plan-derived-doors/1.0":
            raise ValueError("Schema de extensión F10 del Plan no reconocido")
        if overlay.get("plan_revision") != plan_state.get("plan_revision"):
            raise ValueError("La extensión F10 corresponde a otra revisión del Plan Maestro")
        if sha256(plan_state_path) != overlay.get("plan_state_sha256_at_creation"):
            plan_inputs["plan_state_changed_since_overlay"] = sha256(plan_state_path)
        if sha256(plan_catalog_path) != overlay.get("catalog_sha256_at_creation"):
            plan_inputs["plan_catalog_changed_since_overlay"] = sha256(plan_catalog_path)
        activities = _validate_activity_cards(root, overlay.get("activities") or [])
        plan_inputs.update({
            "plan_overlay_sha256": sha256(overlay_path),
            "plan_state_sha256": sha256(plan_state_path),
            "plan_catalog_sha256": sha256(plan_catalog_path),
        })
    source_rows = {str(row["territory_id"]): row for row in catalog["territories"]}
    prep_rows = {str(row["territory_id"]): row for row in config["territories"]}
    dossier_rows = {str(row["territory_id"]): row for row in dossier["rows"]}
    if set(source_rows) != set(prep_rows) or set(source_rows) != set(dossier_rows) or len(source_rows) != 19:
        raise ValueError("Los universos de catálogo, preparación y matriz no coinciden en 19 territorios")

    errors_by_territory: dict[str, list[str]] = {}
    for error in catalog_errors:
        territory_id = next((tid for tid in source_rows if error.startswith(tid + ":") or error.startswith(tid + "/")), None)
        if territory_id:
            errors_by_territory.setdefault(territory_id, []).append(error)

    rows: list[dict[str, Any]] = []
    for territory_id, source_row in source_rows.items():
        state = (source_row.get("editions") or {}).get("2025") or {}
        prep = prep_rows[territory_id]
        dossier_row = dossier_rows[territory_id]
        territorial_receipt: dict[str, Any] | None = None
        territorial_status = "BLOCKED"
        territorial_reason: list[str] = []
        territorial_admissibility = str(dossier_row.get("territorial_admissibility") or "BLOCKED")
        territorial_admissibility_reason: list[str] = []
        territorial_geometry_evidence_path: str | None = None
        territorial_path = _receipt_reference(state)
        territorial_sha = None
        try:
            _, territorial_receipt = validate_territorial_receipt(
                root_dir=root, territory=territory_id, edition="2025"
            )
            if not territorial_path:
                raise ValueError("receipt canónico no referenciado en catálogo")
            receipt_path = root / str(territorial_path)
            territorial_sha = sha256(receipt_path)
            check_territorial_evidence(
                territorial_receipt, territory_id=territory_id,
                receipt_path=str(territorial_path), receipt_sha256=territorial_sha,
                dossier_row=dossier_row,
            )
            territorial_status = "CLOSED"
            (
                territorial_admissibility,
                territorial_admissibility_reason,
                territorial_geometry_evidence_path,
            ) = _geometric_admissibility(
                root, state, territorial_receipt,
                str(dossier_row.get("territorial_admissibility") or "BLOCKED"),
            )
        except Exception as exc:
            territorial_reason.append(str(exc))
            if dossier_row.get("territorial_acquisition") == "CLOSED":
                territorial_reason.append("CONTRADICTION: el expediente afirma CLOSED y el consumidor canónico no lo acredita")

        electoral_status = "BLOCKED"
        electoral_reason: list[str] = []
        electoral_identity_sha = None
        electoral_receipt_path = str(((state.get("evidence") or {}).get("electoral_source")) or "")
        if errors_by_territory.get(territory_id):
            electoral_reason.extend(errors_by_territory[territory_id])
        elif state.get("electoral_source_prepared") is True and electoral_receipt_path:
            try:
                electoral_receipt = _json(root / electoral_receipt_path)
                if electoral_receipt.get("schema") != "ddd.catalog-evidence/1.0" or electoral_receipt.get("kind") != "electoral_source":
                    raise ValueError("receipt electoral no satisface ddd.catalog-evidence/1.0")
                if electoral_receipt.get("territory_id") != territory_id or electoral_receipt.get("edition") != "2025":
                    raise ValueError("receipt electoral con identidad territorial/edición errónea")
                election = prep.get("election_id")
                election_date = str(prep.get("election_date") or "")
                if electoral_receipt.get("election_id") != election or str(electoral_receipt.get("election_date") or election_date) != election_date:
                    raise ValueError("receipt electoral contradice la elección vigente")
                electoral_identity_sha = _electoral_identity(
                    electoral_receipt, election_id=str(election), election_date=election_date
                )
                selected_section_year = (
                    int(territorial_receipt["section_year"]) if territorial_receipt
                    else int((prep.get("territorial") or {}).get("section_selected_year"))
                )
                election_year = int(election_date[:4])
                if selected_section_year != election_year:
                    raise ValueError(
                        f"falta correspondencia electoral acreditada: seccionado {selected_section_year}, elección {election_year}"
                    )
                electoral_status = "ADMISSIBLE"
            except Exception as exc:
                electoral_reason.append(str(exc))
        else:
            electoral_reason.append("fuente electoral definitiva sin receipt preparado")

        joint_status = "BLOCKED"
        joint_reason: list[str] = []
        try:
            if territorial_status != "CLOSED":
                raise ValueError("puerta territorial no CLOSED")
            if electoral_status != "ADMISSIBLE":
                raise ValueError("puerta electoral no ADMISSIBLE")
            pair = resolve_pair(root_dir=root, territory=territory_id, edition="2025")
            if dossier_row.get("joint_admissibility") != "PASS":
                raise ValueError("matriz de seguimiento contradice par canónico admisible")
            joint_status = "PASS"
        except Exception as exc:
            joint_reason.append(str(exc))
            if dossier_row.get("joint_admissibility") == "PASS":
                joint_reason.append("CONTRADICTION: el expediente afirma PASS y el consumidor conjunto no lo acredita")

        # The tracking document is checked against the independent derived doors.
        expected_electoral = dossier_row.get("electoral_admissibility")
        if electoral_status != expected_electoral:
            derived_electoral = electoral_status
            electoral_status = "BLOCKED"
            electoral_reason.append(
                f"CONTRADICTION: matriz electoral={expected_electoral}; derivación canónica={derived_electoral}"
            )
            joint_status = "BLOCKED"
            joint_reason.append("puerta electoral contradictoria")
        if joint_status != dossier_row.get("joint_admissibility"):
            derived_joint = joint_status
            joint_status = "BLOCKED"
            joint_reason.append(
                f"CONTRADICTION: matriz conjunta={dossier_row.get('joint_admissibility')}; consumidor={derived_joint}"
            )

        rows.append({
            "territory_id": territory_id,
            "territory": source_row.get("name"),
            "territorial_acquisition": territorial_status,
            "territorial_reason": territorial_reason,
            "territorial_admissibility": territorial_admissibility,
            "territorial_admissibility_reason": territorial_admissibility_reason,
            "territorial_geometry_evidence_path": territorial_geometry_evidence_path,
            "territorial_receipt_path": territorial_path,
            "territorial_receipt_sha256": territorial_sha,
            "territorial_run_id": (territorial_receipt or {}).get("run_id"),
            "territorial_validation_scope": "canonical #179 receipt schema, identity, edition and receipt-file SHA; package bytes are not re-extracted by this read-only projection",
            "population_year": (territorial_receipt or {}).get("population_year"),
            "section_year": (territorial_receipt or {}).get("section_year"),
            "territorial_identity_sha256": (territorial_receipt or {}).get("territorial_identity_sha256"),
            "electoral_admissibility": electoral_status,
            "electoral_reason": electoral_reason,
            "electoral_receipt_path": electoral_receipt_path or None,
            "electoral_identity_sha256": electoral_identity_sha,
            "electoral_validation_scope": "canonical catalog contract and election identity metadata; source artifact bytes are not revalidated by this projection",
            "joint_admissibility": joint_status,
            "joint_validation_scope": "canonical prepared-pair receipt consumer; never inferred from PR state",
            "joint_reason": joint_reason,
            "production": "NOT_AUTHORIZED_BY_F10",
        })

    grants = activity_authorizations or {}
    work_items = work_items_for(rows, grants, activities)

    counts = {
        "territorial_acquisition": _status_counts(rows, "territorial_acquisition"),
        "territorial_admissibility": _status_counts(rows, "territorial_admissibility"),
        "electoral_admissibility": _status_counts(rows, "electoral_admissibility"),
        "joint_admissibility": _status_counts(rows, "joint_admissibility"),
        "production": _status_counts(rows, "production"),
    }
    return {
        "schema": "ddd.f10-derived-doors/1.0",
        "source_head": _git_head(root),
        "inputs": {
            path.relative_to(root).as_posix(): sha256(path)
            for path in (catalog_path, prep_path, matrix_path)
        } | plan_inputs,
        "counts": counts,
        "f10_global": "PENDING",
        "f10_global_reason": (
            "F10 permanece PENDING: "
            f"adquisición territorial CLOSED {counts['territorial_acquisition'].get('CLOSED', 0)}/19; "
            f"admisibilidad territorial PASS {counts['territorial_admissibility'].get('PASS', 0)}/19; "
            f"admisibilidad electoral ADMISSIBLE {counts['electoral_admissibility'].get('ADMISSIBLE', 0)}/19; "
            f"admisibilidad conjunta PASS {counts['joint_admissibility'].get('PASS', 0)}/19."
        ),
        "production_authorized": False,
        "catalog_validation_errors": catalog_errors,
        "task_spec_validation_errors": [
            {"activity_id": row["id"], "error": row["task_spec_error"]}
            for row in activities or [] if row.get("task_spec_error")
        ],
        "territories": rows,
        "work_items": work_items,
        "next_action_candidate": next((item for item in work_items if item["state"] == "READY_LOCAL"), None),
    }


def _validate_activity_cards(root: Path, activities: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Verify task-card references; a tracking flag alone cannot make work executable."""
    validated = []
    for original in activities:
        activity = dict(original)
        if not activity.get("task_spec_registered"):
            validated.append(activity)
            continue
        try:
            reference = str(activity.get("task_spec_path") or "")
            relative, separator, task_id = reference.partition("#")
            card_path = Path(relative)
            if not separator or card_path.is_absolute() or ".." in card_path.parts or not task_id:
                raise ValueError("referencia de ficha inválida")
            source = root / card_path
            if sha256(source) != activity.get("task_spec_sha256"):
                raise ValueError("hash de ficha distinto")
            catalog = _json(source)
            if catalog.get("schema") != "ddd.f10-auto-task-cards/1.0":
                raise ValueError("schema de fichas desconocido")
            matches = [card for card in catalog.get("cards", []) if card.get("id") == task_id]
            if len(matches) != 1 or matches[0].get("territory_id") != activity.get("territory_id"):
                raise ValueError("identidad de tarea/territorio distinta")
            spec = matches[0].get("spec") or {}
            task = matches[0].get("task") or {}
            acceptance = matches[0].get("acceptance") or []
            validators = spec.get("validators") or []
            covered = {index for validator in validators for index in validator.get("covers", [])}
            if (spec.get("work_class") != "READ_ONLY" or task.get("authority_class") != "local_read_only"
                    or task.get("reserved") is not False or task.get("front") != "fuentes-oficiales"
                    or task.get("depends_on") != [] or not acceptance
                    or covered != set(range(len(acceptance))) or not validators
                    or any(item.get("local_only") is not True or not item.get("argv") for item in validators)
                    or not set(activity.get("required_actions", [])) <= set(spec.get("allowed_actions", []))):
                raise ValueError("ficha excede alcance local READ_ONLY")
            from herramientas.validar_f10_auto_task import validate as validate_card
            validate_card(root, task_id, cards_path=card_path)
        except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
            activity["task_spec_error"] = f"Ficha no verificable: {exc}"
        validated.append(activity)
    return validated


def _git_head(root: Path) -> str | None:
    import subprocess

    try:
        result = subprocess.run(
            ["git", "-C", str(root), "rev-parse", "HEAD"],
            text=True, capture_output=True, check=True,
        )
        return result.stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--policy", type=Path)
    parser.add_argument("--plan", type=Path)
    args = parser.parse_args()
    policy = _json(args.policy) if args.policy else {}
    projection = derive_f10(args.root, activity_authorizations=policy.get("authorized_classes", {}), plan_root=args.plan)
    print(json.dumps(projection, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
