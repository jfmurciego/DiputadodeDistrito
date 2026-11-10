#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PROYECTO: Diputado de Distrito
COMPONENTE: motor 2 — orquestador de la competición «canónico + GerryChain»
VERSIÓN: 1.1.0
NOMBRE DE VERSIÓN: Competición · semilla pública y revisión
FECHA: 2026-11-10
ESTADO: candidato (motor 2; producción no lo importa)
CAMBIOS: 1.1.0 — competir_publico (semillas públicas de semilla.py); Resultado.valido y Resultado.huella()
  (reproducibilidad bit a bit); sin referencia de núcleos y con unidades cerradas, ERROR_DATOS (indicador explícito:
  unidades con nucleo_cerrado, no el texto del aviso); pruebas de desempate por huella y de canónico fallido.
MOTIVO: T-163 / D-48: la primera versión del motor nuevo es una competición entre el canónico y N cadenas de
  GerryChain bajo el núcleo único de reglas; gana el mejor plan válido, así que nunca es peor que el canónico.
ANTERIOR: legacy/ddd_motor2/competicion_v1.0.0_20261110.py
QUÉ HACE: competir(entrada, canonico, cadena, semillas) ejecuta el generador canónico (una vez) y la cadena con cada
  semilla, a través de adaptadores (protocolo Generador: devuelven una composición M06). Cada candidato se juzga con el
  núcleo (adaptadores.problema_y_plan + reglas.evaluar, Criterio D-44 por defecto) y se ordena con la función de
  calidad vigente, lexicográfica:
    1. evaluable (fallo del generador o ErrorDatos/ErrorContrato van detrás de todo);
    2. número de violaciones duras;  3. distritos fuera de tolerancia;  4. desvío máximo |p − obj| / obj;
    5. error cuadrático medio de (p − obj) / obj;  6. huella del plan (independiente de las etiquetas de distrito);
    7. orden de los candidatos (el canónico primero).
  Las métricas 4 y 5 son fracciones exactas: el orden no depende del redondeo.
  Núcleos cerrados: la referencia es entrada.referencia_nucleos o, si falta, la composición del canónico, la misma
  para todos los candidatos (con su propia composición R-NUCLEO sería trivial). Si no hay referencia (el canónico
  falló) y el territorio tiene unidades cerradas, los candidatos quedan ERROR_DATOS: un plan con núcleos rotos no gana.
  El ganador es siempre el primero por calidad aunque nadie sea válido: Resultado.valido lo dice.
  competir_publico deriva antes las semillas públicas: si el contrato no trae el ancla, ErrorContrato y no se ejecuta
  nada (el territorio sale como ERROR explícito; nunca con semillas fijas).
