#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Resolutor de P40 Publicación (T-372, D-134): de los códigos de territorio a los runs de la 00 que se publican.

PROYECTO: Diputado de Distrito
VERSIÓN: 1.1.0
NOMBRE DE VERSIÓN: Resolutor de P40 Publicación
FECHA: 2026-11-21
ESTADO: candidato
CAMBIOS 1.1.0 (T-379 3c-ii, opción A del Planificador del 20-11): cada territorio busca SOLO su registro del run
  (`resolver(root, run, territorio)`); en una campaña de P00 todos los territorios comparten run y su M08 lleva el espacio
  `campaign-<run>-<intento>--<hueco>--<territorio>`: el lote da entonces el par `<run>:<espacio>` (uno por territorio). Una 00 sin
  espacio da el run a secas, como en la 1.0.0.
ANTERIOR (1.0.0): legacy/herramientas/p40_resolver_v1.0.0_20261121.py
CAMBIOS 1.0.0: fichero nuevo (T-372).
QUÉ HACE: `territorios --territorios aut01,nac42 [--root .]` toma, de cada territorio, la ÚLTIMA 00 completa (status SUCCESS) cuya puerta 04 está en
  verde en `territorios/<id>/evidencia/ejecuciones_completas/<run>.json` (misma validación que `resolver_cadena_publicacion.py`; si fue «Reutilizar»
  se publica el run origen de la 04). Imprime un JSON con `production_run_ids` (separados por espacios; todo o nada: un territorio sin run válido
  rechaza el lote) y el detalle; `descartadas` lista, por territorio, las 00 más recientes que la elegida y se saltaron (con su motivo). Los errores salen por stderr (`::error::P40_…`) con rc 1; stdout solo lleva el resultado.
  No descarga ni exige artefactos de Actions: el M06 sale del blob del registro (D-133).
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
_CAMPANA = re.compile(r"^campaign-(?P<run>[0-9]+)-[1-9][0-9]*--(?P<hueco>[0-9]{2})--(?P<t>[a-z0-9_]+)$")


def elemento_lote(r: dict, territorio: str) -> str:
    """`<run>` (00 de siempre) o `<run>:<espacio>` si el M08 es de una campaña (espacio del mismo run y territorio)."""
    run, art = str(r["publish_run_id"]), str(r.get("m08_artifact") or "")
    base = f"ddd-state-{run}-M08-"
    ns = art[len(base):] if art.startswith(base) else ""
    m = _CAMPANA.match(ns)
    if not m:
        return run  # 00 de siempre: el run a secas, como en la 1.0.0
    if m.group("run") != run or m.group("t") != territorio or m.group("hueco") == "00":
        raise ValueError(f"P40_ESPACIO_DE_CAMPANA_AJENO: {territorio}: {art}")
    return f"{run}:{ns}"


def _candidatos(root: Path, territorio: str) -> list[str]:
    d = root / "territorios" / territorio / "evidencia" / "ejecuciones_completas"
    return sorted((p.stem for p in d.glob("*.json") if p.stem.isdigit()), key=int, reverse=True)


def ultima_valida(root: Path, territorio: str) -> dict:
    from resolver_cadena_publicacion import resolver
    vistos: list[str] = []
    descartadas: list[dict] = []
    for run in _candidatos(root, territorio):
        r = resolver(root, run, territorio)
        if r["status"] == "READY":
            r["descartadas"] = descartadas  # las 00 MÁS RECIENTES que la elegida y se saltaron (no se publican en silencio)
            return r
        vistos.append(f"{run}:{'+'.join(r['reasons'])}")
        descartadas.append({"run": run, "motivo": "+".join(r["reasons"])})
    raise ValueError(f"P40_SIN_00_VALIDA: {territorio} no tiene ninguna 00 completa con la puerta 04 en verde"
                     + (f" (vistas: {', '.join(vistos[:3])})" if vistos else ""))


def territorios(root: Path, texto: str) -> dict:
    from ddd_core import territorio_ids as ids
    pedido = [x for x in re.split(r"[,\s]+", (texto or "").strip().lower()) if x]
    if not pedido:
        raise ValueError("P40_TERRITORIOS_VACIO: indica códigos (p. ej. aut01,nac42)")
    sel: dict[str, dict] = {}
    for x in pedido:
        if not _TERR.match(x):
            raise ValueError(f"P40_TERRITORIO_INVALIDO: «{x}»")
        try:
            t = ids.resolver_id(x)
        except (ids.IdTerritorioDesconocido, ids.IdReservado) as exc:
            raise ValueError(f"P40_TERRITORIO_DESCONOCIDO: {x} ({exc})") from exc
        if ids.es_variante_350(t):
            raise ValueError(f"P40_VARIANTE_350_NO_SE_PUBLICA: {t}")
        sel[t] = ultima_valida(root, t)
    runs: list[str] = []
    for t, r in sel.items():
        e = elemento_lote(r, t)
        if e not in runs:
            runs.append(e)
    return {
        "production_run_ids": " ".join(runs),
        "territorios": [{"territory_id": t, "run_00": r["requested_run_id"], "publish_run_id": r["publish_run_id"],
                         "m08_artifact": r["m08_artifact"], "descartadas": r["descartadas"]}
                        for t, r in sorted(sel.items())],
    }


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=(__doc__ or "").splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    t = sub.add_parser("territorios", help="últimos runs 00 válidos de los territorios")
    t.add_argument("--root", default=".")
    t.add_argument("--territorios", required=True)
    a = ap.parse_args(argv)
    try:
        print(json.dumps(territorios(Path(a.root), a.territorios), ensure_ascii=False, sort_keys=True))
    except (ValueError, OSError, KeyError, json.JSONDecodeError) as exc:
        print(f"::error::{exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
