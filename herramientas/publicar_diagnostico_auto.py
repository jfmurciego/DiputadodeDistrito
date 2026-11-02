#!/usr/bin/env python3
"""Empaqueta y publica el diagnóstico automático de una 00 fallida (T-14).

PROYECTO: Diputado de Distrito
VERSIÓN: 1.1.0 · FECHA: 2026-11-02 · ESTADO: candidato
QUÉ HACE: busca en la caché del territorio el M01 (secciones y población), el grafo M03 (se comprime a .gz) y
  el informe M05, los copia a <territorio>/<run>/ y los sube a la rama `diagnostico/auto` para que los chats
  ejecuten el motor en local sin descargar artefactos (403 desde la nube). Falla en silencio útil: es
  best-effort y nunca oculta el fallo original (salida 0 salvo --strict).
MOTIVO: T-14; sustituye a lanzadores/subir_diagnostico_t02.sh, que dependía del Mac del propietario.
CAMBIOS 1.1.0 (T-16, T14-01..05): los ficheros salen de las rutas que declara el contrato del run (nunca por fecha de
  modificación); si falta alguno el paquete se marca PARTIAL; MANIFEST.json con sha256, tamaño, etapa y linaje
  (run y checkpoint); se comprueba el resultado del rebase; un fallo de publicación se anuncia como
  DIAG_PUBLISH_FAILED (anotación y resumen del paso).
ANTERIOR: legacy/herramientas/publicar_diagnostico_auto_v1.0.0_20261102.py
Uso: publicar_diagnostico_auto.py --params P --run-id N [--stage M05 --checkpoint-run-id C] [--repo R --branch B] (token en GH_TOKEN).
Con --dry-run solo empaqueta en --stage-dir.
"""
from __future__ import annotations

import argparse
import base64
import gzip
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

MAX_BYTES = 50 * 1024 * 1024
BRANCH = "diagnostico/auto"
DECLARED = {  # clave -> (módulo del contrato, campo de salida)
    "m01": ("modulo_01_preparar_base_territorial", "out_geojson"),
    "m03": ("modulo_03_construir_grafo", "out_graph_json"),
    "m05": ("modulo_05_optimizar_distritos", "out_report"),
}


def territory_of(params: str) -> str:
    """territorios/<t>/config/<t>_2025.yaml -> <t>."""
    parts = Path(params).parts
    if "territorios" in parts and parts.index("territorios") + 1 < len(parts):
        return parts[parts.index("territorios") + 1]
    return Path(params).stem


