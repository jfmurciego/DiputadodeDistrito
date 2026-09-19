#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import shutil
from pathlib import Path

import yaml

from herramientas.seleccionar_paquete_fuentes import validate_prepared_package

CATALOG = Path("configuracion/catalogo_preparacion.yaml")
MASTER = Path("configuracion/catalogo_territorios_espana_2025.yaml")
GENERATION_WORKFLOW = Path(".github/workflows/produccion-distritos.yml")

REQUIRED_GENERATION_MODULES = (
    "modulo_01_preparar_base_territorial",
    "modulo_02_construir_adyacencias",
    "modulo_03_construir_grafo",
    "modulo_04_generar_semillas",
    "modulo_05_optimizar_distritos",
    "modulo_06_consolidar_distritos",
)


def _yaml(path: Path) -> dict:
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise ValueError(f"YAML inválido: {path}")
    return data


def contract_is_generation_complete(contract: Path) -> tuple[bool, list[str]]:
    data = _yaml(contract)
    reasons: list[str] = []
    meta = data.get("meta") or {}
    tc = data.get("territory_contract") or {}
    modules = data.get("modulos") or {}
    validation = data.get("validation") or {}

    for name in REQUIRED_GENERATION_MODULES:
        if not isinstance(modules.get(name), dict):
            reasons.append(f"falta {name}")

    k = tc.get("k_districts")
    expected = validation.get("expected_districts")
    try:
        k_int = int(k)
        expected_int = int(expected)
        if k_int <= 0 or expected_int <= 0 or k_int != expected_int:
            reasons.append(f"cardinalidad incoherente: k={k!r}, expected={expected!r}")
    except Exception:
        reasons.append("cardinalidad de distritos ausente o inválida")

    if not str(meta.get("territory_id") or "").strip():
        reasons.append("meta.territory_id ausente")
    if not str(meta.get("year") or "").strip():
        reasons.append("meta.year ausente")
    return not reasons, reasons


def _replace_key(lines: list[str], start: int, end: int, indent: str, key: str, value: str) -> None:
    prefix = indent + key + ":"
    for i in range(start, end):
        if lines[i].startswith(prefix):
            lines[i] = f"{prefix} {value}"
            return
    lines.insert(end, f"{prefix} {value}")


def _catalog_state_bounds(lines: list[str], territory_id: str, edition: str) -> tuple[int, int]:
    territory_marker = f"  - territory_id: {territory_id}"
    try:
        t0 = next(i for i, line in enumerate(lines) if line == territory_marker)
    except StopIteration as exc:
        raise ValueError(f"Territorio ausente del catálogo: {territory_id}") from exc
    t1 = next((i for i in range(t0 + 1, len(lines)) if lines[i].startswith("  - territory_id: ")), len(lines))
    edition_markers = {f"      '{edition}':", f'      "{edition}":', f"      {edition}:"}
    try:
        e0 = next(i for i in range(t0, t1) if lines[i] in edition_markers)
    except StopIteration as exc:
        raise ValueError(f"Edición {edition} ausente para {territory_id}") from exc
    e1 = t1
    for i in range(e0 + 1, t1):
        if re.match(r"^      ['\"]?\d{4}['\"]?:$", lines[i]):
            e1 = i
            break
    return e0 + 1, e1


