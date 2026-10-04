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
    _hard_partition_spec,
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
        population_year=meta.get("source_population_year", ""),
        section_year=meta.get("source_section_year", ""),
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
    preparation_evidence: dict | None = None,
) -> dict:
    root = root_dir.resolve()
    contract_file = root / contract_path
    contract = _yaml(contract_file)
    if (contract.get("meta") or {}).get("territory_id") != territory_id:
        raise ValueError("CONTRACT_IDENTITY_MISMATCH")

    row = lookup(territory_id, str(edition), root / CATALOG)
    prep = preparation_evidence or row.get("preparation_evidence") or {}
    for key in (
        "artifact_name",
        "artifact_sha256",
        "package_sha256",
        "compatibility_identity_sha256",
        "population_year",
        "section_year",
    ):
        if prep.get(key) in (None, ""):
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
        hard_partition = _hard_partition_spec(contract, root)
        if job.get("strategy") == "physical_components":
            if not hard_partition:
                raise ValueError("PARTITION_STRATEGY_MISMATCH: physical_components sin contrato físico")
            partitioning = {
                "job_artifact_name": f"ddd-internal-units-{run_id}",
                "job_artifact_sha256": partition_artifact_sha256.removeprefix("sha256:"),
                "status": "PREPARED",
                "strategy": "physical_components",
                "contract_output_geojson": m04.get("in_geojson"),
                "resolved_output_geojson": job.get("output_geojson"),
                "hard_partition_lookup": job.get("hard_partition_lookup"),
                "hard_partition_lookup_sha256": job.get("hard_partition_lookup_sha256"),
                "partition_field": job.get("partition_field"),
                "municipality_field": job.get("municipality_field"),
                "component_sections": job.get("component_sections"),
                "component_districts": job.get("component_districts"),
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
        "evaluation_status": "ENABLED",
        "stage": "M03U",
        "source": {
            "run_id": int(prep["run_id"]),
            "artifact_name": prep["artifact_name"],
            "artifact_sha256": str(prep["artifact_sha256"]).removeprefix("sha256:"),
            "package_sha256": str(prep["package_sha256"]).removeprefix("sha256:"),
            "compatibility_identity_sha256": str(prep["compatibility_identity_sha256"]),
            "territorial_identity_sha256": str(prep.get("territorial_identity_sha256") or ""),
            "population_year": int(prep["population_year"]),
            "section_year": int(prep["section_year"]),
        },
        "implementation": _pre_m04_implementation_binding(root, contract),
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



GENERATION_EVALUATION_STATUSES = {"ENABLED", "BLOCKED", "PENDING", "ERROR_TECHNICAL"}


def build_generation_evaluation(
    *,
    root_dir: Path,
    territory_id: str,
    edition: str,
    run_id: int,
    status: str,
    stage: str,
    reason: str,
    capability: str = "CAP_PRE_M04_EVIDENCE",
    preparation_evidence: dict | None = None,
) -> dict:
    """Materializa una evaluación no habilitante ligada a la fuente acreditada."""
    normalized = str(status or "").upper()
    if normalized not in GENERATION_EVALUATION_STATUSES - {"ENABLED"}:
        raise ValueError(f"GENERATION_EVALUATION_STATUS_INVALID: {status!r}")
    root = root_dir.resolve()
    row = lookup(territory_id, str(edition), root / CATALOG)
    prep = preparation_evidence or row.get("preparation_evidence") or {}
    for key in (
        "run_id",
        "artifact_name",
        "artifact_sha256",
        "package_sha256",
        "compatibility_identity_sha256",
        "population_year",
        "section_year",
    ):
        if prep.get(key) in (None, ""):
            raise ValueError(f"SOURCE_EVIDENCE_INCOMPLETE: {key}")
    return {
        "schema": "ddd.catalog-evidence/1.0",
        "kind": "generation_preflight",
        "territory_id": territory_id,
        "territory_name": row.get("name") or territory_id,
        "edition": str(edition),
        "run_id": int(run_id),
        "source_commit": _git_head(root),
        "decision": normalized,
        "evaluation_status": normalized,
        "stage": str(stage or "PRE_GENERATION"),
        "source": {
            "run_id": int(prep["run_id"]),
            "artifact_name": prep["artifact_name"],
            "artifact_sha256": str(prep["artifact_sha256"]).removeprefix("sha256:"),
            "package_sha256": str(prep["package_sha256"]).removeprefix("sha256:"),
            "compatibility_identity_sha256": str(prep["compatibility_identity_sha256"]),
            "territorial_identity_sha256": str(prep.get("territorial_identity_sha256") or ""),
            "population_year": int(prep["population_year"]),
            "section_year": int(prep["section_year"]),
        },
        "effective_gate": {
            "allowed": False,
            "status": normalized,
            "capability": str(capability or "CAP_PRE_M04_EVIDENCE"),
            "reason": str(reason or normalized),
        },
    }


def _assert_evaluation_source_matches_contract(
    *, contract: dict, evidence: dict
) -> None:
    state = contract.setdefault("generation_state", {})
    baseline = (contract.get("validation") or {}).get("source_baseline") or {}
    source = evidence.get("source") or {}
    if (
        state.get("source_prepared") is not True
        or str(state.get("package_sha256") or "") != str(source.get("package_sha256") or "")
        or str(state.get("compatibility_identity_sha256") or "") != str(source.get("compatibility_identity_sha256") or "")
        or str(baseline.get("package_sha256") or "") != str(source.get("package_sha256") or "")
        or str(baseline.get("compatibility_identity_sha256") or "") != str(source.get("compatibility_identity_sha256") or "")
        or int(baseline.get("population_year") or 0) != int(source.get("population_year") or 0)
        or int(baseline.get("section_year") or 0) != int(source.get("section_year") or 0)
    ):
        raise ValueError("GENERATION_EVALUATION_SOURCE_MISMATCH")


def _disable_contract_after_generation_evaluation(
    *, root_dir: Path, contract_path: str, evidence: dict
) -> None:
    path = root_dir / contract_path
    contract = _yaml(path)
    _assert_evaluation_source_matches_contract(contract=contract, evidence=evidence)
    contract.setdefault("meta", {})["status"] = "source_prepared_pending_pre_m04"
    contract.setdefault("territory_contract", {})["status"] = "source_prepared_pending_pre_m04"
    state = contract.setdefault("generation_state", {})
    state["generation_enabled"] = False
    for key in ("pre_m04_run_id", "pre_m04_source_commit", "pre_m04_artifact_sha256"):
        state.pop(key, None)
    path.write_text(
        yaml.safe_dump(contract, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )


def _set_master_generation_status(
    *, root_dir: Path, territory_id: str, status: str
) -> None:
    path = root_dir / "configuracion/catalogo_territorios_espana_2025.yaml"
    lines = path.read_text(encoding="utf-8").splitlines()
    target = next(
        (i for i, line in enumerate(lines) if f"territory_id: {territory_id}," in line),
        None,
    )
    if target is None:
        raise ValueError(f"{territory_id}: ausente del catálogo territorial maestro")
    import re
    line = lines[target]
    if "status:" in line:
        line = re.sub(r"status: [^,}]+", f"status: {status}", line)
    else:
        line = line[:-1] + f", status: {status}" + "}"
    lines[target] = line
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")

def _enable_contract_after_pre_m04(
    *, root_dir: Path, contract_path: str, evidence: dict
) -> None:
    path = root_dir / contract_path
    contract = _yaml(path)
    _assert_evaluation_source_matches_contract(contract=contract, evidence=evidence)
    state = contract.setdefault("generation_state", {})
    contract.setdefault("meta", {})["status"] = "generation_ready"
    contract.setdefault("territory_contract", {})["status"] = "generation_ready"
    state.update({
        "generation_enabled": True,
        "pre_m04_run_id": int(evidence["run_id"]),
        "pre_m04_source_commit": str(evidence["source_commit"]),
        "pre_m04_artifact_sha256": str(evidence["artifact_sha256"]),
    })
    path.write_text(
        yaml.safe_dump(contract, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )


def _enable_master_after_pre_m04(*, root_dir: Path, territory_id: str) -> None:
    _set_master_generation_status(
        root_dir=root_dir,
        territory_id=territory_id,
        status="generation_ready",
    )


def register_evidence_path(
    *, root_dir: Path, territory_id: str, edition: str, evidence_path: str,
    contract_path: str, evidence: dict
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
    else:
        inline = lines[evidence_start].strip()
        if inline in {"evidence: {}", "evidence: null", "evidence: ~"}:
            lines[evidence_start] = f"{state_indent}evidence:"
    child = state_indent + "  "
    e_end = evidence_start + 1
    while e_end < end and (lines[e_end].startswith(child) or not lines[e_end].strip()):
        e_end += 1
    _replace_key(lines, evidence_start + 1, e_end, child, "generation_preflight", evidence_path)
    start, end = _catalog_state_bounds(lines, territory_id, str(edition))
    state_indent = _catalog_state_indent(lines, start, end)
    evaluation_status = str(
        evidence.get("evaluation_status")
        or "ENABLED"
    ).upper()
    if evaluation_status not in GENERATION_EVALUATION_STATUSES:
        raise ValueError(f"GENERATION_EVALUATION_STATUS_INVALID: {evaluation_status!r}")

    master_path = root_dir / "configuracion/catalogo_territorios_espana_2025.yaml"
    if not master_path.is_file():
        raise ValueError("falta catálogo territorial maestro antes de registrar evaluación")
    master_lines = master_path.read_text(encoding="utf-8").splitlines()
    if not any(f"territory_id: {territory_id}," in line for line in master_lines):
        raise ValueError(f"{territory_id}: ausente del catálogo territorial maestro")

    if evaluation_status == "ENABLED":
        _replace_key(lines, start, end, state_indent, "generation_enabled", "true")
        _enable_contract_after_pre_m04(
            root_dir=root_dir,
            contract_path=contract_path,
            evidence=evidence,
        )
        _enable_master_after_pre_m04(root_dir=root_dir, territory_id=territory_id)
    else:
        _replace_key(lines, start, end, state_indent, "generation_enabled", "false")
        _disable_contract_after_generation_evaluation(
            root_dir=root_dir,
            contract_path=contract_path,
            evidence=evidence,
        )
        _set_master_generation_status(
            root_dir=root_dir,
            territory_id=territory_id,
            status="source_prepared_pending_pre_m04",
        )
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
    ap.add_argument("--preparation-evidence-json", type=Path)
    ap.add_argument("--output", type=Path)
    ap.add_argument("--persist", action="store_true")
    args = ap.parse_args()

    root = args.root_dir.resolve()
    preparation_evidence = (
        _json(args.preparation_evidence_json)
        if args.preparation_evidence_json is not None
        else None
    )
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
        preparation_evidence=preparation_evidence,
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
            contract_path=args.contract_path,
            evidence=evidence,
        )
    print(json.dumps(evidence, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
