#!/usr/bin/env python3
"""Evaluador determinista del conjunto de oro de agentes (T-38).

PROYECTO: Diputado de Distrito
VERSIÓN: 1.0.0
NOMBRE DE VERSIÓN: Conjunto de oro para revisor y forense
FECHA: 2026-11-07
ESTADO: candidato
CAMBIOS: versión inicial.
MOTIVO: §8 del framework de agentes: un agente no se da por listo hasta cazar los defectos históricos.
QUÉ HACE: valida los casos de `evals/oro/casos/*.json`, prepara la entrada de cada caso sin la respuesta
  (`--preparar`), puntúa la salida JSON de un agente (revisor, forense o calibración) contra lo esperado y, con
  `--anotar`, añade una fila a `evals/oro/LIBRO_DE_COSTES.md`.
NO HACE: llamar a modelos, descargar artefactos ni leer la red. Solo biblioteca estándar.
ANTERIOR: ninguna (fichero nuevo)

Uso:
  python herramientas/evaluar_oro.py --validar
  python herramientas/evaluar_oro.py --esperadas > salidas_ideales.json
  python herramientas/evaluar_oro.py --preparar DIR [--agente revisor]   # una entrada por caso, sin respuesta
  python herramientas/evaluar_oro.py --salidas salidas.json [--agente revisor] [--umbral 0.8]
                                     [--anotar --modelo sonnet --etiqueta "T-39 v1"] [--json]
"""
from __future__ import annotations

import argparse
import datetime as _dt
import json
import re
import sys
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CASOS_DIR = ROOT / "evals" / "oro" / "casos"
LIBRO = ROOT / "evals" / "oro" / "LIBRO_DE_COSTES.md"
ESQUEMA = "ddd.oro/1.0"

TIPOS = {"revision": "revisor", "forense": "forense", "calibracion": "cualquiera"}
MODOS = {"revision": {"diff_original", "revertir_arreglo"}, "forense": {"sintoma_run"}, "calibracion": {"escenario"}}
VEREDICTOS_REVISION = {"BLOQUEAR", "APROBAR"}
# Veredictos de la skill revisar-pr: FAIL/BLOCKED bloquean; PASS/PASS_WITH_EXCEPTIONS dejan fusionar.
EQUIVALENTES = {"FAIL": "BLOQUEAR", "BLOCKED": "BLOQUEAR", "PASS": "APROBAR", "PASS_WITH_EXCEPTIONS": "APROBAR"}
SHA_RE = re.compile(r"^[0-9a-f]{40}$")
ID_RE = re.compile(r"^(CR|ADV|REV|CTRL|CAL)-\d{2}$")


# --------------------------------------------------------------------------- utilidades
def normalizar(texto) -> str:
    """Minúsculas, sin tildes y con espacios simples: la comparación no depende de la redacción."""
    if texto is None:
        return ""
    if not isinstance(texto, str):
        texto = json.dumps(texto, ensure_ascii=False)
    t = unicodedata.normalize("NFKD", texto)
    t = "".join(ch for ch in t if not unicodedata.combining(ch))
    return re.sub(r"\s+", " ", t.casefold()).strip()


def contar_claves(texto: str, claves) -> int:
    t = normalizar(texto)
    return sum(1 for k in claves if normalizar(k) and normalizar(k) in t)


def cargar_casos(directorio: Path = CASOS_DIR) -> list[dict]:
    casos = []
    for f in sorted(directorio.glob("*.json")):
        caso = json.loads(f.read_text(encoding="utf-8"))
        caso["_fichero"] = f.name
        casos.append(caso)
    return casos


