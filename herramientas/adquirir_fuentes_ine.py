#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PROYECTO: Diputado de Distrito
HERRAMIENTA: compatibilidad de adquisición oficial INE
VERSIÓN: 1.1.0
NOMBRE DE VERSIÓN: Delegación declarativa Aragón
FECHA: 2026-09-17
ESTADO: vigente como compatibilidad
FUNCIÓN: mantener el punto de entrada histórico delegando en la adquisición genérica y la declaración de Aragón.
CAMBIOS: elimina de este archivo provincias, edición, cardinalidad, endpoints y nombres de salida específicos de Aragón.
MOTIVO: extraer toda especificidad territorial a catálogo y declaración sin reabrir la certificación de Aragón.
ANTERIOR: legacy/herramientas/adquirir_fuentes_ine_v1.0.1.py
"""
from __future__ import annotations

import argparse
from pathlib import Path

from herramientas.adquirir_fuentes_oficiales import acquire, load_yaml

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", default="inputs")
    parser.add_argument("--environment", choices=["development", "test", "production"], default="development")
    args = parser.parse_args()
    catalog = load_yaml(ROOT / "fuentes/catalogo_oficial.yaml")
    declaration = load_yaml(ROOT / "territorios/aragon/config/fuentes_oficiales.yaml")
    inventory, _ = acquire(
        catalog=catalog,
        declaration=declaration,
        out_dir=(ROOT / args.out_dir).resolve(),
        environment=args.environment,
        acquisition_mode="official_live",
    )
    print(f"Fuentes oficiales materializadas para {inventory['territory']} ({inventory['edition']})")


if __name__ == "__main__":
    main()
