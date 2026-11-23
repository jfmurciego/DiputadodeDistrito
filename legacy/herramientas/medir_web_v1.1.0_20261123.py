"""Mide la web pública desde el runner: código HTTP, tiempo hasta el primer byte, tiempo total y bytes, con y sin compresión (T-440).

PROYECTO: Diputado de Distrito
VERSIÓN: 1.1.0 · FECHA: 2026-11-23 · ESTADO: candidato
ANTERIOR: legacy/herramientas/medir_web_v1.0.0_20261123.py
CAMBIOS: 1.1.0 (run 45087927501: 403 desde el runner en todas las páginas salvo explorar.js, ~3-5 KB, ~50 ms): se pide como un navegador
  (User-Agent y Accept habituales) y la tabla distingue «bloqueado por el CDN» (403 con la cabecera `cf-mitigated` o servido por
  Cloudflare) de una web caída. Sale 1 si nada responde 200 y no todo está bloqueado por el CDN; si todo está bloqueado, avisa y sale 0.
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
FORMATO = "%{http_code} %{time_starttransfer} %{time_total} %{size_download} |%header{cf-mitigated}|%header{server}|"
AVISO_CDN = "Aviso: respuestas bloqueadas por el CDN"
NAVEGADOR = ["-A", "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0 Safari/537.36",
             "-H", "Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
             "-H", "Accept-Language: es-ES,es;q=0.9"]


def bloqueado_cdn(codigo: int, mitigado: str, servidor: str) -> bool:
    """403 del CDN: Cloudflare marca sus retos y bloqueos con `cf-mitigated`; sin ella, un 403 servido por Cloudflare también cuenta."""
    return codigo == 403 and (bool(mitigado.strip()) or servidor.strip().lower() == "cloudflare")


def medir(url: str, comprimido: bool, ejecutar=subprocess.run) -> dict:
    args = ["curl", "-s", "-o", "/dev/null", "-w", FORMATO, "--max-time", "60", "-H", "Cache-Control: no-cache", *NAVEGADOR]
    args += ["--compressed"] if comprimido else ["-H", "Accept-Encoding: identity"]
    r = ejecutar(args + [url], capture_output=True, text=True)
    try:
        numeros, mitigado, servidor = (r.stdout.split("|") + ["", ""])[:3]
        codigo, ttfb, total, size = numeros.split()
        return {"codigo": int(codigo), "ttfb": float(ttfb), "total": float(total), "bytes": int(float(size)),
                "cdn": bloqueado_cdn(int(codigo), mitigado, servidor)}
    except ValueError:
        return {"codigo": 0, "ttfb": 0.0, "total": 0.0, "bytes": 0, "cdn": False}


def fila(etiqueta: str, comprimido: bool, ms: list[dict]) -> str:
    codigos = " ".join(sorted({str(m["codigo"]) + (" (bloqueado por el CDN)" if m.get("cdn") else "") for m in ms}))
    med = lambda k: statistics.median(m[k] for m in ms)  # noqa: E731
    tiempos = lambda k: "/".join(f"{m[k] * 1000:.0f}" for m in ms)  # noqa: E731
    return (f"| {etiqueta} | {'sí' if comprimido else 'no'} | {codigos} | {med('ttfb') * 1000:.0f} ({tiempos('ttfb')}) | "
            f"{med('total') * 1000:.0f} ({tiempos('total')}) | {int(med('bytes')):,} |".replace(",", "."))


def tabla(base: str, repeticiones: int, ejecutar=subprocess.run) -> tuple[str, int]:
    lineas = [f"Medición de {base} ({repeticiones} veces por fila; mediana y, entre paréntesis, cada intento en ms)", "",
              "| Página o fichero | Compresión | HTTP | Primer byte ms | Total ms | Bytes |", "|---|---|---|---|---|---|"]
    ok = cdn = total = 0
    for etiqueta, ruta in URLS:
        for comprimido in (True, False):
            ms = [medir(base.rstrip("/") + ruta, comprimido, ejecutar) for _ in range(repeticiones)]
            ok += sum(m["codigo"] == 200 for m in ms)
            cdn += sum(bool(m.get("cdn")) for m in ms)
            total += len(ms)
            lineas.append(fila(etiqueta, comprimido, ms))
    if cdn:
        lineas += ["", f"{AVISO_CDN}: {cdn} de {total} peticiones. Es el filtro de bots del CDN (Cloudflare), no la web caída; "
                   "esas filas no miden la web."]
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
        if AVISO_CDN in texto:
            print("::warning::Ninguna página respondió 200: el CDN bloquea al runner (ver la tabla); no es la web caída")
            return 0
        print("::error::Ninguna página respondió 200")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
