#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Población por sección censal para el histórico de las generales (T-358/T-364, D-125/D-126/D-128). Solo cálculo.

PROYECTO: Diputado de Distrito
VERSIÓN: 1.1.0 · FECHA: 2026-11-16 · ESTADO: candidato
ANTERIOR: legacy/herramientas/poblacion_seccion_historica_v1.0.0_20261115.py
CAMBIOS: 1.1.0 (T-364, D-128): el relleno de D-126 (año más cercano) pasa a INTERPOLACIÓN LINEAL entre el año anterior y el
  siguiente de la misma sección (año más cercano si solo hay un lado) y AJUSTE PROPORCIONAL por municipio a la población oficial
  del INE (tabla 29005, padrón); salida por elección con columnas sección, población, origen, ajustada, años_fuente; informe por
  provincia sobre población estimada, municipios ajustados y desajuste medio. 1.0.0: fichero nuevo.
MOTIVO: D-126 (propietario, 15-11): población por sección de cada elección del histórico: 2011-11 = Censo 2011
  (indicador t1_1, 1-nov-2011); 2015-12, 2016-06 y 2019-04 = Atlas INE tabla 30832 del año de la elección; 2019-11 = Atlas 2020.
  Nunca censo electoral como población.
QUÉ HACE: lee tres ficheros locales (CSV 30832, ZIP de indicadores del Censo 2011 y CSV 29005 «Cifras oficiales del padrón por
  municipio»), verifica su sha256 contra los SHA256SUMS.txt dados (T357 y T364) y falla si no coincide. No descarga nada.
  Criterio de marcadores: «.» = dato no publicado → se ESTIMA; vacío = sección inexistente ese año → NO se estima (ni aparece).
  0) Secciones del SECCIONADO INE del año de la elección que la fuente NO TRAE CON VALOR (no listadas, o listadas como vacío «""»;
     un vacío SIN sección en el seccionado sigue siendo sección inexistente) se tratan igual que las «.» (origen=no_listada; el
     método consta en años_fuente); nunca población 0 ni fusión de secciones. Falla cerrado si falta el seccionado, no se puede
     leer, o más de un 1 % de secciones de un lado no tiene pareja en el otro. Las secciones de la fuente que el seccionado no
     tiene se mantienen y se cuentan (secciones_sin_seccionado). 2011-11 no usa seccionado.
  1) Estimación de cada «.» (origen): INTERPOLACIÓN LINEAL entre el año anterior y el siguiente con dato de ESA misma sección
     (los más próximos a cada lado; redondeo half-up entero) → «interpolada»; si solo hay dato en un lado, el año más cercano con
     dato → «mas_cercana»; sin ningún dato → «sin_dato» (se cuenta aparte; con --estricto falla). Las no listadas llevan origen
     «no_listada» (interpoladas o más cercanas según los años_fuente).
  2) AJUSTE por municipio (solo elecciones con fuente Atlas, contra la población oficial del año de esa fuente): residuo = oficial −
     suma de secciones de dato publicado. Si residuo > 0, las secciones ESTIMADAS del municipio se reescalan proporcionalmente para
     sumar exactamente el residuo (restos mayores; empate por sección ascendente); las de dato publicado no se tocan; «ajustada»=sí
     en las estimadas del municipio reescalado (si ya sumaban el residuo, no hay cambio). AVISO y SIN ajuste (valores de la
     estimación) si: residuo ≤ 0 (la suma publicada ya iguala o excede la oficial), el municipio tiene secciones sin_dato, o no figura
     en la fuente oficial. 2011-11 (Censo, 1-nov-2011) no se ajusta: el padrón es a 1 de enero y no se ha verificado un fichero
     oficial de población municipal censal (NO VERIFICADO); esa elección no tiene «.» en la descarga acreditada.
  3) Informe por provincia: secciones, población, % de población ESTIMADA (interpolada + más cercana, ya ajustada), MARCA si > 1 % o
     si alguna sección queda sin_dato, municipios ajustados y desajuste medio (|oficial − suma antes del ajuste| / oficial).
