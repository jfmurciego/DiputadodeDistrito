#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PROYECTO: Diputado de Distrito
COMPONENTE: estudio T-465/T-466 (piloto del banco) — GerryChain puro con las reglas del núcleo
VERSIÓN: 1.0.0
NOMBRE DE VERSIÓN: GerryChain puro · ReCom sobre átomos, elegido con D8
FECHA: 2026-11-26
ESTADO: estudio (no lo importa el motor ni la producción; solo lee ddd_motor2, certificador_exacto y optimo_d8)
CAMBIOS: fichero nuevo.
MOTIVO: piloto del banco (T-465/T-466): medir GerryChain sin el generador «ponderado» ni recargos frente a Deslinde y
  el óptimo exacto (T-296), con el mismo problema, los mismos átomos y la misma clave D8.
ANTERIOR: ninguna (fichero nuevo)
QUÉ HACE:
  Problema = el de optimo_d8.cargar (unidades de la composición M06 del canónico, reglas del contrato, clave D8 oficial).
  Átomos = certificador_exacto.construir_atomos (los mismos que el exacto). Semilla = recursive_tree_part sobre los
  átomos con el objetivo y epsilon simétrico min(objetivo−suelo, techo−objetivo)/objetivo. Cadena ReCom
  (district_pairs, allow_pair_reselection) con evaluar(...).valido como restricción dura; aceptación siempre.
  Por cada estado distinto se calcula la clave D8 oficial (Natural.clave) y se guarda la mejor y el paso en que aparece.
  Semillas públicas 1..N; presupuesto en pasos (los cortes intermedios se informan sin repetir la cadena).
SALIDA: JSON por territorio en --salida: por semilla, mejor clave D8 por corte, tasa de autobucles, CPU (process_time).
USO: PYTHONHASHSEED=0 python docs/ESTUDIOS/T465_BANCO_PILOTO/gerrychain_puro.py --out /ruta/bateria \
       --semillas 1 2 3 --pasos 100000 --salida /ruta/gc nac09
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from fractions import Fraction
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "herramientas"))
sys.path.insert(0, str(ROOT / "docs" / "ESTUDIOS" / "T296_OPTIMO_D8"))

import optimo_d8 as od  # noqa: E402
from certificador_exacto import construir_atomos  # noqa: E402
from ddd_motor2.reglas import evaluar  # noqa: E402

VERSION = "1.0.0"
CORTES = (100, 1000, 10000, 100000)
INTENTOS = 200  # semillas por árbol hasta la primera válida en el núcleo


