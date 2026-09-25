from __future__ import annotations

import importlib
import unittest

import test_000_integration_138_140 as _integration

_full = importlib.import_module("test_ejecucion_completa")
_full.FullProjectOrchestratorTests.test_reuse_plan_reruns_generation_for_selected_algorithm = _integration._test_reuse_plan_reruns_generation_for_selected_algorithm
_full.FullProjectOrchestratorTests.test_gerrychain_50_is_preserved_in_plan = _integration._test_gerrychain_50_is_preserved_in_plan


class IntegrationLoaderTests(unittest.TestCase):
    def test_140_fixture_patch_is_bound_to_discovery_module(self):
        self.assertIs(
            _full.FullProjectOrchestratorTests.test_reuse_plan_reruns_generation_for_selected_algorithm,
            _integration._test_reuse_plan_reruns_generation_for_selected_algorithm,
        )
        self.assertIs(
            _full.FullProjectOrchestratorTests.test_gerrychain_50_is_preserved_in_plan,
            _integration._test_gerrychain_50_is_preserved_in_plan,
        )
