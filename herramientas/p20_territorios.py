#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Territorio del botón de P20 Distritos (T-377, D-139, D-148): del código al nombre del catálogo.

PROYECTO: Diputado de Distrito
VERSIÓN: 1.0.0
NOMBRE DE VERSIÓN: Territorios de P20 Distritos
FECHA: 2026-11-16
ESTADO: candidato
CAMBIOS: fichero nuevo (T-377).
ANTERIOR: ninguna (fichero nuevo)
QUÉ HACE: `territorio --territorio aut11 [--edicion 2025] [--root .]` valida UN código (D-148: uno por ejecución; varios a la vez,
  con P00) contra la tabla maestra (`ddd_core.territorio_ids`) y el catálogo de preparación (modo generación, con contrato) e imprime
  `{"codigo": "aut11", "nombre": "Extremadura"}`. `nombre` es el nombre del catálogo: el mismo valor que la 00 pasa a P20 como
  `territory_id` (`territory_name` del plan). Rechaza la variante 350 (D-76) como la 00. Un id del histórico por época
  (`<t>_hAAAA_MM`, D-149/D-150) se reconoce y solo pasa si el catálogo trae su contrato; si no, `P20_HISTORICO_SIN_CONTRATO`.
  Fallo cerrado: error por stderr (`::error::P20_…`) y rc 1; stdout solo lleva el resultado.
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
_HISTORICO = re.compile(r"^([a-z0-9]+)_h(\d{4})_(\d{2})$")  # histórico por época: `<t>_hAAAA_MM`


def _fila(root: Path, t: str, edicion: str) -> dict:
    import catalogo_preparacion as cp
    try:
        row = cp.resolve("generation", t, edicion, root / cp.CATALOG)
    except SystemExit as exc:  # el catálogo falla cerrado con SystemExit
        raise LookupError(str(exc)) from exc
    if row.get("territory_id") != t or not row.get("contract_path"):
        raise LookupError(t)
    return row


def territorio(root: Path, texto: str, edicion: str = "2025") -> dict:
    from ddd_core import territorio_ids as ids

    pedido = [x for x in re.split(r"[,\s]+", (texto or "").strip().lower()) if x]
    if not pedido:
        raise ValueError("P20_TERRITORIO_VACIO: indica un código (p. ej. aut11)")
    if len(pedido) > 1:
        raise ValueError(f"P20_UN_TERRITORIO: uno por ejecución (D-148); para varios, P00 ({', '.join(pedido)})")
    x = pedido[0]
    if not _TERR.match(x):
        raise ValueError(f"P20_TERRITORIO_INVALIDO: «{x}»")
    h = _HISTORICO.match(x)
    if h:
        try:
            base = ids.resolver_id(h.group(1))
        except (ids.IdTerritorioDesconocido, ids.IdReservado) as exc:
            raise ValueError(f"P20_TERRITORIO_DESCONOCIDO: {x} ({exc})") from exc
        t = f"{base}_h{h.group(2)}_{h.group(3)}"
        try:
            row = _fila(root, t, edicion)
        except LookupError as exc:
            raise ValueError(f"P20_HISTORICO_SIN_CONTRATO: {t} (el catálogo no trae su contrato)") from exc
        return {"codigo": t, "nombre": str(row["name"])}
    try:
        t = ids.resolver_id(x)
    except (ids.IdTerritorioDesconocido, ids.IdReservado) as exc:
        raise ValueError(f"P20_TERRITORIO_DESCONOCIDO: {x} ({exc})") from exc
    if ids.es_variante_350(t):
        raise ValueError(f"P20_VARIANTE_350_RETIRADA: {t} (D-76)")
    try:
        row = _fila(root, t, edicion)
    except LookupError as exc:
        raise ValueError(f"P20_SIN_CONTRATO: {t} ({exc})") from exc
    return {"codigo": t, "nombre": str(row["name"])}


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=(__doc__ or "").splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    m = sub.add_parser("territorio", help="código y nombre del catálogo de un territorio")
    m.add_argument("--root", default=".")
    m.add_argument("--territorio", required=True)
    m.add_argument("--edicion", default="2025")
    a = ap.parse_args(argv)
    try:
        print(json.dumps(territorio(Path(a.root), a.territorio, a.edicion), ensure_ascii=False, sort_keys=True))
    except (ValueError, OSError, KeyError) as exc:
        print(f"::error::{exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
