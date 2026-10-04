from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
from typing import Any


SCHEMA = "ddd.official-geometry-normalization/2.0"
EVIDENCE_SCHEMA = "ddd.geometry-normalization-evidence/1.0"
PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_POLICY_PATH = PROJECT_ROOT / "configuracion" / "politica_normalizacion_geometrica.yaml"


def _json_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def _sha256_json(value: Any) -> str:
    return hashlib.sha256(_json_bytes(value)).hexdigest()


def load_geometry_policy(path: Path | None = None) -> tuple[dict, str, str]:
    import yaml

    policy_path = Path(path or DEFAULT_POLICY_PATH)
    data = yaml.safe_load(policy_path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or data.get("schema") != "ddd.geometry-normalization-policy/1.0":
        raise ValueError("GEOMETRY_NORMALIZATION_POLICY_INVALID: schema no reconocido")
    if data.get("acceptance", {}).get("numeric_acceptance_tolerance", "MISSING") is not None:
        raise ValueError("GEOMETRY_NORMALIZATION_POLICY_INVALID: se exige tolerancia semántica nula")
    if not data.get("metric_crs"):
        raise ValueError("GEOMETRY_NORMALIZATION_POLICY_INVALID: falta metric_crs")
    known = {
        "DEDUPLICATE_EXACT_MULTIPOLYGON_COMPONENTS",
        "DEDUPLICATE_EXACT_INTERIOR_RINGS",
        "MAKE_VALID_DUAL_CONSENSUS_BOUNDARY_PRESERVING",
    }
    allowed = set(data.get("allowed_methods") or [])
    if not allowed or not allowed.issubset(known):
        raise ValueError("GEOMETRY_NORMALIZATION_POLICY_INVALID: métodos no reconocidos")
    return data, hashlib.sha256(policy_path.read_bytes()).hexdigest(), policy_path.as_posix()


def geometry_runtime_versions() -> dict[str, str]:
    import geopandas
    import pyogrio
    import pyproj
    import shapely

    return {
        "geopandas": str(geopandas.__version__),
        "shapely": str(shapely.__version__),
        "geos": str(shapely.geos_version_string),
        "pyproj": str(pyproj.__version__),
        "pyogrio": str(pyogrio.__version__),
    }



def persist_raw_ogc_response(
    evidence_dir: Path,
    *,
    source_id: str,
    source_year: int,
    province_code: str,
    url: str,
    payload: bytes,
) -> dict:
    """Conserva byte a byte la respuesta HTTP oficial antes de parsearla o transformarla."""
    evidence_dir = Path(evidence_dir).resolve()
    rel = Path("raw") / str(source_id) / str(int(source_year)) / f"{province_code}.geojson"
    destination = evidence_dir / rel
    destination.parent.mkdir(parents=True, exist_ok=True)
    digest = hashlib.sha256(payload).hexdigest()
    if destination.exists():
        existing = destination.read_bytes()
        if hashlib.sha256(existing).hexdigest() != digest:
            raise ValueError(
                "RAW_OFFICIAL_RESPONSE_IDENTITY_COLLISION: "
                f"{rel.as_posix()} ya existe con otra huella"
            )
    else:
        destination.write_bytes(payload)

    record = {
        "source_id": str(source_id),
        "source_year": int(source_year),
        "province_code": str(province_code).zfill(2),
        "url": str(url),
        "path": rel.as_posix(),
        "sha256": digest,
        "bytes": len(payload),
    }
    manifest_path = evidence_dir / "raw_official_responses.json"
    if manifest_path.is_file():
        document = json.loads(manifest_path.read_text(encoding="utf-8"))
        if (
            not isinstance(document, dict)
            or document.get("schema") != "ddd.raw-official-responses/1.0"
        ):
            raise ValueError("RAW_OFFICIAL_RESPONSE_MANIFEST_INVALID")
    else:
        document = {"schema": "ddd.raw-official-responses/1.0", "responses": []}

    responses = [
        row
        for row in (document.get("responses") or [])
        if not (
            str(row.get("source_id")) == record["source_id"]
            and int(row.get("source_year")) == record["source_year"]
            and str(row.get("province_code")).zfill(2) == record["province_code"]
        )
    ]
    responses.append(record)
    responses.sort(
        key=lambda row: (
            str(row["source_id"]),
            int(row["source_year"]),
            str(row["province_code"]),
        )
    )
    document["responses"] = responses
    manifest_path.write_text(
        json.dumps(document, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    return record


def _sha256_geometry(geometry: Any) -> str:
    from shapely import normalize, to_wkb

    canonical = normalize(geometry)
    payload = to_wkb(
        canonical,
        hex=False,
        output_dimension=2,
        byte_order=1,
        include_srid=False,
    )
    return hashlib.sha256(payload).hexdigest()


def _geometry_type(geometry: Any) -> str:
    return str(getattr(geometry, "geom_type", type(geometry).__name__))


def _component_count(geometry: Any) -> int:
    if _geometry_type(geometry) == "MultiPolygon":
        return len(list(geometry.geoms))
    return 1


def _issue(section_id: str, geometry: Any) -> dict:
    from shapely import is_valid_reason

    return {
        "section_id": str(section_id),
        "geometry_type": _geometry_type(geometry),
        "geometry_sha256": _sha256_geometry(geometry),
        "component_count": _component_count(geometry),
        "validity_reason": str(is_valid_reason(geometry)),
    }


def _polygon_parts(geometry: Any) -> list[Any]:
    if geometry.geom_type == "Polygon":
        return [geometry]
    if geometry.geom_type == "MultiPolygon":
        return list(geometry.geoms)
    return []


def _prove_exact_polygonal_set(expected: Any, candidate: Any) -> dict:
    """Demuestra igualdad de conjunto y frontera sin tolerancia numérica."""
    from shapely.ops import unary_union

    expected_boundary = unary_union(
        [part.boundary for part in _polygon_parts(expected)]
    )
    candidate_boundary = unary_union(
        [part.boundary for part in _polygon_parts(candidate)]
    )
    symmetric = expected.symmetric_difference(candidate)
    return {
        "point_set_equal": bool(expected.equals(candidate)),
        "boundary_set_equal": bool(expected_boundary.equals(candidate_boundary)),
        "symmetric_difference_empty": bool(symmetric.is_empty),
        "symmetric_difference_area": float(symmetric.area),
        "tolerance": None,
    }


def _dedupe_multipolygon_components(
    geometry: Any,
) -> tuple[Any | None, dict | None]:
    from shapely import MultiPolygon
    from shapely.ops import unary_union

    if geometry.geom_type != "MultiPolygon":
        return None, None
    parts = list(geometry.geoms)
    if len(parts) < 2 or any(
        part.is_empty or not part.is_valid for part in parts
    ):
        return None, None

    unique: list[Any] = []
    seen: set[str] = set()
    removed: list[dict] = []
    for index, part in enumerate(parts):
        digest = _sha256_geometry(part)
        if digest in seen:
            removed.append(
                {"component_index": index, "geometry_sha256": digest}
            )
            continue
        seen.add(digest)
        unique.append(part)
    if not removed:
        return None, None

    candidate = MultiPolygon(unique)
    if candidate.is_empty or not candidate.is_valid:
        return None, None

    # El contenedor inválido contiene miembros poligonales válidos y duplicados.
    # La referencia semántica se define como su unión exacta, no mediante make_valid.
    expected = unary_union(parts)
    proof = _prove_exact_polygonal_set(expected, candidate)
    required = (
        "point_set_equal",
        "boundary_set_equal",
        "symmetric_difference_empty",
    )
    if not all(proof[key] for key in required):
        return None, None
    if proof["symmetric_difference_area"] != 0.0:
        return None, None

    return candidate, {
        "method": "DEDUPLICATE_EXACT_MULTIPOLYGON_COMPONENTS",
        "removed_components": removed,
        "before_component_count": len(parts),
        "after_component_count": len(unique),
        "proof": proof,
    }


def _dedupe_polygon_holes(
    geometry: Any,
) -> tuple[Any | None, dict | None]:
    from shapely import Polygon
    from shapely.ops import unary_union

    if geometry.geom_type != "Polygon" or not geometry.interiors:
        return None, None

    shell = Polygon(geometry.exterior)
    if shell.is_empty or not shell.is_valid:
        return None, None

    unique_rings = []
    unique_hole_polygons = []
    seen: set[str] = set()
    removed: list[dict] = []
    for index, ring in enumerate(geometry.interiors):
        hole = Polygon(ring)
        if hole.is_empty or not hole.is_valid or hole.area <= 0:
            return None, None
        digest = _sha256_geometry(hole)
        if digest in seen:
            removed.append({"hole_index": index, "geometry_sha256": digest})
            continue
        seen.add(digest)
        unique_rings.append(list(ring.coords))
        unique_hole_polygons.append(hole)
    if not removed:
        return None, None

    candidate = Polygon(
        list(geometry.exterior.coords),
        holes=unique_rings,
    )
    if candidate.is_empty or not candidate.is_valid:
        return None, None

    # La referencia se construye con primitivas válidas: shell menos la unión
    # exacta de huecos únicos. No se pide a GEOS interpretar el polígono inválido.
    expected = shell.difference(unary_union(unique_hole_polygons))
    proof = _prove_exact_polygonal_set(expected, candidate)
    required = (
        "point_set_equal",
        "boundary_set_equal",
        "symmetric_difference_empty",
    )
    if not all(proof[key] for key in required):
        return None, None
    if proof["symmetric_difference_area"] != 0.0:
        return None, None

    return candidate, {
        "method": "DEDUPLICATE_EXACT_INTERIOR_RINGS",
        "removed_holes": removed,
        "before_hole_count": len(geometry.interiors),
        "after_hole_count": len(unique_rings),
        "proof": proof,
    }


def _leaf_types(geometry: Any) -> list[str]:
    if geometry.geom_type == "GeometryCollection":
        result: list[str] = []
        for part in geometry.geoms:
            result.extend(_leaf_types(part))
        return result
    return [geometry.geom_type]


def _polygonal_only(geometry: Any) -> bool:
    return set(_leaf_types(geometry)).issubset({"Polygon", "MultiPolygon"})


def _metric_geometry(geometry: Any, source_crs: str, metric_crs: str) -> Any:
    import geopandas as gpd

    return gpd.GeoSeries([geometry], crs=source_crs).to_crs(metric_crs).iloc[0]


def _metric_change_evidence(a: Any, b: Any, source_crs: str, metric_crs: str) -> dict:
    ma = _metric_geometry(a, source_crs, metric_crs)
    mb = _metric_geometry(b, source_crs, metric_crs)
    symmetric = ma.symmetric_difference(mb)
    return {
        "metric_crs": metric_crs,
        "hausdorff_distance_m": float(ma.hausdorff_distance(mb)),
        "symmetric_difference_area_m2": float(symmetric.area),
    }


def _reason_allowed(policy: dict, method: str, reason: str) -> bool:
    prefixes = (
        policy.get("allowed_invalidity_reason_prefixes", {}).get(method) or []
    )
    return any(str(reason).startswith(str(prefix)) for prefix in prefixes)


def _repair_self_intersection_consensus(
    geometry: Any,
    *,
    source_crs: str,
    metric_crs: str,
) -> tuple[Any | None, dict]:
    from shapely import make_valid

    linework = make_valid(geometry, method="linework", keep_collapsed=True)
    structure = make_valid(geometry, method="structure", keep_collapsed=False)
    audit = {
        "method": "MAKE_VALID_DUAL_CONSENSUS_BOUNDARY_PRESERVING",
        "parameters": {
            "linework": {"method": "linework", "keep_collapsed": True},
            "structure": {"method": "structure", "keep_collapsed": False},
        },
        "linework_type": linework.geom_type,
        "linework_leaf_types": _leaf_types(linework),
        "structure_type": structure.geom_type,
        "structure_leaf_types": _leaf_types(structure),
    }
    if not _polygonal_only(linework) or not _polygonal_only(structure):
        audit["failure"] = "NON_POLYGONAL_COMPONENT_AFTER_REPAIR"
        return None, audit
    if (
        linework.is_empty
        or structure.is_empty
        or not linework.is_valid
        or not structure.is_valid
    ):
        audit["failure"] = "REPAIR_NOT_VALID_POLYGONAL"
        return None, audit

    consensus_equal = bool(linework.equals(structure))
    boundary_equal = bool(geometry.boundary.equals(linework.boundary))
    symmetric = linework.symmetric_difference(structure)
    audit.update({
        "independent_candidate_equal": consensus_equal,
        "source_boundary_set_equal": boundary_equal,
        "candidate_symmetric_difference_empty": bool(symmetric.is_empty),
        "candidate_symmetric_difference_area_source_units": float(symmetric.area),
        "metric_consensus": _metric_change_evidence(
            linework, structure, source_crs, metric_crs
        ),
        "metric_raw_boundary_to_candidate_boundary": _metric_change_evidence(
            geometry.boundary, linework.boundary, source_crs, metric_crs
        ),
    })
    if not consensus_equal:
        audit["failure"] = "INDEPENDENT_REPAIR_DISAGREEMENT"
        return None, audit
    if not boundary_equal:
        audit["failure"] = "SOURCE_BOUNDARY_SET_CHANGED"
        return None, audit
    if not symmetric.is_empty:
        audit["failure"] = "INDEPENDENT_REPAIR_SYMMETRIC_DIFFERENCE"
        return None, audit
    return linework, audit


def normalize_official_geometry(
    section_id: str,
    geometry: Any,
    *,
    source_crs: str = "EPSG:4326",
    policy: dict | None = None,
    raw_geojson: Any | None = None,
    stage: str = "RAW_SOURCE_FEATURE_AFTER_DECODE",
) -> tuple[Any, dict]:
    """Normalización geométrica común, conservadora y fail-closed.

    No acepta make_valid() por sí solo. Las auto-intersecciones sólo se
    normalizan si linework y structure producen exactamente el mismo conjunto
    poligonal y la frontera fuente queda conservada como conjunto. Ningún
    componente no poligonal se descarta.
    """
    policy_data = policy or load_geometry_policy()[0]
    metric_crs = str(policy_data["metric_crs"])
    before = _issue(section_id, geometry)
    before["stage"] = stage
    before["crs"] = str(source_crs)
    before["raw_geojson_sha256"] = (
        _sha256_json(raw_geojson) if raw_geojson is not None else None
    )
    libraries = geometry_runtime_versions()

    if geometry.is_empty:
        return geometry, {
            "status": "BLOCKED",
            "before": before,
            "method": None,
            "reason": "GEOMETRY_EMPTY",
            "libraries": libraries,
        }
    if geometry.geom_type not in {"Polygon", "MultiPolygon"}:
        return geometry, {
            "status": "BLOCKED",
            "before": before,
            "method": None,
            "reason": "NON_POLYGONAL_GEOMETRY",
            "libraries": libraries,
        }
    if geometry.is_valid:
        return geometry, {
            "status": "UNCHANGED",
            "before": before,
            "after": before,
            "method": "NONE",
            "libraries": libraries,
        }

    allowed = set(policy_data.get("allowed_methods") or [])
    exact_repairs = []
    if "DEDUPLICATE_EXACT_INTERIOR_RINGS" in allowed:
        exact_repairs.append(_dedupe_polygon_holes)
    if "DEDUPLICATE_EXACT_MULTIPOLYGON_COMPONENTS" in allowed:
        exact_repairs.append(_dedupe_multipolygon_components)
    for repair in exact_repairs:
        candidate, method_audit = repair(geometry)
        if candidate is None:
            continue
        source_boundary_equal = bool(
            geometry.boundary.equals(candidate.boundary)
        )
        if not source_boundary_equal:
            continue
        after = _issue(section_id, candidate)
        after["stage"] = "NORMALIZED_DERIVED_GEOMETRY"
        after["crs"] = str(source_crs)
        return candidate, {
            "status": "NORMALIZED",
            "before": before,
            "after": after,
            **(method_audit or {}),
            "source_boundary_set_equal": source_boundary_equal,
            "libraries": libraries,
            "raw_polygon_area_comparison": {
                "status": "NOT_USED_FOR_ACCEPTANCE",
                "reason": "invalid_polygon_area_has_no_reliable_equivalence_semantics",
            },
            "metric_boundary_change": _metric_change_evidence(
                geometry.boundary,
                candidate.boundary,
                source_crs,
                metric_crs,
            ),
        }

    method = "MAKE_VALID_DUAL_CONSENSUS_BOUNDARY_PRESERVING"
    if (
        method in allowed
        and _reason_allowed(policy_data, method, before["validity_reason"])
    ):
        candidate, method_audit = _repair_self_intersection_consensus(
            geometry,
            source_crs=source_crs,
            metric_crs=metric_crs,
        )
        if candidate is not None:
            after = _issue(section_id, candidate)
            after["stage"] = "NORMALIZED_DERIVED_GEOMETRY"
            return candidate, {
                "status": "NORMALIZED",
                "before": before,
                "after": after,
                **method_audit,
                "libraries": libraries,
                "raw_polygon_area_comparison": {
                    "status": "NOT_USED_FOR_ACCEPTANCE",
                    "reason": "invalid_polygon_area_has_no_reliable_equivalence_semantics",
                },
            }
        return geometry, {
            "status": "BLOCKED",
            "before": before,
            "method": method,
            "reason": method_audit.get("failure") or "REPAIR_PROOF_FAILED",
            "repair_attempt": method_audit,
            "libraries": libraries,
        }

    return geometry, {
        "status": "BLOCKED",
        "before": before,
        "method": None,
        "reason": "INVALIDITY_CLASS_NOT_AUTO_NORMALIZABLE_BY_POLICY",
        "libraries": libraries,
    }


def _properties_digest(features: list[dict], section_id_field: str) -> str:
    rows = []
    for feature in features:
        props = copy.deepcopy(feature.get("properties") or {})
        rows.append({
            "section_id": str(props.get(section_id_field) or ""),
            "properties": props,
        })
    rows.sort(key=lambda row: row["section_id"])
    return _sha256_json(rows)


def _feature_geometry_digest(features: list[dict], section_id_field: str) -> str:
    from shapely.geometry import shape

    rows = []
    for feature in features:
        props = feature.get("properties") or {}
        raw = feature.get("geometry")
        rows.append({
            "section_id": str(props.get(section_id_field) or ""),
            "geometry_sha256": _sha256_geometry(shape(raw)) if raw is not None else None,
        })
    rows.sort(key=lambda row: row["section_id"])
    return _sha256_json(rows)


def _candidate_overlap_evidence(
    section_ids: list[str],
    geometries: list[Any],
    *,
    source_crs: str,
    metric_crs: str,
) -> list[dict]:
    from shapely.strtree import STRtree

    if not geometries:
        return []
    tree = STRtree(geometries)
    pairs = tree.query(geometries, predicate="intersects")
    overlaps: list[dict] = []
    seen: set[tuple[int, int]] = set()
    for left, right in zip(pairs[0].tolist(), pairs[1].tolist(), strict=False):
        i, j = int(left), int(right)
        if i >= j or (i, j) in seen:
            continue
        seen.add((i, j))
        a, b = geometries[i], geometries[j]
        if not a.relate_pattern(b, "T********"):
            continue
        ma = _metric_geometry(a, source_crs, metric_crs)
        mb = _metric_geometry(b, source_crs, metric_crs)
        overlaps.append({
            "section_a": section_ids[i],
            "section_b": section_ids[j],
            "intersection_area_m2": float(ma.intersection(mb).area),
        })
    overlaps.sort(key=lambda row: (row["section_a"], row["section_b"]))
    return overlaps


def _candidate_gap_diagnostics(
    geometries: list[Any],
    *,
    source_crs: str,
    metric_crs: str,
) -> dict:
    from shapely import Polygon
    from shapely.ops import unary_union

    coverage = unary_union(geometries)
    polygons = _polygon_parts(coverage)
    holes = [
        Polygon(ring)
        for polygon in polygons
        for ring in polygon.interiors
    ]
    hole_areas_m2 = [
        float(_metric_geometry(hole, source_crs, metric_crs).area)
        for hole in holes
    ]
    return {
        "status": "OBSERVED_NOT_CLASSIFIED",
        "coverage_geometry_type": coverage.geom_type,
        "coverage_component_count": len(polygons),
        "interior_gap_count": len(holes),
        "interior_gap_area_m2": float(sum(hole_areas_m2)),
        "reason": (
            "Observed interior holes can be measured, but without an "
            "independent authoritative territory mask they cannot be "
            "classified as legitimate or erroneous."
        ),
    }


def _contact_evidence(
    section_ids: list[str],
    raw_geometries: list[Any],
    derived_geometries: list[Any],
    changed_ids: set[str],
) -> dict:
    by_id = {section_id: index for index, section_id in enumerate(section_ids)}
    changed: list[dict] = []
    limitations: list[dict] = []
    for section_id in sorted(changed_ids):
        i = by_id[section_id]
        raw_boundary = raw_geometries[i].boundary
        derived_boundary = derived_geometries[i].boundary
        raw_contacts: dict[str, str] = {}
        derived_contacts: dict[str, str] = {}
        for j, other_id in enumerate(section_ids):
            if i == j:
                continue
            try:
                raw_contact = raw_boundary.intersection(raw_geometries[j].boundary)
                derived_contact = derived_boundary.intersection(
                    derived_geometries[j].boundary
                )
            except Exception as exc:
                limitations.append({
                    "section_id": section_id,
                    "neighbor_id": other_id,
                    "reason": "BOUNDARY_CONTACT_COMPARISON_UNRELIABLE",
                    "detail": str(exc),
                })
                continue
            if not raw_contact.is_empty:
                raw_contacts[other_id] = _sha256_geometry(raw_contact)
            if not derived_contact.is_empty:
                derived_contacts[other_id] = _sha256_geometry(derived_contact)
        changed.append({
            "section_id": section_id,
            "raw_contact_ids": sorted(raw_contacts),
            "derived_contact_ids": sorted(derived_contacts),
            "contact_id_set_equal": set(raw_contacts) == set(derived_contacts),
            "contact_geometry_equal": raw_contacts == derived_contacts,
        })
    return {
        "changed_sections": changed,
        "limitations": limitations,
        "all_contact_id_sets_preserved": (
            not limitations
            and all(row["contact_id_set_equal"] for row in changed)
        ),
        "all_contact_geometries_preserved": (
            not limitations
            and all(row["contact_geometry_equal"] for row in changed)
        ),
    }


def normalize_official_features(
    features: list[dict],
    section_id_field: str,
    *,
    crs: str = "EPSG:4326",
    coverage_field: str | None = None,
    policy: dict | None = None,
    policy_sha256: str | None = None,
    policy_path: str | None = None,
    source_stage: str = (
        "RAW_SOURCE_FEATURE_AFTER_JSON_DECODE_BEFORE_GEOMETRY_TRANSFORMATION"
    ),
) -> tuple[list[dict], dict]:
    from shapely.geometry import mapping, shape

    if policy is None:
        policy, policy_sha256, policy_path = load_geometry_policy()
    metric_crs = str(policy["metric_crs"])
    normalized: list[dict] = []
    issues: list[dict] = []
    raw_geometries: list[Any] = []
    derived_geometries: list[Any] = []
    section_ids: list[str] = []
    valid_unchanged = 0
    repaired = 0
    blocked = 0

    for feature in features:
        props = feature.get("properties") or {}
        section_id = str(props.get(section_id_field) or "").strip()
        if not section_id:
            raise ValueError("Entidad geométrica sin identificador oficial")
        if section_id in section_ids:
            raise ValueError(
                f"SECTION_ID_DUPLICATE_BEFORE_GEOMETRY_NORMALIZATION: {section_id}"
            )
        section_ids.append(section_id)
        raw_geometry = feature.get("geometry")
        if raw_geometry is None:
            audit = {
                "status": "BLOCKED",
                "before": {
                    "section_id": section_id,
                    "stage": source_stage,
                    "crs": str(crs),
                    "source_partition": (
                        str(props.get(coverage_field) or "")
                        if coverage_field else None
                    ),
                    "geometry_type": None,
                    "geometry_sha256": None,
                    "raw_geojson_sha256": None,
                    "component_count": 0,
                    "validity_reason": "GEOMETRY_NULL",
                },
                "method": None,
                "reason": "GEOMETRY_NULL",
                "libraries": geometry_runtime_versions(),
            }
            issues.append(audit)
            blocked += 1
            normalized.append(copy.deepcopy(feature))
            raw_geometries.append(None)
            derived_geometries.append(None)
            continue

        geometry = shape(raw_geometry)
        candidate, audit = normalize_official_geometry(
            section_id,
            geometry,
            source_crs=crs,
            policy=policy,
            raw_geojson=raw_geometry,
            stage=source_stage,
        )
        audit["before"]["source_partition"] = (
            str(props.get(coverage_field) or "")
            if coverage_field else None
        )
        if isinstance(audit.get("after"), dict):
            audit["after"]["source_partition"] = audit["before"][
                "source_partition"
            ]
        raw_geometries.append(geometry)
        derived_geometries.append(candidate)
        if audit["status"] == "UNCHANGED":
            valid_unchanged += 1
            normalized.append(copy.deepcopy(feature))
            continue

        issues.append(audit)
        if audit["status"] == "NORMALIZED":
            repaired += 1
            changed = copy.deepcopy(feature)
            changed["geometry"] = mapping(candidate)
            normalized.append(changed)
        else:
            blocked += 1
            normalized.append(copy.deepcopy(feature))

    derived_ids = [
        str((feature.get("properties") or {}).get(section_id_field) or "")
        for feature in normalized
    ]
    identity_equal = derived_ids == section_ids
    before_properties = _properties_digest(features, section_id_field)
    after_properties = _properties_digest(normalized, section_id_field)
    properties_equal = before_properties == after_properties

    coverage_before = None
    coverage_after = None
    if coverage_field:
        def coverage(rows: list[dict]) -> dict[str, int]:
            counts: dict[str, int] = {}
            for row in rows:
                key = str(
                    (row.get("properties") or {}).get(coverage_field) or ""
                )
                counts[key] = counts.get(key, 0) + 1
            return dict(sorted(counts.items()))
        coverage_before = coverage(features)
        coverage_after = coverage(normalized)

    population_fields = sorted({
        str(key)
        for feature in features
        for key in (feature.get("properties") or {})
        if (
            "pop" in str(key).lower()
            or str(key).lower() in {"total", "population", "poblacion"}
        )
    })

    changed_ids = {
        str(row["before"]["section_id"])
        for row in issues
        if row.get("status") == "NORMALIZED"
    }
    candidate_basic_valid = (
        blocked == 0
        and all(
            geometry is not None
            and not geometry.is_empty
            and geometry.geom_type in {"Polygon", "MultiPolygon"}
            and geometry.is_valid
            for geometry in derived_geometries
        )
    )
    topology: dict[str, Any] = {
        "metric_crs": metric_crs,
        "metric_units": {"length": "metre", "area": "square_metre"},
        "numeric_acceptance_tolerance": None,
        "invalid_raw_polygon_area_used_for_equivalence": False,
        "global_gap_validation": {
            "status": "LIMITED",
            "reason": (
                "No authoritative territory coverage mask is part of this source "
                "contract; pre-existing global gaps cannot be asserted here."
            ),
            "repair_induced_gap_evidence": (
                "accepted repairs must preserve the source boundary set and "
                "changed-section contacts exactly"
            ),
        },
    }
    if candidate_basic_valid:
        overlaps = _candidate_overlap_evidence(
            section_ids,
            derived_geometries,
            source_crs=crs,
            metric_crs=metric_crs,
        )
        contacts = _contact_evidence(
            section_ids,
            raw_geometries,
            derived_geometries,
            changed_ids,
        )
        gap_diagnostics = _candidate_gap_diagnostics(
            derived_geometries,
            source_crs=crs,
            metric_crs=metric_crs,
        )
        topology.update({
            "candidate_overlap_count": len(overlaps),
            "candidate_overlaps": overlaps,
            "candidate_gap_diagnostics": gap_diagnostics,
            "contacts": contacts,
            "components": [
                {
                    "section_id": section_id,
                    "before": _component_count(raw_geometries[index]),
                    "after": _component_count(derived_geometries[index]),
                }
                for index, section_id in enumerate(section_ids)
                if section_id in changed_ids
            ],
        })
    else:
        topology.update({
            "candidate_overlap_count": None,
            "candidate_overlaps": [],
            "candidate_gap_diagnostics": {
                "status": "NOT_EVALUATED_CANDIDATE_INVALID_OR_BLOCKED"
            },
            "contacts": {
                "status": "NOT_EVALUATED_CANDIDATE_INVALID_OR_BLOCKED"
            },
            "components": [],
        })

    topology_ready = (
        candidate_basic_valid
        and topology.get("candidate_overlap_count") == 0
        and topology.get("contacts", {}).get(
            "all_contact_id_sets_preserved", True
        )
        and topology.get("contacts", {}).get(
            "all_contact_geometries_preserved", True
        )
    )
    structural_ready = (
        identity_equal
        and properties_equal
        and coverage_before == coverage_after
    )
    decision = (
        "READY"
        if blocked == 0 and structural_ready and topology_ready
        else "BLOCKED"
    )

    report = {
        "schema": SCHEMA,
        "feature_count": len(features),
        "valid_unchanged": valid_unchanged,
        "invalid_observed": repaired + blocked,
        "normalized": repaired,
        "blocked": blocked,
        "decision": decision,
        "source_crs": str(crs),
        "source_stage": source_stage,
        "normalization_policy": {
            "schema": policy.get("schema"),
            "version": policy.get("version"),
            "path": policy_path,
            "sha256": policy_sha256,
            "allowed_methods": list(policy.get("allowed_methods") or []),
            "make_valid_used_only_with_independent_consensus": True,
            "numeric_acceptance_tolerance": None,
            "metric_values_are_diagnostic_not_pass_thresholds": True,
        },
        "identity_and_attributes": {
            "section_order_and_identity_equal": identity_equal,
            "section_count_before": len(features),
            "section_count_after": len(normalized),
            "properties_sha256_before": before_properties,
            "properties_sha256_after": after_properties,
            "properties_exact": properties_equal,
            "coverage_field": coverage_field,
            "coverage_before": coverage_before,
            "coverage_after": coverage_after,
            "coverage_exact": coverage_before == coverage_after,
            "population_fields_present": population_fields,
            "population": {
                "status": (
                    "PRESERVED_EXACTLY_AS_ATTRIBUTES"
                    if population_fields
                    else "NOT_PRESENT_IN_SECTION_SOURCE"
                ),
                "note": (
                    "La compatibilidad población-seccionado sigue validándose "
                    "por la puerta territorial existente."
                ),
            },
        },
        "geometry_set_sha256_before": _feature_geometry_digest(
            features, section_id_field
        ),
        "geometry_set_sha256_after": _feature_geometry_digest(
            normalized, section_id_field
        ),
        "topology": topology,
        "libraries": geometry_runtime_versions(),
        "issues": issues,
    }
    return normalized, report


def source_identity_from_records(records: list[dict]) -> dict:
    rows = [{
        "source_id": row.get("source_id"),
        "source_year": row.get("source_year"),
        "province_code": row.get("province_code") or row.get("province"),
        "url": row.get("url"),
        "path": row.get("path"),
        "sha256": row.get("sha256"),
        "bytes": row.get("bytes"),
    } for row in records]
    rows.sort(key=lambda row: (
        str(row.get("source_id")),
        str(row.get("source_year")),
        str(row.get("province_code")),
    ))
    return {
        "records": rows,
        "aggregate_manifest_sha256": _sha256_json(rows),
        "raw_preserved": bool(rows) and all(
            row.get("sha256") and row.get("path") for row in rows
        ),
    }


def persist_geometry_normalization_evidence(
    evidence_dir: Path,
    *,
    source_id: str,
    source_year: int,
    report: dict,
    raw_records: list[dict] | None = None,
    snapshot_identity: dict | None = None,
    derived_path: str | None = None,
    derived_payload: bytes | None = None,
    materialization_validation: dict | None = None,
) -> dict:
    evidence_dir = Path(evidence_dir).resolve()
    rel = (
        Path("geometry_normalization")
        / f"{source_id}_{int(source_year)}.json"
    )
    path = evidence_dir / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    source_identity = source_identity_from_records(raw_records or [])
    if snapshot_identity:
        source_identity["snapshot"] = snapshot_identity
        source_identity["raw_preserved"] = bool(
            snapshot_identity.get("sha256")
            or snapshot_identity.get("snapshot_sha256")
        )
    normalization_decision = str(report.get("decision") or "BLOCKED")
    if normalization_decision != "READY":
        overall_decision = "BLOCKED"
    elif materialization_validation is None:
        overall_decision = "PENDING_MATERIALIZATION"
    elif materialization_validation.get("decision") == "READY":
        overall_decision = "READY"
    else:
        overall_decision = "BLOCKED"

    document = {
        "schema": EVIDENCE_SCHEMA,
        "source_id": source_id,
        "source_year": int(source_year),
        "decision": overall_decision,
        "source_identity": source_identity,
        "normalization": report,
        "derived": None,
        "materialization_validation": materialization_validation,
    }
    if derived_payload is not None:
        document["derived"] = {
            "path": derived_path,
            "sha256": hashlib.sha256(derived_payload).hexdigest(),
            "bytes": len(derived_payload),
            "decision": overall_decision,
        }
    payload = (
        json.dumps(
            document,
            ensure_ascii=False,
            sort_keys=True,
            indent=2,
        )
        + "\n"
    )
    path.write_text(payload, encoding="utf-8")
    return {
        "path": rel.as_posix(),
        "sha256": hashlib.sha256(payload.encode("utf-8")).hexdigest(),
        "source_id": source_id,
        "source_year": int(source_year),
        "decision": overall_decision,
    }


def _normalized_property_value(value: Any) -> Any:
    try:
        import pandas as pd

        if pd.isna(value):
            return None
    except Exception:
        pass
    if value is None:
        return None
    if isinstance(value, bool):
        return bool(value)
    if isinstance(value, int):
        return int(value)
    if isinstance(value, float):
        return float(value)
    return str(value)


def validate_materialization_roundtrip(
    features: list[dict],
    materialized_gdf: Any,
    *,
    section_id_field: str,
    source_crs: str,
    source_partition_field: str | None = None,
) -> dict:
    from pyproj import CRS
    from shapely import is_valid_reason
    from shapely.geometry import shape

    if section_id_field not in materialized_gdf.columns:
        raise ValueError(
            f"GEOMETRY_POST_MATERIALIZATION_ID_MISSING: {section_id_field}"
        )
    actual_crs = getattr(materialized_gdf, "crs", None)
    if (
        actual_crs is None
        or not CRS.from_user_input(actual_crs).equals(
            CRS.from_user_input(source_crs)
        )
    ):
        raise ValueError(
            "GEOMETRY_POST_MATERIALIZATION_CRS_CHANGED: "
            f"{actual_crs!r} != {source_crs!r}"
        )

    expected_by_id: dict[str, dict] = {}
    for feature in features:
        props = feature.get("properties") or {}
        section_id = str(props.get(section_id_field) or "")
        if not section_id or section_id in expected_by_id:
            raise ValueError(
                "GEOMETRY_POST_MATERIALIZATION_SOURCE_ID_INVALID"
            )
        expected_by_id[section_id] = feature

    actual_by_id: dict[str, Any] = {}
    for _, row in materialized_gdf.iterrows():
        section_id = str(row[section_id_field])
        if not section_id or section_id in actual_by_id:
            raise ValueError("GEOMETRY_POST_MATERIALIZATION_ID_INVALID")
        actual_by_id[section_id] = row

    if set(expected_by_id) != set(actual_by_id):
        raise ValueError(
            "GEOMETRY_POST_MATERIALIZATION_IDENTITY_CHANGED: "
            f"before={len(expected_by_id)} after={len(actual_by_id)}"
        )

    defects: list[dict] = []
    changed_attributes: list[dict] = []
    for section_id in sorted(expected_by_id):
        feature = expected_by_id[section_id]
        props = feature.get("properties") or {}
        expected_geometry = shape(feature.get("geometry"))
        actual_geometry = actual_by_id[section_id].geometry
        source_partition = (
            str(props.get(source_partition_field) or "")
            if source_partition_field
            else None
        )
        before = {
            "section_id": section_id,
            "stage": "PRE_SHAPEFILE_WRITE",
            "crs": str(source_crs),
            "source_partition": source_partition,
            "geometry_type": expected_geometry.geom_type,
            "geometry_sha256": _sha256_geometry(expected_geometry),
            "validity_reason": str(is_valid_reason(expected_geometry)),
        }
        after = {
            "section_id": section_id,
            "stage": "POST_SHAPEFILE_WRITE_READBACK",
            "crs": str(actual_crs),
            "source_partition": source_partition,
            "geometry_type": (
                actual_geometry.geom_type
                if actual_geometry is not None else None
            ),
            "geometry_sha256": (
                _sha256_geometry(actual_geometry)
                if actual_geometry is not None else None
            ),
            "validity_reason": (
                str(is_valid_reason(actual_geometry))
                if actual_geometry is not None else "GEOMETRY_NULL"
            ),
        }

        reason = None
        if actual_geometry is None:
            reason = "GEOMETRY_POST_MATERIALIZATION_NULL"
        elif actual_geometry.is_empty:
            reason = "GEOMETRY_POST_MATERIALIZATION_EMPTY"
        elif actual_geometry.geom_type not in {"Polygon", "MultiPolygon"}:
            reason = "GEOMETRY_POST_MATERIALIZATION_NON_POLYGONAL"
        elif not actual_geometry.is_valid:
            reason = "GEOMETRY_POST_MATERIALIZATION_INVALID"
        elif not expected_geometry.equals(actual_geometry):
            reason = "GEOMETRY_POST_MATERIALIZATION_GEOMETRY_CHANGED"

        if reason is not None:
            defects.append({
                "section_id": section_id,
                "stage": "POST_SHAPEFILE_WRITE_READBACK",
                "source_partition": source_partition,
                "reason": reason,
                "before": before,
                "after": after,
            })

        expected_props = feature.get("properties") or {}
        for key, expected_value in expected_props.items():
            if key not in materialized_gdf.columns:
                changed_attributes.append({
                    "section_id": section_id,
                    "field": key,
                    "reason": "FIELD_MISSING",
                })
                continue
            actual_value = actual_by_id[section_id][key]
            before_value = _normalized_property_value(expected_value)
            after_value = _normalized_property_value(actual_value)
            if before_value != after_value:
                changed_attributes.append({
                    "section_id": section_id,
                    "field": key,
                    "before": before_value,
                    "after": after_value,
                })

    decision = "READY" if not defects and not changed_attributes else "BLOCKED"
    return {
        "decision": decision,
        "stage": "POST_SHAPEFILE_WRITE_READBACK",
        "section_count": len(expected_by_id),
        "section_identity_exact": True,
        "attributes_exact": not changed_attributes,
        "attribute_changes": changed_attributes,
        "geometry_topologically_equal": not defects,
        "defects": defects,
        "geometry_types": sorted(
            set(materialized_gdf.geometry.geom_type.astype(str))
        ),
        "empty_geometries": int(materialized_gdf.geometry.is_empty.sum()),
        "invalid_geometries": int(
            (~materialized_gdf.geometry.is_valid).sum()
        ),
        "crs_equivalent": True,
    }

