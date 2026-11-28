#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PROYECTO: Diputado de Distrito
COMPONENTE: estudio T-509 · laboratorio L1 — mejora local exacta del ganador de Deslinde
VERSIÓN: 1.0.0
FECHA: 2026-11-28
ESTADO: estudio (no es motor: importa el paquete Deslinde y copia el modelo de exacto.py; no lanza nada)
ANTERIOR: ninguna (fichero nuevo)
QUÉ HACE:
  Por territorio: (1) corre la competición local (ddd_motor2.competir, D8, 10 cadenas) y anota el ganador;
  (2) parte de ese mapa y reoptimiza de forma exacta con CP-SAT grupos de 2 y de 3 distritos vecinos, con todos los
  demás distritos fijos, hasta que ningún grupo mejora o se agota el tope; (3) juzga el resultado con la clave D8
  oficial (Natural.clave) y con el evaluador del motor (reglas.evaluar).
  El submodelo es el de deslinde/exacto.py (asignación, población, R-NUCLEO, contigüidad por árbol, disciplina
  municipal, clave D8 por etapas) restringido a los átomos de los distritos del grupo. Lo fijo entra como constante:
  distritos fijos que ya contienen una clave municipal (y si son mixtos), suelo del exceso sobre el 8 % y del desvío
  máximo que marcan los distritos fijos. Las demarcaciones y la frontera que tocan un distrito fijo no cambian.
  Un cambio solo se acepta si la clave D8 oficial baja de verdad y el plan entero cumple el núcleo.
  Orden fijo: primero todos los pares; sin pares que mejoren, los tríos; tras una mejora se vuelve a los pares.
USO (una orden; las entradas de la batería deben estar en <out>/entradas/<t>):
  PYTHONHASHSEED=0 python docs/ESTUDIOS/T509_LAB_MEJORA_LOCAL/mejora_local.py --out B nac50 nac03
SALIDA: resultados/<t>_r<n>.json (una por repetición), resultados/<t>_plan.csv (si mejora) y resultados/RESUMEN.{json,csv}.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import sys
import time
from collections import defaultdict
from dataclasses import asdict
from fractions import Fraction
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(RAIZ))

import ddd_motor2  # noqa: E402,F401  (deja importable el paquete deslinde)
import deslinde.competicion as C  # noqa: E402
import deslinde.exacto as EX  # noqa: E402
from deslinde.adaptadores import problema_y_plan  # noqa: E402
from deslinde.naturalidad_clave import natural_desde_m06  # noqa: E402
from deslinde.ponderado import huella_plan  # noqa: E402
from deslinde.reglas import Criterio, Reglas  # noqa: E402
from deslinde.reglas.evaluar import evaluar  # noqa: E402

AQUI = Path(__file__).resolve().parent
TOPE = EX.TOPE_D8
ETAPAS = EX.ETAPAS


def log(*a):
    print(time.strftime("%H:%M:%S"), *a, flush=True)


# ---------------------------------------------------------------- competición y ganador
def competir(t: str, out: Path, cadenas: int) -> dict:
    """Corre la competición local y deja en <out>/lab/<t>/GANADOR.json con qué se juzgó al ganador."""
    from ddd_motor2.competir import competir_territorio
    reg, orig = {}, C.juzgar

    def espia(cand, salida, entrada, criterio, referencia, funcion="A"):
        reg[cand.id] = (salida, criterio, referencia)
        return orig(cand, salida, entrada, criterio, referencia, funcion)

    C.juzgar = espia
    t0 = time.monotonic()
    try:
        fila = competir_territorio(t, out, cadenas, funcion="D8")
    finally:
        C.juzgar = orig
    if fila.get("estado") != "VALIDO":
        raise RuntimeError(f"{t}: competición sin ganador válido: {fila}")
    sal, criterio, ref = reg[fila["ganador"]]
    g = {"territorio": t, "ganador": fila["ganador"], "composicion": str(sal.composicion),
         "atributos": str(sal.atributos_secciones) if sal.atributos_secciones else None,
         "referencia": str(ref) if ref else None, "criterio": asdict(criterio), "cadenas": cadenas,
         "tiempo_competicion_s": round(time.monotonic() - t0, 1), "fila": fila}
    d = out / "lab" / t
    d.mkdir(parents=True, exist_ok=True)
    (d / "GANADOR.json").write_text(json.dumps(g, indent=1, ensure_ascii=False, default=str), encoding="utf-8")
    return g


