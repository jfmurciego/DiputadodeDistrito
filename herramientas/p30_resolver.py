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
QUÉ HACE: `matriz --territorios aut12,nac42 | --territory-id <selector> [--edicion 2025] [--persistir true|false] [--root .]` imprime un JSON
  `{"include":[{"territorio":…,"namespace":…}], "edicion":…, "persistir":…}` para la matriz de P30 (un job por territorio).
  - Botón (`--territorios`): cada código (autNN, nacNN, alias) se resuelve con el catálogo a su nombre visible (el mismo que pasa la 00 a la
    incorporación, por lo que el grupo `ddd-electoral-prod-<territorio>` excluye igual que antes); duplicados se quitan; vacío o desconocido → error.
    Con más de un territorio el `namespace` de los artefactos es el id canónico (en una misma ejecución no pueden chocar dos `ddd-state-<run>-M08`);
    con uno queda vacío (como hoy).
  - Llamada (`--territory-id`): un solo territorio, TAL CUAL llega (la 00 pasa su nombre); `namespace` vacío (el de la llamada va aparte).
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
_COD = re.compile(r"^[a-z0-9_]+$")


def por_codigos(texto: str, edicion: str = EDICION) -> list[dict]:
    from ddd_core import territorio_ids as ids
    import catalogo_preparacion as cat
    pedido = [x for x in re.split(r"[,\s]+", (texto or "").strip().lower()) if x]
    if not pedido:
        raise ValueError("P30_TERRITORIOS_VACIO: indica códigos separados por comas (p. ej. aut12,nac42)")
    vistos: dict[str, str] = {}
    for x in pedido:
        if not _COD.match(x):
            raise ValueError(f"P30_TERRITORIO_INVALIDO: «{x}»")
        try:
            t = ids.resolver_id(x)
            fila = cat.lookup(t, edicion)
        except (ids.IdTerritorioDesconocido, ids.IdReservado, SystemExit) as exc:
            raise ValueError(f"P30_TERRITORIO_DESCONOCIDO: {x} ({exc})") from exc
        vistos.setdefault(fila["territory_id"], fila["name"])
    unico = len(vistos) == 1
    return [{"territorio": n, "namespace": "" if unico else i} for i, n in sorted(vistos.items())]


def matriz(territorios: str, territory_id: str, edicion: str, persistir: str, root: Path | None = None) -> dict:
    if bool(territorios) == bool(territory_id):
        raise ValueError("P30_ENTRADA: indica `territorios` (botón) o `territory-id` (llamada), uno solo")
    ed = (edicion or "").strip() or EDICION
    per = (persistir or "").strip().lower()
    per = "true" if per in ("", "null") else per  # el botón no tiene `persist_state`: toJSON(null) = «null» → registra
    if per not in ("true", "false"):
        raise ValueError(f"P30_PERSISTIR_INVALIDO: «{persistir}»")
    inc = por_codigos(territorios, ed) if territorios else [{"territorio": territory_id.strip(), "namespace": ""}]
    if not all(i["territorio"] for i in inc):
        raise ValueError("P30_TERRITORIO_VACIO")
    return {"include": inc, "edicion": ed, "persistir": per}


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=(__doc__ or "").splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    m = sub.add_parser("matriz", help="matriz de territorios de P30")
    m.add_argument("--root", default=".")
    m.add_argument("--territorios", default="")
    m.add_argument("--territory-id", default="")
    m.add_argument("--edicion", default="")
    m.add_argument("--persistir", default="")
    a = ap.parse_args(argv)
    try:
        print(json.dumps(matriz(a.territorios, a.territory_id, a.edicion, a.persistir), ensure_ascii=False, sort_keys=True))
    except (ValueError, OSError, KeyError) as exc:
        print(f"::error::{exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
