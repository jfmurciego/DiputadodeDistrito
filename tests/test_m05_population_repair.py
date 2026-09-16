import inspect
import unittest
from ddd_core import m05_population_repair as r


def U(pop, province="P", group=None): return {"population":pop,"province":province,"municipality_group":group}
def A(*edges):
    out={}
    for x,y in edges: out.setdefault(x,set()).add(y); out.setdefault(y,set()).add(x)
    return out

class PopulationRepairTests(unittest.TestCase):
    def repair_case(self, assignments, units, adj, **kw):
        return r.repair(assignments=assignments,units=units,adjacency=adj,target=100,tolerance=10,floor=50,cap=150,limits=kw.pop("limits",r.SearchLimits(max_depth=4,max_transfer_set=2,max_candidates=1000,max_seconds=2,seed=7)),**kw)

    def test_simple_transfer_repairs(self):
        units={"a1":U(40),"a2":U(40),"b1":U(20),"b2":U(100)}; ass={"a1":"A","a2":"A","b1":"B","b2":"B"}
        x=self.repair_case(ass,units,A(("a1","a2"),("a2","b1"),("b1","b2")))
        self.assertEqual(x["result"],r.RESULT_REPAIRED); self.assertEqual(len(x["repairs"]),1)

    def test_exchange_requires_two_moves(self):
        # A=80, B=120. Ninguna transferencia simple alcanza tolerancia; el
        # intercambio 30 A->B seguido de 50 B->A deja 100/100. La arista
        # a2-b2 mantiene contiguo al donante B durante el estado intermedio.
        units={"a1":U(50),"a2":U(30),"b1":U(50),"b2":U(70)}; ass={"a1":"A","a2":"A","b1":"B","b2":"B"}
        x=self.repair_case(ass,units,A(("a1","a2"),("a2","b1"),("a1","b1"),("b1","b2"),("a2","b2")))
        self.assertEqual(x["result"],r.RESULT_REPAIRED); self.assertGreaterEqual(len(x["repairs"]),2)

    def test_three_district_chain(self):
        units={"a":U(80),"b1":U(80),"b2":U(20),"c1":U(20),"c2":U(100)}; ass={"a":"A","b1":"B","b2":"B","c1":"C","c2":"C"}
        adj=A(("a","b2"),("b2","b1"),("b1","c1"),("c1","c2"))
        x=self.repair_case(ass,units,adj)
        self.assertEqual(x["result"],r.RESULT_REPAIRED); self.assertGreaterEqual(len(set(x["districts_affected"])),3)

    def test_disconnect_donor_rejected(self):
        units={"x":U(40),"cut":U(20),"y":U(40),"z":U(100)}; ass={"x":"A","cut":"A","y":"A","z":"B"}
        x=self.repair_case(ass,units,A(("x","cut"),("cut","y"),("cut","z")),limits=r.SearchLimits(max_depth=1,max_transfer_set=1,max_candidates=50,max_seconds=1,seed=1))
        self.assertTrue(any(e["reason"]=="DONOR_CONTIGUITY" for e in x["rejections"]))

    def test_municipal_integrity_rejected(self):
        units={"m1":U(20,group="M"),"m2":U(60,group="M"),"b":U(120)}; ass={"m1":"A","m2":"A","b":"B"}
        x=self.repair_case(ass,units,A(("m1","m2"),("m1","b")),limits=r.SearchLimits(max_depth=1,max_transfer_set=1,max_candidates=20,max_seconds=1,seed=1))
        self.assertTrue(any(e["reason"]=="MUNICIPAL_INTEGRITY" for e in x["rejections"]))

    def test_no_solution_within_budget_is_not_impossibility(self):
        units={"a":U(80),"b":U(120)}; ass={"a":"A","b":"B"}
        x=self.repair_case(ass,units,A(("a","b")),limits=r.SearchLimits(max_depth=1,max_transfer_set=1,max_candidates=1,max_seconds=1,seed=1))
        self.assertEqual(x["result"],r.RESULT_NONE); self.assertNotIn("impossible",str(x).lower())

    def test_deterministic_same_seed(self):
        units={"a1":U(40),"a2":U(40),"b1":U(20),"b2":U(100)}; ass={"a1":"A","a2":"A","b1":"B","b2":"B"}; adj=A(("a1","a2"),("a2","b1"),("b1","b2"))
        self.assertEqual(self.repair_case(ass,units,adj),self.repair_case(ass,units,adj))

    def test_regression_monotonic_and_baseline_preserved(self):
        units={"a":U(100),"b":U(100)}; ass={"a":"A","b":"B"}; x=self.repair_case(ass,units,A(("a","b")))
        self.assertEqual(x["objective_after"],x["objective_before"]); self.assertTrue(x["baseline_preserved"])
        self.assertLessEqual(x["objective_after"][0],x["objective_before"][0]); self.assertLessEqual(x["objective_after"][1],x["objective_before"][1])

    def test_no_territorial_literals(self):
        text=inspect.getsource(r)
        forbidden=("Castilla y León","Aragón","Extremadura","Villanubla","Carbajosa","San Cristóbal","Piedrahíta")
        self.assertFalse(any(token in text for token in forbidden))

if __name__=="__main__": unittest.main()
