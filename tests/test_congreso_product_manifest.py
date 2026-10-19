import json
from pathlib import Path
import unittest

from ddd_core.congreso_product_manifest import (
    SCHEMA, build_candidate_manifest, validate_candidate_manifest,
)


ROOT = Path(__file__).resolve().parents[1]


class CandidateManifestTests(unittest.TestCase):
    def setUp(self):
        self.contract = {"sources": {
            "geometry": {"edition": 2025, "sha256": "1" * 64},
            "population": {"edition": 2025, "sha256": "2" * 64},
        }}
        self.binding = {"geometry": {"edition": 2025, "sha256": "1" * 64},
                        "population": {"edition": 2025, "sha256": "2" * 64}}
        self.nodes = [{"id": "0100101001", "pop": 10}]
        self.edges = []
        self.assignments = [{"CUSEC": "0100101001", "district_id": "D1"}]
        self.topology_sha = "a" * 64
        self.manifest = build_candidate_manifest(
            self.contract, self.binding, self.nodes, self.edges,
            self.assignments, self.topology_sha,
        )

    def test_manifest_is_strict_and_generation_disabled(self):
        schema = json.loads((ROOT / "schemas/congreso_candidate_product.schema.json").read_text())
        self.assertEqual(schema["$id"], SCHEMA)
        self.assertEqual(set(schema["properties"]["source_binding"]["required"]),
                         {"geometry", "population"})
        self.assertFalse(self.manifest["generation_authorized"])
        self.assertFalse(self.manifest["synthetic_fixture"])
        validate_candidate_manifest(
            self.manifest, contract=self.contract, source_binding=self.binding,
            nodes=self.nodes, edges=self.edges, assignments=self.assignments,
            trusted_topology_manifest_sha256=self.topology_sha,
        )

    def test_rejects_extra_missing_and_hash_mismatch(self):
        variants = []
        extra = dict(self.manifest, extra="x")
        variants.append(extra)
        missing = dict(self.manifest); missing.pop("edges_sha256")
        variants.append(missing)
        altered = dict(self.manifest, nodes_sha256="b" * 64)
        variants.append(altered)
        for manifest in variants:
            with self.subTest(manifest=manifest):
                with self.assertRaises(ValueError):
                    validate_candidate_manifest(
                        manifest, contract=self.contract, source_binding=self.binding,
                        nodes=self.nodes, edges=self.edges, assignments=self.assignments,
                        trusted_topology_manifest_sha256=self.topology_sha,
                    )

    def test_rejects_authorization_or_synthetic_coercion(self):
        for key, value in (("generation_authorized", True), ("generation_authorized", 0),
                           ("synthetic_fixture", True), ("synthetic_fixture", 0)):
            manifest = dict(self.manifest, **{key: value})
            with self.subTest(key=key, value=value), self.assertRaises(ValueError):
                validate_candidate_manifest(
                    manifest, contract=self.contract, source_binding=self.binding,
                    nodes=self.nodes, edges=self.edges, assignments=self.assignments,
                    trusted_topology_manifest_sha256=self.topology_sha,
                )

    def test_rejects_invalid_topology_hash(self):
        with self.assertRaises(ValueError):
            build_candidate_manifest(self.contract, self.binding, self.nodes, self.edges,
                                     self.assignments, "not-a-hash")

    def test_rejects_source_binding_mismatch_or_non_2025(self):
        for binding in (
            {**self.binding, "extra": {"edition": 2025, "sha256": "3" * 64}},
            {**self.binding, "geometry": {"edition": 2026, "sha256": "1" * 64}},
            {**self.binding, "population": {"edition": True, "sha256": "2" * 64}},
        ):
            with self.subTest(binding=binding), self.assertRaises(ValueError):
                build_candidate_manifest(self.contract, binding, self.nodes, self.edges,
                                         self.assignments, self.topology_sha)


if __name__ == "__main__":
    unittest.main()
