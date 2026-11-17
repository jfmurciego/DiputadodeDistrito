#!/usr/bin/env python3
"""Descarga un artefacto de Actions distinguiendo cuota de egress (transitorio) y caducidad (definitivo).

PROYECTO: Diputado de Distrito
VERSIÓN: 1.0.0
NOMBRE DE VERSIÓN: Descarga de artefactos con clasificación de fallos
FECHA: 2026-11-11
ESTADO: candidato
QUÉ HACE: envuelve `gh run download <run> --name <artefacto> --dir <dir>` y clasifica el fallo:
  - «HTTP 503 Egress is over the account limit» → TRANSITORIO: reintenta con espera creciente
    (tope de intentos) y, si se agota, sale con EXIT_EGRESS explicando que es cuota de Actions
    (Settings → Billing), no un artefacto perdido;
  - artefacto caducado o inexistente (404/410, «no artifact matches», «expired») → DEFINITIVO:
    sale con EXIT_MISSING y la remediación (qué workflow lo regenera), sin reintentar;
  - cualquier otro fallo → EXIT_OTHER con el mensaje original.
CAMBIOS: herramienta nueva (T-251).
MOTIVO: la puerta de validación decía «No se pudo descargar» tanto si el artefacto había caducado
como si la cuenta había agotado el egress de Actions; se tomaban por perdidos artefactos vivos.
ANTERIOR: ninguna (fichero nuevo)
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
import time
from dataclasses import dataclass
from typing import Callable, Sequence

EXIT_OTHER = 42
EXIT_MISSING = 44
EXIT_EGRESS = 75  # EX_TEMPFAIL

ESPERAS_S = (30, 60, 120, 240, 480)  # 5 reintentos, ~15,5 min como máximo

_EGRESS = re.compile(r"egress\s+is\s+over\s+the\s+account\s+limit", re.I)
_MISSING = re.compile(
    r"HTTP\s+(404|410)\b|no\s+valid\s+artifacts\s+found|no\s+artifact\s+matches|artifact\s+has\s+expired",
    re.I,
)

REMEDIACION = (
    ("ddd-state-", "-M06", "regenerar con la 00 (ejecucion-completa-proyecto.yml) en «Generar desde fuente territorial "
     "acreditada»; si la copia durable almacen-m06-* existe, la puerta la usa sola"),
    ("ddd-audit-electoral-", "", "regenerar el producto electoral: 00 en «Reutilizar progreso existente» (rehace 03/04) "
     "o, si caducó el paquete, preparacion-resultados-electorales.yml con reutilizar=false"),
    ("ddd-audit-", "", "regenerar el producto territorial con la 00 en «Generar desde fuente territorial acreditada»"),
    ("ddd-state-", "-M08", "regenerar el producto electoral con la 00 en «Reutilizar progreso existente» (rehace 03/04)"),
    ("ddd-fuentes-", "", "regenerar el paquete con preparacion-fuentes.yml"),
)


def remediacion(nombre: str, run_id: str) -> str:
    for prefijo, sufijo, texto in REMEDIACION:
        if nombre.startswith(prefijo) and nombre.endswith(sufijo):
            return texto
    return f"relanzar el workflow que produjo el run {run_id} para regenerar el artefacto"


@dataclass
class Resultado:
    rc: int
    clase: str  # ok | egress | missing | other
    intentos: int
    mensaje: str


Runner = Callable[[Sequence[str]], "subprocess.CompletedProcess[str]"]


def _run(cmd: Sequence[str]) -> "subprocess.CompletedProcess[str]":
    return subprocess.run(list(cmd), capture_output=True, text=True)


def clasificar(salida: str) -> str:
    if _EGRESS.search(salida):
        return "egress"
    if _MISSING.search(salida):
        return "missing"
    return "other"


def descargar(repo: str, run_id: str, nombre: str, destino: str, *, runner: Runner = _run,
              dormir: Callable[[float], None] = time.sleep, esperas: Sequence[float] = ESPERAS_S) -> Resultado:
    cmd = ["gh", "run", "download", str(run_id), "--repo", repo, "--name", nombre, "--dir", destino]
    intentos = 0
    while True:
        intentos += 1
        proc = runner(cmd)
        if proc.returncode == 0:
            return Resultado(0, "ok", intentos, f"Descargado {nombre} (run {run_id})")
        salida = f"{proc.stdout or ''}\n{proc.stderr or ''}".strip()
        clase = clasificar(salida)
        if clase == "egress" and intentos <= len(esperas):
            espera = esperas[intentos - 1]
            print(f"::warning::ARTIFACT_EGRESS_QUOTA {nombre}: HTTP 503 de cuota de Actions; reintento "
                  f"{intentos}/{len(esperas)} en {espera:g} s", file=sys.stderr)
            dormir(espera)
            continue
        if clase == "egress":
            return Resultado(EXIT_EGRESS, clase, intentos,
                             f"ARTIFACT_EGRESS_QUOTA: {nombre} (run {run_id}) no se pudo descargar tras {intentos} "
                             "intentos por HTTP 503 «Egress is over the account limit»: es la cuota de transferencia de "
                             "Actions de la cuenta (Settings → Billing), NO un artefacto perdido. Relanzar cuando se "
                             "restablezca la cuota o se amplíe el límite; no regenerar.")
        if clase == "missing":
            return Resultado(EXIT_MISSING, clase, intentos,
                             f"ARTIFACT_MISSING: {nombre} (run {run_id}) caducado o inexistente en Actions (fallo "
                             f"definitivo). Remediación: {remediacion(nombre, str(run_id))}. Detalle: {salida[-300:]}")
        return Resultado(EXIT_OTHER, clase, intentos,
                         f"ARTIFACT_DOWNLOAD_FAILED: {nombre} (run {run_id}): {salida[-300:]}")


def main(argv: Sequence[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--repo", required=True)
    p.add_argument("--run-id", required=True)
    p.add_argument("--name", required=True)
    p.add_argument("--dir", required=True)
    a = p.parse_args(argv)
    r = descargar(a.repo, a.run_id, a.name, a.dir)
    if r.rc:
        print(f"::error::{r.mensaje}", file=sys.stderr)
    else:
        print(r.mensaje)
    return r.rc


if __name__ == "__main__":
    sys.exit(main())
