#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

# Ejecución directa: `python herramientas/resolver_preparacion_legislatura.py`
# debe conservar acceso a los paquetes del repositorio (herramientas, ddd_core).
# Al ejecutar un fichero, Python pone herramientas/ en sys.path[0], no la raíz.
_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

import yaml

try:
    from herramientas.identidad_fuentes_legislatura import (
        digest,
        territorial_identity,
    )
    from herramientas.catalogo_territorios import normalize_territory_input
    from herramientas.adquirir_fuentes_oficiales import resolve_runtime_bindings
    from herramientas.resolver_fuentes_territorio import build_declaration
    from herramientas.resolver_adquisicion_electoral_especial import resolve as resolve_special_electoral_acquisition
except ModuleNotFoundError:  # ejecución directa: python herramientas/...
    from identidad_fuentes_legislatura import (
        digest,
        territorial_identity,
    )
    from catalogo_territorios import normalize_territory_input
    from adquirir_fuentes_oficiales import resolve_runtime_bindings
    from resolver_fuentes_territorio import build_declaration
    from resolver_adquisicion_electoral_especial import resolve as resolve_special_electoral_acquisition

MATRIX = Path("configuracion/preparacion_legislatura_vigente.yaml")
CATALOG = Path("configuracion/catalogo_preparacion.yaml")
REGISTRY = Path("configuracion/registro_electoral.yaml")
OFFICIAL_SOURCES = Path("fuentes/catalogo_oficial.yaml")
SHA256 = re.compile(r"^[0-9a-f]{64}$")
GIT_SHA = re.compile(r"^[0-9a-f]{40}$")


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


def _document(path: Path) -> dict:
    return _json(path) if path.suffix.lower() == ".json" else _yaml(path)


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _digest(value: object) -> str | None:
    text = str(value or "").removeprefix("sha256:").strip().lower()
    return text if SHA256.fullmatch(text) else None


def _catalog_state(root: Path, territory_id: str, edition: str) -> tuple[dict, dict]:
    data = _yaml(root / CATALOG)
    rows = [r for r in data.get("territories") or [] if r.get("territory_id") == territory_id]
    if len(rows) != 1:
        raise ValueError(f"Territorio ausente/duplicado en catálogo: {territory_id}")
    state = (rows[0].get("editions") or {}).get(str(edition))
    if not isinstance(state, dict):
        raise ValueError(f"Edición operativa ausente: {territory_id}/{edition}")
    return rows[0], state


def _temporal_evidence(root: Path, matrix: dict) -> dict:
    policy = matrix.get("population_section_policy") or {}
    rel = str(policy.get("availability_evidence") or "")
    if not rel:
        raise ValueError("TEMPORAL_EVIDENCE_MISSING: falta availability_evidence")
    path = root / rel
    if not path.is_file():
        raise ValueError(f"TEMPORAL_EVIDENCE_MISSING: no existe {rel}")
    data = _json(path)
    if data.get("schema") != "ddd.official-temporal-availability-evidence/1.0":
        raise ValueError("TEMPORAL_EVIDENCE_INVALID: schema no reconocido")
    provider = str(data.get("provider") or "").strip()
    checked_at = str(data.get("checked_at") or "").strip()
    if not provider or not checked_at:
        raise ValueError("TEMPORAL_EVIDENCE_INVALID: proveedor/fecha de consulta ausentes")
    checks = data.get("checks") or {}
    for kind in ("population_by_section", "census_sections"):
        row = checks.get(kind)
        if not isinstance(row, dict):
            raise ValueError(f"TEMPORAL_EVIDENCE_INVALID: falta {kind}")
        query = str(row.get("query") or "").strip()
        response = str(row.get("preserved_response") or "")
        declared = str(row.get("response_sha256") or "").lower()
        years = row.get("available_years")
        if not query or not response or not isinstance(years, list) or not years:
            raise ValueError(f"TEMPORAL_EVIDENCE_INVALID: {kind} incompleto")
        actual = _sha256_bytes(response.encode("utf-8"))
        if declared != actual:
            raise ValueError(
                f"TEMPORAL_EVIDENCE_DIGEST_MISMATCH: {kind} {declared} != {actual}"
            )
        normalized = sorted({int(x) for x in years})
        if int(row.get("latest_available_year")) != max(normalized):
            raise ValueError(f"TEMPORAL_EVIDENCE_INVALID: latest_available_year incoherente en {kind}")
        row["available_years"] = normalized
    return {
        "path": rel,
        "sha256": _sha256_bytes(path.read_bytes()),
        "provider": provider,
        "checked_at": checked_at,
        "checks": checks,
    }


