import unittest
from unittest.mock import patch
from pathlib import Path
from ddd_core import m05_population_repair as r


def U(pop, province="P", group=None): return {"population":pop,"province":province,"municipality_group":group}
def A(*edges):
    out={}
    for x,y in edges: out.setdefault(x,set()).add(y); out.setdefault(y,set()).add(x)
    return out


class PopulationRepairTests(unittest.TestCase):
    def repair_case(self,assignments,units,adj,**kw):
        return r.repair(assignments=assignments,units=units,adjacency=adj,target=100,tolerance=10,floor=50,cap=150,
            limits=kw.pop("limits",r.SearchLimits(max_depth=4,max_transfer_set=2,max_candidates=1000,max_seconds=2,seed=7)),**kw)

    def test_zero_outliers_is_repaired_when_primary_candidate_found(self):
        units={"a1":U(40),"a2":U(40),"b1":U(20),"b2":U(100)}; ass={"a1":"A","a2":"A","b1":"B","b2":"B"}
        x=self.repair_case(ass,units,A(("a1","a2"),("a2","b1"),("b1","b2")))
        self.assertEqual(x["result"],r.RESULT_REPAIRED); self.assertEqual(x["objective_after"][1],0)

    def test_secondary_total_deviation_only_restores_baseline(self):
        # A=80, B=120, C=130; mover 5 reduce totaldev pero C fija maxdev en 30%.
        units={"a":U(80),"x":U(5),"b":U(115),"c":U(130)}; ass={"a":"A","x":"B","b":"B","c":"C"}; adj=A(("a","x"),("x","b"))
        x=self.repair_case(ass,units,adj,limits=r.SearchLimits(max_depth=1,max_transfer_set=1,max_candidates=20,max_seconds=2,seed=1))
        self.assertEqual(x["result"],r.RESULT_NONE); self.assertTrue(x["baseline_restored"]); self.assertEqual(x["assignments"],ass)
        self.assertGreaterEqual(x["secondary_only_candidates"],1)

    def test_four_to_three_outliers_is_improved(self):
        units={"a":U(80),"x":U(20),"b":U(100),"c":U(80),"d":U(120),"e":U(120)}
        ass={"a":"A","x":"B","b":"B","c":"C","d":"D","e":"E"}; adj=A(("a","x"),("x","b"),("b","c"),("c","d"),("d","e"))
        x=self.repair_case(ass,units,adj,limits=r.SearchLimits(max_depth=1,max_transfer_set=1,max_candidates=100,max_seconds=2,seed=1))
        self.assertEqual(x["result"],r.RESULT_IMPROVED); self.assertLess(x["objective_after"][1],x["objective_before"][1])

    def test_same_outliers_lower_maxdev_is_improved(self):
        units={"a":U(70),"x":U(10),"b":U(120)}; ass={"a":"A","x":"B","b":"B"}; adj=A(("a","x"),("x","b"))
        x=self.repair_case(ass,units,adj,limits=r.SearchLimits(max_depth=1,max_transfer_set=1,max_candidates=20,max_seconds=2,seed=1))
        self.assertEqual(x["result"],r.RESULT_IMPROVED); self.assertEqual(x["objective_after"][1],x["objective_before"][1]); self.assertLess(x["objective_after"][2],x["objective_before"][2])

    def test_equal_primary_solution_chooses_better_cohesion(self):
        units={"a1":U(40),"a2":U(40),"b1":U(20),"b2":U(20),"bc1":U(40),"bc2":U(40)}; ass={u:("A" if u.startswith("a") else "B") for u in units}
        adj=A(("a1","a2"),("a2","b1"),("a2","b2"),("b1","bc1"),("b1","bc2"),("b2","bc1"),("bc1","bc2"))
        x=self.repair_case(ass,units,adj,limits=r.SearchLimits(max_depth=1,max_transfer_set=1,max_candidates=100,max_seconds=2,seed=3))
        self.assertEqual(x["result"],r.RESULT_REPAIRED); self.assertEqual(x["repairs"][0]["units"],["b2"])

    def test_equivalent_solution_prefers_lower_churn(self):
        p1=[{"units":["x"],"donor":"A","receiver":"B"}]; p2=[{"units":["x","y"],"donor":"A","receiver":"B"}]
        self.assertLess(r._churn(p1),r._churn(p2))

    def test_directed_search_ignores_many_irrelevant_districts(self):
        units={"a":U(80),"x":U(20),"b":U(100)}; ass={"a":"A","x":"B","b":"B"}; edges=[("a","x"),("x","b")]
        for i in range(30):
            u=f"z{i}"; units[u]=U(100); ass[u]=f"Z{i}"
            if i: edges.append((f"z{i-1}",u))
        x=self.repair_case(ass,units,A(*edges),limits=r.SearchLimits(max_depth=1,max_transfer_set=1,max_candidates=10,max_seconds=2,seed=1))
        self.assertEqual(x["result"],r.RESULT_REPAIRED); self.assertLessEqual(x["candidates_examined"],10)

    def test_three_district_preparatory_chain(self):
        units={"a":U(80),"b1":U(80),"b2":U(20),"c1":U(20),"c2":U(100)}; ass={"a":"A","b1":"B","b2":"B","c1":"C","c2":"C"}
        x=self.repair_case(ass,units,A(("a","b2"),("b2","b1"),("b1","c1"),("c1","c2")))
        self.assertEqual(x["result"],r.RESULT_REPAIRED); self.assertGreaterEqual(len(set(x["districts_affected"])),3)

    def test_focal_chain_repairs_low_outlier_by_handoff(self):
        units={"a":U(89),"bx":U(2),"b":U(89),"cy":U(2),"c":U(98)}
        ass={"a":"A","bx":"B","b":"B","cy":"C","c":"C"}
        adj=A(("a","bx"),("bx","b"),("b","cy"),("cy","c"))
        x=self.repair_case(ass,units,adj,limits=r.SearchLimits(max_depth=1,max_transfer_set=1,max_candidates=20,max_seconds=2,seed=1))
        self.assertEqual(x["result"],r.RESULT_REPAIRED)
        self.assertEqual(x["objective_after"][1],0)
        self.assertTrue(x["focal_search"]["complete"])
        self.assertGreaterEqual(len(x["repairs"]),2)

    def test_focal_chain_repairs_oversized_donor_with_cycle(self):
        units={"a":U(95),"x":U(30),"b":U(80),"y":U(25),"c":U(85),"z":U(10)}
        ass={"a":"A","x":"A","b":"B","y":"B","c":"C","z":"C"}
        adj=A(("a","x"),("x","b"),("b","y"),("y","c"),("c","z"),("z","a"))
        x=self.repair_case(ass,units,adj,limits=r.SearchLimits(max_depth=1,max_transfer_set=1,max_candidates=20,max_seconds=2,seed=2))
        self.assertEqual(x["result"],r.RESULT_REPAIRED)
        self.assertEqual(x["objective_after"][1],0)
        self.assertTrue(x["focal_search"]["complete"])
        self.assertGreaterEqual(len(x["repairs"]),3)

    def test_focal_chain_supports_transit_near_population_cap(self):
        units={"a":U(110),"r":U(1),"b":U(108),"q":U(1),"c":U(109),"d":U(107),"t":U(2)}
        ass={"a":"A","r":"A","b":"B","q":"B","c":"C","d":"D","t":"D"}
        adj=A(("a","r"),("r","d"),("a","t"),("t","d"),("t","b"),("b","q"),("q","c"))
        x=self.repair_case(ass,units,adj,limits=r.SearchLimits(max_depth=1,max_transfer_set=1,max_candidates=20,max_seconds=2,seed=3))
        self.assertEqual(x["result"],r.RESULT_REPAIRED)
        self.assertEqual(x["objective_after"][1],0)
        self.assertTrue(x["focal_search"]["complete"])
        pops=x["population_after"]
        self.assertTrue(all(90 <= pops[d] <= 110 for d in ("A","B","C","D")))

    def test_global_candidate_budget_caps_primary_plus_focal_on_large_case(self):
        units={}; ass={}; edges=[]
        # Cuatro distritos, 160 unidades: A queda bajo tolerancia y D alto.
        for d,base in (("A",39),("B",40),("C",40),("D",41)):
            for i in range(40):
                u=f"{d}{i:02d}"; units[u]=U(2); ass[u]=d
                if i: edges.append((f"{d}{i-1:02d}",u))
        edges += [("A39","B00"),("B39","C00"),("C39","D00")]
        x=self.repair_case(
            ass,units,A(*edges),
            limits=r.SearchLimits(max_depth=1,max_transfer_set=1,max_candidates=50,max_seconds=10,seed=1),
        )
        self.assertLessEqual(x["candidates_examined"],50)
        self.assertLessEqual(
            x["primary_candidates_examined"] + x["focal_search"]["candidate_attempts"],
            50,
        )
        self.assertEqual(x["focal_search"]["candidate_budget"],50-x["primary_candidates_examined"])

    def test_total_time_budget_includes_focal_phase_on_large_case(self):
        units={}; ass={}; edges=[]
        for d in ("A","B","C","D"):
            for i in range(50):
                u=f"{d}{i:02d}"; units[u]=U(2); ass[u]=d
                if i: edges.append((f"{d}{i-1:02d}",u))
        # Fuerza dos outliers sin una reparación trivial.
        for i in range(10): units[f"A{i:02d}"]["population"]=1
        for i in range(10): units[f"D{i:02d}"]["population"]=3
        edges += [("A49","B00"),("B49","C00"),("C49","D00")]
        ticks=[i*0.01 for i in range(1000)]
        with patch.object(r.time,"monotonic",side_effect=ticks):
            x=self.repair_case(
                ass,units,A(*edges),
                limits=r.SearchLimits(max_depth=0,max_transfer_set=1,max_candidates=10000,max_seconds=0.08,seed=1),
            )
        self.assertEqual(x["termination_reason"],"TIME_BUDGET_EXHAUSTED")
        self.assertGreater(x["focal_search"]["elapsed_seconds"],0)
        self.assertGreaterEqual(x["elapsed_seconds"],x["focal_search"]["elapsed_seconds"])
        self.assertLessEqual(x["candidates_examined"],10000)

    def test_budget_exhausted_without_primary_restores_baseline(self):
        units={"a":U(80),"b":U(120)}; ass={"a":"A","b":"B"}
        x=self.repair_case(ass,units,A(("a","b")),limits=r.SearchLimits(max_depth=1,max_transfer_set=1,max_candidates=1,max_seconds=2,seed=1))
        self.assertEqual(x["result"],r.RESULT_NONE); self.assertTrue(x["baseline_restored"]); self.assertEqual(x["assignments"],ass)
        self.assertIn(x["termination_reason"],{"CANDIDATE_BUDGET_EXHAUSTED","QUEUE_EMPTY"})

    def test_deterministic_same_seed(self):
        units={"a1":U(40),"a2":U(40),"b1":U(20),"b2":U(100)}; ass={"a1":"A","a2":"A","b1":"B","b2":"B"}; adj=A(("a1","a2"),("a2","b1"),("b1","b2"))
        a=self.repair_case(ass,units,adj); b=self.repair_case(ass,units,adj)
        for x in (a,b): x.pop("elapsed_seconds",None)
        self.assertEqual(a,b)

    def test_no_territorial_literals(self):
        text=Path(r.__file__).read_text(encoding="utf-8").lower()
        for literal in ("castilla","león","leon","aragon","aragón","35155371295","82"):
            self.assertNotIn(literal,text)

    def test_synthetic_m04_to_m05_contract(self):
        units={"m04-a":U(80),"m04-x":U(20),"m04-b":U(100)}; ass={"m04-a":"A","m04-x":"B","m04-b":"B"}
        x=self.repair_case(ass,units,A(("m04-a","m04-x"),("m04-x","m04-b")))
        self.assertEqual(x["result"],r.RESULT_REPAIRED); self.assertEqual(set(x["assignments"]),set(ass)); self.assertTrue(x["constraints_verified"])


if __name__=="__main__": unittest.main()
