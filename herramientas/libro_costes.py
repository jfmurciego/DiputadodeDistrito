#!/usr/bin/env python3
"""Libro de costes de chats de DDD: una fila por sesión, resumen semanal por rol y por tarea.

PROYECTO: Diputado de Distrito
VERSIÓN: 1.0.0 · FECHA: 2026-11-28 · ESTADO: candidato
CAMBIOS 1.0.0 (T-512, D-217): fichero nuevo. `docs/costes/libro.jsonl` con las 97 partidas del 14 al 28-11 (862,13 USD)
  copiadas a mano en ESTADO.md, TRASPASO_*, docs/traspasos/ y docs/registro/, importadas como `origen=historico`
  (sin id de sesión; cada fila lleva `fuente` fichero:línea) y el guion `--resumen`, `--comprobar`, `--anotar`.
ANTERIOR: ninguna (fichero nuevo)
QUÉ HACE: solo biblioteca estándar, sin red ni modelo. Filas JSON, una por línea:
  fecha (AAAA-MM-DD), sesion (id `session_…`), rol, tarea, cost_usd, origen (`historico`|`nuevo`), fuente (histórica) o
  modelo/pr/tokens (opcionales, nuevas). Una fila nueva exige sesión y rol; las históricas están exentas.
MOTIVO: el coste por rol y por tarea no se podía conocer (prosa en 12 ficheros, sin sesión, 0 partidas de Planificador
  y Operador); hallazgo C-3 de la investigación T-509. Quién anota no cambia: el Coordinador, desde `get_session`.
Uso: python herramientas/libro_costes.py --resumen [--desde AAAA-MM-DD] [--hasta AAAA-MM-DD]
     python herramientas/libro_costes.py --comprobar
     python herramientas/libro_costes.py --anotar --sesion session_… --rol R --tarea T --coste 1,23 [--fecha F --modelo M --pr N]
Salida: 0 si el libro es válido; 1 con una línea «::error» por fila inválida (también en --resumen); 2 en uso erróneo.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import sys
from collections import defaultdict
from decimal import Decimal, InvalidOperation
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
LIBRO = RAIZ / "docs" / "costes" / "libro.jsonl"
ROLES = ("implementador", "coordinador", "planificador", "operador", "auditoria", "revisor", "motor")
_SESION = re.compile(r"^session_[A-Za-z0-9]+$")


def leer(ruta: Path = LIBRO) -> list[dict]:
    filas = []
    for n, linea in enumerate(ruta.read_text(encoding="utf-8").splitlines(), 1):
        if linea.strip():
            fila = json.loads(linea)
            fila["_linea"] = n
            filas.append(fila)
    return filas


def validar(filas: list[dict]) -> list[str]:
    """Errores del libro. Las históricas solo exigen fecha, rol conocido, tarea y coste; las nuevas, también sesión."""
    errores = []
    vistas = set()
    for f in filas:
        n = f.get("_linea", "?")
        origen = f.get("origen")
        if origen not in ("historico", "nuevo"):
            errores.append(f"línea {n}: origen debe ser «historico» o «nuevo»")
            continue
        try:
            dt.date.fromisoformat(str(f.get("fecha")))
        except ValueError:
            errores.append(f"línea {n}: fecha no es AAAA-MM-DD")
        if f.get("rol") not in ROLES:
            errores.append(f"línea {n}: rol ausente o desconocido ({f.get('rol')!r}); válidos: {', '.join(ROLES)}")
        if not str(f.get("tarea") or "").strip():
            errores.append(f"línea {n}: falta tarea")
        try:
            if Decimal(str(f.get("cost_usd"))) < 0:
                errores.append(f"línea {n}: cost_usd negativo")
        except InvalidOperation:
            errores.append(f"línea {n}: cost_usd no es un número")
        if origen == "nuevo":
            sesion = f.get("sesion")
            if not sesion or not _SESION.match(str(sesion)):
                errores.append(f"línea {n}: fila nueva sin id de sesión válido (session_…)")
            elif (sesion, f.get("tarea")) in vistas:
                errores.append(f"línea {n}: sesión {sesion} ya anotada para {f.get('tarea')}")
            vistas.add((sesion, f.get("tarea")))
    return errores


def _semana(fecha: str) -> str:
    anio, sem, _ = dt.date.fromisoformat(fecha).isocalendar()
    return f"{anio}-S{sem:02d}"


def resumen(filas: list[dict], desde: str | None = None, hasta: str | None = None) -> str:
    sel = [f for f in filas if (not desde or f["fecha"] >= desde) and (not hasta or f["fecha"] <= hasta)]
    coste = lambda f: Decimal(str(f["cost_usd"]))  # noqa: E731
    total = sum((coste(f) for f in sel), Decimal(0))
    por_rol, por_tarea = defaultdict(Decimal), defaultdict(Decimal)
    por_semana = defaultdict(lambda: defaultdict(Decimal))
    for f in sel:
        por_rol[f["rol"]] += coste(f)
        por_tarea[f["tarea"]] += coste(f)
        por_semana[_semana(f["fecha"])][f["rol"]] += coste(f)
    pct = lambda x: f"{(x / total * 100):.1f} %" if total else "—"  # noqa: E731
    hist = sum(1 for f in sel if f["origen"] == "historico")
    out = [f"Libro de costes: {len(sel)} partidas ({hist} históricas), total {total:.2f} USD"
           + (f", desde {desde}" if desde else "") + (f", hasta {hasta}" if hasta else ""), "", "Por rol:"]
    out += [f"  {r:<14}{v:>10.2f} USD  {pct(v):>8}" for r, v in sorted(por_rol.items(), key=lambda kv: -kv[1])]
    out += ["", "Por semana y rol (semana ISO):"]
    for s in sorted(por_semana):
        suma = sum(por_semana[s].values())
        det = " · ".join(f"{r} {v:.2f}" for r, v in sorted(por_semana[s].items(), key=lambda kv: -kv[1]))
        out.append(f"  {s}  {suma:>9.2f} USD  ({det})")
    out += ["", "Por tarea (mayores 15):"]
    out += [f"  {t:<26}{v:>10.2f} USD" for t, v in sorted(por_tarea.items(), key=lambda kv: -kv[1])[:15]]
    return "\n".join(out)


def anotar(ruta: Path, sesion: str, rol: str, tarea: str, coste: str, fecha: str | None, modelo: str | None,
           pr: str | None) -> list[str]:
    fila = {"fecha": fecha or dt.date.today().isoformat(), "sesion": sesion, "rol": rol, "tarea": tarea,
            "cost_usd": float(coste.replace(",", ".")), "origen": "nuevo"}
    if modelo:
        fila["modelo"] = modelo
    if pr:
        fila["pr"] = pr
    existentes = leer(ruta) if ruta.exists() else []
    errores = validar(existentes + [dict(fila, _linea=len(existentes) + 1)])
    if not errores:
        with ruta.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(fila, ensure_ascii=False) + "\n")
    return errores


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--resumen", action="store_true")
    g.add_argument("--comprobar", action="store_true")
    g.add_argument("--anotar", action="store_true")
    p.add_argument("--libro", type=Path, default=LIBRO)
    p.add_argument("--desde")
    p.add_argument("--hasta")
    p.add_argument("--sesion")
    p.add_argument("--rol")
    p.add_argument("--tarea")
    p.add_argument("--coste")
    p.add_argument("--fecha")
    p.add_argument("--modelo")
    p.add_argument("--pr")
    a = p.parse_args(argv)
    if a.anotar:
        if not (a.rol and a.tarea and a.coste):
            p.error("--anotar exige --rol, --tarea y --coste (y --sesion)")
        errores = anotar(a.libro, a.sesion or "", a.rol, a.tarea, a.coste, a.fecha, a.modelo, a.pr)
    else:
        filas = leer(a.libro)
        errores = validar(filas)
        if a.resumen:
            print(resumen(filas, a.desde, a.hasta))
    for e in errores:
        print(f"::error::{e}", file=sys.stderr)
    return 1 if errores else 0


if __name__ == "__main__":
    sys.exit(main())
