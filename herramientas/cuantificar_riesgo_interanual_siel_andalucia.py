"""Evidence-only reconciliation of 2026 SIEL candidate votes against INE 2025/2026 geometry.

This script measures, but never promotes, the temporal crosswalk: official
section results remain attached to 2026 geographies. No votes are allocated
between different CUSECs, and CERA remains provincial.
"""
from __future__ import annotations
import argparse,csv,hashlib,io,json,zipfile
from pathlib import Path
from collections import Counter,defaultdict
from shapely.geometry import shape

ROOT=Path(__file__).resolve().parents[1]
EVID=ROOT/"docs/AUDITORIAS/CIERRE_FUENTES_20261017"
CONTRACT_SECTIONS_SHA="6ef7fd1efb04ea3623b401b6fd73c1ed3895005384306c75b5953a97ddafa70e"
CONTRACT_CERA_SHA="1a8de1e3e43623f677f5142fc300d70692837b30ffc5aa65e57ece3f6e7e9e7c"
MUNS=("11006","11012","11015","11028","14021","14038","18021","18145","21035","23018","23063","29067","29070","41038","41047","41081","41091")
def sha(data:bytes)->str:
    return hashlib.sha256(data).hexdigest()

def geometries(mun,year):
    raw=(EVID/f"ANDALUCIA_EXTRACTED_{mun}_{year}.geojson").read_bytes()
    doc=json.loads(raw)
    assert doc.get("type")=="FeatureCollection"
    assert doc.get("numberMatched")==len(doc["features"])==doc.get("numberReturned")
    assert doc["crs"]["properties"]["name"]=="urn:ogc:def:crs:EPSG::25830"
    assert doc.get("ddd_extraction",{}).get("method")=="TinyFish textual extraction reserialized; not raw HTTP bytes"
    out={}
    for f in doc["features"]:
        att=f["properties"]
        assert att["CUMUN"]==mun and att["TIPO"]=="SECCIONADO"
        c=att["CUSEC"]
        assert c.startswith(mun) and len(c)==10 and c not in out
        g=shape(f["geometry"])
        assert not g.is_empty and g.is_valid
        out[c]=g
    return out,sha(raw)

def electoral(zip_path:Path):
    with zipfile.ZipFile(zip_path) as z:
        raw=z.read("andalucia_2026_siel_secciones.csv")
        cera=z.read("andalucia_2026_siel_cera_provincias.csv")
        manifest=json.loads(z.read("manifest.json"))
        assert sha(raw)==CONTRACT_SECTIONS_SHA==manifest["sections_sha256"]
        assert sha(cera)==CONTRACT_CERA_SHA==manifest["cera_sha256"]
        assert manifest["sections"]==6044 and manifest["candidate_votes_official"]==4157539
        votes=Counter()
        rows=0
        for row in csv.DictReader(io.StringIO(raw.decode("utf-8"))):
            c=f"{int(row['province']):02d}{int(row['municipality']):03d}{int(row['district']):02d}{int(row['section']):03d}"
            assert len(c)==10
            n=int(row["votes"]); assert n>=0
            votes[c]+=n;rows+=1
        assert len(votes)==6044 and rows==95659 and sum(votes.values())==4136317
        cera_vote_count=sum(int(row["votes"]) for row in csv.DictReader(io.StringIO(cera.decode("utf-8"))))
        assert cera_vote_count==21222 and sum(votes.values())+cera_vote_count==4157539
    return votes,{"official_artifact":11283424306,"official_run":37150399030,
           "official_siel_sections_sha256":sha(raw),"official_siel_cera_sha256":sha(cera)}

def mapping():
    with (EVID/"ANDALUCIA_CANDIDATOS_GEOMETRICOS_34_20261019.csv").open(newline="",encoding="utf-8") as stream:
        rows=list(csv.DictReader(stream,delimiter=";"))
    assert len(rows)==34
    return rows

