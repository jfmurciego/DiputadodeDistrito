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
"""
from __future__ import annotations

import math
from collections import defaultdict, deque
from dataclasses import dataclass, field
from fractions import Fraction
from typing import Mapping

from .modelo import Problema, Reglas


@dataclass(frozen=True, order=True)
class Violacion:
    regla: str
    ambito: str  # distrito, municipio, provincia, núcleo o unidad afectada
    detalle: str = ""


@dataclass(frozen=True)
class Informe:
    valido: bool
    violaciones: tuple[Violacion, ...]
    metricas: dict = field(compare=False)
    huella_reglas: str = ""

    def codigos(self) -> set[str]:
        return {v.regla for v in self.violaciones}


def _ceil(x: Fraction) -> int:
    return math.ceil(x)


def _conexo(miembros: set[str], adj: Mapping[str, set[str]]) -> bool:
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


def exento_de_suelo(reglas: Reglas, unidades) -> bool:
    """Exención por municipio (cualquiera exento) o por partición según Criterio.exencion_particion."""
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


def evaluar(problema: Problema, reglas: Reglas, asignacion: Mapping[str, object]) -> Informe:
    """Veredicto completo de un plan (unidad -> distrito). Lanza ErrorDatos si faltan campos que una regla exige."""
    reglas.comprobar_datos(problema)
    viol: list = []
    asig = {str(u): str(d) for u, d in asignacion.items()}

    faltan = [u.id for u in problema.unidades if u.id not in asig]
    ajenas = sorted(set(asig) - set(problema.por_id))
    if faltan:
        viol.append(Violacion("R-ATOM", "plan", f"unidades sin asignar={len(faltan)} (p. ej. {faltan[0]})"))
    if ajenas:
        viol.append(Violacion("R-ATOM", "plan", f"unidades desconocidas={len(ajenas)} (p. ej. {ajenas[0]})"))

    distritos: dict[str, list] = defaultdict(list)
    for uid, d in asig.items():
        if uid in problema.por_id:
            distritos[d].append(problema.por_id[uid])
    if len(distritos) != reglas.k:
        viol.append(Violacion("R-K", "plan", f"distritos={len(distritos)}, esperados={reglas.k}"))

    objetivo, suelo, techo, tol = reglas.limites(problema.poblacion_total)
    adj = problema.adyacencia(reglas.criterio.contiguidad_con_puentes)
    pob: dict[str, int] = {}
    fuera_tol: list[str] = []
    cuenta_prov: dict[str, int] = defaultdict(int)
    for d, us in sorted(distritos.items()):
        p = sum(u.poblacion for u in us)
        pob[d] = p
        exento = exento_de_suelo(reglas, us)
        if not exento and p < suelo:
            viol.append(Violacion("R-POB-SUELO", d, f"{p} < {float(suelo):.1f}"))
        if p > techo:
            viol.append(Violacion("R-POB-TECHO", d, f"{p} > {float(techo):.1f}"))
        if abs(p - objetivo) > tol:
            fuera_tol.append(d)
            if reglas.criterio.tolerancia == "dura" and not (exento and p < objetivo):
                viol.append(Violacion("R-TOL", d, f"|{p} - {float(objetivo):.1f}| > {float(tol):.1f}"))
        if reglas.contiguidad and not _conexo({u.id for u in us}, adj):
            viol.append(Violacion("R-CONTIG", d))
        if reglas.provincia_unica:
            provs = sorted({u.provincia for u in us})
            if len(provs) != 1:
                viol.append(Violacion("R-PROV", d, ",".join(provs)))
            else:
                cuenta_prov[provs[0]] += 1
    if reglas.provincia_unica:
        for prov, esperados in reglas.cuotas:
            if cuenta_prov.get(prov, 0) != esperados:
                viol.append(Violacion("R-CUOTA", prov, f"distritos={cuenta_prov.get(prov, 0)}, esperados={esperados}"))

    if reglas.disciplina_municipal:
        campo = reglas.campo_r012
        claves_d = {d: {getattr(u, campo) for u in us} for d, us in distritos.items()}
        m_pob: dict[str, int] = defaultdict(int)
        m_d: dict[str, set[str]] = defaultdict(set)
        for d, us in distritos.items():
            for u in us:
                m = getattr(u, campo)
                m_pob[m] += u.poblacion
                m_d[m].add(d)
        for m in sorted(m_d):
            p, ds = m_pob[m], m_d[m]
            minimo = max(1, _ceil(p / techo)) if p > 0 else 1
            maximo = max(1, _ceil(p / objetivo)) if p > 0 else 1
            if len(ds) < minimo:
                viol.append(Violacion("R-MUN-MIN", m, f"distritos={len(ds)} < {minimo}"))
            if len(ds) > maximo:
                viol.append(Violacion("R-MUN-MAX", m, f"distritos={len(ds)} > {maximo}"))
            mixtos = sum(1 for d in ds if len(claves_d[d]) > 1)
            if len(ds) > 1 and mixtos > reglas.max_mixtos:
                viol.append(Violacion("R-MUN-MIXTOS", m, f"mixtos={mixtos} > {reglas.max_mixtos}"))

    if reglas.nucleos_cerrados:
        grupos: dict[str, set[str]] = defaultdict(set)
        for u in problema.unidades:
            if u.nucleo_cerrado is not None:
                grupos[u.nucleo_cerrado].add(u.id)
        for n, miembros in sorted(grupos.items()):
            ds = {asig.get(uid) for uid in miembros}
            if len(ds) != 1 or None in ds or {u.id for u in distritos[next(iter(ds))]} != miembros:
                viol.append(Violacion("R-NUCLEO", n, "el núcleo cerrado no forma exactamente un distrito"))

    dev = max((abs(p - objetivo) for p in pob.values()), default=Fraction(0))
    metricas = {
        "objetivo": float(objetivo), "suelo": float(suelo), "techo": float(techo), "tolerancia": float(tol),
        "max_desviacion_ratio": float(dev / objetivo) if objetivo else 0.0,
        "min_pob": min(pob.values(), default=0), "max_pob": max(pob.values(), default=0),
        "fuera_tolerancia": fuera_tol,
    }
    viol = tuple(sorted(set(viol)))
    return Informe(valido=not viol, violaciones=viol, metricas=metricas, huella_reglas=reglas.huella())
