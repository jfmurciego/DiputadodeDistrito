from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

PASS_CERTIFICATIONS = {"PASS", "PASS_WITH_EXCEPTIONS", "PASS_WITH_GOVERNED_EXCEPTIONS"}
_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_SHA1 = re.compile(r"^[0-9a-f]{40}$")


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


def _manifest(root: Path, territory_id: str, edition: str, run_id: int) -> dict:
    rel = Path("territorios") / territory_id / "evidencia" / "ejecuciones_completas" / f"{run_id}.json"
    path = root / rel
    if not path.is_file():
        _block("DURABLE_LINEAGE_UNPROVEN", f"run {run_id}: manifiesto durable ausente")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        _block("DURABLE_LINEAGE_UNPROVEN", f"run {run_id}: manifiesto durable ilegible")
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
        manifest = _manifest(root, territory_id, edition, territorial_product["run_id"])
        _producer_phase_asset(
            _phase(manifest, "02 ·"),
            territorial_product,
            label="territorial_product",
            require_phase_decision=True,
        )
        if source:
            _same_phase_asset(_phase(manifest, "01 ·"), source, label="territorial_source→territorial_product")

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
    if state.get("electoral_product_available"):
        electoral_product = _receipt(
            root,
            evidence.get("electoral_product"),
            kind="electoral_product",
            territory_id=territory_id,
            edition=edition,
            stage="M08",
        )
        manifest = _manifest(root, territory_id, edition, electoral_product["run_id"])
        _producer_phase_asset(
            _phase(manifest, "04 ·"),
            electoral_product,
            label="electoral_product",
        )
        if territorial_product:
            _same_phase_asset(_phase(manifest, "02 ·"), territorial_product, label="territorial_product→electoral_product")
        if electoral_source:
            _same_phase_asset(_phase(manifest, "03 ·"), electoral_source, label="electoral_source→electoral_product")

    return {
        "territorial_source": source,
        "territorial_product": territorial_product,
        "electoral_source": electoral_source,
        "electoral_product": electoral_product,
    }
