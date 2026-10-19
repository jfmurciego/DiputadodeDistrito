"""Version 0.1.0; pruebas del certificador independiente Congreso; 2026-10-13.

Scope: synthetic fixtures only; no real partition or production run.
Origin: new, no predecessor.
"""
from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from ddd_core.congreso_candidate_certifier import (
    _require_product_gates,
    _trusted_evidence,
    _verify_against_trusted,
    certify_candidate,
)


ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "territorios/congreso/contrato_congreso_2026.json"


def _fixture(*, populations=None):
    contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
    sources = contract["sources"]
    source_binding = {
        role: {"edition": sources[role]["edition"], "sha256": sources[role]["sha256"]}
        for role in ("geometry", "population")
    }
    # Six whole CUSECs form a chain. Population totals 360,000 for CPRO 10,
    # whose approved K=3 therefore remains internally consistent.
    municipalities = ["10002", "10001", "10001", "10003", "10004", "10005"]
    values = populations or [60000] * 6
    nodes = []
    for index, (municipality, population) in enumerate(zip(municipalities, values)):
        ident = f"{municipality}{index + 1:05d}"
        nodes.append({
            "id": ident,
            "CPRO": "10",
            "CUMUN": municipality,
            "pop": population,
            "geometry_sha256": f"{index + 1:064x}",
            "source_geometry_sha256": sources["geometry"]["sha256"],
            "physical_parts": [{
                "id": f"{ident}:p0000",
                "geometry_sha256": f"{index + 11:064x}",
                "physical_component": "10-component-1",
            }],
        })
    edges = [{
        "u": nodes[index]["id"], "v": nodes[index + 1]["id"],
        "shared_border_m": 12.5, "overlap_m2": 0.0,
        "edge_type": "geometric", "contact_sha256": f"{index + 21:064x}",
    } for index in range(len(nodes) - 1)]
    # A connected 80/80/80 fixture: group 10001 is split across the first
    # and second district at the selected boundary, requiring independent proof.
    labels = ["D1", "D1", "D2", "D2", "D3", "D3"]
    assignments = [{"CUSEC": node["id"], "district_id": labels[index],
                    "population": node["pop"]}
                   for index, node in enumerate(nodes)]
    return contract, nodes, edges, assignments, source_binding


