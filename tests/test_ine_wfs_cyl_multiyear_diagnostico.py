"""Evidence-only geometry overlay for 2025/26 CyL CUSEC mismatches.

This test NEVER allocates votes or certifies electoral crosswalk.
"""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import unittest

from pyproj import Transformer
from shapely.geometry import shape
from shapely.ops import transform

ROOT=Path(__file__).resolve().parents[1]
FOLDER=ROOT/"docs/AUDITORIAS/CIERRE_FUENTES_20261017"
CHANGES={
    "24089":({"2408904017","2408906020"},set()),
    "37023":({"3702301002"},set()),
    "42173":({"4217302016"},set()),
    "47010":({"4701001012"},set()),
    "34120":(set(),{"3412004006"}),
    "37107":(set(),{"3710701002"}),
}

def read(territory,year):
    path=FOLDER/f"INE_WFS_CYL_{territory}_{year}.geojson"
    raw=path.read_bytes()
    doc=json.loads(raw)
    assert doc.get("type")=="FeatureCollection"
    assert len(doc["features"])==doc["numberReturned"]==doc["numberMatched"]
    assert all(f["properties"]["TIPO"]=="SECCIONADO" and f["properties"]["CUMUN"]==territory for f in doc["features"])
    result={f["properties"]["CUSEC"]:shape(f["geometry"]) for f in doc["features"]}
    assert len(result)==len(doc["features"])
    return result,hashlib.sha256(raw).hexdigest()

class CyLSectionEvidence(unittest.TestCase):
    def test_official_changed_sections_geometry(self):
        project=Transformer.from_crs("EPSG:25830","EPSG:3035",always_xy=True).transform
        for mun,(expected_added,expected_removed) in CHANGES.items():
            with self.subTest(municipality=mun):
                old,oldsha=read(mun,"2025")
                new,newsha=read(mun,"2026")
                self.assertEqual(set(new)-set(old),expected_added)
                self.assertEqual(set(old)-set(new),expected_removed)
                old={k:transform(project,g) for k,g in old.items()}
                new={k:transform(project,g) for k,g in new.items()}
                comparisons=[]
                for k in sorted(expected_added|expected_removed):
                    is_new=k in expected_added
                    target=(new if is_new else old)[k]
                    competitors=old if is_new else new
                    self.assertTrue(target.is_valid,k)
                    areas=[]
                    for dest,g in competitors.items():
                        if not target.intersects(g):
                            continue
                        area=float(target.intersection(g).area)
                        if area>0:
                            areas.append({"cusec":dest,"overlap_area_m2":round(area,4),
                                 "fraction_of_target":round(area/target.area,9)})
                    areas.sort(key=lambda d:-d["overlap_area_m2"])
                    comparisons.append({"source_CUSEC":k,"direction":"new_2026_to_2025" if is_new else "retired_2025_to_2026",
                        "source_area_m2":round(target.area,4),
                        "overlapping_candidates":areas,
                        "covered_target_fraction":round(sum(x["overlap_area_m2"] for x in areas)/target.area,9)})
                print("DDD_F10_CYL_WFS_SPATIAL_EVIDENCE="+json.dumps({"CUMUN":mun,
                 "sha256":{"2025":oldsha,"2026":newsha},
                 "spatial_matches_NOT_vote_crosswalk":comparisons},sort_keys=True))
