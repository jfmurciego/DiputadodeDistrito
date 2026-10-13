import gzip
import hashlib
import json
from pathlib import Path

from ddd_core.congreso_constructive_witness import evaluate_unit


def _write_json(path: Path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")


def _sha(path: Path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _fixture(tmp_path, *, boundary="ACCREDITED", edge_kind="linear", k=1, part_components=1):
    cpro = "52"
    geometry_sha = "a" * 64
    population_sha = "b" * 64
    contract = {
        "sources": {
            "geometry": {"sha256": geometry_sha, "accreditation": "ACCREDITED", "edition": 2025},
            "population": {"sha256": population_sha, "accreditation": "ACCREDITED", "edition": 2025},
        },
        "decisions": {
            "minimum_unit": {"status": "APPROVED", "decision_id": "N08-OWNER-20261013-7RULES",
                             "value": "official_2025_CUSEC_indivisible"},
            "contiguity": {"status": "APPROVED", "decision_id": "N08-OWNER-20261013-7RULES",
                            "value": "positive_line_shared_boundary_on_original_polygon_parts"},
            "municipal_indivisibility": {"status": "APPROVED", "decision_id": "N08-OWNER-20261013-7RULES",
                                          "value": "preserve_when_feasible_split_by_whole_CUSEC_when_necessary"},
            "population_limits": {
                "status": "APPROVED", "decision_id": "N08-OWNER-20261013-7RULES",
                "value": {"population_floor_ratio": 0.85, "population_cap_ratio": 1.15,
                          "target_tolerance_ratio": 0.15},
            },
        },
        "k_decision": {"status": "APPROVED_BY_OWNER", "total": 407,
                       "quota_method": "max(1,(P_i+60000)//120000); nearest_half_up_independent; reference_2025"},
        "quotas_by_origin_unit": [
            {"code": f"{number:02d}", "k": (k if number == 52 else
             7 if number == 49 and k == 2 else (8 if number <= 49 else 7))}
            for number in range(1, 53)
        ],
        "accreditation": {"generation_authorized": False},
    }
    # 49*8 + 2*7 + 1 = 407.
    contract_path = tmp_path / "contract.json"
    _write_json(contract_path, contract)
    unit = {
        "run_binding": "fixture-run",
        "summary": {
            "CPRO": cpro, "sections": 3, "population": 300, "edges": 2,
            "k": k, "polygon_parts": 3, "physical_part_components": part_components,
            "section_graph_components": 1, "external_gap_accreditation": boundary,
            "discontinuous_municipalities": [],
            "multipart_sections_spanning_physical_components": [],
            "isolated_sections": [],
        },
        "nodes": [
            {"CUSEC": f"52{i:08d}", "id": f"52{i:08d}", "CPRO": cpro,
             "POB_2025": 100, "source_geometry_sha256": geometry_sha,
             "physical_part_components": ["5200000001:p0000" if part_components == 1 or i < 3 else "5200000003:p0000"]}
            for i in range(1, 4)
        ],
        "edges": [
            {"u": "5200000001", "v": "5200000002", "edge_type": "geometric",
             "kind": edge_kind, "shared_border_m": 1.0, "overlap_m2": 0.0,
             "contact_sha256": hashlib.sha256(b"edge-1").hexdigest()},
            {"u": "5200000002", "v": "5200000003", "edge_type": "geometric",
             "kind": edge_kind, "shared_border_m": 1.0, "overlap_m2": 0.0,
             "contact_sha256": hashlib.sha256(b"edge-2").hexdigest()},
        ],
        "polygon_part_components": ([{"id": "5200000001:p0000", "parts": [
            "5200000001:p0000", "5200000002:p0000", "5200000003:p0000",
        ]}] if part_components == 1 else [
            {"id": "5200000001:p0000", "parts": ["5200000001:p0000", "5200000002:p0000"]},
            {"id": "5200000003:p0000", "parts": ["5200000003:p0000"]},
        ]),
    }
    product_root = tmp_path / "product"
    unit_path = product_root / "unidades" / "52.json.gz"
    unit_path.parent.mkdir(parents=True)
    payload = json.dumps(unit, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    with unit_path.open("wb") as raw:
        with gzip.GzipFile(fileobj=raw, mode="wb", mtime=0) as stream:
            stream.write(payload)
    manifest = {
        "run_binding": "fixture-run", "schema": "ddd.congress-topology-diagnostic/1.0",
        "generation_authorized": False,
        "evidence": {"contract_sha256": _sha(contract_path),
                     "source_binding": {"geometry": {"edition": 2025, "sha256": geometry_sha},
                                        "population": {"edition": 2025, "sha256": population_sha}}},
        "artifacts": {"unidades/52.json.gz": {
            "sha256": _sha(unit_path),
            "canonical_json_sha256": hashlib.sha256(json.dumps(
                unit, ensure_ascii=False, sort_keys=True, separators=(",", ":")
            ).encode("utf-8") + b"\n").hexdigest(),
        }},
    }
    manifest["identity_sha256"] = hashlib.sha256((json.dumps(
        manifest, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ) + "\n").encode("utf-8")).hexdigest()
    manifest_path = product_root / "manifest.json"
    _write_json(manifest_path, manifest)
    preflight_path = tmp_path / "preflight" / "PREFLIGHT.json"
    checkpoint_path = tmp_path / "preflight" / "CHECKPOINT.json"
    tool_sha = "d" * 64
    preflight = {
        "province": cpro, "tool_sha256": tool_sha, "version": "1.2.0",
        "source_evidence": {
            "contract_sha256": _sha(contract_path),
            "geometry_operations": "none; no CRS transform, buffer, simplify, repair or precision rounding in physical graph",
        },
        "source_binding": {
            "geometry": {"edition": 2025, "sha256": geometry_sha},
            "population": {"edition": 2025, "sha256": population_sha},
        },
        "topology_manifest_identity_sha256": manifest["identity_sha256"],
        "topology_unit_sha256": _sha(unit_path),
        "modules": {name: {"status": "PASS"} for name in ("M01", "M02", "M03")},
        "generation_authorized": False, "districts_generated": 0,
        "inputs": {"sections": 3, "population": 300, "k_approved": k,
                   "physical_edges": 2},
    }
    _write_json(preflight_path, preflight)
    _write_json(checkpoint_path, {
        "version": "1.2.0", "source_binding": preflight["source_binding"],
        "generation_authorized": False, "districts_generated": 0,
        "province": cpro, "preflight_sha256": _sha(preflight_path),
        "topology_unit_sha256": _sha(unit_path),
        "topology_manifest_identity_sha256": manifest["identity_sha256"],
        "tool_sha256": tool_sha,
    })
    return preflight_path, checkpoint_path, unit_path, manifest_path, contract_path


def _evaluate(tmp_path, **fixture_options):
    paths = _fixture(tmp_path, **fixture_options)
    return evaluate_unit(
        preflight_path=paths[0], checkpoint_path=paths[1], unit_path=paths[2],
        product_manifest_path=paths[3], contract_path=paths[4],
    )


def test_connected_k1_returns_conditional_cusec_atomic_witness_and_keeps_gates_closed(tmp_path):
    result = _evaluate(tmp_path)
    assert result["diagnostic_status"] == "WITNESS_FOUND_CONDITIONAL"
    assert result["territorial_factibility_status"] == "CONDITIONAL_WITNESS_ONLY"
    assert result["assignment"] == [
        {"CUSEC": "5200000001", "district_id": "01"},
        {"CUSEC": "5200000002", "district_id": "01"},
        {"CUSEC": "5200000003", "district_id": "01"},
    ]
    assert result["floor"] <= result["population"] <= result["cap"]
    assert result["generation_authorized"] is False
    assert result["districts_generated"] == 0
    assert result["product_certification"] == "NOT_PERFORMED"


def test_external_boundary_uncertainty_keeps_factibility_insufficient_but_witness_conditional(tmp_path):
    result = _evaluate(tmp_path, boundary="NOT_EVIDENCED_NO_INDEPENDENT_BOUNDARY")
    assert result["diagnostic_status"] == "WITNESS_FOUND_CONDITIONAL"
    assert result["territorial_factibility_status"] == "INSUFFICIENT_EVIDENCE"


def test_point_only_contact_cannot_support_witness(tmp_path):
    result = _evaluate(tmp_path, edge_kind="point")
    assert result["diagnostic_status"] == "INSUFFICIENT_EVIDENCE"
    assert "EDGE_NOT_VALID_POSITIVE_LINEAR_CONTACT" in result["errors"]
    assert result["assignment"] == []


def test_k_greater_than_one_is_search_not_run_and_over_component_bound_is_only_conditional(tmp_path):
    result = _evaluate(tmp_path, k=2)
    assert result["diagnostic_status"] == "SEARCH_NOT_RUN"
    assert result["assignment"] == []


def test_component_bound_is_conditional_necessary_failure_not_impossibility(tmp_path):
    result = _evaluate(tmp_path, k=1, part_components=2)
    assert result["diagnostic_status"] == "NECESSARY_CONDITION_FAILED_CONDITIONAL"
    assert result["condition"] == "PHYSICAL_PART_COMPONENTS_EXCEED_K_IN_SOURCE_PRODUCT"
    assert "impossible" not in result["diagnostic_status"].lower()


def test_preflight_checkpoint_hash_mismatch_rejects_witness(tmp_path):
    paths = _fixture(tmp_path)
    checkpoint = json.loads(paths[1].read_text(encoding="utf-8"))
    checkpoint["preflight_sha256"] = "0" * 64
    _write_json(paths[1], checkpoint)
    result = evaluate_unit(
        preflight_path=paths[0], checkpoint_path=paths[1], unit_path=paths[2],
        product_manifest_path=paths[3], contract_path=paths[4],
    )
    assert result["diagnostic_status"] == "INSUFFICIENT_EVIDENCE"
    assert "PREFLIGHT_CHECKPOINT_HASH_MISMATCH" in result["errors"]
    assert result["assignment"] == []


def test_checkpoint_generation_mutations_reject_witness(tmp_path):
    paths = _fixture(tmp_path)
    checkpoint = json.loads(paths[1].read_text(encoding="utf-8"))
    checkpoint.update({"generation_authorized": True, "districts_generated": 1,
                       "version": "0.0.0",
                       "source_binding": {"geometry": {"sha256": "f" * 64}}})
    _write_json(paths[1], checkpoint)
    result = evaluate_unit(
        preflight_path=paths[0], checkpoint_path=paths[1], unit_path=paths[2],
        product_manifest_path=paths[3], contract_path=paths[4],
    )
    assert result["diagnostic_status"] == "INSUFFICIENT_EVIDENCE"
    assert {"PREFLIGHT_CHECKPOINT_VERSION_MISMATCH", "CHECKPOINT_SOURCE_BINDING_MISMATCH",
            "CHECKPOINT_GENERATION_GATE_NOT_CLOSED", "CHECKPOINT_DISTRICT_COUNT_INVALID"} <= set(result["errors"])
    assert result["assignment"] == []


def test_topology_manifest_identity_or_source_binding_mutation_rejects_witness(tmp_path):
    paths = _fixture(tmp_path)
    manifest = json.loads(paths[3].read_text(encoding="utf-8"))
    manifest["evidence"]["source_binding"]["geometry"]["sha256"] = "f" * 64
    # Deliberately keep the previous identity so both the integrity digest and
    # the contract/preflight source binding are independently exercised.
    _write_json(paths[3], manifest)
    result = evaluate_unit(
        preflight_path=paths[0], checkpoint_path=paths[1], unit_path=paths[2],
        product_manifest_path=paths[3], contract_path=paths[4],
    )
    assert result["diagnostic_status"] == "INSUFFICIENT_EVIDENCE"
    assert "TOPOLOGY_MANIFEST_CANONICAL_IDENTITY_INVALID" in result["errors"]
    assert "TOPOLOGY_MANIFEST_GEOMETRY_BINDING_MISMATCH" in result["errors"]
    assert result["assignment"] == []
