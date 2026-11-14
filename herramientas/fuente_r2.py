#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Fuentes oficiales permanentes en R2 (ARC-E): bajar y subir con verificación de sha256.

PROYECTO: Diputado de Distrito
VERSIÓN: 1.0.0
NOMBRE DE VERSIÓN: Fuentes de ARC-E en R2
FECHA: 2026-11-14
ESTADO: candidato
CAMBIOS: 1.0.0: fichero nuevo (T-299).
MOTIVO: el ZIP por mesa de Infoelectoral vivía solo en un release del repositorio; pasa a R2 (arc-e/fuentes/interior/) con su sha256 en
  el índice orchestracion/fuentes_r2.json y la 03 lo lee de R2 (el release queda como respaldo hasta confirmación del Operador).
ANTERIOR: ninguna (fichero nuevo)
QUÉ HACE: `bajar <nombre> <destino>`: baja de R2 la clave del índice y verifica el sha256 (si no cuadra, borra y sale 53; si no hay objeto o
  credenciales, sale 3 sin tocar red externa). `subir <nombre> <fichero>`: verifica el sha256 del índice y sube con metadato sha256.
USO: python herramientas/fuente_r2.py bajar 02202307_MESA.zip infoelectoral-mesas.zip
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INDICE = ROOT / "orchestracion" / "fuentes_r2.json"


def sha256(ruta: Path) -> str:
    h = hashlib.sha256()
    with open(ruta, "rb") as fh:
        for b in iter(lambda: fh.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def ficha(nombre: str, indice: Path = INDICE) -> dict:
    return json.loads(indice.read_text(encoding="utf-8"))["fuentes"][nombre]


def _cp(origen: str, destino: str, extra: list[str] | None = None) -> None:
    ep = f"https://{os.environ['R2_ACCOUNT_ID']}.r2.cloudflarestorage.com"
    subprocess.run(["aws", "s3", "cp", origen, destino, "--endpoint-url", ep, "--only-show-errors", *(extra or [])], check=True)


def bajar(nombre: str, destino: Path, cp=_cp, indice: Path = INDICE) -> int:
    try:
        f = ficha(nombre, indice)
    except KeyError:
        print(f"fuente_r2: {nombre} no está en el índice", file=sys.stderr)
        return 3
    if not os.environ.get("R2_BUCKET") or not os.environ.get("R2_ACCOUNT_ID"):
        print("fuente_r2: sin credenciales de R2", file=sys.stderr)
        return 3
    try:
        cp(f"s3://{os.environ['R2_BUCKET']}/{f['clave']}", str(destino))
    except Exception as exc:  # noqa: BLE001 - sin objeto o sin red: el llamador usa su respaldo
        print(f"fuente_r2: {f['clave']} no disponible en R2 ({exc})", file=sys.stderr)
        Path(destino).unlink(missing_ok=True)
        return 3
    real = sha256(Path(destino))
    if real != f["sha256"]:
        Path(destino).unlink(missing_ok=True)
        print(f"::error::FUENTE_R2_SHA256 {nombre}: {real} != {f['sha256']}", file=sys.stderr)
        return 53
    print(f"fuente_r2: {nombre} desde R2 ({f['clave']}) sha256 verificado")
    return 0


def subir(nombre: str, fichero: Path, cp=_cp, indice: Path = INDICE) -> int:
    try:
        f = ficha(nombre, indice)
    except KeyError:
        print(f"fuente_r2: {nombre} no está en el índice", file=sys.stderr)
        return 3
    real = sha256(fichero)
    if real != f["sha256"]:
        print(f"::error::FUENTE_R2_SHA256 {nombre}: {real} != {f['sha256']}", file=sys.stderr)
        return 53
    cp(str(fichero), f"s3://{os.environ['R2_BUCKET']}/{f['clave']}", ["--metadata", f"sha256={real}"])
    print(f"fuente_r2: {nombre} subida a {f['clave']}")
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    for c in ("bajar", "subir"):
        p = sub.add_parser(c)
        p.add_argument("nombre")
        p.add_argument("ruta")
    a = ap.parse_args(argv)
    return bajar(a.nombre, Path(a.ruta)) if a.cmd == "bajar" else subir(a.nombre, Path(a.ruta))


if __name__ == "__main__":
    raise SystemExit(main())
