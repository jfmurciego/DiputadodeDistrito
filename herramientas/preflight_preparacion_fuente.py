#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

import yaml

CATALOG = Path("configuracion/catalogo_preparacion.yaml")
SHA256_RE = re.compile(r"^[0-9a-fA-F]{64}$")


def _load_yaml(path: Path) -> dict:
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise ValueError(f"YAML inválido: {path}")
    return data


def _state(root: Path, territory: str, edition: str) -> tuple[str, str, dict]:
    catalog_path = root / CATALOG
    if not catalog_path.is_file():
        raise ValueError(f"Catálogo inexistente: {catalog_path}")
    catalog = _load_yaml(catalog_path)
    token = territory.strip()
    rows = [
        row for row in (catalog.get("territories") or [])
        if token in {str(row.get("territory_id") or ""), str(row.get("name") or "")}
    ]
    if len(rows) != 1:
        raise ValueError(f"Territorio no resoluble de forma unívoca: {territory!r}")
    row = rows[0]
    tid = str(row.get("territory_id") or "")
    name = str(row.get("name") or tid)
    state = (row.get("editions") or {}).get(str(edition))
    if not isinstance(state, dict):
        raise ValueError(f"Edición no registrada: {tid}/{edition}")
    return tid, name, state


def _digest(value: object, label: str) -> str:
    digest = str(value or "").removeprefix("sha256:").strip()
    if not SHA256_RE.fullmatch(digest):
        raise ValueError(f"{label}: SHA-256 ausente o inválido")
    return digest.lower()


def _artifact_fields(data: dict, *, expected_prefix: str, label: str) -> tuple[int, str, str]:
    try:
        run_id = int(data.get("run_id"))
    except Exception as exc:
        raise ValueError(f"{label}: run_id ausente o inválido") from exc
    if run_id <= 0:
        raise ValueError(f"{label}: run_id debe ser positivo")
    artifact_name = str(data.get("artifact_name") or "").strip()
    if not artifact_name.startswith(expected_prefix):
        raise ValueError(
            f"{label}: artifact_name no corresponde al territorio/edición: {artifact_name!r}"
        )
    artifact_sha256 = _digest(data.get("artifact_sha256"), label)
    return run_id, artifact_name, artifact_sha256


def preflight(root: Path, kind: str, territory: str, edition: str) -> dict:
    root = root.resolve()
    tid, name, state = _state(root, territory, edition)
    common = {
        "schema": "ddd.preparation-preflight/1.0",
        "kind": kind,
        "territory_id": tid,
        "territory_name": name,
        "edition": str(edition),
        "registered": False,
        "run_id": None,
        "artifact_name": None,
        "artifact_sha256": None,
        "evidence_path": None,
    }

    if kind == "territorial":
        prepared = bool(state.get("territorial_sources_prepared"))
        evidence = state.get("preparation_evidence")
        if not prepared:
            if isinstance(evidence, dict) and evidence.get("artifact_name"):
                raise ValueError(
                    f"{tid}/{edition}: preparation_evidence existe pero territorial_sources_prepared=false"
                )
            return common
        if not isinstance(evidence, dict):
            raise ValueError(
                f"{tid}/{edition}: fuente territorial marcada preparada sin preparation_evidence"
            )
        prefix = f"ddd-source-package-{tid}-{edition}-"
        run_id, artifact_name, artifact_sha256 = _artifact_fields(
            evidence, expected_prefix=prefix, label=f"{tid}/{edition} registro territorial"
        )
        common.update(
            registered=True,
            run_id=run_id,
            artifact_name=artifact_name,
            artifact_sha256=artifact_sha256,
            evidence_path="configuracion/catalogo_preparacion.yaml#preparation_evidence",
        )
        return common

    if kind == "electoral":
        prepared = bool(state.get("electoral_source_prepared"))
        evidence_map = state.get("evidence") or {}
        evidence_rel = evidence_map.get("electoral_source") if isinstance(evidence_map, dict) else None
        if not prepared:
            if evidence_rel:
                raise ValueError(
                    f"{tid}/{edition}: evidence.electoral_source existe pero electoral_source_prepared=false"
                )
            return common
        if not evidence_rel:
            raise ValueError(
                f"{tid}/{edition}: fuente electoral marcada preparada sin evidence.electoral_source"
            )
        receipt = root / str(evidence_rel)
        if not receipt.is_file():
            raise ValueError(f"{tid}/{edition}: registro electoral inexistente: {evidence_rel}")
        try:
            data = json.loads(receipt.read_text(encoding="utf-8"))
        except Exception as exc:
            raise ValueError(f"{tid}/{edition}: registro electoral ilegible: {evidence_rel}") from exc
        if data.get("schema") != "ddd.catalog-evidence/1.0":
            raise ValueError(f"{tid}/{edition}: schema electoral no soportado")
        if data.get("kind") != "electoral_source":
            raise ValueError(f"{tid}/{edition}: registro no es electoral_source")
        if str(data.get("territory_id") or "") != tid or str(data.get("edition") or "") != str(edition):
            raise ValueError(f"{tid}/{edition}: identidad del registro electoral no coincide")
        prefix = f"ddd-electoral-package-{tid}-{edition}-"
        run_id, artifact_name, artifact_sha256 = _artifact_fields(
            data, expected_prefix=prefix, label=f"{tid}/{edition} registro electoral"
        )
        common.update(
            registered=True,
            run_id=run_id,
            artifact_name=artifact_name,
            artifact_sha256=artifact_sha256,
            evidence_path=str(evidence_rel),
            election_id=data.get("election_id"),
        )
        return common

    raise ValueError(f"Tipo de preflight desconocido: {kind}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root-dir", type=Path, default=Path("."))
    ap.add_argument("--kind", required=True, choices=["territorial", "electoral"])
    ap.add_argument("--territory", required=True)
    ap.add_argument("--edition", required=True)
    args = ap.parse_args()
    try:
        result = preflight(args.root_dir, args.kind, args.territory, args.edition)
    except Exception as exc:
        print(json.dumps({"ok": False, "error": f"{type(exc).__name__}: {exc}"}, ensure_ascii=False))
        return 2
    print(json.dumps({"ok": True, **result}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
