#!/usr/bin/env python3
"""Diagnóstico de distritos fuera de límites de población tras un fallo de M04/M05.

PROYECTO: Diputado de Distrito
VERSIÓN: 1.0.0 · FECHA: 2026-10-29 · ESTADO: candidato
QUÉ HACE: localiza la última salida de M05 (o, si no existe, de M04) en la caché del territorio,
  calcula la población de cada distrito frente al suelo y el techo del contrato y emite, para cada
  distrito que los incumple, su componente (provincia o isla), población, ratio y municipios.
  Escribe un JSON y una anotación ::warning:: por distrito, legible sin descargar artefactos.
MOTIVO: Andalucía, País Vasco, Canarias, Baleares y Cataluña fallan en M05 con
  NO_FEASIBLE_REPAIR_FOUND y el log sólo da el número de distritos imposibles, no cuáles son.
ANTERIOR: ninguno (herramienta nueva).
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _latest(cache: Path, patterns: tuple[str, ...]) -> Path | None:
    found = [p for pattern in patterns for p in cache.rglob(pattern) if p.is_file()]
    return max(found, key=lambda p: p.stat().st_mtime) if found else None


def diagnose(params: Path) -> dict:
    import geopandas as gpd
    from ddd_core.config import load_params_yaml

    cfg = load_params_yaml(str(params))
    m05 = (cfg.get("modulos") or {}).get("modulo_05_optimizar_distritos") or {}
    validation = cfg.get("validation") or {}
    k = int((cfg.get("territory_contract") or {})["k_districts"])
    cache = Path(str(m05.get("in_geojson") or "")).parent
    stage, source = "M05", _latest(cache, ("*m05_distritos_optimizados*.geojson*",))
    if source is None:
        stage, source = "M04", _latest(cache, ("*m04_semillas*.geojson*",))
    if source is None:
        return {"status": "NO_OUTPUT", "cache": str(cache)}
    gdf = gpd.read_file(source)
    pop_field = str(m05.get("pop_field") or "POP")
    district_field = str(m05.get("district_field") or "district_id")
    part_field = str(m05.get("province_field") or "CPRO")
    mun_field = str(m05.get("municipality_field") or "CUMUN")
    total = float(gdf[pop_field].sum())
    target = total / k
    floor = target * float(validation.get("population_floor_ratio", 0.8))
    cap = target * float(validation.get("population_cap_ratio", 1.75))
    exempt = {str(x) for x in validation.get("population_floor_exempt_partitions") or []}
    rows = []
    for district, grp in gdf.groupby(district_field):
        pop = float(grp[pop_field].sum())
        part = str(grp[part_field].mode().iloc[0]) if part_field in grp else ""
        below = pop < floor - 1e-9 and part not in exempt
        if below or pop > cap + 1e-9:
            munis = sorted({str(m) for m in grp[mun_field]}) if mun_field in grp else []
            rows.append({
                "district": str(district), "partition": part, "population": int(round(pop)),
                "ratio_to_target": round(pop / target, 4), "violation": "BELOW_FLOOR" if below else "ABOVE_CAP",
                "sections": int(len(grp)), "municipalities": munis[:12],
            })
    return {
        "status": "OK", "stage": stage, "source": str(source), "k": k,
        "target": round(target, 1), "floor": round(floor, 1), "cap": round(cap, 1),
        "floor_exempt_partitions": sorted(exempt), "violations": rows,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--params", required=True, type=Path)
    ap.add_argument("--output", required=True, type=Path)
    args = ap.parse_args()
    try:
        report = diagnose(args.params)
    except Exception as exc:  # diagnóstico best-effort: nunca oculta el fallo original
        report = {"status": "ERROR", "error": f"{type(exc).__name__}: {exc}"}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    head = {k: report.get(k) for k in ("status", "stage", "k", "target", "floor", "cap", "floor_exempt_partitions")}
    print(f"::warning::DIAG_POBLACION {json.dumps(head, ensure_ascii=False)}")
    for row in (report.get("violations") or [])[:20]:
        print(f"::warning::DIAG_DISTRITO {json.dumps(row, ensure_ascii=False)}")
    if report.get("status") == "ERROR":
        print(f"::warning::DIAG_ERROR {report['error']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
