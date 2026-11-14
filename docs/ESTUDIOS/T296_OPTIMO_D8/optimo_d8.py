#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PROYECTO: Diputado de Distrito
COMPONENTE: estudio T-296 (privado, D-92) — óptimo exacto o cota demostrada de la función D8
VERSIÓN: 1.0.0
NOMBRE DE VERSIÓN: Óptimo D8 · CP-SAT lexicográfico por etapas
FECHA: 2026-11-14
ESTADO: estudio (no lo importa el motor ni la producción; solo lee ddd_motor2 y herramientas/certificador_exacto)
CAMBIOS: fichero nuevo.
MOTIVO: T-296 (D-73.1, D-86.3): resolver con un resolutor exacto abierto (OR-Tools CP-SAT) la función de elección D8
  (D-68) bajo las mismas reglas del núcleo, y medir el hueco entre el ganador de Deslinde y el óptimo o su cota.
ANTERIOR: ninguna (fichero nuevo)
QUÉ HACE:
  Entrada: la competición local de un territorio (<out>/competicion/<t>/COMPETICION.json, de ddd_motor2.competir) y
  las entradas de la batería (<out>/entradas/<t>). El problema es el MISMO que juzga la competición: unidades de la
  composición M06 del canónico (ddd_motor2.adaptadores.problema_y_plan, referencia de núcleos = canónico), reglas
  Reglas.desde_contrato y demarcaciones/frontera de naturalidad_clave.natural_desde_m06 (la clave D8 oficial).
  Átomos = herramientas/certificador_exacto.construir_atomos (unidades que el núcleo obliga a ir juntas).
  Modelo CP-SAT (formulación de certificador_exacto.resolver 1.4.0, sin las exenciones de suelo, que estos
  territorios no tienen; si las tuvieran, el script se niega): asignación, provincia/cuotas, población en
  [suelo, techo], R-NUCLEO, contigüidad (árbol padre/nivel con raíz = átomo mínimo, ruptura de simetría), disciplina
  municipal R012 (K por municipio entre ceil(P/techo) y ceil(P/objetivo), máx. mixtos).
  Objetivo D8 = clave lexicográfica de naturalidad_clave.clave("D8"), por etapas (cada óptimo se fija como restricción
  antes de la siguiente):
    E1 distritos fuera de tolerancia |p − o| > tol
    E2 exceso del desvío máximo de los distritos dentro de tolerancia sobre el 8 %
    E3 partidos judiciales + comarcas agrarias partidos (en más de un distrito)
    E4 frontera cortada (suma de shared_border_m entre unidades de distritos distintos; en mm enteros)
    E5 desvío máximo |p − o| / o
  (el último término, la huella, solo desempata: no se modela; se informa si hay empate).
  Si una etapa no termina dentro de su tope, se da su mejor valor y la cota inferior probada, y se para (las etapas
  siguientes no serían exactas). Cada plan del modelo se vuelve a juzgar con reglas.evaluar y su clave D8 se calcula con
  la función oficial (Natural.clave): el resultado nunca depende solo del modelo.
  Comprobación de modelo: el ganador y el canónico, fijados, son factibles en el modelo y dan su propia clave (si no,
  el modelo sería más estricto que el núcleo y su «óptimo» no probaría nada).
SALIDA: JSON en --salida (por territorio): claves del ganador, del canónico y del óptimo/cota, hueco por término,
  tiempos y estado de cada etapa.
USO (venv fuera del repo: requirements.lock + ortools del lock del banco; ver README):
  PYTHONHASHSEED=0 python docs/ESTUDIOS/T296_OPTIMO_D8/optimo_d8.py --out /ruta/bateria --tiempo 120 nac22
