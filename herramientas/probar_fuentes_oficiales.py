#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Prueba aislada de fuentes oficiales: sondeo mínimo o ciclo completo ACQUIRE/REUSE/BLOCK."""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import time
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit
from urllib.request import Request, urlopen

import yaml

from herramientas.adquirir_fuentes_oficiales import _source_urls
from herramientas.resolver_fuentes_territorio import build_declaration

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "fuentes/catalogo_oficial.yaml"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def file_state(paths: list[Path]) -> dict:
    out = {}
    for p in paths:
        out[str(p)] = {
            "exists": p.is_file(),
            "bytes": p.stat().st_size if p.is_file() else None,
            "sha256": sha256_file(p) if p.is_file() else None,
        }
    return out


def _request(url: str, timeout: int):
    return urlopen(Request(url, headers={"User-Agent": "DiputadoDeDistrito-source-test/1.0"}), timeout=timeout)


def _with_limit(url: str, limit: int) -> str:
    parts = urlsplit(url)
    q = dict(parse_qsl(parts.query, keep_blank_values=True))
    q["limit"] = str(limit)
    return urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(q), parts.fragment))


def probe_static_csv(source: dict, *, timeout: int, sample_size: int) -> dict:
    url = str(source["url"])
    started = time.monotonic()
    with _request(url, timeout) as response:
        status = getattr(response, "status", 200)
        lines = []
        for _ in range(sample_size + 1):
            line = response.readline()
            if not line:
                break
            lines.append(line)
    raw = b"".join(lines)
    low = raw[:2048].lstrip().lower()
    if status >= 400:
        raise RuntimeError(f"HTTP {status}")
    if low.startswith(b"<html") or low.startswith(b"<!doctype html"):
        raise RuntimeError("La fuente devolvió HTML")
    if len(lines) < 2:
        raise RuntimeError("La fuente no entregó cabecera y datos")
    header = lines[0].decode("utf-8-sig", errors="replace").strip()
    return {
        "source_id": source["id"],
        "kind": source["kind"],
        "url": url,
        "status": "PASS",
        "http_status": status,
        "sample_records": max(0, len(lines) - 1),
        "sample_bytes": len(raw),
        "header": header,
        "elapsed_seconds": round(time.monotonic() - started, 3),
    }


def probe_ogc(source: dict, declaration: dict, *, timeout: int, sample_size: int) -> dict:
    territory = declaration["territory"]
    provinces = territory["territorial_codes"]
    edition = int(territory["edition"])
    urls = [_with_limit(u, sample_size) for u in _source_urls(source, edition, provinces)]
    checks = []
    started = time.monotonic()
    for province, url in zip(provinces, urls):
        with _request(url, timeout) as response:
            status = getattr(response, "status", 200)
            raw = response.read()
        if status >= 400:
            raise RuntimeError(f"HTTP {status} para {province['code']}")
        low = raw[:2048].lstrip().lower()
        if low.startswith(b"<html") or low.startswith(b"<!doctype html"):
            raise RuntimeError(f"HTML inesperado para {province['code']}")
        data = json.loads(raw.decode("utf-8-sig"))
        features = data.get("features") or []
        if not features:
            raise RuntimeError(f"Sin features para provincia {province['code']}")
        field = str(source["territorial_filter_field"])
        for feature in features:
            actual = str((feature.get("properties") or {}).get(field, "")).zfill(2)
            if actual != str(province["code"]).zfill(2):
                raise RuntimeError(f"Provincia inesperada {actual} != {province['code']}")
        checks.append({
            "province": str(province["code"]).zfill(2),
            "features": len(features),
            "bytes": len(raw),
            "url": url,
        })
    return {
        "source_id": source["id"],
        "kind": source["kind"],
        "status": "PASS",
        "provinces": checks,
        "sample_records": sum(x["features"] for x in checks),
        "elapsed_seconds": round(time.monotonic() - started, 3),
    }


def unit_test(declaration: dict, catalog: dict, *, timeout: int, sample_size: int) -> dict:
    results = []
    for source_id in declaration["required_sources"]:
        source = catalog["sources"][source_id]
        if source["kind"] == "static_csv":
            results.append(probe_static_csv(source, timeout=timeout, sample_size=sample_size))
        elif source["kind"] == "ogc_features":
            results.append(probe_ogc(source, declaration, timeout=timeout, sample_size=sample_size))
        else:
            raise RuntimeError(f"Tipo no soportado: {source['kind']}")
    return {"mode": "unit", "decision": "PASS", "sources": results}


def run_cmd(args: list[str], *, expect_success: bool = True) -> subprocess.CompletedProcess[str]:
    completed = subprocess.run(args, cwd=ROOT, text=True, capture_output=True)
    if expect_success and completed.returncode != 0:
        raise RuntimeError(
            f"Comando falló ({completed.returncode}): {' '.join(args)}\nSTDOUT:\n{completed.stdout}\nSTDERR:\n{completed.stderr}"
        )
    return completed


