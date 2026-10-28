#!/usr/bin/env python3
"""Localiza un artefacto acreditado en GitHub Actions o, si caducó, en su release draft.

PROYECTO: Diputado de Distrito
VERSIÓN: 1.0.0
NOMBRE DE VERSIÓN: Localización durable de artefactos acreditados
FECHA: 2026-10-28
ESTADO: candidato
QUÉ HACE: dado run, nombre y SHA-256 acreditados, devuelve el artefacto vivo de Actions o su
copia en la release draft `almacen-m06-<territorio>-<run>` (asset `<nombre>-<id>.zip`), y
opcionalmente lo descarga y lo extrae. Solo acepta bytes cuyo SHA-256 coincide.
CAMBIOS: herramienta nueva.
MOTIVO: los artefactos de Actions caducan a los 14–30 días y los M06 certificados dejaban de
ser reutilizables aunque sus bytes estuvieran conservados en releases.
ANTERIOR: ninguno (herramienta nueva).
"""
from __future__ import annotations

import argparse
import hashlib
import json
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

Api = Callable[[str], object]
Download = Callable[[str, Path, bool], None]


class LocationError(RuntimeError):
    def __init__(self, code: int, message: str):
        super().__init__(message)
        self.code = code


def _sha(value: str) -> str:
    value = str(value or "").removeprefix("sha256:").lower()
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


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def locate(repo: str, run_id: int, name: str, sha256: str, *, api: Api = gh_api) -> dict:
    """Devuelve la ubicación verificada por metadatos; no descarga nada."""
    expected = _sha(sha256)
    artifacts = (api(f"repos/{repo}/actions/runs/{run_id}/artifacts?per_page=100") or {}).get("artifacts") or []
    named = [a for a in artifacts if a.get("name") == name]
    live = [a for a in named if not a.get("expired")]
    if len(live) > 1:
        raise LocationError(EXIT_NOT_FOUND, f"Artefacto ambiguo en Actions: {name} (run {run_id})")
    if live:
        observed = str(live[0].get("digest") or "").removeprefix("sha256:").lower()
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
    verified = [c for c in candidates
                if str(c[1].get("digest") or "").removeprefix("sha256:").lower() == expected]
    if not verified:
        reason = "con digest distinto" if candidates else "ni en Actions ni en releases"
        raise LocationError(EXIT_NOT_FOUND if not candidates else EXIT_DIGEST,
                            f"Artefacto acreditado no disponible ({reason}): {name} (run {run_id})")
    release, asset, artifact_id = verified[0]
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


def fetch(location: dict, out_dir: Path, *, extract: bool, download: Download = gh_download) -> dict:
    """Descarga el zip ubicado, comprueba su SHA-256 y, si se pide, lo extrae."""
    out_dir.mkdir(parents=True, exist_ok=True)
    archive = out_dir / f"{location['artifact_name']}.zip"
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
    ap.add_argument("--sha256", required=True)
    ap.add_argument("--out-dir", type=Path, help="descargar aquí; sin él solo se localiza")
    ap.add_argument("--extract", action="store_true", help="extraer el zip como gh run download")
    ns = ap.parse_args(argv)
    try:
        result = locate(ns.repo, ns.run_id, ns.name, ns.sha256)
        if ns.out_dir:
            result = fetch(result, ns.out_dir, extract=ns.extract)
    except LocationError as exc:
        print(f"::error::{exc}", file=sys.stderr)
        return exc.code
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