def _years_from_declaration(declaration: dict, edition: str) -> tuple[int, int]:
    territory = declaration.get("territory") or {}
    legacy = territory.get("source_year")
    population = territory.get("population_year", legacy)
    section = territory.get("section_year", legacy)
    if population in (None, "") or section in (None, ""):
        raise ValueError(
            f"TERRITORIAL_TEMPORAL_IDENTITY_MISSING: {territory.get('id') or '?'}"
        )
    return int(population), int(section)


def _resolved_source_plan(
    root: Path,
    *,
    territory_id: str,
    edition: str,
    population_year: int,
    section_year: int,
    state: dict,
) -> dict:
    """Plan físico previo a adquisición: intención sin fingir bytes observados."""
    declaration_rel = str(
        state.get("territorial_source_declaration")
        or f"territorios/{territory_id}/config/fuentes_oficiales.yaml"
    )
    declaration = build_declaration(
        territory_id,
        int(edition),
        population_year=int(population_year),
        section_year=int(section_year),
        registry_path=root / "fuentes/territorios_espana.yaml",
        catalog_path=root / OFFICIAL_SOURCES,
    )
    catalog = _yaml(root / OFFICIAL_SOURCES)
    source_catalog = catalog.get("sources") or {}
    required = declaration.get("required_sources") or []
    bindings = declaration.get("source_bindings") or {}
    population_rules = declaration.get("population_validation") or {}
    runtime = resolve_runtime_bindings(
        root,
        declaration,
        territory_id=territory_id,
        edition=int(edition),
        population_year=int(population_year),
        section_year=int(section_year),
    )

    sources: dict[str, dict] = {}
    for source_id in required:
        source_id = str(source_id)
        source = source_catalog.get(source_id) or {}
        binding = bindings.get(source_id) or {}
        kind = str(source.get("kind") or "")
        role = "population" if kind == "static_csv" else "sectioning"
        effective_year = population_year if role == "population" else section_year
        entry = {
            "source_id": source_id,
            "role": role,
            "effective_year": int(effective_year),
            "adapter_kind": kind,
            "provider": source.get("provider"),
            "artifact": {
                "planned_path": str(binding.get("materialized_path") or ""),
                "planned_archive_member": str(
                    binding.get("archive_member")
                    or source.get("output_name")
                    or ""
                ),
            },
            "format": {
                "declared_type": source.get("format"),
                "declared_crs": source.get("crs"),
            },
        }
        if role == "population":
            entry["fields"] = {
                "section_id": str(population_rules.get("section_col") or "Secciones"),
                "population": str(population_rules.get("population_col") or "Total"),
                "year": str(population_rules.get("year_col") or "Periodo"),
                "sex": str(population_rules.get("sex_col") or "Sexo"),
                "age": str(population_rules.get("age_col") or "Edad"),
            }
            entry["filters"] = {
                "year_value": int(population_year),
                "sex_total_values": list(
                    population_rules.get("sex_total_values") or ["Total"]
                ),
                "age_total_values": list(
                    population_rules.get("age_total_values") or ["Todas las edades"]
                ),
            }
        else:
            entry["fields"] = {
                "section_id": str(source.get("section_id_field") or ""),
                "territorial_filter": str(source.get("territorial_filter_field") or ""),
            }
        sources[role] = entry

    return {
        "schema": "ddd.resolved-source-plan/1.0",
        "status": "RESOLVED",
        "territory": {
            "territory_id": territory_id,
            "project_edition": str(edition),
        },
        "temporal": {
            "population_year": int(population_year),
            "section_year": int(section_year),
        },
        "declaration": declaration_rel,
        "sources": sources,
        "runtime": runtime,
    }


