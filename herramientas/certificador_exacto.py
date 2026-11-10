#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Certificador exacto (T-136): programación entera con contigüidad para una circunscripción.

PROYECTO: Diputado de Distrito
VERSIÓN: 1.0.0
NOMBRE DE VERSIÓN: Prototipo de certificador exacto (CP-SAT)
FECHA: 2026-11-09
ESTADO: candidato (diagnóstico; no genera productos ni toca el motor)
CAMBIOS: fichero nuevo.
MOTIVO: decisión del propietario sobre el motor (opción B, punto B): saber, para una circunscripción, si existe una
  partición que cumple las reglas de la validación de producción y cuál es la mejor, o probar que no existe, y así
  medir cuánto deja el motor canónico.
ANTERIOR: ninguna (fichero nuevo)
QUÉ HACE: lee el contrato, las secciones (M01 o una composición con población) y el grafo M03, y plantea en OR-Tools
  CP-SAT las reglas de herramientas/validar_ejecucion.py (1.3.5), con los mismos límites (ddd_core.config.hard_limits)
  y exenciones (ddd_core.population_floor_exemptions):
    K distritos no vacíos; cada sección en un distrito; población en [suelo, techo] (suelo 0 si el distrito toca un
    municipio exento); contigüidad en el grafo M03 (flujo desde una raíz por distrito); una provincia por distrito con
    el reparto province_districts; disciplina municipal R012 (entre ceil(P/techo) y ceil(P/objetivo) distritos y, si
    se parte, como mucho un distrito mixto entre los suyos).
  Los municipios que no se pueden partir (ceil(P/objetivo) = 1) se contraen a un nodo por componente conexa
  (igualdad de asignación entre componentes), lo que no cambia el conjunto de soluciones.
  Objetivo: minimizar la mayor desviación absoluta respecto al objetivo (|P_k - P/K|), la mayor población de distrito
  (techo mínimo alcanzable) o solo factibilidad.
  Resultado: OPTIMO, FACTIBLE (con cota), INFACTIBLE (prueba del solver) o DESCONOCIDO (sin respuesta en el tiempo);
  la solución se comprueba aparte con las mismas reglas (evaluar_particion) y se compara con la composición de
  referencia (motor 7.4.4 de la batería T-132 o datos/composicion/<t>.csv).
USO: python herramientas/certificador_exacto.py --params territorios/<t>/config/<t>_2025.yaml \
       --grafo <m03_grafo.json> [--secciones <m01.geojson.zip> | --composicion datos/composicion/<t>.csv] \
       [--referencia <composicion.csv> ...] [--tiempo 600] [--hilos 8] [--techo-ratio 1.15] [--salida <informe.json>]
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
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ddd_core.config import hard_limits, load_params_yaml, module_cfg  # noqa: E402
from ddd_core.population_floor_exemptions import exempt_municipalities  # noqa: E402

VERSION = "1.0.0"


# --------------------------------------------------------------------------- instancia
def _componentes(nodos, adj) -> list[list[str]]:
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


def reglas_contrato(cfg: dict, total_pop: float, techo_ratio: float | None = None, suelo_ratio: float | None = None) -> dict:
    """Límites y reglas de la validación de producción, leídos del contrato."""
    val = cfg.get("validation", {}) or {}
    s6 = module_cfg(cfg, "modulo_06_consolidar_distritos", "step6_export_final")
    k = int(val.get("expected_districts", s6.get("expected_districts", 67)))
    if techo_ratio is not None or suelo_ratio is not None:
        cfg = json.loads(json.dumps(cfg))
        if techo_ratio is not None:
            cfg["validation"]["population_cap_ratio"] = techo_ratio
        if suelo_ratio is not None:
            cfg["validation"]["population_floor_ratio"] = suelo_ratio
    target, floor, cap, _ = hard_limits(cfg, k=k, total_pop=total_pop)
    return {
        "k": k, "objetivo": target, "suelo": floor, "techo": cap,
        "provincia": bool(val.get("require_single_province_per_district", False)),
        "provincias": {str(a): int(b) for a, b in (val.get("province_districts") or {}).items()},
        "municipal": bool(val.get("require_municipality_discipline", False)),
        "exentos": sorted(exempt_municipalities(cfg)),
        "particiones_exentas": sorted(str(x) for x in (val.get("population_floor_exempt_partitions") or [])),
    }


