#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Certificador exacto (T-136): programación entera con contigüidad para una circunscripción.

PROYECTO: Diputado de Distrito
VERSIÓN: 1.4.0
NOMBRE DE VERSIÓN: Certificador exacto · enumeración con la regla de calidad
FECHA: 2026-11-10
ESTADO: candidato (diagnóstico; no genera productos ni toca el motor)
CAMBIOS: 1.4.0 — enumeración: cada plan enumerado se ordena con la regla de calidad vigente (ddd_motor2/calidad.py, la de la
  competición; la huella de desempate es la de la partición en SECCIONES, comparable entre ficheros aunque cambie la
  numeración de unidades entre M04 y M06) y se informa del mejor («mejor_por_calidad»), de los empates y de si
  cada referencia es ese plan. Solo con ENUMERADO (búsqueda completa) el mejor es el óptimo exacto.
  1.3.0 — R-NUCLEO (T-175): las secciones leen district_id y ddd_closed_urban; el adaptador de núcleos desde
  las unidades (ddd_motor2.adaptadores.nucleos_desde_unidades, por unidad M04: cerrada si todas sus secciones lo son)
  marca Unidad.nucleo_cerrado. En el modelo, cada núcleo es un solo grupo de átomos y su distrito no admite otros
  átomos; los superátomos no mezclan núcleo y resto. La relajación fluida lo ignora (sigue siendo cota válida).
  Sin ddd_closed_urban en la entrada (p. ej. M01) no hay núcleos y se avisa. --sin-nucleos para comparar.
  1.2.0 — modelo ligero (T-164, D-48): --modelo ligero da dos cotas que no exigen resolver el modelo completo.
  Cota superior: agrega átomos contiguos en superátomos (población <= grano × objetivo, dentro de un mismo distrito de
  la pista si la hay) y resuelve ese modelo restringido; sus planes son válidos en el modelo completo (se juzgan con
  el núcleo) y, con pista, el plan de la pista sigue siendo factible, así que el óptimo restringido no la empeora.
  Cota inferior: relajación fluida sin contigüidad a nivel de clave R012 (las claves divisibles reparten población
  entera libre entre sus distritos; las indivisibles son un objeto entero); todo plan válido es solución de la
  relajación, así que su cota es válida y su infactibilidad prueba la del problema. Si ambas coinciden, ÓPTIMO
  certificado; si no, hueco absoluto y relativo.
  1.1.0 — las reglas salen del núcleo ddd_motor2.reglas (Reglas.desde_contrato, limites() exactos, Criterio,
  evaluar()); se quitan las reglas propias. Las secciones se leen del M04 (o M05/M06), con provincia, municipio y
  partición de los campos del contrato (DDD_PARTITION y DDD_MUNICIPALITY_PARTITION en las islas), no del CUSEC.
  La atomicidad de las unidades M04 se aplica con unión-búsqueda (una unidad puede abarcar varios municipios).
  Exención por partición, max_mixed y tolerancia según el Criterio. Solo contigüidad por árbol (flujo y cortes se
  quitan: más lentos en el estudio 1.0.0).
MOTIVO: 1.4.0 — que el certificador elija entre los planes enumerados con la misma regla que el motor nuevo.
  1.3.0 — R-NUCLEO no se aplicaba: faltaba el adaptador de núcleos desde las unidades de partición.
  1.2.0 — Madrid (K=59, 3.603 átomos) no resuelve en el modelo monolítico (T-136); hace falta un modelo que
  escale y, donde el exacto no llegue, una cota de calidad. 1.1.0 — fallos F1 (Canarias: infactibilidad falsa por leer la provincia del M01, sin DDD_PARTITION ni exenciones por
  partición) y F2 (Cádiz: unidades M04 partidas) que vio T-132; y acuerdo con T-160 de usar el núcleo único.
