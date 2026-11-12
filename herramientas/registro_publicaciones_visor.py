#!/usr/bin/env python3
"""Registro durable y verificable de publicaciones del visor DDD.

Los artefactos de Actions sólo pueden actuar como fuente transitoria de una
promoción. El registro definitivo acepta únicamente activos persistentes con
ubicación inmutable e integridad SHA-256 verificable.

VERSIÓN: 1.8.1 · FECHA: 2026-11-12 · ESTADO: candidato
CAMBIOS 1.8.0 (T-249): publicar un territorio es registrar el PAR. `candidate` (CLI) rechaza, todo o nada, si en un
  territorio tocado por las entradas canónicas el M08 vigente falta o no es del linaje del M06 vigente
  (`linaje_m06_m08.pares_incompletos`: mismo run o manifiesto del run del M08 que acredita la 02 del M06). `make_candidate`
  no cambia; `--evidence-root` (por defecto la raíz del repo) indica dónde están los manifiestos.
MOTIVO 1.8.0: el lote P50 43030563528 registró solo los M06 de 34 territorios (mapa nuevo con resultados de otro linaje).
CAMBIOS 1.8.1 (T-220): ids de territorio nuevos de la tabla maestra (aut01…nac52, D-61); el id viejo se lee vía ddd_core.territorio_ids.
ANTERIOR: legacy/herramientas/registro_publicaciones_visor_v1.8.0_20261112.py
CAMBIOS 1.7.0 (T-237): publicación por lotes. `parse_run_ids` (CLI `parse-run-ids`) lee `production_run_id` como lista
  separada por espacios o comas: cada id, solo cifras; un id repetido se RECHAZA (no se deduplica: suele ser una errata y
  el lote debe decir exactamente qué se publica); lista vacía = «solo sitio»; `--scenario-id` solo con un id.
  `merge_batch_descriptors` (CLI `merge-descriptors`) junta los descriptores de cada run y rechaza dos runs del mismo
  territorio en un lote. Con un solo id la salida es la misma que en 1.6.1.
MOTIVO 1.7.0: publicar N territorios exigía N despliegues y N aprobaciones de `produccion`.
ANTERIOR: legacy/herramientas/registro_publicaciones_visor_v1.6.1_20261111.py
CAMBIOS 1.6.1 (T-203): ELECCION_POR_DEFECTO se importa de eleccion_por_defecto.py (módulo ligero, sin pyproj); mismo valor.
ANTERIOR: legacy/herramientas/registro_publicaciones_visor_v1.6.0_20261110.py
CAMBIOS 1.6.0 (T-201): `identity_key` incluye la elección como 4.º elemento (`eleccion_de`) y `_already_registered_reused_m06`
  solo reconoce un M06 reutilizado dentro de la misma elección. Sin `election_date` nada cambia (2023-07-23).
ANTERIOR: legacy/herramientas/registro_publicaciones_visor_v1.5.0_20261110.py
CAMBIOS 1.5.0 (T-199, hueco 2 del ensayo T-197): dimensión de elección OPCIONAL en las entradas (`election_date` AAAA-MM-DD y
  `election_id`). Compatible hacia atrás: sin ellas la entrada es de la elección por defecto (ELECCION_POR_DEFECTO,
  2023-07-23) y se lee igual; el esquema sigue en 2.0 y la identidad (territorio, kind, run/escenario) no cambia. Si
  traen `election_date`, debe ser una fecha válida y `election_id` (si está) debe terminar en ella. La unicidad de
  `canonical=true` pasa a ser por territorio, familia y elección. `describe-production --election-date/--election-id` y
  `eleccion_de(entry)` para los consumidores (resultados_ligeros, resultados_partidos).
MOTIVO 1.5.0: un M08 de 2026 con el mismo territory_id desplazaba al de 2023 como vigente (ganaba el run_id mayor).
CAMBIOS 1.4.0 (T-125): el registro rechaza AÑADIR cualquier territorio `congreso350_*` (mapa 350, D-18/D-19: nunca se publica):
  `make_candidate` y `production_descriptors` lanzan ValueError. Las entradas que ya figuran no se tocan y siguen validando
  (`validate_registry` solo avisa con ::warning::); retirarlas es decisión del propietario.
MOTIVO 1.4.0: la 05 42642161355 registró m06/m08 de congreso350_valladolid como canonical al resolver latest_validated.
CAMBIOS 1.3.0 (T-118): `make_candidate` no re-registra un M06 cuyo activo inmutable ya figura para el mismo territorio y
  kind bajo otro run (M06 reutilizado dentro del estado acumulativo del M08): antes fallaba con «Activo inmutable duplicado».
MOTIVO 1.3.0: la 05 de CyL (run 00 42531122768, «Reutilizar») no llegaba a registrar su M08.
CAMBIOS 1.2.0 (T-27 fase c): `describe-production --scenario-id --strategy` describe M06/M08 de una ejecución como `scenario_m06/m08` (solo adición, sin tocar canónicos).
CAMBIOS 1.1.0 (T-27 fase a): escenarios no canónicos. Kinds `scenario_m06` y `scenario_m08` con `scenario_id`, `strategy`,
  `scenario_kind` ("alternative") y `canonical` falso; los `canonical_*` no cambian (si traen `canonical`, debe ser true).
  A lo sumo una entrada `canonical: true` por territorio y familia (m06/m08); un `scenario_m08` exige el `scenario_m06`
  del mismo `scenario_id`. El registro es de solo adición: la identidad de un escenario es territorio+kind+scenario_id.
ANTERIOR: legacy/herramientas/registro_publicaciones_visor_v1.4.0_20261110.py
"""
from __future__ import annotations

