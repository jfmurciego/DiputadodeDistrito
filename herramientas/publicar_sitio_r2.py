"""Sube la web (sin los datos) al bucket público del sitio en R2 y reescribe su índice (T-430, D-193/D-194, paso 2 de REDISENO_R2 §9).

PROYECTO: Diputado de Distrito
VERSIÓN: 1.0.0 · FECHA: 2026-11-22 · ESTADO: candidato
ANTERIOR: ninguna (fichero nuevo)
MOTIVO: D-193: la web se sirve desde R2 (bucket `ddd-web-sitio`), no desde GitHub Pages; los datos ya van a `ddd-web-datos` (#957).
  Mientras dure el ensayo, P40 sube a los dos sitios (Pages y R2) a la vez.
QUÉ HACE: del sitio candidato que ya monta P40 toma TODO salvo los árboles de datos (`datos/`, `data/`, `mapa/datos/`, `v2/datos/`, que
  sirve `datos.diputadodedistrito.es`) y lo deja en la raíz del bucket con su ruta de hoy, solo la versión vigente (D-188):
  (1) sube los ficheros cuyo sha256 difiere del índice `_sitio/actual.json`, primero imágenes, estilos y código y las páginas HTML al
  final (una página nueva nunca apunta a un fichero que aún no está); (2) los vuelve a bajar y exige su sha256; (3) escribe el índice;
  (4) borra lo que salió del índice. Caché de 60 s en todo (la marca de caché larga para estilos y código es de T-441, aparte).
  GUARDA DEL BORRADO (antes de escribir nada, como #957): solo claves relativas sin «..», vacías, absolutas ni dentro de los árboles de
  datos o del índice; sin `--permitir-borrado` aborta si sobran más de `TOPE_BORRAR_FICHEROS` o, a partir de `TOPE_BORRAR_MINIMO`, más del
  `TOPE_BORRAR_PCT` % del índice previo; un sitio sin `index.html` en la raíz no se publica. El bucket del sitio no puede ser el de trabajo
  (`R2_BUCKET`) ni el de datos (`R2_WEB_BUCKET`). Sin `R2_SITIO_BUCKET` no hace nada y sale 0.
USO: python herramientas/publicar_sitio_r2.py --sitio /tmp/site-candidate [--bucket B] [--p40-run N] [--simular] [--permitir-borrado]
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from herramientas.publicar_datos_web import ARBOLES_COMUNES, R2, DatosWebError, sha256

INDICE = "_sitio/actual.json"
CACHE = "public, max-age=60"
TOPE_BORRAR_FICHEROS = 50
TOPE_BORRAR_PCT = 10
TOPE_BORRAR_MINIMO = 5
TIPOS_SITIO = {".html": "text/html; charset=utf-8", ".css": "text/css; charset=utf-8", ".js": "text/javascript; charset=utf-8",
               ".mjs": "text/javascript; charset=utf-8", ".json": "application/json", ".webp": "image/webp", ".png": "image/png",
               ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".svg": "image/svg+xml", ".ico": "image/x-icon", ".woff2": "font/woff2",
               ".woff": "font/woff", ".txt": "text/plain; charset=utf-8", ".md": "text/markdown; charset=utf-8", ".xml": "application/xml",
               ".csv": "text/csv; charset=utf-8", ".geojson": "application/geo+json", ".pdf": "application/pdf"}


def es_dato(ruta: str) -> bool:
    return any(ruta == a or ruta.startswith(a + "/") for a in ARBOLES_COMUNES)


def clave_valida(ruta: str) -> bool:
    partes = ruta.split("/")
    return (bool(ruta) and not ruta.startswith("/") and "\\" not in ruta and ".." not in partes and "" not in partes
            and not es_dato(ruta) and not ruta.startswith("_sitio/"))


def plan(sitio: Path) -> dict[str, tuple[str, Path]]:
    if not (sitio / "index.html").is_file():
        raise DatosWebError("SITIO_SIN_PORTADA: el sitio candidato no tiene index.html en la raíz; no se publica ni se borra nada")
    out = {}
    for p in sorted(sitio.rglob("*")):
        if p.is_file():
            ruta = p.relative_to(sitio).as_posix()
            if not es_dato(ruta):
                if not clave_valida(ruta):
                    raise DatosWebError(f"RUTA_NO_VALIDA: {ruta!r}")
                out[ruta] = (sha256(p.read_bytes()), p)
    return out


def comprobar_borrado(previo: dict[str, str], sobran: list[str], permitir: bool) -> None:
    malas = [r for r in sobran if not clave_valida(r)]
    if malas:
        raise DatosWebError(f"CLAVE_NO_BORRABLE: {malas[0]!r} (y {len(malas) - 1} más); no se borra nada")
    if permitir:
        return
    if len(sobran) > TOPE_BORRAR_FICHEROS or (len(sobran) > TOPE_BORRAR_MINIMO and 100 * len(sobran) > TOPE_BORRAR_PCT * len(previo)):
        raise DatosWebError(f"BORRADO_MASIVO: {len(sobran)} de {len(previo)} ficheros; no se publica ni se borra nada (anulación: --permitir-borrado)")


class R2Sitio(R2):
    """Como el cliente de datos, con los tipos de una web (HTML, CSS, JS, imágenes)."""

    def escribir(self, clave: str, origen: Path, cache: str) -> None:
        from herramientas.publicar_datos_web import _aws
        tipo = TIPOS_SITIO.get(origen.suffix.lower(), "application/octet-stream")
        r = _aws(["cp", str(origen), f"s3://{self.bucket}/{clave}", "--cache-control", cache, "--content-type", tipo])
        if r.returncode != 0:
            raise DatosWebError(f"R2_ESCRITURA: {clave}: {r.stderr.strip()[:300]}")


def publicar(sitio: Path, r2, p40_run: str = "", simular: bool = False, ahora: str = "", permitir_borrado: bool = False) -> dict:
    locales = plan(sitio)
    nuevo = {"version_formato": 1, "publicado": ahora or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), "p40_run": p40_run,
             "ficheros": {r: h for r, (h, _) in locales.items()}}
    previo_b = r2.leer(INDICE)
    previo = (json.loads(previo_b).get("ficheros") or {}) if previo_b else {}
    subir = [(r, h, p) for r, (h, p) in locales.items() if previo.get(r) != h]
    subir.sort(key=lambda x: (x[0].endswith(".html"), x[0]))  # páginas al final
    sobran = sorted(set(previo) - set(locales))
    print(f"[sitio_r2] {len(locales)} ficheros; {len(subir)} a subir; {len(sobran)} a borrar; simular={simular}")
    comprobar_borrado(previo, sobran, permitir_borrado)
    if simular:
        return nuevo
    for r, _, p in subir:
        r2.escribir(r, p, CACHE)
    malos = [r for r, h, _ in subir if sha256(r2.leer(r) or b"") != h]
    if malos:
        raise DatosWebError(f"SHA256_TRAS_SUBIR: {len(malos)} ficheros no casan (p. ej. {malos[0]}); el índice no cambia")
    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / "actual.json"
        p.write_text(json.dumps(nuevo, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        r2.escribir(INDICE, p, CACHE)
        if r2.leer(INDICE) != p.read_bytes():
            raise DatosWebError("INDICE_DISTINTO tras escribirlo")
    for r in sobran:
        assert clave_valida(r)
        r2.borrar(r)
    print(f"[sitio_r2] {INDICE} escrito; {len(sobran)} ficheros viejos borrados")
    return nuevo


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--sitio", type=Path, required=True)
    ap.add_argument("--bucket", default=os.environ.get("R2_SITIO_BUCKET", ""))
    ap.add_argument("--p40-run", default=os.environ.get("GITHUB_RUN_ID", ""))
    ap.add_argument("--simular", action="store_true")
    ap.add_argument("--permitir-borrado", action="store_true", help="anula el tope de borrado (solo a mano, con permiso)")
    a = ap.parse_args(argv)
    if not a.bucket:
        print("[sitio_r2] sin R2_SITIO_BUCKET: no se sube nada (ensayo opcional)")
        return 0
    otros = {os.environ.get("R2_BUCKET", ""), os.environ.get("R2_WEB_BUCKET", "")} - {""}
    if a.bucket in otros:
        print(f"::error::BUCKET_AJENO: R2_SITIO_BUCKET ({a.bucket}) es el bucket de trabajo o el de datos; no se toca")
        return 1
    try:
        publicar(a.sitio, R2Sitio(a.bucket), a.p40_run, a.simular, permitir_borrado=a.permitir_borrado)
    except DatosWebError as exc:
        print(f"::error::{exc}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
