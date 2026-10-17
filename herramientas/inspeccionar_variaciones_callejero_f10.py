"""Inspect INE electoral street-directory variation archive; evidence only, no crosswalk promotion."""
from __future__ import annotations
import argparse, hashlib, io, json, urllib.request, zipfile
from pathlib import Path
from datetime import datetime, timezone

URL = "https://ine.es/prodyser/callejero/Var_Callejero_0725_0126.zip"
CUSEC = ("5002501003","2221301003","2408904017","2408906020",
         "3702301002","4217302016","4701001012","3412004006","3710701002")

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
                for code in CUSEC:
                    if code.encode("ascii") in line:
                        matches[code].append({"member":member.filename,
                          "line":line_number,"prefix":line[:240].decode("latin-1")})
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
    print(json.dumps({"zip_sha256":report["zip_sha256"],
                      "members":len(report["members"]),
                      "literal_hits":{k:v["full_code_literal_occurrences"] for k,v in report["cusec"].items()}},sort_keys=True))
if __name__=="__main__": main()
