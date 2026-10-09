from __future__ import annotations

import hashlib
import io
import json
import re
import zipfile
from pathlib import Path
from typing import Any

from herramientas.validar_puerta_ejecucion import _artifact_name_is_consistent

PASS_DECISIONS = {"PASS", "PASS_WITH_EXCEPTIONS", "PASS_WITH_GOVERNED_EXCEPTIONS"}
_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_SHA1 = re.compile(r"^[0-9a-f]{40}$")
_PRODUCTION_RUN = re.compile(r"^production-(?P<run_id>[1-9][0-9]*)-(?P<attempt>[1-9][0-9]*)$")

# Trust anchors fixed when the original Actions archives were materialized.
# Planning never queries Actions; it requires the durable bytes and provenance
# to match these exact, reviewable materialization results.
_TRUSTED_MATERIALIZATIONS = {
    ("aragon", 36321736287): {
        "source_commit": "2d4ab0f40e6461f9455155246a3238922179146f",
        "product": {
            "name": "ddd-state-36321736287-M06",
            "archive_sha256": "1aa6889ae4e49e49ce2a6b469b6cfbc325d040b30639d5adb8326afde9c89394",
            "artifact_id": 10932782125,
        },
        "gate": {
            "artifact_id": 10933030770,
            "name": "ddd-puerta-territorial_product-36321736287",
            "archive_sha256": "f885e8b325c782badd693fe2174789807fdf678a499ea5ec5c4068c8afca6710",
            "member_name": "puerta.json",
            "content_sha256": "d044c70efc260c6a1646838fcf07cf95df5b433c1a6dca44dacd6a54ffb0d1ad",
        },
        "audit": {
            "artifact_id": 10933135052,
            "name": "ddd-audit-36321736287",
            "archive_sha256": "b8e668142f7801cf5c73ec01cd81811e92151266a86f41ba21f5584e34891c4d",
            "member_name": "production_status.json",
            "content_sha256": "849a15644bae4cd7b3137b2ee96874cbd1a289c8187b3b40709709a28d8af163",
        },
    },
    ("castilla_y_leon", 35889595424): {
        "source_commit": "a041e5bd154c3bf2b01c0accf999771d17127644",
        "product": {
            "name": "ddd-state-35889595424-M06-campaign-35889595424-1--04--castilla_y_leon",
            "archive_sha256": "cfb818ef94bfcf35b64b78dc620a0eadd859c6f95aba1234b2d54898d556016b",
            "artifact_id": 10772774182,
        },
        "gate": {
            "artifact_id": 10773961795,
            "name": "ddd-puerta-territorial_product-35889595424-campaign-35889595424-1--04--castilla_y_leon",
            "archive_sha256": "4d130b6a12494adf5fc5bca2a0bb46fdce2e253a561ebc831bfab4e650f60fca",
            "member_name": "puerta.json",
            "content_sha256": "f375aa583b98902ba68bf7c1bd45b8db8f1104af71962aad801872990f2e81b7",
        },
        "audit": {
            "artifact_id": 10772863961,
            "name": "ddd-audit-35889595424-campaign-35889595424-1--04--castilla_y_leon",
            "archive_sha256": "1a155e24fafe6e948b36673cc68b99099f231297e94f1f36337cfd1614d7af2d",
            "member_name": "production_status.json",
            "content_sha256": "74dfefb61c81e43515751718321515e2489222d5bb807ba2653159480ffe8b47",
        },
    },
}


class HistoricalTerritorialAccreditationBlock(ValueError):
    pass


def _block(code: str, reason: str) -> None:
    raise HistoricalTerritorialAccreditationBlock(f"{code}: {reason}")


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _digest(value: Any, *, label: str) -> str:
    digest = str(value or "").removeprefix("sha256:").lower()
    if not _SHA256.fullmatch(digest):
        _block("HISTORICAL_ACCREDITATION_DIGEST_INVALID", f"{label}: SHA-256 ausente o inválido")
    return digest


