#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Rutas del árbol nuevo de R2 (D-188, D-190): un solo sitio donde se componen las claves que se escriben.

PROYECTO: Diputado de Distrito
VERSIÓN: 1.0.0
NOMBRE DE VERSIÓN: Módulo de rutas de R2
FECHA: 2026-11-22
ESTADO: candidato
CAMBIOS: 1.0.0: fichero nuevo (T-443, paso 1 del §c de docs/ESTUDIOS/T435_ESTRUCTURA_R2/DISENO.md).
MOTIVO: cada herramienta componía su clave a su manera (`<territorio>/<run>/…`, `nacNN/…`, `arc-e/paquetes-p10/<sha>.zip`); D-188 fija
  un árbol en español sin códigos, runs, sha ni versiones en la ruta: `fuentes/`, `mapas/` e `interno/`. El run, la huella y el sha256
  van en `manifiesto.json` de la carpeta.
ANTERIOR: ninguna (fichero nuevo)
QUÉ HACE: funciones puras (sin red): `ruta_fuente`, `ruta_paquete_p10`, `ruta_mapa`, `ruta_informe_doble_vuelta`, `ruta_estado`,
  `ruta_almacen_m06`, `ruta_manifiesto`, `manifiesto`; `validar(ruta)` aplica la regla de nombres y `candidatas(nueva, vieja)` da el orden
  de lectura de la transición (nueva primero, vieja de respaldo). Nombres de territorio: `nombre_es` de la tabla maestra
  (configuracion/notacion_territorial.csv, vía ddd_core.territorio_ids), con su ámbito (`nacionales`/`autonomicas`); los
  `congreso350_*` (competición, T-428) van a `interno/competicion/<provincia>/`.