def _set_catalog_state(
    path: Path,
    *,
    territory_id: str,
    edition: str,
    source_declaration: str,
    contract_complete: bool,
    run_id: int,
    artifact_name: str,
    artifact_sha256: str,
    package_sha256: str,
) -> None:
    lines = path.read_text(encoding="utf-8").splitlines()
    start, end = _catalog_state_bounds(lines, territory_id, edition)

    updates = {
        "preparation_status": "READY",
        "territorial_source_declaration": source_declaration,
        "territorial_sources_prepared": "true",
        "territorial_contract_complete": "true" if contract_complete else "false",
    }
    if contract_complete:
        updates["production_authorization"] = "AUTHORIZED"
        updates["territorial_certification"] = "NOT_CERTIFIED"

    for key, value in updates.items():
        start, end = _catalog_state_bounds(lines, territory_id, edition)
        _replace_key(lines, start, end, "        ", key, value)

    start, end = _catalog_state_bounds(lines, territory_id, edition)
    pe_start = next((i for i in range(start, end) if lines[i].startswith("        preparation_evidence:")), None)
    if pe_start is not None:
        pe_end = pe_start + 1
        while pe_end < end and (lines[pe_end].startswith("          ") or not lines[pe_end].strip()):
            pe_end += 1
        del lines[pe_start:pe_end]
        start, end = _catalog_state_bounds(lines, territory_id, edition)

    insert_at = next((i + 1 for i in range(start, end) if lines[i].startswith("        last_valid_checkpoint:")), end)
    evidence = [
        "        preparation_evidence:",
        f"          run_id: {run_id}",
        f"          artifact_name: {artifact_name}",
        f"          artifact_sha256: {artifact_sha256}",
        f"          package_sha256: {package_sha256}",
    ]
    lines[insert_at:insert_at] = evidence
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _promote_contract(path: Path) -> None:
    lines = path.read_text(encoding="utf-8").splitlines()
    try:
        m0 = lines.index("meta:") + 1
        m1 = next(i for i in range(m0, len(lines)) if lines[i] and not lines[i].startswith("  "))
    except Exception as exc:
        raise ValueError(f"Contrato sin bloque meta legible: {path}") from exc
    _replace_key(lines, m0, m1, "  ", "contract_level", "production_m01_m06")
    _replace_key(lines, m0, m1, "  ", "production_authorization", "AUTHORIZED")
    _replace_key(lines, m0, m1, "  ", "status", "generation_ready")

    tc0 = next((i for i, line in enumerate(lines) if line == "territory_contract:"), None)
    if tc0 is not None:
        tc1 = next((i for i in range(tc0 + 1, len(lines)) if lines[i] and not lines[i].startswith("  ")), len(lines))
        for key in ("promotion_status", "status"):
            for i in range(tc0 + 1, tc1):
                if lines[i].startswith(f"  {key}:"):
                    lines[i] = f"  {key}: generation_ready"
                    break
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _promote_master(path: Path, territory_id: str, contract_complete: bool) -> None:
    if not contract_complete:
        return
    lines = path.read_text(encoding="utf-8").splitlines()
    target = next((i for i, line in enumerate(lines) if f"territory_id: {territory_id}," in line), None)
    if target is None:
        raise ValueError(f"{territory_id}: ausente del catálogo territorial maestro")
    line = lines[target]
    line = re.sub(r"status: [^,}]+", "status: generation_ready", line)
    line = re.sub(r"contract_level: [^,}]+", "contract_level: production_m01_m06", line)
    if "production_authorization:" in line:
        line = re.sub(r"production_authorization: [^,}]+", "production_authorization: AUTHORIZED", line)
    else:
        line = line[:-1] + ", production_authorization: AUTHORIZED}"
    lines[target] = line
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _generation_names(catalog: Path) -> list[str]:
    data = _yaml(catalog)
    out: list[str] = []
    for row in data.get("territories") or []:
        for state in (row.get("editions") or {}).values():
            if (
                state.get("territory_declared")
                and state.get("territorial_sources_prepared")
                and state.get("territorial_contract_complete")
                and state.get("production_authorization") == "AUTHORIZED"
            ):
                out.append(str(row["name"]))
                break
    return out


