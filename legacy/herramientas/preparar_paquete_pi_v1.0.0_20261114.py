#!/usr/bin/env python3
"""Paquete para el registro de propiedad intelectual de Deslinde (instantánea reproducible desde un commit).

PROYECTO: Diputado de Distrito
VERSIÓN: 1.0.0
NOMBRE DE VERSIÓN: Paquete PI de Deslinde 1.0.0
FECHA: 2026-11-14
ESTADO: candidato
CAMBIOS: 1.0.0 — fichero nuevo (T-281).
MOTIVO: D-91 (revisada), D-92 y D-95: el código de Deslinde, su definición formal y los estudios son privados y se
  registran como propiedad intelectual; hace falta una instantánea verificable por hashes, no una copia del repo.
ANTERIOR: ninguna (fichero nuevo)
QUÉ HACE: lee SOLO del objeto git del commit (no del árbol de trabajo) una lista blanca:
  - ddd_motor2/** (el motor Deslinde);
  - los módulos que ddd_motor2 ejecuta (`modulos/0X_*.py` citados literalmente en su código);
  - el cierre de imports `ddd_core` de todo lo anterior (análisis AST, transitivo);
  - docs/ARQUITECTURA/DESLINDE_1_0.md y docs/ESTUDIOS/**.
  Excluye por ruta CLAUDE.md, .claude/, ficheros de secretos (.env, *.pem, *.key, id_rsa…) y cachés; FALLA (código 2)
  si el contenido de un fichero incluido tiene patrones obvios de secreto (tokens, claves privadas) o correos. Las rutas
  /home/ o /Users/ (logs y scripts de estudios) no paran: el paquete es privado y no se debilita el registro quitando
  estudios (decisión del Planificador, T-281); quedan como `avisos` en el manifiesto. `--excluir RUTA` (repetible) quita ficheros a mano y queda en el manifiesto.
  Escribe en la salida (por defecto propiedad_intelectual/): MANIFEST.json (ruta, tamaño y sha256 por fichero, commit,
  fecha UTC del commit, versión de Deslinde, sha256 del ZIP), el ZIP determinista (orden por ruta, fecha fija
  1980-01-01, permisos 0644, sin compresión: idéntico en cualquier máquina), SHA256SUMS y README.md.
  Determinista: dos ejecuciones sobre el mismo commit dan los mismos bytes (la fecha es la del commit, no la de hoy).
Uso: python herramientas/preparar_paquete_pi.py [--commit HEAD] [--salida propiedad_intelectual] [--sin-zip]
     [--excluir RUTA ...] [--raiz RUTA]
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import io
import json
import re
import subprocess
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path

VERSION = "1.0.0"
ROOT = Path(__file__).resolve().parents[1]
NOMBRE_ZIP = "paquete_deslinde.zip"
DOC_DESLINDE = "docs/ARQUITECTURA/DESLINDE_1_0.md"
PREFIJOS_COMPLETOS = ("ddd_motor2/", "docs/ESTUDIOS/")
PAQUETES_SEGUIDOS = ("ddd_core", "ddd_motor2")
FECHA_ZIP = (1980, 1, 1, 0, 0, 0)

# Rutas que nunca entran (se registran como excluidas por política).
RUTAS_PROHIBIDAS = [
    re.compile(r"(^|/)CLAUDE\.md$"),
    re.compile(r"(^|/)\.claude/"),
    re.compile(r"(^|/)\.env(\.|$)"),
    re.compile(r"\.(pem|key|p12|pfx|keystore)$", re.I),
    re.compile(r"(^|/)id_(rsa|dsa|ecdsa|ed25519)(\.pub)?$"),
    re.compile(r"(^|/)(credentials|secrets?)(\.[a-z]+)?$", re.I),
    re.compile(r"(^|/)__pycache__/|\.pyc$"),
]
# Contenido que hace fallar: (nombre, patrón). El nombre va al informe; el texto encontrado, nunca.
PATRONES_SECRETO = [
    ("token_github", re.compile(rb"\b(gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{30,})")),
    ("clave_aws", re.compile(rb"\bAKIA[0-9A-Z]{16}\b")),
    ("clave_privada", re.compile(rb"-----BEGIN [A-Z ]*PRIVATE KEY-----")),
    ("token_slack", re.compile(rb"\bxox[baprs]-[A-Za-z0-9-]{10,}")),
    ("clave_api", re.compile(rb"\bsk-(ant-)?[A-Za-z0-9_-]{20,}")),
    ("correo", re.compile(rb"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,}\b")),
]
# En binarios (PNG, gz) el patrón de correo da falsos positivos con bytes al azar: solo se busca en texto.
SOLO_TEXTO = {"correo"}
# Rutas de máquina: se avisan en el manifiesto, no paran (el paquete PI es privado; sanear solo importa al público).
PATRONES_AVISO = [
    ("ruta_home", re.compile(rb"/home/[A-Za-z0-9_.-]+")),
    ("ruta_users", re.compile(rb"/Users/[A-Za-z0-9_.-]+")),
]
RE_MODULO = re.compile(r"modulos/0\d_[a-z0-9_]+\.py")


class PaqueteError(Exception):
    """Fallo que para el paquete (código 2)."""


def _git(raiz: Path, *args: str) -> bytes:
    return subprocess.run(["git", "-C", str(raiz), *args], check=True, capture_output=True).stdout


class Arbol:
    """Vista de solo lectura de un commit: rutas y contenido de los blobs."""

    def __init__(self, raiz: Path, commit: str):
        self.raiz = raiz
        self.sha = _git(raiz, "rev-parse", "--verify", f"{commit}^{{commit}}").decode().strip()
        salida = _git(raiz, "ls-tree", "-r", "-z", self.sha)
        self.blobs: dict[str, str] = {}
        for linea in salida.split(b"\0"):
            if not linea:
                continue
            meta, ruta = linea.split(b"\t", 1)
            _modo, tipo, obj = meta.decode().split()
            if tipo == "blob":
                self.blobs[ruta.decode("utf-8")] = obj
        self._cache: dict[str, bytes] = {}

    def leer(self, ruta: str) -> bytes:
        if ruta not in self._cache:
            self._cache[ruta] = _git(self.raiz, "cat-file", "blob", self.blobs[ruta])
        return self._cache[ruta]

    def fecha_utc(self) -> str:
        ts = int(_git(self.raiz, "show", "-s", "--format=%ct", self.sha).decode().strip())
        return datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _modulo_a_ruta(arbol: Arbol, modulo: str) -> str | None:
    base = modulo.replace(".", "/")
    for cand in (f"{base}.py", f"{base}/__init__.py"):
        if cand in arbol.blobs:
            return cand
    return None


def _imports(arbol: Arbol, ruta: str) -> tuple[set[str], set[str]]:
    """(rutas de ddd_core/ddd_motor2 importadas, otros paquetes del repo importados)."""
    try:
        tree = ast.parse(arbol.leer(ruta), filename=ruta)
    except SyntaxError:
        return set(), set()
    paquete = ruta.rsplit("/", 1)[0].replace("/", ".") if "/" in ruta else ""
    modulos: set[str] = set()
    for nodo in ast.walk(tree):
        if isinstance(nodo, ast.Import):
            modulos.update(a.name for a in nodo.names)
        elif isinstance(nodo, ast.ImportFrom):
            if nodo.level:
                partes = paquete.split(".")
                base = ".".join(partes[: len(partes) - nodo.level + 1])
                mod = f"{base}.{nodo.module}" if nodo.module else base
            else:
                mod = nodo.module or ""
            modulos.add(mod)
            modulos.update(f"{mod}.{a.name}" for a in nodo.names)
    dentro, fuera = set(), set()
    for mod in modulos:
        top = mod.split(".")[0]
        if top in PAQUETES_SEGUIDOS:
            r = _modulo_a_ruta(arbol, mod)
            if r:
                dentro.add(r)
            ini = _modulo_a_ruta(arbol, top)
            if ini:
                dentro.add(ini)
        elif _modulo_a_ruta(arbol, top):
            fuera.add(top)
    return dentro, fuera


def seleccionar(arbol: Arbol, excluir: list[str]) -> dict:
    if DOC_DESLINDE not in arbol.blobs:
        raise PaqueteError(f"falta {DOC_DESLINDE} en el commit")
    base = {r for r in arbol.blobs if r.startswith(PREFIJOS_COMPLETOS)} | {DOC_DESLINDE}
    for r in sorted(base):
        if r.startswith("ddd_motor2/") and r.endswith(".py"):
            base.update(m for m in RE_MODULO.findall(arbol.leer(r).decode("utf-8", "replace")) if m in arbol.blobs)
    pendientes = sorted(r for r in base if r.endswith(".py") and not r.startswith("docs/"))
    vistos, externos = set(pendientes), set()
    while pendientes:
        dentro, fuera = _imports(arbol, pendientes.pop())
        externos |= fuera
        for r in dentro - vistos:
            vistos.add(r)
            pendientes.append(r)
    candidatos = base | vistos
    politica = sorted(r for r in candidatos if any(p.search(r) for p in RUTAS_PROHIBIDAS))
    manuales = sorted(r for r in candidatos if r in set(excluir))
    desconocidas = sorted(set(excluir) - candidatos)
    if desconocidas:
        raise PaqueteError(f"--excluir no está en la lista blanca: {', '.join(desconocidas)}")
    incluidos = sorted(candidatos - set(politica) - set(manuales))
    return {"incluidos": incluidos, "excluidos_por_politica": politica, "excluidos_explicitos": manuales,
            "paquetes_del_repo_importados_no_incluidos": sorted(externos - set(PAQUETES_SEGUIDOS))}


def detectar_avisos(arbol: Arbol, rutas: list[str]) -> list[dict]:
    return [{"ruta": r, "tipo": nombre} for r in rutas for nombre, patron in PATRONES_AVISO
            if patron.search(arbol.leer(r))]


def detectar_secretos(arbol: Arbol, rutas: list[str]) -> list[tuple[str, str]]:
    hallazgos = []
    for r in rutas:
        datos = arbol.leer(r)
        binario = b"\0" in datos[:8192]
        for nombre, patron in PATRONES_SECRETO:
            if binario and nombre in SOLO_TEXTO:
                continue
            if patron.search(datos):
                hallazgos.append((r, nombre))
    return hallazgos


def version_deslinde(arbol: Arbol) -> str:
    m = re.search(r"(?m)^VERSIÓN:\s*(\S+)", arbol.leer(DOC_DESLINDE).decode("utf-8", "replace"))
    if not m:
        raise PaqueteError(f"{DOC_DESLINDE} no declara VERSIÓN")
    return m.group(1)


def zip_determinista(arbol: Arbol, rutas: list[str]) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_STORED) as z:
        for r in rutas:
            info = zipfile.ZipInfo(r, date_time=FECHA_ZIP)
            info.compress_type = zipfile.ZIP_STORED
            info.external_attr = 0o100644 << 16
            info.create_system = 3
            z.writestr(info, arbol.leer(r))
    return buf.getvalue()


README = """# Paquete de propiedad intelectual de Deslinde

