#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

import yaml

from herramientas.catalogo_preparacion import lookup
from herramientas.promover_catalogo_tras_preparacion import (
    _catalog_state_bounds,
    _catalog_state_indent,
    _replace_key,
)
from herramientas._resolver_ejecucion_completa_core import (
    _bridge_signature,
    _contract_generation_binding,
    _pre_m04_implementation_binding,
)
from herramientas.resolver_ejecucion_completa import generation_enablement

CATALOG = Path("configuracion/catalogo_preparacion.yaml")


def _yaml(path: Path) -> dict:
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise ValueError(f"YAML inválido: {path}")
    return data


def _json(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"JSON inválido: {path}")
    return data


def _find_m03_report(root: Path) -> dict:
    candidates = []
    for path in root.rglob("*.json"):
        try:
            data = _json(path)
        except Exception:
            continue
        if data.get("module") == "03" and "nodes" in data and "edges" in data:
            candidates.append((path, data))
    if len(candidates) != 1:
        raise ValueError(f"M03_REPORT_COUNT: esperada 1 evidencia M03, encontradas {len(candidates)}")
    return candidates[0][1]


def _git_head(root: Path) -> str:
    value = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=root, text=True
    ).strip()
    if len(value) != 40:
        raise ValueError("SOURCE_COMMIT_INVALID")
    return value


def _resolved(path_template: str | None, contract: dict, run_id: int) -> str | None:
    if not path_template:
        return None
    meta = contract.get("meta") or {}
    return str(path_template).format(
        run_name=meta.get("run_name", ""),
        run_id=run_id,
        year=meta.get("year", ""),
    )


def build_evidence(
    *,
    root_dir: Path,
    territory_id: str,
    edition: str,
    run_id: int,
    contract_path: str,
    m03_state_dir: Path,
    partition_job: Path,
    m03_artifact_sha256: str,
    m03u_artifact_sha256: str,
    partition_artifact_sha256: str,
) -> dict:
    root = root_dir.resolve()
    contract_file = root / contract_path
    contract = _yaml(contract_file)
    if (contract.get("meta") or {}).get("territory_id") != territory_id:
        raise ValueError("CONTRACT_IDENTITY_MISMATCH")

    row = lookup(territory_id, str(edition), root / CATALOG)
    prep = row.get("preparation_evidence") or {}
    if prep.get("run_id") != run_id:
        raise ValueError(
            f"SOURCE_RUN_MISMATCH: preparation_evidence.run_id={prep.get('run_id')} run_id={run_id}"
        )
    for key in ("artifact_name", "artifact_sha256", "package_sha256"):
        if not prep.get(key):
            raise ValueError(f"SOURCE_EVIDENCE_INCOMPLETE: {key}")

    report = _find_m03_report(m03_state_dir)
    job = _json(partition_job)
    if job.get("status") not in {"NOOP", "PREPARED"}:
        raise ValueError(f"PARTITION_STATUS_INVALID: {job.get('status')!r}")

    modules = contract.get("modulos") or {}
    m01 = modules.get("modulo_01_preparar_base_territorial") or {}
    m02 = modules.get("modulo_02_construir_adyacencias") or {}
    m04 = modules.get("modulo_04_generar_semillas") or {}
    policy = contract.get("partitioning") or {}

    if job["status"] == "NOOP":
        partitioning = {
            "job_artifact_name": f"ddd-internal-units-{run_id}",
            "job_artifact_sha256": partition_artifact_sha256.removeprefix("sha256:"),
            "status": "NOOP",
            "strategy": None,
            "contract_output_geojson": m04.get("in_geojson"),
            "resolved_output_geojson": _resolved(m04.get("in_geojson"), contract, run_id),
        }
    else:
        partitioning = {
            "job_artifact_name": f"ddd-internal-units-{run_id}",
            "job_artifact_sha256": partition_artifact_sha256.removeprefix("sha256:"),
            "status": "PREPARED",
            "strategy": job.get("strategy"),
            "contract_output_geojson": policy.get("output_geojson"),
            "resolved_output_geojson": job.get("output_geojson"),
            "partition_unit_field": policy.get("partition_unit_field"),
        }

    evidence = {
        "schema": "ddd.catalog-evidence/1.0",
        "kind": "generation_preflight",
        "territory_id": territory_id,
        "territory_name": row.get("name") or territory_id,
        "edition": str(edition),
        "run_id": run_id,
        "source_commit": _git_head(root),
        "artifact_name": f"ddd-state-{run_id}-M03U",
        "artifact_sha256": m03u_artifact_sha256.removeprefix("sha256:"),
        "decision": "READY_FOR_FIRST_GENERATION",
        "stage": "M03U",
        "source": {
            "artifact_name": prep["artifact_name"],
            "artifact_sha256": str(prep["artifact_sha256"]).removeprefix("sha256:"),
            "package_sha256": str(prep["package_sha256"]).removeprefix("sha256:"),
        },
        "implementation": _pre_m04_implementation_binding(root),
        "adjacency": {
            "predicate": m02.get("predicate"),
            "working_crs": m02.get("working_crs"),
            "min_shared_border_m": m02.get("min_shared_border_m"),
            "max_precision_overlap_area_m2": m02.get("max_precision_overlap_area_m2"),
            "buffer_m": m02.get("buffer_m"),
            "simplify_m": m02.get("simplify_m"),
            "topology_bridges": _bridge_signature(m02.get("topology_bridges") or []),
        },
        "graph": {
            "artifact_name": f"ddd-state-{run_id}-M03",
            "artifact_sha256": m03_artifact_sha256.removeprefix("sha256:"),
            "module_version": report.get("version"),
            "nodes": report.get("nodes"),
            "edges": report.get("edges"),
            "population": report.get("total_pop"),
            "isolated": report.get("isolated"),
            "global_components": (report.get("global_component_audit") or {}).get("components"),
            "province_disconnected": (report.get("province_component_audit") or {}).get("disconnected"),
            "municipality_disconnected": (report.get("municipality_component_audit") or {}).get("disconnected"),
        },
        "partitioning": partitioning,
        "contract_binding": _contract_generation_binding(contract),
    }

    gate = generation_enablement(
        root_dir=root,
        contract_path=contract_path,
        territory_id=territory_id,
        certified_product_ready=False,
        first_generation_evidence=evidence,
        preparation_evidence=prep,
        require_source=True,
    )
    if not gate.get("allowed"):
        raise ValueError(gate.get("reason") or "CAP_PRE_M04_EVIDENCE")
    evidence["effective_gate"] = gate
    return evidence


