#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Espejo de solo lectura en R2 de una fuente oficial que solo se alcanza desde un runner de Actions.

PROYECTO: Diputado de Distrito
VERSIÓN: 1.1.0
NOMBRE DE VERSIÓN: Espejo de fuente oficial (D-183, D-188)
FECHA: 2026-11-23
ESTADO: candidato
CAMBIOS: 1.1.0 (T-448, D-202): modo «URL directa» para una entrada con `url` (sin `api_url`): baja ese fichero (mismos hosts, redirecciones,
  `max_bytes` y rechazo de HTML), exige `sha256_esperado` y `bytes_esperados` (si no coinciden, ESPEJO_HUELLA_INESPERADA y no se escribe nada) y
  usa la `extension` declarada (la URL del INE acaba en `.csv_bdsc`). Los campos de la elección (`eleccion`, `fecha`, `dataset_url`) pasan a
  opcionales en el manifiesto. Primera entrada: `ine-censo2011-1mun00` (1mun00.csv del Censo 2011 → fuentes/ine/2011/1mun00.csv). El modo
  datos.gob.es (aut08) no cambia.
  1.0.1 (T-449, run 45158272014 rechazado con ESPEJO_ES_HTML sin decir qué URL): cada distribución aporta `downloadURL` antes que
  `accessURL` (en DCAT `accessURL` suele ser una página de aterrizaje); se prueban en orden todas las candidatas del año (xlsx > csv > xls >
  zip > json; dentro de cada una, descarga antes que acceso) hasta la primera que sea un fichero de datos, y el log lleva `ESPEJO_CANDIDATAS`
  y una línea por intento (URL y motivo). Si ninguna vale, el código común (p. ej. `ESPEJO_ES_HTML`) o `ESPEJO_SIN_FICHERO`, con la lista de lo probado. 1.0.0 (T-449): fichero nuevo.
MOTIVO: las autonómicas de Castilla-La Mancha 2023 por municipio solo están en el catálogo de datos.gob.es; la sesión cloud no llega
  (proxy 403) y la URL del portal autonómico devuelve la portada en obras. El runner las baja una vez, mide sha256 y bytes y las deja en
  R2 bajo `fuentes/<organismo>/<año>/` (árbol de D-188) con `manifiesto.json`; la huella pasa después, por PR, al calendario.
ANTERIOR: legacy/herramientas/espejo_fuente_oficial_v1.0.1_20261123.py
QUÉ HACE: `espejar --territorio aut08 --salida DIR` (SIN secretos): lee la declaración (`configuracion/espejos_fuentes_oficiales.json`), pide a la
  API de datos.gob.es las distribuciones del conjunto, elige la del año (falla si hay 0 o más de una), la baja solo por https de los hosts
  exactos declarados (también en cada redirección, como mucho 5) y hasta `max_bytes`, rechaza HTML (portada en obras), mide sha256/bytes,
  baja también el PDF oficial de verificación si responde, vuelca cada hoja de un xlsx a CSV y escribe `manifiesto.json`.
  `subir --territorio aut08 --salida DIR` (con secretos, en otro paso): comprueba cada pieza contra el manifiesto y la sube con
  `put-object --if-none-match '*'` (nunca sobrescribe; misma huella = `ya_estaba`, otra = `ESPEJO_HUELLA_DISTINTA`); el manifiesto va el
  último y con la misma regla: si una pieza falla no queda manifiesto, y el siguiente intento completa lo que falta.
  Clave codificada aquí (fuentes/<organismo>/<año>/<nombre>); T-443 la migra a `rutas_r2.ruta_fuente` cuando entre #977.
USO: python herramientas/espejo_fuente_oficial.py espejar --territorio aut08 --salida "$RUNNER_TEMP/espejo"
     python herramientas/espejo_fuente_oficial.py subir --territorio aut08 --salida "$RUNNER_TEMP/espejo"
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
    """Una entrada por distribución con sus URL en orden de preferencia: `downloadURL` (fichero) antes que `accessURL` (a menudo, portada)."""
    items = (api.get("result") or {}).get("items") or []
    salida = []
    for it in items:
        dist = it.get("distribution") or []
        for d in dist if isinstance(dist, list) else [dist]:
            urls = []
            for campo in ("downloadURL", "accessURL"):
                u = _texto(d.get(campo)).strip()
                if u and u not in urls:
                    urls.append(u)
            if not urls:
                continue
            salida.append({"url": urls[0], "urls": urls, "titulo": _texto(d.get("title")).strip(),
                           "formato": _texto(d.get("format")).lower()})
    return salida


