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
  - Botón (`--territorio`): un código autNN o nacNN (o `<t>_hAAAA_MM`, histórico por época con su contrato en `configuracion/historico_epoca/`), resuelto con el catálogo a su id CANÓNICO (el código; grupo `ddd-electoral-prod-<id>`; coincide con P10 y P20 al entrar #874 y #880); se rechazan varios, ids viejos, alias y `congreso350_*`.
  - Llamada (`--territory-id`): un solo territorio; lo que llega (nombre del catálogo, «12 Galicia» o código) se resuelve al mismo id canónico, así código y nombre dan el mismo grupo.
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
_COD = re.compile(r"^(aut|nac)\d\d(_h\d{4}_\d{2})?$")  # solo ids canónicos: ni ids viejos (congreso_alava…), ni alias, ni congreso350_* (D-76)


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
    base, _, epoca = x.partition("_h")
    if epoca and not (ROOT / "configuracion" / "historico_epoca" / f"contrato_{epoca}.json").is_file():
        raise ValueError(f"P30_EPOCA_SIN_CONTRATO: {x} (no existe configuracion/historico_epoca/contrato_{epoca}.json)")
    try:
        t = ids.resolver_id(base)
        if ids.es_variante_350(t):
            raise ValueError(f"P30_VARIANTE_350_NO_SE_PUBLICA: {t}")
        canonico = cat.lookup(t, edicion)["territory_id"]
        return f"{canonico}_h{epoca}" if epoca else canonico  # id CANÓNICO (código); histórico por época: `<t>_hAAAA_MM`
    except (ids.IdTerritorioDesconocido, ids.IdReservado, SystemExit) as exc:
        raise ValueError(f"P30_TERRITORIO_DESCONOCIDO: {x} ({exc})") from exc


def canonico_de(selector: str, edicion: str) -> str:
    """Id canónico de lo que llega por la llamada (la 00 pasa el nombre del catálogo; vale también el código o «12 Galicia»): un solo grupo por territorio."""
    import catalogo_preparacion as cat
    try:
        return cat.lookup(selector.strip(), edicion)["territory_id"]
    except SystemExit as exc:
        raise ValueError(f"P30_TERRITORIO_DESCONOCIDO: {selector!r} ({exc})") from exc


def resolver(territorio: str, territory_id: str, edicion: str, persistir: str) -> dict:
    if bool(territorio) == bool(territory_id):
        raise ValueError("P30_ENTRADA: indica `territorio` (botón) o `territory-id` (llamada), uno solo")
    ed = (edicion or "").strip() or EDICION
    per = (persistir or "").strip().lower()
    per = "true" if per in ("", "null") else per  # el botón no tiene `persist_state`: toJSON(null) = «null» → registra
    if per not in ("true", "false"):
        raise ValueError(f"P30_PERSISTIR_INVALIDO: «{persistir}»")
    return {"territorio": por_codigo(territorio, ed) if territorio else canonico_de(territory_id, ed), "edicion": ed, "persistir": per}


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
