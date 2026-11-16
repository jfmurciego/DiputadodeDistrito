#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Resolutor de P30 Resultados electorales (T-376, D-137): del botón o de la llamada de la 00 a la matriz de territorios.

PROYECTO: Diputado de Distrito
VERSIÓN: 1.0.0
NOMBRE DE VERSIÓN: Resolutor de P30 Resultados electorales
FECHA: 2026-11-16
ESTADO: candidato
CAMBIOS: fichero nuevo (T-376).
ANTERIOR: ninguna (fichero nuevo)
QUÉ HACE: `resolver --territorio aut12 | --territory-id <selector> [--edicion 2025] [--persistir true|false] [--root .]` imprime un JSON
  `{"territorio":…, "edicion":…, "persistir":…}` para P30 (UN territorio por ejecución, D-148; varios en paralelo los da P00).
  - Botón (`--territorio`): un código autNN o nacNN, resuelto con el catálogo a su nombre visible (el mismo que pasa la 00 a la incorporación, por lo que el
    grupo `ddd-electoral-prod-<territorio>` excluye igual que antes); se rechazan varios, ids viejos, alias y `congreso350_*`.
  - Llamada (`--territory-id`): un solo territorio, TAL CUAL llega (la 00 pasa su nombre).
  - `edicion` vacía = 2025 (fijada en el código). `persistir` vacío o «null» (toJSON de la entrada ausente del botón) = true (el botón siempre registra; la llamada pasa su valor).
Errores a stderr con `::error::` y rc 1; nada en la salida.
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

EDICION = "2025"
_COD = re.compile(r"^(aut|nac)\d\d$")  # solo ids canónicos: ni ids viejos (congreso_alava…), ni alias, ni congreso350_* (D-76)


def por_codigo(texto: str, edicion: str = EDICION) -> str:
    from ddd_core import territorio_ids as ids
    import catalogo_preparacion as cat
    pedido = [x for x in re.split(r"[,\s]+", (texto or "").strip().lower()) if x]
    if not pedido:
        raise ValueError("P30_TERRITORIO_VACIO: indica un código (p. ej. aut12)")
    if len(pedido) > 1:
        raise ValueError("P30_UN_TERRITORIO: el botón admite UN territorio por ejecución (D-148); varios en paralelo los da P00")
    x = pedido[0]
    if not _COD.match(x):
        raise ValueError(f"P30_TERRITORIO_INVALIDO: «{x}» (solo códigos autNN o nacNN; los «Congreso 350» y los ids viejos no se aceptan)")
    try:
        t = ids.resolver_id(x)
        if ids.es_variante_350(t):
            raise ValueError(f"P30_VARIANTE_350_NO_SE_PUBLICA: {t}")
        return cat.lookup(t, edicion)["name"]
    except (ids.IdTerritorioDesconocido, ids.IdReservado, SystemExit) as exc:
        raise ValueError(f"P30_TERRITORIO_DESCONOCIDO: {x} ({exc})") from exc


def resolver(territorio: str, territory_id: str, edicion: str, persistir: str) -> dict:
    if bool(territorio) == bool(territory_id):
        raise ValueError("P30_ENTRADA: indica `territorio` (botón) o `territory-id` (llamada), uno solo")
    ed = (edicion or "").strip() or EDICION
    per = (persistir or "").strip().lower()
    per = "true" if per in ("", "null") else per  # el botón no tiene `persist_state`: toJSON(null) = «null» → registra
    if per not in ("true", "false"):
        raise ValueError(f"P30_PERSISTIR_INVALIDO: «{persistir}»")
    return {"territorio": por_codigo(territorio, ed) if territorio else territory_id.strip(), "edicion": ed, "persistir": per}


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=(__doc__ or "").splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    m = sub.add_parser("resolver", help="territorio, edición y registro de P30")
    m.add_argument("--root", default=".")
    m.add_argument("--territorio", default="")
    m.add_argument("--territory-id", default="")
    m.add_argument("--edicion", default="")
    m.add_argument("--persistir", default="")
    a = ap.parse_args(argv)
    try:
        print(json.dumps(resolver(a.territorio, a.territory_id, a.edicion, a.persistir), ensure_ascii=False, sort_keys=True))
    except (ValueError, OSError, KeyError) as exc:
        print(f"::error::{exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
