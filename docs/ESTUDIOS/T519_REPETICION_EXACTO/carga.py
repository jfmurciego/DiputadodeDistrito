#!/usr/bin/env python3
"""T-519 · carga de fondo: un núcleo al 100 % con tráfico de memoria (sha256 sobre 64 MB), hasta que lo maten."""
import hashlib

BLOQUE = bytes(64 * 1024 * 1024)
while True:
    hashlib.sha256(BLOQUE).digest()
    sum(i * i for i in range(2_000_000))