def _rewrite_generation_options(path: Path, names: list[str]) -> None:
    if not names:
        raise ValueError("La lista de territorios generables no puede quedar vacía")
    lines = path.read_text(encoding="utf-8").splitlines()
    territory_idx = next(i for i, line in enumerate(lines) if line == "      territory_id:")
    options_idx = next(i for i in range(territory_idx, len(lines)) if lines[i] == "        options:")
    end = options_idx + 1
    while end < len(lines) and lines[end].startswith("          - "):
        end += 1
    lines[options_idx + 1:end] = [f"          - {name}" for name in names]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def promote(
    *,
    root_dir: Path,
    territory_id: str,
    edition: str,
    package: Path,
    source_declaration: Path,
    run_id: int,
    artifact_name: str,
    artifact_sha256: str,
) -> dict:
    root = root_dir.resolve()
    catalog = root / CATALOG
    master = root / MASTER
    generation_workflow = root / GENERATION_WORKFLOW

    catalog_data = _yaml(catalog)
    row = next((r for r in catalog_data.get("territories") or [] if r.get("territory_id") == territory_id), None)
    if row is None:
        raise ValueError(f"Territorio no registrado: {territory_id}")
    state = (row.get("editions") or {}).get(str(edition))
    if not isinstance(state, dict):
        raise ValueError(f"Edición no registrada: {territory_id}/{edition}")

    valid, reasons = validate_prepared_package(package, territory_id=territory_id, edition=edition)
    if not valid:
        raise ValueError("Paquete territorial no promovible: " + "; ".join(reasons))
    manifest = json.loads((package / "manifest.json").read_text(encoding="utf-8"))
    package_sha256 = str(manifest.get("sha256") or "")
    if not package_sha256:
        raise ValueError("Paquete territorial sin SHA-256 interno")

    contract_raw = state.get("contract_path")
    contract = root / str(contract_raw or "")
    if not contract.is_file():
        raise ValueError(f"Contrato territorial inexistente: {contract_raw}")
    contract_complete, contract_reasons = contract_is_generation_complete(contract)

    src_raw = state.get("territorial_source_declaration")
    if src_raw:
        durable_declaration = root / str(src_raw)
    else:
        durable_declaration = root / "territorios" / territory_id / "config" / "fuentes_oficiales.yaml"
    durable_declaration.parent.mkdir(parents=True, exist_ok=True)
    if source_declaration.resolve() != durable_declaration.resolve():
        shutil.copy2(source_declaration, durable_declaration)
    source_rel = durable_declaration.relative_to(root).as_posix()

    if contract_complete:
        _promote_contract(contract)
    _promote_master(master, territory_id, contract_complete)
    _set_catalog_state(
        catalog,
        territory_id=territory_id,
        edition=str(edition),
        source_declaration=source_rel,
        contract_complete=contract_complete,
        run_id=run_id,
        artifact_name=artifact_name,
        artifact_sha256=artifact_sha256.removeprefix("sha256:"),
        package_sha256=package_sha256,
    )
    _rewrite_generation_options(generation_workflow, _generation_names(catalog))

    return {
        "territory_id": territory_id,
        "edition": str(edition),
        "territorial_sources_prepared": True,
        "contract_complete": contract_complete,
        "generation_enabled": contract_complete,
        "contract_reasons": contract_reasons,
        "source_declaration": source_rel,
        "run_id": run_id,
        "artifact_name": artifact_name,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root-dir", type=Path, default=Path("."))
    ap.add_argument("--territory-id", required=True)
    ap.add_argument("--edition", required=True)
    ap.add_argument("--package", required=True, type=Path)
    ap.add_argument("--source-declaration", required=True, type=Path)
    ap.add_argument("--run-id", required=True, type=int)
    ap.add_argument("--artifact-name", required=True)
    ap.add_argument("--artifact-sha256", required=True)
    args = ap.parse_args()
    result = promote(
        root_dir=args.root_dir,
        territory_id=args.territory_id,
        edition=args.edition,
        package=args.package,
        source_declaration=args.source_declaration,
        run_id=args.run_id,
        artifact_name=args.artifact_name,
        artifact_sha256=args.artifact_sha256,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
