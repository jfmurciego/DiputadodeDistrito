"""Conservative composition of accredited gaps in electoral result sources.

This module does not decide that a source is official.  It composes normalized
records only after the caller supplies a canonical election identity, an
accredited expected universe and explicit source admissibility/status metadata.
The primary source is immutable: an explicit zero is a present value, never a
hole, and no fragment can overwrite it.
"""
from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
import csv
import hashlib
import json
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

IDENTITY_FIELDS = ("election_id", "election_date", "election_type", "scope")
REQUIRED_ROW_FIELDS = ("unit_id", "party", "votes")


@dataclass(frozen=True)
class SourceMeta:
    source_id: str
    election_id: str
    election_date: str
    election_type: str
    scope: str
    granularity: str
    result_status: str
    artifact_sha256: str
    artifact: str
    table: str
    identity_evidence: str
    source_class: str = "unspecified"
    production_eligible: bool = False

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "SourceMeta":
        required = (
            "source_id", *IDENTITY_FIELDS, "granularity", "result_status",
            "artifact_sha256", "artifact", "table", "identity_evidence",
        )
        missing = [k for k in required if str(value.get(k) or "").strip() == ""]
        if missing:
            raise ValueError(f"metadatos de fuente incompletos: {missing}")
        sha = str(value["artifact_sha256"]).lower()
        if len(sha) != 64 or any(c not in "0123456789abcdef" for c in sha):
            raise ValueError("artifact_sha256 inválido")
        kwargs = {k: value[k] for k in cls.__dataclass_fields__ if k in value}
        kwargs["production_eligible"] = bool(value.get("production_eligible", False))
        return cls(**kwargs)


def _identity(meta: SourceMeta) -> tuple[str, str, str, str]:
    return tuple(getattr(meta, k) for k in IDENTITY_FIELDS)


def _strict_int(value: Any) -> int:
    if isinstance(value, bool) or value is None:
        raise ValueError(f"votes no entero: {value!r}")
    if isinstance(value, int):
        out = value
    else:
        raw = str(value).strip()
        if not raw or not raw.isdigit():
            raise ValueError(f"votes no entero decimal exacto: {value!r}")
        out = int(raw)
    if out < 0:
        raise ValueError("votes negativo")
    return out


def _row(
    raw: Mapping[str, Any],
    meta: SourceMeta,
    fallback_row: int,
    *,
    preserve_existing_provenance: bool = False,
) -> dict[str, Any]:
    missing = [k for k in REQUIRED_ROW_FIELDS if k not in raw or raw[k] is None]
    if missing:
        raise ValueError(f"registro sin campos obligatorios {missing}")
    unit = str(raw["unit_id"])
    party = str(raw["party"])
    if not unit or not party:
        raise ValueError("unit_id/party vacíos")
    votes = _strict_int(raw["votes"])
    unit_kind = str(raw.get("unit_kind") or "geographic")
    raw_prov = raw.get("provenance")
    provenance = deepcopy(raw_prov) if isinstance(raw_prov, Mapping) else {}
    canonical = {
        "source_id": meta.source_id,
        "election_id": meta.election_id,
        "artifact": meta.artifact,
        "artifact_sha256": meta.artifact_sha256,
        "table": str(raw.get("source_table") or provenance.get("table") or meta.table),
        "source_row": int(raw.get("source_row") or provenance.get("source_row") or fallback_row),
        "result_status": meta.result_status,
        "source_class": meta.source_class,
        "identity_evidence": meta.identity_evidence,
    }
    if preserve_existing_provenance and isinstance(raw_prov, Mapping):
        # Rows already present in the primary may have been incorporated by a
        # previous deterministic composition. Preserve their original source
        # attribution while filling any missing provenance fields.
        for key, value in canonical.items():
            provenance.setdefault(key, value)
    else:
        # A newly supplied fragment cannot spoof the checked source identity.
        provenance.update(canonical)
    locator = raw.get("source_locator") or provenance.get("source_locator")
    if locator not in (None, ""):
        provenance["source_locator"] = str(locator)
    return {
        "unit_id": unit,
        "party": party,
        "votes": votes,
        "unit_kind": unit_kind,
        "provenance": provenance,
    }


