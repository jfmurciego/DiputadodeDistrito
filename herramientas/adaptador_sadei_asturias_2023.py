#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Adaptador de las autonómicas de Asturias (28-05-2023) de SADEI a votos por municipio y partido (T-426).

PROYECTO: Diputado de Distrito
VERSIÓN: 1.0.0 · FECHA: 2026-11-20 · ESTADO: candidato
CAMBIOS: 1.0.0: fichero nuevo.
ANTERIOR: ninguna (fichero nuevo)
MOTIVO: aut03 no tenía votos por partido de su elección vigente (ficha T-421). SADEI publica, por concejo y completos, la tabla
  PxWeb 190426 «Elecciones autonómicas 2023. Votos a candidaturas» (Juntas electorales del Principado). Es nivel MUNICIPIO:
  el reparto a sección/distrito (aproximado_en_distrito, D-183) lo hace M07 después; este adaptador no reparte nada.
QUÉ HACE: verifica el sha256 del CSV exportado de PxWeb, lo pasa a `municipios.csv` (municipio INE de 5 cifras, partido, votos)
  y `MANIFEST.json`; comprueba que concejos + «Residentes ausentes» (voto exterior, declarado y no repartido) = fila ASTURIAS.
NO HACE: descargar, repartir a sección, lanzar ni publicar.
Uso: python herramientas/adaptador_sadei_asturias_2023.py --fuente CSV --salida DIR
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SHA256 = "197045e10fe0d2ada7170054371673340690d36846d85cb5b8b047226f248f06"
URL = "https://www.sadei.es/sadei/pxweb/es/01/19__04/190426.px/"


def _norm(s: str) -> str:
    s = unicodedata.normalize("NFD", s)
    return re.sub(r"[^a-z0-9]", "", "".join(c for c in s if unicodedata.category(c) != "Mn").lower())


def municipios_ine(raiz: Path = ROOT) -> dict[str, str]:
    with (raiz / "datos/distritos/municipios_ine_2025.csv").open(encoding="utf-8", newline="") as f:
        return {_norm(r["nombre_ine"]): r["codigo_ine"] for r in csv.DictReader(f) if r["codigo_ine"].startswith("33")}


def construir(fuente: Path, salida: Path, raiz: Path = ROOT) -> dict:
    h = hashlib.sha256(fuente.read_bytes()).hexdigest()
    if h != SHA256:
        raise ValueError(f"sha256 de SADEI no coincide: {h}")
    filas = [r for r in csv.reader(fuente.read_text(encoding="latin-1").splitlines()) if len(r) > 10 and not r[0].startswith("Ámbito")]
    cab = next(r for r in csv.reader(fuente.read_text(encoding="latin-1").splitlines()) if r and r[0].startswith("Ámbito"))
    nombres = [c.strip().strip('"') for c in cab[1:]]
    partidos = {i: n.split(" - ")[0][6:] for i, n in enumerate(nombres) if n.startswith("Votos ") and n != "Votos TOTAL"}
    if len(partidos) < 10:
        raise ValueError(f"cabecera SADEI inesperada: {len(partidos)} candidaturas")
    muni = municipios_ine(raiz)
    votos, ausentes, region = {}, {}, None
    for r in filas:
        nombre = r[0].strip()
        n = [int(x) if x.isdigit() else 0 for x in r[1:]]
        d = {partidos[i]: n[i] for i in partidos}
        if nombre == "ASTURIAS":
            region = {"total": n[0], **d}
        elif nombre.startswith("Circunscripci"):
            continue
        elif nombre.startswith("Residentes ausentes"):
            ausentes[nombre] = {"total": n[0], **d}
        else:
            if _norm(nombre) not in muni:
                raise ValueError(f"concejo sin código INE: {nombre!r}")
            votos[muni[_norm(nombre)]] = d
    salida.mkdir(parents=True, exist_ok=True)
    with (salida / "municipios.csv").open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["municipio", "partido", "votos"])
        for m in sorted(votos):
            for p, v in sorted(votos[m].items()):
                if v:
                    w.writerow([m, p, v])
    suma = {p: sum(v[p] for v in votos.values()) for p in partidos.values()}
    aus = {p: sum(a[p] for a in ausentes.values()) for p in partidos.values()}
    ok = all(suma[p] + aus[p] == region[p] for p in suma)
    man = {"schema": "ddd-sadei-asturias-2023/1.0", "territorio": "aut03", "eleccion": "202305", "nivel": "municipio",
           "aproximado_en_distrito": True, "fuente": {"url": URL, "sha256": h},
           "municipios": len(votos), "votos_municipios": suma, "votos_ausentes_no_repartidos": aus,
           "total_oficial": {p: region[p] for p in suma}, "cuadra_con_total_oficial": ok}
    (salida / "MANIFEST.json").write_text(json.dumps(man, ensure_ascii=False, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    if not ok:
        raise ValueError("no cuadra con el total oficial ASTURIAS")
    return man


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--fuente", type=Path, required=True)
    ap.add_argument("--salida", type=Path, required=True)
    a = ap.parse_args(argv)
    m = construir(a.fuente, a.salida)
    print(json.dumps({k: m[k] for k in ("municipios", "cuadra_con_total_oficial")}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
