#!/usr/bin/env python3
"""Huella de puentes topológicos antes de M02 (T-09).

PROYECTO: Diputado de Distrito
VERSIÓN: 1.0.0 · FECHA: 2026-11-01 · ESTADO: candidato
QUÉ HACE: comprueba los `topology_bridges` de M02 de cada contrato contra el inventario de secciones que
  consumirá M02 y clasifica cada puente:
    VALIDO · CAMPOS_INCOMPLETOS · EXTREMOS_IGUALES · MUNICIPIO_INEXISTENTE · CODIGO_SECCION_CAMBIADO
    (el municipio existe pero la sección no: recodificación INE) · FUERA_DE_AMBITO (un extremo no cae en el
    `admin_scope` declarado) · FUERA_DE_PROVINCIA.
  Inventario: el ZIP oficial de Interior por mesa (secciones 2023, `--zip`) o el GeoJSON M01 del run
  (`--sections-geojson`, el que lee M02).
NO HACE: medir colindancia ni si el puente reduce componentes; eso exige las aristas de M02 y lo valida
  `ddd_core.topology_preflight.validate_topology_bridges` dentro del módulo.
ANTERIOR: —
"""
from __future__ import annotations

import argparse
import json
import sys
import zipfile
from pathlib import Path

import yaml

REQUIRED = ("u", "v", "admin_scope", "edge_type", "reason", "source")


def sections_from_geojson(path: Path, field: str = "CUSEC_KEY") -> set[str]:
    """CUSEC del GeoJSON (zip o plano) que consume M02."""
    if path.suffix == ".zip":
        with zipfile.ZipFile(path) as archive:
            name = next(n for n in archive.namelist() if n.endswith((".geojson", ".json")))
            data = json.loads(archive.read(name))
    else:
        data = json.loads(path.read_text(encoding="utf-8"))
    return {str((f.get("properties") or {}).get(field) or "") for f in data.get("features") or []} - {""}


def sections_from_zip(path: Path) -> set[str]:
    try:
        from herramientas.generar_provincias_congreso import sections_2023
    except ModuleNotFoundError:
        from generar_provincias_congreso import sections_2023
    return sections_2023(path)


def _in_scope(code: str, scope: str) -> bool:
    kind, _, value = scope.partition(":")
    if kind == "province":
        return code[:2] == value.zfill(2)
    if kind == "municipality":
        return code[:5] == value
    return False


def classify(bridge: dict, sections: set[str], provinces: set[str]) -> str:
    if any(bridge.get(k) in (None, "") for k in REQUIRED):
        return "CAMPOS_INCOMPLETOS"
    u, v = str(bridge["u"]), str(bridge["v"])
    if u == v:
        return "EXTREMOS_IGUALES"
    municipalities = {s[:5] for s in sections}
    for code in (u, v):
        if code not in sections:
            return "CODIGO_SECCION_CAMBIADO" if code[:5] in municipalities else "MUNICIPIO_INEXISTENTE"
    scope = str(bridge["admin_scope"])
    if not (_in_scope(u, scope) and _in_scope(v, scope)):
        return "FUERA_DE_AMBITO"
    if provinces and not {u[:2], v[:2]} <= provinces:
        return "FUERA_DE_PROVINCIA"
    return "VALIDO"


def check_contract(path: Path, sections: set[str]) -> dict:
    cfg = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    m02 = (cfg.get("modulos") or {}).get("modulo_02_construir_adyacencias") or {}
    provinces = {str(c).zfill(2) for c in ((cfg.get("territory_contract") or {}).get("province_codes") or [])}
    if not provinces:
        provinces = {s[:2] for s in sections}
    rows = []
    for bridge in m02.get("topology_bridges") or []:
        rows.append({"u": str(bridge.get("u")), "v": str(bridge.get("v")),
                     "admin_scope": bridge.get("admin_scope"), "edge_type": bridge.get("edge_type"),
                     "status": classify(bridge, sections, provinces)})
    broken = [r for r in rows if r["status"] != "VALIDO"]
    return {"contract": path.as_posix(), "bridges": len(rows), "broken": len(broken),
            "status": "PASS" if not broken else "BLOCK", "rows": rows}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Comprueba los puentes de M02 contra el inventario de secciones.")
    ap.add_argument("--root-dir", type=Path, default=Path("."))
    ap.add_argument("--params", type=Path, action="append", default=[],
                    help="Contrato(s); por defecto todos los territorios/congreso_*/config/*_2025.yaml")
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--zip", type=Path, help="ZIP oficial de Interior por mesa (secciones 2023)")
    src.add_argument("--sections-geojson", type=Path, help="GeoJSON M01 que consume M02")
    ap.add_argument("--json-output", type=Path)
    a = ap.parse_args(argv)
    sections = sections_from_zip(a.zip) if a.zip else sections_from_geojson(a.sections_geojson)
    contracts = a.params or sorted((a.root_dir / "territorios").glob("congreso_*/config/congreso_*_2025.yaml"))
    reports = [check_contract(p, sections) for p in contracts]
    summary = {"schema": "ddd.bridge-fingerprint/1.0", "sections": len(sections),
               "status": "PASS" if all(r["status"] == "PASS" for r in reports) else "BLOCK", "contracts": reports}
    if a.json_output:
        a.json_output.parent.mkdir(parents=True, exist_ok=True)
        a.json_output.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    for r in reports:
        for row in r["rows"]:
            if row["status"] != "VALIDO":
                print(f"::error::Puente {row['u']}-{row['v']} ({row['admin_scope']}) en {r['contract']}: {row['status']}",
                      file=sys.stderr)
    print(json.dumps({k: v for k, v in summary.items() if k != "contracts"} |
                     {"blocked": [r["contract"] for r in reports if r["status"] != "PASS"],
                      "bridges": sum(r["bridges"] for r in reports)}, ensure_ascii=False))
    return 0 if summary["status"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
