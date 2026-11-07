#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Hemiciclo nacional: suma de escaños por partido de tres maneras.

PROYECTO: Diputado de Distrito
VERSIÓN: 1.0.0 · FECHA: 2026-11-07 · ESTADO: candidato
ANTERIOR: ninguna (fichero nuevo)
QUÉ HACE: lee los M08 registrados (distritos_resultados.csv) de las provincias nacionales completas y suma:
  (a) reparto real 2023 (D'Hondt, umbral 3 %), calculado desde los votos y contrastado escaño a escaño con el oficial;
  (b) elección anterior (generales 2019-11): solo si se aporta --generales-2019; si no, «sin fuente»;
  (c) uninominal propio: el ganador de cada distrito DDD (un escaño por distrito).
  Salida JSON y CSV con totales de «Nacional» por partido y la lista de provincias que faltan, calculada de los datos
  (sin M08, o con distritos distintos de los esperados).
ENTRADAS: --m08 DIR  (busca DIR/congreso_<provincia>/**/distritos_resultados.csv; el más reciente por ruta)
          --oficial-2023 CSV (provincia,partido,votos,escanos[,votos_validos]); provincia = código INE o id congreso_*
          --generales-2019 CSV (mismo formato, opcional)
          --distritos CSV (province_code,k_province; por defecto el reparto N06)
Uso: python herramientas/generar_hemiciclo.py --m08 DIR --oficial-2023 CSV --salida DIR [--visor]
Salida: 0 si todo cuadra; 1 si (a) difiere del oficial o (c) no suma un escaño por distrito.
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
N06 = ROOT / "docs/ESTUDIOS/N06_DECISION_K_20261012/resultados/reparto_ddd_52.csv"
UMBRAL = 0.03
ETIQUETA = "Nacional"

# Código INE → (id de territorio, topónimo en español)
PROVINCIAS = {
    "01": ("alava", "Álava"), "02": ("albacete", "Albacete"), "03": ("alicante", "Alicante"),
    "04": ("almeria", "Almería"), "05": ("avila", "Ávila"), "06": ("badajoz", "Badajoz"),
    "07": ("baleares", "Baleares"), "08": ("barcelona", "Barcelona"), "09": ("burgos", "Burgos"),
    "10": ("caceres", "Cáceres"), "11": ("cadiz", "Cádiz"), "12": ("castellon", "Castellón"),
    "13": ("ciudad_real", "Ciudad Real"), "14": ("cordoba", "Córdoba"), "15": ("la_coruna", "La Coruña"),
    "16": ("cuenca", "Cuenca"), "17": ("gerona", "Gerona"), "18": ("granada", "Granada"),
    "19": ("guadalajara", "Guadalajara"), "20": ("guipuzcoa", "Guipúzcoa"), "21": ("huelva", "Huelva"),
    "22": ("huesca", "Huesca"), "23": ("jaen", "Jaén"), "24": ("leon", "León"), "25": ("lerida", "Lérida"),
    "26": ("la_rioja", "La Rioja"), "27": ("lugo", "Lugo"), "28": ("madrid", "Madrid"),
    "29": ("malaga", "Málaga"), "30": ("murcia", "Murcia"), "31": ("navarra", "Navarra"),
    "32": ("orense", "Orense"), "33": ("asturias", "Asturias"), "34": ("palencia", "Palencia"),
    "35": ("las_palmas", "Las Palmas"), "36": ("pontevedra", "Pontevedra"), "37": ("salamanca", "Salamanca"),
    "38": ("santa_cruz_de_tenerife", "Santa Cruz de Tenerife"), "39": ("cantabria", "Cantabria"),
    "40": ("segovia", "Segovia"), "41": ("sevilla", "Sevilla"), "42": ("soria", "Soria"),
    "43": ("tarragona", "Tarragona"), "44": ("teruel", "Teruel"), "45": ("toledo", "Toledo"),
    "46": ("valencia", "Valencia"), "47": ("valladolid", "Valladolid"), "48": ("vizcaya", "Vizcaya"),
    "49": ("zamora", "Zamora"), "50": ("zaragoza", "Zaragoza"), "51": ("ceuta", "Ceuta"), "52": ("melilla", "Melilla"),
}
_POR_ID = {f"congreso_{v[0]}": k for k, v in PROVINCIAS.items()}


def codigo(valor: str) -> str:
    v = valor.strip()
    if v in PROVINCIAS:
        return v
    if v.zfill(2) in PROVINCIAS:
        return v.zfill(2)
    if v in _POR_ID:
        return _POR_ID[v]
    raise ValueError(f"provincia no reconocida: {valor!r}")


def dhondt(votos: dict[str, int], escanos: int, votos_validos: int | None = None) -> dict[str, int]:
    """D'Hondt con umbral del 3 % de los votos válidos de la provincia. Desempate: más votos, luego nombre."""
    total = votos_validos if votos_validos else sum(votos.values())
    aptos = {p: v for p, v in votos.items() if v >= UMBRAL * total and v > 0}
    res = {p: 0 for p in aptos}
    for _ in range(escanos):
        p = max(aptos, key=lambda q: (aptos[q] / (res[q] + 1), aptos[q], q))
        res[p] += 1
    return {p: n for p, n in res.items() if n}


def leer_votos(ruta: Path) -> dict[str, dict]:
    """provincia → {'votos': {partido: v}, 'oficial': {partido: esc}, 'validos': int|None}"""
    out: dict[str, dict] = {}
    with open(ruta, encoding="utf-8", newline="") as f:
        for r in csv.DictReader(f):
            d = out.setdefault(codigo(r["provincia"]), {"votos": {}, "oficial": {}, "validos": None})
            d["votos"][r["partido"]] = int(r["votos"])
            if int(r["escanos"]):
                d["oficial"][r["partido"]] = int(r["escanos"])
            if r.get("votos_validos"):
                d["validos"] = int(r["votos_validos"])
    return out


def leer_distritos(ruta: Path) -> dict[str, int]:
    with open(ruta, encoding="utf-8", newline="") as f:
        return {r["province_code"].zfill(2): int(r["k_province"]) for r in csv.DictReader(f)}


def leer_m08(raiz: Path) -> dict[str, list[str]]:
    """provincia → ganadores (partido) de sus distritos, del distritos_resultados.csv más reciente por ruta."""
    out: dict[str, list[str]] = {}
    for cod, (slug, _) in PROVINCIAS.items():
        ficheros = sorted((raiz / f"congreso_{slug}").glob("**/distritos_resultados.csv"))
        if not ficheros:
            continue
        with open(ficheros[-1], encoding="utf-8", newline="") as f:
            filas = list(csv.DictReader(f))
        out[cod] = [r["winner_party"] for r in sorted(filas, key=lambda r: int(r["district_id"]))]
    return out


def generar(m08: Path, oficial: Path, distritos: Path, generales: Path | None = None) -> dict:
    esperados = leer_distritos(distritos)
    ganadores = leer_m08(m08)
    of23 = leer_votos(oficial)
    of19 = leer_votos(generales) if generales else None
    provincias, faltan, errores = [], [], []
    for cod, (slug, nombre) in PROVINCIAS.items():
        k = esperados.get(cod)
        g = ganadores.get(cod)
        if g is None:
            faltan.append({"codigo": cod, "provincia": nombre, "motivo": "sin M08 registrado"})
            continue
        if k is not None and len(g) != k:
            faltan.append({"codigo": cod, "provincia": nombre,
                           "motivo": f"M08 con {len(g)} distritos de {k} esperados"})
            continue
        c: dict[str, int] = {}
        for p in g:
            c[p] = c.get(p, 0) + 1
        if cod not in of23:
            faltan.append({"codigo": cod, "provincia": nombre, "motivo": "sin resultados oficiales 2023"})
            continue
        d = of23[cod]
        escanos = sum(d["oficial"].values())
        a = dhondt(d["votos"], escanos, d["validos"])
        if a != d["oficial"]:
            errores.append(f"{nombre}: D'Hondt {a} != oficial {d['oficial']}")
        if sum(c.values()) != len(g):
            errores.append(f"{nombre}: (c) no suma un escaño por distrito")
        b = None
        if of19 is not None and cod in of19:
            e19 = of19[cod]
            b = dhondt(e19["votos"], sum(e19["oficial"].values()) or sum(a.values()), e19["validos"])
        provincias.append({"codigo": cod, "provincia": nombre, "distritos": len(g), "escanos_2023": escanos,
                           "a": a, "b": b, "c": c})
    def total(clave):
        t: dict[str, int] = {}
        for p in provincias:
            for par, n in (p[clave] or {}).items():
                t[par] = t.get(par, 0) + n
        return dict(sorted(t.items(), key=lambda x: -x[1]))
    sin_b = of19 is None or any(p["b"] is None for p in provincias)
    return {
        "schema": "ddd.hemiciclo/1.0", "version": "1.0.0", "ambito": ETIQUETA,
        "provincias_incluidas": len(provincias), "faltan": faltan,
        "fuentes": {"a": "reparto real 2023 (D'Hondt oficial)",
                    "b": "sin fuente" if sin_b else "generales 2019-11",
                    "c": "uninominal propio: ganador de cada distrito DDD"},
        "totales": {"a": total("a"), "b": None if sin_b else total("b"), "c": total("c")},
        "escanos": {"a": sum(p["escanos_2023"] for p in provincias),
                    "c": sum(p["distritos"] for p in provincias)},
        "provincias": provincias, "errores": errores,
    }


def escribir(res: dict, salida: Path) -> None:
    salida.mkdir(parents=True, exist_ok=True)
    (salida / "hemiciclo.json").write_text(json.dumps(res, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    with open(salida / "hemiciclo.csv", "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["ambito", "provincia", "partido", "a_real_2023", "b_2019", "c_uninominal"])
        def filas(ambito, a, b, c):
            for p in sorted(set(a) | set(b or {}) | set(c)):
                w.writerow([ambito, ambito if ambito == ETIQUETA else "", p, a.get(p, 0),
                            "sin fuente" if b is None else b.get(p, 0), c.get(p, 0)])
        for pr in res["provincias"]:
            for p in sorted(set(pr["a"]) | set(pr["b"] or {}) | set(pr["c"])):
                w.writerow([pr["provincia"], pr["provincia"], p, pr["a"].get(p, 0),
                            "sin fuente" if pr["b"] is None else pr["b"].get(p, 0), pr["c"].get(p, 0)])
        filas(ETIQUETA, res["totales"]["a"], res["totales"]["b"], res["totales"]["c"])


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--m08", required=True, type=Path)
    ap.add_argument("--oficial-2023", required=True, type=Path)
    ap.add_argument("--generales-2019", type=Path)
    ap.add_argument("--distritos", type=Path, default=N06)
    ap.add_argument("--salida", required=True, type=Path)
    ap.add_argument("--visor", action="store_true", help="copia también hemiciclo.json a dashboard/")
    a = ap.parse_args(argv)
    res = generar(a.m08, a.oficial_2023, a.distritos, a.generales_2019)
    escribir(res, a.salida)
    if a.visor:
        escribir(res, ROOT / "dashboard")
    print(f"{ETIQUETA}: {res['provincias_incluidas']} provincias; faltan "
          f"{[f['provincia'] for f in res['faltan']]}; (b) {res['fuentes']['b']}")
    for e in res["errores"]:
        print(f"::error::{e}")
    return 1 if res["errores"] else 0


if __name__ == "__main__":
    sys.exit(main())
