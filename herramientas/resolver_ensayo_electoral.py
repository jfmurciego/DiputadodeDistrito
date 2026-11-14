#!/usr/bin/env python3
# PROYECTO: Diputado de Distrito
# VERSIÓN: 1.0.0
# FECHA: 2026-11-14
# CAMBIOS 1.0.0 (T-332): resuelve la elección del ENSAYO de las generales 2026-11-29 para una entrada de la 03 sin tocar la
#   elección vigente (configuracion/elecciones_vigentes.yaml, congelada por r3). Solo da identidad (election_id y fecha) y
#   exige un contrato `rehearsal` de ensayo en contratos_minsait_provisionales.yaml; nunca promociona ni persiste.
# ANTERIOR: (fichero nuevo)
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import yaml

if str(Path(__file__).resolve().parents[1]) not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from ddd_core.territorio_ids import mismo_territorio  # noqa: E402

UNIVERSE = Path("configuracion/elecciones_generales_2026.yaml")
CONTRACTS = Path("configuracion/contratos_minsait_provisionales.yaml")


def resolve(territory_id: str, root_dir: Path = Path(".")) -> dict:
    root = Path(root_dir)
    universe = yaml.safe_load((root / UNIVERSE).read_text(encoding="utf-8")) or {}
    rows = [r for r in universe.get("circunscripciones") or [] if mismo_territorio(str(r["territory_id"]), str(territory_id))]
    if len(rows) != 1:
        raise SystemExit(f"ENSAYO_TERRITORIO_NO_DECLARADO: {territory_id!r} no está en {UNIVERSE}")
    election_id = str(rows[0]["election_id"])
    election_date = str(universe["election_date"])
    contracts = (yaml.safe_load((root / CONTRACTS).read_text(encoding="utf-8")) or {}).get("contracts") or {}
    contract = contracts.get(election_id)
    if not isinstance(contract, dict) or contract.get("rehearsal") is not True:
        raise SystemExit(f"ENSAYO_SIN_CONTRATO: no hay contrato de ensayo `rehearsal` para {election_id}")
    return {"election_id": election_id, "election_date": election_date, "rehearsal": True, "persist_state": False}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--territory-id", required=True)
    ap.add_argument("--root-dir", type=Path, default=Path("."))
    ns = ap.parse_args()
    print(json.dumps(resolve(ns.territory_id, ns.root_dir), ensure_ascii=False))


if __name__ == "__main__":
    main()
