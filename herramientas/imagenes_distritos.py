#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Imagen de cada distrito del Congreso: P18 de Wikidata del municipio que da nombre al distrito, con licencia comprobada en Commons.

PROYECTO: Diputado de Distrito
VERSIÓN: 1.0.0
NOMBRE DE VERSIÓN: Imágenes de distritos (T-462, diseño T-458 §3.1)
FECHA: 2026-11-26
ESTADO: candidato
CAMBIOS: 1.0.0: fichero nuevo.
MOTIVO: la ventana emergente del mapa V4 lleva una imagen por distrito (T-458 §3.1, aprobado 25-11). 407 distritos, 295 municipios.
  Wikidata y Commons no se alcanzan desde la nube: la descarga la hace un runner (P10, tipo «Imágenes de distritos»).
ANTERIOR: ninguna (fichero nuevo)
QUÉ HACE:
  `municipios`: lista (sin red) los municipios de `datos/distritos/nombres_congreso_*.csv` (`municipio_principal_codigo`) y los distritos de cada uno.
  `descargar --salida DIR` (solo lectura, sin secretos): por código INE busca el elemento de Wikidata (P772) y su imagen P18 (rango no
    desaprobado); pide a Commons la licencia (extmetadata); acepta solo CC0 / dominio público (sin atribución), CC BY y CC BY-SA
    (con atribución); sin P18 o con otra licencia, el municipio queda SIN imagen (no se rellena con otra). Baja la miniatura de 800 px,
    la pasa a WebP y escribe `DIR/img/<código INE>.webp`, `DIR/catalogo.json` (autor como texto, licencia, origen, sha1 de Commons,
    sha256 del WebP, cambios) y `DIR/hoja_contactos.html` (todas las imágenes con su licencia; el propietario descarta antes de publicar).
    Sale con 3 si alguna descarga falló por red (la hoja se escribe igualmente).
  `hoja --salida DIR`: regenera la hoja desde el catálogo.
  `subir --salida DIR` (con secretos de R2, otro paso): sube a `interno/imagenes-distritos/` (prefijo propio; nunca `fuentes/` ni `mapas/`, D-198):
    comprueba cada WebP contra el catálogo, `head-object` antes de subir y nunca pisa un run mayor (metadatos `sha256` y `run`); el
    catálogo y el manifiesto van los últimos. La promoción a `mapas/` es de P40, tras la aprobación de la hoja.
USO: python herramientas/imagenes_distritos.py descargar --salida "$RUNNER_TEMP/imagenes"
     python herramientas/imagenes_distritos.py subir --salida "$RUNNER_TEMP/imagenes"
