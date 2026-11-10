#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Homologación de siglas de las candidaturas proclamadas de las generales 2026 (T-112, extiende T-97).

PROYECTO: Diputado de Distrito
VERSIÓN: 1.1.0 · FECHA: 2026-11-10 · ESTADO: candidato
CAMBIOS: 1.1.0 (T-200): ``resolver_zip`` / ``siglas_sin_regla`` / ``exigir_siglas_zip``: homologan las siglas del ZIP
  de Interior (no las del BOE) con las reglas 2026, la tabla ``interior`` de reglas_generales.json y las candidaturas
  BOE de la provincia; toda sigla sin regla ni candidatura es SIN_REGLA y la comprobación falla (fail-closed). Nada
  se infiere de memoria: las variantes de Interior 2026 se añaden con el ZIP real (sale tras el 29-11-2026).
MOTIVO: el ensayo T-197 mostró siglas de Interior (PSE-EE (PSOE), SUMAR - ECP…) que pasaban como identidad ALTA sin aviso.
ANTERIOR: legacy/herramientas/homologacion_candidaturas_2026_v1.0.0_20261110.py
QUÉ HACE: aplica datos/homologacion_siglas/reglas_candidaturas_2026.json (familias de D-20: «Podemos–Sumar»,
  «CiU–Junts», «UPN y coaliciones», «CHA-IU») a configuracion/candidaturas_congreso_2026.csv (BOE-A-2026-23103 +
  corrección BOE-A-2026-23383) y escribe datos/homologacion_siglas/homologacion_candidaturas_2026.csv con certeza,
  regla, fuente y sha256. Las filas BAJA no se deciden: las lista para el propietario. No toca la tabla 2011-2023.
