#!/usr/bin/env python3
"""Archiva en R2 (ARC-P) los assets de las releases draft ``almacen-m06-*`` y mantiene su índice versionado.

PROYECTO: Diputado de Distrito
VERSIÓN: 1.1.0
NOMBRE DE VERSIÓN: Archivo en R2 del almacén M06
FECHA: 2026-11-14
ESTADO: candidato
QUÉ HACE: ``archivar`` baja cada asset ``<artefacto>-<id>.zip`` de las releases ``almacen-m06-*``, comprueba su
  SHA-256 contra el digest que registra GitHub, lo sube a ``arc-p/m06/<asset>_<sha12>.zip`` (idempotente: no
  resube si R2 ya tiene el mismo sha256) y deja ``ARCHIVO_ALMACEN_M06.json``. ``indexar`` fusiona ese fichero en
  ``orchestracion/almacen_m06_r2.json`` (la entrada que ``localizar_artefacto_durable`` lee PRIMERO). No borra nada.
CAMBIOS: 1.1.0 (T-302): también archiva los MANIFIESTO-*.tsv de cada release (índice de sus assets) y añade `listar` (BORRAR solo si todos
  los assets están en el índice con su sha256; si no, CONSERVAR). 1.0.0: fichero nuevo (T-302).
MOTIVO: los seis ``almacen-m06-*`` (1,11 GB) son la única copia durable de sus artefactos (T-299).
ANTERIOR: legacy/herramientas/almacen_m06_r2_v1.0.0_20261114.py
Entorno de ``archivar``: GH_TOKEN, R2_BUCKET, R2_ACCOUNT_ID y credenciales AWS_*.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import tempfile
import time
from pathlib import Path
from typing import Callable

try:
    from herramientas.localizar_artefacto_durable import RELEASE_PREFIX, INDICE_R2, gh_api, gh_download
except ImportError:  # ejecución directa
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from herramientas.localizar_artefacto_durable import RELEASE_PREFIX, INDICE_R2, gh_api, gh_download

SCHEMA = "ddd.almacen-m06-r2/1.0"
PREFIJO_CLAVE = "arc-p/m06/"
_ASSET = re.compile(r"^(?P<nombre>.+)-(?P<id>\d+)\.zip$")
_RUN = re.compile(r"-(\d{8,})(?:-M\d+)?$")


def clave(asset: str, sha256: str) -> str:
    stem, ext = asset.rsplit(".", 1)
    return f"{PREFIJO_CLAVE}{stem}_{sha256[:12]}.{ext}"


def _sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def inventario(repo: str, api: Callable = gh_api) -> list[dict]:
    """Assets zip de las releases ``almacen-m06-*``: una fila por asset, con run de origen y digest de GitHub."""
    filas = []
    for rel in api(f"repos/{repo}/releases?per_page=100") or []:
        tag = str(rel.get("tag_name") or "")
        if not tag.startswith(RELEASE_PREFIX):
            continue
        run_release = tag.rsplit("-", 1)[-1]
        for a in rel.get("assets") or []:
            nombre = str(a.get("name") or "")
            m = _ASSET.match(nombre)
            es_tsv = bool(re.fullmatch(r"MANIFIESTO-.+\.tsv", nombre))
            m = m or ({"nombre": nombre.removesuffix(".tsv"), "id": "0"} if es_tsv else None)
            run = (_RUN.search(m["nombre"] if m else nombre) or [None, run_release])[1]
            # los assets que no son <artefacto>-<id>.zip ni MANIFIESTO-*.tsv no se archivan: constan como no archivables
            # y la release que los lleva es CONSERVAR (igual que exige el .ps1)
            filas.append({"release_tag": tag, "asset_id": a["id"], "asset": nombre, "archivable": m is not None,
                          "artifact_name": m["nombre"] if m else nombre, "artifact_id": (int(m["id"]) or None) if m else None,
                          "run_id": run, "digest": str(a.get("digest") or "").removeprefix("sha256:").lower(),
                          "bytes": a.get("size")})
    return sorted(filas, key=lambda f: (f["release_tag"], f["asset"]))


def archivar(repo: str, out: Path, *, api: Callable = gh_api, download: Callable = gh_download,
             r2_sha: Callable[[str], str | None], r2_subir: Callable, simular: bool = False,
             ahora: Callable[[], str] = lambda: time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())) -> tuple[dict, int]:
    """Devuelve (objetos archivados, nº de fallos). Un asset cuyos bytes no coinciden con su digest NO se sube."""
    objetos, fallos = {}, 0
    out.mkdir(parents=True, exist_ok=True)
    todas = inventario(repo, api)
    for f in todas:
        if not f["archivable"]:
            print(f"::warning::{f['release_tag']}/{f['asset']}: asset no archivable; su release queda en CONSERVAR")
    filas = [f for f in todas if f["archivable"]]
    if not filas:
        print("::error::ALMACEN_SIN_ASSETS: ninguna release almacen-m06-* con assets zip (¿token sin contents:read, drafts, paginación?)")
        fallos += 1
    for f in filas:
        if not re.fullmatch(r"[0-9a-f]{64}", f["digest"]):
            print(f"::error::{f['asset']}: la release no registra digest SHA-256; no se archiva")
            fallos += 1
            continue
        k = clave(f["asset"], f["digest"])
        if simular:
            print(f"simular: {f['release_tag']}/{f['asset']} -> {k}")
            continue
        if r2_sha(k) != f["digest"]:
            with tempfile.TemporaryDirectory() as tmp:
                z = Path(tmp) / f["asset"]
                download(f"repos/{repo}/releases/assets/{f['asset_id']}", z, True)
                real = _sha(z)
                if real != f["digest"]:
                    print(f"::error::{f['asset']}: SHA-256 descargado {real} != digest de la release; no se sube")
                    fallos += 1
                    continue
                r2_subir(k, z, real)
        objetos[k] = {"release_tag": f["release_tag"], "asset": f["asset"], "artifact_name": f["artifact_name"],
                      "artifact_id": f["artifact_id"], "run_id": f["run_id"], "sha256": f["digest"],
                      "bytes": f["bytes"], "origen": f"release:{repo}/{f['release_tag']}", "archivado_en": ahora()}
    if not simular and not fallos and len(objetos) != len(filas):
        print(f"::error::ALMACEN_INCOMPLETO: archivados {len(objetos)} de {len(filas)} assets")
        fallos += 1
    (out / "ARCHIVO_ALMACEN_M06.json").write_text(
        json.dumps({"schema": SCHEMA, "objetos": objetos}, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
    return objetos, fallos


def veredicto(filas: list[dict], indice: dict) -> dict[str, dict]:
    """Por release: BORRAR solo si TODOS sus assets zip están en el índice con la clave y el sha256 esperados; si no, CONSERVAR."""
    res: dict[str, dict] = {}
    for f in filas:
        r = res.setdefault(f["release_tag"], {"assets": [], "estado": "BORRAR", "motivo": ""})
        k = clave(f["asset"], f["digest"]) if f["digest"] and f["archivable"] else None
        e = indice.get(k) if k else None
        ok = bool(e) and str(e.get("sha256")).lower() == f["digest"]
        r["assets"].append({"asset": f["asset"], "bytes": f["bytes"], "sha256": f["digest"], "clave_r2": k, "en_r2": ok})
        if not ok:
            r["estado"] = "CONSERVAR"
            r["motivo"] = "NO VERIFICADO EN R2 → CONSERVAR"
    return res


def listar(repo: str, indice: Path = INDICE_R2, api: Callable = gh_api) -> str:
    idx = json.loads(indice.read_text(encoding="utf-8")).get("objetos", {}) if indice.is_file() else {}
    v = veredicto(inventario(repo, api), idx)
    out = ["| Release | Assets | En R2 | Estado |", "|---|---|---|---|"]
    for tag, r in sorted(v.items()):
        n = sum(a["en_r2"] for a in r["assets"])
        out.append(f"| `{tag}` | {len(r['assets'])} | {n} | {r['estado']}{' — ' + r['motivo'] if r['motivo'] else ''} |")
    return "\n".join(out)


def indexar(archivo: Path, indice: Path = INDICE_R2) -> int:
    nuevo = json.loads(archivo.read_text(encoding="utf-8"))["objetos"]
    actual = json.loads(indice.read_text(encoding="utf-8")) if indice.is_file() else {"schema": SCHEMA, "objetos": {}}
    actual.setdefault("objetos", {}).update(nuevo)
    actual["schema"] = SCHEMA
    indice.write_text(json.dumps(actual, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
    return len(nuevo)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("archivar")
    a.add_argument("--repo", default=os.environ.get("GITHUB_REPOSITORY", ""))
    a.add_argument("--out", type=Path, default=Path("almacen_m06"))
    a.add_argument("--simular", action="store_true")
    l = sub.add_parser("listar")
    l.add_argument("--repo", default=os.environ.get("GITHUB_REPOSITORY", ""))
    i = sub.add_parser("indexar")
    i.add_argument("archivo", type=Path)
    ns = ap.parse_args(argv)
    if ns.cmd == "listar":
        print(listar(ns.repo))
        return 0
    if ns.cmd == "indexar":
        print(f"{indexar(ns.archivo)} objeto(s) indexados en {INDICE_R2}")
        return 0
    if not ns.simular and not (os.environ.get("R2_BUCKET") and os.environ.get("R2_ACCOUNT_ID")):
        print("::error::ALMACEN_R2_SIN_CREDENCIALES (R2_BUCKET/R2_ACCOUNT_ID)")
        return 2
    sha, subir = (lambda k: None, None)
    if not ns.simular:
        from herramientas.archivar_artefactos_r2 import r2_cliente
        sha, subir = r2_cliente(os.environ["R2_BUCKET"], os.environ["R2_ACCOUNT_ID"])
    objetos, fallos = archivar(ns.repo, ns.out, r2_sha=sha, r2_subir=subir, simular=ns.simular)
    print(json.dumps({"archivados": len(objetos), "fallos": fallos}))
    return 1 if fallos else 0


if __name__ == "__main__":
    raise SystemExit(main())
