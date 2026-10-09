#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PROYECTO: Diputado de Distrito
HERRAMIENTA: Auditoría C-01 de robustez frente a semilla
VERSIÓN: 1.0.0
NOMBRE DE VERSIÓN: Barrido M05 sobre baseline inmutable
FECHA: 2026-09-13
ESTADO: candidato C-01
QUÉ HACE: ejecuta M05 con 50-200 semillas sobre un M03/M04 ya certificado,
resume equilibrio y forma, sitúa la semilla publicada y elimina geometrías
intermedias.
REGLAS: no ejecuta M01-M04/M06-M08; no lee resultados electorales; no cambia
parámetros salvo la semilla efectiva y las rutas de salida M05.
ANTERIOR: ninguno — herramienta nueva.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
import statistics
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

import yaml


def load_geo(path: Path):
    import geopandas as gpd

    with zipfile.ZipFile(path) as archive:
        member = next(
            name
            for name in archive.namelist()
            if name.lower().endswith((".geojson", ".json")) and not name.endswith("/")
        )
        return gpd.read_file(io.BytesIO(archive.read(member)))


def percentile(values: list[float], observed: float) -> float:
    """Percentil empírico CDF con rango medio para empates."""
    below = sum(value < observed for value in values)
    equal = sum(math.isclose(value, observed, rel_tol=0, abs_tol=1e-12) for value in values)
    return 100.0 * (below + 0.5 * equal) / len(values)


def quantile(values: list[float], q: float) -> float:
    ordered = sorted(values)
    pos = (len(ordered) - 1) * q
    lo, hi = math.floor(pos), math.ceil(pos)
    if lo == hi:
        return ordered[lo]
    return ordered[lo] * (hi - pos) + ordered[hi] * (pos - lo)


def distribution(values: list[float]) -> dict[str, float]:
    return {
        "min": min(values),
        "p05": quantile(values, 0.05),
        "median": statistics.median(values),
        "mean": statistics.fmean(values),
        "p95": quantile(values, 0.95),
        "max": max(values),
        "stdev": statistics.pstdev(values),
    }


def seed_list(samples: int, canonical_seed: int) -> list[int]:
    if not 50 <= samples <= 200:
        raise ValueError("C-01 exige entre 50 y 200 semillas")
    return [canonical_seed, *(100_001 + index for index in range(samples - 1))]


def shape_metrics(gdf, district_field: str) -> dict[str, float | int]:
    projected = gdf.to_crs("EPSG:3035")
    districts = projected[[district_field, "geometry"]].dissolve(by=district_field)
    area = districts.geometry.area
    perimeter = districts.geometry.length
    pp = (4.0 * math.pi * area / perimeter.pow(2)).fillna(0.0)
    return {
        "pp_min": float(pp.min()),
        "pp_mean": float(pp.mean()),
        "pp_median": float(pp.median()),
        "pp_below_015": int((pp < 0.15).sum()),
        "pp_below_015_ratio": float((pp < 0.15).mean()),
    }


