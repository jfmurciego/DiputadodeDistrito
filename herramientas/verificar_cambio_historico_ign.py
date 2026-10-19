"""Bounded, reproducible IGN historic boundary transition evidence (2025 vs 2026).

This compares two authentic HTTP GeoJSON responses for a known June 2025
administrative-boundary change. It never creates a national source receipt,
never infers administrative accreditation and never generates districts.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from urllib.error import URLError
from pathlib import Path
from urllib.parse import urlencode, urlparse
from urllib.request import Request, urlopen

BASE = "https://www.ign.es/wms-inspire/unidades-administrativas"
BBOX = "-0.45,39.16,-0.36,39.24"
BOUNDARY_ID = "M34104646029M34104646197T0246715"
START_OF_NEW_BOUNDARY = "2025-06-19"
DATES = ("2025-01-01", "2026-01-01")
MAX_BYTES = 5 * 1024 * 1024


def build_url(time: str) -> str:
    if time not in DATES:
        raise ValueError("TIME_NOT_APPROVED_FOR_DIAGNOSTIC")
    args = {"SERVICE": "WMS", "REQUEST": "GetMap", "VERSION": "1.3.0",
            "LAYERS": "LimitesTime", "STYLES": "", "CRS": "CRS:84",
            "BBOX": BBOX, "WIDTH": "650", "HEIGHT": "650",
            "FORMAT": "application/json;type=geojson", "TIME": time}
    return BASE + "?" + urlencode(args)


def inspect(raw: bytes, date_requested: str) -> dict:
    if not raw or len(raw) > MAX_BYTES:
        raise ValueError("WMS_RESPONSE_SIZE_INVALID")
    try:
        doc = json.loads(raw)
    except (UnicodeError, ValueError) as error:
        raise ValueError("WMS_INVALID_JSON") from error
    if doc.get("type") != "FeatureCollection" or not isinstance(doc.get("features"), list):
        raise ValueError("WMS_NOT_GEOJSON_FEATURE_COLLECTION")
    if len(doc["features"]) < 1 or len(doc["features"]) > 300:
        raise ValueError("WMS_FEATURE_COUNT_NOT_BOUNDED")
    seen = set()
    target = []
    for feature in doc["features"]:
        if not isinstance(feature, dict) or feature.get("type") != "Feature":
            raise ValueError("WMS_BAD_FEATURE")
        props = feature.get("properties")
        if not isinstance(props, dict):
            raise ValueError("WMS_MISSING_PROPERTIES")
        key = props.get("nationalcode")
        if not isinstance(key, str) or not key or key in seen:
            raise ValueError("WMS_DUPLICATE_OR_MISSING_CODE")
        seen.add(key)
        if feature.get("geometry", {}).get("type") not in ("LineString", "MultiLineString"):
            raise ValueError("WMS_BOUNDARY_GEOMETRY_MISSING")
        if key == BOUNDARY_ID:
            if str(props.get("date_boundary", ""))[:10] != START_OF_NEW_BOUNDARY:
                raise ValueError("EXPECTED_BOUNDARY_START_DATE_CHANGED")
            target.append(feature)
    return {"date": date_requested, "count": len(seen),
            "target_present": len(target) == 1,
            "target_count": len(target),
            "sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw)}


def fetch(url: str) -> bytes:
    req = Request(url, headers={"Accept": "application/json",
                                "User-Agent": "DDD-N08-temporal-source-diagnostic/1.0"})
    with urlopen(req, timeout=40) as response:
        origin = urlparse(response.geturl())
        if origin.scheme != "https" or origin.hostname != "www.ign.es":
            raise ValueError("IGN_SOURCE_REDIRECT_UNTRUSTED")
        data = response.read(MAX_BYTES + 1)
    if len(data) > MAX_BYTES:
        raise ValueError("IGN_SOURCE_RESPONSE_TOO_LARGE")
    return data


def compare(before: bytes, after: bytes) -> dict:
    old = inspect(before, DATES[0])
    new = inspect(after, DATES[1])
    if old["target_present"] or not new["target_present"]:
        raise ValueError("OFFICIAL_IGN_TEMPORAL_TRANSITION_NOT_REPRODUCED")
    return {
        "schema": "ddd.n08.ign-temporal-difference/1.0",
        "source_authority": "IGN/CNIG",
        "wms_layer": "LimitesTime",
        "bbox": BBOX,
        "boundary_id": BOUNDARY_ID,
        "change_effective_start": START_OF_NEW_BOUNDARY,
        "historical": old,
        "later": new,
        "target_excluded_at_2025_01_01": True,
        "target_included_at_2026_01_01": True,
        "obtained_at_utc": datetime.now(timezone.utc).isoformat(),
        "coverage_52_verified": False,
        "official_temporal_source_edition_accredited": False,
        "jurisdictional_legal_causation_accredited": False,
        "n08_discontinuities_resolved": False,
        "generation_authorized": False,
        "status": "OFFICIAL_BOUNDED_TEMPORAL_CHANGE_PROVEN_ONLY",
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--output-directory", type=Path, required=True)
    ap.add_argument("--record-network-unavailable", action="store_true",
                    help="Record independent network failure; do not assert source verification")
    args = ap.parse_args()
    directory = args.output_directory
    directory.mkdir(parents=True, exist_ok=True)
    outputs = [directory / "ign_algemesi_2025-01-01.geojson",
               directory / "ign_algemesi_2026-01-01.geojson",
               directory / "temporal_change_receipt.json"]
    if any(p.exists() for p in outputs):
        raise FileExistsError("NO_OVERWRITE_ORIGINAL_EVIDENCE")
    try:
        original = [fetch(build_url(value)) for value in DATES]
    except (TimeoutError, URLError, ConnectionError, OSError) as error:
        if not args.record_network_unavailable:
            raise
        # A network failure is evidence of no source, not a successful
        # comparison. Keep raw evidence empty and do not assert provenance.
        unavailable = {
            "schema": "ddd.n08.ign-temporal-source-unavailable/1.0",
            "status": "NETWORK_UNAVAILABLE_NO_TEMPORAL_EVIDENCE",
            "dates_requested": list(DATES),
            "source": BASE,
            "error_type": type(error).__name__,
            "complete_52_coverage_verified": False,
            "temporal_transition_proven_in_this_run": False,
            "generation_authorized": False,
        }
        with (directory / "network_unavailable.json").open("x", encoding="utf-8") as out:
            json.dump(unavailable, out, indent=2, sort_keys=True)
            out.write("\n")
        print("::warning::IGN did not answer this run; NO historical data or accreditation was obtained")
        print("IGN_SOURCE_UNAVAILABLE_NOT_A_SUCCESS")
        return
    receipt = compare(*original)
    for path, raw in zip(outputs[:2], original):
        with path.open("xb") as stream:
            stream.write(raw)
    with outputs[2].open("x", encoding="utf-8") as stream:
        json.dump(receipt, stream, ensure_ascii=False, sort_keys=True, indent=2)
        stream.write("\n")
    print("IGN_HISTORIC_TEMPORAL_TRANSITION_PASS " +
          json.dumps({k:receipt[k] for k in (
              "boundary_id","historical","later","coverage_52_verified",
              "generation_authorized")}, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
