#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PROYECTO: Diputado de Distrito
COMPONENTE: núcleo de reglas del motor 2 — poda monótona y enumeración exacta con presupuesto de nodos
VERSIÓN: 1.0.0
NOMBRE DE VERSIÓN: Núcleo único de reglas · F1
FECHA: 2026-11-10
ESTADO: candidato (motor 2; producción no lo importa)
CAMBIOS: fichero nuevo.
MOTIVO: T-160: donde el espacio de planes cabe, enumerar todos en vez de muestrear (criterio del propietario: cadena
  solo donde el espacio es grande). El veredicto de cada plan enumerado es evaluar() del núcleo.
ANTERIOR: ninguna (fichero nuevo)
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

from .evaluar import Contexto, Violacion, evaluar, violaciones_distrito
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


def podar(problema: Problema, reglas: Reglas, parcial: Mapping[str, object],
          ctx: Contexto | None = None) -> list[Violacion]:
    ctx = ctx or Contexto.de(problema, reglas)
    asig = {str(u): str(d) for u, d in parcial.items()}
    libres = {u.id for u in problema.unidades} - set(asig)
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
        if p > ctx.techo:
            out.append(Violacion("R-POB-TECHO", d))
        if reglas.criterio.tolerancia == "dura" and p > ctx.objetivo + ctx.tol:
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
        campo = reglas.campo_r012
        m_tot: dict[str, int] = defaultdict(int)
        m_n: dict[str, int] = defaultdict(int)
        for u in problema.unidades:
            for m, pm in u.piezas(campo):
                m_tot[m] += pm
                m_n[m] += 1
        claves_d = {d: {m for x in ms for m, _ in por[x].piezas(campo)} for d, ms in miembros.items()}
        m_d: dict[str, set[str]] = defaultdict(set)
        m_asig: dict[str, int] = defaultdict(int)
        for uid, d in asig.items():
            for m, _ in por[uid].piezas(campo):
                m_d[m].add(d)
                m_asig[m] += 1
        for m, ds in m_d.items():
            minimo, maximo = ctx.rango_municipal(m_tot[m])
            if len(ds) > maximo:
                out.append(Violacion("R-MUN-MAX", m))
            mixtos = sum(1 for d in ds if len(claves_d[d]) > 1)
            if len(ds) > 1 and mixtos > reglas.max_mixtos:
                out.append(Violacion("R-MUN-MIXTOS", m))
            if m_asig[m] == m_n[m] and len(ds) < minimo:
                out.append(Violacion("R-MUN-MIN", m))
    if reglas.nucleos_cerrados:
        nucleo = {u.id: u.nucleo_cerrado for u in problema.unidades if u.nucleo_cerrado is not None}
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


def enumerar(problema: Problema, reglas: Reglas, presupuesto: int | None = None, max_planes: int = 1000) -> dict:
    """Recuento exacto de planes válidos si cabe en el presupuesto de nodos."""
    ctx = Contexto.de(problema, reglas)
    presupuesto = presupuesto or reglas.criterio.presupuesto_nodos
    orden = _orden_bfs(problema, ctx.adj)
    asig: dict[str, str] = {}
    estado = {"nodos": 0, "agotado": False}
    huellas: list[str] = []
    planes: list[dict] = []

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
        if podar(problema, reglas, asig, ctx):
            return
        if i == len(orden):
            if evaluar(problema, reglas, asig).valido:
                huellas.append(hashlib.sha256(canonico().encode()).hexdigest())
                if len(planes) < max_planes:
                    planes.append(dict(asig))
            return
        u = orden[i]
        for d in range(min(usadas + 1, reglas.k)):
            asig[u] = f"D{d}"
            rec(i + 1, max(usadas, d + 1))
            del asig[u]

    rec(0, 0)
    completo = not estado["agotado"]
    huella = hashlib.sha256("\n".join(sorted(huellas)).encode()).hexdigest() if completo else ""
    return {"completo": completo, "nodos": min(estado["nodos"], presupuesto), "validos": len(huellas),
            "huella": huella, "planes": planes, "huella_reglas": reglas.huella()}