def _run_id(value: Any, *, label: str) -> int:
    if isinstance(value, bool):
        _block("HISTORICAL_ACCREDITATION_IDENTITY_INVALID", f"{label}: run_id inválido")
    try:
        run_id = int(value)
    except (TypeError, ValueError):
        run_id = 0
    if run_id <= 0:
        _block("HISTORICAL_ACCREDITATION_IDENTITY_INVALID", f"{label}: run_id inválido")
    return run_id


def _load_json(path: Path, *, label: str) -> dict:
    if not path.is_file():
        _block("HISTORICAL_ACCREDITATION_MISSING", f"{label}: evidencia ausente")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        _block("HISTORICAL_ACCREDITATION_INVALID", f"{label}: JSON ilegible")
    if not isinstance(payload, dict):
        _block("HISTORICAL_ACCREDITATION_INVALID", f"{label}: contenido inválido")
    return payload


def _action_artifact(
    payload: object,
    *,
    label: str,
    run_id: int,
    source_commit: str,
    expected_name: str | None = None,
    expected_archive_digest: str | None = None,
) -> dict:
    if not isinstance(payload, dict):
        _block("HISTORICAL_ACCREDITATION_MISSING", f"{label}: procedencia de Actions ausente")
    artifact_id = _run_id(payload.get("artifact_id"), label=f"{label}.artifact_id")
    name = str(payload.get("name") or "")
    archive_digest = _digest(
        payload.get("archive_sha256") or payload.get("artifact_sha256"),
        label=f"{label}.archive_sha256",
    )
    workflow_run_id = _run_id(payload.get("workflow_run_id"), label=f"{label}.workflow_run_id")
    head_sha = str(payload.get("head_sha") or "")
    if workflow_run_id != run_id:
        _block("HISTORICAL_ACCREDITATION_IDENTITY_INVALID", f"{label}: workflow_run_id no coincide")
    if head_sha != source_commit or not _SHA1.fullmatch(head_sha):
        _block("HISTORICAL_ACCREDITATION_IDENTITY_INVALID", f"{label}: head_sha/source_commit no coincide")
    if not name:
        _block("HISTORICAL_ACCREDITATION_IDENTITY_INVALID", f"{label}: nombre ausente")
    if expected_name is not None and name != expected_name:
        _block("HISTORICAL_ACCREDITATION_IDENTITY_INVALID", f"{label}: nombre no coincide")
    if expected_archive_digest is not None and archive_digest != expected_archive_digest:
        _block("HISTORICAL_ACCREDITATION_DIGEST_MISMATCH", f"{label}: archive SHA no coincide")
    return {
        "artifact_id": artifact_id,
        "name": name,
        "archive_sha256": archive_digest,
        "workflow_run_id": workflow_run_id,
        "head_sha": head_sha,
    }


def materialization_seal_sha256(record: dict) -> str:
    payload = {key: value for key, value in record.items() if key != "materialization"}
    canonical = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return _sha256_bytes(canonical)


def _verify_materialization_seal(record: dict) -> None:
    seal = record.get("materialization")
    if not isinstance(seal, dict):
        _block("HISTORICAL_ACCREDITATION_SEAL_INVALID", "sello de materialización ausente")
    if seal.get("schema") != "ddd.historical-materialization-seal/1.0":
        _block("HISTORICAL_ACCREDITATION_SEAL_INVALID", "schema del sello no reconocido")
    declared = _digest(seal.get("seal_sha256"), label="materialization.seal_sha256")
    actual = materialization_seal_sha256(record)
    if declared != actual:
        _block("HISTORICAL_ACCREDITATION_SEAL_INVALID", "la procedencia materializada fue alterada")


