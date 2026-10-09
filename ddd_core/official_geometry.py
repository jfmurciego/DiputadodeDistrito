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



def _bbox_candidate_pairs(*geometry_sets: list[Any]) -> list[tuple[int, int]]:
    """Unión determinista de parejas con bounding boxes coincidentes."""
    from shapely.strtree import STRtree

    pairs: set[tuple[int, int]] = set()
    for geometries in geometry_sets:
        kept = [
            (index, geometry)
            for index, geometry in enumerate(geometries)
            if geometry is not None and not geometry.is_empty
        ]
        if not kept:
            continue
        original_indexes = [row[0] for row in kept]
        compact = [row[1] for row in kept]
        tree = STRtree(compact)
        result = tree.query(compact)
        for left, right in zip(
            result[0].tolist(), result[1].tolist(), strict=False
        ):
            i = original_indexes[int(left)]
            j = original_indexes[int(right)]
            if i < j:
                pairs.add((i, j))
            elif j < i:
                pairs.add((j, i))
    return sorted(pairs)


def _safe_pair_relation(left: Any, right: Any, relation: str) -> tuple[Any | None, str | None]:
    try:
        if relation == "overlap":
            value = left.intersection(right)
            if value.is_empty or float(value.area) == 0.0:
                return None, None
            return value, None
        if relation == "contact":
            value = left.boundary.intersection(right.boundary)
            return (None if value.is_empty else value), None
        raise ValueError(f"Relación desconocida: {relation}")
    except Exception as exc:
        return None, f"{type(exc).__name__}: {exc}"


def _relation_observation(
    geometry: Any | None,
    *,
    relation: str,
    source_crs: str,
    metric_crs: str,
) -> dict | None:
    if geometry is None:
        return None
    metric = _metric_geometry(geometry, source_crs, metric_crs)
    row = {
        "geometry_type": geometry.geom_type,
        "geometry_sha256": _sha256_geometry(geometry),
    }
    if relation == "overlap":
        row["area_m2"] = float(metric.area)
    else:
        row["length_m"] = float(metric.length)
    return row


def _classify_spatial_change(
    before: Any | None,
    after: Any | None,
    *,
    relation: str,
) -> str:
    """Clasifica por geometría, nunca por conteos ni suma de áreas."""
    if before is None and after is None:
        return "PRESERVED_NONE"
    if before is None:
        return "NEW"
    if after is None:
        return "REMOVED"
    if before.equals(after):
        return "PRESERVED"
    if relation == "contact":
        return "DISPLACED_OR_RESHAPED"
    try:
        added = after.difference(before)
        removed = before.difference(after)
        added_empty = bool(added.is_empty)
        removed_empty = bool(removed.is_empty)
    except Exception:
        return "DISPLACED_OR_RESHAPED"
    if not added_empty and removed_empty:
        return "INCREASED"
    if added_empty and not removed_empty:
        return "DECREASED"
    return "DISPLACED_OR_RESHAPED"


