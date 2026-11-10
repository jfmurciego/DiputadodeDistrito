#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Rotación 2011-2023 por distrito para el visor v2 (T-119).

PROYECTO: Diputado de Distrito
VERSIÓN: 1.0.0 · FECHA: 2026-11-09 · ESTADO: candidato
ANTERIOR: ninguna (fichero nuevo)
QUÉ HACE: lee datos/resultados/historico/rotacion/congreso_<t>.csv (T-110: ganador homologado por distrito y elección) y
  datos/composicion/congreso_<t>.csv (para el código de provincia, 2 primeras cifras de la sección) y escribe un único JSON
  {schema, elecciones, provincias: {cod: {territorio, sha256, distritos: [{d, g: [ganadores], c: cambios}]}}} con el sha256
  del CSV de origen de cada provincia. Solo copia datos existentes; no calcula votos.
Uso: python herramientas/generar_rotacion_visor.py --salida visor/v2/datos/rotacion.json [--rotacion DIR] [--composicion DIR]
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
ELECCIONES = ["201111", "201512", "201606", "201904", "201911", "202307"]


def generar(salida: Path, rotacion: Path, composicion: Path) -> int:
    provs: dict[str, dict] = {}
    for f in sorted(rotacion.glob("congreso_*.csv")):
        comp = composicion / f.name
        if not comp.exists():
            continue
        with comp.open(encoding="utf-8", newline="") as fh:
            cod = next(csv.DictReader(fh))["seccion"][:2]
        datos = f.read_bytes()
        filas = list(csv.DictReader(datos.decode("utf-8").splitlines()))
        if not filas or any(e not in filas[0] for e in ELECCIONES):
            raise SystemExit(f"{f.name}: faltan columnas de elecciones")
        provs[cod] = {"territorio": f.stem, "sha256": hashlib.sha256(datos).hexdigest(),
                      "distritos": [{"d": int(r["district_id"]), "g": [r[e] for e in ELECCIONES], "c": int(r["cambios"])} for r in filas]}
    if not provs:
        print("AVISO: sin datos de rotación; no se escribe nada.")
        return 0
    salida.parent.mkdir(parents=True, exist_ok=True)
    salida.write_text(json.dumps({"schema": "ddd.rotacion-visor/1.0", "elecciones": ELECCIONES, "provincias": provs},
                                 ensure_ascii=False, separators=(",", ":")), "utf-8")
    print(f"rotación de {len(provs)} provincias")
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--salida", type=Path, required=True)
    ap.add_argument("--rotacion", type=Path, default=RAIZ / "datos" / "resultados" / "historico" / "rotacion")
    ap.add_argument("--composicion", type=Path, default=RAIZ / "datos" / "composicion")
    a = ap.parse_args(argv)
    return generar(a.salida, a.rotacion, a.composicion)


if __name__ == "__main__":
    sys.exit(main())
