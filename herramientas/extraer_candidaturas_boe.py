#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Extrae del BOE las candidaturas proclamadas al Congreso (generales 2026) a CSV con fuente y sha256 (T-112).

PROYECTO: Diputado de Distrito
VERSIÓN: 1.0.0 · FECHA: 2026-11-08 · ESTADO: candidato
ANTERIOR: ninguna (fichero nuevo)
QUÉ HACE: lee el XML del BOE (verifica su sha256 declarado), recorre una Junta Electoral Provincial por bloque
  «CONGRESO DE LOS DIPUTADOS», y escribe una fila por candidatura (provincia, orden, denominación, siglas, nº de
  candidatos y suplentes). Aplica las correcciones de errores que cambian el nombre de una candidatura (BOE-A-2026-23383:
  Navarra). Solo texto oficial; nada de memoria. Topónimos en español (por código de provincia).
Uso: python herramientas/extraer_candidaturas_boe.py --xml BOE-A-2026-23103.xml --corr BOE-A-2026-23383.xml
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import html
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SALIDA = "configuracion/candidaturas_congreso_2026.csv"
SALIDA_JSON = "configuracion/candidaturas_congreso_2026.json"
BOE = {"id": "BOE-A-2026-23103", "sha256_xml": "8513892de37cadae53fac1a61428059c2783dd61d0d3df85c25e8b6ded8f276d",
       "fecha_publicacion": "2026-11-03"}
CORR = {"id": "BOE-A-2026-23383", "sha256_xml": "4c9ada8dd9b83b43dbf045ccb28258d8f19e0912e11c6c2c1b09f5b8d77dba85",
        "fecha_publicacion": "2026-11-07"}
COLUMNAS = ["codigo", "provincia", "orden", "denominacion", "siglas", "proclamada", "candidatos", "suplentes"]
# Junta (mayúsculas del BOE, sin tildes) → código de provincia (configuracion/escanos_oficiales_congreso_2026.csv).
ALIAS = {"ILLES BALEARS": "07", "BIZKAIA": "48", "GIPUZKOA": "20", "GIRONA": "17", "LLEIDA": "25", "A CORUNA": "15",
         "OURENSE": "32", "ALAVA": "01", "VALENCIA": "46", "LAS PALMAS": "35"}


