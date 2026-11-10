#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PROYECTO: Diputado de Distrito
COMPONENTE: motor 2 — laboratorio de naturalidad: competición con cinco funciones de calidad y grafo ponderado
VERSIÓN: 1.1.0
NOMBRE DE VERSIÓN: Naturalidad · competición A/B/C + D5/D8
FECHA: 2026-11-10
ESTADO: experimento (motor 2; producción no lo importa; no lanza nada; el criterio NO se fija aquí)
CAMBIOS: 1.1.0 (T-179): variantes D5 y D8 = C con tope de desvío máximo del 5 % / 8 % solo para elegir entre
  candidatos (no es regla: el núcleo, suelo, techo y K no cambian). Las cadenas ponderadas son las mismas (mismas
  semillas) y registran además el mejor estado bajo cada tope; A/B/C y su huella no cambian con el mismo entorno.
  RESULTADO.json guarda las versiones de shapely/GEOS/geopandas/gerrychain («entorno»): con otra GEOS cambia alguna
  arista y, con ella, las cadenas (Badajoz, Madrid y Barcelona no reprodujeron #651). 1.0.0: fichero nuevo.
MOTIVO: T-172, pasos 3 y 4: ¿cuánta población «cuesta» un mapa más natural? Misma entrada, mismas reglas (núcleo
  ddd_motor2.reglas.evaluar), mismas semillas públicas (semilla.py); cambia solo cómo se elige y cómo se corta.
ANTERIOR: 1.0.0 (T-172, #651)
QUÉ HACE: por territorio,
  entrada   el mapa vigente (datos/composicion/<t>.csv: población por sección) y la geometría INE del contrato
            (naturalidad_mapas.Geometria). Unidades: cada municipio con población <= objetivo es una unidad (la regla
            municipal no permite partirlo); los mayores van por secciones. Aristas: fronteras >= 1 m; los contactos en
            un vértice valen como puentes de contigüidad.
  candidatos el mapa vigente («motor actual») y N cadenas ReCom de GerryChain 1.0 (como producción: epsilon = tolerancia
            del contrato) desde el mapa vigente con las semillas públicas; restricción en cada paso = núcleo completo
            (evaluar sin violaciones). De cada cadena se guarda el mejor estado visto según cada función.
  funciones A  vigente: (fuera de tolerancia, desvío máximo, ECM, huella).
            B  población hasta cumplir la tolerancia y, a igualdad, naturalidad: (fuera de tolerancia, partidos
               judiciales partidos + comarcas agrarias partidas, frontera cortada en km, desvío máximo, huella).
            C  como B, con cadenas sobre el grafo ponderado: árbol de expansión mínimo con peso aleatorio + recargo por
               arista que cruza partido judicial (rpj), comarca agraria (rca), área de movilidad EM-1 (rmov) y por
               frontera corta (rlong · (1 − min(1, longitud / mediana))). Corta, pues, por donde hay menos vínculo.
            D5, D8  como C, con tope de desvío máximo (5 % / 8 %) solo para elegir: (fuera de tolerancia, exceso sobre
               el tope, y después la clave de B). El tope se mide en los distritos dentro de tolerancia (el que ya está
               fuera, p. ej. un municipio exento, no cuenta); si ningún candidato lo cumple gana el de menor exceso.
  salida    <out>/<t>/RESULTADO.json (candidatos, ganadores, tiempos, huella), <t>_{A,B,C}.csv (sección, distrito,
            población) e indicadores de naturalidad de cada ganador (naturalidad_mapas.indicadores).
USO: PYTHONHASHSEED=0 python -m ddd_motor2.naturalidad_competicion --seccionado-dir <dir> --out <dir> \
       [--cadenas 20] [--pasos 150] [--rpj 0.5] [--rca 0.3] [--rmov 0.2] [--rlong 0.3] territorio ...
LÍMITES: laboratorio sobre secciones y mapa vigente (no rehace unidades M04 ni el canónico M05); las cadenas parten del
  mapa vigente. Sin ríos ni relieve (no hay fuente en el repo todavía).
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import random
import statistics
import sys
import time
from collections import defaultdict
from fractions import Fraction
from functools import partial
from pathlib import Path

from . import naturalidad_mapas as nm
from .reglas import Reglas, evaluar
from .reglas.modelo import Problema, Unidad
from .semilla import descripcion

ROOT = nm.ROOT
TOPES = {"D5": 0.05, "D8": 0.08}
FUNCIONES = ("A", "B", "C", "D5", "D8")


def cargar_cfg(t: str) -> dict:
    os.environ.setdefault("DDD_RUN_ID", "laboratorio-naturalidad")
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    from ddd_core.config import load_params_yaml  # noqa: PLC0415
    return load_params_yaml(str(ROOT / "territorios" / t / "config" / f"{t}_2025.yaml"))


class Laboratorio:
    def __init__(self, t: str, seccionado_dir: Path, tablas: dict, mov):
        self.t, self.tablas, self.mov = t, tablas, mov
        self.cfg = cargar_cfg(t)
        self.reglas = Reglas.desde_contrato(self.cfg)
        self.asig0, self.pob_s = nm.leer_composicion(nm.COMPOSICION / f"{t}.csv")
        self.geo = nm.Geometria(nm.shp_de(seccionado_dir, nm.anio_seccionado(t)), set(self.asig0))
        total = sum(self.pob_s.values())
        self.objetivo, self.suelo, self.techo, self.tol = self.reglas.limites(total)
        pob_m: dict[str, int] = defaultdict(int)
        for s, p in self.pob_s.items():
            pob_m[s[:5]] += p
        # unidad de cada sección: municipio entero si no puede partirse (<= objetivo), si no la propia sección
        self.unidad = {s: (s[:5] if pob_m[s[:5]] <= self.objetivo else s) for s in self.asig0}
        self.secciones_de: dict[str, list[str]] = defaultdict(list)
        for s in sorted(self.asig0):
            self.secciones_de[self.unidad[s]].append(s)
        pob_u = {u: sum(self.pob_s[s] for s in ss) for u, ss in self.secciones_de.items()}
        largo: dict[tuple[str, str], float] = defaultdict(float)
        for a, b, w in self.geo.aristas():
            ua, ub = self.unidad[a], self.unidad[b]
            if ua != ub:
                largo[tuple(sorted((ua, ub)))] += w
        contacto = {tuple(sorted((self.unidad[a], self.unidad[b]))) for a, b in self.geo.contactos()}
        contacto = sorted(p for p in contacto if p[0] != p[1] and p not in largo)
        self.largo = dict(sorted(largo.items()))
        self.problema = Problema(
            tuple(Unidad(u, pob_u[u], municipio=u[:5], provincia=u[:2]) for u in sorted(pob_u)),
            tuple(self.largo), tuple(contacto))
        self.pob_u = pob_u
        self.u0 = {u: self.asig0[ss[0]] for u, ss in self.secciones_de.items()}
        if any(self.asig0[s] != self.u0[self.unidad[s]] for s in self.asig0):
            raise ValueError(f"{t}: el mapa vigente parte un municipio que la regla no deja partir")
        # demarcaciones por unidad (la del municipio; la sección hereda la de su municipio)
        self.pj = {u: tablas["pj"].get(u[:5]) for u in pob_u}
        self.ca = {u: tablas["ca"].get(u[:5]) for u in pob_u}
        self.area = {u: nm.grupo_area(self.secciones_de[u][0], mov[0]) for u in pob_u}

    # ---------------------------------------------------------------- métricas baratas por estado (unidades)
    def valido(self, asig: dict[str, str]) -> bool:
        return evaluar(self.problema, self.reglas, asig).valido

    def clave(self, asig: dict[str, str], funcion: str) -> tuple:
        pob: dict[str, int] = defaultdict(int)
        for u, d in asig.items():
            pob[d] += self.pob_u[u]
        dev = [abs(p - self.objetivo) for p in pob.values()]
        fuera = sum(1 for x in dev if x > self.tol)
        dmax = max(dev) / self.objetivo
        ecm = sum(x * x for x in dev) / (len(dev) * self.objetivo * self.objetivo)
        h = huella_plan(asig)
        if funcion == "A":
            return (fuera, dmax, ecm, h)
        if funcion in TOPES:
            dentro = [x for x in dev if x <= self.tol]
            exceso = max(0.0, (max(dentro) if dentro else 0) / self.objetivo - TOPES[funcion])
            return (fuera, exceso, *self.clave(asig, "B")[1:])
        partidas = 0
        for dem in (self.pj, self.ca):
            ds: dict[str, set] = defaultdict(set)
            for u, d in asig.items():
                if dem[u] is not None:
                    ds[dem[u]].add(d)
            partidas += sum(1 for v in ds.values() if len(v) > 1)
        corte = sum(w for (a, b), w in self.largo.items() if asig[a] != asig[b])
        return (fuera, partidas, round(corte / 1000, 3), dmax, h)

    def recargos(self, rpj: float, rca: float, rmov: float, rlong: float) -> dict[tuple[str, str], float]:
        med = statistics.median(self.largo.values()) if self.largo else 1.0
        out = {}
        for (a, b), w in self.largo.items():
            r = 0.0
            for dem, val in ((self.pj, rpj), (self.ca, rca), (self.area, rmov)):
                if dem[a] is None or dem[a] != dem[b]:
                    r += val
            r += rlong * (1 - min(1.0, w / med))
            out[(a, b)] = r
        for a, b in self.problema.puentes:
            out[(a, b)] = rpj + rca + rmov + rlong
        return out

    def a_secciones(self, asig_u: dict[str, str]) -> dict[str, str]:
        return {s: asig_u[self.unidad[s]] for s in self.asig0}


def huella_plan(asig: dict[str, str]) -> str:
    """Independiente de las etiquetas: conjunto de distritos como conjuntos de unidades."""
    g: dict[str, list[str]] = defaultdict(list)
    for u, d in asig.items():
        g[d].append(u)
    forma = sorted("|".join(sorted(v)) for v in g.values())
    return hashlib.sha256("\n".join(forma).encode("utf-8")).hexdigest()


def arbol_ponderado(graph, region_surcharge=None, treat_unassigned_as_single_region=False, rng=None, *, recargo):
    """Kruskal con peso aleatorio [0,1) + recargo fijo de la arista (sustituye a random_spanning_tree)."""
    from gerrychain.tree.spanning_tree import _ordered_edge_ids  # noqa: PLC0415
    if not isinstance(rng, random.Random):
        rng = random.Random(rng)
    for eid in _ordered_edge_ids(graph):
        a, b = (graph.node_data(n)["uid"] for n in graph.get_edge_from_edge_id(eid))
        graph.edge_data(eid)["random_weight"] = rng.random() + recargo.get((a, b) if a < b else (b, a), 0.0)
    return graph.minimum_spanning_tree_from_edge_weight(edge_weight_attribute_name="random_weight")


def cadena(lab: Laboratorio, semilla: int, pasos: int, funciones: tuple[str, ...], recargo: dict | None) -> dict:
    import networkx as nx  # noqa: PLC0415
    from gerrychain import Graph, MarkovChain, Partition, updaters  # noqa: PLC0415
    from gerrychain.proposals import recom  # noqa: PLC0415
    from gerrychain.tree import bipartition_tree  # noqa: PLC0415
    g = nx.Graph()
    for u in sorted(lab.pob_u):
        g.add_node(u, population=lab.pob_u[u], district=lab.u0[u], uid=u)
    g.add_edges_from(sorted(lab.largo) + sorted(lab.problema.puentes))
    graph = Graph.from_networkx(g)
    ini = Partition(graph, assignment="district", updaters={"population": updaters.Tally("population", alias="population")})
    # Reelección de par como producción (m05_gerrychain_engine): si una pareja no admite corte equilibrado (p. ej.
    # un distrito vigente fuera de tolerancia), se prueba otra en lugar de abortar la cadena.
    bip = partial(bipartition_tree, allow_pair_reselection=True, max_attempts=1000)
    if recargo is not None:
        bip = partial(bipartition_tree, allow_pair_reselection=True, max_attempts=1000,
                      spanning_tree_fn=partial(arbol_ponderado, recargo=recargo))
    prop = partial(recom, pop_col="population", pop_target=float(lab.objetivo), epsilon=float(lab.tol / lab.objetivo),
                   node_repeats=0, bipartition_tree_fn=bip)

    uid = {i: ini.graph.node_data(i)["uid"] for i in ini.graph.node_indices}

    def plan(p) -> dict[str, str]:
        return {uid[i]: str(d) for i, d in p.assignment.items()}

    def nucleo(p) -> bool:
        return lab.valido(plan(p))

    ch = MarkovChain(proposal_fn=prop, constraints=[nucleo], initial_partition=ini,
                     total_steps=pasos, rng=semilla)
    mejor: dict[str, tuple] = {}
    vistos = set()
    t0 = time.perf_counter()
    fallo = ""
    try:
        for p in ch:
            asig = plan(p)
            h = huella_plan(asig)
            vistos.add(h)
            for f in funciones:
                k = lab.clave(asig, f)
                if f not in mejor or k < mejor[f][0]:
                    mejor[f] = (k, asig)
    except Exception as e:  # noqa: BLE001  (un fallo de la cadena se informa; sus mejores estados siguen valiendo)
        fallo = f"{type(e).__name__}: {e}"
    return {"semilla": semilla, "mejor": mejor, "unicos": len(vistos), "tiempo_s": time.perf_counter() - t0,
            "fallo": fallo}


def entorno() -> dict:
    from importlib.metadata import version  # noqa: PLC0415
    import shapely  # noqa: PLC0415
    out = {"python": sys.version.split()[0], "geos": shapely.geos_version_string}
    for m in ("shapely", "geopandas", "pyogrio", "gerrychain", "networkx"):
        out[m] = version(m)
    return out


def _j(x):
    if isinstance(x, Fraction):
        return float(x)
    if isinstance(x, tuple):
        return [_j(v) for v in x]
    return x


def correr(t: str, a, tablas: dict, mov) -> dict:
    t0 = time.perf_counter()
    lab = Laboratorio(t, Path(a.seccionado_dir), tablas, mov)
    t_ent = time.perf_counter() - t0
    if not lab.valido(lab.u0):
        raise ValueError(f"{t}: el mapa vigente no es válido para el núcleo con esta entrada")
    desc = descripcion(lab.cfg, t, a.cadenas)
    rec = lab.recargos(a.rpj, a.rca, a.rmov, a.rlong)
    cand = {f: [("vigente", None, lab.clave(lab.u0, f), lab.u0)] for f in FUNCIONES}
    cadenas = {"libre": [], "ponderado": []}
    for s in desc["semillas"]:
        r = cadena(lab, s, a.pasos, ("A", "B"), None)
        cadenas["libre"].append({k: v for k, v in r.items() if k != "mejor"})
        for f in "AB":
            if f in r["mejor"]:
                cand[f].append((f"libre-{s}", s, *r["mejor"][f]))
        r = cadena(lab, s, a.pasos, ("B", *TOPES), rec)
        cadenas["ponderado"].append({k: v for k, v in r.items() if k != "mejor"})
        for f, k in (("C", "B"), *((d, d) for d in TOPES)):
            if k in r["mejor"]:
                cand[f].append((f"ponderado-{s}", s, *r["mejor"][k]))
        print(f"  {t} semilla {s}: ok", flush=True)
    out = Path(a.out) / t
    out.mkdir(parents=True, exist_ok=True)
    ganadores = {}
    for f in FUNCIONES:
        idx = min(range(len(cand[f])), key=lambda i: (cand[f][i][2], i))
        cid, sem, k, asig = cand[f][idx]
        sec = lab.a_secciones(asig)
        with open(out / f"{t}_{f}.csv", "w", newline="", encoding="utf-8") as fh:
            w = csv.writer(fh, lineterminator="\n")
            w.writerow(["seccion", "distrito", "poblacion"])
            for s in sorted(sec):
                w.writerow([s, sec[s], lab.pob_s[s]])
        ind = nm.indicadores(sec, lab.pob_s, lab.geo, tablas, mov)
        ind.pop("por_distrito", None)
        inf = evaluar(lab.problema, lab.reglas, asig)
        pob: dict[str, int] = defaultdict(int)
        for u, d in asig.items():
            pob[d] += lab.pob_u[u]
        ganadores[f] = {"candidato": cid, "semilla": sem, "clave": _j(k), "valido": inf.valido,
                        "fuera_tolerancia": inf.metricas["fuera_tolerancia"],
                        "desvio_max": inf.metricas["max_desviacion_ratio"],
                        "suma_desvio_personas": float(sum(abs(p - lab.objetivo) for p in pob.values())),
                        "max_desvio_personas": float(max(abs(p - lab.objetivo) for p in pob.values())),
                        "indicadores": ind,
                        "sha256_csv": hashlib.sha256((out / f"{t}_{f}.csv").read_bytes()).hexdigest()}
    res = {"territorio": t, "version": "1.1.0", "topes": TOPES, "unidades": len(lab.pob_u), "aristas": len(lab.largo),
           "puentes_contacto": len(lab.problema.puentes), "objetivo": float(lab.objetivo), "tolerancia": float(lab.tol),
           "parametros": {"cadenas": a.cadenas, "pasos": a.pasos, "rpj": a.rpj, "rca": a.rca, "rmov": a.rmov,
                          "rlong": a.rlong},
           "semilla_publica": desc, "huella_reglas": lab.reglas.huella(), "ganadores": ganadores,
           "candidatos": {f: [[c[0], _j(c[2])] for c in cand[f]] for f in FUNCIONES},
           "cadenas": cadenas, "entorno": entorno(), "tiempos_s": {"entrada": t_ent, "total": time.perf_counter() - t0}}

    def _huella(fs) -> str:
        return hashlib.sha256(json.dumps(
            {"g": {f: [ganadores[f]["candidato"], ganadores[f]["sha256_csv"]] for f in fs},
             "c": {f: res["candidatos"][f] for f in fs}, "p": res["parametros"], "r": res["huella_reglas"]},
            sort_keys=True).encode()).hexdigest()
    res["huella"] = _huella("ABC")  # la de 1.0.0: A/B/C no cambian
    res["huella_d"] = _huella(FUNCIONES)
    (out / "RESULTADO.json").write_text(json.dumps(res, ensure_ascii=False, indent=1, default=_j) + "\n", encoding="utf-8")
    return res


def main(argv=None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--seccionado-dir", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--cadenas", type=int, default=20)
    p.add_argument("--pasos", type=int, default=150)
    p.add_argument("--rpj", type=float, default=0.5)
    p.add_argument("--rca", type=float, default=0.3)
    p.add_argument("--rmov", type=float, default=0.2)
    p.add_argument("--rlong", type=float, default=0.3)
    p.add_argument("territorios", nargs="+")
    a = p.parse_args(argv)
    if os.environ.get("PYTHONHASHSEED") != "0":
        print("aviso: sin PYTHONHASHSEED=0 la reproducibilidad bit a bit no está garantizada", file=sys.stderr)
    tablas, mov = nm.tablas_municipio(), nm.movilidad()
    rc = 0
    for t in a.territorios:
        try:
            r = correr(t, a, tablas, mov)
            print(f"{t}: huella {r['huella'][:12]} en {r['tiempos_s']['total']:.0f} s", flush=True)
        except Exception as e:  # noqa: BLE001
            print(f"{t}: ERROR {type(e).__name__}: {e}", flush=True)
            rc = 1
    return rc


if __name__ == "__main__":
    sys.exit(main())
