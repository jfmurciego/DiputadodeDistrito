#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""T-254 · Código muerto del motor (solo lectura; no cambia nada).

PROYECTO: Diputado de Distrito
VERSIÓN: 1.0.0
FECHA: 2026-11-11
ANTERIOR: ninguna (fichero nuevo)
QUÉ HACE: (1) cierre de imports desde los puntos de entrada de producción (modulos/0*.py, ddd_motor2/produccion.py,
  ddd_motor2/competir.py, herramientas/*.py citadas en .github/workflows) y, para cada módulo de ddd_core/ y ddd_motor2/,
  quién lo importa por categoría (producción, herramientas, tests, legacy); (2) para cada función/clase de nivel
  superior de esos paquetes y de modulos/04*, 05*, si su nombre aparece fuera de su propio fichero, por categoría.
USO: python3 docs/ESTUDIOS/T254_MEDICION_DESLINDE/codigo_muerto.py > codigo_muerto.json
"""
from __future__ import annotations

import ast
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
PAQ = ("ddd_core", "ddd_motor2", "ddd_ensemble")
INFORMA = ("ddd_core", "ddd_motor2")


def categoria(p: Path) -> str:
    r = p.relative_to(ROOT).as_posix()
    if r.startswith("legacy/"):
        return "legacy"
    if r.startswith("tests/"):
        return "tests"
    if r.startswith(("modulos/", "ddd_core/", "ddd_motor2/", ".github/")):
        return "produccion"
    if r.startswith("herramientas/"):
        return "herramientas"
    return "otros"


def modulo_de(p: Path) -> str | None:
    r = p.relative_to(ROOT)
    if r.parts[0] in PAQ:
        return ".".join(r.with_suffix("").parts).removesuffix(".__init__")
    return None


def imports(p: Path) -> set[str]:
    try:
        arbol = ast.parse(p.read_text(encoding="utf-8"))
    except (SyntaxError, UnicodeDecodeError):
        return set()
    base = modulo_de(p)
    out = set()
    for n in ast.walk(arbol):
        if isinstance(n, ast.Import):
            out |= {a.name for a in n.names}
        elif isinstance(n, ast.ImportFrom):
            m = n.module or ""
            if n.level and base:
                pk = base.split(".")[: -n.level] if not p.name == "__init__.py" else base.split(".")[: len(base.split(".")) - n.level + 1]
                m = ".".join(pk + ([m] if m else []))
            out.add(m)
            out |= {f"{m}.{a.name}" for a in n.names}
    # imports por ruta o importlib con literal (p. ej. «ddd_core/m04_seed_engine_v7411.py» o importlib.import_module("ddd_core.x"))
    txt = p.read_text(encoding="utf-8", errors="ignore")
    out |= {x.replace("/", ".") for x in re.findall(r"((?:ddd_core|ddd_motor2)[./][A-Za-z0-9_./]+?)(?:\.py)?[\"']", txt)}
    out |= {f"{a}.{b}" for a, b in re.findall(r"[\"'](ddd_core|ddd_motor2)[\"']\s*/\s*[\"']([A-Za-z0-9_]+)\.py[\"']", txt)}
    return {x for x in out if x.split(".")[0] in PAQ}


