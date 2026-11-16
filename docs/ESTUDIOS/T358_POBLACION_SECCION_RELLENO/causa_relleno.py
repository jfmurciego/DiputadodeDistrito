#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""T-358: causa del relleno. Para cada sección rellenada: ¿existe su código en el seccionado INE del año de la elección?
¿El Atlas del año la trae como «.»? Y las secciones del seccionado que NO entran en la tabla (Atlas omite/no lista la sección).
Uso: python -I causa_relleno.py <30832.csv> <seccionado_2015.zip> <seccionado_2016.zip> <seccionado_2019.zip> <SHA256SUMS.txt> <salida.csv>
Verifica sha256 de los 4 ficheros contra SHA256SUMS.txt. Solo lectura de ficheros locales.
HISTÓRICO (T-364): reproduce el estudio de T-358 y solo funciona con la herramienta 1.0.0 (relleno por año más cercano), que ya no está en
herramientas/ (copia en legacy/herramientas/poblacion_seccion_historica_v1.0.0_20261115.py). Con la 1.1.0 aborta con un aviso."""
import csv, io, struct, sys, zipfile, collections
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from herramientas import poblacion_seccion_historica as ph  # noqa: E402

def dbf_cusec(zpath):
    with zipfile.ZipFile(zpath) as z:
        nom = next(n for n in z.namelist() if n.lower().endswith(".dbf"))
        b = z.read(nom)
    n, hl, rl = struct.unpack("<IHH", b[4:12]); campos = []; o = 32
    while b[o] != 13: campos.append((b[o:o+11].split(b"\0")[0].decode(), b[o+16])); o += 32
    off = 1
    for nm, l in campos:
        if nm == "CUSEC": ini, ln = off, l
        off += l
    return {b[hl+i*rl+ini:hl+i*rl+ini+ln].decode("latin1").strip() for i in range(n)} - {""}

def main(a):
    if ph.VERSION != "1.0.0":
        sys.exit(f"ERROR: script histórico de T-358, solo válido con poblacion_seccion_historica 1.0.0 (hay {ph.VERSION}); ver legacy/herramientas/")
    atlas_p, s15, s16, s19, sumas_p, out = a
    sumas = ph.leer_sumas(sumas_p)
    ph.verificar(atlas_p, ph.NOMBRE_ATLAS, sumas)
    for p, y in ((s15, 2015), (s16, 2016), (s19, 2019)): ph.verificar(p, f"seccionado_{y}.zip", sumas)  # nombre oficial en SHA256SUMS
    atlas = ph.leer_atlas(atlas_p)
    sec = {"2015-12": dbf_cusec(s15), "2016-06": dbf_cusec(s16), "2019-04": dbf_cusec(s19)}
    filas = []
    for el, anio in (("2015-12", 2015), ("2016-06", 2016), ("2019-04", 2019)):
        tab = ph.poblacion_eleccion(atlas[anio], anio, atlas)
        en_tabla = {f[0] for f in tab}
        rell = [f for f in tab if f[2] == "relleno"]
        por_prov = collections.defaultdict(lambda: collections.Counter())
        mun = collections.defaultdict(collections.Counter)
        poblacion = collections.Counter(); relpob = collections.Counter(); fuera_s = collections.Counter()
        for s, pob, o, ya in tab:
            poblacion[s[:2]] += pob or 0
        for s, pob, o, ya in rell:
            p = s[:2]; por_prov[p]["relleno"] += 1; relpob[p] += pob; mun[p][s[:5]] += 1
            por_prov[p]["relleno_en_seccionado" if s in sec[el] else "relleno_NO_en_seccionado"] += 1
            por_prov[p]["punto_en_atlas_del_anio"] += atlas[anio][s] == "."
        # secciones del seccionado que no entran en la tabla: el Atlas del año las omite (vacío) o no las lista
        faltan = collections.defaultdict(collections.Counter)
        for s in sec[el] - en_tabla:
            faltan[s[:2]]["atlas_vacio" if atlas[anio].get(s) == "" else "no_listada_en_atlas"] += 1
        for p in sorted(set(por_prov) | set(faltan)):
            c = por_prov[p]; m = mun[p].most_common(1)
            filas.append({"elección": el, "provincia": p, "secciones_relleno": c["relleno"],
                "relleno_en_seccionado": c["relleno_en_seccionado"], "relleno_NO_en_seccionado": c["relleno_NO_en_seccionado"],
                "relleno_con_punto_en_atlas_del_año": c["punto_en_atlas_del_anio"],
                "población_rellena": relpob[p], "población": poblacion[p],
                "pct": ph.pct(relpob[p], poblacion[p]),
                "municipio_top": m[0][0] if m else "", "secciones_municipio_top": m[0][1] if m else 0,
                "seccionado_fuera_de_tabla_atlas_vacio": faltan[p]["atlas_vacio"],
                "seccionado_fuera_de_tabla_no_listada": faltan[p]["no_listada_en_atlas"]})
    with open(out, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(filas[0]), lineterminator="\n"); w.writeheader(); w.writerows(filas)
    print(ph.sha256_fichero(out))

main(sys.argv[1:])
