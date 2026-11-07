#!/usr/bin/env python3
"""Numeración automática del registro de cambios (T-46).

PROYECTO: Diputado de Distrito
VERSIÓN: 1.0.0
NOMBRE DE VERSIÓN: Registro por fragmentos
FECHA: 2026-11-07
ESTADO: candidato
CAMBIOS: versión inicial.
MOTIVO: cada PR editaba la cabecera de docs/REGISTRO_DE_CAMBIOS.md con un número pedido a mano; dos PR abiertas
  chocaban siempre (conflictos y renumeraciones en #429-#436). Ahora cada PR deja su entrada en un fichero propio
  sin número y este script, desde un job de main, asigna los números en orden.
QUÉ HACE: busca en docs/registro/ las entradas (AAAA-MM-DD_<rama>.md) que aún no están en el índice del registro;
  por cada una, en orden de fecha y nombre, copia el registro vigente a legacy/docs/ (gobernanza), sube la Versión
  en 1, reescribe la cabecera y añade la entrada arriba del índice. Idempotente: sin entradas pendientes no cambia nada.
NO HACE: commit ni push (lo hace el workflow «Numeración del Registro»); no toca las entradas históricas.
ANTERIOR: ninguna (fichero nuevo)

Uso: python herramientas/numerar_registro.py [--raiz RUTA] [--fecha AAAA-MM-DD] [--comprobar]
Salida: una línea por entrada numerada («1.0.106 docs/registro/...»); 0 siempre salvo error de formato (1).
"""
from __future__ import annotations

import argparse
import datetime as _dt
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRO = "docs/REGISTRO_DE_CAMBIOS.md"
FRAGMENTOS = "docs/registro"
INICIO = "<!-- indice-registro:inicio -->"
FIN = "<!-- indice-registro:fin -->"
TITULO_INDICE = "## Índice de entradas por fichero (numeración automática)"

NOMBRE_RE = re.compile(r"^(\d{4}-\d{2}-\d{2})_[a-z0-9][a-z0-9._-]*\.md$")
CABECERA_RE = re.compile(r"^## (\d{4}-\d{2}-\d{2}) — (.+?) — (.+?)\s*$")
VERSION_RE = re.compile(r"(?mi)^\s*Versi[oó]n:\s*`?(\d+(?:\.\d+)+)`?\s*$")
INDICE_RE = re.compile(r"^- (\d+(?:\.\d+)+) · \[[^\]]*\]\((registro/[^)]+)\)\s*$")


class FormatoError(ValueError):
    pass


def siguiente(version: str) -> str:
    partes = version.split(".")
    partes[-1] = str(int(partes[-1]) + 1)
    return ".".join(partes)


def leer_fragmento(ruta: Path) -> tuple[str, str, str]:
    """Devuelve (fecha, tarea, título) o lanza FormatoError con el motivo."""
    m = NOMBRE_RE.match(ruta.name)
    if not m:
        raise FormatoError(f"{ruta.name}: el nombre debe ser AAAA-MM-DD_<rama>.md (minúsculas, sin barras)")
    lineas = ruta.read_text(encoding="utf-8").splitlines()
    no_vacias = [ln for ln in lineas if ln.strip()]
    if not no_vacias:
        raise FormatoError(f"{ruta.name}: vacío")
    c = CABECERA_RE.match(no_vacias[0])
    if not c:
        raise FormatoError(f"{ruta.name}: la primera línea debe ser «## AAAA-MM-DD — T-xx — título»")
    if c.group(1) != m.group(1):
        raise FormatoError(f"{ruta.name}: la fecha del título ({c.group(1)}) no es la del nombre ({m.group(1)})")
    texto = "\n".join(lineas)
    if VERSION_RE.search(texto) or "<!--" in texto:
        raise FormatoError(f"{ruta.name}: sin número ni cabecera: la Versión la pone el job de main")
    if len(no_vacias) < 2:
        raise FormatoError(f"{ruta.name}: falta el cuerpo (causa, cambio, pruebas y PR/run)")
    return c.group(1), c.group(2).strip(), c.group(3).strip()


