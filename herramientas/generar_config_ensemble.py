#!/usr/bin/env python3
"""Genera configuracion/ensemble/<territorio>.json de las provincias del Congreso que el ensemble admite.

PROYECTO: Diputado de Distrito
VERSIÓN: 1.0.0 · FECHA: 2026-11-08 · ESTADO: candidato
ANTERIOR: ninguna (fichero nuevo)
QUÉ HACE: toma como molde la config de La Rioja (mismos parámetros que T-61) y rellena id, provincia, K y rutas desde
  el contrato del territorio. No inventa umbrales: los copia de `validation`. Un contrato no es apto si tiene
  `topology_bridges`, exenciones de suelo, K<2, más de una provincia, CRS/POP distintos de los del molde o un techo/
  tolerancia que no sea el del Congreso. Los territorios de EXCLUIDOS_POR_ORDEN quedan fuera hasta nueva orden.
MOTIVO: T-92, ensembles de todas las provincias lanzables.
"""
from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path

import yaml

MOLDE = "congreso_la_rioja"
EXCLUIDOS_POR_ORDEN = {"congreso_cadiz": "techo 1,16 distinto de 1,15; decisión del propietario pendiente"}
LIMITES = ("population_floor_ratio", "population_cap_ratio", "target_tolerance_ratio", "municipality_atomicity_limit_ratio")


def motivo_no_apto(contract: dict, molde: dict) -> str | None:
    val, tc = contract["validation"], contract["territory_contract"]
    m02 = contract["modulos"]["modulo_02_construir_adyacencias"]
    if m02.get("topology_bridges"):
        return f"topology_bridges ({len(m02['topology_bridges'])})"
    for key in ("population_floor_exempt_partitions", "population_floor_exempt_municipalities"):
        if val.get(key):
            return f"exención {key}"
    if len(tc["province_codes"]) != 1:
        return "más de una provincia"
    if tc["k_districts"] < 2:
        return f"K={tc['k_districts']} (un solo distrito, sin ensemble)"
    if m02["working_crs"] != molde["topology"]["working_crs"]:
        return f"CRS {m02['working_crs']}"
    if contract["modulos"]["modulo_03_construir_grafo"]["pop_field"] != molde["fields"]["population"]:
        return "campo de población distinto"
    for key in LIMITES:
        if val[key] != molde["contract"][key]:
            return f"{key}={val[key]} (molde {molde['contract'][key]})"
    return None


def construir(contract: dict, molde: dict) -> dict:
    tid, run = contract["meta"]["territory_id"], contract["meta"]["run_name"]
    k, (cpro,) = contract["territory_contract"]["k_districts"], contract["territory_contract"]["province_codes"]
    cache = f"territorios/{tid}/.cache/ddd/preparacion/{run}"
    cfg = copy.deepcopy(molde)
    cfg["territory_id"] = tid
    cfg["inputs"]["m03_graph"] = f"../../{cache}/{run}_m03_grafo.json"
    cfg["inputs"]["initial_geojson"] = f"../../{cache}/{run}_m05_distritos_optimizados.geojson.zip"
    cfg["contract"]["k"] = k
    cfg["contract"]["province_districts"] = {cpro: k}
    cfg["workflow"].update(contract=f"territorios/{tid}/config/{tid}_2025.yaml", cache_dir=cache, expected_districts=k)
    return cfg


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root-dir", type=Path, default=Path("."))
    ap.add_argument("--escribir", action="store_true", help="crea las que faltan; sin él solo informa")
    args = ap.parse_args()
    root = args.root_dir
    molde = json.loads((root / "configuracion/ensemble" / f"{MOLDE}.json").read_text(encoding="utf-8"))
    for path in sorted((root / "territorios").glob("congreso_*/config/congreso_*_2025.yaml")):
        contract = yaml.safe_load(path.read_text(encoding="utf-8"))
        tid = contract["meta"]["territory_id"]
        destino = root / "configuracion/ensemble" / f"{tid}.json"
        if destino.exists():
            print(f"{tid}\tCON_CONFIG")
        elif tid in EXCLUIDOS_POR_ORDEN:
            print(f"{tid}\tEXCLUIDO_ORDEN\t{EXCLUIDOS_POR_ORDEN[tid]}")
        elif (motivo := motivo_no_apto(contract, molde)):
            print(f"{tid}\tNO_APTO\t{motivo}")
        else:
            print(f"{tid}\tGENERABLE\tK={contract['territory_contract']['k_districts']}")
            if args.escribir:
                destino.write_text(json.dumps(construir(contract, molde), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
