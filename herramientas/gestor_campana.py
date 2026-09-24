#!/usr/bin/env python3
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import shutil
import tempfile
import zipfile
from pathlib import Path
from typing import Any

import yaml

CONFIRMATION = "EXECUTE_CAMPAIGN_CONFIRMED"
ENTRYPOINT = "gerrychain_50"
EXPECTED_FIELDS = {
    "schema": "ddd.campaign-manifest/1.1",
    "data_edition": "2025",
    "execution_mode": "Reutilizar fuente explícita",
    "optimization_algorithm": "GerryChain 50",
    "entrypoint": ENTRYPOINT,
    "candidate_count": 50,
    "require_unique_hashes": True,
    "fail_fast": False,
    "max_parallel": 5,
    "retry_failed": False,
    "campaign_confirmation": CONFIRMATION,
}
EXPECTED_TERRITORIES = [
    ("01", "aragon", "Aragón", "electoral"),
    ("02", "principado_de_asturias", "Principado de Asturias", "electoral"),
    ("03", "galicia", "Galicia", "electoral"),
    ("04", "castilla_y_leon", "Castilla y León", "electoral"),
    ("05", "extremadura", "Extremadura", "territorial_only"),
]
REUSE_FIELDS = (
    "run_id",
    "checkpoint_stage",
    "artifact_name",
    "artifact_sha256",
    "source_sha",
    "m01_artifact_name",
    "m01_artifact_sha256",
    "expected_population_total",
    "expected_section_count",
    "expected_district_count",
    "expected_certification",
)


