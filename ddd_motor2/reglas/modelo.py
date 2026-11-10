#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PROYECTO: Diputado de Distrito
COMPONENTE: núcleo de reglas del motor 2 — modelo declarativo (Unidad, Problema, Criterio, Reglas)
VERSIÓN: 1.0.0
NOMBRE DE VERSIÓN: Núcleo único de reglas · F1
FECHA: 2026-11-10
ESTADO: candidato (motor 2; producción no lo importa)
CAMBIOS: fichero nuevo.
MOTIVO: T-160 (F1 de docs/ARQUITECTURA/NUCLEO_REGLAS.md): una sola definición de «plan válido» con las decisiones
  de criterio como parámetros (Criterio), para que la batería T-132 cuente cuántos territorios cambian de veredicto
  con cada opción.
ANTERIOR: ninguna (fichero nuevo)
REGLAS DE DISEÑO:
  - Solo stdlib. Poblaciones enteras; límites como fracciones exactas (sin márgenes 1e-9: divergencia 7).
  - El municipio, la provincia y la partición son CAMPOS de la unidad; nunca se interpreta ddd_unit_id (divergencia 4).
  - Códigos normalizados una sola vez (norm_codigo) en unidades y contrato (divergencias 5 y 6).
  - Si falta un dato o una clave obligatoria, falla (ErrorContrato/ErrorDatos); nunca se anula una regla en silencio
    (divergencia 3).
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from fractions import Fraction
from typing import Any, Iterable, Mapping

# Códigos estables de violación (los consume la batería T-132).
CODIGOS = (
    "R-ATOM", "R-K", "R-POB-SUELO", "R-POB-TECHO", "R-TOL", "R-CONTIG", "R-PROV", "R-CUOTA",
    "R-MUN-MIN", "R-MUN-MAX", "R-MUN-MIXTOS", "R-NUCLEO",
)


class ErrorContrato(ValueError):
    """El contrato no declara algo que el núcleo exige (no se rellena con valores por defecto ocultos)."""


class ErrorDatos(ValueError):
    """El problema no trae un campo que una regla activa necesita."""


def norm_codigo(valor: Any, ancho: int = 2) -> str | None:
    """Normaliza un código territorial: texto sin espacios; si es solo cifras, relleno a `ancho` (provincia 2,
    municipio 5). «7» y «07» casan; «35-C02» queda igual. None o vacío → None."""
    if valor is None:
        return None
    if isinstance(valor, float) and valor.is_integer():
        valor = int(valor)
    texto = str(valor).strip()
    if not texto:
        return None
    return texto.zfill(ancho) if texto.isdigit() else texto