def correr(t: str, out: Path, semillas: list[int], pasos: int) -> dict:
    import networkx as nx
    from functools import partial
    from gerrychain import Graph, MarkovChain, Partition, updaters
    from gerrychain.accept import always_accept
    from gerrychain.proposals import recom
    from gerrychain.partition import recursive_tree_part
    from gerrychain.tree import bipartition_tree

    t0 = time.process_time()
    comp, reglas, esp = od.cargar(t, out)
    e = esp["canonico"]
    problema, nat = e["problema"], e["nat"]
    atomos, aristas = construir_atomos(problema, reglas, {})
    obj, suelo, techo, tol = reglas.limites(problema.poblacion_total)
    eps = float(min(obj - suelo, techo - obj) / obj)
    nxg = nx.Graph()
    for i, a in enumerate(atomos):
        nxg.add_node(i, population=int(a["pop"]))
    nxg.add_edges_from((int(u), int(v)) for u, v in aristas)
    g = Graph.from_networkx(nxg)
    K = reglas.k

    def a_plan(asig) -> dict[str, str]:
        return {u: f"D{int(asig[i])}" for i, a in enumerate(atomos) for u in a["secs"]}

    def valido(part) -> bool:
        return evaluar(problema, reglas, a_plan(part.assignment)).valido

    gan = od.clave_oficial(esp["ganador"]["nat"], esp["ganador"]["plan"])
    res = {"territorio": t, "version": VERSION, "k": K, "atomos": len(atomos), "aristas": len(aristas),
           "epsilon": eps, "huella_reglas": reglas.huella(), "ganador_deslinde": od.legible(gan), "semillas": []}
    t_carga = time.process_time() - t0
    res["cpu_carga_s"] = round(t_carga, 2)
    for s in semillas:
        ts = time.process_time()
        r = {"semilla": s}
        ini, intentos, motivos = None, 0, set()
        for intentos in range(1, INTENTOS + 1):
            try:
                crudo = recursive_tree_part(g, range(K), float(obj), "population", eps, node_repeats=0,
                                            bipartition_tree_fn=partial(bipartition_tree, max_attempts=10000,
                                                                        allow_pair_reselection=True),
                                            rng=s * 1000 + intentos)
            except Exception as exc:  # noqa: BLE001  BalanceError / RuntimeError
                motivos.add(type(exc).__name__)
                continue
            cand = Partition(g, assignment=crudo,
                             updaters={"population": updaters.Tally("population", alias="population")})
            rep = evaluar(problema, reglas, a_plan(cand.assignment))
            if rep.valido:
                ini = cand
                break
            motivos |= {str(getattr(v, "regla", v)) for v in getattr(rep, "violaciones", [])}
        r["intentos_semilla"] = intentos
        r["motivos_semillas_rechazadas"] = sorted(motivos)[:8]
        if ini is None:
            r.update(estado="SIN_SEMILLA_VALIDA", cpu_s=round(time.process_time() - ts, 2))
            res["semillas"].append(r)
            continue
        prop = partial(recom, pop_col="population", pop_target=float(obj), epsilon=eps, node_repeats=0,
                       bipartition_tree_fn=partial(bipartition_tree, max_attempts=10000, allow_pair_reselection=True))
        chain = MarkovChain(proposal_fn=prop, constraints=[valido], acceptance_fn=always_accept, initial_partition=ini,
                            total_steps=pasos, rng=s)
        mejor, paso_mejor, autobucles, prev, vistos = None, 0, 0, None, 0
        cortes = {}
        try:
            for n, part in enumerate(chain, start=1):
                firma = tuple(part.assignment[i] for i in range(len(atomos)))
                if firma == prev:
                    autobucles += 1
                else:
                    vistos += 1
                    cl = nat.clave(a_plan(part.assignment), "D8")
                    if mejor is None or cl < mejor:
                        mejor, paso_mejor = cl, n
                prev = firma
                if n in CORTES:
                    cortes[str(n)] = {"clave_d8": od.legible(mejor), "cpu_s": round(time.process_time() - ts, 2)}
            r["estado"] = "OK"
        except Exception as exc:  # noqa: BLE001
            r.update(estado="CADENA_CORTADA", error=f"{type(exc).__name__}: {str(exc)[:160]}")
        r.update(pasos=pasos, estados_distintos=vistos, autobucles=autobucles, paso_mejor=paso_mejor,
                 mejor=od.legible(mejor) if mejor else None, cortes=cortes,
                 hueco_frente_a_deslinde=od.comparar(mejor, gan) if mejor else None,
                 cpu_s=round(time.process_time() - ts, 2))
        res["semillas"].append(r)
        print(json.dumps({"t": t, "s": s, "estado": r["estado"], "cpu_s": r["cpu_s"],
                          "mejor": r.get("mejor")}, ensure_ascii=False), flush=True)
    res["cpu_total_s"] = round(time.process_time() - t0, 2)
    return res


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--semillas", type=int, nargs="+", default=list(range(1, 11)), help="semillas públicas (1..10)")
    ap.add_argument("--pasos", type=int, default=10000)
    ap.add_argument("--salida", type=Path, required=True)
    ap.add_argument("territorios", nargs="+")
    a = ap.parse_args(argv)
    a.salida.mkdir(parents=True, exist_ok=True)
    for t in a.territorios:
        r = correr(t, a.out, a.semillas, a.pasos)
        suf = "" if a.semillas == list(range(1, 11)) else "_s" + "-".join(map(str, a.semillas))
        (a.salida / f"{t}{suf}.json").write_text(json.dumps(r, ensure_ascii=False, indent=1, default=str) + "\n",
                                            encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
