#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PROYECTO: Diputado de Distrito
COMPONENTE: preparación declarativa de unidades internas
VERSIÓN: 1.1.0
NOMBRE DE VERSIÓN: Preprocesador común auditable previo a M04
FECHA: 2026-09-17
ESTADO: candidato
FUNCIÓN: materializar, sólo cuando el contrato lo declara, unidades internas conexas antes de M04 sin lógica territorial específica.
CAMBIOS: añade informe de trabajo con entrada, salida, duración, estado y bloqueo estructurado; conserva no-op neutro.
MOTIVO: permitir que el preprocesado sea un trabajo visible y auditable en GitHub Actions.
ANTERIOR: versión 1.0.0 en historial Git.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import subprocess
import sys
import time
from pathlib import Path

import yaml

SUPPORTED_STRATEGIES = {"connected_internal_units"}


def _fmt(value: str, *, cfg: dict, run_id: str) -> str:
    meta = cfg.get("meta") or {}
    return str(value).format(
        run_name=meta.get("run_name", ""),
        run_id=run_id,
        year=meta.get("year", ""),
    )


def _load(params_path: str | Path) -> dict:
    return yaml.safe_load(Path(params_path).read_text(encoding="utf-8")) or {}


def describe(params_path: str | Path, run_id: str) -> dict:
    cfg = _load(params_path)
    policy = cfg.get("partitioning") or {}
    m04 = ((cfg.get("modulos") or {}).get("modulo_04_generar_semillas") or {})
    if not policy or policy.get("enabled") is False or not str(policy.get("strategy") or "").strip():
        return {
            "enabled": False,
            "strategy": None,
            "input_geojson": None,
            "graph": None,
            "output_geojson": _fmt(str(m04.get("in_geojson") or ""), cfg=cfg, run_id=run_id) or None,
            "output_report": None,
        }
    return {
        "enabled": True,
        "strategy": str(policy.get("strategy") or "").strip(),
        "input_geojson": _fmt(str(policy.get("input_geojson") or ""), cfg=cfg, run_id=run_id),
        "graph": _fmt(str(policy.get("graph") or ""), cfg=cfg, run_id=run_id),
        "output_geojson": _fmt(str(policy.get("output_geojson") or ""), cfg=cfg, run_id=run_id),
        "output_report": _fmt(str(policy.get("output_report") or ""), cfg=cfg, run_id=run_id),
    }


def build_command(params_path: str | Path, run_id: str) -> list[str] | None:
    params = Path(params_path)
    cfg = _load(params)
    policy = cfg.get("partitioning") or {}
    if not policy or policy.get("enabled") is False:
        return None
    strategy = str(policy.get("strategy") or "").strip()
    if not strategy:
        return None
    if strategy not in SUPPORTED_STRATEGIES:
        raise ValueError(f"Estrategia común de unidades internas no soportada: {strategy}")

    required = (
        "input_geojson", "graph", "output_geojson", "output_report",
        "partition_unit_field", "atomicity_ratio", "chunk_ratio",
    )
    missing = [key for key in required if policy.get(key) in (None, "")]
    if missing:
        raise ValueError("partitioning incompleto: " + ", ".join(missing))

    contract = cfg.get("territory_contract") or {}
    k = contract.get("k_districts")
    if not isinstance(k, int) or isinstance(k, bool) or k <= 0:
        raise ValueError("territory_contract.k_districts debe ser entero positivo")

    m04 = ((cfg.get("modulos") or {}).get("modulo_04_generar_semillas") or {})
    id_field = str(policy.get("id_field") or m04.get("id_field") or "CUSEC_KEY")
    municipality_field = str(policy.get("municipality_field") or "CUMUN")
    population_field = str(policy.get("population_field") or m04.get("pop_field") or f"POP_{(cfg.get('meta') or {}).get('year', '')}")

    output_geojson = _fmt(policy["output_geojson"], cfg=cfg, run_id=run_id)
    m04_input = _fmt(str(m04.get("in_geojson") or ""), cfg=cfg, run_id=run_id)
    if output_geojson != m04_input:
        raise ValueError("partitioning.output_geojson debe coincidir exactamente con M04.in_geojson")

    return [
        sys.executable,
        str(Path(__file__).with_name("construir_unidades_internas_m04.py")),
        "--geojson", _fmt(policy["input_geojson"], cfg=cfg, run_id=run_id),
        "--graph", _fmt(policy["graph"], cfg=cfg, run_id=run_id),
        "--out-geojson", output_geojson,
        "--out-report", _fmt(policy["output_report"], cfg=cfg, run_id=run_id),
        "--k", str(k),
        "--id-field", id_field,
        "--municipality-field", municipality_field,
        "--population-field", population_field,
        "--partition-unit-field", str(policy["partition_unit_field"]),
        "--atomicity-ratio", str(policy["atomicity_ratio"]),
        "--chunk-ratio", str(policy["chunk_ratio"]),
    ]


def prepare(params_path: str | Path, run_id: str, *, execute: bool = True) -> list[str] | None:
    command = build_command(params_path, run_id)
    if command is None:
        print("[UNIDADES INTERNAS] Contrato sin preprocesado declarativo; no-op.")
        return None
    if execute:
        subprocess.run(command, check=True)
    return command


def _write_job_report(path: str | Path | None, payload: dict) -> None:
    if not path:
        return
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--params", required=True)
    parser.add_argument("--run-id", default="")
    parser.add_argument("--job-report", default="")
    args = parser.parse_args()
    started_monotonic = time.monotonic()
    started_at = dt.datetime.now(dt.timezone.utc).isoformat()
    desc = describe(args.params, args.run_id)
    payload = {
        "schema": "ddd.internal-units-job/1.0",
        "params": args.params,
        "run_id": args.run_id,
        "enabled": desc["enabled"],
        "strategy": desc["strategy"],
        "input_geojson": desc["input_geojson"],
        "graph": desc["graph"],
        "output_geojson": desc["output_geojson"],
        "output_report": desc["output_report"],
        "started_at_utc": started_at,
    }
    try:
        command = prepare(args.params, args.run_id, execute=True)
        payload["status"] = "PREPARED" if command else "NOOP"
        payload["command"] = command
        if command:
            for label in ("input_geojson", "graph", "output_geojson", "output_report"):
                raw = payload.get(label)
                if raw and not Path(raw).exists():
                    raise RuntimeError(f"No existe {label} después de preparar: {raw}")
    except Exception as exc:
        payload["status"] = "BLOCKED"
        payload["error"] = f"{type(exc).__name__}: {exc}"
        payload["finished_at_utc"] = dt.datetime.now(dt.timezone.utc).isoformat()
        payload["duration_seconds"] = round(time.monotonic() - started_monotonic, 6)
        _write_job_report(args.job_report, payload)
        print(f"[UNIDADES INTERNAS] BLOCKED: {exc}", file=sys.stderr)
        raise SystemExit(2)
    payload["finished_at_utc"] = dt.datetime.now(dt.timezone.utc).isoformat()
    payload["duration_seconds"] = round(time.monotonic() - started_monotonic, 6)
    _write_job_report(args.job_report, payload)
    print(json.dumps({k: payload.get(k) for k in ("status", "input_geojson", "output_geojson", "duration_seconds")}, ensure_ascii=False))


if __name__ == "__main__":
    main()
