"""Versión 1.1.0; 2026-10-29; candidato. Reparación privada M05; añade la disciplina municipal (R012).
Anterior: legacy/tests/test_m05_private_annealing_v1.0.0_20261029.py
"""
import unittest

from ddd_core.m05_private_annealing import repair_private


def case():
    # A connected 10-unit chain; one legal boundary transfer resolves both hard limits.
    units={f"u{i}":{"population":20,"province":"01","municipality_group":None} for i in range(10)}
    assignment={f"u{i}":("A" if i < 7 else "B") for i in range(10)}
    adj={f"u{i}":set() for i in range(10)}
    for i in range(9):
        adj[f"u{i}"].add(f"u{i+1}"); adj[f"u{i+1}"].add(f"u{i}")
    return units,assignment,adj


class PrivateAnnealingTests(unittest.TestCase):
    def run_case(self, **kw):
        units,assignment,adj=case()
        args={"assignments":assignment,"units":units,"adjacency":adj,
            "target":100,"tolerance":12,"floor":80,"cap":120,"seed":17,
            "max_candidates":500,"max_seconds":2}
        args.update(kw)
        return repair_private(**args),assignment

    def test_repair_is_admitted_only_after_hard_zero(self):
        result,original=self.run_case()
        self.assertTrue(result["accepted"])
        self.assertEqual(result["final_validation"]["hard_population_violations"],0)
        self.assertGreaterEqual(result["accepted_steps_with_nonzero_hard"],0)
        self.assertGreaterEqual(result["max_private_hard_count"],1)
        self.assertGreater(result["max_private_violation"],0)
        self.assertEqual(set(result["assignments"]),set(original))

    def test_budget_exhaustion_is_atomic(self):
        result,original=self.run_case(max_candidates=1)
        self.assertFalse(result["accepted"])
        self.assertEqual(result["assignments"],original)
        self.assertEqual(original,{f"u{i}":("A" if i < 7 else "B") for i in range(10)})

    def test_deterministic_seed(self):
        a,_=self.run_case(); b,_=self.run_case()
        for result in (a,b): result.pop("elapsed_seconds",None)
        self.assertEqual(a,b)

    def test_invalid_input_rejected_without_mutation(self):
        units,assignment,adj=case(); before=dict(assignment)
        del units["u0"]
        result=repair_private(assignments=assignment,units=units,adjacency=adj,
            target=100,tolerance=12,floor=80,cap=120,seed=17,max_candidates=10,max_seconds=1)
        self.assertFalse(result["accepted"])
        self.assertEqual(result["assignments"],before)

    def test_timeout_is_atomic(self):
        result,original=self.run_case(max_seconds=1e-12)
        self.assertFalse(result["accepted"])
        self.assertEqual(result["termination_reason"],"TIME_BUDGET_EXHAUSTED")
        self.assertEqual(result["assignments"],original)

    def test_province_and_frozen_unit_rules(self):
        units,assignment,adj=case()
        units["u6"]["province"]="02"
        result=repair_private(assignments=assignment,units=units,adjacency=adj,
            target=100,tolerance=12,floor=80,cap=120,seed=17,max_candidates=1,max_seconds=1,
            frozen_units={"u6"})
        self.assertEqual(assignment["u6"],"A")
        if result["accepted"]:
            self.assertEqual(result["assignments"]["u6"],"A")


if __name__=="__main__": unittest.main()


class MunicipalDisciplineTests(unittest.TestCase):
    def test_counts_split_municipality_with_two_mixed_districts(self):
        from ddd_core.m05_private_annealing import _mixed_discipline_violations
        # Municipio 05019 partido en A (con 05001) y B (con 05002): dos distritos mixtos → 1 infracción.
        state={"05:05019:U1":"A","05:05019:U2":"B","05:05001:M":"A","05:05002:M":"B"}
        owned={"A":{"05:05019:U1","05:05001:M"},"B":{"05:05019:U2","05:05002:M"}}
        munis={"05019":{"05:05019:U1","05:05019:U2"},"05001":{"05:05001:M"},"05002":{"05:05002:M"}}
        self.assertEqual(1,_mixed_discipline_violations({"05019","05001","05002"},state,owned,munis))
        # Con B puro (sólo 05019), queda un único distrito mixto: válido.
        state2={**state,"05:05002:M":"A"}; owned2={"A":{"05:05019:U1","05:05001:M","05:05002:M"},"B":{"05:05019:U2"}}
        self.assertEqual(0,_mixed_discipline_violations({"05019","05001","05002"},state2,owned2,munis))