def sha256(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def _sin_tildes(s: str) -> str:
    return s.upper().translate(str.maketrans("ÁÉÍÓÚÜÑ", "AEIOUUN"))


def provincias(root: Path = ROOT) -> dict[str, tuple[str, str]]:
    d = {}
    with (root / "configuracion/escanos_oficiales_congreso_2026.csv").open(encoding="utf-8", newline="") as fh:
        rd = csv.DictReader(l for l in fh if not l.startswith("#"))
        for r in rd:
            d[_sin_tildes(r["provincia"])] = (r["codigo"], r["provincia"])
    return d


def parrafos(xml: str) -> list[tuple[str, str]]:
    return [(c, re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", "", x))).strip())
            for c, x in re.findall(r'<p class="([^"]*)"[^>]*>(.*?)</p>', xml, re.S)]


def extraer(xml: str, provs: dict, nombres: dict[tuple[str, str], str] | None = None) -> list[dict]:
    nombres = nombres or {}
    nom = {c: n for _, (c, n) in provs.items()}
    junta, seccion, filas, cur, suplentes = None, None, [], None, False
    for c, x in parrafos(xml):
        if c == "centro_negrita" and x.upper().startswith("JUNTA ELECTORAL"):
            j = _sin_tildes(re.sub(r"^JUNTA ELECTORAL (PROVINCIAL )?DE ", "", x.upper()))
            cod = ALIAS.get(j) or (provs[j][0] if j in provs else None)
            if cod is None:
                raise ValueError(f"Junta sin provincia: {x!r}")
            junta, seccion = cod, None
        elif c == "centro_cursiva":
            seccion, cur = x, None
        elif c == "centro_redonda" and seccion == "CONGRESO DE LOS DIPUTADOS":
            m = re.fullmatch(r"(\d+)\. (.+) \((.+)\)", x)
            if not m:  # candidato con la clase de párrafo de las candidaturas (BOE)
                if cur is not None and re.match(r"\d+\. ", x):
                    cur["suplentes" if suplentes else "candidatos"] += 1
                    continue
                raise ValueError(f"candidatura ilegible: {x!r}")
            o, den, sig = int(m[1]), m[2], m[3]
            den = nombres.get((junta, str(o)), den)
            cur = {"codigo": junta, "provincia": nom[junta], "orden": o, "denominacion": den, "siglas": sig, "proclamada": "SI",
                   "candidatos": 0, "suplentes": 0}
            filas.append(cur)
            suplentes = False
        elif cur is not None and seccion == "CONGRESO DE LOS DIPUTADOS" and c in ("parrafo", "parrafo_2"):
            if x.startswith("No proclamada"):
                cur["proclamada"] = "NO"
            elif x.startswith("Suplente") and x.endswith(":"):
                suplentes = True
            elif x.startswith("Suplente"):
                cur["suplentes"] += 1
            elif re.match(r"\d+\. ", x):
                cur["suplentes" if suplentes else "candidatos"] += 1
    return filas


def corregir_siglas(filas: list[dict]) -> None:
    """Correcciones de BOE-A-2026-23383 que cambian la denominación de una candidatura de Congreso (Navarra)."""
    for r in filas:
        if r["codigo"] == "31" and r["siglas"] == "EH BILDU-ERC":
            r["denominacion"], r["siglas"] = "EUSKAL HERRIA BILDU", "EH BILDU"
        if r["codigo"] == "31" and r["siglas"] == "FRENTE AMPLIO-FRONTE ZABALA":
            r["denominacion"] = "FRENTE AMPLIO-FRONTE ZABALA"


def corregir_cifras(filas: list[dict]) -> None:
    """BOE-A-2026-23383, La Rioja (Congreso): la candidatura del PCTE pasa a 4 candidatos y 1 suplente."""
    for r in filas:
        if r["codigo"] == "26" and r["siglas"] == "PCTE":
            r["candidatos"], r["suplentes"] = 4, 1


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--xml", required=True, type=Path)
    ap.add_argument("--corr", required=True, type=Path)
    a = ap.parse_args(argv)
    bx, cx = a.xml.read_bytes(), a.corr.read_bytes()
    if sha256(bx) != BOE["sha256_xml"] or sha256(cx) != CORR["sha256_xml"]:
        print("ERROR sha256 del XML distinto al declarado")
        return 1
    provs = provincias()
    filas = extraer(bx.decode("utf-8"), provs)
    corregir_siglas(filas)
    corregir_cifras(filas)
    if {r["codigo"] for r in filas} != {c for c, _ in provs.values()}:
        print("ERROR faltan provincias:", {c for c, _ in provs.values()} - {r["codigo"] for r in filas})
        return 1
    filas.sort(key=lambda r: (r["codigo"], r["orden"]))
    out = ROOT / SALIDA
    with out.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=COLUMNAS, lineterminator="\n")
        w.writeheader()
        w.writerows(filas)
    doc = {"fuente": "Candidaturas proclamadas para las elecciones al Congreso de los Diputados y al Senado, RD 806/2026, de 5 de octubre (Juntas Electorales Provinciales)",
           "boe": BOE["id"], "url": f"https://www.boe.es/diario_boe/xml.php?id={BOE['id']}",
           "fecha_publicacion": BOE["fecha_publicacion"], "sha256_xml": BOE["sha256_xml"],
           "correccion": {"boe": CORR["id"], "url": f"https://www.boe.es/diario_boe/xml.php?id={CORR['id']}",
                          "fecha_publicacion": CORR["fecha_publicacion"], "sha256_xml": CORR["sha256_xml"],
                          "aplicada": "Navarra: EH BILDU-ERC → EH BILDU; FRENTE AMPLIO-FRONTE ZABALA (denominación). La Rioja: PCTE 4 candidatos y 1 suplente. Las demás correcciones de Congreso son de nombres de personas."},
           "sha256_csv": sha256(out.read_bytes()), "filas": len(filas), "provincias": len({r['codigo'] for r in filas})}
    (ROOT / SALIDA_JSON).write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(doc["filas"], "candidaturas,", doc["provincias"], "provincias")
    return 0


if __name__ == "__main__":
    sys.exit(main())
