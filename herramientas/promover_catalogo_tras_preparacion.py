#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
from pathlib import Path

import yaml

from herramientas.seleccionar_paquete_fuentes import validate_prepared_package
from herramientas.compatibilidad_poblacion_seccionado import REPORT_NAME, validate_compatibility_package
from herramientas.identidad_fuentes_legislatura import territorial_identity
from ddd_core.territory_contract import validate_production_contract
from herramientas.materializar_contrato_generacion import materialize as materialize_generation_contract

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
    receipt_path: str | None = None,
    territorial_identity_sha256: str | None = None,
    compatibility_report_sha256: str | None = None,
    compatibility_identity_sha256: str | None = None,
    compatibility_report_member: str | None = None,
    population_year: int | None = None,
    section_year: int | None = None,
    source_commit: str | None = None,
    contract_path: str | None = None,
) -> None:
    lines = path.read_text(encoding="utf-8").splitlines()
    start, end = _catalog_state_bounds(lines, territory_id, edition)

    updates = {
        "preparation_status": "READY",
        "territorial_source_declaration": source_declaration,
        "territorial_sources_prepared": "true",
        "territorial_contract_complete": "true" if contract_complete else "false",
        "generation_enabled": "false",
    }
    if contract_path:
        updates["contract_path"] = contract_path
    if contract_complete:
        updates["production_authorization"] = "AUTHORIZED"

    for key, value in updates.items():
        start, end = _catalog_state_bounds(lines, territory_id, edition)
        state_indent = _catalog_state_indent(lines, start, end)
        _replace_key(lines, start, end, state_indent, key, value)

    # Una fuente nueva invalida únicamente la habilitación/preflight activo.
    # El fichero histórico se conserva; sólo se retira su referencia efectiva.
    start, end = _catalog_state_bounds(lines, territory_id, edition)
    state_indent = _catalog_state_indent(lines, start, end)
    evidence_start = next(
        (i for i in range(start, end) if lines[i].startswith(state_indent + "evidence:")),
        None,
    )
    if evidence_start is not None:
        child_indent = state_indent + "  "
        evidence_end = evidence_start + 1
        while evidence_end < end and (
            lines[evidence_end].startswith(child_indent) or not lines[evidence_end].strip()
        ):
            evidence_end += 1
        lines[evidence_start + 1:evidence_end] = [
            line for line in lines[evidence_start + 1:evidence_end]
            if not line.startswith(child_indent + "generation_preflight:")
        ]

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
    checkpoint_start = next(
        (i for i in range(start, end) if lines[i].startswith(state_indent + "last_valid_checkpoint:")),
        None,
    )
    if checkpoint_start is None:
        insert_at = end
    else:
        insert_at = checkpoint_start + 1
        while insert_at < end and (
            lines[insert_at].startswith(child_indent) or not lines[insert_at].strip()
        ):
            insert_at += 1
    evidence = [
        f"{state_indent}preparation_evidence:",
        f"{child_indent}run_id: {run_id}",
        f"{child_indent}artifact_name: {artifact_name}",
        f"{child_indent}artifact_sha256: {artifact_sha256}",
        f"{child_indent}package_sha256: {package_sha256}",
    ]
    if receipt_path:
        evidence.append(f"{child_indent}receipt_path: {receipt_path}")
    if territorial_identity_sha256:
        evidence.append(f"{child_indent}territorial_identity_sha256: {territorial_identity_sha256}")
    if compatibility_report_sha256:
        evidence.append(f"{child_indent}compatibility_report_sha256: {compatibility_report_sha256}")
    if compatibility_identity_sha256:
        evidence.append(f"{child_indent}compatibility_identity_sha256: {compatibility_identity_sha256}")
    if compatibility_report_member:
        evidence.append(f"{child_indent}compatibility_report_member: {compatibility_report_member}")
    if population_year is not None:
        evidence.append(f"{child_indent}population_year: {int(population_year)}")
    if section_year is not None:
        evidence.append(f"{child_indent}section_year: {int(section_year)}")
    if source_commit:
        evidence.append(f"{child_indent}source_commit: {source_commit}")
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
        ("status", "source_prepared_pending_pre_m04"),
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
                    lines[i] = f"  {key}: source_prepared_pending_pre_m04"
                    break
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _capture_territorial_product_guard(root: Path, state: dict) -> dict | None:
    if not state.get("territorial_product_available"):
        return None
    evidence = state.get("evidence") or {}
    rel = str(evidence.get("territorial_product") or "")
    if not rel:
        raise ValueError("Producto territorial histórico marcado disponible sin receipt")
    path = root / rel
    if not path.is_file():
        raise ValueError(f"Receipt de producto territorial histórico inexistente: {rel}")
    return {
        "receipt_path": rel,
        "receipt_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "territorial_certification": state.get("territorial_certification"),
        "last_valid_checkpoint": json.loads(json.dumps(state.get("last_valid_checkpoint"))),
    }