def _dedupe(
    rows: Sequence[Mapping[str, Any]], meta: SourceMeta, *, primary: bool = False
) -> tuple[dict[tuple[str, str, str], dict[str, Any]], list[dict[str, Any]]]:
    out: dict[tuple[str, str, str], dict[str, Any]] = {}
    conflicts: list[dict[str, Any]] = []
    for i, raw in enumerate(rows, 1):
        item = _row(raw, meta, i, preserve_existing_provenance=primary)
        key = (item["unit_kind"], item["unit_id"], item["party"])
        old = out.get(key)
        if old is None:
            out[key] = item
        elif old["votes"] != item["votes"]:
            conflicts.append({
                "code": "PRIMARY_CONTRADICTORY_DUPLICATE" if primary else "CONTRADICTORY_DUPLICATE",
                "unit_kind": key[0], "unit_id": key[1], "party": key[2],
                "values": sorted({old["votes"], item["votes"]}),
                "source_id": meta.source_id,
            })
    return out, conflicts


def _logical_row(row: Mapping[str, Any]) -> dict[str, Any]:
    prov = row.get("provenance") if isinstance(row.get("provenance"), Mapping) else {}
    return {
        "unit_kind": row["unit_kind"],
        "unit_id": row["unit_id"],
        "party": row["party"],
        "votes": row["votes"],
        "source_id": prov.get("source_id"),
        "artifact_sha256": prov.get("artifact_sha256"),
        "table": prov.get("table"),
        "result_status": prov.get("result_status"),
    }


def _digest(rows: Sequence[Mapping[str, Any]], special: Sequence[Mapping[str, Any]]) -> str:
    key = lambda r: (r["unit_kind"], r["unit_id"], r["party"])
    payload = {
        "rows": [_logical_row(r) for r in sorted(rows, key=key)],
        "special_units": [_logical_row(r) for r in sorted(special, key=key)],
    }
    raw = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(raw).hexdigest()


