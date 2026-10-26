"""León/Cáceres analytical candidate contract and deterministic repair tests."""
import copy
import gzip
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
import zipfile

from ddd_core.congreso_constructive_witness import evaluate_unit
from ddd_core.congreso_pilot_adapter import audit_candidate, canonical_sha, model, state_from_candidate
from herramientas.generar_piloto_congreso_leon import produce


ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "docs/ESTUDIOS/N08_PILOTO_PROVINCIAL_20261026"


def inputs(cpro):
    preflight = ROOT / "docs/ESTUDIOS/CAMPANA_NACIONAL_20261013" / f"PREFLIGHT_CPRO{cpro}"
    product = ROOT / "docs/ESTUDIOS/N08_TOPOLOGIA_NACIONAL_20251012/producto"
    contract_path = ROOT / "territorios/congreso/contrato_congreso_2026.json"
    unit_path = product / "unidades" / f"{cpro}.json.gz"
    binding = evaluate_unit(preflight_path=preflight / "PREFLIGHT.json",
                            checkpoint_path=preflight / "CHECKPOINT.json",
                            unit_path=unit_path,
                            product_manifest_path=product / "manifest.json",
                            contract_path=contract_path)
    if binding["errors"]:
        raise AssertionError(binding["errors"])
    with gzip.open(unit_path, "rt", encoding="utf-8") as stream:
        unit = json.load(stream)
    return unit, json.loads(contract_path.read_text(encoding="utf-8")), binding


