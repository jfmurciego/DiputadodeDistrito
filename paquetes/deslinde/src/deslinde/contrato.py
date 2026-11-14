#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PROYECTO: Diputado de Distrito
COMPONENTE: Deslinde — lectura del contrato del territorio
VERSIÓN: 1.0.0
NOMBRE DE VERSIÓN: Deslinde 1.0.0 · contrato materializado
FECHA: 2026-11-14
ESTADO: candidato (paquete Deslinde, T-257)
CAMBIOS: 1.0.0 — fichero nuevo (T-257, D-88).
MOTIVO: Deslinde lee un contrato YA materializado (bloque `validation` con K, suelo, techo y tolerancia;
  `generation_state.source_inputs` con los sha256 del padrón y del seccionado). Dentro del repo se lee con
  ddd_core.config.load_params_yaml (materializa la política, como hasta ahora); fuera, con yaml.safe_load.
ANTERIOR: ninguna (fichero nuevo)
"""
from __future__ import annotations

from pathlib import Path
from typing import Any


def cargar(ruta: str | Path) -> dict[str, Any]:
    try:
        from ddd_core.config import load_params_yaml  # noqa: PLC0415  (solo dentro del repo)
    except ImportError:
        import yaml  # noqa: PLC0415
        with open(ruta, encoding="utf-8") as fh:
            return yaml.safe_load(fh) or {}
    return load_params_yaml(str(ruta))
