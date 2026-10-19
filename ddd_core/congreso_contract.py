"""VERSIÓN: 1.2.1; NOMBRE: guardas de admisión del contrato Congreso.
FECHA: 2026-10-19; ALCANCE: validación contractual fail-closed, sin ejecutar M01–M08.
ESTADO: candidato local; CAMBIOS: rechazar generation_authorized distinto de false.
MOTIVO: mantener coherentes admisión nacional y autorización productiva.
ANTERIOR: legacy/n08_nac_20261019/congreso_contract_v1.2.0.py.
ORIGEN HISTÓRICO: legacy/n06_contrato_20261012/congreso_contract_v1.0.0.py.
"""
from __future__ import annotations

import re
from decimal import Decimal
from typing import Any, Mapping

VERSION = "1.2.1"
CONGRESS_CODES = tuple(f"{number:02d}" for number in range(1, 53))
PROVINCE_CODES = CONGRESS_CODES[:50]
AUTONOMOUS_CITY_CODES = CONGRESS_CODES[50:]
FORBIDDEN_AUTONOMOUS_FIELDS = frozenset({
    "autonomous_territories", "territorial_units", "autonomous_territory_ids",
    "autonomous_community_codes", "regional_k", "autonomous_k",
    "autonomous_parliament_k", "parliamentary_k", "territorial_quotas",
})
FORBIDDEN_KEY_FRAGMENTS = ("autonomous", "regional", "territorialunit", "parliament", "parlament", "autonomouscommunity")
ALLOWED_ORCHESTRATORS = frozenset({"congress_contract_validator"})
ALLOWED_CONTRACT_FIELDS = frozenset({
    "metadata", "schema", "execution_identity", "territory_id", "scope",
    "metadata_scope", "orchestrator", "circumscription_codes", "circumscriptions",
    "minimum_unit", "sources", "population_reference", "barriers", "decisions",
    "k_decision", "quotas_by_circumscription", "k_alternatives", "accreditation",
    "reproducibility", "institutional_decision", "circumscription_accreditation",
})
AUTONOMOUS_TERRITORY_IDS = frozenset(
    {
        "andalucia", "aragon", "principado_de_asturias", "illes_balears",
        "canarias", "cantabria", "castilla_y_leon", "castilla_la_mancha",
        "cataluna", "comunidad_valenciana", "extremadura", "galicia",
        "comunidad_de_madrid", "region_de_murcia", "comunidad_foral_de_navarra",
        "pais_vasco", "la_rioja", "ceuta", "melilla",
    }
)

_CLOSED_OBJECT_KEYS = {
    ("metadata",): {"version", "name", "date", "scope", "status", "changes", "reason", "origin"},
    ("circumscriptions",): {"code", "class"},
    ("circumscriptions", "*"): {"code", "class"},
    ("minimum_unit",): {"status", "value", "candidate"},
    ("sources",): {"geometry", "population"},
    ("sources", "geometry"): {"accreditation", "edition", "year", "sha256", "authority", "acquisition_record", "uri", "title", "unit", "coverage", "licence", "notes", "territory_id"},
    ("sources", "population"): {"accreditation", "edition", "year", "sha256", "authority", "acquisition_record", "uri", "title", "unit", "coverage", "licence", "notes", "territory_id"},
    ("population_reference",): {"status", "edition", "year", "alignment_rule", "value"},
    ("barriers",): {"province_circumscription", "ceuta_melilla_separate", "cross_circumscription_edges", "basis"},
    ("decisions",): {"minimum_unit", "population_reference", "contiguity", "population_limits", "municipal_indivisibility", "islands", "enclaves", "physical_discontinuities"},
    ("decisions", "*"): {"status", "value", "evidence", "decision_id", "note"},
    ("decisions", "population_limits", "value"): {
        "population_floor_ratio", "population_cap_ratio", "target_tolerance_ratio",
    },
    ("k_decision",): {"status", "total", "source_scope", "source_territory_id", "decision_id", "quota_method"},
    ("quotas_by_circumscription",): {"code", "k"},
    ("quotas_by_circumscription", "*"): {"code", "k"},
    ("k_alternatives",): {"legal_reference", "constitutional_range", "project_precedent", "analytical_scenarios_not_decisions"},
    ("k_alternatives", "legal_reference"): {"total_seats", "meaning", "not_selected"},
    ("k_alternatives", "project_precedent"): {"observed_historical_map_district_count", "discrepancy_392_391", "accredited"},
    ("k_alternatives", "analytical_scenarios_not_decisions"): {"k", "label"},
    ("k_alternatives", "analytical_scenarios_not_decisions", "*"): {"k", "label"},
    ("accreditation",): {"circumscription_accreditation", "generation_authorized"},
    ("reproducibility",): {"required", "inputs_sha256_required", "manifest_required", "fixed_environment_required", "synthetic_pilot_only"},
    ("institutional_decision",): {"status", "decision_id", "decided_at", "authority", "note"},
}