"""
from __future__ import annotations

import argparse
import csv
import datetime as _dt
import hashlib
import html
import io
import json
import os
import re
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIR_NOMBRES = ROOT / "datos" / "distritos"
PREFIJO_R2 = "interno/imagenes-distritos"
ANCHO = 800
CALIDAD_WEBP = 80
TOPE_BYTES_DESCARGA = 30_000_000
HOSTS = {
    "query.wikidata.org": "sparql",
    "commons.wikimedia.org": "api",
    "upload.wikimedia.org": "imagen",
}
# Cliente genérico: sin datos del proyecto ni de personas.
USER_AGENT = "imagenes-distritos/1.0 (cliente de solo lectura)"
LICENCIAS = ("CC0 / dominio público", "CC BY", "CC BY-SA")  # orden de preferencia (0 = sin atribución)
MIMES = {"image/jpeg", "image/png", "image/webp", "image/tiff", "image/svg+xml", "image/gif"}


class ErrorImagenes(RuntimeError):
    def __init__(self, codigo: str, detalle: str):
        super().__init__(f"{codigo}: {detalle}")
        self.codigo = codigo


# ── Municipios y distritos (sin red) ────────────────────────────────────────────────────────────
def leer_distritos(directorio: Path = DIR_NOMBRES) -> tuple[list[dict], dict[str, str]]:
    """(distritos, {código INE: nombre}) a partir de `nombres_congreso_*.csv`."""
    distritos, municipios = [], {}
    for f in sorted(directorio.glob("nombres_congreso_*.csv")):
        with f.open(encoding="utf-8", newline="") as fh:
            for r in csv.DictReader(fh):
                cod = (r.get("municipio_principal_codigo") or "").strip()
                if not re.fullmatch(r"\d{5}", cod):
                    raise ErrorImagenes("IMG_CODIGO_INE", f"{f.name}: código «{cod}» no es de 5 cifras")
                distritos.append({"territorio": r["territorio"], "district_id": int(r["district_id"]), "municipio_codigo": cod})
                municipios.setdefault(cod, r["municipio_principal"])
    if not distritos:
        raise ErrorImagenes("IMG_SIN_DISTRITOS", f"sin nombres_congreso_*.csv en {directorio}")
    return distritos, municipios


# ── Red ─────────────────────────────────────────────────────────────────────────────────────────
def _abrir(url: str, datos: bytes | None = None, tope: int = TOPE_BYTES_DESCARGA, intentos: int = 5) -> bytes:
    p = urllib.parse.urlsplit(url)
    if p.scheme != "https" or p.hostname not in HOSTS:
        raise ErrorImagenes("IMG_HOST", f"host no permitido: {url}")
    espera = 2.0
    for n in range(intentos):
        req = urllib.request.Request(url, data=datos, headers={
            "User-Agent": USER_AGENT, "Accept": "application/json, image/*;q=0.9, */*;q=0.1",
            **({"Content-Type": "application/x-www-form-urlencoded"} if datos is not None else {})})
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                if urllib.parse.urlsplit(r.geturl()).hostname not in HOSTS:
                    raise ErrorImagenes("IMG_REDIRECCION", f"redirección fuera de los hosts permitidos: {r.geturl()}")
                cuerpo = r.read(tope + 1)
            if len(cuerpo) > tope:
                raise ErrorImagenes("IMG_TOPE", f"{url}: más de {tope} bytes")
            return cuerpo
        except urllib.error.HTTPError as e:
            if e.code in (429, 500, 502, 503, 504) and n < intentos - 1:
                time.sleep(min(float(e.headers.get("Retry-After") or espera), 60))
                espera *= 2
                continue
            raise ErrorImagenes("IMG_HTTP", f"{e.code} en {url}") from e
        except (urllib.error.URLError, TimeoutError, ConnectionError) as e:
            if n < intentos - 1:
                time.sleep(espera)
                espera *= 2
                continue
            raise ErrorImagenes("IMG_RED", f"{url}: {e}") from e
    raise ErrorImagenes("IMG_RED", url)


# ── Wikidata ────────────────────────────────────────────────────────────────────────────────────
def consulta_sparql(codigos: list[str]) -> str:
    valores = " ".join(f'"{c}"' for c in codigos)
    return ("SELECT ?code ?item ?img ?rank WHERE { VALUES ?code { " + valores + " } ?item wdt:P772 ?code . "
            "OPTIONAL { ?item p:P18 ?st . ?st ps:P18 ?img . ?st wikibase:rank ?rank } }")


def nombre_fichero(url_img: str) -> str:
    """`http://commons.wikimedia.org/wiki/Special:FilePath/Foo%20bar.jpg` → `Foo bar.jpg`."""
    return urllib.parse.unquote(urllib.parse.urlsplit(url_img).path.rsplit("/", 1)[-1]).replace("_", " ")


def elegir_imagenes(filas: list[dict]) -> dict[str, dict]:
    """{código: {item, fichero} | {item, fichero: None}}. P18 de rango preferente antes que normal; el desaprobado se ignora."""
    por_codigo: dict[str, list[dict]] = {}
    for f in filas:
        por_codigo.setdefault(f["code"]["value"], []).append(f)
    salida = {}
    for cod, fs in por_codigo.items():
        cand = []
        for f in fs:
            if "img" not in f:
                continue
            rango = f.get("rank", {}).get("value", "").rsplit("#", 1)[-1]
            if rango == "DeprecatedRank":
                continue
            cand.append((0 if rango == "PreferredRank" else 1, f["item"]["value"], nombre_fichero(f["img"]["value"])))
        items = sorted({f["item"]["value"] for f in fs})
        qid = (sorted(cand)[0][1] if cand else items[0]).rsplit("/", 1)[-1]
        salida[cod] = {"qid": qid, "fichero": sorted(cand)[0][2] if cand else None}
    return salida


def wikidata(codigos: list[str], abrir=_abrir) -> dict[str, dict]:
    cuerpo = urllib.parse.urlencode({"query": consulta_sparql(codigos), "format": "json"}).encode()
    r = json.loads(abrir("https://query.wikidata.org/sparql", cuerpo))
    return elegir_imagenes(r["results"]["bindings"])


# ── Commons ─────────────────────────────────────────────────────────────────────────────────────
class _Texto(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.t: list[str] = []

    def handle_data(self, d):
        self.t.append(d)


def texto_plano(h: str) -> str:
    """Solo texto: el HTML de los metadatos de Commons no se conserva (T-325: un `<img onerror>` en el autor)."""
    p = _Texto()
    p.feed(h or "")
    p.close()
    return re.sub(r"\s+", " ", "".join(p.t)).strip()[:200]


def clasificar_licencia(meta: dict) -> str | None:
    """«CC0 / dominio público», «CC BY», «CC BY-SA» o None (licencia no permitida)."""
    def v(k):
        return (meta.get(k) or {}).get("value", "")
    if v("NonFree").lower() in ("true", "1"):
        return None
    corta = re.sub(r"\s+", " ", v("LicenseShortName").strip().upper().replace("_", " "))
    if re.match(r"^(CC0|CC[- ]ZERO|PUBLIC DOMAIN|PD)\b", corta) or corta.startswith("DOMINIO PÚBLICO"):
        return "CC0 / dominio público"
    if re.match(r"^CC[- ]BY[- ]SA\b", corta):
        return "CC BY-SA"
    if re.match(r"^CC[- ]BY\b(?![- ](NC|ND))", corta):
        return "CC BY"
    return None


def commons(ficheros: list[str], abrir=_abrir) -> dict[str, dict]:
    """{título sin «File:»: imageinfo} de hasta 50 ficheros por petición."""
    salida: dict[str, dict] = {}
    for i in range(0, len(ficheros), 50):
        lote = ficheros[i:i + 50]
        q = urllib.parse.urlencode({
            "action": "query", "format": "json", "formatversion": "2", "redirects": "1", "prop": "imageinfo",
            "iiprop": "url|extmetadata|sha1|size|mime", "iiurlwidth": str(ANCHO),
            "titles": "|".join("File:" + f for f in lote)})
        r = json.loads(abrir("https://commons.wikimedia.org/w/api.php?" + q))["query"]
        alias = {}
        for lista in (r.get("normalized", []), r.get("redirects", [])):
            for x in lista:
                alias[x["from"]] = x["to"]
        for f in lote:
            t = "File:" + f
            for _ in range(3):
                t = alias.get(t, t)
            pag = next((p for p in r["pages"] if p.get("title") == t and p.get("imageinfo")), None)
            if pag:
                salida[f] = pag["imageinfo"][0] | {"titulo_final": pag["title"][5:]}
    return salida


def ficha(info: dict) -> dict | str:
    """Datos de catálogo de una imageninfo, o el motivo de rechazo (cadena)."""
    meta = info.get("extmetadata") or {}
    lic = clasificar_licencia(meta)
    if lic is None:
        corta = (meta.get("LicenseShortName") or {}).get("value", "") or "sin licencia"
        return f"licencia no permitida: {texto_plano(corta)[:60]}"
    if info.get("mime") not in MIMES:
        return f"tipo no admitido: {info.get('mime')}"
    url = info.get("thumburl") or info.get("url")
    return {
        "licencia": lic,
        "licencia_nombre": texto_plano((meta.get("LicenseShortName") or {}).get("value", "")),
        "licencia_url": (meta.get("LicenseUrl") or {}).get("value", ""),
        "autor": texto_plano((meta.get("Artist") or {}).get("value", "")) or texto_plano((meta.get("Credit") or {}).get("value", "")),
        "titulo_commons": info["titulo_final"],
        "origen_url": info.get("descriptionurl", ""),
        "sha1_original_commons": info.get("sha1", ""),
        "atribucion_obligatoria": lic != LICENCIAS[0],
        "url_imagen": url,
    }


# ── Imagen ──────────────────────────────────────────────────────────────────────────────────────
def a_webp(datos: bytes) -> tuple[bytes, int, int, list[str]]:
    from PIL import Image

    im = Image.open(io.BytesIO(datos))
    cambios = ["recomprimida (WebP)"]
    if im.mode in ("RGBA", "LA", "P"):
        im = im.convert("RGBA")
        fondo = Image.new("RGB", im.size, (255, 255, 255))
        fondo.paste(im, mask=im.split()[-1])
        im = fondo
        cambios.append("transparencia sobre fondo blanco")
    else:
        im = im.convert("RGB")
    if im.width > ANCHO:
        im = im.resize((ANCHO, round(im.height * ANCHO / im.width)), Image.LANCZOS)
        cambios.append(f"reescalada a {ANCHO} px de ancho")
    b = io.BytesIO()
    im.save(b, "WEBP", quality=CALIDAD_WEBP, method=6)
    return b.getvalue(), im.width, im.height, cambios


def sha256(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


# ── Descarga ────────────────────────────────────────────────────────────────────────────────────
def descargar(salida: Path, abrir=_abrir, directorio: Path = DIR_NOMBRES, limite: int | None = None, pausa: float = 0.3) -> dict:
    distritos, municipios = leer_distritos(directorio)
    codigos = sorted(municipios)[:limite]
    (salida / "img").mkdir(parents=True, exist_ok=True)
    wd = wikidata(codigos, abrir)
    pedidos = sorted({wd[c]["fichero"] for c in codigos if c in wd and wd[c]["fichero"]})
    info = commons(pedidos, abrir)
    imagenes, sin, errores = [], [], 0
    for c in codigos:
        w = wd.get(c)
        base = {"municipio_codigo": c, "municipio": municipios[c]}
        if not w:
            sin.append(base | {"motivo": "sin elemento de Wikidata con ese código INE (P772)"})
            continue
        if not w["fichero"]:
            sin.append(base | {"qid": w["qid"], "motivo": "sin imagen P18 en Wikidata"})
            continue
        i = info.get(w["fichero"])
        f = ficha(i) if i else "el fichero no existe en Commons"
        if isinstance(f, str):
            sin.append(base | {"qid": w["qid"], "titulo_commons": w["fichero"], "motivo": f})
            continue
        try:
            time.sleep(pausa)
            webp, ancho, alto, cambios = a_webp(abrir(f.pop("url_imagen")))
        except (ErrorImagenes, OSError, ValueError) as e:
            errores += 1
            sin.append(base | {"qid": w["qid"], "titulo_commons": w["fichero"], "motivo": f"ERROR_DESCARGA: {e}"[:200]})
            continue
        (salida / "img" / f"{c}.webp").write_bytes(webp)
        imagenes.append(base | {"qid": w["qid"], "archivo": f"img/{c}.webp", "ancho": ancho, "alto": alto, "bytes": len(webp),
                                "sha256": sha256(webp), **f, "cambios": cambios})
    cat = {
        "version": "1.0.0", "estado": "candidato", "tarea": "T-462", "anterior": "ninguna (fichero nuevo)",
        "generado": _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "nota": "Imagen principal (P18 de Wikidata) del municipio que da nombre al distrito; WebP de 800 px de ancho. Solo CC0 / dominio público, CC BY y CC BY-SA.",
        "licencias_permitidas": list(LICENCIAS),
        "totales": {"distritos": len(distritos), "municipios": len(codigos), "con_imagen": len(imagenes), "sin_imagen": len(sin),
                    "errores_descarga": errores, "bytes": sum(x["bytes"] for x in imagenes)},
        "imagenes": imagenes, "sin_imagen": sin,
        "distritos": [d for d in distritos if d["municipio_codigo"] in set(codigos)],
    }
    (salida / "catalogo.json").write_text(json.dumps(cat, ensure_ascii=False, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    hoja(salida)
    return cat


# ── Hoja de contactos ───────────────────────────────────────────────────────────────────────────
def hoja(salida: Path) -> Path:
    cat = json.loads((salida / "catalogo.json").read_text(encoding="utf-8"))
    e = html.escape
    uso: dict[str, list[str]] = {}
    for d in cat["distritos"]:
        uso.setdefault(d["municipio_codigo"], []).append(f"{d['territorio'].removeprefix('congreso_')} {d['district_id']}")
    t = cat["totales"]
    out = [
        "<!doctype html><html lang='es'><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'>",
        "<title>Hoja de contactos de imágenes de distritos</title>",
        "<style>body{font:15px system-ui,sans-serif;margin:16px;background:#fff;color:#111}h1{font-size:1.3em}"
        ".g{display:grid;grid-template-columns:repeat(auto-fill,minmax(240px,1fr));gap:12px}"
        ".c{border:1px solid #bbb;border-radius:6px;padding:8px;font-size:13px}.c img{width:100%;height:auto;display:block;margin-bottom:6px;background:#eee}"
        ".c.x{background:#fde8e8}.l{font-weight:700}table{border-collapse:collapse}td,th{border:1px solid #bbb;padding:3px 6px;font-size:13px;text-align:left}"
        "#d{width:100%;min-height:3em}</style>",
        "<h1>Imágenes de distritos del Congreso — hoja de contactos (T-462)</h1>",
        f"<p>{t['con_imagen']} imágenes para {t['municipios']} municipios ({t['distritos']} distritos), {t['bytes'] / 1e6:.1f} MB en WebP. "
        f"{t['sin_imagen']} municipios sin imagen. Marca «descartar» en las que no quieras; la lista de abajo se rellena sola.</p>",
        "<p>Descartadas (códigos INE): <textarea id='d' readonly></textarea></p>",
    ]
    for lic in LICENCIAS:
        grupo = [i for i in cat["imagenes"] if i["licencia"] == lic]
        out.append(f"<h2>{e(lic)} ({len(grupo)}){'' if lic == LICENCIAS[0] else ' — con atribución'}</h2><div class='g'>")
        for i in grupo:
            dist = uso.get(i["municipio_codigo"], [])
            out.append(
                "<div class='c'>"
                f"<img loading='lazy' src='{e(i['archivo'])}' alt='{e(i['municipio'])}'>"
                f"<div><b>{e(i['municipio'])}</b> ({e(i['municipio_codigo'])}) · {len(dist)} distrito(s): {e(', '.join(dist))}</div>"
                f"<div class='l'>{e(i['licencia_nombre'] or i['licencia'])}</div>"
                f"<div>Autor: {e(i['autor'] or '(no consta)')}</div>"
                f"<div><a href='{e(i['origen_url'])}' rel='noopener'>{e(i['titulo_commons'])}</a>"
                + (f" · <a href='{e(i['licencia_url'])}' rel='noopener'>licencia</a>" if i["licencia_url"] else "")
                + f"</div><label><input type='checkbox' data-c='{e(i['municipio_codigo'])}'> descartar</label></div>")
        out.append("</div>")
    out.append(f"<h2>Sin imagen ({len(cat['sin_imagen'])})</h2><table><tr><th>Código</th><th>Municipio</th><th>Distritos</th><th>Motivo</th></tr>")
    for s in cat["sin_imagen"]:
        out.append(f"<tr><td>{e(s['municipio_codigo'])}</td><td>{e(s['municipio'])}</td><td>{len(uso.get(s['municipio_codigo'], []))}</td><td>{e(s['motivo'])}</td></tr>")
    out.append("</table><script>"
               "var d=document.getElementById('d');function f(){d.value=[].slice.call(document.querySelectorAll('input[data-c]:checked')).map(function(x){return x.getAttribute('data-c')}).join(', ')}"
               "document.addEventListener('change',f)</script></html>")
    ruta = salida / "hoja_contactos.html"
    ruta.write_text("\n".join(out) + "\n", encoding="utf-8")
    return ruta


# ── Subida a R2 ─────────────────────────────────────────────────────────────────────────────────
def _aws(args: list[str], capturar: bool = False) -> subprocess.CompletedProcess:
    ep = f"https://{os.environ['R2_ACCOUNT_ID']}.r2.cloudflarestorage.com"
    return subprocess.run(["aws", *args, "--endpoint-url", ep], check=False, capture_output=capturar, text=True)


def _cabeza(clave: str, aws) -> dict | None:
    r = aws(["s3api", "head-object", "--bucket", os.environ["R2_BUCKET"], "--key", clave], True)
    if r.returncode != 0:
        if "404" in (r.stderr or "") or "Not Found" in (r.stderr or ""):
            return None
        raise ErrorImagenes("IMG_R2", f"head-object {clave}: {(r.stderr or '').strip()[:300]}")
    return json.loads(r.stdout or "{}").get("Metadata") or {}


def poner(fichero: Path, clave: str, huella: str, run: int, aws=_aws) -> str:
    """'subido' | 'ya_estaba'. Nunca pisa un run mayor (D-198); con el mismo sha256 no reescribe."""
    previo = _cabeza(clave, aws)
    if previo is not None:
        if previo.get("sha256") == huella:
            return "ya_estaba"
        if int(previo.get("run") or 0) > run:
            raise ErrorImagenes("IMG_RUN_MAYOR", f"{clave} lo escribió el run {previo.get('run')} > {run}")
    r = aws(["s3api", "put-object", "--bucket", os.environ["R2_BUCKET"], "--key", clave, "--body", str(fichero),
             "--metadata", f"sha256={huella},run={run}"], True)
    if r.returncode != 0:
        raise ErrorImagenes("IMG_R2", f"put-object {clave}: {(r.stderr or '').strip()[:300]}")
    return "subido"


def subir(salida: Path, aws=_aws, run: int | None = None) -> dict:
    run = int(run if run is not None else os.environ.get("GITHUB_RUN_ID") or 0)
    cat = json.loads((salida / "catalogo.json").read_text(encoding="utf-8"))
    piezas = []
    for i in cat["imagenes"]:
        f = salida / i["archivo"]
        if not f.is_file() or sha256(f.read_bytes()) != i["sha256"]:
            raise ErrorImagenes("IMG_HUELLA", f"{i['archivo']} no coincide con el catálogo")
        clave = f"{PREFIJO_R2}/{i['archivo']}"
        piezas.append({"clave": clave, "sha256": i["sha256"], "bytes": i["bytes"], "r2": poner(f, clave, i["sha256"], run, aws)})
    c = salida / "catalogo.json"
    man = {"tarea": "T-462", "run": run, "piezas": [p["clave"] for p in piezas], "catalogo_sha256": sha256(c.read_bytes()),
           "bytes": sum(p["bytes"] for p in piezas)}
    m = salida / "manifiesto.json"
    m.write_text(json.dumps(man, ensure_ascii=False, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    for f, nombre in ((c, "catalogo.json"), (m, "manifiesto.json")):  # el manifiesto, el último: sin él la subida no está completa
        clave = f"{PREFIJO_R2}/{nombre}"
        piezas.append({"clave": clave, "sha256": sha256(f.read_bytes()), "bytes": f.stat().st_size,
                       "r2": poner(f, clave, sha256(f.read_bytes()), run, aws)})
    res = {"prefijo": PREFIJO_R2, "run": run, "piezas": piezas}
    (salida / "subida.json").write_text(json.dumps(res, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return res


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("municipios")
    for c in ("descargar", "hoja", "subir"):
        p = sub.add_parser(c)
        p.add_argument("--salida", required=True, type=Path)
    a = ap.parse_args(argv)
    try:
        if a.cmd == "municipios":
            d, m = leer_distritos()
            print(f"{len(d)} distritos, {len(m)} municipios")
        elif a.cmd == "descargar":
            cat = descargar(a.salida)
            print("IMAGENES_TOTALES " + json.dumps(cat["totales"], sort_keys=True))
            for s in cat["sin_imagen"]:
                print(f"IMAGENES_SIN {s['municipio_codigo']} {s['municipio']}: {s['motivo']}")
            if cat["totales"]["errores_descarga"]:
                print("::error::Hay descargas fallidas por red; relanzar", file=sys.stderr)
                return 3
        elif a.cmd == "hoja":
            hoja(a.salida)
        else:
            print("IMAGENES_SUBIDA " + json.dumps(subir(a.salida), ensure_ascii=False, sort_keys=True))
    except ErrorImagenes as exc:
        print(f"::error::{exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