Uso: python herramientas/homologacion_candidaturas_2026.py construir | comprobar
"""
from __future__ import annotations

import csv
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CAND = "configuracion/candidaturas_congreso_2026.csv"
CAND_JSON = "configuracion/candidaturas_congreso_2026.json"
REGLAS = "datos/homologacion_siglas/reglas_candidaturas_2026.json"
SALIDA = "datos/homologacion_siglas/homologacion_candidaturas_2026.csv"
COLUMNAS = ["eleccion", "codigo", "provincia", "sigla_boe", "denominacion_boe", "proclamada", "partido_homologado",
            "nivel_certeza", "regla", "fuente_boe", "sha256_xml"]
CERTEZAS = ("ALTA", "MEDIA", "BAJA", "DECIDIDA")


def sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def resolver(reglas: dict, sigla: str) -> tuple[str, str, str]:
    for r in reglas["siglas"]:
        if sigla in r["siglas"]:
            return r["homologado"], r["certeza"], r["id"]
    return sigla, "ALTA", "IDENTIDAD"


SIN_REGLA = "SIN_REGLA"
GENERALES = "datos/homologacion_siglas/reglas_generales.json"


def candidaturas_boe(root: Path = ROOT) -> dict[str, set[str]]:
    """código de provincia → siglas de las candidaturas BOE 2026."""
    out: dict[str, set[str]] = {}
    with (root / CAND).open(encoding="utf-8", newline="") as fh:
        for c in csv.DictReader(fh):
            out.setdefault(c["codigo"], set()).add(c["siglas"])
    return out


def resolver_zip(reglas: dict, generales: dict, sigla: str, codigo: str, boe: dict[str, set[str]],
                 eleccion: str = "202611") -> tuple[str, str, str]:
    """Sigla del ZIP de Interior → (homologado, certeza, regla). Orden: regla 2026 explícita, tabla ``interior`` de
    la elección en reglas_generales.json, sigla idéntica a una candidatura BOE de la provincia; si no, SIN_REGLA."""
    h, cert, rid = resolver(reglas, sigla)
    if rid != "IDENTIDAD":
        return h, cert, rid
    interior = generales.get("interior", {}).get(eleccion, {})
    if sigla in interior:
        return interior[sigla], "DECIDIDA", f"INTERIOR-{eleccion}"
    if sigla in boe.get(codigo, set()):
        return sigla, "ALTA", "IDENTIDAD_BOE"
    return sigla, SIN_REGLA, SIN_REGLA


def siglas_sin_regla(siglas, codigo: str, eleccion: str = "202611", root: Path = ROOT) -> list[str]:
    reglas = json.loads((root / REGLAS).read_text(encoding="utf-8"))
    generales = json.loads((root / GENERALES).read_text(encoding="utf-8"))
    boe = candidaturas_boe(root)
    return sorted(s for s in set(siglas) if resolver_zip(reglas, generales, s, codigo, boe, eleccion)[1] == SIN_REGLA)


def exigir_siglas_zip(siglas, codigo: str, eleccion: str = "202611", root: Path = ROOT) -> None:
    """Falla (ValueError SIGLAS_SIN_REGLA) si alguna sigla del ZIP no tiene regla ni candidatura BOE."""
    sin = siglas_sin_regla(siglas, codigo, eleccion, root)
    if sin:
        raise ValueError(f"SIGLAS_SIN_REGLA provincia {codigo} elección {eleccion}: {sin}")


def filas(root: Path = ROOT) -> list[dict]:
    reglas = json.loads((root / REGLAS).read_text(encoding="utf-8"))
    meta = json.loads((root / CAND_JSON).read_text(encoding="utf-8"))
    with (root / CAND).open(encoding="utf-8", newline="") as fh:
        cand = list(csv.DictReader(fh))
    out = []
    for c in cand:
        h, cert, rid = resolver(reglas, c["siglas"])
        out.append({"eleccion": "202611", "codigo": c["codigo"], "provincia": c["provincia"], "sigla_boe": c["siglas"],
                    "denominacion_boe": c["denominacion"], "proclamada": c["proclamada"], "partido_homologado": h,
                    "nivel_certeza": cert, "regla": rid, "fuente_boe": meta["boe"], "sha256_xml": meta["sha256_xml"]})
    return out


def validar(root: Path = ROOT) -> list[str]:
    reglas = json.loads((root / REGLAS).read_text(encoding="utf-8"))
    err, vistas = [], {}
    for r in reglas["siglas"]:
        if r["certeza"] not in CERTEZAS or not r["homologado"]:
            err.append(f"regla {r['id']}: inválida")
        for s in r["siglas"]:
            if s in vistas:
                err.append(f"sigla {s!r} en dos reglas: {vistas[s]} y {r['id']}")
            vistas[s] = r["id"]
    meta = json.loads((root / CAND_JSON).read_text(encoding="utf-8"))
    if meta["sha256_csv"] != sha256(root / CAND):
        err.append("sha256 de candidaturas_congreso_2026.csv distinto al declarado")
    return err


def escribir(fs: list[dict], destino: Path) -> None:
    with destino.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=COLUMNAS, lineterminator="\n")
        w.writeheader()
        w.writerows(fs)


def main(argv=None) -> int:
    cmd = (argv or sys.argv[1:] or [""])[0]
    if cmd not in ("construir", "comprobar"):
        print(__doc__)
        return 2
    err = validar()
    fs = filas() if not err else []
    if cmd == "comprobar" and not err:
        actual = (ROOT / SALIDA).read_text(encoding="utf-8")
        tmp = ROOT / (SALIDA + ".tmp")
        escribir(fs, tmp)
        if tmp.read_text(encoding="utf-8") != actual:
            err.append("la tabla no coincide con las reglas: reconstruir")
        tmp.unlink()
    for e in err:
        print("ERROR", e)
    if err:
        return 1
    if cmd == "construir":
        escribir(fs, ROOT / SALIDA)
    from collections import Counter
    print(dict(Counter(r["nivel_certeza"] for r in fs)))
    bajas = sorted({(r["sigla_boe"], r["regla"]) for r in fs if r["nivel_certeza"] == "BAJA"})
    print("BAJA:", bajas)
    return 0


if __name__ == "__main__":
    sys.exit(main())
