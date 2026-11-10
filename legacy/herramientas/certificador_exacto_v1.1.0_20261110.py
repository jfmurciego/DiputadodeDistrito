#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Certificador exacto (T-136): programación entera con contigüidad para una circunscripción.

PROYECTO: Diputado de Distrito
VERSIÓN: 1.1.0
NOMBRE DE VERSIÓN: Certificador exacto sobre el núcleo de reglas
FECHA: 2026-11-10
ESTADO: candidato (diagnóstico; no genera productos ni toca el motor)
CAMBIOS: 1.1.0 — las reglas salen del núcleo ddd_motor2.reglas (Reglas.desde_contrato, limites() exactos, Criterio,
  evaluar()); se quitan las reglas propias. Las secciones se leen del M04 (o M05/M06), con provincia, municipio y
  partición de los campos del contrato (DDD_PARTITION y DDD_MUNICIPALITY_PARTITION en las islas), no del CUSEC.
  La atomicidad de las unidades M04 se aplica con unión-búsqueda (una unidad puede abarcar varios municipios).
  Exención por partición, max_mixed y tolerancia según el Criterio. Solo contigüidad por árbol (flujo y cortes se
  quitan: más lentos en el estudio 1.0.0).
MOTIVO: fallos F1 (Canarias: infactibilidad falsa por leer la provincia del M01, sin DDD_PARTITION ni exenciones por
  partición) y F2 (Cádiz: unidades M04 partidas) que vio T-132; y acuerdo con T-160 de usar el núcleo único.
ANTERIOR: legacy/herramientas/certificador_exacto_v1.0.0_20261110.py
QUÉ HACE: lee el contrato, las secciones de M04 y el grafo M03, y plantea en OR-Tools CP-SAT las reglas del núcleo:
  K, población en [suelo, techo] (exenciones), tolerancia dura si el criterio lo pide, contigüidad (árbol padre/nivel
  por átomo), provincia única y cuotas, disciplina municipal R012 con el campo y max_mixed del núcleo. Átomos:
  unidades M04 (ddd_unit_id) y claves R012 indivisibles (ceil(P/objetivo)=1), unidas y partidas en componentes
  conexas con igualdad de distrito. Objetivos: factibilidad, minimax (|P_k - P/K|), techo (mayor población) y
  enumerar (todos los planes válidos: recuento exacto si termina). Cada plan se juzga con ddd_motor2.reglas.evaluar
  y con la integridad de las unidades M04.
USO: python herramientas/certificador_exacto.py --params territorios/<t>/config/<t>_2025.yaml \
       --grafo <m03_grafo.json> --secciones <m04_semillas.geojson.zip> [--sin-unidades] \
       [--objetivo factibilidad|minimax|techo|enumerar] [--perfil nucleo|produccion] [--referencia <csv>] \
       [--pista <csv>] [--techo-ratio 1.15] [--tiempo 600] [--hilos 4] [--salida <json>] [--asignacion-csv <csv>]
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import resource
import sys
import time
from collections import defaultdict
from fractions import Fraction
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ddd_core.config import load_params_yaml, module_cfg  # noqa: E402
from ddd_motor2.reglas import Criterio, Problema, Reglas, Unidad, evaluar  # noqa: E402

VERSION = "1.1.0"


# --------------------------------------------------------------------------- datos -> núcleo
def _componentes(nodos, adj) -> list[list]:
    rest = set(nodos)
    out = []
    while rest:
        s = min(rest)
        rest.discard(s)
        comp, pila = [s], [s]
        while pila:
            u = pila.pop()
            for v in adj.get(u, ()):
                if v in rest:
                    rest.discard(v)
                    comp.append(v)
                    pila.append(v)
        out.append(sorted(comp))
    return out


