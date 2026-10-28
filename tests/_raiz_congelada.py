"""Raíz del repositorio congelada en aee8215e (main tras #311, 2026-10-28).

Las regresiones F10 que fijan recuentos y receipts exactos se evalúan sobre esta raíz: el resto
del árbol se enlaza al repositorio vivo y los ficheros que reescribe cada ejecución completa
(catálogo, contratos, productos, estado operativo) se superponen desde
tests/fixtures/raiz_congelada_aee8215e. Así una ejecución nueva no cambia el caso histórico.
"""
from __future__ import annotations

import atexit
import shutil
import tempfile
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests/fixtures/raiz_congelada_aee8215e"


def _mirror(src: Path, overlay: Path, dst: Path) -> None:
    dst.mkdir(parents=True, exist_ok=True)
    for entry in src.iterdir():
        if entry.name == ".git":
            continue
        layer = overlay / entry.name
        if layer.is_dir() and entry.is_dir():
            _mirror(entry, layer, dst / entry.name)
        elif layer.is_file():
            shutil.copyfile(layer, dst / entry.name)
        else:
            (dst / entry.name).symlink_to(entry)


@lru_cache(maxsize=None)
def frozen_root() -> Path:
    tmp = Path(tempfile.mkdtemp(prefix="ddd-raiz-congelada-"))
    atexit.register(shutil.rmtree, tmp, True)
    _mirror(ROOT, FIXTURE, tmp)
    return tmp