def _territorial_candidate(
    root: Path,
    territory_id: str,
    edition: str,
    state: dict,
    population_year: int,
    section_year: int,
) -> dict:
    prep = state.get("preparation_evidence")
    declaration_rel = state.get("territorial_source_declaration")
    if not state.get("territorial_sources_prepared") or not isinstance(prep, dict) or not declaration_rel:
        return {"reusable": False, "reason": "TERRITORIAL_PACKAGE_MISSING"}
    declaration_path = root / str(declaration_rel)
    if not declaration_path.is_file():
        return {"reusable": False, "reason": "TERRITORIAL_DECLARATION_MISSING"}
    declaration = _yaml(declaration_path)
    territory = declaration.get("territory") or {}
    if str(territory.get("id") or "") != territory_id:
        return {"reusable": False, "reason": "TERRITORIAL_IDENTITY_MISMATCH"}
    run_id = prep.get("run_id")
    artifact_name = str(prep.get("artifact_name") or "")
    artifact_sha256 = _digest(prep.get("artifact_sha256"))
    package_sha256 = _digest(prep.get("package_sha256"))
    try:
        observed_population_year, observed_section_year = _years_from_declaration(declaration, edition)
    except ValueError:
        # Un receipt histórico puede acreditar años aunque su declaración predatara
        # la separación edition/population_year/section_year. Se preserva esa
        # evidencia explícita; si tampoco existe, el candidato queda bloqueado,
        # nunca se sustituye silenciosamente por la edición.
        prep_population = prep.get("population_year")
        prep_section = prep.get("section_year")
        if prep_population in (None, "") or prep_section in (None, ""):
            return {
                "reusable": False,
                "reason": "TERRITORIAL_TEMPORAL_IDENTITY_MISSING",
                "run_id": run_id,
                "artifact_name": artifact_name or None,
                "artifact_sha256": artifact_sha256,
                "package_sha256": package_sha256,
                "declaration": str(declaration_rel),
            }
        observed_population_year = int(prep_population)
        observed_section_year = int(prep_section)
    if not isinstance(run_id, int) or run_id <= 0:
        return {"reusable": False, "reason": "TERRITORIAL_RUN_INVALID"}
    if artifact_name != f"ddd-source-package-{territory_id}-{edition}-{run_id}":
        return {"reusable": False, "reason": "TERRITORIAL_ARTIFACT_IDENTITY_MISMATCH"}
    if not artifact_sha256 or not package_sha256:
        return {"reusable": False, "reason": "TERRITORIAL_DIGEST_MISSING"}
    compatibility_report_sha256 = _digest(prep.get("compatibility_report_sha256"))
    compatibility_identity_sha256 = _digest(prep.get("compatibility_identity_sha256"))
    compatibility_report_member = str(prep.get("compatibility_report_member") or "")
    if not compatibility_report_sha256 or not compatibility_identity_sha256 or not compatibility_report_member:
        return {
            "reusable": False,
            "reason": "TERRITORIAL_COMPATIBILITY_REPORT_MISSING",
            "run_id": run_id,
            "artifact_name": artifact_name,
            "artifact_sha256": artifact_sha256,
            "package_sha256": package_sha256,
            "population_year": observed_population_year,
            "section_year": observed_section_year,
            "declaration": str(declaration_rel),
            "receipt_path": str(prep.get("receipt_path") or "") or None,
            "source_commit": prep.get("source_commit"),
        }

    identity = territorial_identity(
        territory_id=territory_id,
        edition=edition,
        population_year=observed_population_year,
        section_year=observed_section_year,
        package_sha256=package_sha256,
        compatibility_identity_sha256=compatibility_identity_sha256,
    )
    receipt_rel = str(prep.get("receipt_path") or "")
    if receipt_rel:
        receipt_path = root / receipt_rel
        if not receipt_path.is_file():
            return {"reusable": False, "reason": "TERRITORIAL_RECEIPT_MISSING"}
        receipt = _json(receipt_path)
        if (
            receipt.get("schema") != "ddd.territorial-source-receipt/1.0"
            or receipt.get("kind") != "territorial_source"
            or str(receipt.get("territory_id") or "") != territory_id
            or str(receipt.get("edition") or "") != edition
            or int(receipt.get("run_id") or 0) != run_id
            or str(receipt.get("artifact_name") or "") != artifact_name
            or _digest(receipt.get("artifact_sha256")) != artifact_sha256
            or _digest(receipt.get("package_sha256")) != package_sha256
            or int(receipt.get("population_year") or 0) != observed_population_year
            or int(receipt.get("section_year") or 0) != observed_section_year
            or str(receipt.get("territorial_identity_sha256") or "") != identity["territorial_identity_sha256"]
            or _digest(receipt.get("compatibility_report_sha256")) != compatibility_report_sha256
            or _digest(receipt.get("compatibility_identity_sha256")) != compatibility_identity_sha256
            or str(receipt.get("compatibility_report_member") or "") != compatibility_report_member
        ):
            return {"reusable": False, "reason": "TERRITORIAL_RECEIPT_CONTRADICTORY"}

    durable_candidate = {
        "run_id": run_id,
        "artifact_name": artifact_name,
        "artifact_sha256": artifact_sha256,
        "package_sha256": package_sha256,
        "declaration": str(declaration_rel),
        "receipt_path": receipt_rel or None,
        "source_commit": prep.get("source_commit"),
        "compatibility_report_sha256": compatibility_report_sha256,
        "compatibility_identity_sha256": compatibility_identity_sha256,
        "compatibility_report_member": compatibility_report_member,
    }
    if observed_population_year != population_year:
        return {
            "reusable": False,
            "reason": "TERRITORIAL_POPULATION_YEAR_MISMATCH",
            "observed_population_year": observed_population_year,
            "observed_section_year": observed_section_year,
            **durable_candidate,
            **identity,
        }
    if observed_section_year != section_year:
        return {
            "reusable": False,
            "reason": "TERRITORIAL_SECTION_YEAR_MISMATCH",
            "observed_population_year": observed_population_year,
            "observed_section_year": observed_section_year,
            **durable_candidate,
            **identity,
        }
    source_commit = str(prep.get("source_commit") or "")
    if not receipt_rel or not GIT_SHA.fullmatch(source_commit):
        return {
            "reusable": False,
            "reason": "TERRITORIAL_PROVENANCE_MISSING",
            "observed_population_year": observed_population_year,
            "observed_section_year": observed_section_year,
            **identity,
        }
    return {
        "reusable": True,
        "reason": "TERRITORIAL_DURABLE_CANDIDATE",
        "run_id": run_id,
        "artifact_name": artifact_name,
        "artifact_sha256": artifact_sha256,
        "package_sha256": package_sha256,
        "population_year": observed_population_year,
        "section_year": observed_section_year,
        "declaration": str(declaration_rel),
        "receipt_path": receipt_rel or None,
        "source_commit": source_commit,
        "compatibility_report_sha256": compatibility_report_sha256,
        "compatibility_identity_sha256": compatibility_identity_sha256,
        "compatibility_report_member": compatibility_report_member,
        **identity,
    }


