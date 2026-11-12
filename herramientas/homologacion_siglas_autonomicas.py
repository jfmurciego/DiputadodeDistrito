#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tabla de homologación de siglas de las autonómicas para la capa de rotación (T-121, paso 4, D-20).

PROYECTO: Diputado de Distrito
VERSIÓN: 1.0.1 · FECHA: 2026-11-12 · ESTADO: candidato
CAMBIOS: 1.0.0: fichero nuevo.
MOTIVO: la rotación autonómica no debe contar «PP-EU → PP» ni «PSC → PSOE» como cambio de ganador; extiende la tabla de
  T-97 a los partidos autonómicos sin modificar homologacion_siglas.py (reutiliza su `resolver`).
CAMBIOS 1.0.1 (T-220): ids de territorio nuevos de la tabla maestra (aut01…nac52, D-61); el id viejo se lee vía ddd_core.territorio_ids.
ANTERIOR: legacy/herramientas/homologacion_siglas_autonomicas_v1.0.0_20261112.py
QUÉ HACE: `construir` lee data/autonomikoak/sekzioa/<cca>-<AAAAMM>/<cpro>.json (siglas `s`, familia `f`) del directorio
  dado, y escribe por comunidad, elección y sigla con votos el partido homologado (regla de sigla > familia > identidad,
  reglas_generales.json + reglas_autonomicas.json), el nivel (ALTA/MEDIA/BAJA/DECIDIDA), la regla y el sha256 de la
  fuente, en datos/homologacion_siglas/homologacion_siglas_autonomicas.csv. Sigla de una familia sin regla: se
  deja tal cual con nivel BAJA (no se inventa). `comprobar` revalida sin red: claves únicas y reaplicación de las reglas.
  `dudosas` lista las BAJA y MEDIA agrupadas por partido homologado.
Uso: python herramientas/homologacion_siglas_autonomicas.py construir --obs-dir DIR [--comunidad aut12 …]
     python herramientas/homologacion_siglas_autonomicas.py comprobar | dudosas
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))
import homologacion_siglas as hs  # noqa: E402
import calendario_autonomicas as cal  # noqa: E402

DIR = "datos/homologacion_siglas"
REGLAS_G, REGLAS_A = f"{DIR}/reglas_generales.json", f"{DIR}/reglas_autonomicas.json"
SALIDA = f"{DIR}/homologacion_siglas_autonomicas.csv"
CAMPOS = ["comunidad", "eleccion", "sigla_fuente", "votos_fuente", "familia_fuente", "partido_homologado",
          "nivel_certeza", "regla", "ruta_fuente", "sha256_fuente"]


def reglas(root: Path = ROOT) -> dict:
    g = json.loads((root / REGLAS_G).read_text(encoding="utf-8"))
    a = json.loads((root / REGLAS_A).read_text(encoding="utf-8"))
    return {**g, "familias": {**g["familias"], **a["familias"]}, "siglas": a["siglas"] + g["siglas"]}


def resolver(r: dict, comunidad: str, eleccion: str, sigla: str, familia: str) -> tuple[str, str, str]:
    """Como hs.resolver, pero una familia sin regla no es error: identidad con nivel BAJA."""
    try:
        return hs.resolver(r, eleccion, comunidad, sigla, familia)
    except KeyError:
        return sigla, "BAJA", f"SIN_REGLA_FAMILIA:{familia}"


def construir_filas(obs_dir: Path, r: dict, solo: set | None = None) -> list[dict]:
    por_com = {cod: tid for cod, (tid, _) in cal.COMUNIDADES.items()}
    acum: dict = defaultdict(lambda: {"votos": 0, "ruta": set(), "sha": {}})
    for f in sorted((obs_dir / "sekzioa").glob("*/*.json")):
        cca, ele = f.parent.name.split("-")
        com = por_com[cca]
        if solo and com not in solo:
            continue
        crudo = f.read_bytes()
        d = json.loads(crudo)
        votos: Counter = Counter()
        for _c, (_ce, _v, _cand, ps) in d["r"].items():
            for i, n in ps:
                votos[i] += n
        for i, sigla in enumerate(d["s"]):
            a = acum[(com, ele, sigla, d["f"][i])]
            a["votos"] += votos[i]
            a["sha"][f"sekzioa/{f.parent.name}/{f.name}"] = hashlib.sha256(crudo).hexdigest()
    filas = []
    for (com, ele, sigla, fam), a in sorted(acum.items()):
        if not a["votos"]:
            continue
        h, cert, regla = resolver(r, com, ele, sigla, fam)
        shas = a["sha"]
        filas.append({"comunidad": com, "eleccion": ele, "sigla_fuente": sigla, "votos_fuente": a["votos"],
                      "familia_fuente": fam, "partido_homologado": h, "nivel_certeza": cert, "regla": regla,
                      "ruta_fuente": " ; ".join(sorted(shas)),
                      "sha256_fuente": hashlib.sha256(json.dumps(shas, sort_keys=True).encode()).hexdigest()})
    return filas


def escribir(filas: list[dict], destino: Path) -> None:
    with destino.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, CAMPOS, lineterminator="\n")
        w.writeheader()
        w.writerows(filas)


def comprobar(root: Path = ROOT) -> list[str]:
    errores, r, vistas = [], reglas(root), set()
    with (root / SALIDA).open(encoding="utf-8", newline="") as fh:
        for f in csv.DictReader(fh):
            k = (f["comunidad"], f["eleccion"], f["sigla_fuente"], f["familia_fuente"])
            if k in vistas:
                errores.append(f"clave repetida {k}")
            vistas.add(k)
            esperado = resolver(r, f["comunidad"], f["eleccion"], f["sigla_fuente"], f["familia_fuente"])
            if (f["partido_homologado"], f["nivel_certeza"], f["regla"]) != esperado:
                errores.append(f"{k}: tabla {(f['partido_homologado'], f['nivel_certeza'], f['regla'])} != reglas {esperado}")
    return errores


def dudosas(root: Path = ROOT) -> list[dict]:
    g: dict = defaultdict(lambda: {"siglas": set(), "comunidades": set(), "votos": 0})
    with (root / SALIDA).open(encoding="utf-8", newline="") as fh:
        for f in csv.DictReader(fh):
            if f["nivel_certeza"] in ("BAJA", "MEDIA"):
                x = g[(f["nivel_certeza"], f["partido_homologado"])]
                x["siglas"].add(f["sigla_fuente"])
                x["comunidades"].add(f["comunidad"])
                x["votos"] += int(f["votos_fuente"])
    return [{"nivel": n, "partido_homologado": p, "siglas": sorted(x["siglas"]), "comunidades": sorted(x["comunidades"]),
             "votos": x["votos"]} for (n, p), x in sorted(g.items(), key=lambda kv: (kv[0][0], -kv[1]["votos"]))]


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("modo", choices=["construir", "comprobar", "dudosas"])
    ap.add_argument("--obs-dir", type=Path)
    ap.add_argument("--comunidad", nargs="*")
    a = ap.parse_args(argv)
    if a.modo == "construir":
        filas = construir_filas(a.obs_dir, reglas(), set(a.comunidad or []))
        escribir(filas, ROOT / SALIDA)
        print(f"{len(filas)} filas → {SALIDA}")
        return 0
    if a.modo == "dudosas":
        for d in dudosas():
            print(json.dumps(d, ensure_ascii=False))
        return 0
    e = comprobar()
    print("OK" if not e else "\n".join(e))
    return 1 if e else 0


if __name__ == "__main__":
    sys.exit(main())
