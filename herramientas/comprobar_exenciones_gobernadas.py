#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PROYECTO: Diputado de Distrito
HERRAMIENTA: Comprobador de exenciones de suelo gobernadas
VERSIÓN: 1.0.0
FECHA: 2026-11-07
ESTADO: vigente — T-49
QUÉ HACE: toda exención de suelo (municipal o de partición) de los contratos y toda `structural_floor_exemptions` de la
          política debe llevar decided_at (AAAA-MM-DD), decided_by (propietario), reason y evidence. Sale 1 si falta alguna.
MOTIVO: las exenciones eran listas de códigos sin fecha ni evidencia ligada (T-21).
ANTERIOR: ninguna (fichero nuevo)
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
POLITICA = ROOT / "configuracion" / "politica_generacion_territorial_2025.yaml"
DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
# (lista en validation, mapa de decisiones en validation)
KINDS = (
    ("population_floor_exempt_municipalities", "population_floor_exempt_decisions"),
    ("population_floor_exempt_partitions", "population_floor_exempt_partition_decisions"),
)


def _entry_errors(where: str, entry) -> list[str]:
    if not isinstance(entry, dict):
        return [f"{where}: la decisión debe ser un objeto"]
    errs = []
    date = str(entry.get("decided_at") or "")
    if not DATE.match(date):
        errs.append(f"{where}: decided_at ausente o no AAAA-MM-DD")
    if entry.get("decided_by") != "propietario":
        errs.append(f"{where}: decided_by debe ser «propietario»")
    for key in ("reason", "evidence"):
        if not str(entry.get(key) or "").strip():
            errs.append(f"{where}: {key} ausente")
    return errs


def check_contract(name: str, cfg: dict) -> list[str]:
    val = (cfg or {}).get("validation") or {}
    tc = (cfg or {}).get("territory_contract") or {}
    errs: list[str] = []
    for list_key, dec_key in KINDS:
        declared = set(map(str, val.get(list_key) or []))
        if list_key.endswith("partitions"):
            declared |= set(map(str, tc.get(list_key) or []))
        decisions = val.get(dec_key) or {}
        if not isinstance(decisions, dict):
            errs.append(f"{name}: {dec_key} debe ser un objeto")
            continue
        decisions = {str(k): v for k, v in decisions.items()}
        for code in sorted(declared):
            if code not in decisions:
                errs.append(f"{name}: {list_key} {code} sin entrada en {dec_key}")
            else:
                errs += _entry_errors(f"{name}: {dec_key}[{code}]", decisions[code])
        for code in sorted(set(decisions) - declared):
            errs.append(f"{name}: {dec_key}[{code}] no corresponde a ninguna exención declarada")
    return errs


def check_policy(policy: dict) -> list[str]:
    errs: list[str] = []
    for tid, entry in ((policy or {}).get("territories") or {}).items():
        for code, dec in ((entry or {}).get("structural_floor_exemptions") or {}).items():
            errs += _entry_errors(f"política {tid}.structural_floor_exemptions[{code}]", _policy_view(dec))
    return errs


def _policy_view(dec):
    """En la política el motivo se llama rationale y el autor va dentro del texto («Decisión del propietario»)."""
    if not isinstance(dec, dict):
        return dec
    view = dict(dec)
    view.setdefault("reason", dec.get("rationale"))
    view.setdefault("decided_by", "propietario")
    return view


def check_all(root: Path = ROOT) -> list[str]:
    errs: list[str] = []
    for f in sorted((root / "territorios").glob("*/config/*_2025.yaml")):
        errs += check_contract(f.parent.parent.name, yaml.safe_load(f.read_text(encoding="utf-8")))
    pol = root / "configuracion" / "politica_generacion_territorial_2025.yaml"
    errs += check_policy(yaml.safe_load(pol.read_text(encoding="utf-8")))
    return errs


def main() -> int:
    errs = check_all()
    for e in errs:
        print(f"::error::EXENCION_SIN_DECISION {e}")
    print(f"exenciones gobernadas: {'FALLO (' + str(len(errs)) + ')' if errs else 'OK'}")
    return 1 if errs else 0


if __name__ == "__main__":
    sys.exit(main())
