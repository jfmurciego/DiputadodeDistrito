#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from pathlib import Path

import yaml


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


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
    sources = contract.get("sources") or []
    if len(sources) != 1 or str(sources[0].get("sha256") or "").lower() != source_hash:
        raise ValueError("contrato electoral embebido no referencia la fuente congelada")

    runtime_rel = Path(".ddd-electoral-runtime") / territory_id / str(edition)
    runtime_dir = root / runtime_rel
    runtime_contract = runtime_dir / "election_contract.json"
    runtime_dictionary = runtime_dir / "party_dictionary.json"
    runtime_source = runtime_dir / "data" / source.name

    if materialize:
        runtime_source.parent.mkdir(parents=True, exist_ok=True)
        runtime_dictionary.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, runtime_source)
        shutil.copy2(dictionary_src, runtime_dictionary)
        runtime_contract_payload = dict(contract)
        runtime_contract_payload["sources"] = [dict(sources[0])]
        runtime_contract_payload["sources"][0]["path"] = runtime_source.relative_to(root).as_posix()
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
        matches = [s for s in (contract.get("sources") or []) if str(s.get("sha256") or "").lower() == actual]
        if len(matches) != 1:
            raise ValueError("hash de procedencia electoral distinto del hash contractual")
        target_raw = matches[0].get("path")
        if not target_raw:
            raise ValueError("fuente contractual sin path")
        target = root / str(target_raw)
        if materialize:
            target.parent.mkdir(parents=True, exist_ok=True)
            if source.resolve() != target.resolve():
                shutil.copy2(source, target)
            if sha256(target).lower() != actual:
                raise ValueError("materialización electoral alteró el hash")
        contract_info = {
            "mode": "static_contract",
            "runtime_contract_path": str(contract_raw),
            "contract_sha256": None,
            "party_dictionary_sha256": None,
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