def leer_secciones(args, cfg) -> dict[str, dict]:
    """sección -> {pop, mun, prov}. Municipio por CUMUN o las 5 primeras cifras del CUSEC (como la validación)."""
    s6 = module_cfg(cfg, "modulo_06_consolidar_distritos", "step6_export_final")
    sid, pop = s6.get("id_field", "CUSEC"), s6["pop_field"]
    mun_f, prov_f = s6.get("municipality_field", "CUMUN"), s6.get("province_field", "CPRO")
    out: dict[str, dict] = {}
    if args.secciones:
        import geopandas as gpd
        p = Path(args.secciones)
        g = gpd.read_file(f"zip://{p}" if p.suffix == ".zip" else p, ignore_geometry=True)
        for r in g.to_dict("records"):
            s = str(r[sid])
            mun = str(r[mun_f]).zfill(5) if mun_f in r and r[mun_f] is not None else s[:5]
            prov = str(r[prov_f]).zfill(2) if prov_f in r and r[prov_f] is not None else s[:2]
            out[s] = {"pop": int(round(float(r[pop] or 0))), "mun": mun, "prov": prov}
    else:
        with open(args.composicion, encoding="utf-8") as fh:
            for r in csv.DictReader(fh):
                s = str(r["seccion"])
                out[s] = {"pop": int(r["poblacion"]), "mun": s[:5], "prov": s[:2]}
    return out


def leer_grafo(path: str) -> dict[str, set[str]]:
    g = json.loads(Path(path).read_text(encoding="utf-8"))
    adj: dict[str, set[str]] = defaultdict(set)
    for e in g["edges"]:
        u, v = str(e["u"]), str(e["v"])
        if u != v:
            adj[u].add(v)
            adj[v].add(u)
    return adj


