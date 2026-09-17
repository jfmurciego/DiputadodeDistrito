#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PROYECTO: Diputado de Distrito
COMPONENTE: instalación contractual de fuente electoral oficial
VERSIÓN: 1.0.0
FECHA: 2026-09-17
FUNCIÓN: recuperar una copia oficial aprobada desde el artefacto electoral, verificar nuevamente su SHA-256 e instalarla en la ruta declarada por el contrato electoral de M07.
REGLAS: no contiene nombres territoriales; BLOCK impide habilitar procesamiento; la ruta destino procede exclusivamente del contrato electoral.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from pathlib import Path

import yaml


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _load_params(path: Path) -> dict:
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise ValueError("Contrato territorial inválido")
    return data


def _load_contract(params: dict, root: Path) -> tuple[Path, dict]:
    m07 = (params.get("modulos") or {}).get("modulo_07_agregar_resultados_electorales") or {}
    raw = m07.get("election_contract")
    if not raw:
        raise ValueError("M07 no declara election_contract")
    path = root / str(raw)
    if not path.is_file():
        raise ValueError(f"No existe contrato electoral: {raw}")
    contract = json.loads(path.read_text(encoding="utf-8"))
    return path, contract


def _contract_source(contract: dict, selected: dict | None) -> dict:
    sources = contract.get("sources") or []
    if not isinstance(sources, list) or not sources:
        raise ValueError("Contrato electoral sin sources")
    if selected:
        sid = str(selected.get("id") or "")
        url = str(selected.get("url") or "")
        exact = [s for s in sources if str(s.get("id") or "") == sid and sid]
        if not exact and url:
            exact = [s for s in sources if str(s.get("source_url") or "") == url]
        if len(exact) == 1:
            return exact[0]
    if len(sources) == 1:
        return sources[0]
    raise ValueError("No se puede asociar de forma unívoca la fuente aprobada al contrato electoral")


def install_from_artifact(params_path: str | Path, artifact_dir: str | Path, *, root_dir: str | Path = ".", report_path: str | Path | None = None) -> dict:
    root = Path(root_dir).resolve()
    params = _load_params(Path(params_path))
    _, contract = _load_contract(params, root)
    artifact = Path(artifact_dir)
    decision_path = artifact / "decision_fuente_electoral.json"
    if not decision_path.is_file():
        raise ValueError("Falta decision_fuente_electoral.json en el artefacto")
    decision = json.loads(decision_path.read_text(encoding="utf-8"))
    state = str(decision.get("decision") or "")
    if not state.startswith("READY"):
        raise ValueError(f"Fuente electoral bloqueada: {state or 'sin decisión'}")

    selected = decision.get("selected_source")
    source_cfg = _contract_source(contract, selected if isinstance(selected, dict) else None)
    dest_raw = source_cfg.get("path")
    expected_contract_sha = str(source_cfg.get("sha256") or "").lower()
    if not dest_raw or not expected_contract_sha:
        raise ValueError("La fuente del contrato electoral debe declarar path y sha256")
    destination = root / str(dest_raw)

    if state == "READY_EXISTING_CONTRACT" and not selected:
        if not destination.is_file():
            raise ValueError("El contrato existente declara una fuente que no está materializada")
        actual = sha256_file(destination)
        if actual != expected_contract_sha:
            raise ValueError("Checksum del fichero electoral existente no coincide con el contrato")
        result = {"schema":"ddd-election-source-install/1.0","decision":"READY","processing_enabled":True,"mode":"existing_contract","installed_path":str(dest_raw),"sha256":actual}
    else:
        if not isinstance(selected, dict):
            raise ValueError("READY sin selected_source")
        artifact_path = selected.get("artifact_path")
        checksum_path = selected.get("checksum_path")
        expected_artifact_sha = str(selected.get("sha256") or "").lower()
        if not artifact_path or not checksum_path or not expected_artifact_sha:
            raise ValueError("La decisión READY no transporta fichero, checksum y SHA-256")
        source_file = artifact / str(artifact_path)
        sidecar = artifact / str(checksum_path)
        if not source_file.is_file() or not sidecar.is_file():
            raise ValueError("El artefacto electoral está incompleto")
        sidecar_sha = sidecar.read_text(encoding="utf-8").strip().split()[0].lower()
        actual = sha256_file(source_file)
        if actual != expected_artifact_sha or sidecar_sha != expected_artifact_sha:
            raise ValueError("Checksum del artefacto electoral no coincide con la decisión")
        if actual != expected_contract_sha:
            raise ValueError("Checksum de la copia oficial no coincide con el contrato electoral")
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_file, destination)
        installed = sha256_file(destination)
        if installed != expected_contract_sha:
            raise ValueError("Checksum posterior a la instalación no coincide con el contrato")
        result = {"schema":"ddd-election-source-install/1.0","decision":"READY","processing_enabled":True,"mode":"artifact","installed_path":str(dest_raw),"sha256":installed,"source_artifact_path":str(artifact_path),"checksum_artifact_path":str(checksum_path)}

    if report_path:
        rp = Path(report_path)
        rp.parent.mkdir(parents=True, exist_ok=True)
        rp.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return result


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--params", required=True)
    ap.add_argument("--artifact-dir", required=True)
    ap.add_argument("--root-dir", default=".")
    ap.add_argument("--report", required=True)
    args = ap.parse_args()
    result = install_from_artifact(args.params, args.artifact_dir, root_dir=args.root_dir, report_path=args.report)
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