def materialize_actions_evidence(
    *,
    archive_path: Path,
    destination: Path,
    member_name: str,
    artifact_metadata: dict,
    run_id: int,
    source_commit: str,
    expected_artifact_id: int,
    expected_artifact_name: str,
    expected_archive_sha256: str,
) -> dict:
    """Verify an Actions archive once and materialize one exact member as durable evidence."""
    source = _action_artifact(
        artifact_metadata,
        label="actions_materialization",
        run_id=run_id,
        source_commit=source_commit,
        expected_name=expected_artifact_name,
        expected_archive_digest=expected_archive_sha256,
    )
    if source["artifact_id"] != expected_artifact_id:
        _block("HISTORICAL_ACCREDITATION_IDENTITY_INVALID", "artifact ID no coincide al materializar")
    try:
        archive_bytes = archive_path.read_bytes()
    except OSError:
        _block("HISTORICAL_ACCREDITATION_MISSING", "archive de Actions ausente al materializar")
    if _sha256_bytes(archive_bytes) != expected_archive_sha256:
        _block("HISTORICAL_ACCREDITATION_DIGEST_MISMATCH", "archive de Actions alterado")
    try:
        with zipfile.ZipFile(io.BytesIO(archive_bytes)) as archive:
            members = [name for name in archive.namelist() if name == member_name]
            if len(members) != 1:
                _block("HISTORICAL_ACCREDITATION_INVALID", f"miembro {member_name} ausente o duplicado")
            member_bytes = archive.read(member_name)
    except (zipfile.BadZipFile, OSError):
        _block("HISTORICAL_ACCREDITATION_INVALID", "archive de Actions ilegible")
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(member_bytes)
    return {
        "path": str(destination),
        "content_sha256": _sha256_bytes(member_bytes),
        "source": {
            **source,
            "member_name": member_name,
            "verified_at_materialization": True,
        },
    }


def _sealed_evidence(
    *,
    root: Path,
    record: dict,
    evidence_name: str,
    territory_id: str,
    run_id: int,
    source_commit: str,
    member_name: str,
    trusted: dict,
) -> tuple[dict, dict]:
    sealed = record.get("sealed_evidence")
    if not isinstance(sealed, dict):
        _block("HISTORICAL_ACCREDITATION_MISSING", "bloque sealed_evidence ausente")
    evidence = sealed.get(evidence_name)
    if not isinstance(evidence, dict):
        _block("HISTORICAL_ACCREDITATION_MISSING", f"{evidence_name}: evidencia durable ausente")
    expected_rel = (
        Path("territorios")
        / territory_id
        / "evidencia"
        / "acreditaciones_historicas"
        / str(run_id)
        / "originales"
        / member_name
    )
    rel = Path(str(evidence.get("path") or ""))
    if rel != expected_rel or rel.is_absolute() or ".." in rel.parts:
        _block("HISTORICAL_ACCREDITATION_IDENTITY_INVALID", f"{evidence_name}: ruta durable no canónica")
    expected_content_digest = _digest(
        evidence.get("content_sha256"),
        label=f"{evidence_name}.content_sha256",
    )
    if expected_content_digest != trusted["content_sha256"]:
        _block(
            "HISTORICAL_ACCREDITATION_TRUST_ANCHOR_MISMATCH",
            f"{evidence_name}: content SHA no coincide con la materialización original",
        )
    source_payload = evidence.get("source")
    source = _action_artifact(
        source_payload,
        label=f"{evidence_name}.source",
        run_id=run_id,
        source_commit=source_commit,
        expected_name=trusted["name"],
        expected_archive_digest=trusted["archive_sha256"],
    )
    if (
        not isinstance(source_payload, dict)
        or source["artifact_id"] != trusted["artifact_id"]
        or source_payload.get("verified_at_materialization") is not True
        or str(source_payload.get("member_name") or "") != trusted["member_name"]
        or trusted["member_name"] != member_name
    ):
        _block(
            "HISTORICAL_ACCREDITATION_TRUST_ANCHOR_MISMATCH",
            f"{evidence_name}: procedencia no coincide con la materialización original",
        )

    path = root / rel
    if not path.is_file():
        _block("HISTORICAL_ACCREDITATION_MISSING", f"{evidence_name}: evidencia original durable ausente")
    try:
        raw = path.read_bytes()
    except OSError:
        _block("HISTORICAL_ACCREDITATION_MISSING", f"{evidence_name}: evidencia original durable ilegible")
    if _sha256_bytes(raw) != expected_content_digest:
        _block("HISTORICAL_ACCREDITATION_EVIDENCE_TAMPERED", f"{evidence_name}: contenido durable alterado")
    try:
        payload = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        _block("HISTORICAL_ACCREDITATION_INVALID", f"{evidence_name}: JSON durable inválido")
    if not isinstance(payload, dict):
        _block("HISTORICAL_ACCREDITATION_INVALID", f"{evidence_name}: contenido durable inválido")
    return payload, source


