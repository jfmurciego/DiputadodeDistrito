#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# VERSIÓN: 1.0.0
# FECHA: 2026-11-08
# ESTADO: candidato
# CAMBIOS: T-87, fichero nuevo.
# MOTIVO: la cadena de publicación debe resolver el run origen de una 00 «Reutilizar» antes de publicar.
# ANTERIOR: ninguna (fichero nuevo)
"""T-87 · Resuelve, desde el registro durable de una 00, qué publicar en la cadena 05 + versión de mapa.

Lee `territorios/*/evidencia/ejecuciones_completas/<run>.json` (versionado en git) y devuelve el run que
generó el M08 (el run origen si la 00 fue «Reutilizar»), el run y el artefacto M06 y el territorio.
No descarga nada ni publica: si la puerta 04 no está validada, bloquea con un motivo claro.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

DECISIONES_VALIDAS = {"PASS", "PASS_WITH_EXCEPTIONS"}


def _fase(record: dict, prefijo: str) -> dict:
    for fase in record.get("phases") or []:
        if isinstance(fase, dict) and str(fase.get("name", "")).startswith(prefijo):
            return fase
    return {}


def _validada(fase: dict) -> bool:
    return (
        fase.get("validation_decision") == "VALIDADO"
        and fase.get("phase_decision") in DECISIONES_VALIDAS
        and fase.get("run_id") not in (None, "")
        and bool(fase.get("artifact"))
    )


def resolver(root: Path, run_id: str) -> dict:
    run_id = str(run_id).strip()
    reasons: list[str] = []
    out: dict = {"requested_run_id": run_id, "status": "BLOCK", "reasons": reasons}
    if not run_id.isdigit():
        reasons.append("PRODUCTION_RUN_ID_NO_NUMERICO")
        return out
    registros = sorted(root.glob(f"territorios/*/evidencia/ejecuciones_completas/{run_id}.json"))
    if not registros:
        reasons.append("REGISTRO_00_AUSENTE")
        return out
    if len(registros) > 1:
        reasons.append("REGISTRO_00_DUPLICADO")
        return out
    record = json.loads(registros[0].read_text(encoding="utf-8"))
    out["territory_id"] = record.get("territory_id") or registros[0].parts[-4]
    out["execution_mode"] = record.get("execution_mode")
    if record.get("status") != "SUCCESS":
        reasons.append(f"EJECUCION_00_NO_SUCCESS={record.get('status')}")
    f04, f02 = _fase(record, "04"), _fase(record, "02")
    if not _validada(f04):
        reasons.append("PUERTA_04_NO_VALIDADA")
    if not _validada(f02):
        reasons.append("M06_NO_VALIDADO")
    if reasons:
        return out
    publish_run = str(f04["run_id"])
    out.update(
        publish_run_id=publish_run,
        m08_artifact=f04["artifact"],
        m06_run_id=str(f02["run_id"]),
        m06_artifact=f02["artifact"],
        reused=publish_run != run_id,
        status="READY",
    )
    if publish_run != run_id:
        out["notes"] = [f"EJECUCION_REUTILIZADA_PUBLICAR_CON_PRODUCTION_RUN_ID={publish_run}"]
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--run-id", required=True)
    args = parser.parse_args(argv)
    result = resolver(args.root, args.run_id)
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0 if result["status"] == "READY" else 2


if __name__ == "__main__":
    sys.exit(main())
