#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PROYECTO: Diputado de Distrito
COMPONENTE: comprobación automática de fuente electoral oficial
VERSIÓN: 1.3.0
FECHA: 2026-09-17
FUNCIÓN: consultar fuentes electorales declaradas y admitir fuentes oficiales o mirrors auditables con referencias oficiales explícitas.
REGLAS: no admite sustitutos no oficiales; RTVE queda excluida mediante política declarativa y validación de host/editor.
CAMBIOS: añade selection_mode=all_required para convocatorias publicadas en varios ficheros oficiales.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import mimetypes
import re
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Callable

import yaml

RESOLUTION_RANK = {
    "none": 0,
    "constituency": 1,
    "municipality": 2,
    "section": 3,
    "polling_station": 4,
}


def _norm(value: object) -> str:
    return str(value or "").strip().lower()


def load_declaration(path: str | Path) -> dict:
    data = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise ValueError("La declaración electoral debe ser un objeto YAML")
    for key in ("schema", "territory_id", "election_id", "minimum_resolution", "sources"):
        if data.get(key) in (None, "", []):
            raise ValueError(f"Falta {key} en la declaración electoral")
    allowed = data.get("allowed_official_hosts") or data.get("allowed_source_hosts")
    if not allowed:
        raise ValueError("Falta allowed_official_hosts/allowed_source_hosts en la declaración electoral")
    if data["minimum_resolution"] not in RESOLUTION_RANK:
        raise ValueError("minimum_resolution desconocida")
    if not isinstance(data["sources"], list) or not data["sources"]:
        raise ValueError("sources debe ser una lista no vacía")
    mode = str(data.get("selection_mode") or "first_ready")
    if mode not in {"first_ready", "all_required"}:
        raise ValueError("selection_mode desconocido")
    return data


def _host_allowed(url: str, allowed_hosts: list[str]) -> bool:
    host = (urllib.parse.urlparse(url).hostname or "").lower()
    return any(host == h.lower() or host.endswith("." + h.lower()) for h in allowed_hosts)


def _forbidden(source: dict, forbidden: list[str]) -> str | None:
    haystack = " ".join([str(source.get("publisher") or ""), str(source.get("url") or "")]).lower()
    for token in forbidden:
        if str(token).lower() in haystack:
            return str(token)
    return None


def _content_type(response) -> str:
    headers = getattr(response, "headers", None)
    if headers is None:
        return ""
    try:
        return str(headers.get("Content-Type") or "").split(";", 1)[0].strip().lower()
    except Exception:
        return ""


def _read_limited(response, max_bytes: int) -> bytes:
    data = response.read(max_bytes + 1)
    if len(data) > max_bytes:
        raise ValueError(f"La descarga supera max_bytes={max_bytes}")
    return data


def _looks_html(data: bytes, content_type: str) -> bool:
    head = data[:512].lstrip().lower()
    return "html" in content_type or head.startswith(b"<!doctype html") or head.startswith(b"<html")


def _has_granularity_marker(data: bytes, markers: list[str]) -> bool:
    if not markers:
        return True
    sample = data[:65536].decode("utf-8", errors="ignore").lower()
    return any(re.search(rf"(^|[^a-z0-9_]){re.escape(str(marker).lower())}([^a-z0-9_]|$)", sample) for marker in markers)


def _filename(source: dict, content_type: str) -> str:
    source_id = re.sub(r"[^a-zA-Z0-9_.-]+", "_", str(source.get("id") or "source"))
    path = urllib.parse.urlparse(str(source.get("url") or "")).path
    ext = Path(path).suffix
    if not ext:
        ext = mimetypes.guess_extension(content_type) or ".bin"
    return source_id + ext


