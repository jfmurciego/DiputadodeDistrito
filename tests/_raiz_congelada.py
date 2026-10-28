"""Raíz del repositorio congelada en aee8215e (main tras #311, 2026-10-28).

Las regresiones que fijan recuentos, receipts y linajes exactos de territorios reales se evalúan
sobre esta raíz. Código y fixtures se enlazan al repositorio vivo; las zonas de estado que
reescribe cada ejecución completa (configuracion/, orchestracion/, publicado/dashboard/ y
config/ y evidencia/ de cada territorio) contienen sólo los ficheros que existían en aee8215e:
los idénticos se enlazan, los reescritos después se toman de
tests/fixtures/raiz_congelada_aee8215e/overlay y los añadidos después no aparecen.
"""
from __future__ import annotations

import atexit
import hashlib
import json
import re
import shutil
import tempfile
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests/fixtures/raiz_congelada_aee8215e"
FROZEN = re.compile(r"^(configuracion|orchestracion|publicado/dashboard|territorios/[^/]+/(config|evidencia))$")


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _materialize_frozen(relative: str, files: dict[str, str], root: Path) -> None:
    prefix = relative + "/"
    for rel, expected in files.items():
        if not rel.startswith(prefix):
            continue
        target = root / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        live = ROOT / rel
        overlay = FIXTURE / "overlay" / rel
        if live.is_file() and _sha(live) == expected:
            target.symlink_to(live)
        elif overlay.is_file() and _sha(overlay) == expected:
            shutil.copyfile(overlay, target)
        else:
            raise RuntimeError(
                f"raíz congelada incompleta: {rel} cambió después de aee8215e y no está en overlay/; "
                "añade su versión de aee8215e (git show aee8215e:<ruta>) a tests/fixtures/raiz_congelada_aee8215e/overlay"
            )


def _mirror(src: Path, dst: Path, files: dict[str, str], root: Path) -> None:
    dst.mkdir(parents=True, exist_ok=True)
    for entry in src.iterdir():
        if entry.name == ".git":
            continue
        rel = entry.relative_to(ROOT).as_posix()
        if FROZEN.match(rel):
            (root / rel).mkdir(parents=True, exist_ok=True)
            _materialize_frozen(rel, files, root)
        elif entry.is_dir() and any(f.startswith(rel + "/") for f in files) and not entry.is_symlink():
            _mirror(entry, dst / entry.name, files, root)
        else:
            (dst / entry.name).symlink_to(entry)


@lru_cache(maxsize=None)
def frozen_root() -> Path:
    files = json.loads((FIXTURE / "MANIFEST.json").read_text(encoding="utf-8"))["files"]
    tmp = Path(tempfile.mkdtemp(prefix="ddd-raiz-congelada-"))
    atexit.register(shutil.rmtree, tmp, True)
    _mirror(ROOT, tmp, files, tmp)
    return tmp