# --------------------------------------------------------------------------- datos
@dataclass(frozen=True)
class Unidad:
    """Unidad atómica (la sección es una unidad trivial). `unidad_r012` es la clave de disciplina municipal cuando el
    contrato parte municipios en unidades internas (`connected_internal_units`, p. ej. «35012:35-C01»).
    `desglose`: para unidades atómicas que abarcan varios municipios (grupos administrativos, p. ej. Cataluña
    «25215|25234»), los municipios con su población; entonces `municipio` va vacío y R012 y las exenciones cuentan cada
    municipio por separado, como la validación por secciones. El valor de municipio puede llevar partición
    («35016:35-C01», campo DDD_MUNICIPALITY_PARTITION de las islas): la exención compara el código antes de «:»."""

    id: str
    poblacion: int
    municipio: str | None = None
    provincia: str | None = None
    particion: str | None = None
    unidad_r012: str | None = None
    nucleo_cerrado: str | None = None
    desglose: tuple[tuple[str, int], ...] = ()

    def __post_init__(self):
        if not isinstance(self.poblacion, int) or isinstance(self.poblacion, bool) or self.poblacion < 0:
            raise ErrorDatos(f"unidad {self.id}: población debe ser entero >= 0 (recibido {self.poblacion!r})")
        object.__setattr__(self, "id", str(self.id))
        object.__setattr__(self, "municipio", norm_codigo(self.municipio, 5))
        object.__setattr__(self, "provincia", norm_codigo(self.provincia, 2))
        object.__setattr__(self, "particion", norm_codigo(self.particion, 2))
        if self.unidad_r012 is not None:
            object.__setattr__(self, "unidad_r012", str(self.unidad_r012).strip() or None)
        if self.nucleo_cerrado is not None:
            object.__setattr__(self, "nucleo_cerrado", str(self.nucleo_cerrado).strip() or None)
        if self.desglose:
            desglose = tuple(sorted((norm_codigo(m, 5), int(p)) for m, p in self.desglose))
            if self.municipio is not None:
                raise ErrorDatos(f"unidad {self.id}: municipio y desglose a la vez")
            if len({m for m, _ in desglose}) != len(desglose) or None in {m for m, _ in desglose}:
                raise ErrorDatos(f"unidad {self.id}: desglose con municipios vacíos o repetidos")
            if sum(p for _, p in desglose) != self.poblacion:
                raise ErrorDatos(f"unidad {self.id}: el desglose no suma la población de la unidad")
            object.__setattr__(self, "desglose", desglose)

    def piezas(self, campo: str) -> tuple[tuple[str | None, int], ...]:
        """(clave, población) de la unidad para la disciplina municipal según el campo de R012."""
        if campo == "municipio" and self.desglose:
            return self.desglose
        return ((getattr(self, campo), self.poblacion),)

    def municipios(self) -> set[str]:
        """Códigos INE de municipio de la unidad (antes de «:» si el valor lleva partición)."""
        valores = [m for m, _ in self.desglose] if self.desglose else [self.municipio]
        return {str(m).split(":", 1)[0] for m in valores if m is not None}


@dataclass(frozen=True)
class Problema:
    """Grafo operativo: unidades, aristas y puentes topológicos declarados aparte (para poder informar de ellos)."""

    unidades: tuple[Unidad, ...]
    aristas: tuple[tuple[str, str], ...]
    puentes: tuple[tuple[str, str], ...] = ()
    por_id: Mapping[str, Unidad] = field(init=False, repr=False, compare=False)
    poblacion_total: int = field(init=False, repr=False, compare=False)

    def __post_init__(self):
        unidades = tuple(self.unidades)
        por_id: dict[str, Unidad] = {}
        for u in unidades:
            if u.id in por_id:
                raise ErrorDatos(f"unidad duplicada: {u.id}")
            por_id[u.id] = u

        def limpiar(pares: Iterable) -> tuple[tuple[str, str], ...]:
            out = set()
            for a, b in pares:
                a, b = str(a), str(b)
                if a not in por_id or b not in por_id:
                    raise ErrorDatos(f"arista con unidad desconocida: {a}-{b}")
                if a != b:
                    out.add((a, b) if a < b else (b, a))
            return tuple(sorted(out))

        object.__setattr__(self, "unidades", unidades)
        object.__setattr__(self, "aristas", limpiar(self.aristas))
        object.__setattr__(self, "puentes", limpiar(self.puentes))
        object.__setattr__(self, "por_id", por_id)
        object.__setattr__(self, "poblacion_total", sum(u.poblacion for u in unidades))

    def adyacencia(self, con_puentes: bool) -> dict[str, set[str]]:
        adj: dict[str, set[str]] = {u.id: set() for u in self.unidades}
        for a, b in self.aristas + (self.puentes if con_puentes else ()):
            adj[a].add(b)
            adj[b].add(a)
        return adj


# --------------------------------------------------------------------------- decisiones de criterio
OPCIONES = {
    # (a) métrica, como VAL/GCP; (b) dura, como GCE (con exención por debajo para distritos exentos de suelo).
    "tolerancia": ("metrica", "dura"),
    # (a) del contrato (1 por defecto de política si no lo declara); (b) 1 fijo, como VAL.
    "max_mixtos": ("contrato", "fijo_1"),
    # (a) obligatoria en el contrato; (b) True si falta (GCP/GCE); (c) False si falta (VAL).
    "provincia_defecto": ("obligatoria", "si", "no"),
    # Exención por partición en distritos con varias: (a) basta una; (b) todas; (c) la primera ordenada (VAL).
    "exencion_particion": ("todas", "alguna", "primera"),
    # Cadena frente a enumeración: (a) tamaño a priori; (b) presupuesto de nodos; (c) diagnóstico de la cadena.
    "metodo": ("presupuesto", "tamano", "diagnostico"),
}
MAX_MIXTOS_POLITICA = 1


