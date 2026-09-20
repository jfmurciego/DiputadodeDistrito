#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import shutil
from pathlib import Path

import yaml

from herramientas.seleccionar_paquete_fuentes import validate_prepared_package
from ddd_core.territory_contract import validate_production_contract

CATALOG = Path("configuracion/catalogo_preparacion.yaml")
MASTER = Path("configuracion/catalogo_territorios_espana_2025.yaml")

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
    territory_re = re.compile(rf"^(?P<indent>\s*)-\s+territory_id:\s*{re.escape(territory_id)}\s*$")
    try:
        t0, match = next(
            (i, m) for i, line in enumerate(lines) if (m := territory_re.match(line))
        )
    except StopIteration as exc:
        raise ValueError(f"Territorio ausente del catálogo: {territory_id}") from exc

    territory_indent = match.group("indent")
    next_territory_re = re.compile(rf"^{re.escape(territory_indent)}-\s+territory_id:")
    t1 = next(
        (i for i in range(t0 + 1, len(lines)) if next_territory_re.match(lines[i])),
        len(lines),
    )

    edition_re = re.compile(rf"^(?P<indent>\s*)['\"]?{re.escape(str(edition))}['\"]?:\s*$")
    try:
        e0, edition_match = next(
            (i, m)
            for i in range(t0, t1)
            if (m := edition_re.match(lines[i])) and len(m.group("indent")) > len(territory_indent)
        )
    except StopIteration as exc:
        raise ValueError(f"Edición {edition} ausente para {territory_id}") from exc

    edition_indent = edition_match.group("indent")
    next_edition_re = re.compile(rf"^{re.escape(edition_indent)}['\"]?\d{{4}}['\"]?:\s*$")
    e1 = next(
        (i for i in range(e0 + 1, t1) if next_edition_re.match(lines[i])),
        t1,
    )
    return e0 + 1, e1


def _catalog_state_indent(lines: list[str], start: int, end: int) -> str:
    for line in lines[start:end]:
        if line.strip():
            return line[: len(line) - len(line.lstrip())]
    return "      "
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
        state_indent = _catalog_state_indent(lines, start, end)
        _replace_key(lines, start, end, state_indent, key, value)

    start, end = _catalog_state_bounds(lines, territory_id, edition)
    state_indent = _catalog_state_indent(lines, start, end)
    child_indent = state_indent + "  "
    pe_start = next((i for i in range(start, end) if lines[i].startswith(state_indent + "preparation_evidence:")), None)
    if pe_start is not None:
        pe_end = pe_start + 1
        while pe_end < end and (lines[pe_end].startswith(child_indent) or not lines[pe_end].strip()):
            pe_end += 1
        del lines[pe_start:pe_end]
        start, end = _catalog_state_bounds(lines, territory_id, edition)

    state_indent = _catalog_state_indent(lines, start, end)
    child_indent = state_indent + "  "
    insert_at = next((i + 1 for i in range(start, end) if lines[i].startswith(state_indent + "last_valid_checkpoint:")), end)
    evidence = [
        f"{state_indent}preparation_evidence:",
        f"{child_indent}run_id: {run_id}",
        f"{child_indent}artifact_name: {artifact_name}",
        f"{child_indent}artifact_sha256: {artifact_sha256}",
        f"{child_indent}package_sha256: {package_sha256}",
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
    for key, value in (
        ("contract_level", "production_m01_m06"),
        ("production_authorization", "AUTHORIZED"),
        ("status", "generation_ready"),
    ):
        m0 = lines.index("meta:") + 1
        m1 = next(i for i in range(m0, len(lines)) if lines[i] and not lines[i].startswith("  "))
        _replace_key(lines, m0, m1, "  ", key, value)

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

    catalog_data = _yaml(catalog)
    row = next((r for r in catalog_data.get("territories") or [] if r.get("territory_id") == territory_id), None)
    if row is None:
        raise ValueError(f"Territorio no registrado: {territory_id}")
    state = (row.get("editions") or {}).get(str(edition))
    if not isinstance(state, dict):
        raise ValueError(f"Edición no registrada: {territory_id}/{edition}")

    package_abs = package if package.is_absolute() else root / package
    source_declaration_abs = source_declaration if source_declaration.is_absolute() else root / source_declaration

    valid, reasons = validate_prepared_package(package_abs, territory_id=territory_id, edition=edition)
    if not valid:
        raise ValueError("Paquete territorial no promovible: " + "; ".join(reasons))
    manifest = json.loads((package_abs / "manifest.json").read_text(encoding="utf-8"))
    package_sha256 = str(manifest.get("sha256") or "")
    if not package_sha256:
        raise ValueError("Paquete territorial sin SHA-256 interno")

    contract_raw = state.get("contract_path")
    contract = root / str(contract_raw or "")
    if not contract.is_file():
        raise ValueError(f"Contrato territorial inexistente: {contract_raw}")
    structurally_complete, contract_reasons = contract_is_generation_complete(contract)

    src_raw = state.get("territorial_source_declaration")
    if src_raw:
        durable_declaration = root / str(src_raw)
    else:
        durable_declaration = root / "territorios" / territory_id / "config" / "fuentes_oficiales.yaml"
    durable_declaration.parent.mkdir(parents=True, exist_ok=True)
    if source_declaration_abs.resolve() != durable_declaration.resolve():
        shutil.copy2(source_declaration_abs, durable_declaration)
    source_rel = durable_declaration.relative_to(root).as_posix()

    # Registrar fuentes preparadas es independiente de autorizar generación.
    # La autorización sólo se conserva si la puerta contractual completa admite
    # el contrato ya promovido. Si la puerta lo rechaza, se revierte la promoción
    # y el territorio queda con datos preparados, pero fuera del selector.
    original_contract = contract.read_text(encoding="utf-8")
    original_master = master.read_text(encoding="utf-8")
    original_catalog = catalog.read_text(encoding="utf-8")

    generation_enabled = False
    admission_errors: list[str] = []
    if structurally_complete:
        _promote_contract(contract)
        _promote_master(master, territory_id, True)
        _set_catalog_state(
            catalog,
            territory_id=territory_id,
            edition=str(edition),
            source_declaration=source_rel,
            contract_complete=True,
            run_id=run_id,
            artifact_name=artifact_name,
            artifact_sha256=artifact_sha256.removeprefix("sha256:"),
            package_sha256=package_sha256,
        )
        report = validate_production_contract(contract, expected_territory=territory_id)
        generation_enabled = bool(report.get("status") == "ADMITTED" and report.get("production_authorized"))
        admission_errors = list(report.get("errors") or [])

    if not generation_enabled:
        contract.write_text(original_contract, encoding="utf-8")
        master.write_text(original_master, encoding="utf-8")
        catalog.write_text(original_catalog, encoding="utf-8")
        _set_catalog_state(
            catalog,
            territory_id=territory_id,
            edition=str(edition),
            source_declaration=source_rel,
            contract_complete=False,
            run_id=run_id,
            artifact_name=artifact_name,
            artifact_sha256=artifact_sha256.removeprefix("sha256:"),
            package_sha256=package_sha256,
        )


    return {
        "territory_id": territory_id,
        "edition": str(edition),
        "territorial_sources_prepared": True,
        "contract_complete": generation_enabled,
        "generation_enabled": generation_enabled,
        "contract_reasons": contract_reasons,
        "admission_errors": admission_errors,
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