def run(zip_path:Path,out:Path):
    votes,origin=electoral(zip_path)
    mapped=mapping()
    expected_new={r["CUSEC_cambiada"] for r in mapped if r["sentido"]=="2026_to_2025"}
    expected_old={r["CUSEC_cambiada"] for r in mapped if r["sentido"]=="2025_to_2026"}
    assert len(expected_new)==25 and len(expected_old)==9
    unchanged={}
    all_new=set();all_old=set()
    sources={}
    summary=Counter()
    for mun in MUNS:
        old,h25=geometries(mun,2025);new,h26=geometries(mun,2026)
        sources[mun]={"2025_sha256":h25,"2026_sha256":h26}
        all_new|=set(new)-set(old);all_old|=set(old)-set(new)
        for c in set(new)&set(old):
            left,right=old[c],new[c]
            if left.equals_exact(right,tolerance=0):
                summary["exact"]+=1
                continue
            d=float(left.symmetric_difference(right).area)
            if d<=1.0:summary["tiny_under_1m2"]+=1
            elif d<=100: summary["sliver_1to100m2"]+=1
            else:summary["material_gt_100m2"]+=1
            unchanged[c]={"CUSEC":c,"CUMUN":mun,"symmetric_difference_m2":round(d,4),
              "symmetric_difference_pct_of_2025":round(100*d/max(left.area,1.0),8),
              "old_area_m2":round(float(left.area),2),"new_area_m2":round(float(right.area),2),
              "official_siel_2026_candidate_votes":votes.get(c)}
    assert all_new==expected_new and all_old==expected_old
    material={c:d for c,d in unchanged.items() if d["symmetric_difference_m2"]>100.0}
    assert summary["material_gt_100m2"]==len(material)
    merged={}
    for r in mapped:
        if r["sentido"]=="2025_to_2026":
            c=r["CUSEC_cambiada"];dest=r["CUSEC_contraparte_principal"]
            merged[c]={"retired_2025_CUSEC":c,"geometric_successor_2026":dest,
                       "successor_total_candidate_votes_2026":votes[dest],
                       "shares_distribution_legally_approved":False}
    assert len(merged)==9 and sum(x["successor_total_candidate_votes_2026"] for x in merged.values())==6901
    new_candidate_votes=sum(votes[x] for x in expected_new)
    assert new_candidate_votes==15425
    cortegana="2102502001"
    assert votes[cortegana]==658
    flagged=(set(material)|expected_new|{cortegana})
    assert set(merged.values() and (x["geometric_successor_2026"] for x in merged.values())) <= set(material)
    impact=sum(votes[c] for c in flagged)
    assert summary["exact"]+summary["tiny_under_1m2"]+summary["sliver_1to100m2"]+summary["material_gt_100m2"]==1647
    report={
      "schema":"ddd.f10-andalucia-siel-ine-crossyear-risk/1.0",
      "source":origin,"municipal_source_sha256":sources,"official_election":"2026-05-17",
      "territorial_reference_year":2025,"electoral_year":2026,
      "scope":{"municipalities":17,"common_cusec":1647,"unchanged_geometry":summary["exact"],
               "tiny_differences_under_1m2":summary["tiny_under_1m2"],
               "differences_1to100m2":summary["sliver_1to100m2"],
               "material_geometry_changes_gt_100m2":len(material),
               "new_2026_cusec":25,"retired_2025_cusec":9,"cortegana_2025_map_only_cusec":"2102502002"},
      "votes":{"siel_sections":6044,"siel_geographic_candidate_votes":4136317,"cera_candidate_votes_unassigned":21222,
               "total_official_candidate_votes":4157539,
               "new_2026_25_sections_candidate_votes":new_candidate_votes,
               "merged_2025_9_retired_successor_2026_votes":6901,
               "cortegana_2026_02001_candidate_votes":658,
               "distinct_2026_sections_with_proven_change_or_cortegana_issue":len(flagged),
               "candidate_votes_in_distinct_flagged_sections":impact},
      "materially_changed_persistent_2026_sections":[material[c]|{"votes":votes[c]} for c in sorted(material)],
      "new_2026_sections":[{"cusec":c,"votes":votes[c]} for c in sorted(expected_new)],
      "retired_2025_merged_sections":[merged[c] for c in sorted(merged)],
      "cortegana_election_precinct_source":"https://s2.diphuelva.es/portalweb/bope/anuncios/Anuncio_350957_BOP-61_2026.pdf",
      "limitations":["14,000+ voting records may be in mapped source material; this reports only 17 municipalities and one separately evidenced Cortegana precinct",
                     "Source INE WFS municipal JSON was reserialized, not raw official HTTP receipts",
                     "Official 2026 electoral section is not equivalent to 2025 territorial section just because CUSEC is unchanged",
                     "Merged official 2026 section votes cannot be split across retired 2025 polygons by geometric area",
                     "No old section is credited with votes from a new 2026 section automatically",
                     "CERA remains unassigned geographically"],
      "crosswalk_accredited":False,"pass_F10_electoral":False,"generation_authorized":False
    }
    out.mkdir(parents=True,exist_ok=True)
    output=out/"andalucia_riesgo_geografico_electoral_2025_2026.json"
    output.write_text(json.dumps(report,indent=2,ensure_ascii=False,sort_keys=True)+"\n",encoding="utf-8")
    print("DDD_AND_F10_CONSERVATIVE_RISK="+json.dumps({
        "changed_same_id":len(material),"new_2026":25,"old_retired":9,
        "merged_successor_votes":6901,"new_votes":15425,"cortegana_votes":658,
        "distinct_flagged_2026_codes":len(flagged),"flagged_votes":impact,
        "siel_sha256":origin["official_siel_sections_sha256"],
        "crosswalk_accredited":False},sort_keys=True))
    return report

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--siel-zip",type=Path,required=True)
    parser.add_argument("--out",type=Path,required=True)
    args=parser.parse_args()
    run(args.siel_zip,args.out)
if __name__=="__main__":main()
