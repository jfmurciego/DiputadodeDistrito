#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Indicadores por elección y sistema (T-478, D-214): desproporcionalidad, número efectivo de partidos, prima al ganador,
votos sin representación y desigualdad territorial, para el sistema real, la mayoría simple por distrito y la doble vuelta.

PROYECTO: Diputado de Distrito
VERSIÓN: 1.0.0 · FECHA: 2026-11-28 · ESTADO: candidato
ANTERIOR: ninguna (fichero nuevo)
CAMBIOS: 1.0.0: fichero nuevo. No toca el motor, el contrato ni la publicación: lee tablas ya versionadas y escribe en docs/ESTUDIOS/T478/.
MOTIVO: D-214 (propietario, 26-11): solo los indicadores del paquete H de la auditoría (no es la ficha por mapa, T-470).
QUÉ HACE: fórmulas puras (gallagher, loosemore_hanby, numero_efectivo, prima_ganador, votos_sin_representacion), escaños reales
  del BOE pasados a partido homologado (`escanos_reales`) y un generador que escribe CSV con sha256 de cada fuente.
  Mapas: 2023 «publicado» (datos_abiertos/INDEX.json → datos/resultados/MANIFEST.json) o «historico» (datos/resultados/historico/,
  reagregado sobre mapas M06 anteriores: en 2023 difiere del publicado en 42 de 52 provincias). Doble vuelta: `doble_vuelta.resolver`.
  Votos del sistema real = suma de los distritos por provincia (sin CERA); escaños = BOE (con CERA).
USO: python herramientas/indicadores_sistemas.py --salida docs/ESTUDIOS/T478
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import re
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "herramientas") not in sys.path:
    sys.path.insert(0, str(ROOT / "herramientas"))

import doble_vuelta as dv  # noqa: E402

CONF = ROOT / "configuracion"
ELECCIONES = ("201111", "201512", "201606", "201904", "201911", "202307")
SISTEMAS = ("real", "mayoria_simple", "dv_base", "dv_A", "dv_B")


# ---------------------------------------------------------------- fórmulas puras
def _pct(d: dict) -> dict:
    t = sum(v for v in d.values() if v > 0)
    return {k: 100.0 * v / t for k, v in d.items() if v > 0} if t > 0 else {}


def _diferencias(votos: dict, escanos: dict) -> list[float]:
    pv, pe = _pct(votos), _pct(escanos)
    return [pv.get(k, 0.0) - pe.get(k, 0.0) for k in set(pv) | set(pe)]


def gallagher(votos: dict, escanos: dict) -> float:
    return math.sqrt(sum(x * x for x in _diferencias(votos, escanos)) / 2.0)


def loosemore_hanby(votos: dict, escanos: dict) -> float:
    return sum(abs(x) for x in _diferencias(votos, escanos)) / 2.0


def numero_efectivo(valores: dict) -> float:
    s = sum(p * p for p in _pct(valores).values()) / 10000.0
    return 1.0 / s if s > 0 else 0.0


def ganador_mayoria_simple(votos: dict) -> str:
    return sorted(votos, key=lambda k: (-votos[k], k))[0]


def prima_ganador(votos: dict, escanos: dict) -> dict:
    g = ganador_mayoria_simple(votos)
    pv, pe = _pct(votos).get(g, 0.0), _pct(escanos).get(g, 0.0)
    return {"candidatura": g, "pct_votos": pv, "pct_escanos": pe, "prima": pe - pv, "mayoria_fabricada": pe > 50.0 and pv < 50.0}


def votos_sin_representacion(circs) -> float:
    """% de votos a candidaturas sin escaño en su circunscripción. `circs`: [(votos por candidatura, escaños por candidatura)]."""
    sin = tot = 0
    for v, e in circs:
        for k, n in v.items():
            tot += n
            if e.get(k, 0) <= 0:
                sin += n
    return 100.0 * sin / tot if tot else 0.0


def sumar(dicts) -> dict:
    out: dict = defaultdict(int)
    for d in dicts:
        for k, v in d.items():
            out[k] += v
    return dict(out)


