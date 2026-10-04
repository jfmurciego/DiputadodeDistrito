#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from datetime import datetime
from pathlib import Path

import yaml

from ddd_core.electoral_contract import (
    STRUCTURAL_PROVENANCE_SCHEMA,
    validate_structural_provenance_document,
)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _static_election_identity_mode(contract: dict, manifest: dict) -> str:
    contract_id = str(contract.get("election_id") or "")
    contract_date = str(contract.get("election_date") or "")
    package_id = str(manifest.get("election_id") or "")
    package_date = str(manifest.get("election_date") or "")
    if not contract_id or not contract_date or not package_id or not package_date:
        raise ValueError("identidad electoral incompleta entre contrato estático y paquete")
    if contract_date != package_date:
        raise ValueError("election_date del contrato electoral estático no coincide con el paquete")
    if contract_id == package_id:
        return "exact"
    if contract_id == f"{package_id}-{package_date}":
        return "legacy_date_suffix_alias"
    raise ValueError("election_id del contrato electoral estático no coincide con el paquete")


def _validate_selected_source(package: Path, manifest: dict) -> tuple[dict, Path, str]:
    selected = manifest.get("selected_source") or {}
    source = package / str(selected.get("path") or "")
    if not source.is_file():
        raise ValueError("fuente electoral ausente del paquete")
    actual = sha256(source).lower()
    declared = str(selected.get("sha256") or "").lower()
    if not declared or actual != declared:
        raise ValueError("hash interno del paquete electoral no coincide")
    if source.stat().st_size != int(selected.get("bytes") or -1):
        raise ValueError("tamaño interno del paquete electoral no coincide")
    return selected, source, actual


def _hex64(value: object) -> bool:
    text = str(value or "").lower()
    return len(text) == 64 and all(ch in "0123456789abcdef" for ch in text)


def _aware_timestamp(value: object, *, label: str) -> datetime:
    text = str(value or "").strip()
    try:
        instant = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"ELECCIONESDB_RETRIEVED_AT_BLOCK: {label} ausente o inválido") from exc
    if instant.tzinfo is None:
        raise ValueError(f"ELECCIONESDB_RETRIEVED_AT_BLOCK: {label} debe incluir zona horaria")
    return instant