def check_declaration(
    declaration: dict,
    out_dir: str | Path,
    *,
    opener: Callable = urllib.request.urlopen,
    timeout: int = 20,
) -> dict:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    downloads = out / "downloads"
    downloads.mkdir(parents=True, exist_ok=True)
    allowed_hosts = [str(x) for x in (declaration.get("allowed_official_hosts") or declaration.get("allowed_source_hosts") or [])]
    official_reference_urls = [str(x) for x in declaration.get("official_reference_urls") or []]
    forbidden = [str(x) for x in declaration.get("forbidden_substitutes") or []]
    required = str(declaration["minimum_resolution"])
    required_rank = RESOLUTION_RANK[required]
    max_bytes = int(declaration.get("max_download_bytes") or 50_000_000)
    results = []
    ready = None
    ready_items = []
    selection_mode = str(declaration.get("selection_mode") or "first_ready")

    for source in declaration["sources"]:
        if not isinstance(source, dict):
            raise ValueError("Cada fuente debe ser un objeto")
        sid = str(source.get("id") or "")
        url = str(source.get("url") or "")
        publisher = str(source.get("publisher") or "")
        resolution = str(source.get("declared_resolution") or "none")
        access = str(source.get("access") or "public")
        source_class = str(source.get("source_class") or "official")
        item = {
            "id": sid,
            "publisher": publisher,
            "url": url,
            "declared_resolution": resolution,
            "access": access,
            "required": bool(source.get("required", True)),
            "source_class": source_class,
        }
        if source_class not in {"official", "verified_mirror"}:
            item.update(status="BLOCK_SOURCE_CLASS", reason=f"source_class no soportada: {source_class}")
            results.append(item)
            continue
        if source_class == "verified_mirror" and not official_reference_urls:
            item.update(status="BLOCK_MISSING_OFFICIAL_REFERENCE", reason="Mirror sin referencias oficiales de la elección")
            results.append(item)
            continue
        forbidden_token = _forbidden(source, forbidden)
        if forbidden_token:
            item.update(status="BLOCK_FORBIDDEN_SUBSTITUTE", reason=f"Fuente prohibida por política: {forbidden_token}")
            results.append(item)
            continue
        if not url or not _host_allowed(url, allowed_hosts):
            item.update(status="BLOCK_NOT_OFFICIAL_HOST", reason="Host no incluido en allowed_official_hosts")
            results.append(item)
            continue
        if resolution not in RESOLUTION_RANK:
            item.update(status="BLOCK_INVALID_RESOLUTION", reason=f"Resolución desconocida: {resolution}")
            results.append(item)
            continue

        request = urllib.request.Request(url, headers={"User-Agent": "DDD-official-election-source-check/1.0"})
        data = b""
        content_type = ""
        http_status = None
        try:
            with opener(request, timeout=timeout) as response:
                http_status = getattr(response, "status", 200)
                content_type = _content_type(response)
                data = _read_limited(response, max_bytes)
        except urllib.error.HTTPError as exc:
            http_status = exc.code
            if exc.code in (401, 403):
                item.update(status="BLOCK_CREDENTIALS", http_status=exc.code, reason="La fuente oficial exige autenticación o credenciales")
            else:
                item.update(status="BLOCK_UNAVAILABLE", http_status=exc.code, reason=f"HTTP {exc.code}")
            results.append(item)
            continue
        except Exception as exc:
            item.update(status="BLOCK_UNAVAILABLE", reason=f"{type(exc).__name__}: {exc}")
            results.append(item)
            continue

        item["http_status"] = http_status
        item["content_type"] = content_type
        item["bytes_received"] = len(data)
        if access == "credentials_required":
            item.update(status="BLOCK_CREDENTIALS", reason="La declaración oficial exige credenciales aunque el endpoint responda")
            results.append(item)
            continue
        if RESOLUTION_RANK[resolution] < required_rank:
            item.update(status="BLOCK_GRANULARITY", reason=f"Granularidad {resolution} inferior a {required}")
            results.append(item)
            continue
        if not data:
            item.update(status="BLOCK_EMPTY", reason="La fuente respondió sin contenido")
            results.append(item)
            continue
        if _looks_html(data, content_type):
            item.update(status="BLOCK_NOT_DATA_FILE", reason="La respuesta es HTML y no un fichero electoral desagregado")
            results.append(item)
            continue
        markers = [str(x) for x in source.get("granularity_markers") or []]
        if not _has_granularity_marker(data, markers):
            item.update(status="BLOCK_GRANULARITY", reason="El fichero no contiene marcadores de sección/mesa declarados")
            results.append(item)
            continue

        name = _filename(source, content_type)
        target = downloads / name
        target.write_bytes(data)
        sha = hashlib.sha256(data).hexdigest()
        checksum = downloads / f"{name}.sha256"
        checksum.write_text(f"{sha}  {name}\n", encoding="utf-8")
        item.update(
            status="READY",
            downloaded_path=target.as_posix(),
            artifact_path=(Path("downloads") / name).as_posix(),
            checksum_path=(Path("downloads") / f"{name}.sha256").as_posix(),
            sha256=sha,
            bytes=len(data),
        )
        results.append(item)
        ready = item
        ready_items.append(item)
        if selection_mode == "first_ready":
            break

    if selection_mode == "all_required":
        required_rows = [row for row in results if row.get("required")]
        complete = bool(required_rows) and all(row.get("status") == "READY" for row in required_rows)
        selected_sources = [row for row in required_rows if row.get("status") == "READY"]
        ready = None
    else:
        complete = ready is not None
        selected_sources = [ready] if ready else []

    decision = {
        "schema": "ddd-election-source-decision/1.1",
        "territory_id": declaration["territory_id"],
        "election_id": declaration["election_id"],
        "minimum_resolution": required,
        "rtve_allowed_as_substitute": False,
        "official_reference_urls": official_reference_urls,
        "selection_mode": selection_mode,
        "decision": "READY" if complete else "BLOCK",
        "selected_source": ready,
        "selected_sources": selected_sources,
        "checks": results,
    }
    decision_path = out / "decision_fuente_electoral.json"
    decision_path.write_text(json.dumps(decision, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    report = [
        "# Comprobación automática de fuente electoral oficial",
        "",
        f"- territorio: `{decision['territory_id']}`",
        f"- elección: `{decision['election_id']}`",
        f"- resolución mínima: `{required}`",
        f"- decisión: **{decision['decision']}**",
        "- RTVE como sustituto: **no permitido**",
        f"- referencias oficiales: **{len(official_reference_urls)}**",
        "",
        "## Fuentes consultadas",
    ]
    for row in results:
        report.append(f"- `{row['id']}` — {row['status']} — {row.get('reason') or row.get('sha256') or ''}")
    (out / "informe_fuente_electoral.md").write_text("\n".join(report) + "\n", encoding="utf-8")
    return decision


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--declaration", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--timeout", type=int, default=20)
    args = ap.parse_args()
    declaration = load_declaration(args.declaration)
    decision = check_declaration(declaration, args.out_dir, timeout=args.timeout)
    print(json.dumps({"decision": decision["decision"], "selected_source": decision["selected_source"], "selected_sources": decision.get("selected_sources") or []}, ensure_ascii=False))


if __name__ == "__main__":
    main()
