#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Equivalencia de los seccionados INE históricos (2012-2024) con el seccionado vigente 2025 (T-85).

PROYECTO: Diputado de Distrito
VERSIÓN: 1.0.0 · FECHA: 2026-11-07 · ESTADO: candidato
CAMBIOS: 1.0.0: fichero nuevo.
MOTIVO: decisiones D-9, D-10 y D-11 del propietario: las 6 generales 2011-2023 se pasan a los distritos vigentes, lo que
  exige llevar los votos de cada sección histórica a las secciones del seccionado vigente.
ANTERIOR: ninguna (fichero nuevo)
QUÉ HACE: por provincia y seccionado histórico (geometrías del espejo T-89, geo/sekzioak/<año>/<cpro>.json, WGS84)
  interseca cada sección del seccionado INE histórico (www.ine.es/prodyser/cartografia/seccionado_<año>.zip, ETRS89 H30;
  la geometría simplificada del espejo T-89 da hasta un 35 % de falsos repartos urbanos y no se usa) con las del
  seccionado INE 2025 (inputs/partes/seccionado_2025.zip, sha256 en MANIFEST_PARTES.sha256). Los votos son los del
  espejo T-89 (data/<elección>/sekzioa/<cpro>.json, huellas en orchestracion/fuente_nazioenbehatokia.json). Una sección es 1:1 si al menos `umbral` de su área cae en una vigente y esa vigente procede
  en al menos `umbral` de ella; si no, se reparte con dos pesos alternativos: área (a(h∩v)/a(h)) y población
  (a(h∩v)/a(v)·pob2025(v), normalizado; padrón INE 65034). Las astillas de menos de `astilla` del área histórica se
  descartan (ruido de digitalización). El informe da, por provincia y elección, el % de votos a
  candidaturas que no queda 1:1 y el % de votos que cambia de sección vigente según se use un peso u otro.
  No decide el peso: lo fija el propietario.
Uso: python herramientas/equivalencia_seccionados.py --espejo DIR --historicos DIR --seccionado ZIP --padron ZIP
       --salida JSON [--tablas DIR] [--provincias 28 42]
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import re
import sys
import zipfile
from collections import Counter, defaultdict
from pathlib import Path

from shapely.strtree import STRtree

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = "ddd.equivalencia-seccionados/1.0"
UMBRAL = 0.95
ASTILLA = 0.01
MANIFIESTO_ESPEJO = "orchestracion/fuente_nazioenbehatokia.json"
URL_INE = "https://www.ine.es/prodyser/cartografia/"


# --- núcleo (geometrías shapely ya proyectadas a un CRS métrico) ------------------------------------------------
def equivalencia(hist: dict, vig: dict, pob: dict[str, int], umbral: float = UMBRAL, astilla: float = ASTILLA) -> dict:
    """hist/vig = {cusec: geometría}. Devuelve {cusec_hist: {"tipo": "1:1"|"reparto"|"sin_vigente",
    "area": {cusec_vig: w}, "poblacion": {cusec_vig: w}}}; cada reparto suma 1."""
    claves = list(vig)
    arbol = STRtree([vig[k] for k in claves])
    out = {}
    for h, gh in hist.items():
        ah = gh.area
        trozos = {}
        if ah > 0:
            for i in arbol.query(gh):
                a = gh.intersection(vig[claves[i]]).area
                if a / ah >= astilla:
                    trozos[claves[i]] = a
        if not trozos:
            out[h] = {"tipo": "sin_vigente", "area": {}, "poblacion": {}}
            continue
        total = sum(trozos.values())
        area = {v: a / total for v, a in trozos.items()}
        bruto = {v: a / vig[v].area * pob.get(v, 0) for v, a in trozos.items()}
        sp = sum(bruto.values())
        poblacion = {v: x / sp for v, x in bruto.items()} if sp > 0 else dict(area)
        v_max = max(trozos, key=trozos.get)
        es_1a1 = trozos[v_max] / ah >= umbral and trozos[v_max] / vig[v_max].area >= umbral
        if es_1a1:
            area = poblacion = {v_max: 1.0}
        out[h] = {"tipo": "1:1" if es_1a1 else "reparto", "area": area, "poblacion": poblacion}
    return out


