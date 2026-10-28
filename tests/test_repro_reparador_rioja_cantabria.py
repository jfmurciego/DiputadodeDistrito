"""Versión 1.0.0; 2026-10-08; regresión exacta local; CI_PENDIENTE.
Origen: encargo Work La Rioja/Cantabria. Nuevo archivo sin predecesor.
Cambios/motivo: conservar la obstrucción real y probar cierre de trazabilidad.
"""
import copy
import json
import unittest
from pathlib import Path
from unittest.mock import patch

from herramientas import repro_reparador_rioja_cantabria as h


class RiojaRepairReproductionTests(unittest.TestCase):
    def setUp(self):
        self.case = json.loads((Path(__file__).parent / "fixtures/m05_rioja_37473252569.json").read_text())
        self.case["kwargs"]["district_floors"] = {
            int(d): f for d, f in self.case["kwargs"]["district_floors"].items()}

    def test_exact_initial_partition(self):
        kw = self.case["kwargs"]
        m = h.metrics(self.case, kw["assignments"])
        self.assertEqual(self.case["section_count"], 343)
        self.assertEqual(len(kw["units"]), 193)
        self.assertEqual(len(set(kw["assignments"].values())), 33)
        self.assertEqual(len(self.case["frozen"]), 19)
        self.assertEqual(m["objective"][:2], [0, 1])
        self.assertEqual(m["outside_districts"], {22: 13846})
        self.assertEqual(m["population_min"], 8750)
        self.assertEqual(sum(m["structural_constraints"]["populations"].values()), 322282)
        self.assertTrue(m["structural_constraints"]["valid"])

    def test_real_atomic_graph_exhausts_without_connected_district_in_band(self):
        proof = h.connected_band_obstruction(self.case, "26:26125:M")
        self.assertTrue(proof["exhaustive_no_feasible_set"])
        self.assertIsNone(proof["feasible_connected_set"])
        self.assertEqual([r["population"] for r in proof["explored"]], [4025, 6769])
        self.assertEqual(min(r["population"] for r in proof["over_upper"]), 11580)

    def test_historical_focal_search_requires_matching_repair_code_identity(self):
        # El artefacto conserva el resultado histórico, pero el motor local ya
        # no es idéntico. Debe fallar cerrado antes de atribuirle una reproducción.
        with self.assertRaisesRegex(ValueError, "REPAIR_CODE_DIFFERS_FROM_RUN"):
            h.replay(self.case, h.core.SearchLimits(max_depth=0))

    def test_legal_rincon_transfer_worsens_maximum_deviation(self):
        kw = self.case["kwargs"]
        state = kw["assignments"]
        ok, _, _ = h.core._valid_transfer(state, kw["units"], kw["adjacency"],
                                         ["26:26125:M"], 22, 28, floor=kw["floor"], cap=kw["cap"])
        self.assertTrue(ok)
        trial = dict(state)
        trial["26:26125:M"] = 28
        after = h.metrics(self.case, trial)
        self.assertEqual(after["objective"][:2], [0, 1])
        self.assertGreater(after["max_relative_deviation"], h.metrics(self.case, state)["max_relative_deviation"])

    def test_budget_cut_is_not_impossibility(self):
        proof = h.connected_band_obstruction(self.case, "26:26125:M", max_states=1)
        self.assertFalse(proof["exhaustive_no_feasible_set"])

    def test_feasible_connected_set_is_not_impossibility(self):
        case = copy.deepcopy(self.case)
        case["kwargs"]["units"]["26:26125:M"]["population"] = 9000
        proof = h.connected_band_obstruction(case, "26:26125:M")
        self.assertEqual(proof["feasible_connected_set"], ["26:26125:M"])
        self.assertFalse(proof["exhaustive_no_feasible_set"])

    def test_checkpoint_hash_fails_before_decoding(self):
        with self.assertRaisesRegex(ValueError, "CHECKPOINT_SHA256_MISMATCH"):
            h.decode_checkpoint(b"not exact checkpoint", "la_rioja", h.CHECKPOINTS["la_rioja"]["sha256"])

    def test_repaired_output_cannot_be_relabelled_as_input(self):
        self.case["report"]["population_repair"]["enabled"] = True
        with self.assertRaisesRegex(ValueError, "PRE_REPAIR_STATE_NOT_PROVEN"):
            h.replay(self.case)

    def test_changed_core_requires_explicit_new_experiment(self):
        with patch.object(h, "digest", return_value="changed"):
            with self.assertRaisesRegex(ValueError, "REPAIR_CODE_DIFFERS_FROM_RUN"):
                h.replay(self.case)

    def test_large_search_limit_is_rejected_after_matching_identity(self):
        expected = self.case["compatibility"]["engine_files"]["ddd_core/m05_population_repair.py"]
        # Aísla la guarda de presupuesto sin atribuir el checkpoint al motor local.
        with patch.object(h, "digest", return_value=expected):
            with self.assertRaisesRegex(ValueError, "OPERATIONAL_LIMIT_EXCEEDED"):
                h.replay(self.case, h.core.SearchLimits(max_seconds=60))


if __name__ == "__main__":
    unittest.main()
