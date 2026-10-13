"""Versión 1.1.0; 2026-10-12; regresión fuentes INE coexistentes con N06.
Anterior: legacy/tests/test_materializar_fuentes_nacionales_ine_pre_n06.py.
Cambio: aprobación K/referencia; otras decisiones pendientes y generación bloqueada.
"""
import unittest
from unittest.mock import patch

from herramientas import materializar_fuentes_nacionales_ine as sources


class PopulationPairValidationTests(unittest.TestCase):
    def setUp(self):
        self.crosswalk = [
            {"CUSEC": "0100101001", "CPRO": "01", "CUMUN": "01001"},
            {"CUSEC": "0100201001", "CPRO": "01", "CUMUN": "01002"},
            {"CUSEC": "5100101001", "CPRO": "51", "CUMUN": "51001"},
        ]
        self.rows = [
            {"Periodo": "2025", "Sexo": "Total", "Edad": "Todas las edades",
             "Provincias": "01 Araba/Álava", "Municipios": "01001 Alegría-Dulantzi",
             "Secciones": "0100101001 Alegría sección 001", "Total": "100"},
            {"Periodo": "2025", "Sexo": "Total", "Edad": "Todas las edades",
             "Provincias": "01 Araba/Álava", "Municipios": "01002 Amurrio",
             "Secciones": "0100201001 Amurrio sección 001", "Total": "200"},
            {"Periodo": "2025", "Sexo": "Total", "Edad": "Todas las edades",
             "Provincias": "51 Ceuta", "Municipios": "51001 Ceuta",
             "Secciones": "5100101001 Ceuta sección 001", "Total": "300"},
            {"Periodo": "2025", "Sexo": "Total", "Edad": "Todas las edades",
             "Provincias": "01 Araba/Álava", "Municipios": "", "Secciones": "", "Total": "300"},
            {"Periodo": "2025", "Sexo": "Total", "Edad": "Todas las edades",
             "Provincias": "51 Ceuta", "Municipios": "", "Secciones": "", "Total": "300"},
            {"Periodo": "2025", "Sexo": "Total", "Edad": "Todas las edades",
             "Provincias": "", "Municipios": "", "Secciones": "", "Total": "600"},
        ]

    def run_rows(self, rows):
        provinces = {"01", "51"}
        with (patch.object(sources, "EXPECTED_SECTIONS", len(self.crosswalk)),
              patch.object(sources, "EXPECTED_TOTAL", 600),
              patch.object(sources, "PROVINCES", provinces)):
            return sources.validate_population_rows(
                rows, self.crosswalk, expected_counts={"01": 2, "51": 1})

    def test_exact_identity_aggregates_and_ceuta(self):
        populations, audit = self.run_rows(self.rows)
        self.assertEqual(populations, {"0100101001": 100, "0100201001": 200, "5100101001": 300})
        self.assertEqual(audit["section_count"], 3)
        self.assertEqual(audit["national_official_total"], 600)
        self.assertEqual(audit["ceuta"], {"sections": 1, "population": 300})

    def test_historical_unobserved_section_is_not_zero(self):
        rows = self.rows.copy()
        rows.insert(0, {"Periodo": "2025", "Sexo": "Total", "Edad": "Todas las edades",
                        "Provincias": "02 Albacete", "Municipios": "02072 Socovos",
                        "Secciones": "0207202001 Socovos sección 02001", "Total": ""})
        _, audit = self.run_rows(rows)
        self.assertEqual(audit["row_levels"]["section_unobserved"], 1)

    def test_duplicate_identity_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "POPULATION_DUPLICATE_CUSEC"):
            self.run_rows(self.rows[:3] + [self.rows[0], self.rows[3]])

    def test_invalid_population_is_rejected(self):
        rows = [dict(row) for row in self.rows]
        rows[0]["Total"] = "n.d."
        with self.assertRaisesRegex(ValueError, "POPULATION_VALUE_INVALID"):
            self.run_rows(rows)

    def test_active_extra_cusec_with_population_is_rejected(self):
        rows = self.rows.copy()
        rows.insert(0, {"Periodo": "2025", "Sexo": "Total", "Edad": "Todas las edades",
                        "Provincias": "02 Albacete", "Municipios": "02001 Abengibre",
                        "Secciones": "0200101001 Abengibre sección 001", "Total": "9"})
        with self.assertRaisesRegex(ValueError, "POPULATION_EXTRA_CUSEC_WITH_VALUE"):
            self.run_rows(rows)


