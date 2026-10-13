#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Versión 1.0.0; orquestador diagnóstico serial Congreso; 2026-10-13.

Alcance: ejecuta/reanuda preflights provinciales M01-M04 y pruebas sintéticas
M05/M06 reutilizando preflight_caceres_n08.run; agrega informes 52/52.
Estado: candidato diagnóstico; nunca crea particiones reales ni autoriza generación.
Cambios: serialización, checkpoint por unidad, hashes de contrato/fuentes/grafo.
Motivo: habilitar campaña nacional reanudable sin duplicar el preflight provincial.
Origen: nuevo, sin predecesor.
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
from typing import Any, Mapping

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "territorios/congreso/contrato_congreso_2026.json"
SOURCES = ROOT / "territorios/congreso/fuentes/ine_2025_2025"
PRODUCT = ROOT / "docs/ESTUDIOS/N08_TOPOLOGIA_NACIONAL_20251012/producto"
PROVINCES = tuple(f"{code:02d}" for code in range(1, 53))
VERSION = "1.0.0"
SCHEMA = "ddd.congreso-preflight-campaign/1.0"
PREFLIGHT_TOOL = ROOT / "herramientas/preflight_caceres_n08.py"
# Pin the reviewed provincial runner: a behavior change requires deliberate
# review here rather than silently broadening what the campaign executes.
PREFLIGHT_TOOL_SHA256 = "d46715e27c5ef418c1a5f2de2ced2b2bf2a666b4ca9a0f5f518dfaf43f72f745"
CODE_DEPENDENCIES = (
    "modulos/01_preparar_base_territorial.py",
    "modulos/02_construir_adyacencias.py",
    "modulos/03_construir_grafo.py",
    "modulos/06_consolidar_distritos.py",
    "herramientas/preflight_topologico_nacional.py",
    "ddd_core/congreso_preflight_adapter.py",
    "ddd_core/m04_seed_engine.py",
    "ddd_core/m05_population_repair.py",
    "ddd_core/config.py",
)
M01_M03 = {"PASS"}
M04 = {"PASS_NECESSARY_ONLY", "BLOCKED"}
SYNTHETIC = {"SYNTHETIC_CONTRACT_PASS_ONLY"}


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _canonical(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":"), allow_nan=False).encode("utf-8")


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_bytes())
    if not isinstance(value, dict):
        raise ValueError("JSON_OBJECT_REQUIRED:" + str(path))
    return value


def _atomic_json(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2,
                       allow_nan=False) + "\n").encode("utf-8")
    temporary = path.with_name(path.name + ".tmp")
    with temporary.open("wb") as stream:
        stream.write(data)
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temporary, path)


