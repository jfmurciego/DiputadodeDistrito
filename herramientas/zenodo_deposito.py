#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Depósito de mapas de Deslinde en Zenodo por la API REST (T-388, D-146): solo mapas, sin código.

PROYECTO: Diputado de Distrito
VERSIÓN: 1.1.0
NOMBRE DE VERSIÓN: Depósito de mapas en Zenodo
FECHA: 2026-11-16
ESTADO: candidato
CAMBIOS: 1.1.0: concepto nuevo solo si Zenodo rechaza EXACTAMENTE el cambio de tipo (campo upload_type) y solo con `--permitir-concepto-nuevo`; el resto de 400/422 falla cerrado con el borrador documentado; idempotencia por versión Y título; tiempo de espera ajustable. 1.0.0: fichero nuevo (T-388).
ANTERIOR: legacy/herramientas/zenodo_deposito_v1.0.0_20261116.py
QUÉ HACE: `linaje --dir D --salida F` une los LINAJE.json de los paquetes `ddd-*-v*.tar.gz` de D en un solo fichero.
  `depositar --destino prueba|Zenodo --version V --tag mapas-vV --repo O/R --ficheros F...` crea el depósito, sube los
  ficheros, comprueba sus huellas md5 contra Zenodo y, salvo `--sin-publicar`, publica. Destino `prueba` = sandbox.zenodo.org.
  Token: variable de entorno ZENODO_TOKEN (nunca por argumento, nunca impreso). Zenodo reparte los DOI de la serie: nueva
  versión del concepto `--concepto-id` (registro de cualquier versión; por defecto el de la serie de mapas en Zenodo real,
  ninguno en prueba); si Zenodo rechaza exactamente el cambio de tipo (error en `upload_type`) Y se pasó
  `--permitir-concepto-nuevo`, borra ese borrador y crea un concepto nuevo (`concepto_nuevo` en el informe); sin el permiso,
  o con otro error, falla cerrado y deja el borrador documentado (nunca abre una serie de DOI nueva sin permiso). Fallo cerrado: si ya hay un depósito de esa versión, no crea otro; sin reintentos de escritura; un fallo
  tras crear el borrador lo documenta en stderr (id y URL) y no publica. Informe JSON en stdout; errores en stderr, rc 1.