ANTERIOR: legacy/herramientas/certificador_exacto_v1.3.0_20261110.py
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
       [--pista <csv>] [--modelo exacto|ligero] [--grano 0.25] [--techo-ratio 1.15] [--tiempo 600] [--hilos 4] [--salida <json>] [--asignacion-csv <csv>]
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
from ddd_motor2.adaptadores import VERDADEROS, con_nucleos as con_nucleos_de, nucleos_desde_unidades  # noqa: E402
from ddd_motor2.calidad import legible, metricas  # noqa: E402
from ddd_motor2.reglas import Criterio, ErrorDatos, Problema, Reglas, Unidad, evaluar  # noqa: E402

VERSION = "1.4.0"


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


def leer_secciones(path: str, cfg: dict, criterio: Criterio, con_unidades: bool = True, con_nucleos: bool = True):
    """Unidades del núcleo (una por sección) y unidad M04 de cada sección (ddd_unit_id, si se pide). Con `con_nucleos`
    y las columnas district_id y ddd_closed_urban, las secciones de cada núcleo cerrado llevan nucleo_cerrado."""
    from ddd_core.m04_seed_engine_v7411 import load_geo  # lee ddd_unit_id escalar aunque OGR lo guarde como lista

    c = campos(cfg)
    g = load_geo(path)
    filas = g.drop(columns=[x for x in ("geometry",) if x in g.columns]).to_dict("records")
    unidades, unidad_m04, distrito_ref, cerrada_sec = [], {}, {}, {}
    hay_nucleos = con_nucleos and "ddd_closed_urban" in g.columns and "district_id" in g.columns
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
        if hay_nucleos and not _vacio(r.get("district_id")):
            distrito_ref[sid] = str(r["district_id"])
            cerrada_sec[sid] = str(r.get("ddd_closed_urban")).strip().lower() in VERDADEROS
    if hay_nucleos:
        unidades = list(con_nucleos_de(unidades, nucleos_de_secciones(distrito_ref, cerrada_sec, unidad_m04)))
    return unidades, unidad_m04


def nucleos_de_secciones(distrito_ref: dict[str, str], cerrada: dict[str, bool],
                         unidad_m04: dict[str, str]) -> dict[str, str]:
    """{sección: núcleo}: el adaptador del núcleo sobre las unidades de partición (unidad M04, o la sección si no
    tiene). Una unidad es cerrada si todas sus secciones lo son; su distrito de referencia ha de ser único."""
    dist_u: dict = defaultdict(set)
    cerr_u: dict = defaultdict(lambda: True)
    for s, d in distrito_ref.items():
        u = unidad_m04.get(s, s)
        dist_u[u].add(d)
        cerr_u[u] = cerr_u[u] and bool(cerrada.get(s))
    partidas = sorted(u for u, ds in dist_u.items() if len(ds) > 1)
    if partidas:
        raise ErrorDatos(f"unidades M04 en varios distritos de referencia: {len(partidas)} (p. ej. {partidas[0]})")
    nuc_u = nucleos_desde_unidades({u: next(iter(ds)) for u, ds in dist_u.items()}, dict(cerr_u))
    return {s: nuc_u[unidad_m04.get(s, s)] for s in distrito_ref if unidad_m04.get(s, s) in nuc_u}


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
    if reglas.nucleos_cerrados:  # R-NUCLEO: todo el núcleo en un mismo distrito (y solo él: en resolver)
        por_n: dict = defaultdict(list)
        for u in problema.unidades:
            if u.nucleo_cerrado is not None:
                por_n[u.nucleo_cerrado].append(u.id)
        for ids in por_n.values():
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
                           "muns": set().union(*(u.municipios() for u in us)),
                           "nucleos": ({u.nucleo_cerrado for u in us} if reglas.nucleos_cerrados else {None})})
    aristas = sorted({tuple(sorted((atomo_de[a], atomo_de[b]))) for a, vs in adj.items() for b in vs
                      if atomo_de[a] != atomo_de[b]})
    return atomos, aristas


