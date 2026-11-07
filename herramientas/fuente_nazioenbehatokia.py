#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Fuente secundaria del histórico de generales por sección: Observatorio Electoral de las Naciones (T-89).

PROYECTO: Diputado de Distrito
VERSIÓN: 1.0.0 · FECHA: 2026-11-07 · ESTADO: candidato
CAMBIOS: 1.0.0: fichero nuevo.
MOTIVO: decisión D-8 del propietario: histórico de generales 2011-2023 por sección con una segunda fuente y contraste
  con la oficial.
ANTERIOR: ninguna (fichero nuevo)
QUÉ HACE: (1) lector del formato compacto: data/index.json, data/<elección>/sekzioa/<cpro>.json con s=siglas, k=colores,
  f=familia, b=bloque y r={sección: [censo, votantes, votos a candidaturas, [[índice de partido, votos]…]]}, y
  geo/sekzioak/<año de seccionado>/<cpro>.json; (2) espejo: descarga, calcula sha256 y escribe el manifiesto
  orchestracion/fuente_nazioenbehatokia.json (entrada del catálogo de procedencia); con --subir copia los ficheros a R2
  (clave fuentes/nazioenbehatokia/<ruta>, mismo cliente aws que el archivista); (3) contraste con la fuente oficial
  (configuracion/resultados_oficiales_congreso_*.csv): la suma por sección excluye el voto CERA, así que la
  fuente secundaria nunca puede SUPERAR a la oficial (ERROR) y su defecto se reporta (AVISO si > 10 %).
  Los partidos sin sigla idéntica (p. ej. PSOE frente a PSC) se cuentan como «sin_homologar»; no son error.
Uso: python herramientas/fuente_nazioenbehatokia.py espejar --destino DIR [--subir] [--oficiales ...]
     python herramientas/fuente_nazioenbehatokia.py contrastar --destino DIR
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import sys
import time
import urllib.error
import urllib.request
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = "https://nazioenbehatokia.eus/"
SALIDA = "orchestracion/fuente_nazioenbehatokia.json"
SCHEMA = "ddd.fuente-secundaria/1.0"
UMBRAL_DEFECTO = 0.10
OFICIALES = {"202307": "configuracion/resultados_oficiales_congreso_2023.csv",
             "201911": "configuracion/resultados_oficiales_congreso_2019_11.csv"}


# --- lector del formato compacto -------------------------------------------------------------------------------
def leer_provincia(doc: dict) -> dict:
    """Devuelve {seccion: {censo, votantes, votos_candidaturas, votos: {sigla: n}}} de un data/<elec>/sekzioa/<cpro>.json."""
    siglas = doc["s"]
    out = {}
    for sec, (censo, votantes, cand, partidos) in doc["r"].items():
        votos: Counter = Counter()
        for i, n in partidos:
            votos[siglas[i]] += n
        out[sec] = {"censo": censo, "votantes": votantes, "votos_candidaturas": cand, "votos": dict(votos)}
    return out


def totales_provincia(doc: dict) -> dict[str, int]:
    t: Counter = Counter()
    for s in leer_provincia(doc).values():
        t.update(s["votos"])
    return dict(t)


# --- espejo ----------------------------------------------------------------------------------------------------
def rutas(index: dict) -> list[str]:
    provs = sorted(index["goikoak"]["probintzia"])
    out = ["data/index.json"]
    for e in index["hauteskundeak"]:
        for c in provs:
            out += [f"data/{e['k']}/sekzioa/{c}.json", f"geo/sekzioak/{e['sekzioUrtea']}/{c}.json"]
    return out


def _get(url: str) -> bytes:
    for i in range(5):
        try:
            with urllib.request.urlopen(url, timeout=60) as r:
                return r.read()
        except urllib.error.HTTPError as e:
            if e.code < 500 and e.code != 429:
                raise
        except OSError:
            pass
        time.sleep(2 ** (i + 1))
    raise RuntimeError(f"no se pudo descargar {url}")


