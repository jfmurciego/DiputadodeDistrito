#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Registro de P10-P30 en ensayo dentro de una campaña de P00 y re-aplicación en el cierre (T-379 PR 3b).

PROYECTO: Diputado de Distrito
VERSIÓN: 1.0.0
NOMBRE DE VERSIÓN: Registro de campaña P00
FECHA: 2026-11-19
ESTADO: candidato
ANTERIOR: ninguna (fichero nuevo)
CAMBIOS: 1.0.0: fichero nuevo (T-379 PR 3b, opción A del Planificador del 19-11).
MOTIVO: diseño P00 1.1.4 §5 y §6 (un solo commit en main al cierre) y D-147; las herramientas de registro de P10-P30
  no cambian: escriben y empujan como siempre, pero contra un repositorio local.
QUÉ HACE:
  ensayo    en un job de registro con campaña: `origin` pasa a un repositorio local (copia del checkout con `main` y la
            rama del run en HEAD), re-aplica las capturas anteriores del mismo territorio (orden menor) y las empuja ahí;
            imprime el commit base. Ningún push sale a GitHub.
  capturar  tras el registro: el cambio base..origin/<rama> del ensayo → `campanas/<c>/registro/<t>/<orden>-<nombre>/
            <intento>.json`. JSON con objeto en la raíz → delta por claves (registrar_en_main); fichero nuevo → bytes;
            otro fichero versionado → texto con su base (fusión a tres bandas al re-aplicar); borrado → borrar. El
            catálogo de procedencia no se captura (lo regenera el cierre). Rutas ⊆ RUTAS_ROBOT de P90 +
            `configuracion/catalogo_preparacion.yaml` (D-147); otra → CAPTURA_RUTA_NO_ROBOT.
  rutas     unión de rutas de las capturas de los territorios dados (para el plan del cierre).
  componer  en el cierre: re-aplica sobre el árbol (main vigente), por territorio y orden, el último intento de cada
            captura; un choque de texto → CIERRE_CONFLICTO (fallo cerrado, nada se pisa). Imprime las rutas.
  cerrar    el cierre entero (§6.3-§6.5): plan (campana_estado.plan_cierre: rama main o p00-cierre/<run>, rutas
            admitidas, vacío en ensayo) → si la rama ya tiene el commit de esta campaña y huella, nada → si no, UN commit
            con registrar_en_main (re-deriva desde el HEAD remoto en cada intento, catálogo de procedencia en el mismo
            commit, tope 3 intentos = 2 reintentos) → objeto «cierre» en R2 solo tras el push. Solo los territorios
            sanos del recuento final.
