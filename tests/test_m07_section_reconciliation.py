from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path

import geopandas as gpd
import pandas as pd
from shapely.geometry import Point

ROOT=Path(__file__).resolve().parents[1]
MODULE=ROOT/"modulos/07_agregar_resultados_electorales.py"
spec=importlib.util.spec_from_file_location("m07_agregar_resultados_electorales",MODULE)
m07=importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(m07)


class SectionReconciliationTests(unittest.TestCase):
    def test_aliases_and_population_splits_preserve_votes_exactly(self):
        section_party=pd.DataFrame([
            {"CUSEC_KEY":"OLD","party":"A","votes":101},
            {"CUSEC_KEY":"PARENT","party":"A","votes":11},
            {"CUSEC_KEY":"PARENT","party":"B","votes":7},
        ])
        gdf=gpd.GeoDataFrame(
            {
                "CUSEC_KEY":["NEW","PARENT","CHILD"],
                "POP_2025":[100,300,100],
            },
            geometry=[Point(0,0),Point(1,0),Point(2,0)],
            crs="EPSG:25830",
        )
        contract={
            "section_reconciliation":{
                "aliases":[{"from":"OLD","to":"NEW","method":"exact"}],
                "splits":[{
                    "source_section":"PARENT",
                    "target_sections":["PARENT","CHILD"],
                    "weighting":"current_population",
                    "population_field":"POP_2025",
                }],
            }
        }
        out,report=m07.apply_section_reconciliation(
            section_party,gdf,section_field="CUSEC_KEY",contract=contract
        )
        self.assertEqual(int(out["votes"].sum()),119)
        self.assertEqual(report["votes_before"],119)
        self.assertEqual(report["votes_after"],119)
        a=dict(
            out.loc[out["party"].eq("A"),["CUSEC_KEY","votes"]]
            .set_index("CUSEC_KEY")["votes"]
        )
        self.assertEqual(a["NEW"],101)
        self.assertEqual(a["PARENT"],8)
        self.assertEqual(a["CHILD"],3)
        b=dict(
            out.loc[out["party"].eq("B"),["CUSEC_KEY","votes"]]
            .set_index("CUSEC_KEY")["votes"]
        )
        self.assertEqual(b["PARENT"],5)
        self.assertEqual(b["CHILD"],2)

    def test_split_fails_if_target_population_missing(self):
        section_party=pd.DataFrame([{"CUSEC_KEY":"PARENT","party":"A","votes":10}])
        gdf=gpd.GeoDataFrame(
            {"CUSEC_KEY":["PARENT"],"POP_2025":[100]},
            geometry=[Point(0,0)],crs="EPSG:25830",
        )
        contract={"section_reconciliation":{"splits":[{
            "source_section":"PARENT",
            "target_sections":["PARENT","CHILD"],
            "weighting":"current_population",
            "population_field":"POP_2025",
        }]}}
        with self.assertRaisesRegex(ValueError,"CHILD ausente"):
            m07.apply_section_reconciliation(
                section_party,gdf,section_field="CUSEC_KEY",contract=contract
            )


class AsturiasElectoralGovernanceTests(unittest.TestCase):
    def test_asturias_contract_closes_known_2023_2025_gaps(self):
        import json, yaml
        declaration=ROOT/"territorios/principado_de_asturias/config/elecciones/asturias_jgpa_2023_vigente.yaml"
        crosswalk=ROOT/"territorios/principado_de_asturias/config/elecciones/asturias_2023_oviedo_special_crosswalk.json"
        data=yaml.safe_load(declaration.read_text(encoding="utf-8"))
        cw=json.loads(crosswalk.read_text(encoding="utf-8"))

        self.assertEqual(data["verification"]["mode"],"exact_party_totals")
        self.assertEqual(sum(data["verification"]["official_party_totals"].values()),527500)
        self.assertEqual(data["verification"]["official_candidate_votes"],527500)

        self.assertEqual(cw["schema"],"ddd-election-special-row-crosswalk/1.0")
        self.assertEqual(len(cw["rows"]),81)
        self.assertEqual([row["ordinal"] for row in cw["rows"]],list(range(1,82)))
        self.assertTrue(all(str(row["target_cusec"]).startswith("33044") for row in cw["rows"]))

        reconciliation=data["section_reconciliation"]
        self.assertEqual(len(reconciliation["aliases"]),8)
        self.assertEqual(len(reconciliation["splits"]),2)
        self.assertEqual(data["reconciliation"]["allowed_result_only_sections"],[])
        self.assertEqual(data["reconciliation"]["allowed_map_only_sections"],[])

        cera=data["non_geocodable_vote_policy"]["CERA"]
        self.assertEqual(cera["action"],"exclude_from_geographic_district_allocation")
        self.assertEqual(cera["reporting"],"mandatory")


if __name__=="__main__":
    unittest.main()
