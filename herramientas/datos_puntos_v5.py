#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Datos de la situación actual del Congreso 2023 (un punto por diputado) para el Explorar de la V4 (T-500, diseño T-499 1.0.1).

PROYECTO: Diputado de Distrito
VERSIÓN: 1.0.0 · FECHA: 2026-11-25 · ESTADO: candidato
CAMBIOS: 1.0.0: fichero nuevo.
MOTIVO: T-500, el visor V5 pinta los 350 escaños por provincia y el % de voto sobre votos a candidaturas; ese dato sale solo de ficheros con huella.
ANTERIOR: ninguna (fichero nuevo; parte de docs/ESTUDIOS/T499_v5/extraer_datos_v5.py)
QUÉ HACE: lee el XML de BOE-A-2023-18907 tras comprobar su sha256 contra configuracion/resultados_oficiales_congreso_2023.json, suma por
  circunscripción los votos a candidaturas de los cuadros II y III (el cuadro I, votos válidos, es una imagen en el XML: no se usa), los
  junta con los escaños y votos de configuracion/resultados_oficiales_congreso_2023.csv (huella también comprobada) y escribe
  visor/v4/mapa/puntos_v5_2023.json. Para (sin escribir) si una huella no casa, si no hay 52 circunscripciones, si los escaños no son 350,
  si la suma por circunscripción no es la fila «Total estatal» del BOE o si el cuadro II del XML (votos del PP y suma por fila) no coincide con el CSV.
Uso: python herramientas/datos_puntos_v5.py --documento BOE-A-2023-18907.xml            (comprueba que el JSON vigente es el que sale)
     python herramientas/datos_puntos_v5.py --documento BOE-A-2023-18907.xml --escribir (lo regenera)
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
sys.path.insert(0, str(Path(__file__).resolve().parent))
import resultados_oficiales_boe as boe  # noqa: E402  (ORDEN de circunscripciones)

META = ROOT / "configuracion/resultados_oficiales_congreso_2023.json"
CSV = ROOT / "configuracion/resultados_oficiales_congreso_2023.csv"
SALIDA = ROOT / "visor/v4/mapa/puntos_v5_2023.json"
DENOMINADOR = "votos a candidaturas (suma de los cuadros II y III por circunscripción; sin votos en blanco)"


def _num(s: str) -> int:
    return int(re.sub(r"[^0-9]", "", s) or 0)


def leer_tablas(texto: str) -> tuple[dict[str, dict], int]:
    """({nombre BOE: {"candidaturas": votos de los cuadros II y III, "pp": votos del PP, "cuadro2": votos del cuadro II}}, suma de «Total estatal»)."""
    por_nombre: dict[str, dict] = {}
    estatal = 0
    for tabla in re.findall(r"<table.*?</table>", texto, re.S):
        filas = [[html.unescape(re.sub("<[^>]+>", "", c)).strip() for c in re.findall(r"<t[dh].*?</t[dh]>", r, re.S)]
                 for r in re.findall(r"<tr.*?</tr>", tabla, re.S)]
        con_escanos = filas[1][1] == "Escaños"  # cuadro II: pares Votos/Escaños tras «Total escaños»; cuadro III: solo votos
        for f in filas[2:]:
            votos = [_num(v) for v in (f[2::2] if con_escanos else f[1:])]
            if f[0].startswith("Total estatal"):
                estatal += sum(votos)
                continue
            d = por_nombre.setdefault(f[0].rstrip(".").strip(), {"candidaturas": 0, "pp": 0, "cuadro2": 0})
            d["candidaturas"] += sum(votos)
            if con_escanos:
                d["cuadro2"] += sum(votos)
                d["pp"] = d["pp"] or votos[0]  # la primera columna del primer bloque del cuadro II es el PP
    return por_nombre, estatal