def _load(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("El manifiesto de campaña debe ser un objeto JSON")
    return data


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _hex(value: object, length: int, label: str) -> str:
    text = str(value or "").lower()
    if len(text) != length or any(ch not in "0123456789abcdef" for ch in text):
        raise ValueError(f"{label} debe contener {length} hexadecimales")
    return text


def _validate_reuse(row: dict[str, Any]) -> None:
    reuse = row.get("reuse")
    if not isinstance(reuse, dict):
        raise ValueError(f"{row.get('territory_id')}: reuse ausente")
    missing = [key for key in REUSE_FIELDS if key not in reuse]
    if missing:
        raise ValueError(f"{row.get('territory_id')}: faltan campos de procedencia: {missing}")
    if not isinstance(reuse["run_id"], int) or reuse["run_id"] <= 0:
        raise ValueError("reuse.run_id inválido")
    if reuse["checkpoint_stage"] != "SOURCE_PACKAGE":
        raise ValueError("La campaña sólo admite SOURCE_PACKAGE explícito; no último checkpoint")
    _hex(reuse["artifact_sha256"], 64, "reuse.artifact_sha256")
    _hex(reuse["m01_artifact_sha256"], 64, "reuse.m01_artifact_sha256")
    _hex(reuse["source_sha"], 40, "reuse.source_sha")
    if reuse["expected_certification"] != "READY":
        raise ValueError("La fuente reutilizada debe estar certificada READY")
    for key in ("expected_population_total", "expected_section_count", "expected_district_count"):
        if not isinstance(reuse[key], int) or reuse[key] <= 0:
            raise ValueError(f"{key} debe ser entero positivo")


def validate_manifest(path: Path) -> dict[str, Any]:
    data = _load(path)
    for key, value in EXPECTED_FIELDS.items():
        if data.get(key) != value:
            raise ValueError(f"{key}: esperado {value!r}, observado {data.get(key)!r}")
    if not data.get("campaign_id"):
        raise ValueError("campaign_id ausente")
    territories = data.get("territories")
    if not isinstance(territories, list) or len(territories) != 5:
        raise ValueError("La campaña debe contener exactamente cinco territorios")
    observed = [
        (
            str(row.get("slot")),
            row.get("territory_id"),
            row.get("territory_name"),
            row.get("publication_mode"),
        )
        for row in territories
    ]
    if observed != EXPECTED_TERRITORIES:
        raise ValueError(
            "Territorios, slots o modos no coinciden con el manifiesto aprobado: "
            + repr(observed)
        )
    if len({row[0] for row in observed}) != 5 or len({row[1] for row in observed}) != 5:
        raise ValueError("Slots o territorios duplicados")
    for row in territories:
        _validate_reuse(row)
    return data


def assert_productive_launch(event_name: str, ref_name: str, confirmation: str) -> None:
    if event_name != "workflow_dispatch":
        raise ValueError("La ejecución productiva sólo está permitida desde workflow_dispatch")
    if ref_name != "main":
        raise ValueError("La ejecución productiva sólo está permitida desde main")
    if confirmation != CONFIRMATION:
        raise ValueError("Falta confirmación explícita de campaña")


def artifact_namespace(campaign_instance: str, slot: str, territory_id: str) -> str:
    raw = f"{campaign_instance}--{slot}--{territory_id}"
    allowed = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_."
    cleaned = "".join(ch if ch in allowed else "-" for ch in raw)
    if not cleaned or len(cleaned) > 180:
        raise ValueError("artifact_namespace inválido")
    return cleaned


def build_matrix(
    path: Path,
    *,
    source_sha: str,
    campaign_instance: str,
    confirmation: str,
) -> dict[str, Any]:
    data = validate_manifest(path)
    if confirmation != CONFIRMATION:
        raise ValueError("Confirmación explícita incorrecta")
    code_sha = _hex(source_sha, 40, "source_sha")
    digest = sha256(path)
    include = []
    for territory in data["territories"]:
        slot = territory["slot"]
        territory_id = territory["territory_id"]
        namespace = f"{campaign_instance}/{slot}/{territory_id}"
        reuse = territory["reuse"]
        include.append(
            {
                "campaign_instance": campaign_instance,
                "slot": slot,
                "territory_id": territory_id,
                "territory_name": territory["territory_name"],
                "namespace": namespace,
                "artifact_namespace": artifact_namespace(campaign_instance, slot, territory_id),
                "source_sha": code_sha,
                "manifest_sha256": digest,
                "data_edition": data["data_edition"],
                "execution_mode": data["execution_mode"],
                "optimization_algorithm": data["optimization_algorithm"],
                "entrypoint": data["entrypoint"],
                "candidate_count": data["candidate_count"],
                "require_unique_hashes": data["require_unique_hashes"],
                "publication_mode": territory["publication_mode"],
                "campaign_confirmation": confirmation,
                "retry_failed": data["retry_failed"],
                "reuse_run_id": reuse["run_id"],
                "reuse_artifact_name": reuse["artifact_name"],
                "reuse_artifact_sha256": reuse["artifact_sha256"],
                "reuse_source_sha": reuse["source_sha"],
                "m01_artifact_name": reuse["m01_artifact_name"],
                "m01_artifact_sha256": reuse["m01_artifact_sha256"],
                "expected_population_total": reuse["expected_population_total"],
                "expected_section_count": reuse["expected_section_count"],
                "expected_district_count": reuse["expected_district_count"],
                "expected_certification": reuse["expected_certification"],
            }
        )
    return {"include": include}


def validate_reuse_metadata(
    reuse: dict[str, Any],
    *,
    run_head_sha: str,
    artifact_name: str,
    artifact_digest: str,
    m01_artifact_name: str,
    m01_artifact_digest: str,
) -> None:
    if run_head_sha != reuse["source_sha"]:
        raise ValueError("SHA de procedencia distinto del manifiesto")
    if artifact_name != reuse["artifact_name"]:
        raise ValueError("Artefacto reutilizado distinto del manifiesto")
    if artifact_digest.removeprefix("sha256:") != reuse["artifact_sha256"]:
        raise ValueError("Digest del producto reutilizado distinto del manifiesto")
    if m01_artifact_name != reuse["m01_artifact_name"]:
        raise ValueError("Artefacto M01 distinto del manifiesto")
    if m01_artifact_digest.removeprefix("sha256:") != reuse["m01_artifact_sha256"]:
        raise ValueError("Digest M01 distinto del manifiesto")


def _catalog_entry(root: Path, territory_id: str, edition: str) -> dict[str, Any]:
    catalog = yaml.safe_load(
        (root / "configuracion/catalogo_preparacion.yaml").read_text(encoding="utf-8")
    ) or {}
    for territory in catalog.get("territories", []):
        if territory.get("territory_id") == territory_id:
            edition_data = (territory.get("editions") or {}).get(str(edition))
            if not isinstance(edition_data, dict):
                break
            return edition_data
    raise ValueError(f"Catálogo sin {territory_id}/{edition}")


def _expected_k(contract: dict[str, Any]) -> int:
    validation = contract.get("validation") or {}
    if validation.get("expected_districts") is not None:
        return int(validation["expected_districts"])
    modules = contract.get("modulos") or {}
    m05 = modules.get("modulo_05_optimizar_distritos") or {}
    m04 = modules.get("modulo_04_generar_semillas") or {}
    value = m05.get("expected_districts") or m04.get("k_districts")
    if value is None:
        raise ValueError("Contrato sin número de distritos")
    return int(value)


def validate_repository_binding(
    manifest_path: Path, *, slot: str, root_dir: Path
) -> dict[str, Any]:
    data = validate_manifest(manifest_path)
    row = next((item for item in data["territories"] if item["slot"] == slot), None)
    if row is None:
        raise ValueError(f"Slot desconocido: {slot}")
    reuse = row["reuse"]
    catalog = _catalog_entry(root_dir, row["territory_id"], data["data_edition"])
    if catalog.get("preparation_status") != reuse["expected_certification"]:
        raise ValueError("Certificación de preparación distinta del manifiesto")
    if catalog.get("production_authorization") != "AUTHORIZED":
        raise ValueError("Territorio sin autorización de producción")
    contract_path = catalog.get("contract_path")
    if not contract_path:
        raise ValueError("Contrato territorial ausente")
    contract = yaml.safe_load((root_dir / contract_path).read_text(encoding="utf-8")) or {}
    meta = contract.get("meta") or {}
    if str(meta.get("year")) != data["data_edition"]:
        raise ValueError("Edición del contrato distinta del manifiesto")
    if _expected_k(contract) != reuse["expected_district_count"]:
        raise ValueError("Número de distritos del contrato distinto del manifiesto")
    return {
        "territory_id": row["territory_id"],
        "edition": data["data_edition"],
        "expected_population_total": reuse["expected_population_total"],
        "expected_section_count": reuse["expected_section_count"],
        "expected_district_count": reuse["expected_district_count"],
        "certification": reuse["expected_certification"],
    }


def _find_source_manifest(source_dir: Path) -> dict[str, Any]:
    candidates = []
    for path in source_dir.rglob("manifest.json"):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        if isinstance(data, dict) and "territory_id" in data and "edition" in data:
            candidates.append(data)
    if len(candidates) != 1:
        raise ValueError(f"Se esperaba un manifest.json territorial inequívoco; encontrados={len(candidates)}")
    return candidates[0]


def _read_m01_geojson(m01_dir: Path) -> dict[str, Any]:
    zips = sorted(m01_dir.rglob("*m01*secciones*poblacion*.geojson.zip"))
    if not zips:
        zips = sorted(m01_dir.rglob("*.geojson.zip"))
    if len(zips) != 1:
        raise ValueError(f"Checkpoint M01 no inequívoco; geojson.zip encontrados={len(zips)}")
    with zipfile.ZipFile(zips[0]) as archive:
        members = [name for name in archive.namelist() if name.lower().endswith(".geojson")]
        if len(members) != 1:
            raise ValueError("El ZIP M01 debe contener un único GeoJSON")
        return json.loads(archive.read(members[0]).decode("utf-8"))


def validate_materialized_reuse(
    manifest_path: Path,
    *,
    slot: str,
    root_dir: Path,
    source_dir: Path,
    m01_dir: Path,
) -> dict[str, Any]:
    expected = validate_repository_binding(manifest_path, slot=slot, root_dir=root_dir)
    source = _find_source_manifest(source_dir)
    if source.get("territory_id") != expected["territory_id"]:
        raise ValueError("El artefacto reutilizado pertenece a otro territorio")
    if str(source.get("edition")) != expected["edition"]:
        raise ValueError("El artefacto reutilizado pertenece a otra edición")
    geo = _read_m01_geojson(m01_dir)
    features = geo.get("features") or []
    section_count = len(features)
    pop_field = "POP_" + expected["edition"]
    values = []
    for feature in features:
        props = feature.get("properties") or {}
        value = props.get(pop_field)
        if value is None:
            raise ValueError(f"Sección M01 sin {pop_field}")
        values.append(float(value))
    population_total = sum(values)
    if section_count != expected["expected_section_count"]:
        raise ValueError(
            f"Secciones distintas: {section_count} != {expected['expected_section_count']}"
        )
    if abs(population_total - expected["expected_population_total"]) > 1e-6:
        raise ValueError(
            f"Población distinta: {population_total} != {expected['expected_population_total']}"
        )
    return {
        **expected,
        "population_total": int(population_total),
        "section_count": section_count,
        "status": "VALID",
    }


def validate_portfolio_contract(portfolio: dict[str, Any]) -> dict[str, Any]:
    candidates = portfolio.get("candidates")
    if not isinstance(candidates, list):
        candidates = []
    hashes = [str(row.get("assignment_hash") or "") for row in candidates]
    missing_hashes = sum(1 for value in hashes if not value)
    present = [value for value in hashes if value]
    unique_hashes = len(set(present))
    duplicate_hashes = len(present) - unique_hashes
    expected = 50
    candidate_count = int(portfolio.get("candidate_count") or len(candidates))
    candidate_count_valid = len(candidates)
    valid = (
        candidate_count == expected
        and candidate_count_valid == expected
        and unique_hashes == expected
        and missing_hashes == 0
        and duplicate_hashes == 0
        and int(portfolio.get("unique_candidate_count") or unique_hashes) == expected
    )
    return {
        "candidate_count_expected": expected,
        "candidate_count_valid": candidate_count_valid,
        "unique_candidate_hash_count": unique_hashes,
        "missing_candidate_hash_count": missing_hashes,
        "duplicate_candidate_hash_count": duplicate_hashes,
        "valid": valid,
    }




def portfolio_artifact_name(run_id: int | str, artifact_namespace: str) -> str:
    run_text = str(run_id).strip()
    namespace = str(artifact_namespace or "").strip()
    if not run_text.isdigit() or int(run_text) <= 0:
        raise ValueError("run_id de portfolio inválido")
    return f"ddd-state-{run_text}-M05" + (f"-{namespace}" if namespace else "")


def _iter_coordinate_pairs(value: Any):
    if isinstance(value, list) and len(value) >= 2 and all(isinstance(v, (int, float)) for v in value[:2]):
        yield float(value[0]), float(value[1])
        return
    if isinstance(value, list):
        for item in value:
            yield from _iter_coordinate_pairs(item)


def validate_portfolio_bundle(bundle_root: Path, *, expected_districts: int) -> dict[str, Any]:
    portfolio_path = _single(bundle_root, "portfolio.json")
    portfolio = json.loads(portfolio_path.read_text(encoding="utf-8"))
    strict = validate_portfolio_contract(portfolio)
    if not strict["valid"]:
        raise ValueError(
            "portfolio GerryChain 50 inválido: "
            f"valid={strict['candidate_count_valid']} "
            f"unique={strict['unique_candidate_hash_count']} "
            f"missing={strict['missing_candidate_hash_count']} "
            f"duplicates={strict['duplicate_candidate_hash_count']}"
        )

    verified = []
    for ordinal, row in enumerate(portfolio.get("candidates") or [], start=1):
        source_name = Path(str(row.get("geojson") or row.get("file") or "")).name
        if not source_name:
            seed = row.get("seed")
            source_name = f"candidate_{ordinal:03d}_seed_{seed}.geojson.zip"
        matches = sorted(bundle_root.rglob(source_name))
        if len(matches) != 1:
            raise ValueError(
                f"candidate-{ordinal:03d}: ZIP no inequívoco para {source_name}; encontrados={len(matches)}"
            )
        source = matches[0]
        expected_sha = _hex(row.get("sha256"), 64, f"candidate-{ordinal:03d}.sha256")
        observed_sha = sha256(source)
        if observed_sha != expected_sha:
            raise ValueError(
                f"candidate-{ordinal:03d}: SHA-256 del ZIP no coincide "
                f"observado={observed_sha} esperado={expected_sha}"
            )
        if not zipfile.is_zipfile(source):
            raise ValueError(f"candidate-{ordinal:03d}: candidato no es ZIP")
        with zipfile.ZipFile(source) as archive:
            members = [
                name for name in archive.namelist()
                if name.lower().endswith((".geojson", ".json")) and not name.endswith("/")
            ]
            if len(members) != 1:
                raise ValueError(
                    f"candidate-{ordinal:03d}: esperaba un único GeoJSON; encontrados={members}"
                )
            payload = json.loads(archive.read(members[0]).decode("utf-8"))
        if payload.get("type") != "FeatureCollection":
            raise ValueError(f"candidate-{ordinal:03d}: GeoJSON no es FeatureCollection")
        features = payload.get("features") or []
        if not features:
            raise ValueError(f"candidate-{ordinal:03d}: GeoJSON sin features")
        districts = set()
        for feature in features:
            geometry = feature.get("geometry")
            if not isinstance(geometry, dict) or not geometry.get("type"):
                raise ValueError(f"candidate-{ordinal:03d}: geometría ausente")
            coords = list(_iter_coordinate_pairs(geometry.get("coordinates")))
            if not coords:
                raise ValueError(f"candidate-{ordinal:03d}: geometría sin coordenadas")
            if any(not (-180.0 <= x <= 180.0 and -90.0 <= y <= 90.0) for x, y in coords):
                raise ValueError(f"candidate-{ordinal:03d}: geometría no está en WGS84/CRS84")
            district = str((feature.get("properties") or {}).get("district_id") or "")
            if not district:
                raise ValueError(f"candidate-{ordinal:03d}: feature sin district_id")
            districts.add(district)
        if len(districts) != int(expected_districts):
            raise ValueError(
                f"candidate-{ordinal:03d}: distritos observados={len(districts)} "
                f"esperados={int(expected_districts)}"
            )
        verified.append({
            "candidate_index": ordinal,
            "seed": row.get("seed"),
            "assignment_hash": row.get("assignment_hash"),
            "zip_sha256": observed_sha,
            "feature_count": len(features),
            "district_count": len(districts),
        })
    return {
        **strict,
        "portfolio_path": str(portfolio_path),
        "verified_candidate_zip_count": len(verified),
        "verified_wgs84_candidate_count": len(verified),
        "expected_districts": int(expected_districts),
        "candidates": verified,
    }


def validate_campaign_summary_for_promotion(summary: dict[str, Any]) -> list[dict[str, Any]]:
    territories = summary.get("territories")
    if summary.get("status") != "PASS":
        raise ValueError("La campaña no está en PASS; promoción prohibida")
    if not isinstance(territories, list) or len(territories) != 5:
        raise ValueError("La promoción exige exactamente cinco estados territoriales")
    required = {
        "candidate_count_expected": 50,
        "candidate_count_valid": 50,
        "unique_candidate_hash_count": 50,
        "missing_candidate_hash_count": 0,
        "duplicate_candidate_hash_count": 0,
        "entrypoint": ENTRYPOINT,
        "require_unique_hashes": True,
        "status": "PASS",
    }
    seen: set[str] = set()
    for row in territories:
        territory_id = str(row.get("territory_id") or "")
        if not territory_id or territory_id in seen:
            raise ValueError("Territorio ausente o duplicado en el resumen de campaña")
        seen.add(territory_id)
        mismatches = [
            key for key, expected in required.items()
            if row.get(key) != expected
        ]
        if mismatches:
            raise ValueError(
                f"{territory_id}: estado no promocionable: {', '.join(mismatches)}"
            )
    return territories


def release_identity(
    *,
    campaign_instance: str,
    slot: str,
    territory_id: str,
    asset_sha256: str,
) -> dict[str, str]:
    digest = _hex(asset_sha256, 64, "asset_sha256")
    safe_campaign = artifact_namespace(campaign_instance, slot, territory_id)
    release_tag = f"ensemble-{safe_campaign}-{digest[:16]}"
    return {
        "territory_id": territory_id,
        "slot": slot,
        "namespace": f"{campaign_instance}/{slot}/{territory_id}",
        "release_tag": release_tag,
        "asset_name": f"{release_tag}.zip",
        "sha256": digest,
    }


def publication_matrix(releases: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    if len(releases) != 5:
        raise ValueError("La publicación exige cinco releases")
    tags = [str(row.get("release_tag") or "") for row in releases]
    namespaces = [str(row.get("namespace") or "") for row in releases]
    territories = [str(row.get("territory_id") or "") for row in releases]
    if len(set(tags)) != 5 or not all(tags):
        raise ValueError("Los cinco releases deben ser distintos")
    if len(set(namespaces)) != 5 or not all(namespaces):
        raise ValueError("Los cinco namespaces deben ser distintos")
    if len(set(territories)) != 5 or not all(territories):
        raise ValueError("Los cinco territorios deben ser distintos")
    return {"include": releases}


def _single(root: Path, name: str) -> Path:
    matches = sorted(root.rglob(name))
    if len(matches) != 1:
        raise ValueError(f"{name}: esperaba exactamente uno bajo {root}; encontrados={len(matches)}")
    return matches[0]


def _extract_single_geojson(archive_path: Path, destination: Path) -> None:
    if not zipfile.is_zipfile(archive_path):
        raise ValueError(f"Candidato no es ZIP: {archive_path}")
    with zipfile.ZipFile(archive_path) as archive:
        members = [
            name for name in archive.namelist()
            if name.lower().endswith((".geojson", ".json")) and not name.endswith("/")
        ]
        if len(members) != 1:
            raise ValueError(f"{archive_path}: esperaba un único GeoJSON; encontrados={members}")
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(archive.read(members[0]))


def package_campaign_gallery(
    bundle_root: Path,
    output_zip: Path,
    *,
    campaign_instance: str,
    expected_districts: int,
) -> dict[str, Any]:
    from ddd_ensemble.gallery import _write_web_geojson

    status_path = _single(bundle_root, "campaign_status.json")
    portfolio_path = _single(bundle_root, "portfolio.json")
    status = json.loads(status_path.read_text(encoding="utf-8"))
    portfolio = json.loads(portfolio_path.read_text(encoding="utf-8"))
    strict = validate_portfolio_contract(portfolio)
    required_status = {
        "status": "PASS",
        "entrypoint": ENTRYPOINT,
        "require_unique_hashes": True,
        "candidate_count_expected": 50,
        "candidate_count_valid": 50,
        "unique_candidate_hash_count": 50,
        "missing_candidate_hash_count": 0,
        "duplicate_candidate_hash_count": 0,
    }
    mismatches = [
        key for key, expected in required_status.items()
        if status.get(key) != expected
    ]
    if mismatches or not strict["valid"]:
        raise ValueError(
            f"{status.get('territory_id')}: bundle no promocionable; "
            f"status={mismatches}, portfolio_valid={strict['valid']}"
        )
    if status.get("campaign_instance") != campaign_instance:
        raise ValueError("campaign_instance del bundle no coincide")

    territory_id = str(status["territory_id"])
    territory_name = str(status.get("territory_name") or territory_id)
    slot = str(status["slot"])
    candidates = portfolio.get("candidates") or []
    if len(candidates) != 50:
        raise ValueError(f"{territory_id}: portfolio debe contener 50 candidatos")

    output_zip.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as raw:
        stage = Path(raw) / "ensemble"
        site = stage / "site"
        assets = site / "assets"
        data_dir = site / "data"
        assets.mkdir(parents=True, exist_ok=True)
        data_dir.mkdir(parents=True, exist_ok=True)

        portable_candidates = []
        for ordinal, row in enumerate(candidates, start=1):
            candidate_id = f"candidate-{ordinal:03d}"
            source_name = str(row.get("file") or row.get("geojson") or "")
            source = None
            if source_name:
                matches = sorted(bundle_root.rglob(Path(source_name).name))
                if len(matches) == 1:
                    source = matches[0]
            if source is None:
                seed = row.get("seed")
                pattern = f"candidate_{ordinal:03d}_seed_{seed}.geojson.zip"
                matches = sorted(bundle_root.rglob(pattern))
                if len(matches) != 1:
                    raise ValueError(
                        f"{territory_id}/{candidate_id}: candidato ZIP no inequívoco"
                    )
                source = matches[0]

            analytical = stage / "_analytical" / f"{candidate_id}.geojson"
            _extract_single_geojson(source, analytical)
            web_asset = assets / f"{candidate_id}.geojson"
            _write_web_geojson(analytical, web_asset)
            portable_candidates.append({
                "candidate_id": candidate_id,
                "profile": "gerrychain_50",
                "seed": row.get("seed"),
                "assignment_hash": row.get("assignment_hash"),
                "asset": f"assets/{candidate_id}.geojson",
                "metrics": {"population": {"district_count": int(expected_districts)}},
            })

        summary = {
            "schema": "ddd.campaign-ensemble-summary/1.0",
            "territory_id": territory_id,
            "territory_label": territory_name,
            "ensemble_id": f"{campaign_instance}-{slot}-{territory_id}",
            "campaign_instance": campaign_instance,
            "slot": slot,
            "complete": True,
            "entrypoint": ENTRYPOINT,
            "require_unique_hashes": True,
            "candidate_count_expected": 50,
            "candidate_count_valid": 50,
            "unique_candidate_hash_count": 50,
            "candidates": portable_candidates,
        }
        (data_dir / "summary.json").write_text(
            json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

        source_gallery = sorted(bundle_root.rglob("gallery/index.html"))
        if len(source_gallery) == 1:
            shutil.copy2(source_gallery[0], site / "index.html")
        else:
            (site / "index.html").write_text(
                "<!doctype html><meta charset=utf-8>"
                f"<title>{territory_name}</title><h1>{territory_name}</h1>"
                "<p>Campaña GerryChain 50: 50 alternativas territoriales.</p>",
                encoding="utf-8",
            )

        manifest = {
            "schema": "ddd.ensemble-artifact/1.0",
            "campaign_instance": campaign_instance,
            "territory_id": territory_id,
            "slot": slot,
            "complete": True,
            "entrypoint": ENTRYPOINT,
            "candidate_count_expected": 50,
            "candidate_count_valid": 50,
            "unique_candidate_hash_count": 50,
        }
        (stage / "artifact-manifest.json").write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

        with zipfile.ZipFile(output_zip, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            for path in sorted(stage.rglob("*")):
                if path.is_file() and "_analytical" not in path.parts:
                    archive.write(path, path.relative_to(stage))

    digest = sha256(output_zip)
    identity = release_identity(
        campaign_instance=campaign_instance,
        slot=slot,
        territory_id=territory_id,
        asset_sha256=digest,
    )
    return {
        **identity,
        "candidate_count_expected": 50,
        "candidate_count_valid": 50,
        "unique_candidate_hash_count": 50,
        "gallery": f"{territory_id}/{identity['release_tag']}",
    }


def aggregate(
    path: Path,
    reports_root: Path,
    *,
    campaign_instance: str,
    source_sha: str,
) -> dict[str, Any]:
    data = validate_manifest(path)
    digest = sha256(path)
    reports = {}
    for candidate in reports_root.rglob("campaign_status.json"):
        try:
            row = json.loads(candidate.read_text(encoding="utf-8"))
        except Exception:
            continue
        if row.get("campaign_instance") == campaign_instance:
            reports[row.get("territory_id")] = row

    rows = []
    failed = []
    for territory in data["territories"]:
        territory_id = territory["territory_id"]
        row = reports.get(territory_id)
        if row is None:
            item = {
                "slot": territory["slot"],
                "territory_id": territory_id,
                "territory_name": territory["territory_name"],
                "publication_mode": territory["publication_mode"],
                "status": "MISSING",
                "reason": "campaign_status.json ausente",
            }
        else:
            item = copy.deepcopy(row)
            mismatches = []
            checks = {
                "slot": territory["slot"],
                "publication_mode": territory["publication_mode"],
                "source_sha": source_sha,
                "manifest_sha256": digest,
                "entrypoint": ENTRYPOINT,
                "require_unique_hashes": True,
                "candidate_count_expected": 50,
                "candidate_count_valid": 50,
                "unique_candidate_hash_count": 50,
                "missing_candidate_hash_count": 0,
                "duplicate_candidate_hash_count": 0,
            }
            for key, expected in checks.items():
                if row.get(key) != expected:
                    mismatches.append(key)
            if mismatches:
                item["status"] = "FAIL"
                item["reason"] = "Contrato de campaña inconsistente: " + ", ".join(mismatches)
        rows.append(item)
        if item.get("status") != "PASS":
            failed.append(territory_id)

    return {
        "schema": "ddd.campaign-summary/1.1",
        "campaign_id": data["campaign_id"],
        "campaign_instance": campaign_instance,
        "source_sha": source_sha,
        "manifest_sha256": digest,
        "entrypoint": data["entrypoint"],
        "require_unique_hashes": data["require_unique_hashes"],
        "territory_count_expected": 5,
        "territory_count_reported": len(reports),
        "failed_territories": failed,
        "status": "PASS" if not failed else "FAIL",
        "territories": rows,
    }


def write_markdown(summary: dict[str, Any], path: Path) -> None:
    lines = [
        "# Campaña " + summary["campaign_instance"],
        "",
        "- estado: " + summary["status"],
        "- source SHA: " + summary["source_sha"],
        "- manifest SHA-256: " + summary["manifest_sha256"],
        "- entrypoint: " + summary["entrypoint"],
        "- require_unique_hashes: " + str(summary["require_unique_hashes"]).lower(),
        "",
        "| Slot | Territorio | Publicación | Estado |",
        "|---|---|---|---|",
    ]
    for row in summary["territories"]:
        lines.append(
            "| {slot} | {territory} | {publication} | {status} |".format(
                slot=row.get("slot", ""),
                territory=row.get("territory_name", row.get("territory_id", "")),
                publication=row.get("publication_mode", ""),
                status=row.get("status", ""),
            )
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    commands = parser.add_subparsers(dest="command", required=True)
    validate = commands.add_parser("validate")
    validate.add_argument("--manifest", type=Path, required=True)
    matrix = commands.add_parser("matrix")
    matrix.add_argument("--manifest", type=Path, required=True)
    matrix.add_argument("--source-sha", required=True)
    matrix.add_argument("--campaign-instance", required=True)
    matrix.add_argument("--confirmation", required=True)
    reuse = commands.add_parser("validate-reuse")
    reuse.add_argument("--manifest", type=Path, required=True)
    reuse.add_argument("--slot", required=True)
    reuse.add_argument("--root-dir", type=Path, default=Path("."))
    reuse.add_argument("--source-dir", type=Path, required=True)
    reuse.add_argument("--m01-dir", type=Path, required=True)
    portfolio = commands.add_parser("validate-portfolio")
    portfolio.add_argument("--portfolio", type=Path, required=True)
    package = commands.add_parser("package-ensemble")
    package.add_argument("--bundle-root", type=Path, required=True)
    package.add_argument("--output-zip", type=Path, required=True)
    package.add_argument("--campaign-instance", required=True)
    package.add_argument("--expected-districts", type=int, required=True)
    package.add_argument("--output-json", type=Path)
    aggregate_parser = commands.add_parser("aggregate")
    aggregate_parser.add_argument("--manifest", type=Path, required=True)
    aggregate_parser.add_argument("--reports-root", type=Path, required=True)
    aggregate_parser.add_argument("--campaign-instance", required=True)
    aggregate_parser.add_argument("--source-sha", required=True)
    aggregate_parser.add_argument("--output-json", type=Path, required=True)
    aggregate_parser.add_argument("--output-md", type=Path, required=True)
    return parser


def main() -> None:
    args = _parser().parse_args()
    if args.command == "validate":
        data = validate_manifest(args.manifest)
        print(json.dumps({"status": "VALID", "campaign_id": data["campaign_id"], "manifest_sha256": sha256(args.manifest)}, ensure_ascii=False))
        return
    if args.command == "matrix":
        print(json.dumps(build_matrix(args.manifest, source_sha=args.source_sha, campaign_instance=args.campaign_instance, confirmation=args.confirmation), ensure_ascii=False, separators=(",", ":")))
        return
    if args.command == "validate-reuse":
        result = validate_materialized_reuse(args.manifest, slot=args.slot, root_dir=args.root_dir, source_dir=args.source_dir, m01_dir=args.m01_dir)
        print(json.dumps(result, ensure_ascii=False, sort_keys=True))
        return
    if args.command == "validate-portfolio":
        result = validate_portfolio_contract(_load(args.portfolio))
        print(json.dumps(result, ensure_ascii=False, sort_keys=True))
        raise SystemExit(0 if result["valid"] else 2)
    if args.command == "package-ensemble":
        result = package_campaign_gallery(
            args.bundle_root,
            args.output_zip,
            campaign_instance=args.campaign_instance,
            expected_districts=args.expected_districts,
        )
        if args.output_json:
            args.output_json.parent.mkdir(parents=True, exist_ok=True)
            args.output_json.write_text(
                json.dumps(result, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
        print(json.dumps(result, ensure_ascii=False, sort_keys=True))
        return

    summary = aggregate(args.manifest, args.reports_root, campaign_instance=args.campaign_instance, source_sha=args.source_sha)
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_markdown(summary, args.output_md)
    print(json.dumps(summary, ensure_ascii=False))
    raise SystemExit(0 if summary["status"] == "PASS" else 2)


if __name__ == "__main__":
    main()
