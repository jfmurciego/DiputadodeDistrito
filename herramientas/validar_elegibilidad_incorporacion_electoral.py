#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

import yaml

from herramientas import catalogo_preparacion

SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


def _read_json(path: Path) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise ValueError(f"JSON ilegible: {path}") from exc
    if not isinstance(data, dict):
        raise ValueError(f"JSON inválido: {path}")
    return data


def _normalise_digest(value: str | None) -> str:
    raw = str(value or "").strip().lower().removeprefix("sha256:")
    if not SHA256_RE.fullmatch(raw):
        raise ValueError("digest electoral ausente o inválido")
    return raw


def _registry_identity(root_dir: Path, territory_id: str, edition: str) -> dict:
    path = root_dir / "configuracion/registro_electoral.yaml"
    if not path.is_file():
        raise ValueError("registro electoral común ausente")
    registry = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if registry.get("schema") != "ddd-election-registry/1.0":
        raise ValueError("schema del registro electoral común inválido")
    if str(registry.get("edition") or "") != str(edition):
        raise ValueError("edición del registro electoral común no coincide")
    row = (registry.get("territories") or {}).get(territory_id)
    if not isinstance(row, dict):
        raise ValueError("territorio ausente del registro electoral común")
    if not row.get("election_id") or not row.get("election_date"):
        raise ValueError("identidad electoral común incompleta")
    return row


def resolve_eligibility(
    *,
    root_dir: Path,
    territory: str,
    edition: str,
    gate_evidence: Path | None = None,
    package_manifest: Path | None = None,
    expected_run_id: str = "",
    expected_artifact_name: str = "",
    expected_artifact_digest: str = "",
) -> dict:
    root_dir = root_dir.resolve()

    explicit = any(
        (
            gate_evidence is not None,
            package_manifest is not None,
            expected_run_id,
            expected_artifact_name,
            expected_artifact_digest,
        )
    )
    complete = all(
        (
            gate_evidence is not None,
            package_manifest is not None,
            expected_run_id,
            expected_artifact_name,
            expected_artifact_digest,
        )
    )
    if explicit and not complete:
        raise ValueError("ELECTORAL_GATE_BLOCK: evidencia explícita incompleta")

    if not explicit:
        row = catalogo_preparacion.resolve(
            "electoral_application", territory, str(edition),
            root_dir / "configuracion/catalogo_preparacion.yaml",
        )
        params = str(row.get("contract_path") or "")
        if not params or not (root_dir / params).is_file():
            raise ValueError("ELECTORAL_GATE_BLOCK: contrato territorial ausente")
        return {
            "decision": "ELIGIBLE",
            "route": "catalog_accredited",
            "territory_id": row["territory_id"],
            "edition": str(edition),
            "params": params,
        }

    # La identidad territorial y el contrato se fijan por el SHA inmutable.
    row = catalogo_preparacion.lookup(
        territory, str(edition),
        root_dir / "configuracion/catalogo_preparacion.yaml",
    )
    territory_id = str(row.get("territory_id") or "")
    params = str(row.get("contract_path") or "")
    params_path = root_dir / params if params else None
    if params_path is None or not params_path.is_file():
        raise ValueError("ELECTORAL_GATE_BLOCK: contrato territorial ausente")
    cfg = yaml.safe_load(params_path.read_text(encoding="utf-8")) or {}
    meta = cfg.get("meta") or {}
    if (
        str(meta.get("territory_id") or "") != territory_id
        or str(meta.get("year") or "") != str(edition)
    ):
        raise ValueError("ELECTORAL_GATE_BLOCK: identidad del contrato territorial no coincide")

    gate = _read_json(gate_evidence)
    if gate.get("decision") != "VALIDADO" or gate.get("phase") != "electoral_source":
        raise ValueError("ELECTORAL_GATE_BLOCK: puerta 03→04 no validada")
    if str(gate.get("territory_id") or "") != territory_id:
        raise ValueError("ELECTORAL_GATE_BLOCK: territorio de la puerta no coincide")
    if str(gate.get("edition") or "") != str(edition):
        raise ValueError("ELECTORAL_GATE_BLOCK: edición de la puerta no coincide")
    if str(gate.get("run_id") or "") != str(expected_run_id):
        raise ValueError("ELECTORAL_GATE_BLOCK: run electoral de la puerta no coincide")
    if str(gate.get("artifact_name") or "") != str(expected_artifact_name):
        raise ValueError("ELECTORAL_GATE_BLOCK: artefacto electoral de la puerta no coincide")
    canonical_name = f"ddd-electoral-package-{territory_id}-{edition}-{expected_run_id}"
    if expected_artifact_name != canonical_name:
        raise ValueError("ELECTORAL_GATE_BLOCK: nombre de artefacto electoral no canónico")

    expected_digest = _normalise_digest(expected_artifact_digest)
    gate_digest = _normalise_digest(gate.get("artifact_digest"))
    if gate_digest != expected_digest:
        raise ValueError("ELECTORAL_GATE_BLOCK: digest electoral de la puerta no coincide")

    manifest = _read_json(package_manifest)
    if manifest.get("schema") != "ddd-electoral-package/1.0":
        raise ValueError("ELECTORAL_GATE_BLOCK: schema del paquete electoral inválido")
    if str(manifest.get("territory_id") or "") != territory_id:
        raise ValueError("ELECTORAL_GATE_BLOCK: territorio del paquete electoral no coincide")
    if str(manifest.get("edition") or "") != str(edition):
        raise ValueError("ELECTORAL_GATE_BLOCK: edición del paquete electoral no coincide")
    if manifest.get("decision") not in {"REUSE", "ACQUIRE"}:
        raise ValueError("ELECTORAL_GATE_BLOCK: paquete electoral no utilizable")

    registry = _registry_identity(root_dir, territory_id, str(edition))
    if str(manifest.get("election_id") or "") != str(registry.get("election_id") or ""):
        raise ValueError("ELECTORAL_GATE_BLOCK: election_id del paquete no coincide con el registro")
    if str(manifest.get("election_date") or "") != str(registry.get("election_date") or ""):
        raise ValueError("ELECTORAL_GATE_BLOCK: election_date del paquete no coincide con el registro")

    return {
        "decision": "ELIGIBLE",
        "route": "validated_gate_evidence",
        "territory_id": territory_id,
        "edition": str(edition),
        "params": params,
        "run_id": int(expected_run_id),
        "artifact_name": expected_artifact_name,
        "artifact_digest": f"sha256:{expected_digest}",
        "election_id": manifest.get("election_id"),
        "election_date": manifest.get("election_date"),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root-dir", type=Path, default=Path("."))
    ap.add_argument("--territory", required=True)
    ap.add_argument("--edition", required=True)
    ap.add_argument("--gate-evidence", type=Path)
    ap.add_argument("--package-manifest", type=Path)
    ap.add_argument("--expected-run-id", default="")
    ap.add_argument("--expected-artifact-name", default="")
    ap.add_argument("--expected-artifact-digest", default="")
    ap.add_argument("--output", type=Path)
    args = ap.parse_args()
    try:
        payload = resolve_eligibility(
            root_dir=args.root_dir,
            territory=args.territory,
            edition=args.edition,
            gate_evidence=args.gate_evidence,
            package_manifest=args.package_manifest,
            expected_run_id=args.expected_run_id,
            expected_artifact_name=args.expected_artifact_name,
            expected_artifact_digest=args.expected_artifact_digest,
        )
    except Exception as exc:
        payload = {
            "decision": "BLOCKED",
            "reason": str(exc),
        }
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(payload, ensure_ascii=False))
        return 2
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())