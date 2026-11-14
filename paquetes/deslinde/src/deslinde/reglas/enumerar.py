#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PROYECTO: Diputado de Distrito
COMPONENTE: núcleo de reglas del motor 2 — poda monótona y enumeración exacta con presupuesto de nodos
VERSIÓN: 1.3.0
NOMBRE DE VERSIÓN: Poda con constantes precalculadas
FECHA: 2026-11-12
ESTADO: candidato (motor 2; producción no lo importa)
CAMBIOS: 1.3.0 (T-235, D-83) — la poda no corta por techo ni por tolerancia un distrito de una partición exenta
  (evaluar.exento_de_techo, la misma regla que el evaluador). Sin exención, nada cambia.
  1.2.0 — podar(..., pre=None): las constantes del problema (ids, piezas por unidad, población y nº de unidades
  por municipio, rango_municipal de cada municipio, núcleos cerrados) se calculan una vez por enumeración
  (_Constantes) en vez de en cada nodo. Mismas violaciones, en el mismo orden (test de equivalencia con la 1.1.0).
  1.1.0 — enumerar(..., clave=f): guarda el plan válido de menor f(plan) («mejor», «mejor_clave»), recorriendo
  TODOS los válidos (no solo los max_planes guardados); «segundo_clave» y «empatados» (planes con la mejor clave).
  1.0.0 — fichero nuevo.
MOTIVO: T-160: donde el espacio de planes cabe, enumerar todos en vez de muestrear (criterio del propietario: cadena
  solo donde el espacio es grande). El veredicto de cada plan enumerado es evaluar() del núcleo.
MOTIVO 1.1.0: T-175: enumeración exacta integrada en el competidor y el certificador.
MOTIVO 1.2.0: T-256 (D-89): T-254 midió que podar es casi todo el exhaustivo (recalcula constantes y llama 8,7 M veces
  a rango_municipal con divisiones de Fraction). Optimización bit a bit: mismos nodos, podas y planes.
ANTERIOR: legacy/ddd_motor2/reglas/enumerar_v1.2.0_20261112.py
QUÉ HACE:
  podar(problema, reglas, parcial) -> violaciones SEGURAS de un plan parcial: monótonas, es decir, toda extensión del
    parcial a un plan completo las tiene también (test por fuerza bruta). Techo, provincia única, K, R012 máx y
    mixtos, núcleos cerrados, tolerancia dura por arriba; con contigüidad, además, distritos o componentes cerrados
    (sin unidad libre vecina): un distrito cerrado ya no puede crecer sin quedar desconexo, así que se juzga entero.
  enumerar(problema, reglas, presupuesto=None) -> {"completo", "nodos", "validos", "huella", "planes"}: recorre las
    particiones en etiquetas canónicas (cada partición una sola vez); si agota el presupuesto (Criterio.presupuesto_nodos
    por defecto), completo=False y el recuento es solo una cota inferior.