def register_evidence_path(
    *, root_dir: Path, territory_id: str, edition: str, evidence_path: str
) -> None:
    catalog = root_dir / CATALOG
    lines = catalog.read_text(encoding="utf-8").splitlines()
    start, end = _catalog_state_bounds(lines, territory_id, str(edition))
    state_indent = _catalog_state_indent(lines, start, end)
    evidence_start = next(
        (i for i in range(start, end) if lines[i].startswith(state_indent + "evidence:")),
        None,
    )
    if evidence_start is None:
        lines.insert(end, f"{state_indent}evidence:")
        evidence_start = end
        end += 1
    child = state_indent + "  "
    e_end = evidence_start + 1
    while e_end < end and (lines[e_end].startswith(child) or not lines[e_end].strip()):
        e_end += 1
    _replace_key(lines, evidence_start + 1, e_end, child, "generation_preflight", evidence_path)
    catalog.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root-dir", type=Path, default=Path("."))
    ap.add_argument("--territory-id", required=True)
    ap.add_argument("--edition", required=True)
    ap.add_argument("--run-id", type=int, required=True)
    ap.add_argument("--contract-path", required=True)
    ap.add_argument("--m03-state-dir", type=Path, required=True)
    ap.add_argument("--partition-job", type=Path, required=True)
    ap.add_argument("--m03-artifact-sha256", required=True)
    ap.add_argument("--m03u-artifact-sha256", required=True)
    ap.add_argument("--partition-artifact-sha256", required=True)
    ap.add_argument("--output", type=Path)
    ap.add_argument("--persist", action="store_true")
    args = ap.parse_args()

    root = args.root_dir.resolve()
    evidence = build_evidence(
        root_dir=root,
        territory_id=args.territory_id,
        edition=args.edition,
        run_id=args.run_id,
        contract_path=args.contract_path,
        m03_state_dir=args.m03_state_dir,
        partition_job=args.partition_job,
        m03_artifact_sha256=args.m03_artifact_sha256,
        m03u_artifact_sha256=args.m03u_artifact_sha256,
        partition_artifact_sha256=args.partition_artifact_sha256,
    )
    out = args.output or (
        root
        / "territorios"
        / args.territory_id
        / "evidencia"
        / "catalogo"
        / f"generation_preflight_{args.edition}.json"
    )
    if not out.is_absolute():
        out = root / out
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(evidence, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    if args.persist:
        rel = out.relative_to(root).as_posix()
        register_evidence_path(
            root_dir=root,
            territory_id=args.territory_id,
            edition=args.edition,
            evidence_path=rel,
        )
    print(json.dumps(evidence, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