Instantánea del motor Deslinde (versión {version}) tomada del commit `{sha}` ({fecha} UTC), generada por
`herramientas/preparar_paquete_pi.py` {gen}. Contiene {n} ficheros ({bytes} bytes): `ddd_motor2/`, los módulos que
ejecuta, el `ddd_core` que importan, `{doc}` y `docs/ESTUDIOS/`.

Esta carpeta es privada: no entra en el repositorio público (`configuracion/exclusion_publicacion.txt`).
El envío al registro lo hace el propietario con su asesor.

## Verificar

1. `sha256sum -c SHA256SUMS` comprueba el ZIP y el manifiesto (si el ZIP está presente).
2. Cada fichero del ZIP tiene su tamaño y sha256 en `MANIFEST.json` (`ficheros`).
3. Reproducir: `python herramientas/preparar_paquete_pi.py --commit {sha}{excl}` da los mismos bytes
   (ZIP sin compresión, orden por ruta, fecha fija 1980-01-01, permisos 0644).
"""


def generar(raiz: Path, commit: str, salida: Path, excluir: list[str], con_zip: bool = True) -> dict:
    arbol = Arbol(raiz, commit)
    sel = seleccionar(arbol, excluir)
    hallazgos = detectar_secretos(arbol, sel["incluidos"])
    if hallazgos:
        lineas = "\n".join(f"  {r}: {n}" for r, n in hallazgos)
        raise PaqueteError(f"patrones de secreto o correo en {len(hallazgos)} caso(s):\n{lineas}")
    ficheros = [{"ruta": r, "bytes": len(arbol.leer(r)), "sha256": hashlib.sha256(arbol.leer(r)).hexdigest()}
                for r in sel["incluidos"]]
    datos_zip = zip_determinista(arbol, sel["incluidos"])
    manifiesto = {
        "esquema": "ddd.paquete_pi.v1",
        "generador": {"herramienta": "herramientas/preparar_paquete_pi.py", "version": VERSION},
        "commit": arbol.sha,
        "fecha_utc": arbol.fecha_utc(),
        "deslinde_version": version_deslinde(arbol),
        "zip": {"nombre": NOMBRE_ZIP, "bytes": len(datos_zip), "sha256": hashlib.sha256(datos_zip).hexdigest(),
                "formato": "ZIP_STORED, orden por ruta, fecha 1980-01-01T00:00:00, 0644"},
        "total_ficheros": len(ficheros),
        "total_bytes": sum(f["bytes"] for f in ficheros),
        "excluidos_por_politica": sel["excluidos_por_politica"],
        "excluidos_explicitos": sel["excluidos_explicitos"],
        "avisos": detectar_avisos(arbol, sel["incluidos"]),
        "paquetes_del_repo_importados_no_incluidos": sel["paquetes_del_repo_importados_no_incluidos"],
        "ficheros": ficheros,
    }
    salida.mkdir(parents=True, exist_ok=True)
    texto_manifiesto = json.dumps(manifiesto, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    (salida / "MANIFEST.json").write_text(texto_manifiesto, encoding="utf-8")
    sha_man = hashlib.sha256(texto_manifiesto.encode("utf-8")).hexdigest()
    (salida / "SHA256SUMS").write_text(f"{sha_man}  MANIFEST.json\n{manifiesto['zip']['sha256']}  {NOMBRE_ZIP}\n",
                                       encoding="utf-8")
    if con_zip:
        (salida / NOMBRE_ZIP).write_bytes(datos_zip)
    excl = "".join(f" --excluir {r}" for r in sel["excluidos_explicitos"])
    (salida / "README.md").write_text(README.format(
        version=manifiesto["deslinde_version"], sha=arbol.sha, fecha=manifiesto["fecha_utc"], gen=VERSION,
        n=len(ficheros), bytes=manifiesto["total_bytes"], doc=DOC_DESLINDE, excl=excl), encoding="utf-8")
    return manifiesto


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--commit", default="HEAD")
    ap.add_argument("--salida", default="propiedad_intelectual")
    ap.add_argument("--raiz", default=str(ROOT))
    ap.add_argument("--excluir", action="append", default=[], help="ruta de la lista blanca que se deja fuera")
    ap.add_argument("--sin-zip", action="store_true", help="no escribe el ZIP (su sha256 sí va al manifiesto)")
    a = ap.parse_args(argv)
    raiz = Path(a.raiz).resolve()
    salida = Path(a.salida)
    salida = salida if salida.is_absolute() else raiz / salida
    try:
        m = generar(raiz, a.commit, salida, a.excluir, con_zip=not a.sin_zip)
    except PaqueteError as exc:
        print(f"::error::paquete PI: {exc}", file=sys.stderr)
        return 2
    print(f"paquete PI: {m['total_ficheros']} ficheros, {m['total_bytes']} bytes, commit {m['commit'][:12]}, "
          f"Deslinde {m['deslinde_version']}, zip sha256 {m['zip']['sha256']}, avisos {len(m['avisos'])}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