def cargar(t: str, out: Path, g: dict):
    from ddd_motor2.generadores import entrada_bateria
    ent = entrada_bateria(t, out)
    criterio = Criterio(**g["criterio"])
    reglas = Reglas.desde_contrato(ent.cfg, criterio)
    problema, plan, _ = problema_y_plan(
        g["composicion"], ent.grafo_m03, ent.cfg, referencia_nucleos=Path(g["referencia"]) if g["referencia"] else None,
        atributos_secciones=Path(g["atributos"]) if g["atributos"] else ent.atributos_secciones,
        respaldo_municipio_cusec=criterio.respaldo_municipio_cusec)
    nat = natural_desde_m06(problema, reglas, g["composicion"], ent.grafo_m03, ent.cfg)
    return problema, reglas, nat, {str(u): str(d) for u, d in plan.items()}


# ---------------------------------------------------------------- instancia y submodelo
class Instancia:
    def __init__(self, problema, reglas, nat, plan):
        self.problema, self.reglas, self.nat = problema, reglas, nat
        self.at, aristas, self.atomo_de = EX.atomos(problema, reglas)
        self.obj, self.suelo, self.techo, self.tol = reglas.limites(problema.poblacion_total)
        self.num, self.den = self.obj.numerator, self.obj.denominator
        self.big = self.den * problema.poblacion_total + self.num
        self.total = problema.poblacion_total
        self.vecinos = defaultdict(list)
        for a, b in aristas:
            self.vecinos[a].append(b)
            self.vecinos[b].append(a)
        self.pob_clave, self.atomos_clave = defaultdict(int), defaultdict(list)
        for i, a in enumerate(self.at):
            for c, pc in a["claves"].items():
                self.pob_clave[c] += pc
                self.atomos_clave[c].append(i)
        self.dems = []
        for dem in (nat.pj, nat.ca):
            grupos = defaultdict(set)
            for u, gr in dem.items():
                if gr is not None:
                    grupos[gr].add(self.atomo_de[u])
            self.dems += [sorted(idx) for _, idx in sorted(grupos.items()) if len(idx) >= 2]
        self.w = defaultdict(int)
        for (ua, ub), metros in nat.largo.items():
            i, j = self.atomo_de[ua], self.atomo_de[ub]
            if i != j:
                self.w[tuple(sorted((i, j)))] += int(round(metros * 1000))
        self.plan = dict(plan)
        self.lab = []
        for a in self.at:
            ds = {plan[s] for s in a["secs"]}
            if len(ds) != 1:
                raise RuntimeError("el ganador parte un átomo: la mejora local no aplica")
            self.lab.append(ds.pop())

    def clave(self, plan=None) -> tuple:
        return tuple(self.nat.clave(plan or self.plan, "D8")[:5])

    def vecindad(self) -> dict[str, set[str]]:
        v = defaultdict(set)
        for i, js in self.vecinos.items():
            for j in js:
                if self.lab[i] != self.lab[j]:
                    v[self.lab[i]].add(self.lab[j])
        return v

    def grupos(self, tam: int) -> list[tuple[str, ...]]:
        v = self.vecindad()
        if tam == 2:
            return sorted({tuple(sorted((a, b))) for a, bs in v.items() for b in bs})
        return sorted({tuple(sorted((d, a, b))) for d, bs in v.items() for a in bs for b in bs if a < b})


