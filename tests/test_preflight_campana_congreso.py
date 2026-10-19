"""Versión 1.0.0; pruebas campaña M01-M06 diagnóstico Congreso; 2026-10-13.

Scope: serialización, checkpoint, linaje y rechazo de salidas productivas con
fixtures sintéticos. No lee fuentes territoriales ni ejecuta distritación.
Origen: nuevo, sin predecesor.
"""
from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from herramientas import preflight_campana_congreso as campaign


def _context():
    codes = campaign.PROVINCES
    return {
        "base": "a" * 40,
        "contract_sha256": "b" * 64,
        "source_manifest_sha256": "c" * 64,
        "source_binding": {
            "geometry": {"edition": 2025, "sha256": "d" * 64},
            "population": {"edition": 2025, "sha256": "e" * 64},
        },
        "topology_manifest_sha256": "f" * 64,
        "topology_manifest_identity_sha256": "1" * 64,
        "transition_sha256": "4" * 64,
        "topology_unit_sha256": {code: f"{index + 1:064x}" for index, code in enumerate(codes)},
        "units": {code: {"sections": index + 1, "population": (index + 1) * 10,
                          "edges": index, "k": 1}
                  for index, code in enumerate(codes)},
        "runner_sha256": campaign.PREFLIGHT_TOOL_SHA256,
        "runner_report_version": campaign.PREFLIGHT_RUNNER_CONTRACTS[
            campaign.PREFLIGHT_TOOL_SHA256]["report_version"],
        "campaign_tool_sha256": "2" * 64,
        "consumer_code_sha256": {"fixture.py": "3" * 64},
        "generation_authorized": False,
    }


def _report(code, context):
    unit = context["units"][code]
    return {
        "version": context["runner_report_version"], "province": code, "base": context["base"],
        "tool_sha256": context["runner_sha256"],
        "source_binding": context["source_binding"],
        "source_evidence": {"source_manifest_sha256": context["source_manifest_sha256"],
                            "contract_sha256": context["contract_sha256"]},
        "topology_manifest_identity_sha256": context["topology_manifest_identity_sha256"],
        "topology_unit_sha256": context["topology_unit_sha256"][code],
        "inputs": {"sections": unit["sections"], "population": unit["population"],
                   "physical_edges": unit["edges"], "k_approved": unit["k"]},
        "generation_authorized": False, "real_partition_created": False,
        "districts_generated": 0, "published": False,
        "modules": {"M01": {"status": "PASS"}, "M02": {"status": "PASS"},
                    "M03": {"status": "PASS"}, "M04": {"status": "PASS_NECESSARY_ONLY"},
                    "M05": {"status": "SYNTHETIC_CONTRACT_PASS_ONLY"},
                    "M06": {"status": "SYNTHETIC_CONTRACT_PASS_ONLY"}},
        "preflight_status": "BLOCKED_CONTRACT_OR_OWNER_DECISIONS",
    }


