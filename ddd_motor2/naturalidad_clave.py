#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PROYECTO: Diputado de Distrito
COMPONENTE: motor 2 — funciones de calidad con naturalidad (A, B/C, D5, D8): una sola definición
VERSIÓN: 1.0.0
NOMBRE DE VERSIÓN: Naturalidad · clave compartida
FECHA: 2026-11-10
ESTADO: candidato (motor 2; producción no lo importa)
CAMBIOS: fichero nuevo (sale de naturalidad_competicion.Laboratorio 1.4.0 sin cambiar el orden).
MOTIVO: T-205: la competición del motor nuevo elige con D8 y debe usar la misma clave que el laboratorio de
  naturalidad (T-172/T-179): un mismo plan da la misma clave en los dos.
ANTERIOR: ninguna (fichero nuevo)
QUÉ HACE:
  clave(funcion, pob_obj, tol_ratio, huella, natural) — lexicográfica, menor es mejor; rel = |p − o| / o por distrito
  (o = objetivo de su circunscripción, o el único), fracciones exactas:
    A        (fuera de tolerancia, desvío máximo, error cuadrático medio, huella)
    B (= C)  (fuera, partidos judiciales + comarcas agrarias partidos, frontera cortada en km, desvío máximo, huella)
    D5, D8   (fuera, exceso del desvío máximo de los distritos dentro de tolerancia sobre el 5 % / 8 %, y la cola de B)
  El tope de D solo sirve para elegir: no es regla (suelo, techo, K y tolerancia no cambian).
  Natural: base común (laboratorio y generador «ponderado» de la competición) con población por unidad, objetivos,
  demarcaciones (partido judicial, comarca agraria, área de movilidad) y longitud de frontera por par de unidades;
  da desvios, clave, recargos del árbol ponderado y la validez según el núcleo.
