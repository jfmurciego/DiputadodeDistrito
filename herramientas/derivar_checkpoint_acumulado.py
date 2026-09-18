#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Deriva de forma verificable un checkpoint acumulado antiguo a una etapa anterior."""
from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

import yaml


def _fmt(value, cfg, run_id=""):
    meta=cfg.get("meta") or {}
    return str(value).format(year=meta.get("year"),run_name=meta.get("run_name"),run_id=run_id)


def _stage_number(name: str) -> int | None:
    if not name.startswith("modulo_"):
        return None
    parts=name.split("_",2)
    if len(parts)<2 or not parts[1].isdigit():
        return None
    return int(parts[1])


def _required_outputs(cfg: dict, through_stage: int) -> list[str]:
    names=[]
    for module_name,module_cfg in (cfg.get("modulos") or {}).items():
        stage=_stage_number(str(module_name))
        if stage is None or stage>through_stage or not isinstance(module_cfg,dict):
            continue
        for key,value in module_cfg.items():
            if str(key).startswith("out_") and isinstance(value,str) and value:
                names.append(Path(_fmt(value,cfg)).name)
    return sorted(set(names))


def _later_outputs(cfg: dict, after_stage: int) -> list[str]:
    names=[]
    for module_name,module_cfg in (cfg.get("modulos") or {}).items():
        stage=_stage_number(str(module_name))
        if stage is None or stage<=after_stage or not isinstance(module_cfg,dict):
            continue
        for key,value in module_cfg.items():
            if str(key).startswith("out_") and isinstance(value,str) and value:
                names.append(Path(_fmt(value,cfg)).name)
    return sorted(set(names))


def derive_checkpoint(*, params: Path, state_root: Path, output: Path, target_stage: int = 4) -> dict:
    cfg=yaml.safe_load(params.read_text(encoding="utf-8")) or {}
    cache=state_root/"cache"; run=state_root/"run"; sources=state_root/"sources"
    if not cache.is_dir() or not run.is_dir() or not sources.is_dir():
        raise ValueError("checkpoint acumulado incompleto: requiere cache/, run/ y sources/")
    required=_required_outputs(cfg,target_stage)
    missing=[name for name in required if not any(cache.rglob(name))]
    if missing:
        raise ValueError("checkpoint acumulado no contiene salidas necesarias hasta M%02d: %s" % (target_stage,", ".join(missing)))
    if output.exists():
        shutil.rmtree(output)
    shutil.copytree(state_root,output)
    out_cache=output/"cache"
    removed=[]
    for name in _later_outputs(cfg,target_stage):
        for path in list(out_cache.rglob(name)):
            if path.is_file():
                path.unlink(); removed.append(name)
    chain=output/"run"/"CHAIN_STATE.json"
    if not chain.is_file():
        raise ValueError("checkpoint acumulado sin CHAIN_STATE.json")
    payload=json.loads(chain.read_text(encoding="utf-8"))
    payload["completed_stage"]=target_stage
    payload["completed_stage_label"]=f"M{target_stage:02d}"
    chain.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    logs=output/"run"/"logs"
    if logs.is_dir():
        for path in logs.glob("modulo_*.log"):
            try:
                stage=int(path.stem.split("_")[-1])
            except ValueError:
                continue
            if stage>target_stage:
                path.unlink()
    manifest=output/"manifest.json"
    provenance={
        "schema":"ddd-derived-checkpoint/1.0",
        "source_completed_stage":json.loads((state_root/"run"/"CHAIN_STATE.json").read_text(encoding="utf-8")).get("completed_stage"),
        "derived_stage":f"M{target_stage:02d}",
        "required_outputs":required,
        "removed_outputs":sorted(set(removed)),
    }
    if manifest.is_file():
        try:
            original=json.loads(manifest.read_text(encoding="utf-8"))
        except Exception:
            original={}
        original["completed_stage"]=f"M{target_stage:02d}"
        original["derived_checkpoint"]=provenance
        manifest.write_text(json.dumps(original,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    (output/"DERIVED_CHECKPOINT.json").write_text(json.dumps(provenance,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    return provenance


def main() -> int:
    ap=argparse.ArgumentParser()
    ap.add_argument("--params",required=True,type=Path)
    ap.add_argument("--state-root",required=True,type=Path)
    ap.add_argument("--output",required=True,type=Path)
    ap.add_argument("--target-stage",default="M04")
    args=ap.parse_args()
    raw=str(args.target_stage).upper()
    if not raw.startswith("M") or not raw[1:].isdigit():
        raise SystemExit("target-stage inválido")
    result=derive_checkpoint(params=args.params,state_root=args.state_root,output=args.output,target_stage=int(raw[1:]))
    print(json.dumps(result,ensure_ascii=False))
    return 0


if __name__=="__main__":
    raise SystemExit(main())