def _baseline_variants(
    raw_geometry: Any,
    derived_geometry: Any,
    issue: dict | None,
) -> tuple[list[tuple[str, Any]], list[str]]:
    """Construye interpretaciones verificables del raw sólo cuando la prueba lo permite."""
    if not issue or issue.get("status") != "NORMALIZED":
        try:
            if raw_geometry.is_valid:
                return [("RAW_VALID", raw_geometry)], []
        except Exception:
            pass
        return [], ["RAW_INVALID_WITHOUT_NORMALIZATION_EVIDENCE"]

    method = str(issue.get("method") or "")
    proof = issue.get("proof") or {}
    if method in {
        "DEDUPLICATE_EXACT_MULTIPOLYGON_COMPONENTS",
        "DEDUPLICATE_EXACT_INTERIOR_RINGS",
    }:
        exact = (
            bool(proof.get("point_set_equal"))
            and bool(proof.get("boundary_set_equal"))
            and bool(proof.get("symmetric_difference_empty"))
        )
        if exact:
            return [("EXACT_POINT_SET_DERIVED", derived_geometry)], []
        return [], ["EXACT_DEDUPLICATION_PROOF_INCOMPLETE"]

    if method == "MAKE_VALID_DUAL_CONSENSUS_BOUNDARY_PRESERVING":
        verified = (
            bool(issue.get("independent_candidate_equal"))
            and bool(issue.get("source_boundary_set_equal"))
            and bool(issue.get("candidate_symmetric_difference_empty"))
        )
        if not verified:
            return [], ["DUAL_REPAIR_PROOF_INCOMPLETE"]
        try:
            from shapely import make_valid

            linework = make_valid(
                raw_geometry,
                method="linework",
                keep_collapsed=True,
            )
            structure = make_valid(
                raw_geometry,
                method="structure",
                keep_collapsed=False,
            )
            if (
                not _polygonal_only(linework)
                or not _polygonal_only(structure)
                or linework.is_empty
                or structure.is_empty
                or not linework.is_valid
                or not structure.is_valid
                or not linework.equals(structure)
                or not raw_geometry.boundary.equals(linework.boundary)
                or not linework.equals(derived_geometry)
            ):
                return [], ["DUAL_REPAIR_RECOMPUTATION_DIVERGED"]
            return [
                ("MAKE_VALID_LINEWORK", linework),
                ("MAKE_VALID_STRUCTURE", structure),
            ], []
        except Exception as exc:
            return [], [f"DUAL_REPAIR_RECOMPUTATION_FAILED: {type(exc).__name__}: {exc}"]

    return [], [f"UNSUPPORTED_NORMALIZATION_METHOD: {method or 'NONE'}"]


def _nullable_geometry_equal(left: Any | None, right: Any | None) -> bool:
    if left is None or right is None:
        return left is None and right is None
    try:
        return bool(left.equals(right))
    except Exception:
        return False


def _alternative_pair_baseline(
    raw_left: Any,
    raw_right: Any,
    derived_left: Any,
    derived_right: Any,
    left_issue: dict | None,
    right_issue: dict | None,
    *,
    relation: str,
) -> tuple[Any | None, dict]:
    """Acredita la relación de la pareja, no sólo la reparación de cada sección."""
    left_variants, left_errors = _baseline_variants(
        raw_left, derived_left, left_issue
    )
    right_variants, right_errors = _baseline_variants(
        raw_right, derived_right, right_issue
    )
    errors = [*left_errors, *right_errors]
    if errors or not left_variants or not right_variants:
        return None, {
            "status": "NOT_AVAILABLE",
            "relation": relation,
            "errors": errors or ["PAIR_VARIANTS_EMPTY"],
        }

    observations: list[tuple[str, str, Any | None]] = []
    for left_name, left_geometry in left_variants:
        for right_name, right_geometry in right_variants:
            value, error = _safe_pair_relation(
                left_geometry,
                right_geometry,
                relation,
            )
            if error:
                return None, {
                    "status": "NOT_AVAILABLE",
                    "relation": relation,
                    "errors": [
                        f"{left_name}/{right_name}: {error}"
                    ],
                }
            observations.append((left_name, right_name, value))

    canonical = observations[0][2]
    if not all(
        _nullable_geometry_equal(canonical, value)
        for _, _, value in observations[1:]
    ):
        return None, {
            "status": "NOT_AVAILABLE",
            "relation": relation,
            "errors": ["INDEPENDENT_PAIR_RELATIONS_DISAGREE"],
            "variants": [
                {"left": left, "right": right}
                for left, right, _ in observations
            ],
        }

    after, after_error = _safe_pair_relation(
        derived_left,
        derived_right,
        relation,
    )
    if after_error or not _nullable_geometry_equal(canonical, after):
        return None, {
            "status": "NOT_AVAILABLE",
            "relation": relation,
            "errors": [
                (
                    f"DERIVED_RELATION_ERROR: {after_error}"
                    if after_error
                    else "ALTERNATIVE_BASELINE_DIFFERS_FROM_DERIVED_RELATION"
                )
            ],
        }

    return canonical, {
        "status": "AVAILABLE",
        "relation": relation,
        "proof": "PAIR_RELATION_RECOMPUTED_FROM_VERIFIED_INDEPENDENT_VARIANTS",
        "left_variants": [name for name, _ in left_variants],
        "right_variants": [name for name, _ in right_variants],
        "variant_pair_count": len(observations),
        "all_variant_relations_equal": True,
        "matches_derived_relation": True,
        "note": (
            "The failed raw operation is not replaced by zero or by the "
            "derived result by assumption. The pair relation is independently "
            "recomputed from every repair interpretation already accredited "
            "by the normalization policy and all interpretations must agree."
        ),
    }



