#!/usr/bin/env python3
"""Hook PreToolUse (Bash) de Claude Code: bloquea operaciones de git peligrosas.

PROYECTO: Diputado de Distrito
VERSIÓN: 1.0.0 · FECHA: 2026-11-07 · ESTADO: candidato
ANTERIOR: ninguna (fichero nuevo)
QUÉ HACE: lee el JSON del hook por stdin y, si el comando Bash es
  - `git push` forzado (--force, -f, --force-with-lease, --force-if-includes o refspec «+rama»), lo bloquea;
  - `git commit`, busca marcas de conflicto en los ficheros preparados (y en los modificados si lleva -a/--all)
    y lo bloquea si las hay.
  Bloquear = salida 2 con el motivo en stderr (Claude Code lo devuelve al modelo). Cualquier otro caso: salida 0.
MOTIVO: plan de agentes, paso 1 (FRAMEWORK_AGENTES_Y_ESTRUCTURA §5 y §12); marcas de conflicto en main (#422)
  y reglas del propietario (sin force push).
"""
from __future__ import annotations

import json
import re
import shlex
import subprocess
import sys

_OPEN = re.compile(r"^<{7}(?: |$)")
_BASE = re.compile(r"^\|{7}(?: |$)")
_SEP = re.compile(r"^={7}$")
_CLOSE = re.compile(r"^>{7}(?: |$)")
_FORCE = {"--force", "-f", "--force-with-lease", "--force-if-includes"}


def marcas(texto: str) -> list[int]:
    lineas, abierto = [], False
    for n, linea in enumerate(texto.splitlines(), start=1):
        linea = linea.rstrip("\r")
        if _OPEN.match(linea):
            abierto = True
            lineas.append(n)
        elif _BASE.match(linea) or _CLOSE.match(linea):
            lineas.append(n)
            abierto = abierto and not _CLOSE.match(linea)
        elif abierto and _SEP.match(linea):
            lineas.append(n)
    return lineas


def _segmentos(comando: str) -> list[list[str]]:
    """Divide el comando en subcomandos (&&, ||, ;, |) y los tokeniza."""
    salida = []
    for trozo in re.split(r"&&|\|\||;|\||\n", comando):
        try:
            tokens = shlex.split(trozo)
        except ValueError:
            tokens = trozo.split()
        if tokens:
            salida.append(tokens)
    return salida


def _subcomando_git(tokens: list[str]) -> tuple[str | None, list[str], str | None]:
    """Devuelve (subcomando, argumentos, directorio de -C) si es una llamada a git."""
    while tokens and re.match(r"^[A-Za-z_][A-Za-z0-9_]*=", tokens[0]):
        tokens = tokens[1:]  # VAR=valor git ...
    if not tokens or tokens[0].rsplit("/", 1)[-1] != "git":
        return None, [], None
    i, cwd = 1, None
    while i < len(tokens) and tokens[i].startswith("-"):
        if tokens[i] in ("-C", "-c") and i + 1 < len(tokens):
            if tokens[i] == "-C":
                cwd = tokens[i + 1]
            i += 2
        else:
            i += 1
    if i >= len(tokens):
        return None, [], cwd
    return tokens[i], tokens[i + 1:], cwd


def push_forzado(args: list[str]) -> bool:
    for arg in args:
        if arg in _FORCE or arg.startswith("--force-with-lease=") or arg.startswith("--force-if-includes="):
            return True
        if re.fullmatch(r"-[a-zA-Z]*f[a-zA-Z]*", arg):  # -fu, -uf…
            return True
        if arg.startswith("+") and len(arg) > 1:  # refspec forzada
            return True
    return False


def _git(cwd: str | None, *args: str) -> str:
    base = ["git"] + (["-C", cwd] if cwd else [])
    res = subprocess.run(base + list(args), capture_output=True, text=True, errors="replace")
    return res.stdout if res.returncode == 0 else ""


def marcas_en_commit(args: list[str], cwd: str | None) -> list[str]:
    todos = any(a == "--all" or re.fullmatch(r"-[a-zA-Z]*a[a-zA-Z]*", a) for a in args)
    ficheros = set(_git(cwd, "diff", "--cached", "--name-only", "--diff-filter=ACMR").splitlines())
    if todos:
        ficheros |= set(_git(cwd, "diff", "--name-only", "--diff-filter=ACMR").splitlines())
    raiz = _git(cwd, "rev-parse", "--show-toplevel").strip()
    hallazgos = []
    for rel in sorted(f for f in ficheros if f):
        if todos:  # se confirmará la copia de trabajo
            try:
                with open(f"{raiz}/{rel}", encoding="utf-8", errors="replace") as fh:
                    texto = fh.read()
            except OSError:
                continue
        else:  # se confirmará lo preparado en el índice
            texto = _git(cwd, "show", f":{rel}")
        if "\0" in texto[:8192]:
            continue
        hallazgos += [f"{rel}:{n}" for n in marcas(texto)]
    return hallazgos


def evaluar(comando: str) -> str | None:
    """Motivo de bloqueo o None."""
    for tokens in _segmentos(comando):
        sub, args, cwd = _subcomando_git(tokens)
        if sub == "push" and push_forzado(args):
            return ("Bloqueado por .claude/hooks/guardia_git.py: push forzado prohibido en este repositorio. "
                    "Tras un rebase, fusiona origin/main o usa git revert (CLAUDE.md).")
        if sub == "commit":
            hallazgos = marcas_en_commit(args, cwd)
            if hallazgos:
                return ("Bloqueado por .claude/hooks/guardia_git.py: marcas de conflicto de Git en "
                        + ", ".join(hallazgos[:10]) + ". Resuelve el conflicto antes de hacer commit.")
    return None


def main() -> int:
    try:
        datos = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return 0
    if datos.get("tool_name") != "Bash":
        return 0
    comando = (datos.get("tool_input") or {}).get("command") or ""
    if "git" not in comando:
        return 0
    motivo = evaluar(comando)
    if motivo:
        print(motivo, file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
