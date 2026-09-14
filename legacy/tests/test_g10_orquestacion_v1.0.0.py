#!/usr/bin/env python3
"""Pruebas del Marco G10 sin cómputo GIS."""
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from g10.core import (FailureClass, TaskStatus, aggregate_summaries,
                      classify_failure, compute_fingerprint, decide_admission,
                      loop_guard, retry_decision, validate_plan)


class G10Orquestacion(unittest.TestCase):
    def task(self):
        return {"task_id":"t1", "territory":"aragon", "stage":"M01-M06",
                "depends_on":[], "max_attempts":2, "timeout_minutes":120,
                "estimated_runner_minutes":30, "success_contract":"c.json",
                "action":"territory_m01_m06"}

    def plan(self):
        return {"schema_version":"1.0", "lot_id":"l1",
                "budget":{"runner_minutes":100,"max_parallel":4},
                "tasks":[self.task()]}

    def test_plan_valido_y_duplicado_rechazado(self):
        validate_plan(self.plan())
        plan=self.plan();plan["tasks"].append(dict(self.task()))
        with self.assertRaisesRegex(ValueError,"duplicado"):
            validate_plan(plan)

    def test_huella_determinista_y_sensible_al_contenido(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);(root/"a").write_text("uno",encoding="utf-8");(root/"b").write_text("dos",encoding="utf-8")
            first=compute_fingerprint(["a","b"],root=root,context={"x":1})
            self.assertEqual(first,compute_fingerprint(["b","a"],root=root,context={"x":1}))
            (root/"a").write_text("otro",encoding="utf-8")
            self.assertNotEqual(first,compute_fingerprint(["a","b"],root=root,context={"x":1}))

    def test_admision_reutiliza_y_respeta_presupuesto(self):
        task=self.task();fp="sha256:"+"a"*64
        reused=decide_admission(task,completed=set(),running_fingerprints=set(),successful_fingerprints={fp},fingerprint=fp,remaining_runner_minutes=100)
        self.assertEqual(reused.status,TaskStatus.REUSED)
        budget=decide_admission(task,completed=set(),running_fingerprints=set(),successful_fingerprints=set(),fingerprint=fp,remaining_runner_minutes=5)
        self.assertEqual(budget.status,TaskStatus.REJECTED_BUDGET)

    def test_clasificacion_y_reintento(self):
        failure=classify_failure(exit_code=1,log="503 Service Unavailable")
        self.assertEqual(failure,FailureClass.TRANSIENT_NETWORK)
        decision=retry_decision(failure,attempt=0,max_attempts=2,last_valid_checkpoint="M03")
        self.assertEqual(decision["decision"],"RETRY");self.assertEqual(decision["resume_from"],"M03")
        deterministic=retry_decision(FailureClass.REGRESSION,attempt=0,max_attempts=2,last_valid_checkpoint="M04")
        self.assertEqual(deterministic["decision"],"REQUIRES_AGENT")

    def test_antibucle(self):
        history=[{"fingerprint":"f","failure_class":"REGRESSION","decision":"PATCH_CODE"}]
        self.assertTrue(loop_guard(history,fingerprint="f",failure_class="REGRESSION",decision="PATCH_CODE"))
        self.assertFalse(loop_guard(history,fingerprint="otra",failure_class="REGRESSION",decision="PATCH_CODE"))

    def test_agregacion_no_oculta_fallos(self):
        result=aggregate_summaries([{"task_id":"b","status":"BLOCKED"},{"task_id":"a","status":"SUCCESS"}])
        self.assertEqual(result["counts"],{"BLOCKED":1,"SUCCESS":1})
        self.assertEqual([x["task_id"] for x in result["tasks"]],["a","b"])


if __name__=="__main__":
    unittest.main()