import argparse
import copy
import datetime
import hashlib
import json
import re
import zipfile
from pathlib import Path

from ddd_core import territorio_ids
from herramientas.preparar_visor_ejecucion import (
    certification_status,
    first,
    production_metadata,
    read_json,
)

SCHEMA = "ddd.viewer-publication-registry/2.0"
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
ALLOWED_SOURCES = {"release_asset", "repository_blob"}
SCENARIO_KINDS = {"scenario_m06", "scenario_m08"}
CANONICAL_KINDS = {"canonical_m06", "canonical_m08"}
PRODUCT_KINDS = {"static"} | CANONICAL_KINDS | SCENARIO_KINDS
PREFIJO_MAPA_350 = "congreso350_"
from herramientas.eleccion_por_defecto import ELECCION_POR_DEFECTO  # noqa: E402,F401
import sys as _sys_t220  # noqa: E402
from pathlib import Path as _Path_t220  # noqa: E402
if str(_Path_t220(__file__).resolve().parents[1]) not in _sys_t220.path:
    _sys_t220.path.insert(0, str(_Path_t220(__file__).resolve().parents[1]))
from ddd_core.territorio_ids import mismo_territorio  # noqa: E402  (T-220: id viejo o nuevo)
STRATEGIES = {"Canónico", "GerryChain", "GerryChain 25", "GerryChain 50"}


def eleccion_de(entry: dict) -> str:
    """Fecha (AAAA-MM-DD) de la elección de una entrada; sin `election_date`, la elección por defecto."""
    return str(entry.get("election_date") or ELECCION_POR_DEFECTO)


def _validate_eleccion(entry: dict) -> None:
    fecha = entry.get("election_date")
    if fecha is None:
        if entry.get("election_id") is not None:
            raise ValueError(f"{entry.get('id')}: election_id exige election_date")
        return
    try:
        valida = bool(re.fullmatch(r"\d{4}-\d{2}-\d{2}", str(fecha))) and datetime.date.fromisoformat(str(fecha))
    except ValueError:
        valida = False
    if not valida:
        raise ValueError(f"{entry.get('id')}: election_date inválida: {fecha!r}")
    eid = entry.get("election_id")
    if eid is not None and not str(eid).endswith(str(fecha)):
        raise ValueError(f"{entry.get('id')}: election_id {eid!r} no corresponde a election_date {fecha}")


def safe_id(value: str) -> str:
    normalized = re.sub(r"[^A-Za-z0-9._-]+", "-", str(value).strip()).strip("-")
    if not normalized:
        raise ValueError("Identificador vacío")
    return normalized


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_registry(path: Path) -> dict:
    if not path.exists():
        return {"schema": SCHEMA, "products": [], "ensembles": []}
    data = json.loads(path.read_text(encoding="utf-8"))
    validate_registry(data)
    return data


