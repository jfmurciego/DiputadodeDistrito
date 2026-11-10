#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PROYECTO: Diputado de Distrito
COMPONENTE: motor 2 — indicadores de naturalidad (métricas, no reglas)
VERSIÓN: 1.0.0
NOMBRE DE VERSIÓN: Naturalidad · indicadores
FECHA: 2026-11-10
ESTADO: candidato (motor 2; producción no lo importa)
CAMBIOS: fichero nuevo.
MOTIVO: T-172 (decisión del propietario, 10-11): medir lo «natural» de un plan además de la población: compacidad,
  ángulos, demarcaciones partidas (partidos judiciales, comarcas) y cohesión de movilidad. Son MÉTRICAS para comparar
  planes y para funciones de calidad experimentales; no deciden validez (eso es reglas.evaluar) y ningún umbral se fija
  aquí: el criterio lo decide el propietario.
ANTERIOR: ninguna (fichero nuevo)
QUÉ HACE:
  demarcaciones(asig, pob, grupo_de)  por demarcación (partido judicial, comarca...): cuántas quedan partidas entre
      distritos y qué fracción de la población queda en el distrito mayoritario de su demarcación.
  aristas_de_corte(asig, aristas)     aristas del grafo de unidades con extremos en distritos distintos (y su peso, p. ej.
      longitud de frontera compartida).
  cohesion_movilidad(asig, pob, grupo_de, flujos)  fracción del flujo entre áreas distintas del territorio que queda
      dentro de un mismo distrito (la definición del piloto de movilidad; un área partida reparte su peso por población).
  forma(geometrias)                    por distrito: Polsby-Popper 4πA/P² y convexidad P_envolvente/P (1 = convexo; menor
      = más anguloso o recortado); necesita shapely (solo esta función).
  resumen(...)                         todo junto, con medias y mínimos, en un dict de tipos simples.
Solo stdlib salvo forma(); determinista (sin dependencia del orden de entrada).
"""
from __future__ import annotations

import math
from collections import defaultdict
from typing import Iterable, Mapping

VERSION = "1.0.0"


def demarcaciones(asig: Mapping[str, str], pob: Mapping[str, int], grupo_de: Mapping[str, str | None]) -> dict:
    """asig: unidad -> distrito; pob: unidad -> población; grupo_de: unidad -> demarcación (None = sin dato)."""
    por: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    sin = 0
    for u, d in asig.items():
        g = grupo_de.get(u)
        if g is None:
            sin += int(pob.get(u, 0))
            continue
        por[g][d] += int(pob.get(u, 0))
    total = sum(sum(v.values()) for v in por.values())
    mayor = sum(max(v.values()) for v in por.values())
    partidas = sorted(g for g, v in por.items() if len(v) > 1)
    return {"n": len(por), "partidas": len(partidas), "lista_partidas": partidas,
            "fraccion_poblacion_en_mayoritario": (mayor / total) if total else None,
            "poblacion_fuera_de_mayoritario": total - mayor, "poblacion_sin_dato": sin}


def aristas_de_corte(asig: Mapping[str, str], aristas: Iterable[tuple[str, str, float]]) -> dict:
    n = cortes = 0
    peso = peso_corte = 0.0
    for a, b, w in aristas:
        if a not in asig or b not in asig:
            continue
        n += 1
        peso += w
        if asig[a] != asig[b]:
            cortes += 1
            peso_corte += w
    return {"aristas": n, "cortes": cortes, "fraccion_cortes": cortes / n if n else None,
            "peso_corte": peso_corte, "fraccion_peso_corte": peso_corte / peso if peso else None}


def cohesion_movilidad(asig: Mapping[str, str], pob: Mapping[str, int], grupo_de: Mapping[str, str | None],
                       flujos: Iterable[tuple[str, str, float]]) -> dict:
    peso: dict[str, dict[str, float]] = defaultdict(lambda: defaultdict(float))
    for u, d in asig.items():
        g = grupo_de.get(u)
        if g is not None:
            peso[g][d] += int(pob.get(u, 0))
    for v in peso.values():
        t = sum(v.values())
        for k in v:
            v[k] = v[k] / t if t else 0.0
    dentro = total = 0.0
    for o, d, n in flujos:
        if o == d or o not in peso or d not in peso:
            continue
        total += n
        dentro += n * sum(w * peso[d].get(k, 0.0) for k, w in peso[o].items())
    return {"cohesion": dentro / total if total else None, "flujo": total, "areas": len(peso)}


def forma(geometrias: Mapping[str, object]) -> dict[str, dict]:
    """geometrias: distrito -> geometría shapely en CRS métrico."""
    out = {}
    for d in sorted(geometrias, key=str):
        g = geometrias[d]
        a, p = g.area, g.length
        ph = g.convex_hull.length
        out[str(d)] = {"polsby_popper": 4 * math.pi * a / (p * p) if p else None,
                       "convexidad": ph / p if p else None, "area_km2": a / 1e6, "perimetro_km": p / 1e3}
    return out


def _media_min(v: list[float]) -> tuple[float | None, float | None]:
    v = [x for x in v if x is not None]
    return (sum(v) / len(v), min(v)) if v else (None, None)


def resumen(asig: Mapping[str, str], pob: Mapping[str, int], *, geometrias: Mapping[str, object] | None = None,
            aristas: Iterable[tuple[str, str, float]] | None = None,
            demarcacion: Mapping[str, Mapping[str, str | None]] | None = None,
            movilidad: tuple[Mapping[str, str | None], Iterable[tuple[str, str, float]]] | None = None) -> dict:
    r: dict = {"distritos": len(set(asig.values()))}
    if geometrias is not None:
        f = forma(geometrias)
        r["pp_medio"], r["pp_min"] = _media_min([x["polsby_popper"] for x in f.values()])
        r["convexidad_media"], r["convexidad_min"] = _media_min([x["convexidad"] for x in f.values()])
        r["por_distrito"] = f
    if aristas is not None:
        r["corte"] = aristas_de_corte(asig, aristas)
    for nombre, grupo_de in (demarcacion or {}).items():
        r[nombre] = demarcaciones(asig, pob, grupo_de)
    if movilidad is not None:
        r["movilidad"] = cohesion_movilidad(asig, pob, movilidad[0], movilidad[1])
    return r