def resolver_grupo(I: Instancia, G: tuple[str, ...], tdet: float, tope_reloj: float, hilos: int):
    """Óptimo D8 de los distritos de G con el resto fijo. Devuelve (etiquetas por átomo libre | None, etapas, cerrado)."""
    from ortools.sat.python import cp_model
    t0 = time.monotonic()
    at, reglas, Gs, K = I.at, I.reglas, set(G), len(G)
    F = [i for i in range(len(at)) if I.lab[i] in Gs]
    n, loc = len(F), {i: j for j, i in enumerate(F)}
    num, den, big = I.num, I.den, I.big
    m = cp_model.CpModel()
    x = {(j, k): m.NewBoolVar(f"x{j}_{k}") for j in range(n) for k in range(K)}
    for j in range(n):
        m.AddExactlyOne([x[j, k] for k in range(K)])
    por_grupo = defaultdict(list)
    for j, i in enumerate(F):
        por_grupo[at[i]["grupo"]].append(j)
    for idx in por_grupo.values():
        for j in idx[1:]:
            for k in range(K):
                m.Add(x[j, k] == x[idx[0], k])
    for nu in sorted({nu for i in F for nu in at[i]["nucleos"] if nu is not None}):
        ancla = min(j for j, i in enumerate(F) if nu in at[i]["nucleos"])
        fuera = [j for j, i in enumerate(F) if at[i]["nucleos"] != {nu}]
        for k in range(K):
            if fuera:
                m.Add(sum(x[j, k] for j in fuera) == 0).OnlyEnforceIf(x[ancla, k])
    dev = []
    for k in range(K):
        v = m.NewIntVar(0, I.total, f"p{k}")
        m.Add(v == sum(at[i]["pop"] * x[j, k] for j, i in enumerate(F)))
        m.Add(v <= math.floor(I.techo))
        m.Add(v >= math.ceil(I.suelo))
        if reglas.criterio.tolerancia == "dura":
            m.Add(v <= math.floor(I.obj + I.tol))
            m.Add(v >= math.ceil(I.obj - I.tol))
        d = m.NewIntVar(0, big, f"dev{k}")
        m.AddAbsEquality(d, den * v - num)
        dev.append(d)
    r = {(j, k): m.NewBoolVar(f"r{j}_{k}") for j in range(n) for k in range(K)}
    pos = []
    for k in range(K):
        m.AddExactlyOne([r[j, k] for j in range(n)])
        pv = m.NewIntVar(0, max(0, n - 1), f"pos{k}")
        m.Add(pv == sum(j * r[j, k] for j in range(n)))
        for j in range(n):
            m.AddImplication(r[j, k], x[j, k])
            m.Add(pv <= j).OnlyEnforceIf(x[j, k])
        pos.append(pv)
    for k in range(K - 1):
        m.Add(pos[k] < pos[k + 1])
    dd = [m.NewIntVar(0, K - 1, f"d{j}") for j in range(n)]
    for j in range(n):
        m.Add(dd[j] == sum(k * x[j, k] for k in range(K)))
    if reglas.contiguidad:
        nivel = [m.NewIntVar(0, max(0, n - 1), f"h{j}") for j in range(n)]
        for j, i in enumerate(F):
            es_raiz = [r[j, k] for k in range(K)]
            padres = []
            for b in I.vecinos[i]:
                if b not in loc:
                    continue
                pa = m.NewBoolVar("")
                m.Add(dd[j] == dd[loc[b]]).OnlyEnforceIf(pa)
                m.Add(nivel[j] >= nivel[loc[b]] + 1).OnlyEnforceIf(pa)
                padres.append(pa)
            m.AddExactlyOne(padres + es_raiz)
            ri = m.NewBoolVar("")
            m.Add(sum(es_raiz) == ri)
            m.Add(nivel[j] == 0).OnlyEnforceIf(ri)
    pob_fijo, claves_fijo = defaultdict(int), defaultdict(set)
    for i, a in enumerate(at):
        if I.lab[i] not in Gs:
            pob_fijo[I.lab[i]] += a["pop"]
            claves_fijo[I.lab[i]].update(a["claves"])
    if reglas.disciplina_municipal:
        por_clave = defaultdict(list)
        for j, i in enumerate(F):
            for c in at[i]["claves"]:
                por_clave[c].append(j)
        y = {}
        for c, idx in por_clave.items():
            for k in range(K):
                y[c, k] = m.NewBoolVar("")
                m.AddMaxEquality(y[c, k], [x[j, k] for j in idx])
        mixto = []
        for k in range(K):
            mk = m.NewBoolVar(f"mix{k}")
            ys = [y[c, k] for c in por_clave]
            m.Add(sum(ys) >= 2).OnlyEnforceIf(mk)
            m.Add(sum(ys) <= 1).OnlyEnforceIf(mk.Not())
            mixto.append(mk)
        for c in por_clave:
            fijos = {I.lab[i] for i in I.atomos_clave[c]} - Gs  # distritos fijos que ya tienen parte de la clave
            nf, mf = len(fijos), sum(1 for d in fijos if len(claves_fijo[d]) > 1)
            pc = Fraction(I.pob_clave[c])
            lo = max(1, math.ceil(pc / I.techo)) if pc > 0 else 1
            hi = max(1, math.ceil(pc / I.obj)) if pc > 0 else 1
            ys = [y[c, k] for k in range(K)]
            m.Add(sum(ys) + nf >= lo)
            m.Add(sum(ys) + nf <= hi)
            if hi > 1:
                parte = m.NewBoolVar("")
                m.Add(sum(ys) + nf >= 2).OnlyEnforceIf(parte)
                m.Add(sum(ys) + nf <= 1).OnlyEnforceIf(parte.Not())
                zs = []
                for k in range(K):
                    z = m.NewBoolVar("")
                    m.AddMultiplicationEquality(z, [y[c, k], mixto[k]])
                    zs.append(z)
                m.Add(sum(zs) + mf <= reglas.max_mixtos).OnlyEnforceIf(parte)
    # clave D8: lo fijo marca el suelo del exceso y del desvío máximo
    tol_den = math.floor(I.tol * den)
    dev_fijo = [abs(den * p - num) for p in pob_fijo.values()]
    f = [m.NewBoolVar(f"fuera{k}") for k in range(K)]
    for k in range(K):
        m.Add(dev[k] <= tol_den).OnlyEnforceIf(f[k].Not())
    z = m.NewIntVar(max([TOPE.numerator * num] + [TOPE.denominator * v for v in dev_fijo if v <= tol_den]),
                    TOPE.denominator * big, "exceso")
    for k in range(K):
        m.Add(z >= TOPE.denominator * dev[k]).OnlyEnforceIf(f[k].Not())
    partidas = []
    for idx in I.dems:
        if not all(i in loc for i in idx):
            continue  # toca un distrito fijo: partida (o no) pase lo que pase en el grupo
        ys = []
        for k in range(K):
            yk = m.NewBoolVar("")
            m.AddMaxEquality(yk, [x[loc[i], k] for i in idx])
            ys.append(yk)
        s = m.NewBoolVar("")
        m.Add(sum(ys) <= 1).OnlyEnforceIf(s.Not())
        partidas.append(s)
    cortes = []
    for (a, b), mm in sorted(I.w.items()):
        if mm > 0 and a in loc and b in loc:
            c = m.NewBoolVar("")
            m.Add(dd[loc[a]] == dd[loc[b]]).OnlyEnforceIf(c.Not())
            cortes.append(mm * c)
    dmax = m.NewIntVar(max(dev_fijo, default=0), big, "dmax")
    for k in range(K):
        m.Add(dmax >= dev[k])
    terminos = dict(zip(ETAPAS, (sum(f), z, sum(partidas) if partidas else 0, sum(cortes) if cortes else 0, dmax)))
    orden: dict = {}
    for i in F:
        orden.setdefault(I.lab[i], len(orden))
    for j, i in enumerate(F):
        for k in range(K):
            m.AddHint(x[j, k], orden[I.lab[i]] == k)
    etapas, mejor = [], None
    for nombre in ETAPAS:
        t = terminos[nombre]
        if isinstance(t, int):
            etapas.append([nombre, "CONSTANTE", t])
            continue
        resto = tope_reloj - (time.monotonic() - t0)
        if resto <= 0.5:
            etapas.append([nombre, "TOPE_RELOJ", None])
            break
        m.Minimize(t)
        s = cp_model.CpSolver()
        s.parameters.num_workers = hilos
        s.parameters.interleave_search = True
        s.parameters.random_seed = 0
        s.parameters.max_deterministic_time = float(tdet)
        s.parameters.max_time_in_seconds = float(resto)
        est = s.StatusName(s.Solve(m))
        valor = None
        if est in ("OPTIMAL", "FEASIBLE"):
            valor = int(round(s.ObjectiveValue()))
            mejor = [next(k for k in range(K) if s.Value(x[j, k])) for j in range(n)]
            m.ClearHints()
            for j in range(n):
                for k in range(K):
                    m.AddHint(x[j, k], mejor[j] == k)
        etapas.append([nombre, est, valor])
        if est != "OPTIMAL":
            break
        m.Add(t == valor)
    cerrado = len(etapas) == len(ETAPAS) and all(e[1] in ("OPTIMAL", "CONSTANTE") for e in etapas)
    return F, mejor, etapas, cerrado


