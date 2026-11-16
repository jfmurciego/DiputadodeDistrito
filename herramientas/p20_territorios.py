#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Territorios del botón de P20 Distritos (T-377, D-139): de los códigos a la matriz de un job por territorio.

PROYECTO: Diputado de Distrito
VERSIÓN: 1.0.0
NOMBRE DE VERSIÓN: Territorios de P20 Distritos
FECHA: 2026-11-16
ESTADO: candidato
CAMBIOS: fichero nuevo (T-377).
ANTERIOR: ninguna (fichero nuevo)
QUÉ HACE: `matriz --territorios aut11,nac42 [--edicion 2025] [--root .]` valida cada código contra la tabla maestra
  (`ddd_core.territorio_ids`) y el catálogo de preparación (modo generación, con contrato) e imprime la matriz
  `{"include": [{"codigo": "aut11", "nombre": "Extremadura"}, …]}`. `nombre` es el nombre del catálogo: el mismo valor que
  la 00 pasa a P20 como `territory_id` (`territory_name` del plan), así el grupo de concurrencia del territorio coincide.
  Rechaza la variante 350 (D-76) como la 00. Fallo cerrado: cualquier código inválido rechaza el lote, error por stderr
  (`::error::P20_…`) y rc 1; stdout solo lleva la matriz.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "herramientas"))

_TERR = re.compile(r"^[a-z0-9_]+$")


def matriz(root: Path, texto: str, edicion: str = "2025") -> dict:
    from ddd_core import territorio_ids as ids
    import catalogo_preparacion as cp

    pedido = [x for x in re.split(r"[,\s]+", (texto or "").strip().lower()) if x]
    if not pedido:
        raise ValueError("P20_TERRITORIOS_VACIO: indica códigos (p. ej. aut11,nac42)")
    filas: list[dict] = []
    for x in pedido:
        if not _TERR.match(x):
            raise ValueError(f"P20_TERRITORIO_INVALIDO: «{x}»")
        try:
            t = ids.resolver_id(x)
        except (ids.IdTerritorioDesconocido, ids.IdReservado) as exc:
            raise ValueError(f"P20_TERRITORIO_DESCONOCIDO: {x} ({exc})") from exc
        if ids.es_variante_350(t):
            raise ValueError(f"P20_VARIANTE_350_RETIRADA: {t} (D-76)")
        try:
            row = cp.resolve("generation", t, edicion, root / cp.CATALOG)
        except SystemExit as exc:  # el catálogo falla cerrado con SystemExit
            raise ValueError(f"P20_SIN_CONTRATO: {t} ({exc})") from exc
        if row.get("territory_id") != t or not row.get("contract_path"):
            raise ValueError(f"P20_SIN_CONTRATO: {t}")
        if t not in [f["codigo"] for f in filas]:
            filas.append({"codigo": t, "nombre": str(row["name"])})
    return {"include": filas}


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=(__doc__ or "").splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    m = sub.add_parser("matriz", help="matriz de un job por territorio")
    m.add_argument("--root", default=".")
    m.add_argument("--territorios", required=True)
    m.add_argument("--edicion", default="2025")
    a = ap.parse_args(argv)
    try:
        print(json.dumps(matriz(Path(a.root), a.territorios, a.edicion), ensure_ascii=False, sort_keys=True))
    except (ValueError, OSError, KeyError) as exc:
        print(f"::error::{exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