def _entries(registry: dict) -> list[dict]:
    return list(registry.get("products", [])) + list(registry.get("ensembles", []))


def identity_key(entry: dict) -> tuple[str, str, str, str]:
    territory = str(entry.get("territory_id") or "")
    kind = str(entry.get("kind") or "")
    if kind == "ensemble":
        identity = str(entry.get("ensemble_id") or "")
    elif kind in SCENARIO_KINDS:
        identity = str(entry.get("scenario_id") or "")
    else:
        identity = str(entry.get("run_id") or entry.get("execution_id") or "")
    return territory, kind, identity, eleccion_de(entry)


def _validate_entry(entry: dict) -> None:
    required = (
        "id",
        "asset_type",
        "source_type",
        "immutable_location",
        "territory_id",
        "sha256",
        "kind",
    )
    _validate_eleccion(entry)
    missing = [key for key in required if not entry.get(key)]
    if missing:
        raise ValueError(f"{entry.get('id', '<sin id>')}: campos obligatorios ausentes: {missing}")
    if entry["source_type"] not in ALLOWED_SOURCES:
        raise ValueError(
            f"{entry['id']}: source_type definitivo no permitido: {entry['source_type']}; "
            "workflow_artifact sólo puede ser transitorio"
        )
    if not SHA256_RE.fullmatch(str(entry["sha256"])):
        raise ValueError(f"{entry['id']}: SHA-256 inválido")

    kind = entry["kind"]
    if kind == "ensemble":
        if not entry.get("ensemble_id"):
            raise ValueError(f"{entry['id']}: ensemble_id obligatorio")
    elif kind in PRODUCT_KINDS:
        if not (entry.get("run_id") or entry.get("execution_id")):
            raise ValueError(f"{entry['id']}: ejecución obligatoria")
        if kind in SCENARIO_KINDS:
            if not entry.get("scenario_id"):
                raise ValueError(f"{entry['id']}: scenario_id obligatorio")
            if entry.get("strategy") not in STRATEGIES:
                raise ValueError(f"{entry['id']}: strategy no admitida: {entry.get('strategy')}")
            if entry.get("scenario_kind") != "alternative":
                raise ValueError(f"{entry['id']}: scenario_kind debe ser alternative")
            if entry.get("canonical") not in (None, False):
                raise ValueError(f"{entry['id']}: un escenario no puede ser canónico")
        elif entry.get("canonical") not in (None, True):
            raise ValueError(f"{entry['id']}: canonical solo puede ser true en los kinds canónicos")
    else:
        raise ValueError(f"{entry['id']}: kind no soportado: {kind}")

    if entry["source_type"] == "release_asset":
        for key in ("asset_id", "asset_name", "release_tag"):
            if entry.get(key) in (None, ""):
                raise ValueError(f"{entry['id']}: {key} obligatorio para release_asset")
        expected = f"github-release-asset://{entry.get('repository')}/{entry['asset_id']}"
        if entry["immutable_location"] != expected:
            raise ValueError(
                f"{entry['id']}: ubicación release no inmutable o inconsistente: "
                f"{entry['immutable_location']} != {expected}"
            )
    elif entry["source_type"] == "repository_blob":
        if not entry.get("blob_sha"):
            raise ValueError(f"{entry['id']}: blob_sha obligatorio para repository_blob")
        expected = f"github-git-blob://{entry.get('repository')}/{entry['blob_sha']}"
        if entry["immutable_location"] != expected:
            raise ValueError(
                f"{entry['id']}: ubicación blob inconsistente: "
                f"{entry['immutable_location']} != {expected}"
            )