def _extension(d: dict, url: str | None = None) -> str:
    camino = urllib.parse.urlparse(url or d["url"]).path.lower()
    for ext in FORMATOS:
        if camino.endswith("." + ext):
            return ext
    for ext in FORMATOS:
        if ext in d["formato"].replace("spreadsheetml", "xlsx"):
            return ext
    return ""


ORDEN = ["xlsx", "csv", "xls", "zip", "json"]


def candidatas_del_anyo(api: dict, anyo: int) -> list[dict]:
    """Todas las (distribución, URL) de datos del año, en orden de preferencia. Falla si hay dos distribuciones del año con el mismo formato."""
    patron = re.compile(rf"(?<!\d){int(anyo)}(?!\d)")
    por_dist = []
    for d in distribuciones(api):
        if not (patron.search(d["titulo"]) or any(patron.search(urllib.parse.unquote(u)) for u in d["urls"])):
            continue
        ext = _extension(d)
        if ext in ("", "pdf"):
            ext = next((e for e in (_extension(d, u) for u in d["urls"]) if e not in ("", "pdf")), "")
        if ext in ("", "pdf"):
            continue
        por_dist.append({**d, "extension": ext})
    if not por_dist:
        raise ErrorEspejo("ESPEJO_SIN_DISTRIBUCION", f"ninguna distribución de datos del año {anyo}")
    for ext in ORDEN:
        mismas = [d for d in por_dist if d["extension"] == ext]
        if len(mismas) > 1:
            raise ErrorEspejo("ESPEJO_DISTRIBUCION_AMBIGUA", "; ".join(d["urls"][0] for d in mismas))
    por_dist.sort(key=lambda d: ORDEN.index(d["extension"]))
    return [{**d, "url": u} for d in por_dist for u in d["urls"]]


def elegir_distribucion(api: dict, anyo: int) -> dict:
    """La primera candidata del año (ver `candidatas_del_anyo`)."""
    return candidatas_del_anyo(api, anyo)[0]


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


MAX_REDIRECCIONES = 5


def comprobar_url(url: str, hosts: list[str]) -> None:
    u = urllib.parse.urlparse(url)
    if u.scheme != "https" or (u.hostname or "").lower() not in {h.lower() for h in hosts}:
        raise ErrorEspejo("ESPEJO_HOST_NO_PERMITIDO", f"{url} (solo https de {', '.join(hosts)})")


class _Redirecciones(urllib.request.HTTPRedirectHandler):
    def __init__(self, hosts):
        super().__init__()
        self.hosts, self.saltos = hosts, 0

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        self.saltos += 1
        if self.saltos > MAX_REDIRECCIONES:
            raise ErrorEspejo("ESPEJO_REDIRECCIONES", f"más de {MAX_REDIRECCIONES} hacia {newurl}")
        comprobar_url(newurl, self.hosts)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def _abrir(url: str, hosts: list[str]):
    opener = urllib.request.build_opener(_Redirecciones(hosts))
    return opener.open(urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "*/*"}), timeout=120)


def _get(url: str, hosts: list[str], max_bytes: int, intentos: int = 4, abrir=_abrir) -> bytes:
    comprobar_url(url, hosts)
    ultimo: Exception | None = None
    for i in range(intentos):
        try:
            with abrir(url, hosts) as r:
                datos = r.read(max_bytes + 1)
            if len(datos) > max_bytes:
                raise ErrorEspejo("ESPEJO_DEMASIADO_GRANDE", f"{url} pasa de {max_bytes} bytes")
            return datos
        except ErrorEspejo:
            raise
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