def campos(cfg: dict) -> dict:
    """Campos de sección del contrato, con la precedencia de la validación de producción."""
    s6 = module_cfg(cfg, "modulo_06_consolidar_distritos", "step6_export_final")
    val = cfg.get("validation", {}) or {}
    part = cfg.get("partitioning") or {}
    return {"id": s6.get("id_field", "CUSEC"), "pop": s6["pop_field"],
            "prov": str(val.get("province_field", s6.get("province_field", "CPRO"))),
            "mun": str(val.get("municipality_field", s6.get("municipality_field", "CUMUN"))),
            "r012": str(part.get("partition_unit_field") or "") or None}


def _vacio(v) -> bool:
    return v is None or (isinstance(v, float) and math.isnan(v)) or str(v).strip() in ("", "nan", "None")


def leer_secciones(path: str, cfg: dict, criterio: Criterio, con_unidades: bool = True):
    """Unidades del núcleo (una por sección) y unidad M04 de cada sección (ddd_unit_id, si se pide)."""
    from ddd_core.m04_seed_engine_v7411 import load_geo  # lee ddd_unit_id escalar aunque OGR lo guarde como lista

    c = campos(cfg)
    g = load_geo(path)
    filas = g.drop(columns=[x for x in ("geometry",) if x in g.columns]).to_dict("records")
    unidades, unidad_m04 = [], {}
    for r in filas:
        sid = str(r[c["id"]])
        mun = r.get(c["mun"])
        if _vacio(mun) and criterio.respaldo_municipio_cusec:
            mun = r.get("CUMUN") if not _vacio(r.get("CUMUN")) else sid[:5]
        prov = r.get(c["prov"])
        particion = r.get("DDD_PARTITION")
        r012 = r.get(c["r012"]) if c["r012"] else None
        unidades.append(Unidad(id=sid, poblacion=int(round(float(r[c["pop"]] or 0))),
                               municipio=None if _vacio(mun) else str(mun),
                               provincia=None if _vacio(prov) else str(prov),
                               particion=None if _vacio(particion) else str(particion),
                               unidad_r012=None if _vacio(r012) else str(r012)))
        if con_unidades and not _vacio(r.get("ddd_unit_id")):
            unidad_m04[sid] = str(r["ddd_unit_id"])
    return unidades, unidad_m04


def leer_grafo(path: str, ids: set[str]) -> list[tuple[str, str]]:
    g = json.loads(Path(path).read_text(encoding="utf-8"))
    return [(str(e["u"]), str(e["v"])) for e in g["edges"] if str(e["u"]) in ids and str(e["v"]) in ids]


def leer_composicion(path: str) -> dict[str, str]:
    with open(path, encoding="utf-8") as fh:
        rd = csv.DictReader(fh)
        cols = rd.fieldnames or []
        sid = "seccion" if "seccion" in cols else ("CUSEC_KEY" if "CUSEC_KEY" in cols else cols[0])
        did = "distrito" if "distrito" in cols else "district_id"
        return {str(r[sid]): str(r[did]) for r in rd}


def juzgar(problema: Problema, reglas: Reglas, asig: dict[str, str], unidad_m04: dict[str, str]) -> dict:
    """Veredicto del núcleo más la integridad de las unidades M04 (atomicidad de producción)."""
    inf = evaluar(problema, reglas, asig)
    por_u = defaultdict(set)
    for s, u in unidad_m04.items():
        if s in asig:
            por_u[u].add(asig[s])
    partidas = sorted(u for u, ds in por_u.items() if len(ds) > 1)
    return {"estado": "PASS" if inf.valido and not partidas else "FAIL",
            "violaciones": [f"{v.regla}:{v.ambito}" + (f" {v.detalle}" if v.detalle else "")
                            for v in inf.violaciones][:30],
            "unidades_m04_partidas": partidas[:20],
            "max_desviacion_ratio": round(inf.metricas["max_desviacion_ratio"], 5),
            "min_pob": inf.metricas["min_pob"], "max_pob": inf.metricas["max_pob"]}


