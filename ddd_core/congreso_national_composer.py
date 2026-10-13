"""National composition of already-produced provincial candidate assignments.

Version: 1.0.0; date: 2026-10-13; candidate diagnostic interface.
Scope: resumable identity/coverage/quota composition only. It does not run
M01-M06, generate districts, certify topology/population, or authorize output.
Origin: new; no predecessor.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re
from typing import Mapping, Sequence

SHA256 = re.compile(r"[0-9a-f]{64}\Z")
PROVINCES = tuple(f"{i:02d}" for i in range(1, 53))
SCHEMA = "ddd.congreso-national-composition-checkpoint/1.0"


def _canonical(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":"), allow_nan=False).encode("utf-8")


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _is_sha(value: object) -> bool:
    return isinstance(value, str) and SHA256.fullmatch(value) is not None


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

    ``input_universes`` must be supplied by an upstream hash-verifying reader.
    The composer binds each unit to its declared source/topology/input hashes,
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
            artifact = self.root / f"{code}.json"
            data = artifact.read_bytes()
            if _sha(data) != record.get("artifact_sha256"):
                raise ValueError("COMPOSITION_CHECKPOINT_ARTIFACT_HASH:" + code)
            payload = json.loads(data)
            if payload.get("identity_sha256") != self.identity_sha256:
                raise ValueError("COMPOSITION_CHECKPOINT_ARTIFACT_IDENTITY:" + code)

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
            payload = json.loads((self.root / f"{code}.json").read_bytes())
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