def _validate_closed_objects(value: Any, path: tuple[str, ...] = ()) -> list[str]:
    errors: list[str] = []
    if isinstance(value, Mapping):
        allowed = _CLOSED_OBJECT_KEYS.get(path)
        if allowed is None and path and path[-1] == "*":
            allowed = _CLOSED_OBJECT_KEYS.get(path[:-1] + ("*",))
        if allowed is None and path:
            allowed = _CLOSED_OBJECT_KEYS.get(path[:-1] + ("*",))
        if allowed is not None:
            extra = set(value) - allowed
            if extra:
                errors.append("NESTED_FIELDS_UNKNOWN:" + ".".join(path) + ":" + ",".join(sorted(map(str, extra))))
        elif path:
            errors.append("NESTED_OBJECT_LOCATION_UNKNOWN:" + ".".join(path))
        for key, child in value.items():
            next_path = path + (str(key),)
            errors.extend(_validate_closed_objects(child, next_path))
    elif isinstance(value, (list, tuple)):
        item_path = path + ("*",)
        for child in value:
            errors.extend(_validate_closed_objects(child, item_path))
    return errors


def _normalize_origin_units(payload: Mapping[str, Any]) -> dict[str, Any]:
    """Compatible 0.2 origin names; reject conflicting dual representations."""
    result = dict(payload)
    aliases = {"origin_units": "circumscriptions", "origin_unit_codes": "circumscription_codes",
               "quotas_by_origin_unit": "quotas_by_circumscription"}
    for canonical, legacy in aliases.items():
        if canonical in result:
            if result.get("schema") != "ddd.congress-contract/0.2":
                raise ValueError("ORIGIN_UNITS_REQUIRE_SCHEMA_0_2")
            value = result.pop(canonical)
            if legacy in result and result[legacy] != value:
                raise ValueError("ORIGIN_UNITS_ALIAS_CONFLICT:" + canonical)
            result[legacy] = value
    return result



# Immutable approved values under N08-OWNER-20261013-7RULES.
# A future policy requires a new, explicit decision and validator version.
N06_K_DECISION_ID = "N06-OWNER-20261012-K"
N06_K_TOTAL = 407
N06_K_QUOTA_METHOD = "max(1,(P_i+60000)//120000); nearest_half_up_independent; reference_2025"
N06_K_QUOTAS = dict(zip(CONGRESS_CODES, (3, 3, 17, 6, 1, 6, 10, 50, 3, 3, 11, 5, 4, 6, 9, 2, 7, 8, 2, 6, 4, 2, 5, 4, 4, 3, 3, 59, 15, 13, 6, 3, 8, 1, 10, 8, 3, 9, 5, 1, 16, 1, 7, 1, 6, 23, 4, 10, 1, 8, 1, 1), strict=True))