def _phase(manifest: dict, prefix: str) -> dict:
    rows = [row for row in manifest.get("phases") or [] if str(row.get("name") or "").startswith(prefix)]
    if len(rows) != 1:
        _block("HISTORICAL_ACCREDITATION_MANIFEST_INVALID", f"fase {prefix} ausente o no única")
    return rows[0]


def _same_asset(phase: dict, asset: dict) -> None:
    if (
        _run_id(phase.get("run_id"), label="manifest.phase.run_id") != int(asset["run_id"])
        or str(phase.get("artifact") or "") != str(asset["artifact_name"])
        or _digest(phase.get("artifact_digest"), label="manifest.phase.artifact_digest")
        != str(asset["artifact_sha256"])
    ):
        _block("HISTORICAL_ACCREDITATION_MANIFEST_INVALID", "la fase M06 no enlaza el receipt vigente")


def _validate_gate(
    payload: dict,
    *,
    territory_id: str,
    edition: str,
    run_id: int,
    asset: dict,
) -> dict:
    if (
        payload.get("schema") != "ddd.puerta-validacion/1.0"
        or payload.get("phase") != "territorial_product"
        or str(payload.get("territory_id") or "") != territory_id
        or str(payload.get("edition") or "") != edition
        or _run_id(payload.get("run_id"), label="gate.run_id") != run_id
        or str(payload.get("artifact_name") or "") != asset["artifact_name"]
        or _digest(payload.get("artifact_digest"), label="gate.artifact_digest")
        != asset["artifact_sha256"]
    ):
        _block("HISTORICAL_ACCREDITATION_GATE_INVALID", "la puerta durable no identifica exactamente el M06 acreditado")
    return payload


def _validate_audit(
    status: dict,
    *,
    territory_id: str,
    run_id: int,
    receipt_decision: str,
) -> dict:
    production_run = _PRODUCTION_RUN.fullmatch(str(status.get("run_id") or ""))
    if (
        status.get("schema") != "ddd.production-status/1.3"
        or str(status.get("territory_id") or "") != territory_id
        or not production_run
        or int(production_run.group("run_id")) != run_id
        or str(status.get("to_stage") or "") != "M06"
        or str(status.get("scope_through_stage") or "") != "M06"
        or str(status.get("execution_outcome") or "") != "success"
        or str(status.get("geometric_outcome") or "") != "success"
        or str(status.get("decision") or "") not in PASS_DECISIONS
        or str(status.get("territorial_certification_status") or "") not in PASS_DECISIONS
        or str(status.get("decision") or "") != receipt_decision
        or str(status.get("territorial_certification_status") or "") != receipt_decision
        or str(status.get("population_evidence_status") or "") != "VALID"
        or str(status.get("population_decision") or "") != "TARGET_MET"
        or int(status.get("population_hard_constraints_after") or 0) != 0
    ):
        _block("HISTORICAL_ACCREDITATION_AUDIT_INVALID", "la auditoría durable no acredita exactamente el M06")
    return status


