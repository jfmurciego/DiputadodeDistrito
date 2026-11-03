#!/usr/bin/env python3
"""Verificar bytes de un portfolio en un checkpoint ZIP sin extraer sus rutas.

PROYECTO: Diputado de Distrito
VERSIÓN: 1.0.0
FECHA: 2026-11-03
ANTERIOR: archivo nuevo
No ejecuta el motor ni certifica restricciones geométricas.
"""
import argparse
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import zipfile


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def verify(path, expected_count=50, expected_sha256=None):
    raw = Path(path).read_bytes()
    archive_sha = digest(raw)
    if expected_sha256 and archive_sha != expected_sha256:
        raise ValueError("SHA-256 del checkpoint no coincide")
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        names = archive.namelist()
        if len(names) != len(set(names)):
            raise ValueError("Entradas ZIP duplicadas")
        portfolios = [n for n in names if n.endswith("/portfolio.json")]
        if len(portfolios) != 1:
            raise ValueError("Se requiere exactamente un portfolio.json")
        portfolio_name = portfolios[0]
        portfolio = json.loads(archive.read(portfolio_name))
        rows = portfolio.get("candidates", [])
        if portfolio.get("candidate_count") != expected_count or len(rows) != expected_count:
            raise ValueError("Número de candidatos inesperado")
        prefix = str(PurePosixPath(portfolio_name).parent) + "/"
        verified, universe, members = [], None, set()
        for row in rows:
            member = prefix + PurePosixPath(row["geojson"]).name
            if member in members:
                raise ValueError("Archivo de candidato repetido")
            members.add(member)
            candidate = archive.read(member)
            if digest(candidate) != row["sha256"]:
                raise ValueError("SHA-256 del candidato no coincide")
            with zipfile.ZipFile(io.BytesIO(candidate)) as inner:
                geo = [n for n in inner.namelist() if n.endswith(".geojson")]
                if len(geo) != 1:
                    raise ValueError("Candidato requiere un GeoJSON")
                features = json.loads(inner.read(geo[0]))["features"]
            assignment, sections = {}, set()
            for feature in features:
                properties = feature["properties"]
                section = str(properties["CUSEC_KEY"])
                if section in sections:
                    raise ValueError("Sección duplicada")
                sections.add(section)
                unit, district = str(properties["ddd_unit_id"]), str(properties["district_id"])
                if unit in assignment and assignment[unit] != district:
                    raise ValueError("Unidad asignada a varios distritos")
                assignment[unit] = district
            if not sections:
                raise ValueError("Candidato vacío")
            if universe is not None and sections != universe:
                raise ValueError("Cobertura de secciones distinta entre candidatos")
            universe = sections
            identity = digest(json.dumps(sorted(assignment.items()), ensure_ascii=False,
                                         separators=(",", ":")).encode())
            if identity != row["assignment_hash"]:
                raise ValueError("Hash de asignación no coincide")
            verified.append({"index": row["index"], "seed": row["seed"],
                             "sha256": row["sha256"], "assignment_hash": identity,
                             "sections": len(sections), "units": len(assignment),
                             "districts": len(set(assignment.values())),
                             "bytes": len(candidate), "selected": row.get("selected") is True})
        hashes = {row["assignment_hash"] for row in verified}
        if len(hashes) != expected_count or portfolio.get("unique_candidate_count") != expected_count:
            raise ValueError("Asignaciones no distintas")
        selected = [r for r in verified if r["selected"]]
        if len(selected) != 1 or selected[0]["assignment_hash"] != portfolio.get("selected_assignment_hash"):
            raise ValueError("Selección inconsistente")
    return {"schema": "ddd.audit-portfolio-bytecheck/1.0", "artifact_sha256": archive_sha,
            "artifact_bytes": len(raw), "candidate_count": len(verified),
            "unique_assignment_count": len(hashes), "all_candidate_hashes_verified": True,
            "all_assignment_hashes_recomputed": True,
            "total_candidate_bytes": sum(r["bytes"] for r in verified),
            "scope": "integridad y recuperabilidad; sin auditoría geométrica ni reoptimización",
            "candidates": verified}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("checkpoint", type=Path)
    parser.add_argument("--expected", type=int, default=50)
    parser.add_argument("--sha256")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.expected < 1:
        parser.error("--expected debe ser positivo")
    if args.output.resolve() == args.checkpoint.resolve():
        parser.error("La salida no puede sobrescribir el checkpoint")
    result = verify(args.checkpoint, args.expected, args.sha256)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in result.items() if k != "candidates"}, ensure_ascii=False))


if __name__ == "__main__":
    main()
