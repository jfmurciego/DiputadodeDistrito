#!/usr/bin/env python3
"""Empaqueta y publica el diagnóstico automático de una 00 fallida (T-14).

PROYECTO: Diputado de Distrito
VERSIÓN: 1.0.0 · FECHA: 2026-11-01 · ESTADO: candidato
QUÉ HACE: busca en la caché del territorio el M01 (secciones y población), el grafo M03 (se comprime a .gz) y
  el informe M05, los copia a <territorio>/<run>/ y los sube a la rama `diagnostico/auto` para que los chats
  ejecuten el motor en local sin descargar artefactos (403 desde la nube). Falla en silencio útil: es
  best-effort y nunca oculta el fallo original (salida 0 salvo --strict).
MOTIVO: T-14; sustituye a lanzadores/subir_diagnostico_t02.sh, que dependía del Mac del propietario.
Uso: publicar_diagnostico_auto.py --params P --cache-dir C --run-id N [--repo R --branch B] (token en GH_TOKEN).
Con --dry-run solo empaqueta en --stage-dir.
"""
from __future__ import annotations

import argparse
import base64
import gzip
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

MAX_BYTES = 50 * 1024 * 1024
BRANCH = "diagnostico/auto"
PATTERNS = {
    "m01": ("*_m01_secciones_poblacion.geojson.zip",),
    "m03": ("*_m03_grafo.json", "*_m03_grafo.json.gz"),
    "m05": ("*m05*informe*.json",),
}


def territory_of(params: str) -> str:
    """territorios/<t>/config/<t>_2025.yaml -> <t>."""
    parts = Path(params).parts
    if "territorios" in parts and parts.index("territorios") + 1 < len(parts):
        return parts[parts.index("territorios") + 1]
    return Path(params).stem


def _latest(cache: Path, patterns: tuple[str, ...]) -> Path | None:
    found = [p for pat in patterns for p in cache.rglob(pat) if p.is_file()]
    return max(found, key=lambda p: p.stat().st_mtime) if found else None


def collect(cache: Path, dest: Path) -> list[Path]:
    """Copia a dest los ficheros de diagnóstico hallados; el grafo M03 se guarda en gzip."""
    dest.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for kind, patterns in PATTERNS.items():
        src = _latest(cache, patterns)
        if src is None:
            print(f"::warning::Diagnóstico automático: sin {kind.upper()} en {cache}")
            continue
        if kind == "m03" and src.suffix != ".gz":
            out = dest / (src.name + ".gz")
            with src.open("rb") as fi, gzip.open(out, "wb", compresslevel=9) as fo:
                shutil.copyfileobj(fi, fo)
        else:
            out = dest / src.name
            shutil.copy2(src, out)
        written.append(out)
    total = sum(p.stat().st_size for p in written)
    if total > MAX_BYTES:
        for p in written:
            p.unlink()
        raise RuntimeError(f"paquete de {total} bytes supera el máximo de {MAX_BYTES}")
    return written


def _git(args: list[str], cwd: Path, token: str) -> subprocess.CompletedProcess:
    header = "AUTHORIZATION: basic " + base64.b64encode(f"x-access-token:{token}".encode()).decode()
    return subprocess.run(["git", "-c", f"http.https://github.com/.extraheader={header}", *args],
                          cwd=cwd, capture_output=True, text=True)


def publish(files: list[Path], territory: str, run_id: str, repo: str, branch: str, token: str) -> None:
    if not files:
        raise RuntimeError("nada que publicar")
    url = f"https://github.com/{repo}.git"
    with tempfile.TemporaryDirectory() as td:
        work = Path(td) / "repo"
        work.mkdir()
        for cmd in (["init", "-q"], ["config", "user.name", "ddd-diagnostico-auto"],
                    ["config", "user.email", "ddd-diagnostico-auto@users.noreply.github.com"],
                    ["remote", "add", "origin", url]):
            subprocess.run(["git", *cmd], cwd=work, check=True, capture_output=True)
        has_branch = _git(["ls-remote", "--exit-code", "--heads", "origin", branch], work, token).returncode == 0
        if has_branch:
            r = _git(["fetch", "-q", "--depth", "1", "origin", branch], work, token)
            if r.returncode:
                raise RuntimeError(r.stderr[-300:])
            subprocess.run(["git", "checkout", "-q", "-B", branch, "FETCH_HEAD"], cwd=work, check=True, capture_output=True)
        else:
            subprocess.run(["git", "checkout", "-q", "--orphan", branch], cwd=work, check=True, capture_output=True)
        target = work / territory / str(run_id)
        target.mkdir(parents=True, exist_ok=True)
        for f in files:
            shutil.copy2(f, target / f.name)
        (target / "ORIGEN.txt").write_text(f"run={run_id} territorio={territory}\n", encoding="utf-8")
        subprocess.run(["git", "add", "-A"], cwd=work, check=True, capture_output=True)
        c = subprocess.run(["git", "commit", "-q", "-m", f"diagnóstico automático: {territory} run {run_id}"],
                           cwd=work, capture_output=True, text=True)
        if c.returncode:
            raise RuntimeError(c.stderr[-300:] or c.stdout[-300:])
        for attempt in range(4):  # runs concurrentes empujan a la misma rama
            p = _git(["push", "-q", "origin", f"HEAD:refs/heads/{branch}"], work, token)
            if p.returncode == 0:
                return
            f = _git(["fetch", "-q", "--depth", "1", "origin", branch], work, token)
            if f.returncode == 0:
                subprocess.run(["git", "rebase", "-q", "FETCH_HEAD"], cwd=work, capture_output=True)
        raise RuntimeError("push fallido: " + p.stderr[-300:])


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--params", required=True)
    ap.add_argument("--cache-dir", required=True, type=Path)
    ap.add_argument("--run-id", required=True)
    ap.add_argument("--repo", default=os.environ.get("GITHUB_REPOSITORY", ""))
    ap.add_argument("--branch", default=BRANCH)
    ap.add_argument("--stage-dir", type=Path)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--strict", action="store_true")
    a = ap.parse_args()
    territory = territory_of(a.params)
    try:
        with tempfile.TemporaryDirectory() as td:
            stage = a.stage_dir or Path(td) / "stage"
            files = collect(a.cache_dir, stage)
            print(f"Diagnóstico automático {territory}/{a.run_id}: {[f.name for f in files]}")
            if not a.dry_run:
                publish(files, territory, a.run_id, a.repo, a.branch, os.environ.get("GH_TOKEN", ""))
                print(f"::notice::Diagnóstico subido a {a.branch}/{territory}/{a.run_id}")
    except Exception as exc:  # best-effort
        print(f"::warning::Diagnóstico automático no publicado: {type(exc).__name__}: {exc}")
        return 1 if a.strict else 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