class MaterializedPackageTests(unittest.TestCase):
    def test_real_materialized_package_manifest_and_artifacts(self):
        import hashlib
        import json
        from pathlib import Path

        package = Path(__file__).resolve().parents[1] / "territorios/congreso/fuentes/ine_2025_2025"
        manifest = json.loads((package / "manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["status"], "SOURCE_PAIR_ACCREDITED; CONTRACT_WAIT_OWNER; GENERATION_DISABLED")
        self.assertEqual(manifest["population"]["section_count"], 36554)
        self.assertEqual(manifest["population"]["section_population_total"], 49128297)
        self.assertEqual(manifest["population"]["row_levels"]["section_unobserved"], 338)
        self.assertEqual(manifest["input_contract"]["geometry"]["required_fields"],
                         ["CUSEC", "CUMUN", "CPRO", "CMUN", "CDIS", "CSEC"])
        self.assertEqual(manifest["input_contract"]["population"]["filter"],
                         {"Periodo": "2025", "Sexo": "Total", "Edad": "Todas las edades"})
        self.assertEqual(manifest["population"]["ceuta"], {"sections": 56, "population": 83567})
        self.assertEqual(manifest["population"]["melilla"], {"sections": 44, "population": 87067})
        self.assertNotIn("by_cusec", manifest["geometry"])
        self.assertEqual(
            manifest["geometry"]["geometry_identity_sha256"],
            "6eccbc0c7f4867656c235462ae0b6d381dcdaeb5c912e5295976ca8f120860ff",
        )
        self.assertEqual(manifest["sources"]["geometry"]["sha256"], sources.EXPECTED_SECTIONING_SHA)
        self.assertEqual(manifest["sources"]["population"]["sha256"], sources.EXPECTED_POPULATION_SHA)
        self.assertFalse(manifest["delivery_contract"]["geometry_coordinates_duplicated"])
        self.assertEqual(manifest["delivery_contract"]["geometry_join_key"], "CUSEC")

        canonical = dict(manifest)
        identity = canonical.pop("manifest_identity_sha256")
        payload = json.dumps(canonical, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
        self.assertEqual(hashlib.sha256(payload).hexdigest(), identity)
        for name, record in manifest["outputs"].items():
            artifact = package / name
            self.assertEqual(hashlib.sha256(artifact.read_bytes()).hexdigest(), record["sha256"])
            self.assertEqual(artifact.stat().st_size, record["bytes"])

        with (package / "poblacion_por_seccion_2025.csv").open(encoding="utf-8", newline="") as stream:
            import csv
            rows = list(csv.DictReader(stream))
        self.assertEqual(len(rows), 36554)
        self.assertEqual(len({row["CUSEC"] for row in rows}), 36554)
        self.assertEqual(sum(int(row["POB_2025"]) for row in rows), 49128297)
        self.assertEqual(list(rows[0]), ["CUSEC", "CUMUN", "CPRO", "CMUN", "CDIS", "CSEC", "POB_2025"])
        with (package / "crosswalk_n07_2025.csv").open(encoding="utf-8-sig", newline="") as stream:
            crosswalk = {row["CUSEC"]: row for row in csv.DictReader(stream)}
        self.assertEqual(len(crosswalk), 36554)
        self.assertTrue(all(all(row[field] == crosswalk[row["CUSEC"]][field]
                                for field in ("CUMUN", "CPRO", "CMUN", "CDIS", "CSEC"))
                            for row in rows))

        contract_path = package.parents[1] / "contrato_congreso_2026.json"
        contract = json.loads(contract_path.read_text(encoding="utf-8"))
        self.assertEqual(contract["metadata"]["status"], "CANDIDATO_N08_7_REGLAS_APROBADAS_GENERACION_BLOQUEADA")
        self.assertEqual(contract["population_reference"]["status"], "APPROVED_BY_OWNER")
        self.assertTrue(all(decision["status"] == "APPROVED" and decision["value"] is not None
                            for name, decision in contract["decisions"].items()
                            if name != "population_reference"))
        self.assertEqual(contract["decisions"]["population_reference"]["status"], "APPROVED")
        self.assertEqual(contract["k_decision"]["status"], "APPROVED_BY_OWNER")
        self.assertEqual(contract["k_decision"]["total"], 407)
        self.assertEqual(sum(row["k"] for row in contract["quotas_by_origin_unit"]), 407)
        self.assertFalse(contract["accreditation"]["circumscription_accreditation"])
        self.assertFalse(contract["accreditation"]["generation_authorized"])
        self.assertTrue(all(contract["sources"][role]["accreditation"] == "ACCREDITED"
                            for role in ("geometry", "population")))
        from ddd_core.congreso_contract import production_blockers
        blockers = production_blockers(contract)
        self.assertNotIn("OWNER_DECISION_PENDING", blockers)
        self.assertNotIn("DECISION_POPULATION_REFERENCE_PENDING", blockers)
        self.assertNotIn("CONGRESS_K_UNDECIDED_OR_INVALID", blockers)
        self.assertFalse(any(item.startswith("SOURCE_") for item in blockers))


if __name__ == "__main__":
    unittest.main()
