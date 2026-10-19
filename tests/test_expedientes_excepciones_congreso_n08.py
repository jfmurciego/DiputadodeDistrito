"""N08 nominal component evidence is sourced only from trusted original INE input."""
import hashlib
import json
import unittest

from herramientas.expedientes_excepciones_congreso_n08 import build_dossier


class N08FiveProvinceDossiers(unittest.TestCase):
    def test_all_five_unfeasible_strict_provinces_and_ten_secondary_components(self):
        result = build_dossier()
        self.assertEqual(result["candidate_provinces"], ["07", "09", "17", "34", "36"])
        self.assertEqual(result["secondary_count"], 10)
        self.assertEqual(
            {p["CPRO"]: p["strict_disconnected_component_count"] for p in result["provinces"]},
            {"07": 4, "09": 4, "17": 2, "34": 3, "36": 2})
        self.assertEqual(result["approved_national_K"], 407)
        self.assertEqual(result["districts_generated"], 0)
        self.assertFalse(result["generation_authorized"])

    def test_each_nominal_candidate_has_original_sections_and_unapproved_exception(self):
        records = build_dossier()["secondary_components_requiring_classification"]
        self.assertEqual(len({(r["CPRO"], r["component_id"]) for r in records}), 10)
        for r in records:
            with self.subTest(province=r["CPRO"], component=r["component_id"]):
                self.assertGreater(r["population_2025"], 0)
                self.assertGreater(len(r["CUSEC_sha256"]), 63)
                self.assertFalse(r["source_effective_2025_cnig_verified"])
                self.assertTrue(r["requires_individual_owner_decision"])
                self.assertEqual(r["legal_geographic_exception_status"], "NOT_APPROVED")

    def test_burgos_and_palencia_known_isolated_cusec_are_present_without_bridges(self):
        result = build_dossier()
        get = lambda code: [r for r in result["secondary_components_requiring_classification"]
                            if r["CPRO"] == code]
        burgos = {u for comp in get("09") for u in comp["CUSEC_list"]}
        palencia = {u for comp in get("34") for u in comp["CUSEC_list"]}
        self.assertTrue({"0910901001", "0927601001", "0915401001", "0922301001"}.issubset(burgos))
        self.assertTrue({"3403201001", "3424201001"}.issubset(palencia))

    def test_missing_historical_accreditation_is_not_promoted(self):
        result = build_dossier()
        for field in ("cnig_2025_independent_boundary_crossvalidation",
                      "individual_geographical_exceptions_approved",
                      "full_52_province_feasibility_proven", "generation_authorized"):
            self.assertIs(result[field], False)


if __name__ == "__main__":
    unittest.main()