# ---------------------------------------------------------------- búsqueda local
def clave_json(c) -> list:
    return [int(c[0]), float(c[1]), int(c[2]), float(c[3]), float(c[4])]


def mejorar(I: Instancia, tdet: float, tope_sub: float, tope_total: float, hilos: int) -> dict:
    t0 = time.monotonic()
    actual = I.clave()
    version = defaultdict(int)
    vistos: set = set()
    cuenta = {"resueltos": 0, "cerrados": 0, "sin_cerrar": 0, "sin_solucion": 0, "no_mejora_clave_oficial": 0,
              "invalidos": 0}
    mejoras, por_tam, agotado = [], {2: 0, 3: 0}, False
    while not agotado:
        pendiente = None
        for tam in (2, 3):
            for G in I.grupos(tam):
                if tuple((d, version[d]) for d in G) not in vistos:
                    pendiente = G
                    break
            if pendiente:
                break
        if pendiente is None:
            break
        resto = tope_total - (time.monotonic() - t0)
        if resto <= 1:
            agotado = True
            break
        G = pendiente
        vistos.add(tuple((d, version[d]) for d in G))
        F, lab, etapas, cerrado = resolver_grupo(I, G, tdet, min(tope_sub, resto), hilos)
        cuenta["resueltos"] += 1
        cuenta["cerrados" if cerrado else "sin_cerrar"] += 1
        if lab is None:
            cuenta["sin_solucion"] += 1
            continue
        plan2 = dict(I.plan)
        for j, i in enumerate(F):
            for s in I.at[i]["secs"]:
                plan2[s] = G[lab[j]]
        if plan2 == I.plan:
            continue
        c2 = I.clave(plan2)
        if not c2 < actual:
            cuenta["no_mejora_clave_oficial"] += 1
            continue
        if not I.nat.valido(plan2):
            cuenta["invalidos"] += 1
            continue
        I.plan, actual = plan2, c2
        for j, i in enumerate(F):
            I.lab[i] = G[lab[j]]
        for d in G:
            version[d] += 1
        por_tam[len(G)] += 1
        mejoras.append({"grupo": list(G), "clave": clave_json(c2), "cerrado": cerrado,
                        "t_s": round(time.monotonic() - t0, 1)})
        log("  mejora", G, clave_json(c2), f"{time.monotonic() - t0:.0f}s")
    return {"clave": actual, "mejoras": mejoras, "mejoras_pares": por_tam[2], "mejoras_trios": por_tam[3], **cuenta,
            "tope_total_alcanzado": agotado, "tiempo_s": round(time.monotonic() - t0, 1),
            "optimo_local_demostrado": (not agotado) and cuenta["sin_cerrar"] == 0}


