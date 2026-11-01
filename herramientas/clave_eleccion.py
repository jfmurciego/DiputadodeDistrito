#!/usr/bin/env python3
"""Clave de elección y expansión elección → territorios.

PROYECTO: Diputado de Distrito
VERSIÓN: 1.0.1 · FECHA: 2026-11-01 · ESTADO: candidato
QUÉ HACE: define la clave `ES-<ámbito>-[<unidad>-]<AAAAMMDD>` y la resuelve contra el registro electoral.
  - Ámbito NAC (Congreso): unidad = número INE de provincia (canónico, D-2) o letras de matrícula (alias).
    `ES-NAC-20230723` es la elección entera (todas sus provincias); `ES-NAC-22-20230723` = `ES-NAC-HU-20230723`.
  - Ámbito AUT (autonómicas): unidad = CODAUTO. `ES-AUT-02-20260208` es Aragón; `ES-AUT-20230528` agrupa
    todas las autonómicas registradas con esa fecha.
  La fecha forma parte de la clave: dos elecciones distintas nunca resuelven al mismo territorio, y cada
  elección histórica necesita su propio territory_id (catálogo, checkpoints y artefactos van por territory_id).
  `validar` comprueba que ninguna clave canónica ni territory_id se repite en el registro.
NO HACE: lanzar ejecuciones. El plan que imprime lo consume `.github/workflows/activacion-por-eleccion.yml`.
CAMBIOS 1.0.1: D-2 confirmada (INE canónico); solo matrículas en español, las del catálogo maestro
  (PM, GE, OR…); IB, GI u OU se rechazan.
ANTERIOR: legacy/herramientas/clave_eleccion_v1.0.0_20261101.py
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import date
from pathlib import Path

import yaml

REGISTRY = Path("configuracion/registro_electoral.yaml")
MASTER = Path("configuracion/catalogo_territorios_espana_2025.yaml")


# Workflow, input del territorio y entradas fijas de cada fase.
PHASES = {
    "activar": ("preparacion-legislatura-vigente.yml", "territory", {"operation": "prepare_one"}),
    "electoral": ("preparacion-resultados-electorales.yml", "territory_id", {}),
    "completa": ("ejecucion-completa-proyecto.yml", "territory_id", {}),
}

_KEY = re.compile(r"^ES-(NAC|AUT)-(?:([0-9A-Z]{1,3})-)?(\d{8})$")


class ClaveError(ValueError):
    pass


def normalize(key: str) -> str:
    """Admite minúsculas, `/`, `_` o espacios como separador y la fecha con guiones (2023-07-23)."""
    text = str(key or "").strip().upper()
    text = re.sub(r"(\d{4})-(\d{2})-(\d{2})$", r"\1\2\3", text)
    return re.sub(r"[\s/_]+|-+", "-", text)


def parse(key: str) -> dict:
    m = _KEY.match(normalize(key))
    if not m:
        raise ClaveError(f"Clave de elección no válida: {key!r} (esperado ES-NAC|AUT-[unidad-]AAAAMMDD)")
    scope, unit, raw = m.groups()
    try:
        day = date(int(raw[:4]), int(raw[4:6]), int(raw[6:]))
    except ValueError as exc:
        raise ClaveError(f"Fecha inválida en la clave {key!r}") from exc
    return {"scope": scope, "unit": unit, "date": day.isoformat()}


def _load(path: Path) -> dict:
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return data if isinstance(data, dict) else {}


def load_units(root: Path = Path(".")) -> list[dict]:
    """Una unidad por territorio del registro electoral, con su clave canónica y alias."""
    registry = _load(root / REGISTRY)
    master = _load(root / MASTER) if (root / MASTER).is_file() else {}
    plates = {str(p.get("territory_id")): str(p.get("plate_code") or "")
              for p in master.get("pilot_territories") or []}
    edition = str(registry.get("edition") or "")
    units = []
    for tid, row in (registry.get("territories") or {}).items():
        row = row or {}
        pilot = str(row.get("pilot_code") or "")
        if re.fullmatch(r"C\d{2}", pilot):
            scope, code = "NAC", pilot[1:]
            aliases = [a for a in [plates.get(str(tid), "")] if a]
            dispatch = str(row["name"])
        elif re.fullmatch(r"\d{2}", str(row.get("codauto") or "")):
            scope, code, aliases = "AUT", str(row["codauto"]), []
            dispatch = f"{row['codauto']} {row['name']}"
        else:
            raise ClaveError(f"Territorio sin pilot_code Cnn ni CODAUTO: {tid}")
        day = date.fromisoformat(str(row["election_date"]))
        units.append({
            "key": f"ES-{scope}-{code}-{day:%Y%m%d}", "scope": scope, "code": code,
            "aliases": [f"ES-{scope}-{a}-{day:%Y%m%d}" for a in dict.fromkeys(aliases)],
            "territory_id": str(tid), "name": str(row["name"]), "dispatch_name": dispatch,
            "election_id": str(row["election_id"]), "election_date": day.isoformat(), "edition": edition,
        })
    return units


def _unit_code(scope: str, unit: str, units: list[dict]) -> str:
    if unit.isdigit():
        return unit.zfill(2)
    for u in units:
        if u["scope"] == scope and any(a.split("-")[2] == unit for a in u["aliases"]):
            return u["code"]
    raise ClaveError(f"Matrícula desconocida: {unit}")


def canonical(key: str, units: list[dict]) -> str:
    p = parse(key)
    if p["unit"] is None:
        return f"ES-{p['scope']}-{p['date'].replace('-', '')}"
    return f"ES-{p['scope']}-{_unit_code(p['scope'], p['unit'], units)}-{p['date'].replace('-', '')}"


def _matches_filter(u: dict, token: str) -> bool:
    t = normalize(token)
    if t.isdigit():
        return u["code"] == t.zfill(2)
    names = {normalize(u["name"]), normalize(u["territory_id"]), normalize(u["dispatch_name"])}
    names |= {n.removeprefix("CONGRESO-") for n in names}
    return t in {a.split("-")[2] for a in u["aliases"]} or t in names


def expand(key: str, units: list[dict], only: list[str] | None = None) -> list[dict]:
    """Territorios de una elección (o de una sola unidad), ordenados por código."""
    p = parse(key)
    canon = canonical(key, units)
    if p["unit"] is None:
        rows = [u for u in units if u["scope"] == p["scope"] and u["election_date"] == p["date"]]
    else:
        rows = [u for u in units if u["key"] == canon]
    if not rows:
        raise ClaveError(f"Elección no registrada: {canon}")
    if only:
        tokens = [t for t in only if str(t).strip()]
        unknown = [t for t in tokens if not any(_matches_filter(u, t) for u in rows)]
        if unknown:
            raise ClaveError(f"Filtro fuera de la elección {canon}: {', '.join(unknown)}")
        rows = [u for u in rows if any(_matches_filter(u, t) for t in tokens)]
    return sorted(rows, key=lambda u: u["code"])


def validate(units: list[dict]) -> list[str]:
    """Errores de colisión: misma clave canónica, mismo alias o mismo territory_id."""
    errors, seen = [], {}
    for u in units:
        for k in [u["key"], *u["aliases"]]:
            if k in seen and seen[k] != u["territory_id"]:
                errors.append(f"Clave {k} compartida por {seen[k]} y {u['territory_id']}")
            seen.setdefault(k, u["territory_id"])
    tids = [u["territory_id"] for u in units]
    errors += [f"territory_id repetido: {t}" for t in sorted({t for t in tids if tids.count(t) > 1})]
    return errors


def plan(key: str, phase: str, units: list[dict], only: list[str] | None = None, inputs: dict | None = None) -> dict:
    """Lanzamientos (workflow + inputs) de una fase para toda la elección; no lanza nada."""
    if phase not in PHASES:
        raise ClaveError(f"Fase desconocida: {phase}")
    workflow, field, fixed = PHASES[phase]
    rows = expand(key, units, only)
    dispatches = []
    for u in rows:
        args = {field: u["dispatch_name"], **fixed}
        if phase == "electoral":
            args.update({"data_edition": u["edition"], **(inputs or {})})
        elif phase == "completa":
            args.update({"data_edition": u["edition"], **(inputs or {}), "lanzado_por_eleccion": "true"})
        dispatches.append({"key": u["key"], "territory_id": u["territory_id"], "workflow": workflow, "inputs": args})
    return {"election": canonical(key, units), "phase": phase, "count": len(dispatches), "dispatches": dispatches}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("accion", choices=["canonica", "expandir", "validar", "plan"])
    ap.add_argument("--clave", default="")
    ap.add_argument("--fase", default="completa", choices=sorted(PHASES))
    ap.add_argument("--solo", default="", help="Lista separada por comas (INE, matrícula, CODAUTO o nombre)")
    ap.add_argument("--input", action="append", default=[], help="k=v añadido a cada lanzamiento")
    ap.add_argument("--root-dir", type=Path, default=Path("."))
    a = ap.parse_args(argv)
    try:
        units = load_units(a.root_dir)
        only = [t.strip() for t in a.solo.split(",") if t.strip()] or None
        if a.accion == "validar":
            errors = validate(units)
            print(json.dumps({"ok": not errors, "units": len(units), "errors": errors}, ensure_ascii=False))
            return 1 if errors else 0
        if a.accion == "canonica":
            out = {"canonical": canonical(a.clave, units)}
        elif a.accion == "expandir":
            out = {"election": canonical(a.clave, units), "territories": expand(a.clave, units, only)}
        else:
            extra = dict(kv.split("=", 1) for kv in a.input)
            out = plan(a.clave, a.fase, units, only, extra)
    except ClaveError as exc:
        print(f"::error::{exc}", file=sys.stderr)
        return 2
    print(json.dumps(out, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
