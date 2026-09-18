"""Bloque B: despliegue y certificación territorial son dimensiones independientes."""
import json
import tempfile
import unittest
from pathlib import Path

from herramientas.estado_produccion import build_production_status
from herramientas.evaluar_publicacion_visor import evaluate_publication


def geometry():
    return {"decision":"PASS","blocked_districts":0,"policy_mismatches":0,"contract_blockers":[],"districts":[]}


class DeploymentVsCertificationTests(unittest.TestCase):
    def test_cyl_can_be_deployed_while_population_certification_is_blocked(self):
        report={
            "population_repair":{
                "enabled":True,
                "result":"IMPROVED_NOT_REPAIRED",
                "objective_before":[0,4,0.255430466417,4.096682479455,2026],
                "objective_after":[0,3,0.255430466417,4.096682479455,2016],
            }
        }
        territorial=build_production_status(
            territory_id="castilla_y_leon",params="fixture.yaml",run_id="production-123-1",
            from_stage="M05",to_stage="M06",execution_outcome="success",
            geometric_outcome="success",geometric_decision="PASS",
            m05_report=report,geometric_audit=geometry(),
        )
        self.assertEqual(territorial["decision"],"BLOCK")  # compatibilidad
        self.assertEqual(territorial["territorial_certification_status"],"BLOCK")
        self.assertEqual(territorial["block_cause"],"POPULATION_TARGET_NOT_MET")

        with tempfile.TemporaryDirectory() as td:
            root=Path(td)/"production"; root.mkdir()
            (root/"production_status.json").write_text(json.dumps(territorial),encoding="utf-8")
            registry=Path(td)/"viewer-results.json"
            registry.write_text(json.dumps({"results":[{
                "kind":"canonical_m06","run_id":"123","territory_id":"castilla_y_leon",
                "viewer_path":"data/results/m06-123.geojson"
            }]}),encoding="utf-8")
            deployment=evaluate_publication(
                requested_run_id="123",production_root=root,registry_path=registry,
                viewer_url="https://example.test/visor/",deployment_outcome="success",phase="final",
            )
        self.assertEqual(deployment["status"],"SUCCESS")  # compatibilidad
        self.assertEqual(deployment["deployment_status"],"SUCCESS")
        self.assertEqual(territorial["territorial_certification_status"],"BLOCK")

    def test_legacy_fields_remain(self):
        report={"objective_start":[0,0,0,0.1,0.1],"objective_final":[0,0,0,0.1,0.1],
                "population_repair":{"enabled":False}}
        territorial=build_production_status(
            territory_id="fixture",params="fixture.yaml",run_id="production-1-1",
            from_stage="M05",to_stage="M06",execution_outcome="success",
            geometric_outcome="success",geometric_decision="PASS",
            m05_report=report,geometric_audit=geometry(),
        )
        self.assertIn("decision",territorial)
        deployment=evaluate_publication(requested_run_id="",phase="final")
        self.assertIn("status",deployment)
        self.assertIn("deployment_outcome",deployment)

if __name__=="__main__": unittest.main()