def declared_paths(params: str, run_id: str) -> dict[str, Path | None]:
    """Rutas de salida M01, grafo M03 e informe M05 que declara el contrato (linaje explícito, sin mtime)."""
    import yaml
    cfg = yaml.safe_load(Path(params).read_text(encoding="utf-8")) or {}
    meta = cfg.get("meta") or {}
    fmt = {"run_name": meta.get("run_name", Path(params).stem), "year": meta.get("year", ""),
           "run_id": run_id, "scope": meta.get("scope", "")}
    mods = cfg.get("modulos") or {}
    out: dict[str, Path | None] = {}
    for kind, (module, field) in DECLARED.items():
        raw = (mods.get(module) or {}).get(field)
        out[kind] = Path(str(raw).format(**fmt)) if raw else None
    return out


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def collect(paths: dict[str, Path | None], dest: Path, *, meta: dict | None = None) -> list[Path]:
    """Copia a dest los ficheros declarados (el grafo M03 en gzip) y escribe MANIFEST.json.

    El paquete queda PARTIAL si falta alguno de los tres ficheros declarados.
    """
    dest.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    entries: list[dict] = []
    missing: list[str] = []
    for kind in DECLARED:
        src = paths.get(kind)
        if src is None or not src.is_file():
            print(f"::warning::Diagnóstico automático: falta {kind.upper()} ({src})")
            missing.append(kind)
            continue
        if kind == "m03" and src.suffix != ".gz":
            out = dest / (src.name + ".gz")
            with src.open("rb") as fi, out.open("wb") as raw, \
                    gzip.GzipFile(filename="", mode="wb", compresslevel=9, fileobj=raw, mtime=0) as fo:
                shutil.copyfileobj(fi, fo)
        else:
            out = dest / src.name
            shutil.copy2(src, out)
        written.append(out)
        entries.append({"kind": kind, "file": out.name, "source": str(src), "bytes": out.stat().st_size,
                        "sha256": _sha256(out), "source_sha256": _sha256(src)})
    total = sum(p.stat().st_size for p in written)
    if total > MAX_BYTES:
        for p in written:
            p.unlink()
        raise RuntimeError(f"paquete de {total} bytes supera el máximo de {MAX_BYTES}")
    manifest = {"schema": "ddd.diagnostico-auto/1.0", "status": "PARTIAL" if missing else "COMPLETE",
                "missing": missing, "files": entries, **(meta or {})}
    mpath = dest / "MANIFEST.json"
    mpath.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    written.append(mpath)
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
        status = "PARTIAL" if any(f.name == "MANIFEST.json" and '"PARTIAL"' in f.read_text(encoding="utf-8") for f in files) else "COMPLETE"
        subprocess.run(["git", "add", "-A"], cwd=work, check=True, capture_output=True)
        c = subprocess.run(["git", "commit", "-q", "-m", f"diagnóstico automático ({status}): {territory} run {run_id}"],
                           cwd=work, capture_output=True, text=True)
        if c.returncode:
            raise RuntimeError(c.stderr[-300:] or c.stdout[-300:])
        for attempt in range(4):  # runs concurrentes empujan a la misma rama
            p = _git(["push", "-q", "origin", f"HEAD:refs/heads/{branch}"], work, token)
            if p.returncode == 0:
                return
            f = _git(["fetch", "-q", "--depth", "1", "origin", branch], work, token)
            if f.returncode == 0:
                rb = subprocess.run(["git", "rebase", "-q", "FETCH_HEAD"], cwd=work, capture_output=True, text=True)
                if rb.returncode:
                    subprocess.run(["git", "rebase", "--abort"], cwd=work, capture_output=True)
                    raise RuntimeError("rebase fallido: " + (rb.stderr or rb.stdout)[-300:])
        raise RuntimeError("push fallido: " + p.stderr[-300:])


def _announce_failure(territory: str, run_id: str, exc: Exception) -> None:
    msg = f"{territory}/{run_id}: {type(exc).__name__}: {exc}"
    print(f"::error title=DIAG_PUBLISH_FAILED::{msg}")
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary, "a", encoding="utf-8") as fh:
            fh.write(f"### DIAG_PUBLISH_FAILED\n\nNo se publicó el diagnóstico automático: {msg}\n")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--params", required=True)
    ap.add_argument("--run-id", required=True)
    ap.add_argument("--stage", default=os.environ.get("STAGE", ""))
    ap.add_argument("--checkpoint-run-id", default=os.environ.get("CHECKPOINT_RUN_ID", ""))
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
            meta = {"territory": territory, "run_id": a.run_id, "checkpoint_run_id": a.checkpoint_run_id or None,
                    "stage": a.stage or None, "params": a.params}
            files = collect(declared_paths(a.params, a.run_id), stage, meta=meta)
            print(f"Diagnóstico automático {territory}/{a.run_id}: {[f.name for f in files]}")
            if not a.dry_run:
                publish(files, territory, a.run_id, a.repo, a.branch, os.environ.get("GH_TOKEN", ""))
                print(f"::notice::Diagnóstico subido a {a.branch}/{territory}/{a.run_id}")
    except Exception as exc:  # best-effort: nunca oculta el fallo original, pero se hace visible
        _announce_failure(territory, a.run_id, exc)
        return 1 if a.strict else 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