def _pairwise_topology_evidence(
    section_ids: list[str],
    raw_geometries: list[Any],
    derived_geometries: list[Any],
    issues: list[dict],
    *,
    source_crs: str,
    metric_crs: str,
) -> dict:
    issues_by_id = {
        str((row.get("before") or {}).get("section_id") or ""): row
        for row in issues
        if isinstance(row, dict)
    }
    overlap_rows: list[dict] = []
    contact_rows: list[dict] = []
    limitations: list[dict] = []
    overlap_changes: list[dict] = []
    contact_changes: list[dict] = []

    for i, j in _bbox_candidate_pairs(raw_geometries, derived_geometries):
        pair = (section_ids[i], section_ids[j])
        for relation, output, changes in (
            ("overlap", overlap_rows, overlap_changes),
            ("contact", contact_rows, contact_changes),
        ):
            raw_geometry = raw_geometries[i]
            other_raw = raw_geometries[j]
            derived_geometry = derived_geometries[i]
            other_derived = derived_geometries[j]
            if (
                raw_geometry is None
                or other_raw is None
                or derived_geometry is None
                or other_derived is None
            ):
                continue

            try:
                raw_pair_valid = bool(
                    raw_geometry.is_valid and other_raw.is_valid
                )
            except Exception:
                raw_pair_valid = False
            if raw_pair_valid:
                before, before_error = _safe_pair_relation(
                    raw_geometry, other_raw, relation
                )
            else:
                before = None
                before_error = (
                    "RAW_GEOMETRY_INVALID_PAIR_BASELINE_REQUIRES_"
                    "ALTERNATIVE_EVIDENCE"
                )
            after, after_error = _safe_pair_relation(
                derived_geometry, other_derived, relation
            )
            alternative = None
            baseline_method = "RAW_PAIR_OPERATION"
            unresolved = False
            if before_error:
                before, alternative = _alternative_pair_baseline(
                    raw_geometry,
                    other_raw,
                    derived_geometry,
                    other_derived,
                    issues_by_id.get(pair[0]),
                    issues_by_id.get(pair[1]),
                    relation=relation,
                )
                if alternative["status"] == "AVAILABLE" and after_error is None:
                    baseline_method = "ALTERNATIVE_PAIR_EVIDENCE"
                else:
                    unresolved = True
                    baseline_method = "NOT_EVALUABLE"
            if after_error:
                unresolved = True

            classification = (
                "BASELINE_NOT_EVALUABLE"
                if unresolved
                else _classify_spatial_change(
                    before, after, relation=relation
                )
            )
            before_observation = _relation_observation(
                before,
                relation=relation,
                source_crs=source_crs,
                metric_crs=metric_crs,
            )
            after_observation = _relation_observation(
                after,
                relation=relation,
                source_crs=source_crs,
                metric_crs=metric_crs,
            )
            # Persistimos únicamente parejas con relación, cambio o limitación.
            if (
                before_observation is None
                and after_observation is None
                and not before_error
                and not after_error
            ):
                continue
            row = {
                "section_a": pair[0],
                "section_b": pair[1],
                "classification": classification,
                "baseline_method": baseline_method,
                "before": before_observation,
                "after": after_observation,
            }
            if alternative is not None:
                row["alternative_baseline_evidence"] = alternative
            if before_error:
                row["before_error"] = before_error
            if after_error:
                row["after_error"] = after_error
            output.append(row)

            if unresolved:
                limitations.append({
                    "section_a": pair[0],
                    "section_b": pair[1],
                    "relation": relation,
                    "reason": "PAIR_BASELINE_NOT_EVALUABLE",
                    "before_error": before_error,
                    "after_error": after_error,
                    "alternative_baseline_evidence": alternative,
                })
            elif classification not in {
                "PRESERVED_NONE",
                "PRESERVED",
            }:
                changes.append({
                    "section_a": pair[0],
                    "section_b": pair[1],
                    "classification": classification,
                    "before": before_observation,
                    "after": after_observation,
                })

    return {
        "comparison": "PAIRWISE_EXACT_GEOMETRY",
        "metric_crs": metric_crs,
        "numeric_acceptance_tolerance": None,
        "overlaps": sorted(
            overlap_rows,
            key=lambda row: (row["section_a"], row["section_b"]),
        ),
        "contacts": sorted(
            contact_rows,
            key=lambda row: (row["section_a"], row["section_b"]),
        ),
        "overlap_changes": sorted(
            overlap_changes,
            key=lambda row: (row["section_a"], row["section_b"]),
        ),
        "contact_changes": sorted(
            contact_changes,
            key=lambda row: (row["section_a"], row["section_b"]),
        ),
        "baseline_limitations": limitations,
        "overlap_change_count": len(overlap_changes),
        "contact_change_count": len(contact_changes),
        "unresolved_baseline_count": len(limitations),
    }


