"""Mide la web pública desde el runner: código HTTP, tiempo hasta el primer byte, tiempo total y bytes, con y sin compresión (T-440).

PROYECTO: Diputado de Distrito
VERSIÓN: 1.0.0 · FECHA: 2026-11-22 · ESTADO: candidato
ANTERIOR: ninguna (fichero nuevo)
MOTIVO: el propietario (22-11) quiere cifras reales de carga de la web (portada, una página de territorio, el mapa y sus datos
  principales) para el diseño de la carga ligera en el móvil (T-441). La nube no llega a la web; el runner sí: se mide allí y se
  imprime como tabla en el log y en el resumen del job, para leerlo desde la nube.
QUÉ HACE: por cada URL de `URLS`, `REPETICIONES` veces con compresión (`--compressed`: gzip/br) y otras tantas sin ella
  (`Accept-Encoding: identity`), llama a `curl` (sin caché, sin cookies, sin secretos) y anota código HTTP, tiempo hasta el primer
  byte, tiempo total y bytes transferidos. Solo lectura. Sale 0 aunque una URL falle (la tabla lo muestra); sale 1 solo si ninguna
  responde 200.
USO: python3 herramientas/medir_web.py [--base https://diputadodedistrito.es] [--repeticiones 3] [--resumen $GITHUB_STEP_SUMMARY]
"""
from __future__ import annotations

import argparse
import statistics
import subprocess
import sys

BASE = "https://diputadodedistrito.es"
REPETICIONES = 3
URLS = [  # (etiqueta, ruta): portada, una página de territorio, el mapa y sus datos principales
    ("Portada", "/"),
    ("Página de territorio (Madrid)", "/mapa/?territorio=nac28"),
    ("Mapa (Explorar)", "/mapa/"),
    ("Código del mapa", "/mapa/explorar.js"),
    ("Índice de datos", "/datos/INDEX.json"),
    ("Provincias", "/v2/datos/provincias.json"),
    ("Distritos de Madrid", "/datos/nac28/distritos.geojson"),
    ("Registro del visor", "/data/viewer-results.json"),
    ("Doble vuelta: índice", "/mapa/datos/INDEX.json"),
]
FORMATO = "%{http_code} %{time_starttransfer} %{time_total} %{size_download}"


def medir(url: str, comprimido: bool, ejecutar=subprocess.run) -> dict:
    args = ["curl", "-s", "-o", "/dev/null", "-w", FORMATO, "--max-time", "60", "-H", "Cache-Control: no-cache"]
    args += ["--compressed"] if comprimido else ["-H", "Accept-Encoding: identity"]
    r = ejecutar(args + [url], capture_output=True, text=True)
    try:
        codigo, ttfb, total, size = r.stdout.split()
        return {"codigo": int(codigo), "ttfb": float(ttfb), "total": float(total), "bytes": int(float(size))}
    except ValueError:
        return {"codigo": 0, "ttfb": 0.0, "total": 0.0, "bytes": 0}


def fila(etiqueta: str, comprimido: bool, ms: list[dict]) -> str:
    codigos = " ".join(sorted({str(m["codigo"]) for m in ms}))
    med = lambda k: statistics.median(m[k] for m in ms)  # noqa: E731
    tiempos = lambda k: "/".join(f"{m[k] * 1000:.0f}" for m in ms)  # noqa: E731
    return (f"| {etiqueta} | {'sí' if comprimido else 'no'} | {codigos} | {med('ttfb') * 1000:.0f} ({tiempos('ttfb')}) | "
            f"{med('total') * 1000:.0f} ({tiempos('total')}) | {int(med('bytes')):,} |".replace(",", "."))


def tabla(base: str, repeticiones: int, ejecutar=subprocess.run) -> tuple[str, int]:
    lineas = [f"Medición de {base} ({repeticiones} veces por fila; mediana y, entre paréntesis, cada intento en ms)", "",
              "| Página o fichero | Compresión | HTTP | Primer byte ms | Total ms | Bytes |", "|---|---|---|---|---|---|"]
    ok = 0
    for etiqueta, ruta in URLS:
        for comprimido in (True, False):
            ms = [medir(base.rstrip("/") + ruta, comprimido, ejecutar) for _ in range(repeticiones)]
            ok += sum(m["codigo"] == 200 for m in ms)
            lineas.append(fila(etiqueta, comprimido, ms))
    return "\n".join(lineas) + "\n", ok


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--base", default=BASE)
    ap.add_argument("--repeticiones", type=int, default=REPETICIONES)
    ap.add_argument("--resumen", default="")
    a = ap.parse_args(argv)
    texto, ok = tabla(a.base, a.repeticiones)
    print(texto)
    if a.resumen:
        with open(a.resumen, "a", encoding="utf-8") as f:
            f.write(texto)
    if ok == 0:
        print("::error::Ninguna página respondió 200")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
