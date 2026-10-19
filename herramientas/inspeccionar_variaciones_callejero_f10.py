"""Inspect INE electoral street-directory variation archive; evidence only, no crosswalk promotion."""
from __future__ import annotations
import argparse, hashlib, io, json, urllib.request, zipfile
from pathlib import Path
from datetime import datetime, timezone

URL = "https://ine.es/prodyser/callejero/Var_Callejero_0725_0126.zip"
ALLOWED_URLS = {
    URL:"2025-07_to_2026-01",
    "https://ine.es/prodyser/callejero/Var_Callejero_0126_0726.zip":"2026-01_to_2026-07",
    "https://ine.es/prodyser/callejero/Var_Callejero_0125_0725.zip":"2025-01_to_2025-07",
}
CUSEC = ("5002501003","2221301003","2408904017","2408906020",
         "3702301002","4217302016","4701001012","3412004006","3710701002")

def known_f10_targets() -> tuple[str,...]:
    """Include every added/removed INE Andalusian 2025/26 identity, no inferred match."""
    path=(Path(__file__).resolve().parents[1]/
        "docs/AUDITORIAS/CIERRE_FUENTES_20261017/IDENTIDADES_INE_2025_2026_F10.json")
    data=json.loads(path.read_text(encoding="utf-8"))
    codes=set(CUSEC)
    provinces=data["andaluces"]["provinces"]
    for row in provinces:
        codes.update(row["added_2026"])
        codes.update(row["removed_since_2025"])
    if len(provinces)!=8 or sum(len(row["added_2026"]) for row in provinces)!=25:
        raise ValueError("ANDALUCIA_EDITION_EVIDENCE_CHANGED")
    if sum(len(row["removed_since_2025"]) for row in provinces)!=9:
        raise ValueError("ANDALUCIA_REMOVED_EDITION_CHANGED")
    # Persistent code + materially modified boundary is not a harmless identity match.
    # Count only the CSV of material changes already confirmed by the 17 municipal WFS pairs.
    risk=Path(__file__).resolve().parents[1]/"docs/AUDITORIAS/CIERRE_FUENTES_20261019/ANDALUCIA_41_CUSEC_MISMO_CODIGO_LIMITES_CAMBIADOS_VOTOS_2026.csv"
    import csv
    with risk.open(newline="",encoding="utf-8") as stream:
        impacted=list(csv.DictReader(stream,delimiter=";"))
    if len(impacted)!=41:
        raise ValueError("PERSISTENT_GEOMETRY_CHANGE_UNIVERSE_NOT_41")
    persistent={row["CUSEC_2025_y_2026"] for row in impacted}
    if len(persistent)!=41 or codes & persistent:
        raise ValueError("PERSISTENT_CHANGED_CODES_DUPLICATED")
    codes.update(persistent)
    codes.add("2102502001") # Cortegana official election-day district 02 precinct 001.
    codes.add("2102502002") # INE 2025/2026 map only, not electoral 2026.
    if len(codes)!=86:
        raise ValueError("F10_TARGET_UNIVERSE_NOT_86")
    return tuple(sorted(codes))

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
    targets = known_f10_targets()
    matches = {code: [] for code in targets}
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
                    if changed and (changed["source_section"] in targets or changed["other_section"] in targets):
                        relevant_changes.append({"member":member.filename,"line":line_number,**changed})
                for code in targets:
                    if code.encode("ascii") in line:
                        matches[code].append({"member":member.filename,
                          "line":line_number,"prefix":line[:240].decode("latin-1")})
    report["target_count"]=len(targets)
    report["change_records_involving_targets"] = relevant_changes
    report["change_record_scope"] = "TRAM fixed-width segment changes only; no official complete-section/vote crosswalk"
    report["cusec"] = {code: {
        "full_code_literal_occurrences":len(matches[code]),
        "examples":matches[code][:5],
        "interpretation":"Literal scan only; zero matches DOES NOT rule out fixed-width separated CPRO/CMUN/CDIS/CSEC"
    } for code in targets}
    return report

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--zip",type=Path,help="Protected official ZIP for offline verification")
    parser.add_argument("--output",type=Path,required=True)
    parser.add_argument("--source-url",default=URL,choices=sorted(ALLOWED_URLS))
    parser.add_argument("--raw-out",type=Path,help="Persist byte-exact downloaded ZIP; fail if existing differs")
    args=parser.parse_args()
    if args.zip:
        raw=args.zip.read_bytes()
    else:
        req=urllib.request.Request(args.source_url,headers={"User-Agent":"DDD-F10-FuentesOficiales/1.0"})
        with urllib.request.urlopen(req,timeout=45) as response:
            if response.status!=200: raise RuntimeError("HTTP_"+str(response.status))
            raw=response.read(100_000_001)
    report=inspect(raw)
    if args.raw_out:
        args.raw_out.parent.mkdir(parents=True,exist_ok=True)
        if args.raw_out.exists():
            if hashlib.sha256(args.raw_out.read_bytes()).hexdigest()!=report["zip_sha256"]:
                raise ValueError("EXISTING_RAW_ZIP_HASH_COLLISION")
        else:
            args.raw_out.write_bytes(raw)
        if hashlib.sha256(args.raw_out.read_bytes()).hexdigest()!=report["zip_sha256"]:
            raise ValueError("RAW_PERSISTENCE_HASH_MISMATCH")
        report["raw_original_archive"]=str(args.raw_out)
    report["source_url"]=args.source_url
    report["interval"]=ALLOWED_URLS[args.source_url]
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,sort_keys=True,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    from collections import Counter
    grouped = Counter((x["source_section"],x["other_section"],x["date"],x["change_code"]) for x in report["change_records_involving_targets"])
    print("DDD_F10_INE_TRAM_CHANGES="+json.dumps(
        [{"source":a,"other":b,"date":d,"code":kind,"records":n}
         for (a,b,d,kind),n in sorted(grouped.items(), key=lambda kv:(kv[0][0] or "",kv[0][1] or "",kv[0][2] or "",kv[0][3] or ""))],
        ensure_ascii=False,sort_keys=True))
    print("DDD_F10_INE_VARIACIONES_FORMAT="+json.dumps({"members":report["members"],"examples":{k:v["examples"][:2] for k,v in report["cusec"].items() if v["examples"]}},ensure_ascii=False,sort_keys=True))
    print(json.dumps({"zip_sha256":report["zip_sha256"],
                      "members":len(report["members"]),
                      "literal_hits":{k:v["full_code_literal_occurrences"] for k,v in report["cusec"].items()}},sort_keys=True))
if __name__=="__main__": main()
