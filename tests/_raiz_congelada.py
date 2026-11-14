"""Raíz del repositorio congelada en aee8215e (main tras #311, 2026-10-28).

Las regresiones que fijan recuentos, receipts y linajes exactos de territorios reales se evalúan
sobre esta raíz. Código y fixtures se enlazan al repositorio vivo; las zonas de estado que
reescribe cada ejecución completa (configuracion/, orchestracion/, publicado/dashboard/ y
config/ y evidencia/ de cada territorio) contienen sólo los ficheros que existían en aee8215e:
los idénticos se enlazan, los reescritos después se toman de
tests/fixtures/raiz_congelada_aee8215e/overlay y los añadidos después no aparecen.

T-220: en aee8215e las carpetas llevaban el id viejo (`territorios/galicia`); la raíz congelada las conserva con ese
nombre y enlaza cada carpeta viva renombrada (`territorios/aut12`) bajo su id viejo. Un fichero de aee8215e se busca
en su ruta viva (id nuevo, `config/<nuevo>_AAAA.yaml`) y solo se enlaza si su sha256 coincide.
"""
from __future__ import annotations

import atexit
import hashlib
import json
import re
import shutil
import sys
import tempfile
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from ddd_core import territorio_ids  # noqa: E402

FIXTURE = ROOT / "tests/fixtures/raiz_congelada_aee8215e"
FROZEN = re.compile(r"^(configuracion|orchestracion|publicado/dashboard|territorios/[^/]+/(config|evidencia))$")


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _nuevo(viejo: str) -> str | None:
    """Id nuevo de una carpeta de aee8215e, o None si no cambió de nombre."""
    try:
        nuevo = territorio_ids.resolver_id(viejo)
    except (territorio_ids.IdTerritorioDesconocido, territorio_ids.IdReservado):
        return None
    return nuevo if nuevo != viejo else None


def _ruta_viva(rel: str) -> Path:
    partes = rel.split("/")
    if len(partes) > 1 and partes[0] == "territorios" and (nuevo := _nuevo(partes[1])):
        viejo, partes[1] = partes[1], nuevo
        if len(partes) == 4 and partes[2] == "config" and re.fullmatch(re.escape(viejo) + r"_\d{4}\.yaml", partes[3]):
            partes[3] = nuevo + partes[3][len(viejo):]
    return ROOT / "/".join(partes)


def _materialize_frozen(relative: str, files: dict[str, str], root: Path) -> None:
    prefix = relative + "/"
    for rel, expected in files.items():
        if not rel.startswith(prefix):
            continue
        target = root / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        live = _ruta_viva(rel)
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


def _mirror(src: Path, dst: Path, files: dict[str, str], root: Path, rel_src: str | None = None) -> None:
    dst.mkdir(parents=True, exist_ok=True)
    viejos = {}
    if src == ROOT / "territorios":  # T-220: cada carpeta renombrada vuelve a su id viejo
        viejos = {t.id: t.id_legacy for t in territorio_ids.tabla().values()}
    for entry in src.iterdir():
        if entry.name == ".git":
            continue
        nombre = viejos.get(entry.name, entry.name)
        rel = f"{rel_src}/{nombre}" if rel_src else entry.relative_to(ROOT).as_posix()
        if nombre != entry.name:
            rel = f"territorios/{nombre}"
        if FROZEN.match(rel):
            (root / rel).mkdir(parents=True, exist_ok=True)
            _materialize_frozen(rel, files, root)
        elif entry.is_dir() and any(f.startswith(rel + "/") for f in files) and not entry.is_symlink():
            _mirror(entry, dst / nombre, files, root, rel)
        elif nombre == entry.name:
            (dst / entry.name).symlink_to(entry)
        # una carpeta renombrada sin ficheros de aee8215e no existía entonces: no aparece


@lru_cache(maxsize=None)
def frozen_root() -> Path:
    files = json.loads((FIXTURE / "MANIFEST.json").read_text(encoding="utf-8"))["files"]
    tmp = Path(tempfile.mkdtemp(prefix="ddd-raiz-congelada-"))
    atexit.register(shutil.rmtree, tmp, True)
    _mirror(ROOT, tmp, files, tmp)
    return tmp