# --------------------------------------------------------------------------- validación de casos
def validar_caso(c: dict) -> list[str]:
    e = []
    cid = c.get("id", "?")
    req = ["id", "tipo", "agente", "titulo", "causa", "origen", "entrada", "esperado", "procedencia"]
    for k in req:
        if k not in c:
            e.append(f"{cid}: falta {k}")
    if e:
        return e
    if not ID_RE.match(cid):
        e.append(f"{cid}: id mal formado")
    if c.get("_fichero") and c["_fichero"] != f"{cid}.json":
        e.append(f"{cid}: el fichero debe llamarse {cid}.json")
    tipo = c["tipo"]
    if tipo not in TIPOS:
        return e + [f"{cid}: tipo desconocido {tipo}"]
    if c["agente"] != TIPOS[tipo]:
        e.append(f"{cid}: agente {c['agente']} no corresponde a {tipo}")
    if not str(c["causa"]).strip() or "\n" in c["causa"]:
        e.append(f"{cid}: la causa es una línea no vacía")
    o = c["origen"]
    prs, runs = o.get("prs", []), o.get("runs", [])
    if not prs and not runs:
        e.append(f"{cid}: sin fuente verificable (PR o run)")
    if not all(isinstance(p, int) and p > 0 for p in prs):
        e.append(f"{cid}: PR mal formada")
    if not all(isinstance(r, int) and r > 10 ** 9 for r in runs):
        e.append(f"{cid}: run mal formado")
    if not o.get("referencia"):
        e.append(f"{cid}: falta origen.referencia")
    p = c["procedencia"]
    for k in ("fuente", "verificado", "fecha"):
        if not p.get(k):
            e.append(f"{cid}: falta procedencia.{k}")
    ent, esp = c["entrada"], c["esperado"]
    if ent.get("modo") not in MODOS[tipo]:
        e.append(f"{cid}: modo {ent.get('modo')} no válido para {tipo}")
    if tipo == "revision":
        for k in ("sha_desde", "sha_candidato"):
            if not SHA_RE.match(str(ent.get(k, ""))):
                e.append(f"{cid}: entrada.{k} no es un SHA de 40")
        if not ent.get("ficheros") or not str(ent.get("comando", "")).startswith("git diff "):
            e.append(f"{cid}: entrada sin ficheros o sin comando git diff")
        if esp.get("veredicto") not in VEREDICTOS_REVISION:
            e.append(f"{cid}: veredicto esperado inválido")
        if esp.get("veredicto") == "BLOQUEAR" and not (esp.get("clases") and esp.get("ficheros") and esp.get("claves")):
            e.append(f"{cid}: un BLOQUEAR necesita clases, ficheros y claves")
    elif tipo == "forense":
        if not ent.get("sintoma"):
            e.append(f"{cid}: falta entrada.sintoma")
        if not esp.get("causa_id") or not esp.get("claves"):
            e.append(f"{cid}: falta causa_id o claves")
        if not 1 <= int(esp.get("min_claves", 0)) <= len(esp.get("claves", [])):
            e.append(f"{cid}: min_claves fuera de rango")
        if int(esp.get("max_lineas", 0)) != 5:
            e.append(f"{cid}: max_lineas debe ser 5")
    else:
        if not ent.get("escenario"):
            e.append(f"{cid}: falta entrada.escenario")
        ac, pr = set(esp.get("veredictos_aceptados", [])), set(esp.get("veredictos_prohibidos", []))
        if not ac or not pr or ac & pr:
            e.append(f"{cid}: veredictos aceptados/prohibidos vacíos o solapados")
        if not 1 <= int(esp.get("min_claves", 0)) <= len(esp.get("claves", [])):
            e.append(f"{cid}: min_claves fuera de rango")
    return e


def validar(casos: list[dict]) -> list[str]:
    errores = []
    vistos = set()
    for c in casos:
        errores += validar_caso(c)
        if c.get("id") in vistos:
            errores.append(f"{c.get('id')}: id duplicado")
        vistos.add(c.get("id"))
    return errores


# --------------------------------------------------------------------------- salidas ideales
def salida_ideal(c: dict) -> dict:
    esp, ent = c["esperado"], c["entrada"]
    if c["tipo"] == "revision":
        s = {"caso": c["id"], "sha": ent["sha_candidato"], "veredicto": esp["veredicto"], "defectos": []}
        if esp["veredicto"] == "BLOQUEAR":
            s["defectos"].append({"clase": esp["clases"][0], "fichero": esp["ficheros"][0],
                                  "detalle": c["causa"] + " " + " ".join(esp["claves"])})
        return s
    if c["tipo"] == "forense":
        return {"caso": c["id"], "causa_id": esp["causa_id"],
                "lineas": [c["causa"], "Claves: " + ", ".join(esp["claves"])]}
    s = {"caso": c["id"], "veredicto": esp["veredictos_aceptados"][0],
         "evidencia": c["causa"] + " " + " ".join(esp["claves"])}
    if "acciones_permitidas" in esp:
        s["acciones"] = list(esp["acciones_permitidas"])
    return s