def completar_geometrias(votos: dict, año: int, por_año: dict[int, dict]) -> tuple[dict, list[str]]:
    """Geometrías del seccionado `año`; las secciones con votos que no están en él se toman del seccionado más
    cercano que las tenga (el Observatorio usa a veces el código de un año contiguo). Devuelve (hist, tomadas)."""
    hist = dict(por_año[año])
    otros = sorted((y for y in por_año if y != año), key=lambda y: (abs(y - año), y))
    tomadas = []
    for h in sorted(set(votos) - set(hist)):
        y = next((y for y in otros if h in por_año[y]), None)
        if y is not None:
            hist[h] = por_año[y][h]
            tomadas.append(h)
    return hist, tomadas


def informe_eleccion(votos: dict, eq: dict) -> dict:
    """votos = {cusec_hist: {"votos_candidaturas": n, "votos": {sigla: n}}} (lector de T-89)."""
    total = uno = sin_geo = sin_vig = 0
    por_area: dict = defaultdict(Counter)
    por_pob: dict = defaultdict(Counter)
    for h, s in votos.items():
        n = s["votos_candidaturas"]
        total += n
        e = eq.get(h)
        if e is None:
            sin_geo += n
            continue
        if e["tipo"] == "1:1":
            uno += n
        elif e["tipo"] == "sin_vigente":
            sin_vig += n
        for p, x in s["votos"].items():
            for v, w in e["area"].items():
                por_area[v][p] += x * w
            for v, w in e["poblacion"].items():
                por_pob[v][p] += x * w
    dif = sum(abs(por_area[v][p] - por_pob[v][p]) for v in set(por_area) | set(por_pob)
              for p in set(por_area[v]) | set(por_pob[v])) / 2
    pct = (lambda x: round(100 * x / total, 3) if total else 0.0)
    return {"votos": total, "pct_1a1": pct(uno), "pct_no_1a1": pct(total - uno), "pct_sin_geometria": pct(sin_geo),
            "pct_sin_vigente": pct(sin_vig), "pct_difiere_area_poblacion": pct(dif)}


# --- lectura de fuentes ----------------------------------------------------------------------------------------
def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def leer_seccionado(zip_seccionado: Path) -> dict[str, dict]:
    """{cpro: {cusec: geometría}} de un shapefile de seccionado INE (EPSG:25830)."""
    import geopandas as gpd
    with zipfile.ZipFile(zip_seccionado) as z:
        shp = next(n for n in z.namelist() if n.lower().endswith(".shp"))
    gdf = gpd.read_file(f"zip://{zip_seccionado}!{shp}", columns=["CUSEC"]).to_crs(25830)
    out: dict[str, dict] = defaultdict(dict)
    for cusec, g in zip(gdf["CUSEC"], gdf.geometry):
        out[cusec[:2]][cusec] = g if g.is_valid else g.buffer(0)
    return out