# ---------------------------------------------------------------- fuentes
def _fichero_oficial(eleccion: str) -> Path:
    return CONF / ("resultados_oficiales_congreso_2023.csv" if eleccion == "202307"
                   else f"resultados_oficiales_congreso_{eleccion[:4]}_{eleccion[4:]}.csv")


def escanos_reales(eleccion: str) -> dict[str, dict[str, int]]:
    """Escaños oficiales (BOE, cuadro por circunscripción): {código INE de provincia: {partido homologado: escaños}}."""
    espejo: dict[tuple, str] = {}
    with open(CONF / "alias_siglas_boe_espejo.csv", encoding="utf-8", newline="") as f:
        for r in csv.DictReader(f):
            if r["eleccion"] == eleccion:
                espejo[(r["provincia"], r["sigla_boe"])] = r["siglas_espejo"]
    alias = dv.cargar_alias(CONF / "alias_partidos_generales.csv", eleccion)
    out: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    with open(_fichero_oficial(eleccion), encoding="utf-8", newline="") as f:
        for r in csv.DictReader(f):
            e = int(r["escanos"])
            sigla = espejo.get((r["codigo"], r["partido"]), r["partido"])
            out[r["codigo"]][alias.get(sigla, sigla)] += e
    return {k: {p: n for p, n in v.items() if n > 0} for k, v in out.items()}


def _leer_votos(path: Path) -> tuple[dict, dict]:
    """(distrito → partido → votos, distrito → censo) de un *_partidos.csv."""
    v: dict = defaultdict(lambda: defaultdict(int))
    censo: dict = {}
    with open(path, encoding="utf-8", newline="") as f:
        for r in csv.DictReader(f):
            v[r["distrito"]][r["partido"]] += int(r["votos"])
            if r.get("censo"):
                censo[r["distrito"]] = int(r["censo"])
    return {d: dict(x) for d, x in v.items()}, censo


def _provincia_de(tid: str) -> str:
    m = re.fullmatch(r"nac(\d{2})", tid)
    if not m:
        raise ValueError(f"Id de territorio inesperado: {tid}")
    return m.group(1)


def mapas(eleccion: str, mapa: str) -> list[dict]:
    """Un dict por provincia: provincia, ruta, sha256, votos (distrito → partido → votos), censo, k (distritos del mapa)."""
    out = []
    if mapa == "publicado":
        if eleccion != "202307":
            raise ValueError("Mapas publicados: solo 2023")
        idx = json.load(open(ROOT / "datos_abiertos/INDEX.json", encoding="utf-8"))["territorios"]
        man = json.load(open(ROOT / "datos/resultados/MANIFEST.json", encoding="utf-8"))["partidos_runs"]
        for tid, t in sorted(idx.items()):
            ent = man[f"{tid}/{t['resultados']['run_id']}"]
            ruta = ROOT / ent["ruta"]
            if dv.sha256(ruta) != ent["sha256_csv"]:
                raise ValueError(f"sha256 distinto en {ent['ruta']}")
            v, censo = _leer_votos(ruta)
            out.append({"provincia": _provincia_de(tid), "ruta": ent["ruta"], "sha256": ent["sha256_csv"], "votos": v, "censo": censo,
                        "k": t["n_distritos"], "desajuste_pct": (ent.get("desajustes") or {}).get("pct_desajuste"),
                        "desajuste_tope": (ent.get("desajustes") or {}).get("tope_pct")})
    else:
        man = json.load(open(ROOT / "datos/resultados/historico/MANIFEST.json", encoding="utf-8"))["territorios"]
        for clave, t in sorted(man.items(), key=lambda kv: kv[1]["provincia"]):
            ruta = ROOT / "datos/resultados/historico" / eleccion / f"{clave}_partidos.csv"
            v, censo = _leer_votos(ruta)
            out.append({"provincia": t["provincia"], "ruta": str(ruta.relative_to(ROOT)), "sha256": dv.sha256(ruta), "votos": v,
                        "censo": censo, "k": len(v), "desajuste_pct": None, "desajuste_tope": None})
    return out