def _root_context(*, root: Path = ROOT, contract_path: Path = CONTRACT,
                  source_dir: Path = SOURCES, product_dir: Path = PRODUCT,
                  runner_path: Path = PREFLIGHT_TOOL) -> dict[str, Any]:
    contract_bytes = contract_path.read_bytes()
    contract = json.loads(contract_bytes)
    if contract.get("accreditation", {}).get("generation_authorized") is not False:
        raise ValueError("GENERATION_AUTHORIZATION_MUST_REMAIN_FALSE")
    try:
        from ddd_core.congreso_contract import validate_congress_identity
        validate_congress_identity(contract)
    except (ImportError, TypeError, ValueError) as exc:
        raise ValueError("CONGRESS_CONTRACT_INVALID") from exc

    source_manifest_path = source_dir / "manifest.json"
    source_manifest_bytes = source_manifest_path.read_bytes()
    source_manifest = json.loads(source_manifest_bytes)
    if (source_manifest.get("edition") != 2025
            or source_manifest.get("generation_authorized") is not False):
        raise ValueError("INE_SOURCE_MANIFEST_INVALID")
    source_binding = {}
    for role in ("geometry", "population"):
        contract_source = contract.get("sources", {}).get(role, {})
        source = source_manifest.get("sources", {}).get(role, {})
        if (contract_source.get("edition") != 2025 or contract_source.get("year") != 2025
                or contract_source.get("sha256") != source.get("sha256")):
            raise ValueError("CONTRACT_SOURCE_BINDING:" + role)
        source_binding[role] = {"edition": 2025, "sha256": source["sha256"]}

    population_record = source_manifest.get("outputs", {}).get("poblacion_por_seccion_2025.csv", {})
    crosswalk_record = source_manifest.get("crosswalk", {})
    for relative, record in (("poblacion_por_seccion_2025.csv", population_record),
                             (crosswalk_record.get("path"), crosswalk_record)):
        expected = record.get("sha256")
        if not isinstance(relative, str) or not isinstance(expected, str):
            raise ValueError("INE_SOURCE_OUTPUT_RECORD_INVALID")
        path = (source_dir / relative).resolve(strict=True)
        if not path.is_relative_to(source_dir.resolve()) or _sha(path.read_bytes()) != expected:
            raise ValueError("INE_SOURCE_OUTPUT_HASH:" + relative)

    topology_path = product_dir / "manifest.json"
    topology_bytes = topology_path.read_bytes()
    topology = json.loads(topology_bytes)
    topology_identity = topology.get("identity_sha256")
    identity_body = dict(topology)
    identity_body.pop("identity_sha256", None)
    if topology_identity != _sha(_canonical(identity_body)):
        raise ValueError("TOPOLOGY_MANIFEST_IDENTITY")
    if topology.get("generation_authorized") is not False:
        raise ValueError("TOPOLOGY_GENERATION_AUTHORIZATION")
    evidence = topology.get("evidence", {})
    if (evidence.get("source_binding") != source_binding
            or evidence.get("source_manifest_sha256") != _sha(source_manifest_bytes)):
        raise ValueError("TOPOLOGY_SOURCE_BINDING")

    quotas = {row["code"]: row["k"] for row in contract["quotas_by_origin_unit"]}
    if len(quotas) != 52 or set(quotas) != set(PROVINCES) or sum(quotas.values()) != 407:
        raise ValueError("CONGRESS_QUOTA_COVERAGE")
    unit_hashes, units = {}, {}
    for code in PROVINCES:
        relative = f"unidades/{code}.json.gz"
        record = topology.get("artifacts", {}).get(relative)
        if not isinstance(record, Mapping):
            raise ValueError("TOPOLOGY_UNIT_UNPINNED:" + code)
        raw = (product_dir / relative).read_bytes()
        if _sha(raw) != record.get("sha256") or len(raw) != record.get("bytes"):
            raise ValueError("TOPOLOGY_UNIT_HASH:" + code)
        decoded = gzip.decompress(raw)
        unit = json.loads(decoded)
        if (_sha(decoded) != record.get("canonical_json_sha256")
                or decoded != _canonical(unit) + b"\n"):
            raise ValueError("TOPOLOGY_UNIT_CANONICAL:" + code)
        summary = unit.get("summary", {})
        if (summary.get("CPRO") != code or summary.get("generation_authorized") is not False
                or summary.get("k") != quotas.get(code)
                or summary.get("k") != max(1, (int(summary.get("population", -1)) + 60000) // 120000)):
            raise ValueError("TOPOLOGY_UNIT_IDENTITY_OR_POLICY:" + code)
        unit_hashes[code] = _sha(raw)
        units[code] = summary
    if (sum(int(unit["sections"]) for unit in units.values()) != 36554
            or sum(int(unit["population"]) for unit in units.values()) != 49128297):
        raise ValueError("NATIONAL_TOPOLOGY_COVERAGE")

    runner_hash = _sha(runner_path.read_bytes())
    if runner_hash != PREFLIGHT_TOOL_SHA256:
        raise ValueError("PROVINCIAL_PREFLIGHT_RUNNER_NOT_REVIEWED")
    try:
        base_sha = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()
    except (OSError, subprocess.CalledProcessError) as exc:
        raise ValueError("GIT_BASE_IDENTITY_UNAVAILABLE") from exc
    return {
        "base": base_sha,
        "contract": contract,
        "contract_sha256": _sha(contract_bytes),
        "source_manifest_sha256": _sha(source_manifest_bytes),
        "source_binding": source_binding,
        "topology_manifest_sha256": _sha(topology_bytes),
        "topology_manifest_identity_sha256": topology_identity,
        "topology_unit_sha256": unit_hashes,
        "units": units,
        "runner_sha256": runner_hash,
        "campaign_tool_sha256": _sha(Path(__file__).read_bytes()),
        "consumer_code_sha256": {
            relative: _sha((root / relative).read_bytes()) for relative in CODE_DEPENDENCIES
        },
        "generation_authorized": False,
    }


def validate_province_report(report: Mapping[str, Any], code: str,
                             context: Mapping[str, Any]) -> None:
    """Validate a report emitted by the pinned provincial diagnostic runner."""
    if not isinstance(report, Mapping) or code not in PROVINCES:
        raise ValueError("PROVINCE_REPORT_INVALID")
    unit = context["units"][code]
    if report.get("version") != "1.2.0" or report.get("province") != code:
        raise ValueError("PROVINCE_REPORT_IDENTITY:" + code)
    if report.get("base") != context["base"] or report.get("tool_sha256") != context["runner_sha256"]:
        raise ValueError("PROVINCE_REPORT_CODE_IDENTITY:" + code)
    if report.get("source_binding") != context["source_binding"]:
        raise ValueError("PROVINCE_REPORT_SOURCE_BINDING:" + code)
    if report.get("source_evidence", {}).get("source_manifest_sha256") != context["source_manifest_sha256"]:
        raise ValueError("PROVINCE_REPORT_SOURCE_MANIFEST:" + code)
    if report.get("topology_manifest_identity_sha256") != context["topology_manifest_identity_sha256"]:
        raise ValueError("PROVINCE_REPORT_TOPOLOGY_MANIFEST:" + code)
    if report.get("topology_unit_sha256") != context["topology_unit_sha256"][code]:
        raise ValueError("PROVINCE_REPORT_TOPOLOGY_UNIT:" + code)
    if report.get("source_evidence", {}).get("contract_sha256") != context["contract_sha256"]:
        raise ValueError("PROVINCE_REPORT_CONTRACT:" + code)
    inputs = report.get("inputs", {})
    for key, expected in (("sections", unit["sections"]), ("population", unit["population"]),
                          ("physical_edges", unit["edges"]), ("k_approved", unit["k"])):
        if inputs.get(key) != expected:
            raise ValueError("PROVINCE_REPORT_INPUT_MISMATCH:" + code + ":" + key)
    if (report.get("generation_authorized") is not False
            or report.get("real_partition_created") is not False
            or report.get("districts_generated") != 0
            or report.get("published") is not False):
        raise ValueError("PROVINCE_REPORT_PRODUCTION_GUARD:" + code)
    modules = report.get("modules", {})
    expected_states = {"M01": M01_M03, "M02": M01_M03, "M03": M01_M03,
                       "M04": M04, "M05": SYNTHETIC, "M06": SYNTHETIC}
    if set(modules) != set(expected_states):
        raise ValueError("PROVINCE_REPORT_MODULE_SET:" + code)
    for module, states in expected_states.items():
        if modules[module].get("status") not in states:
            raise ValueError("PROVINCE_REPORT_MODULE_STATUS:" + code + ":" + module)
    if report.get("preflight_status") not in {
        "PASS_TECHNICAL_PREFLIGHT_PRODUCTION_DISABLED",
        "BLOCKED_CONTRACT_OR_OWNER_DECISIONS",
    }:
        raise ValueError("PROVINCE_REPORT_CAMPAIGN_STATUS:" + code)


def _checkpoint_digest(payload: Mapping[str, Any]) -> str:
    body = dict(payload)
    body.pop("checkpoint_sha256", None)
    return _sha(_canonical(body))


def _save_checkpoint(path: Path, payload: dict[str, Any]) -> None:
    payload["checkpoint_sha256"] = _checkpoint_digest(payload)
    _atomic_json(path, payload)


def _load_checkpoint(path: Path, identity: Mapping[str, Any]) -> dict[str, Any]:
    checkpoint = _read_json(path)
    claimed = checkpoint.get("checkpoint_sha256")
    if claimed != _checkpoint_digest(checkpoint):
        raise ValueError("CAMPAIGN_CHECKPOINT_HASH")
    if checkpoint.get("schema") != SCHEMA or checkpoint.get("identity") != identity:
        raise ValueError("CAMPAIGN_CHECKPOINT_IDENTITY_CHANGED")
    if checkpoint.get("generation_authorized") is not False:
        raise ValueError("CAMPAIGN_CHECKPOINT_PRODUCTION_GUARD")
    if not isinstance(checkpoint.get("records"), dict):
        raise ValueError("CAMPAIGN_CHECKPOINT_RECORDS")
    return checkpoint


def run_campaign(parts_dir: Path, output: Path, *, product_dir: Path = PRODUCT,
                 resume: bool = False, retry_failed: bool = False) -> dict[str, Any]:
    """Run provincial diagnostic preflights serially and checkpoint each result.

    The pinned runner uses real M01-M03 inputs and M04 necessary checks, then
    only synthetic M05/M06 tests. It has no path that generates districts.
    """
    from herramientas.preflight_caceres_n08 import run as provincial_run

    context = _root_context(product_dir=product_dir)
    execute = provincial_run
    identity = {key: context[key] for key in (
        "base", "contract_sha256", "source_manifest_sha256", "source_binding",
        "topology_manifest_sha256", "topology_manifest_identity_sha256",
        "topology_unit_sha256", "runner_sha256", "campaign_tool_sha256",
        "consumer_code_sha256")}
    checkpoint_path = output / "CHECKPOINT.json"
    if resume:
        if not checkpoint_path.is_file():
            raise ValueError("CAMPAIGN_CHECKPOINT_MISSING")
        checkpoint = _load_checkpoint(checkpoint_path, identity)
    else:
        if checkpoint_path.exists():
            raise ValueError("CAMPAIGN_CHECKPOINT_EXISTS_USE_RESUME")
        checkpoint = {"schema": SCHEMA, "version": VERSION, "identity": identity,
                      "records": {}, "generation_authorized": False}

    records = checkpoint["records"]
    output.mkdir(parents=True, exist_ok=True)
    for code in PROVINCES:
        prior = records.get(code)
        if prior is not None and prior.get("status") not in {"PASS", "FAILED"}:
            raise ValueError("CAMPAIGN_CHECKPOINT_PROVINCE_STATUS:" + code)
        province_dir = output / code
        report_path, province_checkpoint_path = province_dir / "PREFLIGHT.json", province_dir / "CHECKPOINT.json"
        if prior and prior.get("status") == "PASS":
            if not report_path.is_file() or not province_checkpoint_path.is_file():
                raise ValueError("CHECKPOINTED_PROVINCE_EVIDENCE_MISSING:" + code)
            report_bytes, pc_bytes = report_path.read_bytes(), province_checkpoint_path.read_bytes()
            if (_sha(report_bytes) != prior.get("report_sha256")
                    or _sha(pc_bytes) != prior.get("province_checkpoint_sha256")):
                raise ValueError("CHECKPOINTED_PROVINCE_EVIDENCE_CHANGED:" + code)
            validate_province_report(json.loads(report_bytes), code, context)
            continue
        if prior and prior.get("status") == "FAILED" and not retry_failed:
            continue
        try:
            report = execute(parts_dir, province_dir, code, product_dir)
            validate_province_report(report, code, context)
            if not report_path.is_file() or not province_checkpoint_path.is_file():
                raise ValueError("PROVINCIAL_RUNNER_OUTPUT_MISSING:" + code)
            report_bytes, pc_bytes = report_path.read_bytes(), province_checkpoint_path.read_bytes()
            province_checkpoint = json.loads(pc_bytes)
            if (province_checkpoint.get("province") != code
                    or province_checkpoint.get("generation_authorized") is not False
                    or province_checkpoint.get("districts_generated") != 0
                    or province_checkpoint.get("preflight_sha256") != _sha(report_bytes)):
                raise ValueError("PROVINCIAL_CHECKPOINT_INVALID:" + code)
            records[code] = {"status": "PASS", "preflight_status": report["preflight_status"],
                             "report_sha256": _sha(report_bytes),
                             "province_checkpoint_sha256": _sha(pc_bytes)}
        except Exception as exc:
            records[code] = {"status": "FAILED", "error": type(exc).__name__ + ":" + str(exc)}
        checkpoint.update({"records": records, "updated_province": code,
                           "generation_authorized": False})
        checkpoint["coverage"] = {
            "passed": sum(row.get("status") == "PASS" for row in records.values()),
            "failed": sum(row.get("status") == "FAILED" for row in records.values()),
            "expected": len(PROVINCES),
        }
        _save_checkpoint(checkpoint_path, checkpoint)

    passed = sorted(code for code, row in records.items() if row.get("status") == "PASS")
    failed = sorted(code for code, row in records.items() if row.get("status") == "FAILED")
    missing = sorted(set(PROVINCES) - set(passed) - set(failed))
    result = {"schema": SCHEMA, "version": VERSION, "base": context["base"],
              "identity": identity, "coverage": {"passed": len(passed), "failed": len(failed),
                                                   "not_evaluated": len(missing), "expected": 52},
              "passed_cpro": passed, "failed_cpro": failed, "not_evaluated_cpro": missing,
              "status": "DIAGNOSTIC_COVERAGE_COMPLETE" if len(passed) == 52
                        else "PARTIAL_DIAGNOSTIC_COVERAGE",
              "generation_authorized": False, "real_partition_created": False,
              "districts_generated": 0, "published": False}
    _atomic_json(output / "CAMPAIGN_PREFLIGHT.json", result)
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--parts-dir", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--product-dir", type=Path, default=PRODUCT)
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--retry-failed", action="store_true",
                        help="explicitly rerun units recorded FAILED after an environmental change")
    args = parser.parse_args()
    result = run_campaign(args.parts_dir, args.output, product_dir=args.product_dir,
                          resume=args.resume, retry_failed=args.retry_failed)
    print(json.dumps({"status": result["status"], "coverage": result["coverage"],
                      "generation_authorized": result["generation_authorized"]}, sort_keys=True))


if __name__ == "__main__":
    main()