Solo stdlib (el núcleo de reglas se importa del paquete).
"""
from __future__ import annotations

import statistics
from collections import defaultdict
from fractions import Fraction
from functools import lru_cache
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping

from .reglas import evaluar

TOPES = {"D5": 0.05, "D8": 0.08}
FUNCIONES_CLAVE = ("A", "B", "C", "D5", "D8")  # C elige con la clave de B (lo que cambia son sus cadenas)


def partidas(asig: Mapping[str, str], dems: Iterable[Mapping[str, str | None]]) -> int:
    """Demarcaciones (de cada tabla) repartidas en más de un distrito."""
    n = 0
    for dem in dems:
        ds: dict[str, set] = defaultdict(set)
        for u, d in asig.items():
            if dem.get(u) is not None:
                ds[dem[u]].add(d)
        n += sum(1 for v in ds.values() if len(v) > 1)
    return n


def corte_km(asig: Mapping[str, str], largo: Mapping[tuple[str, str], float]) -> float:
    """Frontera entre distritos distintos, en km con 3 decimales (suma en el orden de `largo`)."""
    return round(sum(w for (a, b), w in largo.items() if asig[a] != asig[b]) / 1000, 3)


def clave(funcion: str, pob_obj: Iterable[tuple[int, Fraction]], tol_ratio: Fraction, huella: str,
          natural: Callable[[], tuple[int, float]]) -> tuple:
    if funcion not in FUNCIONES_CLAVE:
        raise ValueError(f"función de calidad desconocida: {funcion}")
    rel = [abs(Fraction(p) - o) / o for p, o in pob_obj]
    fuera = sum(1 for x in rel if x > tol_ratio)
    dmax = max(rel)
    if funcion == "A":
        return (fuera, dmax, sum(x * x for x in rel) / len(rel), huella)
    cola = (*natural(), dmax, huella)
    if funcion in TOPES:
        dentro = [x for x in rel if x <= tol_ratio]
        return (fuera, max(0.0, (max(dentro) if dentro else 0) - TOPES[funcion]), *cola)
    return (fuera, *cola)


class Natural:
    """Atributos que pone quien la construye: pob_u, objetivo, tol, obj_circ ({circ: objetivo} o {}), circ_u,
    pj, ca, area ({unidad: id o None}), largo ({(a, b) ordenado: metros}, en orden), problema, reglas."""

    obj_circ: dict = {}
    circ_u: dict = {}

    def valido(self, asig: dict[str, str]) -> bool:
        return evaluar(self.problema, self.reglas, asig).valido

    def desvios(self, asig: dict[str, str]) -> dict[str, tuple[int, Fraction]]:
        """Por distrito: (población, objetivo de su circunscripción, o el único si no hay cuotas múltiples)."""
        pob: dict[str, int] = defaultdict(int)
        circ: dict[str, str] = {}
        for u, d in asig.items():
            pob[d] += self.pob_u[u]
            circ.setdefault(d, self.circ_u.get(u, ""))
        return {d: (p, self.obj_circ.get(circ[d], self.objetivo) if self.obj_circ else self.objetivo)
                for d, p in pob.items()}

    def natural(self, asig: dict[str, str]) -> tuple[int, float]:
        return partidas(asig, (self.pj, self.ca)), corte_km(asig, self.largo)

    def clave(self, asig: dict[str, str], funcion: str, huella: str = "") -> tuple:
        from .naturalidad_competicion import huella_plan  # noqa: PLC0415  (la del laboratorio, por defecto)
        return clave(funcion, self.desvios(asig).values(), self.tol / self.objetivo, huella or huella_plan(asig),
                     lambda: self.natural(asig))

    def recargos(self, rpj: float, rca: float, rmov: float, rlong: float) -> dict[tuple[str, str], float]:
        med = (statistics.median(self.largo.values()) if self.largo else 0) or 1.0  # grafo sin longitudes: 1
        out = {}
        for (a, b), w in self.largo.items():
            r = 0.0
            for dem, val in ((self.pj, rpj), (self.ca, rca), (self.area, rmov)):
                if dem[a] is None or dem[a] != dem[b]:
                    r += val
            r += rlong * (1 - min(1.0, w / med))
            out[(a, b)] = r
        for a, b in self.problema.puentes:
            out[(a, b)] = rpj + rca + rmov + rlong
        return out


@lru_cache(maxsize=1)
def _tablas() -> tuple[dict, dict]:
    from . import naturalidad_mapas as nm  # noqa: PLC0415  (solo csv)
    return nm.tablas_municipio(), nm.movilidad()[0]


def natural_desde_m06(problema, reglas, composicion: str | Path, grafo_m03: str | Path,
                      cfg: Mapping[str, Any]) -> Natural:
    """Natural sobre las unidades de una composición M06 (las del Problema del adaptador) y el grafo M03: frontera por
    par de unidades = suma de shared_border_m de sus aristas entre secciones (0 si el grafo no la trae), demarcaciones
    por el municipio de la unidad y área de movilidad por su primera sección."""
    import json  # noqa: PLC0415
    from .adaptadores import columnas_de_contrato, leer_composicion  # noqa: PLC0415
    from .naturalidad_mapas import grupo_area  # noqa: PLC0415
    tablas, indice = _tablas()
    col = columnas_de_contrato(cfg)
    sec_u: dict[str, str] = {}
    for f in leer_composicion(composicion, col):
        sec = str(f[col["seccion"]]).strip()
        sec_u[sec] = str(f.get(col["unidad"]) or sec).strip()
    n = Natural()
    n.problema, n.reglas = problema, reglas
    n.pob_u = {u.id: u.poblacion for u in problema.unidades}
    n.objetivo, _, _, n.tol = reglas.limites(problema.poblacion_total)
    n.circ_u = {u.id: u.provincia for u in problema.unidades}
    cuotas = dict(reglas.cuotas)
    n.obj_circ = {}
    if len(cuotas) > 1:
        pc: dict[str, int] = defaultdict(int)
        for u, c in n.circ_u.items():
            pc[c] += n.pob_u[u]
        n.obj_circ = {c: Fraction(pc[c], k) for c, k in sorted(cuotas.items()) if k > 0}
    mun = {u.id: (u.municipio or "")[:5] or None for u in problema.unidades}
    n.pj = {u: tablas["pj"].get(m) if m else None for u, m in mun.items()}
    n.ca = {u: tablas["ca"].get(m) if m else None for u, m in mun.items()}
    primera: dict[str, str] = {}
    for sec in sorted(sec_u):
        primera.setdefault(sec_u[sec], sec)
    n.area = {u: grupo_area(primera[u], indice) if u in primera else None for u in n.pob_u}
    largo: dict[tuple[str, str], float] = defaultdict(float)
    g = json.loads(Path(grafo_m03).read_text(encoding="utf-8"))
    for e in g.get("edges", []):
        a, b = sec_u.get(str(e.get("u"))), sec_u.get(str(e.get("v")))
        if a and b and a != b and a in n.pob_u and b in n.pob_u:
            largo[tuple(sorted((a, b)))] += float(e.get("shared_border_m") or 0)
    for a, b in problema.aristas:  # toda arista del núcleo está en el grafo de la cadena, aunque mida 0
        largo.setdefault(tuple(sorted((a, b))), 0.0)
    n.largo = dict(sorted(largo.items()))
    return n
