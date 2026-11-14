#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PROYECTO: Diputado de Distrito
COMPONENTE: motor 2 — resolutor del repo para la semilla pública de Deslinde
VERSIÓN: 1.2.0
NOMBRE DE VERSIÓN: Deslinde 1.0.0 · resolutor de la tabla maestra
FECHA: 2026-11-14
ESTADO: candidato (motor 2)
CAMBIOS: 1.2.0 — (T-257, D-88) la fórmula se mueve al paquete Deslinde (paquetes/deslinde/src/deslinde/semilla.py);
  aquí queda el resolutor del repo: el código oficial sale de la tabla maestra (configuracion/notacion_territorial.csv)
  con ddd_core.territorio_ids, y se registra en Deslinde al importar ddd_motor2. Mismas semillas y misma descripción.
  1.1.0 — (T-265, D-90) semilla por código oficial. 1.0.1 — ancla aprobada (D-50). 1.0.0 — fichero nuevo.
MOTIVO: T-257 (D-88): Deslinde no depende de rutas del repo; el repo le da la tabla maestra.
ANTERIOR: legacy/ddd_motor2/semilla_v1.1.0_20261114.py
"""
from __future__ import annotations

import hashlib
import sys
from pathlib import Path

from deslinde import territorio as _territorio
from deslinde.reglas import ErrorContrato
from deslinde.semilla import ESQUEMA, FORMULA, MODULO, ROLES, ancla, descripcion, semillas  # noqa: F401 (API)

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ddd_core import territorio_ids  # noqa: E402  (stdlib; única fuente del código, D-61/6)

DERIVACION = "ddd_core.territorio_ids.codigo_semilla(<territorio>) sobre configuracion/notacion_territorial.csv"


def tabla_maestra() -> dict[str, str]:
    """Ruta y sha256 de la tabla maestra con la que se resuelve el código (se publica con la semilla)."""
    ruta = Path(territorio_ids.TABLA_MAESTRA)
    try:
        rel = ruta.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        rel = ruta.as_posix()
    return {"ruta": rel, "sha256": hashlib.sha256(ruta.read_bytes()).hexdigest()}


def codigo(territorio: str) -> str:
    """Código oficial de la tabla maestra (NAC01, AUT17…) para el id viejo, el nuevo o el propio código."""
    t = str(territorio).strip()
    if not t:
        raise ValueError("territorio vacío")
    try:
        return territorio_ids.codigo_semilla(t)
    except (territorio_ids.IdTerritorioDesconocido, territorio_ids.IdReservado) as exc:
        raise ErrorContrato(f"semilla: el territorio {t!r} no está en la tabla maestra ({exc})") from exc


class TablaMaestra:
    """Resolutor de Deslinde con la tabla maestra del repo."""

    derivacion = DERIVACION

    def codigo(self, territorio: str) -> str:
        return codigo(territorio)

    def es_nacional(self, territorio: str) -> bool:
        return territorio_ids.es_nacional(territorio)

    def tabla_maestra(self) -> dict:
        return tabla_maestra()


_territorio.registrar(TablaMaestra())
