#!/usr/bin/env python3
"""Informe operativo de orquestación v1.1.0: estado durable legible y de máquina."""
from __future__ import annotations
import argparse,json
from collections import Counter
from datetime import date
from pathlib import Path

def read(path): return json.loads(Path(path).read_text(encoding="utf-8"))

def build(state,factual):
    latest={}
    for item in state.get("records",[]): latest[(str(item.get("territory")),str(item.get("task_id")))]=item
    records=sorted(latest.values(),key=lambda x:(str(x.get("territory")),str(x.get("task_id"))))
    blocked=[x for x in records if x.get("status") in {"REQUIRES_AGENT","BLOCKED","FAIL"}]
    territories=[{"territory":key,"status":value.get("status"),"promotion":value.get("promotion",value.get("status")=="PASS"),"districts":value.get("districts"),"evidence":value.get("evidence")} for key,value in factual.get("territories",{}).items()]
    next_step={"kind":"REVIEW_BLOCKED_TASKS","tasks":[x["task_id"] for x in blocked],"message":"Revisar sólo las tareas bloqueadas; las SUCCESS o REUSED no se repiten."} if blocked else {"kind":"WAIT_FOR_MATERIAL_CHANGE","tasks":[],"message":"No hay cálculo territorial autorizado. Relanzar la orquestación únicamente si cambia una huella, contrato, fuente o producto."}
    orchestration={"state_schema_version":state.get("schema_version"),"stage_catalog_version":state.get("stage_catalog_version"),"latest_task_count":len(records),"status_counts":dict(sorted(Counter(x.get("status","UNKNOWN") for x in records).items())),"latest_tasks":records}
    return {"schema_version":"1.1.0","generated_at":str(date.today()),"phase":factual.get("phase"),"phase_status":factual.get("status"),"territories":territories,"orquestacion":orchestration,"g10":orchestration,"next_reengagement":next_step,"execution_policy":"No repetir M01–M06 ni abrir territorios nuevos sin cambio material y orden explícita."}

def markdown(report):
    lines=["# Estado operativo de orquestación","","Generado: "+report["generated_at"],"Fase: "+str(report["phase"])+" — "+str(report["phase_status"]),"","## Territorios","","| Territorio | Estado | Distritos |","|---|---|---:|"]
    for item in report["territories"]: lines.append("| {0} | {1} | {2} |".format(item["territory"],item["status"],item.get("districts","—")))
    lines+=["","## Reenganche","",report["next_reengagement"]["kind"]+" — "+report["next_reengagement"]["message"],"","## Regla","",report["execution_policy"],""]
    return "\n".join(lines)

def main():
    p=argparse.ArgumentParser(description="Genera el informe operativo de orquestación");p.add_argument("--state",required=True);p.add_argument("--factual",required=True);p.add_argument("--output-json",required=True);p.add_argument("--output-md",required=True)
    a=p.parse_args();report=build(read(a.state),read(a.factual))
    Path(a.output_json).write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    Path(a.output_md).write_text(markdown(report),encoding="utf-8");return 0
if __name__=="__main__": raise SystemExit(main())