"""
from __future__ import annotations

import hashlib
from collections import defaultdict, deque
from typing import Mapping

from .evaluar import Contexto, Violacion, evaluar, exento_de_techo, violaciones_distrito
from .modelo import Problema, Reglas


def _componentes(miembros: set[str], adj) -> list[set[str]]:
    resto, out = set(miembros), []
    while resto:
        s = resto.pop()
        comp, cola = {s}, deque([s])
        while cola:
            x = cola.popleft()
            for y in adj.get(x, ()):
                if y in resto:
                    resto.discard(y)
                    comp.add(y)
                    cola.append(y)
        out.append(comp)
    return out


class _Constantes:
    """Lo que podar() necesita del problema y no depende del plan parcial."""

    def __init__(self, problema: Problema, reglas: Reglas, ctx: Contexto):
        self.ids = frozenset(u.id for u in problema.unidades)
        self.claves: dict[str, tuple] = {}
        m_tot: dict[str, int] = defaultdict(int)
        self.m_n: dict[str, int] = defaultdict(int)
        if reglas.disciplina_municipal:
            campo = reglas.campo_r012
            self.claves = {u.id: tuple(m for m, _ in u.piezas(campo)) for u in problema.unidades}
            for u in problema.unidades:
                for m, pm in u.piezas(campo):
                    m_tot[m] += pm
                    self.m_n[m] += 1
        self.rango = {m: ctx.rango_municipal(p) for m, p in m_tot.items()}
        self.nucleo = {u.id: u.nucleo_cerrado for u in problema.unidades if u.nucleo_cerrado is not None}


def podar(problema: Problema, reglas: Reglas, parcial: Mapping[str, object],
          ctx: Contexto | None = None, pre: _Constantes | None = None) -> list[Violacion]:
    ctx = ctx or Contexto.de(problema, reglas)
    pre = pre or _Constantes(problema, reglas, ctx)
    asig = {str(u): str(d) for u, d in parcial.items()}
    libres = pre.ids - set(asig)
    miembros: dict[str, set[str]] = defaultdict(set)
    for uid, d in asig.items():
        miembros[d].add(uid)
    out: list[Violacion] = []
    if len(miembros) > reglas.k:
        out.append(Violacion("R-K", "plan", f"distritos>{reglas.k}"))
    if len(miembros) + len(libres) < reglas.k:
        out.append(Violacion("R-K", "plan", f"distritos<{reglas.k}"))
    por = problema.por_id
    for d, ms in miembros.items():
        us = [por[x] for x in ms]
        p = sum(u.poblacion for u in us)
        sin_techo = exento_de_techo(reglas, us)
        if p > ctx.techo and not sin_techo:
            out.append(Violacion("R-POB-TECHO", d))
        if reglas.criterio.tolerancia == "dura" and p > ctx.objetivo + ctx.tol and not sin_techo:
            out.append(Violacion("R-TOL", d))
        if reglas.provincia_unica and len({u.provincia for u in us}) > 1:
            out.append(Violacion("R-PROV", d))
        if reglas.contiguidad:
            comps = _componentes(ms, ctx.adj)
            cerradas = [c for c in comps if not any(y in libres for x in c for y in ctx.adj.get(x, ()))]
            if cerradas and len(comps) > 1:
                out.append(Violacion("R-CONTIG", d))
            elif cerradas:  # distrito entero cerrado: ya es definitivo
                out += violaciones_distrito(ctx, d, us)
    if reglas.disciplina_municipal:
        claves = pre.claves
        claves_d = {d: {m for x in ms for m in claves[x]} for d, ms in miembros.items()}
        m_d: dict[str, set[str]] = defaultdict(set)
        m_asig: dict[str, int] = defaultdict(int)
        for uid, d in asig.items():
            for m in claves[uid]:
                m_d[m].add(d)
                m_asig[m] += 1
        for m, ds in m_d.items():
            minimo, maximo = pre.rango[m]
            if len(ds) > maximo:
                out.append(Violacion("R-MUN-MAX", m))
            mixtos = sum(1 for d in ds if len(claves_d[d]) > 1)
            if len(ds) > 1 and mixtos > reglas.max_mixtos:
                out.append(Violacion("R-MUN-MIXTOS", m))
            if m_asig[m] == pre.m_n[m] and len(ds) < minimo:
                out.append(Violacion("R-MUN-MIN", m))
    if reglas.nucleos_cerrados:
        nucleo = pre.nucleo
        for d, ms in miembros.items():
            ns = {nucleo.get(x) for x in ms}
            if len(ns) > 1 and any(n is not None for n in ns):
                out.append(Violacion("R-NUCLEO", d))
        n_d: dict[str, set[str]] = defaultdict(set)
        for uid, n in nucleo.items():
            if uid in asig:
                n_d[n].add(asig[uid])
        out += [Violacion("R-NUCLEO", n) for n, ds in n_d.items() if len(ds) > 1]
    return out


def _orden_bfs(problema: Problema, adj) -> list[str]:
    orden, vistos = [], set()
    for u in problema.unidades:
        if u.id in vistos:
            continue
        vistos.add(u.id)
        cola = deque([u.id])
        while cola:
            x = cola.popleft()
            orden.append(x)
            for y in sorted(adj.get(x, ())):
                if y not in vistos:
                    vistos.add(y)
                    cola.append(y)
    return orden


def enumerar(problema: Problema, reglas: Reglas, presupuesto: int | None = None, max_planes: int = 1000,
             clave=None) -> dict:
    """Recuento exacto de planes válidos si cabe en el presupuesto de nodos. Con `clave` (plan -> valor ordenable),
    además el mejor plan válido (menor clave) entre TODOS los recorridos."""
    ctx = Contexto.de(problema, reglas)
    pre = _Constantes(problema, reglas, ctx)
    if presupuesto is None:
        presupuesto = reglas.criterio.presupuesto_nodos
    if presupuesto < 1:
        raise ValueError("presupuesto de nodos debe ser >= 1")
    orden = _orden_bfs(problema, ctx.adj)
    asig: dict[str, str] = {}
    estado = {"nodos": 0, "agotado": False}
    huellas: list[str] = []
    planes: list[dict] = []
    mejor = {"plan": None, "clave": None, "segundo": None, "empatados": 0}

    def canonico() -> str:
        bloques = defaultdict(list)
        for uid, d in asig.items():
            bloques[d].append(uid)
        return "|".join(sorted(",".join(sorted(b)) for b in bloques.values()))

    def rec(i: int, usadas: int):
        if estado["agotado"]:
            return
        estado["nodos"] += 1
        if estado["nodos"] > presupuesto:
            estado["agotado"] = True
            return
        if podar(problema, reglas, asig, ctx, pre):
            return
        if i == len(orden):
            if evaluar(problema, reglas, asig).valido:
                huellas.append(hashlib.sha256(canonico().encode()).hexdigest())
                if len(planes) < max_planes:
                    planes.append(dict(asig))
                if clave is not None:
                    c = clave(asig)
                    if mejor["clave"] is None or c < mejor["clave"]:
                        mejor["segundo"] = mejor["clave"]
                        mejor.update(plan=dict(asig), clave=c, empatados=1)
                    elif c == mejor["clave"]:
                        mejor["empatados"] += 1
                    elif mejor["segundo"] is None or c < mejor["segundo"]:
                        mejor["segundo"] = c
            return
        u = orden[i]
        for d in range(min(usadas + 1, reglas.k)):
            asig[u] = f"D{d}"
            rec(i + 1, max(usadas, d + 1))
            del asig[u]

    rec(0, 0)
    completo = not estado["agotado"]
    huella = hashlib.sha256("\n".join(sorted(huellas)).encode()).hexdigest() if completo else ""
    out = {"completo": completo, "nodos": min(estado["nodos"], presupuesto), "validos": len(huellas),
           "huella": huella, "planes": planes, "huella_reglas": reglas.huella()}
    if clave is not None:
        out.update(mejor=mejor["plan"], mejor_clave=mejor["clave"], segundo_clave=mejor["segundo"],
                   empatados=mejor["empatados"])
    return out