# --------------------------------------------------------------------------- átomos
def construir_atomos(problema: Problema, reglas: Reglas, unidad_m04: dict[str, str]):
    """Une secciones de una misma unidad M04 y de una misma clave R012 indivisible; parte cada grupo en componentes
    conexas (átomos) con igualdad de distrito entre las de un mismo grupo."""
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

    por_clave: dict = defaultdict(list)
    pob_clave: dict = defaultdict(int)
    for u in problema.unidades:
        for m, p in u.piezas(campo):
            por_clave[m].append(u.id)
            pob_clave[m] += p
    if reglas.disciplina_municipal:
        for m, ids in por_clave.items():
            if m is not None and (pob_clave[m] <= 0 or math.ceil(Fraction(pob_clave[m]) / objetivo) <= 1):
                for s in ids[1:]:
                    unir(ids[0], s)
    por_u: dict = defaultdict(list)
    for s, um in unidad_m04.items():
        if s in padre:
            por_u[um].append(s)
    for ids in por_u.values():
        for s in ids[1:]:
            unir(ids[0], s)
    grupos: dict = defaultdict(list)
    for u in problema.unidades:
        grupos[raiz(u.id)].append(u.id)
    adj = problema.adyacencia(reglas.criterio.contiguidad_con_puentes)
    atomos, atomo_de = [], {}
    for g, ids in sorted(grupos.items()):
        ss = set(ids)
        for comp in _componentes(ids, {s: [v for v in adj[s] if v in ss] for s in ids}):
            us = [problema.por_id[s] for s in comp]
            claves: dict = defaultdict(int)
            for u in us:
                for m, p in u.piezas(campo):
                    claves[m] += p
            atomo_de.update({s: len(atomos) for s in comp})
            atomos.append({"secs": comp, "pop": sum(u.poblacion for u in us), "grupo": g, "claves": dict(claves),
                           "provs": {u.provincia for u in us}, "parts": {u.particion for u in us},
                           "muns": set().union(*(u.municipios() for u in us))})
    aristas = sorted({tuple(sorted((atomo_de[a], atomo_de[b]))) for a, vs in adj.items() for b in vs
                      if atomo_de[a] != atomo_de[b]})
    return atomos, aristas