# --------------------------------------------------------------------------- entradas sin respuesta
_CABECERA_RE = re.compile(r"^-\s*(#|//|\"\"\"|\*)?\s*(VERSIÓN|NOMBRE DE VERSIÓN|FECHA|ESTADO|CAMBIOS?\b|MOTIVO|ANTERIOR)")
_COMENTARIO_RE = re.compile(r"^-\s*(#|//)")


def ocultar_explicacion_del_arreglo(diff: str) -> str:
    """En `revertir_arreglo` el diff quita la cabecera y los comentarios del arreglo, que lo explican: se omiten."""
    return "\n".join(ln for ln in diff.splitlines()
                     if not (_CABECERA_RE.match(ln) or _COMENTARIO_RE.match(ln))) + "\n"


def entrada_agente(c: dict, raiz: Path = ROOT) -> str:
    """Texto que recibe el agente: nunca lleva titulo, causa, esperado, origen ni contexto (darían la respuesta)."""
    ent = c["entrada"]
    if c["tipo"] == "revision":
        import subprocess
        diff = subprocess.run(ent["comando"], shell=True, cwd=raiz, capture_output=True, text=True)
        if diff.returncode != 0 or not diff.stdout.strip():
            raise RuntimeError(f"{c['id']}: no se pudo generar el diff ({diff.stderr.strip()[:200]}); "
                               f"git fetch --depth=2 origin {ent['sha_desde']} {ent['sha_candidato']}")
        texto = diff.stdout
        if ent["modo"] == "revertir_arreglo":
            texto = ocultar_explicacion_del_arreglo(texto)
        return (f"# Caso {c['id']} · revisión\n\nCandidato (HEAD): `{ent['sha_candidato']}`\n"
                f"Ficheros: {', '.join(ent['ficheros'])}\nCI: no aplica en modo oro (juzga solo el diff).\n\n"
                f"```diff\n{texto}```\n")
    if c["tipo"] == "forense":
        runs = ", ".join(str(r) for r in ent.get("runs", [])) or "sin run (CI o main)"
        terr = ent.get("territorio", "—")
        return f"# Caso {c['id']} · diagnóstico\n\nTerritorio: {terr}\nRuns: {runs}\nSíntoma: {ent['sintoma']}\n"
    datos = {k: v for k, v in ent.items() if k not in ("modo", "escenario")}
    return (f"# Caso {c['id']} · calibración\n\n{ent['escenario']}\n\nDatos: "
            f"{json.dumps(datos, ensure_ascii=False)}\n")


def preparar(casos: list[dict], destino: Path, raiz: Path = ROOT) -> list[Path]:
    destino.mkdir(parents=True, exist_ok=True)
    escritos = []
    for c in casos:
        f = destino / f"{c['id']}.md"
        f.write_text(entrada_agente(c, raiz), encoding="utf-8")
        escritos.append(f)
    return escritos


# --------------------------------------------------------------------------- puntuación
def _lineas(s: dict) -> list[str]:
    v = s.get("lineas")
    if isinstance(v, list):
        return [str(x) for x in v if str(x).strip()]
    texto = s.get("diagnostico") or s.get("causa") or ""
    return [ln for ln in str(texto).splitlines() if ln.strip()]


