#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Registro de los robots en la rama de producción con re-derivación y reintento acotado (T-360).

PROYECTO: Diputado de Distrito
VERSIÓN: 1.0.0 · FECHA: 2026-11-16 · ESTADO: candidato
CAMBIOS: 1.0.0 (T-360): fichero nuevo.
MOTIVO: las cadenas de la r4 se serializaban en los grupos únicos `ddd-catalog-promotion` y
  `ddd-shared-operational-state` y los registros hechos con `git pull --rebase` chocaban en ficheros compartidos
  (catalogo_preparacion.yaml, archivo_r2.json, MANIFEST); el catálogo de procedencia iba un commit por detrás.
ANTERIOR: ninguna (fichero nuevo)
QUÉ HACE: toma el cambio que el paso ya dejó en el árbol bajo ``--ruta`` y lo registra en ``--rama`` sin rebase textual:
  en cada intento descarta el árbol, parte del HEAD remoto vigente y re-aplica el cambio:
  - JSON (objetos): se re-aplica el DELTA por claves (lo añadido, cambiado o quitado por este run frente a HEAD), así
    las entradas que otros robots añadieron mientras tanto se conservan;
  - el resto de ficheros: se restaura el contenido de este run (ficheros propios del run: CSV, manifiestos);
  - ``--aplicar CMD`` (opcional): orden que re-deriva el cambio desde el HEAD vigente (p. ej. la promoción del catálogo
    YAML); se ejecuta en cada intento, NO antes.
  Después regenera ``orchestracion/catalogo_procedencia.json`` (si existe) en el MISMO commit y empuja. Un push rechazado
  repite con espera exponencial y jitter (2, 4, 8… s, tope 30) hasta ``--max-intentos`` (10); agotados, sale con 75 y
  ``::error title=PUSH_RECHAZADO_TRAS_N::``. Sin cambio que registrar, sale con 0 (NO_OP).
