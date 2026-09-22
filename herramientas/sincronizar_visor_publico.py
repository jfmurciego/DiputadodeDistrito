#!/usr/bin/env python3
"""Sincroniza los productos web durables que consume el visor público.

El visor no depende del último despliegue de Pages. Los GeoJSON web se conservan
por territorio en rutas estables del repositorio y el catálogo público apunta a
esas rutas. El estado funcional se consume aparte desde estado_operativo.json.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

import yaml

from herramientas.preparar_visor_ejecucion import write_geojson_from_zip


SCHEMA = "ddd.public-viewer-catalog/1.0"


def _first(root: Path, pattern: str) -> Path | None:
    found = sorted(root.rglob(pattern))
    return found[0] if found else None


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_catalog(path: Path) -> dict:
    if not path.is_file():
        return {"schema": SCHEMA, "territories": []}
    payload = _load_json(path)
    if payload.get("schema") != SCHEMA:
        raise ValueError(f"Catálogo de visor con schema no soportado: {payload.get('schema')!r}")
    payload.setdefault("territories", [])
    return payload


def _election_metadata(root: Path, territory: dict) -> tuple[str | None, str | None]:
    source = ((territory.get("phase_evidence") or {}).get("electoral_source") or {})
    election_id = source.get("election_id")
    election_date = source.get("election_date")
    contract_raw = source.get("election_contract")
    declaration_raw = source.get("declaration")

    if contract_raw:
        path = root / str(contract_raw)
        if path.is_file():
            data = _load_json(path)
            election_id = election_id or data.get("election_id")
            election_date = election_date or data.get("election_date")

    if declaration_raw and not election_date:
        path = root / str(declaration_raw)
        if path.is_file():
            data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
            election_id = election_id or data.get("election_id")
            election_date = data.get("election_date")

    return (
        str(election_id) if election_id else None,
        str(election_date) if election_date else None,
    )


def _download_artifact(
    *,
    repository: str,
    run_id: int,
    artifact_name: str,
    destination: Path,
) -> Path:
    destination.mkdir(parents=True, exist_ok=True)
    env = dict(os.environ)
    if not env.get("GH_TOKEN"):
        raise RuntimeError("GH_TOKEN es obligatorio para recuperar artefactos de producción")
    cmd = [
        "gh", "run", "download", str(run_id),
        "--repo", repository,
        "--name", artifact_name,
        "--dir", str(destination),
    ]
    subprocess.run(cmd, check=True, env=env)
    return destination


def _product_from_artifact(
    *,
    artifact_root: Path,
    stage: str,
    destination: Path,
) -> int:
    pattern = "*_m06_distritos.geojson.zip" if stage == "M06" else "*_m08_distritos_resultados.geojson.zip"
    source = _first(artifact_root, pattern)
    if source is None:
        raise FileNotFoundError(f"No se encontró {pattern} en {artifact_root}")
    return write_geojson_from_zip(source, destination)


def _product_entry(
    *,
    kind: str,
    source_path: Path,
    district_count: int,
    source_run_id: int,
    election_id: str | None = None,
    election_date: str | None = None,
) -> dict:
    entry = {
        "kind": kind,
        "source_path": source_path.as_posix(),
        "districts": int(district_count),
        "source_run_id": int(source_run_id),
    }
    if election_id:
        entry["election_id"] = election_id
    if election_date:
        entry["election_date"] = election_date
    return entry


def sync_territory_from_artifact_roots(
    *,
    root: Path,
    state: dict,
    territory_id: str,
    m06_root: Path | None,
    m08_root: Path | None,
    catalog_path: Path,
    output_root: Path,
) -> dict:
    territory = next(
        (row for row in state.get("territories", []) if row.get("territory_id") == territory_id),
        None,
    )
    if territory is None:
        raise ValueError(f"Territorio no encontrado en estado operativo: {territory_id}")

    phase = territory.get("phase_evidence") or {}
    territorial = phase.get("territorial_product") or {}
    electoral = phase.get("electoral_product") or {}
    election_id, election_date = _election_metadata(root, territory)

    catalog = _load_catalog(catalog_path)
    existing = {
        item.get("territory_id"): item
        for item in catalog.get("territories", [])
        if item.get("territory_id")
    }
    current = existing.get(territory_id, {})
    products = {
        item.get("kind"): item
        for item in current.get("products", [])
        if item.get("kind")
    }

    territory_dir = output_root / territory_id
    territory_dir.mkdir(parents=True, exist_ok=True)

    if territorial:
        run_id = int(territorial["run_id"])
        destination = territory_dir / "territorial.geojson"
        if m06_root is None:
            raise ValueError(f"{territory_id}: falta artefacto M06")
        count = _product_from_artifact(
            artifact_root=m06_root,
            stage="M06",
            destination=destination,
        )
        products["territorial"] = _product_entry(
            kind="territorial",
            source_path=destination.relative_to(root),
            district_count=count,
            source_run_id=run_id,
        )

    if electoral:
        run_id = int(electoral["run_id"])
        destination = territory_dir / "electoral.geojson"
        if m08_root is None:
            raise ValueError(f"{territory_id}: falta artefacto M08")
        count = _product_from_artifact(
            artifact_root=m08_root,
            stage="M08",
            destination=destination,
        )
        products["electoral"] = _product_entry(
            kind="electoral",
            source_path=destination.relative_to(root),
            district_count=count,
            source_run_id=run_id,
            election_id=election_id,
            election_date=election_date,
        )

    if not products:
        return catalog

    existing[territory_id] = {
        "territory_id": territory_id,
        "name": territory.get("name") or territory_id,
        "edition": str(territory.get("edition") or state.get("edition") or ""),
        "products": sorted(products.values(), key=lambda p: p["kind"]),
    }
    catalog = {
        "schema": SCHEMA,
        "updated_at": state.get("generated_at"),
        "source": "orchestracion/estado_operativo.json",
        "territories": sorted(existing.values(), key=lambda row: row["name"]),
    }
    catalog_path.parent.mkdir(parents=True, exist_ok=True)
    catalog_path.write_text(
        json.dumps(catalog, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return catalog


def sync_territory(
    *,
    root: Path,
    state: dict,
    territory_id: str,
    repository: str,
    catalog_path: Path,
    output_root: Path,
) -> dict:
    territory = next(
        (row for row in state.get("territories", []) if row.get("territory_id") == territory_id),
        None,
    )
    if territory is None:
        raise ValueError(f"Territorio no encontrado: {territory_id}")
    phase = territory.get("phase_evidence") or {}
    territorial = phase.get("territorial_product")
    electoral = phase.get("electoral_product")
    if not territorial and not electoral:
        return _load_catalog(catalog_path)

    with tempfile.TemporaryDirectory(prefix=f"ddd-visor-{territory_id}-") as td:
        work = Path(td)
        m06_root = None
        m08_root = None
        if territorial:
            run_id = int(territorial["run_id"])
            artifact_name = str(territorial.get("artifact_name") or f"ddd-state-{run_id}-M06")
            m06_root = _download_artifact(
                repository=repository,
                run_id=run_id,
                artifact_name=artifact_name,
                destination=work / "m06",
            )
        if electoral:
            run_id = int(electoral["run_id"])
            artifact_name = str(electoral.get("artifact_name") or f"ddd-state-{run_id}-M08")
            m08_root = _download_artifact(
                repository=repository,
                run_id=run_id,
                artifact_name=artifact_name,
                destination=work / "m08",
            )
        return sync_territory_from_artifact_roots(
            root=root,
            state=state,
            territory_id=territory_id,
            m06_root=m06_root,
            m08_root=m08_root,
            catalog_path=catalog_path,
            output_root=output_root,
        )


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root-dir", type=Path, default=Path("."))
    ap.add_argument("--state", type=Path, default=Path("orchestracion/estado_operativo.json"))
    ap.add_argument("--catalog", type=Path, default=Path("publicado/visor/catalogo.json"))
    ap.add_argument("--output-root", type=Path, default=Path("publicado/visor/data"))
    ap.add_argument("--repository", required=True)
    group = ap.add_mutually_exclusive_group(required=True)
    group.add_argument("--territory-id")
    group.add_argument("--all", action="store_true")
    args = ap.parse_args()

    root = args.root_dir.resolve()
    state = _load_json(root / args.state)
    catalog_path = root / args.catalog
    output_root = root / args.output_root

    if args.all:
        candidates = [
            row["territory_id"]
            for row in state.get("territories", [])
            if ((row.get("phase_evidence") or {}).get("territorial_product")
                or (row.get("phase_evidence") or {}).get("electoral_product"))
        ]
    else:
        candidates = [str(args.territory_id)]

    for territory_id in candidates:
        sync_territory(
            root=root,
            state=state,
            territory_id=territory_id,
            repository=args.repository,
            catalog_path=catalog_path,
            output_root=output_root,
        )
        print(f"[VISOR VIVO] sincronizado {territory_id}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
