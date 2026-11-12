#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# PROYECTO: Diputado de Distrito
# CLASE: herramienta de diagnóstico de CI (revisor de PR)
# VERSIÓN: 1.0.0
# FECHA: 2026-11-12
# ESTADO: candidato
# CAMBIOS: valida salida del agente y diagnostica rechazos de proveedor sin mostrar payload sensible.
# MOTIVO: no convertir un fallo de Claude Code Action en un PASS sin revisión real.
# ANTERIOR: ninguna (fichero nuevo)
"""Valida el veredicto de Claude y clasifica errores del proveedor sin revelar su contenido."""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

VALID = {"PASS", "PASS_WITH_EXCEPTIONS", "FAIL", "BLOCKED"}


class RevisionInvalida(ValueError):
    """No consta un veredicto real ligado al HEAD revisado."""


def _walk(obj: Any):
    if isinstance(obj, dict):
        yield obj
        for value in obj.values():
            yield from _walk(value)
    elif isinstance(obj, list):
        for value in obj:
            yield from _walk(value)


def _read_execution(path: str) -> list[Any]:
    """El SDK entrega JSON; la salida de diagnóstico puede ser también JSONL."""
    if not path:
        return []
    file = Path(path)
    if not file.is_file():
        return []
    raw = file.read_text(encoding="utf-8", errors="replace")
    try:
        return [json.loads(raw)]
    except json.JSONDecodeError:
        records = []
        for line in raw.splitlines():
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError:
                continue
        return records


def clasificar_fallo(documento: list[Any]) -> str:
    """Solo códigos y campos de estado; nunca imprime prompts, tokens ni respuestas."""
    objects = [v for root in documento for v in _walk(root) if isinstance(v, dict)]
    statuses = [str(v.get("api_error_status") or v.get("error_status") or "")
                for v in objects]
    statuses += [str(v.get("status")) for v in objects
                 if v.get("status") in (400, 401, 403, 429)]
    if "401" in statuses or "403" in statuses:
        return ("El proveedor ha rechazado la autenticación (HTTP 401/403). "
                "Comprobar el secreto de Anthropic en Actions y su acceso al modelo; "
                "renovar las credenciales si procede.")
    if "429" in statuses:
        return ("El proveedor ha limitado las peticiones (HTTP 429). "
                "Verificar cuota, créditos o rate limits antes de reintentar.")
    if "400" in statuses:
        return ("El proveedor rechazó la petición (HTTP 400). "
                "Verificar crédito, modelo, permisos y parámetros de Claude Code.")
    if any(v.get("is_error") is True and v.get("num_turns") == 1 for v in objects):
        return ("Claude inicializó el SDK pero la primera llamada terminó en error "
                "(una interacción, ningún trabajo de revisión). Posibles causas: "
                "OAuth, límites del proveedor o incidencia de Claude Code.")
    if documento:
        return ("Claude no entregó salida estructurada utilizable. "
                "Inspeccionar la ejecución y la compatibilidad del Agent SDK.")
    return ("Claude no entregó salida estructurada ni archivo de diagnóstico; "
            "verificar autenticación de Anthropic y compatibilidad de claude-code-action.")


def validar_resultado(structured: str, expected_sha: str, events: list[Any]) -> dict:
    if not structured.strip():
        raise RevisionInvalida(clasificar_fallo(events))
    try:
        data = json.loads(structured)
    except json.JSONDecodeError as exc:
        raise RevisionInvalida("La salida del revisor no es JSON válido.") from exc
    if not isinstance(data, dict):
        raise RevisionInvalida("La salida del revisor no es un objeto JSON.")
    if data.get("sha") != expected_sha:
        raise RevisionInvalida("SHA del veredicto diferente del HEAD revisado.")
    if data.get("veredicto") not in VALID:
        raise RevisionInvalida("Veredicto ausente o inválido.")
    if not isinstance(data.get("defectos"), list) or not isinstance(data.get("siguiente"), str):
        raise RevisionInvalida("Contrato del veredicto incompleto.")
    if any(not isinstance(x, dict) or not all(k in x for k in
           ("gravedad", "clase", "fichero", "detalle")) for x in data["defectos"]):
        raise RevisionInvalida("Campos obligatorios de los defectos ausentes.")
    return data


def main() -> int:
    output = os.environ.get("CLAUDE_STRUCTURED_OUTPUT", "")
    sha = os.environ.get("EXPECTED_HEAD_SHA", "")
    candidate = os.environ.get("CLAUDE_EXECUTION_FILE") or ""
    local = str(Path(os.environ.get("RUNNER_TEMP", "/tmp")) / "claude-execution-output.json")
    events = _read_execution(candidate) or _read_execution(local)
    try:
        verdict = validar_resultado(output, sha, events)
    except RevisionInvalida as exc:
        print(f"::error title=Revisor independiente no disponible::{exc}")
        return 1
    if verdict["veredicto"] == "BLOCKED":
        print("::error title=Revisor bloqueado::El revisor ha emitido BLOCKED; no hay GO.")
        return 1
    print("Revisor independiente: salida JSON y SHA íntegros. Veredicto=" +
          verdict["veredicto"] + ", HEAD=" + sha[:12])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
