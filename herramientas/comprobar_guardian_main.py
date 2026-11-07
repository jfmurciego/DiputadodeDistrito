#!/usr/bin/env python3
"""Guardián de main: comprobaciones mecánicas que antes rompieron main.

PROYECTO: Diputado de Distrito
VERSIÓN: 1.0.0 · FECHA: 2026-11-07 · ESTADO: candidato
ANTERIOR: ninguna (fichero nuevo)
QUÉ HACE: dos comprobaciones deterministas, sin modelo y solo con la biblioteca estándar:
  - marcas: ningún fichero versionado (git ls-files) contiene marcas de conflicto de Git
    (líneas que empiezan por «<<<<<<<», «|||||||» o «>>>>>>>», o «=======» dentro de un bloque abierto).
  - registro: la cabecera de docs/REGISTRO_DE_CAMBIOS.md es consecutiva a su ANTERIOR: el predecesor existe,
    su propia Versión es la que nombra el fichero y la Versión actual es la siguiente (último componente + 1).
MOTIVO: marcas de conflicto en el registro rompieron main (hotfix #422); el plan de agentes (paso 1,
  docs/ARQUITECTURA/FRAMEWORK_AGENTES_Y_ESTRUCTURA.md §12) pide estas dos comprobaciones en CI.
Uso: python herramientas/comprobar_guardian_main.py {marcas,registro,todo} [--raiz RUTA]
Salida: 0 si pasa; 1 con una línea «::error» por fallo.
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRO = "docs/REGISTRO_DE_CAMBIOS.md"

_OPEN = re.compile(r"^<{7}(?: |$)")
_BASE = re.compile(r"^\|{7}(?: |$)")
_SEP = re.compile(r"^={7}$")
_CLOSE = re.compile(r"^>{7}(?: |$)")
_VERSION = re.compile(r"(?mi)^\s*(?:\*\*)?Versi[oó]n:(?:\*\*)?\s*`?(\d+(?:\.\d+)+)`?\s*$")
_ANTERIOR = re.compile(r"(?mi)^\s*(?:\*\*)?Anterior:(?:\*\*)?\s*`?([^`\s]+)`?\s*$")


def marcas_en_texto(texto: str) -> list[int]:
    """Números de línea (1-based) con marcas de conflicto."""
    lineas: list[int] = []
    abierto = False
    for numero, linea in enumerate(texto.splitlines(), start=1):
        linea = linea.rstrip("\r")
        if _OPEN.match(linea):
            abierto = True
            lineas.append(numero)
        elif _BASE.match(linea) or _CLOSE.match(linea):
            lineas.append(numero)
            if _CLOSE.match(linea):
                abierto = False
        elif abierto and _SEP.match(linea):
            lineas.append(numero)
    return lineas


def ficheros_versionados(raiz: Path) -> list[Path]:
    salida = subprocess.run(
        ["git", "-C", str(raiz), "ls-files", "-z"], capture_output=True, check=True
    ).stdout.decode("utf-8", "surrogateescape")
    return [raiz / rel for rel in salida.split("\0") if rel]


def comprobar_marcas(ficheros: list[Path], raiz: Path) -> list[str]:
    errores: list[str] = []
    for ruta in ficheros:
        try:
            datos = ruta.read_bytes()
        except (FileNotFoundError, IsADirectoryError):
            continue
        if b"\0" in datos[:8192]:
            continue  # binario
        texto = datos.decode("utf-8", "replace")
        if "<<<<<<<" not in texto and ">>>>>>>" not in texto and "|||||||" not in texto:
            continue
        for numero in marcas_en_texto(texto):
            rel = ruta.relative_to(raiz) if ruta.is_relative_to(raiz) else ruta
            errores.append(f"::error file={rel},line={numero}::marca de conflicto de Git en {rel}:{numero}")
    return errores


def _version(texto: str) -> str | None:
    m = _VERSION.search(texto[:5000])
    return m.group(1) if m else None


def siguiente(version: str) -> str:
    partes = version.split(".")
    partes[-1] = str(int(partes[-1]) + 1)
    return ".".join(partes)


def comprobar_registro(raiz: Path) -> list[str]:
    ruta = raiz / REGISTRO
    if not ruta.is_file():
        return [f"::error file={REGISTRO}::no existe {REGISTRO}"]
    texto = ruta.read_text(encoding="utf-8")
    actual = _version(texto)
    if not actual:
        return [f"::error file={REGISTRO}::cabecera sin «Versión: X.Y.Z» parseable"]
    m = _ANTERIOR.search(texto[:5000])
    if not m:
        return [f"::error file={REGISTRO}::cabecera sin «Anterior:» parseable"]
    anterior_rel = m.group(1)
    if not anterior_rel.startswith("legacy/"):
        return [f"::error file={REGISTRO}::Anterior debe apuntar a legacy/: {anterior_rel}"]
    anterior = raiz / anterior_rel
    if not anterior.is_file():
        return [f"::error file={REGISTRO}::falta la copia legacy del predecesor: {anterior_rel}"]
    previa = _version(anterior.read_text(encoding="utf-8"))
    if not previa:
        return [f"::error file={anterior_rel}::el predecesor no tiene «Versión:» parseable"]
    errores: list[str] = []
    nombrada = re.search(r"_v(\d+(?:\.\d+)+)(?:_|\.md$)", anterior.name)
    if nombrada and nombrada.group(1) != previa:
        errores.append(
            f"::error file={anterior_rel}::el nombre dice {nombrada.group(1)} y la cabecera {previa}"
        )
    if actual != siguiente(previa):
        errores.append(
            f"::error file={REGISTRO}::numeración no consecutiva: Versión {actual} tras {previa} "
            f"(se esperaba {siguiente(previa)}); pide el número al planificador"
        )
    return errores


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("comprobacion", choices=["marcas", "registro", "todo"])
    parser.add_argument("--raiz", type=Path, default=ROOT)
    args = parser.parse_args(argv)
    raiz = args.raiz.resolve()
    errores: list[str] = []
    if args.comprobacion in ("marcas", "todo"):
        errores += comprobar_marcas(ficheros_versionados(raiz), raiz)
    if args.comprobacion in ("registro", "todo"):
        errores += comprobar_registro(raiz)
    for error in errores:
        print(error)
    if not errores:
        print(f"OK: {args.comprobacion}")
    return 1 if errores else 0


if __name__ == "__main__":
    sys.exit(main())
