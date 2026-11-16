#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Población por sección censal para el histórico de las generales (T-358, D-125/D-126). Solo cálculo.

PROYECTO: Diputado de Distrito
VERSIÓN: 1.0.0 · FECHA: 2026-11-15 · ESTADO: candidato
ANTERIOR: ninguna (fichero nuevo)
CAMBIOS: 1.0.0: fichero nuevo (revisión de #832: falla ante líneas Población mal formadas en vez de descartarlas; MARCA también si hay sin_dato).
MOTIVO: D-126 (propietario, 15-11): población por sección de cada elección del histórico: 2011-11 = Censo 2011
  (indicador t1_1, 1-nov-2011); 2015-12, 2016-06 y 2019-04 = Atlas INE tabla 30832 del año de la elección; 2019-11 = Atlas 2020.
  Nunca censo electoral como población.
QUÉ HACE: lee dos ficheros locales (el CSV 30832 y el ZIP de indicadores del Censo 2011), verifica su sha256 contra
  SHA256SUMS.txt (docs/ESTUDIOS/T357_PADRON_SECCION_2011_2020) y falla si no coincide. No descarga nada.
  Criterio explícito: «.» = dato no publicado → se RELLENA; vacío = sección inexistente ese año → NO se rellena (ni aparece).
  Relleno: valor de la MISMA sección en el año del Atlas más cercano al de la fuente que lo tenga (empate: el anterior),
  marcado sección a sección (origen=relleno, año_fuente_relleno). Sin ningún año con dato: origen=sin_dato (se cuenta aparte).
  Informe por provincia: secciones, población, % de población rellenada y marca si > 1 % o si alguna sección queda sin_dato (población 0 en el denominador; no se publica sin decisión del propietario).
USO: python -I herramientas/poblacion_seccion_historica.py --atlas 30832.csv --censo indicadores_seccion_censal_csv.zip \\
       --sumas docs/ESTUDIOS/T357_PADRON_SECCION_2011_2020/SHA256SUMS.txt --tabla tabla.csv --informe informe_provincias.csv
Determinista: sin reloj, orden por elección y sección, saltos de línea «\\n».
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import sys
import zipfile
from pathlib import Path

VERSION = "1.0.0"
NOMBRE_ATLAS = "30832.csv"
NOMBRE_CENSO = "indicadores_seccion_censal_csv.zip"
UMBRAL_MARCA_PCT = 1  # > 1 % de población rellenada → MARCA
# elección → (fuente, año de la fuente)
ELECCIONES = {
    "2011-11": ("censo", 2011),
    "2015-12": ("atlas", 2015),
    "2016-06": ("atlas", 2016),
    "2019-04": ("atlas", 2019),
    "2019-11": ("atlas", 2020),
}
PUNTO = "."  # no publicado
VACIO = ""   # sección inexistente ese año


class ErrorFuente(Exception):
    pass


def sha256_fichero(ruta) -> str:
    h = hashlib.sha256()
    with open(ruta, "rb") as f:
        for bloque in iter(lambda: f.read(1 << 20), b""):
            h.update(bloque)
    return h.hexdigest()


def leer_sumas(ruta) -> dict[str, str]:
    """SHA256SUMS.txt (`sha256  bytes  URL`) → {nombre de fichero de la URL: sha256}."""
    out: dict[str, str] = {}
    for linea in Path(ruta).read_text(encoding="utf-8").splitlines():
        if not linea.strip() or linea.lstrip().startswith("#"):
            continue
        p = linea.split()
        url = next((x for x in p[1:] if "://" in x), None)
        if len(p[0]) == 64 and url:
            out[url.rsplit("/", 1)[-1]] = p[0].lower()
    return out


def verificar(ruta, nombre: str, sumas: dict[str, str]) -> str:
    if nombre not in sumas:
        raise ErrorFuente(f"{nombre}: sin sha256 en SHA256SUMS.txt")
    real = sha256_fichero(ruta)
    if real != sumas[nombre]:
        raise ErrorFuente(f"{nombre}: sha256 distinto (esperado {sumas[nombre]}, real {real})")
    return real


def _num(s: str):
    """'1.357' → 1357; '.' o '..' → PUNTO; '' o '""' → VACIO; otro texto → error."""
    s = s.strip()
    if s in ('""', "''"):  # el CSV 30832 marca la sección inexistente con comillas literales
        s = ""
    if s == "..":  # 18 filas, solo 2022 en la descarga acreditada: se trata como «.» (no publicado)
        return PUNTO
    if s == "" or s == PUNTO:
        return s
    t = s.replace(".", "")
    if not t.isdigit():
        raise ErrorFuente(f"valor de población no numérico: {s!r}")
    return int(t)


def leer_atlas(ruta) -> dict[int, dict[str, object]]:
    """{año: {sección(10 dígitos): int | '.' | ''}} del indicador «Población» a nivel de sección."""
    out: dict[int, dict[str, object]] = {}
    with open(ruta, encoding="utf-8-sig", newline="") as f:
        for n, linea in enumerate(f, 1):
            p = linea.rstrip("\r\n").split(";")
            if "Población" not in p:
                continue  # cabecera, otros indicadores y líneas en blanco: no son del indicador
            if len(p) != 6 or p[3] != "Población":
                raise ErrorFuente(f"línea {n} del indicador Población con formato inesperado: {linea[:120]!r}")
            if not p[2]:
                continue  # filas de municipio o distrito (no de sección)
            cod = p[2][:10]
            if len(cod) != 10 or not cod.isdigit() or not p[4].isdigit():
                raise ErrorFuente(f"línea {n}: sección o periodo no válidos: {linea[:120]!r}")
            out.setdefault(int(p[4]), {})[cod] = _num(p[5])
    return out


def leer_censo(ruta) -> dict[str, object]:
    """{sección: t1_1} de todos los C2011_ccaa*_Indicadores.csv del ZIP (orden por nombre)."""
    out: dict[str, object] = {}
    with zipfile.ZipFile(ruta) as z:
        for nombre in sorted(n for n in z.namelist() if n.endswith("_Indicadores.csv")):
            texto = io.TextIOWrapper(z.open(nombre), encoding="utf-8-sig", newline="")
            for d in csv.DictReader(texto):
                cod = d["cpro"].zfill(2) + d["cmun"].zfill(3) + d["dist"].zfill(2) + d["secc"].zfill(3)
                out[cod] = _num(d["t1_1"])
    return out


def anios_por_cercania(objetivo: int, disponibles) -> list[int]:
    """Años ordenados por distancia al objetivo; empate: el anterior."""
    return sorted(disponibles, key=lambda a: (abs(a - objetivo), a))


def poblacion_eleccion(fuente: dict[str, object], anio_fuente: int, atlas: dict[int, dict[str, object]]):
    """Filas (sección, población|None, origen, año_relleno|None) ordenadas por sección.

    Universo = secciones con valor o «.» en la fuente; las vacías no se rellenan ni aparecen."""
    orden = anios_por_cercania(anio_fuente, atlas)
    filas = []
    for sec in sorted(fuente):
        v = fuente[sec]
        if v == VACIO:
            continue
        if isinstance(v, int):
            filas.append((sec, v, "dato", None))
            continue
        for a in orden:
            w = atlas[a].get(sec)
            if isinstance(w, int):
                filas.append((sec, w, "relleno", a))
                break
        else:
            filas.append((sec, None, "sin_dato", None))
    return filas


def informe_provincias(eleccion: str, filas) -> list[dict]:
    acc: dict[str, dict] = {}
    for sec, pob, origen, _ in filas:
        d = acc.setdefault(sec[:2], dict(secciones=0, relleno=0, sin_dato=0, poblacion=0, pob_relleno=0))
        d["secciones"] += 1
        if origen == "sin_dato":
            d["sin_dato"] += 1
            continue
        d["poblacion"] += pob
        if origen == "relleno":
            d["relleno"] += 1
            d["pob_relleno"] += pob
    out = []
    for prov in sorted(acc):
        d = acc[prov]
        out.append({
            "elección": eleccion, "provincia": prov, "secciones": d["secciones"],
            "secciones_relleno": d["relleno"], "secciones_sin_dato": d["sin_dato"],
            "población": d["poblacion"], "población_rellena": d["pob_relleno"],
            "pct_relleno": pct(d["pob_relleno"], d["poblacion"]),
            "marca": "MARCA" if (d["pob_relleno"] * 100 > UMBRAL_MARCA_PCT * d["poblacion"] or d["sin_dato"]) else "",
        })
    return out


def pct(parte: int, total: int) -> str:
    """% con 4 decimales, aritmética entera (redondeo half-up), sin flotantes."""
    if total == 0:
        return "0.0000"
    n = (parte * 1_000_000 + total // 2) // total  # centésimas de punto porcentual ×100
    return f"{n // 10000}.{n % 10000:04d}"


def calcular(atlas, censo):
    tabla, informe = [], []
    for el in sorted(ELECCIONES):
        tipo, anio = ELECCIONES[el]
        fuente = censo if tipo == "censo" else atlas.get(anio)
        if not fuente:
            raise ErrorFuente(f"{el}: la fuente {tipo} {anio} no tiene secciones")
        filas = poblacion_eleccion(fuente, anio, atlas)
        tabla += [(el,) + f for f in filas]
        informe += informe_provincias(el, filas)
    return tabla, informe


def escribir_tabla(ruta, tabla) -> str:
    with open(ruta, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["elección", "sección", "población", "origen", "año_fuente_relleno"])
        for el, sec, pob, origen, anio in tabla:
            w.writerow([el, sec, "" if pob is None else pob, origen, "" if anio is None else anio])
    return sha256_fichero(ruta)


def escribir_informe(ruta, informe) -> str:
    cols = ["elección", "provincia", "secciones", "secciones_relleno", "secciones_sin_dato",
            "población", "población_rellena", "pct_relleno", "marca"]
    with open(ruta, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols, lineterminator="\n")
        w.writeheader()
        w.writerows(informe)
    return sha256_fichero(ruta)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--atlas", required=True, help="CSV 30832 del INE (local)")
    ap.add_argument("--censo", required=True, help="ZIP indicadores_seccion_censal_csv del Censo 2011 (local)")
    ap.add_argument("--sumas", required=True, help="SHA256SUMS.txt")
    ap.add_argument("--tabla", required=True)
    ap.add_argument("--informe", required=True)
    a = ap.parse_args(argv)
    try:
        sumas = leer_sumas(a.sumas)
        verificar(a.atlas, NOMBRE_ATLAS, sumas)
        verificar(a.censo, NOMBRE_CENSO, sumas)
        tabla, informe = calcular(leer_atlas(a.atlas), leer_censo(a.censo))
    except (ErrorFuente, OSError, zipfile.BadZipFile) as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1
    print("tabla sha256", escribir_tabla(a.tabla, tabla), len(tabla), "filas")
    print("informe sha256", escribir_informe(a.informe, informe))
    marcadas = sorted({(r["elección"], r["provincia"]) for r in informe if r["marca"]})
    print("provincias MARCA (>1 %):", len(marcadas), marcadas)
    return 0


if __name__ == "__main__":
    sys.exit(main())