@dataclass(frozen=True)
class Criterio:
    """Decisiones de criterio. Los valores por defecto son los aprobados por el propietario (D-44, 10-11); siguen
    siendo parámetros para que la batería mida cuántos territorios cambian de veredicto con cada opción."""

    tolerancia: str = "metrica"
    max_mixtos: str = "contrato"
    provincia_defecto: str = "obligatoria"
    exencion_particion: str = "todas"
    metodo: str = "presupuesto"
    presupuesto_nodos: int = 200_000
    tamano_max_k: int = 3
    tamano_max_unidades: int = 40
    diagnostico_min_unicos: float = 0.10
    diagnostico_max_bucles: float = 0.90
    contiguidad_con_puentes: bool = True

    def __post_init__(self):
        for nombre, validas in OPCIONES.items():
            if getattr(self, nombre) not in validas:
                raise ValueError(f"Criterio.{nombre}={getattr(self, nombre)!r}; opciones: {validas}")
        if self.presupuesto_nodos <= 0 or self.tamano_max_k < 1 or self.tamano_max_unidades < 1:
            raise ValueError("Criterio: presupuesto y umbrales de tamaño deben ser positivos")
        if not (0.0 < self.diagnostico_min_unicos <= 1.0 and 0.0 <= self.diagnostico_max_bucles < 1.0):
            raise ValueError("Criterio: umbrales de diagnóstico fuera de rango")


# --------------------------------------------------------------------------- reglas
def _ratio(val: Mapping, clave: str) -> Fraction:
    if clave not in val or val[clave] is None:
        raise ErrorContrato(f"el contrato no declara validation.{clave} (sin valores por defecto)")
    try:
        return Fraction(str(val[clave]))
    except (ValueError, ZeroDivisionError) as exc:
        raise ErrorContrato(f"validation.{clave}={val[clave]!r} no es un número") from exc


def _booleano(val: Mapping, clave: str, defecto: bool) -> bool:
    v = val.get(clave, defecto)
    if not isinstance(v, bool):
        raise ErrorContrato(f"validation.{clave}={v!r} debe ser booleano")
    return v