def puntuar_caso(c: dict, s: dict | None) -> dict:
    """Devuelve {'caso', 'acierto': bool, 'motivo': str}. Determinista."""
    r = {"caso": c["id"], "tipo": c["tipo"], "acierto": False, "motivo": ""}
    if not isinstance(s, dict) or not s:
        r["motivo"] = "sin_salida"
        return r
    esp = c["esperado"]
    if c["tipo"] == "revision":
        sha = str(s.get("sha", "")).strip().lower()
        cand = c["entrada"]["sha_candidato"]
        if len(sha) < 7 or not cand.startswith(sha):
            r["motivo"] = "sha_distinto"
            return r
        ver = str(s.get("veredicto", "")).strip().upper()
        ver = EQUIVALENTES.get(ver, ver)
        if ver != esp["veredicto"]:
            r["motivo"] = f"veredicto {ver or '∅'} != {esp['veredicto']}"
            return r
        if ver == "APROBAR":
            r.update(acierto=True, motivo="ok")
            return r
        clases = {normalizar(x) for x in esp["clases"]}
        ficheros = set(esp["ficheros"])
        for d in s.get("defectos") or []:
            if not isinstance(d, dict):
                continue
            if normalizar(d.get("clase")) in clases:
                r.update(acierto=True, motivo="ok_clase")
                return r
            if d.get("fichero") in ficheros and contar_claves(d.get("detalle", ""), esp["claves"]) >= 1:
                r.update(acierto=True, motivo="ok_fichero_y_clave")
                return r
        r["motivo"] = "defecto_no_cazado"
        return r
    if c["tipo"] == "forense":
        lineas = _lineas(s)
        if not lineas and not s.get("causa_id"):
            r["motivo"] = "sin_diagnostico"
            return r
        if len(lineas) > int(esp.get("max_lineas", 5)):
            r["motivo"] = f"excede_lineas ({len(lineas)})"
            return r
        if normalizar(s.get("causa_id")) == normalizar(esp["causa_id"]):
            r.update(acierto=True, motivo="ok_causa_id")
            return r
        n = contar_claves(" ".join(lineas), esp["claves"])
        if n >= int(esp["min_claves"]):
            r.update(acierto=True, motivo=f"ok_claves ({n})")
            return r
        r["motivo"] = f"causa_no_identificada ({n}/{esp['min_claves']} claves)"
        return r
    # calibración
    ver = str(s.get("veredicto", "")).strip().upper()
    if ver in {v.upper() for v in esp["veredictos_prohibidos"]}:
        r["motivo"] = f"veredicto_prohibido {ver}"
        return r
    if ver not in {v.upper() for v in esp["veredictos_aceptados"]}:
        r["motivo"] = f"veredicto {ver or '∅'} no aceptado"
        return r
    if "acciones_permitidas" in esp:
        sobrantes = [a for a in (s.get("acciones") or []) if a not in esp["acciones_permitidas"]]
        if sobrantes:
            r["motivo"] = f"acciones_no_permitidas {sobrantes}"
            return r
    texto = " ".join(str(s.get(k, "")) for k in ("evidencia", "siguiente", "detalle", "lineas"))
    n = contar_claves(texto, esp["claves"])
    if n < int(esp["min_claves"]):
        r["motivo"] = f"sin_evidencia ({n}/{esp['min_claves']} claves)"
        return r
    r.update(acierto=True, motivo="ok")
    return r


def leer_salidas(dato) -> tuple[dict, dict]:
    """Acepta lista de salidas, {'salidas': [...], ...meta} o una sola salida. Devuelve (por_caso, meta)."""
    meta = {}
    if isinstance(dato, dict) and "salidas" in dato:
        meta = {k: v for k, v in dato.items() if k != "salidas"}
        dato = dato["salidas"]
    if isinstance(dato, dict):
        dato = [dato] if dato else []
    por_caso = {}
    for s in dato or []:
        if isinstance(s, dict) and s.get("caso"):
            por_caso[str(s["caso"])] = s
    return por_caso, meta


def seleccionar(casos: list[dict], agente: str | None = None, ids: list[str] | None = None) -> list[dict]:
    sel = casos
    if agente:
        sel = [c for c in sel if c["agente"] in (agente, "cualquiera")]
    if ids:
        quiero = set(ids)
        sel = [c for c in sel if c["id"] in quiero]
    return sel


def evaluar(casos: list[dict], salidas) -> dict:
    por_caso, meta = leer_salidas(salidas)
    resultados = [puntuar_caso(c, por_caso.get(c["id"])) for c in casos]
    aciertos = sum(r["acierto"] for r in resultados)
    tokens = sum(int(s.get("tokens") or 0) for s in por_caso.values())
    primera = [s for s in por_caso.values() if "intento" in s]
    a_la_primera = sum(1 for s in primera if int(s["intento"]) == 1)
    total = len(resultados)
    return {"total": total, "aciertos": aciertos, "porcentaje": round(100.0 * aciertos / total, 1) if total else 0.0,
            "tokens": tokens, "a_la_primera": a_la_primera, "con_intento": len(primera),
            "resultados": resultados, "meta": meta}