def _electoral_candidate(root: Path, territory_id: str, state: dict, election_id: str) -> dict:
    evidence = state.get("evidence") or {}
    rel = evidence.get("electoral_source") if isinstance(evidence, dict) else None
    if not state.get("electoral_source_prepared") or not rel:
        return {"reusable": False, "reason": "ELECTORAL_PACKAGE_MISSING"}
    path = root / str(rel)
    if not path.is_file():
        return {"reusable": False, "reason": "ELECTORAL_RECEIPT_MISSING"}
    data = _json(path)
    schema = data.get("schema")
    if str(data.get("territory_id") or "") != territory_id:
        return {"reusable": False, "reason": "ELECTORAL_IDENTITY_MISMATCH"}
    if str(data.get("election_id") or "") != election_id:
        return {"reusable": False, "reason": "ELECTORAL_ELECTION_MISMATCH"}

    if schema == "ddd.catalog-evidence/1.0":
        if data.get("kind") != "electoral_source":
            return {"reusable": False, "reason": "ELECTORAL_RECEIPT_KIND"}
        run_id = data.get("run_id")
        artifact_name = str(data.get("artifact_name") or "")
        artifact_sha256 = _digest(data.get("artifact_sha256"))
        source_commit = str(data.get("source_commit") or "")
        if not isinstance(run_id, int) or run_id <= 0:
            return {"reusable": False, "reason": "ELECTORAL_RUN_INVALID"}
        if artifact_name != f"ddd-electoral-package-{territory_id}-2025-{run_id}":
            return {"reusable": False, "reason": "ELECTORAL_ARTIFACT_IDENTITY_MISMATCH"}
        if not artifact_sha256:
            return {"reusable": False, "reason": "ELECTORAL_DIGEST_MISSING"}
        if not GIT_SHA.fullmatch(source_commit):
            return {"reusable": False, "reason": "ELECTORAL_PROVENANCE_MISSING"}

        provenance_reference = None
        provenance_election_date = ""
        declaration_rel = str(data.get("declaration") or "").strip()
        registry_rel = str(data.get("election_registry") or "").strip()
        contract_rel = str(data.get("election_contract") or "").strip()
        if declaration_rel:
            ref_path = root / declaration_rel
            if not ref_path.is_file():
                return {"reusable": False, "reason": "ELECTORAL_PROVENANCE_REFERENCE_MISSING"}
            ref = _document(ref_path)
            if str(ref.get("territory_id") or "") != territory_id or str(ref.get("election_id") or "") != election_id:
                return {"reusable": False, "reason": "ELECTORAL_PROVENANCE_MISMATCH"}
            provenance_reference = declaration_rel
            provenance_election_date = str(ref.get("election_date") or "")
        elif registry_rel:
            if registry_rel != REGISTRY.as_posix():
                return {"reusable": False, "reason": "ELECTORAL_PROVENANCE_MISMATCH"}
            registry = _yaml(root / REGISTRY)
            registered = (registry.get("territories") or {}).get(territory_id) or {}
            if str(registered.get("election_id") or "") != election_id:
                return {"reusable": False, "reason": "ELECTORAL_PROVENANCE_MISMATCH"}
            provenance_reference = registry_rel
            provenance_election_date = str(registered.get("election_date") or "")
        elif contract_rel:
            ref_path = root / contract_rel
            if not ref_path.is_file():
                return {"reusable": False, "reason": "ELECTORAL_PROVENANCE_REFERENCE_MISSING"}
            ref = _document(ref_path)
            if str(ref.get("territory_id") or "") != territory_id or str(ref.get("election_id") or "") != election_id:
                return {"reusable": False, "reason": "ELECTORAL_PROVENANCE_MISMATCH"}
            provenance_reference = contract_rel
            provenance_election_date = str(ref.get("election_date") or "")
        else:
            return {"reusable": False, "reason": "ELECTORAL_PROVENANCE_REFERENCE_MISSING"}

        return {
            "reusable": True,
            "reason": "ELECTORAL_DURABLE_CANDIDATE",
            "run_id": run_id,
            "artifact_name": artifact_name,
            "artifact_sha256": artifact_sha256,
            "source_commit": source_commit,
            "election_id": election_id,
            "election_date": str(data.get("election_date") or provenance_election_date),
            "receipt": str(rel),
            "provenance_reference": provenance_reference,
        }

    if schema == "ddd-election-source-provenance/1.0":
        source_digest = _digest(data.get("normalized_sha256")) or _digest(data.get("source_sha256"))
        if not source_digest or not data.get("publisher") or not data.get("source_url") or not data.get("retrieved_at"):
            return {"reusable": False, "reason": "ELECTORAL_LEGACY_PROVENANCE_INCOMPLETE"}
        return {
            "reusable": False,
            "legacy": True,
            "reason": "ELECTORAL_PACKAGE_IDENTITY_NOT_DURABLE",
            "artifact_sha256": source_digest,
            "receipt": str(rel),
        }
    return {"reusable": False, "reason": "ELECTORAL_RECEIPT_SCHEMA"}