def poblacion(path) -> dict[str, int]:
    with open(path, encoding="utf-8", newline="") as f:
        return {r["codigo"]: int(r["poblacion"]) for r in csv.DictReader(l for l in f if not l.startswith("#"))}


# ---------------------------------------------------------------- cálculo por elección, mapa y sistema
def calcular(eleccion: str, mapa: str) -> dict:
    """Indicadores y detalle de los cinco sistemas. Devuelve {'filas': [...], 'partidos': [...], 'territorial': [...], 'fuentes': [...]}"""
    ed = f"{eleccion[:4]}-{eleccion[4:]}"
    alias = dv.cargar_alias(CONF / "alias_partidos_generales.csv", eleccion)
    tabla = dv.cargar_tabla(CONF / "bloques_partidos_2026-11-25.csv", ed)
    bloque_de = {k: v for k, v in tabla.items() if v}
    provs = mapas(eleccion, mapa)
    reales = escanos_reales(eleccion)
    fuentes = [(p["ruta"], p["sha256"]) for p in provs]
    # votos homologados por distrito
    dist: dict[str, dict[str, int]] = {}
    por_prov: dict[str, dict[str, dict[str, int]]] = {}
    for p in provs:
        h = dv.aplicar_alias(p["votos"], alias)
        por_prov[p["provincia"]] = {f"{p['provincia']}:{d}": x for d, x in h.items()}
        dist.update(por_prov[p["provincia"]])
    nacional = sumar(dist.values())
    filas, partidos = [], []

    def anotar(sistema, votos_n, escanos_n, circs, n_escanos, extra=None):
        pr = prima_ganador(votos_n, escanos_n)
        fila = {"eleccion": eleccion, "mapa": mapa, "sistema": sistema, "escanos": n_escanos,
                "gallagher": round(gallagher(votos_n, escanos_n), 3), "loosemore_hanby": round(loosemore_hanby(votos_n, escanos_n), 3),
                "np_votos": round(numero_efectivo(votos_n), 3), "np_escanos": round(numero_efectivo(escanos_n), 3),
                "ganador": pr["candidatura"], "pct_votos_ganador": round(pr["pct_votos"], 2), "pct_escanos_ganador": round(pr["pct_escanos"], 2),
                "prima": round(pr["prima"], 2), "mayoria_fabricada": pr["mayoria_fabricada"],
                "votos_sin_representacion": round(votos_sin_representacion(circs), 2)}
        fila.update(extra or {})
        filas.append(fila)
        for c in sorted(set(votos_n) | set(escanos_n), key=lambda k: (-escanos_n.get(k, 0), -votos_n.get(k, 0), k)):
            partidos.append({"eleccion": eleccion, "mapa": mapa, "sistema": sistema, "candidatura": c,
                             "votos": votos_n.get(c, 0), "escanos": escanos_n.get(c, 0)})

    # real: circunscripción = provincia; votos de los distritos, escaños del BOE
    esc_real = sumar(reales.values())
    circs = [(sumar(por_prov[c].values()), reales.get(c, {})) for c in sorted(por_prov)]
    anotar("real", nacional, esc_real, circs, sum(esc_real.values()))
    # mayoría simple: un escaño por distrito
    gan = {d: ganador_mayoria_simple(v) for d, v in dist.items() if v}
    esc_ms = sumar({g: 1} for g in gan.values())
    anotar("mayoria_simple", nacional, esc_ms, [(v, {gan[d]: 1}) for d, v in dist.items() if v], len(gan))
    # doble vuelta: unidad = candidatura (bloque coaligado en dv_A y dv_B)
    for esc in ("dv_base", "dv_A", "dv_B"):
        votos_c: dict[str, int] = defaultdict(int)
        ganadores: dict[str, str] = {}
        circs_dv = []
        n_vueltas = {1: 0, 2: 0}
        for d, v in sorted(dist.items()):
            det = dv.detalle(v, bloque_de, esc)
            vc: dict[str, int] = {}
            for f in det:
                vc[f["candidatura"]] = f["votos_candidatura"]
            for k, n in vc.items():
                votos_c[k] += n
            r = dv.resolver(v, bloque_de, esc)
            if r["candidatura_ganadora"]:
                ganadores[d] = r["candidatura_ganadora"]
                n_vueltas[int(r["vuelta_decisiva"])] += 1
                circs_dv.append((vc, {r["candidatura_ganadora"]: 1}))
        esc_dv = sumar({g: 1} for g in ganadores.values())
        anotar(esc, dict(votos_c), esc_dv, circs_dv, len(ganadores),
               {"distritos_1v": n_vueltas[1], "distritos_2v": n_vueltas[2]})
    # desigualdad territorial: escaños reales y distritos del mapa frente a población y censo
    territorial = []
    pob = {a: poblacion(CONF / f"poblacion_oficial_provincias_{a}-01-01.csv") for a in ("2022", "2025")}
    k_prov = {p["provincia"]: p["k"] for p in provs}
    esc_prov = {c: sum(v.values()) for c, v in reales.items()}
    censo_prov = {p["provincia"]: sum(p["censo"].values()) for p in provs if p["censo"]}
    for etiqueta, base in (("poblacion_2022", pob["2022"]), ("poblacion_2025", pob["2025"]), ("censo_eleccion", censo_prov)):
        if not base:
            continue
        for reparto, r in (("escanos_reales", esc_prov), ("distritos_mapa", k_prov)):
            territorial.append({"eleccion": eleccion, "mapa": mapa, "base": etiqueta, "reparto": reparto,
                                "loosemore_hanby": round(loosemore_hanby({c: base[c] for c in r}, r), 3),
                                "unidades": sum(r.values())})
    return {"filas": filas, "partidos": partidos, "territorial": territorial, "fuentes": fuentes,
            "desajustes": [(p["provincia"], p["desajuste_pct"], p["desajuste_tope"]) for p in provs if p["desajuste_pct"] is not None]}


