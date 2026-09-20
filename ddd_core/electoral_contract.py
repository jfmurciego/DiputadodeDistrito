"""
PROYECTO: Diputado de Distrito
COMPONENTE: Contrato electoral común
VERSIÓN: 1.0.0
NOMBRE DE VERSIÓN: Entrada electoral verificable
FECHA: 2026-09-14
QUÉ HACE: valida convocatoria, fuentes, adaptadores y diccionario de partidos de M07.
ESTADO: vigente — R039
CAMBIOS: componente nuevo independiente de cualquier territorio.
MOTIVO: impedir entradas electorales artesanales, no trazadas o normalizadas en código.
ANTERIOR: ninguno — componente nuevo.
"""
from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from pathlib import Path
from typing import Any, Mapping


SCHEMA_FAMILY = "ddd-election"
SCHEMA_VERSION = "1.0.0"
SUPPORTED_ADAPTERS = {"long_csv", "nested_json", "wide_polling_station_csv"}


def _required(mapping: Mapping[str, Any], key: str, context: str) -> Any:
    value = mapping.get(key)
    if value is None or value == "" or value == []:
        raise ValueError(f"{context}: falta {key}")
    return value


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def party_key(value: Any) -> str:
    """Clave Unicode estable para resolver alias; no inventa equivalencias."""
    text = unicodedata.normalize("NFKC", str(value or ""))
    return re.sub(r"\s+", " ", text.strip()).casefold()


class PartyDictionary:
    def __init__(self, data: Mapping[str, Any]):
        if data.get("schema_family") != "ddd-party-dictionary":
            raise ValueError("diccionario: schema_family debe ser ddd-party-dictionary")
        if data.get("schema_version") != SCHEMA_VERSION:
            raise ValueError(f"diccionario: schema_version debe ser {SCHEMA_VERSION}")
        if data.get("unknown_party_policy") != "reject":
            raise ValueError("diccionario: unknown_party_policy debe ser reject")
        self._aliases: dict[str, str] = {}
        self._classification: dict[str, str] = {}
        parties = _required(data, "parties", "diccionario")
        if not isinstance(parties, list):
            raise ValueError("diccionario.parties debe ser una lista")
        for item in parties:
            if not isinstance(item, Mapping):
                raise ValueError("diccionario.parties contiene una entrada inválida")
            canonical = str(_required(item, "canonical_id", "partido")).strip()
            aliases = [canonical, str(_required(item, "display_name", canonical))]
            aliases.extend(str(alias) for alias in item.get("aliases", []))
            for alias in aliases:
                key = party_key(alias)
                if not key:
                    raise ValueError(f"partido {canonical}: alias vacío")
                owner = self._aliases.get(key)
                if owner is not None and owner != canonical:
                    raise ValueError(
                        f"diccionario: alias ambiguo {alias!r} para {owner} y {canonical}"
                    )
                self._aliases[key] = canonical
            self._classification[canonical] = str(item.get("classification", ""))

    def canonicalize(self, value: Any) -> str:
        raw = re.sub(r"\s+", " ", unicodedata.normalize("NFKC", str(value or "")).strip())
        canonical = self._aliases.get(party_key(raw))
        if canonical is None:
            raise ValueError(f"partido no declarado en el diccionario: {raw!r}")
        return canonical

    def classification(self, canonical_id: str) -> str:
        return self._classification.get(canonical_id, "")


def _load_json(path: Path, context: str) -> dict[str, Any]:
    if not path.is_file():
        raise FileNotFoundError(f"{context} no encontrado: {path}")
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{context} debe contener un objeto JSON")
    return data


def _resolve(project_root: Path, raw_path: Any) -> Path:
    path = Path(str(raw_path)).expanduser()
    return path.resolve() if path.is_absolute() else (project_root / path).resolve()


def _verify_file(record: Mapping[str, Any], project_root: Path, context: str) -> Path:
    path = _resolve(project_root, _required(record, "path", context))
    expected = str(_required(record, "sha256", context)).lower()
    if not re.fullmatch(r"[0-9a-f]{64}", expected):
        raise ValueError(f"{context}: sha256 inválido")
    if not path.is_file():
        raise FileNotFoundError(f"{context} no encontrado: {path}")
    actual = sha256_file(path)
    if actual != expected:
        raise ValueError(f"{context}: checksum incorrecto {actual} != {expected}")
    return path


def load_election_contract(
    contract_path: str | Path,
    *,
    project_root: str | Path,
    expected_territory_id: str | None = None,
) -> tuple[dict[str, Any], PartyDictionary]:
    """Carga y verifica todo lo necesario antes de leer un solo voto."""
    root = Path(project_root).resolve()
    path = Path(contract_path).resolve()
    contract = _load_json(path, "contrato electoral")
    if contract.get("schema_family") != SCHEMA_FAMILY:
        raise ValueError(f"contrato: schema_family debe ser {SCHEMA_FAMILY}")
    if contract.get("schema_version") != SCHEMA_VERSION:
        raise ValueError(f"contrato: schema_version debe ser {SCHEMA_VERSION}")
    for key in ("election_id", "territory_id", "title", "election_date"):
        _required(contract, key, "contrato")
    if expected_territory_id and contract["territory_id"] != expected_territory_id:
        raise ValueError(
            "contrato electoral de otro territorio: "
            f"{contract['territory_id']} != {expected_territory_id}"
        )
    if contract.get("input_mode") != "verifiable_file":
        raise ValueError("contrato: input_mode debe ser verifiable_file")
    if contract.get("boundary_independence") is not True:
        raise ValueError("contrato: boundary_independence debe ser true")

    sources = _required(contract, "sources", "contrato")
    if not isinstance(sources, list):
        raise ValueError("contrato.sources debe ser una lista")
    resolved_sources = []
    for index, source in enumerate(sources):
        context = f"contrato.sources[{index}]"
        if not isinstance(source, Mapping):
            raise ValueError(f"{context}: entrada inválida")
        for key in ("publisher", "source_url", "retrieved_at"):
            _required(source, key, context)
        adapter = _required(source, "adapter", context)
        if not isinstance(adapter, Mapping) or adapter.get("kind") not in SUPPORTED_ADAPTERS:
            raise ValueError(f"{context}: adaptador no soportado")
        resolved = dict(source)
        resolved["resolved_path"] = str(_verify_file(source, root, context))
        resolved_sources.append(resolved)
    contract["sources"] = resolved_sources

    dictionary_record = _required(contract, "party_dictionary", "contrato")
    if not isinstance(dictionary_record, Mapping):
        raise ValueError("contrato.party_dictionary debe ser un objeto")
    dictionary_path = _verify_file(dictionary_record, root, "diccionario")
    dictionary = PartyDictionary(_load_json(dictionary_path, "diccionario"))
    contract["party_dictionary"] = {
        **dictionary_record,
        "resolved_path": str(dictionary_path),
    }
    reconciliation = _required(contract, "reconciliation", "contrato")
    if not isinstance(reconciliation, Mapping):
        raise ValueError("contrato.reconciliation debe ser un objeto")
    return contract, dictionary
