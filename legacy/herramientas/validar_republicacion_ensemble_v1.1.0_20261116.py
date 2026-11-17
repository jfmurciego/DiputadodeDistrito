#!/usr/bin/env python3
"""Valida un ensemble republicado: 10 candidatos válidos y copias web en WGS84 sin confundirlas con las analíticas.

PROYECTO: Diputado de Distrito
VERSIÓN: 1.1.0 · FECHA: 2026-11-03 · ESTADO: candidato
ANTERIOR: legacy/herramientas/validar_republicacion_ensemble_v1.0.0_20261103.py
CAMBIOS 1.1.0 (T-37): la copia web lleva una feature por distrito (K), no por sección; se comprueba contra los distritos del candidato analítico y,
  si ya está en WGS84, contra su disolución (bounds y área por distrito).
QUÉ HACE: antes estaba incrustado en generar-alternativas-territoriales.yml y asumía candidatos analíticos proyectados (Aragón).
  Ahora cada candidato puede estar en coordenadas proyectadas (la web debe ser su transformación a WGS84 y distinta) o ya en
  grados (la web debe coincidir byte a byte con la analítica): en ambos casos se comprueba el emparejamiento por candidato.
MOTIVO: T-36, la republicación de Salamanca (run 41603638308) abortaba con «No se reconoce la copia analítica proyectada
  esperada»: sus candidatos ya vienen en WGS84 (T-31).
Salida: líneas clave=valor para GITHUB_OUTPUT.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ddd_ensemble.gallery import dissolve_by_district  # noqa: E402

WGS84_NAMES = ("CRS84", "EPSG::4326", "EPSG:4326", "4326")


def pairs(value):
    if isinstance(value, list):
        if len(value) >= 2 and all(isinstance(v, (int, float)) for v in value[:2]):
            yield value[0], value[1]
        else:
            for item in value:
                yield from pairs(item)


def coordinates(payload: dict):
    for feature in payload.get("features", []):
        yield from pairs((feature.get("geometry") or {}).get("coordinates"))


def is_projected(payload: dict) -> bool:
    return any(abs(x) > 180 or abs(y) > 90 for x, y in coordinates(payload))


def declares_non_wgs84(payload: dict) -> bool:
    name = str(((payload.get("crs") or {}).get("properties") or {}).get("name") or "")
    return bool(payload.get("crs")) and not any(token in name for token in WGS84_NAMES)


def validate(root: Path, expected: int = 10) -> dict:
    summary = json.loads((root / "analysis/summary.json").read_text(encoding="utf-8"))
    if not summary.get("complete") or summary.get("candidate_count_valid") != expected:
        raise SystemExit(f"Ensemble incompleto: {summary.get('candidate_count_valid')}/{expected}")
    assets = {p.stem: p for p in sorted((root / "site/assets").glob("*.geojson"))}
    analytical = {p.parent.name: p for p in sorted((root / "results").glob("*/candidate.geojson"))}
    if len(assets) != expected or len(analytical) != expected:
        raise SystemExit(f"Esperaba {expected} assets web y {expected} analíticos; hay {len(assets)} y {len(analytical)}")
    if set(assets) != set(analytical):
        raise SystemExit(f"Los assets web y los candidatos analíticos no se corresponden: {sorted(set(assets) ^ set(analytical))[:5]}")

    projected_candidates = 0
    for candidate, web_path in assets.items():
        web = json.loads(web_path.read_text(encoding="utf-8"))
        if declares_non_wgs84(web):
            raise SystemExit(f"{web_path}: la copia web conserva CRS proyectado")
        count = 0
        for lon, lat in coordinates(web):
            count += 1
            if not (-180 <= lon <= 180 and -90 <= lat <= 90):
                raise SystemExit(f"{web_path}: coordenada fuera de WGS84: {lon}, {lat}")
        if count == 0:
            raise SystemExit(f"{web_path}: sin coordenadas")
        source = analytical[candidate]
        source_data = json.loads(source.read_text(encoding="utf-8"))
        ids = [(f.get("properties") or {}).get("district_id") for f in source_data.get("features", [])]
        if any(i is None for i in ids):
            raise SystemExit(f"{candidate}: el candidato analítico tiene features sin district_id")
        districts = {str(i) for i in ids}
        web_ids = [str((f.get("properties") or {}).get("district_id")) for f in web.get("features", [])]
        if len(web_ids) != len(districts) or set(web_ids) != districts:
            raise SystemExit(
                f"{candidate}: la copia web tiene {len(web_ids)} features y el candidato {len(districts)} distritos; "
                "debe haber una por distrito."
            )
        if is_projected(source_data):
            projected_candidates += 1  # la web es su transformación a WGS84: ya comprobado que está en rango y sin crs proyectado
        else:
            expected_web = dissolve_by_district(source_data)
            by_id = {str((f.get("properties") or {}).get("district_id")): f for f in expected_web["features"]}
            from shapely.geometry import shape

            for feature in web["features"]:
                key = str((feature.get("properties") or {}).get("district_id"))
                a, b = shape(by_id[key]["geometry"]), shape(feature["geometry"])
                if max(abs(x - y) for x, y in zip(a.bounds, b.bounds)) > 1e-9 or abs(a.area - b.area) > 1e-9 * max(a.area, 1e-12):
                    raise SystemExit(
                        f"{candidate}: la copia web del distrito {key} no coincide con su analítica en WGS84; "
                        "se aborta para no confundir canónico y web."
                    )
    return {"complete": "true", "web_asset_count": expected, "analytical_projected": projected_candidates,
            "analytical_wgs84": expected - projected_candidates}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", type=Path, default=Path("work/ensemble"))
    ap.add_argument("--expected", type=int, default=10)
    args = ap.parse_args()
    for key, value in validate(args.root, args.expected).items():
        print(f"{key}={value}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