def poner_si_no_existe(fichero: Path, clave: str, huella: str, aws=_aws) -> str:
    """Solo lectura: escritura condicional (`If-None-Match: *`), nunca sobrescribe. Devuelve 'subido' o 'ya_estaba'."""
    previo = sha_remoto(clave, aws)
    if previo is None:
        r = aws(["s3api", "put-object", "--bucket", os.environ["R2_BUCKET"], "--key", clave, "--body", str(fichero),
                 "--metadata", f"sha256={huella}", "--if-none-match", "*"], True)
        if r.returncode == 0:
            return "subido"
        if "PreconditionFailed" not in (r.stderr or "") and "412" not in (r.stderr or ""):
            raise ErrorEspejo("ESPEJO_R2", f"put-object {clave}: {(r.stderr or '').strip()[:300]}")
        previo = sha_remoto(clave, aws)  # otro escritor ganó la carrera: se compara con lo que dejó
    if previo == huella:
        return "ya_estaba"
    raise ErrorEspejo("ESPEJO_HUELLA_DISTINTA", f"{clave} ya existe con sha256 {previo or '(sin metadato)'} ≠ {huella}")


def _piezas_clave(m: dict) -> list[tuple[str, str]]:
    return sorted((p["clave"], p["sha256"]) for p in m.get("piezas") or [])


def _directa(e: dict, get, hosts: list[str], tope: int) -> tuple[dict, bytes]:
    """D-202: URL directa con huella esperada; falla cerrado antes de escribir nada si sha256 o bytes no son los declarados."""
    ext = e.get("extension") or ""
    if ext not in FORMATOS or not e.get("sha256_esperado") or not e.get("bytes_esperados"):
        raise ErrorEspejo("ESPEJO_DECLARACION", "la URL directa exige extension, sha256_esperado y bytes_esperados")
    datos = get(e["url"], hosts, tope)
    comprobar_contenido(datos, ext)
    if (sha256(datos), len(datos)) != (e["sha256_esperado"], int(e["bytes_esperados"])):
        raise ErrorEspejo("ESPEJO_HUELLA_INESPERADA", f"{e['url']}: sha256 {sha256(datos)} · {len(datos)} B ≠ "
                                                      f"{e['sha256_esperado']} · {e['bytes_esperados']} B")
    print(f"ESPEJO_ELEGIDA {e['url']}")
    return {"url": e["url"], "titulo": e.get("titulo", ""), "formato": ext, "extension": ext}, datos


def espejar(territorio: str, salida: Path, get=_get, ruta_decl: Path = DECLARACION) -> dict:
    """Bajar, comprobar y medir; sin credenciales ni escritura remota."""
    e = declaracion(territorio, ruta_decl)
    hosts, tope = e["hosts_permitidos"], int(e["max_bytes"])
    if e.get("url") and not e.get("api_url"):
        dist, datos = _directa(e, get, hosts, tope)
    else:
        dist, datos = _por_catalogo(e, get, hosts, tope)
    salida.mkdir(parents=True, exist_ok=True)
    return _escribir(territorio, e, dist, datos, salida, get, hosts, tope)


def _por_catalogo(e: dict, get, hosts: list[str], tope: int) -> tuple[dict, bytes]:
    """T-449: la API de datos.gob.es y la primera candidata del año que sea un fichero de datos."""
    api = json.loads(get(e["api_url"], hosts, tope).decode("utf-8"))
    candidatas = candidatas_del_anyo(api, e["anyo"])
    print("ESPEJO_CANDIDATAS " + json.dumps([{"url": c["url"], "formato": c["formato"], "titulo": c["titulo"]} for c in candidatas],
                                           ensure_ascii=False))
    dist, datos, intentos, codigos = None, b"", [], set()
    for c in candidatas:
        try:
            datos = get(c["url"], hosts, tope)
            comprobar_contenido(datos, c["extension"])
        except ErrorEspejo as exc:
            intentos.append(f"{c['url']} → {exc.codigo}")
            codigos.add(exc.codigo)
            print(f"::warning::ESPEJO_INTENTO {c['url']}: {exc}")
            continue
        dist = c
        print(f"ESPEJO_ELEGIDA {c['url']}")
        break
    if dist is None:
        codigo = codigos.pop() if len(codigos) == 1 else "ESPEJO_SIN_FICHERO"  # el mismo motivo en todas, o «varios»
        raise ErrorEspejo(codigo, "ninguna candidata es un fichero de datos: " + "; ".join(intentos))
    return dist, datos


