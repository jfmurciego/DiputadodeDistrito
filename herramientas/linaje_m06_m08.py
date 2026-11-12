#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Linaje M06/M08 de un territorio publicado (T-249).

PROYECTO: Diputado de Distrito
VERSIÓN: 1.0.0 · FECHA: 2026-11-11 · ESTADO: candidato
ANTERIOR: ninguna (fichero nuevo)
QUÉ HACE: publicar un territorio es registrar el PAR: canonical_m06 (00 territorial) y canonical_m08 (00 electoral de la
  misma cadena, a menudo «Reutilizar» del bot con otro run_id). Un M08 es del linaje de un M06 si comparten run o si el
  manifiesto del run del M08 (territorios/<t>/evidencia/ejecuciones_completas/<run>.json) acredita que su 02 es el run del
  M06 y su 04 es el propio run en success (mismo criterio que el dashboard, #354).
MOTIVO: el lote P50 43030563528 registró solo los M06 de 34 territorios; el visor mostraba mapas nuevos con resultados de
  otro linaje y datos abiertos borró esos territorios.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "herramientas"))
import resultados_ligeros as rl  # noqa: E402
import sys as _sys_t220  # noqa: E402
from pathlib import Path as _Path_t220  # noqa: E402
if str(_Path_t220(__file__).resolve().parents[1]) not in _sys_t220.path:
    _sys_t220.path.insert(0, str(_Path_t220(__file__).resolve().parents[1]))
from ddd_core.territorio_ids import mismo_territorio  # noqa: E402  (T-220: id viejo o nuevo)


def m06_run_acreditado(m08_run: object, territorio: str, root: Path = ROOT) -> str | None:
    """Run del M06 que consumió la 04 del run `m08_run`, según su manifiesto; None si no lo acredita."""
    ruta = root / "territorios" / territorio / "evidencia" / "ejecuciones_completas" / f"{m08_run}.json"
    try:
        man = json.loads(ruta.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    fases = {str(p.get("name", ""))[:2]: p for p in man.get("phases") or [] if isinstance(p, dict)}
    f02, f04 = fases.get("02") or {}, fases.get("04") or {}
    if str(f04.get("run_id")) != str(m08_run) or f04.get("result") != "success" or not f02.get("run_id"):
        return None
    return str(f02["run_id"])


def m06_del_m08(products: list[dict], p8: dict, root: Path = ROOT) -> dict | None:
    """canonical_m06 del linaje de `p8` (mismo territorio y elección): el de su run o el acreditado por su manifiesto."""
    t, elec = p8["territory_id"], rl.eleccion_de(p8)
    m6 = {str(p["run_id"]): p for p in products
          if p.get("kind") == "canonical_m06" and mismo_territorio(str(p.get("territory_id") or ""), str(t)) and rl.eleccion_de(p) == elec}
    run = str(p8["run_id"])
    if run in m6:
        return m6[run]
    acreditado = m06_run_acreditado(run, t, root)
    return m6.get(acreditado) if acreditado else None


def pares_incompletos(products: list[dict], claves: set[tuple[str, str]], root: Path = ROOT) -> list[str]:
    """Para cada (territorio, elección): el M08 vigente debe existir y ser del linaje del M06 vigente."""
    err = []
    for t, elec in sorted(claves):
        p6 = rl.vigente_por_eleccion(products, "canonical_m06", elec).get(t)
        p8 = rl.vigente_por_eleccion(products, "canonical_m08", elec).get(t)
        if not p6:
            continue
        if not p8:
            err.append(f"{t} ({elec}): M06 {p6['run_id']} sin M08")
            continue
        m6 = m06_del_m08(products, p8, root)
        if not m6 or m6.get("run_id") != p6.get("run_id"):
            err.append(f"{t} ({elec}): M08 {p8['run_id']} no es del linaje del M06 {p6['run_id']}")
    return err
