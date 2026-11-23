#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Espejo de solo lectura en R2 de una fuente oficial que solo se alcanza desde un runner de Actions.

PROYECTO: Diputado de Distrito
VERSIÓN: 1.0.0
NOMBRE DE VERSIÓN: Espejo de fuente oficial (D-183, D-188)
FECHA: 2026-11-23
ESTADO: candidato
CAMBIOS: 1.0.0 (T-449): fichero nuevo.
MOTIVO: las autonómicas de Castilla-La Mancha 2023 por municipio solo están en el catálogo de datos.gob.es; la sesión cloud no llega
  (proxy 403) y la URL del portal autonómico devuelve la portada en obras. El runner las baja una vez, mide sha256 y bytes y las deja en
  R2 bajo `fuentes/<organismo>/<año>/` (árbol de D-188) con `manifiesto.json`; la huella pasa después, por PR, al calendario.
ANTERIOR: ninguna (fichero nuevo)
QUÉ HACE: `espejar --territorio aut08 --salida DIR [--subir]`: lee la declaración (`configuracion/espejos_fuentes_oficiales.json`), pide a la
  API de datos.gob.es las distribuciones del conjunto, elige la del año (falla si hay 0 o más de una), la baja, rechaza HTML (portada en
  obras), mide sha256/bytes, baja también el PDF oficial de verificación si responde, vuelca cada hoja de un xlsx a CSV (para el cuadre)
  y escribe `manifiesto.json`. Con `--subir`, nunca sobrescribe: si la clave ya existe con otro sha256 falla (`ESPEJO_HUELLA_DISTINTA`).