def _coverage_preservation_evidence(
    issues: list[dict],
    *,
    geometry_digest_equal: bool,
) -> dict:
    normalized = [row for row in issues if row.get("status") == "NORMALIZED"]
    if not normalized:
        return {
            "decision": "READY" if geometry_digest_equal else "BLOCKED",
            "method": "EXACT_DATASET_GEOMETRY_IDENTITY",
            "geometry_digest_equal": geometry_digest_equal,
            "sections": [],
        }

    evidence: list[dict] = []
    safe = True
    for issue in normalized:
        method = str(issue.get("method") or "")
        proof = issue.get("proof") or {}
        if method in {
            "DEDUPLICATE_EXACT_MULTIPOLYGON_COMPONENTS",
            "DEDUPLICATE_EXACT_INTERIOR_RINGS",
        }:
            ok = bool(proof.get("point_set_equal")) and bool(
                proof.get("boundary_set_equal")
            )
            kind = "EXACT_POINT_AND_BOUNDARY_SET_PROOF"
        elif method == "MAKE_VALID_DUAL_CONSENSUS_BOUNDARY_PRESERVING":
            ok = (
                bool(issue.get("independent_candidate_equal"))
                and bool(issue.get("source_boundary_set_equal"))
                and bool(issue.get("candidate_symmetric_difference_empty"))
            )
            kind = "DUAL_REPAIR_CONSENSUS_WITH_EXACT_SOURCE_BOUNDARY"
        else:
            ok = False
            kind = "UNSUPPORTED"
        safe = safe and ok
        evidence.append({
            "section_id": str((issue.get("before") or {}).get("section_id") or ""),
            "method": method,
            "evidence": kind,
            "verified": ok,
        })
    return {
        "decision": "READY" if safe else "BLOCKED",
        "method": "PER_SECTION_EXACT_OR_INDEPENDENT_ALTERNATIVE_EVIDENCE",
        "geometry_digest_equal": geometry_digest_equal,
        "sections": evidence,
        "note": (
            "Invalid raw polygon area is never used as equivalence evidence."
        ),
    }