def _approved_k_errors(payload: Mapping[str, Any]) -> list[str]:
    """Reject changes to N06 owner-approved K, quotas or decision provenance."""
    # Partial/legacy candidates do not assert the approved N06 decision.
    k_input = payload.get("k_decision")
    owner_input = payload.get("institutional_decision")
    # Structural admission remains possible for legacy candidates, but any
    # assertion of owner approval must match the fixed N06 decision.
    approved_status = "APPROVED_BY_OWNER"
    if not (
        isinstance(k_input, Mapping) and (
            k_input.get("decision_id") == N06_K_DECISION_ID
            or k_input.get("status") == approved_status
        )
        or isinstance(owner_input, Mapping) and (
            owner_input.get("decision_id") == N06_K_DECISION_ID
            or owner_input.get("status") == approved_status
        )
    ):
        return []
    errors: list[str] = []
    decision = payload.get("k_decision")
    expected = {
        "status": "APPROVED_BY_OWNER",
        "total": N06_K_TOTAL,
        "source_scope": "congreso",
        "decision_id": N06_K_DECISION_ID,
        "quota_method": N06_K_QUOTA_METHOD,
    }
    if not isinstance(decision, Mapping):
        errors.append("N06_K_DECISION_MISSING")
    else:
        for field, approved in expected.items():
            value = decision.get(field)
            if type(value) is not type(approved) or value != approved:
                errors.append("N06_DECISION_INVALID:N06_K_DECISION_NOT_APPROVED:" + field)
        if decision.get("source_territory_id") not in (None, "espana_congreso"):
            errors.append("N06_K_SOURCE_TERRITORY_INVALID")

    institutional = payload.get("institutional_decision")
    if (not isinstance(institutional, Mapping)
            or institutional.get("status") != "APPROVED_BY_OWNER"
            or institutional.get("decision_id") != N06_K_DECISION_ID
            or institutional.get("authority") != "propietario; instrucción expresa a Ejecutor, Work dirige"):
        errors.append("N06_K_INSTITUTIONAL_PROVENANCE_INVALID")

    rows = payload.get("quotas_by_circumscription")
    if not isinstance(rows, list) or len(rows) != len(CONGRESS_CODES):
        errors.append("N06_K_QUOTAS_INVALID")
    else:
        seen: dict[str, int] = {}
        for row in rows:
            if not isinstance(row, Mapping):
                errors.append("N06_K_QUOTAS_INVALID")
                break
            code, count = row.get("code"), row.get("k")
            if (not isinstance(code, str) or code not in N06_K_QUOTAS
                    or code in seen or type(count) is not int):
                errors.append("N06_K_QUOTAS_INVALID")
                break
            seen[code] = count
        if seen != N06_K_QUOTAS:
            errors.append("N06_QUOTAS_INVALID:N06_K_QUOTAS_NOT_APPROVED")
            if (isinstance(decision, Mapping) and type(decision.get("total")) is int
                    and all(type(value) is int for value in seen.values())
                    and sum(seen.values()) != decision["total"]):
                errors.append("CIRCUMSCRIPTION_QUOTAS_DO_NOT_SUM_TO_K")
    return errors


N08_OWNER_DECISION_ID = "N08-OWNER-20261013-7RULES"
N08_POLICY_VALUES = {
    "minimum_unit": "official_2025_CUSEC_indivisible",
    "contiguity": "positive_line_shared_boundary_on_original_polygon_parts",
    "municipal_indivisibility": "preserve_when_feasible_split_by_whole_CUSEC_when_necessary",
    "islands": "preserve_physical_islands_named_exceptions_only",
    "enclaves": "accredited_administrative_enclaves_named_exceptions_only",
    "physical_discontinuities": "case_registry_bound_to_edition_cusec_parts_and_hashes",
}
N08_POPULATION_RATIOS = {
    "population_floor_ratio": Decimal("0.85"),
    "population_cap_ratio": Decimal("1.15"),
    "target_tolerance_ratio": Decimal("0.15"),
}
POLICY_RULES = (
    "minimum_unit", "contiguity", "population_limits",
    "municipal_indivisibility", "islands", "enclaves",
    "physical_discontinuities",
)


def _approved_policy_errors(payload: Mapping[str, Any]) -> list[str]:
    """Admit only explicitly versioned owner-approved national policies."""
    decisions = payload.get("decisions")
    if not isinstance(decisions, Mapping):
        return []
    errors: list[str] = []
    for name in POLICY_RULES:
        decision = decisions.get(name)
        if not isinstance(decision, Mapping) or decision.get("status") != "APPROVED":
            continue
        if decision.get("decision_id") != N08_OWNER_DECISION_ID:
            errors.append("APPROVED_POLICY_DECISION_ID_INVALID:" + name)
        value = decision.get("value")
        if name != "population_limits":
            if not isinstance(value, str) or value != N08_POLICY_VALUES[name]:
                errors.append("APPROVED_POLICY_VALUE_INVALID:" + name)
            continue
        if not isinstance(value, Mapping) or set(value) != set(N08_POPULATION_RATIOS):
            errors.append("APPROVED_POPULATION_LIMITS_FIELDS_INVALID")
            continue
        if any(type(value[key]) not in (int, float) for key in N08_POPULATION_RATIOS):
            errors.append("APPROVED_POPULATION_LIMITS_NUMERIC_REQUIRED")
            continue
        numbers = {key: Decimal(str(value[key])) for key in N08_POPULATION_RATIOS}
        if not all(number.is_finite() for number in numbers.values()):
            errors.append("APPROVED_POPULATION_LIMITS_NONFINITE")
        elif numbers != N08_POPULATION_RATIOS:
            errors.append("APPROVED_POPULATION_LIMITS_NOT_OWNER_APPROVED")
    minimum = payload.get("minimum_unit")
    named = decisions.get("minimum_unit")
    if isinstance(named, Mapping) and named.get("status") == "APPROVED":
        if (not isinstance(minimum, Mapping)
                or minimum.get("status") != "APPROVED"
                or minimum.get("value") != named.get("value")):
            errors.append("APPROVED_MINIMUM_UNIT_REPRESENTATIONS_CONFLICT")
    return errors