def _electoral_plan(
    root: Path,
    territory_id: str,
    state: dict,
    row: dict,
) -> tuple[dict, str]:
    special = resolve_special_electoral_acquisition(
        root_dir=root,
        election_id=str(row["election_id"]),
        territory_id=territory_id,
        election_date=str(row["election_date"]),
    )
    if special is not None:
        candidate = _electoral_candidate(root, territory_id, state, str(row["election_id"]))
        if candidate.get("reusable"):
            return candidate, "REUSE"
        return {
            **candidate,
            "reason": "OFFICIAL_SPECIAL_ACQUISITION_AVAILABLE",
            "acquisition_kind": special["kind"],
            "provider": special["provider"],
            "source_status": special["source_status"],
        }, "ACQUIRE"

    electoral = row.get("electoral") or {}
    if electoral.get("action") == "BLOCKED_PROVISIONAL":
        return {"reusable": False, "reason": "PROVISIONAL_NOT_PRODUCTION_ELIGIBLE"}, "BLOCKED_PROVISIONAL"

    candidate = _electoral_candidate(root, territory_id, state, str(row["election_id"]))
    return candidate, "REUSE" if candidate.get("reusable") else "ACQUIRE"


def validate_matrix(root: Path) -> list[dict]:
    matrix = _yaml(root / MATRIX)
    registry = _yaml(root / REGISTRY)
    evidence = _temporal_evidence(root, matrix)
    rows = matrix.get("territories") or []
    registered = registry.get("territories") or {}
    if len(rows) != 19 or len(registered) != 19:
        raise ValueError(f"La matriz y el registro deben contener 19 territorios: {len(rows)}/{len(registered)}")
    ids = [str(r.get("territory_id") or "") for r in rows]
    if len(set(ids)) != 19 or set(ids) != set(registered):
        raise ValueError("La matriz no coincide exactamente con los 19 territorios del registro electoral")

    pop_available = set(evidence["checks"]["population_by_section"]["available_years"])
    section_available = set(evidence["checks"]["census_sections"]["available_years"])
    latest_pop = max(pop_available)
    latest_section = max(section_available)
    for row in rows:
        tid = row["territory_id"]
        reg = registered[tid]
        if row.get("election_id") != reg.get("election_id") or str(row.get("election_date")) != str(reg.get("election_date")):
            raise ValueError(f"{tid}: identidad electoral de matriz no coincide con registro")
        election_year = int(str(row["election_date"])[:4])
        terr = row.get("territorial") or {}
        pop_required = int(terr.get("population_required_year"))
        pop_selected = int(terr.get("population_selected_year"))
        section_required = int(terr.get("section_required_year"))
        section_selected = int(terr.get("section_selected_year"))
        if pop_required != election_year or section_required != election_year:
            raise ValueError(f"{tid}: población y seccionado requeridos deben referir al año electoral")
        if str(terr.get("temporal_evidence") or "") != evidence["path"]:
            raise ValueError(f"{tid}: evidencia temporal no coincide con la fuente durable común")

        if pop_required in pop_available:
            if pop_selected != pop_required or int(terr.get("population_lag_years", 0)) != 0:
                raise ValueError(f"{tid}: población oficial del año requerida existe y no admite sustitución")
        else:
            if pop_selected != latest_pop or int(terr.get("population_lag_years", 0)) != pop_required - latest_pop:
                raise ValueError(f"{tid}: sustitución poblacional no acredita la última edición oficial")
            if not str(terr.get("reason") or "").strip():
                raise ValueError(f"{tid}: sustitución poblacional sin razón explícita")

        if section_required in section_available:
            if section_selected != section_required or int(terr.get("section_lag_years", 0)) != 0:
                raise ValueError(f"{tid}: seccionado oficial del año requerido existe y no admite sustitución")
        else:
            if section_selected != latest_section or int(terr.get("section_lag_years", 0)) != section_required - latest_section:
                raise ValueError(f"{tid}: sustitución de seccionado no acredita la última edición oficial")

        if not str(terr.get("population_reference_date") or "") or not str(terr.get("section_reference_label") or ""):
            raise ValueError(f"{tid}: faltan fechas/etiquetas de referencia territorial")
    return rows


