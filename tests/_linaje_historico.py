"""Catálogo de preparación con el linaje anterior a la adopción de los M06 del 28-10.

Aragón (36321736287) y Extremadura (36472516474) adoptaron los M06 40656036271 y 40656175842.
Las regresiones que ejercitan su producto histórico usan la fila del catálogo y el receipt
territorial del commit d497bf39, guardados en tests/fixtures/linaje_historico.
"""
from __future__ import annotations

import copy
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests/fixtures/linaje_historico"


def historical_catalog(output: Path, territory_id: str) -> Path:
    live = yaml.safe_load((ROOT / "configuracion/catalogo_preparacion.yaml").read_text(encoding="utf-8"))
    row = yaml.safe_load((FIXTURES / f"{territory_id}_catalog_row_2025.yaml").read_text(encoding="utf-8"))
    row = copy.deepcopy(row)
    row["editions"]["2025"]["evidence"]["territorial_product"] = (
        f"tests/fixtures/linaje_historico/{territory_id}_territorial_product_2025.json"
    )
    live["territories"] = [row if r["territory_id"] == territory_id else r for r in live["territories"]]
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(yaml.safe_dump(live, sort_keys=False, allow_unicode=True), encoding="utf-8")
    return output
