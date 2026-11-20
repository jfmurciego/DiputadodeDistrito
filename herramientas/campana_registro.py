#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Registro de P10-P30 en ensayo dentro de una campaña de P00 y re-aplicación en el cierre (T-379 PR 3b).

PROYECTO: Diputado de Distrito
VERSIÓN: 1.1.0
NOMBRE DE VERSIÓN: Registro de campaña P00
FECHA: 2026-11-20
ESTADO: candidato
ANTERIOR: legacy/herramientas/campana_registro_v1.0.0_20261120.py
CAMBIOS: 1.1.0 (T-379 3c-i, Planificador 20-11): `cerrar` escribe, en el mismo commit y por territorio sano, el manifiesto
  de ejecución completa `territorios/<id>/evidencia/ejecuciones_completas/<run>.json` (el que el job `manifestar` de la 00
  escribe con escribir_manifest_ejecucion_completa.py), con los datos de las puertas 01-04 y la optimización que la cadena
  deja en las huellas de P10, P20 y P30; sin esos datos → CIERRE_MANIFIESTO_INCOMPLETO (fallo cerrado, sin commit). Nueva
  entrada obligatoria `--source-sha` (versión de la campaña). Sin campaña nada cambia: la herramienta solo la usa P00 Campaña.
CAMBIOS 1.0.0: fichero nuevo (T-379 PR 3b, opción A del Planificador del 19-11).
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
            sanos del recuento final. Retira, por territorio, el M06 que contiene su M08 (manifiesto en el commit; borrado
            en R2 después del push). Escribe el manifiesto de ejecución completa de cada sano (1.1.0) para P40.
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
import archivar_artefactos_r2 as ar  # noqa: E402
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


def retirar_m06(root: Path, run_id: str, territorios: list[str]) -> list[str]:
    """Retirada del M06 que contiene el M08 (lo que P30 hace con `--sustituye-m06-run` fuera de campaña), POR TERRITORIO:
    en una campaña todos comparten run y retirar por run borraría el M06 de los demás. Solo edita el manifiesto (entra en
    el commit de cierre); devuelve las claves de R2 a borrar DESPUÉS del push. Sin M08 del territorio, no retira nada."""
    ruta = Path(root) / ar.MANIFIESTO
    if not ruta.is_file():
        return []
    man = ar.cargar_manifiesto(ruta)
    arts = man.get("artefactos") or {}
    claves = []

    def final(e, n):
        m = ar._FINAL.match(str(e.get("artefacto", "")))
        return bool(m) and m.group(2) == n and str(e.get("run_id")) == str(run_id)

    for t in sorted(territorios):
        slug = ar._slug(t)
        m08 = [k for k, e in arts.items() if final(e, "8") and e.get("territorio") == slug]
        if not m08:
            continue
        for k in m08:
            arts[k]["incluye_m06_run"] = str(run_id)
        for k, e in list(arts.items()):
            if final(e, "6") and e.get("territorio") == slug:
                del arts[k]
                claves.append(k)
    if claves:
        ar.guardar_manifiesto(ruta, man)
    return sorted(claves)


ESCRITOR = ROOT / "herramientas" / "escribir_manifest_ejecucion_completa.py"
PUERTAS = (("P10", "puerta_01", "territorial-source"), ("P20", "puerta_02", "territorial-product"),
           ("P30", "puerta_03", "electoral-source"), ("P30", "puerta_04", "electoral-product"))


def ruta_manifiesto(territory_id: str, run_id: str) -> str:
    return f"territorios/{territory_id}/evidencia/ejecuciones_completas/{run_id}.json"


def _huellas(alm, campana: str, territorio: str) -> dict[str, dict]:
    regs = ce._registros(alm, campana)
    out = {}
    for paso in ce.PASOS:
        u = ce._ultimo(regs, territorio, paso)
        out[paso] = (u[1].get("huellas") or {}) if u and u[1].get("estado") == "ok" else {}
    return out


