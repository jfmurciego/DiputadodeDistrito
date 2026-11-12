#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PROYECTO: Diputado de Distrito
HERRAMIENTA: compatibilidad de adquisición oficial INE
VERSIÓN: 1.2.1
NOMBRE DE VERSIÓN: Delegación a adquisición verificable
FECHA: 2026-11-12
ESTADO: vigente como compatibilidad
FUNCIÓN: mantener el punto de entrada histórico delegando en la adquisición genérica y la declaración de Aragón.
CAMBIOS: adopta evidencia estructurada, tres modos y salida fail-closed de la implementación genérica.
MOTIVO: evitar una segunda lógica de adquisición específica de Aragón.
CAMBIOS 1.2.1 (T-220): ids de territorio nuevos de la tabla maestra (aut01…nac52, D-61); el id viejo se lee vía ddd_core.territorio_ids.
ANTERIOR: legacy/herramientas/adquirir_fuentes_ine_v1.2.0_20261112.py
"""
from __future__ import annotations

import argparse
from pathlib import Path

from herramientas.adquirir_fuentes_oficiales import acquire, load_yaml

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--evidence-dir", default=".ddd-sources/evidence")
    parser.add_argument("--environment", choices=["development", "test", "production"], default="development")
    parser.add_argument("--acquisition-mode", choices=["official_live", "verified_snapshot"], default=None)
    args = parser.parse_args()
    catalog = load_yaml(ROOT / "fuentes/catalogo_oficial.yaml")
    declaration = load_yaml(ROOT / "territorios/aut02/config/fuentes_oficiales.yaml")
    _, inventory, _, decision = acquire(
        catalog=catalog,
        declaration=declaration,
        evidence_dir=(ROOT / args.evidence_dir).resolve(),
        environment=args.environment,
        acquisition_mode=args.acquisition_mode,
        root_dir=ROOT,
    )
    print(f"Fuentes oficiales materializadas para {inventory['territory']} ({inventory['edition']}): {decision['decision']}")
    if decision["decision"] != "READY":
        raise SystemExit(2)


if __name__ == "__main__":
    main()