@dataclass(frozen=True)
class Reglas:
    k: int
    suelo_ratio: Fraction
    techo_ratio: Fraction
    tolerancia_ratio: Fraction
    provincia_unica: bool
    cuotas: tuple[tuple[str, int], ...]
    exentos_municipio: frozenset[str]
    exentas_particion: frozenset[str]
    disciplina_municipal: bool
    campo_r012: str  # "municipio" | "unidad_r012"
    max_mixtos: int
    nucleos_cerrados: bool
    contiguidad: bool
    criterio: Criterio = Criterio()

    @classmethod
    def desde_contrato(cls, cfg: Mapping[str, Any], criterio: Criterio | None = None) -> "Reglas":
        """Única puerta de entrada: una precedencia y una normalización; falla si falta una clave obligatoria."""
        criterio = criterio or Criterio()
        val = (cfg or {}).get("validation")
        if not isinstance(val, Mapping):
            raise ErrorContrato("el contrato no tiene bloque validation")
        if "expected_districts" not in val:
            raise ErrorContrato("el contrato no declara validation.expected_districts (K)")
        k = int(val["expected_districts"])
        if k < 1:
            raise ErrorContrato(f"K={k} no válido")
        suelo, techo, tol = (_ratio(val, c) for c in
                             ("population_floor_ratio", "population_cap_ratio", "target_tolerance_ratio"))
        if not (0 <= suelo <= 1 <= techo) or tol < 0:
            raise ErrorContrato(f"razones incoherentes: suelo={suelo}, techo={techo}, tolerancia={tol}")

        if "require_single_province_per_district" in val:
            provincia_unica = _booleano(val, "require_single_province_per_district", False)
        elif criterio.provincia_defecto == "obligatoria":
            raise ErrorContrato("el contrato no declara validation.require_single_province_per_district "
                                "(criterio provincia_defecto=obligatoria)")
        else:
            provincia_unica = criterio.provincia_defecto == "si"

        cuotas: dict[str, int] = {}
        for clave, n in (val.get("province_districts") or {}).items():
            c = norm_codigo(clave, 2)
            if c in cuotas:
                raise ErrorContrato(f"province_districts repite la provincia {c} tras normalizar")
            cuotas[c] = int(n)

        if criterio.max_mixtos == "fijo_1":
            max_mixtos = 1
        else:
            max_mixtos = int(val.get("max_mixed_districts_per_split_municipality", MAX_MIXTOS_POLITICA))
        if max_mixtos < 1:
            raise ErrorContrato(f"max_mixed_districts_per_split_municipality={max_mixtos} < 1")

        part = (cfg or {}).get("partitioning") or {}
        campo_r012 = ("unidad_r012" if bool(part.get("enabled"))
                      and str(part.get("strategy") or "") == "connected_internal_units" else "municipio")

        return cls(
            k=k, suelo_ratio=suelo, techo_ratio=techo, tolerancia_ratio=tol,
            provincia_unica=provincia_unica,
            cuotas=tuple(sorted(cuotas.items())),
            exentos_municipio=frozenset(norm_codigo(x, 5) for x in
                                        (val.get("population_floor_exempt_municipalities") or [])),
            exentas_particion=frozenset(norm_codigo(x, 2) for x in
                                        (val.get("population_floor_exempt_partitions") or [])),
            disciplina_municipal=_booleano(val, "require_municipality_discipline", False),
            campo_r012=campo_r012,
            max_mixtos=max_mixtos,
            nucleos_cerrados=_booleano(val, "preserve_closed_urban", True),
            contiguidad=_booleano(val, "require_graph_contiguity", True),
            criterio=criterio,
        )

    def limites(self, poblacion_total: int) -> tuple[Fraction, Fraction, Fraction, Fraction]:
        """(objetivo, suelo, techo, tolerancia absoluta), exactos."""
        objetivo = Fraction(poblacion_total, self.k)
        return objetivo, objetivo * self.suelo_ratio, objetivo * self.techo_ratio, objetivo * self.tolerancia_ratio

    def forma_canonica(self) -> dict:
        d = asdict(self)
        for c in ("suelo_ratio", "techo_ratio", "tolerancia_ratio"):
            d[c] = str(d[c])
        d["exentos_municipio"] = sorted(self.exentos_municipio)
        d["exentas_particion"] = sorted(self.exentas_particion)
        d["cuotas"] = [list(x) for x in self.cuotas]
        return d

    def huella(self) -> str:
        """sha256 de la forma canónica: batería y evidencias dicen con qué reglas se midió."""
        texto = json.dumps(self.forma_canonica(), sort_keys=True, ensure_ascii=False, separators=(",", ":"))
        return hashlib.sha256(texto.encode("utf-8")).hexdigest()

    def comprobar_datos(self, problema: Problema) -> None:
        """Falla si una regla activa necesita un campo que alguna unidad no trae (nunca se anula en silencio)."""
        faltan: dict[str, list[str]] = {}

        def exigir(campo: str):
            ids = [u.id for u in problema.unidades
                   if getattr(u, campo) is None and not (campo == "municipio" and u.desglose)]
            if ids:
                faltan[campo] = ids

        if self.provincia_unica:  # las cuotas solo se comprueban con provincia única (como VAL)
            exigir("provincia")
        if self.exentos_municipio:
            exigir("municipio")
        if self.exentas_particion:
            exigir("particion")
        if self.disciplina_municipal:
            exigir(self.campo_r012)
        if faltan:
            detalle = "; ".join(f"{c}: {len(ids)} unidades (p. ej. {ids[0]})" for c, ids in sorted(faltan.items()))
            raise ErrorDatos(f"faltan campos requeridos por las reglas activas: {detalle}")