def _verified_eleccionesdb_retrieved_at(
    manifest: dict,
    source: dict,
    *,
    root: Path,
) -> tuple[str, dict]:
    """Resolve legacy retrieved_at only from durable upstream artifact evidence."""
    if str(manifest.get("adapter") or "") != "eleccionesdb_sqlite/1.0":
        raise ValueError("contrato electoral embebido sin retrieved_at")
    if str(manifest.get("source_status") or "") != "VERIFIED_SOURCE_CHAIN":
        raise ValueError("ELECCIONESDB_RETRIEVED_AT_BLOCK: cadena de procedencia no está verificada")

    snapshot = str(manifest.get("snapshot_sha256") or "").lower()
    upstream = source.get("upstream_snapshot") or {}
    if not _hex64(snapshot) or str(upstream.get("snapshot_sha256") or "").lower() != snapshot:
        raise ValueError(
            "ELECCIONESDB_RETRIEVED_AT_BLOCK: snapshot SHA-256 no acredita la procedencia"
        )
    provenance = upstream.get("provenance") or manifest.get("provenance") or []
    if not isinstance(provenance, list) or not any(
        isinstance(row, dict) and (str(row.get("url") or "").strip() or str(row.get("fuente") or "").strip())
        for row in provenance
    ):
        raise ValueError(
            "ELECCIONESDB_RETRIEVED_AT_BLOCK: procedencia upstream verificable ausente"
        )

    registry_path = root / "configuracion/procedencia_eleccionesdb_legacy.json"
    if not registry_path.is_file():
        raise ValueError(
            "ELECCIONESDB_RETRIEVED_AT_BLOCK: evidencia temporal legacy durable ausente"
        )
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    if registry.get("schema") != "ddd-eleccionesdb-legacy-provenance/1.0":
        raise ValueError(
            "ELECCIONESDB_RETRIEVED_AT_BLOCK: schema de procedencia legacy inválido"
        )
    entry = (registry.get("snapshots") or {}).get(snapshot)
    if not isinstance(entry, dict):
        raise ValueError(
            "ELECCIONESDB_RETRIEVED_AT_BLOCK: snapshot legacy sin procedencia temporal acreditada"
        )
    if str(entry.get("rule") or "") != "retrieved_at_equals_upstream_artifact_created_at":
        raise ValueError(
            "ELECCIONESDB_RETRIEVED_AT_BLOCK: regla temporal legacy no reconocida"
        )

    retrieved_at = str(entry.get("retrieved_at") or "").strip()
    retrieved_instant = _aware_timestamp(retrieved_at, label="retrieved_at legacy")
    upstream_artifact = entry.get("upstream_artifact") or {}
    upstream_created_at = str(upstream_artifact.get("created_at") or "").strip()
    upstream_instant = _aware_timestamp(
        upstream_created_at,
        label="created_at del artefacto upstream",
    )
    if retrieved_instant != upstream_instant:
        raise ValueError(
            "ELECCIONESDB_RETRIEVED_AT_BLOCK: retrieved_at no coincide con created_at upstream"
        )
    if (
        str(upstream_artifact.get("repository") or "") != "hmeleiro/eleccionesdb-etl"
        or str(upstream_artifact.get("name") or "") != "eleccionesdb-descargas"
        or int(upstream_artifact.get("artifact_id") or 0) <= 0
        or not _hex64(upstream_artifact.get("extracted_sqlite_sha256"))
    ):
        raise ValueError(
            "ELECCIONESDB_RETRIEVED_AT_BLOCK: identidad o digest del artefacto upstream inválidos"
        )

    snapshot_artifact = entry.get("snapshot_artifact") or {}
    if (
        str(snapshot_artifact.get("repository") or "") != "jfmurciego/DiputadodeDistrito"
        or str(snapshot_artifact.get("name") or "") != "ddd-eleccionesdb-snapshot"
        or int(snapshot_artifact.get("producer_run_id") or 0) <= 0
        or int(snapshot_artifact.get("artifact_id") or 0) <= 0
        or str(snapshot_artifact.get("snapshot_sha256") or "").lower() != snapshot
        or not _hex64(snapshot_artifact.get("artifact_sha256"))
    ):
        raise ValueError(
            "ELECCIONESDB_RETRIEVED_AT_BLOCK: identidad o digest del snapshot durable inválidos"
        )
    snapshot_created_at = str(snapshot_artifact.get("created_at") or "").strip()
    snapshot_instant = _aware_timestamp(
        snapshot_created_at,
        label="created_at del snapshot durable",
    )
    if snapshot_instant < upstream_instant:
        raise ValueError(
            "ELECCIONESDB_RETRIEVED_AT_BLOCK: snapshot durable anterior al artefacto upstream"
        )

    return retrieved_at, {
        "mode": "verified_legacy_snapshot_registry",
        "rule": "retrieved_at_equals_upstream_artifact_created_at",
        "snapshot_sha256": snapshot,
        "upstream_artifact": {
            "repository": upstream_artifact["repository"],
            "name": upstream_artifact["name"],
            "artifact_id": int(upstream_artifact["artifact_id"]),
            "created_at": upstream_created_at,
            "extracted_sqlite_sha256": str(
                upstream_artifact["extracted_sqlite_sha256"]
            ).lower(),
        },
        "snapshot_artifact": {
            "producer_run_id": int(snapshot_artifact["producer_run_id"]),
            "artifact_id": int(snapshot_artifact["artifact_id"]),
            "created_at": snapshot_created_at,
            "artifact_sha256": str(snapshot_artifact["artifact_sha256"]).lower(),
        },
    }


