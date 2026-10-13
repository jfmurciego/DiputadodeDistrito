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
        self.assertEqual(x["termination_reason"],"TARGET_TOLERANCE_REPAIRED")

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

    def test_focal_allows_preparatory_move_between_conforming_districts(self):
        # A está bajo suelo. x no puede pasar inicialmente B→A porque articula B.
        # El paso previo y(C→B) ocurre entre distritos inicialmente conformes y crea
        # una ruta alternativa que permite mover x sin romper contigüidad.
        units={
            "a":U(40),
            "x":U(20),"b1":U(40),"b2":U(40),
            "y":U(10),"c":U(90),
        }
        ass={"a":"A","x":"B","b1":"B","b2":"B","y":"C","c":"C"}
        adj=A(
            ("a","x"),("x","b1"),("x","b2"),
            ("y","c"),("y","b1"),("y","b2"),
        )
        baseline_check=r.verify_partition_constraints(ass,units,adj,floor=50,cap=150)
        self.assertTrue(baseline_check["valid"])
        self.assertEqual(set(ass.values()), {"A","B","C"})
        x=self.repair_case(
            ass,units,adj,
            limits=r.SearchLimits(max_depth=0,max_transfer_set=1,max_candidates=200,max_seconds=2,seed=5),
        )
        final_check=r.verify_partition_constraints(x["assignments"],units,adj,floor=50,cap=150)
        self.assertTrue(final_check["valid"])
        self.assertEqual(set(x["assignments"].values()), set(ass.values()))
        self.assertTrue(x["hard_limits_met"])
        self.assertEqual(x["final_hard_population_violations"],0)
        self.assertGreaterEqual(len(x["repairs"]),2)
        self.assertEqual(x["repairs"][0]["donor"],"C")
        self.assertEqual(x["repairs"][0]["receiver"],"B")
        self.assertTrue(90 <= x["population_before"]["B"] <= 110)
        self.assertTrue(90 <= x["population_before"]["C"] <= 110)
        self.assertTrue(x["controlled_improvement_verified"])

    def test_hard_repair_stops_at_zero_hard_even_with_soft_outlier_remaining(self):
        # A empieza bajo suelo. El único movimiento reparador lleva A y B a
        # suelo/techo válidos, mientras C queda fuera de la banda objetivo.
        # La reparación dura debe detenerse ahí: C no es una infracción dura.
        units={"a":U(40),"x":U(50),"b":U(100),"c":U(140)}
        ass={"a":"A","x":"B","b":"B","c":"C"}
        adj=A(("a","x"),("x","b"))
        x=self.repair_case(
            ass,units,adj,
            limits=r.SearchLimits(max_depth=0,max_transfer_set=1,max_candidates=50,max_seconds=2,seed=13),
        )
        self.assertTrue(x["hard_limits_met"])
        self.assertEqual(x["final_hard_population_violations"],0)
        self.assertTrue(x["focal_search"]["complete"])
        self.assertEqual(x["focal_search"]["completion_target"],"HARD_POPULATION_LIMITS")
        self.assertEqual(x["termination_reason"],"HARD_LIMITS_REPAIRED")
        self.assertEqual(len(x["repairs"]),1)
        self.assertEqual(x["population_after"]["A"],90)
        self.assertEqual(x["population_after"]["B"],100)
        self.assertEqual(x["population_after"]["C"],140)
        self.assertGreater(x["objective_after"][1],0)
        self.assertIn("C", r._outliers(x["population_after"],100,10))

    def test_hard_population_repair_can_require_multiple_controlled_moves(self):
        units={
            "a":U(40),
            "x1":U(10),"x2":U(10),
            "x3":U(10),"x4":U(10),"x5":U(10),
            "b":U(120),
        }
        ass={"a":"A", **{u:"B" for u in ("x1","x2","x3","x4","x5","b")}}
        adj=A(("a","x1"),("x1","x2"),("x2","x3"),("x3","x4"),("x4","x5"),("x5","b"))
        x=self.repair_case(
            ass,units,adj,
            limits=r.SearchLimits(max_depth=2,max_transfer_set=1,max_candidates=200,max_seconds=2,seed=11),
        )
        self.assertTrue(x["hard_limits_met"])
        self.assertEqual(x["final_hard_population_violations"],0)
        self.assertGreaterEqual(len(x["repairs"]),2)
        self.assertTrue(x["controlled_improvement_verified"])
        self.assertEqual(x["primary_candidate_budget"],50)
        self.assertGreaterEqual(
            x["primary_transitions_evaluated"],
            x["primary_candidates_examined"],
        )
        self.assertGreaterEqual(
            x["transitions_evaluated"],
            x["candidates_examined"],
        )
        self.assertIn("PROVINCE",x["constraints_verified"])
        self.assertIn("CONTIGUITY",x["constraints_verified"])
        self.assertIn("ATOMIC_UNITS",x["constraints_verified"])
        self.assertIn("MUNICIPAL_INTEGRITY",x["constraints_verified"])
        self.assertIn("HARD_POPULATION_LIMITS_FINAL",x["constraints_verified"])
        signatures=[tuple(step["hard_signature_after"]) for step in x["repairs"]]
        previous=r._hard_population_signature(x["population_before"],floor=50,cap=150)
        for signature in signatures:
            self.assertLessEqual(signature,previous)
            previous=signature
        self.assertLess(
            x["final_hard_violation_magnitude"],
            r._hard_population_signature(x["population_before"],floor=50,cap=150)[1],
        )

    def test_district_floor_override_exempts_only_floor_not_ceiling(self):
        units={
            "a":U(40),
            "b":U(100),
        }
        assignments={"a":"A","b":"B"}
        adjacency=A(("a","b"))

        governed=r.verify_partition_constraints(
            assignments,
            units,
            adjacency,
            floor=50,
            cap=150,
            district_floors={"A":0.0,"B":50.0},
        )
        self.assertTrue(governed["valid"])
        self.assertTrue(governed["hard_limits_met"])
        self.assertEqual(governed["hard_population_violations"],0)

        units_over={
            "a":U(160),
            "b":U(100),
        }
        ceiling=r.verify_partition_constraints(
            assignments,
            units_over,
            adjacency,
            floor=50,
            cap=150,
            district_floors={"A":0.0,"B":50.0},
        )
        self.assertTrue(ceiling["valid"])
        self.assertFalse(ceiling["hard_limits_met"])
        self.assertEqual(ceiling["hard_population_violations"],1)
        self.assertEqual(ceiling["hard_violation_magnitude"],10)

    def test_repair_uses_effective_floor_in_hard_signature_and_evidence(self):
        units={
            "a":U(40),
            "b":U(100),
        }
        assignments={"a":"A","b":"B"}
        x=r.repair(
            assignments=assignments,
            units=units,
            adjacency=A(("a","b")),
            target=100,
            tolerance=10,
            floor=50,
            cap=150,
            district_floors={"A":0.0,"B":50.0},
            limits=r.SearchLimits(
                max_depth=1,
                max_transfer_set=1,
                max_candidates=10,
                max_seconds=1,
                seed=0,
            ),
        )
        self.assertEqual(x["hard_signature_before"],[0,0])
        self.assertEqual(x["hard_signature_after"],[0,0])
        self.assertEqual(x["hard_population_floor"],50.0)
        self.assertEqual(x["hard_population_cap"],150.0)
        self.assertEqual(x["district_floor_overrides"],{"A":0.0})
        self.assertTrue(x["hard_limits_met"])

    def test_durable_objective_vector_stays_five_dimensional_and_hard_signature_is_explicit(self):
        units={"a":U(40),"x":U(50),"b":U(100),"c":U(140)}
        ass={"a":"A","x":"B","b":"B","c":"C"}
        adj=A(("a","x"),("x","b"))
        x=self.repair_case(
            ass,units,adj,
            limits=r.SearchLimits(max_depth=0,max_transfer_set=1,max_candidates=50,max_seconds=2,seed=13),
        )
        self.assertEqual(x["schema"],"ddd.m05-population-repair/1.6")
        self.assertEqual(
            x["objective_hierarchy"],
            ["hard_violation_count","outliers","max_deviation","total_deviation","cohesion"],
        )
        self.assertEqual(len(x["objective_before"]),5)
        self.assertEqual(len(x["objective_after"]),5)
        self.assertEqual(x["objective_before"][0],x["hard_signature_before"][0])
        self.assertEqual(x["objective_after"][0],x["hard_signature_after"][0])
        self.assertEqual(
            x["hard_violation_magnitude_before"],
            x["hard_signature_before"][1],
        )
        self.assertEqual(
            x["hard_violation_magnitude_after"],
            x["hard_signature_after"][1],
        )
        self.assertEqual(
            x["final_hard_violation_magnitude"],
            x["hard_signature_after"][1],
        )

    def test_unsolved_hard_population_case_is_preserved_and_reported(self):
        units={
            "a":U(40),
            "b1":U(80,group="municipio-indivisible"),
            "b2":U(80,group="municipio-indivisible"),
        }
        ass={"a":"A","b1":"B","b2":"B"}
        x=self.repair_case(
            ass,units,A(("a","b1"),("b1","b2")),
            limits=r.SearchLimits(max_depth=4,max_transfer_set=1,max_candidates=100,max_seconds=2,seed=3),
        )
        self.assertEqual(x["result"],r.RESULT_NONE)
        self.assertFalse(x["hard_limits_met"])
        self.assertEqual(x["assignments"],ass)
        self.assertGreater(x["final_hard_population_violations"],0)
        self.assertIn("HARD_POPULATION_LIMITS_FINAL",x["constraints_checked"])
        self.assertNotIn("HARD_POPULATION_LIMITS_FINAL",x["constraints_verified"])
        self.assertGreater(x["rejection_classification"]["municipal_integrity"],0)

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
        self.assertGreaterEqual(
            x["focal_search"]["transitions_evaluated"],
            x["focal_search"]["candidate_attempts"],
        )

    def test_total_time_budget_includes_focal_phase_on_large_case(self):
        units={}; ass={}; edges=[]
        for d in ("A","B","C","D"):
            for i in range(50):
                u=f"{d}{i:02d}"; units[u]=U(2); ass[u]=d
                if i: edges.append((f"{d}{i-1:02d}",u))
        # Fuerza dos outliers sin una reparación trivial.
        for i in range(12): units[f"A{i:02d}"]["population"]=1
        for i in range(12): units[f"D{i:02d}"]["population"]=3
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
        self.assertEqual(x["primary_candidate_budget"],1)
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