def resolve(root: Path, territory: str = "Todos") -> dict:
    root = root.resolve()
    matrix = _yaml(root / MATRIX)
    temporal = _temporal_evidence(root, matrix)
    rows = validate_matrix(root)
    edition = str(matrix.get("project_edition") or "2025")
    raw_territory = territory.strip()
    normalized_territory = raw_territory if raw_territory.casefold() in {"todos", "all"} else normalize_territory_input(raw_territory)
    wanted = normalized_territory.casefold()
    selected_rows = rows if wanted in {"todos", "all"} else [
        r for r in rows
        if wanted in {str(r["territory_id"]).casefold(), str(r["name"]).casefold()}
    ]
    if not selected_rows:
        raise ValueError(f"Territorio no encontrado: {territory}")

    plans = []
    for row in selected_rows:
        tid = row["territory_id"]
        _, state = _catalog_state(root, tid, edition)
        terr = row["territorial"]
        electoral = row["electoral"]
        population_year = int(terr["population_selected_year"])
        section_year = int(terr["section_selected_year"])
        t_candidate = _territorial_candidate(
            root,
            tid,
            edition,
            state,
            population_year,
            section_year,
        )
        if t_candidate.get("reusable"):
            t_action = (
                "REUSE_TEMPORAL_SUBSTITUTION"
                if int(terr["population_required_year"]) != population_year
                or int(terr["section_required_year"]) != section_year
                else "REUSE"
            )
        else:
            t_action = "ACQUIRE"

        e_candidate, e_action = _electoral_plan(root, tid, state, row)

        current_population_year = int(
            t_candidate.get("population_year", t_candidate.get("observed_population_year", terr["population_current_year"]))
        )
        current_section_year = int(
            t_candidate.get("section_year", t_candidate.get("observed_section_year", terr["section_current_year"]))
        )
        plans.append({
            "territory_id": tid,
            "name": row["name"],
            "election_id": row["election_id"],
            "election_date": str(row["election_date"]),
            "project_edition": edition,
            "population_year_required": int(terr["population_required_year"]),
            "population_year_current": current_population_year,
            "population_year_selected": population_year,
            "population_reference_date": str(terr["population_reference_date"]),
            "section_year_required": int(terr["section_required_year"]),
            "section_year_current": current_section_year,
            "section_year_selected": section_year,
            "section_reference_label": str(terr["section_reference_label"]),
            "population_temporal_lag_years": int(terr.get("population_lag_years", 0)),
            "section_temporal_lag_years": int(terr.get("section_lag_years", 0)),
            "temporal_reason": terr.get("reason"),
            "temporal_evidence": {
                "path": temporal["path"],
                "sha256": temporal["sha256"],
                "provider": temporal["provider"],
                "checked_at": temporal["checked_at"],
            },
            "territorial_action": t_action,
            "territorial_package_state": "READY_REUSABLE" if t_action.startswith("REUSE") else "ACQUIRE_REQUIRED",
            "territorial_reason": t_candidate.get("reason"),
            "territorial_candidate": t_candidate,
            "resolved_source_plan": _resolved_source_plan(
                root,
                territory_id=tid,
                edition=edition,
                population_year=population_year,
                section_year=section_year,
                state=state,
            ),
            "electoral_source": electoral.get("source"),
            "electoral_granularity": electoral.get("granularity"),
            "electoral_action": e_action,
            "electoral_package_state": (
                "BLOCKED_PROVISIONAL" if e_action == "BLOCKED_PROVISIONAL"
                else "READY_REUSABLE" if e_action == "REUSE"
                else "ACQUIRE_REQUIRED"
            ),
            "electoral_reason": e_candidate.get("reason"),
            "electoral_candidate": e_candidate,
            "definitive_gap": {
                k: v for k, v in electoral.items()
                if k.startswith("definitive_") or k.endswith("_candidate_votes")
            },
            "blocked": e_action.startswith("BLOCKED"),
            "block_reason": e_candidate.get("reason") if e_action.startswith("BLOCKED") else None,
        })
    return {
        "schema": "ddd-current-legislature-preparation-plan/1.1",
        "project_edition": edition,
        "as_of": matrix.get("as_of"),
        "temporal_evidence": {
            "path": temporal["path"],
            "sha256": temporal["sha256"],
            "provider": temporal["provider"],
            "checked_at": temporal["checked_at"],
        },
        "plans": plans,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root-dir", type=Path, default=Path("."))
    ap.add_argument("--territory", default="Todos")
    ap.add_argument("--output", type=Path)
    args = ap.parse_args()
    try:
        result = resolve(args.root_dir, args.territory)
    except Exception as exc:
        print(json.dumps({"ok": False, "error": f"{type(exc).__name__}: {exc}"}, ensure_ascii=False))
        return 2
    payload = json.dumps({"ok": True, **result}, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload, encoding="utf-8")
    else:
        print(payload, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
