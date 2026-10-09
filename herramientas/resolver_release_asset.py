#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def _as_list(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        rows = payload
    elif isinstance(payload, dict) and isinstance(payload.get("releases"), list):
        rows = payload["releases"]
    else:
        raise ValueError("Payload de releases inválido")
    return [row for row in rows if isinstance(row, dict)]


def resolve_release(releases: Any, tag_name: str) -> dict[str, Any] | None:
    matches = [
        row for row in _as_list(releases)
        if row.get("tag_name") == tag_name
    ]
    if not matches:
        return None
    if len(matches) != 1:
        raise ValueError(
            f"release tag {tag_name!r}: esperaba 0 o 1 releases; encontrados={len(matches)}"
        )
    release = matches[0]
    release_id = release.get("id")
    if not isinstance(release_id, int) or release_id <= 0:
        raise ValueError(f"release tag {tag_name!r}: release id inválido")
    if release.get("tag_name") != tag_name:
        raise ValueError(f"release id {release_id}: tag_name no coincide")
    return release


def resolve_asset(release: dict[str, Any], asset_name: str) -> dict[str, Any] | None:
    assets = release.get("assets")
    if not isinstance(assets, list):
        raise ValueError("release sin lista de assets")
    matches = [
        row for row in assets
        if isinstance(row, dict) and row.get("name") == asset_name
    ]
    if not matches:
        return None
    if len(matches) != 1:
        raise ValueError(
            f"asset {asset_name!r}: esperaba 0 o 1 activos; encontrados={len(matches)}"
        )
    asset = matches[0]
    asset_id = asset.get("id")
    if not isinstance(asset_id, int) or asset_id <= 0:
        raise ValueError(f"asset {asset_name!r}: asset id inválido")
    return asset


def require_release(releases: Any, tag_name: str) -> dict[str, Any]:
    release = resolve_release(releases, tag_name)
    if release is None:
        raise ValueError(f"release tag {tag_name!r}: release inexistente")
    return release


def require_asset(release: dict[str, Any], asset_name: str) -> dict[str, Any]:
    asset = resolve_asset(release, asset_name)
    if asset is None:
        raise ValueError(f"asset {asset_name!r}: activo inexistente")
    return asset


def validate_downloaded_sha(expected_sha256: str, observed_sha256: str) -> None:
    if expected_sha256 != observed_sha256:
        raise ValueError(
            "SHA-256 distinto: "
            f"esperado={expected_sha256} observado={observed_sha256}"
        )


def decide_release_action(releases: Any, tag_name: str) -> str:
    return "create" if resolve_release(releases, tag_name) is None else "reuse"


def decide_asset_action(release: dict[str, Any], asset_name: str) -> str:
    return "upload" if resolve_asset(release, asset_name) is None else "reuse"


def _load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> None:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)

    release = sub.add_parser("release")
    release.add_argument("--releases", type=Path, required=True)
    release.add_argument("--tag", required=True)

    asset = sub.add_parser("asset")
    asset.add_argument("--release", type=Path, required=True)
    asset.add_argument("--name", required=True)

    args = parser.parse_args()
    try:
        if args.command == "release":
            row = resolve_release(_load(args.releases), args.tag)
        else:
            row = resolve_asset(_load(args.release), args.name)
    except ValueError as exc:
        raise SystemExit(str(exc))

    if row is None:
        raise SystemExit(3)
    print(json.dumps(row, ensure_ascii=False, separators=(",", ":")))


if __name__ == "__main__":
    main()