class CongressMunicipalPolicyTests(unittest.TestCase):
    policy = r.MUNICIPAL_POLICY_N08

    def cusec_units(self, populations=(100, 100, 100, 100), groups=("39001", "39001", "39001", "39002")):
        ids = ("3900101001", "3900101002", "3900101003", "3900201001")
        return {
            ident: {"population": population, "province": ident[:2],
                    "municipality_group": group, "CPRO": ident[:2], "CUMUN": ident[:5]}
            for ident, population, group in zip(ids, populations, groups)
        }

    def test_under_cap_municipality_stays_whole_and_split_is_rejected(self):
        ids = ("3900101001", "3900101002", "3900201001")
        units = {
            ids[0]: {"population": 60, "province": "39", "municipality_group": "39001", "CPRO": "39", "CUMUN": "39001"},
            ids[1]: {"population": 60, "province": "39", "municipality_group": "39001", "CPRO": "39", "CUMUN": "39001"},
            ids[2]: {"population": 100, "province": "39", "municipality_group": "39002", "CPRO": "39", "CUMUN": "39002"},
        }
        adjacency = {ids[0]: {ids[1]}, ids[1]: {ids[0], ids[2]}, ids[2]: {ids[1]}}
        whole = {ids[0]: "A", ids[1]: "A", ids[2]: "B"}
        checked = r.verify_partition_constraints(whole, units, adjacency, floor=50, cap=200,
                                                 municipality_policy=self.policy)
        self.assertTrue(checked["valid"])
        self.assertEqual(checked["municipality_splits"], [])
        split = {ids[0]: "A", ids[1]: "B", ids[2]: "B"}
        checked = r.verify_partition_constraints(split, units, adjacency, floor=50, cap=200,
                                                 municipality_policy=self.policy)
        self.assertEqual(checked["reason"], "MUNICIPAL_SPLIT_NOT_MINIMAL")
        self.assertEqual(checked["topology_check"]["smaller_feasible_count"], 1)

    def test_necessary_split_is_limited_to_whole_cusec_and_audited(self):
        units = self.cusec_units()
        ids = tuple(units)
        adjacency = {ids[0]: {ids[1]}, ids[1]: {ids[0], ids[2]},
                     ids[2]: {ids[1], ids[3]}, ids[3]: {ids[2]}}
        state = {ids[0]: "A", ids[1]: "A", ids[2]: "B", ids[3]: "B"}
        checked = r.verify_partition_constraints(state, units, adjacency, floor=100, cap=200,
                                                 municipality_policy=self.policy)
        self.assertTrue(checked["valid"])
        self.assertTrue(checked["hard_limits_met"])
        self.assertEqual(checked["municipality_splits"][0]["necessity"],
                         "MINIMUM_DISTRICT_COUNT_REQUIRED_BY_HARD_POPULATION_CAP")
        self.assertEqual(checked["municipality_splits"][0]["cusecs"], list(ids[:3]))
        overfragmented = {ids[0]: "A", ids[1]: "B", ids[2]: "C", ids[3]: "C"}
        rejected = r.verify_partition_constraints(overfragmented, units, adjacency, floor=1, cap=200,
                                                  municipality_policy=self.policy)
        self.assertEqual(rejected["reason"], "MUNICIPAL_SPLIT_NOT_MINIMAL")
        self.assertEqual(rejected["topology_check"]["smaller_feasible_count"], 2)
        broken = dict(units)
        broken[ids[0]] = {**units[ids[0]], "CUMUN": "39002"}
        with self.assertRaisesRegex(ValueError, "MUNICIPAL_CUT_REQUIRES_WHOLE_CUSEC"):
            r.verify_partition_constraints(state, broken, adjacency, floor=100, cap=200,
                                           municipality_policy=self.policy)

    def test_split_that_disconnects_district_remains_rejected(self):
        units = self.cusec_units()
        ids = tuple(units)
        adjacency = {ids[0]: {ids[1]}, ids[1]: {ids[0], ids[2]},
                     ids[2]: {ids[1], ids[3]}, ids[3]: {ids[2]}}
        state = {ids[0]: "A", ids[1]: "B", ids[2]: "A", ids[3]: "B"}
        result = r.verify_partition_constraints(state, units, adjacency, floor=1, cap=500,
                                                municipality_policy=self.policy)
        self.assertEqual(result["reason"], "DISTRICT_CONTIGUITY")

    def test_topology_and_population_bounds_can_require_split_below_municipal_cap(self):
        ids = ("3900101001", "3900201001", "3900101002", "3900301001")
        units = {
            ident: {"population": 40, "province": "39", "municipality_group": ident[:5],
                    "CPRO": "39", "CUMUN": ident[:5]}
            for ident in ids
        }
        adjacency = {ids[0]: {ids[1]}, ids[1]: {ids[0], ids[2]},
                     ids[2]: {ids[1], ids[3]}, ids[3]: {ids[2]}}
        state = {ids[0]: "D1", ids[1]: "D1", ids[2]: "D2", ids[3]: "D2"}
        checked = r.verify_partition_constraints(state, units, adjacency, floor=80, cap=80,
                                                 municipality_policy=self.policy)
        self.assertTrue(checked["valid"])
        self.assertTrue(checked["hard_limits_met"])
        split = next(row for row in checked["municipality_splits"]
                     if row["municipality_group"] == "39001")
        self.assertEqual(split["population"], 80)  # P_municipio <= cap
        self.assertEqual(split["districts_used"], 2)
        self.assertEqual(split["necessity"],
                         "MINIMUM_DISTRICT_COUNT_REQUIRED_BY_TOPOLOGY_AND_POPULATION_BOUNDS")
        self.assertEqual(split["topology_certificate"]["certificate"],
                         "NO_FEASIBLE_LOWER_COUNT_PRESERVING_CONNECTIVITY_AND_POPULATION_BOUNDS")
        repaired = r.repair(
            assignments=state, units=units, adjacency=adjacency,
            target=80, tolerance=0, floor=80, cap=80,
            municipality_policy=self.policy,
            limits=r.SearchLimits(max_depth=1, max_transfer_set=1,
                                  max_candidates=30, max_seconds=1, seed=0),
        )
        self.assertTrue(repaired["constraints_verified"])
        self.assertTrue(repaired["hard_limits_met"])
        self.assertEqual(repaired["assignments"], state)

    def test_topology_minimality_search_exhaustion_is_not_proof(self):
        units = self.cusec_units()
        ids = tuple(units)
        adjacency = {ids[0]: {ids[1]}, ids[1]: {ids[0], ids[2]},
                     ids[2]: {ids[1], ids[3]}, ids[3]: {ids[2]}}
        state = {ids[0]: "A", ids[1]: "A", ids[2]: "B", ids[3]: "B"}
        result = r._topological_municipal_minimum(
            "39001", state, units, adjacency, floor=100, cap=200, node_budget=1,
        )
        self.assertTrue(result["search_exhausted"])
        self.assertFalse(result["proven"])

    def test_population_repair_creates_only_needed_municipal_split(self):
        units = self.cusec_units()
        ids = tuple(units)
        adjacency = {ids[0]: {ids[1]}, ids[1]: {ids[0], ids[2]},
                     ids[2]: {ids[1], ids[3]}, ids[3]: {ids[2]}}
        assignments = {ids[0]: "A", ids[1]: "A", ids[2]: "A", ids[3]: "B"}
        result = r.repair(assignments=assignments, units=units, adjacency=adjacency,
                          target=150, tolerance=50, floor=100, cap=200,
                          municipality_policy=self.policy,
                          limits=r.SearchLimits(max_depth=2, max_transfer_set=1,
                                                max_candidates=100, max_seconds=2, seed=0))
        self.assertEqual(result["result"], r.RESULT_REPAIRED)
        self.assertEqual(result["schema"], "ddd.m05-population-repair/1.8")
        self.assertTrue(result["hard_limits_met"])
        self.assertEqual(result["municipality_splits"][0]["municipality_group"], "39001")
        self.assertEqual(result["municipality_splits"][0]["necessity"],
                         "MINIMUM_DISTRICT_COUNT_REQUIRED_BY_HARD_POPULATION_CAP")

    def test_repair_can_build_minimum_three_district_split_through_valid_intermediate_state(self):
        ids = tuple(f"390010100{i}" for i in range(1, 7))
        units = {ident: {"population": 80, "province": "39", "municipality_group": "39001",
                         "CPRO": "39", "CUMUN": "39001"} for ident in ids}
        units.update({
            "3900201001": {"population": 20, "province": "39", "municipality_group": "39002",
                            "CPRO": "39", "CUMUN": "39002"},
            "3900301001": {"population": 20, "province": "39", "municipality_group": "39003",
                            "CPRO": "39", "CUMUN": "39003"},
        })
        adjacency = {ident: set() for ident in units}
        for left, right in zip(ids, ids[1:]):
            adjacency[left].add(right); adjacency[right].add(left)
        for left, right in ((ids[1], "3900201001"), (ids[4], "3900301001")):
            adjacency[left].add(right); adjacency[right].add(left)
        assignments = {ident: "A" for ident in ids}
        assignments.update({"3900201001": "B", "3900301001": "C"})
        result = r.repair(assignments=assignments, units=units, adjacency=adjacency,
                          target=200, tolerance=50, floor=100, cap=200,
                          municipality_policy=self.policy,
                          limits=r.SearchLimits(max_depth=4, max_transfer_set=2,
                                                max_candidates=1000, max_seconds=3, seed=0))
        self.assertEqual(result["result"], r.RESULT_REPAIRED)
        self.assertTrue(result["hard_limits_met"])
        self.assertEqual(result["municipality_splits"][0]["minimum_districts_by_population"], 3)
        self.assertEqual(result["municipality_splits"][0]["districts_used"], 3)

    def test_national_mode_does_not_weaken_autonomous_default_or_population_gate(self):
        units = self.cusec_units()
        ids = tuple(units)
        adjacency = {ids[0]: {ids[1]}, ids[1]: {ids[0], ids[2]},
                     ids[2]: {ids[1], ids[3]}, ids[3]: {ids[2]}}
        split = {ids[0]: "A", ids[1]: "B", ids[2]: "C", ids[3]: "C"}
        self.assertEqual(r.verify_partition_constraints(split, units, adjacency, floor=100, cap=200)["reason"],
                         "MUNICIPAL_INTEGRITY")
        over = dict(units)
        over[ids[0]] = {**units[ids[0]], "population": 210}
        checked = r.verify_partition_constraints(split, over, adjacency, floor=100, cap=200,
                                                 municipality_policy=self.policy)
        self.assertTrue(checked["valid"])
        self.assertFalse(checked["hard_limits_met"])


if __name__=="__main__": unittest.main()
