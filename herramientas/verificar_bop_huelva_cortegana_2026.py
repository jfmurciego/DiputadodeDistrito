"""Preserve INE OCE Huelva official 30-03-2026 PDF and attest Cortegana's effective polling sections.

Read-only evidence; does not infer crosswalk for territorial CUSEC 2102502002.
"""
from __future__ import annotations
import argparse, hashlib, json, re, subprocess, tempfile, urllib.request
from pathlib import Path

SOURCE="https://s2.diphuelva.es/portalweb/bope/anuncios/Anuncio_350957_BOP-61_2026.pdf"
ISSUE="61/26"
TARGET="MUNICIPIO : 025 CORTEGANA"
NEXT="MUNICIPIO : 026 CORTELAZOR"

def sha(b:bytes)->str:
    return hashlib.sha256(b).hexdigest()

def extract(raw_pdf:Path)->str:
    run=subprocess.run(["pdftotext","-layout","-enc","UTF-8",str(raw_pdf),"-"],text=True,capture_output=True,check=True)
    return run.stdout

def verify_document(text:str,original:bytes)->dict:
    if not original.startswith(b"%PDF-") or len(original)<20000:
        raise ValueError("INADEQUATE_OR_NON_PDF_OFFICIAL_SOURCE")
    if "DELEGACIÓN PROVINCIAL DE LA OFICINA DEL CENSO ELECTORAL DE HUELVA" not in text and "DELEGACION PROVINCIAL DE LA OFICINA DEL CENSO ELECTORAL DE HUELVA" not in text:
        raise ValueError("WRONG_OCE_HUELVA_AUTHORITY")
    if "17 DE MAYO DE 2026" not in text:
        raise ValueError("WRONG_ELECTION_DATE")
    start=text.find(TARGET)
    end=text.find(NEXT,start)
    if start<0 or end<=start:
        raise ValueError("MUNICIPAL_BOUNDARY_NOT_DEMONSTRATED")
    only=text[start:end]
    lines=[line.strip() for line in only.splitlines()]
    # Multiple pages can repeat headings. A repeated header is not another polling table.
    found=[]
    for line in lines:
        m=re.match(r"^02\s+(\d{3})\s+(\d{2})\s+([A-Z])\b",line)
        if m:
            found.append({"section":m.group(1),"subsection":m.group(2),
                          "table":m.group(3),"record":line})
    expected={("001","01","A"),("001","02","B"),("001","03","C")}
    observed={(x["section"],x["subsection"],x["table"]) for x in found}
    if observed!=expected or len(found)!=3:
        raise ValueError("CORTENGANA_DISTRICT_02_TABLES_NOT_EXACT:"+repr(found))
    if "BIBLIOTECA MUNICIPAL" not in only or "AYUNTAMIENTO SAN TELMO" not in only or "AYUNTAMIENTO VALDELAMUSA" not in only:
        raise ValueError("POLLING_TABLE_VENUES_MISSING")
    if "BOPxs26061jVldjgyeLoBlnuo=" not in text:
        raise ValueError("OCE_DOCUMENT_VERIFICATION_CODE_MISSING")
    return {
      "schema":"ddd.f10.and.official-2026-polling-pdf-acquisition/1.0",
      "source_url":SOURCE,
      "source_bytes":len(original),
      "source_sha256":sha(original),
      "source_kind":"byte-exact officially hosted PDF",
      "authority":"INE Oficina del Censo Electoral Huelva",
      "issue":ISSUE,"date":"2026-03-30",
      "election_date":"2026-05-17",
      "municipality":"21025","district":"02",
      "official_electoral_sections":["001"],
      "polling_table_records":found,
      "electoral_section_002_separate":False,
      "source_text_sha256":sha(text.encode("utf-8")),
      "proof":"Records 02/001/01/A, 02/001/02/B, 02/001/03/C; no 02/002 within full municipality block",
      "votes_redistribution_authorized":False,
      "F10_electoral_gate":"BLOCKED_CROSSWALK_NOT_PROVEN"
    }

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--pdf",type=Path)
    parser.add_argument("--archive",type=Path,required=True)
    parser.add_argument("--result",type=Path,required=True)
    args=parser.parse_args()
    if args.pdf:
        raw=args.pdf.read_bytes()
    else:
        req=urllib.request.Request(SOURCE,headers={"User-Agent":"DDD-Fuentes-INE-2026/1.0"})
        with urllib.request.urlopen(req,timeout=35) as response:
            if response.status!=200:
                raise RuntimeError("SOURCE_HTTP_NOT_200")
            raw=response.read(25_000_001)
    if len(raw)>25_000_000 or not raw.startswith(b"%PDF-"):
        raise ValueError("INVALID_SOURCE_PDF")
    args.archive.parent.mkdir(parents=True,exist_ok=True)
    args.result.parent.mkdir(parents=True,exist_ok=True)
    if args.archive.exists() and sha(args.archive.read_bytes())!=sha(raw):
        raise ValueError("ORIGINAL_ARCHIVE_COLLISION")
    if not args.archive.exists():
        args.archive.write_bytes(raw)
    with tempfile.NamedTemporaryFile(suffix=".pdf") as tmp:
        tmp.write(raw);tmp.flush()
        content=extract(Path(tmp.name))
    report=verify_document(content,raw)
    args.result.write_text(json.dumps(report,ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print("DDD_F10_CORTEGANA_BOP_2026="+json.dumps({k:report[k] for k in (
        "source_sha256","source_bytes","official_electoral_sections",
        "polling_table_records","electoral_section_002_separate")},ensure_ascii=False))
if __name__=="__main__":main()
