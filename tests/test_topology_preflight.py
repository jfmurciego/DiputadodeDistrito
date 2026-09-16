#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Pruebas sintéticas reutilizables del preflight topológico territorial."""
import unittest

from ddd_core.topology_preflight import evaluate_topology_preflight


def unit(province="01", municipality="001", multipart=False):
    return {"province": province, "municipality": municipality, "multipart": multipart}


def bridge(u, v, **extra):
    data = {
        "u": u,
        "v": v,
        "admin_scope": "province:01",
        "edge_type": "administrative_exclave",
        "reason": "synthetic diagnosed disconnection",
        "source": "synthetic fixture",
    }
    data.update(extra)
    return data


class TopologyPreflightSyntheticCases(unittest.TestCase):
    def run_case(self, units, contacts, bridges=None, threshold=1.0):
        return evaluate_topology_preflight(
            units=units,
            contacts=contacts,
            bridges=bridges or [],
            min_shared_border_m=threshold,
            productive_continental=True,
        )

    def test_01_point_contact(self):
        r = self.run_case(
            {"a": unit(), "b": unit(municipality="002")},
            [{"u": "a", "v": "b", "shared_border_m": 0.0}],
        )
        self.assertEqual("NEEDS_POLICY", r["decision"])
        self.assertEqual(1, len(r["point_contacts_removed"]))

    def test_02_border_below_threshold(self):
        r = self.run_case(
            {"a": unit(), "b": unit(municipality="002")},
            [{"u": "a", "v": "b", "shared_border_m": 0.5}],
        )
        self.assertEqual("NEEDS_POLICY", r["decision"])
        self.assertEqual(1, len(r["edges_below_threshold"]))

    def test_03_enclave_or_exclave_without_policy(self):
        r = self.run_case(
            {"a": unit(), "b": unit(municipality="002"), "c": unit(municipality="003")},
            [{"u": "a", "v": "b", "shared_border_m": 10.0}],
        )
        self.assertEqual("NEEDS_POLICY", r["decision"])
        self.assertIn("c", r["isolated_sections"])

    def test_04_multipart_section(self):
        r = self.run_case(
            {"a": unit(multipart=True), "b": unit(municipality="002")},
            [{"u": "a", "v": "b", "shared_border_m": 10.0}],
        )
        self.assertEqual("READY", r["decision"])
        self.assertEqual(["a"], r["multipart_sections"])

    def test_05_valid_bridge(self):
        r = self.run_case(
            {"a": unit(), "b": unit(municipality="002")},
            [],
            [bridge("a", "b")],
        )
        self.assertEqual("READY", r["decision"])
        self.assertEqual(1, len(r["bridges"]["accepted"]))

    def test_06_missing_endpoint(self):
        r = self.run_case(
            {"a": unit()},
            [],
            [bridge("a", "missing")],
        )
        self.assertEqual("BLOCKED", r["decision"])
        self.assertEqual(1, len(r["bridges"]["rejected"]))

    def test_07_cross_province_bridge(self):
        r = self.run_case(
            {"a": unit(province="01"), "b": unit(province="02", municipality="002")},
            [],
            [bridge("a", "b")],
        )
        self.assertEqual("BLOCKED", r["decision"])
        self.assertIn("cross-province", r["bridges"]["rejected"][0]["rejection_reason"])

    def test_08_unnecessary_bridge(self):
        r = self.run_case(
            {"a": unit(), "b": unit(municipality="002")},
            [{"u": "a", "v": "b", "shared_border_m": 10.0}],
            [bridge("a", "b")],
        )
        self.assertEqual("BLOCKED", r["decision"])
        self.assertIn("does not resolve", r["bridges"]["rejected"][0]["rejection_reason"])

    def test_09_unresolved_disconnection(self):
        r = self.run_case(
            {"a": unit(), "b": unit(municipality="002"), "c": unit(municipality="003")},
            [],
            [bridge("a", "b")],
        )
        self.assertEqual("NEEDS_POLICY", r["decision"])
        self.assertEqual(2, len(r["components"]["territorial_operational"]))


if __name__ == "__main__":
    unittest.main()