def derive_historical_territorial_producer(
    *,
    root_dir: Path,
    territory_id: str,
    edition: str,
    receipt_rel: str,
    asset: dict,
) -> dict | None:
    root = root_dir.resolve()
    run_id = _run_id(asset.get("run_id"), label="territorial_product")
    path = (
        root
        / "territorios"
        / territory_id
        / "evidencia"
        / "acreditaciones_historicas"
        / f"{run_id}.json"
    )
    if not path.is_file():
        return None

    record = _load_json(path, label="acreditación histórica")
    source_commit = str(asset.get("source_commit") or "")
    if not _SHA1.fullmatch(source_commit):
        _block("HISTORICAL_ACCREDITATION_IDENTITY_INVALID", "receipt sin source_commit válido")
    if (
        record.get("schema") != "ddd.historical-territorial-accreditation/1.1"
        or record.get("kind") != "territorial_product"
        or str(record.get("territory_id") or "") != territory_id
        or str(record.get("edition") or "") != edition
        or _run_id(record.get("run_id"), label="record.run_id") != run_id
        or str(record.get("source_commit") or "") != source_commit
        or str(record.get("receipt_path") or "") != str(receipt_rel)
    ):
        _block("HISTORICAL_ACCREDITATION_IDENTITY_INVALID", "identidad base de la acreditación no coincide con el receipt")
    _verify_materialization_seal(record)

    # Preserve the historical namespace negatives explicitly, before applying
    # the fixed trust anchor for the known product identity.
    pre_historical = record.get("historical_manifest")
    if isinstance(pre_historical, dict) and str(pre_historical.get("mode") or "") == "legacy_campaign_namespace_false_rejection":
        pre_namespace = str(pre_historical.get("artifact_namespace") or "")
        pre_canonical = f"ddd-state-{run_id}-M06"
        if (
            not pre_namespace
            or str(asset.get("artifact_name") or "") != f"{pre_canonical}-{pre_namespace}"
            or not _artifact_name_is_consistent(
                "territorial_product",
                territory_id,
                edition,
                str(run_id),
                str(asset.get("artifact_name") or ""),
                pre_namespace,
            )
        ):
            _block(
                "HISTORICAL_ACCREDITATION_NAMESPACE_INVALID",
                "namespace histórico no satisface las reglas estrictas de #129",
            )

    trusted = _TRUSTED_MATERIALIZATIONS.get((territory_id, run_id))
    if not isinstance(trusted, dict):
        _block(
            "HISTORICAL_ACCREDITATION_TRUST_ANCHOR_MISSING",
            "no existe materialización histórica confiable para este territorio/run",
        )
    if source_commit != trusted["source_commit"]:
        _block(
            "HISTORICAL_ACCREDITATION_TRUST_ANCHOR_MISMATCH",
            "source_commit no coincide con la materialización original",
        )
    product_anchor = trusted["product"]
    if (
        str(asset.get("artifact_name") or "") != product_anchor["name"]
        or str(asset.get("artifact_sha256") or "") != product_anchor["archive_sha256"]
    ):
        _block(
            "HISTORICAL_ACCREDITATION_TRUST_ANCHOR_MISMATCH",
            "receipt/producto no coincide con la materialización original",
        )

    original = _action_artifact(
        record.get("original_artifact"),
        label="original_artifact",
        run_id=run_id,
        source_commit=source_commit,
        expected_name=product_anchor["name"],
        expected_archive_digest=product_anchor["archive_sha256"],
    )
    if original["artifact_id"] != product_anchor["artifact_id"]:
        _block(
            "HISTORICAL_ACCREDITATION_TRUST_ANCHOR_MISMATCH",
            "artifact ID del producto no coincide con la materialización original",
        )

    gate_payload, gate_source = _sealed_evidence(
        root=root,
        record=record,
        evidence_name="gate",
        territory_id=territory_id,
        run_id=run_id,
        source_commit=source_commit,
        member_name="puerta.json",
        trusted=trusted["gate"],
    )
    gate = _validate_gate(
        gate_payload,
        territory_id=territory_id,
        edition=edition,
        run_id=run_id,
        asset=asset,
    )
    receipt_decision = str(asset.get("decision") or "")
    if receipt_decision not in PASS_DECISIONS:
        _block("HISTORICAL_ACCREDITATION_RECEIPT_INVALID", "receipt no certifica PASS")

    audit_payload, audit_source = _sealed_evidence(
        root=root,
        record=record,
        evidence_name="audit",
        territory_id=territory_id,
        run_id=run_id,
        source_commit=source_commit,
        member_name="production_status.json",
        trusted=trusted["audit"],
    )
    audit = _validate_audit(
        audit_payload,
        territory_id=territory_id,
        run_id=run_id,
        receipt_decision=receipt_decision,
    )

    historical = record.get("historical_manifest")
    if not isinstance(historical, dict):
        _block("HISTORICAL_ACCREDITATION_MISSING", "tratamiento histórico del manifiesto ausente")
    mode = str(historical.get("mode") or "")
    manifest_path = (
        root / "territorios" / territory_id / "evidencia" / "ejecuciones_completas" / f"{run_id}.json"
    )

    if mode == "missing_durable_manifest":
        if manifest_path.exists():
            _block("HISTORICAL_ACCREDITATION_MANIFEST_INVALID", "el registro declara manifiesto ausente pero existe uno durable")
        if (
            str(gate.get("decision") or "") != "VALIDADO"
            or str(gate.get("phase_decision") or "") != receipt_decision
            or list(gate.get("reasons") or []) != []
        ):
            _block("HISTORICAL_ACCREDITATION_GATE_INVALID", "la puerta histórica no acredita limpiamente el producto")
        phase = {
            "name": "02 · Generación de Distritos Autonómicos",
            "executed": True,
            "result": "success",
            "run_id": run_id,
            "artifact": asset["artifact_name"],
            "artifact_digest": f"sha256:{asset['artifact_sha256']}",
            "validation_decision": "VALIDADO",
            "phase_decision": receipt_decision,
            "derived_from": "historical_accreditation",
        }
        return {
            "phase": phase,
            "manifest": None,
            "accreditation_path": str(path.relative_to(root)),
            "mode": mode,
            "original_artifact": original,
            "gate": gate,
            "gate_source": gate_source,
            "audit": audit,
            "audit_source": audit_source,
        }

    if mode != "legacy_campaign_namespace_false_rejection":
        _block("HISTORICAL_ACCREDITATION_MODE_INVALID", f"modo histórico no admitido: {mode!r}")

    manifest = _load_json(manifest_path, label="manifiesto histórico durable")
    if (
        manifest.get("schema") != "ddd.full-run-manifest/2.1"
        or str(manifest.get("territory_id") or "") != territory_id
        or str(manifest.get("edition") or "") != edition
        or _run_id(manifest.get("workflow_run_id"), label="manifest.workflow_run_id") != run_id
        or str(manifest.get("source_sha") or "") != source_commit
    ):
        _block("HISTORICAL_ACCREDITATION_MANIFEST_INVALID", "identidad del manifiesto histórico no coincide")

    _action_artifact(
        historical.get("actions_artifact"),
        label="historical_manifest",
        run_id=run_id,
        source_commit=source_commit,
    )
    producer = _phase(manifest, "02 ·")
    _same_asset(producer, asset)
    if (
        producer.get("executed") is not True
        or str(producer.get("result") or "") != "success"
        or str(producer.get("validation_decision") or "") != "BLOQUEADO"
        or producer.get("phase_decision") is not None
    ):
        _block("HISTORICAL_ACCREDITATION_MANIFEST_INVALID", "el hecho histórico BLOQUEADO no se conserva")

    reason = "NOMBRE_ARTEFACTO_NO_COINCIDE_CON_RUN"
    if (
        str(gate.get("decision") or "") != "BLOQUEADO"
        or gate.get("phase_decision") is not None
        or list(gate.get("reasons") or []) != [reason]
    ):
        _block("HISTORICAL_ACCREDITATION_GATE_INVALID", "el bloqueo histórico no es exclusivamente el falso rechazo del namespace")

    namespace = str(historical.get("artifact_namespace") or "")
    canonical = f"ddd-state-{run_id}-M06"
    if (
        not namespace
        or asset["artifact_name"] != f"{canonical}-{namespace}"
        or not _artifact_name_is_consistent(
            "territorial_product",
            territory_id,
            edition,
            str(run_id),
            asset["artifact_name"],
            namespace,
        )
    ):
        _block("HISTORICAL_ACCREDITATION_NAMESPACE_INVALID", "namespace histórico no satisface las reglas estrictas de #129")

    phase = {
        **producer,
        "validation_decision": "VALIDADO",
        "phase_decision": receipt_decision,
        "historical_validation_decision": "BLOQUEADO",
        "historical_block_reason": reason,
        "derived_from": "historical_accreditation",
    }
    return {
        "phase": phase,
        "manifest": manifest,
        "accreditation_path": str(path.relative_to(root)),
        "mode": mode,
        "original_artifact": original,
        "gate": gate,
        "gate_source": gate_source,
        "audit": audit,
        "audit_source": audit_source,
    }