"""
from __future__ import annotations

import argparse
import json
import math
import resource
import sys
import time
from collections import defaultdict
from fractions import Fraction
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "herramientas"))

from ddd_motor2.adaptadores import columnas_de_contrato, leer_composicion, problema_y_plan  # noqa: E402
from ddd_motor2.generadores import entrada_bateria  # noqa: E402
from ddd_motor2.naturalidad_clave import TOPES, natural_desde_m06  # noqa: E402
from ddd_motor2.reglas import Criterio, Reglas, evaluar  # noqa: E402
from certificador_exacto import construir_atomos  # noqa: E402

VERSION = "1.0.0"
ETAPAS = ("fuera", "exceso_8", "partidas", "frontera_mm", "desvio")


def _comp(cand: dict) -> Path:
    return Path(cand["composicion"])


def cargar(t: str, out: Path):
    """COMPETICION.json, entrada y, por candidato (canónico y ganador), su Problema (unidades de SU composición),
    su plan y su Natural (clave D8 oficial). Núcleos cerrados: referencia = canónico, como en la competición."""
    comp = json.loads((out / "competicion" / t / "COMPETICION.json").read_text(encoding="utf-8"))
    cands = {c["id"]: c for c in comp["candidatos"]}
    entrada = entrada_bateria(t, out)
    criterio = Criterio()
    reglas = Reglas.desde_contrato(entrada.cfg, criterio)
    ref = _comp(cands["canonico"])
    espacios = {}
    for nombre, c in (("canonico", cands["canonico"]), ("ganador", cands[comp["ganador"]])):
        atributos = (c.get("extra") or {}).get("atributos_secciones") or entrada.atributos_secciones
        problema, plan, _ = problema_y_plan(_comp(c), entrada.grafo_m03, entrada.cfg, referencia_nucleos=ref,
                                            atributos_secciones=atributos,
                                            respaldo_municipio_cusec=criterio.respaldo_municipio_cusec)
        nat = natural_desde_m06(problema, reglas, _comp(c), entrada.grafo_m03, entrada.cfg)
        col = columnas_de_contrato(entrada.cfg)
        filas = leer_composicion(_comp(c), col)
        sec_u = {str(f[col["seccion"]]).strip(): str(f.get(col["unidad"]) or f[col["seccion"]]).strip() for f in filas}
        sec_d = {s: plan[u] for s, u in sec_u.items()}
        espacios[nombre] = {"problema": problema, "plan": plan, "nat": nat, "cand": c, "sec_u": sec_u,
                            "sec_d": sec_d}
    return comp, reglas, espacios


def a_unidades(plan_secciones: dict[str, str], seccion_unidad: dict[str, str]) -> dict[str, str] | None:
    """Plan por secciones a plan por unidades; None si alguna unidad quedaría partida."""
    out: dict[str, str] = {}
    for s, d in plan_secciones.items():
        u = seccion_unidad[s]
        if out.setdefault(u, d) != d:
            return None
    return out


def clave_oficial(nat, plan) -> tuple:
    return nat.clave(plan, "D8")


def legible(cl: tuple) -> dict:
    return {"fuera": cl[0], "exceso_8": float(cl[1]), "partidas": cl[2], "frontera_km": cl[3],
            "desvio_max": float(cl[4]), "huella": cl[5]}


class Modelo:
    def __init__(self, problema, reglas, nat):
        from ortools.sat.python import cp_model
        self.cp = cp_model
        self.problema, self.reglas, self.nat = problema, reglas, nat
        if reglas.exentos_municipio or reglas.exentas_particion or reglas.exentas_techo:
            raise SystemExit("territorio con exenciones de suelo/techo: fuera del alcance de este prototipo")
        if len(dict(reglas.cuotas)) > 1:
            raise SystemExit("varias circunscripciones: la clave D8 usa objetivos por circunscripción (no modelado)")
        atomos, aristas = construir_atomos(problema, reglas, {})
        self.atomos, self.aristas = atomos, aristas
        n, K = len(atomos), reglas.k
        self.n, self.K = n, K
        obj, suelo, techo, tol = reglas.limites(problema.poblacion_total)
        self.obj, self.tol = obj, tol
        m = self.m = cp_model.CpModel()
        x = self.x = {(i, k): m.NewBoolVar(f"x{i}_{k}") for i in range(n) for k in range(K)}
        for i in range(n):
            m.AddExactlyOne([x[i, k] for k in range(K)])
        por_grupo = defaultdict(list)
        for i, a in enumerate(atomos):
            por_grupo[a["grupo"]].append(i)
        for idx in por_grupo.values():
            for j in idx[1:]:
                for k in range(K):
                    m.Add(x[j, k] == x[idx[0], k])
        for nu in sorted({nu for a in atomos for nu in a["nucleos"] if nu is not None}):
            ancla = min(i for i, a in enumerate(atomos) if nu in a["nucleos"])
            fuera = [j for j, a in enumerate(atomos) if a["nucleos"] != {nu}]
            for k in range(K):
                if fuera:
                    m.Add(sum(x[j, k] for j in fuera) == 0).OnlyEnforceIf(x[ancla, k])
        total = problema.poblacion_total
        num, den = obj.numerator, obj.denominator
        self.p, self.dev = [], []  # dev_k = den·|p_k − o| (entero)
        for k in range(K):
            v = m.NewIntVar(0, total, f"p{k}")
            m.Add(v == sum(a["pop"] * x[i, k] for i, a in enumerate(atomos)))
            m.Add(v <= math.floor(techo))
            m.Add(v >= math.ceil(suelo))
            if reglas.criterio.tolerancia == "dura":
                m.Add(v <= math.floor(obj + tol))
                m.Add(v >= math.ceil(obj - tol))
            d = m.NewIntVar(0, den * total + num, f"dev{k}")
            m.AddAbsEquality(d, den * v - num)
            self.p.append(v)
            self.dev.append(d)
        # contigüidad y ruptura de simetría (como certificador_exacto.resolver)
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
        self.d = d = [m.NewIntVar(0, K - 1, f"d{i}") for i in range(n)]
        for i in range(n):
            m.Add(d[i] == sum(k * x[i, k] for k in range(K)))
        if reglas.contiguidad:
            nivel = [m.NewIntVar(0, max(0, n - 1), f"h{i}") for i in range(n)]
            for i in range(n):
                es_raiz = [r[i, k] for k in range(K)]
                padres = []
                for j in vecinos[i]:
                    pa = m.NewBoolVar(f"pa{i}_{j}")
                    m.Add(d[i] == d[j]).OnlyEnforceIf(pa)
                    m.Add(nivel[i] >= nivel[j] + 1).OnlyEnforceIf(pa)
                    padres.append(pa)
                m.AddExactlyOne(padres + es_raiz)
                ri = m.NewBoolVar(f"raiz{i}")
                m.Add(sum(es_raiz) == ri)
                m.Add(nivel[i] == 0).OnlyEnforceIf(ri)
        if reglas.disciplina_municipal:
            por_clave, pob_clave = defaultdict(list), defaultdict(int)
            for i, a in enumerate(atomos):
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
        self._objetivos(num, den)

    # ------------------------------------------------------------------ términos de la clave D8
    def _objetivos(self, num, den):
        m, x, K = self.m, self.x, self.K
        nat, atomos = self.nat, self.atomos
        tol_d = self.tol * den  # |den·p − num| > tol·den  <=>  fuera
        big = max(1, den * self.problema.poblacion_total + num)
        f = [m.NewBoolVar(f"fuera{k}") for k in range(K)]
        for k in range(K):
            m.Add(self.dev[k] <= math.floor(tol_d)).OnlyEnforceIf(f[k].Not())
        self.t_fuera = sum(f)
        # exceso sobre el 8 %: Z = max(25·dev_k de los dentro, 2·num) — término 0 <=> Z = 2·num (8 % = 2/25)
        tope = Fraction(str(TOPES["D8"]))
        a, b = tope.denominator, tope.numerator  # 25, 2
        z = m.NewIntVar(b * num, a * big, "exceso")
        for k in range(K):
            m.Add(z >= a * self.dev[k]).OnlyEnforceIf(f[k].Not())
        self.t_exceso = z
        # demarcaciones partidas (partido judicial y comarca agraria por unidad, como Natural.natural)
        atomo_de = {s: i for i, at in enumerate(atomos) for s in at["secs"]}
        partidas = []
        for dem in (nat.pj, nat.ca):
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
                    m.AddMaxEquality(yk, [x[i, k] for i in idx])
                    ys.append(yk)
                s = m.NewBoolVar(f"part_{g}")
                m.Add(sum(ys) <= 1).OnlyEnforceIf(s.Not())
                partidas.append(s)
        self.t_partidas = sum(partidas) if partidas else 0
        # frontera cortada (mm enteros entre átomos)
        w = defaultdict(int)
        for (ua, ub), metros in nat.largo.items():
            i, j = atomo_de[ua], atomo_de[ub]
            if i != j:
                w[tuple(sorted((i, j)))] += int(round(metros * 1000))
        cortes = []
        for (i, j), mm in sorted(w.items()):
            if mm <= 0:
                continue
            c = m.NewBoolVar("")
            m.Add(self.d[i] == self.d[j]).OnlyEnforceIf(c.Not())
            cortes.append(mm * c)
        self.t_frontera = sum(cortes) if cortes else 0
        dmax = m.NewIntVar(0, big, "dmax")
        m.AddMaxEquality(dmax, self.dev)
        self.t_desvio = dmax
        self.terminos = dict(zip(ETAPAS, (self.t_fuera, self.t_exceso, self.t_partidas, self.t_frontera,
                                          self.t_desvio)))

    # ------------------------------------------------------------------ utilidades
    def etiquetas(self, plan: dict[str, str]) -> list[int]:
        """Plan (unidad -> distrito) a etiquetas por átomo con la ruptura de simetría del modelo."""
        lab = [plan[a["secs"][0]] for a in self.atomos]
        orden = {}
        for v in lab:  # átomo mínimo de cada distrito, en orden creciente
            orden.setdefault(v, len(orden))
        return [orden[v] for v in lab]

    def a_plan(self, sol) -> dict[str, str]:
        return {s: f"D{k}" for i, a in enumerate(self.atomos) for k in range(self.K) if sol.Value(self.x[i, k])
                for s in a["secs"]}

    def solver(self, tiempo: float, hilos: int):
        s = self.cp.CpSolver()
        s.parameters.max_time_in_seconds = float(tiempo)
        s.parameters.num_workers = int(hilos)
        s.parameters.random_seed = 0
        return s

    def fijado(self, plan, tiempo, hilos) -> dict:
        """¿El plan es factible en el modelo? (comprobación de que el modelo no es más estricto que el núcleo) y sus
        términos (las holguras de E1 y E2 interactúan: se resuelven también por etapas)."""
        cl = self.m.Clone()
        for i, k in enumerate(self.etiquetas(plan)):
            cl.Add(self.x[i, k] == 1)
        lx = self.lexicografico(tiempo, hilos, None, modelo=cl)
        ter = {e["etapa"]: e.get("valor") for e in lx["etapas"]}
        out = {"estado": "FACTIBLE" if lx["exacto"] else "NO_FACTIBLE_O_SIN_RESPUESTA", "terminos": ter}
        if lx["exacto"]:
            out["coincide_con_clave_oficial"] = all(
                math.isclose(a, float(b), rel_tol=0, abs_tol=1e-12)  # el exceso oficial resta 0.08 en coma flotante
                for a, b in zip(self.a_clave(ter), self.nat.clave(plan, "D8")[:5]))
        return out

    def a_clave(self, ter: dict) -> tuple:
        """Términos enteros del modelo -> los cinco primeros de la clave D8 oficial (fracciones exactas)."""
        num = self.obj.numerator
        tope = Fraction(str(TOPES["D8"]))
        exceso = Fraction(ter["exceso_8"], tope.denominator * num) - tope
        return (float(ter["fuera"]), float(max(Fraction(0), exceso)), float(ter["partidas"]), round(ter["frontera_mm"] / 1e6, 3),
                float(Fraction(ter["desvio"], num)))

    def pista(self, plan):
        self.m.ClearHints()
        for i, k in enumerate(self.etiquetas(plan)):
            for kk in range(self.K):
                self.m.AddHint(self.x[i, kk], kk == k)

    def lexicografico(self, tiempo: float, hilos: int, pista: dict | None, modelo=None) -> dict:
        etapas, mejor = [], None
        m = self.m if modelo is None else modelo
        if pista:
            self.pista(pista)
        for nombre in ETAPAS:
            t = self.terminos[nombre]
            if isinstance(t, int):  # término constante (p. ej. sin frontera medida)
                etapas.append({"etapa": nombre, "estado": "CONSTANTE", "valor": t, "cota": t})
                continue
            m.Minimize(t)
            s = self.solver(tiempo, hilos)
            t0 = time.time()
            est = s.StatusName(s.Solve(m))
            e = {"etapa": nombre, "estado": est, "t_s": round(time.time() - t0, 2)}
            if est in ("OPTIMAL", "FEASIBLE"):
                e["valor"] = int(round(s.ObjectiveValue()))
                e["cota"] = int(math.ceil(s.BestObjectiveBound() - 1e-9))
                mejor = self.a_plan(s)
                if modelo is None:
                    self.pista(mejor)
            elif est == "UNKNOWN":
                e["cota"] = int(math.ceil(s.BestObjectiveBound() - 1e-9))
            etapas.append(e)
            if est != "OPTIMAL":
                break
            m.Add(t == e["valor"])
        return {"etapas": etapas, "plan": mejor,
                "exacto": all(e["estado"] in ("OPTIMAL", "CONSTANTE") for e in etapas) and len(etapas) == len(ETAPAS)}


def comparar(a: tuple, b: tuple) -> dict:
    """Primer término (sin huella) en que difieren a (ganador) y b (óptimo)."""
    for nombre, va, vb in zip(("fuera", "exceso_8", "partidas", "frontera_km", "desvio_max"), a[:5], b[:5]):
        if va != vb:
            return {"termino": nombre, "ganador": float(va), "optimo": float(vb), "diferencia": float(va - vb)}
    return {"termino": None, "empate_hasta_huella": True, "misma_particion": a[5] == b[5]}


def instancia(t: str, reglas, e: dict, mod: "Modelo") -> dict:
    """Instancia neutra (para `redist` y GerryChain con las mismas reglas): átomos con población y demarcaciones,
    aristas entre átomos, K, límites exactos y reglas R012 / núcleo ya resueltas en los átomos."""
    obj, suelo, techo, tol = reglas.limites(e["problema"].poblacion_total)
    nat = e["nat"]
    return {"schema": "ddd.t296-instancia/1.0", "territorio": t, "k": reglas.k, "huella_reglas": reglas.huella(),
            "limites": {"objetivo": str(obj), "suelo": str(suelo), "techo": str(techo), "tolerancia": str(tol)},
            "max_mixtos": reglas.max_mixtos, "tope_d8": TOPES["D8"],
            "atomos": [{"id": i, "unidades": a["secs"], "poblacion": a["pop"], "claves_r012": sorted(map(str, a["claves"])),
                        "nucleo": next(iter(a["nucleos"] - {None}), None),
                        "partidos": sorted({nat.pj[u] for u in a["secs"] if nat.pj[u]}),
                        "comarcas": sorted({nat.ca[u] for u in a["secs"] if nat.ca[u]})}
                       for i, a in enumerate(mod.atomos)],
            "aristas": [list(x) for x in mod.aristas]}


def estudiar(t: str, out: Path, tiempo: float, hilos: int, exportar: Path | None = None) -> dict:
    t0 = time.time()
    comp, reglas, esp = cargar(t, out)
    gan = esp["ganador"]
    clave_gan = clave_oficial(gan["nat"], gan["plan"])
    res = {"territorio": t, "version": VERSION, "k": reglas.k, "huella_reglas": reglas.huella(),
           "ganador_competicion": comp["ganador"],
           "ganador": {"clave_d8": legible(clave_gan),
                       "igual_a_competicion": list(map(float, clave_gan[:5])) == list(
                           map(float, gan["cand"]["clave_naturalidad"][:5]))},
           "canonico": {"clave_d8": legible(clave_oficial(esp["canonico"]["nat"], esp["canonico"]["plan"]))},
           "espacios": {}}
    if reglas.k == 1:
        res["estado"] = "TRIVIAL_K1"
        return res
    # espacio = unidades de una composición; si el ganador usa las mismas que el canónico, uno solo
    nombres = ["canonico"] + (["ganador"] if set(gan["plan"]) != set(esp["canonico"]["plan"]) else [])
    for nombre in nombres:
        e = esp[nombre]
        mod = Modelo(e["problema"], reglas, e["nat"])
        if exportar is not None:
            exportar.mkdir(parents=True, exist_ok=True)
            (exportar / f"{t}_{nombre}_instancia.json").write_text(
                json.dumps(instancia(t, reglas, e, mod), ensure_ascii=False, separators=(",", ":")) + "\n",
                encoding="utf-8")
        r = {"unidades": len(e["problema"].unidades), "atomos": mod.n, "aristas_atomos": len(mod.aristas),
             "variables": len(mod.m.Proto().variables), "restricciones": len(mod.m.Proto().constraints),
             "modelo_acepta": {}}
        planes = {}
        for otro in ("canonico", "ganador"):
            p = a_unidades(esp[otro]["sec_d"], e["sec_u"])
            if p is None:
                r["modelo_acepta"][otro] = {"estado": "NO_REPRESENTABLE (parte unidades de este espacio)"}
                continue
            planes[otro] = p
            r["modelo_acepta"][otro] = mod.fijado(p, min(60, tiempo), hilos)
        lx = mod.lexicografico(tiempo, hilos, planes.get("ganador") or planes.get("canonico"))
        r["etapas"], r["exacto"] = lx["etapas"], lx["exacto"]
        if lx["plan"] is not None:
            cl = clave_oficial(e["nat"], lx["plan"])
            r["mejor_modelo"] = {"valido_nucleo": evaluar(e["problema"], reglas, lx["plan"]).valido,
                                 "clave_d8": legible(cl)}
            r["hueco_ganador_menos_mejor"] = comparar(clave_gan, cl)
            r["_plan"] = lx["plan"]
        r["estado"] = "OPTIMO_D8" if r["exacto"] else "COTA_D8"
        res["espacios"][nombre] = r
    res["t_total_s"] = round(time.time() - t0, 1)
    res["memoria_max_mb"] = round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024, 1)
    return res


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("QUÉ HACE:")[0])
    ap.add_argument("territorios", nargs="+")
    ap.add_argument("--out", type=Path, required=True, help="directorio de la batería (entradas + competicion)")
    ap.add_argument("--tiempo", type=float, default=120, help="tope por etapa (s)")
    ap.add_argument("--hilos", type=int, default=4)
    ap.add_argument("--salida", type=Path, default=Path(__file__).parent / "resultados")
    ap.add_argument("--exportar", type=Path, default=None, help="escribe la instancia neutra (redist / GerryChain)")
    a = ap.parse_args(argv)
    a.salida.mkdir(parents=True, exist_ok=True)
    for t in a.territorios:
        r = estudiar(t, a.out, a.tiempo, a.hilos, a.exportar)
        planes = {n: e.pop("_plan") for n, e in r.get("espacios", {}).items() if "_plan" in e}
        (a.salida / f"{t}.json").write_text(json.dumps(r, ensure_ascii=False, indent=1, default=str) + "\n",
                                            encoding="utf-8")
        for n, plan in planes.items():
            with open(a.salida / f"{t}_{n}_mejor_modelo.csv", "w", encoding="utf-8") as fh:
                fh.write("unidad,distrito\n")
                for u in sorted(plan):
                    fh.write(f"{u},{plan[u]}\n")
        print(json.dumps({"territorio": t, "t_total_s": r.get("t_total_s"), **{
            n: (e["estado"], e.get("hueco_ganador_menos_mejor")) for n, e in r.get("espacios", {}).items()}},
            ensure_ascii=False, default=str), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