def compose_records(
    primary_rows: Sequence[Mapping[str, Any]],
    primary_source: Mapping[str, Any],
    fragments: Sequence[tuple[Mapping[str, Any], Sequence[Mapping[str, Any]]]],
    *,
    expected_keys: Iterable[tuple[str, str]],
    allowed_parties: Iterable[str] | None = None,
    allowed_status_pairs: Iterable[tuple[str, str]] = (),
    official_geographic_candidate_votes: int | None = None,
    official_total_candidate_votes: int | None = None,
) -> dict[str, Any]:
    """Fill only absent accredited (unit, party) keys and preserve provenance.

    Non-geographic units such as CERA are never inserted in the geographic
    product. They are kept under special_units for separate reconciliation.
    Differing primary values, including explicit zeroes, are immutable and block
    the affected unit instead of being overwritten.
    """
    pmeta = SourceMeta.from_mapping(primary_source)
    pindex, conflicts = _dedupe(primary_rows, pmeta, primary=True)
    expected = {(str(u), str(p)) for u, p in expected_keys}
    parties = None if allowed_parties is None else {str(p) for p in allowed_parties}
    status_pairs = {(str(a), str(b)) for a, b in allowed_status_pairs}

    primary_geo = {k: v for k, v in pindex.items() if k[0] == "geographic"}
    primary_special = {k: v for k, v in pindex.items() if k[0] != "geographic"}
    primary_pairs = {(k[1], k[2]) for k in primary_geo}
    primary_outside = sorted(primary_pairs - expected)
    for unit, party in primary_outside:
        conflicts.append({
            "code": "PRIMARY_OUTSIDE_ACCREDITED_UNIVERSE",
            "unit_id": unit,
            "party": party,
            "source_id": pmeta.source_id,
        })
    base_snapshot = deepcopy(list(primary_geo.values()))
    additions: dict[tuple[str, str, str], dict[str, Any]] = {}
    special = dict(primary_special)
    ignored_identical: list[dict[str, Any]] = []
    blocked_units: set[str] = {
        str(c["unit_id"]) for c in conflicts if c.get("unit_id")
    }
    used_fragment_metas: dict[str, SourceMeta] = {}
    mixed_status = False

    for raw_meta, rows in fragments:
        meta = SourceMeta.from_mapping(raw_meta)
        if _identity(meta) != _identity(pmeta):
            conflicts.append({
                "code": "ELECTION_IDENTITY_MISMATCH",
                "source_id": meta.source_id,
                "primary_identity": dict(zip(IDENTITY_FIELDS, _identity(pmeta))),
                "fragment_identity": dict(zip(IDENTITY_FIELDS, _identity(meta))),
            })
            continue
        if meta.granularity != pmeta.granularity:
            conflicts.append({
                "code": "GRANULARITY_MISMATCH",
                "source_id": meta.source_id,
                "primary_granularity": pmeta.granularity,
                "fragment_granularity": meta.granularity,
            })
            continue
        if meta.result_status != pmeta.result_status:
            if (pmeta.result_status, meta.result_status) not in status_pairs:
                conflicts.append({
                    "code": "RESULT_STATUS_MISMATCH",
                    "source_id": meta.source_id,
                    "primary_status": pmeta.result_status,
                    "fragment_status": meta.result_status,
                })
                continue
            mixed_status = True

        findex, local_conflicts = _dedupe(rows, meta)
        conflicts.extend(local_conflicts)
        blocked_units.update(str(c["unit_id"]) for c in local_conflicts if c.get("unit_id"))
        used_fragment_metas[meta.source_id] = meta

        for key, item in sorted(findex.items()):
            kind, unit, party = key
            if parties is not None and party not in parties:
                conflicts.append({
                    "code": "UNRESOLVED_PARTY", "source_id": meta.source_id,
                    "unit_id": unit, "party": party,
                })
                blocked_units.add(unit)
                continue

            if kind != "geographic":
                old = special.get(key)
                if old is None:
                    special[key] = item
                elif old["votes"] == item["votes"]:
                    ignored_identical.append({
                        "unit_kind": kind, "unit_id": unit, "party": party,
                        "source_id": meta.source_id,
                    })
                else:
                    conflicts.append({
                        "code": "SPECIAL_UNIT_CONFLICT", "unit_id": unit,
                        "party": party, "values": [old["votes"], item["votes"]],
                        "source_id": meta.source_id,
                    })
                continue

            pair = (unit, party)
            old = primary_geo.get(key)
            if old is not None:
                if old["votes"] == item["votes"]:
                    ignored_identical.append({
                        "unit_id": unit, "party": party, "source_id": meta.source_id,
                    })
                else:
                    conflicts.append({
                        "code": "PRIMARY_VALUE_CONFLICT", "unit_id": unit,
                        "party": party, "primary_votes": old["votes"],
                        "fragment_votes": item["votes"], "source_id": meta.source_id,
                        "primary_was_explicit_zero": old["votes"] == 0,
                        "primary_provenance": old.get("provenance"),
                        "fragment_provenance": item.get("provenance"),
                    })
                    blocked_units.add(unit)
                continue
            if pair not in expected:
                conflicts.append({
                    "code": "OUTSIDE_ACCREDITED_UNIVERSE", "unit_id": unit,
                    "party": party, "source_id": meta.source_id,
                })
                blocked_units.add(unit)
                continue
            old_add = additions.get(key)
            if old_add is not None and old_add["votes"] != item["votes"]:
                conflicts.append({
                    "code": "FRAGMENT_CONFLICT", "unit_id": unit, "party": party,
                    "values": [old_add["votes"], item["votes"]],
                    "source_ids": [
                        old_add.get("provenance", {}).get("source_id"), meta.source_id
                    ],
                })
                blocked_units.add(unit)
            elif old_add is None:
                item = deepcopy(item)
                item["provenance"]["gap_completed"] = {"unit_id": unit, "party": party}
                additions[key] = item

    # A contradiction makes an affected geographic unit atomic: retain primary
    # content and do not inject a subset of fragment parties for that unit.
    additions = {k: v for k, v in additions.items() if k[1] not in blocked_units}
    composed_index = dict(primary_geo)
    composed_index.update(additions)

    present_pairs = {(k[1], k[2]) for k in composed_index}
    missing = sorted(expected - present_pairs)
    geo_rows = [composed_index[k] for k in sorted(composed_index)]
    special_rows = [special[k] for k in sorted(special)]
    geographic_votes = sum(r["votes"] for r in geo_rows)
    special_votes = sum(r["votes"] for r in special_rows)
    total_with_special = geographic_votes + special_votes

    reconciliation_errors: list[dict[str, Any]] = []
    if official_geographic_candidate_votes is not None and geographic_votes != int(official_geographic_candidate_votes):
        reconciliation_errors.append({
            "code": "GEOGRAPHIC_TOTAL_MISMATCH", "actual": geographic_votes,
            "expected": int(official_geographic_candidate_votes),
        })
    if official_total_candidate_votes is not None and total_with_special != int(official_total_candidate_votes):
        reconciliation_errors.append({
            "code": "TOTAL_WITH_SPECIAL_MISMATCH", "actual": total_with_special,
            "expected": int(official_total_candidate_votes),
        })

    used_sources = [pmeta, *used_fragment_metas.values()]
    admissibility_blockers = [
        {
            "code": "SOURCE_NOT_PRODUCTION_ELIGIBLE",
            "source_id": meta.source_id,
            "source_class": meta.source_class,
        }
        for meta in used_sources if not meta.production_eligible
    ]
    if mixed_status:
        admissibility_blockers.append({
            "code": "MIXED_RESULT_STATUS_REQUIRES_EXPLICIT_POLICY",
            "primary_status": pmeta.result_status,
            "fragment_status_pairs": sorted({
                (pmeta.result_status, meta.result_status)
                for meta in used_fragment_metas.values()
                if meta.result_status != pmeta.result_status
            }),
        })

    if conflicts or reconciliation_errors:
        status = "BLOCK"
    elif missing:
        status = "BLOCK_INCOMPLETE"
    elif admissibility_blockers:
        status = "BLOCK_ADMISSIBILITY"
    else:
        status = "PASS"

    # Strong conservation assertion: primary geographic content is immutable.
    primary_after = {(r["unit_kind"], r["unit_id"], r["party"], r["votes"]) for r in geo_rows}
    for r in base_snapshot:
        assert (r["unit_kind"], r["unit_id"], r["party"], r["votes"]) in primary_after

    report = {
        "schema": "ddd-electoral-gap-fill/1.0",
        "status": status,
        "identity": dict(zip(IDENTITY_FIELDS, _identity(pmeta))),
        "granularity": pmeta.granularity,
        "primary_source_id": pmeta.source_id,
        "expected_keys": len(expected),
        "primary_present_keys": len({(k[1], k[2]) for k in primary_geo}),
        "added_keys": len(additions),
        "remaining_missing_keys": [{"unit_id": u, "party": p} for u, p in missing],
        "blocked_units": sorted(blocked_units),
        "conflicts": conflicts,
        "ignored_identical_duplicates": ignored_identical,
        "incorporated_records": [
            {
                "unit_kind": row["unit_kind"], "unit_id": row["unit_id"],
                "party": row["party"], "votes": row["votes"],
                "provenance": row.get("provenance"),
            }
            for _, row in sorted(additions.items())
        ],
        "special_units": [
            {
                "unit_kind": row["unit_kind"], "unit_id": row["unit_id"],
                "party": row["party"], "votes": row["votes"],
                "provenance": row.get("provenance"),
            }
            for row in special_rows
        ],
        "geographic_candidate_votes": geographic_votes,
        "special_candidate_votes": special_votes,
        "candidate_votes_with_special": total_with_special,
        "reconciliation_errors": reconciliation_errors,
        "admissibility_blockers": admissibility_blockers,
        "logical_digest": _digest(geo_rows, special_rows),
        "production_eligible": status == "PASS" and not admissibility_blockers,
    }
    return {"rows": geo_rows, "special_units": special_rows, "report": report}


