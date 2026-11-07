#!/usr/bin/env python3
"""Reparte la suite unittest en grupos equilibrados por tiempo y ejecuta uno (T-50).

PROYECTO: Diputado de Distrito
VERSIÓN: 1.0.0
NOMBRE DE VERSIÓN: Suite en paralelo
FECHA: 2026-11-07
ESTADO: candidato
CAMBIOS: versión inicial.
MOTIVO: el job `pruebas` tardaba ~13-15 min porque la suite (2.168 tests, ~660 s) corría en un solo proceso.
QUÉ HACE: descubre exactamente lo mismo que `python -m unittest discover -s tests -p 'test_*.py'` (mismo cargador,
  mismo directorio), toma cada fichero descubierto como unidad, lo pesa con `tests/tiempos_ci.json` (los que no
  están pesan la mediana) y reparte las unidades entre N grupos con el algoritmo LPT (la más pesada al grupo menos
  cargado; empates por nombre e índice). El reparto es determinista: todos los grupos calculan la misma partición
  y cada unidad cae en uno solo. Ejecuta el grupo pedido con salida -v y sale 1 si falla algún test o import.
NO HACE: quitar ni filtrar tests; un fallo de import (_FailedTest) se ejecuta como cualquier otra unidad.
ANTERIOR: ninguna (fichero nuevo)

Uso: python herramientas/repartir_tests.py --grupos N --grupo K   (K de 1 a N)
     python herramientas/repartir_tests.py --grupos N --listar      (partición y carga estimada, sin ejecutar)
"""
from __future__ import annotations

import argparse
import json
import os
import statistics
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TIEMPOS = ROOT / "tests" / "tiempos_ci.json"


def repartir(pesos: dict[str, float], grupos: int) -> list[list[str]]:
    """LPT determinista: cada nombre en un único grupo."""
    if grupos < 1:
        raise ValueError("grupos debe ser ≥ 1")
    carga = [0.0] * grupos
    salida: list[list[str]] = [[] for _ in range(grupos)]
    for nombre in sorted(pesos, key=lambda n: (-pesos[n], n)):
        g = min(range(grupos), key=lambda i: (carga[i], i))
        salida[g].append(nombre)
        carga[g] += pesos[nombre]
    return salida


def _primer_id(suite) -> str | None:
    for t in suite:
        if isinstance(t, unittest.TestSuite):
            r = _primer_id(t)
            if r:
                return r
        else:
            return t.id()
    return None


def unidades() -> dict[str, unittest.TestSuite]:
    """Un TestSuite por fichero descubierto, con nombre único (módulo del primer test)."""
    os.chdir(ROOT)
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    suite = unittest.defaultTestLoader.discover(start_dir="tests", pattern="test_*.py")
    salida: dict[str, unittest.TestSuite] = {}
    for i, hijo in enumerate(suite):
        if hijo.countTestCases() == 0:
            continue
        tid = _primer_id(hijo) or f"vacio.{i}"
        nombre = tid.rsplit(".", 2)[0] if tid.count(".") >= 2 else tid
        if nombre in salida or nombre == "unittest.loader":
            nombre = f"{nombre}#{i}" if nombre != "unittest.loader" else f"{tid}#{i}"
        salida[nombre] = hijo
    return salida


def pesos_de(nombres, tiempos: dict[str, float]) -> dict[str, float]:
    conocidos = [v for v in tiempos.values() if v > 0]
    defecto = statistics.median(conocidos) if conocidos else 1.0
    return {n: float(tiempos.get(n.split("#")[0], defecto)) or 0.01 for n in nombres}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--grupos", type=int, required=True)
    ap.add_argument("--grupo", type=int, help="1..N")
    ap.add_argument("--listar", action="store_true")
    ap.add_argument("--tiempos", type=Path, default=TIEMPOS)
    a = ap.parse_args(argv)
    tiempos = json.loads(a.tiempos.read_text(encoding="utf-8")).get("modulos", {}) if a.tiempos.is_file() else {}
    todas = unidades()
    pesos = pesos_de(todas, tiempos)
    particion = repartir(pesos, a.grupos)
    if a.listar:
        print(json.dumps([{"grupo": i + 1, "unidades": len(g), "tests": sum(todas[n].countTestCases() for n in g),
                           "segundos_estimados": round(sum(pesos[n] for n in g), 1)} for i, g in enumerate(particion)],
                         ensure_ascii=False, indent=1))
        return 0
    if not a.grupo or not 1 <= a.grupo <= a.grupos:
        ap.error("--grupo debe estar entre 1 y --grupos")
    mio = particion[a.grupo - 1]
    suite = unittest.TestSuite(todas[n] for n in mio)
    total = sum(s.countTestCases() for s in todas.values())
    print(f"Grupo {a.grupo}/{a.grupos}: {len(mio)} de {len(todas)} ficheros, {suite.countTestCases()} de {total} tests, "
          f"~{round(sum(pesos[n] for n in mio))} s estimados.", flush=True)
    resultado = unittest.TextTestRunner(verbosity=2).run(suite)
    return 0 if resultado.wasSuccessful() else 1


if __name__ == "__main__":
    sys.exit(main())
