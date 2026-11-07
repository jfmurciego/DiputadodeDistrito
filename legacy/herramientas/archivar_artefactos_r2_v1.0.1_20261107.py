#!/usr/bin/env python3
"""Archivista: copia a Cloudflare R2 los artefactos de Actions referenciados antes de que caduquen.

PROYECTO: Diputado de Distrito
VERSIÓN: 1.0.1
NOMBRE DE VERSIÓN: Archivista R2 con reintentos
FECHA: 2026-11-07
ESTADO: candidato
QUÉ HACE: lee el catálogo operativo (orchestracion/estado_operativo.json) y orchestracion/publicaciones_visor.json,
  obtiene los runs y artefactos «ddd-state-<run>-M0x», «ddd-audit-<run>…» (y paquetes fuente) que referencian,
  lista los que siguen vivos en Actions, ordenados por caducidad (primero lo que caduca antes), y por cada uno:
  descarga el ZIP, calcula sha256 y tamaño, lo sube a R2 con clave <territorio>/<run>/<artefacto>.zip y anota
  la entrada en orchestracion/archivo_r2.json (URL R2, sha256, tamaño, caducidad original, fecha de archivado).
IDEMPOTENTE: no vuelve a descargar un artefacto (mismo id) ya archivado, y no vuelve a subir si R2 ya tiene
  la misma clave con el mismo sha256. Un artefacto caducado y no archivado se informa como «perdido».
CAMBIOS: 1.0.1: reintentos con espera exponencial (2, 4, 8, 16, 32 s; 6 intentos) ante 5xx, 429 y errores de red
  en la API de GitHub y en R2, con registro de cada intento (run 42393003447: HTTP 500 al listar artefactos).
  1.0.0: fichero nuevo (T-47).
MOTIVO: los artefactos caducan a los 14 días y con ellos productos registrados en el catálogo (p. ej. M05 de
  Cantabria, run 41037133327).
ANTERIOR: legacy/herramientas/archivar_artefactos_r2_v1.0.0_20261107.py
Uso: python herramientas/archivar_artefactos_r2.py [--root-dir .] [--caduca-antes AAAA-MM-DD] [--max N] [--simular]
Entorno: GITHUB_TOKEN, GITHUB_REPOSITORY; R2_BUCKET, R2_ACCOUNT_ID y credenciales AWS_* (aws cli) salvo --simular.
Salida: 0 si todo lo archivable quedó archivado; 1 si hubo errores de copia.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Optional

ROOT = Path(__file__).resolve().parents[1]
CATALOGO = "orchestracion/estado_operativo.json"
VISOR = "orchestracion/publicaciones_visor.json"
MANIFIESTO = "orchestracion/archivo_r2.json"
SCHEMA = "ddd.archivo-r2/1.0"

_NOMBRE = re.compile(r"^ddd-(state|audit|source-package)-")
_RUN = re.compile(r"(?<!\d)(\d{8,})(?!\d)")


def _utcnow() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _run_de_nombre(nombre: str) -> Optional[str]:
    m = _RUN.search(nombre)
    return m.group(1) if m else None


def _slug(txt: str) -> str:
    return re.sub(r"[^a-z0-9_.-]+", "_", (txt or "sin_territorio").lower()).strip("_") or "sin_territorio"


def referencias(root: Path) -> tuple[dict[str, str], dict[str, str]]:
    """Devuelve (nombres explícitos → territorio, run → territorio) del catálogo y del visor."""
    nombres: dict[str, str] = {}
    runs: dict[str, str] = {}

    def visitar(x, territorio=None):
        if isinstance(x, dict):
            territorio = x.get("territory_id") or territorio
            nom = x.get("artifact_name")
            if isinstance(nom, str) and _NOMBRE.match(nom):
                nombres.setdefault(nom, territorio or "sin_territorio")
            for v in x.values():
                visitar(v, territorio)
        elif isinstance(x, list):
            for v in x:
                visitar(v, territorio)

    cat = root / CATALOGO
    if cat.is_file():
        visitar(json.loads(cat.read_text(encoding="utf-8")))
    vis = root / VISOR
    if vis.is_file():
        for p in json.loads(vis.read_text(encoding="utf-8")).get("products", []):
            run = str(p.get("run_id") or "")
            if run.isdigit() and p.get("territory_id"):
                runs.setdefault(run, p["territory_id"])
    for nom, terr in nombres.items():
        run = _run_de_nombre(nom)
        if run and nom.startswith(("ddd-state-", "ddd-audit-")):
            runs.setdefault(run, terr)
    return nombres, runs


def seleccionar(vivos: list[dict], nombres: dict[str, str], runs: dict[str, str]) -> list[dict]:
    """Artefactos vivos referenciados, con territorio y run, por caducidad ascendente."""
    out = []
    for a in vivos:
        if a.get("expired"):
            continue
        nom = a["name"]
        run = str((a.get("workflow_run") or {}).get("id") or _run_de_nombre(nom) or "")
        if nom in nombres:
            terr = nombres[nom]
        elif nom.startswith(("ddd-state-", "ddd-audit-")) and _run_de_nombre(nom) in runs:
            terr = runs[_run_de_nombre(nom)]
            run = _run_de_nombre(nom)
        else:
            continue
        out.append({**a, "territorio": _slug(terr), "run": run})
    out.sort(key=lambda a: (a.get("expires_at") or "9999", a["name"]))
    return out


def clave(a: dict) -> str:
    return f"{a['territorio']}/{a['run']}/{a['name']}.zip"


def sha256_fichero(ruta: Path) -> str:
    h = hashlib.sha256()
    with open(ruta, "rb") as f:
        for bloque in iter(lambda: f.read(1 << 20), b""):
            h.update(bloque)
    return h.hexdigest()


def archivar(
    vivos: list[dict],
    nombres: dict[str, str],
    runs: dict[str, str],
    manifiesto: dict,
    descargar: Callable[[dict, Path], None],
    r2_sha: Callable[[str], Optional[str]],
    r2_subir: Callable[[str, Path, str], None],
    bucket: str,
    ahora: Callable[[], str] = _utcnow,
    caduca_antes: Optional[str] = None,
    maximo: Optional[int] = None,
) -> dict:
    """Núcleo sin red: aplica la política y devuelve el resumen; muta `manifiesto`."""
    entradas = manifiesto.setdefault("artefactos", {})
    res = {"archivados": [], "ya_archivados": [], "sin_cambios_r2": [], "errores": [], "omitidos": []}
    ya_ids = {e.get("artifact_id") for e in entradas.values()}
    pendientes = seleccionar(vivos, nombres, runs)
    for a in pendientes:
        k = clave(a)
        if caduca_antes and (a.get("expires_at") or "9999") >= caduca_antes:
            res["omitidos"].append(k)
            continue
        if a["id"] in ya_ids and k in entradas:
            res["ya_archivados"].append(k)
            continue
        if maximo is not None and len(res["archivados"]) + len(res["sin_cambios_r2"]) >= maximo:
            res["omitidos"].append(k)
            continue
        try:
            with tempfile.TemporaryDirectory() as td:
                zip_ = Path(td) / "a.zip"
                descargar(a, zip_)
                sha, tam = sha256_fichero(zip_), zip_.stat().st_size
                if r2_sha(k) == sha:
                    res["sin_cambios_r2"].append(k)
                else:
                    r2_subir(k, zip_, sha)
                    res["archivados"].append(k)
        except Exception as exc:  # noqa: BLE001 - se informa y se sigue con el siguiente
            res["errores"].append(f"{k}: {exc}")
            continue
        entradas[k] = {
            "artefacto": a["name"],
            "territorio": a["territorio"],
            "run_id": a["run"],
            "artifact_id": a["id"],
            "url": f"r2://{bucket}/{k}",
            "sha256": sha,
            "tamano_bytes": tam,
            "caducidad_original": a.get("expires_at"),
            "archivado_en": ahora(),
        }
    existentes = {a["name"] for a in vivos}
    res["perdidos"] = sorted(
        n for n in nombres if n not in existentes and not any(e["artefacto"] == n for e in entradas.values())
    )
    manifiesto["schema"] = SCHEMA
    manifiesto["actualizado_en"] = ahora()
    return res


def cargar_manifiesto(ruta: Path) -> dict:
    if ruta.is_file():
        return json.loads(ruta.read_text(encoding="utf-8"))
    return {"schema": SCHEMA, "artefactos": {}}


def guardar_manifiesto(ruta: Path, m: dict) -> bool:
    """Escribe de forma determinista; devuelve True si el contenido cambió (ignora `actualizado_en`)."""
    m["artefactos"] = dict(sorted(m["artefactos"].items()))
    previo = cargar_manifiesto(ruta)
    if previo.get("artefactos") == m["artefactos"]:
        return False
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_text(json.dumps(m, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return True


# --- Implementaciones reales (GitHub y R2) -------------------------------------------------------

INTENTOS = 6
ESPERA_BASE = 2  # s; espera 2, 4, 8, 16, 32 entre intentos
_dormir = time.sleep  # los tests lo sustituyen


def _transitorio(exc: BaseException) -> bool:
    if isinstance(exc, urllib.error.HTTPError):
        return exc.code >= 500 or exc.code == 429
    return isinstance(exc, (urllib.error.URLError, TimeoutError, ConnectionError, OSError, subprocess.CalledProcessError))


def con_reintentos(fn: Callable, descripcion: str, intentos: int = INTENTOS):
    """Ejecuta fn(); reintenta con espera exponencial los fallos transitorios y registra cada intento."""
    for n in range(1, intentos + 1):
        try:
            return fn()
        except Exception as exc:  # noqa: BLE001
            if not _transitorio(exc) or n == intentos:
                raise
            espera = ESPERA_BASE * 2 ** (n - 1)
            print(f"::warning::{descripcion}: intento {n}/{intentos} falló ({exc}); reintento en {espera}s", flush=True)
            _dormir(espera)


def _gh_json(url: str, token: str):
    def _f():
        req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"})
        with urllib.request.urlopen(req, timeout=120) as r:
            return json.load(r)

    return con_reintentos(_f, f"GET {url}")


def listar_artefactos_gh(repo: str, token: str) -> list[dict]:
    out, pagina = [], 1
    while True:
        datos = _gh_json(f"https://api.github.com/repos/{repo}/actions/artifacts?per_page=100&page={pagina}", token)
        lote = datos.get("artifacts", [])
        out += lote
        if len(lote) < 100:
            return out
        pagina += 1


def descargar_gh(repo: str, token: str):
    class _SinAuthEnRedireccion(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, req, fp, code, msg, headers, newurl):
            nuevo = super().redirect_request(req, fp, code, msg, headers, newurl)
            if nuevo is not None:
                nuevo.headers.pop("Authorization", None)
            return nuevo

    def _una_vez(a: dict, destino: Path) -> None:
        req = urllib.request.Request(
            f"https://api.github.com/repos/{repo}/actions/artifacts/{a['id']}/zip",
            headers={"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"},
        )
        op = urllib.request.build_opener(_SinAuthEnRedireccion)
        with op.open(req, timeout=600) as r, open(destino, "wb") as f:
            while bloque := r.read(1 << 20):
                f.write(bloque)

    def _f(a: dict, destino: Path) -> None:
        con_reintentos(lambda: _una_vez(a, destino), f"descarga artefacto {a['name']}")

    return _f


def r2_cliente(bucket: str, account: str):
    ep = f"https://{account}.r2.cloudflarestorage.com"

    def _sha(k: str) -> Optional[str]:
        p = subprocess.run(
            ["aws", "s3api", "head-object", "--bucket", bucket, "--key", k, "--endpoint-url", ep, "--output", "json"],
            capture_output=True, text=True,
        )
        if p.returncode != 0:
            if re.search(r"404|Not Found|NoSuchKey", p.stderr or ""):
                return None
            raise subprocess.CalledProcessError(p.returncode, "head-object", stderr=p.stderr)
        return (json.loads(p.stdout).get("Metadata") or {}).get("sha256")

    def sha(k: str) -> Optional[str]:
        return con_reintentos(lambda: _sha(k), f"R2 head {k}")

    def _subir(k: str, ruta: Path, h: str) -> None:
        subprocess.run(
            ["aws", "s3", "cp", str(ruta), f"s3://{bucket}/{k}", "--endpoint-url", ep, "--metadata", f"sha256={h}", "--only-show-errors"],
            check=True,
        )

    def subir(k: str, ruta: Path, h: str) -> None:
        con_reintentos(lambda: _subir(k, ruta, h), f"R2 subida {k}")

    return sha, subir


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--root-dir", default=str(ROOT))
    ap.add_argument("--caduca-antes", help="solo artefactos que caducan antes de esta fecha (AAAA-MM-DD)")
    ap.add_argument("--max", type=int, help="máximo de copias en esta ejecución")
    ap.add_argument("--simular", action="store_true", help="lista lo que copiaría; no descarga ni sube")
    a = ap.parse_args(argv)
    root = Path(a.root_dir)
    repo, token = os.environ.get("GITHUB_REPOSITORY", ""), os.environ.get("GITHUB_TOKEN", "")
    if not repo or not token:
        print("::error::Faltan GITHUB_REPOSITORY o GITHUB_TOKEN.")
        return 1
    nombres, runs = referencias(root)
    vivos = listar_artefactos_gh(repo, token)
    man = cargar_manifiesto(root / MANIFIESTO)
    if a.simular:
        for x in seleccionar(vivos, nombres, runs):
            print(f"{x.get('expires_at')}  {clave(x)}  {x.get('size_in_bytes')}")
        return 0
    bucket, cuenta = os.environ.get("R2_BUCKET", ""), os.environ.get("R2_ACCOUNT_ID", "")
    if not bucket or not cuenta:
        print("::error::Faltan R2_BUCKET o R2_ACCOUNT_ID.")
        return 1
    sha, subir = r2_cliente(bucket, cuenta)
    res = archivar(vivos, nombres, runs, man, descargar_gh(repo, token), sha, subir, bucket,
                   caduca_antes=a.caduca_antes, maximo=a.max)
    cambio = guardar_manifiesto(root / MANIFIESTO, man)
    print(json.dumps({k: (len(v) if k != "errores" else v) for k, v in res.items()}, ensure_ascii=False))
    for p in res["perdidos"]:
        print(f"::warning::Artefacto referenciado ya caducado y sin archivar: {p}")
    for e in res["errores"]:
        print(f"::error::{e}")
    print(f"manifiesto_cambiado={'true' if cambio else 'false'}")
    return 1 if res["errores"] else 0


if __name__ == "__main__":
    sys.exit(main())
