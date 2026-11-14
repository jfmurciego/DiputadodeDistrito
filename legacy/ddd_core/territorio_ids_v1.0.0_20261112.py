# PROYECTO: Diputado de Distrito
# VERSIÓN: 1.0.0
# NOMBRE DE VERSIÓN: Resolutor único de ids de territorio (T-214, corte 5.0.0 paso 1)
# FECHA: 2026-11-10
# ESTADO: vigente — T-214
# QUÉ HACE: núcleo del resolutor (CLI en herramientas/resolver_territorio.py). resolver_id(x) acepta el id viejo (`congreso_alava`), el nuevo (`nac01`) o el código de la tabla maestra
#   (`NAC01`) y devuelve el id nuevo; da también el id viejo, la notación, la etiqueta visible («NAC01 · Álava») y el
#   código para la semilla pública. Única fuente: configuracion/notacion_territorial.csv (tabla maestra, D-54).
# CAMBIOS: fichero nuevo.
# MOTIVO: D-61 (id interno en minúsculas, a la vista «NAC01 · Álava», semilla con el código de la tabla maestra) y
#   T-170 §2 (un solo resolutor; prohibido comparar ids con literales fuera de él; contador de lecturas por id viejo).
#   Variante de 350: el sufijo `-350` queda RESERVADO y sin uso (D-76: el mapa de 350 queda fuera del corte); los
#   ids `congreso350_*` no se migran y se devuelven tal cual.
# ANTERIOR: ninguna (fichero nuevo)
"""Resolutor único de identificadores de territorio (id viejo ↔ id nuevo ↔ código AUT/NAC)."""
from __future__ import annotations

import csv
import io
import re
from collections import Counter
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TABLA_MAESTRA = ROOT / "configuracion" / "notacion_territorial.csv"
SUFIJO_350 = "-350"  # RESERVADO (D-76): no se emite ni se resuelve en el corte 5.0.0
PREFIJO_350_LEGACY = "congreso350_"
_RE_CODIGO = re.compile(r"^(aut|nac)(\d\d)$", re.IGNORECASE)
_RE_350 = re.compile(r"^(aut|nac)\d\d-350$", re.IGNORECASE)

LECTURAS_LEGACY: Counter = Counter()  # T-170 §2: la retirada de alias exige este contador a cero un ciclo


class IdTerritorioDesconocido(KeyError):
    pass


class IdReservado(ValueError):
    pass


@dataclass(frozen=True)
class Territorio:
    codigo: str      # NAC01 (tabla maestra)
    ambito: str      # AUT | NAC
    nombre_es: str   # Álava
    id_legacy: str   # congreso_alava

    @property
    def id(self) -> str:
        return self.codigo.lower()

    @property
    def etiqueta(self) -> str:
        return f"{self.codigo} · {self.nombre_es}"


def _leer_tabla(texto: str) -> dict[str, Territorio]:
    filas = [l for l in texto.splitlines() if l and not l.startswith("#")]
    tabla: dict[str, Territorio] = {}
    for r in csv.DictReader(io.StringIO("\n".join(filas))):
        t = Territorio(r["codigo"].strip(), r["ambito"].strip(), r["nombre_es"].strip(), r["id_interno"].strip())
        if not _RE_CODIGO.match(t.codigo) or t.codigo[:3].upper() != t.ambito:
            raise ValueError(f"tabla maestra: código mal formado {t.codigo!r}")
        if t.id in tabla:
            raise ValueError(f"tabla maestra: código duplicado {t.codigo}")
        tabla[t.id] = t
    legacy = Counter(t.id_legacy for t in tabla.values())
    dup = [k for k, n in legacy.items() if n > 1]
    if dup:
        raise ValueError(f"tabla maestra: id viejo repetido {dup}")
    choque = set(legacy) & set(tabla)
    if choque:
        raise ValueError(f"tabla maestra: id viejo que colisiona con uno nuevo {sorted(choque)}")
    return tabla


@lru_cache(maxsize=1)
def tabla() -> dict[str, Territorio]:
    return _leer_tabla(TABLA_MAESTRA.read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def _por_legacy() -> dict[str, Territorio]:
    return {t.id_legacy: t for t in tabla().values()}


def es_variante_350(x: str) -> bool:
    return str(x).startswith(PREFIJO_350_LEGACY) or bool(_RE_350.match(str(x)))


def territorio(x: str) -> Territorio:
    """Territorio de la tabla maestra para un id viejo, un id nuevo o un código. Coincidencia exacta por id."""
    s = str(x).strip()
    if _RE_350.match(s):
        raise IdReservado(f"{s}: el sufijo {SUFIJO_350} está reservado y sin uso (D-76)")
    m = _RE_CODIGO.match(s)
    if m:
        t = tabla().get(s.lower())
        if t:
            return t
    t = _por_legacy().get(s)
    if t:
        LECTURAS_LEGACY[s] += 1
        return t
    raise IdTerritorioDesconocido(f"id de territorio desconocido: {s!r} (ni viejo, ni nuevo, ni código AUT/NAC)")


def resolver_id(x: str) -> str:
    """Id nuevo (`nac01`). Los `congreso350_*` no se migran en el corte (D-76) y se devuelven tal cual."""
    if str(x).startswith(PREFIJO_350_LEGACY):
        return str(x)
    return territorio(x).id


def id_legacy(x: str) -> str:
    if str(x).startswith(PREFIJO_350_LEGACY):
        return str(x)
    return territorio(x).id_legacy


def notacion(x: str) -> str:
    return territorio(x).codigo


def etiqueta(x: str) -> str:
    return territorio(x).etiqueta


def codigo_semilla(x: str) -> str:
    """Código de la tabla maestra para la semilla pública (D-61, DECISIÓN 6): igual con id viejo o nuevo."""
    return territorio(x).codigo


def mismo_territorio(a: str, b: str) -> bool:
    """Lectura con ambos ids: `congreso_alava` y `nac01` son el mismo territorio; `madrid` y `nac28`, no.

    Un id que no está en la tabla maestra (ids sintéticos de pruebas) solo coincide consigo mismo.
    """
    a, b = str(a), str(b)
    if a == b:
        return True
    try:
        return resolver_id(a) == resolver_id(b)
    except (IdTerritorioDesconocido, IdReservado):
        return False
