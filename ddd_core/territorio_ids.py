# PROYECTO: Diputado de Distrito
# VERSIÓN: 1.1.0
# NOMBRE DE VERSIÓN: Resolutor único de ids de territorio (T-214) con ámbito (T-220)
# FECHA: 2026-11-12
# ESTADO: vigente — T-214
# QUÉ HACE: núcleo del resolutor (CLI en herramientas/resolver_territorio.py). resolver_id(x) acepta el id viejo (`congreso_alava`), el nuevo (`nac01`) o el código de la tabla maestra
#   (`NAC01`) y devuelve el id nuevo; da también el id viejo, la notación, la etiqueta visible («NAC01 · Álava») y el
#   código para la semilla pública. Única fuente: configuracion/notacion_territorial.csv (tabla maestra, D-54).
# CAMBIOS: fichero nuevo.
# MOTIVO: D-61 (id interno en minúsculas, a la vista «NAC01 · Álava», semilla con el código de la tabla maestra) y
#   T-170 §2 (un solo resolutor; prohibido comparar ids con literales fuera de él; contador de lecturas por id viejo).
#   Variante de 350: el sufijo `-350` queda RESERVADO y sin uso (D-76: el mapa de 350 queda fuera del corte); los
#   ids `congreso350_*` no se migran y se devuelven tal cual.
# CAMBIOS 1.1.0 (T-220): las carpetas ya usan el id nuevo; `ambito(x)` (AUT | NAC | NAC350 | CONGRESO) sustituye
#   a la detección por prefijo `congreso_` en código y workflows (test_t220_renombrado lo vigila); `es_nacional(x)`.
#   CLI: `python -m ddd_core.territorio_ids ambito <id>` para los workflows.
# ANTERIOR: legacy/ddd_core/territorio_ids_v1.0.0_20261112.py
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


AMBITO_AGREGADO = "congreso"  # carpeta agregada del Congreso (fuera del renombrado)


def ambito(x: str) -> str:
    """Ámbito de un id: `AUT` (comunidad), `NAC` (circunscripción del Congreso), `NAC350` (variante `congreso350_*`,
    D-76) o `CONGRESO` (la carpeta agregada). Sustituye a `startswith("congreso_")` (T-220). Id desconocido: error."""
    s = str(x).strip()
    if s == AMBITO_AGREGADO:
        return "CONGRESO"
    if s.startswith(PREFIJO_350_LEGACY):
        return "NAC350"
    return territorio(s).ambito


def es_nacional(x: str) -> bool:
    """Circunscripción del Congreso (NAC); un id que no está en la tabla maestra no lo es."""
    try:
        return ambito(x) == "NAC"
    except (IdTerritorioDesconocido, IdReservado):
        return False


def ids_nuevos(ambito_: str | None = None) -> list[str]:
    """Ids nuevos de la tabla maestra (orden de código), opcionalmente de un ámbito (`AUT` | `NAC`)."""
    return [t.id for t in sorted(tabla().values(), key=lambda t: t.codigo) if ambito_ in (None, t.ambito)]


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


def variantes(x: str) -> tuple[str, ...]:
    """Ids con los que puede aparecer un territorio en nombres ya emitidos (artefactos, claves): el dado, el nuevo
    y el viejo, sin repetir. Un id fuera de la tabla maestra solo se tiene a sí mismo."""
    s = str(x)
    try:
        t = territorio(s)
    except (IdTerritorioDesconocido, IdReservado):
        return (s,)
    return tuple(dict.fromkeys((s, t.id, t.id_legacy)))


def fichero_por_id(carpeta, plantilla: str, x: str):
    """Fichero de datos derivados nombrado por id (`datos/composicion/<id>.csv`): el que exista con el id dado, el
    nuevo o el viejo (los productos ya publicados conservan el id viejo, D-61). Si ninguno existe, el del id dado."""
    carpeta = Path(carpeta)
    candidatas = [carpeta / plantilla.format(v) for v in variantes(x)]
    return next((c for c in candidatas if c.exists()), candidatas[0])


def en_mapa(d, x: str, defecto=None):
    """Valor de un dict indexado por id de territorio con cualquiera de sus variantes (dado, nuevo, viejo)."""
    if not isinstance(d, dict):
        return defecto
    for v in variantes(x):
        if v in d:
            return d[v]
    return defecto


def carpeta_de(root, x: str) -> str:
    """Nombre de la carpeta `territorios/<…>` de un territorio bajo `root`: la que exista entre el id dado, el nuevo
    y el viejo (raíces históricas y fixtures conservan el viejo). Si no existe ninguna, el id nuevo (o el dado)."""
    vs = variantes(x)
    base = Path(root) / "territorios"
    existente = next((v for v in vs if (base / v).is_dir()), None)
    if existente:
        return existente
    try:
        return resolver_id(x)
    except (IdTerritorioDesconocido, IdReservado):
        return str(x)


def ruta_nueva(rel: str) -> str:
    """`territorios/<viejo>/…` (y `config/<viejo>_AAAA.yaml`) → la ruta con el id nuevo; el resto, igual."""
    partes = str(rel).replace("\\", "/").split("/")
    if len(partes) < 2 or partes[0] != "territorios":
        return str(rel)
    try:
        t = territorio(partes[1])
    except (IdTerritorioDesconocido, IdReservado):
        return str(rel)
    viejo, partes[1] = partes[1], t.id
    if len(partes) == 4 and partes[2] == "config" and re.fullmatch(re.escape(viejo) + r"_\d{4}\.yaml", partes[3]):
        partes[3] = t.id + partes[3][len(viejo):]
    return "/".join(partes)


def misma_ruta(a: str, b: str) -> bool:
    """Dos rutas del repositorio iguales salvo por el id (viejo o nuevo) de su carpeta de territorio."""
    return str(a) == str(b) or ruta_nueva(str(a)) == ruta_nueva(str(b))


def ruta_existente(root, rel: str):
    """`root/rel` con la carpeta `territorios/<id>/` que exista: la del id nuevo o, en raíces históricas, la del viejo
    (también `config/<id>_AAAA.yaml`). Si no existe ninguna, la del id nuevo. Para leer evidencias y fixtures viejas."""
    root = Path(root)
    partes = str(rel).split("/")
    if len(partes) < 2 or partes[0] != "territorios":
        return root / rel
    try:
        t = territorio(partes[1])
    except (IdTerritorioDesconocido, IdReservado):
        return root / rel
    candidatas = []
    for carpeta in (t.id, t.id_legacy):
        p = list(partes)
        viejo, p[1] = p[1], carpeta
        if len(p) == 4 and p[2] == "config" and re.fullmatch(re.escape(viejo) + r"_\d{4}\.yaml", p[3]):
            p[3] = carpeta + p[3][len(viejo):]
        candidatas.append(root / "/".join(p))
    return next((c for c in candidatas if c.exists()), candidatas[0])


def _main(argv: list[str]) -> int:
    """CLI mínima para workflows: `ambito <id>` | `resolver <id>` (imprime el valor; código 2 si es desconocido)."""
    import sys
    if len(argv) != 2 or argv[0] not in ("ambito", "resolver"):
        print("uso: python -m ddd_core.territorio_ids ambito|resolver <id>", file=sys.stderr)
        return 64
    try:
        print(ambito(argv[1]) if argv[0] == "ambito" else resolver_id(argv[1]))
    except (IdTerritorioDesconocido, IdReservado) as exc:
        print(exc, file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    import sys
    raise SystemExit(_main(sys.argv[1:]))
