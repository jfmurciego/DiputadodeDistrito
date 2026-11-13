#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""PROYECTO: Diputado de Distrito
HERRAMIENTA: expediente probatorio reproducible Deslinde 1.0
VERSION: 1.0.0
FECHA: 2026-11-13
ESTADO: auxiliar, no invocada por produccion
MOTIVO: congelar codigo, autor identificado y huellas SHA-256 desde un commit.
ANTERIOR: ninguno.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import subprocess
import zipfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCES = (
    "ddd_motor2", "ddd_core", "modulos", "herramientas",
    "configuracion/notacion_territorial.csv",
    "configuracion/politica_generacion_territorial_2025.yaml",
    "docs/ARQUITECTURA/DESLINDE_1_0.md",
    "docs/ARQUITECTURA/ACEPTACION_MOTOR2.md",
    "CITATION.cff", "LICENSE", "NOTICE", "README.md",
)


def output_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for block in iter(lambda: file.read(1048576), b""):
            digest.update(block)
    return digest.hexdigest()


def revision() -> tuple[str, str]:
    def call(*args: str) -> str:
        return subprocess.check_output(
            ["git", "-C", str(ROOT), *args], text=True
        ).strip()
    return call("rev-parse", "HEAD"), call("show", "-s", "--format=%cI", "HEAD")


def crear(destination: Path) -> None:
    if destination.suffix.lower() != ".zip":
        raise ValueError("La salida debe terminar en .zip")
    if destination.exists():
        raise FileExistsError("El expediente ya existe: " + str(destination))
    missing = [p for p in SOURCES if not (ROOT / p).exists()]
    if missing:
        raise FileNotFoundError("Faltan archivos requeridos: " + ", ".join(missing))
    sha, fecha = revision()
    destination.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run([
        "git", "-C", str(ROOT), "archive", "--format=zip",
        "--output=" + str(destination.resolve()), sha, *SOURCES,
    ], check=True)
    with zipfile.ZipFile(destination, "a") as archive:
        listed = []
        for member in archive.infolist():
            if member.is_dir():
                continue
            body = archive.read(member.filename)
            listed.append({
                "ruta": member.filename,
                "bytes": len(body),
                "sha256": hashlib.sha256(body).hexdigest(),
            })
        listed.sort(key=lambda x: x["ruta"])
        record = {
            "schema": "ddd.deslinde.evidencia/1",
            "nombre": "Deslinde 1.0",
            "autor_segun_CITATION_cff": "Jesús Murciego",
            "repositorio": "https://github.com/jfmurciego/DiputadodeDistrito",
            "commit": sha,
            "fecha_git": fecha,
            "fecha_paquete_utc": datetime.now(timezone.utc).isoformat(),
            "fuentes": listed,
        }
        memo = (
            "# Deslinde 1.0: memoria técnica para acreditar versión\n\n"
            "Software Python que genera y evalúa distritos uninominales.\n"
            "Entradas: secciones censales, población, grafo y contratos.\n"
            "Flujo: M04/M05 canónico + ReCom ponderado + vigente → "
            "validaciones territoriales → criterio D8 → plan ganador.\n"
            "Salida: composición M06, geometría y evidencias P30.\n"
            "El código se invoca desde la cadena y no genera un ejecutable "
            "binario independiente.\n\n"
            "Esta memoria y el paquete deben revisarse y completarse "
            "antes del registro formal: titularidad, colaboradores, "
            "fecha de creación, intervención humana y utilización de IA.\n"
            "El paquete es una evidencia técnica, NO un registro oficial.\n\n"
            "Commit exacto: " + sha + "\n"
            "Fecha Git: " + fecha + "\n"
        )
        archive.writestr(
            "EVIDENCIA/MANIFEST_SHA256.json",
            json.dumps(record, ensure_ascii=False, indent=2) + "\n",
        )
        archive.writestr("EVIDENCIA/MEMORIA_REGISTRO.md", memo)
    digest = output_sha256(destination)
    destination.with_suffix(".zip.sha256").write_text(
        digest + "  " + destination.name + "\n", encoding="utf-8"
    )
    print("ZIP:", destination)
    print("SHA256:", digest)
    print("Commit:", sha)
    print("Archivos:", len(listed))


def verificar(destination: Path) -> None:
    sidecar = destination.with_suffix(".zip.sha256")
    saved = sidecar.read_text(encoding="utf-8").split()[0]
    if saved != output_sha256(destination):
        raise ValueError("La huella SHA-256 del paquete no coincide")
    with zipfile.ZipFile(destination) as zipfile_reader:
        record = json.loads(zipfile_reader.read("EVIDENCIA/MANIFEST_SHA256.json"))
        for item in record["fuentes"]:
            if hashlib.sha256(zipfile_reader.read(item["ruta"])).hexdigest() != item["sha256"]:
                raise ValueError("Archivo alterado: " + item["ruta"])
    print("OK: ZIP y", len(record["fuentes"]), "archivos íntegros")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--salida", required=True, type=Path)
    parser.add_argument("--verificar", action="store_true")
    args = parser.parse_args()
    if args.verificar:
        verificar(args.salida)
    else:
        crear(args.salida)