def _assert_territorial_product_guard(
    root: Path,
    catalog_path: Path,
    *,
    territory_id: str,
    edition: str,
    guard: dict | None,
) -> None:
    if guard is None:
        return
    catalog = _yaml(catalog_path)
    row = next(r for r in catalog.get("territories") or [] if r.get("territory_id") == territory_id)
    state = (row.get("editions") or {}).get(str(edition)) or {}
    if not state.get("territorial_product_available"):
        raise ValueError("La promoción de fuente eliminó la disponibilidad del producto territorial histórico")
    rel = str((state.get("evidence") or {}).get("territorial_product") or "")
    if rel != guard["receipt_path"]:
        raise ValueError("La promoción de fuente cambió el receipt del producto territorial histórico")
    path = root / rel
    if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != guard["receipt_sha256"]:
        raise ValueError("La promoción de fuente alteró el producto territorial histórico")
    if state.get("territorial_certification") != guard["territorial_certification"]:
        raise ValueError("La promoción de fuente alteró la certificación territorial histórica")
    if state.get("last_valid_checkpoint") != guard["last_valid_checkpoint"]:
        raise ValueError("La promoción de fuente alteró el último checkpoint certificado histórico")


def _promote_master(path: Path, territory_id: str, contract_complete: bool) -> None:
    if not contract_complete:
        return
    lines = path.read_text(encoding="utf-8").splitlines()
    target = next((i for i, line in enumerate(lines) if f"territory_id: {territory_id}," in line), None)
    if target is None:
        raise ValueError(f"{territory_id}: ausente del catálogo territorial maestro")
    line = lines[target]
    line = re.sub(r"status: [^,}]+", "status: source_prepared_pending_pre_m04", line)
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
    source_commit: str | None = None,
) -> dict:
    root = root_dir.resolve()
    catalog = root / CATALOG

    catalog_data = _yaml(catalog)
    row = next((r for r in catalog_data.get("territories") or [] if r.get("territory_id") == territory_id), None)
    if row is None:
        raise ValueError(f"Territorio no registrado: {territory_id}")
    state = (row.get("editions") or {}).get(str(edition))
    if not isinstance(state, dict):
        raise ValueError(f"Edición no registrada: {territory_id}/{edition}")
    product_guard = _capture_territorial_product_guard(root, state)

    package_abs = package if package.is_absolute() else root / package
    source_declaration_abs = source_declaration if source_declaration.is_absolute() else root / source_declaration
    declaration_data = _yaml(source_declaration_abs)
    declaration_territory = declaration_data.get("territory") or {}
    legacy_year = declaration_territory.get("source_year")
    population_raw = declaration_territory.get("population_year", legacy_year)
    section_raw = declaration_territory.get("section_year", legacy_year)
    if population_raw in (None, "") or section_raw in (None, ""):
        raise ValueError("La declaración promovida debe fijar population_year y section_year explícitos")
    population_year = int(population_raw)
    section_year = int(section_raw)
    valid, reasons = validate_prepared_package(
        package_abs,
        territory_id=territory_id,
        edition=edition,
        population_year=population_year,
        section_year=section_year,
    )
    if not valid:
        raise ValueError("Paquete territorial no promovible: " + "; ".join(reasons))
    manifest = json.loads((package_abs / "manifest.json").read_text(encoding="utf-8"))
    package_sha256 = str(manifest.get("sha256") or "")
    if not package_sha256:
        raise ValueError("Paquete territorial sin SHA-256 interno")
    compatibility, compatibility_report_sha256, compatibility_reasons = validate_compatibility_package(
        package_abs,
        territory_id=territory_id,
        edition=str(edition),
        population_year=population_year,
        section_year=section_year,
        require_ready=True,
    )
    if compatibility_reasons:
        raise ValueError(
            "Paquete territorial bloqueado por compatibilidad población↔seccionado: "
            + "; ".join(compatibility_reasons)
        )
    compatibility_identity_sha256 = str(
        compatibility.get("compatibility_identity_sha256") or ""
    )

    identity = territorial_identity(
        territory_id=territory_id,
        edition=str(edition),
        population_year=population_year,
        section_year=section_year,
        package_sha256=package_sha256,
        compatibility_identity_sha256=compatibility_identity_sha256,
    )
    identity_sha = identity["territorial_identity_sha256"]
    version_root = (
        root
        / "territorios"
        / territory_id
        / "evidencia"
        / "fuentes_territoriales"
        / str(edition)
        / identity_sha
        / str(run_id)
    )
    version_root.mkdir(parents=True, exist_ok=True)
    versioned_declaration = version_root / "fuentes_oficiales.yaml"
    if not versioned_declaration.exists():
        shutil.copy2(source_declaration_abs, versioned_declaration)
    elif versioned_declaration.read_bytes() != source_declaration_abs.read_bytes():
        raise ValueError("Identidad territorial existente apunta a una declaración distinta")

    receipt_path = version_root / "receipt.json"
    receipt = {
        "schema": "ddd.territorial-source-receipt/1.0",
        "kind": "territorial_source",
        "territory_id": territory_id,
        "edition": str(edition),
        "population_year": population_year,
        "section_year": section_year,
        "run_id": int(run_id),
        "artifact_name": artifact_name,
        "artifact_sha256": artifact_sha256.removeprefix("sha256:"),
        "package_sha256": package_sha256,
        "source_commit": source_commit,
        "source_declaration": versioned_declaration.relative_to(root).as_posix(),
        "territorial_identity_sha256": identity_sha,
        "compatibility_report_member": REPORT_NAME,
        "compatibility_report_sha256": compatibility_report_sha256,
        "compatibility_identity_sha256": compatibility_identity_sha256,
    }
    rendered_receipt = json.dumps(receipt, ensure_ascii=False, indent=2) + "\n"
    if receipt_path.exists() and receipt_path.read_text(encoding="utf-8") != rendered_receipt:
        raise ValueError("Receipt territorial versionado ya existe con contenido contradictorio")
    receipt_path.write_text(rendered_receipt, encoding="utf-8")

    src_raw = state.get("territorial_source_declaration")
    durable_declaration = root / str(src_raw) if src_raw else root / "territorios" / territory_id / "config" / "fuentes_oficiales.yaml"
    durable_declaration.parent.mkdir(parents=True, exist_ok=True)
    if source_declaration_abs.resolve() != durable_declaration.resolve():
        shutil.copy2(source_declaration_abs, durable_declaration)
    source_rel = durable_declaration.relative_to(root).as_posix()
    receipt_rel = receipt_path.relative_to(root).as_posix()

    # Desde R046 la preparación territorial no deja un territorio a medias:
    # materializa automáticamente el contrato completo que consumirá 02 y lo
    # somete a la misma puerta estructural R036. No hay alta manual por región.
    materialized = materialize_generation_contract(
        root,
        territory_id,
        str(edition),
        package_abs,
        population_year=str(population_year),
        section_year=str(section_year),
    )
    contract_rel = str(materialized["contract_path"])
    contract = root / contract_rel
    report = validate_production_contract(contract, expected_territory=territory_id)
    if report.get("status") != "ADMITTED" or not report.get("production_authorized"):
        raise ValueError(
            "Contrato territorial auto-materializado no autorizado: "
            + "; ".join(report.get("errors") or [])
        )

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
        receipt_path=receipt_rel,
        territorial_identity_sha256=identity_sha,
        compatibility_report_sha256=compatibility_report_sha256,
        compatibility_identity_sha256=compatibility_identity_sha256,
        compatibility_report_member=REPORT_NAME,
        population_year=population_year,
        section_year=section_year,
        source_commit=source_commit,
        contract_path=contract_rel,
    )

    # La fuente queda preparada pero NO habilitada. El producto certificado previo
    # permanece disponible y sólo una evidencia pre-M04 ligada a esta identidad
    # podrá habilitar una nueva generación.
    _assert_territorial_product_guard(
        root,
        catalog,
        territory_id=territory_id,
        edition=str(edition),
        guard=product_guard,
    )
    effective_gate = {
        "allowed": False,
        "capability": "CAP_PRE_M04_EVIDENCE",
        "reason": "CAP_PRE_M04_EVIDENCE: fuente preparada pendiente de acreditación vinculada",
    }

    return {
        "territory_id": territory_id,
        "edition": str(edition),
        "territorial_sources_prepared": True,
        "contract_complete": True,
        "generation_enabled": bool(effective_gate.get("allowed")),
        "generation_gate": effective_gate,
        "contract_reasons": [],
        "admission_errors": [],
        "source_declaration": source_rel,
        "contract_path": contract_rel,
        "generation_contract": materialized,
        "run_id": run_id,
        "artifact_name": artifact_name,
        "artifact_sha256": artifact_sha256.removeprefix("sha256:"),
        "package_sha256": package_sha256,
        "population_year": population_year,
        "section_year": section_year,
        "territorial_identity_sha256": identity_sha,
        "compatibility_report_member": REPORT_NAME,
        "compatibility_report_sha256": compatibility_report_sha256,
        "compatibility_identity_sha256": compatibility_identity_sha256,
        "source_receipt": receipt_rel,
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
    ap.add_argument("--source-commit")
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
        source_commit=args.source_commit,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
