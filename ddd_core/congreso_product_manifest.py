"""Strict manifest contract for a source-bound Congress candidate product.

This describes evidence only. A valid manifest never authorizes generation.
"""
from __future__ import annotations

import hashlib
import json
import re
from typing import Any, Mapping, Sequence

SCHEMA = "ddd.congreso-candidate-product/1.0"
_SHA256 = re.compile(r"[0-9a-f]{64}\Z")
_FIELDS = frozenset({
    "schema", "synthetic_fixture", "generation_authorized", "contract_sha256",
    "source_binding", "nodes_sha256", "edges_sha256", "assignments_sha256",
    "topology_manifest_sha256",
})


def _canonical_sha(value: Any) -> str:
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":"), allow_nan=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def build_candidate_manifest(contract: Mapping[str, Any], source_binding: Mapping[str, Any],
                             nodes: Sequence[Mapping[str, Any]],
                             edges: Sequence[Mapping[str, Any]],
                             assignments: Sequence[Mapping[str, Any]],
                             topology_manifest_sha256: str) -> dict[str, Any]:
    """Create the canonical, generation-disabled manifest for an audited candidate."""
    if not isinstance(topology_manifest_sha256, str) or not _SHA256.fullmatch(topology_manifest_sha256):
        raise ValueError("TOPOLOGY_MANIFEST_SHA256_INVALID")
    sources = contract.get("sources")
    if not isinstance(sources, Mapping) or set(sources) != {"geometry", "population"}:
        raise ValueError("CONTRACT_SOURCES_INVALID")
    expected_binding = {}
    for role, source in sources.items():
        if (not isinstance(source, Mapping) or source.get("edition") != 2025
                or type(source.get("edition")) is not int
                or not isinstance(source.get("sha256"), str)
                or not _SHA256.fullmatch(source["sha256"])):
            raise ValueError("CONTRACT_SOURCE_IDENTITY_INVALID:" + role)
        expected_binding[role] = {"edition": 2025, "sha256": source["sha256"]}
    if dict(source_binding) != expected_binding:
        raise ValueError("PRODUCT_SOURCE_BINDING_MISMATCH")
    return {
        "schema": SCHEMA,
        "synthetic_fixture": False,
        "generation_authorized": False,
        "contract_sha256": _canonical_sha(contract),
        "source_binding": dict(source_binding),
        "nodes_sha256": _canonical_sha(list(nodes)),
        "edges_sha256": _canonical_sha(list(edges)),
        "assignments_sha256": _canonical_sha(list(assignments)),
        "topology_manifest_sha256": topology_manifest_sha256,
    }


def validate_candidate_manifest(manifest: Mapping[str, Any], *, contract: Mapping[str, Any],
                                source_binding: Mapping[str, Any],
                                nodes: Sequence[Mapping[str, Any]],
                                edges: Sequence[Mapping[str, Any]],
                                assignments: Sequence[Mapping[str, Any]],
                                trusted_topology_manifest_sha256: str) -> None:
    """Fail closed unless exact keys and hashes bind this candidate to trusted inputs."""
    if not isinstance(manifest, Mapping) or set(manifest) != _FIELDS:
        raise ValueError("PRODUCT_MANIFEST_FIELDS_INVALID")
    expected = build_candidate_manifest(contract, source_binding, nodes, edges,
                                        assignments, trusted_topology_manifest_sha256)
    if manifest.get("schema") != SCHEMA or type(manifest.get("synthetic_fixture")) is not bool \
            or manifest["synthetic_fixture"] is not False \
            or type(manifest.get("generation_authorized")) is not bool \
            or manifest["generation_authorized"] is not False:
        raise ValueError("PRODUCT_MANIFEST_IDENTITY_INVALID")
    if dict(manifest) != expected:
        raise ValueError("PRODUCT_MANIFEST_BINDING_MISMATCH")
