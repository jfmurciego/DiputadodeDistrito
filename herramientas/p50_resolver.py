#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Resolutor de P50 Publicación académica (T-370, D-133): territorios, M06 del visor y versión automática.

PROYECTO: Diputado de Distrito
VERSIÓN: 1.0.0
NOMBRE DE VERSIÓN: Resolutor de P50 Publicación académica
FECHA: 2026-11-16
ESTADO: candidato
CAMBIOS: 1.0.0: fichero nuevo (T-370).
ANTERIOR: ninguna (fichero nuevo)
QUÉ HACE: `ultima --tags FICHERO` imprime la última etiqueta `mapas-v<X.Y.Z>` (vacío si no hay).
  `plan --territorios T --tags FICHERO [--previo MAPAS.json]` resuelve cada territorio a su M06 vigente de
  `orchestracion/publicaciones_visor.json` (blob + sha256; «todos» = los publicados) y da la versión: 1.0.0 la primera;
  sube la menor si el mapa (territorio → sha256 del M06) cambia respecto de la última Release; se NIEGA si no cambia.
  `blob --blob-sha S --sha256 H --salida F` baja el blob del visor y comprueba su sha256 (fallo cerrado).
  Los errores salen por stderr con rc 1; stdout solo lleva el resultado.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "herramientas"))

VISOR = "orchestracion/publicaciones_visor.json"
PREFIJO = "mapas-v"
_TAG = re.compile(r"^mapas-v(\d+)\.(\d+)\.(\d+)$")
_TERR = re.compile(r"^[a-z0-9_]+$")


def _tags(texto: str) -> list[tuple[int, int, int]]:
    return sorted(tuple(int(x) for x in m.groups()) for m in (_TAG.match(l.strip()) for l in texto.splitlines()) if m)


def ultima(texto_tags: str) -> str:
    t = _tags(texto_tags)
    return f"{PREFIJO}{'.'.join(map(str, t[-1]))}" if t else ""


def vigentes(root: Path) -> dict[str, dict]:
    """territorio (id nuevo) → producto canonical_m06 vigente del visor; sin variantes 350."""
    import resultados_ligeros as rl
    from ddd_core import territorio_ids as ids
    prods = json.loads((root / VISOR).read_text(encoding="utf-8"))["products"]
    out: dict[str, dict] = {}
    for t, p in rl.vigente_por_eleccion(prods, "canonical_m06").items():
        try:
            nuevo = ids.resolver_id(t)
        except (ids.IdTerritorioDesconocido, ids.IdReservado):
            continue
        if not ids.es_variante_350(nuevo):
            out[nuevo] = p
    return dict(sorted(out.items()))


def elegir(root: Path, territorios: str) -> dict[str, dict]:
    pub = vigentes(root)
    pedido = [x for x in re.split(r"[,\s]+", territorios.strip().lower()) if x]
    if not pedido:
        raise ValueError("P50_TERRITORIOS_VACIO: indica códigos (p. ej. aut01,nac42) o «todos»")
    if pedido == ["todos"]:
        if not pub:
            raise ValueError("P50_SIN_PUBLICADOS: el visor no tiene ningún M06 publicado")
        return pub
    from ddd_core import territorio_ids as ids
    sel: dict[str, dict] = {}
    for x in pedido:
        if not _TERR.match(x):
            raise ValueError(f"P50_TERRITORIO_INVALIDO: «{x}»")
        try:
            t = ids.resolver_id(x)
        except (ids.IdTerritorioDesconocido, ids.IdReservado) as exc:
            raise ValueError(f"P50_TERRITORIO_DESCONOCIDO: {x} ({exc})") from exc
        if t not in pub:
            raise ValueError(f"P50_NO_PUBLICADO: {t} no tiene M06 en el visor")
        sel[t] = pub[t]
    return dict(sorted(sel.items()))


def version(tags: str, previo: dict | None, mapa: dict[str, str]) -> str:
    t = _tags(tags)
    if not t:
        return "1.0.0"
    if previo is None:
        raise ValueError("P50_SIN_MAPAS_PREVIO: la última Release no trae MAPAS.json; no se puede decidir la versión")
    if previo == mapa:
        raise ValueError(f"P50_MAPA_SIN_CAMBIOS: el mapa es idéntico al de {ultima(tags)}; no se publica una versión nueva")
    ma, mi, _ = t[-1]
    return f"{ma}.{mi + 1}.0"


def plan(root: Path, territorios: str, tags: str, previo: dict | None) -> dict:
    sel = elegir(root, territorios)
    mapa = {t: p["sha256"] for t, p in sel.items()}
    v = version(tags, previo, mapa)
    return {
        "version": v, "tag": f"{PREFIJO}{v}", "mapa": mapa,
        "territorios": [{"territory_id": t, "run_id": str(p["run_id"]), "blob_sha": p["blob_sha"], "sha256": p["sha256"]}
                        for t, p in sel.items()],
    }


def bajar(blob_sha: str, sha256: str, salida: Path, repo: str) -> None:
    if not re.fullmatch(r"[0-9a-f]{40}", blob_sha) or not re.fullmatch(r"[0-9a-f]{64}", sha256):
        raise ValueError("P50_BLOB_INVALIDO: blob_sha o sha256 mal formados")
    r = subprocess.run(["gh", "api", f"repos/{repo}/git/blobs/{blob_sha}", "-H", "Accept: application/vnd.github.raw"],
                       capture_output=True)
    if r.returncode:
        raise ValueError(f"P50_BLOB_NO_BAJA: {blob_sha}: {r.stderr.decode(errors='replace')[:200]}")
    if hashlib.sha256(r.stdout).hexdigest() != sha256:
        raise ValueError(f"P50_SHA256_NO_CUADRA: el blob {blob_sha} no coincide con el sha256 del visor")
    salida.parent.mkdir(parents=True, exist_ok=True)
    salida.write_bytes(r.stdout)


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=(__doc__ or "").splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    u = sub.add_parser("ultima", help="última etiqueta mapas-vX.Y.Z")
    u.add_argument("--tags", required=True)
    p = sub.add_parser("plan", help="territorios, M06 y versión")
    p.add_argument("--root", default=str(ROOT))
    p.add_argument("--territorios", required=True)
    p.add_argument("--tags", required=True)
    p.add_argument("--previo", default="")
    b = sub.add_parser("blob", help="baja un M06 del visor y verifica su sha256")
    b.add_argument("--blob-sha", required=True)
    b.add_argument("--sha256", required=True)
    b.add_argument("--salida", required=True)
    b.add_argument("--repo", required=True)
    a = ap.parse_args(argv)
    try:
        if a.cmd == "ultima":
            print(ultima(Path(a.tags).read_text(encoding="utf-8")))
        elif a.cmd == "plan":
            prev = json.loads(Path(a.previo).read_text(encoding="utf-8")) if a.previo and Path(a.previo).is_file() else None
            print(json.dumps(plan(Path(a.root), a.territorios, Path(a.tags).read_text(encoding="utf-8"), prev), indent=2))
        else:
            bajar(a.blob_sha, a.sha256, Path(a.salida), a.repo)
    except (ValueError, OSError, KeyError, json.JSONDecodeError) as exc:
        print(f"::error::{exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
