#!/usr/bin/env python3
from __future__ import annotations
import argparse,json
from pathlib import Path

ROUTES={
    "Distritos":{"to_stage":"M06","checkpoint_policy":"latest_before_target","requires_electoral_package":False},
    "Resultados electorales":{"to_stage":"M08","checkpoint_policy":"require_m06","requires_electoral_package":True},
    "Ambos":{"to_stage":"M08","checkpoint_policy":"latest_before_target","requires_electoral_package":True},
}

def resolve_product(product:str)->dict:
    try:
        return {"product":product,**ROUTES[product]}
    except KeyError as exc:
        raise ValueError(f"Producto no reconocido: {product}") from exc

def synthetic_matrix_decision(product:str,m06_state:str,electoral_state:str)->dict:
    """Contrato sintético de prerrequisitos; no ejecuta módulos ni consulta GitHub."""
    route=resolve_product(product)
    if route["checkpoint_policy"]=="require_m06" and m06_state!="existing":
        return {**route,"runnable":False,"block_reason":"M06_REQUIRED"}
    if route["requires_electoral_package"] and electoral_state!="existing":
        return {**route,"runnable":False,"block_reason":"ELECTORAL_PACKAGE_REQUIRED"}
    return {**route,"runnable":True,"block_reason":None}

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--product",required=True,choices=list(ROUTES))
    ap.add_argument("--output",type=Path)
    a=ap.parse_args()
    payload=resolve_product(a.product)
    text=json.dumps(payload,ensure_ascii=False)
    if a.output:
        a.output.parent.mkdir(parents=True,exist_ok=True)
        a.output.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(text)
if __name__=="__main__": main()