def leer_padron(zip_padron: Path, año: str = "2025") -> dict[str, int]:
    """{cusec: población} del INE 65034 (Total, Todas las edades, periodo `año`)."""
    out = {}
    with zipfile.ZipFile(zip_padron) as z, z.open("65034.csv") as crudo:
        for linea in io.TextIOWrapper(crudo, encoding="utf-8-sig"):
            p = linea.rstrip("\r\n").split("\t")
            if len(p) == 8 and p[6] == año and p[4] == "Total" and p[5] == "Todas las edades":
                m = re.match(r"^(\d{10}) ", p[3])
                n = p[7].strip('"').replace(".", "")
                if m and n.isdigit():
                    out[m.group(1)] = int(n)
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--espejo", type=Path, required=True, help="directorio del espejo T-89 (data/)")
    ap.add_argument("--historicos", type=Path, required=True, help="directorio con seccionado_<año>.zip del INE")
    ap.add_argument("--seccionado", type=Path, required=True)
    ap.add_argument("--padron", type=Path, required=True)
    ap.add_argument("--salida", type=Path, required=True)
    ap.add_argument("--tablas", type=Path, help="directorio para las tablas CSV de equivalencia (opcional)")
    ap.add_argument("--provincias", nargs="*")
    a = ap.parse_args(argv)
    sys.path.insert(0, str(Path(__file__).parent))
    from fuente_nazioenbehatokia import leer_provincia
    espejo = json.loads((ROOT / MANIFIESTO_ESPEJO).read_text(encoding="utf-8"))
    for e in espejo["elecciones"]:
        for ruta, f in espejo["ficheros"].items():
            if ruta.startswith(f"data/{e['clave']}/") and sha256(a.espejo / ruta) != f["sha256"]:
                raise SystemExit(f"HUELLA_ESPEJO_DISTINTA {ruta}")
    vig, pob = leer_seccionado(a.seccionado), leer_padron(a.padron)
    provs = a.provincias or sorted(vig)
    res, historicos, todos = {}, {}, {}
    for e in espejo["elecciones"]:
        año = e["seccionado"]
        z = a.historicos / f"seccionado_{año}.zip"
        historicos[str(año)] = {"url": f"{URL_INE}seccionado_{año}.zip", "sha256": sha256(z)}
        todos[año] = leer_seccionado(z)
    for e in espejo["elecciones"]:
        clave, año = e["clave"], e["seccionado"]
        for c in provs:
            votos = leer_provincia(json.loads((a.espejo / f"data/{clave}/sekzioa/{c}.json").read_text(encoding="utf-8")))
            hist, otro = completar_geometrias(votos, año, {y: t.get(c, {}) for y, t in todos.items()})
            eq = equivalencia(hist, vig[c], pob)
            r = informe_eleccion(votos, eq)
            r["pct_geometria_otro_seccionado"] = round(100 * sum(votos[h]["votos_candidaturas"] for h in otro)
                                                       / r["votos"], 3) if r["votos"] else 0.0
            r.update(seccionado=año, secciones=len(eq), secciones_reparto=sum(x["tipo"] != "1:1" for x in eq.values()))
            res.setdefault(c, {})[clave] = r
            if a.tablas:
                p = a.tablas / str(año) / f"{c}.csv"
                p.parent.mkdir(parents=True, exist_ok=True)
                with open(p, "w", encoding="utf-8", newline="") as f:
                    w = csv.writer(f, lineterminator="\n")
                    w.writerow(["cusec_historica", "cusec_vigente", "tipo", "peso_area", "peso_poblacion"])
                    for h, x in sorted(eq.items()):
                        for v in sorted(set(x["area"]) | set(x["poblacion"])):
                            w.writerow([h, v, x["tipo"], f"{x['area'].get(v, 0):.6f}", f"{x['poblacion'].get(v, 0):.6f}"])
            print(c, clave, r["pct_no_1a1"], r["pct_difiere_area_poblacion"], flush=True)
    salida = {"schema": SCHEMA, "umbral_1a1": UMBRAL, "astilla": ASTILLA, "vigente": "INE seccionado 2025",
              "fuentes": {"seccionado_2025": {"fichero": a.seccionado.name, "sha256": sha256(a.seccionado)},
                          "padron_65034": {"fichero": a.padron.name, "sha256": sha256(a.padron), "periodo": "2025"},
                          "historicos": historicos,
                          "espejo": {"manifiesto": MANIFIESTO_ESPEJO, "sha256": sha256(ROOT / MANIFIESTO_ESPEJO)}},
              "provincias": res}
    a.salida.parent.mkdir(parents=True, exist_ok=True)
    a.salida.write_text(json.dumps(salida, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
