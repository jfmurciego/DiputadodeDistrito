#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from herramientas.generar_estado_operativo import build


def main() -> int:
    ap=argparse.ArgumentParser()
    ap.add_argument("--root-dir",type=Path,default=Path("."))
    ap.add_argument("--edition",default="2025")
    ap.add_argument("--output",type=Path,required=True)
    args=ap.parse_args()
    payload=build(args.root_dir,args.edition)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"output":str(args.output),"territories":len(payload["territories"]),"latest_validated":payload["latest_validated"]},ensure_ascii=False))
    return 0


if __name__=="__main__":
    raise SystemExit(main())
