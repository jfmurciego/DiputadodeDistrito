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