# --------------------------------------------------------------------------- evaluación (mismas reglas)
def evaluar_particion(asig: dict[str, str], sec: dict[str, dict], adj, reglas: dict) -> dict:
    """Reglas de validar_ejecucion.py sobre una asignación sección -> distrito."""
    fallos = []
    por_d: dict[str, list[str]] = defaultdict(list)
    for s, d in asig.items():
        por_d[str(d)].append(s)
    if set(asig) != set(sec):
        fallos.append(f"secciones sin asignar={len(set(sec) - set(asig))}, ajenas={len(set(asig) - set(sec))}")
    if len(por_d) != reglas["k"]:
        fallos.append(f"distritos={len(por_d)}, esperados={reglas['k']}")
    pops = {d: sum(sec[s]["pop"] for s in ss if s in sec) for d, ss in por_d.items()}
    exentos = set(reglas["exentos"])
    bajo, sobre, descon, interprov = [], [], [], []
    for d, ss in por_d.items():
        muns = {sec[s]["mun"] for s in ss if s in sec}
        provs = sorted({sec[s]["prov"] for s in ss if s in sec})
        exento = bool(muns & exentos) or (bool(provs) and provs[0] in set(reglas["particiones_exentas"]))
        if pops[d] < (0.0 if exento else reglas["suelo"]):
            bajo.append(d)
        if pops[d] > reglas["techo"]:
            sobre.append(d)
        sub = {s: [v for v in adj.get(s, ()) if v in set(ss)] for s in ss}
        if len(_componentes(ss, sub)) != 1:
            descon.append(d)
        if reglas["provincia"] and len(provs) != 1:
            interprov.append(d)
    for lista, txt in ((bajo, "bajo suelo"), (sobre, "sobre techo"), (descon, "desconectados"), (interprov, "interprovinciales")):
        if lista:
            fallos.append(f"distritos {txt}={len(lista)}")
    if reglas["provincia"] and reglas["provincias"]:
        cuenta: dict[str, int] = defaultdict(int)
        for d, ss in por_d.items():
            provs = {sec[s]["prov"] for s in ss if s in sec}
            if len(provs) == 1:
                cuenta[provs.pop()] += 1
        for p, n in reglas["provincias"].items():
            if cuenta.get(p, 0) != n:
                fallos.append(f"provincia {p}: distritos={cuenta.get(p, 0)}, esperados={n}")
    mun_viol = []
    if reglas["municipal"]:
        d_muns = {d: {sec[s]["mun"] for s in ss if s in sec} for d, ss in por_d.items()}
        m_pop: dict[str, int] = defaultdict(int)
        m_d: dict[str, set] = defaultdict(set)
        for s, d in asig.items():
            if s in sec:
                m_pop[sec[s]["mun"]] += sec[s]["pop"]
                m_d[sec[s]["mun"]].add(str(d))
        for m, ds in m_d.items():
            p = m_pop[m]
            lo = max(1, math.ceil(p / reglas["techo"])) if p > 0 else 1
            hi = max(1, math.ceil(p / reglas["objetivo"])) if p > 0 else 1
            mixtos = [d for d in ds if len(d_muns[d]) > 1]
            if len(ds) < lo or len(ds) > hi or (len(ds) > 1 and len(mixtos) > 1):
                mun_viol.append(m)
        if mun_viol:
            fallos.append(f"municipios con fragmentación inválida={len(mun_viol)}")
    dev = max((abs(p - reglas["objetivo"]) for p in pops.values()), default=0.0)
    return {"estado": "PASS" if not fallos else "FAIL", "fallos": fallos, "max_desviacion": round(dev, 1),
            "max_desviacion_ratio": round(dev / reglas["objetivo"], 5),
            "min_pop": min(pops.values(), default=0), "max_pop": max(pops.values(), default=0),
            "municipios_invalidos": sorted(mun_viol)[:20]}


# --------------------------------------------------------------------------- modelo
def construir_atomos(sec, adj, reglas):
    """Contrae municipios indivisibles a un átomo por componente conexa; los divisibles quedan por sección."""
    m_secs: dict[str, list[str]] = defaultdict(list)
    for s, r in sec.items():
        m_secs[r["mun"]].append(s)
    atomo_de: dict[str, int] = {}
    atomos: list[dict] = []
    for m in sorted(m_secs):
        ss = sorted(m_secs[m])
        p = sum(sec[s]["pop"] for s in ss)
        hi = max(1, math.ceil(p / reglas["objetivo"])) if p > 0 else 1
        divisible = reglas["municipal"] is False or hi > 1
        if divisible:
            grupos = [[s] for s in ss]
        else:
            sub = {s: [v for v in adj.get(s, ()) if sec.get(v, {}).get("mun") == m] for s in ss}
            grupos = _componentes(ss, sub)
        for gr in grupos:
            atomo_de.update({s: len(atomos) for s in gr})
            atomos.append({"secs": gr, "pop": sum(sec[s]["pop"] for s in gr), "mun": m, "prov": sec[gr[0]]["prov"],
                           "divisible": divisible, "hermanos": len(grupos)})
    aristas = set()
    for u, vs in adj.items():
        if u not in atomo_de:
            continue
        for v in vs:
            if v in atomo_de and atomo_de[u] != atomo_de[v]:
                a, b = sorted((atomo_de[u], atomo_de[v]))
                aristas.add((a, b))
    return atomos, sorted(aristas), atomo_de


