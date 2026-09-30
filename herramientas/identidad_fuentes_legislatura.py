from __future__ import annotations

import hashlib
import json
import re
from typing import Any

SHA256 = re.compile(r"^[0-9a-f]{64}$")


class PreparedSourceIdentityBlock(ValueError):
    pass


def digest(value: Any, *, label: str) -> str:
    raw = str(value or "").strip().lower().removeprefix("sha256:")
    if not SHA256.fullmatch(raw):
        raise PreparedSourceIdentityBlock(f"{label}: SHA-256 durable inválido")
    return raw


def canonical_sha256(payload: dict) -> str:
    raw = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def territorial_identity(
    *,
    territory_id: str,
    edition: str,
    population_year: int,
    section_year: int,
    package_sha256: str,
    compatibility_identity_sha256: str | None = None,
) -> dict:
    payload = {
        "territory_id": str(territory_id),
        "edition": str(edition),
        "population_year": int(population_year),
        "section_year": int(section_year),
        "package_sha256": digest(package_sha256, label="territorial.package_sha256"),
    }
    if compatibility_identity_sha256 is not None:
        payload["compatibility_identity_sha256"] = digest(
            compatibility_identity_sha256,
            label="territorial.compatibility_identity_sha256",
        )
    return {
        **payload,
        "territorial_identity_sha256": canonical_sha256(payload),
    }


def electoral_identity(
    *,
    territory_id: str,
    edition: str,
    election_id: str,
    election_date: str,
    artifact_sha256: str,
) -> dict:
    payload = {
        "territory_id": str(territory_id),
        "edition": str(edition),
        "election_id": str(election_id),
        "election_date": str(election_date),
        "artifact_sha256": digest(artifact_sha256, label="electoral.artifact_sha256"),
    }
    return {
        **payload,
        "electoral_identity_sha256": canonical_sha256(payload),
    }


def geometric_reuse_compatible(
    *,
    product_territorial_identity_sha256: str | None,
    current_territorial_identity_sha256: str,
) -> bool:
    current = digest(
        current_territorial_identity_sha256,
        label="current.territorial_identity_sha256",
    )
    if not product_territorial_identity_sha256:
        return False
    historical = digest(
        product_territorial_identity_sha256,
        label="product.territorial_identity_sha256",
    )
    return historical == current