def _escribir(territorio: str, e: dict, dist: dict, datos: bytes, salida: Path, get, hosts: list[str], tope: int) -> dict:
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
            pdf = get(verif["url"], hosts, tope, 2)
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
        "eleccion": e.get("eleccion", ""),
        "fecha_eleccion": e.get("fecha", ""),
        "catalogo": e.get("dataset_url") or e.get("url", ""),
        "medido": _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "run": os.environ.get("GITHUB_RUN_ID", ""),
        "piezas": piezas,
    }
    (salida / "manifiesto.json").write_text(json.dumps(manifiesto, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return manifiesto


def subir_espejo(territorio: str, salida: Path, aws=_aws, ruta_decl: Path = DECLARACION) -> dict:
    """Subir lo medido por `espejar`: piezas primero y manifiesto el último, todo condicional."""
    if not os.environ.get("R2_BUCKET") or not os.environ.get("R2_ACCOUNT_ID"):
        raise ErrorEspejo("ESPEJO_R2", "faltan R2_BUCKET o R2_ACCOUNT_ID")
    e = declaracion(territorio, ruta_decl)
    prefijo = clave_r2(e["organismo"], e["anyo"], "x")[:-1]
    mf = salida / "manifiesto.json"
    m = json.loads(mf.read_text(encoding="utf-8"))
    if m.get("territorio") != territorio or not m.get("piezas"):
        raise ErrorEspejo("ESPEJO_MANIFIESTO", "manifiesto de otro territorio o sin piezas")
    estado = {}
    for p in m["piezas"]:
        f = salida / p["nombre"]
        if not p["clave"].startswith(prefijo) or p["clave"] != clave_r2(e["organismo"], e["anyo"], p["nombre"]):
            raise ErrorEspejo("ESPEJO_NOMBRE_INVALIDO", f"{p['clave']} fuera de {prefijo}")
        if sha256(f.read_bytes()) != p["sha256"]:
            raise ErrorEspejo("ESPEJO_HUELLA_LOCAL", f"{p['nombre']} no cuadra con el manifiesto")
        estado[p["clave"]] = poner_si_no_existe(f, p["clave"], p["sha256"], aws)
    clave_m = clave_r2(e["organismo"], e["anyo"], "manifiesto.json")
    huella_m = sha256(mf.read_bytes())
    if sha_remoto(clave_m, aws) is None:
        estado[clave_m] = poner_si_no_existe(mf, clave_m, huella_m, aws)
    else:
        import tempfile

        with tempfile.TemporaryDirectory() as td:
            r = aws(["s3", "cp", f"s3://{os.environ['R2_BUCKET']}/{clave_m}", str(Path(td) / "m.json"), "--only-show-errors"])
            if r.returncode != 0:
                raise ErrorEspejo("ESPEJO_R2", f"no se pudo leer {clave_m}")
            remoto = json.loads((Path(td) / "m.json").read_text(encoding="utf-8"))
        if _piezas_clave(remoto) != _piezas_clave(m):
            raise ErrorEspejo("ESPEJO_MANIFIESTO_DISTINTO", f"{clave_m} ya existe con otras piezas")
        estado[clave_m] = "ya_estaba"
    resultado = {"territorio": territorio, "estado": estado,
                 "piezas": [{"clave": p["clave"], "sha256": p["sha256"], "bytes": p["bytes"], "r2": estado[p["clave"]]} for p in m["piezas"]]}
    (salida / "subida.json").write_text(json.dumps(resultado, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return resultado


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    for c in ("espejar", "subir"):
        p = sub.add_parser(c)
        p.add_argument("--territorio", required=True)
        p.add_argument("--salida", required=True, type=Path)
    a = ap.parse_args(argv)
    try:
        if a.cmd == "espejar":
            # El log es la vía para leer la huella desde la sesión cloud (los artefactos no se descargan allí).
            print("ESPEJO_MANIFIESTO " + json.dumps(espejar(a.territorio, a.salida), ensure_ascii=False, sort_keys=True))
        else:
            print("ESPEJO_SUBIDA " + json.dumps(subir_espejo(a.territorio, a.salida), ensure_ascii=False, sort_keys=True))
    except ErrorEspejo as exc:
        print(f"::error::{exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
