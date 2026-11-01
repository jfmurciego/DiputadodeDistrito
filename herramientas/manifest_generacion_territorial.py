#!/usr/bin/env python3
"""Serializa y verifica linaje durable de un M06 emitido por el workflow 02.

PROYECTO: Diputado de Distrito
VERSIÓN: 1.0.1
NOMBRE DE VERSIÓN: Manifiesto durable M06 independiente
FECHA: 2026-11-01
ESTADO: candidato
QUÉ HACE: enlaza contrato, ejecución, inputs, M05, certificación M06 y referencias de artefactos.
CAMBIOS: 1.0.1: artifact_ref deduplica por id; al reanudar desde M05 el índice trae el mismo artefacto M04 como
  «checkpoint» y como «m04» (Congreso Álava, run 41335088773). Ids distintos con el mismo nombre siguen fallando.
  1.0.0: añade un manifiesto M06 posterior al empaquetado, sin incluirlo en el artefacto que acredita.
MOTIVO: conservar linaje durable cuando la generación se ejecuta por 02 y no por 00.
ANTERIOR: legacy/herramientas/manifest_generacion_territorial_v1.0.0_20261101.py
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import zipfile
from pathlib import Path
from typing import Any

import yaml

SCHEMA = "ddd.territorial-generation-manifest/1.0"
SHA256 = re.compile(r"^[0-9a-f]{64}$")
SHA1 = re.compile(r"^[0-9a-f]{40}$")
STRATEGIES = {"Canónico", "GerryChain", "GerryChain 25", "GerryChain 50"}
PASS = {"PASS", "PASS_WITH_EXCEPTIONS", "PASS_WITH_GOVERNED_EXCEPTIONS"}


class GenerationManifestError(ValueError):
    pass


def _canonical(payload: dict[str, Any]) -> bytes:
    body = {key: value for key, value in payload.items() if key != "manifest_sha256"}
    return json.dumps(body, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def manifest_sha256(payload: dict[str, Any]) -> str:
    return hashlib.sha256(_canonical(payload)).hexdigest()


def _sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _single_geojson_member_sha256(path: Path, *, label: str) -> str:
    """Hash the exact GeoJSON payload inside a one-member M05 ZIP archive."""
    try:
        with zipfile.ZipFile(path) as archive:
            members = [name for name in archive.namelist() if not name.endswith("/")]
            if len(members) != 1 or not members[0].lower().endswith(".geojson"):
                raise GenerationManifestError(f"{label}: se esperaba un único miembro GeoJSON")
            bad_member = archive.testzip()
            if bad_member is not None:
                raise GenerationManifestError(f"{label}: ZIP dañado en {bad_member}")
            payload = archive.read(members[0])
    except zipfile.BadZipFile as exc:
        raise GenerationManifestError(f"{label}: ZIP ilegible") from exc
    return hashlib.sha256(payload).hexdigest()


def _require_sha(value: Any, label: str) -> str:
    result = str(value or "").removeprefix("sha256:").lower()
    if not SHA256.fullmatch(result):
        raise GenerationManifestError(f"{label}: SHA-256 ausente o inválido")
    return result


def artifact_ref(index: dict[str, Any], *, run_id: int, name: str) -> dict[str, Any]:
    artifacts = index.get("artifacts")
    if not isinstance(artifacts, list):
        raise GenerationManifestError("Índice de artefactos inválido")
    matches = [
        item for item in artifacts
        if isinstance(item, dict)
        and int(item.get("workflow_run_id") or item.get("run_id") or 0) == run_id
        and str(item.get("name") or "") == name
    ]
    unique: dict[str, dict[str, Any]] = {}
    for item in matches:
        key = str(item.get("id") or item.get("artifact_id") or "")
        if key and key in unique and unique[key] != item:
            raise GenerationManifestError(f"Artefacto {name} en run {run_id}: id {key} repetido con datos distintos")
        unique.setdefault(key or f"sin-id-{len(unique)}", item)
    matches = list(unique.values())
    if len(matches) != 1:
        raise GenerationManifestError(f"Artefacto {name} en run {run_id}: se esperaba una coincidencia, hay {len(matches)}")
    item = matches[0]
    if item.get("expired") is True:
        raise GenerationManifestError(f"Artefacto expirado: {name}")
    artifact_id = item.get("id") or item.get("artifact_id")
    if isinstance(artifact_id, bool) or not str(artifact_id or "").isdigit() or int(artifact_id) <= 0:
        raise GenerationManifestError(f"Artefacto sin id válido: {name}")
    digest = _require_sha(item.get("digest") or item.get("sha256"), f"artefacto {name}")
    size = item.get("size_in_bytes") or item.get("size")
    if isinstance(size, bool) or not isinstance(size, int) or size < 0:
        raise GenerationManifestError(f"Artefacto sin tamaño válido: {name}")
    return {
        "run_id": run_id,
        "artifact_id": int(artifact_id),
        "artifact_name": name,
        "artifact_sha256": digest,
        "size_in_bytes": size,
    }


def _find_one(root: Path, pattern: str, *, label: str) -> Path:
    matches = [path for path in root.rglob(pattern) if path.is_file()]
    if len(matches) != 1:
        raise GenerationManifestError(f"{label}: se esperaba un archivo único, hay {len(matches)}")
    return matches[0]


def resolve_checkpoint_source_package(
    *, root_dir: Path, state_dir: Path, territory_id: str, edition: str,
) -> dict[str, Any]:
    """Recupera el paquete fuente del catálogo sólo si coincide con los bytes del checkpoint.

    La identidad del artefacto no puede deducirse del nombre del checkpoint.
    El manifiesto de fuentes conserva el SHA del ZIP congelado; éste debe ser
    idéntico al package_sha256 de la evidencia de preparación acreditada.
    """
    root = root_dir.resolve()
    state = state_dir.resolve()
    source_manifest_path = state / "sources" / "manifest.json"
    if not source_manifest_path.is_file():
        raise GenerationManifestError("CHECKPOINT_SOURCE_UNPROVEN: falta sources/manifest.json")
    try:
        source_manifest = json.loads(source_manifest_path.read_text(encoding="utf-8"))
        catalog = yaml.safe_load((root / "configuracion/catalogo_preparacion.yaml").read_text(encoding="utf-8")) or {}
    except (OSError, ValueError, yaml.YAMLError) as exc:
        raise GenerationManifestError("CHECKPOINT_SOURCE_UNPROVEN: manifiesto/catálogo ilegible") from exc
    if not isinstance(source_manifest, dict) or not isinstance(catalog, dict):
        raise GenerationManifestError("CHECKPOINT_SOURCE_UNPROVEN: manifiesto/catálogo inválido")
    rows = [row for row in (catalog.get("territories") or []) if row.get("territory_id") == territory_id]
    if len(rows) != 1:
        raise GenerationManifestError("CHECKPOINT_SOURCE_UNPROVEN: territorio no único en catálogo")
    registered = ((rows[0].get("editions") or {}).get(str(edition)) or {}).get("preparation_evidence") or {}
    if not isinstance(registered, dict):
        raise GenerationManifestError("CHECKPOINT_SOURCE_UNPROVEN: evidencia fuente no válida")
    try:
        run_id = int(registered.get("run_id") or 0)
        name = str(registered.get("artifact_name") or "")
        artifact_sha = _require_sha(registered.get("artifact_sha256"), "fuente catalogada")
        package_sha = _require_sha(registered.get("package_sha256"), "paquete fuente catalogado")
        observed_package_sha = _require_sha(source_manifest.get("sha256"), "fuente congelada checkpoint")
    except (TypeError, ValueError) as exc:
        raise GenerationManifestError("CHECKPOINT_SOURCE_UNPROVEN: evidencia fuente incompleta") from exc
    if (
        run_id <= 0 or not name or
        str(source_manifest.get("territory_id") or "") != territory_id or
        str(source_manifest.get("edition") or "") != str(edition) or
        observed_package_sha != package_sha
    ):
        raise GenerationManifestError("CHECKPOINT_SOURCE_UNPROVEN: la fuente del checkpoint no coincide con el catálogo")
    return {"run_id": run_id, "artifact_name": name, "artifact_sha256": artifact_sha}


def _candidate_proof(state_dir: Path, report_path: Path) -> dict[str, Any]:
    try:
        report = json.loads(report_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise GenerationManifestError(f"Informe M05 ilegible: {exc}") from exc
    if report.get("schema") != "ddd.m05-gerrychain-strategy/2.0":
        raise GenerationManifestError("Informe M05 con schema inesperado")
    portfolio = report.get("portfolio")
    rows = portfolio.get("candidates") if isinstance(portfolio, dict) else None
    if not isinstance(rows, list) or len(rows) != 50 or portfolio.get("candidate_count") != 50:
        raise GenerationManifestError("GERRYCHAIN50_CANDIDATE_COUNT_NOT_50")
    hashes: list[str] = []
    for index, row in enumerate(rows, start=1):
        if not isinstance(row, dict):
            raise GenerationManifestError(f"Candidato {index} no es un objeto")
        assignment_hash = _require_sha(row.get("assignment_hash"), f"candidato {index} assignment_hash")
        expected_file_sha = _require_sha(row.get("sha256"), f"candidato {index} sha256")
        raw_path = str(row.get("geojson") or "")
        if not raw_path:
            raise GenerationManifestError(f"Candidato {index} no declara su artefacto")
        basename = Path(raw_path).name
        candidates = [path for path in state_dir.rglob(basename) if path.is_file()]
        if len(candidates) != 1:
            raise GenerationManifestError(f"Candidato {index}: artefacto ausente o ambiguo en el estado M06")
        candidate_path = candidates[0]
        if _sha(candidate_path) != expected_file_sha:
            raise GenerationManifestError(f"Candidato {index}: SHA del archivo no coincide")
        try:
            with zipfile.ZipFile(candidate_path) as archive:
                bad_member = archive.testzip()
                if bad_member is not None:
                    raise GenerationManifestError(f"Candidato {index}: ZIP dañado en {bad_member}")
        except zipfile.BadZipFile as exc:
            raise GenerationManifestError(f"Candidato {index}: no es un ZIP íntegro") from exc
        hashes.append(assignment_hash)
    if len(set(hashes)) != 50 or portfolio.get("unique_candidate_count") != 50:
        raise GenerationManifestError("GERRYCHAIN50_ASSIGNMENT_HASHES_NOT_UNIQUE")
    selected = [row for row in rows if row.get("selected") is True]
    selected_hash = str((report.get("search") or {}).get("selected_assignment_hash") or "")
    if (
        len(selected) != 1
        or selected[0].get("assignment_hash") != selected_hash
        or (
            portfolio.get("selected_assignment_hash") is not None
            and str(portfolio.get("selected_assignment_hash") or "") != selected_hash
        )
    ):
        raise GenerationManifestError("GERRYCHAIN50_SELECTED_ASSIGNMENT_MISMATCH")
    selected_file_sha = str(selected[0].get("sha256") or "").lower()
    output = report.get("output") if isinstance(report.get("output"), dict) else {}
    output_sha = _require_sha(output.get("sha256"), "salida M05 seleccionada")
    output_path_text = str(output.get("geojson") or "")
    if not output_path_text:
        raise GenerationManifestError("La salida M05 seleccionada no declara su ruta")
    selected_path_text = str(selected[0].get("geojson") or "")
    selected_matches = [path for path in state_dir.rglob(Path(selected_path_text).name) if path.is_file()]
    output_matches = [path for path in state_dir.rglob(Path(output_path_text).name) if path.is_file()]
    if len(selected_matches) != 1 or len(output_matches) != 1 or _sha(output_matches[0]) != output_sha:
        raise GenerationManifestError("La salida M05 no coincide con el candidato seleccionado del portfolio")
    selected_content_sha = _single_geojson_member_sha256(
        selected_matches[0], label="artefacto M05 seleccionado"
    )
    output_content_sha = _single_geojson_member_sha256(
        output_matches[0], label="salida M05 seleccionada"
    )
    if selected_content_sha != output_content_sha:
        raise GenerationManifestError("El contenido GeoJSON de la salida M05 difiere del candidato seleccionado")
    return {
        "report_sha256": _sha(report_path),
        "report_relative_path": report_path.relative_to(state_dir).as_posix(),
        "candidate_count": 50,
        "unique_assignment_hash_count": 50,
        "assignment_hashes": hashes,
        "selected_assignment_hash": selected_hash,
        "selected_artifact_sha256": selected_file_sha,
        "selected_output_sha256": output_sha,
        "selected_artifact_content_sha256": selected_content_sha,
        "selected_output_content_sha256": output_content_sha,
    }


def build_manifest(
    *, root_dir: Path, state_dir: Path, audit_dir: Path, artifact_index_path: Path,
    artifact_roles_path: Path, territory_id: str, territory_name: str, edition: str,
    contract_path: str, workflow_run_id: int, workflow_run_attempt: int,
    workflow_sha: str, checkout_sha: str, workflow_name: str,
    execution_mode: str, from_stage: str, to_stage: str, checkpoint_run_id: int | None,
    optimization_algorithm: str, gerrychain_entrypoint: str, require_unique_hashes: bool,
    record_type: str = "run_time",
) -> dict[str, Any]:
    root = root_dir.resolve()
    state_dir = state_dir.resolve()
    audit_dir = audit_dir.resolve()
    params = root / contract_path
    if not params.resolve().is_relative_to(root):
        raise GenerationManifestError("La ruta del contrato sale del repositorio")
    if not params.is_file():
        raise GenerationManifestError(f"Contrato no encontrado: {contract_path}")
    if optimization_algorithm not in STRATEGIES:
        raise GenerationManifestError("Estrategia solicitada inválida")
    if not SHA1.fullmatch(workflow_sha) or not SHA1.fullmatch(checkout_sha):
        raise GenerationManifestError("SHA de ejecución o checkout inválido")
    if workflow_run_id <= 0 or workflow_run_attempt <= 0:
        raise GenerationManifestError("Identidad de ejecución inválida")
    if record_type not in {"run_time", "post_run_recovery"}:
        raise GenerationManifestError("Tipo de constancia M06 inválido")
    cfg = yaml.safe_load(params.read_text(encoding="utf-8")) or {}
    meta = cfg.get("meta") or {}
    if str(meta.get("territory_id") or "") != territory_id or str(meta.get("year") or "") != str(edition):
        raise GenerationManifestError("El contrato no coincide con territorio/edición")
    contract_digest = _sha(params)
    artifact_index = json.loads(artifact_index_path.read_text(encoding="utf-8"))
    roles = json.loads(artifact_roles_path.read_text(encoding="utf-8"))
    artifact_refs = {}
    for role in ("m05", "m06", "audit"):
        item = roles.get(role) or {}
        artifact_refs[role] = artifact_ref(
            artifact_index,
            run_id=int(item.get("run_id") or 0),
            name=str(item.get("name") or ""),
        )
    if roles.get("m04"):
        item = roles["m04"]
        artifact_refs["m04"] = artifact_ref(
            artifact_index,
            run_id=int(item.get("run_id") or 0),
            name=str(item.get("name") or ""),
        )
    if artifact_refs["m06"]["run_id"] != workflow_run_id or artifact_refs["audit"]["run_id"] != workflow_run_id:
        raise GenerationManifestError("M06 y auditoría deben pertenecer al run actual")
    if artifact_refs["m05"]["run_id"] > workflow_run_id:
        raise GenerationManifestError("Un checkpoint M04/M05 no puede pertenecer a un run futuro")
    try:
        status_path = audit_dir / "production_status.json"
        status = json.loads(status_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise GenerationManifestError("production_status.json ausente o ilegible") from exc
    decision = str(status.get("decision") or "")
    if decision not in PASS:
        raise GenerationManifestError(f"Certificación M06 no aprobatoria: {decision or 'UNKNOWN'}")
    audit_files = {}
    for path in sorted(audit_dir.rglob("*")):
        if path.is_file():
            rel = path.relative_to(audit_dir).as_posix()
            audit_files[rel] = {"sha256": _sha(path), "size_in_bytes": path.stat().st_size}
    required_audit_files = {"production_status.json"}
    if not required_audit_files.issubset(audit_files):
        raise GenerationManifestError("La auditoría no contiene production_status.json")

    optimization_path = _find_one(state_dir, "OPTIMIZATION_EXECUTION.json", label="Evidencia de estrategia M05")
    try:
        optimization = json.loads(optimization_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise GenerationManifestError("OPTIMIZATION_EXECUTION.json ilegible") from exc
    if optimization.get("requested_algorithm") != optimization_algorithm:
        raise GenerationManifestError("La estrategia solicitada no coincide con OPTIMIZATION_EXECUTION")
    if optimization.get("execution_status") != "M05_SUCCESS":
        raise GenerationManifestError("La ejecución M05 no terminó en M05_SUCCESS")
    effective = optimization.get("effective_algorithm")
    fallback = optimization.get("fallback")
    if effective not in STRATEGIES or not isinstance(fallback, bool):
        raise GenerationManifestError("La estrategia efectiva o fallback M05 no tienen tipos verificables")
    if (not fallback and effective != optimization_algorithm) or (fallback and effective != "Canónico"):
        raise GenerationManifestError("La estrategia efectiva M05 contradice la solicitud/fallback")
    if optimization_algorithm == "GerryChain 50":
        if gerrychain_entrypoint != "gerrychain_50" or require_unique_hashes is not True:
            raise GenerationManifestError("GerryChain 50 no conserva su contrato interno")
        if optimization.get("effective_algorithm") != "GerryChain 50" or optimization.get("fallback") is not False:
            raise GenerationManifestError("GerryChain 50 no fue efectivo o declaró fallback")
        if optimization.get("candidate_count") != 50:
            raise GenerationManifestError("GerryChain 50 no registra 50 candidatos")
        reports = []
        for path in state_dir.rglob("*.json"):
            try:
                raw = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            if raw.get("schema") == "ddd.m05-gerrychain-strategy/2.0":
                reports.append(path)
        if len(reports) != 1:
            raise GenerationManifestError("Informe de portfolio M05 ausente o ambiguo")
        portfolio_proof = _candidate_proof(state_dir, reports[0])
    else:
        if bool(optimization.get("fallback")) and optimization.get("effective_algorithm") != "Canónico":
            raise GenerationManifestError("Evidencia de fallback contradictoria")
        portfolio_proof = None

    source_manifest_path = _find_one(
        state_dir, "manifest.json", label="Manifiesto del paquete de fuentes"
    )
    if "sources" not in source_manifest_path.parts:
        raise GenerationManifestError("El manifiesto de fuentes no está bajo sources/")
    inputs = {
        "checkpoint_run_id": checkpoint_run_id,
        "checkpoint_artifact": None,
        "source_manifest_sha256": _sha(source_manifest_path),
    }
    if roles.get("checkpoint"):
        checkpoint_role = roles["checkpoint"]
        inputs["checkpoint_artifact"] = artifact_ref(
            artifact_index,
            run_id=int(checkpoint_role.get("run_id") or 0),
            name=str(checkpoint_role.get("name") or ""),
        )
        inputs["checkpoint_stage"] = str(checkpoint_role.get("stage") or "")
    if "m04" in artifact_refs:
        inputs["m04_artifact"] = artifact_refs["m04"]
    if roles.get("source_package"):
        source_role = roles["source_package"]
        inputs["source_package_artifact"] = artifact_ref(
            artifact_index,
            run_id=int(source_role.get("run_id") or 0),
            name=str(source_role.get("name") or ""),
        )
    if roles.get("source_evidence"):
        evidence_role = roles["source_evidence"]
        inputs["source_evidence_artifact"] = artifact_ref(
            artifact_index,
            run_id=int(evidence_role.get("run_id") or 0),
            name=str(evidence_role.get("name") or ""),
        )
        expected_evidence_sha = str(evidence_role.get("expected_sha256") or "").removeprefix("sha256:").lower()
        if expected_evidence_sha and inputs["source_evidence_artifact"]["artifact_sha256"] != expected_evidence_sha:
            raise GenerationManifestError("El digest de evidencia de fuente declarado no coincide con GitHub")

    payload: dict[str, Any] = {
        "schema": SCHEMA,
        "record_type": record_type,
        "identity": {
            "territory_id": territory_id,
            "territory_name": territory_name,
            "edition": str(edition),
            "workflow_run_id": workflow_run_id,
            "workflow_run_attempt": workflow_run_attempt,
            "workflow_name": workflow_name,
            "workflow_sha": workflow_sha,
            "checkout_sha": checkout_sha,
        },
        "contract": {"path": contract_path, "sha256": contract_digest},
        "execution": {
            "mode": execution_mode,
            "from_stage": from_stage,
            "to_stage": to_stage,
            "checkpoint_run_id": checkpoint_run_id,
            "optimization_algorithm_requested": optimization_algorithm,
        "optimization_algorithm_effective": effective,
        "fallback": fallback,
            "fallback_reason": optimization.get("fallback_reason"),
            "gerrychain_entrypoint": gerrychain_entrypoint or None,
            "require_unique_hashes": bool(require_unique_hashes),
            "candidate_count": int(optimization.get("candidate_count") or 0),
            "optimization_evidence_sha256": _sha(optimization_path),
            "portfolio_proof": portfolio_proof,
        },
        "inputs": inputs,
        "artifacts": {
            "m04": artifact_refs.get("m04"),
            "m05": artifact_refs["m05"],
            "m06": artifact_refs["m06"],
            "audit": artifact_refs["audit"],
        },
        "certification": {
            "stage": "M06_INDEPENDENT_GEOMETRIC_AUDIT",
            "decision": decision,
            "production_status_sha256": audit_files["production_status.json"]["sha256"],
            "audit_files": audit_files,
        },
    }
    payload["manifest_sha256"] = manifest_sha256(payload)
    return payload


def write_idempotent(path: Path, payload: dict[str, Any]) -> bool:
    if payload.get("schema") != SCHEMA or manifest_sha256(payload) != payload.get("manifest_sha256"):
        raise GenerationManifestError("Manifiesto sin integridad interna válida")
    rendered = json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        if path.read_text(encoding="utf-8") == rendered:
            return False
        raise GenerationManifestError(f"M06_MANIFEST_CONFLICT: se conserva el contenido existente: {path}")
    temp = path.with_name(path.name + ".tmp")
    try:
        temp.write_text(rendered, encoding="utf-8")
        temp.replace(path)
    finally:
        if temp.exists():
            temp.unlink()
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("root-dir", "state-dir", "audit-dir", "artifact-index", "artifact-roles"):
        parser.add_argument("--" + name, required=True, type=Path)
    for name in ("territory-id", "territory-name", "edition", "contract-path", "workflow-sha", "checkout-sha", "workflow-name", "execution-mode", "from-stage", "to-stage", "optimization-algorithm"):
        parser.add_argument("--" + name, required=True)
    for name in ("workflow-run-id", "workflow-run-attempt"):
        parser.add_argument("--" + name, required=True, type=int)
    parser.add_argument("--checkpoint-run-id", type=int)
    parser.add_argument("--gerrychain-entrypoint", default="")
    parser.add_argument("--require-unique-hashes", action="store_true")
    parser.add_argument("--record-type", choices=("run_time", "post_run_recovery"), default="run_time")
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    payload = build_manifest(
        root_dir=args.root_dir, state_dir=args.state_dir, audit_dir=args.audit_dir,
        artifact_index_path=args.artifact_index, artifact_roles_path=args.artifact_roles,
        territory_id=args.territory_id, territory_name=args.territory_name, edition=args.edition,
        contract_path=args.contract_path, workflow_run_id=args.workflow_run_id,
        workflow_run_attempt=args.workflow_run_attempt, workflow_sha=args.workflow_sha,
        checkout_sha=args.checkout_sha, workflow_name=args.workflow_name,
        execution_mode=args.execution_mode, from_stage=args.from_stage, to_stage=args.to_stage,
        checkpoint_run_id=args.checkpoint_run_id, optimization_algorithm=args.optimization_algorithm,
        gerrychain_entrypoint=args.gerrychain_entrypoint,
        require_unique_hashes=args.require_unique_hashes,
        record_type=args.record_type,
    )
    changed = write_idempotent(args.output, payload)
    print(json.dumps({"manifest_sha256": payload["manifest_sha256"], "changed": changed}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
