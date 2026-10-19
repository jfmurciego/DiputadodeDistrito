"""Read-only, bounded historical vector WMS probe at the official IGN endpoint.

The WMS LimitesTime layer supports TIME and GeoJSON GetMap, but a WMS response
does not prove full administrative coverage or legal effectiveness. A successful
probe is evidence of response bytes only; it must NEVER promote NAT-C-056.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from datetime import date, datetime, timezone
from pathlib import Path
from urllib.parse import urlencode, urlparse
from urllib.request import Request, urlopen

WMS_URL = "https://www.ign.es/wms-inspire/unidades-administrativas"
HISTORIC_TIME = "2025-01-01"
MAX_RESPONSE_BYTES = 12 * 1024 * 1024
MAX_BBOX_DEGREES = 1.0


def request_url(bbox: tuple[float, float, float, float], time: str = HISTORIC_TIME) -> str:
    if time != HISTORIC_TIME:
        raise ValueError("ONLY_APPROVED_HISTORICAL_REFERENCE_2025_01_01")
    if len(bbox) != 4 or not all(math.isfinite(float(v)) for v in bbox):
        raise ValueError("BBOX_INVALID")
    minx, miny, maxx, maxy = map(float, bbox)
    if (not (-20 <= minx < maxx <= 5 and 27 <= miny < maxy <= 44)
            or maxx - minx > MAX_BBOX_DEGREES
            or maxy - miny > MAX_BBOX_DEGREES):
        raise ValueError("BBOX_UNBOUNDED_OR_OUTSIDE_SPAIN")
    params = {
        "SERVICE": "WMS", "REQUEST": "GetMap", "VERSION": "1.3.0",
        "LAYERS": "LimitesTime", "STYLES": "", "CRS": "CRS:84",
        "BBOX": ",".join(format(float(x), ".9f") for x in bbox),
        "WIDTH": "600", "HEIGHT": "600",
        "FORMAT": "application/json;type=geojson",
        "TIME": time,
    }
    return WMS_URL + "?" + urlencode(params)


def inspect_historical_response(raw: bytes, source_url: str) -> dict:
    if not raw or len(raw) > MAX_RESPONSE_BYTES:
        raise ValueError("SOURCE_WMS_RESPONSE_SIZE_INVALID")
    try:
        document = json.loads(raw)
    except (UnicodeError, ValueError) as error:
        raise ValueError("SOURCE_WMS_GEOJSON_INVALID") from error
    if document.get("type") != "FeatureCollection" or not isinstance(document.get("features"), list):
        raise ValueError("SOURCE_WMS_NOT_FEATURE_COLLECTION")
    if len(document["features"]) > 50000:
        raise ValueError("SOURCE_WMS_UNBOUNDED_FEATURE_COUNT")
    identifiers = set()
    date_strings = set()
    for row in document["features"]:
        if not isinstance(row, dict) or row.get("type") != "Feature":
            raise ValueError("SOURCE_WMS_FEATURE_INVALID")
        properties = row.get("properties")
        if not isinstance(properties, dict):
            raise ValueError("SOURCE_WMS_PROPERTIES_REQUIRED")
        for field in ("nationalcode", "date_boundary", "endlifespanversion"):
            if not isinstance(properties.get(field), str) or not properties.get(field):
                raise ValueError("SOURCE_WMS_TEMPORAL_PROVENANCE_MISSING:" + field)
        ident = row.get("id")
        if not isinstance(ident, str) or not ident or ident in identifiers:
            raise ValueError("SOURCE_WMS_DUPLICATE_OR_INVALID_FEATURE_ID")
        identifiers.add(ident)
        if row.get("geometry", {}).get("type") not in ("LineString", "MultiLineString"):
            raise ValueError("SOURCE_WMS_BOUNDARY_GEOMETRY_REQUIRED")
        date_strings.add(properties["date_boundary"])
    return {
        "schema": "ddd.ign-2025-temporal-wms-probe/1.0",
        "official_url": source_url,
        "authority": "IGN/CNIG",
        "layer": "LimitesTime",
        "time_requested": HISTORIC_TIME,
        "downloaded_at": datetime.now(timezone.utc).isoformat(),
        "raw_sha256": hashlib.sha256(raw).hexdigest(),
        "raw_bytes": len(raw),
        "features_in_view": len(identifiers),
        "date_boundary_distinct_values": sorted(date_strings),
        "total_features_claim": document.get("totalFeatures"),
        "crs_query": "CRS:84",
        "zip_of_official_boundary_source": False,
        "complete_52_province_coverage_verified": False,
        "temporal_legal_coverage_verified": False,
        "municipality_code_crosswalk_verified": False,
        "eligible_for_NAT_C_056_accreditation": False,
        "generation_authorized": False,
        "status": "BOUNDED_OFFICIAL_VIEW_ONLY_NOT_ACREDITATION",
    }


def probe(bbox: tuple[float, float, float, float], fetcher=None) -> tuple[bytes, dict]:
    url = request_url(bbox)
    if fetcher is None:
        def fetcher(request: str) -> bytes:
            response = urlopen(Request(request, headers={"Accept": "application/json",
                                                         "User-Agent": "DDD-2026-historical-IGN-probe"}), timeout=35)
            with response:
                final = urlparse(response.geturl())
                if final.scheme != "https" or final.hostname != "www.ign.es":
                    raise ValueError("WMS_REDIRECT_TO_UNTRUSTED_ORIGIN")
                data = response.read(MAX_RESPONSE_BYTES + 1)
                if len(data) > MAX_RESPONSE_BYTES:
                    raise ValueError("SOURCE_WMS_RESPONSE_SIZE_INVALID")
                return data
    raw = fetcher(url)
    return raw, inspect_historical_response(raw, url)


def main() -> None:
    parser = argparse.ArgumentParser(description="Bounded official IGN GeoJSON sample, not accreditation")
    parser.add_argument("--bbox", type=float, nargs=4, required=True,
                        metavar=("MIN_LON", "MIN_LAT", "MAX_LON", "MAX_LAT"))
    parser.add_argument("--raw-output", type=Path, required=True)
    parser.add_argument("--receipt-output", type=Path, required=True)
    args = parser.parse_args()
    if args.raw_output.resolve() == args.receipt_output.resolve():
        raise ValueError("OUTPUT_PATHS_MUST_DIFFER")
    if args.raw_output.exists() or args.receipt_output.exists():
        raise FileExistsError("SOURCE_RECEIPT_OUTPUT_ALREADY_EXISTS")
    raw, receipt = probe(tuple(args.bbox))
    args.raw_output.parent.mkdir(parents=True, exist_ok=True)
    args.receipt_output.parent.mkdir(parents=True, exist_ok=True)
    with args.raw_output.open("xb") as fh:
        fh.write(raw)
    with args.receipt_output.open("x", encoding="utf-8") as fh:
        json.dump(receipt, fh, sort_keys=True, indent=2)
        fh.write("\n")
    print("IGN_2025_WMS_BOUNDED_PROBE_ONLY", receipt["raw_sha256"], receipt["features_in_view"])


if __name__ == "__main__":
    main()