def una(t: str, out: Path, a, rep: int) -> dict:
    gf = out / "lab" / t / "GANADOR.json"
    g = json.loads(gf.read_text(encoding="utf-8")) if gf.is_file() else competir(t, out, a.cadenas)
    problema, reglas, nat, plan = cargar(t, out, g)
    inf0 = evaluar(problema, reglas, plan)
    I = Instancia(problema, reglas, nat, plan)
    antes = I.clave()
    log(t, f"rep {rep}: K={reglas.k} átomos={len(I.at)} unidades={len(problema.unidades)} ganador={g['ganador']}",
        clave_json(antes))
    res = mejorar(I, a.tdet, a.tope_sub, a.tope_total, a.hilos)
    inf1 = evaluar(problema, reglas, I.plan)
    despues = res.pop("clave")
    termino = next((n for n, x, y in zip(ETAPAS, antes, despues) if x != y), None)
    r = {"territorio": t, "repeticion": rep, "k": reglas.k, "atomos": len(I.at), "tamano": len(I.at) * reglas.k,
         "unidades": len(problema.unidades), "ganador": g["ganador"],
         "tiempo_competicion_s": g["tiempo_competicion_s"], "exacto_motor": EX.aplicable(problema, reglas, "D8"),
         "d8_antes": clave_json(antes), "d8_despues": clave_json(despues), "mejora": despues < antes,
         "termino_que_mejora": termino, "reglas_duras_antes_ok": inf0.valido, "reglas_duras_despues_ok": inf1.valido,
         "violaciones_despues": [[v.regla, v.ambito] for v in inf1.violaciones][:20],
         "huella_plan_antes": huella_plan(plan), "huella_plan_despues": huella_plan(I.plan), **res,
         "parametros": {"tdet_por_etapa": a.tdet, "tope_subproblema_s": a.tope_sub, "tope_total_s": a.tope_total,
                        "hilos": a.hilos, "cadenas": g["cadenas"]}}
    import ortools
    r["ortools"] = ortools.__version__
    a.salida.mkdir(parents=True, exist_ok=True)
    (a.salida / f"{t}_r{rep}.json").write_text(json.dumps(r, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    if r["mejora"] and rep == 1:
        with (a.salida / f"{t}_plan.csv").open("w", newline="", encoding="utf-8") as fh:
            w = csv.writer(fh)
            w.writerow(["unidad", "distrito_ganador", "distrito_mejora_local"])
            for u in sorted(plan):
                w.writerow([u, plan[u], I.plan[u]])
    log(t, f"rep {rep}: {clave_json(antes)} -> {clave_json(despues)} en {res['tiempo_s']} s; duras ok={inf1.valido}; "
           f"subproblemas={res['resueltos']} (sin cerrar {res['sin_cerrar']}); tope={res['tope_total_alcanzado']}")
    return r


def resumen(salida: Path) -> None:
    filas = defaultdict(dict)
    for f in sorted(salida.glob("*_r[0-9]*.json")):
        d = json.loads(f.read_text(encoding="utf-8"))
        filas[d["territorio"]][d["repeticion"]] = d
    out = []
    for t, reps in sorted(filas.items(), key=lambda kv: kv[1][min(kv[1])]["tamano"]):
        d = reps[min(reps)]
        hs = {x["huella_plan_despues"] for x in reps.values()}
        out.append({"territorio": t, "k": d["k"], "atomos": d["atomos"], "tamano": d["tamano"], "ganador": d["ganador"],
                    "d8_antes": d["d8_antes"], "d8_despues": d["d8_despues"], "mejora": d["mejora"],
                    "termino_que_mejora": d["termino_que_mejora"],
                    "tiempo_s": [reps[k]["tiempo_s"] for k in sorted(reps)],
                    "tiempo_competicion_s": d["tiempo_competicion_s"],
                    "reglas_duras_ok": all(x["reglas_duras_despues_ok"] for x in reps.values()),
                    "repeticiones": len(reps), "se_repite": (len(hs) == 1) if len(reps) > 1 else None,
                    "tope_total_alcanzado": [reps[k]["tope_total_alcanzado"] for k in sorted(reps)],
                    "optimo_local_demostrado": all(x["optimo_local_demostrado"] for x in reps.values()),
                    "subproblemas": d["resueltos"], "sin_cerrar": d["sin_cerrar"],
                    "mejoras_pares": d["mejoras_pares"], "mejoras_trios": d["mejoras_trios"]})
    (salida / "RESUMEN.json").write_text(json.dumps(out, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    with (salida / "RESUMEN.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["territorio", "k", "atomos", "tamano", "ganador", "fuera_antes", "exceso8_antes", "partidas_antes",
                    "frontera_km_antes", "desvio_antes", "fuera_despues", "exceso8_despues", "partidas_despues",
                    "frontera_km_despues", "desvio_despues", "mejora", "tiempo_s_r1", "tiempo_s_r2", "reglas_duras_ok",
                    "se_repite", "tope_total_alcanzado", "optimo_local_demostrado"])
        for x in out:
            ts = x["tiempo_s"] + [""] * 2
            w.writerow([x["territorio"], x["k"], x["atomos"], x["tamano"], x["ganador"], *x["d8_antes"],
                        *x["d8_despues"], x["mejora"], ts[0], ts[1], x["reglas_duras_ok"], x["se_repite"],
                        any(x["tope_total_alcanzado"]), x["optimo_local_demostrado"]])


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="T-509 L1: mejora local exacta del ganador de Deslinde")
    ap.add_argument("--out", default="B", type=Path, help="carpeta de la batería (con entradas/<t>)")
    ap.add_argument("--salida", default=AQUI / "resultados", type=Path)
    ap.add_argument("--cadenas", type=int, default=10)
    ap.add_argument("--repeticiones", type=int, default=2)
    ap.add_argument("--tdet", type=float, default=12.0, help="tope determinista de CP-SAT por etapa (5 etapas)")
    ap.add_argument("--tope-sub", type=float, default=60.0, help="tope de reloj por subproblema (s)")
    ap.add_argument("--tope-total", type=float, default=900.0, help="tope de reloj por territorio (s)")
    ap.add_argument("--hilos", type=int, default=4)
    ap.add_argument("territorios", nargs="+")
    a = ap.parse_args(argv)
    rc = 0
    for t in a.territorios:
        for rep in range(1, a.repeticiones + 1):
            try:
                una(t, a.out, a, rep)
            except Exception as exc:  # un territorio que falla no para la tanda; consta
                log(t, f"rep {rep}: ERROR {type(exc).__name__}: {exc}")
                a.salida.mkdir(parents=True, exist_ok=True)
                (a.salida / f"{t}_ERROR.txt").write_text(f"{type(exc).__name__}: {exc}\n", encoding="utf-8")
                rc = 1
                break
        resumen(a.salida)
    return rc


if __name__ == "__main__":
    sys.exit(main())