def _load_package_structural_provenance(
    *,
    package: Path,
    manifest: dict,
    source_hash: str,
    adapter: dict,
) -> tuple[Path, str, dict] | None:
    manifest_decl = manifest.get("structural_provenance")
    adapter_decl = adapter.get("structural_provenance")
    if manifest_decl is None and adapter_decl is None:
        return None
    if not isinstance(manifest_decl, dict) or not isinstance(adapter_decl, dict):
        raise ValueError(
            "paquete y contrato deben declarar conjuntamente "
            "structural_provenance"
        )
    manifest_path = str(manifest_decl.get("path") or "").strip()
    adapter_path = str(adapter_decl.get("path") or "").strip()
    manifest_sha = str(manifest_decl.get("sha256") or "").lower()
    adapter_sha = str(adapter_decl.get("sha256") or "").lower()
    if (
        not manifest_path
        or manifest_path != adapter_path
        or not _hex64(manifest_sha)
        or manifest_sha != adapter_sha
        or str(
            manifest_decl.get("merged_source_sha256") or ""
        ).lower() != source_hash
    ):
        raise ValueError(
            "declaración estructural del paquete no coincide con contrato"
        )
    sidecar = package / manifest_path
    if not sidecar.is_file() or sha256(sidecar).lower() != manifest_sha:
        raise ValueError(
            "procedencia estructural embebida ausente o alterada"
        )
    document = json.loads(sidecar.read_text(encoding="utf-8"))
    validate_structural_provenance_document(
        document,
        context="procedencia estructural del paquete",
        expected_source_sha256=source_hash,
    )
    return sidecar, manifest_sha, document


def _validate_static_structural_provenance(
    *,
    root: Path,
    manifest: dict,
    source_hash: str,
    adapter: dict,
) -> str | None:
    contract_decl = adapter.get("structural_provenance")
    if contract_decl is None:
        if manifest.get("structural_provenance") is not None:
            raise ValueError(
                "paquete declara procedencia estructural ausente "
                "del contrato estático"
            )
        return None
    if not isinstance(contract_decl, dict):
        raise ValueError("structural_provenance contractual inválido")
    path_raw = str(contract_decl.get("path") or "").strip()
    expected = str(contract_decl.get("sha256") or "").lower()
    if not path_raw or not _hex64(expected):
        raise ValueError("structural_provenance contractual incompleto")
    sidecar = root / path_raw
    if not sidecar.is_file() or sha256(sidecar).lower() != expected:
        raise ValueError("sidecar estructural contractual ausente o alterado")
    document = json.loads(sidecar.read_text(encoding="utf-8"))
    validate_structural_provenance_document(
        document,
        context="procedencia estructural contractual",
        expected_source_sha256=source_hash,
    )
    packaged = manifest.get("structural_provenance")
    if packaged is not None:
        if not isinstance(packaged, dict):
            raise ValueError("procedencia estructural del paquete inválida")
        package_path = str(packaged.get("path") or "").strip()
        package_sha = str(packaged.get("sha256") or "").lower()
        if (
            not package_path
            or package_sha != expected
            or str(
                packaged.get("merged_source_sha256") or ""
            ).lower() != source_hash
        ):
            raise ValueError(
                "sidecar estructural del paquete no coincide "
                "con el contrato estático"
            )
    return expected