class CongressCandidateCertifierTests(unittest.TestCase):
    def test_valid_synthetic_candidate_is_diagnostic_only(self):
        contract, nodes, edges, assignments, binding = _fixture()
        result = certify_candidate(contract, nodes, edges, assignments, binding,
                                   synthetic_fixture=True)
        self.assertEqual(result["status"], "SYNTHETIC_DIAGNOSTIC_PASS")
        self.assertFalse(result["generation_authorized"])
        self.assertEqual(result["population_bounds"]["10"],
                         {"floor": 102000, "cap": 138000, "quota": 3})
        split = next(row for row in result["municipality_splits"] if row["CUMUN"] == "10001")
        self.assertTrue(split["proof"]["proven"])
        self.assertEqual(split["proof"]["scope"], "OTHER_CUSECS_FIXED")

    def test_synthetic_fixture_cannot_be_declared_product_certified(self):
        contract, nodes, edges, assignments, binding = _fixture()
        result = certify_candidate(contract, nodes, edges, assignments, binding,
                                   synthetic_fixture=False)
        self.assertEqual(result["status"], "NOT_CERTIFIABLE")
        self.assertIn("NATIONAL_PRODUCT_COVERAGE_REQUIRED_OR_MARK_FIXTURE_SYNTHETIC",
                      result["blockers"])
        self.assertFalse(result["generation_authorized"])

        fake_manifest = {"schema": "ddd.congreso-candidate-product/1.0",
                         "synthetic_fixture": False, "generation_authorized": False}
        result = certify_candidate(contract, nodes, edges, assignments, binding,
                                   synthetic_fixture=True, product_manifest=fake_manifest)
        self.assertEqual(result["status"], "NOT_CERTIFIABLE")
        self.assertIn("SYNTHETIC_FIXTURE_CANNOT_BIND_PRODUCT_MANIFEST", result["blockers"])

    def test_cusec_duplicate_and_administrative_mismatch_rejected(self):
        contract, nodes, edges, assignments, binding = _fixture()
        duplicated = copy.deepcopy(nodes)
        duplicated[1]["id"] = duplicated[0]["id"]
        result = certify_candidate(contract, duplicated, edges, assignments, binding,
                                   synthetic_fixture=True)
        self.assertIn("CUSEC_DUPLICATE", result["blockers"])

        contract, nodes, edges, assignments, binding = _fixture()
        nodes[0]["CUMUN"] = "10099"
        result = certify_candidate(contract, nodes, edges, assignments, binding,
                                   synthetic_fixture=True)
        self.assertIn("CUSEC_CPRO_CUMUN_IDENTITY_MISMATCH", result["blockers"])

    def test_district_disconnection_rejected(self):
        contract, nodes, edges, assignments, binding = _fixture()
        assignments[1]["district_id"] = "D2"
        assignments[2]["district_id"] = "D1"
        result = certify_candidate(contract, nodes, edges, assignments, binding,
                                   synthetic_fixture=True)
        self.assertIn("DISTRICT_NOT_PHYSICALLY_CONNECTED", result["blockers"])

    def test_assignment_population_and_linear_contact_evidence_are_required(self):
        contract, nodes, edges, assignments, binding = _fixture()
        assignments[0]["population"] += 1
        result = certify_candidate(contract, nodes, edges, assignments, binding,
                                   synthetic_fixture=True)
        self.assertIn("ASSIGNMENT_POPULATION_MISMATCH", result["blockers"])

        contract, nodes, edges, assignments, binding = _fixture()
        edges[0]["shared_border_m"] = 0
        result = certify_candidate(contract, nodes, edges, assignments, binding,
                                   synthetic_fixture=True)
        self.assertIn("EDGE_NOT_POSITIVE_LINEAR_BOUNDARY", result["blockers"])

        contract, nodes, edges, assignments, binding = _fixture()
        edges[0]["overlap_m2"] = 0.01
        result = certify_candidate(contract, nodes, edges, assignments, binding,
                                   synthetic_fixture=True)
        self.assertIn("EDGE_OVERLAP_NOT_ALLOWED", result["blockers"])

    def test_cross_province_edge_and_duplicate_edge_rejected(self):
        contract, nodes, edges, assignments, binding = _fixture()
        nodes[1]["CPRO"] = "11"
        nodes[1]["id"] = "1100101002"
        nodes[1]["CUMUN"] = "11001"
        nodes[1]["physical_parts"][0]["id"] = nodes[1]["id"] + ":p0000"
        assignments[1]["CUSEC"] = nodes[1]["id"]
        old_id = "1000100002"
        for edge in edges:
            if edge["u"] == old_id:
                edge["u"] = nodes[1]["id"]
            if edge["v"] == old_id:
                edge["v"] = nodes[1]["id"]
        result = certify_candidate(contract, nodes, edges, assignments, binding,
                                   synthetic_fixture=True)
        self.assertIn("EDGE_CROSSES_PROVINCES", result["blockers"])

        contract, nodes, edges, assignments, binding = _fixture()
        edges.append({**edges[0], "u": edges[0]["v"], "v": edges[0]["u"]})
        result = certify_candidate(contract, nodes, edges, assignments, binding,
                                   synthetic_fixture=True)
        self.assertIn("EDGE_DUPLICATE_OR_ASYMMETRIC", result["blockers"])

    def test_bad_population_and_contract_source_hash_rejected(self):
        contract, nodes, edges, assignments, binding = _fixture(
            populations=[60000, 60000, 60000, 40000, 0, 0]
        )
        result = certify_candidate(contract, nodes, edges, assignments, binding,
                                   synthetic_fixture=True)
        self.assertIn("PROVINCIAL_POPULATION_DOES_NOT_MATCH_CONTRACT_QUOTA",
                      result["blockers"])

        contract, nodes, edges, assignments, binding = _fixture()
        binding["geometry"]["sha256"] = "f" * 64
        result = certify_candidate(contract, nodes, edges, assignments, binding,
                                   synthetic_fixture=True)
        self.assertIn("SOURCE_BINDING_MISMATCH:geometry", result["blockers"])

    def test_multipart_without_nominal_exception_and_wrong_policy_rejected(self):
        contract, nodes, edges, assignments, binding = _fixture()
        nodes[0]["physical_parts"].append({
            "id": nodes[0]["id"] + ":p0001", "geometry_sha256": "a" * 64,
            "physical_component": "10-component-2",
        })
        result = certify_candidate(contract, nodes, edges, assignments, binding,
                                   synthetic_fixture=True)
        self.assertIn("MULTIPART_NOMINAL_EXCEPTION_NOT_APPROVED", result["blockers"])

        contract, nodes, edges, assignments, binding = _fixture()
        contract["decisions"]["contiguity"]["value"] = "point_contact"
        result = certify_candidate(contract, nodes, edges, assignments, binding,
                                   synthetic_fixture=True)
        self.assertEqual(result["blockers"], ["CONGRESS_CONTRACT_INVALID"])

    def test_municipal_split_fails_closed_without_independent_search_proof(self):
        contract, nodes, edges, assignments, binding = _fixture()
        result = certify_candidate(contract, nodes, edges, assignments, binding,
                                   synthetic_fixture=True, municipal_search_budget=1)
        self.assertEqual(result["status"], "NOT_CERTIFIABLE")
        self.assertIn("MUNICIPAL_MINIMALITY_SEARCH_EXHAUSTED", result["blockers"])
        self.assertFalse(result["generation_authorized"])

    def test_product_gate_rejects_blocked_topology_and_conditional_split_proof(self):
        with self.assertRaisesRegex(ValueError, "NATIONAL_TOPOLOGY_GATE_BLOCKED"):
            _require_product_gates({"topology_gate": "BLOCKED"}, [])
        with self.assertRaisesRegex(ValueError, "MUNICIPAL_SPLIT_PROOF_SCOPE_INSUFFICIENT"):
            _require_product_gates({"topology_gate": "PASS"}, [{
                "proof": {"method": "BOUNDED_EXHAUSTIVE_FIXED_OTHER_CUSECS",
                          "scope": "OTHER_CUSECS_FIXED"}
            }])

    def test_trusted_evidence_is_pinned_and_candidate_fields_are_compared_exactly(self):
        contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
        trusted = _trusted_evidence(ROOT, contract)
        self.assertEqual(trusted["topology_gate"], "BLOCKED")
        self.assertEqual(len(trusted["units"]), 52)

        nodes, edges = [], []
        for unit in trusted["units"].values():
            for original in unit["nodes"]:
                nodes.append({
                    "id": original["CUSEC"], "CPRO": original["CPRO"],
                    "CUMUN": original["CUMUN"], "pop": original["POB_2025"],
                    "geometry_sha256": original["geometry_sha256"],
                    "source_geometry_sha256": original["source_geometry_sha256"],
                    "physical_parts": [{
                        "id": part, "geometry_sha256": original["geometry_sha256"],
                        "physical_component": original["physical_component"],
                    } for part in original["physical_part_components"]],
                })
            edges.extend(unit["edges"])
        _verify_against_trusted(nodes, edges, trusted)
        altered = copy.deepcopy(nodes)
        altered[0]["pop"] += 1
        with self.assertRaisesRegex(ValueError, "CANDIDATE_ADMIN_OR_POPULATION_TRUST_MISMATCH"):
            _verify_against_trusted(altered, edges, trusted)

        altered_edges = copy.deepcopy(edges)
        altered_edges[0]["shared_border_m"] += 1
        with self.assertRaisesRegex(ValueError, "CANDIDATE_EDGE_EVIDENCE_TRUST_MISMATCH"):
            _verify_against_trusted(nodes, altered_edges, trusted)


if __name__ == "__main__":
    unittest.main()
