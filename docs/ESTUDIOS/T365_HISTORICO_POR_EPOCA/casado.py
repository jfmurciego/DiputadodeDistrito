#!/usr/bin/env python3
# PROYECTO: Diputado de Distrito · VERSIÓN: 1.0.0 · FECHA: 2026-11-16 · ANTERIOR: ninguna (fichero nuevo)
# MOTIVO: T-365. Casado por provincia de seccionado, población y votos de una elección (sha256 contra el contrato).
# USO: python -I casado.py <contrato_AAAA_MM.json> <carpeta de fuentes> > casado_AAAA_MM.csv
import collections, csv, hashlib, json, sys, zipfile
import geopandas as gpd
c = json.load(open(sys.argv[1], encoding="utf-8")); F = sys.argv[2]
def sha(p): return hashlib.sha256(open(p, "rb").read()).hexdigest()
z = f"{F}/{c['seccionado']['fichero']}"; assert sha(z) == c["seccionado"]["sha256"], z
t = f"{F}/{c['poblacion']['fichero']}"; assert sha(t) == c["poblacion"]["sha256"], t
shp = next(n for n in zipfile.ZipFile(z).namelist() if n.lower().endswith(".shp"))
geo = collections.defaultdict(set)
for x in gpd.read_file(f"zip://{z}!{shp}", columns=["CUSEC"], ignore_geometry=True)["CUSEC"]:
    geo[x[:2]].add(x)
pob = collections.defaultdict(set)
for r in csv.DictReader(open(t, encoding="utf-8")):
    if r["elección"] == c["eleccion"]:
        pob[r["sección"][:2]].add(r["sección"])
w = csv.writer(sys.stdout, lineterminator="\n")
w.writerow(["provincia", "territorio", "secciones_seccionado", "sin_poblacion", "poblacion_sin_geometria", "votos_sin_geometria", "casado"])
for cp, p in sorted(c["provincias"].items()):
    f = f"{F}/nazioenbehatokia/{p['votos']['ruta']}"; assert sha(f) == p["votos"]["sha256"], f
    v = set(json.load(open(f, encoding="utf-8"))["r"])
    a, b, d = geo[cp] - pob[cp], pob[cp] - geo[cp], v - geo[cp]
    w.writerow([cp, p["territorio"], len(geo[cp]), len(a), len(b), len(d), "OK" if not (a or b) else "FALLA"])
