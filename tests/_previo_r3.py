"""VERSIÓN: 1.0.0
FECHA: 2026-11-14
CAMBIOS: T-322 — raíz congelada del estado de aut01 (receipt) y aut08 (M06 + M08) previo a la campaña r3 (git cc34b0c).
MOTIVO: un P10 nuevo reescribe territorios/*/evidencia y el catálogo; los tests de reutilización que leían el estado vivo
rompían `main`. Los ficheros llevan sha256 en MANIFEST.json (se comprueba al montar); el valor esperado es el de entonces.
ANTERIOR: ninguna (fichero nuevo)
"""
from __future__ import annotations

import hashlib
import json
import shutil
import tempfile
from pathlib import Path

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "previo_r3"


def raiz_previo_r3(tmp: Path | None = None) -> Path:
    """Copia escribible de la raíz congelada, tras verificar el sha256 de cada fichero."""
    files = json.loads((FIXTURE / "MANIFEST.json").read_text(encoding="utf-8"))["files"]
    for rel, sha in files.items():
        if hashlib.sha256((FIXTURE / rel).read_bytes()).hexdigest() != sha:
            raise AssertionError(f"fixture previo_r3 alterado: {rel}")
    raiz = Path(tmp or tempfile.mkdtemp(prefix="ddd-previo-r3-")) / "raiz"
    shutil.copytree(FIXTURE, raiz, ignore=shutil.ignore_patterns("MANIFEST.json"))
    return raiz