Solo stdlib; los generadores reales están en ddd_motor2/generadores.py.
"""
from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass, field
from fractions import Fraction
from pathlib import Path
from typing import Any, Iterable, Mapping, Protocol

from .adaptadores import problema_y_plan
from .reglas import Criterio, ErrorContrato, ErrorDatos, Reglas, evaluar

VERSION = "1.1.0"


@dataclass(frozen=True)
class EntradaTerritorio:
    """Entradas ARC-E de un territorio para la competición (lo que no depende del generador)."""

    territorio: str
    cfg: Mapping[str, Any]
    grafo_m03: Path
    atributos_secciones: Path | None = None
    referencia_nucleos: Path | None = None
    contexto: Mapping[str, Any] = field(default_factory=dict)  # lo que el adaptador del generador necesite


@dataclass
class Salida:
    """Lo que devuelve un generador: su composición M06 (o None si falló)."""

    composicion: Path | None
    estado: str = "OK"
    detalle: str = ""
    atributos_secciones: Path | None = None  # sustituye a los de la entrada (p. ej. el GeoJSON M06 de este plan)
    extra: dict = field(default_factory=dict)


class Generador(Protocol):
    nombre: str

    def generar(self, entrada: EntradaTerritorio, semilla: int | None, destino: Path) -> Salida: ...


@dataclass
class Candidato:
    id: str
    generador: str
    semilla: int | None
    orden: int
    estado: str = "PENDIENTE"  # VALIDO | INVALIDO | FALLO_GENERADOR | ERROR_DATOS | ERROR_CONTRATO
    detalle: str = ""
    violaciones: list[dict] = field(default_factory=list)
    duras: int | None = None
    fuera_tolerancia: int | None = None
    desvio_max: Fraction | None = None
    ecm: Fraction | None = None
    huella_plan: str = ""
    composicion: str = ""
    composicion_sha256: str = ""
    tiempos: dict = field(default_factory=dict)
    avisos: list[str] = field(default_factory=list)
    extra: dict = field(default_factory=dict)

    @property
    def evaluable(self) -> bool:
        return self.estado in ("VALIDO", "INVALIDO")

    def clave(self) -> tuple:
        if not self.evaluable:
            return (1, 0, 0, Fraction(0), Fraction(0), "", self.orden)
        return (0, self.duras, self.fuera_tolerancia, self.desvio_max, self.ecm, self.huella_plan, self.orden)

    def a_dict(self) -> dict:
        return {
            "id": self.id, "generador": self.generador, "semilla": self.semilla, "estado": self.estado,
            "detalle": self.detalle, "violaciones_duras": self.duras, "fuera_tolerancia": self.fuera_tolerancia,
            "desvio_max": None if self.desvio_max is None else float(self.desvio_max),
            "ecm": None if self.ecm is None else float(self.ecm),
            "huella_plan": self.huella_plan, "composicion": self.composicion,
            "composicion_sha256": self.composicion_sha256, "violaciones": self.violaciones,
            "tiempos": self.tiempos, "avisos": self.avisos, "extra": self.extra,
        }


@dataclass
class Resultado:
    territorio: str
    candidatos: list[Candidato]
    ganador: Candidato
    canonico: Candidato
    huella_reglas: str
    criterio: dict
    tiempo_total_s: float
    semilla_publica: dict = field(default_factory=dict)

    @property
    def valido(self) -> bool:
        return self.ganador.estado == "VALIDO"

    def huella(self) -> str:
        """sha256 de lo que debe repetirse bit a bit con la misma entrada: reglas, semillas, plan y composición de
        cada candidato y ganador (sin tiempos ni rutas)."""
        forma = {"reglas": self.huella_reglas, "ganador": self.ganador.id,
                 "candidatos": [[c.id, c.semilla, c.estado, c.huella_plan, c.composicion_sha256]
                                for c in sorted(self.candidatos, key=lambda c: c.orden)]}
        return hashlib.sha256(json.dumps(forma, separators=(",", ":")).encode("utf-8")).hexdigest()

    def a_dict(self) -> dict:
        return {
            "version_orquestador": VERSION, "territorio": self.territorio, "ganador": self.ganador.id,
            "valido": self.valido, "huella_resultado": self.huella(), "semilla_publica": self.semilla_publica,
            "canonico": self.canonico.id, "huella_reglas": self.huella_reglas, "criterio": self.criterio,
            "orden_calidad": ["evaluable", "violaciones_duras", "fuera_tolerancia", "desvio_max", "ecm",
                              "huella_plan", "orden"],
            "tiempo_total_s": round(self.tiempo_total_s, 3),
            "candidatos": [c.a_dict() for c in sorted(self.candidatos, key=Candidato.clave)],
        }


def sha256_fichero(ruta: Path) -> str:
    h = hashlib.sha256()
    with open(ruta, "rb") as fh:
        for bloque in iter(lambda: fh.read(1 << 20), b""):
            h.update(bloque)
    return h.hexdigest()


def huella_plan(plan: Mapping[str, str]) -> str:
    """sha256 del plan como partición (conjuntos de unidades), sin depender de las etiquetas de distrito."""
    grupos: dict[str, list[str]] = {}
    for u, d in plan.items():
        grupos.setdefault(str(d), []).append(str(u))
    forma = sorted(sorted(us) for us in grupos.values())
    return hashlib.sha256(json.dumps(forma, separators=(",", ":"), ensure_ascii=False).encode("utf-8")).hexdigest()


def juzgar(cand: Candidato, salida: Salida, entrada: EntradaTerritorio, criterio: Criterio,
           referencia: Path | None) -> None:
    """Rellena el veredicto y las métricas de calidad del candidato con el núcleo de reglas."""
    if salida.composicion is None or not Path(salida.composicion).is_file():
        cand.estado = "FALLO_GENERADOR"
        cand.detalle = salida.detalle or f"sin composición ({salida.estado})"
        return
    cand.composicion = str(salida.composicion)
    cand.composicion_sha256 = sha256_fichero(Path(salida.composicion))
    try:
        reglas = Reglas.desde_contrato(entrada.cfg, criterio)
        problema, plan, avisos = problema_y_plan(
            salida.composicion, entrada.grafo_m03, entrada.cfg, referencia_nucleos=referencia,
            atributos_secciones=salida.atributos_secciones or entrada.atributos_secciones,
            respaldo_municipio_cusec=criterio.respaldo_municipio_cusec)
        inf = evaluar(problema, reglas, plan)
    except ErrorContrato as exc:
        cand.estado, cand.detalle = "ERROR_CONTRATO", str(exc)
        return
    except ErrorDatos as exc:
        cand.estado, cand.detalle = "ERROR_DATOS", str(exc)
        return
    cand.avisos = list(avisos)
    if referencia is None and any(u.nucleo_cerrado is not None for u in problema.unidades):
        cand.estado = "ERROR_DATOS"
        cand.detalle = "sin referencia de núcleos cerrados (el canónico no dio composición): R-NUCLEO no juzgable"
        return
    cand.violaciones = [{"regla": v.regla, "ambito": v.ambito, "detalle": v.detalle} for v in inf.violaciones]
    cand.duras = len(inf.violaciones)
    cand.fuera_tolerancia = len(inf.metricas["fuera_tolerancia"])
    objetivo = reglas.limites(problema.poblacion_total)[0]
    pob: dict[str, int] = {}
    for u, d in plan.items():
        pob[d] = pob.get(d, 0) + problema.por_id[u].poblacion
    desv = [Fraction(p) / objetivo - 1 for p in pob.values()] if objetivo else [Fraction(0)]
    cand.desvio_max = max(abs(x) for x in desv)
    cand.ecm = sum((x * x for x in desv), Fraction(0)) / len(desv)
    cand.huella_plan = huella_plan(plan)
    cand.estado = "VALIDO" if inf.valido else "INVALIDO"


def _ejecutar(gen: Generador, entrada: EntradaTerritorio, semilla: int | None, destino: Path,
              cand: Candidato) -> Salida:
    t0 = time.monotonic()
    try:
        salida = gen.generar(entrada, semilla, destino)
    except Exception as exc:  # un generador roto no tumba la competición: el candidato queda fuera
        salida = Salida(None, "EXCEPCION", f"{type(exc).__name__}: {exc}")
    cand.tiempos["generar_s"] = round(time.monotonic() - t0, 3)
    cand.extra = dict(salida.extra)
    return salida


def competir(entrada: EntradaTerritorio, canonico: Generador, cadena: Generador, semillas: Iterable[int],
             destino: Path, *, criterio: Criterio | None = None, semilla_canonica: int | None = None) -> Resultado:
    """Canónico + una cadena por semilla; devuelve todos los candidatos juzgados y el ganador."""
    t_ini = time.monotonic()
    criterio = criterio or Criterio()
    destino = Path(destino)
    destino.mkdir(parents=True, exist_ok=True)
    semillas = list(semillas)
    if len(set(semillas)) != len(semillas):
        raise ValueError(f"semillas repetidas: {semillas}")

    can = Candidato("canonico", canonico.nombre, semilla_canonica, 0)
    sal_can = _ejecutar(canonico, entrada, semilla_canonica, destino / can.id, can)
    referencia = entrada.referencia_nucleos
    if referencia is None and sal_can.composicion is not None and Path(sal_can.composicion).is_file():
        referencia = Path(sal_can.composicion)
    pendientes = [(can, sal_can)]
    for i, s in enumerate(semillas, start=1):
        c = Candidato(f"{cadena.nombre}-s{s}", cadena.nombre, s, i)
        pendientes.append((c, _ejecutar(cadena, entrada, s, destino / c.id, c)))
    for c, sal in pendientes:
        t0 = time.monotonic()
        juzgar(c, sal, entrada, criterio, referencia)
        c.tiempos["juzgar_s"] = round(time.monotonic() - t0, 3)

    candidatos = [c for c, _ in pendientes]
    ganador = min(candidatos, key=Candidato.clave)
    assert ganador.clave() <= can.clave()  # por construcción: el canónico compite
    try:
        huella = Reglas.desde_contrato(entrada.cfg, criterio).huella()
    except ErrorContrato:
        huella = ""
    return Resultado(entrada.territorio, candidatos, ganador, can, huella,
                     {k: getattr(criterio, k) for k in criterio.__dataclass_fields__},
                     time.monotonic() - t_ini)


def competir_publico(entrada: EntradaTerritorio, canonico: Generador, cadena: Generador, destino: Path, *,
                     n_cadenas: int = 5, criterio: Criterio | None = None) -> Resultado:
    """La competición con las N semillas públicas del territorio (semilla.py): misma entrada ⇒ mismo resultado."""
    from .semilla import descripcion
    desc = descripcion(entrada.cfg, entrada.territorio, n_cadenas)
    r = competir(entrada, canonico, cadena, desc["semillas"], destino, criterio=criterio)
    r.semilla_publica = desc
    return r