# --------------------------------------------------------------------------- modelo
def resolver(problema: Problema, reglas: Reglas, unidad_m04: dict[str, str] | None = None, *, tiempo: float,
             hilos: int, objetivo: str = "factibilidad", pista: dict | None = None,
             cota_desviacion: float | None = None) -> dict:
    from ortools.sat.python import cp_model

    t0 = time.time()
    unidad_m04 = unidad_m04 or {}
    atomos, aristas = construir_atomos(problema, reglas, unidad_m04)
    n, K = len(atomos), reglas.k
    obj, suelo, techo, tol = reglas.limites(problema.poblacion_total)
    crit = reglas.criterio
    base = {"atomos": n, "aristas_atomos": len(aristas), "secciones": len(problema.unidades), "k": K,
            "huella_reglas": reglas.huella(),
            "limites": {"objetivo": float(obj), "suelo": float(suelo), "techo": float(techo), "tolerancia": float(tol)}}
    if reglas.provincia_unica and any(len(a["provs"]) > 1 for a in atomos):
        return {**base, "estado": "INFACTIBLE",
                "prueba": "un átomo (unidad M04 o municipio indivisible) cruza provincias"}
    cuotas = dict(reglas.cuotas)
    if reglas.provincia_unica and cuotas:
        prov_d = [p for p, c in sorted(cuotas.items()) for _ in range(c)]
        if len(prov_d) != K:
            return {**base, "estado": "INFACTIBLE", "prueba": "las cuotas provinciales no suman K"}
    else:
        prov_d = [None] * K
    vecinos: dict = defaultdict(list)
    for a, b in aristas:
        vecinos[a].append(b)
        vecinos[b].append(a)
    m = cp_model.CpModel()
    permitido = {(i, k) for i in range(n) for k in range(K)
                 if prov_d[k] is None or atomos[i]["provs"] == {prov_d[k]}}
    x = {(i, k): m.NewBoolVar(f"x{i}_{k}") for (i, k) in permitido}
    for i in range(n):
        xs = [x[i, k] for k in range(K) if (i, k) in x]
        if not xs:
            return {**base, "estado": "INFACTIBLE",
                    "prueba": f"átomo {atomos[i]['secs'][0]} sin distrito de su provincia en las cuotas"}
        m.AddExactlyOne(xs)
    por_grupo: dict = defaultdict(list)
    for i, a in enumerate(atomos):
        por_grupo[a["grupo"]].append(i)
    for idx in por_grupo.values():
        for j in idx[1:]:
            for k in range(K):
                if (idx[0], k) in x:
                    m.Add(x[j, k] == x[idx[0], k])
    total = problema.poblacion_total

    def tiene(pred, k):
        """Booleano «el distrito k contiene algún átomo que cumple pred» (None si ninguno puede)."""
        xs = [x[i, k] for i in range(n) if (i, k) in x and pred(atomos[i])]
        if not xs:
            return None
        b = m.NewBoolVar("")
        m.AddMaxEquality(b, xs)
        return b

    pk = []
    partes = sorted({p for a in atomos for p in a["parts"] if p is not None})
    for k in range(K):
        v = m.NewIntVar(0, total, f"p{k}")
        m.Add(v == sum(atomos[i]["pop"] * x[i, k] for i in range(n) if (i, k) in x))
        m.Add(v <= math.floor(techo))
        # Exención de suelo, como ddd_motor2.reglas.evaluar.exento_de_suelo.
        ex = []
        if reglas.exentos_municipio:
            b = tiene(lambda a: bool(a["muns"] & reglas.exentos_municipio), k)
            if b is not None:
                ex.append(b)
        if reglas.exentas_particion and partes:
            has = {p: tiene(lambda a, p=p: p in a["parts"], k) for p in partes}
            exentas = [p for p in partes if p in reglas.exentas_particion and has[p] is not None]
            no_exentas = [has[p] for p in partes if p not in reglas.exentas_particion and has[p] is not None]
            if exentas:
                e = m.NewBoolVar(f"expart{k}")
                if crit.exencion_particion == "todas":
                    if no_exentas:
                        m.AddBoolAnd([b.Not() for b in no_exentas]).OnlyEnforceIf(e)
                        m.AddBoolOr(no_exentas).OnlyEnforceIf(e.Not())
                    else:
                        m.Add(e == 1)
                elif crit.exencion_particion == "alguna":
                    m.AddMaxEquality(e, [has[p] for p in exentas])
                else:  # "primera": la menor partición del distrito está exenta (VAL 1.3.5)
                    primeras = []
                    for p in exentas:
                        f = m.NewBoolVar("")
                        menores = [has[q] for q in partes if q < p and has[q] is not None]
                        m.AddBoolAnd([has[p]] + [b.Not() for b in menores]).OnlyEnforceIf(f)
                        m.AddBoolOr([has[p].Not()] + menores).OnlyEnforceIf(f.Not())
                        primeras.append(f)
                    m.AddMaxEquality(e, primeras)
                ex.append(e)
        exento = None
        if ex:
            exento = m.NewBoolVar(f"ex{k}")
            m.AddMaxEquality(exento, ex)
            m.Add(v >= math.ceil(suelo)).OnlyEnforceIf(exento.Not())
        else:
            m.Add(v >= math.ceil(suelo))
        if crit.tolerancia == "dura":
            m.Add(v <= math.floor(obj + tol))
            if exento is None:
                m.Add(v >= math.ceil(obj - tol))
            else:
                m.Add(v >= math.ceil(obj - tol)).OnlyEnforceIf(exento.Not())
        pk.append(v)
    # Contigüidad: raíz = átomo mínimo del distrito (rompe la simetría) y árbol padre/nivel, O(E + n).
    r = {(i, k): m.NewBoolVar(f"r{i}_{k}") for (i, k) in permitido}
    pos = []
    for k in range(K):
        m.AddExactlyOne([r[i, k] for i in range(n) if (i, k) in r])
        pv = m.NewIntVar(0, max(0, n - 1), f"pos{k}")
        m.Add(pv == sum(i * r[i, k] for i in range(n) if (i, k) in r))
        for i in range(n):
            if (i, k) in x:
                m.AddImplication(r[i, k], x[i, k])
                m.Add(pv <= i).OnlyEnforceIf(x[i, k])
        pos.append(pv)
    for k in range(K - 1):
        if prov_d[k] == prov_d[k + 1]:
            m.Add(pos[k] < pos[k + 1])
    if reglas.contiguidad:
        d = [m.NewIntVar(0, K - 1, f"d{i}") for i in range(n)]
        nivel = [m.NewIntVar(0, max(0, n - 1), f"h{i}") for i in range(n)]
        for i in range(n):
            m.Add(d[i] == sum(k * x[i, k] for k in range(K) if (i, k) in x))
            es_raiz = [r[i, k] for k in range(K) if (i, k) in r]
            padres = []
            for j in vecinos[i]:
                pa = m.NewBoolVar(f"pa{i}_{j}")
                m.Add(d[i] == d[j]).OnlyEnforceIf(pa)
                m.Add(nivel[i] >= nivel[j] + 1).OnlyEnforceIf(pa)
                padres.append(pa)
            m.AddExactlyOne(padres + es_raiz)
            raiz_i = m.NewBoolVar(f"raiz{i}")
            m.Add(sum(es_raiz) == raiz_i)
            m.Add(nivel[i] == 0).OnlyEnforceIf(raiz_i)
    # Disciplina municipal R012 (campo y max_mixed del núcleo).
    if reglas.disciplina_municipal:
        por_clave: dict = defaultdict(list)
        pob_clave: dict = defaultdict(int)
        for i, a in enumerate(atomos):
            for c, p in a["claves"].items():
                por_clave[c].append(i)
                pob_clave[c] += p
        y = {}
        for c, idx in por_clave.items():
            for k in range(K):
                xs = [x[i, k] for i in idx if (i, k) in x]
                if xs:
                    y[c, k] = m.NewBoolVar("")
                    m.AddMaxEquality(y[c, k], xs)
        mixto = []
        for k in range(K):
            ys = [y[c, k] for c in por_clave if (c, k) in y]
            mk = m.NewBoolVar(f"mix{k}")
            m.Add(sum(ys) >= 2).OnlyEnforceIf(mk)
            m.Add(sum(ys) <= 1).OnlyEnforceIf(mk.Not())
            mixto.append(mk)
        for c, idx in por_clave.items():
            p = Fraction(pob_clave[c])
            lo = max(1, math.ceil(p / techo)) if p > 0 else 1
            hi = max(1, math.ceil(p / obj)) if p > 0 else 1
            ys = [(k, y[c, k]) for k in range(K) if (c, k) in y]
            m.Add(sum(v for _, v in ys) >= lo)
            m.Add(sum(v for _, v in ys) <= hi)
            if hi > 1:
                parte = m.NewBoolVar("")
                m.Add(sum(v for _, v in ys) >= 2).OnlyEnforceIf(parte)
                m.Add(sum(v for _, v in ys) <= 1).OnlyEnforceIf(parte.Not())
                zs = []
                for k, v in ys:
                    z = m.NewBoolVar("")
                    m.AddMultiplicationEquality(z, [v, mixto[k]])
                    zs.append(z)
                m.Add(sum(zs) <= reglas.max_mixtos).OnlyEnforceIf(parte)
    if objetivo == "minimax" or cota_desviacion is not None:
        dev = m.NewIntVar(0, total, "dev")
        for v in pk:
            m.Add(v - dev <= math.floor(obj))
            m.Add(v + dev >= math.ceil(obj))
        if cota_desviacion is not None:
            m.Add(dev <= math.ceil(cota_desviacion) - 1)
        if objetivo == "minimax":
            m.Minimize(dev)
    if objetivo == "techo":
        mx = m.NewIntVar(0, total, "pmax")
        m.AddMaxEquality(mx, pk)
        m.Minimize(mx)
    if pista:
        # Pista (no restringe): la composición dada, renumerada por átomo mínimo dentro de cada provincia.
        d_atomos: dict = defaultdict(list)
        for i, a in enumerate(atomos):
            if a["secs"][0] in pista:
                d_atomos[str(pista[a["secs"][0]])].append(i)
        libres: dict = defaultdict(list)
        for k in range(K):
            libres[prov_d[k]].append(k)
        for grupo in sorted(d_atomos.values(), key=min):
            clave = next(iter(atomos[grupo[0]]["provs"])) if prov_d[0] is not None else None
            if not libres[clave]:
                break
            k = libres[clave].pop(0)
            for i in grupo:
                for kk in range(K):
                    if (i, kk) in x:
                        m.AddHint(x[i, kk], kk == k)
                if (i, k) in r:
                    m.AddHint(r[i, k], i == min(grupo))
    t_modelo = time.time() - t0
    limite = time.time() + float(tiempo)
    planes, t_solver, iteraciones = [], 0.0, 0
    while True:
        iteraciones += 1
        sol = cp_model.CpSolver()
        sol.parameters.max_time_in_seconds = max(1.0, limite - time.time())
        sol.parameters.num_workers = int(hilos)
        est = sol.Solve(m)
        t_solver += sol.WallTime()
        nombre = sol.StatusName(est)
        if objetivo != "enumerar" or nombre not in ("OPTIMAL", "FEASIBLE"):
            break
        # Enumeración: la ruptura de simetría hace única la etiqueta de cada plan; se excluye y se repite.
        planes.append([next(k for k in range(K) if (i, k) in x and sol.Value(x[i, k])) for i in range(n)])
        m.AddBoolOr([x[i, k].Not() for (i, k) in x if sol.Value(x[i, k])])
        if time.time() >= limite:
            nombre = "UNKNOWN"
            break

    def a_secciones(etiquetas):
        return {s: str(k) for i, k in enumerate(etiquetas) for s in atomos[i]["secs"]}

    res = {**base, "variables": len(m.Proto().variables), "restricciones": len(m.Proto().constraints),
           "t_modelo_s": round(t_modelo, 2), "t_solver_s": round(t_solver, 2), "iteraciones": iteraciones,
           "estado_solver": nombre,
           "memoria_max_mb": round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024, 1)}
    if objetivo == "enumerar":
        res["planes_validos"] = len(planes)
        res["enumeracion_completa"] = nombre == "INFEASIBLE"
        res["estado"] = "ENUMERADO" if nombre == "INFEASIBLE" else "ENUMERACION_PARCIAL"
        res["_planes"] = [a_secciones(p) for p in planes]
        return res
    res["estado"] = {"OPTIMAL": "FACTIBLE" if objetivo == "factibilidad" else "OPTIMO", "FEASIBLE": "FACTIBLE",
                     "INFEASIBLE": "INFACTIBLE"}.get(nombre, "DESCONOCIDO")
    if nombre == "INFEASIBLE":
        res["prueba"] = "CP-SAT: modelo infactible (búsqueda completa) con las reglas del núcleo"
    if nombre in ("OPTIMAL", "FEASIBLE"):
        res["asignacion"] = a_secciones([next(k for k in range(K) if (i, k) in x and sol.Value(x[i, k]))
                                         for i in range(n)])
        if objetivo in ("minimax", "techo"):
            res["valor_objetivo"] = round(sol.ObjectiveValue(), 1)
            res["cota_inferior_objetivo"] = round(sol.BestObjectiveBound(), 1)
            if objetivo == "techo":
                res["techo_minimo_ratio"] = round(sol.ObjectiveValue() / float(obj), 5)
    return res