# --------------------------------------------------------------------------- libro de costes
CABECERA_TABLA = "| Fecha | Agente | Modelo | Etiqueta | Casos | Aciertos | % | Tokens | A la primera |"


def anotar_libro(informe: dict, agente: str, modelo: str, etiqueta: str, libro: Path = LIBRO,
                 fecha: str | None = None) -> str:
    fecha = fecha or _dt.date.today().isoformat()
    primera = (f"{informe['a_la_primera']}/{informe['con_intento']}" if informe["con_intento"] else "—")
    fila = (f"| {fecha} | {agente or 'todos'} | {modelo or '—'} | {etiqueta or '—'} | {informe['total']} | "
            f"{informe['aciertos']} | {informe['porcentaje']} | {informe['tokens']} | {primera} |")
    texto = libro.read_text(encoding="utf-8") if libro.exists() else ""
    if CABECERA_TABLA not in texto:
        texto = texto.rstrip("\n") + ("\n\n" if texto else "") + CABECERA_TABLA + "\n|---|---|---|---|---|---|---|---|---|\n"
    libro.write_text(texto.rstrip("\n") + "\n" + fila + "\n", encoding="utf-8")
    return fila


# --------------------------------------------------------------------------- CLI
def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Evaluador del conjunto de oro (T-38)")
    ap.add_argument("--casos-dir", type=Path, default=CASOS_DIR)
    ap.add_argument("--validar", action="store_true", help="solo valida los casos")
    ap.add_argument("--esperadas", action="store_true", help="imprime las salidas ideales")
    ap.add_argument("--preparar", type=Path, help="escribe en DIR la entrada de cada caso, sin la respuesta")
    ap.add_argument("--salidas", type=Path, help="JSON con las salidas del agente")
    ap.add_argument("--agente", choices=["revisor", "forense", "cualquiera"])
    ap.add_argument("--casos", help="ids separados por comas")
    ap.add_argument("--umbral", type=float, help="fracción mínima de aciertos (p. ej. 0.8); si no se llega, sale 1")
    ap.add_argument("--anotar", action="store_true", help="añade una fila al libro de costes")
    ap.add_argument("--libro", type=Path, default=LIBRO)
    ap.add_argument("--modelo", default="")
    ap.add_argument("--etiqueta", default="")
    ap.add_argument("--json", action="store_true", help="informe completo en JSON")
    a = ap.parse_args(argv)

    casos = cargar_casos(a.casos_dir)
    errores = validar(casos)
    if errores:
        print("\n".join(errores), file=sys.stderr)
        return 2
    sel = seleccionar(casos, a.agente, a.casos.split(",") if a.casos else None)
    if a.validar:
        print(f"{len(casos)} casos válidos")
        return 0
    if a.preparar:
        print(f"{len(preparar(sel, a.preparar))} entradas en {a.preparar}")
        return 0
    if a.esperadas:
        print(json.dumps({"salidas": [salida_ideal(c) for c in sel]}, ensure_ascii=False, indent=2))
        return 0
    if not a.salidas:
        ap.error("falta --salidas (o --validar / --esperadas)")
    informe = evaluar(sel, json.loads(a.salidas.read_text(encoding="utf-8")))
    if a.json:
        print(json.dumps(informe, ensure_ascii=False, indent=2))
    else:
        for r in informe["resultados"]:
            print(f"{'OK ' if r['acierto'] else 'NO '} {r['caso']:8} {r['motivo']}")
        print(f"{informe['aciertos']}/{informe['total']} ({informe['porcentaje']} %) · tokens {informe['tokens']}")
    if a.anotar:
        meta = informe["meta"]
        anotar_libro(informe, a.agente or meta.get("agente", ""), a.modelo or meta.get("modelo", ""),
                     a.etiqueta or meta.get("etiqueta", ""), a.libro)
    if a.umbral is not None and informe["total"] and informe["aciertos"] / informe["total"] < a.umbral:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
