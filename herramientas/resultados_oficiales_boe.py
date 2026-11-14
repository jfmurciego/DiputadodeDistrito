#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CSV oficial de resultados por circunscripción de las generales 2011, 2015, 2016 y 2019-04 desde el BOE (T-330).

PROYECTO: Diputado de Distrito
VERSIÓN: 1.0.0 · FECHA: 2026-11-14 · ESTADO: candidato
CAMBIOS: 1.0.0: fichero nuevo.
MOTIVO: contraste oficial local de las elecciones que no lo tenían (T-306 §1): mismo formato que
  configuracion/resultados_oficiales_congreso_2019_11.csv y _2023.csv (cuadro II del BOE: candidaturas con escaño en el total
  estatal, con sus votos en cada circunscripción, también donde no obtuvieron escaño).
ANTERIOR: ninguna (fichero nuevo)
QUÉ HACE: lee el documento del BOE (XML de https://www.boe.es/diario_boe/xml.php?id=<id>; para 2016-06, cuyas tablas son imágenes en el XML,
  el PDF con capa de texto) tras comprobar su sha256 contra configuracion/identificadores_boe_resultados_congreso.json, extrae el
  cuadro II y escribe configuracion/resultados_oficiales_congreso_<AAAA_MM>.csv (codigo, provincia, escanos_circunscripcion,
  partido, votos, escanos; provincias y partidos en el orden de las columnas del BOE) y el .json con la fuente, el sha256 del
  documento y del CSV y la fila «Total estatal» del BOE (votos y escaños por partido). Para (sin escribir) si una suma de las
  circunscripciones no cuadra con ese total, si los escaños no son 350 o si falta una provincia. El verificador reproduce
  exactamente el CSV de 2019-11 (BOE-A-2019-18147). Las siglas son las de la cabecera del BOE; los topónimos, en español.
Uso: python herramientas/resultados_oficiales_boe.py --eleccion 2011-11 --documento BOE-A-2011-19391.xml
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import html
import io
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
IDENTIFICADORES = ROOT / "configuracion/identificadores_boe_resultados_congreso.json"
ELECCIONES = {"2011-11": "2011_11", "2015-12": "2015_12", "2016-06": "2016_06", "2019-04": "2019_04", "2019-11": "2019_11"}
# (código INE, nombre en español) en el orden en que el BOE lista las circunscripciones (igual en todas las convocatorias);
# derivado del cuadro II de BOE-A-2019-18147 emparejando cada fila con configuracion/resultados_oficiales_congreso_2019_11.csv.
ORDEN = [("02", "Albacete"), ("03", "Alicante"), ("04", "Almería"), ("01", "Álava"), ("33", "Asturias"), ("05", "Ávila"),
         ("06", "Badajoz"), ("07", "Baleares"), ("08", "Barcelona"), ("48", "Vizcaya"), ("09", "Burgos"), ("10", "Cáceres"),
         ("11", "Cádiz"), ("39", "Cantabria"), ("12", "Castellón"), ("13", "Ciudad Real"), ("14", "Córdoba"),
         ("15", "La Coruña"), ("16", "Cuenca"), ("20", "Guipúzcoa"), ("17", "Gerona"), ("18", "Granada"),
         ("19", "Guadalajara"), ("21", "Huelva"), ("22", "Huesca"), ("23", "Jaén"), ("24", "León"), ("25", "Lérida"),
         ("27", "Lugo"), ("28", "Madrid"), ("29", "Málaga"), ("30", "Murcia"), ("31", "Navarra"), ("32", "Orense"),
         ("34", "Palencia"), ("35", "Las Palmas"), ("36", "Pontevedra"), ("26", "La Rioja"), ("37", "Salamanca"),
         ("38", "Santa Cruz de Tenerife"), ("40", "Segovia"), ("41", "Sevilla"), ("42", "Soria"), ("43", "Tarragona"),
         ("44", "Teruel"), ("45", "Toledo"), ("46", "Valencia"), ("47", "Valladolid"), ("49", "Zamora"),
         ("50", "Zaragoza"), ("51", "Ceuta"), ("52", "Melilla")]
# 2016-06 (PDF): siglas del cuadro II en el orden de las columnas de cada bloque, transcritas de la cabecera del BOE-A-2016-7133.
COLUMNAS_2016 = [["PP", "PSOE", "PODEMOS-IU-EQUO-CLIAS", "C's", "ECP"],
                 ["PODEMOS-COMPROMÍS-EUPV", "ERC-CATSÍ", "PSC-PSOE", "CDC", "PODEMOS-EN MAREA-ANOVA-EU"],
                 ["EAJ-PNV", "PP-PAR", "PSOE-NCa", "PP-FORO", "EH Bildu"],
                 ["UPN-PP", "CCa"]]


