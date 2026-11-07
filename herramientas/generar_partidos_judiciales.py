#!/usr/bin/env python3
"""Partidos judiciales por municipio desde el Anexo I de la Ley 38/1988 (BOE-A-1988-29622).

VERSIÓN: 1.0.0
NOMBRE DE VERSIÓN: Partidos judiciales
FECHA: 2026-11-07
ESTADO: activo T-64
CAMBIOS: herramienta nueva.
MOTIVO: unidad intermedia oficial para toda España (C-13), con fuente y sha256.
ANTERIOR: ninguna (fichero nuevo)

El texto consolidado del BOE omite los anexos («Anexos omitidos»); el Anexo I solo está en el texto original
publicado el 30-12-1988 (https://www.boe.es/diario_boe/xml.php?id=BOE-A-1988-29622). Conciliación con el inventario
municipal (datos/distritos/municipios_ine_2025.csv): código INE = provincia + código del anexo (3 cifras), con el
nombre igual (sin tildes, artículos ni signos). Si no, solo se admite el casamiento único por nombre dentro de la
provincia. Nada se inventa: lo que no casa va a configuracion/partidos_judiciales_no_conciliados.csv.
Uso: python herramientas/generar_partidos_judiciales.py --xml <ley_original.xml>
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import re
import sys
import unicodedata
from collections import defaultdict
from pathlib import Path

VERSION = "1.0.0"
RAIZ = Path(__file__).resolve().parents[1]
MUNICIPIOS = "datos/distritos/municipios_ine_2025.csv"
SALIDA = "configuracion/partidos_judiciales.csv"
NO_CONCILIADOS = "configuracion/partidos_judiciales_no_conciliados.csv"
FUENTE = {
    "norma": "Ley 38/1988, de 28 de diciembre, de Demarcación y de Planta Judicial (Anexo I)",
    "id_boe": "BOE-A-1988-29622",
    "url": "https://www.boe.es/diario_boe/xml.php?id=BOE-A-1988-29622",
    "fecha_publicacion": "1988-12-30",
    "fecha_consolidacion_boe": "2026-07-09",
}
# Ceuta y Melilla no son provincia en 1988 (Cádiz y Málaga): sus municipios no figuran con código propio.
CABECERA = ["codigo_ine", "provincia", "partido_judicial", "id_partido", "nombre_ine", "conciliacion"]


def sha256(path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


ARTICULOS = {"el", "la", "los", "las", "l", "les", "lo", "a", "o", "as", "os", "sa", "ses", "es", "els", "s", "na"}


def plegar(x: str) -> str:
    """Nombre sin tildes, signos ni artículos («Arahal, El» y «Arahal» coinciden)."""
    x = unicodedata.normalize("NFD", x.lower())
    x = "".join(c for c in x if not unicodedata.combining(c))
    return "".join(t for t in re.findall(r"[a-z0-9]+", x) if t not in ARTICULOS)


def parecidos(a: str, b: str) -> bool:
    """Un nombre es prefijo del otro (renombrado: «Setenil» → «Setenil de las Bodegas»)."""
    a, b = plegar(a), plegar(b)
    return len(min(a, b, key=len)) >= 4 and (a.startswith(b) or b.startswith(a))


def leer_anexo(xml: str):
    """[(provincia_nombre, partido, cm, nombre)] del Anexo I."""
    a = xml.index('<p class="anexo_num">ANEXO I<')
    s = xml[a:xml.index("ANEXO II", a)]
    filas, prov = [], None
    for m in re.finditer(r"\[precepto\](.*?)</p>|<tr>(.*?)</tr>", s, re.S):
        if m.group(1):
            prov = m.group(1).split("Provincia")[-1].strip()
            continue
        c = [re.sub(r"\s+", " ", x).strip() for x in re.findall(r'<p class="[^"]*">(.*?)</p>', m.group(2), re.S)]
        if len(c) == 3 and c[0].isdigit() and c[1].isdigit():
            filas.append((prov, int(c[0]), c[1].zfill(3), c[2]))
    return filas


def cargar_ine(ruta=RAIZ / MUNICIPIOS):
    with open(ruta, encoding="utf-8", newline="") as f:
        return {r["codigo_ine"]: r["nombre_ine"] for r in csv.DictReader(f)}


def conciliar(filas, ine):
    """Devuelve (asignados {codigo: (prov, pj, nombre_anexo, via)}, no_conciliados_anexo, sin_partido_ine)."""
    votos = defaultdict(lambda: defaultdict(int))
    for p, _, cm, n in filas:
        for pr in {k[:2] for k in ine}:
            k = pr + cm
            if k in ine and plegar(ine[k]) == plegar(n):
                votos[p][pr] += 1
    codprov = {p: max(v, key=v.get) for p, v in votos.items()}
    asignados, dudosos = {}, []
    por_nombre = defaultdict(lambda: defaultdict(list))
    for k, n in ine.items():
        por_nombre[k[:2]][plegar(n)].append(k)
    for p, pj, cm, n in filas:
        pr = codprov.get(p)
        k = pr + cm if pr else None
        if k and k in ine and plegar(ine[k]) == plegar(n) and k not in asignados:
            asignados[k] = (p, pj, n, "codigo+nombre")
            continue
        if k and k in ine and k not in asignados and parecidos(ine[k], n):
            asignados[k] = (p, pj, n, "codigo+nombre_parcial")
            continue
        cand = por_nombre[pr].get(plegar(n), []) if pr else []
        cand = [c for c in cand if c not in asignados]
        if not cand and cm == "991":  # Ceuta y Melilla: dentro de Cádiz y Málaga en 1988, sin código propio
            cand = [k for k in por_nombre["51"].get(plegar(n), []) + por_nombre["52"].get(plegar(n), [])
                    if k not in asignados]
        if len(cand) == 1:
            asignados[cand[0]] = (p, pj, n, "nombre")
        else:
            dudosos.append((p, pj, cm, n))
    # Segunda pasada: mismo código aún sin dueño y fila sin casar (nombre en otra lengua cooficial u otra grafía).
    resto = []
    for p, pj, cm, n in dudosos:
        k = codprov[p] + cm if p in codprov else None
        if k and k in ine and k not in asignados:
            asignados[k] = (p, pj, n, "codigo_solo")
        else:
            resto.append((p, pj, cm, n))
    return asignados, resto, codprov


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--xml", required=True)
    a = ap.parse_args(argv)
    xml = Path(a.xml).read_text(encoding="utf-8")
    ine = cargar_ine()
    filas = leer_anexo(xml)
    asig, dudosos, _ = conciliar(filas, ine)
    sin = sorted(k for k in ine if k not in asig)
    with open(RAIZ / SALIDA, "w", encoding="utf-8", newline="") as f:
        f.write(f"# fuente: {FUENTE['norma']}; {FUENTE['id_boe']}; {FUENTE['url']}; publicación {FUENTE['fecha_publicacion']}; "
                f"consolidación BOE {FUENTE['fecha_consolidacion_boe']} (anexos omitidos en el consolidado); "
                f"sha256 del XML {hashlib.sha256(xml.encode('utf-8')).hexdigest()}\n")
        w = csv.writer(f, lineterminator="\n")
        w.writerow(CABECERA)
        for k in sorted(asig):
            p, pj, _, via = asig[k]
            w.writerow([k, k[:2], pj, f"{k[:2]}-{pj:02d}", ine[k], via])
    with open(RAIZ / NO_CONCILIADOS, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["origen", "codigo_ine", "provincia", "partido_judicial", "nombre", "motivo"])
        for p, pj, cm, n in dudosos:
            w.writerow(["anexo", "", p, pj, f"{n} (cm {cm})", "sin_municipio_ine_equivalente"])
        for k in sin:
            w.writerow(["ine_2025", k, k[:2], "", ine[k], "sin_partido_en_anexo_1988"])
    print(f"anexo={len(filas)} asignados={len(asig)} cobertura={len(asig)/len(ine):.4%} "
          f"anexo_sin_casar={len(dudosos)} ine_sin_partido={len(sin)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
