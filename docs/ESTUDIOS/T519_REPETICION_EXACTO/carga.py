#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PROYECTO: Diputado de Distrito
COMPONENTE: estudio T-519 (repetición del exacto de Deslinde) — carga de fondo
VERSIÓN: 1.0.0
NOMBRE DE VERSIÓN: Carga de fondo
FECHA: 2026-11-28
ESTADO: estudio (no cambia el motor ni lanza nada)
CAMBIOS: fichero nuevo.
MOTIVO: T-509, hallazgo A1-4: comprobar si el mapa y la huella del exacto se repiten cuando cambia la velocidad de la máquina.
ANTERIOR: ninguna (fichero nuevo)
QUÉ HACE: carga de fondo: un núcleo al 100 % con tráfico de memoria (sha256 sobre 64 MB), hasta que lo maten."""
import hashlib

BLOQUE = bytes(64 * 1024 * 1024)
while True:
    hashlib.sha256(BLOQUE).digest()
    sum(i * i for i in range(2_000_000))