class CongressPilotAdapterTests(unittest.TestCase):
    def test_recovered_original_artifact_matches_candidate_bytes_and_receipt_hashes(self):
        archive = EVIDENCE / "LEON/leon-original-artifact.zip"
        candidate = EVIDENCE / "LEON/leon-original.json"
        self.assertEqual(hashlib.sha256(archive.read_bytes()).hexdigest(),
                         "9bc7edf8f6a76b1f706c692c6f71972c1f6eff01c3a1c18758ff5a1324aa9c15")
        self.assertEqual(hashlib.sha256(candidate.read_bytes()).hexdigest(),
                         "237f7a73218347aab56964fe2b1ae918d5b2516f8bb33f842be15459637ed8c9")
        with zipfile.ZipFile(archive) as source:
            self.assertEqual(source.namelist(), ["leon-4-candidatos.json"])
            self.assertEqual(source.read(source.namelist()[0]), candidate.read_bytes())

    def test_original_leon_candidate_audit_records_all_six_splits_and_failures(self):
        unit, contract, bound = inputs("24")
        candidate = json.loads((EVIDENCE / "LEON/leon-original.json").read_text(encoding="utf-8"))
        audit = audit_candidate(candidate, unit, contract, expected_binding=bound["input_sha256"])
        self.assertEqual((audit["sections"], audit["population"], audit["k"]), (444, 448030, 4))
        self.assertEqual(audit["checks"]["municipal_discipline"], "INCUMPLIDO")
        self.assertEqual(audit["checks"]["section_graph_contiguity"], "DEMOSTRADO")
        self.assertEqual(audit["checks"]["original_polygon_part_contiguity"], "PENDIENTE")
        self.assertEqual({row["CUMUN"] for row in audit["municipalities_split"]},
                         {"24056", "24089", "24115", "24163", "24170", "24202"})

    def test_leon_repair_is_byte_deterministic_and_keeps_gates_closed(self):
        source = EVIDENCE / "LEON/leon-original.json"
        expected = (EVIDENCE / "LEON/leon-corrected.json").read_bytes()
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "candidate.json"
            result = produce(ROOT, output, cpro="24", input_candidate=source, repair=True)
            self.assertEqual(output.read_bytes(), expected)
        audit = result["audit"]
        self.assertEqual(audit["checks"]["municipal_discipline"], "DEMOSTRADO")
        self.assertEqual(audit["municipalities_split"], [])
        self.assertTrue(all(v == "DEMOSTRADO" for k, v in audit["checks"].items()
                            if k in {"CUSEC_coverage_and_atomicity", "population_conservation",
                                     "province_and_K", "population_bounds", "section_graph_contiguity"}))
        self.assertIs(result["candidate"]["generation_authorized"], False)
        self.assertEqual(result["candidate"]["product_certification"], "NOT_PERFORMED")

    def test_caceres_reuses_generic_province_and_existing_witness(self):
        unit, contract, bound = inputs("10")
        candidate = json.loads((EVIDENCE / "CACERES/caceres-3-analitico.json").read_text(encoding="utf-8"))
        audit = audit_candidate(candidate, unit, contract, expected_binding=bound["input_sha256"])
        self.assertEqual(candidate["source_witness_sha256"], "f387c48696abbedf7dc1cc6084fef863a8e8eea9251ad084c4f566db94063ce2")
        self.assertEqual((audit["sections"], audit["population"], audit["k"]), (411, 388190, 3))
        self.assertEqual(candidate["input_sha256"], "38c4ae7c5720645698e0fe90cf3ea95f8ba90e18bd761d1693c5c4b658a18910")
        self.assertEqual(audit["checks"]["municipal_discipline"], "DEMOSTRADO")
        self.assertEqual(audit["checks"]["section_graph_contiguity"], "DEMOSTRADO")
        self.assertIs(candidate["generation_authorized"], False)
        self.assertEqual(candidate["municipalities_split"], ["10037"])
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "caceres.json"
            produce(ROOT, output, cpro="10", repair=True)
            self.assertEqual(output.read_bytes(),
                             (EVIDENCE / "CACERES/caceres-3-analitico.json").read_bytes())

    def test_candidate_contract_rejects_cusec_duplication_population_and_gate(self):
        unit, contract, bound = inputs("24")
        candidate = json.loads((EVIDENCE / "LEON/leon-corrected.json").read_text(encoding="utf-8"))
        duplicate = copy.deepcopy(candidate)
        duplicate["districts"][1]["cusecs"].append(duplicate["districts"][0]["cusecs"][0])
        with self.assertRaisesRegex(ValueError, "CUSEC_UNKNOWN_OR_DUPLICATE"):
            audit_candidate(duplicate, unit, contract, expected_binding=bound["input_sha256"])
        wrong_population = copy.deepcopy(candidate)
        wrong_population["districts"][0]["population"] += 1
        with self.assertRaisesRegex(ValueError, "DISTRICT_POPULATION_MISMATCH"):
            audit_candidate(wrong_population, unit, contract, expected_binding=bound["input_sha256"])
        opened = copy.deepcopy(candidate)
        opened["generation_authorized"] = True
        with self.assertRaisesRegex(ValueError, "CANDIDATE_AUTHORIZATION_INVALID"):
            audit_candidate(opened, unit, contract, expected_binding=bound["input_sha256"])
        forged = copy.deepcopy(candidate)
        forged["witness_sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "CANDIDATE_ASSIGNMENT_WITNESS_MISMATCH"):
            audit_candidate(forged, unit, contract, expected_binding=bound["input_sha256"])

    def test_physical_contiguity_cannot_be_promoted_by_caller_supplied_boolean(self):
        unit, contract, bound = inputs("24")
        candidate = json.loads((EVIDENCE / "LEON/leon-corrected.json").read_text(encoding="utf-8"))
        forged_geometry = {
            "candidate_canonical_sha256": canonical_sha(candidate),
            "cpro": "24", "k": 4,
            "source": {"archive_sha256": contract["sources"]["geometry"]["sha256"]},
            "within_district_part_graph_connected": True,
        }
        with self.assertRaisesRegex(TypeError, "unexpected keyword argument"):
            audit_candidate(candidate, unit, contract,
                            expected_binding=bound["input_sha256"], geometry=forged_geometry)
        audit = audit_candidate(candidate, unit, contract, expected_binding=bound["input_sha256"])
        self.assertEqual(audit["checks"]["original_polygon_part_contiguity"], "PENDIENTE")

    def test_model_rejects_point_or_nonfinite_edges_and_wrong_source_binding(self):
        unit, contract, bound = inputs("24")
        candidate = json.loads((EVIDENCE / "LEON/leon-corrected.json").read_text(encoding="utf-8"))
        wrong_binding = dict(bound["input_sha256"])
        wrong_binding["contract"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "SOURCE_BINDING_MISMATCH"):
            audit_candidate(candidate, unit, contract, expected_binding=wrong_binding)
        malformed = copy.deepcopy(unit)
        malformed["edges"][0]["kind"] = "point"
        with self.assertRaisesRegex(ValueError, "NON_PHYSICAL_EDGE"):
            model(malformed, contract)
        malformed = copy.deepcopy(unit)
        malformed["edges"][0]["shared_border_m"] = float("nan")
        with self.assertRaisesRegex(ValueError, "NON_PHYSICAL_EDGE"):
            model(malformed, contract)
        malformed = copy.deepcopy(unit)
        malformed["edges"][0]["shared_border_m"] = True
        with self.assertRaisesRegex(ValueError, "NON_PHYSICAL_EDGE"):
            model(malformed, contract)


if __name__ == "__main__":
    unittest.main()