"""
from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import os
import re
import sys
import tarfile
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

BASES = {"prueba": "https://sandbox.zenodo.org", "Zenodo": "https://zenodo.org"}
CONCEPTO_REAL = "24093968"  # registro de la serie de mapas en Zenodo (DOI de concepto 10.5281/zenodo.24093967)
CREADOR = {"name": "Murciego, Jesus", "affiliation": "Independent researcher", "orcid": "0009-0002-4434-959X"}
VISOR = "https://jfmurciego.github.io/DiputadodeDistrito/"
REQUERIDOS = ("SHA256SUMS", "LINAJE.json", "LICENCIA_CC-BY-4.0.txt", "NOTA_FUENTES.md")
_PAQUETE = re.compile(r"^ddd-[a-z0-9_]+-v\d+\.\d+\.\d+\.tar\.gz$")
_VERSION = re.compile(r"^\d+\.\d+\.\d+$")
_REPO = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
_ESPERA_GET = (1, 3)  # reintentos solo de lecturas
_TIMEOUT = 120
TITULO = "Deslinde: mapas de distritos uninominales, v"


class ErrorDeposito(Exception):
    def __init__(self, mensaje, codigo=None, cuerpo=None):
        super().__init__(mensaje)
        self.codigo, self.cuerpo = codigo, cuerpo


def _solo_cambio_de_tipo(e: ErrorDeposito) -> bool:
    """True solo si TODOS los errores de validación de Zenodo son del campo `upload_type`."""
    if e.codigo not in (400, 422) or not isinstance(e.cuerpo, dict):
        return False
    errs = e.cuerpo.get("errors")
    return bool(errs) and isinstance(errs, list) and all(
        isinstance(x, dict) and str(x.get("field", "")).split(".")[-1] == "upload_type" for x in errs)


def _limpiar(texto: str, token: str) -> str:
    return texto.replace(token, "***") if token else texto


def validar_ficheros(rutas: list[Path]) -> list[dict]:
    """Solo mapas: paquetes `ddd-*-v*.tar.gz` y los cuatro ficheros de acompañamiento; nada más (sin código)."""
    if not rutas:
        raise ErrorDeposito("ZENODO_SIN_FICHEROS: no hay ficheros que depositar")
    out, nombres = [], set()
    for r in rutas:
        if not r.is_file():
            raise ErrorDeposito(f"ZENODO_FICHERO_AUSENTE: {r.name}")
        n = r.name
        if n in nombres:
            raise ErrorDeposito(f"ZENODO_FICHERO_REPETIDO: {n}")
        if not (_PAQUETE.match(n) or n in REQUERIDOS):
            raise ErrorDeposito(f"ZENODO_FICHERO_NO_PERMITIDO: {n} (solo paquetes de mapas y su documentación; sin código)")
        nombres.add(n)
        md5, sha = hashlib.md5(), hashlib.sha256()
        with r.open("rb") as f:
            for bloque in iter(lambda: f.read(1 << 20), b""):
                md5.update(bloque)
                sha.update(bloque)
        out.append({"ruta": r, "nombre": n, "md5": md5.hexdigest(), "sha256": sha.hexdigest(), "bytes": r.stat().st_size})
    if not any(_PAQUETE.match(n) for n in nombres):
        raise ErrorDeposito("ZENODO_SIN_PAQUETE: falta algún paquete ddd-<territorio>-v<versión>.tar.gz")
    faltan = [n for n in REQUERIDOS if n not in nombres]
    if faltan:
        raise ErrorDeposito(f"ZENODO_FALTAN_FICHEROS: {', '.join(faltan)}")
    return sorted(out, key=lambda x: x["nombre"])


def metadatos(version: str, tag: str, repo: str, fecha: str | None = None) -> dict:
    return {
        "title": f"{TITULO}{version}",
        "upload_type": "dataset",
        "description": (
            f"<p>Mapas de distritos uninominales (Deslinde) en su versión {version}: paquetes firmados por territorio, manifiesto "
            "SHA-256 y linaje. Solo mapas, sin código ni motor.</p>"
            "<p><strong>Sin valor oficial:</strong> son un ejercicio de investigación.</p>"
            f"<p>Release de origen y atestación de procedencia (Sigstore): https://github.com/{repo}/releases/tag/{tag}. "
            f"Visor: {VISOR}</p>"
        ),
        "version": version,
        "publication_date": fecha or datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d"),
        "creators": [dict(CREADOR)],
        "license": "cc-by-4.0",
        "access_right": "open",
        "language": "spa",
        "keywords": ["redistricting", "distritos uninominales", "secciones censales", "INE", "España"],
        "related_identifiers": [
            {"identifier": f"https://github.com/{repo}/releases/tag/{tag}", "relation": "isSupplementTo", "scheme": "url"},
            {"identifier": VISOR, "relation": "isDocumentedBy", "scheme": "url"},
        ],
        "notes": ("Mapas de investigación sin valor oficial. Fuentes: INE (secciones censales y padrón) y Ministerio del Interior "
                  "(resultados electorales); ver NOTA_FUENTES.md. Licencia de los mapas: CC BY 4.0."),
    }


def unir_linaje(directorio: Path) -> list[dict]:
    paquetes = sorted(p for p in directorio.glob("ddd-*-v*.tar.gz") if _PAQUETE.match(p.name))
    if not paquetes:
        raise ErrorDeposito("ZENODO_SIN_PAQUETE: no hay paquetes en el directorio")
    out = []
    for p in paquetes:
        with tarfile.open(p, "r:gz") as t:
            try:
                m = t.extractfile("./LINAJE.json") or t.extractfile("LINAJE.json")
            except KeyError:
                m = None
            if m is None:
                raise ErrorDeposito(f"ZENODO_SIN_LINAJE: {p.name} no trae LINAJE.json")
            out.append(json.loads(m.read().decode("utf-8")))
    return out


class Cliente:
    """Cliente mínimo de la API de depósitos. Escrituras: un solo intento. Lecturas: reintentos ante 5xx/red."""

    def __init__(self, base: str, token: str):
        self.base, self.token = base.rstrip("/"), token

    def _req(self, metodo, url, datos=None, cabeceras=None, timeout=None, lectura=False):
        timeout = timeout or _TIMEOUT
        if url.startswith("/"):
            url = self.base + url
        if urllib.parse.urlsplit(url).netloc != urllib.parse.urlsplit(self.base).netloc:
            raise ErrorDeposito("ZENODO_URL_AJENA: la API devolvió un enlace de otro servidor; se aborta sin enviar el token")
        h = {"Authorization": f"Bearer {self.token}", "Accept": "application/json", **(cabeceras or {})}
        intentos = (0,) + _ESPERA_GET if lectura else (0,)
        for i, espera in enumerate(intentos):
            time.sleep(espera)
            ultimo = i == len(intentos) - 1
            try:
                rq = urllib.request.Request(url, data=datos, headers=h, method=metodo)
                with urllib.request.urlopen(rq, timeout=timeout) as r:
                    cuerpo = r.read()
                    return r.status, (json.loads(cuerpo) if cuerpo else {})
            except urllib.error.HTTPError as e:
                bruto = _limpiar(e.read().decode("utf-8", "replace"), self.token)
                if lectura and e.code >= 500 and not ultimo:
                    continue
                try:
                    parseado = json.loads(bruto)
                except ValueError:
                    parseado = None
                raise ErrorDeposito(f"ZENODO_HTTP_{e.code}: {metodo} {urllib.parse.urlsplit(url).path}: {bruto[:600]}",
                                    e.code, parseado) from None
            except (urllib.error.URLError, TimeoutError, OSError) as e:
                if lectura and not ultimo:
                    continue
                raise ErrorDeposito(f"ZENODO_RED: {metodo} {urllib.parse.urlsplit(url).path}: {_limpiar(str(e), self.token)}") from None
        raise ErrorDeposito("ZENODO_RED: sin respuesta")  # inalcanzable

    def get(self, url):
        return self._req("GET", url, lectura=True)[1]

    def post(self, url, cuerpo=None):
        d = json.dumps(cuerpo).encode("utf-8") if cuerpo is not None else b""
        return self._req("POST", url, d, {"Content-Type": "application/json"})[1]

    def put_json(self, url, cuerpo):
        return self._req("PUT", url, json.dumps(cuerpo).encode("utf-8"), {"Content-Type": "application/json"})[1]

    def delete(self, url):
        self._req("DELETE", url)

    def subir(self, bucket, f: dict):
        url = f"{bucket.rstrip('/')}/{urllib.parse.quote(f['nombre'])}"
        with f["ruta"].open("rb") as fh:
            return self._req("PUT", url, fh, {"Content-Type": "application/octet-stream", "Content-Length": str(f["bytes"])},
                             timeout=max(_TIMEOUT, 1800))[1]


def existentes(c: Cliente, version: str) -> list[dict]:
    """Depósitos NUESTROS (borradores o publicados; misma versión y título «Deslinde: mapas…») de cualquier serie.
    El registro histórico de Huesca (otro título) no bloquea el primer depósito, aunque su versión fuera «1.0.0»."""
    out, pagina = [], 1
    while True:
        lote = c.get(f"/api/deposit/depositions?size=100&page={pagina}&all_versions=1")
        if not isinstance(lote, list):
            raise ErrorDeposito("ZENODO_LISTADO_INESPERADO: la API no devolvió una lista de depósitos")
        out += [d for d in lote if (d.get("metadata") or {}).get("version") == version
                and str((d.get("metadata") or {}).get("title", "")).startswith(TITULO)]
        if len(lote) < 100:
            return out
        pagina += 1


def _borrador(c: Cliente, estado: dict, concepto_id: str | None, meta: dict, declarar, permitir_nuevo: bool) -> tuple[dict, bool]:
    """Devuelve (borrador con metadatos puestos, concepto_nuevo)."""
    if concepto_id:
        try:
            nuevo = c.post(f"/api/deposit/depositions/{concepto_id}/actions/newversion")
            dep = c.get(nuevo["links"]["latest_draft"])
        except (KeyError, TypeError):
            raise ErrorDeposito(f"ZENODO_NEWVERSION_INESPERADA: la API no devolvió el borrador de la nueva versión; puede haber un "
                                f"borrador huérfano en la serie del registro {concepto_id}: revísalo y bórralo en Zenodo antes de relanzar") from None
        estado["borrador"] = dep
        for f in c.get(dep["links"]["files"]):  # los ficheros heredados (p. ej. el ZIP de código) no se conservan
            c.delete(f["links"]["self"])
        try:
            c.put_json(dep["links"]["self"], {"metadata": meta})
            return c.get(dep["links"]["self"]), False
        except ErrorDeposito as e:
            if not _solo_cambio_de_tipo(e):
                raise  # cualquier otro error: falla cerrado, borrador documentado, sin serie nueva
            if not permitir_nuevo:
                raise ErrorDeposito("ZENODO_CONCEPTO_NUEVO_NO_PERMITIDO: Zenodo no admite pasar la serie de software a dataset; crear un "
                                    "concepto nuevo abre una serie de DOI nueva y exige marcar «concepto_nuevo» en el botón. "
                                    f"Detalle: {str(e)[:200]}") from None
            declarar(f"aviso: Zenodo no admite el cambio de tipo en la serie ({str(e)[:200]}); concepto nuevo (permitido)")
            c.delete(dep["links"]["self"])  # si no se borra, se aborta: no se crea un segundo borrador
            estado["borrador"] = None
    dep = c.post("/api/deposit/depositions", {})
    estado["borrador"] = dep
    c.put_json(dep["links"]["self"], {"metadata": meta})
    return c.get(dep["links"]["self"]), True


def depositar(destino: str, token: str, version: str, tag: str, repo: str, rutas: list[Path], concepto_id: str | None,
              publicar: bool = True, api_base: str | None = None, fecha: str | None = None, avisar=lambda m: None,
              permitir_concepto_nuevo: bool = False) -> dict:
    if destino not in BASES:
        raise ErrorDeposito(f"ZENODO_DESTINO_INVALIDO: {destino!r} (prueba|Zenodo)")
    if not token:
        raise ErrorDeposito("ZENODO_SIN_TOKEN: falta la variable ZENODO_TOKEN")
    if not _VERSION.match(version) or tag != f"mapas-v{version}":
        raise ErrorDeposito(f"ZENODO_VERSION_INVALIDA: versión {version!r} y etiqueta {tag!r} no cuadran")
    if not _REPO.match(repo):
        raise ErrorDeposito(f"ZENODO_REPO_INVALIDO: {repo!r}")
    if api_base and urllib.parse.urlsplit(api_base).hostname not in ("127.0.0.1", "localhost"):
        raise ErrorDeposito("ZENODO_API_BASE_NO_LOCAL: solo se admite un servidor local de pruebas")
    ficheros = validar_ficheros(rutas)
    c = Cliente(api_base or BASES[destino], token)
    previos = existentes(c, version)
    if previos:
        d = previos[0]
        raise ErrorDeposito(f"ZENODO_YA_EXISTE: la versión {version} ya tiene depósito (id {d.get('id')}, estado {d.get('state')}); "
                            "no se crea otro: revísalo o bórralo a mano")
    estado: dict = {"borrador": None}
    try:
        dep, nuevo = _borrador(c, estado, concepto_id, metadatos(version, tag, repo, fecha), avisar, permitir_concepto_nuevo)
        bucket = dep["links"]["bucket"]
        for f in ficheros:
            c.subir(bucket, f)
        subidos = {x["filename"]: str(x.get("checksum", "")).removeprefix("md5:") for x in c.get(dep["links"]["files"])}
        esperado = {f["nombre"]: f["md5"] for f in ficheros}
        if subidos != esperado:
            raise ErrorDeposito(f"ZENODO_BORRADOR_NO_VALIDA: ficheros del borrador distintos de los locales ({sorted(subidos)})")
        informe = {"destino": destino, "deposito_id": dep["id"], "concepto_nuevo": nuevo, "publicado": False,
                   "url_borrador": (dep.get("links") or {}).get("html"), "version": version, "tag": tag,
                   "ficheros": [{k: f[k] for k in ("nombre", "bytes", "sha256")} for f in ficheros]}
        if publicar:
            r = c.post(dep["links"]["publish"])
            informe.update(publicado=True, doi=r.get("doi"), doi_concepto=r.get("conceptdoi"), url=(r.get("links") or {}).get("html"))
        return informe
    except ErrorDeposito as e:
        b = estado.get("borrador")
        if b:
            raise ErrorDeposito(f"{e}\nBORRADOR sin publicar: id {b.get('id')} {(b.get('links') or {}).get('html', '')} "
                                "(bórralo en Zenodo o continúa a mano; no se reintenta solo)") from None
        raise


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Depósito de mapas de Deslinde en Zenodo (API REST; token en ZENODO_TOKEN)")
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("linaje", help="une los LINAJE.json de los paquetes de un directorio")
    s.add_argument("--dir", required=True)
    s.add_argument("--salida", required=True)
    d = sub.add_parser("depositar", help="crea el depósito, sube los ficheros y publica")
    d.add_argument("--destino", required=True, choices=sorted(BASES))
    d.add_argument("--version", required=True)
    d.add_argument("--tag", required=True)
    d.add_argument("--repo", required=True)
    d.add_argument("--ficheros", nargs="+", required=True)
    d.add_argument("--concepto-id", default=None, help=f"registro de una versión de la serie (por defecto {CONCEPTO_REAL} solo en Zenodo)")
    d.add_argument("--permitir-concepto-nuevo", action="store_true", help="si Zenodo rechaza el cambio de tipo, abre una serie de DOI nueva")
    d.add_argument("--sin-publicar", action="store_true", help="deja el borrador validado sin publicar")
    d.add_argument("--api-base", default=None, help="solo servidor local de pruebas")
    a = ap.parse_args(argv)
    try:
        if a.cmd == "linaje":
            Path(a.salida).write_text(json.dumps(unir_linaje(Path(a.dir)), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            return 0
        concepto = a.concepto_id if a.concepto_id is not None else (CONCEPTO_REAL if a.destino == "Zenodo" else None)
        informe = depositar(a.destino, os.environ.get("ZENODO_TOKEN", ""), a.version, a.tag, a.repo, [Path(x) for x in a.ficheros],
                            concepto or None, not a.sin_publicar, a.api_base, avisar=lambda m: print(m, file=sys.stderr),
                            permitir_concepto_nuevo=a.permitir_concepto_nuevo)
        print(json.dumps(informe, ensure_ascii=False, indent=2))
        return 0
    except ErrorDeposito as e:
        print(f"::error::{e}" if os.environ.get("GITHUB_ACTIONS") else str(e), file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