def resolver(sec, adj, reglas, *, tiempo: float, hilos: int, objetivo: str = "minimax", pista: dict | None = None,
            cota_desviacion: float | None = None, contiguidad: str = "arbol") -> dict:
    from ortools.sat.python import cp_model

    t0 = time.time()
    atomos, aristas, atomo_de = construir_atomos(sec, adj, reglas)
    n, K = len(atomos), reglas["k"]
    # Distritos por provincia (bloques contiguos de índices).
    if reglas["provincia"] and reglas["provincias"]:
        prov_d = [p for p, c in sorted(reglas["provincias"].items()) for _ in range(c)]
    else:
        prov_d = [None] * K
    if len(prov_d) != K:
        return {"estado": "INFACTIBLE", "prueba": "reparto provincial no suma K", "atomos": n}
    vecinos: dict[int, list[int]] = defaultdict(list)
    for a, b in aristas:
        vecinos[a].append(b)
        vecinos[b].append(a)
    m = cp_model.CpModel()
    permitido = {(i, k) for i in range(n) for k in range(K) if prov_d[k] is None or prov_d[k] == atomos[i]["prov"]}
    x = {(i, k): m.NewBoolVar(f"x{i}_{k}") for (i, k) in permitido}
    for i in range(n):
        m.AddExactlyOne([x[i, k] for k in range(K) if (i, k) in x])
    # Componentes de un mismo municipio indivisible: mismo distrito.
    por_mun: dict[str, list[int]] = defaultdict(list)
    for i, a in enumerate(atomos):
        por_mun[a["mun"]].append(i)
    for mun, idx in por_mun.items():
        if not atomos[idx[0]]["divisible"] and len(idx) > 1:
            for j in idx[1:]:
                for k in range(K):
                    if (idx[0], k) in x:
                        m.Add(x[j, k] == x[idx[0], k])
    total = sum(a["pop"] for a in atomos)
    pk = []
    exentos = set(reglas["exentos"])
    for k in range(K):
        v = m.NewIntVar(0, total, f"p{k}")
        m.Add(v == sum(atomos[i]["pop"] * x[i, k] for i in range(n) if (i, k) in x))
        m.Add(v <= math.floor(reglas["techo"]))
        ex_atomos = [x[i, k] for i in range(n) if (i, k) in x and atomos[i]["mun"] in exentos]
        if prov_d[k] in set(reglas["particiones_exentas"]):
            pass  # suelo 0 en la partición exenta
        elif ex_atomos:
            ex = m.NewBoolVar(f"ex{k}")
            m.AddMaxEquality(ex, ex_atomos)
            m.Add(v >= math.ceil(reglas["suelo"])).OnlyEnforceIf(ex.Not())
        else:
            m.Add(v >= math.ceil(reglas["suelo"]))
        pk.append(v)
    # Contigüidad: una raíz por distrito; flujo de la raíz a cada átomo del distrito por aristas internas.
    r = {(i, k): m.NewBoolVar(f"r{i}_{k}") for (i, k) in permitido}
    pos = []
    for k in range(K):
        m.AddExactlyOne([r[i, k] for i in range(n) if (i, k) in r])
        for i in range(n):
            if (i, k) in r:
                m.AddImplication(r[i, k], x[i, k])
        # Ruptura de simetría: la raíz es el átomo de menor índice del distrito y las raíces crecen con k
        # dentro de cada provincia.
        pv = m.NewIntVar(0, n - 1, f"pos{k}")
        m.Add(pv == sum(i * r[i, k] for i in range(n) if (i, k) in r))
        for i in range(n):
            if (i, k) in x:
                m.Add(pv <= i).OnlyEnforceIf(x[i, k])
        pos.append(pv)
    for k in range(K - 1):
        if prov_d[k] == prov_d[k + 1]:
            m.Add(pos[k] < pos[k + 1])
    M = n
    for k in range(K if contiguidad == "flujo" else 0):
        f = {}
        for a, b in aristas:
            if (a, k) in x and (b, k) in x:
                for u, v in ((a, b), (b, a)):
                    fv = m.NewIntVar(0, M, f"f{k}_{u}_{v}")
                    m.Add(fv == 0).OnlyEnforceIf(x[u, k].Not())
                    m.Add(fv == 0).OnlyEnforceIf(x[v, k].Not())
                    f[u, v] = fv
        for i in range(n):
            if (i, k) not in x:
                continue
            ent = [f[j, i] for j in vecinos[i] if (j, i) in f]
            sal = [f[i, j] for j in vecinos[i] if (i, j) in f]
            # Cada átomo no raíz del distrito consume una unidad; la raíz no recibe flujo.
            m.Add(sum(ent) - sum(sal) >= 1).OnlyEnforceIf([x[i, k], r[i, k].Not()])
            if ent:
                m.Add(sum(ent) == 0).OnlyEnforceIf(r[i, k])
    if contiguidad == "arbol":
        # Árbol de expansión por distrito: cada átomo que no es raíz elige un padre vecino del mismo distrito con nivel
        # menor; la raíz (átomo mínimo del distrito) tiene nivel 0. Tamaño O(E + n), independiente de K.
        d = [m.NewIntVar(0, K - 1, f"d{i}") for i in range(n)]
        nivel = [m.NewIntVar(0, n - 1, f"h{i}") for i in range(n)]
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
            raiz = m.NewBoolVar(f"raiz{i}")
            m.Add(sum(es_raiz) == raiz)
            m.Add(nivel[i] == 0).OnlyEnforceIf(raiz)
    # Disciplina municipal (municipios divisibles; los indivisibles ya son un átomo).
    if reglas["municipal"]:
        y = {}
        for mun, idx in por_mun.items():
            for k in range(K):
                xs = [x[i, k] for i in idx if (i, k) in x]
                if xs:
                    y[mun, k] = m.NewBoolVar(f"y{mun}_{k}")
                    m.AddMaxEquality(y[mun, k], xs)
        mixto = []
        for k in range(K):
            ys = [y[mun, k] for mun in por_mun if (mun, k) in y]
            mk = m.NewBoolVar(f"mix{k}")
            m.Add(sum(ys) >= 2).OnlyEnforceIf(mk)
            m.Add(sum(ys) <= 1).OnlyEnforceIf(mk.Not())
            mixto.append(mk)
        for mun, idx in por_mun.items():
            if not atomos[idx[0]]["divisible"]:
                continue
            p = sum(atomos[i]["pop"] for i in idx)
            lo = max(1, math.ceil(p / reglas["techo"])) if p > 0 else 1
            hi = max(1, math.ceil(p / reglas["objetivo"])) if p > 0 else 1
            ys = [(k, y[mun, k]) for k in range(K) if (mun, k) in y]
            m.Add(sum(v for _, v in ys) >= lo)
            m.Add(sum(v for _, v in ys) <= hi)
            parte = m.NewBoolVar(f"parte{mun}")
            m.Add(sum(v for _, v in ys) >= 2).OnlyEnforceIf(parte)
            m.Add(sum(v for _, v in ys) <= 1).OnlyEnforceIf(parte.Not())
            ym = []
            for k, v in ys:
                z = m.NewBoolVar(f"z{mun}_{k}")
                m.AddMultiplicationEquality(z, [v, mixto[k]])
                ym.append(z)
            m.Add(sum(ym) <= 1).OnlyEnforceIf(parte)
    objetivo_pob = total / K
    if objetivo == "minimax" or cota_desviacion is not None:
        dev = m.NewIntVar(0, total, "dev")
        for v in pk:
            m.Add(v - dev <= math.floor(objetivo_pob))
            m.Add(v + dev >= math.ceil(objetivo_pob))
        if cota_desviacion is not None:
            # Pregunta de decisión: ¿hay partición válida con desviación máxima estrictamente menor que la cota?
            m.Add(dev <= math.ceil(cota_desviacion) - 1)
        if objetivo == "minimax":
            m.Minimize(dev)
    if objetivo == "techo":
        # Menor techo alcanzable: minimiza la mayor población de distrito (con el suelo y las exenciones del contrato).
        mx = m.NewIntVar(0, total, "pmax")
        m.AddMaxEquality(mx, pk)
        m.Minimize(mx)
    if pista:
        # Pista (no restricción): la referencia, con distritos renumerados por su átomo mínimo dentro de cada provincia.
        d_atomos: dict[str, list[int]] = defaultdict(list)
        for i, a in enumerate(atomos):
            d = pista.get(a["secs"][0])
            if d is not None:
                d_atomos[str(d)].append(i)
        orden = sorted(d_atomos.values(), key=min)
        libres = {p: [k for k in range(K) if prov_d[k] == p] for p in set(prov_d)}
        for grupo in orden:
            ks = libres.get(atomos[grupo[0]]["prov"]) or libres.get(None) or []
            if not ks:
                break
            k = ks.pop(0)
            for i in grupo:
                for kk in range(K):
                    if (i, kk) in x:
                        m.AddHint(x[i, kk], kk == k)
                if (i, k) in r:
                    m.AddHint(r[i, k], i == min(grupo))
    t_modelo = time.time() - t0
    # Con «cortes», la contigüidad se impone por separadores con raíz (Validi y Buchanan): se resuelve, y para cada
    # componente C de un distrito desconectado se añade, para todo a en C y toda etiqueta k,
    # x[a,k] <= sum(x[c,k], c en N(C)) + sum(r[c,k], c en C). Es una relajación válida: INFACTIBLE en una iteración prueba la infactibilidad, y
    # una solución conexa (óptima) de la relajación lo es del problema.
    limite = time.time() + float(tiempo)
    iteraciones, cortes, t_solver = 0, 0, 0.0
    sol = cp_model.CpSolver()
    while True:
        iteraciones += 1
        sol = cp_model.CpSolver()
        sol.parameters.max_time_in_seconds = max(1.0, limite - time.time())
        sol.parameters.num_workers = int(hilos)
        est = sol.Solve(m)
        t_solver += sol.WallTime()
        nombre = sol.StatusName(est)
        if nombre not in ("OPTIMAL", "FEASIBLE") or contiguidad in ("flujo", "arbol", "ninguna"):
            break
        asig_k = {i: next(k for k in range(K) if (i, k) in x and sol.Value(x[i, k])) for i in range(n)}
        nuevos = 0
        miembros: dict[int, set] = defaultdict(set)
        for i, k in asig_k.items():
            miembros[k].add(i)
        for k, ms in miembros.items():
            comps = _componentes(ms, {i: [j for j in vecinos[i] if j in ms] for i in ms})
            if len(comps) == 1:
                continue
            for comp in comps:
                cs = set(comp)
                frontera = sorted({j for i in comp for j in vecinos[i] if j not in cs})
                # Con raíz: si a está en el distrito y la raíz no está en C, algún nodo de N(C) está en el distrito.
                for a_i in comp:
                    for kk in range(K):
                        if (a_i, kk) in x:
                            m.Add(x[a_i, kk] - sum(x[c, kk] for c in frontera if (c, kk) in x)
                                  - sum(r[c, kk] for c in comp if (c, kk) in r) <= 0)
                            nuevos += 1
        if not nuevos:
            break
        cortes += nuevos
        m.ClearHints()
        for i, k in asig_k.items():
            for kk in range(K):
                if (i, kk) in x:
                    m.AddHint(x[i, kk], kk == k)
        if time.time() >= limite:
            nombre = "UNKNOWN"
            break
    res = {"atomos": n, "aristas_atomos": len(aristas), "secciones": len(sec), "k": K, "contiguidad": contiguidad,
           "iteraciones": iteraciones, "cortes": cortes,
           "variables": len(m.Proto().variables), "restricciones": len(m.Proto().constraints),
           "t_modelo_s": round(t_modelo, 2), "t_solver_s": round(t_solver, 2),
           "estado_solver": nombre, "memoria_max_mb": round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024, 1)}
    if nombre == "OPTIMAL":
        res["estado"] = "FACTIBLE" if objetivo == "factibilidad" else "OPTIMO"
    elif nombre == "FEASIBLE":
        res["estado"] = "FACTIBLE"
    elif nombre == "INFEASIBLE":
        res["estado"] = "INFACTIBLE"
        res["prueba"] = "CP-SAT: modelo infactible (búsqueda completa) con las reglas del contrato"
    else:
        res["estado"] = "DESCONOCIDO"
    if nombre in ("OPTIMAL", "FEASIBLE"):
        asig = {}
        for i, a in enumerate(atomos):
            k = next(k for k in range(K) if (i, k) in x and sol.Value(x[i, k]))
            for s in a["secs"]:
                asig[s] = str(k)
        res["asignacion"] = asig
        if objetivo != "factibilidad":
            res["valor_objetivo"] = round(sol.ObjectiveValue(), 1)
            res["cota_inferior_objetivo"] = round(sol.BestObjectiveBound(), 1)
            if objetivo == "techo":
                res["techo_minimo_ratio"] = round(sol.ObjectiveValue() / objetivo_pob, 5)
    return res


