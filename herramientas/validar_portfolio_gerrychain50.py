#!/usr/bin/env python3
"""P0: valida el portfolio GerryChain 50 antes de permitir el paso a M06."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import zipfile
from pathlib import Path

SHA256 = re.compile(r"^[0-9a-f]{64}$")


class PortfolioBlock(ValueError):
    pass


def assignment_hash_from_zip(path: Path) -> str:
    with zipfile.ZipFile(path) as archive:
        members = [m for m in archive.namelist() if m.lower().endswith((".geojson", ".json"))]
        if len(members) != 1:
            raise PortfolioBlock(f"GeoJSON único exigido: {path}")
        doc = json.loads(archive.read(members[0]).decode("utf-8"))
    features = doc.get("features")
    if not isinstance(features, list) or not features:
        raise PortfolioBlock(f"GeoJSON sin secciones: {path}")
    assignment = {}
    seen_sections = set()
    for feature in features:
        props = feature.get("properties") or {}
        section = str(props.get("CUSEC_KEY") or "").strip()
        unit = str(props.get("ddd_unit_id") or "").strip()
        district = props.get("district_id")
        if not section or not unit or district is None or section in seen_sections:
            raise PortfolioBlock(f"Sección/unidad/distrito ausente o duplicado: {path}")
        seen_sections.add(section)
        value = str(int(district)) if isinstance(district, (int, float)) and not isinstance(district, bool) and float(district).is_integer() else str(district)
        if unit in assignment and assignment[unit] != value:
            raise PortfolioBlock(f"Unidad indivisible partida: {unit}")
        assignment[unit] = value
    payload = json.dumps(sorted((str(k), str(v)) for k, v in assignment.items()), ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def validate_directory(directory: Path, expected: int = 50, selected_output: Path | None = None) -> dict:
    directory = directory.resolve()
    manifest = directory / "portfolio.json"
    data = json.loads(manifest.read_text(encoding="utf-8"))
    rows = data.get("candidates")
    if not isinstance(rows, list) or len(rows) != expected or data.get("candidate_count") != expected:
        raise PortfolioBlock(f"Portfolio incompleto: se esperaban {expected} candidatos")
    hashes = [row.get("assignment_hash") for row in rows]
    if not all(isinstance(h, str) and SHA256.fullmatch(h) for h in hashes):
        raise PortfolioBlock("Hashes de asignación ausentes o inválidos")
    if len(set(hashes)) != expected or data.get("unique_candidate_count") != expected:
        raise PortfolioBlock("GerryChain 50 exige 50 asignaciones distintas")
    selected_hash = data.get("selected_assignment_hash")
    marked = [row for row in rows if row.get("selected") is True]
    if len(marked) != 1 or marked[0]["assignment_hash"] != selected_hash:
        raise PortfolioBlock("Candidato seleccionado no único o incoherente")
    for row in rows:
        path = Path(str(row.get("geojson") or ""))
        if not path.is_absolute():
            path = directory / path
        path = path.resolve()
        if directory not in path.parents or not path.is_file():
            raise PortfolioBlock(f"Candidato fuera del portfolio o ausente: {path}")
        expected_sha = row.get("sha256")
        if not isinstance(expected_sha, str) or not SHA256.fullmatch(expected_sha):
            raise PortfolioBlock(f"SHA-256 de artefacto inválido: {path}")
        actual_sha = hashlib.sha256(path.read_bytes()).hexdigest()
        if actual_sha != expected_sha:
            raise PortfolioBlock(f"SHA-256 de artefacto no coincide: {path}")
        if assignment_hash_from_zip(path) != row["assignment_hash"]:
            raise PortfolioBlock(f"El hash declarado no coincide con las asignaciones: {path}")
    if selected_output is not None:
        if not selected_output.is_file() or assignment_hash_from_zip(selected_output) != selected_hash:
            raise PortfolioBlock("La salida seleccionada no coincide con el portfolio")
    return {"decision": "VALIDATED", "candidate_count": expected, "unique_candidate_count": expected, "selected_assignment_hash": selected_hash}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--params", required=True)
    parser.add_argument("--run-id", required=True)
    args = parser.parse_args()
    import yaml
    from ddd_core.m05_gerrychain_strategy import resolve_paths
    params = Path(args.params)
    config = yaml.safe_load(params.read_text(encoding="utf-8")) or {}
    output = resolve_paths(config, params, args.run_id)["output"]
    suffix = "_m05_distritos_optimizados.geojson.zip"
    directory_name = output.name[:-len(suffix)] + "_m05_gerrychain_portfolio" if output.name.endswith(suffix) else output.stem + "_gerrychain_portfolio"
    directory = output.parent / directory_name
    try:
        result = validate_directory(directory, selected_output=output)
    except (OSError, ValueError, KeyError, zipfile.BadZipFile) as exc:
        print(json.dumps({"decision": "BLOCKED", "reason": str(exc)}, ensure_ascii=False))
        raise SystemExit(44) from exc
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
