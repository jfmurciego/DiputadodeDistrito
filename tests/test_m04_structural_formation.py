from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import pandas as pd

from ddd_core import m04_closed_target_cores as closed_target
from ddd_core import m04_seed_engine as engine

ROOT = Path(__file__).resolve().parents[1]
CLOSED_TARGET_FIXTURE = ROOT / "tests/fixtures/m04_closed_target_cores/la_rioja_run_37298033194.json"


class StructuralFormationTests(unittest.TestCase):
    def _real_closed_target_case(self, municipality_code):
        payload=json.loads(CLOSED_TARGET_FIXTURE.read_text(encoding="utf-8"))
        contract=payload["contract"]
        item=payload["municipalities"][municipality_code]
        node_ids=item["node_ids"]
        weights=dict(zip(node_ids,item["populations"]))
        adjacency={node:set() for node in node_ids}
        for left_index,right_index in item["internal_edges"]:
            left=node_ids[left_index]
            right=node_ids[right_index]
            adjacency[left].add(right)
            adjacency[right].add(left)
        gateways={node_ids[index] for index in item["gateway_indices"]}

        def unit_order(unit_id):
            if unit_id.endswith(":R"):
                return (1,999)
            return (0,int(unit_id.rsplit("U",1)[1]))

        unit_ids=sorted(item["initial_parts"],key=unit_order)
        parts=[
            {node_ids[index] for index in item["initial_parts"][unit_id]}
            for unit_id in unit_ids
        ]
        target=contract["territory_population"]/contract["k"]
        floor=target*contract["population_floor_ratio"]
        cap=target*contract["population_cap_ratio"]
        tolerance=target*contract["target_tolerance_ratio"]
        return {
            "weights":weights,
            "adjacency":adjacency,
            "gateways":gateways,
            "unit_ids":unit_ids,
            "closed":parts[:-1],
            "residual":parts[-1],
            "target":target,
            "floor":floor,
            "cap":cap,
            "tolerance":tolerance,
        }

    def test_explicit_component_gateway_preserves_unique_external_connection(self):
        municipality={"h1","h2","h3"}
        province_nodes=municipality | {"external"}
        adjacency={
            "h1":{"h2"},
            "h2":{"h1","h3","external"},
            "h3":{"h2"},
            "external":{"h2"},
        }
        self.assertEqual(
            engine._protected_component_gateways(
                municipality,province_nodes,adjacency
            ),
            {"h2"},
        )

    def test_dependent_gateway_does_not_overprotect_connected_exterior(self):
        municipality={"h1","h2","h3"}
        province_nodes=municipality | {"external"}
        adjacency={
            "h1":{"h2"},
            "h2":{"h1","h3","external"},
            "h3":{"h2"},
            "external":{"h2"},
        }
        self.assertEqual(
            engine._protected_component_gateways(
                municipality,province_nodes,adjacency,dependent_only=True
            ),
            set(),
        )

    def test_dependent_gateway_keeps_one_deterministic_gate_per_external_component(self):
        municipality={"m1","m2","m3","m4"}
        province_nodes=municipality | {"a1","a2","b1"}
        adjacency={
            "m1":{"m2","a1"},
            "m2":{"m1","m3","a1","a2"},
            "m3":{"m2","m4","b1"},
            "m4":{"m3","b1"},
            "a1":{"m1","m2","a2"},
            "a2":{"m2","a1"},
            "b1":{"m3","m4"},
        }
        protected=engine._protected_component_gateways(
            municipality,province_nodes,adjacency,dependent_only=True
        )
        self.assertEqual(len(protected),2)
        self.assertIn("m2",protected)
        self.assertIn("m3",protected)

    def test_la_rioja_haro_cut_keeps_brinas_gateway_from_real_run(self):
        # Certificado mínimo extraído de M03U del run 37161772942.
        # Al retirar Haro, Briñas (2603301001, 182 habitantes) queda como
        # componente exterior dependiente y sólo enlaza por 2607104002.
        haro={
            "2607101001","2607102001","2607102002","2607103001",
            "2607104001","2607104002","2607104003","2607104004",
        }
        brinas="2603301001"
        gimileo="2606801001"
        province_nodes=haro | {brinas,gimileo}
        adjacency={node:set() for node in province_nodes}
        edges=[
            ("2607101001","2607102002"),
            ("2607101001","2607103001"),
            ("2607101001","2607104002"),
            ("2607102001","2607102002"),
            ("2607102001","2607103001"),
            ("2607102001","2607104001"),
            ("2607102001","2607104003"),
            ("2607102001","2607104004"),
            ("2607102002","2607103001"),
            ("2607102002","2607104002"),
            ("2607102002","2607104004"),
            ("2607103001","2607104001"),
            ("2607103001","2607104002"),
            ("2607104001","2607104003"),
            ("2607104002","2607104004"),
            ("2607104003","2607104004"),
            ("2607104002",brinas),
            ("2607103001",gimileo),
            ("2607104001",gimileo),
        ]
        for left,right in edges:
            adjacency[left].add(right)
            adjacency[right].add(left)

        protected=engine._protected_component_gateways(
            haro,province_nodes,adjacency,dependent_only=True
        )
        self.assertIn("2607104002",protected)
        self.assertEqual(len(engine._components(province_nodes-haro,adjacency)),2)

        weights={
            "2607101001":685,
            "2607102001":2103,
            "2607102002":707,
            "2607103001":1503,
            "2607104001":2129,
            "2607104002":852,
            "2607104003":1729,
            "2607104004":2042,
        }
        target=322282/33
        floor=target*0.8
        cap=target*1.75
        tolerance=target*0.12
        cores,residual,_mode,_gateways=engine.partition_oversized_municipality(
            haro,target,floor,cap,tolerance,adjacency,weights,
            label="real-run-cut-certificate",protected=protected,
        )
        self.assertTrue(cores)
        self.assertTrue(protected <= residual)
        self.assertIn("2607104002",residual)
        self.assertTrue(engine.core.previous.connected(residual,adjacency))
        self.assertTrue(all(
            floor <= sum(weights[node] for node in core) <= cap
            for core in cores
        ))
        self.assertLessEqual(sum(weights[node] for node in residual),cap)

    def test_la_rioja_calahorra_allows_open_residual_below_floor(self):
        case=self._real_closed_target_case("26036")
        before=[
            sum(case["weights"][node] for node in part)
            for part in case["closed"]
        ]
        self.assertEqual(before,[7986,8797])

        cores,residual,evidence=closed_target.repair_closed_target_cores(
            case["closed"],
            case["residual"],
            target=case["target"],
            floor=case["floor"],
            cap=case["cap"],
            tolerance=case["tolerance"],
            adjacency=case["adjacency"],
            weights=case["weights"],
            residual_gateways=case["gateways"],
        )

        lo=case["target"]-case["tolerance"]
        hi=case["target"]+case["tolerance"]
        populations=[
            sum(case["weights"][node] for node in part)
            for part in cores
        ]
        residual_population=sum(case["weights"][node] for node in residual)
        self.assertEqual(evidence["strategy"],"exact_connected_target_cores")
        self.assertTrue(all(lo <= population <= hi for population in populations))
        self.assertLess(residual_population,case["floor"])
        self.assertLessEqual(residual_population,case["cap"])
        self.assertTrue(all(
            closed_target._connected(part,case["adjacency"])
            for part in cores
        ))
        self.assertTrue(closed_target._connected(residual,case["adjacency"]))
        self.assertTrue(residual & case["gateways"])
        self.assertEqual(
            set().union(*cores,residual),
            set().union(*case["closed"],case["residual"]),
        )
        self.assertEqual(len(cores),len(case["closed"]))

    def test_la_rioja_logrono_repairs_outlier_without_touching_residual(self):
        case=self._real_closed_target_case("26089")
        initial=[
            sum(case["weights"][node] for node in part)
            for part in case["closed"]
        ]
        self.assertEqual(initial[13],13425)
        original_residual=set(case["residual"])

        cores,residual,evidence=closed_target.repair_closed_target_cores(
            case["closed"],
            case["residual"],
            target=case["target"],
            floor=case["floor"],
            cap=case["cap"],
            tolerance=case["tolerance"],
            adjacency=case["adjacency"],
            weights=case["weights"],
            residual_gateways=case["gateways"],
        )

        populations=[
            sum(case["weights"][node] for node in part)
            for part in cores
        ]
        lo=case["target"]-case["tolerance"]
        hi=case["target"]+case["tolerance"]
        self.assertEqual(evidence["strategy"],"beam_core_only_focused")
        self.assertEqual(residual,original_residual)
        self.assertEqual(sum(case["weights"][node] for node in residual),10509)
        self.assertEqual(populations[4],10592)
        self.assertEqual(populations[11],10714)
        self.assertEqual(populations[13],10905)
        self.assertTrue(all(lo <= population <= hi for population in populations))
        self.assertTrue(all(
            closed_target._connected(part,case["adjacency"])
            for part in cores
        ))
        self.assertTrue(closed_target._connected(residual,case["adjacency"]))

    def test_closed_target_contract_fails_closed_instead_of_freezing_outlier(self):
        adjacency={"a":{"b"},"b":{"a"}}
        weights={"a":6,"b":6}
        with self.assertRaisesRegex(
            SystemExit,
            "CLOSED_CORE_TARGET_INCOMPATIBLE",
        ):
            closed_target.repair_closed_target_cores(
                [{"a"}],
                {"b"},
                target=10,
                floor=5,
                cap=20,
                tolerance=1,
                adjacency=adjacency,
                weights=weights,
                residual_gateways={"b"},
            )

    def test_closed_target_report_rejects_any_frozen_population_exception(self):
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/"m04.json"
            path.write_text(
                json.dumps({
                    "closed_core_population_exceptions":[
                        {"district_id":1,"population":7}
                    ]
                }),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(
                SystemExit,
                "CLOSED_CORE_TARGET_CONTRACT_BREACH",
            ):
                engine._assert_closed_target_report(path)

            path.write_text(
                json.dumps({"closed_core_population_exceptions":[]}),
                encoding="utf-8",
            )
            engine._assert_closed_target_report(path)
            report=json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(report["closed_core_target_contract"],"PASS")
            self.assertTrue(
                report["rules"]["closed_urban_requires_target_tolerance"]
            )

    def test_melilla_real_run_is_atomically_incompatible_before_search(self):
        # Poblaciones M03U del run 37148646551: 44 secciones, K=25.
        # Por cardinalidad, al menos 2*K-N = 6 distritos han de ser singleton.
        # Sólo dos secciones alcanzan el suelo 2735.776, por lo que ni siquiera
        # el modelo relajado (sin contigüidad ni disciplina municipal) es viable.
        populations=[
            1090,1939,1414,1553,2291,1199,1548,1776,2341,2407,2384,
            1833,1247,2843,1573,2005,2364,2013,1587,1631,1859,2491,
            2052,1950,2143,1949,1627,2617,1710,2974,1317,2063,2499,
            1946,1842,2369,1573,2027,1370,2549,2356,1605,1195,2372,
        ]
        nodes={f"s{i:02d}" for i in range(len(populations))}
        weights={node:pop for node,pop in zip(sorted(nodes),populations)}
        ok,reason,detail=engine._atomic_population_necessary_conditions(
            nodes,weights,k=25,floor=2735.776,cap=5984.51
        )
        self.assertFalse(ok)
        self.assertEqual(reason,"INSUFFICIENT_HARD_VALID_SINGLETONS")
        self.assertEqual(detail["nodes"],44)
        self.assertEqual(detail["required_singletons"],6)
        self.assertEqual(detail["hard_valid_singletons"],2)
        self.assertEqual(detail["population"],85493)

    def test_preflight_rejects_m03_geometry_universe_mismatch_explicitly(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            graph=root/"graph.json"
            graph.write_text(
                json.dumps({
                    "nodes":[{"id":"a","pop":10},{"id":"b","pop":10}],
                    "edges":[{"u":"a","v":"b"}],
                }),
                encoding="utf-8",
            )
            step={
                "in_graph_json":str(graph),
                "in_geojson":str(root/"geo.json"),
                "id_field":"CUSEC_KEY",
                "province_field":"CPRO",
                "municipality_field":"CUMUN",
                "k_districts":1,
            }
            cfg={"validation":{"expected_districts":1,"province_districts":{"01":1}}}
            cases=(
                pd.DataFrame([
                    {"CUSEC_KEY":"a","CPRO":"01","CUMUN":"001"},
                ]),
                pd.DataFrame([
                    {"CUSEC_KEY":"a","CPRO":"01","CUMUN":"001"},
                    {"CUSEC_KEY":"b","CPRO":"01","CUMUN":"001"},
                    {"CUSEC_KEY":"c","CPRO":"01","CUMUN":"001"},
                ]),
            )
            for frame in cases:
                with self.subTest(ids=sorted(frame["CUSEC_KEY"])):
                    with patch.object(engine.core,"load_geo",return_value=frame):
                        with self.assertRaisesRegex(
                            SystemExit,"universo M03/geometría incoherente"
                        ):
                            engine._preflight_atomic_population_connectivity(cfg,step)

    def test_floor_exemption_does_not_exempt_atomic_k_or_ceiling_conditions(self):
        nodes={"a","b"}
        weights={"a":8,"b":8}
        ok,reason,detail=engine._atomic_population_necessary_conditions(
            nodes,weights,k=3,floor=0,cap=10
        )
        self.assertFalse(ok)
        self.assertEqual(reason,"K_EXCEEDS_ATOMIC_UNITS")
        self.assertEqual(detail["nodes"],2)
        self.assertEqual(detail["k"],3)

        ok,reason,_=engine._atomic_population_necessary_conditions(
            nodes,weights,k=1,floor=0,cap=10
        )
        self.assertFalse(ok)
        self.assertEqual(reason,"PROVINCE_POPULATION_OUTSIDE_K_HARD_RANGE")

    def test_exact_atomic_cover_detects_aggregate_feasible_but_atomic_infeasible(self):
        # Total=12 y k=2 admiten agregadamente [10,14], pero cada sección pesa
        # 4: los singles quedan bajo suelo y cualquier pareja supera el techo.
        nodes={"a","b","c"}
        weights={"a":4,"b":4,"c":4}
        adjacency={
            "a":{"b"},
            "b":{"a","c"},
            "c":{"b"},
        }
        groups,seen=engine._enumerate_connected_hard_groups(
            nodes,adjacency,weights,floor=5,cap=7
        )
        self.assertIsNotNone(groups)
        self.assertGreater(seen,0)
        self.assertEqual(groups,[])
        feasible,states=engine._exact_connected_hard_partition(
            nodes,groups,weights,k=2,floor=5,cap=7
        )
        self.assertIs(feasible,False)
        self.assertGreater(states,0)

    def test_exact_cover_keeps_zero_population_nodes_at_the_ceiling(self):
        # Un distrito puede estar exactamente en el techo y aun necesitar
        # absorber secciones de población cero para cubrir todo su componente.
        # Podar al alcanzar cap fabricaría una imposibilidad falsa.
        nodes={"a","z1","z2"}
        weights={"a":5,"z1":0,"z2":0}
        adjacency={
            "a":{"z1","z2"},
            "z1":{"a"},
            "z2":{"a"},
        }
        groups,_=engine._enumerate_connected_hard_groups(
            nodes,adjacency,weights,floor=5,cap=5
        )
        self.assertIn(frozenset(nodes),groups)
        feasible,states=engine._exact_connected_hard_partition(
            nodes,groups,weights,k=1,floor=5,cap=5
        )
        self.assertIs(feasible,True)
        self.assertGreater(states,0)

    def test_exact_atomic_cover_accepts_connected_feasible_partition(self):
        nodes={"a","b","c","d"}
        weights={node:3 for node in nodes}
        adjacency={
            "a":{"b"},
            "b":{"a","c"},
            "c":{"b","d"},
            "d":{"c"},
        }
        groups,_=engine._enumerate_connected_hard_groups(
            nodes,adjacency,weights,floor=5,cap=7
        )
        feasible,states=engine._exact_connected_hard_partition(
            nodes,groups,weights,k=2,floor=5,cap=7
        )
        self.assertIs(feasible,True)
        self.assertGreater(states,0)

    def test_exact_atomic_cover_returns_unknown_when_state_budget_exhausts(self):
        nodes={"a","b","c","d"}
        weights={node:3 for node in nodes}
        adjacency={
            "a":{"b"},
            "b":{"a","c"},
            "c":{"b","d"},
            "d":{"c"},
        }
        groups,_=engine._enumerate_connected_hard_groups(
            nodes,adjacency,weights,floor=5,cap=7
        )
        feasible,states=engine._exact_connected_hard_partition(
            nodes,groups,weights,k=2,floor=5,cap=7,max_states=1
        )
        self.assertIsNone(feasible)
        self.assertGreater(states,1)


if __name__ == "__main__":
    unittest.main()