def read_long_csv(path: Path, meta: Mapping[str, Any], *, separator: str = ";") -> list[dict[str, Any]]:
    """Read the existing DDD long section-party shape without coercing identifiers."""
    rows: list[dict[str, Any]] = []
    with Path(path).open("r", encoding="utf-8-sig", newline="") as fh:
        reader = csv.DictReader(fh, delimiter=separator)
        fields = set(reader.fieldnames or [])
        required = {"CUSEC_KEY", "party", "votes"}
        if not required.issubset(fields):
            raise ValueError(f"CSV gap filler sin columnas {sorted(required-fields)}")
        for line_no, raw in enumerate(reader, 2):
            rows.append({
                "unit_id": str(raw["CUSEC_KEY"]),
                "party": str(raw["party"]),
                "votes": raw["votes"],
                "unit_kind": str(raw.get("unit_kind") or "geographic"),
                "source_row": raw.get("source_row") or line_no,
                "source_table": str(raw.get("source_table") or meta.get("table") or Path(path).name),
                "source_locator": raw.get("source_locator") or "",
            })
    return rows


def write_composed_long_csv(result: Mapping[str, Any], out: Path) -> None:
    """Write only the geographic DDD product; special units remain in evidence."""
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=["CUSEC_KEY", "party", "votes"], delimiter=";")
        writer.writeheader()
        for row in result["rows"]:
            writer.writerow({"CUSEC_KEY": row["unit_id"], "party": row["party"], "votes": row["votes"]})


