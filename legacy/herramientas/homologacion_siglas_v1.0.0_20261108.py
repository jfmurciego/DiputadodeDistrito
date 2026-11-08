#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tabla de homologación de siglas de las generales 2011-2023 para la capa de rotación del visor (T-97).

PROYECTO: Diputado de Distrito
VERSIÓN: 1.0.0 · FECHA: 2026-11-08 · ESTADO: candidato
CAMBIOS: 1.0.0: fichero nuevo.
MOTIVO: la rotación (T-84) cuenta «PP-EU → PP» como cambio de ganador (hallazgo de T-83A). La tabla se presenta al
  propietario ANTES de usarse; esta herramienta NO la aplica a la rotación ni toca el visor.
ANTERIOR: ninguna (fichero nuevo)
QUÉ HACE: `construir` lee el espejo T-89 (data/<elección>/sekzioa/<cpro>.json: siglas `s` y familia `f`), comprueba el
  sha256 de cada fichero contra orchestracion/fuente_nazioenbehatokia.json y escribe, por elección, circunscripción y
  sigla con votos, el partido homologado según datos/homologacion_siglas/reglas_generales.json (regla de sigla > regla
  de familia > identidad), el nivel de certeza (ALTA/MEDIA/BAJA), la corroboración con Interior (resultados oficiales
  versionados de 2019-11 y 2023; el resto no está adquirido) y la fuente con su sha256.
  `comprobar` revalida la tabla sin red: cabecera, claves únicas, sha256 de cada fila contra el manifiesto, reaplicación
  de las reglas, cobertura de Interior y huellas del CSV y de las reglas.
Uso: python herramientas/homologacion_siglas.py construir --obs-dir DIR     (DIR contiene data/<elección>/sekzioa/<cpro>.json)
     python herramientas/homologacion_siglas.py comprobar
Salida: 0 si todo cuadra; 1 si hay errores.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))
import fuente_nazioenbehatokia as fn  # noqa: E402

DIR = "datos/homologacion_siglas"
REGLAS = f"{DIR}/reglas_generales.json"
SALIDA_CSV = f"{DIR}/homologacion_siglas_generales.csv"
SALIDA_JSON = f"{DIR}/homologacion_siglas_generales.json"
MANIFIESTO = fn.SALIDA
SCHEMA = "ddd.homologacion-siglas/1.0"
VERSION = "1.0.0"
CERTEZAS = ("ALTA", "MEDIA", "BAJA")
COLUMNAS = ["eleccion", "provincia", "sigla_fuente", "votos_fuente", "familia_fuente", "partido_homologado",
            "nivel_certeza", "regla", "interior", "ruta_fuente", "sha256_fuente"]
FAMILIA_RE = re.compile(r"^a\d+$")
FECHA = "2026-11-08"


def sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


# --- reglas ------------------------------------------------------------------------------------------------------
def _coincide(valor, x) -> bool:
    return valor == "*" or x in valor


def resolver(reglas: dict, eleccion: str, provincia: str, sigla: str, familia: str) -> tuple[str, str, str]:
    """(partido homologado, certeza, id de regla). Precedencia: sigla (más específica) > familia > identidad."""
    mejor, mejor_pts = None, -1
    for r in reglas["siglas"]:
        if sigla in r["siglas"] and _coincide(r["elecciones"], eleccion) and _coincide(r["provincias"], provincia):
            pts = (r["elecciones"] != "*") + (r["provincias"] != "*")
            if pts > mejor_pts:
                mejor, mejor_pts = r, pts
    if mejor:
        return mejor["homologado"], mejor["certeza"], f"SIGLA:{mejor['id']}"
    if FAMILIA_RE.match(familia):
        fam = reglas["familias"].get(familia)
        if fam is None:
            raise KeyError(f"familia sin regla: {familia} ({eleccion}/{provincia}/{sigla})")
        extra = fam.get("por_eleccion", {}).get(eleccion)
        cert = (extra or {}).get("certeza", fam["certeza"])
        return fam["homologado"], cert, f"FAMILIA:{familia}" + (f"@{eleccion}" if extra else "")
    return sigla, "ALTA", "IDENTIDAD"