def espejar(destino: Path, descargar=_get) -> dict:
    destino.mkdir(parents=True, exist_ok=True)
    cuerpo = descargar(BASE + "data/index.json")
    index = json.loads(cuerpo)
    ficheros = {}
    for ruta in rutas(index):
        b = cuerpo if ruta == "data/index.json" else descargar(BASE + ruta)
        p = destino / ruta
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(b)
        ficheros[ruta] = {"bytes": len(b), "sha256": hashlib.sha256(b).hexdigest()}
    return {
        "schema": SCHEMA,
        "id": "nazioenbehatokia",
        "proveedor": "Observatorio Electoral de las Naciones",
        "url": BASE,
        "rol": "secundaria",
        "contenido": "generales 2011-2023 por sección censal",
        "elecciones": [{"clave": e["k"], "seccionado": e["sekzioUrtea"]} for e in index["hauteskundeak"]],
        "copia_r2_prefijo": "fuentes/nazioenbehatokia/",
        "ficheros": dict(sorted(ficheros.items())),
    }


def subir_r2(manifiesto: dict, destino: Path) -> int:
    from archivar_artefactos_r2 import r2_cliente
    sha, subir = r2_cliente(os.environ["R2_BUCKET"], os.environ["R2_ACCOUNT_ID"])
    n = 0
    for ruta, f in manifiesto["ficheros"].items():
        k = manifiesto["copia_r2_prefijo"] + ruta
        if sha(k) != f["sha256"]:
            subir(k, destino / ruta, f["sha256"])
            n += 1
    return n


# --- contraste con la fuente oficial -----------------------------------------------------------------------------
def contrastar_provincia(totales: dict[str, int], oficial: dict[str, int], umbral: float = UMBRAL_DEFECTO) -> dict:
    """oficial = {sigla: votos} de la provincia. Devuelve comparaciones, sin_homologar y errores/avisos."""
    comp, sin, errores, avisos = {}, [], [], []
    for p, v in oficial.items():
        if p not in totales:
            sin.append(p)
            continue
        d = (v - totales[p]) / v if v else 0.0
        comp[p] = {"oficial": v, "secundaria": totales[p], "defecto": round(d, 5)}
        if totales[p] > v:
            errores.append(f"{p}: secundaria {totales[p]} > oficial {v}")
        elif d > umbral:
            avisos.append(f"{p}: defecto {d:.1%}")
    return {"comparaciones": comp, "sin_homologar": sorted(sin), "errores": errores, "avisos": avisos}


def contrastar(destino: Path, raiz: Path = ROOT, oficiales: dict | None = None) -> dict:
    res = {}
    for clave, rel in (oficiales or OFICIALES).items():
        of: dict[str, dict] = {}
        with open(raiz / rel, encoding="utf-8", newline="") as f:
            for r in csv.DictReader(f):
                of.setdefault(r["codigo"], {})[r["partido"]] = int(r["votos"])
        provs = {"comparadas": 0, "sin_homologar": Counter(), "errores": [], "avisos": [], "defecto_max": 0.0}
        for c, o in sorted(of.items()):
            doc = json.loads((destino / f"data/{clave}/sekzioa/{c}.json").read_text(encoding="utf-8"))
            r = contrastar_provincia(totales_provincia(doc), o)
            provs["comparadas"] += len(r["comparaciones"])
            provs["sin_homologar"].update(r["sin_homologar"])
            provs["errores"] += [f"{c} {e}" for e in r["errores"]]
            provs["avisos"] += [f"{c} {e}" for e in r["avisos"]]
            provs["defecto_max"] = max([provs["defecto_max"]] + [x["defecto"] for x in r["comparaciones"].values()])
        provs["sin_homologar"] = dict(sorted(provs["sin_homologar"].items()))
        res[clave] = provs
    return res


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("orden", choices=["espejar", "contrastar"])
    ap.add_argument("--destino", type=Path, required=True)
    ap.add_argument("--subir", action="store_true")
    a = ap.parse_args(argv)
    if a.orden == "espejar":
        m = espejar(a.destino)
        m["contraste"] = contrastar(a.destino)
        if a.subir:
            sys.path.insert(0, str(Path(__file__).parent))
            m["subidos_r2"] = subir_r2(m, a.destino)
        (ROOT / SALIDA).write_text(json.dumps(m, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        print(f"{len(m['ficheros'])} ficheros; errores de contraste: {sum(len(v['errores']) for v in m['contraste'].values())}")
        return 0
    c = contrastar(a.destino)
    print(json.dumps(c, ensure_ascii=False, indent=1))
    return 1 if any(v["errores"] for v in c.values()) else 0


if __name__ == "__main__":
    sys.exit(main())
