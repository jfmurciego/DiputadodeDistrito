#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Restaura desde R2 el estado M08/M06 de un run cuyo artefacto de Actions ya no existe (T-305).

PROYECTO: Diputado de Distrito
VERSIÓN: 1.1.0
NOMBRE DE VERSIÓN: Restauración del estado final desde R2
FECHA: 2026-11-22
ESTADO: candidato
CAMBIOS: 1.1.0 (T-443, D-188): si la entrada de orchestracion/archivo_r2.json lleva `clave_anterior` (ruta vieja, transición al árbol nuevo), la
  prueba cuando falta el objeto de la clave de la entrada; sha256 distinto sigue fallando cerrado (53). 1.0.0: fichero nuevo (T-305).
MOTIVO: la poda T-278 borró de Actions el ddd-state-<run>-M08 de los runs ya archivados en R2 y la P50 por lotes solo lo buscaba
  allí (LOTE_RECHAZADO «sin producto publicable», run 43617006619).
ANTERIOR: legacy/herramientas/restaurar_estado_r2_v1.0.0_20261122.py
QUÉ HACE: busca en orchestracion/archivo_r2.json el paquete ``ddd-minimo-<run>-<estado>`` (por defecto M08 y luego M06), lo baja de R2
  (aws s3 cp, como fuente_r2.py), verifica su sha256 contra el manifiesto y extrae ``estado/`` en
  ``<destino>/ddd-state-<run>-<estado>/``. Salidas: 0 restaurado; 3 no está en el manifiesto o R2 no disponible/sin credenciales
  (mensaje ::error con run, estado y claves buscadas); 53 sha256 distinto (se borra lo bajado).
USO: python herramientas/restaurar_estado_r2.py <run> <destino> [--estados M08,M06]
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
import zipfile
from pathlib import Path, PurePosixPath

sys.path.insert(0, str(Path(__file__).resolve().parent))
import fuente_r2  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
MANIFIESTO = ROOT / "orchestracion" / "archivo_r2.json"


def buscar(run: str, estado: str, manifiesto: dict) -> tuple[str, dict] | None:
    nombre = f"ddd-minimo-{run}-{estado}"
    for clave, e in manifiesto.get("artefactos", {}).items():
        if str(e.get("run_id")) == str(run) and e.get("artefacto") == nombre:
            return clave, e
    return None


def _extraer(archivo: Path, destino: Path) -> int:
    n = 0
    with zipfile.ZipFile(archivo) as z:
        for m in z.infolist():
            p = PurePosixPath(m.filename)
            if m.is_dir() or p.is_absolute() or ".." in p.parts or not p.parts or p.parts[0] != "estado":
                continue
            dest = destino.joinpath(*p.parts[1:])
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(z.read(m))
            n += 1
    return n


def restaurar(run: str, destino: Path, estados=("M08", "M06"), manifiesto: Path = MANIFIESTO, cp=fuente_r2._cp) -> int:
    man = json.loads(manifiesto.read_text(encoding="utf-8")) if manifiesto.is_file() else {}
    buscadas = []
    for estado in estados:
        hallado = buscar(run, estado, man)
        buscadas.append(f"ddd-minimo-{run}-{estado}" + ("" if hallado else " (no está en orchestracion/archivo_r2.json)"))
        if not hallado:
            continue
        clave, e = hallado
        bucket = os.environ.get("R2_BUCKET")
        if not bucket or not os.environ.get("R2_ACCOUNT_ID"):
            print(f"::error::RESTAURAR_R2_SIN_CREDENCIALES run {run} estado {estado}: falta R2_BUCKET/R2_ACCOUNT_ID; clave {clave}", file=sys.stderr)
            return 3
        with tempfile.TemporaryDirectory() as td:
            zip_ = Path(td) / "paquete.zip"
            try:
                clave = fuente_r2.cp_primera(cp, bucket, fuente_r2.claves({**e, "clave": clave}), str(zip_))
            except Exception as exc:  # noqa: BLE001 - sin objeto o sin red
                print(f"::error::RESTAURAR_R2_NO_DISPONIBLE run {run} estado {estado}: {' ni '.join(fuente_r2.claves({**e, 'clave': clave}))} ({exc})",
                      file=sys.stderr)
                return 3
            real = fuente_r2.sha256(zip_)
            if real != e.get("sha256"):
                print(f"::error::RESTAURAR_R2_SHA256 run {run} estado {estado}: {clave} {real} != {e.get('sha256')}", file=sys.stderr)
                return 53
            n = _extraer(zip_, Path(destino) / f"ddd-state-{run}-{estado}")
        print(f"restaurar_estado_r2: run {run} {estado} desde R2 ({clave}) sha256 verificado, {n} ficheros")
        return 0
    print(f"::error::RESTAURAR_R2_AUSENTE run {run}: sin estado {'/'.join(estados)} en Actions ni en R2; claves buscadas: "
          + "; ".join(buscadas), file=sys.stderr)
    return 3


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("run")
    ap.add_argument("destino")
    ap.add_argument("--estados", default="M08,M06")
    a = ap.parse_args(argv)
    return restaurar(a.run, Path(a.destino), tuple(a.estados.split(",")))


if __name__ == "__main__":
    raise SystemExit(main())