USO: python herramientas/espejo_fuente_oficial.py espejar --territorio aut08 --salida "$RUNNER_TEMP/espejo" --subir
"""
from __future__ import annotations

import argparse
import csv
import datetime as _dt
import hashlib
import io
import json
import os
import re
import subprocess
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DECLARACION = ROOT / "configuracion" / "espejos_fuentes_oficiales.json"
UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
NOMBRE_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
FORMATOS = {"xlsx": "xlsx", "csv": "csv", "xls": "xls", "zip": "zip", "json": "json", "pdf": "pdf"}


class ErrorEspejo(RuntimeError):
    def __init__(self, codigo: str, detalle: str):
        super().__init__(f"{codigo}: {detalle}")
        self.codigo = codigo


def declaracion(territorio: str, ruta: Path = DECLARACION) -> dict:
    d = json.loads(ruta.read_text(encoding="utf-8"))["espejos"]
    if territorio not in d:
        raise ErrorEspejo("ESPEJO_SIN_DECLARACION", f"{territorio} no está en {ruta.name}")
    e = d[territorio]
    for campo in ("organismo", "fichero"):
        if not NOMBRE_RE.match(e[campo]):
            raise ErrorEspejo("ESPEJO_NOMBRE_INVALIDO", f"{campo}={e[campo]!r} (D-188: minúsculas y guiones)")
    return e


def clave_r2(organismo: str, anyo: int, nombre: str) -> str:
    """Clave del árbol de D-188: fuentes/<organismo>/<año>/<nombre>; sin códigos de territorio, run ni sha."""
    if not NOMBRE_RE.match(organismo) or not re.match(r"^[a-z0-9-]+(\.[a-z0-9]+)?$", nombre):
        raise ErrorEspejo("ESPEJO_NOMBRE_INVALIDO", f"{organismo}/{nombre}")
    if re.search(r"(^|-)(nac|aut)\d{2}|sha|\d{6,}", nombre):
        raise ErrorEspejo("ESPEJO_NOMBRE_INVALIDO", f"{nombre} lleva código, sha o run (D-188)")
    return f"fuentes/{organismo}/{int(anyo)}/{nombre}"


def _texto(v) -> str:
    """Los literales de la API de datos.gob.es llegan como str, {"_value": …} o lista de ellos (uno por idioma)."""
    if v is None:
        return ""
    if isinstance(v, str):
        return v
    if isinstance(v, dict):
        return _texto(v.get("_value") or v.get("value") or v.get("_about"))
    if isinstance(v, list):
        es = [x for x in v if isinstance(x, dict) and x.get("_lang") == "es"]
        return " ".join(_texto(x) for x in (es or v))
    return str(v)


def distribuciones(api: dict) -> list[dict]:
    items = (api.get("result") or {}).get("items") or []
    salida = []
    for it in items:
        dist = it.get("distribution") or []
        for d in dist if isinstance(dist, list) else [dist]:
            url = _texto(d.get("accessURL") or d.get("downloadURL"))
            if not url:
                continue
            fmt = _texto(d.get("format")).lower()
            salida.append({"url": url.strip(), "titulo": _texto(d.get("title")).strip(), "formato": fmt})
    return salida


def _extension(d: dict) -> str:
    camino = urllib.parse.urlparse(d["url"]).path.lower()
    for ext in FORMATOS:
        if camino.endswith("." + ext):
            return ext
    for ext in FORMATOS:
        if ext in d["formato"].replace("spreadsheetml", "xlsx"):
            return ext
    return ""


def elegir_distribucion(api: dict, anyo: int) -> dict:
    """La única distribución de datos del año (en título o URL), prefiriendo xlsx > csv > xls > zip si hay varias del mismo año."""
    patron = re.compile(rf"(?<!\d){int(anyo)}(?!\d)")
    candidatas = []
    for d in distribuciones(api):
        ext = _extension(d)
        if ext in ("", "pdf"):
            continue
        if patron.search(d["titulo"]) or patron.search(urllib.parse.unquote(d["url"])):
            candidatas.append({**d, "extension": ext})
    if not candidatas:
        raise ErrorEspejo("ESPEJO_SIN_DISTRIBUCION", f"ninguna distribución de datos del año {anyo}")
    orden = ["xlsx", "csv", "xls", "zip", "json"]
    mejor = min(orden.index(c["extension"]) for c in candidatas)
    elegidas = [c for c in candidatas if orden.index(c["extension"]) == mejor]
    if len({c["url"] for c in elegidas}) > 1:
        raise ErrorEspejo("ESPEJO_DISTRIBUCION_AMBIGUA", "; ".join(c["url"] for c in elegidas))
    return elegidas[0]


def es_html(datos: bytes) -> bool:
    cabeza = datos[:512].lstrip().lower()
    return cabeza.startswith(b"<!doctype html") or cabeza.startswith(b"<html") or b"<html" in cabeza[:256]


def comprobar_contenido(datos: bytes, extension: str) -> None:
    if not datos:
        raise ErrorEspejo("ESPEJO_VACIO", "0 bytes")
    if es_html(datos):
        raise ErrorEspejo("ESPEJO_ES_HTML", "la URL devuelve una página web, no el fichero de datos")
    firmas = {"xlsx": b"PK\x03\x04", "zip": b"PK\x03\x04", "xls": b"\xd0\xcf\x11\xe0", "pdf": b"%PDF"}
    if extension in firmas and not datos.startswith(firmas[extension]):
        raise ErrorEspejo("ESPEJO_FORMATO", f"no empieza como un {extension}")


def _get(url: str, intentos: int = 4, abrir=urllib.request.urlopen) -> bytes:
    ultimo: Exception | None = None
    for i in range(intentos):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "*/*"})
            with abrir(req, timeout=120) as r:
                return r.read()
        except Exception as exc:  # noqa: BLE001 - reintento con backoff ante red/5xx
            ultimo = exc
            if i + 1 < intentos:
                time.sleep(2 ** i * 3)
    raise ErrorEspejo("ESPEJO_DESCARGA", f"{url}: {ultimo}")


def sha256(datos: bytes) -> str:
    return hashlib.sha256(datos).hexdigest()


def volcar_xlsx(datos: bytes, destino: Path) -> list[dict]:
    """Cada hoja a CSV (UTF-8, valores tal cual) para versionar el volcado y cuadrar sin openpyxl en la CI."""
    import openpyxl

    libro = openpyxl.load_workbook(io.BytesIO(datos), read_only=True, data_only=True)
    hojas = []
    for i, hoja in enumerate(libro.worksheets, 1):
        ruta = destino / f"hoja-{i}.csv"
        filas = 0
        with open(ruta, "w", encoding="utf-8", newline="") as fh:
            w = csv.writer(fh)
            for fila in hoja.iter_rows(values_only=True):
                w.writerow(["" if v is None else v for v in fila])
                filas += 1
        b = ruta.read_bytes()
        hojas.append({"hoja": hoja.title, "csv": ruta.name, "filas": filas, "sha256": sha256(b), "bytes": len(b)})
    return hojas


def _aws(args: list[str], capturar: bool = False) -> subprocess.CompletedProcess:
    ep = f"https://{os.environ['R2_ACCOUNT_ID']}.r2.cloudflarestorage.com"
    return subprocess.run(["aws", *args, "--endpoint-url", ep], check=False, capture_output=capturar, text=True)


def sha_remoto(clave: str, aws=_aws) -> str | None:
    """sha256 del metadato del objeto, '' si existe sin metadato, None si no existe."""
    r = aws(["s3api", "head-object", "--bucket", os.environ["R2_BUCKET"], "--key", clave], True)
    if r.returncode != 0:
        if "404" in (r.stderr or "") or "Not Found" in (r.stderr or ""):
            return None
        raise ErrorEspejo("ESPEJO_R2", f"head-object {clave}: {(r.stderr or '').strip()[:300]}")
    return (json.loads(r.stdout or "{}").get("Metadata") or {}).get("sha256", "")


def subir(fichero: Path, clave: str, huella: str, aws=_aws) -> str:
    """Solo lectura: no sobrescribe nunca. Devuelve 'subido' o 'ya_estaba'."""
    previo = sha_remoto(clave, aws)
    if previo == huella:
        return "ya_estaba"
    if previo is not None:
        raise ErrorEspejo("ESPEJO_HUELLA_DISTINTA", f"{clave} ya existe con sha256 {previo or '(sin metadato)'} ≠ {huella}")
    r = aws(["s3", "cp", str(fichero), f"s3://{os.environ['R2_BUCKET']}/{clave}", "--only-show-errors",
             "--metadata", f"sha256={huella}"])
    if r.returncode != 0:
        raise ErrorEspejo("ESPEJO_R2", f"no se pudo subir {clave}")
    return "subido"


def espejar(territorio: str, salida: Path, subir_r2: bool, get=_get, aws=_aws, ruta_decl: Path = DECLARACION) -> dict:
    e = declaracion(territorio, ruta_decl)
    salida.mkdir(parents=True, exist_ok=True)
    api = json.loads(get(e["api_url"]).decode("utf-8"))
    dist = elegir_distribucion(api, e["anyo"])
    datos = get(dist["url"])
    comprobar_contenido(datos, dist["extension"])
    nombre = f"{e['fichero']}.{dist['extension']}"
    (salida / nombre).write_bytes(datos)
    piezas = [{"nombre": nombre, "clave": clave_r2(e["organismo"], e["anyo"], nombre), "origen_url": dist["url"],
               "titulo_catalogo": dist["titulo"], "sha256": sha256(datos), "bytes": len(datos), "oficial": True}]
    if dist["extension"] == "xlsx":
        volcado = salida / "volcado"
        volcado.mkdir(exist_ok=True)
        piezas[0]["volcado_csv"] = volcar_xlsx(datos, volcado)
    verif = e.get("verificacion") or {}
    if verif.get("url"):
        try:
            pdf = get(verif["url"], 2)
            comprobar_contenido(pdf, "pdf")
            nombre_pdf = f"{verif['fichero']}.pdf"
            (salida / nombre_pdf).write_bytes(pdf)
            piezas.append({"nombre": nombre_pdf, "clave": clave_r2(e["organismo"], e["anyo"], nombre_pdf),
                           "origen_url": verif["url"], "sha256": sha256(pdf), "bytes": len(pdf), "oficial": True})
        except ErrorEspejo as exc:
            print(f"::warning::Verificación oficial no disponible ({exc}); el cuadre irá contra los escaños oficiales.")
    manifiesto = {
        "schema": "ddd-manifiesto-fuente/1.0",
        "territorio": territorio,
        "eleccion": e["eleccion"],
        "fecha_eleccion": e["fecha"],
        "catalogo": e["dataset_url"],
        "medido": _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "run": os.environ.get("GITHUB_RUN_ID", ""),
        "piezas": piezas,
    }
    (salida / "manifiesto.json").write_text(json.dumps(manifiesto, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if subir_r2:
        if not os.environ.get("R2_BUCKET") or not os.environ.get("R2_ACCOUNT_ID"):
            raise ErrorEspejo("ESPEJO_R2", "faltan R2_BUCKET o R2_ACCOUNT_ID")
        for p in piezas:
            p["r2"] = subir(salida / p["nombre"], p["clave"], p["sha256"], aws)
        if all(p["r2"] == "ya_estaba" for p in piezas):
            return manifiesto  # nada nuevo: el manifiesto de R2 se queda como estaba
        (salida / "manifiesto.json").write_text(json.dumps(manifiesto, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        mb = (salida / "manifiesto.json")
        clave_m = clave_r2(e["organismo"], e["anyo"], "manifiesto.json")
        r = aws(["s3", "cp", str(mb), f"s3://{os.environ['R2_BUCKET']}/{clave_m}", "--only-show-errors",
                 "--metadata", f"sha256={sha256(mb.read_bytes())}"])
        if r.returncode != 0:
            raise ErrorEspejo("ESPEJO_R2", f"no se pudo subir {clave_m}")
    return manifiesto


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("espejar")
    p.add_argument("--territorio", required=True)
    p.add_argument("--salida", required=True, type=Path)
    p.add_argument("--subir", action="store_true")
    a = ap.parse_args(argv)
    try:
        m = espejar(a.territorio, a.salida, a.subir)
    except ErrorEspejo as exc:
        print(f"::error::{exc}", file=sys.stderr)
        return 2
    # El log es la vía para leer la huella desde la sesión cloud (los artefactos no se descargan allí).
    print("ESPEJO_MANIFIESTO " + json.dumps(m, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
