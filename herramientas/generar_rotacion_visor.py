#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Rotación 2011-2023 por distrito para el visor v2 (T-119).

PROYECTO: Diputado de Distrito
VERSIÓN: 1.1.1 · FECHA: 2026-11-12 · ESTADO: candidato
CAMBIOS 1.1.1 (T-220): ids de territorio nuevos de la tabla maestra (aut01…nac52, D-61); el id viejo se lee vía ddd_core.territorio_ids.
ANTERIOR: legacy/herramientas/generar_rotacion_visor_v1.1.0_20261112.py
CAMBIOS 1.1.0 (T-135): el número de distrito sale en numeración pública 1..K (no existe el 0).
QUÉ HACE: lee datos/resultados/historico/rotacion/<circunscripción NAC>.csv (T-110: ganador homologado por distrito y elección) y
  datos/composicion/<circunscripción NAC>.csv (para el código de provincia, 2 primeras cifras de la sección) y escribe un único JSON
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
import sys as _sys
_RAIZ = str(Path(__file__).resolve().parents[1])
if _RAIZ not in _sys.path:
    _sys.path.insert(0, _RAIZ)
from ddd_core import territorio_ids  # noqa: E402  (T-220: ámbito e ids por el resolutor, nunca por prefijo)

sys.path.insert(0, str(Path(__file__).resolve().parent))
from numeracion_publica import numero_publico  # noqa: E402

RAIZ = Path(__file__).resolve().parent.parent
ELECCIONES = ["201111", "201512", "201606", "201904", "201911", "202307"]


def generar(salida: Path, rotacion: Path, composicion: Path) -> int:
    provs: dict[str, dict] = {}
    for f in sorted(f for f in rotacion.glob("*.csv") if territorio_ids.es_nacional(f.stem)):
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
                      "distritos": [{"d": numero_publico(r["district_id"]), "g": [r[e] for e in ELECCIONES], "c": int(r["cambios"])} for r in filas]}
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