def _source_admissibility(
    pairwise: dict,
    *,
    declared_use: dict | None,
    section_ids: list[str] | None = None,
    derived_geometries: list[Any] | None = None,
    source_crs: str | None = None,
) -> dict:
    if not declared_use:
        return {
            "decision": "NOT_EVALUATED",
            "allows_staging": False,
            "reason": (
                "No declared consumer contract was supplied. Normalization "
                "safety may be READY, but source admissibility is fail-closed."
            ),
        }

    role = str(declared_use.get("role") or "")
    consumer = str(declared_use.get("consumer") or "")
    topology_changes = (
        int(pairwise.get("overlap_change_count") or 0)
        + int(pairwise.get("contact_change_count") or 0)
        + int(pairwise.get("unresolved_baseline_count") or 0)
    )
    if topology_changes:
        return {
            "decision": "BLOCKED",
            "allows_staging": False,
            "role": role,
            "consumer": consumer,
            "declared_use": declared_use,
            "reason": "Normalization changed topology or left an unevaluable baseline.",
            "adjacency_impact": {
                "normalization_pair_changes": topology_changes,
                "decision": "BLOCKED",
            },
        }

    if role == "population_sectioning_origin":
        return {
            "decision": "DEFERRED_TO_CONSUMER_GATE",
            "allows_staging": True,
            "role": role,
            "consumer": consumer or "population_sectioning_compatibility",
            "required_evidence": (
                "compatibilidad_poblacion_seccionado.json geometry_admissibility "
                "decision READY"
            ),
            "original_overlap_pairs": [
                {
                    "section_a": row["section_a"],
                    "section_b": row["section_b"],
                    "relation_geometry_sha256": (
                        (row.get("after") or {}).get("geometry_sha256")
                    ),
                }
                for row in (pairwise.get("overlaps") or [])
                if row.get("after") is not None
                and row.get("classification") == "PRESERVED"
            ],
            "reason": (
                "Origin section geometry is consumed jointly with target "
                "sectioning and population. Staging is allowed only so the "
                "mandatory compatibility gate can bind every original defect "
                "to an exact one-to-one destination and to an admissible target "
                "relation; provenance or invariance alone is insufficient."
            ),
        }

    if role != "target_sectioning":
        return {
            "decision": "BLOCKED",
            "allows_staging": False,
            "role": role,
            "consumer": consumer,
            "reason": "Unsupported or missing declared geometry source role.",
        }

    original_overlaps = [
        row for row in pairwise.get("overlaps") or []
        if row.get("after") is not None
        and row.get("classification") == "PRESERVED"
    ]
    if not original_overlaps:
        return {
            "decision": "READY",
            "allows_staging": True,
            "role": role,
            "consumer": consumer,
            "declared_use": declared_use,
            "original_overlap_pairs": [],
            "inadmissible_overlap_pairs": [],
            "adjacency_impact": {
                "normalization_pair_changes": 0,
                "decision": "READY",
            },
            "coverage_impact": {
                "assessment": "NO_ORIGINAL_OVERLAP_DEFECT",
                "global_gap_mask": "NOT_AVAILABLE",
            },
            "threshold_origin": None,
        }

    adjacency = declared_use.get("adjacency") or {}
    predicate = str(adjacency.get("predicate") or "")
    working_crs = str(adjacency.get("working_crs") or "")
    min_shared = adjacency.get("min_shared_border_m")
    max_overlap = adjacency.get("max_precision_overlap_area_m2")
    if not predicate or min_shared is None or not working_crs:
        return {
            "decision": "BLOCKED",
            "allows_staging": False,
            "role": role,
            "consumer": consumer,
            "reason": (
                "Declared target-sectioning consumer contract is incomplete "
                "for assessing an original overlap defect."
            ),
            "declared_use": declared_use,
        }
    if (
        not section_ids
        or not derived_geometries
        or source_crs is None
        or len(section_ids) != len(derived_geometries)
    ):
        return {
            "decision": "BLOCKED",
            "allows_staging": False,
            "role": role,
            "consumer": consumer,
            "reason": "Geometry context missing for consumer-CRS defect assessment.",
        }

    index_by_id = {
        str(section_id): index
        for index, section_id in enumerate(section_ids)
    }
    violations: list[dict] = []
    assessed: list[dict] = []
    for row in original_overlaps:
        section_a = str(row["section_a"])
        section_b = str(row["section_b"])
        if section_a not in index_by_id or section_b not in index_by_id:
            violations.append({
                "section_a": section_a,
                "section_b": section_b,
                "reason": "PAIR_GEOMETRY_NOT_FOUND",
                "admissible": False,
            })
            continue
        left = derived_geometries[index_by_id[section_a]]
        right = derived_geometries[index_by_id[section_b]]
        try:
            left_metric = _metric_geometry(
                left,
                str(source_crs),
                working_crs,
            )
            right_metric = _metric_geometry(
                right,
                str(source_crs),
                working_crs,
            )
            overlap_metric = left_metric.intersection(right_metric)
            boundary_metric = left_metric.boundary.intersection(
                right_metric.boundary
            )
            area = float(overlap_metric.area)
            shared = float(boundary_metric.length)
        except Exception as exc:
            violations.append({
                "section_a": section_a,
                "section_b": section_b,
                "reason": (
                    f"CONSUMER_CRS_MEASUREMENT_FAILED: "
                    f"{type(exc).__name__}: {exc}"
                ),
                "admissible": False,
            })
            continue

        pair = {
            "section_a": section_a,
            "section_b": section_b,
            "overlap_area_m2": area,
            "shared_boundary_m": shared,
            "measurement_crs": working_crs,
        }
        if predicate == "contact" and max_overlap is not None:
            precision_admissible = area <= float(max_overlap)
            would_form_edge = bool(
                shared >= float(min_shared)
                and (bool(left_metric.touches(right_metric)) or precision_admissible)
            )
            admissible = precision_admissible
            pair.update({
                "consumer_rule": (
                    "pre-existing overlap <= "
                    "max_precision_overlap_area_m2; M02 edge effect recorded "
                    "separately using its full contact predicate"
                ),
                "declared_min_shared_border_m": float(min_shared),
                "declared_max_precision_overlap_area_m2": float(max_overlap),
                "would_form_m02_edge": would_form_edge,
                "adjacency_effect": (
                    "GEOMETRIC_EDGE"
                    if would_form_edge
                    else "NO_EDGE_UNDER_DECLARED_CONSUMER"
                ),
                "admissible": admissible,
            })
        else:
            admissible = False
            pair.update({
                "consumer_rule": (
                    "overlap_not_declared_admissible_for_this_predicate"
                ),
                "admissible": False,
            })
        assessed.append(pair)
        if not admissible:
            violations.append(pair)

    ready = not violations
    return {
        "decision": "READY" if ready else "BLOCKED",
        "allows_staging": ready,
        "role": role,
        "consumer": consumer,
        "declared_use": declared_use,
        "original_overlap_pairs": assessed,
        "inadmissible_overlap_pairs": violations,
        "adjacency_impact": {
            "normalization_pair_changes": 0,
            "decision": "READY",
            "assessment": "EXISTING_M02_RELATION_RULE_REPLAYED_PER_PAIR",
        },
        "coverage_impact": {
            "assessment": (
                "PAIRWISE_AGAINST_DECLARED_CONSUMER_PRECISION_RULE"
                if predicate == "contact" and max_overlap is not None
                else "NO_OVERLAP_ALLOWANCE_DECLARED"
            ),
            "global_gap_mask": "NOT_AVAILABLE",
            "note": (
                "No sum of overlap areas is used for acceptance; every pair is "
                "recomputed in the consumer working CRS. The existing "
                "precision-overlap ceiling governs coverage admissibility, "
                "while the full M02 predicate is replayed and recorded as the "
                "pair's adjacency effect."
            ),
        },
        "threshold_origin": (
            "Existing territorial adjacency contract; not a normalization tolerance."
        ),
    }



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
    declared_use: dict | None = None,
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
    before_geometry_digest = _feature_geometry_digest(
        features, section_id_field
    )
    after_geometry_digest = _feature_geometry_digest(
        normalized, section_id_field
    )
    coverage_preservation = _coverage_preservation_evidence(
        issues,
        geometry_digest_equal=(
            before_geometry_digest == after_geometry_digest
        ),
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
                "pairwise overlap/contact comparison plus exact or independent "
                "per-section coverage evidence"
            ),
        },
    }
    if candidate_basic_valid:
        pairwise = _pairwise_topology_evidence(
            section_ids,
            raw_geometries,
            derived_geometries,
            issues,
            source_crs=crs,
            metric_crs=metric_crs,
        )
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
            "pairwise": pairwise,
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
        pairwise = {
            "comparison": "NOT_EVALUATED_CANDIDATE_INVALID_OR_BLOCKED",
            "overlaps": [],
            "contacts": [],
            "overlap_changes": [],
            "contact_changes": [],
            "baseline_limitations": [],
            "overlap_change_count": 0,
            "contact_change_count": 0,
            "unresolved_baseline_count": 0,
        }
        topology.update({
            "candidate_overlap_count": None,
            "candidate_overlaps": [],
            "pairwise": pairwise,
            "candidate_gap_diagnostics": {
                "status": "NOT_EVALUATED_CANDIDATE_INVALID_OR_BLOCKED"
            },
            "contacts": {
                "status": "NOT_EVALUATED_CANDIDATE_INVALID_OR_BLOCKED"
            },
            "components": [],
        })

    structural_ready = (
        identity_equal
        and properties_equal
        and coverage_before == coverage_after
    )
    topology_preserved = (
        candidate_basic_valid
        and int(pairwise.get("overlap_change_count") or 0) == 0
        and int(pairwise.get("contact_change_count") or 0) == 0
        and int(pairwise.get("unresolved_baseline_count") or 0) == 0
    )
    normalization_safety_ready = (
        blocked == 0
        and structural_ready
        and topology_preserved
        and coverage_preservation.get("decision") == "READY"
    )
    normalization_safety = {
        "decision": "READY" if normalization_safety_ready else "BLOCKED",
        "identity_preserved": identity_equal,
        "attributes_preserved": properties_equal,
        "declared_coverage_preserved": coverage_before == coverage_after,
        "coverage_evidence": coverage_preservation,
        "pairwise_topology_preserved": topology_preserved,
        "overlap_change_count": int(
            pairwise.get("overlap_change_count") or 0
        ),
        "contact_change_count": int(
            pairwise.get("contact_change_count") or 0
        ),
        "unresolved_baseline_count": int(
            pairwise.get("unresolved_baseline_count") or 0
        ),
    }

    source_admissibility = _source_admissibility(
        pairwise,
        declared_use=declared_use,
        section_ids=section_ids,
        derived_geometries=derived_geometries,
        source_crs=str(crs),
    )
    source_allows_stage = bool(
        source_admissibility.get("allows_staging", False)
    )
    decision = (
        "READY"
        if normalization_safety_ready and source_allows_stage
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
        "declared_use": declared_use,
        "normalization_safety": normalization_safety,
        "source_admissibility": source_admissibility,
        "normalization_policy": {
            "schema": policy.get("schema"),
            "version": policy.get("version"),
            "path": policy_path,
            "sha256": policy_sha256,
            "allowed_methods": list(policy.get("allowed_methods") or []),
            "make_valid_used_only_with_independent_consensus": True,
            "numeric_acceptance_tolerance": None,
            "metric_values_are_diagnostic_not_pass_thresholds": True,
            "preexisting_source_defects_are_not_normalization_failures": True,
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
        "geometry_set_sha256_before": before_geometry_digest,
        "geometry_set_sha256_after": after_geometry_digest,
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