def validate_congress_identity(payload: Mapping[str, Any]) -> dict[str, Any]:
    """Validate routing identity and the fixed 52-code universe only.

    A successful result is structural admission for a synthetic contract test;
    it does not accredit sources, select K, or authorize territorial modules.
    """
    if not isinstance(payload, Mapping):
        raise ValueError("CONGRESS_CONTRACT_INVALID: payload must be an object")
    payload = _normalize_origin_units(payload)
    errors: list[str] = []
    unknown = set(payload) - ALLOWED_CONTRACT_FIELDS
    if unknown:
        errors.append("CONTRACT_FIELDS_UNKNOWN:" + ",".join(sorted(map(str, unknown))))
    errors.extend(_validate_closed_objects(payload))
    errors.extend(_approved_policy_errors(payload))
    errors.extend(_approved_k_errors(payload))
    accreditation = payload.get("accreditation")
    if ("accreditation" in payload
            and (not isinstance(accreditation, Mapping)
                 or accreditation.get("generation_authorized") is not False)):
        errors.append("GENERATION_AUTHORIZATION_MUST_REMAIN_FALSE")
    def find_forbidden(value: Any, path: str = "$") -> list[str]:
        found: list[str] = []
        if isinstance(value, Mapping):
            for key, child in value.items():
                normalized = re.sub(r"[^a-z0-9]", "", str(key).lower())
                if (normalized in {re.sub(r"[^a-z0-9]", "", x.lower()) for x in FORBIDDEN_AUTONOMOUS_FIELDS}
                        or any(fragment in normalized for fragment in FORBIDDEN_KEY_FRAGMENTS)):
                    found.append(f"{path}.{key}")
                found.extend(find_forbidden(child, f"{path}.{key}"))
        elif isinstance(value, (list, tuple)):
            for index, child in enumerate(value):
                found.extend(find_forbidden(child, f"{path}[{index}]"))
        return found
    contaminated = find_forbidden(payload)
    if contaminated:
        errors.append("AUTONOMOUS_INPUT_FORBIDDEN:" + ",".join(contaminated))
    if payload.get("execution_identity") != "congreso":
        errors.append("EXECUTION_IDENTITY_MUST_BE_CONGRESO")
    if payload.get("territory_id") != "espana_congreso":
        errors.append("TERRITORY_ID_MUST_BE_ESPANA_CONGRESO")
    if payload.get("scope") != "congreso":
        errors.append("SCOPE_MUST_BE_CONGRESO")
    if payload.get("orchestrator") not in ALLOWED_ORCHESTRATORS:
        errors.append("CONGRESS_ORCHESTRATOR_NOT_ALLOWED")

    raw_codes = payload.get("circumscription_codes")
    rows = payload.get("circumscriptions")
    row_codes = None
    if "circumscriptions" in payload and not isinstance(rows, list):
        errors.append("CIRCUMSCRIPTIONS_MUST_BE_LIST")
    if isinstance(rows, list):
        row_codes = [
            row.get("code") if isinstance(row, Mapping) else None
            for row in rows
        ]
        if raw_codes is None:
            raw_codes = row_codes
    if not isinstance(raw_codes, list) or any(not isinstance(code, str) for code in raw_codes):
        errors.append("CIRCUMSCRIPTION_CODES_MUST_BE_STRING_LIST")
    else:
        if len(raw_codes) != len(set(raw_codes)):
            errors.append("CIRCUMSCRIPTION_CODE_DUPLICATE")
        found = set(raw_codes)
        missing = sorted(set(CONGRESS_CODES) - found)
        extra = sorted(found - set(CONGRESS_CODES))
        if missing:
            errors.append("CIRCUMSCRIPTION_CODE_MISSING:" + ",".join(missing))
        if extra:
            errors.append("CIRCUMSCRIPTION_CODE_UNEXPECTED:" + ",".join(extra))
        if row_codes is not None:
            representations_match = (
                len(row_codes) == len(raw_codes)
                and all(isinstance(code, str) for code in row_codes)
                and len(set(row_codes)) == len(set(raw_codes))
                and set(row_codes) == set(raw_codes)
            )
            if not representations_match:
                errors.append("CIRCUMSCRIPTION_REPRESENTATIONS_CONFLICT")
        if isinstance(rows, list) and len(rows) == 52:
            expected_classes = {
                **{code: "province" for code in PROVINCE_CODES},
                **{code: "autonomous_city" for code in AUTONOMOUS_CITY_CODES},
            }
            if any(
                not isinstance(row, Mapping)
                or not isinstance(row.get("code"), str)
                or row.get("class") != expected_classes.get(row["code"])
                or set(row) - {"code", "class"}
                for row in rows
            ):
                errors.append("CIRCUMSCRIPTION_CLASSIFICATION_INVALID")

    k_decision = payload.get("k_decision")
    if isinstance(k_decision, Mapping):
        if set(k_decision) - {"status", "total", "source_scope", "source_territory_id", "decision_id", "quota_method"}:
            errors.append("K_DECISION_FIELDS_UNKNOWN")
        if k_decision.get("source_scope") not in (None, "congreso"):
            errors.append("K_SOURCE_SCOPE_MUST_BE_CONGRESO")
        if k_decision.get("source_territory_id") not in (None, "espana_congreso"):
            errors.append("K_SOURCE_TERRITORY_MUST_BE_CONGRESO")

    if errors:
        raise ValueError("CONGRESS_CONTRACT_INVALID: " + ";".join(errors))
    return {
        "status": "STRUCTURAL_SCOPE_ADMITTED",
        "execution_identity": "congreso",
        "territory_id": "espana_congreso",
        "province_codes": list(PROVINCE_CODES),
        "autonomous_city_codes": list(AUTONOMOUS_CITY_CODES),
        "circumscription_count": len(CONGRESS_CODES),  # deprecated administrative count
        "origin_unit_count": len(CONGRESS_CODES),
        "electoral_district_count": (payload["k_decision"].get("total") if isinstance(payload.get("k_decision"), Mapping) else None),
        "generation_authorized": False,
    }


