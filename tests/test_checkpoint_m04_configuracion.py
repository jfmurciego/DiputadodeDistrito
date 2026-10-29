"""Versión 1.0.0; 2026-10-29; candidato. Un checkpoint M04 sólo se reutiliza con la misma K y atomicidad.
Origen: nuevo, sin predecesor.
"""
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

import yaml

from unittest import mock

from herramientas import seleccionar_checkpoint_productivo as selector
from herramientas.seleccionar_checkpoint_productivo import _validate_m04_configuration


class M04CheckpointConfigurationTests(unittest.TestCase):
    def _case(self, *, contract_ratio, report_ratio, k=109, report=True):
        tmp = tempfile.TemporaryDirectory()
        root = Path(tmp.name)
        params = root / "params.yaml"
        params.write_text(yaml.safe_dump({"modulos": {"modulo_04_generar_semillas": {
            "k_districts": 109, "municipality_atomicity_limit_ratio": contract_ratio}}}), encoding="utf-8")
        state = root / "state"
        (state / "cache").mkdir(parents=True)
        if report:
            (state / "cache/andalucia_2025_m04_informe.json").write_text(
                json.dumps({"K": k, "municipality_atomicity_limit_ratio": report_ratio}), encoding="utf-8")
        self.addCleanup(tmp.cleanup)
        return params, state

    def test_same_configuration_matches(self):
        params, state = self._case(contract_ratio=1.25, report_ratio=1.25)
        self.assertEqual("MATCH", _validate_m04_configuration(params=params, state_root=state)["status"])

    def test_old_atomicity_is_rejected(self):
        params, state = self._case(contract_ratio=1.25, report_ratio=1.75)
        with self.assertRaisesRegex(ValueError, "municipality_atomicity_limit_ratio"):
            _validate_m04_configuration(params=params, state_root=state)

    def test_other_k_is_rejected(self):
        params, state = self._case(contract_ratio=1.25, report_ratio=1.25, k=108)
        with self.assertRaisesRegex(ValueError, "k_districts"):
            _validate_m04_configuration(params=params, state_root=state)

    def test_missing_report_is_unverified(self):
        params, state = self._case(contract_ratio=1.25, report_ratio=None, report=False)
        self.assertEqual("UNVERIFIED_NO_M04_REPORT", _validate_m04_configuration(params=params, state_root=state)["status"])


    def test_certified_product_does_not_require_m05_fingerprint(self):
        params, state = self._case(contract_ratio=1.25, report_ratio=1.25)
        with mock.patch.object(selector, "validate_resume_sources", return_value={}), \
             mock.patch.object(selector, "_validate_population_certification", return_value={"ok": True}), \
             mock.patch.object(selector, "_validate_m05_compatibility", side_effect=ValueError("huella distinta")):
            consumed = selector.evaluate_candidate(params=params, package=state, run_id="1", stage="M06",
                                                   state_root=state, consume_certified=True)
            resumed = selector.evaluate_candidate(params=params, package=state, run_id="1", stage="M06",
                                                  state_root=state)
        self.assertTrue(consumed["valid"])
        self.assertEqual("M06", consumed["effective_stage"])
        self.assertFalse(consumed["requires_derivation"])
        self.assertNotEqual("M06", resumed.get("effective_stage"))


if __name__ == "__main__":
    unittest.main()
