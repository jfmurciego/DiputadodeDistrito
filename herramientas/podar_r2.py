#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Poda de R2 con lista aprobada (T-145): verifica cada clave y su copia, y solo entonces borra.

PROYECTO: Diputado de Distrito
VERSIÓN: 1.0.0
NOMBRE DE VERSIÓN: Poda de R2 con lista aprobada
FECHA: 2026-11-10
ESTADO: candidato
CAMBIOS: 1.0.0: fichero nuevo (T-145).
MOTIVO: R2 tiene 28 GB frente a 10 GB gratuitos; el propietario aprobó la lista docs/ESTUDIOS/T145_PODA_R2/ola1_borrar.csv
  (234 claves). El borrado en R2 es irreversible: esta herramienta no borra nada fuera de esa lista.
ANTERIOR: ninguna (fichero nuevo)
QUÉ HACE: lee la lista (el sha256 del fichero debe ser el fijado en la entrada), y por cada fila comprueba (1) que la clave es un
  ``ddd-state-<run>-M0x.zip``, (2) que R2 la tiene con el sha256 de la lista y el manifiesto la anota igual, (3) que la copia que
  conserva existe en R2 y en el manifiesto con su sha256 y que no está en la propia lista, y (4) para M01/M02/M03/M03U, que
  el territorio tiene su entrada mínima ``bateria/entradas/<territorio>/*.zip`` con metadato sha256. Simulación por defecto: informa
  de todo y no borra. Con ``--ejecutar``: si algún desajuste, no borra nada; si no hay, borra una a una, comprueba que desaparece, quita la
  entrada del manifiesto y se detiene al primer error. Informe JSON de lo borrado.
USO: python herramientas/podar_r2.py --sha256-lista <sha> [--ejecutar] [--informe ruta.json]
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Optional

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "herramientas"))
import archivar_artefactos_r2 as ar  # noqa: E402

LISTA = "docs/ESTUDIOS/T145_PODA_R2/ola1_borrar.csv"
_ESTADO = re.compile(r"^[a-z0-9_]+/\d+/ddd-state-\d+-(M0\d[A-Z]?)\.zip$")
_ETAPAS_BATERIA = {"M01", "M02", "M03", "M03U"}


def sha256_fichero(ruta: Path) -> str:
    return hashlib.sha256(ruta.read_bytes()).hexdigest()


def leer_lista(ruta: Path, sha_esperado: str) -> list[dict]:
    real = sha256_fichero(ruta)
    if real != sha_esperado.strip().lower():
        raise ValueError(f"LISTA_NO_APROBADA: sha256 de la lista {real} != fijado {sha_esperado}")
    with ruta.open(encoding="utf-8", newline="") as fh:
        filas = list(csv.DictReader(fh))
    claves = [f["clave"] for f in filas]
    if len(set(claves)) != len(claves):
        raise ValueError("LISTA_INVALIDA: claves duplicadas")
    for f in filas:
        if not _ESTADO.match(f["clave"]):
            raise ValueError(f"LISTA_INVALIDA: {f['clave']} no es un estado ddd-state-*")
    return filas


def verificar(filas: list[dict], man: dict, sha: Callable[[str], Optional[str]],
              tiene_entrada: Callable[[str], bool]) -> list[dict]:
    """Devuelve la lista de desajustes (vacía = todo verificado). Solo lectura."""
    arts, claves = man["artefactos"], {f["clave"] for f in filas}
    fallos = []
    for f in filas:
        k, h, ck, ch = f["clave"], f["sha256"], f["copia_clave"], f["copia_sha256"]
        err = None
        etapa = _ESTADO.match(k).group(1)
        if ck in claves:
            err = "COPIA_EN_LA_LISTA"
        elif arts.get(k, {}).get("sha256") != h:
            err = "MANIFIESTO_DISTINTO"
        elif sha(k) != h:
            err = "SHA_R2_DISTINTO"
        elif arts.get(ck, {}).get("sha256") != ch:
            err = "COPIA_MANIFIESTO_DISTINTO"
        elif sha(ck) != ch:
            err = "COPIA_SHA_R2_DISTINTO"
        elif etapa in _ETAPAS_BATERIA and not tiene_entrada(f["territorio"]):
            err = "SIN_ENTRADA_MINIMA_BATERIA"
        if err:
            fallos.append({"clave": k, "error": err})
    return fallos


def podar(filas: list[dict], ruta_man: Path, sha, tiene_entrada, borrar, ejecutar: bool) -> dict:
    man = ar.cargar_manifiesto(ruta_man)
    fallos = verificar(filas, man, sha, tiene_entrada)
    informe = {"ejecutar": ejecutar, "claves": len(filas), "bytes_lista": sum(int(f["tamano_bytes"]) for f in filas),
               "desajustes": fallos, "borradas": [], "error": None,
               "fecha": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")}
    if fallos or not ejecutar:
        return informe
    try:
        for f in filas:
            k = f["clave"]
            borrar(k)
            if sha(k) is not None:
                raise RuntimeError(f"BORRADO_NO_EFECTIVO {k}")
            man["artefactos"].pop(k, None)
            informe["borradas"].append({"clave": k, "tamano_bytes": int(f["tamano_bytes"]), "sha256": f["sha256"],
                                        "copia_clave": f["copia_clave"], "copia_sha256": f["copia_sha256"]})
    except Exception as exc:  # noqa: BLE001 - se detiene al primer error y deja constancia
        informe["error"] = f"{type(exc).__name__}: {exc}"
    finally:
        ar.guardar_manifiesto(ruta_man, man)
    informe["bytes_borrados"] = sum(b["tamano_bytes"] for b in informe["borradas"])
    return informe


def clientes_r2(bucket: str, cuenta: str):
    sha, _ = ar.r2_cliente(bucket, cuenta)
    ep = f"https://{cuenta}.r2.cloudflarestorage.com"

    def _lista(prefijo: str) -> list[str]:
        p = subprocess.run(["aws", "s3api", "list-objects-v2", "--bucket", bucket, "--prefix", prefijo,
                            "--endpoint-url", ep, "--output", "json"], capture_output=True, text=True, check=True)
        return [o["Key"] for o in (json.loads(p.stdout or "{}").get("Contents") or [])]

    def tiene_entrada(territorio: str) -> bool:
        claves = ar.con_reintentos(lambda: _lista(f"bateria/entradas/{territorio}/"), f"R2 lista {territorio}")
        return any(k.endswith(".zip") and sha(k) for k in claves)

    def borrar(k: str) -> None:
        ar.con_reintentos(lambda: subprocess.run(
            ["aws", "s3", "rm", f"s3://{bucket}/{k}", "--endpoint-url", ep, "--only-show-errors"], check=True),
            f"R2 borrado {k}")

    return sha, tiene_entrada, borrar


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--root-dir", default=str(ROOT))
    ap.add_argument("--sha256-lista", required=True, help="sha256 aprobado de la lista CSV")
    ap.add_argument("--ejecutar", action="store_true", help="borra de verdad; sin él, solo simula")
    ap.add_argument("--informe", help="ruta del informe JSON")
    a = ap.parse_args(argv)
    root = Path(a.root_dir)
    bucket, cuenta = os.environ.get("R2_BUCKET", ""), os.environ.get("R2_ACCOUNT_ID", "")
    if not bucket or not cuenta:
        print("::error::Faltan R2_BUCKET o R2_ACCOUNT_ID.")
        return 1
    try:
        filas = leer_lista(root / LISTA, a.sha256_lista)
    except ValueError as exc:
        print(f"::error::{exc}")
        return 1
    sha, tiene_entrada, borrar = clientes_r2(bucket, cuenta)
    inf = podar(filas, root / ar.MANIFIESTO, sha, tiene_entrada, borrar, a.ejecutar)
    texto = json.dumps(inf, ensure_ascii=False, indent=2, sort_keys=True)
    if a.informe:
        Path(a.informe).parent.mkdir(parents=True, exist_ok=True)
        Path(a.informe).write_text(texto + "\n", encoding="utf-8")
    print(texto)
    for d in inf["desajustes"]:
        print(f"::error::{d['error']} {d['clave']}")
    if inf["error"]:
        print(f"::error::PODA_DETENIDA {inf['error']}")
    return 1 if inf["desajustes"] or inf["error"] else 0


if __name__ == "__main__":
    sys.exit(main())
