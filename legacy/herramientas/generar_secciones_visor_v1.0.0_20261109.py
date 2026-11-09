#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Capa de secciones censales del visor v2, por provincia (T-119).

PROYECTO: Diputado de Distrito
VERSIÓN: 1.0.0 · FECHA: 2026-11-09 · ESTADO: candidato
ANTERIOR: ninguna (fichero nuevo)
QUÉ HACE: une el seccionado INE (ZIP con shapefile, columnas CUSEC y NMUN) con datos/composicion/<territorio>.csv
  (seccion, distrito, poblacion; MANIFEST con sha256) y escribe SALIDA/<cod provincia>.geojson (WGS84, simplificado,
  5 decimales; propiedades s=sección, m=municipio, p=población, d=distrito, t=territorio) y SALIDA/INDEX.json
  (sha256 del seccionado de origen, de cada CSV y de cada GeoJSON). La salida se genera en la publicación; no se versiona.
  Opcional: si falta el seccionado, no escribe nada y sale con 0 (el visor v2 funciona igual sin la capa).
Uso: python herramientas/generar_secciones_visor.py --seccionado ZIP --salida DIR [--composicion DIR] [--tolerancia 0.0001]
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def leer_composicion(carpeta: Path, patron: str = "congreso_*.csv") -> tuple[dict[str, dict], dict[str, str]]:
    """{seccion: {d, p, t}} (solo los territorios congreso_*: un distrito por provincia, como el mapa) y {territorio: sha256 del CSV}; verifica el CSV contra MANIFEST.json si existe."""
    man = carpeta / "MANIFEST.json"
    esperado = json.loads(man.read_text("utf-8")).get("territorios", {}) if man.exists() else {}
    sec: dict[str, dict] = {}
    huellas: dict[str, str] = {}
    for f in sorted(carpeta.glob(patron)):
        datos = f.read_bytes()
        h = sha(datos)
        e = esperado.get(f.stem, {}).get("sha256_csv")
        if e and e != h:
            raise SystemExit(f"composición {f.name}: sha256 {h[:12]} no coincide con MANIFEST ({e[:12]})")
        huellas[f.stem] = h
        for r in csv.DictReader(datos.decode("utf-8").splitlines()):
            sec[r["seccion"]] = {"d": int(r["distrito"]), "p": int(float(r["poblacion"])), "t": f.stem}
    return sec, huellas


def generar(seccionado: Path, salida: Path, composicion: Path, tolerancia: float = 0.0001) -> int:
    if not seccionado.exists():
        print(f"AVISO: sin seccionado ({seccionado}); la capa de secciones se omite.")
        return 0
    import geopandas as gpd  # perezoso: solo hace falta con seccionado

    comp, huellas = leer_composicion(composicion)
    import zipfile
    shp = next(n for n in sorted(zipfile.ZipFile(seccionado).namelist()) if n.lower().endswith(".shp"))
    g = gpd.read_file(f"zip://{seccionado}!{shp}", columns=["CUSEC", "NMUN"])
    g = g[g["CUSEC"].isin(comp)].to_crs(4326)
    set_geo = set(g["CUSEC"])
    g["geometry"] = g.geometry.simplify(tolerancia, preserve_topology=True)
    salida.mkdir(parents=True, exist_ok=True)
    indice = {"schema": "ddd.secciones-visor/1.0", "seccionado_sha256": sha(seccionado.read_bytes()),
              "composicion_sha256": huellas, "provincias": {}}
    sin = {}
    for k in comp:
        if k not in set_geo:
            sin[k[:2]] = sin.get(k[:2], 0) + 1
    for cod, sub in g.groupby(g["CUSEC"].str[:2]):
        feats = []
        for _, r in sub.iterrows():
            c = comp[r["CUSEC"]]
            feats.append({"type": "Feature", "geometry": json.loads(gpd.GeoSeries([r.geometry]).to_json())["features"][0]["geometry"],
                          "properties": {"s": r["CUSEC"], "m": str(r.get("NMUN") or ""), "p": c["p"], "d": c["d"], "t": c["t"]}})
        datos = json.dumps({"type": "FeatureCollection", "features": feats}, ensure_ascii=False, separators=(",", ":"),
                           default=lambda x: round(x, 5)).encode("utf-8")
        datos = _redondear(datos)
        (salida / f"{cod}.geojson").write_bytes(datos)
        indice["provincias"][cod] = {"secciones": len(feats), "bytes": len(datos), "sha256": sha(datos), "sin_geometria": sin.get(cod, 0)}
    (salida / "INDEX.json").write_text(json.dumps(indice, ensure_ascii=False, indent=1), "utf-8")
    print(f"{sum(v['secciones'] for v in indice['provincias'].values())} secciones en {len(indice['provincias'])} provincias")
    return 0


def _redondear(datos: bytes) -> bytes:
    """Recorta coordenadas a 5 decimales (≈1 m) para aligerar el GeoJSON."""
    import re
    return re.sub(rb"(-?\d+\.\d{5})\d+", rb"\1", datos)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--seccionado", type=Path, required=True)
    ap.add_argument("--salida", type=Path, required=True)
    ap.add_argument("--composicion", type=Path, default=RAIZ / "datos" / "composicion")
    ap.add_argument("--tolerancia", type=float, default=0.0001)
    a = ap.parse_args(argv)
    return generar(a.seccionado, a.salida, a.composicion, a.tolerancia)


if __name__ == "__main__":
    sys.exit(main())