def validate_registry(registry: dict) -> None:
    if registry.get("schema") != SCHEMA:
        raise ValueError(f"Schema de registro no soportado: {registry.get('schema')}")
    if not isinstance(registry.get("products", []), list) or not isinstance(registry.get("ensembles", []), list):
        raise ValueError("products y ensembles deben ser listas")

    ids: set[str] = set()
    identities: set[tuple[str, str, str]] = set()
    locations: set[str] = set()
    for entry in _entries(registry):
        _validate_entry(entry)
        entry_id = str(entry["id"])
        if entry_id in ids:
            raise ValueError(f"ID duplicado en registro: {entry_id}")
        ids.add(entry_id)

        identity = identity_key(entry)
        if identity in identities:
            raise ValueError(f"Identidad de publicación duplicada: {identity}")
        identities.add(identity)

        location = str(entry["immutable_location"])
        if location in locations:
            raise ValueError(f"Activo inmutable duplicado en varias entradas: {location}")
        locations.add(location)

    canonical_marked: set[tuple[str, str, str]] = set()
    scenario_m06: set[tuple[str, str]] = set()
    for entry in registry.get("products", []):
        territory = str(entry.get("territory_id") or "")
        if entry.get("canonical") is True:
            family = str(entry["kind"]).rsplit("_", 1)[-1]
            if (territory, family, eleccion_de(entry)) in canonical_marked:
                raise ValueError(f"{territory}: más de una entrada canonical=true para {family}")
            canonical_marked.add((territory, family, eleccion_de(entry)))
        if entry.get("kind") == "scenario_m06":
            scenario_m06.add((territory, str(entry["scenario_id"])))
    for entry in registry.get("products", []):
        if entry.get("kind") == "scenario_m08" and (str(entry["territory_id"]), str(entry["scenario_id"])) not in scenario_m06:
            raise ValueError(f"{entry['id']}: scenario_m08 sin scenario_m06 del mismo scenario_id")


def _sorted_registry(registry: dict) -> dict:
    registry = copy.deepcopy(registry)
    registry["products"] = sorted(
        registry.get("products", []),
        key=lambda item: (
            item.get("territory_id", ""),
            item.get("kind", ""),
            str(item.get("scenario_id") or item.get("run_id") or item.get("execution_id") or ""),
            item.get("id", ""),
        ),
    )
    registry["ensembles"] = sorted(
        registry.get("ensembles", []),
        key=lambda item: (item.get("territory_id", ""), item.get("ensemble_id", ""), item.get("id", "")),
    )
    return registry


def save_registry(path: Path, registry: dict) -> None:
    validate_registry(registry)
    payload = _sorted_registry(registry)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def upsert_entry(registry: dict, entry: dict) -> None:
    _validate_entry(entry)
    collection_name = "ensembles" if entry["kind"] == "ensemble" else "products"
    collection = registry.setdefault(collection_name, [])
    identity = identity_key(entry)
    matches = [index for index, current in enumerate(collection) if identity_key(current) == identity]
    if len(matches) > 1:
        raise ValueError(f"Registro base ya contiene identidad duplicada: {identity}")
    if matches:
        collection[matches[0]] = copy.deepcopy(entry)
    else:
        collection.append(copy.deepcopy(entry))
    validate_registry(registry)


def _already_registered_reused_m06(registry: dict, entry: dict) -> bool:
    """M06 reutilizado: mismos bytes ya registrados para el territorio bajo otro run (no es un producto nuevo)."""
    if entry.get("kind") != "canonical_m06":
        return False
    key = identity_key(entry)
    for current in registry.get("products", []):
        if (
            mismo_territorio(str(current.get("territory_id") or ""), str(entry.get("territory_id")))
            and current.get("kind") == "canonical_m06"
            and current.get("immutable_location") == entry.get("immutable_location")
            and eleccion_de(current) == eleccion_de(entry)
            and identity_key(current) != key
        ):
            return True
    return False


def alias_de(territory_id: str) -> str | None:
    """T-220: id viejo del mismo territorio para una entrada nueva (`nac01` → `congreso_alava`); None si no cambia.

    El registro es de solo adición: las entradas viejas quedan intactas y las nuevas llevan `alias_de`.
    """
    try:
        viejo = territorio_ids.id_legacy(territory_id)
    except (territorio_ids.IdTerritorioDesconocido, territorio_ids.IdReservado):
        return None
    return viejo if viejo != str(territory_id) else None


def rechazar_mapa_350(territory_id: str) -> None:
    if str(territory_id).startswith(PREFIJO_MAPA_350):
        raise ValueError(f"El mapa 350 no se publica (D-18/D-19): territorio {territory_id} rechazado en el registro")


RUN_ID_RE = re.compile(r"^[0-9]+$")