def validar_reglas(reglas: dict) -> list[str]:
    err = []
    for k, f in reglas["familias"].items():
        if f["certeza"] not in CERTEZAS or not f["homologado"]:
            err.append(f"familia {k}: certeza u homologado inválidos")
        for e, x in f.get("por_eleccion", {}).items():
            if x.get("certeza") not in CERTEZAS:
                err.append(f"familia {k}@{e}: certeza inválida")
    ids = [r["id"] for r in reglas["siglas"]]
    err += [f"id de regla repetido: {i}" for i, n in Counter(ids).items() if n > 1]
    for r in reglas["siglas"]:
        if r["certeza"] not in CERTEZAS or not r["homologado"] or not r["siglas"]:
            err.append(f"regla {r['id']}: inválida")
    return err


# --- Interior (oficial versionado) -------------------------------------------------------------------------------
def leer_interior(root: Path = ROOT) -> dict[str, dict[str, set[str]]]:
    """{elección: {provincia: {siglas oficiales con escaño}}} de configuracion/resultados_oficiales_congreso_*.csv."""
    out = {}
    for e, ruta in fn.OFICIALES.items():
        p = root / ruta
        if not p.exists():
            continue
        d: dict[str, set[str]] = defaultdict(set)
        with p.open(encoding="utf-8", newline="") as fh:
            for r in csv.DictReader(fh):
                d[r["codigo"].zfill(2)].add(r["partido"])
        out[e] = dict(d)
    return out


def homologado_interior(reglas: dict, eleccion: str, nombre: str) -> str:
    return reglas["interior"].get(eleccion, {}).get(nombre, nombre)


def corroboracion(reglas: dict, interior: dict, eleccion: str, provincia: str, homologado: str) -> str:
    if eleccion not in interior:
        return "INTERIOR_NO_ADQUIRIDA"
    oficiales = {homologado_interior(reglas, eleccion, n) for n in interior[eleccion].get(provincia, set())}
    return "COINCIDE" if homologado in oficiales else "SIN_ESCAÑO_EN_INTERIOR"


# --- construir ----------------------------------------------------------------------------------------------------
def construir_filas(obs_dir: Path, reglas: dict, manifiesto: dict, interior: dict) -> tuple[list[dict], list[str]]:
    filas, errores = [], []
    for ruta, meta in sorted(manifiesto["ficheros"].items()):
        m = re.fullmatch(r"data/(\d{6})/sekzioa/(\d{2})\.json", ruta)
        if not m:
            continue
        eleccion, prov = m.groups()
        p = obs_dir / ruta
        if not p.exists():
            errores.append(f"falta {ruta}")
            continue
        if sha256(p) != meta["sha256"]:
            errores.append(f"sha256 distinto al manifiesto: {ruta}")
            continue
        doc = json.loads(p.read_text(encoding="utf-8"))
        fam: dict[str, str] = {}
        for s, f in zip(doc["s"], doc["f"]):
            if fam.setdefault(s, f) != f:
                errores.append(f"{ruta}: sigla {s!r} con dos familias")
        for sigla, votos in sorted(fn.totales_provincia(doc).items()):
            if votos <= 0:
                continue
            try:
                h, c, rid = resolver(reglas, eleccion, prov, sigla, fam[sigla])
            except KeyError as ex:
                errores.append(str(ex))
                continue
            filas.append({"eleccion": eleccion, "provincia": prov, "sigla_fuente": sigla, "votos_fuente": votos,
                          "familia_fuente": fam[sigla], "partido_homologado": h, "nivel_certeza": c, "regla": rid,
                          "interior": corroboracion(reglas, interior, eleccion, prov, h),
                          "ruta_fuente": ruta, "sha256_fuente": meta["sha256"]})
    filas.sort(key=lambda r: (r["eleccion"], r["provincia"], r["sigla_fuente"]))
    return filas, errores


