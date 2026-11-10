#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PROYECTO: Diputado de Distrito
COMPONENTE: núcleo de reglas del motor 2 — estado incremental (camino caliente de los generadores)
VERSIÓN: 1.0.0
NOMBRE DE VERSIÓN: Núcleo único de reglas · F1
FECHA: 2026-11-10
ESTADO: candidato (motor 2; producción no lo importa)
CAMBIOS: fichero nuevo.
MOTIVO: T-160: Flip/ReCom/recocido consultan lo mismo que evaluar() sin recalcular el plan entero.
ANTERIOR: ninguna (fichero nuevo)
QUÉ HACE: Estado(problema, reglas, asignacion) guarda las violaciones por ámbito con las funciones de evaluar.py;
  aplicar(u, d1) solo recalcula los ámbitos tocados (distritos origen y destino, municipios presentes en ellos,
  cuotas, núcleos afectados y plan). Invariante probado: violaciones() == evaluar(...).violaciones.
"""
from __future__ import annotations

from collections import defaultdict
from typing import Mapping

from .evaluar import (Contexto, Violacion, grupos_nucleo, provincia_de, violaciones_cuotas, violaciones_distrito,
                      violaciones_municipio, violaciones_nucleo, violaciones_plan)
from .modelo import Problema, Reglas


class Estado:
    def __init__(self, problema: Problema, reglas: Reglas, asignacion: Mapping[str, object]):
        self.p, self.r = problema, reglas
        self.ctx = Contexto.de(problema, reglas)
        self.campo = reglas.campo_r012
        self.asig = {str(u): str(d) for u, d in asignacion.items()}
        self.miembros: dict[str, set[str]] = defaultdict(set)
        for uid, d in self.asig.items():
            if uid in problema.por_id:
                self.miembros[d].add(uid)
        self.nucleos = grupos_nucleo(problema) if reglas.nucleos_cerrados else {}
        self.nucleo_de = {uid: n for n, ms in self.nucleos.items() for uid in ms}
        self.m_pob: dict[str, int] = defaultdict(int)
        self.m_d: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))  # municipio -> distrito -> nº
        self.d_m: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))  # distrito -> municipio -> nº
        if reglas.disciplina_municipal:
            for uid, d in self.asig.items():
                if uid in problema.por_id:
                    m = getattr(problema.por_id[uid], self.campo)
                    self.m_pob[m] += problema.por_id[uid].poblacion
                    self.m_d[m][d] += 1
                    self.d_m[d][m] += 1
        self.v_dist = {d: violaciones_distrito(self.ctx, d, self._us(d)) for d in self.miembros}
        self.prov_d = {d: provincia_de(reglas, self._us(d)) for d in self.miembros}
        self.v_mun = {m: self._v_mun(m) for m in self.m_pob}
        self.v_nuc = {n: self._v_nuc(n) for n in self.nucleos}
        self._recalcular_globales()

    # ------------------------------------------------------------------ auxiliares
    def _us(self, d):
        return [self.p.por_id[uid] for uid in self.miembros.get(d, ())]

    def _v_mun(self, m):
        ds = {d for d, n in self.m_d[m].items() if n > 0}
        mixtos = sum(1 for d in ds if sum(1 for x in self.d_m[d].values() if x > 0) > 1)
        return violaciones_municipio(self.ctx, m, self.m_pob[m], ds, mixtos)

    def _v_nuc(self, n):
        return violaciones_nucleo(n, self.nucleos[n], self.asig, self.miembros)

    def _recalcular_globales(self):
        cuenta: dict[str, int] = defaultdict(int)
        for prov in self.prov_d.values():
            if prov is not None:
                cuenta[prov] += 1
        self.v_cuotas = violaciones_cuotas(self.ctx, cuenta)
        self.v_plan = violaciones_plan(self.p, self.r, self.asig, sum(1 for ms in self.miembros.values() if ms))

    # ------------------------------------------------------------------ interfaz
    def violaciones(self) -> tuple[Violacion, ...]:
        todas = list(self.v_plan) + list(self.v_cuotas)
        for grupo in (self.v_dist, self.v_mun, self.v_nuc):
            for vs in grupo.values():
                todas += vs
        return tuple(sorted(set(todas)))

    def aplicar(self, u: str, d1: object) -> None:
        u, d1 = str(u), str(d1)
        d0 = self.asig[u]
        if d0 == d1:
            return
        self.asig[u] = d1
        self.miembros[d0].discard(u)
        self.miembros[d1].add(u)
        tocados_m: set[str] = set()
        if self.r.disciplina_municipal:
            m = getattr(self.p.por_id[u], self.campo)
            self.m_d[m][d0] -= 1
            self.m_d[m][d1] += 1
            self.d_m[d0][m] -= 1
            self.d_m[d1][m] += 1
            tocados_m = {x for d in (d0, d1) for x, n in self.d_m[d].items() if n > 0} | {m}
        for d in (d0, d1):
            if self.miembros[d]:
                us = self._us(d)
                self.v_dist[d] = violaciones_distrito(self.ctx, d, us)
                self.prov_d[d] = provincia_de(self.r, us)
            else:
                self.miembros.pop(d, None)
                self.v_dist.pop(d, None)
                self.prov_d.pop(d, None)
        for m in tocados_m:
            self.v_mun[m] = self._v_mun(m)
        afectadas = self.miembros.get(d0, set()) | self.miembros.get(d1, set())
        for n in {self.nucleo_de[x] for x in afectadas if x in self.nucleo_de}:
            self.v_nuc[n] = self._v_nuc(n)
        self._recalcular_globales()

    def movimiento_valido(self, u: str, d1: object) -> bool:
        """True si mover `u` a `d1` no añade ninguna violación (regla, ámbito) que el plan no tuviera ya: en un plan
        válido equivale a «sigue siendo válido»; en uno inválido permite reparar sin empeorar. Prueba y deshace."""
        u, d1 = str(u), str(d1)
        d0 = self.asig[u]
        if d0 == d1:
            return True
        antes = {(v.regla, v.ambito) for v in self.violaciones()}
        self.aplicar(u, d1)
        try:
            return {(v.regla, v.ambito) for v in self.violaciones()} <= antes
        finally:
            self.aplicar(u, d0)
