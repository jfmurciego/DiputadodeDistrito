#!/usr/bin/env python3
"""Hook PreToolUse de Claude Code: allowlist de herramientas por rol, aplicada por configuración.

PROYECTO: Diputado de Distrito
VERSIÓN: 1.0.0 · FECHA: 2026-11-07 · ESTADO: candidato
ANTERIOR: ninguna (fichero nuevo)
QUÉ HACE: lee el JSON del hook por stdin y decide según el rol: `--rol X`; si no, el `agent_type` del subagente que
  llama (revisor y forense → solo-lectura); si no, la variable DDD_ROL del entorno de la sesión.
  - `solo-lectura` (subagentes revisor y forense): bloquea las herramientas que escriben
    (Edit, Write, NotebookEdit, Agent…), las MCP que no son de lectura y los Bash que no estén en la lista de
    lectura (git diff/show/log…, gh api GET, gh pr/run/issue view, cat/grep/jq…); bloquea redirecciones a fichero.
  - `operador` (sesión con DDD_ROL=operador en su entorno): bloquea la edición de ficheros (Edit, Write,
    NotebookEdit). Bash no se restringe: el Operador lanza con `gh api -X POST …/dispatches`.
  - Sin rol: deja pasar (salida 0).
  Bloquear = salida 2 con el motivo en stderr (Claude Code lo devuelve al modelo).
MOTIVO: T-78, gobierno de agentes en runtime: que la autoridad de cada rol no dependa solo de la instrucción.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shlex
import sys

ESCRITURA = {"Edit", "MultiEdit", "Write", "NotebookEdit"}
SOLO_LECTURA_DENEGADAS = ESCRITURA | {"Agent", "Task", "Workflow", "Artifact", "ArtifactData", "SendMessage",
                                      "CronCreate", "CronDelete", "ScheduleWakeup", "PushNotification"}
MCP_LECTURA = re.compile(r"__(get|list|read|search|describe)[a-z_]*$|__(pull_request|issue)_read$")
LECTURA = {"cat", "head", "tail", "grep", "rg", "egrep", "fgrep", "ls", "wc", "sort", "uniq", "cut", "tr", "jq",
           "awk", "sed", "find", "diff", "comm", "column", "echo", "printf", "true", "basename", "dirname",
           "date", "pwd", "file", "stat", "sha256sum", "base64", "zcat", "unzip", "test", "[", "cd", "xargs"}
GIT_LECTURA = {"diff", "show", "log", "status", "fetch", "rev-parse", "ls-files", "ls-tree", "blame", "grep",
               "cat-file", "merge-base", "describe", "shortlog", "branch", "tag", "remote", "config"}
GH_VER = {("pr", "view"), ("pr", "diff"), ("pr", "list"), ("pr", "checks"), ("run", "view"), ("run", "list"),
          ("issue", "view"), ("issue", "list"), ("release", "view"), ("release", "list")}
SUBAGENTES_SOLO_LECTURA = {"revisor", "forense"}
GH_API_ESCRIBE = {"-f", "-F", "--field", "--raw-field", "--input"}


def _segmentos(comando: str) -> list[list[str]]:
    salida = []
    for trozo in re.split(r"&&|\|\||;|\||\n|\$\(|`", comando):
        try:
            tokens = shlex.split(trozo, posix=True)
        except ValueError:
            tokens = trozo.split()
        while tokens and re.match(r"^[A-Za-z_][A-Za-z0-9_]*=", tokens[0]):
            tokens = tokens[1:]
        tokens = [t.rstrip(")") for t in tokens if t.rstrip(")")]
        if tokens:
            salida.append(tokens)
    return salida


def _redireccion_a_fichero(comando: str) -> bool:
    sin_comillas = re.sub(r"'[^']*'|\"[^\"]*\"", "", comando)
    for m in re.finditer(r"(\d?)>>?\s*(&?\S+)", sin_comillas):
        destino = m.group(2)
        if destino not in ("/dev/null", "&1", "&2"):
            return True
    return False


def _gh_api_escribe(args: list[str]) -> bool:
    metodo = None
    for i, a in enumerate(args):
        if a in ("-X", "--method") and i + 1 < len(args):
            metodo = args[i + 1].upper()
        elif a.startswith("--method=") or (a.startswith("-X") and len(a) > 2):
            metodo = a.split("=", 1)[-1].removeprefix("-X").upper()
    if metodo and metodo != "GET":
        return True
    # gh api con -f/-F sin -X GET pasa a POST
    return metodo is None and any(a in GH_API_ESCRIBE or a.startswith(("--field=", "--raw-field=", "--input="))
                                  for a in args)


def bash_solo_lectura(comando: str) -> str | None:
    """Devuelve el motivo del bloqueo, o None si el comando es de lectura."""
    if _redireccion_a_fichero(comando) or re.search(r"\btee\b", comando):
        return "redirección o escritura a fichero"
    for tokens in _segmentos(comando):
        prog = tokens[0].rsplit("/", 1)[-1]
        if prog == "git":
            sub = next((t for t in tokens[1:] if not t.startswith("-")), None)
            if "-C" in tokens:
                i = tokens.index("-C")
                sub = next((t for t in tokens[i + 2:] if not t.startswith("-")), None)
            if sub not in GIT_LECTURA:
                return f"git {sub} no es de lectura"
            if sub in ("branch", "tag", "remote", "config") and len([t for t in tokens if not t.startswith("-")]) > 2:
                return f"git {sub} con argumentos modifica el repositorio"
        elif prog == "gh":
            if len(tokens) > 1 and tokens[1] == "api":
                if _gh_api_escribe(tokens[2:]):
                    return "gh api con método de escritura"
            elif tuple(tokens[1:3]) not in GH_VER:
                return f"gh {' '.join(tokens[1:3])} no es de lectura"
        elif prog == "sed" and any(t == "-i" or re.fullmatch(r"-[a-zA-Z]*i\S*", t) or t.startswith("--in-place")
                                   for t in tokens[1:]):
            return "sed -i edita ficheros"
        elif prog == "find" and any(t in ("-delete", "-exec", "-execdir", "-ok", "-fprint") for t in tokens):
            return "find con acción"
        elif prog == "xargs":
            resto = [t for t in tokens[1:] if not t.startswith("-")]
            if resto and bash_solo_lectura(" ".join(resto)):
                return "xargs con un comando que no es de lectura"
        elif prog == "unzip" and not any(t in ("-l", "-p", "-Z", "-v") for t in tokens[1:]):
            return "unzip solo para listar (-l) o volcar (-p)"
        elif prog not in LECTURA:
            return f"{prog} no está en la lista de lectura"
    return None


def decidir(rol: str | None, entrada: dict) -> str | None:
    herramienta = entrada.get("tool_name", "")
    if rol == "solo-lectura":
        if herramienta in SOLO_LECTURA_DENEGADAS:
            return f"{herramienta} denegada al rol solo-lectura"
        if herramienta.startswith("mcp__") and not MCP_LECTURA.search(herramienta):
            return f"{herramienta} no es una herramienta MCP de lectura"
        if herramienta == "Bash":
            motivo = bash_solo_lectura((entrada.get("tool_input") or {}).get("command", ""))
            return f"Bash denegado al rol solo-lectura: {motivo}" if motivo else None
    elif rol == "operador" and herramienta in ESCRITURA:
        return f"{herramienta} denegada al Operador: no edita código ni el plan"
    return None


def rol_de(entrada: dict, rol_arg: str | None) -> str | None:
    if rol_arg:
        return rol_arg
    if entrada.get("agent_type") in SUBAGENTES_SOLO_LECTURA:
        return "solo-lectura"
    return os.environ.get("DDD_ROL") or None


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--rol", default=None)
    rol_arg = p.parse_args(argv).rol
    try:
        entrada = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return 0
    rol = rol_de(entrada, rol_arg)
    motivo = decidir(rol, entrada)
    if motivo:
        print(f"Bloqueado por rol_herramientas.py: {motivo}.", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