def sha256(datos: bytes) -> str:
    return hashlib.sha256(datos).hexdigest()


def num(s: str) -> int | None:
    s = s.strip()
    return int(s.replace(".", "")) if s and s != "." else None


def _filas_html(tabla: str) -> list[list[str]]:
    return [[html.unescape(re.sub(r"<[^>]+>", "", c)).strip() for c in re.findall(r"<t[hd][^>]*>(.*?)</t[hd]>", r, re.S)]
            for r in re.findall(r"<tr[ >].*?</tr>", tabla, re.S)]


def _nuevo():
    return {"provincias": [], "totales": {}, "bloque": {}}  # bloque: sigla → (tabla, columna)


def parsear_xml(texto: str) -> dict:
    """{"provincias": [(nombre BOE, escaños, [(sigla, votos, escaños)])], "totales": {sigla: (votos, escaños)}} del cuadro II."""
    i, j = re.search(r"CUADRO II\s*<", texto).start(), re.search(r"CUADRO III\s*<", texto).start()
    out, vistas, ordenadas = _nuevo(), {}, []
    for b, tabla in enumerate(re.findall(r"<table.*?</table>", texto[i:j], re.S)):
        filas = _filas_html(tabla)
        n = len(filas[2]) // 2  # pares «Votos/Escaños»; una columna sin sigla (BOE 2015: «Unidad Popular», «Podemos - Ahora Alto Aragón
        nombres = filas[0][2:]  # en Común») toma su nombre de la cabecera
        siglas = [(filas[1][k] if k < len(filas[1]) and filas[1][k] else
                   re.sub(r"\s+", " ", nombres[k]).replace(" *", "").strip()) for k in range(n)]
        out["bloque"].update({s: (b, k) for k, s in enumerate(siglas)})
        for f in filas[3:]:
            if len(f) < 3 or not f[1].isdigit():
                continue  # nota al pie
            nombre, vals = f[0].rstrip(".").strip(), f[2:] + [""] * (2 * len(siglas))
            pares = [(s, num(vals[2 * k]), num(vals[2 * k + 1])) for k, s in enumerate(siglas)]
            if nombre.lower().startswith("total"):
                out["totales"].update({s: (v, e or 0) for s, v, e in pares if v is not None})
            else:
                if nombre not in vistas:
                    vistas[nombre] = (nombre, int(f[1]), [])
                    ordenadas.append(vistas[nombre])
                vistas[nombre][2].extend((s, v, e or 0) for s, v, e in pares if v is not None)
    out["provincias"] = ordenadas
    return out


def parsear_pdf(texto: str) -> dict:
    """Cuadro II del BOE-A-2016-7133 desde su capa de texto (`pdftotext -layout`), con COLUMNAS_2016."""
    lineas = texto.splitlines()
    ini = [k for k, l in enumerate(lineas) if re.fullmatch(r"\s*CUADRO II( \(Continuación\))?\s*", l)]
    fin = next(k for k, l in enumerate(lineas) if re.fullmatch(r"\s*CUADRO III\s*", l))
    if len(ini) != len(COLUMNAS_2016):
        raise SystemExit(f"BLOQUES_INESPERADOS {len(ini)}")
    out, vistas = _nuevo(), {}
    for b, (a, z) in enumerate(zip(ini, ini[1:] + [fin])):
        siglas = COLUMNAS_2016[b]
        out["bloque"].update({s: (b, k) for k, s in enumerate(siglas)})
        for l in lineas[a:z]:
            m = re.match(r"^\s+(\D+?)\s+(\d+)\s+((?:(?:\d{1,3}(?:\.\d{3})+|\d+|\.)\s*)+)$", l)
            if not m:
                continue
            nombre, esc, toks = m.group(1).strip(), int(m.group(2)), m.group(3).split()
            if len(toks) < 2 * len(siglas) or any(t != "." for t in toks[2 * len(siglas):]):
                raise SystemExit(f"FILA_INESPERADA {l.strip()}")
            pares = [(s, num(toks[2 * k]), num(toks[2 * k + 1])) for k, s in enumerate(siglas)]
            if nombre.lower().startswith("total"):
                out["totales"].update({s: (v, e or 0) for s, v, e in pares if v is not None})
                continue
            if nombre not in vistas:
                vistas[nombre] = (nombre, esc, [])
                out["provincias"].append(vistas[nombre])
            vistas[nombre][2].extend((s, v, e or 0) for s, v, e in pares if v is not None)
    return out