USO: python herramientas/rutas_r2.py validar <ruta>…  ·  python herramientas/rutas_r2.py paquete-p10 <territorio>
"""
from __future__ import annotations

import csv
import re
import sys
import unicodedata
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from ddd_core import territorio_ids as ti  # noqa: E402

CALENDARIO_AUT = ROOT / "configuracion" / "calendario_autonomicas.csv"
RAICES = ("fuentes/", "mapas/", "interno/")
ELECCION_NACIONAL_VIGENTE = "2023-07"
FICHEROS_MAPA = ("manifiesto.json", "mapa.geojson", "composicion.csv", "resultados.zip", "doble-vuelta.zip")
TIPOS_ESTADO = ("audit", "audit-electoral", "minimo-m06", "minimo-m08", "decision")
ORGANISMOS = ("ine", "interior", "xunta", "gobierno-vasco", "crem", "sadei", "observatorio-autonomicas")
CARPETA_ORGANISMO = {"nazioenbehatokia": "gobierno-vasco"}  # el nombre en euskera sale de la ruta (D-188)

_RE_SHA12 = re.compile(r"_[0-9a-f]{12}(?=\.[a-z0-9.]+$|$)")
_RE_RUN = re.compile(r"(?<!\d)\d{10,}(?!\d)")
_RE_HEX = re.compile(r"(?<![0-9a-f])[0-9a-f]{12,}(?![0-9a-f])")
_RE_CODIGO = re.compile(r"(?<![a-z0-9])(nac|aut)\d\d(?![0-9])")
_RE_VERSION = re.compile(r"(?<![a-z0-9])v\d+(\.\d+)+")
_RE_CARPETA = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
# Excepción documentada: el almacén M06 conserva el nombre de asset de los releases (su origen) hasta que la regeneración lo sustituya (T-416).
EXCEPCION_NOMBRE = ("interno/almacen-m06/",)


class RutaInvalida(ValueError):
    pass


def slug(texto: str) -> str:
    """«Santa Cruz de Tenerife» → `santa-cruz-de-tenerife`; «La Coruña» → `la-coruna`; «Castilla-La Mancha» → `castilla-la-mancha`."""
    s = unicodedata.normalize("NFKD", str(texto)).encode("ascii", "ignore").decode("ascii").lower()
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")


def territorio_r2(tid: str) -> tuple[str, str]:
    """(ámbito de carpeta, nombre) de un id viejo, nuevo o código: `nacionales`/`autonomicas` o `competicion` para los `congreso350_*`."""
    s = str(tid).strip()
    if s.startswith(ti.PREFIJO_350_LEGACY):
        return "competicion", slug(s[len(ti.PREFIJO_350_LEGACY):].replace("_", " "))
    t = ti.territorio(s)
    return ("nacionales" if t.ambito == "NAC" else "autonomicas"), slug(t.nombre_es)


@lru_cache(maxsize=1)
def _anios_autonomica() -> dict[str, str]:
    filas = [l for l in CALENDARIO_AUT.read_text(encoding="utf-8").splitlines() if l and not l.startswith("#")]
    return {r["comunidad"].strip(): r["mes"].strip()[:4] for r in csv.DictReader(filas) if r.get("vigente", "").strip() == "si"}


def anio_autonomica(tid: str) -> str:
    """Año de la autonómica vigente (`vigente=si` en calendario_autonomicas.csv). Sin vigente (Ceuta, Melilla): RutaInvalida."""
    t = ti.resolver_id(tid)
    a = _anios_autonomica().get(t)
    if not a:
        raise RutaInvalida(f"{tid}: sin autonómica vigente en {CALENDARIO_AUT.name}; año por fijar (CRUCE.md, hallazgo 5)")
    return a


def etiqueta_eleccion(eleccion: str) -> str:
    """`2023-07` → `congreso-2023`; las dos de 2019 conservan el mes (`congreso-2019-11`)."""
    e = str(eleccion).strip()
    if not re.fullmatch(r"\d{4}(-\d{2})?", e):
        raise RutaInvalida(f"elección mal formada: {eleccion!r} (AAAA o AAAA-MM)")
    return f"congreso-{e if e.startswith('2019') else e[:4]}"


def sin_sha12(nombre: str) -> str:
    """Quita el sufijo `_<sha12>` del nombre original (`seccionado_2021_ab12cd34ef56.zip` → `seccionado_2021.zip`)."""
    return _RE_SHA12.sub("", nombre)


def ruta_fuente(organismo: str, anio: str | None, nombre: str) -> str:
    """`fuentes/<organismo>/<año>/<nombre original sin sha12>`; el sha12 y el nombre original van en el manifiesto de la carpeta."""
    org = CARPETA_ORGANISMO.get(organismo, organismo)
    if org not in ORGANISMOS:
        raise RutaInvalida(f"organismo no previsto: {organismo!r} ({', '.join(ORGANISMOS)})")
    if anio is None:  # Gobierno Vasco: la época va en la ruta original (data/<época>/…), como en CRUCE_claves.csv
        return _ok(f"fuentes/{org}/{sin_sha12(nombre).strip('/')}")
    if not re.fullmatch(r"\d{4}", str(anio)):
        raise RutaInvalida(f"año de fuente mal formado: {anio!r}")
    return _ok(f"fuentes/{org}/{anio}/{sin_sha12(nombre).strip('/')}")


def carpeta_territorio(raiz: str, tid: str) -> str:
    amb, nombre = territorio_r2(tid)
    if amb == "competicion":
        return f"interno/competicion/{nombre}"
    return f"{raiz}/{amb}/{nombre}"


def ruta_paquete_p10(tid: str) -> str:
    """Paquete P10 de la fuente del territorio: `fuentes/por-territorio/<ámbito>/<territorio>/paquete.zip` (D-190); su package_sha256 va
    en el manifiesto de la carpeta. Los `congreso350_*` van a `interno/competicion/<provincia>/paquete.zip` (no son producto, T-428)."""
    return _ok(f"{carpeta_territorio('fuentes/por-territorio', tid)}/paquete.zip")


def carpeta_mapa(tid: str, eleccion: str | None = None) -> str:
    """Nacional vigente: `mapas/nacionales/congreso-2023/<provincia>`; histórica: `mapas/historicos/congreso-<e>/<provincia>`;
    autonómica: `mapas/autonomicas/<comunidad>-<año>` (un mapa por comunidad, CRUCE_claves.csv)."""
    amb, nombre = territorio_r2(tid)
    if amb == "competicion":
        raise RutaInvalida(f"{tid}: la competición no tiene carpeta de mapa (va a interno/competicion/)")
    if amb == "autonomicas":
        return f"mapas/autonomicas/{nombre}-{anio_autonomica(tid)}"
    e = eleccion or ELECCION_NACIONAL_VIGENTE
    grupo = "nacionales" if etiqueta_eleccion(e) == etiqueta_eleccion(ELECCION_NACIONAL_VIGENTE) else "historicos"
    return f"mapas/{grupo}/{etiqueta_eleccion(e)}/{nombre}"


def ruta_mapa(tid: str, fichero: str, eleccion: str | None = None) -> str:
    if fichero not in FICHEROS_MAPA:
        raise RutaInvalida(f"fichero de mapa no previsto: {fichero!r} ({', '.join(FICHEROS_MAPA)})")
    return _ok(f"{carpeta_mapa(tid, eleccion)}/{fichero}")


def ruta_informe_doble_vuelta(ambito: str, eleccion: str | None = None) -> str:
    """Informe del P75: `mapas/nacionales/congreso-2023/informe-doble-vuelta.json` o `mapas/autonomicas/informe-doble-vuelta.json`."""
    if str(ambito).lower() in ("aut", "autonomicas"):
        return _ok("mapas/autonomicas/informe-doble-vuelta.json")
    return _ok(f"mapas/nacionales/{etiqueta_eleccion(eleccion or ELECCION_NACIONAL_VIGENTE)}/informe-doble-vuelta.json")


def tipo_artefacto(nombre: str) -> str:
    """`ddd-minimo-<run>-M08` → `minimo-m08`; `ddd-audit-electoral-<run>` → `audit-electoral`; `ddd-state-<run>-M06` → `minimo-m06`
    (el archivista sube el paquete mínimo del estado). Otro nombre: RutaInvalida."""
    n = re.sub(r"\.zip$", "", str(nombre))
    m = re.fullmatch(r"ddd-(minimo|state)-\d+-(M0\d)(?:-.+)?", n)
    if m:
        tipo = f"minimo-{m.group(2).lower()}"
    else:
        m = re.fullmatch(r"ddd-(audit-electoral|audit|decision)-\d+(?:-.+)?", n)
        if not m:
            raise RutaInvalida(f"artefacto sin tipo conocido: {nombre!r}")
        tipo = m.group(1)
    if tipo not in TIPOS_ESTADO:
        raise RutaInvalida(f"tipo no previsto: {tipo!r} ({', '.join(TIPOS_ESTADO)})")
    return tipo


def ruta_estado(tid: str, nombre_artefacto: str) -> str:
    """Último estado/auditoría de un territorio (solo la vigente): `interno/estados/<ámbito>/<territorio>/<tipo>.zip`;
    competición: `interno/competicion/<provincia>/<tipo>.zip`. El run va en el manifiesto de la carpeta."""
    return _ok(f"{carpeta_territorio('interno/estados', tid)}/{tipo_artefacto(nombre_artefacto)}.zip")


def ruta_almacen_m06(asset: str) -> str:
    """Almacén M06 heredado de los releases (T-302): `interno/almacen-m06/<asset>` sin sha12 (excepción de nombre, EXCEPCION_NOMBRE)."""
    return _ok(f"interno/almacen-m06/{sin_sha12(asset)}")


def ruta_manifiesto(ruta: str) -> str:
    """`manifiesto.json` de la carpeta que contiene `ruta`."""
    return _ok(f"{ruta.rsplit('/', 1)[0]}/manifiesto.json")


def manifiesto(ficheros: dict[str, dict], *, run: str | None = None, huella: str | None = None, fecha: str = "",
               extra: dict | None = None) -> dict:
    """Contenido de `manifiesto.json`: run, huella (motor/contrato o package_sha256), fecha y sha256/bytes de cada fichero de la carpeta."""
    return {"schema": "ddd.r2-manifiesto/1.0", "run": run, "huella": huella, "fecha": fecha,
            "ficheros": {k: {"sha256": v.get("sha256"), "bytes": v.get("bytes"), **{x: y for x, y in v.items() if x not in ("sha256", "bytes")}}
                         for k, v in sorted(ficheros.items())}, **(extra or {})}


def es_nueva(ruta: str) -> bool:
    return str(ruta).startswith(RAICES)


def validar(ruta: str) -> list[str]:
    """Problemas de `ruta` frente a la regla de nombres (D-188 §a); lista vacía si vale."""
    r = str(ruta)
    p: list[str] = []
    if not es_nueva(r):
        return [f"fuera del árbol nuevo ({', '.join(RAICES)})"]
    partes = r.split("/")
    carpetas, fichero = partes[:-1], partes[-1]
    if r.startswith("fuentes/") and len(partes) > 3 and partes[1] != "por-territorio":
        carpetas = partes[:3]  # fuentes/<organismo>/<año>/: debajo conserva la estructura original (gobierno-vasco/data/…)
        fichero = "/".join(partes[3:])
    for c in carpetas:
        if not _RE_CARPETA.match(c):
            p.append(f"carpeta {c!r}: solo minúsculas, cifras y guiones, sin tildes ni «ñ»")
    exento = r.startswith(EXCEPCION_NOMBRE)
    for parte in [*carpetas, *([] if exento else [fichero])]:
        low = parte.lower()
        if _RE_CODIGO.search(low):
            p.append(f"{parte!r}: código de territorio (nacNN/autNN) prohibido")
        if "congreso_" in low or "congreso350" in low:
            p.append(f"{parte!r}: id antiguo de territorio prohibido")
        if _RE_RUN.search(low):
            p.append(f"{parte!r}: id de run prohibido")
        if _RE_HEX.search(low) or "sha" in low.split("-") or "sha" in re.split(r"[_.\-]", low):
            p.append(f"{parte!r}: sha prohibido")
        if _RE_VERSION.search(low):
            p.append(f"{parte!r}: versión prohibida")
    if not fichero:
        p.append("sin nombre de fichero")
    return p


def _ok(ruta: str) -> str:
    problemas = validar(ruta)
    if problemas:
        raise RutaInvalida(f"{ruta}: " + "; ".join(problemas))
    return ruta


def candidatas(nueva: str | None, vieja: str | None) -> list[str]:
    """Orden de lectura en la transición (D-188 §c paso 2): la nueva primero, la vieja de respaldo; sin repetir ni vacías."""
    out: list[str] = []
    for k in (nueva, vieja):
        if k and k not in out:
            out.append(k)
    return out


def main(argv: list[str] | None = None) -> int:
    a = list(sys.argv[1:] if argv is None else argv)
    if len(a) >= 2 and a[0] == "validar":
        mal = 0
        for r in a[1:]:
            pr = validar(r)
            print(f"{'OK ' if not pr else 'MAL'} {r}" + ("" if not pr else "  · " + "; ".join(pr)))
            mal += bool(pr)
        return 1 if mal else 0
    if len(a) == 2 and a[0] == "paquete-p10":
        print(ruta_paquete_p10(a[1]))
        return 0
    print(__doc__.splitlines()[-1].strip(), file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
