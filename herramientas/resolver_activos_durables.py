"""Resolver de activos durables M06/M08.

PROYECTO: Diputado de Distrito
VERSIÓN: 1.1.1
NOMBRE DE VERSIÓN: Contrastar fuentes del manifiesto M06 02
FECHA: 2026-10-26
ESTADO: candidato
QUÉ HACE: valida activos territoriales/electorales y sus manifiestos de productor.
CAMBIOS: compara la fuente M06 standalone con el artefacto territorial declarado en sus inputs.
MOTIVO: evitar buscar fases 00 inexistentes y bloquear fuentes cruzadas.
ANTERIOR: legacy/herramientas/resolver_activos_durables_pre_source_m06_inputs_20261026.py
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any

from herramientas.acreditar_producto_territorial_historico import (
    HistoricalTerritorialAccreditationBlock,
    derive_historical_territorial_producer,
)

PASS_CERTIFICATIONS = {"PASS", "PASS_WITH_EXCEPTIONS", "PASS_WITH_GOVERNED_EXCEPTIONS"}
_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_SHA1 = re.compile(r"^[0-9a-f]{40}$")
_M06_SCHEMA = "ddd.territorial-generation-manifest/1.0"


class DurableAssetBlock(ValueError):
    pass


def _block(code: str, reason: str) -> None:
    raise DurableAssetBlock(f"{code}: {reason}")


def _digest(value: Any, *, label: str) -> str:
    digest = str(value or "").removeprefix("sha256:").lower()
    if not _SHA256.fullmatch(digest):
        _block("DURABLE_ASSET_DIGEST_INVALID", f"{label}: SHA-256 ausente o inválido")
    return digest


def _run_id(value: Any, *, label: str) -> int:
    if isinstance(value, bool):
        _block("DURABLE_ASSET_IDENTITY_INVALID", f"{label}: run_id inválido")
    try:
        run_id = int(value)
    except (TypeError, ValueError):
        run_id = 0
    if run_id <= 0:
        _block("DURABLE_ASSET_IDENTITY_INVALID", f"{label}: run_id inválido")
    return run_id


def _load_json(root: Path, rel: str | None, *, label: str) -> dict:
    if not rel:
        _block("DURABLE_ASSET_MISSING", f"{label}: receipt durable no declarado")
    path = root / str(rel)
    if not path.is_file():
        _block("DURABLE_ASSET_MISSING", f"{label}: receipt durable inexistente: {rel}")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        _block("DURABLE_ASSET_INVALID", f"{label}: receipt durable ilegible")
    if not isinstance(payload, dict):
        _block("DURABLE_ASSET_INVALID", f"{label}: receipt durable inválido")
    return payload


def _receipt(
    root: Path,
    rel: str | None,
    *,
    kind: str,
    territory_id: str,
    edition: str,
    stage: str | None = None,
    require_decision: bool = False,
) -> dict:
    payload = _load_json(root, rel, label=kind)
    if payload.get("schema") != "ddd.catalog-evidence/1.0" or payload.get("kind") != kind:
        _block("DURABLE_ASSET_IDENTITY_INVALID", f"{kind}: schema/kind no coincide")
    if str(payload.get("territory_id") or "") != territory_id or str(payload.get("edition") or "") != str(edition):
        _block("DURABLE_ASSET_IDENTITY_INVALID", f"{kind}: territorio/edición no coincide")
    run_id = _run_id(payload.get("run_id"), label=kind)
    artifact = str(payload.get("artifact_name") or "")
    if not artifact:
        _block("DURABLE_ASSET_IDENTITY_INVALID", f"{kind}: artifact_name ausente")
    digest = _digest(payload.get("artifact_sha256"), label=kind)
    if stage and str(payload.get("stage") or "") != stage:
        _block("DURABLE_ASSET_IDENTITY_INVALID", f"{kind}: stage distinto de {stage}")
    if require_decision and str(payload.get("decision") or "") not in PASS_CERTIFICATIONS:
        _block("DURABLE_ASSET_CERTIFICATION_INVALID", f"{kind}: producto no certificado")
    source_commit = payload.get("source_commit")
    if source_commit is not None and not _SHA1.fullmatch(str(source_commit)):
        _block("DURABLE_ASSET_IDENTITY_INVALID", f"{kind}: source_commit inválido")
    return {**payload, "run_id": run_id, "artifact_name": artifact, "artifact_sha256": digest}


def _canonical_manifest_sha(payload: dict) -> str:
    body = {key: value for key, value in payload.items() if key != "manifest_sha256"}
    encoded = json.dumps(body, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _validate_m06_manifest(
    *, root: Path, payload: dict, territory_id: str, edition: str, run_id: int,
    receipt: dict, contract_path: str | None,
) -> dict:
    identity = payload.get("identity") or {}
    contract = payload.get("contract") or {}
    execution = payload.get("execution") or {}
    artifacts = payload.get("artifacts") or {}
    certification = payload.get("certification") or {}
    inputs = payload.get("inputs") or {}
    if payload.get("schema") != _M06_SCHEMA:
        _block("DURABLE_LINEAGE_UNPROVEN", f"run {run_id}: schema M06 desconocido")
    if payload.get("record_type") not in {"run_time", "post_run_recovery"}:
        _block("DURABLE_LINEAGE_UNPROVEN", f"run {run_id}: tipo de constancia M06 ausente o inválido")
    if _canonical_manifest_sha(payload) != str(payload.get("manifest_sha256") or ""):
        _block("DURABLE_LINEAGE_UNPROVEN", f"run {run_id}: SHA del manifiesto M06 no coincide")
    try:
        manifest_run = int(identity.get("workflow_run_id") or 0)
        manifest_attempt = int(identity.get("workflow_run_attempt") or 0)
    except (TypeError, ValueError):
        manifest_run = manifest_attempt = 0
    if (
        str(identity.get("territory_id") or "") != territory_id
        or str(identity.get("edition") or "") != str(edition)
        or manifest_run != run_id
        or manifest_attempt <= 0
        or not _SHA1.fullmatch(str(identity.get("workflow_sha") or ""))
        or not _SHA1.fullmatch(str(identity.get("checkout_sha") or ""))
    ):
        _block("DURABLE_LINEAGE_UNPROVEN", f"run {run_id}: identidad M06 incompleta o cruzada")
    # El recibo acredita el mismo commit de código que ejecutó la generación.
    # Comparar sólo el formato de cada SHA aceptaría productores contradictorios.
    checkout_sha = str(identity.get("checkout_sha") or "")
    receipt_source_commit = str(receipt.get("source_commit") or "")
    if not _SHA1.fullmatch(receipt_source_commit):
        _block(
            "DURABLE_LINEAGE_UNPROVEN",
            f"run {run_id}: source_commit ausente o inválido en el recibo M06",
        )
    if receipt_source_commit != checkout_sha:
        _block(
            "DURABLE_LINEAGE_INCOMPATIBLE",
            f"run {run_id}: source_commit del recibo M06 no coincide con identity.checkout_sha",
        )
    if not contract_path or str(contract.get("path") or "") != str(contract_path):
        _block("DURABLE_LINEAGE_UNPROVEN", f"run {run_id}: ruta del contrato no coincide")
    params = root / str(contract_path)
    if not params.is_file():
        _block("DURABLE_LINEAGE_UNPROVEN", f"run {run_id}: contrato materializado ausente")
    expected_contract_sha = hashlib.sha256(params.read_bytes()).hexdigest()
    if str(contract.get("sha256") or "") != expected_contract_sha:
        _block("DURABLE_LINEAGE_INCOMPATIBLE", f"run {run_id}: SHA del contrato cambió")

    product = artifacts.get("m06") or {}
    try:
        product_run = _run_id(product.get("run_id"), label="m06_manifest.artifacts.m06")
        _run_id(product.get("artifact_id"), label="m06_manifest.artifacts.m06.artifact_id")
        product_sha = _digest(product.get("artifact_sha256"), label="m06_manifest.artifacts.m06")
    except DurableAssetBlock as exc:
        _block("DURABLE_LINEAGE_UNPROVEN", str(exc))
    if (
        product_run != run_id
        or str(product.get("artifact_name") or "") != str(receipt.get("artifact_name") or "")
        or product_sha != str(receipt.get("artifact_sha256") or "")
        or int(receipt.get("run_id") or 0) != run_id
        or isinstance(product.get("size_in_bytes"), bool)
        or not isinstance(product.get("size_in_bytes"), int)
        or product.get("size_in_bytes") < 0
    ):
        _block("DURABLE_LINEAGE_INCOMPATIBLE", f"run {run_id}: artefacto M06 distinto del recibo registrado")
    decision = str(certification.get("decision") or "")
    if decision not in PASS_CERTIFICATIONS or decision != str(receipt.get("decision") or ""):
        _block("DURABLE_ASSET_CERTIFICATION_INVALID", f"run {run_id}: certificación M06 no coincide con el recibo")
    if certification.get("stage") != "M06_INDEPENDENT_GEOMETRIC_AUDIT":
        _block("DURABLE_ASSET_CERTIFICATION_INVALID", f"run {run_id}: falta auditoría geométrica M06")
    audit_files = certification.get("audit_files")
    if not isinstance(audit_files, dict) or "production_status.json" not in audit_files:
        _block("DURABLE_ASSET_CERTIFICATION_INVALID", f"run {run_id}: evidencias de auditoría incompletas")
    for name, row in audit_files.items():
        if not isinstance(row, dict) or not _SHA256.fullmatch(str(row.get("sha256") or "")):
            _block("DURABLE_ASSET_CERTIFICATION_INVALID", f"run {run_id}: hash de auditoría inválido: {name}")
    if certification.get("production_status_sha256") != audit_files["production_status.json"].get("sha256"):
        _block("DURABLE_ASSET_CERTIFICATION_INVALID", f"run {run_id}: hash de producción contradictorio")

    for label, ref in [
        (f"artifacts.{name}", value) for name, value in artifacts.items() if value is not None
    ] + [
        (f"inputs.{name}", value) for name, value in inputs.items() if name.endswith("_artifact") and value is not None
    ]:
        if not isinstance(ref, dict):
            _block("DURABLE_LINEAGE_UNPROVEN", f"run {run_id}: referencia {label} inválida")
        try:
            _run_id(ref.get("run_id"), label=f"{label}.run_id")
            _run_id(ref.get("artifact_id"), label=f"{label}.artifact_id")
            _digest(ref.get("artifact_sha256"), label=label)
        except DurableAssetBlock as exc:
            _block("DURABLE_LINEAGE_UNPROVEN", str(exc))
        size = ref.get("size_in_bytes")
        if (
            not str(ref.get("artifact_name") or "")
            or isinstance(size, bool)
            or not isinstance(size, int)
            or size < 0
        ):
            _block("DURABLE_LINEAGE_UNPROVEN", f"run {run_id}: referencia {label} incompleta")

    requested = str(execution.get("optimization_algorithm_requested") or "")
    effective = str(execution.get("optimization_algorithm_effective") or "")
    if requested not in {"Canónico", "GerryChain", "GerryChain 25", "GerryChain 50"}:
        _block("DURABLE_LINEAGE_UNPROVEN", f"run {run_id}: estrategia solicitada ausente")
    if not _SHA256.fullmatch(str(execution.get("optimization_evidence_sha256") or "")):
        _block("DURABLE_LINEAGE_UNPROVEN", f"run {run_id}: evidencia de optimización incompleta")
    if requested == "GerryChain 50":
        proof = execution.get("portfolio_proof") or {}
        hashes = proof.get("assignment_hashes")
        if (
            effective != "GerryChain 50"
            or execution.get("fallback") is not False
            or execution.get("gerrychain_entrypoint") != "gerrychain_50"
            or execution.get("require_unique_hashes") is not True
            or execution.get("candidate_count") != 50
            or not isinstance(hashes, list)
            or len(hashes) != 50
            or any(not _SHA256.fullmatch(str(value)) for value in hashes)
            or len(set(hashes)) != 50
            or proof.get("candidate_count") != 50
            or proof.get("unique_assignment_hash_count") != 50
            or not _SHA256.fullmatch(str(proof.get("selected_assignment_hash") or ""))
            or proof.get("selected_assignment_hash") not in hashes
            or not _SHA256.fullmatch(str(proof.get("selected_artifact_sha256") or ""))
            or proof.get("selected_output_sha256") != proof.get("selected_artifact_sha256")
        ):
            _block("DURABLE_LINEAGE_UNPROVEN", f"run {run_id}: portfolio GerryChain 50 incompleto")
    for role in ("m05", "audit"):
        ref = artifacts.get(role) or {}
        try:
            ref_run = _run_id(ref.get("run_id"), label=f"m06_manifest.artifacts.{role}")
            _digest(ref.get("artifact_sha256"), label=f"m06_manifest.artifacts.{role}")
            _run_id(ref.get("artifact_id"), label=f"m06_manifest.artifacts.{role}.artifact_id")
        except DurableAssetBlock as exc:
            _block("DURABLE_LINEAGE_UNPROVEN", str(exc))
        size = ref.get("size_in_bytes")
        if not str(ref.get("artifact_name") or "") or isinstance(size, bool) or not isinstance(size, int) or size < 0:
            _block("DURABLE_LINEAGE_UNPROVEN", f"run {run_id}: referencia de artefacto {role} incompleta")
        if role == "audit" and ref_run != run_id:
            _block("DURABLE_LINEAGE_UNPROVEN", f"run {run_id}: auditoría no pertenece al run M06")
    m04_ref = artifacts.get("m04")
    if m04_ref is not None:
        try:
            _run_id(m04_ref.get("run_id"), label="m06_manifest.artifacts.m04")
            _run_id(m04_ref.get("artifact_id"), label="m06_manifest.artifacts.m04.artifact_id")
            _digest(m04_ref.get("artifact_sha256"), label="m06_manifest.artifacts.m04")
        except (AttributeError, DurableAssetBlock) as exc:
            _block("DURABLE_LINEAGE_UNPROVEN", f"run {run_id}: referencia M04 incompleta: {exc}")
    source_manifest_sha = inputs.get("source_manifest_sha256")
    if not isinstance(source_manifest_sha, str) or not _SHA256.fullmatch(source_manifest_sha):
        _block("DURABLE_LINEAGE_UNPROVEN", f"run {run_id}: manifiesto de fuentes ausente")
    checkpoint = inputs.get("checkpoint_artifact")
    if checkpoint is not None:
        try:
            _run_id(checkpoint.get("run_id"), label="m06_manifest.checkpoint")
            _digest(checkpoint.get("artifact_sha256"), label="m06_manifest.checkpoint")
        except (AttributeError, DurableAssetBlock) as exc:
            _block("DURABLE_LINEAGE_UNPROVEN", f"run {run_id}: referencia de checkpoint incompleta: {exc}")
    if execution.get("checkpoint_run_id") is not None:
        try:
            checkpoint_id = _run_id(execution.get("checkpoint_run_id"), label="m06_manifest.execution.checkpoint_run_id")
            checkpoint_ref_id = _run_id((checkpoint or {}).get("run_id"), label="m06_manifest.checkpoint")
        except (AttributeError, DurableAssetBlock) as exc:
            _block("DURABLE_LINEAGE_UNPROVEN", f"run {run_id}: checkpoint incompleto: {exc}")
        if checkpoint_ref_id != checkpoint_id:
            _block("DURABLE_LINEAGE_INCOMPATIBLE", f"run {run_id}: checkpoint y referencia de entrada difieren")
    return payload


def _manifest(
    root: Path, territory_id: str, edition: str, run_id: int,
    *, receipt: dict | None = None, contract_path: str | None = None,
) -> dict:
    rel = Path("territorios") / territory_id / "evidencia" / "ejecuciones_completas" / f"{run_id}.json"
    path = root / rel
    standalone = False
    if not path.is_file():
        explicit = str((receipt or {}).get("producer_manifest_path") or "")
        if explicit:
            candidate = (root / explicit).resolve()
            if not candidate.is_relative_to(root.resolve()):
                _block("DURABLE_LINEAGE_UNPROVEN", f"run {run_id}: ruta de manifiesto fuera del repositorio")
            path = candidate
        else:
            path = root / "territorios" / territory_id / "evidencia" / "generaciones_m06" / f"{run_id}.json"
        standalone = True
    if not path.is_file():
        _block("DURABLE_LINEAGE_UNPROVEN", f"run {run_id}: manifiesto durable ausente")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        _block("DURABLE_LINEAGE_UNPROVEN", f"run {run_id}: manifiesto durable ilegible")
    if standalone:
        return _validate_m06_manifest(
            root=root, payload=payload, territory_id=territory_id, edition=edition,
            run_id=run_id, receipt=receipt or {}, contract_path=contract_path,
        )
    if (
        payload.get("schema") != "ddd.full-run-manifest/2.1"
        or str(payload.get("territory_id") or "") != territory_id
        or str(payload.get("edition") or "") != str(edition)
        or int(payload.get("workflow_run_id") or 0) != run_id
    ):
        _block("DURABLE_LINEAGE_UNPROVEN", f"run {run_id}: identidad del manifiesto no coincide")
    return payload


def _phase(manifest: dict, prefix: str) -> dict:
    phases = [row for row in manifest.get("phases") or [] if str(row.get("name") or "").startswith(prefix)]
    if len(phases) != 1:
        _block("DURABLE_LINEAGE_UNPROVEN", f"run {manifest.get('workflow_run_id')}: fase {prefix} no es única")
    return phases[0]


def _same_phase_asset(phase: dict, asset: dict, *, label: str) -> None:
    phase_digest = str(phase.get("artifact_digest") or "").removeprefix("sha256:").lower()
    if (
        int(phase.get("run_id") or 0) != int(asset["run_id"])
        or str(phase.get("artifact") or "") != str(asset["artifact_name"])
        or phase_digest != str(asset["artifact_sha256"])
    ):
        _block("DURABLE_LINEAGE_INCOMPATIBLE", f"{label}: el manifiesto no enlaza el activo durable vigente")


def _producer_phase_asset(
    phase: dict,
    asset: dict,
    *,
    label: str,
    require_phase_decision: bool = False,
) -> None:
    _same_phase_asset(phase, asset, label=label)
    if phase.get("executed") is not True or str(phase.get("result") or "") != "success":
        _block(
            "DURABLE_PRODUCER_PHASE_INVALID",
            f"{label}: la fase productora no terminó correctamente",
        )
    if str(phase.get("validation_decision") or "") != "VALIDADO":
        _block(
            "DURABLE_PRODUCER_PHASE_INVALID",
            f"{label}: la fase productora no quedó validada",
        )
    if require_phase_decision and str(phase.get("phase_decision") or "") not in PASS_CERTIFICATIONS:
        _block(
            "DURABLE_PRODUCER_PHASE_INVALID",
            f"{label}: la decisión de la fase productora no certifica el producto",
        )


def validate_durable_assets(
    *,
    root_dir: Path,
    state: dict,
    territory_id: str,
    edition: str,
    territorial_source: dict | None,
    expected_election_id: str | None,
) -> dict:
    root = root_dir.resolve()
    evidence = state.get("evidence") or {}

    source = None
    if state.get("territorial_sources_prepared"):
        source = dict(territorial_source or {})
        if not source:
            _block("DURABLE_ASSET_MISSING", "territorial_source: preparación marcada disponible sin evidencia")
        source["run_id"] = _run_id(source.get("run_id"), label="territorial_source")
        source["artifact_sha256"] = _digest(source.get("artifact_sha256"), label="territorial_source")
        package_digest = str(source.get("package_sha256") or "").removeprefix("sha256:").lower()
        if package_digest and not _SHA256.fullmatch(package_digest):
            _block("DURABLE_ASSET_DIGEST_INVALID", "territorial_source: package_sha256 inválido")
        source["package_sha256"] = package_digest or None
        artifact = str(source.get("artifact_name") or "")
        if not artifact:
            _block("DURABLE_ASSET_IDENTITY_INVALID", "territorial_source: artifact_name ausente")
        source["artifact_name"] = artifact

    territorial_product = None
    if state.get("territorial_product_available"):
        if str(state.get("territorial_certification") or "") not in PASS_CERTIFICATIONS:
            _block("DURABLE_ASSET_CERTIFICATION_INVALID", "territorial_product: catálogo no acredita certificación PASS")
        territorial_product = _receipt(
            root,
            evidence.get("territorial_product"),
            kind="territorial_product",
            territory_id=territory_id,
            edition=edition,
            stage="M06",
            require_decision=True,
        )
        manifest = None
        historical_accreditation = None
        try:
            manifest = _manifest(
                root, territory_id, edition, territorial_product["run_id"],
                receipt=territorial_product, contract_path=state.get("contract_path"),
            )
            if manifest.get("schema") != _M06_SCHEMA:
                _producer_phase_asset(
                    _phase(manifest, "02 ·"),
                    territorial_product,
                    label="territorial_product",
                    require_phase_decision=True,
                )
        except DurableAssetBlock as ordinary_error:
            if territorial_product.get("producer_manifest_path"):
                raise ordinary_error
            try:
                historical_accreditation = derive_historical_territorial_producer(
                    root_dir=root,
                    territory_id=territory_id,
                    edition=str(edition),
                    receipt_rel=str(evidence.get("territorial_product") or ""),
                    asset=territorial_product,
                )
            except HistoricalTerritorialAccreditationBlock as exc:
                _block("DURABLE_HISTORICAL_ACCREDITATION_INVALID", str(exc))
            if historical_accreditation is None:
                raise ordinary_error
            manifest = historical_accreditation.get("manifest")
            territorial_product["producer_accreditation"] = {
                "mode": "historical_derived",
                "path": historical_accreditation["accreditation_path"],
                "historical_mode": historical_accreditation["mode"],
            }
            if manifest is None:
                territorial_product["producer_lineage_scope"] = "M06_ONLY"

        if source and manifest is not None:
            if manifest.get("schema") == _M06_SCHEMA:
                source_ref = (manifest.get("inputs") or {}).get("source_package_artifact") or {}
                try:
                    source_ref_run = _run_id(source_ref.get("run_id"), label="m06_manifest.inputs.source_package")
                    source_ref_digest = _digest(source_ref.get("artifact_sha256"), label="m06_manifest.inputs.source_package")
                except DurableAssetBlock as exc:
                    _block("DURABLE_LINEAGE_UNPROVEN", f"run {territorial_product['run_id']}: {exc}")
                if (
                    source_ref_run != int(source["run_id"])
                    or str(source_ref.get("artifact_name") or "") != str(source["artifact_name"])
                    or source_ref_digest != str(source["artifact_sha256"])
                ):
                    _block(
                        "DURABLE_LINEAGE_INCOMPATIBLE",
                        "territorial_source→territorial_product: artefacto, SHA o run contradice las entradas M06",
                    )
            else:
                source_phase = _phase(manifest, "01 ·")
                phase_artifact = str(source_phase.get("artifact") or "")
                phase_digest = str(source_phase.get("artifact_digest") or "").removeprefix("sha256:").lower()
                if (
                    phase_artifact != str(source["artifact_name"])
                    or phase_digest != str(source["artifact_sha256"])
                ):
                    _block(
                        "DURABLE_LINEAGE_INCOMPATIBLE",
                        "territorial_source→territorial_product: artefacto o SHA contradice el manifiesto productor",
                    )
                if str(source_phase.get("validation_decision") or "") != "VALIDADO":
                    _block(
                        "DURABLE_LINEAGE_INCOMPATIBLE",
                        "territorial_source→territorial_product: la fuente del manifiesto no quedó validada",
                    )
                phase_run = _run_id(source_phase.get("run_id"), label="territorial_source→territorial_product")
                if int(source["run_id"]) != phase_run:
                    source["catalog_run_id"] = source["run_id"]
                    source["run_id"] = phase_run
                _same_phase_asset(
                    source_phase,
                    source,
                    label="territorial_source→territorial_product",
                )

    electoral_source = None
    if state.get("electoral_source_prepared"):
        electoral_source = _receipt(
            root,
            evidence.get("electoral_source"),
            kind="electoral_source",
            territory_id=territory_id,
            edition=edition,
        )
        election_id = str(electoral_source.get("election_id") or "")
        if not election_id or (expected_election_id and election_id != expected_election_id):
            _block("DURABLE_ASSET_IDENTITY_INVALID", "electoral_source: election_id no coincide con el registro vigente")

    electoral_product = None
    rejected_electoral_product = None
    if state.get("electoral_product_available"):
        # El M08 debe ser auténtico y válido ANTES de evaluar si pertenece al
        # M06 territorial vigente. Sólo esa discrepancia permite descartarlo
        # para una reincorporación nueva; cualquier otro defecto bloquea.
        electoral_product = _receipt(
            root,
            evidence.get("electoral_product"),
            kind="electoral_product",
            territory_id=territory_id,
            edition=edition,
            stage="M08",
        )
        manifest = _manifest(
            root, territory_id, edition, electoral_product["run_id"],
            receipt=electoral_product, contract_path=state.get("contract_path"),
        )
        _producer_phase_asset(
            _phase(manifest, "04 ·"),
            electoral_product,
            label="electoral_product",
        )
        if electoral_source:
            _same_phase_asset(_phase(manifest, "03 ·"), electoral_source, label="electoral_source→electoral_product")
        if territorial_product:
            try:
                _same_phase_asset(
                    _phase(manifest, "02 ·"), territorial_product,
                    label="territorial_product→electoral_product",
                )
            except DurableAssetBlock as exc:
                if not str(exc).startswith(
                    "DURABLE_LINEAGE_INCOMPATIBLE: territorial_product→electoral_product:"
                ):
                    raise
                rejected_electoral_product = {
                    "asset": electoral_product,
                    "reason": str(exc),
                    "reusable": False,
                }
                electoral_product = None

    return {
        "territorial_source": source,
        "territorial_product": territorial_product,
        "electoral_source": electoral_source,
        "electoral_product": electoral_product,
        "rejected_electoral_product": rejected_electoral_product,
    }
