"""National composition of already-produced provincial candidate assignments.

Version: 1.1.0; date: 2026-10-13; candidate diagnostic interface.
Scope: resumable identity/coverage/quota composition only. It does not run
M01-M06, generate districts, certify topology/population, or authorize output.
Origin: new; no predecessor.
"""
from __future__ import annotations

import hashlib
import gzip
import json
import os
from pathlib import Path
import re
from typing import Mapping, Sequence

SHA256 = re.compile(r"[0-9a-f]{64}\Z")
PROVINCES = tuple(f"{i:02d}" for i in range(1, 53))
SCHEMA = "ddd.congreso-national-composition-checkpoint/1.0"
# Root identities from the reviewed N08 inputs at the base revision. Changing
# any of these requires an explicit update/review of the accreditation bridge.
TRUSTED_CONTRACT_SHA256 = "3dbdbe42f2a7c77dc95140fcf81fb81cb7e847f496c92de971813b3dc1417223"
TRUSTED_SOURCE_MANIFEST_SHA256 = "f99e1690071b6383d90094b35fe024865d5bc75ef95983014452d1d25dbadc37"
TRUSTED_TOPOLOGY_MANIFEST_SHA256 = "3d34d38396f8921a0916568d17919324a6409c37c49c514f3db54743150b176f"


def _canonical(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":"), allow_nan=False).encode("utf-8")


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _is_sha(value: object) -> bool:
    return isinstance(value, str) and SHA256.fullmatch(value) is not None


def _read_trusted_bytes(path: Path, expected_sha256: str, label: str) -> bytes:
    raw = Path(path).read_bytes()
    if _sha(raw) != expected_sha256:
        raise ValueError("TRUSTED_INPUT_SHA256_MISMATCH:" + label)
    return raw


def _validate_topology_unit_quota(code: str, expected_quota: int,
                                  summary: Mapping[str, object]) -> None:
    if summary.get("CPRO") != code:
        raise ValueError("TOPOLOGY_UNIT_PROVINCE_MISMATCH:" + code)
    if summary.get("k") != expected_quota:
        raise ValueError("TOPOLOGY_UNIT_QUOTA_MISMATCH:" + code)


def _atomic_json(path: Path, value: Mapping[str, object]) -> bytes:
    data = (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2,
                       allow_nan=False) + "\n").encode("utf-8")
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    with temporary.open("wb") as stream:
        stream.write(data)
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temporary, path)
    return data