# --------------------------------------------------------------------------- modelo
def resolver(problema: Problema, reglas: Reglas, unidad_m04: dict[str, str] | None = None, *, tiempo: float,
             hilos: int, objetivo: str = "factibilidad", pista: dict | None = None,
             cota_desviacion: float | None = None, grano: float | None = None) -> dict:
    """Modelo completo; con `grano`, modelo restringido de superátomos (cota superior: sus planes son válidos, pero su
    infactibilidad no prueba nada)."""
    from ortools.sat.python import cp_model

    t0 = time.time()
    unidad_m04 = unidad_m04 or {}
    atomos, aristas = construir_atomos(problema, reglas, unidad_m04)
    obj, suelo, techo, tol = reglas.limites(problema.poblacion_total)
    atomos_completos = len(atomos)
    if grano:
        atomos, aristas = agregar_atomos(atomos, aristas, Fraction(str(grano)) * obj, pista)
    n, K = len(atomos), reglas.k
    crit = reglas.criterio
    base = {"atomos": n, "atomos_modelo_completo": atomos_completos, "restringido": bool(grano), "aristas_atomos": len(aristas), "secciones": len(problema.unidades), "k": K,
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
    # R-NUCLEO: el distrito de un núcleo cerrado no admite átomos de fuera del núcleo (todo el núcleo ya va junto).
    nucleos = sorted({nu for a in atomos for nu in a.get("nucleos", {None}) if nu is not None})
    for nu in nucleos:
        ancla = min(i for i, a in enumerate(atomos) if nu in a["nucleos"])
        fuera = [j for j, a in enumerate(atomos) if a.get("nucleos", {None}) != {nu}]
        for k in range(K):
            if (ancla, k) in x:
                xs = [x[j, k] for j in fuera if (j, k) in x]
                if xs:
                    m.Add(sum(xs) == 0).OnlyEnforceIf(x[ancla, k])
    base["nucleos_cerrados"] = len(nucleos)
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
    if grano and res["estado"] == "OPTIMO":
        res["estado"] = "OPTIMO_RESTRINGIDO"
    if nombre == "INFEASIBLE" and grano:
        res["estado"] = "INFACTIBLE_RESTRINGIDO"  # sin valor de prueba: la agregación quita planes
    elif nombre == "INFEASIBLE":
        res["prueba"] = "CP-SAT: modelo infactible (búsqueda completa) con las reglas del núcleo"
    if nombre in ("OPTIMAL", "FEASIBLE"):
        res["asignacion"] = a_secciones([next(k for k in range(K) if (i, k) in x and sol.Value(x[i, k]))
                                         for i in range(n)])
        if objetivo in ("minimax", "techo"):
            res["valor_objetivo"] = round(sol.ObjectiveValue(), 1)
            res["cota_inferior_objetivo"] = round(sol.BestObjectiveBound(), 1)
            if objetivo == "techo":
                res["techo_minimo_ratio"] = round(sol.ObjectiveValue() / float(obj), 5)
    elif nombre == "UNKNOWN" and objetivo in ("minimax", "techo"):
        res["cota_inferior_objetivo"] = round(sol.BestObjectiveBound(), 1)  # cota probada aunque no termine
    return res


# --------------------------------------------------------------------------- modelo ligero (T-164)
def agregar_atomos(atomos: list[dict], aristas: list[tuple[int, int]], tope, pista: dict | None = None):
    """Superátomos: une átomos contiguos de la misma provincia (y del mismo distrito de la pista, si la hay) mientras la
    población no pase de `tope`. Restricción del modelo: cada superátomo es conexo, así que sus planes son planes del
    modelo completo; las igualdades de grupo se conservan uniendo los superátomos que comparten grupo."""
    vec: dict = defaultdict(list)
    for a, b in aristas:
        vec[a].append(b)
        vec[b].append(a)

    def etiqueta(i):
        a = atomos[i]
        return (tuple(sorted(map(str, a["provs"]))), pista.get(a["secs"][0]) if pista else None,
                tuple(sorted(map(str, a.get("nucleos", {None})))))

    sup_de, grupos = {}, []
    for i in range(len(atomos)):  # orden de índice: determinista
        if i in sup_de:
            continue
        g, pob, et, cola = [i], atomos[i]["pop"], etiqueta(i), [i]
        sup_de[i] = len(grupos)
        while cola:
            u = cola.pop(0)
            for v in sorted(vec[u]):
                if v not in sup_de and etiqueta(v) == et and pob + atomos[v]["pop"] <= tope:
                    sup_de[v] = len(grupos)
                    g.append(v)
                    pob += atomos[v]["pop"]
                    cola.append(v)
        grupos.append(g)
    # Superátomos que comparten grupo original van al mismo distrito: grupo nuevo = componente de esa relación.
    padre = list(range(len(grupos)))

    def raiz(a):
        while padre[a] != a:
            padre[a] = padre[padre[a]]
            a = padre[a]
        return a

    primero: dict = {}
    for i, a in enumerate(atomos):
        s = sup_de[i]
        if a["grupo"] in primero:
            ra, rb = raiz(primero[a["grupo"]]), raiz(s)
            padre[max(ra, rb)] = min(ra, rb)
        else:
            primero[a["grupo"]] = s
    nuevos = []
    for j, g in enumerate(grupos):
        claves: dict = defaultdict(int)
        for i in g:
            for c, p in atomos[i]["claves"].items():
                claves[c] += p
        nuevos.append({"secs": sorted(s for i in g for s in atomos[i]["secs"]),
                       "pop": sum(atomos[i]["pop"] for i in g), "grupo": f"S{raiz(j)}", "claves": dict(claves),
                       "provs": set().union(*(atomos[i]["provs"] for i in g)),
                       "parts": set().union(*(atomos[i]["parts"] for i in g)),
                       "muns": set().union(*(atomos[i]["muns"] for i in g)),
                       "nucleos": set().union(*(atomos[i].get("nucleos", {None}) for i in g))})
    # Orden por primera sección (la ruptura de simetría usa el índice); aristas entre superátomos distintos.
    orden = sorted(range(len(nuevos)), key=lambda j: nuevos[j]["secs"][0])
    nuevo_idx = {j: t for t, j in enumerate(orden)}
    nuevas_aristas = sorted({tuple(sorted((nuevo_idx[sup_de[a]], nuevo_idx[sup_de[b]]))) for a, b in aristas
                             if sup_de[a] != sup_de[b]})
    return [nuevos[j] for j in orden], nuevas_aristas


def cota_relajada(problema: Problema, reglas: Reglas, unidad_m04: dict[str, str] | None = None, *, tiempo: float,
                  hilos: int, objetivo: str = "factibilidad", pista: dict | None = None,
                  fijar_pista: bool = False) -> dict:
    """Relajación fluida sin contigüidad. Objetos: claves R012 (o átomos si no hay disciplina municipal). Una clave
    indivisible (ceil(P/objetivo)=1) va entera a un distrito; una divisible reparte su población en enteros libres
    entre lo..hi distritos (hi <= sus grupos indivisibles; cada trozo >= su menor pieza; el resto de la granularidad
    se ignora). Se conservan K, cuotas, suelo, techo,
    tolerancia, exenciones (permisivas: basta una clave exenta) y la regla de mixtos. Todo plan válido proyecta en una
    solución, así que la cota es válida para minimax y techo, y INFACTIBLE prueba que no hay plan. La pista guía la
    búsqueda; con fijar_pista se impone (comprobación de que la relajación acepta un plan válido)."""
    from ortools.sat.python import cp_model

    t0 = time.time()
    atomos, _ = construir_atomos(problema, reglas, unidad_m04 or {})
    K = reglas.k
    obj, suelo, techo, tol = reglas.limites(problema.poblacion_total)
    crit = reglas.criterio
    objs: dict = {}  # clave -> {pop, provs, parts, muns, divisible, lo, hi}
    if reglas.disciplina_municipal:
        piezas: dict = defaultdict(lambda: defaultdict(int))  # clave -> grupo -> población de la clave en el grupo
        for a in atomos:
            for c, p in a["claves"].items():
                o = objs.setdefault(("c", c), {"pop": 0, "provs": set(), "parts": set(), "muns": set()})
                o["pop"] += p
                o["provs"] |= a["provs"]
                o["parts"] |= a["parts"]
                o["muns"] |= a["muns"]
                piezas[("c", c)][a["grupo"]] += p
        for c, o in objs.items():
            pf = Fraction(o["pop"])
            o["lo"] = max(1, math.ceil(pf / techo)) if o["pop"] > 0 else 1
            # Refuerzo válido: no se reparte en más distritos que grupos indivisibles tiene, y cada trozo presente
            # lleva al menos la menor pieza.
            o["hi"] = min(max(1, math.ceil(pf / obj)) if o["pop"] > 0 else 1, len(piezas[c]))
            o["min_pieza"] = min(piezas[c].values())
            o["divisible"] = o["hi"] > 1
    else:  # sin R012: los grupos de átomos (unidades M04) son objetos enteros
        for a in atomos:
            o = objs.setdefault(("g", a["grupo"]), {"pop": 0, "provs": set(), "parts": set(), "muns": set(),
                                                     "lo": 1, "hi": 1, "divisible": False})
            o["pop"] += a["pop"]
            o["provs"] |= a["provs"]
            o["parts"] |= a["parts"]
            o["muns"] |= a["muns"]
    claves = sorted(objs, key=str)
    base = {"objetos": len(claves), "divisibles": sum(objs[c]["divisible"] for c in claves), "k": K,
            "atomos_modelo_completo": len(atomos), "huella_reglas": reglas.huella()}
    cuotas = dict(reglas.cuotas)
    prov_d = ([p for p, c in sorted(cuotas.items()) for _ in range(c)] if reglas.provincia_unica and cuotas
              else [None] * K)
    if len(prov_d) != K:
        return {**base, "estado": "INFACTIBLE", "prueba": "las cuotas provinciales no suman K"}
    m = cp_model.CpModel()
    y, q = {}, {}
    for c in claves:
        o = objs[c]
        ks = [k for k in range(K) if prov_d[k] is None or prov_d[k] in o["provs"]]
        if not ks:
            return {**base, "estado": "INFACTIBLE", "prueba": f"objeto {c[1]} sin distrito de su provincia"}
        for k in ks:
            y[c, k] = m.NewBoolVar("")
            if o["divisible"]:
                q[c, k] = m.NewIntVar(0, o["pop"], "")
                m.Add(q[c, k] <= o["pop"] * y[c, k])
                m.Add(q[c, k] >= o["min_pieza"] * y[c, k])
        ys = [y[c, k] for k in ks]
        if o["divisible"]:
            m.Add(sum(q[c, k] for k in ks) == o["pop"])
            m.Add(sum(ys) >= o["lo"])
            m.Add(sum(ys) <= o["hi"])
            for k in ks:  # lo que queda para los demás trozos presentes
                m.Add(q[c, k] + o["min_pieza"] * (sum(ys) - y[c, k]) <= o["pop"])
        else:
            m.AddExactlyOne(ys)
    total = problema.poblacion_total
    pk = []
    for k in range(K):
        presentes = [c for c in claves if (c, k) in y]
        v = m.NewIntVar(0, total, f"p{k}")
        m.Add(v == sum(q[c, k] if objs[c]["divisible"] else objs[c]["pop"] * y[c, k] for c in presentes))
        m.Add(v <= math.floor(techo))
        exentables = [y[c, k] for c in presentes
                      if objs[c]["muns"] & reglas.exentos_municipio or objs[c]["parts"] & reglas.exentas_particion]
        if exentables:
            e = m.NewBoolVar("")
            m.AddBoolOr(exentables).OnlyEnforceIf(e)
            m.Add(v >= math.ceil(suelo)).OnlyEnforceIf(e.Not())
            if crit.tolerancia == "dura":
                m.Add(v >= math.ceil(obj - tol)).OnlyEnforceIf(e.Not())
        else:
            m.Add(v >= math.ceil(suelo))
            if crit.tolerancia == "dura":
                m.Add(v >= math.ceil(obj - tol))
        if crit.tolerancia == "dura":
            m.Add(v <= math.floor(obj + tol))
        pk.append(v)
        if reglas.disciplina_municipal:  # mixto: dos o más claves; una clave partida toca <= max_mixtos mixtos
            mk = m.NewBoolVar("")
            m.Add(sum(y[c, k] for c in presentes) >= 2).OnlyEnforceIf(mk)
            m.Add(sum(y[c, k] for c in presentes) <= 1).OnlyEnforceIf(mk.Not())
            for c in presentes:
                if objs[c]["divisible"]:
                    objs[c].setdefault("_z", []).append((k, y[c, k], mk))
    for c in claves:
        zs_in = objs[c].pop("_z", [])
        if zs_in:
            parte = m.NewBoolVar("")
            ys = [b for _, b, _ in zs_in]
            m.Add(sum(ys) >= 2).OnlyEnforceIf(parte)
            m.Add(sum(ys) <= 1).OnlyEnforceIf(parte.Not())
            zs = []
            for _, b, mk in zs_in:
                z = m.NewBoolVar("")
                m.AddMultiplicationEquality(z, [b, mk])
                zs.append(z)
            m.Add(sum(zs) <= reglas.max_mixtos).OnlyEnforceIf(parte)
    for k in range(K - 1):  # simetría: distritos de una misma provincia ordenados por población
        if prov_d[k] == prov_d[k + 1]:
            m.Add(pk[k] >= pk[k + 1])
    if objetivo == "minimax":
        dev = m.NewIntVar(0, total, "dev")
        for v in pk:
            m.Add(v - dev <= math.floor(obj))
            m.Add(v + dev >= math.ceil(obj))
        m.Minimize(dev)
    elif objetivo == "techo":
        mx = m.NewIntVar(0, total, "pmax")
        m.AddMaxEquality(mx, pk)
        m.Minimize(mx)
    if pista:  # pista proyectada: distritos de cada provincia por población decreciente (la ruptura de simetría)
        pob_d: dict = defaultdict(int)
        clave_d: dict = defaultdict(lambda: defaultdict(int))
        prov_de: dict = {}
        for a in atomos:
            d = pista.get(a["secs"][0])
            if d is None:
                continue
            pob_d[d] += a["pop"]
            prov_de.setdefault(d, next(iter(a["provs"])))
            for c, p in a["claves"].items():
                clave_d[d][("c", c) if reglas.disciplina_municipal else ("g", a["grupo"])] += p
        libres: dict = defaultdict(list)
        for k in range(K):
            libres[prov_d[k]].append(k)
        for d in sorted(pob_d, key=lambda d: -pob_d[d]):
            lst = libres[prov_de[d] if prov_d[0] is not None else None]
            if not lst:
                break
            k = lst.pop(0)
            fijar = (lambda v, val: m.Add(v == int(val))) if fijar_pista else m.AddHint
            for c in claves:
                if (c, k) in y:
                    fijar(y[c, k], c in clave_d[d])
                if (c, k) in q:
                    fijar(q[c, k], clave_d[d].get(c, 0))
    sol = cp_model.CpSolver()
    sol.parameters.max_time_in_seconds = float(tiempo)
    sol.parameters.num_workers = int(hilos)
    est = sol.StatusName(sol.Solve(m))
    res = {**base, "variables": len(m.Proto().variables), "t_s": round(time.time() - t0, 2), "estado_solver": est}
    if est == "INFEASIBLE":
        res.update(estado="INFACTIBLE", prueba="relajación fluida infactible: no existe plan válido")
        return res
    res["estado"] = "RELAJACION_FACTIBLE" if est in ("OPTIMAL", "FEASIBLE") else "DESCONOCIDO"
    if objetivo in ("minimax", "techo"):
        # La cota probada de CP-SAT vale aunque no haya terminado (UNKNOWN): es la cota del árbol explorado.
        res["cota_inferior"] = math.ceil(sol.BestObjectiveBound() - 1e-6)
        res["cota_optima_relajacion"] = est == "OPTIMAL"
    return res


def _valor(asig: dict[str, str], problema: Problema, obj, objetivo: str) -> int:
    pob: dict = defaultdict(int)
    for u in problema.unidades:
        pob[asig[u.id]] += u.poblacion
    if objetivo == "techo":
        return max(pob.values())
    return max(max(p - math.floor(obj), math.ceil(obj) - p) for p in pob.values())


def certificar_ligero(problema: Problema, reglas: Reglas, unidad_m04: dict[str, str] | None = None, *, tiempo: float,
                      hilos: int, objetivo: str = "minimax", pista: dict | None = None, grano: float = 0.25,
                      umbral_exacto: int = 400) -> dict:
    """Cota inferior (relajación) + cota superior (modelo restringido, y la pista si es válida). Si el modelo completo
    tiene <= umbral_exacto átomos, también se resuelve y su cota y su plan entran en la combinación. Resultado:
    ÓPTIMO certificado si las cotas coinciden, si no COTA con el hueco."""
    if objetivo not in ("factibilidad", "minimax", "techo"):
        raise ValueError("el modelo ligero admite factibilidad, minimax o techo")
    unidad_m04 = unidad_m04 or {}
    obj = reglas.limites(problema.poblacion_total)[0]
    inf = cota_relajada(problema, reglas, unidad_m04, tiempo=tiempo / 2, hilos=hilos, objetivo=objetivo, pista=pista)
    out = {"modelo": "ligero", "grano": grano, "objetivo": objetivo, "inferior": inf}
    if inf["estado"] == "INFACTIBLE":
        out.update(estado="INFACTIBLE", prueba=inf["prueba"])
        return out
    sup = resolver(problema, reglas, unidad_m04, tiempo=tiempo / 2, hilos=hilos, objetivo=objetivo, pista=pista,
                   grano=grano)
    asig = sup.pop("asignacion", None)
    out["superior"] = sup
    candidatos = []
    if asig and juzgar(problema, reglas, asig, unidad_m04)["estado"] == "PASS":
        candidatos.append(("restringido", asig))
    lb_exacto = None
    if len(construir_atomos(problema, reglas, unidad_m04)[0]) <= umbral_exacto:
        ex = resolver(problema, reglas, unidad_m04, tiempo=tiempo / 2, hilos=hilos, objetivo=objetivo, pista=pista)
        a_ex = ex.pop("asignacion", None)
        out["exacto"] = ex
        if ex["estado"] == "INFACTIBLE":
            out.update(estado="INFACTIBLE", prueba=ex["prueba"])
            return out
        if a_ex and juzgar(problema, reglas, a_ex, unidad_m04)["estado"] == "PASS":
            candidatos.append(("exacto", a_ex))
        if "cota_inferior_objetivo" in ex:
            lb_exacto = math.ceil(ex["cota_inferior_objetivo"] - 1e-6)
    if pista and set(pista) >= {u.id for u in problema.unidades} and \
            juzgar(problema, reglas, pista, unidad_m04)["estado"] == "PASS":
        candidatos.append(("pista", pista))
    if not candidatos:
        out["estado"] = "DESCONOCIDO"
        return out
    if objetivo == "factibilidad":
        out.update(estado="FACTIBLE", asignacion=candidatos[0][1], origen=candidatos[0][0])
        return out
    origen, mejor = min(candidatos, key=lambda c: _valor(c[1], problema, obj, objetivo))
    ub = _valor(mejor, problema, obj, objetivo)
    lbs = [v for v in (inf.get("cota_inferior"), lb_exacto) if v is not None]
    lb = max(lbs) if lbs else None
    out.update(asignacion=mejor, origen=origen, cota_superior=ub, cota_inferior=lb)
    if lb is not None:
        out["hueco"] = ub - lb
        out["hueco_relativo_objetivo"] = round((ub - lb) / float(obj), 6)
    out["estado"] = "OPTIMO_CERTIFICADO" if lb is not None and ub <= lb else "COTA"
    return out


# --------------------------------------------------------------------------- CLI
def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Certificador exacto CP-SAT sobre el núcleo de reglas (T-136)")
    ap.add_argument("--params", required=True)
    ap.add_argument("--grafo", required=True)
    ap.add_argument("--secciones", required=True, help="GeoJSON de secciones del M04 (o M05/M06), con ddd_unit_id")
    ap.add_argument("--sin-unidades", action="store_true", help="ignora ddd_unit_id (solo reglas de la validación)")
    ap.add_argument("--sin-nucleos", action="store_true",
                    help="no marca núcleos cerrados (R-NUCLEO no se aplica; solo para comparar)")
    ap.add_argument("--perfil", choices=("nucleo", "produccion"), default="nucleo",
                    help="nucleo: Criterio aprobado (D-44); produccion: compatibilidad con validar_ejecucion 1.3.5")
    ap.add_argument("--referencia", action="append", default=[], help="composición a juzgar (nombre=ruta o ruta)")
    ap.add_argument("--pista", help="composición usada como solución inicial (no restringe)")
    ap.add_argument("--objetivo", choices=("factibilidad", "minimax", "techo", "enumerar"), default="factibilidad")
    ap.add_argument("--modelo", choices=("exacto", "ligero"), default="exacto",
                    help="ligero: cota inferior por relajación fluida + cota superior por superátomos (T-164)")
    ap.add_argument("--grano", type=float, default=0.25, help="ligero: población máxima del superátomo / objetivo")
    ap.add_argument("--umbral-exacto", type=int, default=400,
                    help="ligero: con hasta tantos átomos se resuelve también el modelo completo")
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
    unidades, unidad_m04 = leer_secciones(a.secciones, cfg, criterio, con_unidades=not a.sin_unidades,
                                          con_nucleos=not a.sin_nucleos)
    problema = Problema(tuple(unidades), tuple(leer_grafo(a.grafo, {u.id for u in unidades})))
    reglas.comprobar_datos(problema)
    pista = leer_composicion(a.pista) if a.pista else None
    res = {"version": VERSION, "params": a.params, "perfil": a.perfil, "unidades_m04": len(set(unidad_m04.values())),
           "nucleos_cerrados_entrada": len({u.nucleo_cerrado for u in unidades if u.nucleo_cerrado}),
           "r_nucleo": bool(reglas.nucleos_cerrados and not a.sin_nucleos)}
    if res["r_nucleo"] and not res["nucleos_cerrados_entrada"]:
        res["aviso_nucleos"] = "la entrada no trae núcleos cerrados (sin district_id/ddd_closed_urban o ninguno)"
    if a.modelo == "ligero":
        res.update(certificar_ligero(problema, reglas, unidad_m04, tiempo=a.tiempo, hilos=a.hilos,
                                     objetivo=a.objetivo, pista=pista, grano=a.grano,
                                     umbral_exacto=a.umbral_exacto))
    else:
        res.update(resolver(problema, reglas, unidad_m04, tiempo=a.tiempo, hilos=a.hilos, objetivo=a.objetivo,
                            pista=pista, cota_desviacion=a.cota_desviacion))
    asig = res.pop("asignacion", None)
    planes = res.pop("_planes", None)
    if asig:
        res["comprobacion"] = juzgar(problema, reglas, asig, unidad_m04)
    mejor_huella = None
    if planes is not None:
        res["planes_comprobados_pass"] = sum(juzgar(problema, reglas, p, unidad_m04)["estado"] == "PASS"
                                             for p in planes)
        if planes:
            ms = [metricas(problema, reglas, p) for p in planes]
            j = min(range(len(ms)), key=lambda i: ms[i]["clave"])
            mejor_huella = ms[j]["huella_plan"]
            res["mejor_por_calidad"] = {"plan": j, "exacto": res.get("estado") == "ENUMERADO",
                                        "empatados": sum(m["clave"][:4] == ms[j]["clave"][:4] for m in ms),
                                        **legible(ms[j])}
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
        if mejor_huella is not None and set(comp) >= {u.id for u in problema.unidades}:
            mr = metricas(problema, reglas, comp)
            ev["calidad"] = legible(mr)
            ev["es_el_mejor_por_calidad"] = mr["huella_plan"] == mejor_huella
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