def _csv(path: Path, filas: list[dict]):
    cols = list(dict.fromkeys(k for f in filas for k in f))
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols, lineterminator="\n")
        w.writeheader()
        w.writerows(filas)


def generar(salida) -> None:
    salida = Path(salida)
    salida.mkdir(parents=True, exist_ok=True)
    todo = {"filas": [], "partidos": [], "territorial": []}
    fuentes: dict[str, str] = {}
    desajustes = []
    for e in ELECCIONES:
        for mapa in ("historico", "publicado") if e == "202307" else ("historico",):
            r = calcular(e, mapa)
            for k in todo:
                todo[k] += r[k]
            fuentes.update(dict(r["fuentes"]))
            desajustes += r["desajustes"]
        for ruta in (_fichero_oficial(e), CONF / "alias_siglas_boe_espejo.csv", CONF / "alias_partidos_generales.csv"):
            fuentes[str(ruta.relative_to(ROOT))] = dv.sha256(ruta)
    for ruta in ("configuracion/bloques_partidos_2026-11-25.csv", "configuracion/poblacion_oficial_provincias_2022-01-01.csv",
                 "configuracion/poblacion_oficial_provincias_2025-01-01.csv", "datos_abiertos/INDEX.json",
                 "datos/resultados/MANIFEST.json", "datos/resultados/historico/MANIFEST.json"):
        fuentes[ruta] = dv.sha256(ROOT / ruta)
    _csv(salida / "indicadores.csv", todo["filas"])
    _csv(salida / "reparto_por_candidatura.csv", todo["partidos"])
    _csv(salida / "desigualdad_territorial.csv", todo["territorial"])
    _csv(salida / "fuentes.csv", [{"fichero": k, "sha256": v} for k, v in sorted(fuentes.items())])
    if desajustes:
        _csv(salida / "desajustes_publicado.csv", [{"provincia": p, "pct_desajuste": d, "tope_pct": t} for p, d, t in desajustes])


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--salida", default=str(ROOT / "docs/ESTUDIOS/T478"))
    generar(ap.parse_args().salida)


if __name__ == "__main__":
    main()
