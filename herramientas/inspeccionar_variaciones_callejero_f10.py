"""Inspect INE electoral street-directory variation archive; evidence only, no crosswalk promotion."""
from __future__ import annotations
import argparse, hashlib, io, json, urllib.request, zipfile
from pathlib import Path
from datetime import datetime, timezone

URL = "https://ine.es/prodyser/callejero/Var_Callejero_0725_0126.zip"
CUSEC = ("5002501003","2221301003","2408904017","2408906020",
         "3702301002","4217302016","4701001012","3412004006","3710701002")

def decode_tram_change(line: bytes):
    """Fixed-width TRAM layout from INE Variacionesencallejero.pdf, pages 6-7.

    The two identities are two sections named in a change record, not an
    accredited vote transfer or necessarily a whole-section correspondence.
    """
    if len(line) < 79:
        return None
    old = line[0:10].decode("ascii", errors="ignore")
    next_code = old[:5] + line[74:79].decode("ascii", errors="ignore")
    if len(old)!=10 or not old.isascii() or not old.isdigit():
        return None
    if not next_code[5:].strip():
        next_code = None
    elif len(next_code)!=10 or not next_code.isascii() or not next_code.isdigit():
        next_code = None
    return {"source_section":old, "other_section":next_code,
            "date":line[61:69].decode("ascii", errors="replace"),
            "sequence":line[69:73].decode("ascii", errors="replace"),
            "change_code":line[73:74].decode("ascii", errors="replace")}

def inspect(data: bytes) -> dict:
    if len(data) > 100_000_000 or not data.startswith(b"PK"):
        raise ValueError("ZIP_EXPECTED_UNDER_100MB")
    report = {
        "schema": "ddd.f10-ine-callejero-variations-scan/1.0",
        "authority": "Instituto Nacional de Estadística (INE)",
        "source_url": URL, "interval": "2025-07_to_2026-01",
        "zip_sha256": hashlib.sha256(data).hexdigest(), "zip_bytes": len(data),
        "scanned_at_utc": datetime.now(timezone.utc).isoformat(),
        "members": [], "cusec": {},
        "crosswalk_accredited": False, "generation_authorized": False
    }
    matches = {code: [] for code in CUSEC}
    relevant_changes=[]
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        bad = z.testzip()
        if bad is not None:
            raise ValueError("ZIP_CRC_FAIL:"+bad)
        for member in sorted(z.infolist(), key=lambda x:x.filename):
            if member.is_dir(): continue
            if member.file_size > 65_000_000:
                raise ValueError("ZIP_MEMBER_TOO_LARGE")
            raw = z.read(member)
            family = Path(member.filename).name.split(".")[0].upper()
            lines = raw.splitlines()
            report["members"].append({
                "file": member.filename, "bytes":len(raw),
                "sha256":hashlib.sha256(raw).hexdigest(), "lines":len(lines),
                "family":family,
                "first_record_prefix":lines[0][:60].decode("latin-1") if lines else ""
            })
            if family not in {"SECC","TRAM","VIAS","PSEU","UP"}: continue
            for line_number,line in enumerate(lines,1):
                if family == "TRAM":
                    changed = decode_tram_change(line)
                    if changed and (changed["source_section"] in CUSEC or changed["other_section"] in CUSEC):
                        relevant_changes.append({"member":member.filename,"line":line_number,**changed})
                for code in CUSEC:
                    if code.encode("ascii") in line:
                        matches[code].append({"member":member.filename,
                          "line":line_number,"prefix":line[:240].decode("latin-1")})
    report["change_records_involving_targets"] = relevant_changes
    report["change_record_scope"] = "TRAM fixed-width segment changes only; no official complete-section/vote crosswalk"
    report["cusec"] = {code: {
        "full_code_literal_occurrences":len(matches[code]),
        "examples":matches[code][:5],
        "interpretation":"Literal scan only; zero matches DOES NOT rule out fixed-width separated CPRO/CMUN/CDIS/CSEC"
    } for code in CUSEC}
    return report

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--zip",type=Path,help="Protected official ZIP for offline verification")
    parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args()
    if args.zip:
        raw=args.zip.read_bytes()
    else:
        req=urllib.request.Request(URL,headers={"User-Agent":"DDD-F10-FuentesOficiales/1.0"})
        with urllib.request.urlopen(req,timeout=45) as response:
            if response.status!=200: raise RuntimeError("HTTP_"+str(response.status))
            raw=response.read(100_000_001)
    report=inspect(raw)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,sort_keys=True,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    from collections import Counter
    grouped = Counter((x["source_section"],x["other_section"],x["date"],x["change_code"]) for x in report["change_records_involving_targets"])
    print("DDD_F10_INE_TRAM_CHANGES="+json.dumps(
        [{"source":a,"other":b,"date":d,"code":kind,"records":n}
         for (a,b,d,kind),n in sorted(grouped.items())],
        ensure_ascii=False,sort_keys=True))
    print("DDD_F10_INE_VARIACIONES_FORMAT="+json.dumps({"members":report["members"],"examples":{k:v["examples"][:2] for k,v in report["cusec"].items() if v["examples"]}},ensure_ascii=False,sort_keys=True))
    print(json.dumps({"zip_sha256":report["zip_sha256"],
                      "members":len(report["members"]),
                      "literal_hits":{k:v["full_code_literal_occurrences"] for k,v in report["cusec"].items()}},sort_keys=True))
if __name__=="__main__": main()
