#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Ver el visor v2 en local con las secciones censales y la rotación, sin publicar (T-119).

PROYECTO: Diputado de Distrito
VERSIÓN: 1.0.0 · FECHA: 2026-11-09 · ESTADO: candidato
ANTERIOR: ninguna (fichero nuevo)
QUÉ HACE: reconstruye el seccionado INE 2025 de inputs/partes (sha256 verificado), genera visor/v2/datos/secciones/ y
  visor/v2/datos/rotacion.json (no versionados) y sirve el repositorio en http://localhost:8000/visor/v2/ (Ctrl+C para parar).
  Funciona igual en Windows PowerShell, macOS y Linux. Necesita internet (MapLibre) y geopandas (`pip install geopandas`).
Uso (desde la raíz del repositorio): python herramientas/ver_visor_v2_local.py [--puerto 8000] [--sin-servidor]
"""
from __future__ import annotations

import argparse
import functools
import hashlib
import http.server
import sys
import webbrowser
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "herramientas"))
ZIP_SHA = "55c9da7e34d3bb3cb725400c35b58e72f4db2ea8321ef91237a89e708d2dbcc4"


def reconstruir(destino: Path) -> Path:
    zp = destino / "seccionado_2025.zip"
    if zp.exists() and hashlib.sha256(zp.read_bytes()).hexdigest() == ZIP_SHA:
        return zp
    datos = b"".join((RAIZ / "inputs" / "partes" / f"seccionado_2025.zip.part0{i}").read_bytes() for i in range(3))
    if hashlib.sha256(datos).hexdigest() != ZIP_SHA:
        raise SystemExit("El seccionado reconstruido no coincide con el sha256 esperado.")
    destino.mkdir(parents=True, exist_ok=True)
    zp.write_bytes(datos)
    return zp


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--puerto", type=int, default=8000)
    ap.add_argument("--sin-servidor", action="store_true")
    a = ap.parse_args(argv)
    import generar_rotacion_visor as gr
    import generar_secciones_visor as gs
    zp = reconstruir(RAIZ / "inputs" / "reconstruido")
    gs.generar(zp, RAIZ / "visor" / "v2" / "datos" / "secciones", RAIZ / "datos" / "composicion",
               indice=RAIZ / "datos_abiertos" / "INDEX.json")
    gr.generar(RAIZ / "visor" / "v2" / "datos" / "rotacion.json", RAIZ / "datos" / "resultados" / "historico" / "rotacion", RAIZ / "datos" / "composicion")
    if a.sin_servidor:
        return 0
    url = f"http://localhost:{a.puerto}/visor/v2/"
    print(f"Abre {url} (elige una provincia, pulsa «Secciones» y acerca el mapa). Ctrl+C para parar.")
    webbrowser.open(url)
    h = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(RAIZ))
    http.server.ThreadingHTTPServer(("127.0.0.1", a.puerto), h).serve_forever()
    return 0


if __name__ == "__main__":
    sys.exit(main())
