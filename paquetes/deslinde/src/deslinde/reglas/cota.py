#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PROYECTO: Diputado de Distrito
COMPONENTE: núcleo de reglas del motor 2 — cota inferior de los nodos de la enumeración exacta
VERSIÓN: 1.0.0
NOMBRE DE VERSIÓN: Cota de nodos · no lanzar el exhaustivo que no acaba
FECHA: 2026-11-11
ESTADO: candidato (motor 2; producción no lo importa)
CAMBIOS: fichero nuevo.
MOTIVO: T-261 (D-89): T-254 midió que el exhaustivo agota el presupuesto sin aportar candidato y se lleva el 60-87 %
  de la competición. Si una cota demuestra que el árbol de enumerar() tiene más nodos que el presupuesto, no se lanza.
ANTERIOR: ninguna (fichero nuevo)
QUÉ HACE:
  cota_nodos(problema, reglas, plan, presupuesto) -> dict: cota INFERIOR del número de nodos que visitaría
    enumerar(problema, reglas) sin presupuesto. Argumento:
    1. enumerar() recorre las particiones en etiquetas canónicas (D0, D1… por orden de aparición en _orden_bfs) y
       cuenta un nodo en cada llamada; cada nodo no podado de profundidad i < n visita min(usadas + 1, K) hijos
       (podados o no). Total = 1 + Σ_{nodos internos no podados} min(usadas + 1, K).
    2. podar() solo da violaciones seguras (toda extensión las tiene; contrato de enumerar.py, probado por fuerza
       bruta): ningún prefijo de un plan VÁLIDO (evaluar) se poda, y todos se visitan.
    3. Así, para un conjunto de planes válidos, el árbol de prefijos (trie) de sus etiquetas canónicas está dentro del
       árbol no podado, y 1 + Σ_{nodos del trie con profundidad < n} min(usadas + 1, K) <= total.
    Los planes válidos salen de un recorrido en anchura determinista desde `plan` (el canónico) moviendo una unidad
    a un distrito vecino, con tope de evaluaciones. Si `plan` no es válido no hay cota (0) y se enumera como siempre.
    Campos: cota (int), supera (cota > presupuesto, es decir, enumerar() agotaría el presupuesto), planes_validos,
    evaluaciones, tiempo_s.
Solo stdlib.
"""
from __future__ import annotations

import time
from typing import Mapping

from .enumerar import _orden_bfs
from .evaluar import Contexto, evaluar
from .modelo import Problema, Reglas

MAX_EVALUACIONES = 20_000


def cota_nodos(problema: Problema, reglas: Reglas, plan: Mapping[str, object], presupuesto: int,
               max_evaluaciones: int = MAX_EVALUACIONES) -> dict:
    t0 = time.monotonic()
    plan0 = {str(u): str(d) for u, d in plan.items()}
    ids = [u.id for u in problema.unidades]
    out = {"cota": 0, "supera": False, "planes_validos": 0, "evaluaciones": 0, "presupuesto": presupuesto}
    if set(plan0) != set(ids) or not evaluar(problema, reglas, plan0).valido:
        out["motivo"] = "el plan de partida no es válido: sin cota"
        out["tiempo_s"] = round(time.monotonic() - t0, 3)
        return out
    ctx = Contexto.de(problema, reglas)
    adj = ctx.adj
    orden = _orden_bfs(problema, adj)
    n, k = len(orden), reglas.k
    raiz: dict = {}
    cota = 2  # la raíz (1) y sus hijos: con usadas=0 solo D0 (min(1, K) = 1)

    def etiquetas(p: Mapping[str, str]) -> tuple[int, ...]:
        m: dict[str, int] = {}
        return tuple(m.setdefault(p[u], len(m)) for u in orden)

    def insertar(s: tuple[int, ...]) -> int:
        nodo, usadas, nuevos = raiz, 0, 0
        for i, et in enumerate(s):
            usadas = max(usadas, et + 1)
            hijo = nodo.get(et)
            if hijo is None:
                hijo = nodo[et] = {}
                if i + 1 < n:  # nodo nuevo de profundidad i+1 < n: visita min(usadas + 1, K) hijos
                    nuevos += min(usadas + 1, k)
            nodo = hijo
        return nuevos

    s0 = etiquetas(plan0)
    cota += insertar(s0)
    vistos, cola, qi, evals = {s0}, [plan0], 0, 0
    while qi < len(cola) and cota <= presupuesto and evals < max_evaluaciones:
        p = cola[qi]
        qi += 1
        for u in orden:
            for d in sorted({p[v] for v in adj[u]} - {p[u]}):
                q = dict(p)
                q[u] = d
                s = etiquetas(q)
                if s in vistos:
                    continue
                vistos.add(s)
                evals += 1
                if evaluar(problema, reglas, q).valido:
                    cota += insertar(s)
                    cola.append(q)
                if cota > presupuesto or evals >= max_evaluaciones:
                    break
            if cota > presupuesto or evals >= max_evaluaciones:
                break
    out.update(cota=cota, supera=cota > presupuesto, planes_validos=len(cola), evaluaciones=evals,
               tiempo_s=round(time.monotonic() - t0, 3))
    return out