class NationalCandidateComposer:
    """Checkpoint one completed provincial assignment at a time.

    Production scope is created only by ``from_accredited_inputs``, which reads
    and verifies contract, source manifest, protected source bytes, topology
    manifest and all 52 topology artifacts. Synthetic subsets use the explicit
    constructor flag and can never be promoted to production certification.
    The composer binds each unit to its source/topology/input hashes,
    enforces exact CUSEC coverage and quota, and gives local district labels
    deterministic national IDs. The independent candidate certifier remains
    responsible for geometry, contiguity, populations, exceptions and policy.

    A subset is accepted only when explicitly marked synthetic. Complete
    52-unit inputs must carry the approved 52 quotas summing to 407. This class
    never executes an algorithm and always emits generation_authorized=false.
    """

    def __init__(self, checkpoint_dir: Path, *, contract_sha256: str,
                 source_manifest_sha256: str, topology_manifest_sha256: str,
                 quotas: Mapping[str, int],
                 input_universes: Mapping[str, Mapping[str, object]],
                 synthetic_fixture: bool = False):
        if synthetic_fixture is not True:
            raise ValueError("ACCREDITED_INPUTS_REQUIRED")
        self._initialize(
            checkpoint_dir, contract_sha256=contract_sha256,
            source_manifest_sha256=source_manifest_sha256,
            topology_manifest_sha256=topology_manifest_sha256,
            quotas=quotas, input_universes=input_universes,
            synthetic_fixture=True,
        )

    @classmethod
    def from_accredited_inputs(cls, checkpoint_dir: Path, *, contract_path: Path,
                               source_dir: Path, source_parts_dir: Path,
                               topology_product_dir: Path) -> "NationalCandidateComposer":
        """Build from verified 2025 contract/source/topology bytes.

        All external identity values are derived from and checked against files;
        the caller cannot supply replacement quotas or hashes. No districts are
        generated. The resulting composer still emits a non-certified,
        generation-disabled candidate envelope.
        """
        from ddd_core.congreso_contract import validate_congress_identity

        def safe_file(root: Path, relative: str, code: str) -> bytes:
            candidate = (root / relative).resolve(strict=True)
            if not candidate.is_relative_to(root.resolve()):
                raise ValueError(code)
            return candidate.read_bytes()

        contract_bytes = _read_trusted_bytes(contract_path, TRUSTED_CONTRACT_SHA256, "contract")
        contract = json.loads(contract_bytes)
        if not isinstance(contract, dict):
            raise ValueError("CONGRESS_CONTRACT_INVALID")
        validate_congress_identity(contract)
        if contract.get("accreditation", {}).get("generation_authorized") is not False:
            raise ValueError("GENERATION_AUTHORIZATION_MUST_REMAIN_FALSE")
        if contract.get("k_decision", {}).get("total") != 407:
            raise ValueError("NATIONAL_K_MUST_EQUAL_407")
        quotas_rows = contract.get("quotas_by_origin_unit")
        if not isinstance(quotas_rows, list):
            raise ValueError("CONTRACT_QUOTAS_MISSING")
        quotas = {row.get("code"): row.get("k") for row in quotas_rows
                  if isinstance(row, Mapping)}
        if (len(quotas_rows) != 52 or set(quotas) != set(PROVINCES)
                or len(quotas) != 52 or sum(quotas.values()) != 407
                or any(type(value) is not int or value < 1 for value in quotas.values())):
            raise ValueError("CONTRACT_QUOTAS_INVALID")

        source_dir = Path(source_dir)
        source_manifest_bytes = _read_trusted_bytes(
            source_dir / "manifest.json", TRUSTED_SOURCE_MANIFEST_SHA256, "source_manifest")
        source_manifest = json.loads(source_manifest_bytes)
        if not isinstance(source_manifest, dict):
            raise ValueError("SOURCE_MANIFEST_INVALID")
        source_identity = source_manifest.get("manifest_identity_sha256")
        source_identity_body = {k: v for k, v in source_manifest.items()
                                if k != "manifest_identity_sha256"}
        if source_identity != _sha(_canonical(source_identity_body)):
            raise ValueError("SOURCE_MANIFEST_IDENTITY")
        if (source_manifest.get("edition") != 2025
                or source_manifest.get("section_year") != 2025
                or source_manifest.get("population_year") != 2025
                or source_manifest.get("generation_authorized") is not False):
            raise ValueError("SOURCE_MANIFEST_EDITION_OR_AUTHORIZATION")
        source_binding = {}
        for role in ("geometry", "population"):
            expected = contract.get("sources", {}).get(role, {})
            recorded = source_manifest.get("sources", {}).get(role, {})
            if (expected.get("edition") != 2025 or expected.get("year") != 2025
                    or expected.get("sha256") != recorded.get("sha256")):
                raise ValueError("CONTRACT_SOURCE_BINDING:" + role)
            parts = recorded.get("part_sha256")
            if not isinstance(parts, Mapping) or not parts:
                raise ValueError("SOURCE_PART_MANIFEST_MISSING:" + role)
            concatenated = b"".join(safe_file(Path(source_parts_dir), name,
                                                 "SOURCE_PART_PATH:" + role)
                                     for name in sorted(parts))
            for name, expected_part_sha in parts.items():
                part = safe_file(Path(source_parts_dir), name,
                                 "SOURCE_PART_PATH:" + role)
                if _sha(part) != expected_part_sha:
                    raise ValueError("SOURCE_PART_HASH:" + role + ":" + name)
            if (_sha(concatenated) != recorded.get("sha256")
                    or expected.get("sha256") != recorded.get("sha256")):
                raise ValueError("SOURCE_ARCHIVE_HASH:" + role)
            source_binding[role] = {"edition": 2025, "sha256": recorded["sha256"]}
        for relative, record in (
            ("poblacion_por_seccion_2025.csv",
             source_manifest.get("outputs", {}).get("poblacion_por_seccion_2025.csv", {})),
            (source_manifest.get("crosswalk", {}).get("path"),
             source_manifest.get("crosswalk", {})),
        ):
            if not isinstance(relative, str) or not isinstance(record, Mapping):
                raise ValueError("SOURCE_OUTPUT_RECORD_INVALID")
            if _sha(safe_file(source_dir, relative, "SOURCE_OUTPUT_PATH")) != record.get("sha256"):
                raise ValueError("SOURCE_OUTPUT_HASH:" + relative)

        topology_product_dir = Path(topology_product_dir)
        topology_bytes = _read_trusted_bytes(
            topology_product_dir / "manifest.json", TRUSTED_TOPOLOGY_MANIFEST_SHA256,
            "topology_manifest")
        topology = json.loads(topology_bytes)
        if not isinstance(topology, dict):
            raise ValueError("TOPOLOGY_MANIFEST_INVALID")
        topology_identity = topology.get("identity_sha256")
        topology_body = {k: v for k, v in topology.items() if k != "identity_sha256"}
        if topology_identity != _sha(_canonical(topology_body)):
            raise ValueError("TOPOLOGY_MANIFEST_IDENTITY")
        if topology.get("generation_authorized") is not False:
            raise ValueError("TOPOLOGY_GENERATION_AUTHORIZATION")
        evidence = topology.get("evidence", {})
        if (evidence.get("source_binding") != source_binding
                or evidence.get("source_manifest_sha256") != _sha(source_manifest_bytes)):
            raise ValueError("TOPOLOGY_SOURCE_BINDING")
        if (topology.get("sections") != 36554 or topology.get("population") != 49128297
                or topology.get("k") != 407):
            raise ValueError("TOPOLOGY_NATIONAL_COVERAGE")

        units: dict[str, dict[str, object]] = {}
        artifacts = topology.get("artifacts", {})
        total_population = 0
        for code in PROVINCES:
            relative = f"unidades/{code}.json.gz"
            record = artifacts.get(relative)
            if not isinstance(record, Mapping):
                raise ValueError("TOPOLOGY_UNIT_UNPINNED:" + code)
            compressed = safe_file(topology_product_dir, relative, "TOPOLOGY_UNIT_PATH")
            if (_sha(compressed) != record.get("sha256")
                    or len(compressed) != record.get("bytes")):
                raise ValueError("TOPOLOGY_UNIT_HASH:" + code)
            decoded = gzip.decompress(compressed)
            unit = json.loads(decoded)
            if (_sha(decoded) != record.get("canonical_json_sha256")
                    or decoded != _canonical(unit) + b"\n"):
                raise ValueError("TOPOLOGY_UNIT_CANONICAL:" + code)
            nodes = unit.get("nodes", [])
            cusecs = [node.get("id") for node in nodes]
            summary = unit.get("summary", {})
            _validate_topology_unit_quota(code, quotas[code], summary)
            if (summary.get("sections") != len(cusecs)
                    or summary.get("population") != sum(node.get("pop", -1) for node in nodes)
                    or any(not isinstance(c, str) or c[:2] != code for c in cusecs)
                    or len(set(cusecs)) != len(cusecs)):
                raise ValueError("TOPOLOGY_UNIT_IDENTITY:" + code)
            total_population += sum(node.get("pop", -1) for node in nodes)
            units[code] = {"cusecs": cusecs, "input_sha256": _sha(compressed)}
        if sum(len(unit["cusecs"]) for unit in units.values()) != 36554:
            raise ValueError("TOPOLOGY_CUSEC_COVERAGE")
        if total_population != 49128297:
            raise ValueError("TOPOLOGY_NATIONAL_POPULATION")

        instance = cls.__new__(cls)
        instance._initialize(
            checkpoint_dir, contract_sha256=_sha(contract_bytes),
            source_manifest_sha256=_sha(source_manifest_bytes),
            topology_manifest_sha256=_sha(topology_bytes),
            quotas=quotas, input_universes=units, synthetic_fixture=False,
        )
        return instance

    def _initialize(self, checkpoint_dir: Path, *, contract_sha256: str,
                    source_manifest_sha256: str, topology_manifest_sha256: str,
                    quotas: Mapping[str, int],
                    input_universes: Mapping[str, Mapping[str, object]],
                    synthetic_fixture: bool) -> None:
        for name, digest in (("contract", contract_sha256),
                             ("source_manifest", source_manifest_sha256),
                             ("topology_manifest", topology_manifest_sha256)):
            if not _is_sha(digest):
                raise ValueError("COMPOSITION_HASH_INVALID:" + name)
        if type(synthetic_fixture) is not bool:
            raise ValueError("SYNTHETIC_FIXTURE_FLAG_INVALID")
        if not quotas or set(quotas) != set(input_universes):
            raise ValueError("PROVINCE_QUOTA_UNIVERSE_MISMATCH")
        if any(code not in PROVINCES for code in quotas):
            raise ValueError("PROVINCE_CODE_INVALID")
        if any(type(value) is not int or value < 1 for value in quotas.values()):
            raise ValueError("PROVINCE_QUOTA_INVALID")
        if set(quotas) != set(PROVINCES):
            if not synthetic_fixture:
                raise ValueError("NATIONAL_52_UNITS_REQUIRED")
        elif sum(quotas.values()) != 407:
            raise ValueError("NATIONAL_K_MUST_EQUAL_407")

        units: dict[str, dict[str, object]] = {}
        for code in sorted(input_universes):
            raw = input_universes[code]
            cusecs = raw.get("cusecs")
            input_sha = raw.get("input_sha256")
            if not isinstance(cusecs, Sequence) or isinstance(cusecs, (str, bytes)):
                raise ValueError("INPUT_CUSECS_INVALID:" + code)
            ordered = tuple(sorted(cusecs))
            if (not ordered or any(not isinstance(c, str) or len(c) != 10 or not c.isdecimal()
                                   or c[:2] != code for c in ordered)
                    or len(set(ordered)) != len(ordered)):
                raise ValueError("INPUT_CUSECS_IDENTITY:" + code)
            if not _is_sha(input_sha):
                raise ValueError("INPUT_HASH_INVALID:" + code)
            units[code] = {"cusecs": ordered, "input_sha256": input_sha,
                           "quota": quotas[code],
                           "universe_sha256": _sha(_canonical(ordered))}
        if not synthetic_fixture and sum(len(unit["cusecs"]) for unit in units.values()) != 36554:
            raise ValueError("NATIONAL_CUSEC_COVERAGE_MUST_EQUAL_36554")

        self.root = Path(checkpoint_dir)
        self.root.mkdir(parents=True, exist_ok=True)
        self.identity = {
            "schema": SCHEMA,
            "contract_sha256": contract_sha256,
            "source_manifest_sha256": source_manifest_sha256,
            "topology_manifest_sha256": topology_manifest_sha256,
            "units": units,
            "synthetic_fixture": synthetic_fixture,
            "generation_authorized": False,
        }
        self.identity_sha256 = _sha(_canonical(self.identity))
        self._load_checkpoint()

    def _load_checkpoint(self) -> None:
        path = self.root / "CHECKPOINT.json"
        if not path.exists():
            self.records: dict[str, dict[str, object]] = {}
            self._save_checkpoint()
            return
        checkpoint = json.loads(path.read_bytes())
        digest = checkpoint.get("checkpoint_sha256")
        body = {k: v for k, v in checkpoint.items() if k != "checkpoint_sha256"}
        if digest != _sha(_canonical(body)):
            raise ValueError("COMPOSITION_CHECKPOINT_HASH")
        if checkpoint.get("identity_sha256") != self.identity_sha256:
            raise ValueError("COMPOSITION_CHECKPOINT_IDENTITY_CHANGED")
        if checkpoint.get("generation_authorized") is not False:
            raise ValueError("COMPOSITION_CHECKPOINT_PRODUCTION_GUARD")
        records = checkpoint.get("records")
        if not isinstance(records, dict):
            raise ValueError("COMPOSITION_CHECKPOINT_RECORDS")
        self.records = records
        for code, record in self.records.items():
            if code not in self.identity["units"]:
                raise ValueError("COMPOSITION_CHECKPOINT_UNIT_UNKNOWN:" + str(code))
            self._read_unit_artifact(code)

    def _read_unit_artifact(self, code: str) -> dict[str, object]:
        record = self.records.get(code)
        if not isinstance(record, Mapping):
            raise ValueError("COMPOSITION_CHECKPOINT_RECORD_MISSING:" + code)
        data = (self.root / f"{code}.json").read_bytes()
        if _sha(data) != record.get("artifact_sha256"):
            raise ValueError("COMPOSITION_ARTIFACT_HASH:" + code)
        payload = json.loads(data)
        expected = self.identity["units"][code]
        if (payload.get("schema") != SCHEMA or payload.get("province") != code
                or payload.get("identity_sha256") != self.identity_sha256
                or payload.get("input_sha256") != expected["input_sha256"]
                or payload.get("universe_sha256") != expected["universe_sha256"]):
            raise ValueError("COMPOSITION_ARTIFACT_IDENTITY:" + code)
        if (payload.get("generation_authorized") is not False
                or payload.get("certification_status") != "NOT_PERFORMED"):
            raise ValueError("COMPOSITION_ARTIFACT_PRODUCTION_GUARD:" + code)
        rows = payload.get("assignments")
        if not isinstance(rows, list):
            raise ValueError("COMPOSITION_ASSIGNMENTS_INVALID:" + code)
        cusecs, labels = [], set()
        for row in rows:
            if (not isinstance(row, Mapping) or set(row) != {"cusec", "district_id"}
                    or not isinstance(row["cusec"], str)
                    or not isinstance(row["district_id"], str)):
                raise ValueError("COMPOSITION_ASSIGNMENT_ROW_INVALID:" + code)
            cusec, district = row["cusec"], row["district_id"]
            if (cusec[:2] != code or district[:len(f"DDD-{code}-")] != f"DDD-{code}-"
                    or not district[len(f"DDD-{code}-"):].isdecimal()):
                raise ValueError("COMPOSITION_ASSIGNMENT_IDENTITY:" + code)
            cusecs.append(cusec)
            labels.add(district)
        expected_labels = {f"DDD-{code}-{index:03d}"
                           for index in range(1, expected["quota"] + 1)}
        if (cusecs != list(expected["cusecs"]) or len(set(cusecs)) != len(cusecs)
                or labels != expected_labels
                or payload.get("district_count") != expected["quota"]
                or record.get("district_count") != expected["quota"]
                or record.get("cusecs") != len(expected["cusecs"])):
            raise ValueError("COMPOSITION_ASSIGNMENT_COVERAGE_OR_QUOTA:" + code)
        return payload

    def _save_checkpoint(self) -> None:
        body = {"schema": SCHEMA, "identity_sha256": self.identity_sha256,
                "records": self.records, "generation_authorized": False}
        body["checkpoint_sha256"] = _sha(_canonical(body))
        _atomic_json(self.root / "CHECKPOINT.json", body)

    def record_province(self, code: str, assignments: Sequence[Mapping[str, str]]) -> dict[str, object]:
        if code not in self.identity["units"]:
            raise ValueError("COMPOSITION_PROVINCE_NOT_EXPECTED:" + str(code))
        expected = self.identity["units"][code]
        cusecs = expected["cusecs"]
        if not isinstance(assignments, Sequence) or isinstance(assignments, (str, bytes)):
            raise ValueError("PROVINCIAL_ASSIGNMENTS_INVALID")
        normalized: dict[str, str] = {}
        for row in assignments:
            if not isinstance(row, Mapping) or set(row) != {"cusec", "district_id"}:
                raise ValueError("PROVINCIAL_ASSIGNMENT_ROW_INVALID")
            cusec, district = row["cusec"], row["district_id"]
            if (not isinstance(cusec, str) or cusec in normalized
                    or not isinstance(district, str) or not district.strip()):
                raise ValueError("PROVINCIAL_ASSIGNMENT_VALUE_INVALID")
            normalized[cusec] = district.strip()
        if set(normalized) != set(cusecs):
            raise ValueError("PROVINCIAL_CUSEC_COVERAGE_MISMATCH")
        labels = sorted(set(normalized.values()))
        if len(labels) != expected["quota"]:
            raise ValueError("PROVINCIAL_QUOTA_MISMATCH")
        local_to_global = {label: f"DDD-{code}-{index:03d}"
                           for index, label in enumerate(labels, start=1)}
        rows = [{"cusec": cusec, "district_id": local_to_global[normalized[cusec]]}
                for cusec in cusecs]
        payload = {"schema": SCHEMA, "province": code,
                   "input_sha256": expected["input_sha256"],
                   "universe_sha256": expected["universe_sha256"],
                   "identity_sha256": self.identity_sha256,
                   "assignments": rows, "district_count": len(labels),
                   "generation_authorized": False,
                   "certification_status": "NOT_PERFORMED"}
        artifact_path = self.root / f"{code}.json"
        encoded = (json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2,
                               allow_nan=False) + "\n").encode("utf-8")
        data = encoded
        record = {"artifact_sha256": _sha(data), "district_count": len(labels),
                  "cusecs": len(rows)}
        prior = self.records.get(code)
        if prior is not None and prior != record:
            raise ValueError("PROVINCIAL_CHECKPOINT_RESULT_CHANGED:" + code)
        if prior is None:
            _atomic_json(artifact_path, payload)
        elif _sha(artifact_path.read_bytes()) != record["artifact_sha256"]:
            raise ValueError("COMPOSITION_CHECKPOINT_ARTIFACT_HASH:" + code)
        self.records[code] = record
        self._save_checkpoint()
        return record

    def compose(self) -> dict[str, object]:
        expected_codes = set(self.identity["units"])
        if set(self.records) != expected_codes:
            missing = sorted(expected_codes - set(self.records))
            raise ValueError("COMPOSITION_UNITS_INCOMPLETE:" + ",".join(missing))
        assignments = []
        for code in sorted(expected_codes):
            payload = self._read_unit_artifact(code)
            expected = self.identity["units"][code]
            if (payload.get("input_sha256") != expected["input_sha256"]
                    or payload.get("universe_sha256") != expected["universe_sha256"]
                    or payload.get("district_count") != expected["quota"]):
                raise ValueError("COMPOSITION_PROVINCE_IDENTITY:" + code)
            assignments.extend(payload["assignments"])
        if len({row["cusec"] for row in assignments}) != len(assignments):
            raise ValueError("COMPOSITION_DUPLICATE_CUSEC")
        candidate = {"schema": "ddd.congreso-national-candidate/1.0",
                     "identity_sha256": self.identity_sha256,
                     "province_count": len(expected_codes),
                     "cusec_count": len(assignments),
                     "district_count": sum(self.identity["units"][p]["quota"]
                                           for p in expected_codes),
                     "assignments": assignments,
                     "generation_authorized": False,
                     "certification_status": "NOT_PERFORMED",
                     "diagnostic_only": True}
        candidate["candidate_sha256"] = _sha(_canonical(candidate))
        return candidate
