#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PROYECTO: Diputado de Distrito
COMPONENTE: Deslinde — cadena ReCom ponderado de GerryChain (las «10 cadenas» de Deslinde 1.0)
VERSIÓN: 1.0.0
NOMBRE DE VERSIÓN: Deslinde 1.0.0 · cadena ReCom ponderado
FECHA: 2026-11-14
ESTADO: candidato (paquete Deslinde, T-257)
CAMBIOS: 1.0.0 — fichero nuevo (T-257, D-88): huella_plan, _bip_mitad, arbol_ponderado y cadena salen sin cambios de
  ddd_motor2/naturalidad_competicion.py 1.6.1 (el laboratorio los importa de aquí). Mismo RNG y mismos planes.
MOTIVO: T-257: paquete independiente con fuente única.
QUÉ HACE: cadena(lab, semilla, pasos, funciones, recargo) — ReCom de GerryChain 1.0 sobre el grafo de unidades de
  `lab` (Natural): árbol de expansión mínimo con peso aleatorio [0,1) + recargo fijo por arista (partido judicial,
  comarca agraria, área de movilidad, frontera corta), restricción en cada paso = núcleo completo (lab.valido);
  devuelve el mejor estado visto según cada función. Dependencias: gerrychain 1.0.0 y networkx (importados en diferido).
ANTERIOR: ninguna (fichero nuevo)
"""
from __future__ import annotations

import hashlib
import random
import time
from collections import defaultdict
from functools import partial

from .naturalidad_clave import Natural


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