def argumentos_manifiesto(alm, campana: str, territorio: str, run_id: str, source_sha: str, evidencia: Path) -> list[str]:
    """Argumentos de escribir_manifest_ejecucion_completa.py para un territorio sano, desde las huellas de la cadena (la
    misma información que la 00 pasa desde los `needs.puerta_0X.outputs`). Las cuatro puertas pasaron (son obligatorias
    en sus pasos): validación VALIDADO. La publicación no es de la cadena: «05» no pedida (P40 registra la suya)."""
    h = _huellas(alm, campana, territorio)
    plan, optim = h["P10"].get("plan") or {}, h["P20"].get("optimizacion") or {}
    faltan = [k for k in ("territory_id", "territory_name", "edition", "modo") if not plan.get(k)]
    if not optim.get("effective_algorithm"):
        faltan.append("optimizacion.effective_algorithm")
    args = ["--territory-id", str(plan.get("territory_id", "")), "--territory-name", str(plan.get("territory_name", "")),
            "--edition", str(plan.get("edition", "")), "--execution-mode", str(plan.get("modo", "")),
            "--optimization-algorithm", "Canónico", "--optimization-evidence", str(evidencia),
            "--workflow-run-id", str(run_id), "--source-sha", source_sha,
            "--publication-mode-requested", "electoral", "--publication-mode-effective", "electoral",
            "--publish-requested", "false", "--publish-result", "skipped"]
    for fase in ("prepare-territorial", "generate", "prepare-electoral", "incorporate"):
        args += [f"--{fase}-result", "success", f"--{fase}-executed", "true"]
    for paso, puerta, prefijo in PUERTAS:
        p = h[paso].get(puerta) or {}
        for campo in ("run_id", "artifact_name", "artifact_digest", "phase_decision"):
            if not str(p.get(campo) or "").strip():
                faltan.append(f"{puerta}.{campo}")
        args += [f"--{prefijo}-run-id", str(p.get("run_id", "")), f"--{prefijo}-artifact", str(p.get("artifact_name", "")),
                 f"--{prefijo}-digest", str(p.get("artifact_digest", "")), f"--{prefijo}-validation", "VALIDADO",
                 f"--{prefijo}-phase-decision", str(p.get("phase_decision", ""))]
    if faltan:
        raise RegistroError(f"CIERRE_MANIFIESTO_INCOMPLETO: {territorio} sin {', '.join(faltan)} en las huellas de la cadena")
    evidencia.write_text(json.dumps({"requested_algorithm": optim.get("requested_algorithm") or "Canónico",
                                     "effective_algorithm": optim["effective_algorithm"],
                                     "fallback": bool(optim.get("fallback", False)),
                                     "fallback_reason": optim.get("fallback_reason")}, ensure_ascii=False), encoding="utf-8")
    return args


def manifiestos(root: Path, alm, campana: str, run_id: str, source_sha: str, territorios: list[str]) -> list[str]:
    """Escribe el manifiesto de ejecución completa de cada territorio (P40 resuelve con él); devuelve las rutas."""
    if not re.fullmatch(r"[0-9a-f]{40}", source_sha or ""):
        raise RegistroError(f"source_sha no válido: {source_sha!r}")
    rutas_m = []
    with tempfile.TemporaryDirectory() as td:
        for t in sorted(territorios):
            evidencia = Path(td) / f"{t}_optimizacion.json"
            args = argumentos_manifiesto(alm, campana, t, run_id, source_sha, evidencia)
            rel = ruta_manifiesto(args[1], run_id)
            r = subprocess.run([sys.executable, str(ESCRITOR), *args, "--output", str(Path(root) / rel)],
                               capture_output=True, text=True)
            if r.returncode != 0:
                raise RegistroError(f"CIERRE_MANIFIESTO_INCOMPLETO: {t}: {r.stderr.strip()[-400:]}")
            if json.loads((Path(root) / rel).read_text(encoding="utf-8")).get("status") != "SUCCESS":
                raise RegistroError(f"CIERRE_MANIFIESTO_INCOMPLETO: {t}: el manifiesto no sale SUCCESS")
            rutas_m.append(rel)
    return rutas_m


