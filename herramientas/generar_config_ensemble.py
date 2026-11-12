#!/usr/bin/env python3
"""Genera configuracion/ensemble/<territorio>.json de las provincias del Congreso que el ensemble admite.

PROYECTO: Diputado de Distrito
VERSIÓN: 1.3.1 · FECHA: 2026-11-12 · ESTADO: candidato
CAMBIOS 1.3.1 (T-220): ids de territorio nuevos de la tabla maestra (aut01…nac52, D-61); el id viejo se lee vía ddd_core.territorio_ids.
ANTERIOR: legacy/herramientas/generar_config_ensemble_v1.3.0_20261112.py
CAMBIOS 1.3.0 (T-128): molde autonómico. Ceuta, Melilla, Madrid, La Rioja y Asturias (comunidades de una provincia, sin puentes ni
  exenciones) entran con los límites de su contrato de producción (0,80/1,75/0,12; Melilla, su excepción gobernada), copiados sin cambio;
  el resto de comunidades sigue fuera (puentes, exención por partición o varias provincias). Orden del Planificador, 09-11.
CAMBIOS 1.2.0 (T-120): Barcelona entra con su exención municipal 08073 (Cornellà, decisión gobernada del contrato, propietario
  2026-11-01); límites iguales a los del molde. B2 del propietario, 09-11.
CAMBIOS 1.1.0 (T-98): APROBADOS_PROPIETARIO admite, por territorio, límites distintos del molde y la exención municipal de
  suelo ya gobernada en el contrato (el motor del ensemble la modela desde m05_gerrychain_engine 1.3.0). La config copia
  los valores del contrato y deja en `decisions` decided_at/decided_by/reason/evidence. Cádiz sale de EXCLUIDOS_POR_ORDEN.
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
import sys as _sys
_RAIZ = str(Path(__file__).resolve().parents[1])
if _RAIZ not in _sys.path:
    _sys.path.insert(0, _RAIZ)
from ddd_core import territorio_ids  # noqa: E402  (T-220: ámbito por el resolutor, nunca por prefijo)

import yaml

MOLDE = "nac26"
EXCLUIDOS_POR_ORDEN: dict[str, str] = {}
EXENCION = "population_floor_exempt_municipalities"
# Lo que el propietario ha aprobado para el ensemble y difiere del molde. La exención se toma del contrato (con su decisión).
APROBADOS_PROPIETARIO = {
    "nac11": {
        "admite": {"population_cap_ratio", "target_tolerance_ratio", EXENCION},
        "decisions": {
            "population_cap_ratio": {
                "decided_at": "2026-11-08",
                "decided_by": "propietario",
                "reason": "Techo 1,16 de Cádiz (tolerancia 0,16) aprobado para el ensemble; se copian del contrato de producción, que no cambia.",
                "evidence": "docs/registro/2026-11-08_claude-t92-ensembles-configs.md (T-92, «techo 1,16 aprobado para el ensemble»); T-98",
            },
        },
    },
    "nac08": {
        "admite": {EXENCION},
        "decisions": {},
    },
}
_AUTONOMICA = {
    "admite": {"population_floor_ratio", "population_cap_ratio", "target_tolerance_ratio", "municipality_atomicity_limit_ratio"},
    "decisions": {
        "limits": {
            "decided_at": "2026-11-09",
            "decided_by": "planificador (delegación del propietario)",
            "reason": "Comunidad uniprovincial: el ensemble copia los límites de su contrato de producción, que no cambia.",
            "evidence": "territorios/<territorio>/config/<territorio>_2025.yaml#validation; T-128",
        },
    },
}
for _tid in ("aut18", "aut19", "aut13", "aut17", "aut03"):
    APROBADOS_PROPIETARIO[_tid] = _AUTONOMICA
LIMITES = ("population_floor_ratio", "population_cap_ratio", "target_tolerance_ratio", "municipality_atomicity_limit_ratio")


def motivo_no_apto(contract: dict, molde: dict) -> str | None:
    val, tc = contract["validation"], contract["territory_contract"]
    admite = APROBADOS_PROPIETARIO.get(contract["meta"]["territory_id"], {}).get("admite", set())
    m02 = contract["modulos"]["modulo_02_construir_adyacencias"]
    if m02.get("topology_bridges"):
        return f"topology_bridges ({len(m02['topology_bridges'])})"
    for key in ("population_floor_exempt_partitions", EXENCION):
        if val.get(key) and key not in admite:
            return f"exención {key}"
    decisiones = val.get("population_floor_exempt_decisions") or {}
    for code in val.get(EXENCION) or []:
        if not {"decided_at", "decided_by", "reason", "evidence"} <= set(decisiones.get(str(code)) or {}):
            return f"exención {code} sin decisión gobernada"
    if len(tc["province_codes"]) != 1:
        return "más de una provincia"
    if tc["k_districts"] < 2:
        return f"K={tc['k_districts']} (un solo distrito, sin ensemble)"
    if m02["working_crs"] != molde["topology"]["working_crs"]:
        return f"CRS {m02['working_crs']}"
    if contract["modulos"]["modulo_03_construir_grafo"]["pop_field"] != molde["fields"]["population"]:
        return "campo de población distinto"
    for key in LIMITES:
        if val[key] != molde["contract"][key] and key not in admite:
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
    aprobado = APROBADOS_PROPIETARIO.get(tid)
    if aprobado:
        val = contract["validation"]
        for key in LIMITES:
            cfg["contract"][key] = val[key]
        decisions = dict(aprobado["decisions"])
        exentos = [str(c) for c in val.get(EXENCION) or []]
        if exentos:
            cfg["contract"][EXENCION] = exentos
            for code in exentos:
                decisions[f"{EXENCION}:{code}"] = dict(val["population_floor_exempt_decisions"][code])
        cfg["decisions"] = decisions
    cfg["workflow"].update(contract=f"territorios/{tid}/config/{tid}_2025.yaml", cache_dir=cache, expected_districts=k)
    return cfg


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root-dir", type=Path, default=Path("."))
    ap.add_argument("--escribir", action="store_true", help="crea las que faltan; sin él solo informa")
    args = ap.parse_args()
    root = args.root_dir
    molde = json.loads((root / "configuracion/ensemble" / f"{MOLDE}.json").read_text(encoding="utf-8"))
    rutas = [root / "territorios" / t / "config" / f"{t}_2025.yaml" for t in territorio_ids.ids_nuevos("NAC")]
    rutas = [r for r in rutas if r.exists()]
    rutas += [root / "territorios" / t / "config" / f"{t}_2025.yaml" for t in sorted(APROBADOS_PROPIETARIO)
              if not territorio_ids.es_nacional(t)]
    for path in rutas:
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
