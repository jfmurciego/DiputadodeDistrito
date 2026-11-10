#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PROYECTO: Diputado de Distrito
COMPONENTE: motor 2 — indicadores de naturalidad de los mapas vigentes y de cualquier composición
VERSIÓN: 1.0.0
NOMBRE DE VERSIÓN: Naturalidad · mapas
FECHA: 2026-11-10
ESTADO: candidato (motor 2; producción no lo importa; no lanza nada)
CAMBIOS: fichero nuevo.
MOTIVO: T-172: calcular las métricas de ddd_motor2/naturalidad.py sobre los mapas vigentes (datos/composicion/*.csv)
  y sobre los candidatos de la competición, con la geometría oficial del INE.
ANTERIOR: ninguna (fichero nuevo)
USO: python -m ddd_motor2.naturalidad_mapas vigentes --seccionado-dir <dir con SECC_CE_AAAA0101.shp por año> \
       [--salida datos/naturalidad] [territorio ...]
  --seccionado-dir: carpeta con s2023/, s2024/, s2025/ (el shapefile nacional del INE descomprimido); el año es el
  source_section_year del contrato. Necesita geopandas/shapely (venv aparte; producción no lo usa).
FUENTES (todas en el repo, con sha256 en sus cabeceras o manifiestos): partidos judiciales (configuracion/partidos_
  judiciales.csv, Ley 38/1988); comarcas agrarias (docs/ESTUDIOS/T64_comarcas_partidos/comarcas_agrarias.csv, RD
  1076/2014, nacional); comarcas administrativas de Aragón (inputs/COMARCAS.csv) y Cataluña (comarcas_cataluna_idescat
  .csv); movilidad INE EM-1 (datos/movilidad/). Geometría: seccionado INE (sha256 en la salida).
SALIDA: <salida>/vigentes.csv (una fila por mapa) y <salida>/MANIFEST.json (sha256 de entradas y salida).
  Distancias y áreas en EPSG:3035. Aristas: fronteras compartidas de al menos 1 m entre secciones (contacto de
  vértice no cuenta); el peso de arista es la longitud compartida.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

from . import naturalidad as nat

ROOT = Path(__file__).resolve().parents[1]
COMPOSICION = ROOT / "datos" / "composicion"
PARTIDOS = ROOT / "configuracion" / "partidos_judiciales.csv"
T64 = ROOT / "docs" / "ESTUDIOS" / "T64_comarcas_partidos"
AGRARIAS = T64 / "comarcas_agrarias.csv"
CATALUNA = T64 / "comarcas_cataluna_idescat.csv"
ARAGON = ROOT / "inputs" / "COMARCAS.csv"
MOVILIDAD = ROOT / "datos" / "movilidad"
CRS = "EPSG:3035"
MIN_FRONTERA_M = 1.0
COLUMNAS = ["territorio", "anio_seccionado", "distritos", "secciones", "poblacion", "pp_medio", "pp_min",
            "convexidad_media", "convexidad_min", "aristas", "aristas_corte", "fraccion_frontera_cortada",
            "pj_n", "pj_partidos", "pj_fraccion_pob_mayoritario", "pj_pob_fuera",
            "ca_n", "ca_partidas", "ca_fraccion_pob_mayoritario",
            "comarca_n", "comarca_partidas", "comarca_fraccion_pob_mayoritario",
            "movilidad_cohesion", "movilidad_flujo"]


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def _csv_comentado(p: Path) -> list[dict]:
    with open(p, encoding="utf-8-sig") as f:
        return list(csv.DictReader(line for line in f if not line.startswith("#")))


def tablas_municipio() -> dict[str, dict[str, str]]:
    """{demarcación: {municipio INE: id}} — solo las fuentes del repo."""
    t = {"pj": {r["codigo_ine"]: r["id_partido"] for r in _csv_comentado(PARTIDOS)},
         "ca": {r["codigo_ine"]: r["id_comarca"] for r in _csv_comentado(AGRARIAS)}}
    com = {r["codigo_ine"]: "09-" + r["id_comarca"] for r in _csv_comentado(CATALUNA)}
    for r in _csv_comentado(ARAGON):
        com[str(r["Municipio código"]).zfill(5)] = "02-" + r["Comarca código"]
    t["comarca"] = com
    return t


def movilidad() -> tuple[dict, list[tuple[str, str, float]]]:
    """(índice sección->área, flujos entre áreas) de datos/movilidad/ (EM-1, CC BY 4.0)."""
    sys.path.insert(0, str(ROOT / "herramientas"))
    import movilidad_em_union as m  # noqa: PLC0415
    areas = m.leer_csv(m.AREAS_CSV)
    mapa = m.unir(areas, m.leer_csv(m.CODIGOS_CSV))
    flujos = [(mapa[f["cod_origen"]], mapa[f["cod_destino"]], float(f["flujo"])) for f in m.leer_csv(m.FLUJOS_CSV)
              if f["cod_origen"] in mapa and f["cod_destino"] in mapa]
    return m.indice_secciones(areas), flujos


def grupo_area(sec: str, ind: dict) -> str | None:
    for k in (sec[:10], sec[:7], sec[:5]):
        if k in ind:
            return ind[k][0]
    return None


def anio_seccionado(territorio: str) -> str:
    txt = (ROOT / "territorios" / territorio / "config" / f"{territorio}_2025.yaml").read_text(encoding="utf-8")
    m = re.search(r"source_section_year:\s*(\d{4})", txt)
    if not m:
        raise ValueError(f"{territorio}: el contrato no declara source_section_year")
    return m.group(1)


def leer_composicion(p: Path) -> tuple[dict[str, str], dict[str, int]]:
    asig, pob = {}, {}
    for r in _csv_comentado(p):
        asig[r["seccion"]] = str(r["distrito"])
        pob[r["seccion"]] = int(r["poblacion"])
    return asig, pob


class Geometria:
    """Secciones de un territorio (geopandas, EPSG:3035), su grafo de fronteras y la disolución por distrito."""

    def __init__(self, shp: Path, secciones: set[str]):
        import geopandas as gpd  # noqa: PLC0415
        import shapely  # noqa: PLC0415
        self._shapely = shapely
        provs = sorted({s[:2] for s in secciones})
        where = "CPRO IN (" + ",".join(f"'{p}'" for p in provs) + ")"
        g = gpd.read_file(shp, columns=["CUSEC", "CPRO"], where=where, engine="pyogrio")
        g = g[g["CUSEC"].isin(secciones)].sort_values("CUSEC").reset_index(drop=True)
        faltan = secciones - set(g["CUSEC"])
        if faltan:
            raise ValueError(f"{len(faltan)} secciones sin geometría en {shp.name} (p. ej. {sorted(faltan)[:3]})")
        self.gdf = g.to_crs(CRS)
        self.gdf["geometry"] = shapely.make_valid(self.gdf.geometry.values)
        self._aristas = None

    def aristas(self) -> list[tuple[str, str, float]]:
        if self._aristas is None:
            shp = self._shapely
            geoms = self.gdf.geometry.values
            ids = self.gdf["CUSEC"].tolist()
            i, j = self.gdf.sindex.query(geoms, predicate="intersects")
            sel = i < j
            i, j = i[sel], j[sel]
            bi, bj = shp.boundary(geoms[i]), shp.boundary(geoms[j])
            largo = shp.length(shp.intersection(bi, bj))
            self._aristas = [(ids[a], ids[b], float(w)) for a, b, w in zip(i, j, largo) if w >= MIN_FRONTERA_M]
        return self._aristas

    def distritos(self, asig: dict[str, str]) -> dict[str, object]:
        g = self.gdf.assign(d=self.gdf["CUSEC"].map(asig))
        out = {}
        for d, sub in g.groupby("d", sort=True):
            out[str(d)] = self._shapely.union_all(sub.geometry.values, grid_size=0.01)
        return out


def indicadores(asig: dict[str, str], pob: dict[str, int], geo: Geometria | None, tablas: dict, mov) -> dict:
    dem = {k: {s: v.get(s[:5]) for s in asig} for k, v in tablas.items()}
    movi = ({s: grupo_area(s, mov[0]) for s in asig}, mov[1]) if mov else None
    return nat.resumen(asig, pob, geometrias=geo.distritos(asig) if geo else None,
                       aristas=geo.aristas() if geo else None, demarcacion=dem, movilidad=movi)


def fila(territorio: str, anio: str, asig, pob, r: dict) -> dict:
    def g(k, sub=None):
        v = r.get(k) if sub is None else (r.get(k) or {}).get(sub)
        return "" if v is None else (round(v, 6) if isinstance(v, float) else v)

    def dem(k, campo):
        x = r.get(k) or {}
        return "" if not x.get("n") else (round(x[campo], 6) if isinstance(x.get(campo), float) else x.get(campo, ""))
    return {"territorio": territorio, "anio_seccionado": anio, "distritos": r["distritos"], "secciones": len(asig),
            "poblacion": sum(pob.values()), "pp_medio": g("pp_medio"), "pp_min": g("pp_min"),
            "convexidad_media": g("convexidad_media"), "convexidad_min": g("convexidad_min"),
            "aristas": g("corte", "aristas"), "aristas_corte": g("corte", "cortes"),
            "fraccion_frontera_cortada": g("corte", "fraccion_peso_corte"),
            "pj_n": dem("pj", "n"), "pj_partidos": dem("pj", "partidas"),
            "pj_fraccion_pob_mayoritario": dem("pj", "fraccion_poblacion_en_mayoritario"),
            "pj_pob_fuera": dem("pj", "poblacion_fuera_de_mayoritario"),
            "ca_n": dem("ca", "n"), "ca_partidas": dem("ca", "partidas"),
            "ca_fraccion_pob_mayoritario": dem("ca", "fraccion_poblacion_en_mayoritario"),
            "comarca_n": dem("comarca", "n"), "comarca_partidas": dem("comarca", "partidas"),
            "comarca_fraccion_pob_mayoritario": dem("comarca", "fraccion_poblacion_en_mayoritario"),
            "movilidad_cohesion": g("movilidad", "cohesion"), "movilidad_flujo": round((r.get("movilidad") or {}).get("flujo", 0))}


def shp_de(dirbase: Path, anio: str) -> Path:
    p = dirbase / f"s{anio}" / f"SECC_CE_{anio}0101.shp"
    if not p.exists():
        raise FileNotFoundError(p)
    return p


def cmd_vigentes(a) -> int:
    man = json.loads((COMPOSICION / "MANIFEST.json").read_text(encoding="utf-8"))["territorios"]
    terrs = a.territorios or sorted(man)
    tablas, mov = tablas_municipio(), movilidad()
    salida = Path(a.salida)
    salida.mkdir(parents=True, exist_ok=True)
    filas, errores, shps = [], {}, {}
    for t in terrs:
        try:
            anio = anio_seccionado(t)
            shp = shp_de(Path(a.seccionado_dir), anio)
            shps[anio] = shp
            asig, pob = leer_composicion(COMPOSICION / f"{t}.csv")
            geo = Geometria(shp, set(asig))
            filas.append(fila(t, anio, asig, pob, indicadores(asig, pob, geo, tablas, mov)))
            print(f"{t}: ok", flush=True)
        except Exception as e:  # el mapa sale como error explícito, no se omite en silencio
            errores[t] = f"{type(e).__name__}: {e}"
            print(f"{t}: ERROR {errores[t]}", flush=True)
    out = salida / "vigentes.csv"
    with open(out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNAS, lineterminator="\n")
        w.writeheader()
        w.writerows(filas)
    fuentes = [PARTIDOS, AGRARIAS, CATALUNA, ARAGON, COMPOSICION / "MANIFEST.json",
               *(MOVILIDAD / n for n in ("areas_movilidad_2019.csv", "flujos_em1_origen_destino.csv", "codigos_flujo.csv"))]
    manifest = {"schema": "ddd.naturalidad-vigentes/1.0", "motor2_naturalidad": nat.VERSION, "crs": CRS,
                "min_frontera_m": MIN_FRONTERA_M,
                "seccionado_ine": {k: {"fichero": v.name, "sha256_shp": sha256(v),
                                       "url_zip": f"https://www.ine.es/prodyser/cartografia/seccionado_{k}.zip"}
                                   for k, v in sorted(shps.items())},
                "fuentes": {str(p.relative_to(ROOT)): sha256(p) for p in fuentes},
                "errores": errores, "salida": {"vigentes.csv": sha256(out)}}
    (salida / "MANIFEST.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return 0 if not errores else 1


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n")[3])
    s = p.add_subparsers(dest="cmd", required=True)
    v = s.add_parser("vigentes")
    v.add_argument("--seccionado-dir", required=True)
    v.add_argument("--salida", default=str(ROOT / "datos" / "naturalidad"))
    v.add_argument("territorios", nargs="*")
    a = p.parse_args(argv)
    return cmd_vigentes(a)


if __name__ == "__main__":
    sys.exit(main())