def mensaje_cierre(campana: str, huella: str) -> str:
    return f"P00 campaña {campana} · cierre · huella {huella}"


def cerrar(root: Path, alm, campana: str, ref: str, run_id: str, source_sha: str, intentos: int = 3, backoff=rem.espera,
           borrar_r2=None) -> dict:
    root = Path(root).resolve()
    sem = ce.leer_semaforo(alm, campana)
    rec = ce.recuento(alm, campana, final=True)
    sanos = sorted(t for t, f in rec["territorios"].items() if f["estado"] == "sano")
    ensayo_ = sem["eleccion"]["ensayo"]
    # Rutas de los manifiestos sin escribirlos todavía (se escriben en `aplicar`, sobre el HEAD remoto de cada intento).
    with tempfile.TemporaryDirectory() as td:
        rutas_m = [] if ensayo_ else manifiestos(Path(td), alm, campana, run_id, source_sha, sanos)
    plan = ce.plan_cierre(alm, campana, ref, run_id, ensayo_, rutas(alm, campana, sanos) + rutas_m, ROOT)  # RUTAS_ROBOT de la versión fija
    rama, huella = plan["rama"], plan["huella"]
    if not plan["commit"]:
        ce.registrar_cierre(alm, campana, huella, rama, None)
        return {"rama": rama, "sha": None, "commit": False, "sanos": sanos, "huella": huella}
    mensaje = mensaje_cierre(campana, huella)
    _git(root, "fetch", "--quiet", "origin", rama)
    previo = _git(root, "log", "FETCH_HEAD", "-n", "200", "--format=%H%x00%s", check=False).stdout
    hecho = next((ln.split("\0")[0] for ln in previo.splitlines() if ln.split("\0")[-1] == mensaje), None)
    retiradas: list[str] = []

    def aplicar(r: Path) -> None:
        componer(r, alm, campana, sanos)
        manifiestos(r, alm, campana, run_id, source_sha, sanos)
        retiradas[:] = retirar_m06(r, campana, sanos)

    rutas_commit = sorted(set(plan["ficheros"]) | ({ar.MANIFIESTO} if (root / ar.MANIFIESTO).is_file() else set()))
    nuevo = hecho is None
    if nuevo:
        res = rem.registrar(root_dir=root, rama=rama, mensaje=mensaje, rutas=rutas_commit, aplicar=aplicar,
                            max_intentos=intentos, backoff=backoff)
        hecho = res.head_sha if res.estado == "REGISTRADO" else None
    ce.registrar_cierre(alm, campana, huella, rama, hecho)
    fallidas = []
    if nuevo and hecho and retiradas:  # borrado en R2 solo tras el push confirmado; si falla, ocupa espacio, no pierde datos
        borrar = borrar_r2 or _borrador_r2()
        for k in retiradas:
            try:
                borrar(k)
            except Exception as exc:  # noqa: BLE001
                print(f"::warning::No se pudo retirar {k} de R2: {exc}", file=sys.stderr)
                fallidas.append(k)
    return {"rama": rama, "sha": hecho, "commit": hecho is not None, "sanos": sanos, "huella": huella,
            "retiradas": retiradas, "retiradas_fallidas": fallidas}


def _borrador_r2():
    import os
    from herramientas import archivo_origen as ao
    bucket, cuenta = os.environ.get("R2_BUCKET", ""), os.environ.get("R2_ACCOUNT_ID", "")
    if not (bucket and cuenta):
        raise RegistroError("CIERRE_SIN_R2: faltan R2_BUCKET/R2_ACCOUNT_ID para retirar el M06")
    return ao.r2_borrador(bucket, cuenta)


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
    p.add_argument("--source-sha", required=True, help="versión de la campaña (GITHUB_SHA), para el manifiesto")
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
            print(json.dumps(cerrar(Path(ns.root_dir), alm, ns.campana, ns.ref, ns.run_id, ns.source_sha), ensure_ascii=False))
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
