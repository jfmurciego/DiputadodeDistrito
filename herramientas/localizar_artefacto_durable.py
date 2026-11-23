#!/usr/bin/env python3
"""Localiza un artefacto acreditado en GitHub Actions o, si caducó, en su release draft.

PROYECTO: Diputado de Distrito
VERSIÓN: 1.2.0
NOMBRE DE VERSIÓN: Localización durable de artefactos acreditados (R2 primero)
FECHA: 2026-11-22
ESTADO: candidato
QUÉ HACE: dado run, nombre y SHA-256 acreditados, devuelve el artefacto vivo de Actions o su
copia en la release draft `almacen-m06-<territorio>-<run>` (asset `<nombre>-<id>.zip`), y
opcionalmente lo descarga y lo extrae. Solo acepta bytes cuyo SHA-256 coincide.
CAMBIOS: 1.2.0 (T-443, D-188): una entrada del índice con `clave_anterior` (ruta vieja, transición al árbol nuevo de R2) añade esa clave
como primer respaldo (fuente `r2`) antes de Actions y la release; mismas comprobaciones de SHA-256. Sin `clave_anterior`, como 1.1.0.
CAMBIOS: 1.1.0 (T-302): lee PRIMERO de R2 (arc-p/m06/, índice orchestracion/almacen_m06_r2.json, sha256 verificado)
y, si la entrada no existe, R2 no está configurado o sus bytes no valen, cae a Actions y a la release draft como
antes («R2 primero» vale dentro de esta herramienta; la puerta solo la invoca con el artefacto de Actions
caducado o ausente). Un objeto de R2 alterado nunca se acepta. 1.0.0: herramienta nueva.
MOTIVO: los artefactos de Actions caducan a los 14–30 días y los M06 certificados dejaban de
ser reutilizables aunque sus bytes estuvieran conservados en releases.
ANTERIOR: legacy/herramientas/localizar_artefacto_durable_v1.1.0_20261122.py
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import zipfile
from pathlib import Path, PurePosixPath
from typing import Callable

SCHEMA = "ddd.durable-artifact-location/1.0"
RELEASE_PREFIX = "almacen-m06-"
EXIT_NOT_FOUND = 44
EXIT_DIGEST = 45

INDICE_R2 = Path(__file__).resolve().parents[1] / "orchestracion" / "almacen_m06_r2.json"

Api = Callable[[str], object]
Download = Callable[[str, Path, bool], None]
R2Download = Callable[[str, Path], None]


class LocationError(RuntimeError):
    def __init__(self, code: int, message: str):
        super().__init__(message)
        self.code = code


def _sha(value: str | None) -> str | None:
    if value in (None, ""):
        return None  # sin acreditación previa: se adopta el digest observado
    value = str(value).removeprefix("sha256:").lower()
    if not re.fullmatch(r"[0-9a-f]{64}", value):
        raise LocationError(EXIT_DIGEST, f"SHA-256 acreditado inválido: {value!r}")
    return value


def gh_api(path: str) -> object:
    out = subprocess.run(["gh", "api", path], check=True, capture_output=True, text=True).stdout
    return json.loads(out)


def gh_download(path: str, target: Path, release_asset: bool) -> None:
    headers = ["-H", "Accept: application/octet-stream"] if release_asset else []
    with target.open("wb") as stream:
        subprocess.run(["gh", "api", *headers, path], check=True, stdout=stream)


def r2_configurado() -> bool:
    return bool(os.environ.get("R2_BUCKET") and os.environ.get("R2_ACCOUNT_ID"))


def r2_download(clave: str, target: Path) -> None:
    ep = f"https://{os.environ['R2_ACCOUNT_ID']}.r2.cloudflarestorage.com"
    subprocess.run(["aws", "s3", "cp", f"s3://{os.environ['R2_BUCKET']}/{clave}", str(target),
                    "--endpoint-url", ep, "--only-show-errors"], check=True)


def cargar_indice(path: Path = INDICE_R2) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8")).get("objetos") or {}
    except (OSError, ValueError):
        return {}


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def locate(repo: str, run_id: int, name: str, sha256: str | None, *, api: Api = gh_api,
           r2_index: dict | None = None) -> dict:
    """Como ``_locate`` pero, si ``r2_index`` trae una entrada del artefacto con el SHA-256 acreditado, la devuelve
    primero (source ``r2``) con el resto de fuentes como ``fallback``. Sin índice o sin entrada: Actions y release."""
    expected = _sha(sha256)
    for clave, e in sorted((r2_index or {}).items()):
        if str(e.get("run_id")) != str(run_id) or e.get("artifact_name") != name:
            continue
        digest = str(e.get("sha256") or "").lower()
        if not re.fullmatch(r"[0-9a-f]{64}", digest) or (expected is not None and digest != expected):
            continue
        try:
            fallback = _locate(repo, run_id, name, digest, api=api)
        except LocationError:
            fallback = None
        base = {"schema": SCHEMA, "source": "r2", "run_id": run_id, "artifact_name": name,
                "artifact_id": e.get("artifact_id"), "artifact_sha256": digest}
        anterior = e.get("clave_anterior")
        if anterior and anterior != clave:  # T-443: la ruta vieja, antes de Actions y la release
            fallback = dict(base, r2_key=anterior, download_path=anterior, fallback=fallback)
        return dict(base, r2_key=clave, download_path=clave, fallback=fallback)
    return _locate(repo, run_id, name, sha256, api=api)


def _locate(repo: str, run_id: int, name: str, sha256: str | None, *, api: Api = gh_api) -> dict:
    """Devuelve la ubicación verificada por metadatos; no descarga nada.

    Sin ``sha256`` (p. ej. la auditoría que acompaña a un M06) se adopta el digest que
    GitHub registró para el artefacto o, si caducó, el que conserva su copia en la release.
    """
    expected = _sha(sha256)
    artifacts = (api(f"repos/{repo}/actions/runs/{run_id}/artifacts?per_page=100") or {}).get("artifacts") or []
    named = [a for a in artifacts if a.get("name") == name]
    live = [a for a in named if not a.get("expired")]
    if len(live) > 1:
        raise LocationError(EXIT_NOT_FOUND, f"Artefacto ambiguo en Actions: {name} (run {run_id})")
    if live:
        observed = str(live[0].get("digest") or "").removeprefix("sha256:").lower()
        if expected is None and re.fullmatch(r"[0-9a-f]{64}", observed):
            expected = observed
        if observed != expected:
            raise LocationError(EXIT_DIGEST, f"Digest de Actions contradice la acreditación: {name}")
        return {"schema": SCHEMA, "source": "actions", "run_id": run_id, "artifact_name": name,
                "artifact_id": live[0]["id"], "artifact_sha256": expected,
                "download_path": f"repos/{repo}/actions/artifacts/{live[0]['id']}/zip"}

    # Caducado o eliminado: buscar la copia durable. El asset conserva el nombre y el id del
    # artefacto original. Se busca en todas las releases del almacén porque el paquete de
    # fuentes de otra ejecución se guarda junto al M06 que lo consume; el SHA-256 decide.
    pattern = re.compile(rf"^{re.escape(name)}-(\d+)\.zip$")
    candidates = []
    releases = sorted(api(f"repos/{repo}/releases?per_page=100") or [],
                      key=lambda r: not str(r.get("tag_name") or "").endswith(f"-{run_id}"))
    for release in releases:
        tag = str(release.get("tag_name") or "")
        if not tag.startswith(RELEASE_PREFIX):
            continue
        for asset in release.get("assets") or []:
            match = pattern.match(str(asset.get("name") or ""))
            if match:
                candidates.append((release, asset, int(match.group(1))))
    def _asset_sha(asset: dict) -> str:
        return str(asset.get("digest") or "").removeprefix("sha256:").lower()
    verified = [c for c in candidates
                if (expected is None and re.fullmatch(r"[0-9a-f]{64}", _asset_sha(c[1])))
                or _asset_sha(c[1]) == expected]
    if not verified:
        reason = "con digest distinto" if candidates else "ni en Actions ni en releases"
        raise LocationError(EXIT_NOT_FOUND if not candidates else EXIT_DIGEST,
                            f"Artefacto acreditado no disponible ({reason}): {name} (run {run_id})")
    release, asset, artifact_id = verified[0]
    expected = expected or _asset_sha(asset)
    return {"schema": SCHEMA, "source": "release", "run_id": run_id, "artifact_name": name,
            "artifact_id": artifact_id, "artifact_sha256": expected,
            "release_tag": release["tag_name"], "asset_id": asset["id"],
            "download_path": f"repos/{repo}/releases/assets/{asset['id']}"}


def _extract(archive: Path, target: Path) -> None:
    target.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(archive) as zf:
        for member in zf.infolist():
            path = PurePosixPath(member.filename)
            if path.is_absolute() or ".." in path.parts:
                raise LocationError(EXIT_DIGEST, f"Ruta insegura en el zip: {member.filename}")
        zf.extractall(target)


def fetch(location: dict, out_dir: Path, *, extract: bool, download: Download = gh_download,
          r2: R2Download = r2_download) -> dict:
    """Descarga el zip ubicado, comprueba su SHA-256 y, si se pide, lo extrae.

    Un objeto de R2 ausente o alterado se descarta (se avisa) y se usa el respaldo (Actions o release), que se
    verifica igual; sin respaldo válido, error."""
    out_dir.mkdir(parents=True, exist_ok=True)
    archive = out_dir / f"{location['artifact_name']}.zip"
    if location["source"] == "r2":
        fallback = location.get("fallback")
        try:
            archive.unlink(missing_ok=True)
            r2(location["r2_key"], archive)
            observed = file_sha256(archive)
            if observed != location["artifact_sha256"]:
                raise LocationError(EXIT_DIGEST, f"Objeto de R2 con SHA-256 distinto: {observed}")
        except (LocationError, subprocess.CalledProcessError, OSError) as exc:
            archive.unlink(missing_ok=True)
            if not fallback:
                raise exc if isinstance(exc, LocationError) else LocationError(
                    EXIT_NOT_FOUND, f"Objeto de R2 no disponible: {location['r2_key']}") from exc
            print(f"::warning::R2 descartado ({exc}); se usa {fallback['source']}", file=sys.stderr)
            return fetch(fallback, out_dir, extract=extract, download=download, r2=r2)
    else:
        download(location["download_path"], archive, location["source"] == "release")
        observed = file_sha256(archive)
        if observed != location["artifact_sha256"]:
            archive.unlink(missing_ok=True)
            raise LocationError(EXIT_DIGEST, f"Bytes descargados con SHA-256 distinto: {observed}")
    result = dict(location, archive=str(archive))
    if extract:
        _extract(archive, out_dir)
        archive.unlink()
        result["archive"] = None
        result["extracted_to"] = str(out_dir)
    return result


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--repo", required=True)
    ap.add_argument("--run-id", required=True, type=int)
    ap.add_argument("--name", required=True)
    ap.add_argument("--sha256", default="", help="SHA-256 acreditado; vacío = digest registrado")
    ap.add_argument("--out-dir", type=Path, help="descargar aquí; sin él solo se localiza")
    ap.add_argument("--extract", action="store_true", help="extraer el zip como gh run download")
    ns = ap.parse_args(argv)
    try:
        result = locate(ns.repo, ns.run_id, ns.name, ns.sha256,
                        r2_index=cargar_indice() if r2_configurado() else None)
        if ns.out_dir:
            result = fetch(result, ns.out_dir, extract=ns.extract)
    except LocationError as exc:
        print(f"::error::{exc}", file=sys.stderr)
        return exc.code
    result.pop("fallback", None)
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
