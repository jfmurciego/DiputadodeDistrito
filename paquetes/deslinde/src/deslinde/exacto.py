#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PROYECTO: Diputado de Distrito
COMPONENTE: Deslinde — candidato «exacto»: óptimo D8 con un resolutor exacto abierto (OR-Tools CP-SAT)
VERSIÓN: 1.0.0
NOMBRE DE VERSIÓN: Exacto D8 · CP-SAT lexicográfico determinista
FECHA: 2026-11-14
ESTADO: candidato (Deslinde 1.1)
CAMBIOS: fichero nuevo.
MOTIVO: T-297 (H1, D-73): el estudio T-296 demostró el óptimo D8 en 8 provincias con K ≤ 4 en segundos y halló planes
  mejores que el ganador en Burgos y Valladolid. El resolutor entra como un competidor más; la aceptación no cambia.
ANTERIOR: ninguna (fichero nuevo)
QUÉ HACE:
  resolver(problema, reglas, natural, pista) -> (plan | None, info). Se aplica solo con D8, 2 ≤ K ≤ K_MAX (4), una
  circunscripción y sin exenciones de suelo ni techo (si no, info["aplicable"] = False con el motivo y no hay plan).
  Átomos: unidades que el núcleo obliga a ir juntas (clave R012 indivisible y núcleo cerrado), por componentes conexas.
  Modelo (el del estudio T-296 y herramientas/certificador_exacto 1.4.0): asignación, población en [suelo, techo]
  (tolerancia dura si el criterio lo pide), R-NUCLEO, contigüidad por árbol padre/nivel con raíz en el átomo mínimo
  (ruptura de simetría), disciplina municipal R012 (K por clave entre ceil(P/techo) y ceil(P/objetivo), máx. mixtos).
  Objetivo: la clave D8 de naturalidad_clave por etapas (fuera de tolerancia → exceso sobre el 8 % → partidos y
  comarcas partidos → frontera cortada en mm → desvío máximo); cada óptimo se fija antes de la siguiente. Si una etapa
  no prueba el óptimo dentro de su tope, se para y se devuelve la mejor solución hallada.
  DETERMINISTA: 1 hilo, random_seed 0 y tope en tiempo DETERMINISTA de CP-SAT (no de reloj): misma entrada, mismo plan.
  El plan devuelto se vuelve a comprobar con el núcleo (reglas.evaluar.valido); si no es válido, no hay plan. Quien llama
  lo juzga además con la clave oficial, como a cualquier candidato.
  info: aplicable, motivo, estado (OPTIMO | MEJOR_VALIDO | SIN_SOLUCION | NO_APLICA), etapas [(nombre, estado, valor,
  cota)], átomos, versión de ortools; todo lo que cambia el plan entra en la huella de la competición.
