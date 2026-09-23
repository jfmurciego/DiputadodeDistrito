#!/usr/bin/env python3
"""Promoción verificable de un activo a un GitHub draft release.

Resuelve releases por el listado /releases (que incluye drafts), nunca por
/releases/tags/<tag>. La identidad durable es release_id + tag_name y la del
activo es asset_id + nombre. La republicación es idempotente: un activo ya
existente se verifica y nunca se sustituye.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Callable


class PromotionError(RuntimeError):
    pass


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def exactly_one_release(releases: list[dict], tag: str) -> dict | None:
    matches = [r for r in releases if r.get("tag_name") == tag]
    if len(matches) > 1:
        raise PromotionError(f"tag {tag}: se esperaban 0/1 releases; encontrados={len(matches)}")
    return matches[0] if matches else None


def exactly_one_asset(release: dict, asset_name: str, *, allow_zero: bool) -> dict | None:
    matches = [a for a in release.get("assets", []) if a.get("name") == asset_name]
    if len(matches) > 1 or (not allow_zero and len(matches) != 1):
        expected = "0/1" if allow_zero else "1"
        raise PromotionError(
            f"release {release.get('id')}/{release.get('tag_name')}: "
            f"se esperaban {expected} assets {asset_name}; encontrados={len(matches)}"
        )
    return matches[0] if matches else None


class GhApi:
    def __init__(self, run: Callable[..., subprocess.CompletedProcess] = subprocess.run):
        self.run = run

    def _json(self, args: list[str], *, input_text: str | None = None) -> object:
        cp = self.run(
            ["gh", "api", *args], check=True, capture_output=True, text=True,
            input=input_text,
        )
        return json.loads(cp.stdout)

    def list_releases(self, repo: str) -> list[dict]:
        # /releases incluye publicados y drafts. --paginate evita depender de la
        # primera página si el repositorio acumula releases.
        cp = self.run(
            ["gh", "api", "--paginate", f"repos/{repo}/releases?per_page=100"],
            check=True, capture_output=True, text=True,
        )
        pages = [json.loads(line) for line in cp.stdout.splitlines() if line.strip()]
        if not pages:
            return []
        if all(isinstance(page, list) for page in pages):
            return [item for page in pages for item in page]
        raise PromotionError("respuesta inesperada al listar releases")

    def create_draft(self, repo: str, tag: str, target: str) -> dict:
        payload = json.dumps({
            "tag_name": tag,
            "target_commitish": target,
            "name": tag,
            "body": "Activo persistente e inmutable del visor DDD; no sustituir ni clobber.",
            "draft": True,
            "prerelease": False,
        })
        result = self._json(["--method", "POST", f"repos/{repo}/releases", "--input", "-"], input_text=payload)
        if not isinstance(result, dict):
            raise PromotionError("creación de release sin objeto de respuesta")
        return result

    def release_by_id(self, repo: str, release_id: int) -> dict:
        result = self._json([f"repos/{repo}/releases/{release_id}"])
        if not isinstance(result, dict):
            raise PromotionError("release por ID inválido")
        return result

    def upload_asset(self, repo: str, release_id: int, asset_name: str, source: Path) -> dict:
        cp = self.run(
            [
                "gh", "api", "--method", "POST", "--hostname", "uploads.github.com",
                "-H", "Content-Type: application/octet-stream",
                f"repos/{repo}/releases/{release_id}/assets?name={asset_name}",
                "--input", str(source),
            ],
            check=True, capture_output=True, text=True,
        )
        result = json.loads(cp.stdout)
        if not isinstance(result, dict):
            raise PromotionError("upload de asset sin objeto de respuesta")
        return result

    def download_asset(self, repo: str, asset_id: int, target: Path) -> None:
        with target.open("wb") as out:
            self.run(
                [
                    "gh", "api", "-H", "Accept: application/octet-stream",
                    f"repos/{repo}/releases/assets/{asset_id}",
                ],
                check=True, stdout=out,
            )


def promote(
    api: GhApi,
    *,
    repo: str,
    tag: str,
    target_commit: str,
    asset_name: str,
    source: Path,
    verify_path: Path,
) -> dict:
    expected_sha = sha256_file(source)
    release = exactly_one_release(api.list_releases(repo), tag)
    created = False
    if release is None:
        created_release = api.create_draft(repo, tag, target_commit)
        if created_release.get("tag_name") != tag or not isinstance(created_release.get("id"), int):
            raise PromotionError("release creado no conserva id + tag_name solicitados")
        created = True
        # Re-resolver desde /releases prueba que el draft recién creado es
        # visible por el mismo mecanismo usado para reutilizaciones.
        release = exactly_one_release(api.list_releases(repo), tag)
        if release is None:
            raise PromotionError(f"draft recién creado no resoluble: {tag}")

    release_id = release.get("id")
    if not isinstance(release_id, int) or release.get("tag_name") != tag:
        raise PromotionError("release no identificado inequívocamente por id + tag_name")

    asset = exactly_one_asset(release, asset_name, allow_zero=True)
    uploaded = False
    if asset is None:
        api.upload_asset(repo, release_id, asset_name, source)
        uploaded = True

    current = api.release_by_id(repo, release_id)
    if current.get("id") != release_id or current.get("tag_name") != tag:
        raise PromotionError("release cambió de identidad durante la promoción")
    asset = exactly_one_asset(current, asset_name, allow_zero=False)
    asset_id = asset.get("id")
    if not isinstance(asset_id, int):
        raise PromotionError("asset único sin asset_id entero")

    verify_path.parent.mkdir(parents=True, exist_ok=True)
    api.download_asset(repo, asset_id, verify_path)
    observed_sha = sha256_file(verify_path)
    if observed_sha != expected_sha:
        raise PromotionError(
            f"SHA-256 distinto para asset {asset_id}: esperado={expected_sha} observado={observed_sha}"
        )
    return {
        "release_id": release_id,
        "release_tag": tag,
        "release_draft": bool(current.get("draft")),
        "asset_id": asset_id,
        "asset_name": asset_name,
        "sha256": expected_sha,
        "created_release": created,
        "uploaded_asset": uploaded,
    }


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--repository", required=True)
    p.add_argument("--tag", required=True)
    p.add_argument("--target-commit", required=True)
    p.add_argument("--asset-name", required=True)
    p.add_argument("--source", type=Path, required=True)
    p.add_argument("--verify-path", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    result = promote(
        GhApi(), repo=a.repository, tag=a.tag, target_commit=a.target_commit,
        asset_name=a.asset_name, source=a.source, verify_path=a.verify_path,
    )
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
