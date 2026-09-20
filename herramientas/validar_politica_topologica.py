#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PROYECTO: Diputado de Distrito
COMPONENTE: Validador de política topológica
VERSIÓN: 1.0.0
NOMBRE DE VERSIÓN: Admisión topológica previa a M04
FECHA: 2026-09-13
ESTADO: vigente — R037
QUÉ HACE: contrasta el registro topológico con R023 y rechaza admisiones o puentes insuficientemente documentados.
MOTIVO: convertir anomalías observadas y archipiélagos en decisiones reproducibles sin ejecutar módulos territoriales.
ANTERIOR: ninguno — componente nuevo.
"""
from __future__ import annotations
import argparse, json
from pathlib import Path
from typing import Any
import yaml

LAND_DECISIONS={"BLOCKED_PENDING_REVIEW","ADMITTED_NO_ANOMALIES","ADMITTED_WITH_DECLARED_REPAIRS"}

def validate(policy_path: str|Path, root: str|Path|None=None)->dict[str,Any]:
    path=Path(policy_path).resolve(); project=Path(root).resolve() if root else path.parents[1]
    data=yaml.safe_load(path.read_text(encoding="utf-8")) or {}; errors=[]
    if data.get("schema_version")!="1.0.0": errors.append("schema_version debe ser 1.0.0")
    policies=data.get("policies") or {}; land=policies.get("land_connected") or {}; islands=policies.get("archipelago_components") or {}
    required_fields=set(land.get("repair_required_fields") or [])
    if required_fields!={"u","v","edge_type","reason","source"}: errors.append("campos obligatorios de reparación incompletos")
    if land.get("automatic_nearest_bridge")!="forbidden": errors.append("los puentes automáticos deben estar prohibidos")
    if islands.get("inter_component_edges")!="forbidden" or islands.get("district_cross_component") is not False: errors.append("un archipiélago no puede simular contigüidad entre componentes")
    if islands.get("component_apportionment")!="required_before_m04": errors.append("el reparto por componente debe preceder a M04")
    partition_registry = project / str(islands.get("component_partition_registry") or "")
    generation_policy = project / str(islands.get("component_generation_policy") or "")
    if not partition_registry.is_file(): errors.append("falta registro de particiones insulares")
    if not generation_policy.is_file(): errors.append("falta política de generación insular")
    records=data.get("territories") or []; ids=[x.get("territory_id") for x in records if isinstance(x,dict)]
    if len(ids)!=len(set(ids)): errors.append("territory_id duplicado")
    summary_path=project/(data.get("evidence") or {}).get("r023","")
    summary=json.loads(summary_path.read_text(encoding="utf-8")) if summary_path.is_file() else {"territories":[]}
    observed={x["territory_id"]:x for x in summary.get("territories",[])}
    for item in records:
        tid=item.get("territory_id"); mode=item.get("mode"); decision=item.get("decision")
        if mode=="land_connected":
            if decision not in LAND_DECISIONS: errors.append(f"{tid}: decisión continental inválida")
            source=observed.get(tid)
            if not source: errors.append(f"{tid}: falta evidencia R023"); continue
            expected=(source.get("isolated"),source.get("province_disconnected"),source.get("municipality_disconnected"))
            declared=(item.get("isolated"),item.get("admin_level_1_disconnected"),item.get("admin_level_2_disconnected"))
            if expected!=declared: errors.append(f"{tid}: contadores no coinciden con R023")
            anomalies=sum(int(x or 0) for x in declared)
            repairs=item.get("repairs") or []
            if anomalies and decision=="ADMITTED_NO_ANOMALIES": errors.append(f"{tid}: anomalías no pueden admitirse como inexistentes")
            if decision=="ADMITTED_WITH_DECLARED_REPAIRS":
                if not repairs: errors.append(f"{tid}: admisión sin reparaciones declaradas")
                for repair in repairs:
                    if not required_fields.issubset(repair) or any(repair.get(k) in (None,"") for k in required_fields): errors.append(f"{tid}: reparación incompleta")
                    if repair.get("edge_type") not in set(land.get("admitted_repairs") or []): errors.append(f"{tid}: tipo de reparación no admitido")
            elif repairs: errors.append(f"{tid}: reparaciones presentes sin decisión de admisión")
        elif mode=="archipelago_components":
            if decision not in {"POLICY_DEFINED_NOT_ADMITTED","ADMITTED_COMPONENT_PARTITIONS"}:
                errors.append(f"{tid}: decisión insular inválida")
            if decision=="ADMITTED_COMPONENT_PARTITIONS":
                if not partition_registry.is_file():
                    errors.append(f"{tid}: admisión sin registro de particiones")
                else:
                    pdata=json.loads(partition_registry.read_text(encoding="utf-8"))
                    tdata=(pdata.get("territories") or {}).get(tid) or {}
                    if not tdata.get("components") or not tdata.get("municipality_to_partition"):
                        errors.append(f"{tid}: particiones físicas incompletas")
        else: errors.append(f"{tid}: modo topológico inválido")
    return {"schema_version":"1.0.0","status":"PASS" if not errors else "FAIL","errors":errors,"territories":len(records)}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--policy",default="configuracion/politica_topologia_territorial_2025.yaml"); ap.add_argument("--out"); args=ap.parse_args()
    report=validate(args.policy); payload=json.dumps(report,ensure_ascii=False,indent=2)+"\n"
    if args.out: Path(args.out).write_text(payload,encoding="utf-8")
    print(payload,end=""); raise SystemExit(0 if report["status"]=="PASS" else 1)
if __name__=="__main__": main()