def main() -> int:
    pys = [p for p in ROOT.rglob("*.py") if ".git" not in p.parts and "bateria" not in p.relative_to(ROOT).parts[:1]
           and ".cache" not in p.parts]
    mods = {modulo_de(p): p for p in pys if modulo_de(p)}
    deps = {p: {m for m in imports(p) if m in mods} | {m.rsplit(".", 1)[0] for m in imports(p) if m.rsplit(".", 1)[0] in mods}
            for p in pys}
    # puntos de entrada de producción
    wf = "\n".join(f.read_text(encoding="utf-8") for f in [*(ROOT / ".github" / "workflows").glob("*.y*ml"),
                                                            *ROOT.glob("*.sh")])
    entradas = [p for p in pys if p.relative_to(ROOT).as_posix().startswith("modulos/")]
    entradas += [ROOT / "ddd_motor2" / "produccion.py", ROOT / "ddd_motor2" / "competir.py"]
    entradas += [p for p in pys if p.relative_to(ROOT).parts[0] == "ddd_ensemble"]  # paquete de la 07 (alternativas)
    citadas = set(re.findall(r"herramientas/([A-Za-z0-9_]+\.py)", wf))
    entradas += [ROOT / "herramientas" / c for c in citadas if (ROOT / "herramientas" / c).is_file()]
    for a_, b_ in re.findall(r"(ddd_core|ddd_motor2|ddd_ensemble)/([A-Za-z0-9_]+)\.py", wf):
        if (ROOT / a_ / f"{b_}.py").is_file():
            entradas.append(ROOT / a_ / f"{b_}.py")
    for m in re.findall(r"python3? -m ((?:ddd_core|ddd_motor2|herramientas)\.[A-Za-z0-9_.]+)", wf):
        f = ROOT / (m.replace(".", "/") + ".py")
        if f.is_file():
            entradas.append(f)
    # herramientas importadas por las citadas (cierre sobre todo el repo, no solo paquetes)
    alcanzados, pila = set(), list(entradas)
    vistos = set()
    while pila:
        p = pila.pop()
        if p in vistos:
            continue
        vistos.add(p)
        txt = p.read_text(encoding="utf-8", errors="ignore")
        for h in re.findall(r"(?:from herramientas(?:\.| import )|herramientas/)([A-Za-z0-9_]+)", txt):
            f = ROOT / "herramientas" / f"{h}.py"
            if f.is_file():
                pila.append(f)
        for m in deps.get(p, ()):
            alcanzados.add(m)
            pila.append(mods[m])
    importadores = defaultdict(lambda: defaultdict(set))
    for p, ms in deps.items():
        for m in ms:
            if mods[m] != p:
                importadores[m][categoria(p)].add(p.relative_to(ROOT).as_posix())
    modulos = []
    for m, p in sorted(mods.items()):
        if not m.startswith(INFORMA):
            continue
        cat = {k: len(v) for k, v in importadores[m].items()}
        estado = ("vivo (producción)" if m in alcanzados else
                  "solo herramientas" if cat.get("herramientas") else
                  "solo tests" if cat.get("tests") else
                  "solo legacy" if cat.get("legacy") else "sin referencias")
        modulos.append({"modulo": m, "lineas": len(p.read_text(encoding="utf-8").splitlines()), "estado": estado,
                        "importadores": cat})
    # símbolos de nivel superior
    textos = {p: p.read_text(encoding="utf-8", errors="ignore") for p in pys}
    wf_txt = {f: f.read_text(encoding="utf-8") for f in (ROOT / ".github" / "workflows").glob("*.y*ml")}
    objetivo = [p for p in pys if (modulo_de(p) or "").startswith(INFORMA)] + [p for p in pys if re.match(r"modulos/0[45]_", p.relative_to(ROOT).as_posix())]
    simbolos = []
    for p in objetivo:
        if p.name == "__init__.py":
            continue
        arbol = ast.parse(textos[p])
        for n in arbol.body:
            if not isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) or n.name.startswith("__"):
                continue
            pat = re.compile(rf"\b{re.escape(n.name)}\b")
            propio = len(pat.findall(textos[p])) - 1
            fuera = defaultdict(int)
            for q, t in textos.items():
                if q != p and pat.search(t):
                    fuera[categoria(q)] += 1
            if any(pat.search(t) for t in wf_txt.values()):
                fuera["produccion"] += 1
            if propio == 0 and not fuera:
                estado = "muerto"
            elif propio == 0 and not fuera.get("produccion") and not fuera.get("herramientas"):
                estado = "solo " + "/".join(sorted(fuera))
            else:
                continue
            simbolos.append({"fichero": p.relative_to(ROOT).as_posix(), "linea": n.lineno, "simbolo": n.name,
                             "lineas": (n.end_lineno or n.lineno) - n.lineno + 1, "estado": estado,
                             "fuera": dict(fuera), "modulo_vivo": modulo_de(p) in alcanzados})
    json.dump({"modulos": modulos, "simbolos": simbolos,
               "entradas": sorted({p.relative_to(ROOT).as_posix() for p in entradas})},
              sys.stdout, indent=1, ensure_ascii=False)
    return 0


if __name__ == "__main__":
    sys.exit(main())
