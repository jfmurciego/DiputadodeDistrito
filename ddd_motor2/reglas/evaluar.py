#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PROYECTO: Diputado de Distrito
COMPONENTE: núcleo de reglas del motor 2 — evaluador completo de un plan
VERSIÓN: 1.0.0
NOMBRE DE VERSIÓN: Núcleo único de reglas · F1
FECHA: 2026-11-10
ESTADO: candidato (motor 2; producción no lo importa)
CAMBIOS: fichero nuevo.
MOTIVO: T-160: una sola definición ejecutable de «plan válido» para batería (T-132), certificador (T-136) y motor 2.
ANTERIOR: ninguna (fichero nuevo)
QUÉ HACE: evaluar(problema, reglas, asignacion) -> Informe con violaciones de códigos estables (modelo.CODIGOS) y
  métricas no duras (desviación, distritos fuera de tolerancia). Comparaciones exactas (enteros contra fracciones).
  Las reglas se calculan por ÁMBITO (distrito, municipio, cuotas, núcleo, plan) con las mismas funciones que usa el
  Estado incremental (estado.py), de modo que ambos no pueden divergir.
"""
from __future__ import annotations

import math
from collections import defaultdict, deque
from dataclasses import dataclass, field
from fractions import Fraction
from typing import Iterable, Mapping

from .modelo import Problema, Reglas, Unidad


@dataclass(frozen=True, order=True)
class Violacion:
    regla: str
    ambito: str  # distrito, municipio, provincia, núcleo o «plan»
    detalle: str = ""


@dataclass(frozen=True)
class Informe:
    valido: bool
    violaciones: tuple[Violacion, ...]
    metricas: dict = field(compare=False)
    huella_reglas: str = ""

    def codigos(self) -> set[str]:
        return {v.regla for v in self.violaciones}


def conexo(miembros: set[str], adj: Mapping[str, set[str]]) -> bool:
    if not miembros:
        return True
    inicio = next(iter(miembros))
    vistos = {inicio}
    cola = deque([inicio])
    while cola:
        u = cola.popleft()
        for v in adj.get(u, ()):
            if v in miembros and v not in vistos:
                vistos.add(v)
                cola.append(v)
    return len(vistos) == len(miembros)


def exento_de_suelo(reglas: Reglas, unidades: Iterable[Unidad]) -> bool:
    """Exención por municipio (cualquiera exento) o por partición según Criterio.exencion_particion."""
    unidades = list(unidades)
    if reglas.exentos_municipio and any(u.municipio in reglas.exentos_municipio for u in unidades):
        return True
    if not reglas.exentas_particion:
        return False
    partes = sorted({u.particion for u in unidades})
    if not partes:
        return False
    modo = reglas.criterio.exencion_particion
    if modo == "todas":
        return all(p in reglas.exentas_particion for p in partes)
    if modo == "alguna":
        return any(p in reglas.exentas_particion for p in partes)
    return partes[0] in reglas.exentas_particion  # "primera", como VAL 1.3.5


@dataclass(frozen=True)
class Contexto:
    """Lo que no depende del plan: límites exactos y adyacencia."""

    reglas: Reglas
    objetivo: Fraction
    suelo: Fraction
    techo: Fraction
    tol: Fraction
    adj: Mapping[str, set[str]]

    @classmethod
    def de(cls, problema: Problema, reglas: Reglas) -> "Contexto":
        reglas.comprobar_datos(problema)
        objetivo, suelo, techo, tol = reglas.limites(problema.poblacion_total)
        return cls(reglas, objetivo, suelo, techo, tol, problema.adyacencia(reglas.criterio.contiguidad_con_puentes))

    def rango_municipal(self, p: int) -> tuple[int, int]:
        if p <= 0:
            return 1, 1
        return max(1, math.ceil(p / self.techo)), max(1, math.ceil(p / self.objetivo))


def violaciones_distrito(ctx: Contexto, d: str, us: list[Unidad]) -> list[Violacion]:
    r, out = ctx.reglas, []
    if not us:
        return out
    p = sum(u.poblacion for u in us)
    exento = exento_de_suelo(r, us)
    if not exento and p < ctx.suelo:
        out.append(Violacion("R-POB-SUELO", d, f"{p} < {float(ctx.suelo):.1f}"))
    if p > ctx.techo:
        out.append(Violacion("R-POB-TECHO", d, f"{p} > {float(ctx.techo):.1f}"))
    if (r.criterio.tolerancia == "dura" and abs(p - ctx.objetivo) > ctx.tol
            and not (exento and p < ctx.objetivo)):
        out.append(Violacion("R-TOL", d, f"|{p} - {float(ctx.objetivo):.1f}| > {float(ctx.tol):.1f}"))
    if r.contiguidad and not conexo({u.id for u in us}, ctx.adj):
        out.append(Violacion("R-CONTIG", d))
    if r.provincia_unica:
        provs = sorted({u.provincia for u in us})
        if len(provs) != 1:
            out.append(Violacion("R-PROV", d, ",".join(provs)))
    return out


def violaciones_municipio(ctx: Contexto, m: str, pob: int, distritos: set[str], mixtos: int) -> list[Violacion]:
    out = []
    minimo, maximo = ctx.rango_municipal(pob)
    if len(distritos) < minimo:
        out.append(Violacion("R-MUN-MIN", m, f"distritos={len(distritos)} < {minimo}"))
    if len(distritos) > maximo:
        out.append(Violacion("R-MUN-MAX", m, f"distritos={len(distritos)} > {maximo}"))
    if len(distritos) > 1 and mixtos > ctx.reglas.max_mixtos:
        out.append(Violacion("R-MUN-MIXTOS", m, f"mixtos={mixtos} > {ctx.reglas.max_mixtos}"))
    return out


def violaciones_cuotas(ctx: Contexto, cuenta_prov: Mapping[str, int]) -> list[Violacion]:
    if not ctx.reglas.provincia_unica:
        return []
    return [Violacion("R-CUOTA", prov, f"distritos={cuenta_prov.get(prov, 0)}, esperados={n}")
            for prov, n in ctx.reglas.cuotas if cuenta_prov.get(prov, 0) != n]


def violaciones_nucleo(n: str, miembros: set[str], asig: Mapping[str, str],
                       miembros_de: Mapping[str, set[str]]) -> list[Violacion]:
    ds = {asig.get(uid) for uid in miembros}
    if len(ds) != 1 or None in ds or miembros_de.get(next(iter(ds)), set()) != miembros:
        return [Violacion("R-NUCLEO", n, "el núcleo cerrado no forma exactamente un distrito")]
    return []


def violaciones_plan(problema: Problema, reglas: Reglas, asig: Mapping[str, str], n_distritos: int) -> list[Violacion]:
    out = []
    faltan = [u.id for u in problema.unidades if u.id not in asig]
    ajenas = sorted(set(asig) - set(problema.por_id))
    if faltan:
        out.append(Violacion("R-ATOM", "plan", f"unidades sin asignar={len(faltan)} (p. ej. {faltan[0]})"))
    if ajenas:
        out.append(Violacion("R-ATOM", "plan", f"unidades desconocidas={len(ajenas)} (p. ej. {ajenas[0]})"))
    if n_distritos != reglas.k:
        out.append(Violacion("R-K", "plan", f"distritos={n_distritos}, esperados={reglas.k}"))
    return out


def grupos_nucleo(problema: Problema) -> dict[str, set[str]]:
    grupos: dict[str, set[str]] = defaultdict(set)
    for u in problema.unidades:
        if u.nucleo_cerrado is not None:
            grupos[u.nucleo_cerrado].add(u.id)
    return dict(grupos)


def provincia_de(reglas: Reglas, us: list[Unidad]) -> str | None:
    """Provincia del distrito para las cuotas (solo si es única)."""
    provs = {u.provincia for u in us}
    return next(iter(provs)) if reglas.provincia_unica and len(provs) == 1 else None


def evaluar(problema: Problema, reglas: Reglas, asignacion: Mapping[str, object]) -> Informe:
    """Veredicto completo de un plan (unidad -> distrito). Lanza ErrorDatos si faltan campos que una regla exige."""
    ctx = Contexto.de(problema, reglas)
    asig = {str(u): str(d) for u, d in asignacion.items()}
    distritos: dict[str, list[Unidad]] = defaultdict(list)
    for uid, d in asig.items():
        if uid in problema.por_id:
            distritos[d].append(problema.por_id[uid])

    viol = violaciones_plan(problema, reglas, asig, len(distritos))
    cuenta_prov: dict[str, int] = defaultdict(int)
    for d, us in distritos.items():
        viol += violaciones_distrito(ctx, d, us)
        prov = provincia_de(reglas, us)
        if prov is not None:
            cuenta_prov[prov] += 1
    viol += violaciones_cuotas(ctx, cuenta_prov)

    if reglas.disciplina_municipal:
        campo = reglas.campo_r012
        claves_d = {d: {getattr(u, campo) for u in us} for d, us in distritos.items()}
        m_pob: dict[str, int] = defaultdict(int)
        m_d: dict[str, set[str]] = defaultdict(set)
        for d, us in distritos.items():
            for u in us:
                m_pob[getattr(u, campo)] += u.poblacion
                m_d[getattr(u, campo)].add(d)
        for m, ds in m_d.items():
            viol += violaciones_municipio(ctx, m, m_pob[m], ds, sum(1 for d in ds if len(claves_d[d]) > 1))

    if reglas.nucleos_cerrados:
        miembros_de = {d: {u.id for u in us} for d, us in distritos.items()}
        for n, miembros in grupos_nucleo(problema).items():
            viol += violaciones_nucleo(n, miembros, asig, miembros_de)

    pob = {d: sum(u.poblacion for u in us) for d, us in distritos.items()}
    dev = max((abs(p - ctx.objetivo) for p in pob.values()), default=Fraction(0))
    metricas = {
        "objetivo": float(ctx.objetivo), "suelo": float(ctx.suelo), "techo": float(ctx.techo),
        "tolerancia": float(ctx.tol),
        "max_desviacion_ratio": float(dev / ctx.objetivo) if ctx.objetivo else 0.0,
        "min_pob": min(pob.values(), default=0), "max_pob": max(pob.values(), default=0),
        "fuera_tolerancia": sorted(d for d, p in pob.items() if abs(p - ctx.objetivo) > ctx.tol),
    }
    viol = tuple(sorted(set(viol)))
    return Informe(valido=not viol, violaciones=viol, metricas=metricas, huella_reglas=reglas.huella())
