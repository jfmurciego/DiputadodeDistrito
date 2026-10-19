"""Exploratory official section-geometry overlap; never allocates electoral votes."""
from __future__ import annotations
import json, hashlib
from pathlib import Path
import unittest
from shapely.geometry import shape
from shapely.ops import transform
from pyproj import Transformer

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/"docs/AUDITORIAS/CIERRE_FUENTES_20261017"

def load(municipality,year):
    p=BASE/f"INE_WFS_ARAGON_{municipality}_{year}.geojson"
    raw=p.read_bytes(); doc=json.loads(raw)
    assert doc["type"]=="FeatureCollection"
    shapes={f["properties"]["CUSEC"]: shape(f["geometry"]) for f in doc["features"]}
    assert len(shapes)==doc["numberMatched"]==doc["numberReturned"]
    assert all(f["properties"]["CUMUN"]==municipality and f["properties"]["TIPO"]=="SECCIONADO" for f in doc["features"])
    assert all(x.is_valid and not x.is_empty for x in shapes.values())
    return shapes,hashlib.sha256(raw).hexdigest()

class AragonINE2025to2026(unittest.TestCase):
    def test_area_overlay_without_vote_transfer(self):
        prj=Transformer.from_crs("EPSG:25830","EPSG:3035",always_xy=True).transform
        expected={"50025":({"5002501003"},set()),"22213":(set(),{"2221301003"})}
        for mun,(newcodes,oldcodes) in expected.items():
            with self.subTest(mun=mun):
                old,sha25=load(mun,"2025")
                new,sha26=load(mun,"2026")
                self.assertEqual(set(new)-set(old),newcodes)
                self.assertEqual(set(old)-set(new),oldcodes)
                old={k:transform(prj,v) for k,v in old.items()}
                new={k:transform(prj,v) for k,v in new.items()}
                target=sorted(newcodes or oldcodes)
                matrix=[]
                for code in target:
                    if code in newcodes:
                        g=new[code]; competitors=old; direction="2026_new_to_2025"
                    else:
                        g=old[code]; competitors=new; direction="2025_removed_to_2026"
                    cols=[{"CUSEC":k,"area_m2":round(g.intersection(other).area,4),
                           "fraction_of_target":round(g.intersection(other).area/g.area,9)}
                           for k,other in competitors.items() if g.intersection(other).area>0]
                    cols.sort(key=lambda t:-t["area_m2"])
                    matrix.append({"target":code,"direction":direction,"geometry_area_m2":round(g.area,4),
                                  "candidates":cols,"sum_overlap_fraction":round(sum(v["fraction_of_target"] for v in cols),9)})
                print("DDD_F10_ARAGON_INE_SPATIAL_CANDIDATES="+json.dumps(
                    {"mun":mun,"source_sha256":{"2025":sha25,"2026":sha26},
                     "geometry_matches_not_official_vote_crosswalk":matrix},sort_keys=True))