def cobertura_interior(reglas: dict, interior: dict, filas: list[dict]) -> list[str]:
    """Cada partido oficial con escaño debe tener fila homologada con votos en su provincia y elección."""
    hay = defaultdict(set)
    for r in filas:
        hay[(r["eleccion"], r["provincia"])].add(r["partido_homologado"])
    err = []
    for e, provs in interior.items():
        for prov, nombres in provs.items():
            if prov not in {r["provincia"] for r in filas if r["eleccion"] == e}:
                continue  # filas de ámbito superior (p. ej. 99)
            for n in sorted(nombres):
                if homologado_interior(reglas, e, n) not in hay[(e, prov)]:
                    err.append(f"Interior {e}/{prov}: {n!r} → {homologado_interior(reglas, e, n)!r} sin fila en la tabla")
    return err


def escribir_csv(filas: list[dict], destino: Path) -> None:
    destino.parent.mkdir(parents=True, exist_ok=True)
    with destino.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=COLUMNAS, lineterminator="\n")
        w.writeheader()
        w.writerows(filas)


def resumen(filas: list[dict], reglas: dict) -> dict:
    por_cert = Counter(r["nivel_certeza"] for r in filas)
    por_ele = {e: dict(Counter(r["nivel_certeza"] for r in filas if r["eleccion"] == e)) for e in sorted({r["eleccion"] for r in filas})}
    cambios: dict = {}
    for r in filas:
        if r["partido_homologado"] != r["sigla_fuente"] or r["nivel_certeza"] == "BAJA":
            k = (r["eleccion"], r["sigla_fuente"], r["partido_homologado"], r["nivel_certeza"], r["regla"])
            cambios.setdefault(k, [0, 0])
            cambios[k][0] += 1
            cambios[k][1] += r["votos_fuente"]
    decisiones = [{"eleccion": e, "sigla_fuente": s, "partido_homologado": h, "regla": rid, "circunscripciones": n, "votos": v}
                  for (e, s, h, c, rid), (n, v) in sorted(cambios.items()) if c == "BAJA"]
    inter = Counter(r["interior"] for r in filas)
    return {"filas": len(filas), "por_certeza": dict(por_cert), "por_eleccion": por_ele,
            "corroboracion_interior": dict(inter), "decisiones_baja_para_el_propietario": decisiones}


