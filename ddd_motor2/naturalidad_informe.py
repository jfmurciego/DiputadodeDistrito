#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PROYECTO: Diputado de Distrito
COMPONENTE: motor 2 — entregable del laboratorio de naturalidad: mapas A/D5/D8/C/B lado a lado y tablas
VERSIÓN: 1.1.0
NOMBRE DE VERSIÓN: Naturalidad · informe con topes D5/D8
FECHA: 2026-11-10
ESTADO: experimento (motor 2; producción no lo importa; nada se publica)
CAMBIOS: 1.1.0 (T-179): cinco paneles (A, D5, D8, C, B), filas D5/D8 en la tabla y DISTRITOS.csv (por distrito:
  superficie, población, municipio principal y si es un núcleo cerrado dentro de un solo municipio), para explicar los
  distritos urbanos minúsculos en superficie. 1.0.0: fichero nuevo.
MOTIVO: T-172, paso 5: que el propietario decida con los mapas delante; el criterio no se fija en código.
ANTERIOR: 1.0.0 (T-172, #651) — legacy/ddd_motor2/naturalidad_informe_v1.0.0_20261110.py
USO: python -m ddd_motor2.naturalidad_informe --seccionado-dir <dir> --resultados <out del laboratorio> --salida <dir>
QUÉ HACE: por territorio, un PNG con los cinco ganadores (misma escala y mismos colores: cada distrito de B y C toma el
  color del distrito de A con el que más población comparte), límites de partidos judiciales de fondo (gris) y
  límites de distrito (negro); y TABLA.md / TABLA.csv con población fuera de tolerancia, desvío máximo, compacidad,
  demarcaciones partidas, cohesión de movilidad y el «coste» en población de cada mejora (frente a A).
  Ríos y relieve: no hay fuente en el repo; el fondo es solo de partidos judiciales.
"""
from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path

from . import naturalidad_mapas as nm

NOMBRES = {"A": "A · solo población (función vigente)", "B": "B · población y luego naturalidad",
           "C": "C · como B con grafo ponderado", "D5": "D5 · como C, desvío máx. ≤ 5 %",
           "D8": "D8 · como C, desvío máx. ≤ 8 %"}
ORDEN = ("A", "D5", "D8", "C", "B")
PALETA = ["#4e79a7", "#f28e2b", "#e15759", "#76b7b2", "#59a14f", "#edc948", "#b07aa1", "#ff9da7", "#9c755f",
          "#bab0ac", "#86bcb6", "#d37295", "#a0cbe8", "#ffbe7d", "#8cd17d", "#b6992d", "#f1ce63", "#499894",
          "#d4a6c8", "#fabfd2"]
NOMBRE_TERRITORIO = {"congreso_leon": "León", "congreso_cadiz": "Cádiz", "congreso_badajoz": "Badajoz",
                     "congreso_asturias": "Asturias", "congreso_madrid": "Madrid", "congreso_barcelona": "Barcelona"}
COLUMNAS = ["territorio", "funcion", "candidato", "fuera_tolerancia", "desvio_max_pct", "max_desvio_personas",
            "suma_desvio_personas", "coste_suma_desvio_vs_A", "pp_medio", "pp_min", "convexidad_media",
            "pj_partidos", "pj_n", "pj_pob_fuera_mayoritario", "ca_partidas", "ca_n", "comarca_partidas",
            "movilidad_cohesion", "frontera_cortada"]


def leer(p: Path) -> dict[str, str]:
    with open(p, encoding="utf-8") as f:
        return {r["seccion"]: r["distrito"] for r in csv.DictReader(f)}


def colores(planes: dict[str, dict[str, str]], pob: dict[str, int]) -> dict[str, dict[str, str]]:
    base = sorted(set(planes["A"].values()), key=lambda d: (len(d), d))
    color_a = {d: PALETA[i % len(PALETA)] for i, d in enumerate(base)}
    out = {"A": color_a}
    for f in sorted(k for k in planes if k != "A"):
        comun: dict[tuple[str, str], int] = defaultdict(int)
        for s, d in planes[f].items():
            comun[(d, planes["A"][s])] += pob[s]
        libres, cmap = set(base), {}
        for (d, da), _ in sorted(comun.items(), key=lambda kv: (-kv[1], kv[0])):  # emparejamiento voraz 1 a 1
            if d not in cmap and da in libres:
                cmap[d] = color_a[da]
                libres.discard(da)
        for d in sorted(set(planes[f].values())):
            cmap.setdefault(d, "#cccccc")
        out[f] = cmap
    return out


def figura(t: str, geo: nm.Geometria, planes: dict, pob: dict, filas: dict, destino: Path) -> None:
    import matplotlib  # noqa: PLC0415
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt  # noqa: PLC0415
    import shapely  # noqa: PLC0415
    from geopandas import GeoSeries  # noqa: PLC0415
    tablas = nm.tablas_municipio()
    gdf = geo.gdf
    pj = gdf.assign(pj=gdf["CUSEC"].str[:5].map(tablas["pj"]).fillna("?")).dissolve("pj")
    cols = colores(planes, pob)
    x0, y0, x1, y1 = gdf.total_bounds
    fs = [f for f in ORDEN if f in planes]
    fig, ejes = plt.subplots(1, len(fs), figsize=(6 * len(fs), 7.2), dpi=110)
    for ax, f in zip(ejes, fs):
        g = gdf.assign(d=gdf["CUSEC"].map(planes[f]))
        g.plot(ax=ax, color=g["d"].map(cols[f]), linewidth=0)
        pj.boundary.plot(ax=ax, color="#555555", linewidth=0.5, linestyle=(0, (2, 2)))
        GeoSeries([shapely.union_all(s.geometry.values, grid_size=0.01).boundary
                   for _, s in g.groupby("d", sort=True)], crs=gdf.crs).plot(ax=ax, color="black", linewidth=0.9)
        r = filas[f]
        ax.set_title(f"{NOMBRES[f]}\nfuera de tolerancia {r['fuera_tolerancia']} · desvío máx. {r['desvio_max_pct']} % · "
                     f"PP {r['pp_medio']}\npartidos judiciales partidos {r['pj_partidos']}/{r['pj_n']} · "
                     f"comarcas agrarias {r['ca_partidas']}/{r['ca_n']}", fontsize=9)
        ax.set_xlim(x0, x1)
        ax.set_ylim(y0, y1)
        ax.set_axis_off()
    fig.suptitle(f"{NOMBRE_TERRITORIO.get(t, t)} — mismos datos y reglas; cambia cómo se elige "
                 "y cómo se corta (línea discontinua: partidos judiciales)", fontsize=11)
    fig.tight_layout(rect=(0, 0, 1, 0.94))
    fig.savefig(destino, metadata={"Software": None})
    plt.close(fig)


def distritos(t: str, planes: dict, pob: dict, geo: nm.Geometria, nombres: dict) -> list[dict]:
    """Por distrito: superficie (km², suma de secciones), población, municipio principal y si es un núcleo cerrado
    (todas sus secciones en un solo municipio, que entonces es mayor que la población objetivo y se parte)."""
    area = dict(zip(geo.gdf["CUSEC"], geo.gdf.geometry.area / 1e6))
    filas = []
    for f in ORDEN:
        if f not in planes:
            continue
        por: dict[str, list[str]] = defaultdict(list)
        for s, d in planes[f].items():
            por[d].append(s)
        for d in sorted(por, key=lambda x: (len(x), x)):
            ss = por[d]
            pm: dict[str, int] = defaultdict(int)
            for s in ss:
                pm[s[:5]] += pob[s]
            m, pmax = max(pm.items(), key=lambda kv: (kv[1], kv[0]))
            p = sum(pob[s] for s in ss)
            filas.append({"territorio": t, "funcion": f, "distrito": d, "superficie_km2": round(sum(area[s] for s in ss), 1),
                          "poblacion": p, "municipio_principal": nombres.get(m, m), "codigo_ine": m,
                          "fraccion_pob_municipio_principal": round(pmax / p, 3), "municipios": len(pm),
                          "nucleo_cerrado": len(pm) == 1})
    return filas


def r3(x):
    return "" if x is None else round(x, 3)


def main(argv=None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--seccionado-dir", required=True)
    p.add_argument("--resultados", required=True)
    p.add_argument("--salida", required=True)
    a = p.parse_args(argv)
    sal = Path(a.salida)
    sal.mkdir(parents=True, exist_ok=True)
    todas, dist = [], []
    with open(nm.ROOT / "configuracion" / "partidos_judiciales.csv", encoding="utf-8") as fh:
        nombres = {r["codigo_ine"]: r["nombre_ine"] for r in csv.DictReader(x for x in fh if not x.startswith("#"))}
    for res in sorted(Path(a.resultados).glob("*/RESULTADO.json")):
        r = json.loads(res.read_text(encoding="utf-8"))
        t = r["territorio"]
        planes = {f: leer(res.parent / f"{t}_{f}.csv") for f in ORDEN if f in r["ganadores"]}
        _, pob = nm.leer_composicion(res.parent / f"{t}_A.csv")
        filas = {}
        for f in planes:
            g, i = r["ganadores"][f], r["ganadores"][f]["indicadores"]
            filas[f] = {"territorio": t, "funcion": f, "candidato": g["candidato"],
                        "fuera_tolerancia": len(g["fuera_tolerancia"]), "desvio_max_pct": round(100 * g["desvio_max"], 2),
                        "max_desvio_personas": round(g["max_desvio_personas"]),
                        "suma_desvio_personas": round(g["suma_desvio_personas"]),
                        "coste_suma_desvio_vs_A": round(g["suma_desvio_personas"]
                                                        - r["ganadores"]["A"]["suma_desvio_personas"]),
                        "pp_medio": r3(i.get("pp_medio")), "pp_min": r3(i.get("pp_min")),
                        "convexidad_media": r3(i.get("convexidad_media")),
                        "pj_partidos": i["pj"]["partidas"], "pj_n": i["pj"]["n"],
                        "pj_pob_fuera_mayoritario": i["pj"]["poblacion_fuera_de_mayoritario"],
                        "ca_partidas": i["ca"]["partidas"], "ca_n": i["ca"]["n"],
                        "comarca_partidas": i["comarca"]["partidas"] if i["comarca"]["n"] else "",
                        "movilidad_cohesion": r3(i["movilidad"]["cohesion"]),
                        "frontera_cortada": r3(i["corte"]["fraccion_peso_corte"])}
        geo = nm.Geometria(nm.shp_de(Path(a.seccionado_dir), nm.anio_seccionado(t)), set(planes["A"]))
        figura(t, geo, planes, pob, filas, sal / f"{t}.png")
        todas += [filas[f] for f in ORDEN if f in filas]
        dist += distritos(t, planes, pob, geo, nombres)
        print(f"{t}: ok", flush=True)
    with open(sal / "TABLA.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNAS, lineterminator="\n")
        w.writeheader()
        w.writerows(todas)
    cab = ["Territorio", "Función", "Fuera de tolerancia", "Desvío máx. %", "Suma de desvíos (personas)",
           "Coste frente a A (personas)", "Polsby-Popper medio", "Convexidad media", "Partidos judiciales partidos",
           "Comarcas agrarias partidas", "Cohesión de movilidad"]
    md = ["| " + " | ".join(cab) + " |", "|" + "---|" * len(cab)]
    for x in todas:
        md.append("| " + " | ".join(str(v) for v in [
            NOMBRE_TERRITORIO.get(x["territorio"], x["territorio"]), x["funcion"], x["fuera_tolerancia"], x["desvio_max_pct"],
            x["suma_desvio_personas"], x["coste_suma_desvio_vs_A"], x["pp_medio"], x["convexidad_media"],
            f"{x['pj_partidos']}/{x['pj_n']}", f"{x['ca_partidas']}/{x['ca_n']}", x["movilidad_cohesion"]]) + " |")
    (sal / "TABLA.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    with open(sal / "DISTRITOS.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(dist[0]), lineterminator="\n")
        w.writeheader()
        w.writerows(dist)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
