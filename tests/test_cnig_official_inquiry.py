"""CNIG inquiry is not an accredited geospatial source receipt."""
import json
import unittest
from pathlib import Path

CAMPAIGN = Path(__file__).resolve().parents[1] / "docs/ESTUDIOS/CAMPANA_NACIONAL_20261013"

class OfficialCNIGInquiryTests(unittest.TestCase):
    def test_confirmed_form_submission_does_not_unlock_source_or_production(self):
        inquiry = json.loads((CAMPAIGN / "CNIG_CONSULTA_OFICIAL_20261018.json").read_text())
        manifest = json.loads((CAMPAIGN / "CAMPAIGN_MANIFEST.json").read_text())
        registry = json.loads((CAMPAIGN / "TASK_REGISTRY.json").read_text())
        blockers = json.loads((CAMPAIGN / "BLOCKER_REGISTRY.json").read_text())
        tasks = {task["id"]: task for task in registry["tasks"]}
        self.assertEqual(inquiry["submission_status"], "CONFIRMED_SUBMITTED")
        self.assertIsNone(inquiry["reference_number"])
        self.assertFalse(inquiry["source_bytes_received"])
        self.assertFalse(inquiry["source_accredited"])
        self.assertFalse(inquiry["additional_costs_authorized"])
        self.assertFalse(manifest["source_acquisition_authorization"]["receipt_verified"])
        self.assertFalse(manifest["official_source_inquiry"]["official_reply_received"])
        self.assertEqual(tasks["NAT-C-056"]["status"], "READY")
        self.assertEqual(tasks["NAT-F-003"]["status"], "WAIT_OWNER")
        self.assertTrue(all(tasks[f"NAT-C-{number:03d}"]["status"] == "BLOCKED_DEPENDENCY"
                            for number in range(3, 55)))
        self.assertEqual(tasks["NAT-C-002"]["status"], "BLOCKED_DEPENDENCY")
        self.assertFalse(manifest["permissions"]["production_generation"])
        self.assertTrue(any(b["id"] == "NAT-BLK-CPRO-COMPARISONS" for b in blockers["blockers"]))

if __name__ == "__main__":
    unittest.main()
