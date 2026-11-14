#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PROYECTO: Diputado de Distrito
COMPONENTE: motor 2 — laboratorio de naturalidad: competición con cinco funciones de calidad y grafo ponderado
VERSIÓN: 1.6.0
NOMBRE DE VERSIÓN: Naturalidad · árbol ponderado sobre RX
FECHA: 2026-11-11
ESTADO: experimento (motor 2; producción no lo importa; no lanza nada; el criterio NO se fija aquí)
CAMBIOS: 1.6.0 (T-262, D-89): `arbol_ponderado` sobre grafos RX lee extremos y datos de todas las aristas de una vez
  (edge_index_map) en vez de get_edge_from_edge_id/node_data/edge_data por arista: mismo orden de aristas
  (_ordered_edge_ids) y una llamada a rng.random() por arista, mismos pesos, mismo árbol y mismos mapas bit a bit.
  1.5.0 (T-205): la clave de calidad (A, B, D5, D8), los desvíos, la naturalidad y los recargos salen a
  ddd_motor2/naturalidad_clave.py (Natural), que comparte la competición del motor nuevo; mismo orden y mismos valores
  (fracciones exactas también con objetivos por circunscripción). `cadena` admite cualquier Natural (el generador
  «ponderado» de la competición la usa sobre las unidades M04 y el grafo M03).
  1.4.0 (T-202): (1) contratos con unidades internas (partitioning connected_internal_units: Extremadura,
  Principado de Asturias): el municipio es atómico hasta atomicity_ratio × objetivo, como en producción; por encima,
  la unidad (y su clave R012) es la sección: más fina que los trozos de producción, que no se pueden reconstruir sin el
  grafo M03 original (caducado). (2) Mapa vigente que incumple el núcleo (D-66; p. ej. Ávila en dos distritos
  mixtos en Castilla y León): A sigue siendo el vigente, marcado no válido; C y D8 parten de un «vigente reparado»
  (las secciones del municipio en el distrito mixto sobrante pasan a otro distrito del mismo municipio, si el plan
  queda válido) y solo eligen entre mapas válidos; si no hay reparación, se informa con los intentos.
  1.3.0 (T-179, autonómicas): objetivo por circunscripción cuando el contrato trae province_districts de más de
  una provincia o isla: objetivo = población de la circunscripción / su cuota; desvíos, tolerancia, topes y fuera de
  tolerancia se miden contra él, y ReCom corta cada par fusionado por la mitad de su población. ReCom no limita el par a una
  circunscripción: un par de circunscripciones distintas da un plan que rechaza la restricción `nucleo` (R-CUOTA /
  provincia única), y la cadena se queda en el estado anterior.
  Sin cuotas múltiples (Congreso), todo igual que 1.2.0.
  --reanudar solo salta un territorio si su RESULTADO.json tiene la misma versión, parámetros (con funciones) y
  entorno; si no, lo rechaza sin sobrescribirlo.
  1.2.0 (T-179, nacional): --funciones (p. ej. C,D8: sin las cadenas libres; A queda como el mapa vigente,
  candidato «vigente») y --reanudar (salta los territorios que ya tienen RESULTADO.json en --out), para
  recorrer los territorios en sesión. Con las cinco funciones el resultado es idéntico a 1.1.0. Islas: partición
  de cada unidad según configuracion/particiones_insulares_2025.json (hard_partition_lookup del contrato) y sus
  puentes marítimos; enclaves: topology_bridges del contrato (p. ej. Treviño en Burgos) como puentes.
  1.1.0 (T-179): variantes D5 y D8 = C con tope de desvío máximo del 5 % / 8 % solo para elegir entre
  candidatos (no es regla: el núcleo, suelo, techo y K no cambian). Las cadenas ponderadas son las mismas (mismas
  semillas) y registran además el mejor estado bajo cada tope; A/B/C y su huella no cambian con el mismo entorno.
  RESULTADO.json guarda las versiones de shapely/GEOS/geopandas/gerrychain («entorno»): con otra GEOS cambia alguna
  arista y, con ella, las cadenas (Badajoz, Madrid y Barcelona no reprodujeron #651). 1.0.0: fichero nuevo.
MOTIVO: T-172, pasos 3 y 4: ¿cuánta población «cuesta» un mapa más natural? Misma entrada, mismas reglas (núcleo
  ddd_motor2.reglas.evaluar), mismas semillas públicas (semilla.py); cambia solo cómo se elige y cómo se corta.
ANTERIOR: 1.5.0 (T-205) — legacy/ddd_motor2/naturalidad_competicion_v1.5.0_20261110.py
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
       [--cadenas 20] [--pasos 150] [--rpj 0.5] [--rca 0.3] [--rmov 0.2] [--rlong 0.3] [--funciones A,B,C,D5,D8]
       [--reanudar] territorio ...
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
import sys
import time
from collections import defaultdict
from fractions import Fraction
from functools import partial
from pathlib import Path

from . import naturalidad_mapas as nm
from .naturalidad_clave import TOPES, Natural
from .reglas import Reglas, evaluar
from .reglas.modelo import Problema, Unidad
from .semilla import descripcion

ROOT = nm.ROOT
VERSION = "1.5.0"
FUNCIONES = ("A", "B", "C", "D5", "D8")


def cargar_cfg(t: str) -> dict:
    os.environ.setdefault("DDD_RUN_ID", "laboratorio-naturalidad")
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    from ddd_core.config import load_params_yaml  # noqa: PLC0415
    return load_params_yaml(str(ROOT / "territorios" / t / "config" / f"{t}_2025.yaml"))


class Laboratorio(Natural):
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
        part = particiones(self.cfg)
        psec = {s: (part.get(s) or part.get(s[:5])) for s in self.asig0} if part else {}
        cp = self.cfg.get("partitioning") or {}
        self.internas = bool(cp.get("enabled")) and cp.get("strategy") == "connected_internal_units"
        limite = self.objetivo * Fraction(str(cp.get("atomicity_ratio", 1))) if self.internas else self.objetivo
        self.unidad = unidades_de(self.asig0, pob_m, limite, psec)
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
        # los CUSEC del YAML pueden llegar como enteros sin el cero inicial (0910901001 → 910901001)
        puentes_sec = {tuple(x.zfill(10) for x in p) for p in set(part.pop("_puentes", ())) | puentes_contrato(self.cfg)}
        contacto |= {tuple(sorted((self.unidad[a], self.unidad[b]))) for a, b in puentes_sec
                     if a in self.unidad and b in self.unidad}
        contacto = sorted(p for p in contacto if p[0] != p[1] and p not in largo)
        self.largo = dict(sorted(largo.items()))
        self.problema = Problema(
            tuple(Unidad(u, pob_u[u], municipio=u if ":" in u else u[:5], provincia=pi, particion=pi if part else None,
                         unidad_r012=u if self.internas else None)
                  for u in sorted(pob_u)
                  # en las islas el contrato usa la partición como campo de provincia (DDD_PARTITION)
                  for pi in [(part.get(self.secciones_de[u][0]) or part.get(u[:5])) if part else u[:2]]),
            tuple(self.largo), tuple(contacto))
        self.pob_u = pob_u
        self.u0 = {u: self.asig0[ss[0]] for u, ss in self.secciones_de.items()}
        if any(self.asig0[s] != self.u0[self.unidad[s]] for s in self.asig0):
            raise ValueError(f"{t}: el mapa vigente parte un municipio que la regla no deja partir")
        # demarcaciones por unidad (la del municipio; la sección hereda la de su municipio)
        self.pj = {u: tablas["pj"].get(u[:5]) for u in pob_u}
        self.ca = {u: tablas["ca"].get(u[:5]) for u in pob_u}
        self.area = {u: nm.grupo_area(self.secciones_de[u][0], mov[0]) for u in pob_u}
        # objetivo por circunscripción (autonómicas: provincia o isla con su cuota de escaños)
        self.circ_u = {un.id: un.provincia for un in self.problema.unidades}
        cuotas = dict(self.reglas.cuotas)
        self.obj_circ: dict[str, Fraction] = {}
        if len(cuotas) > 1:
            pc: dict[str, int] = defaultdict(int)
            for u, c in self.circ_u.items():
                pc[c] += pob_u[u]
            self.obj_circ = {c: Fraction(pc[c], n) for c, n in sorted(cuotas.items()) if n > 0}

    # ---------------------------------------------------------------- métricas baratas por estado (unidades)
    def reparar(self, asig: dict[str, str]) -> tuple[dict[str, str], list[str]]:
        """Plan válido cercano al vigente: para cada municipio con más distritos mixtos de los permitidos, pasa sus
        unidades de un distrito mixto a otro distrito del mismo municipio. Devuelve (plan, notas); plan vacío si no."""
        plan, notas = dict(asig), []
        for _ in range(20):
            inf = evaluar(self.problema, self.reglas, plan)
            if inf.valido:
                return plan, notas
            v = next((x for x in inf.violaciones if x.regla == "R-MUN-MIXTOS"), None)
            if v is None:
                notas.append(f"sin reparación para {[(x.regla, x.ambito) for x in inf.violaciones][:5]}")
                return {}, notas
            m = v.ambito
            de_m: dict[str, list[str]] = defaultdict(list)
            otros: dict[str, int] = defaultdict(int)
            for u, d in plan.items():
                (de_m[d].append(u) if u[:5] == m else otros.__setitem__(d, otros[d] + 1))
            mixtos = sorted((d for d in de_m if otros.get(d)), key=lambda d: (sum(self.pob_u[u] for u in de_m[d]), d))
            hecho = False
            for d in mixtos:
                for destino in sorted(x for x in de_m if x != d):
                    prueba = {**plan, **{u: destino for u in de_m[d]}}
                    inf2 = evaluar(self.problema, self.reglas, prueba)
                    if not any(x.regla == "R-MUN-MIXTOS" and x.ambito == m for x in inf2.violaciones) and \
                            all(x.regla == "R-MUN-MIXTOS" for x in inf2.violaciones):
                        notas.append(f"{m}: {len(de_m[d])} unidades del distrito {d} al {destino}")
                        plan, hecho = prueba, True
                        break
                    notas.append(f"{m}: {d}→{destino} no vale ({[(x.regla, x.ambito) for x in inf2.violaciones][:3]})")
                if hecho:
                    break
            if not hecho:
                return {}, notas
        return {}, notas

    def a_secciones(self, asig_u: dict[str, str]) -> dict[str, str]:
        return {s: asig_u[self.unidad[s]] for s in self.asig0}


def _buscar(x, clave: str):
    if isinstance(x, dict):
        for k, v in x.items():
            if k == clave:
                return v
            r = _buscar(v, clave)
            if r is not None:
                return r
    return None


def unidades_de(secciones, pob_m: dict[str, int], objetivo, psec: dict[str, str]) -> dict[str, str]:
    """Unidad de cada sección: el municipio entero si no puede partirse (<= objetivo), si no la propia sección; un
    municipio en dos islas (Teguise y La Graciosa) es una unidad por isla, «municipio:partición», como el contrato."""
    islas_m: dict[str, set] = defaultdict(set)
    for s, pi in psec.items():
        islas_m[s[:5]].add(pi)
    return {s: (s if pob_m[s[:5]] > objetivo else
                f"{s[:5]}:{psec[s]}" if len(islas_m.get(s[:5], ())) > 1 else s[:5]) for s in secciones}


def funciones_de(texto: str) -> tuple[str, ...]:
    """--funciones: A siempre (referencia); el resto en el orden de FUNCIONES."""
    pedidas = set(filter(None, texto.split(",")))
    if pedidas - set(FUNCIONES):
        raise ValueError(f"funciones desconocidas: {sorted(pedidas - set(FUNCIONES))}")
    return tuple(f for f in FUNCIONES if f == "A" or f in pedidas)


def parametros(a, funciones: tuple[str, ...]) -> dict:
    return {"cadenas": a.cadenas, "pasos": a.pasos, "rpj": a.rpj, "rca": a.rca, "rmov": a.rmov, "rlong": a.rlong,
            **({} if funciones == FUNCIONES else {"funciones": list(funciones)})}


def incompatible(previo: dict, a, funciones: tuple[str, ...], ent: dict) -> str:
    """--reanudar: motivo por el que un RESULTADO.json existente no vale para esta ejecución («» si vale)."""
    for nombre, antes, ahora in (("versión", previo.get("version"), VERSION), ("parámetros", previo.get("parametros"),
                                 parametros(a, funciones)), ("entorno", previo.get("entorno"), ent)):
        if antes != ahora:
            return f"{nombre} distinta ({antes} ≠ {ahora})"
    return ""


def puentes_contrato(cfg) -> set[tuple[str, str]]:
    """Todas las topology_bridges del contrato, en cualquier módulo (enclaves y exclaves)."""
    out: set[tuple[str, str]] = set()

    def ver(x):
        if isinstance(x, dict):
            for k, v in x.items():
                if k == "topology_bridges" and isinstance(v, list):
                    out.update(tuple(sorted((str(b["u"]), str(b["v"])))) for b in v
                               if isinstance(b, dict) and b.get("u") is not None and b.get("v") is not None)
                else:
                    ver(v)
        elif isinstance(x, list):
            for v in x:
                ver(v)
    ver(cfg)
    return out


def particiones(cfg: dict) -> dict:
    """Partición insular por sección (overrides) y municipio, y puentes marítimos («_puentes»), de la tabla del contrato."""
    ruta, tid = _buscar(cfg, "hard_partition_lookup"), _buscar(cfg, "hard_partition_territory_id")
    if not ruta or not tid:
        return {}
    t = json.loads((ROOT / str(ruta)).read_text(encoding="utf-8"))["territories"][str(tid)]
    out = {**t.get("municipality_to_partition", {}), **t.get("section_overrides", {})}
    out["_puentes"] = [tuple(sorted((str(b["u"]), str(b["v"])))) for b in t.get("bridges", [])]
    return out


def huella_plan(asig: dict[str, str]) -> str:
    """Independiente de las etiquetas: conjunto de distritos como conjuntos de unidades."""
    g: dict[str, list[str]] = defaultdict(list)
    for u, d in asig.items():
        g[d].append(u)
    forma = sorted("|".join(sorted(v)) for v in g.values())
    return hashlib.sha256("\n".join(forma).encode("utf-8")).hexdigest()


def _bip_mitad(subgraph, pop_col, pop_target, epsilon, *args, bip, eps, **kw):
    """Corta el par fusionado por la mitad de su población con la tolerancia real `eps` (recom recibe un epsilon
    holgado porque comprueba contra su pop_target único, que con objetivos por circunscripción no vale)."""
    total = sum(subgraph.node_data(n)[pop_col] for n in subgraph.node_indices)
    return bip(subgraph, pop_col, total / 2, eps, *args, **kw)


def arbol_ponderado(graph, region_surcharge=None, treat_unassigned_as_single_region=False, rng=None, *, recargo):
    """Kruskal con peso aleatorio [0,1) + recargo fijo de la arista (sustituye a random_spanning_tree)."""
    from gerrychain.tree.spanning_tree import _ordered_edge_ids  # noqa: PLC0415
    if not isinstance(rng, random.Random):
        rng = random.Random(rng)
    if graph.is_rx_graph():
        # mismo orden de aristas y una sola llamada a rng.random() por arista que la ruta general; los extremos y los
        # datos salen de una vez del grafo RX (sin get_edge_from_edge_id/node_data/edge_data por arista)
        rx = graph.get_rx_graph()
        extremos = rx.edge_index_map()
        get = recargo.get
        for eid in _ordered_edge_ids(graph):
            na, nb, datos = extremos[eid]
            a, b = rx[na]["uid"], rx[nb]["uid"]
            datos["random_weight"] = rng.random() + get((a, b) if a < b else (b, a), 0.0)
        return graph.minimum_spanning_tree_from_edge_weight(edge_weight_attribute_name="random_weight")
    for eid in _ordered_edge_ids(graph):
        a, b = (graph.node_data(n)["uid"] for n in graph.get_edge_from_edge_id(eid))
        graph.edge_data(eid)["random_weight"] = rng.random() + recargo.get((a, b) if a < b else (b, a), 0.0)
    return graph.minimum_spanning_tree_from_edge_weight(edge_weight_attribute_name="random_weight")


def cadena(lab: Natural, semilla: int, pasos: int, funciones: tuple[str, ...], recargo: dict | None) -> dict:
    import networkx as nx  # noqa: PLC0415
    from gerrychain import Graph, MarkovChain, Partition, updaters  # noqa: PLC0415
    from gerrychain.proposals import recom  # noqa: PLC0415
    from gerrychain.tree import bipartition_tree  # noqa: PLC0415
    g = nx.Graph()
    for u in sorted(lab.pob_u):
        g.add_node(u, population=lab.pob_u[u], district=getattr(lab, "u_ini", lab.u0)[u], uid=u)
    g.add_edges_from(sorted(lab.largo) + sorted(lab.problema.puentes))
    graph = Graph.from_networkx(g)
    ini = Partition(graph, assignment="district", updaters={"population": updaters.Tally("population", alias="population")})
    # Reelección de par como producción (m05_gerrychain_engine): si una pareja no admite corte equilibrado (p. ej.
    # un distrito vigente fuera de tolerancia), se prueba otra en lugar de abortar la cadena.
    bip = partial(bipartition_tree, allow_pair_reselection=True, max_attempts=1000)
    if recargo is not None:
        bip = partial(bipartition_tree, allow_pair_reselection=True, max_attempts=1000,
                      spanning_tree_fn=partial(arbol_ponderado, recargo=recargo))
    eps = float(lab.tol / lab.objetivo)
    # con objetivos por circunscripción se corta por la mitad de la población del par; si el par mezcla
    # circunscripciones, el plan resultante lo rechaza `nucleo` (R-CUOTA / provincia única)
    if lab.obj_circ:
        bip, eps = partial(_bip_mitad, bip=bip, eps=eps), 1e6
    prop = partial(recom, pop_col="population", pop_target=float(lab.objetivo), epsilon=eps,
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
    funciones = funciones_de(a.funciones)
    libres = "B" in funciones  # sin B no se recorren las cadenas libres: A queda como el mapa vigente
    ponderadas = tuple((f, k) for f, k in (("C", "B"), ("D5", "D5"), ("D8", "D8")) if f in funciones)
    t0 = time.perf_counter()
    lab = Laboratorio(t, Path(a.seccionado_dir), tablas, mov)
    t_ent = time.perf_counter() - t0
    lab.u_ini, reparacion = lab.u0, []
    if not lab.valido(lab.u0):  # D-66: A sigue siendo el vigente; C/D8 solo entre mapas válidos
        lab.u_ini, reparacion = lab.reparar(lab.u0)
        if not lab.u_ini:
            raise ValueError(f"{t}: el mapa vigente no es válido y no se repara: {reparacion[-3:]}")
    desc = descripcion(lab.cfg, t, a.cadenas)
    rec = lab.recargos(a.rpj, a.rca, a.rmov, a.rlong)
    cand = {f: [("vigente", None, lab.clave(lab.u0, f), lab.u0)] if f == "A" or lab.u_ini is lab.u0 else
            [("vigente-reparado", None, lab.clave(lab.u_ini, f), lab.u_ini)] for f in funciones}
    cadenas = {"libre": [], "ponderado": []}
    for s in desc["semillas"]:
        if libres:
            r = cadena(lab, s, a.pasos, ("A", "B"), None)
            cadenas["libre"].append({k: v for k, v in r.items() if k != "mejor"})
            for f in "AB":
                if f in r["mejor"]:
                    cand[f].append((f"libre-{s}", s, *r["mejor"][f]))
        if not ponderadas:
            continue
        r = cadena(lab, s, a.pasos, tuple(dict.fromkeys(k for _, k in ponderadas)), rec)
        cadenas["ponderado"].append({k: v for k, v in r.items() if k != "mejor"})
        for f, k in ponderadas:
            if k in r["mejor"]:
                cand[f].append((f"ponderado-{s}", s, *r["mejor"][k]))
        print(f"  {t} semilla {s}: ok", flush=True)
    out = Path(a.out) / t
    out.mkdir(parents=True, exist_ok=True)
    ganadores = {}
    for f in funciones:
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
        dv = lab.desvios(asig)
        tr = lab.tol / lab.objetivo
        ganadores[f] = {"candidato": cid, "semilla": sem, "clave": _j(k), "valido": inf.valido,
                        "fuera_tolerancia": (sorted(d for d, (p, o) in dv.items() if abs(p - o) / o > tr) if lab.obj_circ
                                             else inf.metricas["fuera_tolerancia"]),
                        "desvio_max": (float(max(abs(p - o) / o for p, o in dv.values())) if lab.obj_circ
                                       else inf.metricas["max_desviacion_ratio"]),
                        "suma_desvio_personas": float(sum(abs(p - o) for p, o in dv.values())),
                        "max_desvio_personas": float(max(abs(p - o) for p, o in dv.values())),
                        "indicadores": ind,
                        "sha256_csv": hashlib.sha256((out / f"{t}_{f}.csv").read_bytes()).hexdigest()}
    res = {"territorio": t, "version": VERSION, "topes": TOPES, "unidades": len(lab.pob_u), "aristas": len(lab.largo),
           **({"vigente_valido": False, "reparacion": reparacion} if lab.u_ini is not lab.u0 else {}),
           **({"unidades_internas": "seccion por encima de atomicity_ratio x objetivo"} if lab.internas else {}),
           "puentes_contacto": len(lab.problema.puentes), "objetivo": float(lab.objetivo), "tolerancia": float(lab.tol),
           **({"objetivos_circunscripcion": {c: float(o) for c, o in lab.obj_circ.items()}} if lab.obj_circ else {}),
           "parametros": parametros(a, funciones),
           "semilla_publica": desc, "huella_reglas": lab.reglas.huella(), "ganadores": ganadores,
           "candidatos": {f: [[c[0], _j(c[2])] for c in cand[f]] for f in funciones},
           "cadenas": cadenas, "entorno": entorno(), "tiempos_s": {"entrada": t_ent, "total": time.perf_counter() - t0}}

    def _huella(fs) -> str:
        return hashlib.sha256(json.dumps(
            {"g": {f: [ganadores[f]["candidato"], ganadores[f]["sha256_csv"]] for f in fs},
             "c": {f: res["candidatos"][f] for f in fs}, "p": res["parametros"], "r": res["huella_reglas"]},
            sort_keys=True).encode()).hexdigest()
    res["huella"] = _huella([f for f in "ABC" if f in funciones])  # con las cinco, la de 1.0.0
    res["huella_d"] = _huella(funciones)
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
    p.add_argument("--funciones", default=",".join(FUNCIONES))
    p.add_argument("--reanudar", action="store_true")
    p.add_argument("territorios", nargs="+")
    a = p.parse_args(argv)
    if os.environ.get("PYTHONHASHSEED") != "0":
        print("aviso: sin PYTHONHASHSEED=0 la reproducibilidad bit a bit no está garantizada", file=sys.stderr)
    tablas, mov = nm.tablas_municipio(), nm.movilidad()
    rc = 0
    for t in a.territorios:
        hecho = Path(a.out) / t / "RESULTADO.json"
        if a.reanudar and hecho.exists():
            motivo = incompatible(json.loads(hecho.read_text(encoding="utf-8")), a, funciones_de(a.funciones), entorno())
            if motivo:  # no se mezcla con un resultado de otra versión, parámetros o entorno; tampoco se sobrescribe
                print(f"{t}: ERROR --reanudar rechaza el RESULTADO.json existente: {motivo}", flush=True)
                rc = 1
            else:
                print(f"{t}: ya hecho (reanudar)", flush=True)
            continue
        try:
            r = correr(t, a, tablas, mov)
            print(f"{t}: huella {r['huella'][:12]} en {r['tiempos_s']['total']:.0f} s", flush=True)
        except Exception as e:  # noqa: BLE001
            print(f"{t}: ERROR {type(e).__name__}: {e}", flush=True)
            rc = 1
    return rc


if __name__ == "__main__":
    sys.exit(main())
