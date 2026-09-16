#!/usr/bin/env python3
"""CLI de orquestación v1.2.0: planifica, admite, verifica evidencia y materializa estado."""
from __future__ import annotations
import argparse,hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from g10.core import admission_matrix,aggregate_summaries,atomic_write_json,classify_failure,compute_fingerprint,merge_successful_state,validate_plan

def read_json(path:str):return json.loads(Path(path).read_text(encoding="utf-8"))
def evidence(paths:list[str])->dict:
    found=[];missing=[]
    for raw in paths:
        p=Path(raw)
        if not p.is_file():missing.append(raw);continue
        found.append({"path":raw,"sha256":hashlib.sha256(p.read_bytes()).hexdigest(),"bytes":p.stat().st_size})
    if missing:raise FileNotFoundError(", ".join(missing))
    return {"artifacts":found}
def main()->int:
    parser=argparse.ArgumentParser(description="Orquestación reproducible y durable");sub=parser.add_subparsers(dest="command",required=True)
    for name in ("validate-plan","matrix","admit"):
        x=sub.add_parser(name);x.add_argument("--plan",required=True)
        if name=="admit":x.add_argument("--state",required=True);x.add_argument("--root",default=".")
    fp=sub.add_parser("fingerprint");fp.add_argument("--root",default=".");fp.add_argument("--context",default="{}");fp.add_argument("paths",nargs="+")
    verify=sub.add_parser("verify-evidence");verify.add_argument("paths",nargs="+")
    classify=sub.add_parser("classify");classify.add_argument("--exit-code",type=int,required=True);classify.add_argument("--log",required=True);classify.add_argument("--stage")
    aggregate=sub.add_parser("aggregate");aggregate.add_argument("--output",required=True);aggregate.add_argument("summaries",nargs="+")
    merge=sub.add_parser("merge-state");merge.add_argument("--state",required=True);merge.add_argument("--output",required=True);merge.add_argument("--run-id",required=True);merge.add_argument("summaries",nargs="+")
    args=parser.parse_args()
    if args.command=="validate-plan":
        plan=read_json(args.plan);validate_plan(plan);print(f"ORQUESTACION PLAN PASS: {plan['lot_id']} tasks={len(plan['tasks'])}")
    elif args.command=="matrix":
        plan=read_json(args.plan);validate_plan(plan);print(json.dumps({"include":plan["tasks"]},separators=(",",":")))
    elif args.command=="admit":
        result=admission_matrix(read_json(args.plan),read_json(args.state),root=args.root);print(json.dumps(result,separators=(",",":"),ensure_ascii=False))
    elif args.command=="fingerprint":print(compute_fingerprint(args.paths,context=json.loads(args.context),root=args.root))
    elif args.command=="verify-evidence":print(json.dumps(evidence(args.paths),ensure_ascii=False))
    elif args.command=="classify":
        failure=classify_failure(exit_code=args.exit_code,log=Path(args.log).read_text(encoding="utf-8",errors="replace"),failed_stage=args.stage);print("SUCCESS" if failure is None else failure.value)
    elif args.command=="aggregate":
        result=aggregate_summaries([read_json(x) for x in args.summaries]);atomic_write_json(args.output,result);print(json.dumps(result["counts"],sort_keys=True))
    elif args.command=="merge-state":
        result=merge_successful_state(read_json(args.state),[read_json(x) for x in args.summaries],run_id=args.run_id);atomic_write_json(args.output,result);print(len(result["records"]))
    return 0
if __name__=="__main__":raise SystemExit(main())