def _is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
        return True
    except ValueError:
        return False


def _load_governed_universe(
    composition: Mapping[str, Any],
    *,
    repository_root: Path,
    acquisition_root: Path | None,
    source_paths: Sequence[Path],
    source_ids: Sequence[str],
    canonical_identity: tuple[str, str, str, str],
    canonical_granularity: str,
) -> tuple[set[tuple[str, str]], dict[str, Any]]:
    declaration = composition.get("expected_universe")
    if not isinstance(declaration, Mapping):
        raise ValueError(
            "electoral_gap_filler requiere expected_universe gobernado; "
            "expected_universe_path aislado no acredita independencia"
        )

    required = (
        "path", "sha256", "source_id", "source_class", "identity_evidence",
        "election_identity", "granularity", "derived_from_source_ids",
    )
    missing = [k for k in required if k not in declaration or declaration.get(k) in (None, "")]
    if missing:
        raise ValueError(f"expected_universe incompleto: {missing}")

    raw_path = Path(str(declaration["path"]))
    if raw_path.is_absolute():
        raise ValueError("expected_universe.path debe ser relativo al repositorio")
    if any(part.startswith(".ddd-") for part in raw_path.parts):
        raise ValueError("expected_universe.path no puede apuntar a artefactos temporales .ddd-*")

    repo = Path(repository_root).resolve()
    universe_path = (repo / raw_path).resolve()
    if not _is_relative_to(universe_path, repo):
        raise ValueError("expected_universe.path escapa de la raíz del repositorio")
    if not universe_path.is_file():
        raise ValueError(f"expected_universe ausente: {raw_path.as_posix()}")

    if acquisition_root is not None:
        acquire = Path(acquisition_root).resolve()
        if _is_relative_to(universe_path, acquire):
            raise ValueError("expected_universe no puede proceder del directorio temporal de adquisición")

    resolved_sources = {Path(p).resolve() for p in source_paths}
    if universe_path in resolved_sources:
        raise ValueError("expected_universe no puede ser uno de los fragmentos consumidos")

    universe_source_id = str(declaration.get("source_id") or "")
    if universe_source_id in {str(x) for x in source_ids}:
        raise ValueError("expected_universe.source_id debe ser independiente de las fuentes de votos")

    derived_raw = declaration.get("derived_from_source_ids")
    if not isinstance(derived_raw, list):
        raise ValueError("expected_universe.derived_from_source_ids debe ser una lista explícita")
    derived_from = {str(x) for x in derived_raw}
    overlap = sorted(derived_from & {str(x) for x in source_ids})
    if overlap:
        raise ValueError(
            "expected_universe declara derivación desde fuentes de votos consumidas: "
            + ", ".join(overlap)
        )

    expected_sha = str(declaration.get("sha256") or "").lower()
    if len(expected_sha) != 64 or any(c not in "0123456789abcdef" for c in expected_sha):
        raise ValueError("expected_universe.sha256 inválido")
    actual_sha = hashlib.sha256(universe_path.read_bytes()).hexdigest()
    if actual_sha != expected_sha:
        raise ValueError(
            f"SHA-256 del expected_universe no coincide: declared={expected_sha} actual={actual_sha}"
        )

    universe_identity_raw = declaration.get("election_identity") or {}
    universe_identity = tuple(str(universe_identity_raw.get(k) or "") for k in IDENTITY_FIELDS)
    if universe_identity != canonical_identity:
        raise ValueError(
            "Identidad electoral del expected_universe no coincide con la composición canónica: "
            f"universe={universe_identity} canonical={canonical_identity}"
        )
    universe_granularity = str(declaration.get("granularity") or "")
    if universe_granularity != canonical_granularity:
        raise ValueError(
            "Granularidad del expected_universe no coincide con la composición canónica: "
            f"universe={universe_granularity} canonical={canonical_granularity}"
        )

    with universe_path.open("r", encoding="utf-8-sig", newline="") as fh:
        reader = csv.DictReader(
            fh, delimiter=str(declaration.get("separator") or composition.get("universe_separator") or ";")
        )
        fields = set(reader.fieldnames or [])
        required_fields = {"CUSEC_KEY", "party"}
        if not required_fields.issubset(fields):
            raise ValueError(f"Universo electoral sin columnas {sorted(required_fields-fields)}")
        expected_rows = [(str(r["CUSEC_KEY"]), str(r["party"])) for r in reader]
    if not expected_rows:
        raise ValueError("Universo electoral acreditado vacío")
    expected = set(expected_rows)
    if len(expected) != len(expected_rows):
        raise ValueError("Universo electoral acreditado contiene claves unidad+candidatura duplicadas")

    evidence = {
        "source_id": universe_source_id,
        "source_class": str(declaration.get("source_class") or ""),
        "identity_evidence": str(declaration.get("identity_evidence") or ""),
        "path": raw_path.as_posix(),
        "sha256": actual_sha,
        "election_identity": dict(zip(IDENTITY_FIELDS, universe_identity)),
        "granularity": universe_granularity,
        "derived_from_source_ids": sorted(derived_from),
        "records": len(expected_rows),
        "unique_keys": len(expected),
    }
    return expected, evidence