def parse_run_ids(value: str | None, scenario_id: str | None = None) -> list[str]:
    """Lista de runs 00 de `production_run_id` (T-237): separadores espacio o coma; todo o nada."""
    tokens = [token for token in re.split(r"[\s,]+", str(value or "").strip()) if token]
    invalid = [token for token in tokens if not RUN_ID_RE.fullmatch(token)]
    if invalid:
        raise ValueError(f"LOTE_RUN_ID_INVALIDO: {' '.join(invalid)} (cada id es un número de run 00)")
    repeated = [token for index, token in enumerate(tokens) if token in tokens[:index]]
    if repeated:
        raise ValueError(f"LOTE_RUN_ID_DUPLICADO: {' '.join(dict.fromkeys(repeated))} (quita la repetición)")
    if scenario_id and len(tokens) > 1:
        raise ValueError("LOTE_CON_ESCENARIO: scenario_id solo admite un production_run_id")
    return tokens


def merge_batch_descriptors(per_run: list[list[dict]]) -> list[dict]:
    """Une los descriptores de cada run del lote; rechaza dos runs del mismo territorio."""
    owner: dict[str, str] = {}
    merged: list[dict] = []
    for descriptors in per_run:
        for descriptor in descriptors:
            territory, run = str(descriptor.get("territory_id", "")), str(descriptor.get("run_id", ""))
            rechazar_mapa_350(territory)
            if owner.setdefault(territory, run) != run:
                raise ValueError(
                    f"LOTE_TERRITORIO_REPETIDO: {territory} en los runs {owner[territory]} y {run}")
            merged.append(descriptor)
    return merged


def make_candidate(registry: dict, entries: list[dict]) -> dict:
    validate_registry(registry)
    for entry in entries:
        rechazar_mapa_350(entry.get("territory_id", ""))
    candidate = copy.deepcopy(registry)
    for entry in entries:
        if _already_registered_reused_m06(candidate, entry):
            continue
        upsert_entry(candidate, entry)
    validate_registry(candidate)
    return _sorted_registry(candidate)


def check_pairs(candidate: dict, entries: list[dict], evidence_root: Path | None = None) -> None:
    """T-249: cada territorio tocado por una entrada canónica queda con el par M06/M08 del mismo linaje."""
    from herramientas.linaje_m06_m08 import ROOT, pares_incompletos

    claves = {(str(e.get("territory_id", "")), eleccion_de(e)) for e in entries if e.get("kind") in CANONICAL_KINDS}
    err = pares_incompletos(_entries(candidate), claves, evidence_root or ROOT)
    if err:
        raise ValueError("PAR_INCOMPLETO (publica el M08 de la cadena; no se registra ninguno): " + "; ".join(err))


def materialized_asset_path(materialized_root: Path, entry: dict) -> Path:
    return materialized_root / safe_id(entry["id"]) / "asset"


def verify_materialized_registry(registry: dict, materialized_root: Path) -> list[dict]:
    validate_registry(registry)
    verified: list[dict] = []
    for entry in _entries(registry):
        asset = materialized_asset_path(materialized_root, entry)
        if not asset.is_file():
            raise FileNotFoundError(f"{entry['id']}: activo ausente en preflight: {asset}")
        observed = sha256_file(asset)
        expected = str(entry["sha256"])
        if observed != expected:
            raise ValueError(
                f"{entry['id']}: SHA-256 no coincide; esperado={expected} observado={observed}"
            )
        asset_type = entry["asset_type"]
        if asset_type in {"territorial_product", "electoral_product"}:
            if not zipfile.is_zipfile(asset):
                raise ValueError(f"{entry['id']}: producto persistente no es ZIP")
            with zipfile.ZipFile(asset) as archive:
                geodata = [
                    name for name in archive.namelist()
                    if name.lower().endswith((".geojson", ".json")) and not name.endswith("/")
                ]
                if len(geodata) != 1:
                    raise ValueError(f"{entry['id']}: ZIP no contiene un único GeoJSON: {geodata}")
        elif asset_type == "ensemble_archive":
            if not zipfile.is_zipfile(asset):
                raise ValueError(f"{entry['id']}: ensemble persistente no es ZIP")
        elif asset_type == "territorial_geojson":
            payload = json.loads(asset.read_text(encoding="utf-8"))
            if payload.get("type") != "FeatureCollection":
                raise ValueError(f"{entry['id']}: GeoJSON histórico inválido")
        else:
            raise ValueError(f"{entry['id']}: asset_type no soportado: {asset_type}")
        verified.append({
            "id": entry["id"],
            "immutable_location": entry["immutable_location"],
            "sha256": observed,
        })
    return verified


