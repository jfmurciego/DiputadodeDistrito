"""Independent F10 2026 Cortegana: compare byte-verifiable INE OCE BOP + SIEL original.
No transfer of 2026 electoral votes to territorial CUSEC 2025.
"""
from __future__ import annotations
import argparse,csv,hashlib,json,sys
from collections import defaultdict
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from herramientas.verificar_bop_huelva_cortegana_2026 import extract,verify_document

BOP_SHA="cdd97765f72121a31774d7c0c37f572399ba3c3dca767b44e42bdc4493497dfa"
SECTIONS_SHA="6ef7fd1efb04ea3623b401b6fd73c1ed3895005384306c75b5953a97ddafa70e"
CERA_SHA="1a8de1e3e43623f677f5142fc300d70692837b30ffc5aa65e57ece3f6e7e9e7c"
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def norm(v,n):
    v=str(v).strip()
    if not v.isdigit():raise ValueError("INVALID_ELECTORAL_CODE")
    return str(int(v)).zfill(n)
def verify(siel,bop):
    if sha(bop)!=BOP_SHA:raise ValueError("BOP_SHA_MISMATCH")
    oce=verify_document(extract(bop),bop.read_bytes())
    manifest=json.loads((siel/"manifest.json").read_text(encoding="utf-8"))
    sections=siel/"andalucia_2026_siel_secciones.csv"
    cera=siel/"andalucia_2026_siel_cera_provincias.csv"
    if sha(sections)!=SECTIONS_SHA or sha(cera)!=CERA_SHA:raise ValueError("SIEL_SOURCE_SHA_MISMATCH")
    expected={"schema":"ddd-siel-andalucia-snapshot/1.0","election_id":"andalucia_parlamento_2026",
              "election_date":"2026-05-17","siel_election_key":202605,"sections":6044,
              "vote_rows":95659,"candidate_votes_sections":4136317,
              "candidate_votes_cera":21222,"candidate_votes_official":4157539,
              "sections_sha256":SECTIONS_SHA,"cera_sha256":CERA_SHA}
    if any(manifest.get(k)!=v for k,v in expected.items()):raise ValueError("SIEL_MANIFEST_NOT_ADMISSIBLE")
    universe=set();county=set();tot=0;per=defaultdict(int);rows=0;parties=0
    with sections.open(encoding="utf-8",newline="") as fh:
        rd=csv.DictReader(fh)
        for x in rd:
            p,m,d,s=(norm(x[k],n) for k,n in (("province",2),("municipality",3),("district",2),("section",3)))
            code=p+m+d+s;n=int(x["votes"])
            if n<0 or not x["party"].strip():raise ValueError("INVALID_CANDIDACY")
            universe.add(code);per[code]+=n;tot+=n;rows+=1
            if p=="21" and m=="025":
                county.add(code)
                if d=="02":
                    if s!="001":raise ValueError("SECOND_ELECTORAL_SECTION_IN_CORTEGANA")
                    parties+=1
    if len(universe)!=6044 or rows!=95659 or tot!=4136317:raise ValueError("SIEL_TERRITORIAL_NOT_RECONCILED")
    if per["2102502001"]!=658 or parties!=15 or "2102502002" in universe:raise ValueError("CORTEGANA_VOTES_NOT_VERIFIED")
    if county!={"2102501001","2102501002","2102501003","2102502001"}:raise ValueError("CORTEGANA_SECTION_UNIVERSE_NOT_EXPECTED")
    cera_votes=0
    with cera.open(encoding="utf-8",newline="") as fh:
        for x in csv.DictReader(fh):
            if norm(x["province"],2) not in {"04","11","14","18","21","23","29","41"}:raise ValueError("INVALID_CERA")
            n=int(x["votes"])
            if n<0:raise ValueError("INVALID_CERA_VOTES")
            cera_votes+=n
    if cera_votes!=21222 or cera_votes+tot!=4157539:raise ValueError("CERA_TOTALLY_NOT_RECONCILED")
    return {
      "schema":"ddd.f10.andalucia.cortegana-official-BOP-SIEL-evidence/1.0",
      "OCE":{"sha256":sha(bop),"source_url":oce["source_url"],"tables":oce["polling_table_records"],
              "effective_district_02_electoral_sections":["001"]},
      "SIEL":{"sections_sha256":SECTIONS_SHA,"cera_sha256":CERA_SHA,"sections":6044,
          "candidate_votes_sections":tot,"candidate_votes_cera":cera_votes,
          "candidate_votes_total":tot+cera_votes,
          "cortegana_02_001_votes":658,"cortegana_02_001_party_rows":15,
          "cortegana_02_002_electoral_section_absent":True,
          "cortegana_municipal_electoral_sections":sorted(county)},
      "result":{"electoral_identity":"SOURCE_ACCREDITED",
          "difference_6045_ine_2026_6044_siel":"OFFICIAL_OCE_EDITION_EXPLAINS_CORTENGANA_002",
          "crosswalk_to_ine_2025":"BLOCKED_CROSSWALK_NOT_PROVEN",
          "f10_electoral":"BLOCKED","votes_redistributed":0,
          "generation_authorized":False}}
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--bop",type=Path,required=True)
    p.add_argument("--siel",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    args=p.parse_args()
    doc=verify(args.siel,args.bop)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(doc,ensure_ascii=False,sort_keys=True,indent=2)+"\n",encoding="utf-8")
    print("DDD_F10_AND_CORTEGANA_OFFICIAL_SOURCE_PROOF="+json.dumps(doc["result"],sort_keys=True))
if __name__=="__main__":main()