def generar(xml: bytes, csv_bytes: bytes, meta: dict) -> dict:
    """El JSON de los puntos; lanza ValueError con la causa si algo no cuadra."""
    if hashlib.sha256(xml).hexdigest() != meta["sha256_xml"]:
        raise ValueError("el XML no coincide con el sha256_xml de " + META.name)
    if hashlib.sha256(csv_bytes).hexdigest() != meta["sha256_csv"]:
        raise ValueError("el CSV no coincide con el sha256_csv de " + META.name)
    por_nombre, estatal = leer_tablas(xml.decode("utf-8"))
    if len(por_nombre) != 52 or sum(d["candidaturas"] for d in por_nombre.values()) != estatal:
        raise ValueError(f"{len(por_nombre)} circunscripciones y suma {sum(d['candidaturas'] for d in por_nombre.values())} frente a Total estatal {estatal}")
    filas = list(csv.DictReader(csv_bytes.decode("utf-8").splitlines()))
    provincias = {}
    # El BOE lista las circunscripciones en el orden de boe.ORDEN; cada fila se casa con el CSV por los votos del PP y la suma del cuadro II.
    for (cod, _), (nombre_boe, d) in zip(boe.ORDEN, por_nombre.items()):
        del_csv = [f for f in filas if f["codigo"] == cod]
        votos = {f["partido"]: int(f["votos"]) for f in del_csv}
        if votos.get("PP") != d["pp"] or sum(votos.values()) != d["cuadro2"]:
            raise ValueError(f"{nombre_boe}: el cuadro II del XML no coincide con el CSV de {cod}")
        esc = {int(f["escanos_circunscripcion"]) for f in del_csv}
        if len(esc) != 1 or sum(int(f["escanos"]) for f in del_csv) != next(iter(esc)):
            raise ValueError(f"{nombre_boe}: escaños por partido distintos de los de la circunscripción")
        if sum(votos.values()) > d["candidaturas"]:
            raise ValueError(f"{nombre_boe}: los votos de los partidos con escaño superan los votos a candidaturas")
        provincias[cod] = {
            "nombre": del_csv[0]["provincia"], "escanos": next(iter(esc)), "votos_candidaturas": d["candidaturas"],
            "partidos": sorted(({"p": f["partido"], "votos": int(f["votos"]), "escanos": int(f["escanos"])} for f in del_csv),
                               key=lambda x: (-x["escanos"], -x["votos"]))}
    if sum(p["escanos"] for p in provincias.values()) != 350:
        raise ValueError("los escaños no suman 350")
    return {"fuente": "BOE-A-2023-18907 (cuadros II y III)", "sha256_xml": meta["sha256_xml"],
            "csv": CSV.relative_to(ROOT).as_posix(), "sha256_csv": meta["sha256_csv"],
            "votos_candidaturas_estatal": estatal, "denominador": DENOMINADOR, "provincias": provincias}


def serializar(d: dict) -> bytes:
    return (json.dumps(d, ensure_ascii=False, indent=1) + "\n").encode("utf-8")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--documento", type=Path, required=True, help="XML de BOE-A-2023-18907 (https://www.boe.es/diario_boe/xml.php?id=BOE-A-2023-18907)")
    ap.add_argument("--escribir", action="store_true", help="escribe visor/v4/mapa/puntos_v5_2023.json (por defecto solo comprueba)")
    a = ap.parse_args(argv)
    try:
        nuevo = serializar(generar(a.documento.read_bytes(), CSV.read_bytes(), json.loads(META.read_text(encoding="utf-8"))))
    except ValueError as e:
        print("PARADA: " + str(e), file=sys.stderr)
        return 2
    if a.escribir:
        SALIDA.write_bytes(nuevo)
        print(f"escrito {SALIDA.relative_to(ROOT)} sha256 {hashlib.sha256(nuevo).hexdigest()}")
        return 0
    if not SALIDA.exists() or SALIDA.read_bytes() != nuevo:
        print("PARADA: puntos_v5_2023.json no es el que sale de los ficheros con huella (usa --escribir)", file=sys.stderr)
        return 1
    print(f"OK {SALIDA.relative_to(ROOT)} sha256 {hashlib.sha256(nuevo).hexdigest()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