def production_descriptors(
    production_root: Path, run_id: str, scenario_id: str | None = None, strategy: str | None = None,
    election_date: str | None = None, election_id: str | None = None,
) -> list[dict]:
    metadata = production_metadata(production_root)
    rechazar_mapa_350(metadata["territory_id"])
    audit_path = first(production_root, "*_m06_contiguedad_geometrica.json")
    audit = read_json(audit_path)
    geometric_status = audit.get("decision", "NOT_AUDITED")
    status = metadata["production_status"]
    recorded_status = status.get("territorial_certification_status", status.get("decision"))

    descriptors: list[dict] = []
    for stage, pattern, kind, asset_type, label in (
        ("M06", "*_m06_distritos.geojson.zip", "canonical_m06", "territorial_product", "M06 territorial"),
        ("M08", "*_m08_distritos_resultados.geojson.zip", "canonical_m08", "electoral_product", "M08 electoral"),
    ):
        source = first(production_root, pattern)
        if not source:
            continue
        technical_status = recorded_status or ("BLOCK" if geometric_status == "BLOCK" else "UNKNOWN")
        certified = certification_status(technical_status, audit)
        if stage == "M06" and certified not in {"CERTIFIED", "CERTIFIED_WITH_GOVERNED_EXCEPTIONS"}:
            raise ValueError(
                f"No se promueve M06 no certificado: territorio={metadata['territory_id']} "
                f"run={run_id} technical={technical_status} geometric={geometric_status}"
            )
        if scenario_id:
            kind = kind.replace("canonical_", "scenario_")
        descriptor = {
            "id": f"{stage.lower()}-{safe_id(metadata['territory_id'])}-{safe_id(scenario_id or run_id)}",
            "asset_type": asset_type,
            "kind": kind,
            "stage": stage,
            "territory_id": metadata["territory_id"],
            "territory_label": metadata["territory_label"],
            "run_id": str(run_id),
            "expected_districts": metadata["expected_districts"],
            "technical_status": technical_status,
            "certification_status": certified,
            "territorial_certification_status": certified,
            "publication_status": "PUBLICABLE",
            "geometric_status": geometric_status,
            "geometric_gate": audit.get("gate_statement"),
            "label": f"{label} · {strategy} · {scenario_id}" if scenario_id else f"{label} · run {run_id}",
            "local_source": str(source),
        }
        if scenario_id:
            descriptor.update(scenario_id=scenario_id, strategy=strategy, scenario_kind="alternative", canonical=False)
        if alias_de(metadata["territory_id"]):
            descriptor["alias_de"] = alias_de(metadata["territory_id"])
        if election_date:
            descriptor["election_date"] = election_date
            if election_id:
                descriptor["election_id"] = election_id
        _validate_eleccion({"id": descriptor["id"], **{k: descriptor[k] for k in ("election_date", "election_id") if k in descriptor}})
        descriptors.append(descriptor)
    if not descriptors:
        raise ValueError(f"La ejecución {run_id} no contiene M06 ni M08 publicable")
    return descriptors


def _ensemble_summary(root: Path) -> tuple[Path, dict]:
    preferred = sorted(root.rglob("site/data/summary.json"))
    summary_path = preferred[0] if preferred else first(root, "summary.json")
    if not summary_path:
        raise ValueError(f"No se encontró summary.json de ensemble bajo {root}")
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    if not summary.get("territory_id"):
        raise ValueError("El ensemble no identifica territory_id")
    if not summary.get("complete"):
        raise ValueError("No se promueve un ensemble incompleto")
    return summary_path, summary