def _materialize_embedded_contract(
    *,
    package: Path,
    manifest: dict,
    root: Path,
    territory_id: str,
    edition: str,
    source: Path,
    source_hash: str,
    materialize: bool,
) -> dict:
    embedded = manifest.get("embedded_contract") or {}
    contract_rel = str(embedded.get("election_contract") or "")
    dictionary_rel = str(embedded.get("party_dictionary") or "")
    if not contract_rel or not dictionary_rel:
        raise ValueError("paquete sin contrato electoral embebido completo")
    contract_src = package / contract_rel
    dictionary_src = package / dictionary_rel
    if not contract_src.is_file() or not dictionary_src.is_file():
        raise ValueError("contrato o diccionario electoral embebido ausente")
    expected_contract_hash = str(embedded.get("contract_sha256") or "").lower()
    expected_dictionary_hash = str(embedded.get("party_dictionary_sha256") or "").lower()
    if not expected_contract_hash or sha256(contract_src).lower() != expected_contract_hash:
        raise ValueError("hash del contrato electoral embebido no coincide")
    if not expected_dictionary_hash or sha256(dictionary_src).lower() != expected_dictionary_hash:
        raise ValueError("hash del diccionario electoral embebido no coincide")

    contract = json.loads(contract_src.read_text(encoding="utf-8"))
    if contract.get("schema_family") != "ddd-election" or contract.get("schema_version") != "1.0.0":
        raise ValueError("contrato electoral embebido con schema inválido")
    if str(contract.get("territory_id") or "") != territory_id:
        raise ValueError("contrato electoral embebido pertenece a otro territorio")
    if str(contract.get("election_id") or "") != str(manifest.get("election_id") or ""):
        raise ValueError("election_id del contrato electoral embebido no coincide con el paquete")
    if str(contract.get("election_date") or "") != str(manifest.get("election_date") or ""):
        raise ValueError("election_date del contrato electoral embebido no coincide con el paquete")
    sources = contract.get("sources") or []
    if len(sources) != 1 or str(sources[0].get("sha256") or "").lower() != source_hash:
        raise ValueError("contrato electoral embebido no referencia la fuente congelada")

    runtime_rel = Path(".ddd-electoral-runtime") / territory_id / str(edition)
    runtime_dir = root / runtime_rel
    runtime_contract = runtime_dir / "election_contract.json"
    runtime_dictionary = runtime_dir / "party_dictionary.json"
    runtime_source = runtime_dir / "data" / source.name
    runtime_structural = (
        runtime_dir / "evidence" / "structural_provenance.json"
    )

    runtime_source_contract = dict(sources[0])
    runtime_adapter = dict(runtime_source_contract.get("adapter") or {})
    structural = _load_package_structural_provenance(
        package=package,
        manifest=manifest,
        source_hash=source_hash,
        adapter=runtime_adapter,
    )
    if (
        str(manifest.get("adapter") or "") == "eleccionesdb_sqlite/1.0"
        and not str(runtime_source_contract.get("retrieved_at") or "").strip()
    ):
        retrieved_at, provenance = _verified_eleccionesdb_retrieved_at(
            manifest,
            runtime_source_contract,
            root=root,
        )
        runtime_source_contract["retrieved_at"] = retrieved_at
        runtime_source_contract["retrieved_at_provenance"] = provenance

    if materialize:
        runtime_source.parent.mkdir(parents=True, exist_ok=True)
        runtime_dictionary.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, runtime_source)
        shutil.copy2(dictionary_src, runtime_dictionary)
        if structural is not None:
            structural_src, structural_sha, _ = structural
            runtime_structural.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(structural_src, runtime_structural)
            if sha256(runtime_structural).lower() != structural_sha:
                raise ValueError(
                    "materialización alteró la procedencia estructural"
                )
            runtime_adapter["structural_provenance"] = {
                "path": runtime_structural.relative_to(root).as_posix(),
                "sha256": structural_sha,
            }
            runtime_source_contract["adapter"] = runtime_adapter
        runtime_contract_payload = dict(contract)
        runtime_contract_payload["sources"] = [runtime_source_contract]
        runtime_source_contract["path"] = runtime_source.relative_to(root).as_posix()
        runtime_contract_payload["party_dictionary"] = dict(contract.get("party_dictionary") or {})
        runtime_contract_payload["party_dictionary"]["path"] = runtime_dictionary.relative_to(root).as_posix()
        runtime_contract_payload["party_dictionary"]["sha256"] = sha256(runtime_dictionary)
        runtime_contract.write_text(
            json.dumps(runtime_contract_payload, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        if sha256(runtime_source).lower() != source_hash:
            raise ValueError("materialización electoral alteró el hash")

    return {
        "mode": "embedded_runtime_contract",
        "runtime_contract_path": runtime_contract.relative_to(root).as_posix(),
        "contract_sha256": expected_contract_hash,
        "party_dictionary_sha256": expected_dictionary_hash,
        "structural_provenance_sha256": (
            structural[1] if structural is not None else None
        ),
        "election_identity_mode": "exact",
        "contract_election_id": contract.get("election_id"),
        "package_election_id": manifest.get("election_id"),
    }


def validate_package(
    *,
    package: Path,
    params: Path,
    territory_id: str,
    edition: str,
    root: Path,
    materialize: bool = False,
) -> dict:
    root = root.resolve()
    manifest = json.loads((package / "manifest.json").read_text(encoding="utf-8"))
    if manifest.get("schema") != "ddd-electoral-package/1.0":
        raise ValueError("schema electoral package inválido")
    if manifest.get("decision") not in {"REUSE", "ACQUIRE"}:
        raise ValueError("paquete electoral no utilizable")
    if str(manifest.get("territory_id")) != territory_id or str(manifest.get("edition")) != str(edition):
        raise ValueError("territorio o edición del paquete electoral no coincide")
    selected, source, actual = _validate_selected_source(package, manifest)

    cfg = yaml.safe_load(params.read_text(encoding="utf-8")) or {}
    meta = cfg.get("meta") or {}
    if str(meta.get("territory_id") or "") != territory_id or str(meta.get("year") or "") != str(edition):
        raise ValueError("contrato territorial no corresponde al paquete electoral")
    m07 = (cfg.get("modulos") or {}).get("modulo_07_agregar_resultados_electorales") or {}
    contract_raw = m07.get("election_contract")

    if contract_raw:
        contract_path = root / str(contract_raw)
        contract = json.loads(contract_path.read_text(encoding="utf-8"))
        if contract.get("schema_family") != "ddd-election" or contract.get("schema_version") != "1.0.0":
            raise ValueError("contrato electoral estático con schema inválido")
        if str(contract.get("territory_id") or "") != territory_id:
            raise ValueError("contrato electoral estático pertenece a otro territorio")
        election_identity_mode = _static_election_identity_mode(contract, manifest)
        matches = [s for s in (contract.get("sources") or []) if str(s.get("sha256") or "").lower() == actual]
        if len(matches) != 1:
            raise ValueError("hash de procedencia electoral distinto del hash contractual")
        target_raw = matches[0].get("path")
        if not target_raw:
            raise ValueError("fuente contractual sin path")
        target = root / str(target_raw)
        static_structural_sha = _validate_static_structural_provenance(
            root=root,
            manifest=manifest,
            source_hash=actual,
            adapter=dict(matches[0].get("adapter") or {}),
        )
        if materialize:
            target.parent.mkdir(parents=True, exist_ok=True)
            if source.resolve() != target.resolve():
                shutil.copy2(source, target)
            if sha256(target).lower() != actual:
                raise ValueError("materialización electoral alteró el hash")
        contract_info = {
            "mode": "static_contract",
            "runtime_contract_path": str(contract_raw),
            # Compatibilidad con el contrato histórico del validador: este campo
            # representa el hash contractual de la fuente seleccionada.
            "contract_sha256": actual,
            "contract_source_path": str(target_raw),
            "party_dictionary_sha256": None,
            "structural_provenance_sha256": static_structural_sha,
            "election_identity_mode": election_identity_mode,
            "contract_election_id": contract.get("election_id"),
            "package_election_id": manifest.get("election_id"),
        }
    else:
        contract_info = _materialize_embedded_contract(
            package=package,
            manifest=manifest,
            root=root,
            territory_id=territory_id,
            edition=str(edition),
            source=source,
            source_hash=actual,
            materialize=materialize,
        )

    return {
        "schema": "ddd-electoral-package-validation/1.1",
        "decision": "READY_PACKAGE",
        "territory_id": territory_id,
        "edition": str(edition),
        "election_id": manifest.get("election_id"),
        "package_sha256": actual,
        "provenance_hash_matches_contract": True,
        "package_source_path": str(selected.get("path")),
        "materialized": bool(materialize),
        **contract_info,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--package", type=Path, required=True)
    ap.add_argument("--params", type=Path, required=True)
    ap.add_argument("--territory-id", required=True)
    ap.add_argument("--edition", required=True)
    ap.add_argument("--root-dir", type=Path, default=Path("."))
    ap.add_argument("--materialize", action="store_true")
    ap.add_argument("--output", type=Path)
    a = ap.parse_args()
    try:
        payload = validate_package(
            package=a.package,
            params=a.params,
            territory_id=a.territory_id,
            edition=a.edition,
            root=a.root_dir,
            materialize=a.materialize,
        )
    except Exception as exc:
        payload = {
            "schema": "ddd-electoral-package-validation/1.1",
            "decision": "BLOCK",
            "reason": str(exc),
        }
        if a.output:
            a.output.parent.mkdir(parents=True, exist_ok=True)
            a.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(payload, ensure_ascii=False))
        raise SystemExit(2)
    if a.output:
        a.output.parent.mkdir(parents=True, exist_ok=True)
        a.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False))


if __name__ == "__main__":
    main()