USO: python -I herramientas/poblacion_seccion_historica.py --atlas 30832.csv --censo indicadores_seccion_censal_csv.zip \\
       --oficial 29005.csv --seccionados <dir con seccionado_AAAA.zip> --sumas docs/ESTUDIOS/T357_PADRON_SECCION_2011_2020/SHA256SUMS.txt \\
       docs/ESTUDIOS/T364_POBLACION_SECCION_INTERPOLADA/SHA256SUMS.txt --salida <directorio>
  Escribe poblacion_seccion_<elección>.csv (interfaz para T-365: sección,población,origen,ajustada,años_fuente),
  informe_provincias.csv e informe_municipios.csv. Con --estricto y algún aviso de municipio: sale con 2 y NO escribe las tablas.
Determinista: sin reloj, orden por elección y sección, saltos de línea «\\n».
"""
from __future__ import annotations

import argparse
import csv
from fractions import Fraction
import hashlib
import io
import struct
import sys
import zipfile
from pathlib import Path

VERSION = "1.1.0"
NOMBRE_ATLAS = "30832.csv"
NOMBRE_CENSO = "indicadores_seccion_censal_csv.zip"
NOMBRE_OFICIAL = "29005.csv"
UMBRAL_MARCA_PCT = 1  # > 1 % de población estimada → MARCA
# elección → (fuente, año de la fuente); el padrón oficial se compara solo con fuente atlas (mismo año)
ELECCIONES = {
    "2011-11": ("censo", 2011),
    "2015-12": ("atlas", 2015),
    "2016-06": ("atlas", 2016),
    "2019-04": ("atlas", 2019),
    "2019-11": ("atlas", 2020),
}
# elección → año del seccionado INE (secciones existentes en la fecha de la elección)
# 2011-11: None (el Censo 2011 es el universo; no hay seccionado acreditado a la fecha de esa elección: NO VERIFICADO)
SECCIONADO = {"2011-11": None, "2015-12": 2015, "2016-06": 2016, "2019-04": 2019, "2019-11": 2020}
TOPE_DESCUADRE_PCT = 1  # > 1 % de las secciones de un lado sin pareja en el otro (seccionado ↔ fuente) → falla cerrado
COLUMNAS_TABLA = ["sección", "población", "origen", "ajustada", "años_fuente"]
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




def leer_oficial(ruta, anios) -> dict[int, dict[str, int]]:
    """{año: {municipio(5 dígitos): población}} de la tabla 29005 (Sexo = Total) para los años pedidos."""
    anios = set(anios)
    out: dict[int, dict[str, int]] = {a: {} for a in anios}
    with open(ruta, encoding="utf-8-sig", newline="") as f:
        cab = f.readline().rstrip("\r\n")
        if cab != "Municipios;Sexo;Periodo;Total":
            raise ErrorFuente(f"cabecera inesperada en la tabla oficial: {cab!r}")
        for n, linea in enumerate(f, 2):
            p = linea.rstrip("\r\n").split(";")
            if len(p) != 4:
                raise ErrorFuente(f"línea {n} de la tabla oficial con formato inesperado: {linea[:120]!r}")
            if p[1] != "Total" or not p[2].isdigit() or int(p[2]) not in anios:
                continue
            cod = p[0][:5]
            v = _num(p[3])
            if v == VACIO and len(cod) == 5 and cod.isdigit():
                continue  # municipio inexistente ese año (valor «""»): no figura → aviso_sin_oficial si tuviera secciones
            if len(cod) != 5 or not cod.isdigit() or not isinstance(v, int):
                raise ErrorFuente(f"línea {n} de la tabla oficial no válida: {linea[:120]!r}")
            if cod in out[int(p[2])]:
                raise ErrorFuente(f"municipio {cod} repetido en {p[2]}")
            out[int(p[2])][cod] = v
    return out


def leer_seccionado(ruta) -> set[str]:
    """Códigos CUSEC (10 dígitos) del .dbf del ZIP del seccionado INE. Falla si no hay .dbf, CUSEC, códigos válidos o filas."""
    with zipfile.ZipFile(ruta) as z:
        dbfs = sorted(n for n in z.namelist() if n.lower().endswith(".dbf"))
        if not dbfs:
            raise ErrorFuente(f"{Path(ruta).name}: el ZIP no trae .dbf")
        b = z.read(dbfs[0])
    try:
        n, hl, rl = struct.unpack("<IHH", b[4:12])
        campos, o = [], 32
        while b[o] != 13:
            campos.append((b[o:o + 11].split(b"\0")[0].decode("ascii"), b[o + 16]))
            o += 32
    except (struct.error, IndexError, UnicodeDecodeError) as e:
        raise ErrorFuente(f"{Path(ruta).name}: cabecera .dbf ilegible ({e})") from e
    off, pos = 1, None
    for nombre, ln in campos:
        if nombre == "CUSEC":
            pos = (off, ln)
        off += ln
    if pos is None or pos[1] != 10:
        raise ErrorFuente(f"{Path(ruta).name}: sin campo CUSEC de 10 caracteres")
    out = {b[hl + i * rl + pos[0]: hl + i * rl + pos[0] + 10].decode("latin1").strip() for i in range(n)}
    if not out or any(len(c) != 10 or not c.isdigit() for c in out):
        raise ErrorFuente(f"{Path(ruta).name}: CUSEC vacío o con códigos no válidos")
    return out


def estimar(sec: str, anio: int, atlas: dict[int, dict[str, object]]):
    """Estimación de una sección «.» en el año de la fuente → (población|None, origen, años_fuente)."""
    con_dato = sorted(a for a in atlas if isinstance(atlas[a].get(sec), int))
    ant = [a for a in con_dato if a < anio]
    sig = [a for a in con_dato if a > anio]
    if ant and sig:
        p, n = max(ant), min(sig)
        vp, vn = atlas[p][sec], atlas[n][sec]
        num, den = vp * (n - anio) + vn * (anio - p), n - p
        return (2 * num + den) // (2 * den), "interpolada", f"{p}-{n}"
    if ant or sig:
        a = max(ant) if ant else min(sig)
        return atlas[a][sec], "mas_cercana", str(a)
    return None, "sin_dato", ""


def poblacion_eleccion(fuente: dict[str, object], anio_fuente: int, atlas: dict[int, dict[str, object]],
                       seccionado: set[str] | None = None):
    """Filas (sección, población|None, origen, ajustada, años_fuente) ordenadas por sección, sin ajustar.

    Universo = secciones con valor o «.» en la fuente (las vacías no se estiman ni aparecen) más, si se da `seccionado`, las del
    seccionado que la fuente no trae con valor (no listadas o vacías): se estiman como las «.» con origen «no_listada» (sin dato en
    ningún año: «sin_dato»).
    Falla cerrado si más de un TOPE_DESCUADRE_PCT % de un lado no tiene pareja en el otro."""
    filas = []
    for sec in sorted(fuente):
        v = fuente[sec]
        if v == VACIO:
            continue
        if isinstance(v, int):
            filas.append((sec, v, "dato", "no", str(anio_fuente)))
        else:
            pob, origen, anios = estimar(sec, anio_fuente, atlas)
            filas.append((sec, pob, origen, "no", anios))
    if seccionado is not None:
        en_fuente = {f[0] for f in filas}
        existentes = {s for s, v in fuente.items() if v != VACIO}
        no_listadas = sorted(seccionado - existentes)  # existentes = con valor o «.»; las vacías del seccionado también
        sin_seccionado = len(en_fuente - seccionado)
        for lado, n, base in (("seccionado sin pareja en la fuente", len(no_listadas), len(seccionado)),
                              ("fuente sin pareja en el seccionado", sin_seccionado, len(existentes))):
            if n * 100 > TOPE_DESCUADRE_PCT * base:
                raise ErrorFuente(f"el seccionado no cuadra con la fuente de {anio_fuente}: {lado} = {n} de {base} (> {TOPE_DESCUADRE_PCT} %)")
        for sec in no_listadas:
            pob, origen, anios = estimar(sec, anio_fuente, atlas)
            filas.append((sec, pob, "no_listada" if pob is not None else "sin_dato", "no", anios))
        filas.sort(key=lambda f: f[0])
    return filas


def reparto(valores: list[int], total: int) -> list[int]:
    """Reescala enteros a suma exacta `total` (restos mayores; empate: el primero por orden de entrada)."""
    s = sum(valores)
    base = [v * total // s for v in valores]
    resto = [v * total % s for v in valores]
    falta = total - sum(base)
    for i in sorted(range(len(valores)), key=lambda i: (-resto[i], i))[:falta]:
        base[i] += 1
    return base


def ajustar(eleccion: str, filas, oficial: dict[str, int] | None):
    """Ajuste proporcional por municipio. Devuelve (filas nuevas en el mismo orden, filas de informe por municipio)."""
    por_mun: dict[str, list[int]] = {}
    for i, f in enumerate(filas):
        por_mun.setdefault(f[0][:5], []).append(i)
    nuevas = list(filas)
    inf = []
    for mun in sorted(por_mun):
        idx = por_mun[mun]
        est = [i for i in idx if filas[i][2] in ("interpolada", "mas_cercana", "no_listada")]
        if not est and not any(filas[i][2] == "sin_dato" for i in idx):
            continue
        pub = sum(filas[i][1] for i in idx if filas[i][2] == "dato")
        antes = sum(filas[i][1] for i in est)  # 0 si solo hay sin_dato (el aviso lo recoge)
        fila = {"elección": eleccion, "municipio": mun, "oficial": "", "publicada": pub, "estimada_antes": antes,
                "estimada_despues": antes, "secciones_estimadas": len(est), "desajuste_pct": "", "estado": ""}
        ofi = (oficial or {}).get(mun)
        if oficial is None:
            fila["estado"] = "sin_ajuste_fuente"
        elif ofi is None:
            fila["estado"] = "aviso_sin_oficial"
        elif any(filas[i][2] == "sin_dato" for i in idx):
            fila["oficial"] = ofi
            fila["estado"] = "aviso_sin_dato"
        elif ofi - pub <= 0:
            fila["oficial"] = ofi
            fila["estado"] = "aviso_residuo_no_positivo"
        elif antes == 0:
            fila["oficial"] = ofi
            fila["estado"] = "aviso_estimada_cero"
        else:
            fila["oficial"] = ofi
            fila["desajuste_pct"] = pct(abs(ofi - pub - antes), ofi)
            res = ofi - pub
            if res == antes:
                fila["estado"] = "cuadra"
            else:
                for i, v in zip(est, reparto([filas[i][1] for i in est], res)):
                    f = filas[i]
                    nuevas[i] = (f[0], v, f[2], "sí", f[4])
                fila["estimada_despues"] = res
                fila["estado"] = "ajustado"
        inf.append(fila)
    return nuevas, inf


def pct(parte: int, total: int) -> str:
    """% con 4 decimales, aritmética entera (redondeo half-up), sin flotantes."""
    if total == 0:
        return "0.0000"
    n = (parte * 1_000_000 + total // 2) // total  # centésimas de punto porcentual ×100
    return f"{n // 10000}.{n % 10000:04d}"


def informe_provincias(eleccion: str, filas, municipios=(), seccionado=None) -> list[dict]:
    acc: dict[str, dict] = {}
    for sec, pob, origen, ajustada, _ in filas:
        d = acc.setdefault(sec[:2], dict(secciones=0, interpolada=0, mas_cercana=0, no_listada=0, ajustadas=0, sin_dato=0,
                                         poblacion=0, pob_est=0, mun_aj=0, mun_aviso=0, sin_secc=0, desv=Fraction(0)))
        d["secciones"] += 1
        if seccionado is not None and sec not in seccionado:
            d["sin_secc"] += 1  # sección de la fuente que el seccionado de ese año no tiene (se mantiene)
        if origen == "sin_dato":
            d["sin_dato"] += 1
            continue
        d["poblacion"] += pob
        if origen != "dato":
            d[origen] += 1
            d["pob_est"] += pob
            d["ajustadas"] += ajustada == "sí"
    for m in municipios:
        d = acc.get(m["municipio"][:2])
        if d is None:
            continue
        if m["estado"] == "ajustado":
            d["mun_aj"] += 1
            d["desv"] += Fraction(abs(m["oficial"] - m["publicada"] - m["estimada_antes"]), m["oficial"])
        elif m["estado"].startswith("aviso"):
            d["mun_aviso"] += 1
    out = []
    for prov in sorted(acc):
        d = acc[prov]
        medio = pct(d["desv"].numerator, d["desv"].denominator * d["mun_aj"]) if d["mun_aj"] else "0.0000"
        out.append({
            "elección": eleccion, "provincia": prov, "secciones": d["secciones"],
            "secciones_interpoladas": d["interpolada"], "secciones_mas_cercanas": d["mas_cercana"],
            "secciones_no_listadas": d["no_listada"],
            "secciones_sin_seccionado": d["sin_secc"] if seccionado is not None else "", "secciones_ajustadas": d["ajustadas"], "secciones_sin_dato": d["sin_dato"],
            "población": d["poblacion"], "población_estimada": d["pob_est"],
            "pct_estimada": pct(d["pob_est"], d["poblacion"]),
            "municipios_ajustados": d["mun_aj"], "desajuste_medio_pct": medio, "municipios_aviso": d["mun_aviso"],
            "marca": "MARCA" if (d["pob_est"] * 100 > UMBRAL_MARCA_PCT * d["poblacion"] or d["sin_dato"]) else "",
        })
    return out


def calcular(atlas, censo, oficial=None, seccionados=None):
    """→ ({elección: filas}, informe provincias, informe municipios).

    `oficial` = {año: {municipio: población}}; `seccionados` = {año del seccionado: {CUSEC}} (obligatorio: falla cerrado si falta)."""
    tablas, informe, municipios = {}, [], []
    for el in sorted(ELECCIONES):
        tipo, anio = ELECCIONES[el]
        fuente = censo if tipo == "censo" else atlas.get(anio)
        if not fuente:
            raise ErrorFuente(f"{el}: la fuente {tipo} {anio} no tiene secciones")
        sa = SECCIONADO[el]
        if sa is not None and not (seccionados or {}).get(sa):
            raise ErrorFuente(f"{el}: falta el seccionado {sa}")
        filas = poblacion_eleccion(fuente, anio, atlas, None if sa is None else seccionados[sa])
        if tipo == "atlas":
            if oficial is None or anio not in oficial:
                raise ErrorFuente(f"{el}: falta la población oficial del año {anio}")
            filas, mun = ajustar(el, filas, oficial[anio])
        else:
            filas, mun = ajustar(el, filas, None)
        tablas[el] = filas
        municipios += mun
        informe += informe_provincias(el, filas, mun, None if sa is None else seccionados[sa])
    return tablas, informe, municipios


def _escribir(ruta, cols, filas) -> str:
    with open(ruta, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(cols)
        w.writerows(filas)
    return sha256_fichero(ruta)


def escribir_tabla(ruta, filas) -> str:
    """CSV de una elección: sección, población, origen (dato/interpolada/mas_cercana/sin_dato), ajustada (sí/no), años_fuente."""
    return _escribir(ruta, COLUMNAS_TABLA, [(s, "" if p is None else p, o, a, y) for s, p, o, a, y in filas])


COLS_INFORME = ["elección", "provincia", "secciones", "secciones_interpoladas", "secciones_mas_cercanas",
                "secciones_no_listadas", "secciones_sin_seccionado", "secciones_ajustadas", "secciones_sin_dato", "población", "población_estimada", "pct_estimada",
                "municipios_ajustados", "desajuste_medio_pct", "municipios_aviso", "marca"]
COLS_MUNICIPIOS = ["elección", "municipio", "oficial", "publicada", "estimada_antes", "estimada_despues",
                   "secciones_estimadas", "desajuste_pct", "estado"]


def escribir_informe(ruta, informe, cols=COLS_INFORME) -> str:
    return _escribir(ruta, cols, [[r[c] for c in cols] for r in informe])


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--atlas", required=True, help="CSV 30832 del INE (local)")
    ap.add_argument("--censo", required=True, help="ZIP indicadores_seccion_censal_csv del Censo 2011 (local)")
    ap.add_argument("--oficial", required=True, help="CSV 29005 del INE: cifras oficiales del padrón por municipio (local)")
    ap.add_argument("--seccionados", required=True, help="directorio con seccionado_AAAA.zip del INE (local)")
    ap.add_argument("--sumas", required=True, nargs="+", help="SHA256SUMS.txt (uno o varios)")
    ap.add_argument("--salida", required=True, help="directorio de salida")
    ap.add_argument("--estricto", action="store_true", help="si algún municipio tiene aviso: salir con 2 sin escribir las tablas")
    a = ap.parse_args(argv)
    try:
        sumas: dict[str, str] = {}
        for s in a.sumas:
            sumas.update(leer_sumas(s))
        verificar(a.atlas, NOMBRE_ATLAS, sumas)
        verificar(a.censo, NOMBRE_CENSO, sumas)
        verificar(a.oficial, NOMBRE_OFICIAL, sumas)
        secc = {}
        for anio in sorted(set(SECCIONADO.values()) - {None}):
            ruta = Path(a.seccionados) / f"seccionado_{anio}.zip"
            verificar(ruta, ruta.name, sumas)
            secc[anio] = leer_seccionado(ruta)
        anios = {anio for tipo, anio in ELECCIONES.values() if tipo == "atlas"}
        tablas, informe, municipios = calcular(leer_atlas(a.atlas), leer_censo(a.censo), leer_oficial(a.oficial, anios), secc)
    except (ErrorFuente, OSError, zipfile.BadZipFile) as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1
    out = Path(a.salida)
    out.mkdir(parents=True, exist_ok=True)
    avisos = [m for m in municipios if m["estado"].startswith("aviso")]
    if a.estricto and avisos:  # a prueba de fallos: sin tablas, el consumidor no puede usar una elección con avisos
        escribir_informe(out / "informe_provincias.csv", informe)
        escribir_informe(out / "informe_municipios.csv", municipios, COLS_MUNICIPIOS)
        print(f"ERROR (--estricto): {len(avisos)} municipios con aviso; no se escriben tablas.", file=sys.stderr)
        return 2
    for el, filas in tablas.items():
        print(f"poblacion_seccion_{el}.csv sha256", escribir_tabla(out / f"poblacion_seccion_{el}.csv", filas), len(filas), "filas")
    print("informe_provincias.csv sha256", escribir_informe(out / "informe_provincias.csv", informe))
    print("informe_municipios.csv sha256", escribir_informe(out / "informe_municipios.csv", municipios, COLS_MUNICIPIOS))
    marcadas = sorted({(r["elección"], r["provincia"]) for r in informe if r["marca"]})
    print("provincias MARCA (>1 % estimada):", len(marcadas), marcadas)
    print("municipios con aviso:", len(avisos), [(m["elección"], m["municipio"], m["estado"]) for m in avisos[:20]])
    return 0


if __name__ == "__main__":
    sys.exit(main())
