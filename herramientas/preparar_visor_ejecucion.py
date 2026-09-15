#!/usr/bin/env python3
"""Prepara el registro y los GeoJSON que consume el visor técnico DDD."""
from __future__ import annotations

import argparse
import json
import shutil
import zipfile
from pathlib import Path


def read_geojson_zip(path: Path) -> dict:
    with zipfile.ZipFile(path) as archive:
        members = [
            name for name in archive.namelist()
            if name.lower().endswith((".geojson", ".json")) and not name.endswith("/")
        ]
        if len(members) != 1:
            raise ValueError(f"{path}: esperaba un GeoJSON, encontró {members}")
        return json.loads(archive.read(members[0]).decode("utf-8"))


def write_geojson_from_zip(src: Path, dst: Path) -> int:
    payload = read_geojson_zip(src)
    if payload.get("type") != "FeatureCollection":
        raise ValueError(f"{src}: no es FeatureCollection")
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(
        json.dumps(payload, ensure_ascii=False, separators=(",", ":")),
        encoding="utf-8",
    )
    return len(payload.get("features", []))


def first(root: Path | None, pattern: str) -> Path | None:
    if root is None or not root.exists():
        return None
    found = sorted(root.rglob(pattern))
    return found[0] if found else None


def add_static(registry_path: Path | None, site: Path, results: list[dict]) -> None:
    if not registry_path or not registry_path.exists():
        return
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    for product in registry.get("products", []):
        src = Path(product["source_path"])
        if not src.exists():
            continue
        dst = site / "data" / "static" / f"{product['id']}.geojson"
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        results.append({
            "id": f"static-{product['id']}",
            "territory_id": product["id"],
            "territory_label": product["label"],
            "label": f"{product['label']} · producto histórico",
            "kind": "static",
            "expected_districts": product["expected_districts"],
            "viewer_path": str(dst.relative_to(site)).replace("\\", "/"),
            "technical_status": product.get("technical_status", product.get("status", "UNKNOWN")),
            "publication_status": product.get("publication_status", "BLOCKED"),
            "geometric_status": "LEGACY_OR_NOT_AUDITED",
        })


def add_production(
    root: Path | None,
    site: Path,
    run_id: str | None,
    results: list[dict],
    external_audit: Path | None = None,
) -> None:
    if root is None or not root.exists():
        return
    audit_path = first(root, "*_m06_contiguedad_geometrica.json")
    if audit_path is None and external_audit and external_audit.exists():
        audit_path = external_audit
    audit = json.loads(audit_path.read_text(encoding="utf-8")) if audit_path else None
    geometric_status = (audit or {}).get("decision", "NOT_AUDITED")
    gate = (audit or {}).get("gate_statement")
    for stage, pattern, label, kind in [
        ("M06", "*_m06_distritos.geojson.zip", "M06 territorial", "canonical_m06"),
        ("M08", "*_m08_distritos_resultados.geojson.zip", "M08 electoral", "canonical_m08"),
    ]:
        src = first(root, pattern)
        if not src:
            continue
        rid = run_id or "desconocido"
        dst = site / "data" / "results" / f"{stage.lower()}-{rid}.geojson"
        count = write_geojson_from_zip(src, dst)
        results.append({
            "id": f"{stage.lower()}-{rid}",
            "territory_id": "aragon",
            "territory_label": "Aragón",
            "label": f"{label} · run {rid}",
            "kind": kind,
            "run_id": rid,
            "expected_districts": count,
            "viewer_path": str(dst.relative_to(site)).replace("\\", "/"),
            "technical_status": "PASS",
            "publication_status": "BLOCKED",
            "geometric_status": geometric_status,
            "geometric_gate": gate,
        })


def add_ensemble(root: Path | None, site: Path, results: list[dict]) -> None:
    if root is None or not root.exists():
        return
    preferred = sorted(root.rglob("site/data/summary.json"))
    summary_path = preferred[0] if preferred else first(root, "summary.json")
    if not summary_path:
        return
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    base = summary_path.parent.parent if summary_path.parent.name == "data" else summary_path.parent
    for candidate in summary.get("candidates", []):
        asset = candidate.get("asset") or candidate.get("geojson")
        if not asset:
            continue
        src = (base / asset).resolve() if not Path(asset).is_absolute() else Path(asset)
        if not src.exists():
            matches = sorted(root.rglob(Path(asset).name))
            if not matches:
                continue
            src = matches[0]
        candidate_id = str(candidate.get("candidate_id") or src.stem)
        dst = site / "data" / "ensemble" / f"{candidate_id}.geojson"
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        results.append({
            "id": f"ensemble-{candidate_id}",
            "territory_id": summary.get("territory_id", "aragon"),
            "territory_label": "Aragón",
            "label": f"Ensemble {candidate_id} · {candidate.get('profile', 'sin perfil')}",
            "kind": "ensemble_candidate",
            "candidate_id": candidate_id,
            "profile": candidate.get("profile"),
            "seed": candidate.get("seed"),
            "expected_districts": 67,
            "viewer_path": str(dst.relative_to(site)).replace("\\", "/"),
            "technical_status": "PASS",
            "publication_status": "BLOCKED",
            "geometric_status": "ENSEMBLE_PRECHECK_ONLY",
            "metrics": candidate.get("metrics", {}),
        })


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--site", type=Path, required=True)
    parser.add_argument("--production-root", type=Path)
    parser.add_argument("--production-run-id")
    parser.add_argument("--production-audit", type=Path)
    parser.add_argument("--ensemble-root", type=Path)
    parser.add_argument("--static-registry", type=Path)
    args = parser.parse_args()

    args.site.mkdir(parents=True, exist_ok=True)
    results: list[dict] = []
    add_production(
        args.production_root,
        args.site,
        args.production_run_id,
        results,
        external_audit=args.production_audit,
    )
    add_ensemble(args.ensemble_root, args.site, results)
    add_static(args.static_registry, args.site, results)
    if not results:
        raise SystemExit("No se encontró ningún resultado visualizable")

    priority = {"canonical_m08": 0, "canonical_m06": 1, "ensemble_candidate": 2, "static": 3}
    results.sort(key=lambda item: (priority.get(item["kind"], 9), item["label"]))
    payload = {"schema": "ddd.viewer-results/1.0", "results": results}
    output = args.site / "data" / "viewer-results.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"[VISOR] resultados={len(results)} registry={output}")


if __name__ == "__main__":
    main()
