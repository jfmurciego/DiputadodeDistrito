#!/usr/bin/env python3
"""PR A: selección nacional y manifiesto inmutable, sin ejecución productiva."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

import yaml

SCHEMA = "ddd.campaign-selection/2.0-pr-a"
MAX_PARALLEL = 5
CANONICAL_IDS = (
    "andalucia", "aragon", "principado_de_asturias", "illes_balears", "canarias",
    "cantabria", "castilla_la_mancha", "castilla_y_leon", "cataluna",
    "comunidad_valenciana", "extremadura", "galicia", "madrid",
    "region_de_murcia", "comunidad_foral_de_navarra", "pais_vasco", "la_rioja",
    "ceuta", "melilla",
)


def _catalog(root: Path) -> dict[str, Any]:
    data = yaml.safe_load((root / "configuracion/catalogo_preparacion.yaml").read_text(encoding="utf-8")) or {}
    if not isinstance(data.get("territories"), list):
        raise ValueError("Catálogo territorial inválido")
    return data


def _catalog_index(root: Path, edition: str) -> dict[str, dict[str, Any]]:
    index: dict[str, dict[str, Any]] = {}
    for row in _catalog(root)["territories"]:
        tid = row.get("territory_id")
        edition_row = (row.get("editions") or {}).get(str(edition))
        if tid and isinstance(edition_row, dict):
            index[str(tid)] = {"name": row.get("name"), **edition_row}
    return index


def build_selection_manifest(root: Path, selected_ids: list[str], *, edition: str,
                             execution_mode: str, strategy: str, source_sha: str,
                             campaign_instance: str) -> dict[str, Any]:
    selected = set(selected_ids)
    if len(selected) != len(selected_ids):
        raise ValueError("Selección territorial duplicada")
    unknown = selected.difference(CANONICAL_IDS)
    if unknown:
        raise ValueError(f"Territorios no canónicos: {sorted(unknown)}")
    if not 1 <= len(selected) <= 19:
        raise ValueError("Seleccione entre 1 y 19 territorios")
    if len(source_sha) != 40 or any(c not in "0123456789abcdef" for c in source_sha.lower()):
        raise ValueError("source_sha debe ser SHA-1 hexadecimal de 40 caracteres")

    catalog = _catalog_index(root, edition)
    territories: list[dict[str, Any]] = []
    for slot_number, tid in enumerate((x for x in CANONICAL_IDS if x in selected), start=1):
        entry = catalog.get(tid)
        if not entry:
            raise ValueError(f"Catálogo sin {tid}/{edition}")
        contract_path = entry.get("contract_path")
        if not contract_path:
            raise ValueError(f"Catálogo sin contract_path para {tid}/{edition}")
        if not (root / str(contract_path)).is_file():
            raise ValueError(f"Contrato no encontrado para {tid}: {contract_path}")
        territories.append({
            "slot": f"{slot_number:02d}",
            "territory_id": tid,
            "territory_name": entry.get("name"),
            "contract_path": contract_path,
        })

    manifest = {
        "schema": SCHEMA,
        "campaign_instance": campaign_instance,
        "source_sha": source_sha.lower(),
        "data_edition": str(edition),
        "execution_mode": execution_mode,
        "optimization_algorithm": strategy,
        "fail_fast": False,
        "max_parallel": MAX_PARALLEL,
        "publish_result": False,
        "persist_state": False,
        "production_execution_enabled": False,
        "production_block_reason": "PR_A_CLOSEOUT_STILL_LIMITED_TO_FIVE",
        "territories": territories,
    }
    canonical = json.dumps(manifest, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    manifest["manifest_sha256"] = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    return manifest


def matrix_from_manifest(manifest: dict[str, Any]) -> dict[str, Any]:
    common = {
        "data_edition": manifest["data_edition"],
        "execution_mode": manifest["execution_mode"],
        "optimization_algorithm": manifest["optimization_algorithm"],
        "source_sha": manifest["source_sha"],
        "campaign_instance": manifest["campaign_instance"],
        "manifest_sha256": manifest["manifest_sha256"],
        "publish_result": False,
        "persist_state": False,
    }
    return {"include": [{**common, **row} for row in manifest["territories"]]}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--selected", nargs="*", default=[])
    parser.add_argument("--edition", default="2025")
    parser.add_argument("--execution-mode", default="Reutilizar progreso existente")
    parser.add_argument("--strategy", default="GerryChain 50")
    parser.add_argument("--source-sha", required=True)
    parser.add_argument("--campaign-instance", required=True)
    parser.add_argument("--output-manifest", required=True)
    args = parser.parse_args()
    manifest = build_selection_manifest(Path(args.root), args.selected, edition=args.edition,
        execution_mode=args.execution_mode, strategy=args.strategy, source_sha=args.source_sha,
        campaign_instance=args.campaign_instance)
    output = Path(args.output_manifest)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(matrix_from_manifest(manifest), ensure_ascii=False, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