def ensemble_descriptor(ensemble_root: Path, release_tag: str) -> dict:
    _, summary = _ensemble_summary(ensemble_root)
    territory_id = str(summary["territory_id"])
    ensemble_id = safe_id(release_tag)
    return {
        "id": f"ensemble-{safe_id(territory_id)}-{ensemble_id}",
        "asset_type": "ensemble_archive",
        "kind": "ensemble",
        "territory_id": territory_id,
        "territory_label": summary.get("territory_label") or territory_id,
        **({"alias_de": alias_de(territory_id)} if alias_de(territory_id) else {}),
        "ensemble_id": ensemble_id,
        "candidate_count_expected": int(summary.get("candidate_count_expected", 0)),
        "candidate_count_valid": int(summary.get("candidate_count_valid", 0)),
        "publication_status": "PUBLICABLE",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)

    validate = sub.add_parser("validate")
    validate.add_argument("--registry", type=Path, required=True)

    verify = sub.add_parser("verify")
    verify.add_argument("--registry", type=Path, required=True)
    verify.add_argument("--materialized-root", type=Path, required=True)
    verify.add_argument("--output", type=Path)

    describe_product = sub.add_parser("describe-production")
    describe_product.add_argument("--production-root", type=Path, required=True)
    describe_product.add_argument("--run-id", required=True)
    describe_product.add_argument("--scenario-id", help="Registra la ejecución como escenario no canónico (con --strategy)")
    describe_product.add_argument("--strategy", choices=sorted(STRATEGIES))
    describe_product.add_argument("--election-date", help="AAAA-MM-DD; sin él, la entrada es de la elección por defecto")
    describe_product.add_argument("--election-id")
    describe_product.add_argument("--output", type=Path, required=True)

    describe_ens = sub.add_parser("describe-ensemble")
    describe_ens.add_argument("--ensemble-root", type=Path, required=True)
    describe_ens.add_argument("--release-tag", required=True)
    describe_ens.add_argument("--output", type=Path, required=True)

    parse_ids = sub.add_parser("parse-run-ids")
    parse_ids.add_argument("--value", default="")
    parse_ids.add_argument("--scenario-id", default="")

    merge = sub.add_parser("merge-descriptors")
    merge.add_argument("--inputs", type=Path, nargs="+", required=True)
    merge.add_argument("--output", type=Path, required=True)

    candidate = sub.add_parser("candidate")
    candidate.add_argument("--registry", type=Path, required=True)
    candidate.add_argument("--entries", type=Path, required=True)
    candidate.add_argument("--output", type=Path, required=True)
    candidate.add_argument("--evidence-root", type=Path, help="raíz con territorios/*/evidencia (por defecto, el repo)")

    args = parser.parse_args()

    if args.command == "validate":
        registry = load_registry(args.registry)
        print(json.dumps({"status": "PASS", "entries": len(_entries(registry))}, ensure_ascii=False))
        return

    if args.command == "verify":
        registry = load_registry(args.registry)
        verified = verify_materialized_registry(registry, args.materialized_root)
        payload = {"status": "PASS", "verified": verified}
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(payload, ensure_ascii=False))
        return

    if args.command == "describe-production":
        if bool(args.scenario_id) != bool(args.strategy):
            raise SystemExit("--scenario-id y --strategy van juntos")
        if args.scenario_id and not re.fullmatch(r"[a-z0-9][a-z0-9._-]{2,80}", args.scenario_id):
            raise SystemExit("--scenario-id inválido (minúsculas, cifras, punto, guion)")
        payload = production_descriptors(
            args.production_root, args.run_id, args.scenario_id, args.strategy, args.election_date, args.election_id)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return

    if args.command == "parse-run-ids":
        try:
            print(" ".join(parse_run_ids(args.value, args.scenario_id)))
        except ValueError as error:
            raise SystemExit(f"::error::{error}")
        return

    if args.command == "merge-descriptors":
        try:
            payload = merge_batch_descriptors(
                [json.loads(path.read_text(encoding="utf-8")) for path in args.inputs])
        except ValueError as error:
            raise SystemExit(f"::error::{error}")
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return

    if args.command == "describe-ensemble":
        payload = ensemble_descriptor(args.ensemble_root, args.release_tag)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return

    registry = load_registry(args.registry)
    entries = json.loads(args.entries.read_text(encoding="utf-8"))
    if not isinstance(entries, list):
        raise ValueError("--entries debe contener una lista JSON")
    result = make_candidate(registry, entries)
    check_pairs(result, entries, args.evidence_root)
    save_registry(args.output, result)
    print(json.dumps({"status": "PASS", "entries": len(_entries(result)), "output": str(args.output)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