NO HACE: borrar en R2 ni abrir la PR de la rama de cierre (lo hace el workflow).
CÓDIGOS DE SALIDA: 0 bien · 2 entrada o estado inválido · 3 conflicto o ruta no admitida.
"""
from __future__ import annotations

import argparse
import base64
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for p in (ROOT, ROOT / "herramientas"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))
import campana_estado as ce  # noqa: E402
from herramientas import registrar_en_main as rem  # noqa: E402

CATALOGO = "configuracion/catalogo_preparacion.yaml"
EXCLUIDAS = {rem.CATALOGO_PROCEDENCIA}
RE_NOMBRE = re.compile(r"[a-z0-9_]{1,40}")


class RegistroError(Exception):
    """Conflicto, ruta no admitida o entrada inválida (fallo cerrado)."""


def _git(root: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess:
    r = subprocess.run(["git", "-c", "user.name=github-actions", "-c", "user.email=github-actions@github.com", *args],
                       cwd=root, capture_output=True, text=True)
    if check and r.returncode != 0:
        raise RegistroError(f"git {' '.join(args)}: {r.stderr.strip()}")
    return r


def _prefijo(campana: str, territorio: str) -> str:
    ce._prefijo(campana)  # valida el id de campaña
    if not re.fullmatch(r"(aut|nac)\d\d", territorio):
        raise RegistroError(f"territorio no válido: {territorio!r}")
    return f"campanas/{campana}/registro/{territorio}/"


def _capturas(alm, campana: str, territorio: str, antes: int | None = None) -> list[dict]:
    """Último intento de cada (orden, nombre), en orden; solo las de orden < `antes` si se da."""
    ult: dict[tuple[int, str], tuple[int, str]] = {}
    for clave in alm.listar(_prefijo(campana, territorio)):
        m = re.search(r"/(\d{2})-([a-z0-9_]+)/(\d+)\.json$", clave)
        if not m:
            continue
        orden, nombre, intento = int(m.group(1)), m.group(2), int(m.group(3))
        if antes is not None and orden >= antes:
            continue
        if (orden, nombre) not in ult or intento > ult[(orden, nombre)][0]:
            ult[(orden, nombre)] = (intento, clave)
    return [json.loads(alm.leer(ult[k][1])) for k in sorted(ult)]


def _admitida(rel: str, patron: re.Pattern) -> bool:
    return rel == CATALOGO or bool(patron.match(rel))


# ─────────────────────────────── re-aplicación ───────────────────────────────

def _fusion_texto(actual: str, base: str, nuevo: str, rel: str) -> str:
    with tempfile.TemporaryDirectory() as td:
        rutas = []
        for nombre, texto in (("actual", actual), ("base", base), ("nuevo", nuevo)):
            p = Path(td) / nombre
            p.write_text(texto, encoding="utf-8")
            rutas.append(str(p))
        r = subprocess.run(["git", "merge-file", "-p", *rutas], capture_output=True, text=True)
    if r.returncode != 0:
        raise RegistroError(f"CIERRE_CONFLICTO: {rel} cambió también en otro territorio o en main en las mismas líneas")
    return r.stdout


def aplicar(root: Path, captura: dict) -> list[str]:
    hechas = []
    for e in captura["entradas"]:
        rel, tipo = e["ruta"], e["tipo"]
        p = Path(root) / rel
        if tipo == "borrar":
            p.unlink(missing_ok=True)
        elif tipo == "nuevo":
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes(base64.b64decode(e["contenido"]))
        elif tipo == "texto":
            actual = p.read_text(encoding="utf-8") if p.is_file() else ""
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(_fusion_texto(actual, e["base"], e["nuevo"], rel), encoding="utf-8")
        elif tipo == "json":
            previo = p.read_text(encoding="utf-8") if p.is_file() else None
            doc = json.loads(previo) if previo is not None else {}
            if not isinstance(doc, dict):
                raise RegistroError(f"CIERRE_CONFLICTO: {rel} ya no tiene un objeto JSON en la raíz")
            ops = [(tuple(o["claves"]), rem._BORRAR if o.get("borrar") else o["valor"]) for o in e["delta"]]
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(rem._volcar_json(rem.aplicar_delta(doc, ops), previo), encoding="utf-8")
        else:
            raise RegistroError(f"tipo de captura no válido: {tipo!r}")
        hechas.append(rel)
    return hechas


# ─────────────────────────────── órdenes ───────────────────────────────

def ensayo(root: Path, destino: Path, rama: str, alm, campana: str, territorio: str, antes: int) -> str:
    root, destino = Path(root).resolve(), Path(destino).resolve()
    _git(root, "clone", "--quiet", "--bare", str(root), str(destino))
    head = _git(root, "rev-parse", "HEAD").stdout.strip()
    for r in {"main", rama}:
        _git(destino, "update-ref", f"refs/heads/{r}", head)
    _git(root, "config", "--local", "--unset-all", "http.https://github.com/.extraheader", check=False)
    for inc in _git(root, "config", "--local", "--name-only", "--get-regexp", r"^includeIf\.gitdir:", check=False).stdout.split():
        _git(root, "config", "--local", "--unset-all", inc, check=False)
    _git(root, "remote", "set-url", "origin", f"file://{destino}")
    tocadas: set[str] = set()
    for c in _capturas(alm, campana, territorio, antes):
        tocadas.update(aplicar(root, c))
    if tocadas:
        _git(root, "add", "-A", "--", *sorted(tocadas))
        if _git(root, "diff", "--cached", "--quiet", check=False).returncode != 0:
            _git(root, "commit", "--quiet", "-m", f"P00 campaña {campana}: re-aplicación de {territorio} (ensayo)")
            for r in {"main", rama}:
                _git(root, "push", "--quiet", "origin", f"HEAD:refs/heads/{r}")
    return _git(root, "rev-parse", "HEAD").stdout.strip()


def capturar(root: Path, base: str, rama: str, alm, campana: str, territorio: str, orden: int, nombre: str,
             intento: int) -> dict:
    root = Path(root).resolve()
    if not RE_NOMBRE.fullmatch(nombre) or not (0 <= orden < 100) or intento < 1:
        raise RegistroError(f"captura no válida: orden={orden} nombre={nombre!r} intento={intento}")
    if "file://" not in _git(root, "remote", "get-url", "origin").stdout:
        raise RegistroError("CAPTURA_SIN_ENSAYO: origin no es el repositorio de ensayo")
    _git(root, "fetch", "--quiet", "origin", rama)
    fin = _git(root, "rev-parse", "FETCH_HEAD").stdout.strip()
    nombres = _git(root, "diff", "--name-only", "--no-renames", base, fin).stdout.split("\n")
    patron = ce.rutas_robot(ROOT)
    entradas = []
    for rel in sorted(n for n in nombres if n and n not in EXCLUIDAS):
        if not _admitida(rel, patron):
            raise RegistroError(f"CAPTURA_RUTA_NO_ROBOT: {rel} (fuera de RUTAS_ROBOT y no es {CATALOGO}; D-147)")
        antes = _git(root, "show", f"{base}:{rel}", check=False)
        despues = _git(root, "show", f"{fin}:{rel}", check=False)
        if despues.returncode != 0:
            entradas.append({"ruta": rel, "tipo": "borrar"})
        elif antes.returncode != 0:
            datos = subprocess.run(["git", "show", f"{fin}:{rel}"], cwd=root, capture_output=True, check=True).stdout
            entradas.append({"ruta": rel, "tipo": "nuevo", "contenido": base64.b64encode(datos).decode("ascii")})
        elif rel.endswith(".json") and _objeto(antes.stdout) and _objeto(despues.stdout):
            ops = rem.delta_json(json.loads(antes.stdout), json.loads(despues.stdout))
            entradas.append({"ruta": rel, "tipo": "json", "delta": [
                {"claves": list(k), "borrar": True} if v is rem._BORRAR else {"claves": list(k), "valor": v} for k, v in ops]})
        else:
            entradas.append({"ruta": rel, "tipo": "texto", "base": antes.stdout, "nuevo": despues.stdout})
    captura = {"campana": campana, "territorio": territorio, "orden": orden, "nombre": nombre, "intento": intento,
               "base": base, "fin": fin, "entradas": entradas}
    alm.escribir(f"{_prefijo(campana, territorio)}{orden:02d}-{nombre}/{intento}.json", ce._json(captura))
    return captura


def _objeto(texto: str) -> bool:
    try:
        return isinstance(json.loads(texto), dict)
    except ValueError:
        return False


def rutas(alm, campana: str, territorios: list[str]) -> list[str]:
    return sorted({e["ruta"] for t in territorios for c in _capturas(alm, campana, t) for e in c["entradas"]})


def componer(root: Path, alm, campana: str, territorios: list[str]) -> list[str]:
    hechas: set[str] = set()
    for t in sorted(territorios):
        for c in _capturas(alm, campana, t):
            hechas.update(aplicar(Path(root), c))
    return sorted(hechas)


def mensaje_cierre(campana: str, huella: str) -> str:
    return f"P00 campaña {campana} · cierre · huella {huella}"


def cerrar(root: Path, alm, campana: str, ref: str, run_id: str, intentos: int = 3, backoff=rem.espera) -> dict:
    root = Path(root).resolve()
    sem = ce.leer_semaforo(alm, campana)
    rec = ce.recuento(alm, campana, final=True)
    sanos = sorted(t for t, f in rec["territorios"].items() if f["estado"] == "sano")
    plan = ce.plan_cierre(alm, campana, ref, run_id, sem["eleccion"]["ensayo"], rutas(alm, campana, sanos), ROOT)  # RUTAS_ROBOT de la versión fija
    rama, huella = plan["rama"], plan["huella"]
    if not plan["commit"]:
        ce.registrar_cierre(alm, campana, huella, rama, None)
        return {"rama": rama, "sha": None, "commit": False, "sanos": sanos, "huella": huella}
    mensaje = mensaje_cierre(campana, huella)
    _git(root, "fetch", "--quiet", "origin", rama)
    previo = _git(root, "log", "FETCH_HEAD", "-n", "200", "--format=%H%x00%s", check=False).stdout
    hecho = next((ln.split("\0")[0] for ln in previo.splitlines() if ln.split("\0")[-1] == mensaje), None)
    if hecho is None:
        res = rem.registrar(root_dir=root, rama=rama, mensaje=mensaje, rutas=plan["ficheros"],
                            aplicar=lambda r: componer(r, alm, campana, sanos), max_intentos=intentos, backoff=backoff)
        hecho = res.head_sha if res.estado == "REGISTRADO" else None
    ce.registrar_cierre(alm, campana, huella, rama, hecho)
    return {"rama": rama, "sha": hecho, "commit": hecho is not None, "sanos": sanos, "huella": huella}


def _territorios(valor: str) -> list[str]:
    return [t for t in re.split(r"[,\s]+", valor or "") if t]


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=(__doc__ or "").splitlines()[0])
    sub = ap.add_subparsers(dest="accion", required=True)

    def comunes(p, territorio=True):
        p.add_argument("--almacen", required=True, help="r2 | dir:<ruta>")
        p.add_argument("--campana", required=True)
        if territorio:
            p.add_argument("--territorio", required=True)
        return p

    p = comunes(sub.add_parser("ensayo"))
    p.add_argument("--root-dir", default=".")
    p.add_argument("--destino", required=True)
    p.add_argument("--rama", required=True)
    p.add_argument("--antes", required=True, type=int, help="re-aplica las capturas de orden menor")
    p = comunes(sub.add_parser("capturar"))
    p.add_argument("--root-dir", default=".")
    p.add_argument("--base", required=True)
    p.add_argument("--rama", required=True)
    p.add_argument("--orden", required=True, type=int)
    p.add_argument("--nombre", required=True)
    p.add_argument("--intento", required=True, type=int)
    p = comunes(sub.add_parser("rutas"), territorio=False)
    p.add_argument("--territorios", required=True)
    p = comunes(sub.add_parser("cerrar"), territorio=False)
    p.add_argument("--root-dir", default=".")
    p.add_argument("--ref", required=True)
    p.add_argument("--run-id", required=True)
    p = comunes(sub.add_parser("componer"), territorio=False)
    p.add_argument("--root-dir", default=".")
    p.add_argument("--territorios", required=True)
    ns = ap.parse_args(argv)
    try:
        alm = ce.almacen(ns.almacen)
        if ns.accion == "ensayo":
            print(ensayo(Path(ns.root_dir), Path(ns.destino), ns.rama, alm, ns.campana, ns.territorio, ns.antes))
        elif ns.accion == "capturar":
            c = capturar(Path(ns.root_dir), ns.base, ns.rama, alm, ns.campana, ns.territorio, ns.orden, ns.nombre,
                         ns.intento)
            print(json.dumps([e["ruta"] for e in c["entradas"]], ensure_ascii=False))
        elif ns.accion == "cerrar":
            print(json.dumps(cerrar(Path(ns.root_dir), alm, ns.campana, ns.ref, ns.run_id), ensure_ascii=False))
        elif ns.accion == "rutas":
            print("\n".join(rutas(alm, ns.campana, _territorios(ns.territorios))))
        else:
            print("\n".join(componer(Path(ns.root_dir), alm, ns.campana, _territorios(ns.territorios))))
        return 0
    except RegistroError as exc:
        ce._error(str(exc))
        return 3
    except rem.PushRechazado as exc:
        ce._error(f"CIERRE_PENDIENTE: {exc}")
        return rem.SALIDA_AGOTADO
    except rem.RutaNoFusionable as exc:
        ce._error(str(exc))
        return rem.SALIDA_NO_FUSIONABLE
    except (ce.EstadoError, ValueError) as exc:
        ce._error(str(exc))
        return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
