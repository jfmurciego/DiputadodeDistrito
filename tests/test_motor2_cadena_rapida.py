#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""T-262: las cadenas ReCom más baratas dan lo mismo bit a bit.
- reglas.evaluar.valido (Contexto reutilizado, sin métricas) == evaluar(...).valido en planes aleatorios, y
  Natural.valido rehace el Contexto si cambia el problema;
- Contexto.rango_municipal memorizado == la fórmula;
- arbol_ponderado sobre RX (naturalidad_competicion 1.6.0) == el bucle por arista de la 1.5.0: mismos pesos, mismo
  árbol y el RNG en el mismo estado (requiere gerrychain; sin él, se salta)."""
from __future__ import annotations

import math
import random
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests"))

from ddd_motor2.naturalidad_clave import Natural  # noqa: E402
from ddd_motor2.reglas import Criterio, Reglas, evaluar  # noqa: E402
from ddd_motor2.reglas.evaluar import Contexto, valido  # noqa: E402
from test_motor2_reglas import _contrato_aleatorio, _rejilla  # noqa: E402

try:
    import gerrychain  # noqa: F401
    import networkx as nx
    HAY_GC = True
except ImportError:  # pragma: no cover
    HAY_GC = False


class ValidoSinMetricas(unittest.TestCase):
    def test_valido_igual_que_evaluar(self):
        rng = random.Random(262)
        n_validos = n_total = 0
        for caso in range(120):
            p = _rejilla(rng, filas=rng.choice([2, 3]), cols=rng.choice([3, 4]), nucleos=caso % 3 == 0)
            k = rng.choice([2, 3, 4])
            r = Reglas.desde_contrato(_contrato_aleatorio(rng, k, permisivo=caso % 2 == 0),
                                      Criterio(tolerancia=rng.choice(["metrica", "dura"])))
            ctx = Contexto.de(p, r)
            ids = [u.id for u in p.unidades]
            for _ in range(25):
                plan = {u: str(rng.randint(1, k)) for u in ids}
                if rng.random() < 0.1:
                    plan.pop(ids[0])
                esperado = evaluar(p, r, plan).valido
                self.assertEqual(valido(p, r, plan, ctx), esperado)
                self.assertEqual(valido(p, r, plan), esperado)
                n_validos += esperado
                n_total += 1
        self.assertGreater(n_validos, 0)
        self.assertLess(n_validos, n_total)

    def test_natural_rehace_el_contexto_si_cambia_el_problema(self):
        rng = random.Random(7)
        r = Reglas.desde_contrato(_contrato_aleatorio(rng, 2, permisivo=True), Criterio())
        nat = Natural()
        nat.reglas = r
        for _ in range(10):
            nat.problema = _rejilla(rng)
            plan = {u.id: str(rng.randint(1, 2)) for u in nat.problema.unidades}
            self.assertEqual(nat.valido(plan), evaluar(nat.problema, r, plan).valido)
            self.assertIs(nat._ctx[0], nat.problema)

    def test_rango_municipal_memorizado(self):
        rng = random.Random(3)
        p = _rejilla(rng)
        ctx = Contexto.de(p, Reglas.desde_contrato(_contrato_aleatorio(rng, 2), Criterio()))
        for x in [0, -1, 1, 5, 999, 10**6, 5, 0]:
            esperado = (1, 1) if x <= 0 else (max(1, math.ceil(x / ctx.techo)), max(1, math.ceil(x / ctx.objetivo)))
            self.assertEqual(ctx.rango_municipal(x), esperado)
            self.assertEqual(ctx.rango_municipal(x), esperado)


def _arbol_v150(graph, rng, recargo):
    """naturalidad_competicion 1.5.0 (legacy): un peso por arista con get_edge_from_edge_id/node_data/edge_data."""
    from gerrychain.tree.spanning_tree import _ordered_edge_ids
    for eid in _ordered_edge_ids(graph):
        a, b = (graph.node_data(n)["uid"] for n in graph.get_edge_from_edge_id(eid))
        graph.edge_data(eid)["random_weight"] = rng.random() + recargo.get((a, b) if a < b else (b, a), 0.0)
    return graph.minimum_spanning_tree_from_edge_weight(edge_weight_attribute_name="random_weight")


def _grafo(rng, n):
    from gerrychain import Graph
    g = nx.connected_watts_strogatz_graph(n, 4, 0.3, seed=rng.randint(0, 10**6))
    h = nx.Graph()
    nombre = {i: f"u{i:03d}" for i in g.nodes}
    for i in sorted(g.nodes):
        h.add_node(nombre[i], population=rng.randint(1, 100), district="1", uid=nombre[i])
    h.add_edges_from(sorted(tuple(sorted((nombre[a], nombre[b]))) for a, b in g.edges))
    recargo = {e: rng.choice([0.0, 0.2, 0.5, 1.3]) for e in sorted(h.edges) if rng.random() < 0.7}
    return Graph.from_networkx(h), recargo


@unittest.skipUnless(HAY_GC, "requiere gerrychain")
class ArbolPonderadoRX(unittest.TestCase):
    def test_mismos_pesos_arbol_y_rng(self):
        from gerrychain.graph import FrozenGraph
        from ddd_motor2.naturalidad_competicion import arbol_ponderado
        rng = random.Random(262)
        for caso in range(30):
            n = rng.randint(6, 40)
            semilla = rng.randint(0, 10**9)
            arboles, pesos, estados = [], [], []
            for impl in ("nueva", "v150"):
                g, recargo = _grafo(random.Random(caso), n)
                g = FrozenGraph(g)
                nodos = sorted(g.node_indices)
                sub = g.subgraph(nodos[: max(3, len(nodos) * 2 // 3)]) if caso % 2 else g
                r = random.Random(semilla)
                t = (arbol_ponderado(sub, rng=r, recargo=recargo) if impl == "nueva" else _arbol_v150(sub, r, recargo))
                uid = {i: sub.node_data(i)["uid"] for i in sub.node_indices}
                arboles.append(sorted(tuple(sorted((t.node_data(a)["uid"], t.node_data(b)["uid"]))) for a, b in t.edges))
                pesos.append(sorted((tuple(sorted((uid[a], uid[b]))), sub.edge_data(sub.get_edge_id_from_edge((a, b)))
                                     ["random_weight"]) for a, b in sub.edges))
                estados.append(r.getstate())
            self.assertEqual(pesos[0], pesos[1])
            self.assertEqual(arboles[0], arboles[1])
            self.assertEqual(estados[0], estados[1])


if __name__ == "__main__":
    unittest.main()