def compose_delimited_sources(
    source_paths: Sequence[Path],
    source_declarations: Sequence[Mapping[str, Any]],
    selected_sources: Sequence[Mapping[str, Any]],
    composition: Mapping[str, Any],
    out: Path,
    *,
    repository_root: Path | None = None,
    acquisition_root: Path | None = None,
) -> dict[str, Any]:
    """Integration hook for preparar_fuente_electoral.

    Vote sources have already passed the repository checker. The expected
    universe is a separate governed artifact: repo-confined, hash-pinned,
    election-identified, granular, and explicitly independent from consumed
    vote-source ids.
    """
    if len(source_paths) != len(source_declarations) or len(source_paths) != len(selected_sources):
        raise ValueError("electoral_gap_filler recibió metadatos de fuentes desalineados")
    primary_id = str(composition.get("primary_source_id") or "")
    if not primary_id:
        raise ValueError("electoral_gap_filler requiere primary_source_id")

    identities = {
        "election_id": str(composition.get("election_id") or ""),
        "election_date": str(composition.get("election_date") or ""),
        "election_type": str(composition.get("election_type") or ""),
        "scope": str(composition.get("scope") or ""),
        "granularity": str(composition.get("granularity") or "section_party"),
    }
    if any(not identities[k] for k in IDENTITY_FIELDS):
        raise ValueError("electoral_gap_filler requiere identidad canónica completa")

    declared_ids = [str(row.get("id") or "").strip() for row in source_declarations]
    selected_ids = [str(row.get("id") or "").strip() for row in selected_sources]
    if any(not sid for sid in declared_ids):
        raise ValueError("source_declarations contiene source.id vacío")
    if any(not sid for sid in selected_ids):
        raise ValueError("selected_sources contiene id vacío")
    if len(set(declared_ids)) != len(declared_ids):
        raise ValueError("source_declarations contiene source.id duplicado")
    if len(set(selected_ids)) != len(selected_ids):
        raise ValueError("selected_sources contiene id duplicado")

    metas: list[dict[str, Any]] = []
    source_rows: list[list[dict[str, Any]]] = []
    source_ids: list[str] = []
    for path, declared, selected in zip(source_paths, source_declarations, selected_sources, strict=True):
        declared_id = str(declared.get("id") or "").strip()
        selected_id = str(selected.get("id") or "").strip()
        if declared_id != selected_id:
            raise ValueError(
                "Asociación fuente/artefacto inconsistente: "
                f"declared.id={declared_id!r} selected.id={selected_id!r}"
            )
        sid = declared_id
        selected_sha = str(selected.get("sha256") or "").lower()
        actual_sha = hashlib.sha256(Path(path).read_bytes()).hexdigest()
        if not selected_sha or actual_sha != selected_sha:
            raise ValueError(
                f"SHA-256 de artefacto no coincide para {sid}: declared={selected_sha} actual={actual_sha}"
            )
        source_identity = declared.get("election_identity") or {}
        meta = {
            "source_id": sid,
            **{field: str(source_identity.get(field) or "") for field in IDENTITY_FIELDS},
            "granularity": str(declared.get("granularity") or ""),
            "result_status": str(declared.get("result_status") or ""),
            "artifact_sha256": selected_sha,
            "artifact": str(selected.get("artifact_path") or Path(path).name),
            "table": str(declared.get("table") or Path(path).name),
            "source_class": str(declared.get("source_class") or "official"),
            "identity_evidence": str(declared.get("identity_evidence") or ""),
            "production_eligible": bool(declared.get("promotion_allowed", False)),
        }
        metas.append(meta)
        source_ids.append(sid)
        source_rows.append(read_long_csv(Path(path), meta))

    try:
        primary_pos = next(i for i, m in enumerate(metas) if m["source_id"] == primary_id)
    except StopIteration as exc:
        raise ValueError(f"primary_source_id no seleccionado: {primary_id}") from exc

    canonical_identity = tuple(identities[field] for field in IDENTITY_FIELDS)
    primary_identity = tuple(str(metas[primary_pos].get(field) or "") for field in IDENTITY_FIELDS)
    if primary_identity != canonical_identity:
        raise ValueError(
            "La identidad electoral de la fuente principal no coincide con la composición canónica: "
            f"primary={primary_identity} canonical={canonical_identity}"
        )
    if str(metas[primary_pos].get("granularity") or "") != identities["granularity"]:
        raise ValueError(
            "La granularidad de la fuente principal no coincide con la composición canónica: "
            f"primary={metas[primary_pos].get('granularity')} canonical={identities['granularity']}"
        )

    repo_root = Path(repository_root or ".").resolve()
    expected, universe_evidence = _load_governed_universe(
        composition,
        repository_root=repo_root,
        acquisition_root=acquisition_root,
        source_paths=[Path(p) for p in source_paths],
        source_ids=source_ids,
        canonical_identity=canonical_identity,
        canonical_granularity=identities["granularity"],
    )

    allowed_parties = sorted({party for _, party in expected})
    status_pairs = [tuple(x) for x in (composition.get("allowed_status_pairs") or [])]
    result = compose_records(
        source_rows[primary_pos], metas[primary_pos],
        [(metas[i], source_rows[i]) for i in range(len(metas)) if i != primary_pos],
        expected_keys=expected,
        allowed_parties=allowed_parties,
        allowed_status_pairs=status_pairs,
        official_geographic_candidate_votes=composition.get("official_geographic_candidate_votes"),
        official_total_candidate_votes=composition.get("official_total_candidate_votes"),
    )
    result["report"]["expected_universe"] = universe_evidence

    evidence = Path(out).with_suffix(Path(out).suffix + ".gap-fill.json")
    evidence.write_text(
        json.dumps(result["report"], ensure_ascii=False, indent=2, sort_keys=True)+"\n",
        encoding="utf-8",
    )
    status = str(result["report"]["status"])
    if status == "PASS":
        write_composed_long_csv(result, Path(out))
    return {
        "records": len(result["rows"]),
        "columns": ["CUSEC_KEY", "party", "votes"],
        "composition": "electoral_gap_filler",
        "status": status,
        "production_eligible": bool(result["report"]["production_eligible"]),
        "evidence_path": evidence.as_posix(),
        "logical_digest": result["report"]["logical_digest"],
        "expected_universe": universe_evidence,
    }

