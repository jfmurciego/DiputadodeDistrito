#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""P10 desde la copia de R2 con aviso de cambios del INE (T-323, D-112).

PROYECTO: Diputado de Distrito
VERSIÓN: 1.0.0
NOMBRE DE VERSIÓN: P10 lee de R2 y consulta el INE sin descargar
FECHA: 2026-11-14
ESTADO: candidato
CAMBIOS: 1.0.0: fichero nuevo (T-323).
MOTIVO: D-112: P10 no descarga del INE en cada ejecución; usa el paquete de R2 (clave por package_sha256 del contrato, sha256 verificado) y
  solo consulta el INE con HEAD (Content-Length, Last-Modified) frente a la huella del índice orchestracion/fuentes_r2.json.
ANTERIOR: ninguna (fichero nuevo)
QUÉ HACE: `preparar`: 1) restaura el paquete P10 del contrato desde R2 y lo valida (bateria_motor.paquete_p10_desde_r2); sin paquete o sin
  credenciales: aviso y `desde_r2=false` (P10 adquiere como hasta ahora). 2) con paquete, consulta el INE (HEAD, sin descargar): fichero
  cambiado = evidencia positiva → `::error::FUENTE_INE_CAMBIADA`, salida 54, sin sustituir nada (decide el propietario). Sin respuesta,
  503, 403 o red caída → `::warning::` y sigue con R2 (política T-246: solo bloquea la evidencia positiva). Paquete corrupto: salida 53.
USO: python herramientas/p10_desde_r2.py preparar --territory aut02 --edition 2025 --population-year 2025 --section-year 2025 --out .ddd-source-package
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INDICE = ROOT / "orchestracion" / "fuentes_r2.json"
SALIDA_CAMBIADA = 54
SALIDA_CORRUPTO = 53


def head_ine(url: str, timeout: int = 30) -> tuple[int, dict]:
    """HEAD al INE sin descargar el cuerpo. Devuelve (estado, cabeceras en minúsculas)."""
    req = urllib.request.Request(url, method="HEAD", headers={"User-Agent": "DiputadoDeDistrito/2.1 (+GitHub Actions; comprobación de cambios)"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, {k.lower(): v for k, v in r.headers.items()}
    except urllib.error.HTTPError as exc:
        return exc.code, {k.lower(): v for k, v in exc.headers.items()}


def fuentes_necesarias(population_year: str, section_year: str, indice: Path = INDICE) -> tuple[list[str], list[str]]:
    """(nombres del índice que consume el territorio, nombres que faltan en el índice)."""
    fuentes = json.loads(indice.read_text(encoding="utf-8"))["fuentes"]
    pedidos = [f"seccionado_{section_year}.zip", "65034.csv.zip"]
    return [n for n in pedidos if n in fuentes], [n for n in pedidos if n not in fuentes]


def comprobar_ine(nombres: list[str], head=head_ine, indice: Path = INDICE) -> tuple[list[str], list[str]]:
    """(cambiadas, avisos). Cambiada = evidencia positiva: Content-Length de un .zip distinto de `bytes` o Last-Modified posterior a
    `descargado_en`. Cualquier otra cosa (red, 5xx, 403, 404, sin cabeceras) es solo un aviso."""
    fuentes = json.loads(indice.read_text(encoding="utf-8"))["fuentes"]
    cambiadas, avisos = [], []
    for n in nombres:
        f = fuentes[n]
        url = f["origen_url"]
        try:
            estado, h = head(url)
        except Exception as exc:  # noqa: BLE001 - sin red al INE: se degrada
            avisos.append(f"{n}: sin respuesta del INE ({exc}); no se puede comprobar si cambió")
            continue
        if not 200 <= estado < 300:
            avisos.append(f"{n}: el INE respondió {estado}; no se puede comprobar si cambió")
            continue
        motivos = []
        cl = h.get("content-length")
        if url.lower().endswith(".zip") and cl and cl.isdigit() and int(cl) != int(f["bytes"]):
            motivos.append(f"tamaño {cl} != {f['bytes']}")
        lm = h.get("last-modified")
        if lm:
            try:
                fecha = parsedate_to_datetime(lm)
                if fecha.tzinfo is None:
                    fecha = fecha.replace(tzinfo=timezone.utc)
                limite = datetime.fromisoformat(f["descargado_en"]).replace(tzinfo=timezone.utc).replace(hour=23, minute=59, second=59)
                if fecha > limite:
                    motivos.append(f"Last-Modified {lm} posterior a la copia ({f['descargado_en']})")
            except (TypeError, ValueError):
                avisos.append(f"{n}: Last-Modified ilegible ({lm})")
        if not cl and not lm:
            avisos.append(f"{n}: el INE no devolvió Content-Length ni Last-Modified; no se puede comprobar")
        if motivos:
            cambiadas.append(f"{n} ({'; '.join(motivos)})")
    return cambiadas, avisos


def _salida(clave: str, valor: str) -> None:
    ruta = os.environ.get("GITHUB_OUTPUT")
    if ruta:
        with open(ruta, "a", encoding="utf-8") as fh:
            fh.write(f"{clave}={valor}\n")


def preparar(territorio: str, edicion: str, anio_poblacion: str, anio_seccion: str, destino: Path, *, restaurar=None, head=head_ine,
             indice: Path = INDICE) -> int:
    from herramientas import bateria_motor as bm
    restaurar = restaurar or bm.paquete_p10_desde_r2
    work = destino.parent / "_p10_r2"
    try:
        carpeta = restaurar(territorio, work)
    except bm.PaqueteP10Corrupto as exc:
        print(f"::error::P10_PAQUETE_R2_CORRUPTO {territorio}: {exc}", file=sys.stderr)
        _salida("desde_r2", "false")
        return SALIDA_CORRUPTO
    if carpeta is None:
        print(f"::warning::P10_SIN_PAQUETE_R2 {territorio}: no hay paquete en R2 o faltan credenciales; P10 adquiere de la fuente oficial como hasta ahora.")
        _salida("desde_r2", "false")
        return 0
    nombres, faltan = fuentes_necesarias(anio_poblacion, anio_seccion, indice)
    for n in faltan:
        print(f"::warning::P10_FUENTE_SIN_HUELLA {n} no está en fuentes_r2.json: no se comprueba si el INE cambió.")
    cambiadas, avisos = comprobar_ine(nombres, head, indice)
    for a in avisos:
        print(f"::warning::P10_INE_SIN_COMPROBAR {a}")
    if cambiadas:
        print("::error::FUENTE_INE_CAMBIADA " + "; ".join(cambiadas) + ". P10 se detiene: no se sigue con datos viejos ni se sustituye en silencio. "
              "El propietario decide si se adopta la versión nueva (D-112).", file=sys.stderr)
        _salida("desde_r2", "false")
        return SALIDA_CAMBIADA
    shutil.rmtree(destino, ignore_errors=True)
    shutil.copytree(carpeta, destino)
    shutil.rmtree(work, ignore_errors=True)
    print(f"p10_desde_r2: {territorio} restaurado desde R2 (sha256 verificado); INE sin cambios detectados ({len(nombres)} fuentes consultadas).")
    _salida("desde_r2", "true")
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("preparar")
    for k in ("territory", "edition", "population-year", "section-year", "out"):
        p.add_argument("--" + k, required=True)
    a = ap.parse_args(argv)
    return preparar(a.territory, a.edition, a.population_year, a.section_year, Path(a.out))


if __name__ == "__main__":
    raise SystemExit(main())