# --------------------------------------------------------------------------- CLI
def leer_composicion(path: str) -> dict[str, str]:
    with open(path, encoding="utf-8") as fh:
        rd = csv.DictReader(fh)
        cols = rd.fieldnames or []
        sid = "seccion" if "seccion" in cols else ("CUSEC_KEY" if "CUSEC_KEY" in cols else cols[0])
        did = "distrito" if "distrito" in cols else "district_id"
        return {str(r[sid]): str(r[did]) for r in rd}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Certificador exacto CP-SAT (T-136)")
    ap.add_argument("--params", required=True)
    ap.add_argument("--grafo", required=True)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--secciones")
    g.add_argument("--composicion")
    ap.add_argument("--referencia", action="append", default=[], help="composición a comparar (nombre=ruta o ruta)")
    ap.add_argument("--tiempo", type=float, default=600)
    ap.add_argument("--hilos", type=int, default=4)
    ap.add_argument("--objetivo", choices=("minimax", "techo", "factibilidad"), default="minimax")
    ap.add_argument("--techo-ratio", type=float)
    ap.add_argument("--suelo-ratio", type=float)
    ap.add_argument("--pista", help="composición usada como solución inicial (no restringe)")
    ap.add_argument("--cota-desviacion", type=float,
                    help="exige desviación máxima < cota (p. ej. la del motor): INFACTIBLE prueba que no hay mejora")
    ap.add_argument("--contiguidad", choices=("arbol", "cortes", "flujo"), default="arbol")
    ap.add_argument("--salida")
    ap.add_argument("--asignacion-csv")
    a = ap.parse_args(argv)
    cfg = load_params_yaml(a.params)
    sec = leer_secciones(a, cfg)
    adj = leer_grafo(a.grafo)
    reglas = reglas_contrato(cfg, sum(r["pop"] for r in sec.values()), a.techo_ratio, a.suelo_ratio)
    res = {"version": VERSION, "params": a.params, "reglas": reglas}
    pista = leer_composicion(a.pista) if a.pista else None
    res.update(resolver(sec, adj, reglas, tiempo=a.tiempo, hilos=a.hilos, objetivo=a.objetivo, pista=pista,
                        cota_desviacion=a.cota_desviacion, contiguidad=a.contiguidad))
    asig = res.pop("asignacion", None)
    if asig:
        res["comprobacion"] = evaluar_particion(asig, sec, adj, reglas)
        if a.asignacion_csv:
            with open(a.asignacion_csv, "w", encoding="utf-8", newline="") as fh:
                w = csv.writer(fh)
                w.writerow(["seccion", "distrito"])
                w.writerows(sorted(asig.items()))
    res["referencias"] = {}
    for ref in a.referencia:
        nombre, _, ruta = ref.rpartition("=")
        comp = leer_composicion(ruta)
        ev = evaluar_particion(comp, sec, adj, reglas)
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
