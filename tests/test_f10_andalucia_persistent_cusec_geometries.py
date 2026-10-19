"""F10 Andalucia: measure topology/area changes under unchanged section identifiers.

Never infer that equal CUSEC strings imply equal election-day footprints.
All geometries are official INE WFS editions reserialized during earlier research.
This diagnostic does not allocate votes or certify the electoral crosswalk.
"""
from __future__ import annotations
import json
from pathlib import Path
import unittest

from shapely.geometry import shape
from shapely.ops import unary_union

BASE=Path(__file__).resolve().parents[1]/"docs/AUDITORIAS/CIERRE_FUENTES_20261017"
MUNICIPALITIES=("11006","11012","11015","11028","14021","14038","18021",
                "18145","21035","23018","23063","29067","29070","41038",
                "41047","41081","41091")

def load(mun,year):
    p=BASE/f"ANDALUCIA_EXTRACTED_{mun}_{year}.geojson"
    obj=json.loads(p.read_text(encoding="utf-8"))
    assert obj.get("type")=="FeatureCollection"
    assert obj["numberMatched"]==obj["numberReturned"]==len(obj["features"])
    assert obj["crs"]["properties"]["name"]=="urn:ogc:def:crs:EPSG::25830"
    codes={}
    for f in obj["features"]:
        cid=f["properties"]["CUSEC"]
        assert f["properties"]["CUMUN"]==mun and f["properties"]["TIPO"]=="SECCIONADO"
        g=shape(f["geometry"])
        assert g.is_valid and not g.is_empty
        assert cid not in codes
        codes[cid]=g
    return codes

class AndaluciaUnchangedCodes(unittest.TestCase):
    def test_common_cusec_area_unchanged_vs_2025(self):
        all_changed=[]
        totals={"common":0,"exact_geometry":0,"symmetric_diff_0_to_1_m2":0,
                "symmetric_diff_1_to_100_m2":0,"symmetric_diff_gt_100_m2":0,
                "geometry_changed_0p01_percent":0}
        for mun in MUNICIPALITIES:
            with self.subTest(mun=mun):
                old=load(mun,2025)
                new=load(mun,2026)
                common=set(old)&set(new)
                totals["common"]+=len(common)
                for c in sorted(common):
                    g=old[c];h=new[c]
                    if g.equals_exact(h,tolerance=0.0):
                        totals["exact_geometry"]+=1
                        continue
                    sym=float(g.symmetric_difference(h).area)
                    symmetric_relative=sym/max(g.area,1.0)
                    if sym<=1.0: totals["symmetric_diff_0_to_1_m2"]+=1
                    elif sym<=100.0: totals["symmetric_diff_1_to_100_m2"]+=1
                    else: totals["symmetric_diff_gt_100_m2"]+=1
                    if symmetric_relative>0.0001:
                        totals["geometry_changed_0p01_percent"]+=1
                    all_changed.append({"CUSEC":c,"CUMUN":mun,
                        "symmetric_diff_m2":round(sym,4),
                        "symmetric_diff_to_old_pct":round(100*symmetric_relative,8),
                        "old_area_m2":round(g.area,2),
                        "new_area_m2":round(h.area,2)})
        all_changed.sort(key=lambda x:-x["symmetric_diff_m2"])
        print("DDD_F10_ANDALUCIA_SAMECODE_GEOMETRY_DRIFT="+json.dumps({
            "year_1":2025,"year_2":2026,"crs":"EPSG:25830",
            "scope_municipalities":len(MUNICIPALITIES),
            "counting_scope":"Sections with CUSEC present in both annual INE editions in 17 affected municipalities",
            "summary":totals,"top_changes":all_changed[:40],
            "crosswalk_accredited":False,
            "no_vote_transfer":True},sort_keys=True))
        self.assertEqual(sum(totals[k] for k in ("exact_geometry","symmetric_diff_0_to_1_m2",
                    "symmetric_diff_1_to_100_m2","symmetric_diff_gt_100_m2")),totals["common"])
        self.assertGreater(totals["common"],0)
if __name__=="__main__": unittest.main()