NO HACE: resolver conflictos de valores (en una misma clave gana este run) ni reintentar errores que no sean de push.
Uso: python -m herramientas.registrar_en_main --rama main --mensaje "chore: …" --ruta R [--ruta R…] [--aplicar CMD]
"""
from __future__ import annotations

import argparse
import json
import random
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterable

CATALOGO_PROCEDENCIA = "orchestracion/catalogo_procedencia.json"
MAX_INTENTOS = 10
SALIDA_AGOTADO = 75
_BORRAR = object()


class PushRechazado(RuntimeError):
    """El remoto rechazó el push en todos los intentos (código PUSH_RECHAZADO_TRAS_N)."""

    def __init__(self, intentos: int, detalle: str):
        self.codigo = f"PUSH_RECHAZADO_TRAS_{intentos}"
        super().__init__(f"{self.codigo}: {detalle}")


@dataclass(frozen=True)
class Resultado:
    estado: str  # REGISTRADO | NO_OP
    head_sha: str
    intento: int


def espera(intento: int) -> float:
    """Espera exponencial con jitter (2, 4, 8… s, tope 30), la misma que el estado operativo compartido."""
    return min(2.0 ** intento, 30.0) * random.uniform(0.5, 1.0)


def _git(root: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["git", *args], cwd=root, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                          check=check)


# --- catálogo de procedencia -------------------------------------------------------------------------

def regenerar_catalogo_procedencia(root: Path) -> bool:
    """Regenera el catálogo de procedencia si está versionado en ``root``; True si cambió.

    Un fallo al regenerar avisa (::warning::) y no bloquea el registro: el job ``catalogo`` de la CI lo repone.
    """
    destino = Path(root) / CATALOGO_PROCEDENCIA
    if not destino.is_file():
        return False
    try:
        from herramientas import catalogo_procedencia as cp
        texto = cp.serializar(cp.generar(Path(root)))
    except Exception as exc:  # noqa: BLE001 - aviso, no bloqueo
        print(f"::warning title=CATALOGO_PROCEDENCIA_NO_REGENERADO::{type(exc).__name__}: {exc}", file=sys.stderr)
        return False
    if destino.read_text(encoding="utf-8") == texto:
        return False
    destino.write_text(texto, encoding="utf-8")
    return True


def anadir_catalogo_procedencia(root: Path) -> None:
    """Regenera el catálogo y lo añade al índice (para los persistidores que re-derivan desde el HEAD)."""
    if regenerar_catalogo_procedencia(root):
        _git(Path(root), "add", CATALOGO_PROCEDENCIA)


# --- delta JSON --------------------------------------------------------------------------------------

def delta_json(base, nuevo, prefijo: tuple = ()) -> list[tuple[tuple, object]]:
    """Operaciones (ruta de claves, valor | _BORRAR) que llevan ``base`` a ``nuevo`` por claves de objeto."""
    if not (isinstance(base, dict) and isinstance(nuevo, dict)):
        return [] if base == nuevo else [(prefijo, nuevo)]
    ops: list[tuple[tuple, object]] = []
    for k, v in nuevo.items():
        if k not in base:
            ops.append((prefijo + (k,), v))
        else:
            ops.extend(delta_json(base[k], v, prefijo + (k,)))
    ops.extend((prefijo + (k,), _BORRAR) for k in base if k not in nuevo)
    return ops


def aplicar_delta(doc, ops: Iterable[tuple[tuple, object]]):
    for ruta, valor in ops:
        if not ruta:
            doc = valor
            continue
        nodo = doc if isinstance(doc, dict) else {}
        doc = nodo
        for k in ruta[:-1]:
            if not isinstance(nodo.get(k), dict):
                nodo[k] = {}
            nodo = nodo[k]
        if valor is _BORRAR:
            nodo.pop(ruta[-1], None)
        else:
            nodo[ruta[-1]] = valor
    return doc


def _volcar_json(doc, previo: str | None) -> str:
    for indent in (1, 2):
        if previo is not None:
            try:
                if json.dumps(json.loads(previo), ensure_ascii=False, indent=indent) + "\n" == previo:
                    return json.dumps(doc, ensure_ascii=False, indent=indent) + "\n"
            except ValueError:
                break
    return json.dumps(doc, ensure_ascii=False, indent=1) + "\n"


# --- captura y re-aplicación -------------------------------------------------------------------------

def _cambiados(root: Path, rutas: list[str]) -> list[str]:
    out = _git(root, "status", "--porcelain=v1", "-z", "--untracked-files=all", "--no-renames", "--", *rutas).stdout
    return sorted({e[3:] for e in out.split("\0") if len(e) > 3})


def capturar(root: Path, rutas: list[str]) -> list[tuple[str, str, object]]:
    """El cambio del run frente a HEAD: (ruta, 'json'|'bytes'|'borrar', carga)."""
    cambio = []
    for rel in _cambiados(root, rutas):
        p = root / rel
        if not p.exists():
            cambio.append((rel, "borrar", None))
            continue
        if p.suffix == ".json":
            try:
                nuevo = json.loads(p.read_text(encoding="utf-8"))
                previo = _git(root, "show", f"HEAD:{rel}", check=False)
                base = json.loads(previo.stdout) if previo.returncode == 0 else {}
                cambio.append((rel, "json", delta_json(base, nuevo)))
                continue
            except ValueError:
                pass
        cambio.append((rel, "bytes", p.read_bytes()))
    return cambio


def reaplicar(root: Path, cambio: list[tuple[str, str, object]]) -> None:
    for rel, tipo, carga in cambio:
        p = root / rel
        if tipo == "borrar":
            p.unlink(missing_ok=True)
        elif tipo == "bytes":
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes(carga)
        else:
            previo = p.read_text(encoding="utf-8") if p.is_file() else None
            doc = json.loads(previo) if previo is not None else {}
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(_volcar_json(aplicar_delta(doc, carga), previo), encoding="utf-8")


def registrar(*, root_dir: Path, rama: str, mensaje: str, rutas: list[str],
              aplicar: str | Callable[[Path], None] | None = None, max_intentos: int = MAX_INTENTOS,
              backoff: Callable[[int], float] | None = espera, antes_de_push: Callable[[int], None] | None = None,
              catalogo: bool = True) -> Resultado:
    root = Path(root_dir).resolve()
    if not rutas:
        raise ValueError("hace falta al menos una --ruta")
    if max_intentos < 1:
        raise ValueError("max_intentos debe ser >= 1")
    _git(root, "config", "user.name", "github-actions")
    _git(root, "config", "user.email", "github-actions@github.com")
    cambio = capturar(root, rutas)
    ultimo = ""
    for intento in range(1, max_intentos + 1):
        _git(root, "fetch", "--quiet", "origin", rama)
        _git(root, "reset", "--quiet", "--hard", "FETCH_HEAD")
        reaplicar(root, cambio)
        if aplicar is not None:
            if callable(aplicar):
                aplicar(root)
            else:
                subprocess.run(["bash", "-eo", "pipefail", "-c", aplicar], cwd=root, check=True)
        presentes = [r for r in rutas if (root / r).exists()
                     or _git(root, "ls-files", "--error-unmatch", "--", r, check=False).returncode == 0]
        if presentes:
            _git(root, "add", "-A", "--", *presentes)
        if _git(root, "diff", "--cached", "--quiet", check=False).returncode == 0:
            return Resultado("NO_OP", _git(root, "rev-parse", "HEAD").stdout.strip(), intento)
        if catalogo:
            anadir_catalogo_procedencia(root)
        _git(root, "commit", "--quiet", "-m", mensaje)
        if antes_de_push is not None:
            antes_de_push(intento)
        empuje = _git(root, "push", "origin", f"HEAD:refs/heads/{rama}", check=False)
        if empuje.returncode == 0:
            return Resultado("REGISTRADO", _git(root, "rev-parse", "HEAD").stdout.strip(), intento)
        ultimo = (empuje.stderr.strip().splitlines() or [""])[-1]
        if intento < max_intentos and backoff is not None:
            time.sleep(backoff(intento))
    raise PushRechazado(max_intentos, f"el remoto rechazó el registro en {rama} ({mensaje}): {ultimo}")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--root-dir", type=Path, default=Path("."))
    ap.add_argument("--rama", default="main")
    ap.add_argument("--mensaje", required=True)
    ap.add_argument("--ruta", action="append", required=True, dest="rutas")
    ap.add_argument("--aplicar")
    ap.add_argument("--max-intentos", type=int, default=MAX_INTENTOS)
    ap.add_argument("--sin-catalogo", action="store_true")
    a = ap.parse_args(argv)
    try:
        r = registrar(root_dir=a.root_dir, rama=a.rama, mensaje=a.mensaje, rutas=a.rutas, aplicar=a.aplicar,
                      max_intentos=a.max_intentos, catalogo=not a.sin_catalogo)
    except PushRechazado as exc:
        print(f"::error title={exc.codigo}::{exc}", file=sys.stderr)
        return SALIDA_AGOTADO
    print(json.dumps({"estado": r.estado, "head_sha": r.head_sha, "intento": r.intento}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