def assignment_hash(gdf, id_field: str, district_field: str) -> str:
    pairs = sorted(
        zip(gdf[id_field].astype(str), gdf[district_field].astype(int)),
        key=lambda item: item[0],
    )
    raw = "\n".join(f"{section},{district}" for section, district in pairs)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def decide(
    rows: list[dict], canonical: dict, expected_samples: int = 50
) -> tuple[str, list[str]]:
    reasons: list[str] = []
    success_ratio = len(rows) / expected_samples
    if success_ratio < 0.95:
        reasons.append("menos del 95 % de las semillas produjo solución técnica")
    for field in ("max_rel_dev", "pp_mean", "pp_min"):
        values = [float(row[field]) for row in rows]
        pct = percentile(values, float(canonical[field]))
        if pct < 5.0 or pct > 95.0:
            reasons.append(f"la semilla publicada es atípica en {field} (percentil {pct:.1f})")
    if float(canonical["max_rel_dev"]) > 0.12:
        reasons.append("la semilla publicada incumple tolerancia poblacional")
    if float(canonical["pp_min"]) < 0.05 or float(canonical["pp_below_015_ratio"]) > 0.30:
        reasons.append("la semilla publicada incumple la puerta provisional de forma")
    return ("PASS" if not reasons else "FAIL", reasons)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--params", required=True, type=Path)
    parser.add_argument("--graph", required=True, type=Path)
    parser.add_argument("--initial", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--samples", type=int, default=50)
    parser.add_argument("--canonical-seed", type=int, default=12345)
    args = parser.parse_args()

    seeds = seed_list(args.samples, args.canonical_seed)
    raw_cfg = yaml.safe_load(args.params.read_text(encoding="utf-8"))
    s5 = raw_cfg["modulos"]["modulo_05_optimizar_distritos"]
    id_field = str(s5["id_field"])
    district_field = str(s5.get("district_field", "district_id"))
    args.output_dir.mkdir(parents=True, exist_ok=True)
    rows: list[dict] = []
    failures: list[dict] = []

    with tempfile.TemporaryDirectory(prefix="ddd-c01-") as tmp_name:
        tmp = Path(tmp_name)
        for index, seed in enumerate(seeds, start=1):
            cfg = json.loads(json.dumps(raw_cfg))
            cfg_s5 = cfg["modulos"]["modulo_05_optimizar_distritos"]
            out_geo = tmp / f"seed-{seed}.geojson.zip"
            out_report = tmp / f"seed-{seed}.json"
            cfg_s5.update(
                {
                    "in_graph_json": str(args.graph.resolve()),
                    "in_geojson": str(args.initial.resolve()),
                    "out_geojson": str(out_geo),
                    "out_report": str(out_report),
                    "seed": seed,
                    "anneal_seed_offset": 0,
                }
            )
            cfg_path = tmp / f"params-{seed}.yaml"
            cfg_path.write_text(
                yaml.safe_dump(cfg, sort_keys=False, allow_unicode=True), encoding="utf-8"
            )
            result = subprocess.run(
                [sys.executable, "modulos/05_optimizar_distritos.py", "--params", str(cfg_path)],
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                check=False,
            )
            if result.returncode:
                failures.append(
                    {"seed": seed, "returncode": result.returncode, "output": result.stdout[-2000:]}
                )
                print(f"C-01 {index}/{len(seeds)} seed={seed} FAIL", flush=True)
                continue
            report = json.loads(out_report.read_text(encoding="utf-8"))
            gdf = load_geo(out_geo)
            row = {
                "seed": seed,
                "canonical": seed == args.canonical_seed,
                "max_rel_dev": float(report["best_max_rel_dev"]),
                "districts_outside_tolerance": int(report["districts_outside_tolerance"]),
                "accepted_moves": int(report["accepted_unit_moves"]),
                "assignment_sha256": assignment_hash(gdf, id_field, district_field),
                **shape_metrics(gdf, district_field),
            }
            rows.append(row)
            out_geo.unlink(missing_ok=True)
            out_report.unlink(missing_ok=True)
            print(
                f"C-01 {index}/{len(seeds)} seed={seed} "
                f"maxdev={row['max_rel_dev']:.6f} pp_mean={row['pp_mean']:.6f}",
                flush=True,
            )

    csv_path = args.output_dir / "C01_SEMILLAS.csv"
    if rows:
        with csv_path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)
    canonical = next((row for row in rows if row["canonical"]), None)
    metrics = ("max_rel_dev", "pp_mean", "pp_median", "pp_min", "pp_below_015_ratio")
    evidence = {
        "schema_version": "1.0.0",
        "audit_finding": "C-01",
        "scope": "Aragón; M05 sobre M03/M04 certificados; sin datos partidistas",
        "requested_samples": len(seeds),
        "successful_samples": len(rows),
        "failed_samples": len(failures),
        "canonical_seed": args.canonical_seed,
        "seeds": seeds,
        "unique_assignments": len({row["assignment_sha256"] for row in rows}),
        "distributions": {
            metric: distribution([float(row[metric]) for row in rows]) for metric in metrics
        } if rows else {},
        "canonical": canonical,
        "canonical_percentiles_cdf": {
            metric: percentile([float(row[metric]) for row in rows], float(canonical[metric]))
            for metric in metrics
        } if canonical else {},
        "failures": failures,
    }
    if canonical:
        evidence["decision"], evidence["decision_reasons"] = decide(
            rows, canonical, len(seeds)
        )
    else:
        evidence["decision"] = "FAIL"
        evidence["decision_reasons"] = ["la semilla publicada no produjo resultado"]
    (args.output_dir / "EVIDENCIA_C01.json").write_text(
        json.dumps(evidence, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    if evidence["decision"] != "PASS":
        raise SystemExit("C-01 FAIL: " + "; ".join(evidence["decision_reasons"]))


if __name__ == "__main__":
    main()