def fragmentos(raiz: Path) -> list[Path]:
    d = raiz / FRAGMENTOS
    if not d.is_dir():
        return []
    return sorted((p for p in d.glob("*.md") if p.name.lower() != "readme.md"), key=lambda p: p.name)


def indice(texto: str) -> list[tuple[str, str]]:
    """[(versión, ruta relativa a docs/)] del índice, en el orden del fichero."""
    if INICIO not in texto or FIN not in texto:
        return []
    bloque = texto[texto.index(INICIO) + len(INICIO):texto.index(FIN)]
    return [(m.group(1), m.group(2)) for ln in bloque.splitlines() if (m := INDICE_RE.match(ln.strip()))]


def _cabecera(texto: str) -> tuple[int, int]:
    ini = texto.find("<!--")
    fin = texto.find("-->", ini)
    if ini != 0 or fin < 0:
        raise FormatoError(f"{REGISTRO}: debe empezar por la cabecera <!-- … -->")
    return ini, fin + 3


def numerar(raiz: Path, fecha: str | None = None, escribir: bool = True) -> list[tuple[str, str]]:
    fecha = fecha or _dt.date.today().isoformat()
    ruta = raiz / REGISTRO
    texto = ruta.read_text(encoding="utf-8")
    ya = {rel for _, rel in indice(texto)}
    pendientes = []
    for f in fragmentos(raiz):
        rel = f"registro/{f.name}"
        if rel not in ya:
            pendientes.append((f, rel, *leer_fragmento(f)))
    pendientes.sort(key=lambda x: (x[2], x[0].name))
    hechos = []
    for f, rel, fecha_f, tarea, titulo in pendientes:
        m = VERSION_RE.search(texto[:5000])
        if not m:
            raise FormatoError(f"{REGISTRO}: cabecera sin Versión")
        previa = m.group(1)
        nueva = siguiente(previa)
        copia = f"legacy/docs/REGISTRO_DE_CAMBIOS_v{previa}_registro_{fecha.replace('-', '')}.md"
        if escribir:
            (raiz / copia).parent.mkdir(parents=True, exist_ok=True)
            (raiz / copia).write_text(texto, encoding="utf-8")
        ini, fin = _cabecera(texto)
        nombre = re.search(r"(?m)^Nombre:.*$", texto[ini:fin])
        cab = "\n".join([
            "<!--",
            nombre.group(0) if nombre else "Nombre: Registro de cambios DDD",
            f"Versión: {nueva}",
            f"Fecha: {fecha}",
            f"Alcance: {tarea} — {titulo}",
            "Estado: vigente",
            f"Cambios/motivo: entrada docs/{rel} numerada al fusionar en main (herramientas/numerar_registro.py)",
            f"Anterior: {copia}",
            "-->",
        ])
        cuerpo = texto[fin:]
        linea = f"- {nueva} · [{fecha_f} — {tarea} — {titulo}]({rel})"
        if INICIO in cuerpo and FIN in cuerpo:
            i = cuerpo.index(INICIO) + len(INICIO)
            cuerpo = cuerpo[:i] + "\n" + linea + cuerpo[i:]
        else:
            cuerpo = (f"\n\n{TITULO_INDICE}\n\nCada entrada vive en `docs/registro/`; el número lo asigna el job "
                      f"«Numeración del Registro» al fusionar en `main`.\n\n{INICIO}\n{linea}\n{FIN}\n\n"
                      + cuerpo.lstrip("\n"))
        texto = cab + cuerpo
        hechos.append((nueva, f"docs/{rel}"))
    if escribir and hechos:
        ruta.write_text(texto, encoding="utf-8")
    return hechos


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--raiz", type=Path, default=ROOT)
    ap.add_argument("--fecha", help="fecha de numeración (por defecto, hoy)")
    ap.add_argument("--comprobar", action="store_true", help="solo lista lo pendiente, sin escribir")
    a = ap.parse_args(argv)
    try:
        hechos = numerar(a.raiz.resolve(), a.fecha, escribir=not a.comprobar)
    except FormatoError as e:
        print(f"::error::{e}")
        return 1
    for version, rel in hechos:
        print(f"{version} {rel}")
    if not hechos:
        print("Sin entradas pendientes.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
