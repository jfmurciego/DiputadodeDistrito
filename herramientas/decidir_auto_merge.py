#!/usr/bin/env python3
"""Decide si una PR se fusiona automáticamente (T-54b).

PROYECTO: Diputado de Distrito
VERSIÓN: 1.0.0
NOMBRE DE VERSIÓN: Fusión solo con `pruebas` en success sobre el HEAD exacto
FECHA: 2026-11-07
ESTADO: candidato
CAMBIOS: versión inicial.
MOTIVO: auto-merge.yml 1.0.0 fusionó #453 y #454 sin `pruebas`: con el token de la app ddd-registro (actor exento del
  ruleset) la PR salía «clean» al instante y la rama «si ya está clean, fusiona» se saltaba el check obligatorio.
QUÉ HACE: con el JSON de la PR (GET pulls/<n>) y el de los check-runs `pruebas` del SHA (GET commits/<sha>/check-runs
  ?check_name=pruebas), devuelve FUSIONAR solo si la PR está abierta, no es borrador, va a main, sale del propio
  repositorio, no lleva `no-automerge`, su HEAD es el SHA evaluado y el último check-run `pruebas` de ese SHA está
  completed/success. Pendiente → ESPERAR; failure o cualquier otra cosa → NO. Nunca mira mergeable_state.
ANTERIOR: ninguna (fichero nuevo)

Uso: python herramientas/decidir_auto_merge.py --pr pr.json --checks checks.json --sha SHA --repo owner/repo
Salida: una línea JSON {"decision": "FUSIONAR|ESPERAR|NO", "motivo": "..."}; código 0 siempre.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

CHECK = "pruebas"
ETIQUETA = "no-automerge"


def decidir(pr: dict, checks: dict, sha: str, repo: str) -> dict:
    def r(decision, motivo):
        return {"decision": decision, "motivo": motivo}

    if pr.get("state") != "open" or pr.get("merged"):
        return r("NO", "la PR no está abierta")
    if pr.get("draft"):
        return r("NO", "borrador")
    if (pr.get("base") or {}).get("ref") != "main":
        return r("NO", "no va a main")
    if ((pr.get("head") or {}).get("repo") or {}).get("full_name") != repo:
        return r("NO", "sale de un fork")
    if ETIQUETA in {l.get("name") for l in pr.get("labels") or []}:
        return r("NO", f"etiqueta {ETIQUETA}")
    if (pr.get("head") or {}).get("sha") != sha:
        return r("NO", "el HEAD de la PR ya no es el SHA evaluado")
    runs = [c for c in (checks.get("check_runs") or [])
            if c.get("name") == CHECK and c.get("head_sha") == sha]
    if not runs:
        return r("ESPERAR", f"sin check-run {CHECK} para {sha[:10]}")
    ultimo = max(runs, key=lambda c: (c.get("started_at") or "", c.get("id") or 0))
    if ultimo.get("status") != "completed":
        return r("ESPERAR", f"{CHECK} {ultimo.get('status')} en {sha[:10]}")
    if ultimo.get("conclusion") != "success":
        return r("NO", f"{CHECK} {ultimo.get('conclusion')} en {sha[:10]}")
    return r("FUSIONAR", f"{CHECK} success en {sha[:10]}")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--pr", type=Path, required=True)
    ap.add_argument("--checks", type=Path, required=True)
    ap.add_argument("--sha", required=True)
    ap.add_argument("--repo", required=True)
    a = ap.parse_args(argv)
    res = decidir(json.loads(a.pr.read_text(encoding="utf-8")), json.loads(a.checks.read_text(encoding="utf-8")),
                  a.sha, a.repo)
    print(json.dumps(res, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