def full_test(declaration_path: Path, out: Path, *, timeout: int) -> dict:
    # El sondeo mínimo corre siempre antes de una descarga completa.
    declaration = yaml.safe_load(declaration_path.read_text(encoding="utf-8"))
    catalog = yaml.safe_load(CATALOG.read_text(encoding="utf-8"))
    probe = unit_test(declaration, catalog, timeout=timeout, sample_size=10)

    working1 = out / "working-acquire"
    checkpoint1 = out / "checkpoint-acquire"
    evidence1 = out / "evidence-acquire"
    cmd1 = [
        sys.executable, "-m", "herramientas.ejecutar_fuentes_workflow",
        "--declaration", str(declaration_path),
        "--working", str(working1),
        "--checkpoint-out", str(checkpoint1),
        "--acquisition-evidence", str(evidence1),
        "--environment", "production",
        "--acquisition-mode", "official_live",
        "--root-dir", str(ROOT),
    ]
    t0 = time.monotonic()
    first = run_cmd(cmd1)
    acquire_seconds = time.monotonic() - t0
    first_exec = json.loads((checkpoint1 / "source_execution.json").read_text(encoding="utf-8"))
    if first_exec["decision"] != "ACQUIRE":
        raise RuntimeError(f"Se esperaba ACQUIRE y se obtuvo {first_exec['decision']}")

    working2 = out / "working-reuse"
    checkpoint2 = out / "checkpoint-reuse"
    evidence2 = out / "evidence-reuse"
    cmd2 = [
        sys.executable, "-m", "herramientas.ejecutar_fuentes_workflow",
        "--declaration", str(declaration_path),
        "--working", str(working2),
        "--checkpoint-in", str(checkpoint1),
        "--checkpoint-out", str(checkpoint2),
        "--acquisition-evidence", str(evidence2),
        "--environment", "production",
        "--acquisition-mode", "official_live",
        "--root-dir", str(ROOT),
    ]
    t1 = time.monotonic()
    second = run_cmd(cmd2)
    reuse_seconds = time.monotonic() - t1
    second_exec = json.loads((checkpoint2 / "source_execution.json").read_text(encoding="utf-8"))
    if second_exec["decision"] != "REUSE":
        raise RuntimeError(f"Se esperaba REUSE y se obtuvo {second_exec['decision']}")
    if first_exec["sha256"] != second_exec["sha256"]:
        raise RuntimeError("REUSE no conserva el hash del paquete")

    corrupt = out / "checkpoint-corrupt"
    shutil.copytree(checkpoint1, corrupt)
    bundle = corrupt / "sources" / "prepared_sources.zip"
    with bundle.open("ab") as fh:
        fh.write(b"corrupt")
    cmd3 = [
        sys.executable, "-m", "herramientas.ejecutar_fuentes_workflow",
        "--declaration", str(declaration_path),
        "--working", str(out / "working-corrupt"),
        "--checkpoint-in", str(corrupt),
        "--checkpoint-out", str(out / "checkpoint-corrupt-out"),
        "--acquisition-evidence", str(out / "evidence-corrupt"),
        "--environment", "production",
        "--acquisition-mode", "official_live",
        "--root-dir", str(ROOT),
    ]
    third = run_cmd(cmd3, expect_success=False)
    if third.returncode == 0:
        raise RuntimeError("Un paquete corrupto fue aceptado")

    return {
        "mode": "full",
        "decision": "PASS",
        "network_probe": probe,
        "acquire": {
            "decision": first_exec["decision"],
            "sha256": first_exec["sha256"],
            "bytes": first_exec["bytes"],
            "records": first_exec["records"],
            "elapsed_seconds": round(acquire_seconds, 3),
            "stdout": first.stdout.strip(),
        },
        "reuse": {
            "decision": second_exec["decision"],
            "sha256": second_exec["sha256"],
            "bytes": second_exec["bytes"],
            "records": second_exec["records"],
            "elapsed_seconds": round(reuse_seconds, 3),
            "stdout": second.stdout.strip(),
        },
        "corruption": {
            "decision": "BLOCK",
            "returncode": third.returncode,
            "stderr_tail": third.stderr[-2000:],
        },
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--territory", required=True)
    ap.add_argument("--edition", default="2025")
    ap.add_argument("--mode", choices=["unit", "full"], required=True)
    ap.add_argument("--output-dir", type=Path, required=True)
    ap.add_argument("--timeout-seconds", type=int, default=10)
    ap.add_argument("--sample-size", type=int, default=10)
    args = ap.parse_args()

    out = args.output_dir.resolve()
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    declaration = build_declaration(args.territory, int(args.edition))
    declaration_path = out / "fuentes_territorio.yaml"
    declaration_path.write_text(yaml.safe_dump(declaration, allow_unicode=True, sort_keys=False), encoding="utf-8")
    catalog = yaml.safe_load(CATALOG.read_text(encoding="utf-8"))

    protected = [ROOT / "inputs/65034.csv.zip", ROOT / f"inputs/seccionado_{args.edition}.zip"]
    before = file_state(protected)
    started = time.monotonic()
    try:
        if args.mode == "unit":
            result = unit_test(declaration, catalog, timeout=args.timeout_seconds, sample_size=args.sample_size)
        else:
            result = full_test(declaration_path, out, timeout=args.timeout_seconds)
        decision = "PASS"
    except Exception as exc:
        result = {"mode": args.mode, "decision": "BLOCK", "error": str(exc)}
        decision = "BLOCK"
    after = file_state(protected)
    if before != after:
        result = {
            "mode": args.mode,
            "decision": "BLOCK",
            "error": "La prueba modificó una fuente original protegida",
            "before": before,
            "after": after,
        }
        decision = "BLOCK"

    report = {
        "schema": "ddd-official-source-test/1.0",
        "territory": declaration["territory"],
        "requested_mode": args.mode,
        "timeout_seconds": args.timeout_seconds,
        "sample_size": args.sample_size,
        "original_sources_unchanged": before == after,
        "protected_sources": after,
        "elapsed_seconds": round(time.monotonic() - started, 3),
        **result,
    }
    (out / "report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False))
    return 0 if decision == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
