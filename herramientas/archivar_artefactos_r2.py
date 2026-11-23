#!/usr/bin/env python3
"""Archivista: copia a Cloudflare R2 los artefactos de Actions referenciados antes de que caduquen.

PROYECTO: Diputado de Distrito
VERSIÓN: 1.2.0
NOMBRE DE VERSIÓN: Archivista R2 solo de productos finales
FECHA: 2026-11-23
ESTADO: candidato
QUÉ HACE: lee el catálogo operativo (orchestracion/estado_operativo.json) y orchestracion/publicaciones_visor.json,
  obtiene los runs y artefactos «ddd-state-<run>-M0x», «ddd-audit-<run>…» (y paquetes fuente) que referencian,
  lista los que siguen vivos en Actions, ordenados por caducidad (primero lo que caduca antes), y por cada uno:
  descarga el ZIP, calcula sha256 y tamaño, lo sube a R2 con clave <territorio>/<run>/<artefacto>.zip y anota
  la entrada en orchestracion/archivo_r2.json (URL R2, sha256, tamaño, caducidad original, fecha de archivado).
IDEMPOTENTE: no vuelve a descargar un artefacto (mismo id) ya archivado, y no vuelve a subir si R2 ya tiene
  la misma clave con el mismo sha256. Un artefacto caducado y no archivado se informa como «perdido».
CAMBIOS: 1.2.0 (T-443, D-188/D-190/D-198): escribe en el árbol nuevo de R2, sin run en la ruta. Vigente = publicado + último (D-198):
  `interno/estados/<ámbito>/<territorio>/ultimo/<tipo>.zip` (el run más reciente) y, si el run es el publicado del territorio en
  orchestracion/publicaciones_visor.json, también `…/publicado/<tipo>.zip` (solo cambia al publicar otro run). Guarda en R2, no en el índice: antes
  de subir lee el metadato `run` del objeto (head-object) y nunca pisa un run mayor en `ultimo/` (`superados`); cada objeto sube con metadatos
  `sha256` y `run`. Tras subir, el `manifiesto.json` de cada carpeta tocada se rehace con las cabeceras de R2 (run, sha256 y bytes de lo que hay
  de verdad). Las entradas de orchestracion/archivo_r2.json siguen con run, territorio y sha256 (restaurar_estado_r2 y P75 buscan por run, en
  `publicado/` o `ultimo/`). Estado completo y territorio sin resolver: clave vieja `<territorio>/<run>/<artefacto>.zip`.
  1.1.1 (T-90): el paquete mínimo acepta los GeoJSON comprimidos *.geojson.zip, que es como los
  escriben M01-M08 (sin ellos el M08 de Barcelona, run 42416213698, falló con «ningún GeoJSON distrital»).
  1.1.0 (T-72): solo archiva el producto final de cada run (ddd-state-<run>-M06/M08) y las auditorías
  (KB); nunca los estados intermedios M01-M05 ni los paquetes fuente. Si el run tiene vivo su M08, no copia su M06:
  el estado M08 es acumulativo (lleva cache/run del M06; M08 = M06 + 1-10 MB). Tampoco sube el ZIP de estado
  completo: sube un paquete mínimo ddd-minimo-<run>-M0x.zip (GeoJSON distritales, CSV/JSON de M06-M08, VALIDACION,
  CHAIN_STATE y manifiestos, con MANIFEST_MINIMO.json: sha256 de cada fichero y del estado original). Decisión del
  propietario: R2 total ≤ 8 GB.
  1.0.1: reintentos con espera exponencial (2, 4, 8, 16, 32 s; 6 intentos) ante 5xx, 429 y errores de red
  en la API de GitHub y en R2, con registro de cada intento (run 42393003447: HTTP 500 al listar artefactos).
  1.0.0: fichero nuevo (T-47).
MOTIVO: los artefactos caducan a los 14 días y con ellos productos registrados en el catálogo (p. ej. M05 de
  Cantabria, run 41037133327).
ANTERIOR: legacy/herramientas/archivar_artefactos_r2_v1.1.1_20261123.py
Uso: python herramientas/archivar_artefactos_r2.py [--root-dir .] [--caduca-antes AAAA-MM-DD] [--max N] [--simular]
Entorno: GITHUB_TOKEN, GITHUB_REPOSITORY; R2_BUCKET, R2_ACCOUNT_ID y credenciales AWS_* (aws cli) salvo --simular.
Salida: 0 si todo lo archivable quedó archivado; 1 si hubo errores de copia.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Optional

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from herramientas import rutas_r2  # noqa: E402
CATALOGO = "orchestracion/estado_operativo.json"
VISOR = "orchestracion/publicaciones_visor.json"
MANIFIESTO = "orchestracion/archivo_r2.json"
SCHEMA = "ddd.archivo-r2/1.0"

_NOMBRE = re.compile(r"^ddd-(state|audit|source-package)-")
_FINAL = re.compile(r"^ddd-(?:state|minimo)-(\d+)-M0([68])(?:-|$)")


def es_final(nombre: str) -> bool:
    """Producto final archivable: estado M06/M08 o auditoría (no M01-M05 ni paquetes fuente)."""
    return bool(_FINAL.match(nombre)) or nombre.startswith("ddd-audit-")
_RUN = re.compile(r"(?<!\d)(\d{8,})(?!\d)")


def _utcnow() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _run_de_nombre(nombre: str) -> Optional[str]:
    m = _RUN.search(nombre)
    return m.group(1) if m else None


def _slug(txt: str) -> str:
    return re.sub(r"[^a-z0-9_.-]+", "_", (txt or "sin_territorio").lower()).strip("_") or "sin_territorio"


def referencias(root: Path) -> tuple[dict[str, str], dict[str, str]]:
    """Devuelve (nombres explícitos → territorio, run → territorio) del catálogo y del visor."""
    nombres: dict[str, str] = {}
    runs: dict[str, str] = {}

    def visitar(x, territorio=None):
        if isinstance(x, dict):
            territorio = x.get("territory_id") or territorio
            nom = x.get("artifact_name")
            if isinstance(nom, str) and _NOMBRE.match(nom):
                nombres.setdefault(nom, territorio or "sin_territorio")
            for v in x.values():
                visitar(v, territorio)
        elif isinstance(x, list):
            for v in x:
                visitar(v, territorio)

    cat = root / CATALOGO
    if cat.is_file():
        visitar(json.loads(cat.read_text(encoding="utf-8")))
    vis = root / VISOR
    if vis.is_file():
        for p in json.loads(vis.read_text(encoding="utf-8")).get("products", []):
            run = str(p.get("run_id") or "")
            if run.isdigit() and p.get("territory_id"):
                runs.setdefault(run, p["territory_id"])
    for nom, terr in nombres.items():
        run = _run_de_nombre(nom)
        if run and nom.startswith(("ddd-state-", "ddd-audit-")):
            runs.setdefault(run, terr)
    return nombres, runs


def cubierto_por_m08(nombre: str, entradas: dict) -> bool:
    """Un M06 está en R2 dentro del M08 acumulativo de su run o del M08 que lo declara (``incluye_m06_run``)."""
    m = _FINAL.match(nombre)
    if not m or m.group(2) != "6":
        return False
    for e in entradas.values():
        f = _FINAL.match(str(e.get("artefacto", "")))
        if f and f.group(2) == "8" and m.group(1) in (f.group(1), str(e.get("incluye_m06_run", ""))):
            return True
    return False


def seleccionar(vivos: list[dict], nombres: dict[str, str], runs: dict[str, str]) -> list[dict]:
    """Artefactos vivos referenciados, con territorio y run, por caducidad ascendente."""
    out = []
    con_m08 = {m.group(1) for a in vivos if not a.get("expired") and (m := _FINAL.match(a["name"])) and m.group(2) == "8"}
    for a in vivos:
        if a.get("expired"):
            continue
        nom = a["name"]
        m = _FINAL.match(nom)
        if not es_final(nom) or (m and m.group(2) == "6" and m.group(1) in con_m08):
            continue
        run = str((a.get("workflow_run") or {}).get("id") or _run_de_nombre(nom) or "")
        if nom in nombres:
            terr = nombres[nom]
        elif nom.startswith(("ddd-state-", "ddd-audit-")) and _run_de_nombre(nom) in runs:
            terr = runs[_run_de_nombre(nom)]
            run = _run_de_nombre(nom)
        else:
            continue
        out.append({**a, "territorio": _slug(terr), "run": run})
    out.sort(key=lambda a: (a.get("expires_at") or "9999", a["name"]))
    return out


def nombre_paquete(nombre: str) -> str:
    """ddd-state-<run>-M0x… → ddd-minimo-<run>-M0x… (el paquete mínimo que va a R2)."""
    return nombre.replace("ddd-state-", "ddd-minimo-", 1) if nombre.startswith("ddd-state-") else nombre


def clave_vieja(a: dict, empaquetado: bool = False) -> str:
    """Clave anterior a T-443: `<territorio>/<run>/<artefacto>.zip`."""
    nombre = nombre_paquete(a["name"]) if empaquetado else a["name"]
    return f"{a['territorio']}/{a['run']}/{nombre}.zip"


def clave(a: dict, empaquetado: bool = False, hueco: str = "ultimo") -> str:
    """Clave en el árbol nuevo (D-188/D-198): `interno/estados/<ámbito>/<territorio>/<hueco>/<tipo>.zip`; sin territorio resuelto, la vieja."""
    nombre = nombre_paquete(a["name"]) if empaquetado else a["name"]
    if nombre.startswith("ddd-state-"):  # el estado completo no entra en el árbol nuevo: interno/ guarda solo el paquete mínimo
        return clave_vieja(a, empaquetado)
    try:
        return rutas_r2.ruta_estado(a["territorio"], nombre, hueco)
    except (rutas_r2.RutaInvalida, KeyError, ValueError):
        return clave_vieja(a, empaquetado)


def _norm(t: str) -> str:
    try:
        return rutas_r2.ti.resolver_id(t)
    except (KeyError, ValueError):
        return str(t)


def publicados(root: Path) -> dict[str, str]:
    """Territorio (id nuevo) → run publicado (el mayor de sus productos en orchestracion/publicaciones_visor.json)."""
    vis = root / VISOR
    out: dict[str, str] = {}
    if not vis.is_file():
        return out
    for p in json.loads(vis.read_text(encoding="utf-8")).get("products", []):
        run, t = str(p.get("run_id") or ""), p.get("territory_id")
        if run.isdigit() and t and _run_num(run) > _run_num(out.get(_norm(t))):
            out[_norm(t)] = run
    return out


def _run_num(x) -> int:
    return int(x) if str(x or "").isdigit() else -1


def manifiesto_carpeta(entradas: dict, carpeta: str, r2_cab: Optional[Callable[[str], Optional[dict]]] = None) -> dict:
    """`manifiesto.json` de una carpeta del árbol nuevo. Con `r2_cab`, cada fichero con lo que R2 tiene de verdad (sha256, run y bytes de su
    cabecera; uno que ya no está en R2 sale del manifiesto); sin él, lo que anota el índice."""
    fich = {}
    for k, e in entradas.items():
        if k.rsplit("/", 1)[0] != carpeta or k.endswith("/manifiesto.json"):
            continue
        ficha = {"sha256": e.get("sha256"), "bytes": e.get("tamano_bytes"), "run": e.get("run_id"), "artefacto": e.get("artefacto")}
        if r2_cab is not None:
            cab = r2_cab(k)
            if cab is None:
                continue
            ficha.update({x: cab[x] for x in ("sha256", "bytes", "run") if cab.get(x) is not None})
        fich[k.rsplit("/", 1)[1]] = ficha
    return rutas_r2.manifiesto(fich, extra={"carpeta": carpeta})


def subir_manifiestos(carpetas, entradas: dict, r2_subir: Callable[[str, Path, str], None],
                      r2_sha: Optional[Callable[[str], Optional[str]]] = None,
                      r2_cab: Optional[Callable[[str], Optional[dict]]] = None) -> list[str]:
    """Sube el `manifiesto.json` de cada carpeta tocada (contenido determinista; no resube si R2 ya lo tiene igual)."""
    hechos = []
    for c in sorted(carpetas):
        datos = (json.dumps(manifiesto_carpeta(entradas, c, r2_cab), ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")
        with tempfile.TemporaryDirectory() as td:
            f = Path(td) / "manifiesto.json"
            f.write_bytes(datos)
            h, k = hashlib.sha256(datos).hexdigest(), f"{c}/manifiesto.json"
            if r2_sha is not None and r2_sha(k) == h:
                continue
            r2_subir(k, f, h)
        hechos.append(k)
    return hechos


def sha256_fichero(ruta: Path) -> str:
    h = hashlib.sha256()
    with open(ruta, "rb") as f:
        for bloque in iter(lambda: f.read(1 << 20), b""):
            h.update(bloque)
    return h.hexdigest()


def archivar(
    vivos: list[dict],
    nombres: dict[str, str],
    runs: dict[str, str],
    manifiesto: dict,
    descargar: Callable[[dict, Path], None],
    r2_sha: Callable[[str], Optional[str]],
    r2_subir: Callable[..., None],
    bucket: str,
    ahora: Callable[[], str] = _utcnow,
    caduca_antes: Optional[str] = None,
    maximo: Optional[int] = None,
    empaquetar: Optional[Callable[[dict, Path, Path], Path]] = None,
    publicado: Optional[dict[str, str]] = None,
    r2_cab: Optional[Callable[[str], Optional[dict]]] = None,
) -> dict:
    """Núcleo sin red: aplica la política y devuelve el resumen; muta `manifiesto`.

    Con ``empaquetar(a, zip_estado, dir_tmp) -> zip_paquete``, los estados ddd-state-* no se suben enteros: se sube el
    paquete mínimo (clave ddd-minimo-…) y la entrada guarda el sha256 y el tamaño del estado original.
    ``publicado`` (territorio → run publicado, `publicados()`) añade el hueco `publicado/`; ``r2_cab(k)`` → {sha256, run, bytes} | None es la
    guarda en R2 (sin ella, la del índice)."""
    entradas = manifiesto.setdefault("artefactos", {})
    res = {"archivados": [], "ya_archivados": [], "sin_cambios_r2": [], "errores": [], "omitidos": [], "superados": [], "manifiestos": []}
    tocadas: set[str] = set()
    publicado = publicado or {}

    def run_remoto(k: str) -> int:
        if r2_cab is not None:
            cab = r2_cab(k)
            return _run_num((cab or {}).get("run"))
        return _run_num((entradas.get(k) or {}).get("run_id"))

    for a in seleccionar(vivos, nombres, runs):
        emp = empaquetar is not None and a["name"].startswith("ddd-state-")
        k = clave(a, emp)
        destinos = [k]
        if rutas_r2.es_nueva(k) and publicado.get(_norm(a["territorio"])) == str(a["run"]):
            destinos.append(clave(a, emp, "publicado"))
        if caduca_antes and (a.get("expires_at") or "9999") >= caduca_antes:
            res["omitidos"].append(k)
            continue
        if all(d in entradas and str(entradas[d].get("artifact_id")) == str(a["id"]) for d in destinos):
            res["ya_archivados"].append(k)
            continue
        if maximo is not None and len(res["archivados"]) + len(res["sin_cambios_r2"]) >= maximo:
            res["omitidos"].append(k)
            continue
        try:
            if rutas_r2.es_nueva(k) and run_remoto(k) > _run_num(a["run"]):
                res["superados"].append(k)  # D-198: un run anterior nunca pisa al último (guarda en R2)
                destinos.remove(k)
            if not destinos:
                continue
            with tempfile.TemporaryDirectory() as td:
                zip_ = Path(td) / "a.zip"
                descargar(a, zip_)
                origen = {}
                if emp:
                    origen = {"artefacto_origen": a["name"], "sha256_estado_original": sha256_fichero(zip_),
                              "tamano_estado_original": zip_.stat().st_size}
                    zip_ = empaquetar(a, zip_, Path(td))
                sha, tam = sha256_fichero(zip_), zip_.stat().st_size
                for d in destinos:
                    if r2_sha(d) == sha:
                        res["sin_cambios_r2"].append(d)
                    elif rutas_r2.es_nueva(d):
                        r2_subir(d, zip_, sha, str(a["run"]))
                        res["archivados"].append(d)
                    else:
                        r2_subir(d, zip_, sha)
                        res["archivados"].append(d)
        except Exception as exc:  # noqa: BLE001 - se informa y se sigue con el siguiente
            res["errores"].append(f"{k}: {exc}")
            continue
        for d in destinos:
            entradas[d] = {
                **origen,
                "artefacto": nombre_paquete(a["name"]) if emp else a["name"],
                "territorio": a["territorio"],
                "run_id": a["run"],
                "artifact_id": a["id"],
                "url": f"r2://{bucket}/{d}",
                "sha256": sha,
                "tamano_bytes": tam,
                "caducidad_original": a.get("expires_at"),
                "archivado_en": ahora(),
            }
            if rutas_r2.es_nueva(d):
                tocadas.add(d.rsplit("/", 1)[0])
    try:
        res["manifiestos"] = subir_manifiestos(tocadas, entradas, r2_subir, r2_sha, r2_cab)
    except Exception as exc:  # noqa: BLE001 - el objeto ya está y su entrada también; se informa
        res["errores"].append(f"manifiesto.json: {exc}")
    existentes = {a["name"] for a in vivos}
    res["perdidos"] = sorted(
        n for n in nombres if es_final(n) and n not in existentes and not any(n in (e["artefacto"], e.get("artefacto_origen")) for e in entradas.values())
        and not cubierto_por_m08(n, entradas)
    )
    manifiesto["schema"] = SCHEMA
    manifiesto["actualizado_en"] = ahora()
    return res


def cargar_manifiesto(ruta: Path) -> dict:
    if ruta.is_file():
        return json.loads(ruta.read_text(encoding="utf-8"))
    return {"schema": SCHEMA, "artefactos": {}}


def guardar_manifiesto(ruta: Path, m: dict) -> bool:
    """Escribe de forma determinista; devuelve True si el contenido cambió (ignora `actualizado_en`)."""
    m["artefactos"] = dict(sorted(m["artefactos"].items()))
    previo = cargar_manifiesto(ruta)
    if previo.get("artefactos") == m["artefactos"]:
        return False
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_text(json.dumps(m, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return True


# --- Paquete mínimo -------------------------------------------------------------------------------

PAQUETE_SCHEMA = "ddd.paquete-minimo/1.0"
_PAQ_EXT = {".geojson", ".csv", ".json"}
_PAQ_NOMBRE = re.compile(r"_m0[678]_|^(VALIDACION|CHAIN_STATE|production_status|manifest)\.json$", re.I)
MAX_FEATURES_PAQUETE = 2000  # un GeoJSON con más features es de secciones, no de distritos
_FECHA_ZIP = (2020, 1, 1, 0, 0, 0)


_CLAVES_SECCION = {"CUSEC", "CUSEC_KEY", "section_id", "cusec"}


def es_geojson(ruta: Path) -> bool:
    """``*.geojson`` o ``*.geojson.zip`` (los módulos escriben el GeoJSON comprimido)."""
    return ruta.name.lower().endswith((".geojson", ".geojson.zip"))


def leer_geojson(ruta: Path) -> dict:
    """Lee un ``*.geojson`` o el primer GeoJSON de un ``*.geojson.zip``."""
    if ruta.name.lower().endswith(".zip"):
        import zipfile
        with zipfile.ZipFile(ruta) as z:
            nombre = next(n for n in z.namelist() if n.lower().endswith((".geojson", ".json")) and not n.endswith("/"))
            return json.loads(z.read(nombre))
    return json.loads(ruta.read_bytes())


def _geojson_distrital(ruta: Path) -> bool:
    """GeoJSON de distritos: pocas features y ninguna con clave de sección (la asignación va en la composición)."""
    try:
        fs = leer_geojson(ruta).get("features", [])
        return 0 < len(fs) <= MAX_FEATURES_PAQUETE and not any(_CLAVES_SECCION & set(f.get("properties") or {}) for f in fs)
    except (ValueError, OSError, AttributeError, StopIteration, zipfile.BadZipFile):
        return False


def seleccionar_paquete(base: Path) -> list[Path]:
    """Ficheros del estado que reproducen y verifican lo publicado: GeoJSON distritales, CSV y JSON de M06-M08
    (composición sección→distrito, resúmenes, resultados, reconciliación), VALIDACION, CHAIN_STATE y manifiestos."""
    out = []
    for f in sorted(base.rglob("*")):
        if not f.is_file() or not (f.suffix.lower() in _PAQ_EXT or es_geojson(f)) or not _PAQ_NOMBRE.search(f.name):
            continue
        if es_geojson(f) and not _geojson_distrital(f):
            continue
        out.append(f)
    return out


def empaquetar_minimo(extras: tuple = ()) -> Callable[[dict, Path, Path], Path]:
    """Devuelve empaquetar(a, zip_estado, dir) → ZIP determinista con la selección, los ``extras`` (ficheros o
    directorios locales, p. ej. la auditoría) y MANIFEST_MINIMO.json (sha256 de cada fichero y del estado original)."""
    def _f(a: dict, zip_estado: Path, td: Path) -> Path:
        import zipfile
        ext = td / "estado"
        with zipfile.ZipFile(zip_estado) as z:
            z.extractall(ext)
        ficheros = [(f"estado/{f.relative_to(ext).as_posix()}", f) for f in seleccionar_paquete(ext)]
        for x in extras:
            x = Path(x)
            if x.is_dir():
                ficheros += [(f"extra/{x.name}/{f.relative_to(x).as_posix()}", f) for f in sorted(x.rglob("*")) if f.is_file()]
            elif x.is_file():
                ficheros.append((f"extra/{x.name}", x))
        if not any(es_geojson(Path(r)) for r, _ in ficheros):
            raise ValueError(f"{a['name']}: el paquete mínimo no tendría ningún GeoJSON distrital")
        man = {"schema": PAQUETE_SCHEMA, "artefacto_origen": a["name"], "run_id": str(a.get("run", "")),
               "sha256_estado_original": sha256_fichero(zip_estado),
               "tamano_estado_original": zip_estado.stat().st_size,
               "ficheros": {r: sha256_fichero(f) for r, f in ficheros}}
        destino = td / f"{nombre_paquete(a['name'])}.zip"
        with zipfile.ZipFile(destino, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
            for r, f in sorted(ficheros) + [("MANIFEST_MINIMO.json", None)]:
                info = zipfile.ZipInfo(r, _FECHA_ZIP)
                info.compress_type = zipfile.ZIP_DEFLATED
                datos = f.read_bytes() if f else (json.dumps(man, ensure_ascii=False, indent=1, sort_keys=True) + "\n").encode()
                z.writestr(info, datos)
        return destino
    return _f


# --- Implementaciones reales (GitHub y R2) -------------------------------------------------------

INTENTOS = 6
ESPERA_BASE = 2  # s; espera 2, 4, 8, 16, 32 entre intentos
_dormir = time.sleep  # los tests lo sustituyen


def _transitorio(exc: BaseException) -> bool:
    if isinstance(exc, urllib.error.HTTPError):
        return exc.code >= 500 or exc.code == 429
    return isinstance(exc, (urllib.error.URLError, TimeoutError, ConnectionError, OSError, subprocess.CalledProcessError))


def con_reintentos(fn: Callable, descripcion: str, intentos: int = INTENTOS):
    """Ejecuta fn(); reintenta con espera exponencial los fallos transitorios y registra cada intento."""
    for n in range(1, intentos + 1):
        try:
            return fn()
        except Exception as exc:  # noqa: BLE001
            if not _transitorio(exc) or n == intentos:
                raise
            espera = ESPERA_BASE * 2 ** (n - 1)
            print(f"::warning::{descripcion}: intento {n}/{intentos} falló ({exc}); reintento en {espera}s", flush=True)
            _dormir(espera)


def _gh_json(url: str, token: str):
    def _f():
        req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"})
        with urllib.request.urlopen(req, timeout=120) as r:
            return json.load(r)

    return con_reintentos(_f, f"GET {url}")


def listar_artefactos_gh(repo: str, token: str) -> list[dict]:
    out, pagina = [], 1
    while True:
        datos = _gh_json(f"https://api.github.com/repos/{repo}/actions/artifacts?per_page=100&page={pagina}", token)
        lote = datos.get("artifacts", [])
        out += lote
        if len(lote) < 100:
            return out
        pagina += 1


def descargar_gh(repo: str, token: str):
    class _SinAuthEnRedireccion(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, req, fp, code, msg, headers, newurl):
            nuevo = super().redirect_request(req, fp, code, msg, headers, newurl)
            if nuevo is not None:
                nuevo.headers.pop("Authorization", None)
            return nuevo

    def _una_vez(a: dict, destino: Path) -> None:
        req = urllib.request.Request(
            f"https://api.github.com/repos/{repo}/actions/artifacts/{a['id']}/zip",
            headers={"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"},
        )
        op = urllib.request.build_opener(_SinAuthEnRedireccion)
        with op.open(req, timeout=600) as r, open(destino, "wb") as f:
            while bloque := r.read(1 << 20):
                f.write(bloque)

    def _f(a: dict, destino: Path) -> None:
        con_reintentos(lambda: _una_vez(a, destino), f"descarga artefacto {a['name']}")

    return _f


def r2_cliente(bucket: str, account: str):
    ep = f"https://{account}.r2.cloudflarestorage.com"

    def _sha(k: str) -> Optional[str]:
        p = subprocess.run(
            ["aws", "s3api", "head-object", "--bucket", bucket, "--key", k, "--endpoint-url", ep, "--output", "json"],
            capture_output=True, text=True,
        )
        if p.returncode != 0:
            if re.search(r"404|Not Found|NoSuchKey", p.stderr or ""):
                return None
            raise subprocess.CalledProcessError(p.returncode, "head-object", stderr=p.stderr)
        return (json.loads(p.stdout).get("Metadata") or {}).get("sha256")

    def sha(k: str) -> Optional[str]:
        return con_reintentos(lambda: _sha(k), f"R2 head {k}")

    def _subir(k: str, ruta: Path, h: str, run: Optional[str] = None) -> None:
        meta = f"sha256={h}" + (f",run={run}" if run else "")
        subprocess.run(
            ["aws", "s3", "cp", str(ruta), f"s3://{bucket}/{k}", "--endpoint-url", ep, "--metadata", meta, "--only-show-errors"],
            check=True,
        )

    def subir(k: str, ruta: Path, h: str, run: Optional[str] = None) -> None:
        con_reintentos(lambda: _subir(k, ruta, h, run), f"R2 subida {k}")

    return sha, subir


def r2_cabecera(bucket: str, account: str) -> Callable[[str], Optional[dict]]:
    """cab(k) → {sha256, run, bytes} del objeto (head-object) o None si no existe (404); otro fallo se propaga (T-443, D-198)."""
    ep = f"https://{account}.r2.cloudflarestorage.com"

    def _cab(k: str) -> Optional[dict]:
        p = subprocess.run(
            ["aws", "s3api", "head-object", "--bucket", bucket, "--key", k, "--endpoint-url", ep, "--output", "json"],
            capture_output=True, text=True,
        )
        if p.returncode != 0:
            if re.search(r"\(404\)|NoSuchKey|Not Found", p.stderr or ""):
                return None
            raise subprocess.CalledProcessError(p.returncode, "head-object", stderr=p.stderr)
        j = json.loads(p.stdout)
        m = j.get("Metadata") or {}
        return {"sha256": m.get("sha256"), "run": m.get("run"), "bytes": j.get("ContentLength")}

    return lambda k: con_reintentos(lambda: _cab(k), f"R2 head {k}")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--root-dir", default=str(ROOT))
    ap.add_argument("--caduca-antes", help="solo artefactos que caducan antes de esta fecha (AAAA-MM-DD)")
    ap.add_argument("--max", type=int, help="máximo de copias en esta ejecución")
    ap.add_argument("--simular", action="store_true", help="lista lo que copiaría; no descarga ni sube")
    a = ap.parse_args(argv)
    root = Path(a.root_dir)
    repo, token = os.environ.get("GITHUB_REPOSITORY", ""), os.environ.get("GITHUB_TOKEN", "")
    if not repo or not token:
        print("::error::Faltan GITHUB_REPOSITORY o GITHUB_TOKEN.")
        return 1
    nombres, runs = referencias(root)
    vivos = listar_artefactos_gh(repo, token)
    man = cargar_manifiesto(root / MANIFIESTO)
    if a.simular:
        for x in seleccionar(vivos, nombres, runs):
            print(f"{x.get('expires_at')}  {clave(x)}  {x.get('size_in_bytes')}")
        return 0
    bucket, cuenta = os.environ.get("R2_BUCKET", ""), os.environ.get("R2_ACCOUNT_ID", "")
    if not bucket or not cuenta:
        print("::error::Faltan R2_BUCKET o R2_ACCOUNT_ID.")
        return 1
    sha, subir = r2_cliente(bucket, cuenta)
    res = archivar(vivos, nombres, runs, man, descargar_gh(repo, token), sha, subir, bucket,
                   caduca_antes=a.caduca_antes, maximo=a.max, empaquetar=empaquetar_minimo(),
                   publicado=publicados(root), r2_cab=r2_cabecera(bucket, cuenta))
    cambio = guardar_manifiesto(root / MANIFIESTO, man)
    print(json.dumps({k: (len(v) if k != "errores" else v) for k, v in res.items()}, ensure_ascii=False))
    for p in res["perdidos"]:
        print(f"::warning::Artefacto referenciado ya caducado y sin archivar: {p}")
    for e in res["errores"]:
        print(f"::error::{e}")
    print(f"manifiesto_cambiado={'true' if cambio else 'false'}")
    return 1 if res["errores"] else 0


if __name__ == "__main__":
    sys.exit(main())