def escribir_json(filas: list[dict], reglas_p: Path, csv_p: Path, destino: Path, root: Path = ROOT) -> dict:
    reglas = json.loads(reglas_p.read_text(encoding="utf-8"))
    interior_f = {}
    for e, ruta in fn.OFICIALES.items():
        if (root / ruta).exists():
            interior_f[e] = {"ruta": ruta, "sha256": sha256(root / ruta)}
    doc = {"schema": SCHEMA, "version": VERSION, "fecha": FECHA, "estado": "PROPUESTA_PENDIENTE_PROPIETARIO",
           "uso": "No aplicada a la rotación ni al visor hasta decisión del propietario (T-97).",
           "niveles_certeza": reglas["niveles"],
           "fuentes": {"observatorio": {"manifiesto": MANIFIESTO, "sha256_manifiesto": sha256(root / MANIFIESTO),
                                        "url": fn.BASE, "campos": "s (siglas), f (familia)"},
                       "interior": interior_f,
                       "nota_interior": "Solo 2019-11 y 2023 están versionadas (BOE); 2011, 2015, 2016 y 2019-04 no están adquiridas."},
           "reglas": {"ruta": REGLAS, "sha256": sha256(reglas_p)},
           "tabla": {"ruta": SALIDA_CSV, "sha256": sha256(csv_p)},
           "resumen": resumen(filas, reglas)}
    destino.write_text(json.dumps(doc, ensure_ascii=False, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    return doc


# --- comprobar ----------------------------------------------------------------------------------------------------
def comprobar(root: Path = ROOT) -> list[str]:
    err: list[str] = []
    reglas_p, csv_p, json_p = root / REGLAS, root / SALIDA_CSV, root / SALIDA_JSON
    reglas = json.loads(reglas_p.read_text(encoding="utf-8"))
    err += validar_reglas(reglas)
    manifiesto = json.loads((root / MANIFIESTO).read_text(encoding="utf-8"))
    meta = json.loads(json_p.read_text(encoding="utf-8"))
    if meta["tabla"]["sha256"] != sha256(csv_p):
        err.append("sha256 del CSV distinto al declarado")
    if meta["reglas"]["sha256"] != sha256(reglas_p):
        err.append("sha256 de las reglas distinto al declarado: reconstruir la tabla")
    if meta["fuentes"]["observatorio"]["sha256_manifiesto"] != sha256(root / MANIFIESTO):
        err.append("sha256 del manifiesto T-89 distinto al declarado")
    with csv_p.open(encoding="utf-8", newline="") as fh:
        rd = csv.DictReader(fh)
        if rd.fieldnames != COLUMNAS:
            return err + [f"columnas inesperadas: {rd.fieldnames}"]
        filas = list(rd)
    claves = Counter((r["eleccion"], r["provincia"], r["sigla_fuente"]) for r in filas)
    err += [f"clave repetida: {k}" for k, n in claves.items() if n > 1]
    interior = leer_interior(root)
    for r in filas:
        k = (r["eleccion"], r["provincia"], r["sigla_fuente"])
        if r["nivel_certeza"] not in CERTEZAS:
            err.append(f"{k}: certeza {r['nivel_certeza']!r}")
        if not r["partido_homologado"]:
            err.append(f"{k}: sin partido homologado")
        m = manifiesto["ficheros"].get(r["ruta_fuente"])
        if not m or m["sha256"] != r["sha256_fuente"]:
            err.append(f"{k}: sha256 de la fuente no coincide con el manifiesto")
        try:
            esperado = resolver(reglas, r["eleccion"], r["provincia"], r["sigla_fuente"], r["familia_fuente"])
        except KeyError as ex:
            err.append(str(ex))
            continue
        if esperado != (r["partido_homologado"], r["nivel_certeza"], r["regla"]):
            err.append(f"{k}: no coincide con las reglas ({esperado} frente a {(r['partido_homologado'], r['nivel_certeza'], r['regla'])})")
        if r["interior"] != corroboracion(reglas, interior, r["eleccion"], r["provincia"], r["partido_homologado"]):
            err.append(f"{k}: corroboración de Interior desactualizada")
    err += cobertura_interior(reglas, interior, filas)
    return err[:200]


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("construir")
    c.add_argument("--obs-dir", required=True, type=Path)
    sub.add_parser("comprobar")
    a = ap.parse_args(argv)
    if a.cmd == "comprobar":
        err = comprobar()
        for e in err:
            print("ERROR", e)
        print("OK" if not err else f"{len(err)} errores")
        return 1 if err else 0
    reglas_p = ROOT / REGLAS
    reglas = json.loads(reglas_p.read_text(encoding="utf-8"))
    err = validar_reglas(reglas)
    manifiesto = json.loads((ROOT / MANIFIESTO).read_text(encoding="utf-8"))
    interior = leer_interior()
    filas, e2 = construir_filas(a.obs_dir, reglas, manifiesto, interior)
    err += e2 + cobertura_interior(reglas, interior, filas)
    for e in err[:50]:
        print("ERROR", e)
    if err:
        return 1
    escribir_csv(filas, ROOT / SALIDA_CSV)
    doc = escribir_json(filas, reglas_p, ROOT / SALIDA_CSV, ROOT / SALIDA_JSON)
    print(json.dumps(doc["resumen"]["por_certeza"]), doc["resumen"]["corroboracion_interior"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
