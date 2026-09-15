#!/usr/bin/env python3
"""Prepara el registro verificable y los GeoJSON que consume el visor DDD.

VERSIÓN: 1.1.1
La identidad, K y estado de una ejecución proceden de su contrato y de
``production_status.json``; nunca se infiere PASS porque exista un ZIP.
Las copias destinadas al visor se publican en WGS84 sin alterar los artefactos analíticos.
"""
from __future__ import annotations

import argparse
import json
import shutil
import zipfile
from pathlib import Path

import yaml
from pyproj import Transformer

from ddd_ensemble.gallery import _epsg_from_geojson, _transform_coordinates


TERRITORY_LABELS = {
    "andalucia": "Andalucía",
    "aragon": "Aragón",
    "principado_de_asturias": "Principado de Asturias",
    "illes_balears": "Islas Baleares",
    "canarias": "Canarias",
    "cantabria": "Cantabria",
    "castilla_la_mancha": "Castilla-La Mancha",
    "castilla_y_leon": "Castilla y León",
    "cataluna": "Cataluña",
    "comunidad_valenciana": "Comunidad Valenciana",
    "extremadura": "Extremadura",
    "galicia": "Galicia",
    "madrid": "Comunidad de Madrid",
    "region_de_murcia": "Región de Murcia",
    "comunidad_foral_de_navarra": "Comunidad Foral de Navarra",
    "pais_vasco": "País Vasco",
    "la_rioja": "La Rioja",
    "ceuta": "Ceuta",
    "melilla": "Melilla",
}


def read_geojson_zip(path: Path) -> dict:
    with zipfile.ZipFile(path) as archive:
        members = [
            name for name in archive.namelist()
            if name.lower().endswith((".geojson", ".json")) and not name.endswith("/")
        ]
        if len(members) != 1:
            raise ValueError(f"{path}: esperaba un GeoJSON, encontró {members}")
        return json.loads(archive.read(members[0]).decode("utf-8"))


def _web_payload(payload: dict) -> dict:
    source_epsg = _epsg_from_geojson(payload)
    if source_epsg not in (None, 4326):
        transformer = Transformer.from_crs(f"EPSG:{source_epsg}", "EPSG:4326", always_xy=True)
        for feature in payload.get("features", []):
            geometry = feature.get("geometry") or {}
            if "coordinates" in geometry:
                geometry["coordinates"] = _transform_coordinates(geometry["coordinates"], transformer)
            elif geometry.get("type") == "GeometryCollection":
                for child in geometry.get("geometries", []):
                    if "coordinates" in child:
                        child["coordinates"] = _transform_coordinates(child["coordinates"], transformer)
    payload.pop("crs", None)
    return payload


def write_geojson_from_zip(src: Path, dst: Path) -> int:
    payload = read_geojson_zip(src)
    if payload.get("type") != "FeatureCollection":
        raise ValueError(f"{src}: no es FeatureCollection")
    payload = _web_payload(payload)
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


def read_json(path: Path | None) -> dict:
    return json.loads(path.read_text(encoding="utf-8")) if path and path.is_file() else {}


def production_metadata(root: Path) -> dict:
    decision = read_json(first(root, "decision.json"))
    status = read_json(first(root, "production_status.json"))
    params_value = status.get("params") or decision.get("params")
    config = {}
    if params_value:
        params = Path(params_value)
        if params.is_file():
            config = yaml.safe_load(params.read_text(encoding="utf-8")) or {}
    meta = config.get("meta") or {}
    m06 = (config.get("modulos") or {}).get("modulo_06_consolidar_distritos") or {}
    validation = config.get("validation") or {}
    territory_id = status.get("territory_id") or decision.get("territory_id") or meta.get("territory_id")
    if not territory_id:
        raise ValueError("El artefacto de producción no identifica el territorio")
    expected = m06.get("expected_districts") or validation.get("expected_districts")
    if expected is None:
        raise ValueError(f"El contrato de {territory_id} no declara expected_districts")
    return {
        "territory_id": territory_id,
        "territory_label": meta.get("territory") or TERRITORY_LABELS.get(territory_id, territory_id),
        "expected_districts": int(expected),
        "production_status": status,
    }


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
    metadata = production_metadata(root)
    audit_path = first(root, "*_m06_contiguedad_geometrica.json")
    if audit_path is None and external_audit and external_audit.exists():
        audit_path = external_audit
    audit = json.loads(audit_path.read_text(encoding="utf-8")) if audit_path else None
    geometric_status = (audit or {}).get("decision", "NOT_AUDITED")
    gate = (audit or {}).get("gate_statement")
    production_status = metadata["production_status"]
    recorded_status = production_status.get("decision")
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
        technical_status = recorded_status or (
            "BLOCK" if geometric_status == "BLOCK" else "UNKNOWN"
        )
        status_reasons = []
        if not recorded_status:
            status_reasons.append("MISSING_PRODUCTION_STATUS")
        if geometric_status == "BLOCK":
            technical_status = "BLOCK"
            status_reasons.append("GEOMETRIC_CONTIGUITY_BLOCK")
        if count != metadata["expected_districts"]:
            technical_status = "BLOCK"
            status_reasons.append("DISTRICT_COUNT_MISMATCH")
        results.append({
            "id": f"{stage.lower()}-{rid}",
            "territory_id": metadata["territory_id"],
            "territory_label": metadata["territory_label"],
            "label": f"{label} · run {rid}",
            "kind": kind,
            "run_id": rid,
            "expected_districts": metadata["expected_districts"],
            "observed_districts": count,
            "viewer_path": str(dst.relative_to(site)).replace("\\", "/"),
            "technical_status": technical_status,
            "status_reasons": status_reasons,
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
    territory_id = summary.get("territory_id")
    territory_label = summary.get("territory_label") or TERRITORY_LABELS.get(
        territory_id, territory_id or "Territorio no identificado"
    )
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
            "territory_id": territory_id,
            "territory_label": territory_label,
            "label": f"Ensemble {candidate_id} · {candidate.get('profile', 'sin perfil')}",
            "kind": "ensemble_candidate",
            "candidate_id": candidate_id,
            "profile": candidate.get("profile"),
            "seed": candidate.get("seed"),
            "expected_districts": int(
                ((candidate.get("metrics") or {}).get("population") or {}).get("district_count", 0)
            ),
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