def production_blockers(contract: Mapping[str, Any]) -> list[str]:
    """Fail-closed readiness check; this function never launches modules."""
    blockers: list[str] = []
    try:
        contract = _normalize_origin_units(contract)
        validate_congress_identity(contract)
    except ValueError as exc:
        message = str(exc)
        blockers.append(message)
        if message.startswith("CONGRESS_CONTRACT_INVALID: "):
            blockers.extend(message.split(": ", 1)[1].split(";"))
        # Preserve independently actionable structural blockers even when
        # an owner-approved K claim is rejected first.
        barriers = contract.get("barriers") if isinstance(contract, Mapping) else None
        if (not isinstance(barriers, Mapping)
                or barriers.get("province_circumscription") != "hard"
                or barriers.get("ceuta_melilla_separate") is not True
                or barriers.get("cross_circumscription_edges") is not False):
            blockers.append("MANDATORY_CIRCUMSCRIPTION_BARRIERS_MISSING_OR_INVALID")
        quotas = contract.get("quotas_by_circumscription") if isinstance(contract, Mapping) else None
        if isinstance(quotas, list):
            codes = [row.get("code") for row in quotas if isinstance(row, Mapping)]
            if (len(quotas) != 52 or len(codes) != 52
                    or any(not isinstance(code, str) for code in codes)
                    or len(set(codes)) != 52 or set(codes) != set(CONGRESS_CODES)):
                blockers.append("CIRCUMSCRIPTION_QUOTAS_MUST_COVER_52_CODES_EXACTLY")
        return sorted(set(blockers))

    decision = contract.get("institutional_decision")
    k = contract.get("k_decision")
    if not isinstance(decision, Mapping) or decision.get("status") != "APPROVED_BY_OWNER":
        blockers.append("OWNER_DECISION_PENDING")
    if not isinstance(k, Mapping) or type(k.get("total")) is not int or k["total"] < 52:
        blockers.append("CONGRESS_K_UNDECIDED_OR_INVALID")
    elif k.get("source_scope") != "congreso" or not k.get("decision_id"):
        blockers.append("CONGRESS_K_PROVENANCE_MISSING")

    barriers = contract.get("barriers")
    if (not isinstance(barriers, Mapping)
            or barriers.get("province_circumscription") != "hard"
            or barriers.get("ceuta_melilla_separate") is not True
            or barriers.get("cross_circumscription_edges") is not False):
        blockers.append("MANDATORY_CIRCUMSCRIPTION_BARRIERS_MISSING_OR_INVALID")

    quotas = contract.get("quotas_by_circumscription")
    if not isinstance(quotas, list):
        blockers.append("CIRCUMSCRIPTION_QUOTAS_MISSING")
    else:
        if any(not isinstance(row, Mapping) or set(row) - {"code", "k"} for row in quotas):
            blockers.append("CIRCUMSCRIPTION_QUOTA_FIELDS_INVALID")
        quota_codes = [row.get("code") for row in quotas if isinstance(row, Mapping)]
        valid_quota_codes = all(isinstance(code, str) for code in quota_codes)
        if (len(quotas) != 52 or not valid_quota_codes
                or len(quota_codes) != len(set(quota_codes))
                or set(quota_codes) != set(CONGRESS_CODES)):
            blockers.append("CIRCUMSCRIPTION_QUOTAS_MUST_COVER_52_CODES_EXACTLY")
        elif any(type(row.get("k")) is not int or row["k"] < 1 for row in quotas):
            blockers.append("CIRCUMSCRIPTION_QUOTAS_MUST_BE_POSITIVE_INTEGERS")
        elif isinstance(k, Mapping) and sum(row["k"] for row in quotas) != k.get("total"):
            blockers.append("CIRCUMSCRIPTION_QUOTAS_DO_NOT_SUM_TO_K")

    sources = contract.get("sources")
    for role in ("geometry", "population"):
        source = sources.get(role) if isinstance(sources, Mapping) else None
        if not isinstance(source, Mapping):
            blockers.append(f"SOURCE_{role.upper()}_MISSING")
            continue
        if source.get("accreditation") != "ACCREDITED":
            blockers.append(f"SOURCE_{role.upper()}_NOT_ACCREDITED")
        if not source.get("edition") or not source.get("year"):
            blockers.append(f"SOURCE_{role.upper()}_EDITION_OR_YEAR_MISSING")
        if not re.fullmatch(r"[0-9a-f]{64}", str(source.get("sha256") or "")):
            blockers.append(f"SOURCE_{role.upper()}_SHA256_INVALID")
        if not source.get("authority") or not source.get("acquisition_record"):
            blockers.append(f"SOURCE_{role.upper()}_PROVENANCE_MISSING")

    accreditation = contract.get("accreditation")
    if (not isinstance(accreditation, Mapping)
            or accreditation.get("generation_authorized") is not False):
        blockers.append("GENERATION_AUTHORIZATION_MUST_REMAIN_FALSE")

    decisions = contract.get("decisions")
    required_decisions = (
        "minimum_unit", "population_reference", "contiguity", "population_limits",
        "municipal_indivisibility", "islands", "enclaves", "physical_discontinuities",
    )
    for item in required_decisions:
        value = decisions.get(item) if isinstance(decisions, Mapping) else None
        if not isinstance(value, Mapping) or value.get("status") != "APPROVED":
            blockers.append(f"DECISION_{item.upper()}_PENDING")

    accreditation = contract.get("circumscription_accreditation")
    accredited_codes = accreditation if isinstance(accreditation, list) else []
    valid_accredited_codes = all(isinstance(code, str) for code in accredited_codes)
    if (len(accredited_codes) != 52 or not valid_accredited_codes
            or len(set(accredited_codes)) != 52 or set(accredited_codes) != set(CONGRESS_CODES)):
        blockers.append("CIRCUMSCRIPTION_COVERAGE_NOT_ACCREDITED_52_OF_52")

    return sorted(set(blockers))


def validate_production_admission(contract: Mapping[str, Any]) -> dict[str, Any]:
    """Raise unless every institutional, source and coverage gate is satisfied."""
    blockers = production_blockers(contract)
    if blockers:
        raise ValueError("CONGRESS_PRODUCTION_BLOCKED: " + ";".join(blockers))
    return {"status": "CONTRACT_ADMITTED_ONLY", "generation_authorized": False}