class CongressPreflightCampaignTests(unittest.TestCase):
    def test_current_contract_source_and_topology_hash_inventory_is_52_units(self):
        # The runtime Docker image deliberately contains no .git directory.
        # Stub only the Git identity lookup; all source, contract and topology
        # hashes are still verified against the actual versioned inputs.
        with patch.object(campaign.subprocess, "check_output",
                          return_value="a" * 40 + "\n") as git_identity:
            context = campaign._root_context()
        git_identity.assert_called_once()
        self.assertEqual(context["base"], "a" * 40)
        self.assertEqual(len(context["topology_unit_sha256"]), 52)
        self.assertEqual(sum(row["sections"] for row in context["units"].values()), 36554)
        self.assertEqual(sum(row["population"] for row in context["units"].values()), 49128297)
        self.assertEqual(len(context["consumer_code_sha256"]), len(campaign.CODE_DEPENDENCIES))
        self.assertEqual(context["runner_sha256"], campaign.PREFLIGHT_TOOL_SHA256)
        self.assertEqual(context["runner_report_version"], "1.2.0")
        self.assertFalse(context["generation_authorized"])

    def test_serial_52_province_run_and_resume_do_not_reexecute_completed_units(self):
        context = _context()
        calls = []

        def runner(_parts, output, code, _product, _transition):
            calls.append(code)
            output.mkdir(parents=True, exist_ok=True)
            report = _report(code, context)
            report_bytes = (json.dumps(report, sort_keys=True) + "\n").encode()
            (output / "PREFLIGHT.json").write_bytes(report_bytes)
            provincial = {"province": code,
                          "version": context["runner_report_version"],
                          "tool_sha256": context["runner_sha256"],
                          "source_binding": context["source_binding"],
                          "topology_manifest_identity_sha256": context["topology_manifest_identity_sha256"],
                          "topology_unit_sha256": context["topology_unit_sha256"][code],
                          "generation_authorized": False,
                          "districts_generated": 0,
                          "preflight_sha256": campaign._sha(report_bytes)}
            checkpoint_bytes = (json.dumps(provincial, sort_keys=True) + "\n").encode()
            (output / "CHECKPOINT.json").write_bytes(checkpoint_bytes)
            return report

        with tempfile.TemporaryDirectory() as temporary, patch.object(
            campaign, "_root_context", return_value=context
        ), patch("herramientas.preflight_caceres_n08.run", side_effect=runner):
            output = Path(temporary) / "campaign"
            first = campaign.run_campaign(Path("unused-fixture"), output)
            self.assertEqual(first["status"], "DIAGNOSTIC_COVERAGE_COMPLETE")
            self.assertEqual(first["coverage"], {"passed": 52, "failed": 0,
                                                  "not_evaluated": 0, "expected": 52})
            self.assertEqual(calls, list(campaign.PROVINCES))
            self.assertFalse(first["generation_authorized"])

            with patch("herramientas.preflight_caceres_n08.run",
                       side_effect=lambda *_args: self.fail("completed province was rerun")):
                second = campaign.run_campaign(Path("unused-fixture"), output, resume=True)
            self.assertEqual(second["passed_cpro"], list(campaign.PROVINCES))
            checkpoint = json.loads((output / "CHECKPOINT.json").read_text())
            self.assertEqual(checkpoint["coverage"]["passed"], 52)
            self.assertFalse(checkpoint["generation_authorized"])

    def test_campaign_rejects_checkpoint_with_wrong_runner_identity(self):
        context = _context()

        def runner(_parts, output, code, _product, _transition):
            output.mkdir(parents=True, exist_ok=True)
            report = _report(code, context)
            report_bytes = (json.dumps(report, sort_keys=True) + "\n").encode()
            (output / "PREFLIGHT.json").write_bytes(report_bytes)
            provincial = {"province": code,
                          "version": context["runner_report_version"],
                          "tool_sha256": context["runner_sha256"],
                          "generation_authorized": False, "districts_generated": 0,
                          "preflight_sha256": campaign._sha(report_bytes)}
            (output / "CHECKPOINT.json").write_text(json.dumps(provincial))
            return report

        for field, bad_value in (("version", "1.0.0"), ("tool_sha256", "0" * 64)):
            with self.subTest(field=field), tempfile.TemporaryDirectory() as temporary, patch.object(
                campaign, "_root_context", return_value=context
            ), patch("herramientas.preflight_caceres_n08.run", side_effect=runner):
                output = Path(temporary) / "campaign"
                def inconsistent_runner(_parts, province_output, code, _product, _transition):
                    report = _report(code, context)
                    report_bytes = (json.dumps(report, sort_keys=True) + "\n").encode()
                    province_output.mkdir(parents=True, exist_ok=True)
                    (province_output / "PREFLIGHT.json").write_bytes(report_bytes)
                    provincial = {"province": code,
                                  "version": context["runner_report_version"],
                                  "tool_sha256": context["runner_sha256"],
                                  "source_binding": context["source_binding"],
                                  "topology_manifest_identity_sha256": context["topology_manifest_identity_sha256"],
                                  "topology_unit_sha256": context["topology_unit_sha256"][code],
                                  "generation_authorized": False, "districts_generated": 0,
                                  "preflight_sha256": campaign._sha(report_bytes)}
                    provincial[field] = bad_value
                    (province_output / "CHECKPOINT.json").write_text(json.dumps(provincial))
                    return report

                with patch("herramientas.preflight_caceres_n08.run",
                           side_effect=inconsistent_runner):
                    result = campaign.run_campaign(Path("unused-fixture"), output)
                self.assertEqual(result["coverage"], {
                    "passed": 0, "failed": 52, "not_evaluated": 0, "expected": 52,
                })
                self.assertFalse(result["generation_authorized"])

    def test_report_validator_rejects_real_partition_or_real_m05_m06(self):
        context = _context()
        report = _report("10", context)
        campaign.validate_province_report(report, "10", context)
        def mutate_topology(value):
            value["topology_unit_sha256"] = "0" * 64

        for mutate in (
            lambda value: value.update(version="1.0.0"),
            lambda value: value.update(generation_authorized=True),
            lambda value: value.update(real_partition_created=True),
            lambda value: value["modules"]["M05"].update(status="PASS"),
            lambda value: value["modules"]["M06"].update(status="REAL_PARTITION_PASS"),
            mutate_topology,
        ):
            corrupted = json.loads(json.dumps(report))
            mutate(corrupted)
            with self.assertRaises(ValueError):
                campaign.validate_province_report(corrupted, "10", context)

    def test_checkpoint_validator_binds_runner_and_all_current_evidence(self):
        context = _context()
        report_bytes = json.dumps(_report("10", context), sort_keys=True).encode()
        checkpoint = {"province": "10", "version": context["runner_report_version"],
                      "tool_sha256": context["runner_sha256"],
                      "source_binding": context["source_binding"],
                      "topology_manifest_identity_sha256": context["topology_manifest_identity_sha256"],
                      "topology_unit_sha256": context["topology_unit_sha256"]["10"],
                      "generation_authorized": False, "districts_generated": 0,
                      "preflight_sha256": campaign._sha(report_bytes)}
        campaign.validate_province_checkpoint(checkpoint, "10", context, report_bytes)
        for field, invalid in (("version", "1.0.0"),
                               ("tool_sha256", "0" * 64),
                               ("source_binding", {}),
                               ("topology_unit_sha256", "f" * 64)):
            corrupted = dict(checkpoint)
            corrupted[field] = invalid
            with self.subTest(field=field), self.assertRaises(ValueError):
                campaign.validate_province_checkpoint(corrupted, "10", context, report_bytes)

    def test_resume_refuses_changed_contract_or_source_identity(self):
        context = _context()
        checkpoint = {"schema": campaign.SCHEMA, "version": campaign.VERSION,
                      "identity": {key: context[key] for key in (
                          "base", "contract_sha256", "source_manifest_sha256", "source_binding",
                          "topology_manifest_sha256", "topology_manifest_identity_sha256",
                          "topology_unit_sha256", "transition_sha256", "runner_sha256", "runner_report_version",
                          "campaign_tool_sha256",
                          "consumer_code_sha256")},
                      "records": {}, "generation_authorized": False}
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "CHECKPOINT.json"
            campaign._save_checkpoint(path, checkpoint)
            changed = json.loads(path.read_text())
            changed["identity"]["contract_sha256"] = "9" * 64
            campaign._save_checkpoint(path, changed)
            with self.assertRaisesRegex(ValueError, "CAMPAIGN_CHECKPOINT_IDENTITY_CHANGED"):
                campaign._load_checkpoint(path, checkpoint["identity"])


if __name__ == "__main__":
    unittest.main()