# --------------------------------------------------------------------------- CLI
def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Certificador exacto CP-SAT sobre el núcleo de reglas (T-136)")
    ap.add_argument("--params", required=True)
    ap.add_argument("--grafo", required=True)
    ap.add_argument("--secciones", required=True, help="GeoJSON de secciones del M04 (o M05/M06), con ddd_unit_id")
    ap.add_argument("--sin-unidades", action="store_true", help="ignora ddd_unit_id (solo reglas de la validación)")
    ap.add_argument("--perfil", choices=("nucleo", "produccion"), default="nucleo",
                    help="nucleo: Criterio aprobado (D-44); produccion: compatibilidad con validar_ejecucion 1.3.5")
    ap.add_argument("--referencia", action="append", default=[], help="composición a juzgar (nombre=ruta o ruta)")
    ap.add_argument("--pista", help="composición usada como solución inicial (no restringe)")
    ap.add_argument("--objetivo", choices=("factibilidad", "minimax", "techo", "enumerar"), default="factibilidad")
    ap.add_argument("--cota-desviacion", type=float, help="exige desviación máxima < cota")
    ap.add_argument("--techo-ratio", help="sustituye population_cap_ratio (pregunta «¿y si?»)")
    ap.add_argument("--suelo-ratio", help="sustituye population_floor_ratio")
    ap.add_argument("--tiempo", type=float, default=600)
    ap.add_argument("--hilos", type=int, default=4)
    ap.add_argument("--salida")
    ap.add_argument("--asignacion-csv")
    a = ap.parse_args(argv)
    cfg = load_params_yaml(a.params)
    if a.techo_ratio or a.suelo_ratio:
        cfg = json.loads(json.dumps(cfg, default=str))
        if a.techo_ratio:
            cfg["validation"]["population_cap_ratio"] = a.techo_ratio
        if a.suelo_ratio:
            cfg["validation"]["population_floor_ratio"] = a.suelo_ratio
    criterio = Criterio.compatibilidad_produccion() if a.perfil == "produccion" else Criterio()
    reglas = Reglas.desde_contrato(cfg, criterio)
    unidades, unidad_m04 = leer_secciones(a.secciones, cfg, criterio, con_unidades=not a.sin_unidades)
    problema = Problema(tuple(unidades), tuple(leer_grafo(a.grafo, {u.id for u in unidades})))
    reglas.comprobar_datos(problema)
    pista = leer_composicion(a.pista) if a.pista else None
    res = {"version": VERSION, "params": a.params, "perfil": a.perfil, "unidades_m04": len(set(unidad_m04.values()))}
    res.update(resolver(problema, reglas, unidad_m04, tiempo=a.tiempo, hilos=a.hilos, objetivo=a.objetivo,
                        pista=pista, cota_desviacion=a.cota_desviacion))
    asig = res.pop("asignacion", None)
    planes = res.pop("_planes", None)
    if asig:
        res["comprobacion"] = juzgar(problema, reglas, asig, unidad_m04)
    if planes is not None:
        res["planes_comprobados_pass"] = sum(juzgar(problema, reglas, p, unidad_m04)["estado"] == "PASS"
                                             for p in planes)
    filas = [(0, asig)] if asig else list(enumerate(planes or []))
    if a.asignacion_csv and filas:
        with open(a.asignacion_csv, "w", encoding="utf-8", newline="") as fh:
            w = csv.writer(fh)
            w.writerow(["plan", "seccion", "distrito"])
            for j, pl in filas:
                w.writerows([j, s, d] for s, d in sorted(pl.items()))
    res["referencias"] = {}
    for ref in a.referencia:
        nombre, _, ruta = ref.rpartition("=")
        comp = leer_composicion(ruta)
        ev = juzgar(problema, reglas, comp, unidad_m04)
        if asig:
            pa = {frozenset(s for s, d in asig.items() if d == k) for k in set(asig.values())}
            pb = {frozenset(s for s, d in comp.items() if d == k) for k in set(comp.values())}
            ev["distritos_iguales_certificador"] = len(pa & pb)
        res["referencias"][nombre or Path(ruta).stem] = ev
    txt = json.dumps(res, ensure_ascii=False, indent=2)
    if a.salida:
        Path(a.salida).write_text(txt + "\n", encoding="utf-8")
    print(txt)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
