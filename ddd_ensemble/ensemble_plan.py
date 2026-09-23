from __future__ import annotations

import hashlib
import json
from typing import Any


SCHEMA = "ddd.ensemble-plan/1.0"
GERRYCHAIN50_ENTRYPOINT = "gerrychain_50"
GERRYCHAIN50_CANDIDATE_COUNT = 50
GERRYCHAIN50_MANAGER_CONTRACT_SCHEMA = "ddd.gerrychain50-manager-contract/1.0"

PROFILES: dict[str, dict[str, float]] = {
    "balanced": {"population": 1.00, "shape": 0.55, "comarca": 0.20, "comarca_surcharge": 0.00},
    "comarca": {"population": 1.00, "shape": 0.55, "comarca": 0.80, "comarca_surcharge": 0.30},
    "comarca_strong": {"population": 1.00, "shape": 0.50, "comarca": 1.20, "comarca_surcharge": 0.60},
    "shape": {"population": 1.00, "shape": 1.20, "comarca": 0.45, "comarca_surcharge": 0.20},
    "exploratory": {"population": 1.00, "shape": 0.80, "comarca": 0.65, "comarca_surcharge": 0.40},
}


def _seed(*parts: str) -> int:
    digest = hashlib.sha256("|".join(parts).encode("utf-8")).digest()
    return int.from_bytes(digest[:4], "big") & 0x7FFFFFFF


def build_plan(
    territory_id: str,
    prepared_bundle_id: str,
    count: int = 50,
    *,
    seed: int | None = None,
    require_unique_hashes: bool | None = None,
) -> dict[str, Any]:
    if not territory_id or not prepared_bundle_id:
        raise ValueError("territory_id y prepared_bundle_id son obligatorios")
    if count < 5 or count % 5:
        raise ValueError("El tamaño debe ser múltiplo de cinco y al menos cinco")
    if seed is not None and isinstance(seed, bool):
        raise ValueError("seed debe ser entero")
    if require_unique_hashes is None:
        require_unique_hashes = count == 50

    per_profile = count // len(PROFILES)
    candidates: list[dict[str, Any]] = []
    shards: list[dict[str, Any]] = []
    for shard_index, (profile, base_parameters) in enumerate(PROFILES.items(), start=1):
        shard_ids: list[str] = []
        for ordinal in range(1, per_profile + 1):
            candidate_id = f"{profile}-{ordinal:02d}"
            parameters = dict(base_parameters)
            if profile == "exploratory":
                parameters["shape"] = round(0.45 + 0.10 * ((ordinal - 1) % 6), 2)
                parameters["comarca"] = round(0.35 + 0.15 * ((ordinal + 1) % 6), 2)
                parameters["comarca_surcharge"] = round(0.10 + 0.15 * ((ordinal - 1) % 5), 2)
            seed_parts = [territory_id, prepared_bundle_id, candidate_id]
            if seed is not None:
                seed_parts.insert(0, str(int(seed)))
            candidate = {
                "candidate_id": candidate_id,
                "profile": profile,
                "ordinal": ordinal,
                "seed": _seed(*seed_parts),
                "parameters": parameters,
            }
            candidates.append(candidate)
            shard_ids.append(candidate_id)
        shards.append({"shard": shard_index, "profile": profile, "candidate_ids": shard_ids})

    requirements = {"unique_assignment_hashes": bool(require_unique_hashes)}
    canonical = json.dumps(
        {"seed": seed, "requirements": requirements, "candidates": candidates},
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return {
        "schema": SCHEMA,
        "territory_id": territory_id,
        "prepared_bundle_id": prepared_bundle_id,
        "candidate_count": count,
        "seed": seed,
        "requirements": requirements,
        "profiles": list(PROFILES),
        "plan_sha256": hashlib.sha256(canonical.encode("utf-8")).hexdigest(),
        "candidates": candidates,
        "shards": shards,
        "github_matrix": {"include": shards},
    }



def gerrychain50_manager_contract(*, seed: int) -> dict[str, Any]:
    """Contrato estricto que debe consumir el gestor para GerryChain 50."""
    if isinstance(seed, bool) or not isinstance(seed, int):
        raise ValueError("GerryChain 50 requiere una semilla entera")
    return {
        "schema": GERRYCHAIN50_MANAGER_CONTRACT_SCHEMA,
        "entrypoint": GERRYCHAIN50_ENTRYPOINT,
        "candidate_count": GERRYCHAIN50_CANDIDATE_COUNT,
        "seed": int(seed),
        "require_unique_hashes": True,
    }


def build_gerrychain50_plan(
    territory_id: str,
    prepared_bundle_id: str,
    *,
    seed: int,
    candidate_count: int = GERRYCHAIN50_CANDIDATE_COUNT,
    require_unique_hashes: bool = True,
) -> dict[str, Any]:
    """Punto de entrada estricto: exactamente 50 candidatos y 50 hashes únicos."""
    if candidate_count != GERRYCHAIN50_CANDIDATE_COUNT:
        raise ValueError(
            f"GerryChain 50 exige candidate_count={GERRYCHAIN50_CANDIDATE_COUNT}"
        )
    if require_unique_hashes is not True:
        raise ValueError("GerryChain 50 exige require_unique_hashes=true")
    manager = gerrychain50_manager_contract(seed=seed)
    plan = build_plan(
        territory_id,
        prepared_bundle_id,
        GERRYCHAIN50_CANDIDATE_COUNT,
        seed=seed,
        require_unique_hashes=True,
    )
    plan["entrypoint"] = GERRYCHAIN50_ENTRYPOINT
    plan["manager_contract"] = manager
    plan["requirements"]["candidate_count_exact"] = GERRYCHAIN50_CANDIDATE_COUNT
    strict_canonical = json.dumps(
        {
            "entrypoint": GERRYCHAIN50_ENTRYPOINT,
            "manager_contract": manager,
            "base_plan_sha256": plan["plan_sha256"],
        },
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    plan["plan_sha256"] = hashlib.sha256(strict_canonical.encode("utf-8")).hexdigest()
    return plan