Necesita ortools (pin en paquetes/deslinde/requirements-deslinde.lock); sin él, info["estado"] = "SIN_ORTOOLS".
"""
from __future__ import annotations

import math
from collections import defaultdict
from fractions import Fraction
from typing import Mapping

from .reglas import Problema, Reglas
from .reglas.evaluar import valido

VERSION = "1.0.0"
K_MAX = 4
TOPE_D8 = Fraction(2, 25)  # 8 %, como naturalidad_clave.TOPES["D8"]
TIEMPO_DETERMINISTA = 60.0  # por etapa, unidades deterministas de CP-SAT
ETAPAS = ("fuera", "exceso_8", "partidas", "frontera_mm", "desvio")


def aplicable(problema: Problema, reglas: Reglas, funcion: str) -> str | None:
    """None si se aplica; si no, el motivo."""
    if funcion != "D8":
        return f"función {funcion} (solo D8)"
    if not 2 <= reglas.k <= K_MAX:
        return f"K={reglas.k} fuera de 2..{K_MAX}"
    if len(dict(reglas.cuotas)) > 1:
        return "varias circunscripciones"
    if reglas.exentos_municipio or reglas.exentas_particion or reglas.exentas_techo:
        return "exenciones de suelo o techo"
    if reglas.provincia_unica and len({u.provincia for u in problema.unidades}) > 1:
        return "varias provincias"
    return None


def _componentes(nodos, adj) -> list[list]:
    vistos, out = set(), []
    for s in sorted(nodos):
        if s in vistos:
            continue
        comp, pila = [], [s]
        vistos.add(s)
        while pila:
            a = pila.pop()
            comp.append(a)
            for b in sorted(adj[a]):
                if b not in vistos:
                    vistos.add(b)
                    pila.append(b)
        out.append(sorted(comp))
    return out


def atomos(problema: Problema, reglas: Reglas):
    """Grupos de unidades que van juntas por regla (clave R012 indivisible, núcleo cerrado), en componentes conexas."""
    objetivo = reglas.limites(problema.poblacion_total)[0]
    campo = reglas.campo_r012
    padre = {u.id: u.id for u in problema.unidades}

    def raiz(a):
        while padre[a] != a:
            padre[a] = padre[padre[a]]
            a = padre[a]
        return a

    def unir(a, b):
        ra, rb = raiz(a), raiz(b)
        if ra != rb:
            padre[max(ra, rb)] = min(ra, rb)

    por_clave, pob_clave = defaultdict(list), defaultdict(int)
    for u in problema.unidades:
        for m, p in u.piezas(campo):
            por_clave[m].append(u.id)
            pob_clave[m] += p
    if reglas.disciplina_municipal:
        for m, ids in por_clave.items():
            if m is not None and (pob_clave[m] <= 0 or math.ceil(Fraction(pob_clave[m]) / objetivo) <= 1):
                for s in ids[1:]:
                    unir(ids[0], s)
    if reglas.nucleos_cerrados:
        por_n = defaultdict(list)
        for u in problema.unidades:
            if u.nucleo_cerrado is not None:
                por_n[u.nucleo_cerrado].append(u.id)
        for ids in por_n.values():
            for s in ids[1:]:
                unir(ids[0], s)
    grupos = defaultdict(list)
    for u in problema.unidades:
        grupos[raiz(u.id)].append(u.id)
    adj = problema.adyacencia(reglas.criterio.contiguidad_con_puentes)
    out, atomo_de = [], {}
    for g, ids in sorted(grupos.items()):
        ss = set(ids)
        for comp in _componentes(ids, {s: [v for v in adj[s] if v in ss] for s in ids}):
            us = [problema.por_id[s] for s in comp]
            claves = defaultdict(int)
            for u in us:
                for m, p in u.piezas(campo):
                    claves[m] += p
            atomo_de.update({s: len(out) for s in comp})
            out.append({"secs": comp, "pop": sum(u.poblacion for u in us), "grupo": g, "claves": dict(claves),
                        "nucleos": ({u.nucleo_cerrado for u in us} if reglas.nucleos_cerrados else {None})})
    aristas = sorted({tuple(sorted((atomo_de[a], atomo_de[b]))) for a, vs in adj.items() for b in vs
                      if atomo_de[a] != atomo_de[b]})
    return out, aristas, atomo_de


class _Modelo:
    def __init__(self, problema: Problema, reglas: Reglas, natural):
        from ortools.sat.python import cp_model
        self.cp = cp_model
        self.at, aristas, atomo_de = atomos(problema, reglas)
        at, n, K = self.at, len(self.at), reglas.k
        self.n, self.K = n, K
        obj, suelo, techo, tol = reglas.limites(problema.poblacion_total)
        num, den = obj.numerator, obj.denominator
        self.num = num
        m = self.m = cp_model.CpModel()
        x = self.x = {(i, k): m.NewBoolVar(f"x{i}_{k}") for i in range(n) for k in range(K)}
        for i in range(n):
            m.AddExactlyOne([x[i, k] for k in range(K)])
        por_grupo = defaultdict(list)
        for i, a in enumerate(at):
            por_grupo[a["grupo"]].append(i)
        for idx in por_grupo.values():
            for j in idx[1:]:
                for k in range(K):
                    m.Add(x[j, k] == x[idx[0], k])
        for nu in sorted({nu for a in at for nu in a["nucleos"] if nu is not None}):
            ancla = min(i for i, a in enumerate(at) if nu in a["nucleos"])
            fuera = [j for j, a in enumerate(at) if a["nucleos"] != {nu}]
            for k in range(K):
                if fuera:
                    m.Add(sum(x[j, k] for j in fuera) == 0).OnlyEnforceIf(x[ancla, k])
        total = problema.poblacion_total
        big = den * total + num
        dev = []
        for k in range(K):
            v = m.NewIntVar(0, total, f"p{k}")
            m.Add(v == sum(a["pop"] * x[i, k] for i, a in enumerate(at)))
            m.Add(v <= math.floor(techo))
            m.Add(v >= math.ceil(suelo))
            if reglas.criterio.tolerancia == "dura":
                m.Add(v <= math.floor(obj + tol))
                m.Add(v >= math.ceil(obj - tol))
            d = m.NewIntVar(0, big, f"dev{k}")  # den·|p − objetivo|
            m.AddAbsEquality(d, den * v - num)
            dev.append(d)
        r = {(i, k): m.NewBoolVar(f"r{i}_{k}") for i in range(n) for k in range(K)}
        pos = []
        for k in range(K):
            m.AddExactlyOne([r[i, k] for i in range(n)])
            pv = m.NewIntVar(0, max(0, n - 1), f"pos{k}")
            m.Add(pv == sum(i * r[i, k] for i in range(n)))
            for i in range(n):
                m.AddImplication(r[i, k], x[i, k])
                m.Add(pv <= i).OnlyEnforceIf(x[i, k])
            pos.append(pv)
        for k in range(K - 1):
            m.Add(pos[k] < pos[k + 1])
        vecinos = defaultdict(list)
        for a, b in aristas:
            vecinos[a].append(b)
            vecinos[b].append(a)
        dd = self.d = [m.NewIntVar(0, K - 1, f"d{i}") for i in range(n)]
        for i in range(n):
            m.Add(dd[i] == sum(k * x[i, k] for k in range(K)))
        if reglas.contiguidad:
            nivel = [m.NewIntVar(0, max(0, n - 1), f"h{i}") for i in range(n)]
            for i in range(n):
                es_raiz = [r[i, k] for k in range(K)]
                padres = []
                for j in vecinos[i]:
                    pa = m.NewBoolVar(f"pa{i}_{j}")
                    m.Add(dd[i] == dd[j]).OnlyEnforceIf(pa)
                    m.Add(nivel[i] >= nivel[j] + 1).OnlyEnforceIf(pa)
                    padres.append(pa)
                m.AddExactlyOne(padres + es_raiz)
                ri = m.NewBoolVar(f"raiz{i}")
                m.Add(sum(es_raiz) == ri)
                m.Add(nivel[i] == 0).OnlyEnforceIf(ri)
        if reglas.disciplina_municipal:
            por_clave, pob_clave = defaultdict(list), defaultdict(int)
            for i, a in enumerate(at):
                for c, pc in a["claves"].items():
                    por_clave[c].append(i)
                    pob_clave[c] += pc
            y = {}
            for c, idx in por_clave.items():
                for k in range(K):
                    y[c, k] = m.NewBoolVar("")
                    m.AddMaxEquality(y[c, k], [x[i, k] for i in idx])
            mixto = []
            for k in range(K):
                mk = m.NewBoolVar(f"mix{k}")
                ys = [y[c, k] for c in por_clave]
                m.Add(sum(ys) >= 2).OnlyEnforceIf(mk)
                m.Add(sum(ys) <= 1).OnlyEnforceIf(mk.Not())
                mixto.append(mk)
            for c in por_clave:
                pc = Fraction(pob_clave[c])
                lo = max(1, math.ceil(pc / techo)) if pc > 0 else 1
                hi = max(1, math.ceil(pc / obj)) if pc > 0 else 1
                ys = [y[c, k] for k in range(K)]
                m.Add(sum(ys) >= lo)
                m.Add(sum(ys) <= hi)
                if hi > 1:
                    parte = m.NewBoolVar("")
                    m.Add(sum(ys) >= 2).OnlyEnforceIf(parte)
                    m.Add(sum(ys) <= 1).OnlyEnforceIf(parte.Not())
                    zs = []
                    for k in range(K):
                        z = m.NewBoolVar("")
                        m.AddMultiplicationEquality(z, [y[c, k], mixto[k]])
                        zs.append(z)
                    m.Add(sum(zs) <= reglas.max_mixtos).OnlyEnforceIf(parte)
        # términos de la clave D8 (enteros exactos)
        f = [m.NewBoolVar(f"fuera{k}") for k in range(K)]
        for k in range(K):
            m.Add(dev[k] <= math.floor(tol * den)).OnlyEnforceIf(f[k].Not())
        z = m.NewIntVar(TOPE_D8.numerator * num, TOPE_D8.denominator * big, "exceso")
        for k in range(K):
            m.Add(z >= TOPE_D8.denominator * dev[k]).OnlyEnforceIf(f[k].Not())
        partidas = []
        for dem in (natural.pj, natural.ca):
            grupos = defaultdict(set)
            for u, g in dem.items():
                if g is not None:
                    grupos[g].add(atomo_de[u])
            for g, idx in sorted(grupos.items()):
                if len(idx) < 2:
                    continue
                ys = []
                for k in range(K):
                    yk = m.NewBoolVar("")
                    m.AddMaxEquality(yk, [x[i, k] for i in sorted(idx)])
                    ys.append(yk)
                s = m.NewBoolVar("")
                m.Add(sum(ys) <= 1).OnlyEnforceIf(s.Not())
                partidas.append(s)
        w = defaultdict(int)
        for (ua, ub), metros in natural.largo.items():
            i, j = atomo_de[ua], atomo_de[ub]
            if i != j:
                w[tuple(sorted((i, j)))] += int(round(metros * 1000))
        cortes = []
        for (i, j), mm in sorted(w.items()):
            if mm > 0:
                c = m.NewBoolVar("")
                m.Add(dd[i] == dd[j]).OnlyEnforceIf(c.Not())
                cortes.append(mm * c)
        dmax = m.NewIntVar(0, big, "dmax")
        m.AddMaxEquality(dmax, dev)
        self.terminos = dict(zip(ETAPAS, (sum(f), z, sum(partidas) if partidas else 0,
                                          sum(cortes) if cortes else 0, dmax)))

    def etiquetas(self, plan: Mapping[str, str]) -> list[int] | None:
        """Plan (unidad → distrito) a etiquetas por átomo con la ruptura de simetría; None si parte un átomo."""
        lab = []
        for a in self.at:
            ds = {plan.get(s) for s in a["secs"]}
            if len(ds) != 1 or None in ds:
                return None
            lab.append(ds.pop())
        orden: dict = {}
        for v in lab:
            orden.setdefault(v, len(orden))
        return [orden[v] for v in lab] if len(orden) == self.K else None

    def a_plan(self, sol) -> dict[str, str]:
        return {s: f"X{k}" for i, a in enumerate(self.at) for k in range(self.K) if sol.Value(self.x[i, k])
                for s in a["secs"]}

    def resolver(self, pista: Mapping[str, str] | None, tiempo_det: float) -> tuple[dict | None, list]:
        lab = self.etiquetas(pista) if pista else None
        if lab is not None:
            for i, k in enumerate(lab):
                for kk in range(self.K):
                    self.m.AddHint(self.x[i, kk], kk == k)
        etapas, mejor = [], None
        for nombre in ETAPAS:
            t = self.terminos[nombre]
            if isinstance(t, int):
                etapas.append([nombre, "CONSTANTE", t, t])
                continue
            self.m.Minimize(t)
            s = self.cp.CpSolver()
            s.parameters.num_workers = 1
            s.parameters.random_seed = 0
            s.parameters.max_deterministic_time = float(tiempo_det)
            est = s.StatusName(s.Solve(self.m))
            valor = cota = None
            if est in ("OPTIMAL", "FEASIBLE"):
                valor = int(round(s.ObjectiveValue()))
                mejor = self.a_plan(s)
                self.m.ClearHints()
                for i, a in enumerate(self.at):
                    for k in range(self.K):
                        self.m.AddHint(self.x[i, k], bool(s.Value(self.x[i, k])))
            if est in ("OPTIMAL", "FEASIBLE", "UNKNOWN"):
                cota = int(math.ceil(s.BestObjectiveBound() - 1e-9))
            etapas.append([nombre, est, valor, cota])
            if est != "OPTIMAL":
                break
            self.m.Add(t == valor)
        return mejor, etapas


def resolver(problema: Problema, reglas: Reglas, natural, pista: Mapping[str, str] | None = None, *,
             funcion: str = "D8", tiempo_det: float = TIEMPO_DETERMINISTA) -> tuple[dict | None, dict]:
    info: dict = {"version": VERSION, "k_max": K_MAX, "tiempo_determinista": tiempo_det}
    motivo = aplicable(problema, reglas, funcion)
    if motivo is not None:
        return None, {**info, "aplicable": False, "motivo": motivo, "estado": "NO_APLICA"}
    try:
        import ortools  # noqa: PLC0415
    except ImportError:
        return None, {**info, "aplicable": True, "estado": "SIN_ORTOOLS"}
    info.update({"aplicable": True, "ortools": ortools.__version__})
    mod = _Modelo(problema, reglas, natural)
    info["atomos"] = mod.n
    plan, etapas = mod.resolver(pista, tiempo_det)
    info["etapas"] = etapas
    if plan is None:
        info["estado"] = "SIN_SOLUCION"
        return None, info
    if not valido(problema, reglas, plan):
        info["estado"] = "SIN_SOLUCION"
        info["motivo"] = "el plan del modelo no cumple el núcleo"
        return None, info
    info["estado"] = "OPTIMO" if len(etapas) == len(ETAPAS) and all(
        e[1] in ("OPTIMAL", "CONSTANTE") for e in etapas) else "MEJOR_VALIDO"
    return plan, info