def comprobar(d: dict) -> list[str]:
    """Errores de coherencia: 52 circunscripciones, 350 escaños, cada partido suma su «Total estatal» del BOE."""
    err = []
    if len(d["provincias"]) != 52:
        err.append(f"{len(d['provincias'])} circunscripciones, no 52")
    if sum(e for _, e, _ in d["provincias"]) != 350:
        err.append("los escaños de las circunscripciones no suman 350")
    suma: dict = {}
    for nombre, esc, partidos in d["provincias"]:
        if sum(e for _, _, e in partidos) != esc:
            err.append(f"{nombre}: escaños por partido {sum(e for _, _, e in partidos)} ≠ {esc}")
        for s, v, e in partidos:
            a = suma.setdefault(s, [0, 0])
            a[0] += v
            a[1] += e
    for s, (v, e) in d["totales"].items():
        if suma.get(s) != [v, e]:
            err.append(f"{s}: suma de circunscripciones {suma.get(s)} ≠ Total estatal {[v, e]}")
    if set(suma) != set(d["totales"]):
        err.append(f"partidos sin total o total sin partido: {sorted(set(suma) ^ set(d['totales']))}")
    return err


def filas_csv(d: dict) -> list[list]:
    """Orden de los CSV de T-86: por tabla del cuadro II, luego circunscripción (orden del BOE) y columna."""
    filas = []
    for i, ((cod, prov), (_, esc, partidos)) in enumerate(zip(ORDEN, d["provincias"])):
        for s, v, e in partidos:
            filas.append((d["bloque"][s], i, [cod, prov, esc, s, v, e]))
    return [f for _, _, f in sorted(filas, key=lambda x: (x[0][0], x[1], x[0][1]))]


def csv_bytes(filas: list[list]) -> bytes:
    buf = io.StringIO(newline="")
    w = csv.writer(buf)  # CRLF, como los CSV de T-86
    w.writerow(["codigo", "provincia", "escanos_circunscripcion", "partido", "votos", "escanos"])
    w.writerows(filas)
    return buf.getvalue().encode("utf-8")


def salida(eleccion: str) -> Path:
    return ROOT / f"configuracion/resultados_oficiales_congreso_{ELECCIONES[eleccion]}.csv"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--eleccion", required=True, choices=sorted(ELECCIONES))
    ap.add_argument("--documento", type=Path, required=True, help="XML del BOE (o PDF para 2016-06)")
    ap.add_argument("--escribir", action="store_true", help="escribe el CSV y el JSON (por defecto solo comprueba)")
    a = ap.parse_args(argv)
    if a.eleccion == "2019-11":  # solo verificación del extractor: el CSV vigente es el de T-86 (no se reescribe)
        meta = json.loads(salida(a.eleccion).with_suffix(".json").read_text(encoding="utf-8"))
        ident = {"boe": meta["boe"], "url": meta["url"], "titulo": meta["fuente"],
                 "fecha_publicacion": meta["fecha_publicacion"], "sha256_xml": meta["sha256_xml"]}
        a.escribir = False
    else:
        ident = json.loads(IDENTIFICADORES.read_text(encoding="utf-8"))["elecciones"].get(a.eleccion)
    raw = a.documento.read_bytes()
    pdf = raw[:4] == b"%PDF"
    clave = "sha256_pdf" if pdf else "sha256_xml"
    if ident is None or sha256(raw) != ident.get(clave):
        print(f"PARADA: {a.documento.name} ({clave} {sha256(raw)}) no coincide con {IDENTIFICADORES.name}", file=sys.stderr)
        return 2
    if pdf:
        import subprocess
        texto = subprocess.run(["pdftotext", "-layout", str(a.documento), "-"], capture_output=True, text=True, check=True).stdout
        d = parsear_pdf(texto)
    else:
        d = parsear_xml(raw.decode("utf-8"))
    err = comprobar(d)
    if err:
        print("PARADA: " + "; ".join(err), file=sys.stderr)
        return 3
    cuerpo = csv_bytes(filas_csv(d))
    print(a.eleccion, len(filas_csv(d)), "filas", sha256(cuerpo))
    if a.eleccion == "2019-11":
        return 0 if sha256(cuerpo) == meta["sha256_csv"] else 4
    if a.escribir:
        salida(a.eleccion).write_bytes(cuerpo)
        meta = {"fuente": ident["titulo"], "boe": ident["boe"], "url": ident["url"],
                "fecha_publicacion": ident["fecha_publicacion"], "sha256_xml": ident["sha256_xml"]}
        if ident.get("sha256_pdf"):
            meta["sha256_pdf"] = ident["sha256_pdf"]
            meta["datos_desde"] = "pdf (las tablas del XML son imágenes)"
        meta.update({"sha256_csv": sha256(cuerpo), "cuadro": "II (candidaturas con escaño en el total estatal)",
                     "total_escanos": 350,
                     "totales_oficiales": {s: {"votos": v, "escanos": e} for s, (v, e) in d["totales"].items()}})
        salida(a.eleccion).with_suffix(".json").write_text(json.dumps(meta, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
