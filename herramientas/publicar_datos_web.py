"""Sube a R2 los datos que lee la web (ddd-web) y reescribe el índice vigente `actual.json` (T-430, D-186, fase 1).

PROYECTO: Diputado de Distrito
VERSIÓN: 1.0.0 · FECHA: 2026-11-20 · ESTADO: candidato
ANTERIOR: ninguna (fichero nuevo)
CAMBIOS (antes de fusionar, D-188): solo la versión vigente en `web/actual/` (sin carpetas inmutables); se borra lo que sale del índice.
MOTIVO: D-186: los cálculos están en GitHub y los mapas generados en R2; la web tira de R2 cada vez a través de un índice publicado
  («actual») que dice qué versión de cada mapa y dato está vigente, con sha256. Una regeneración se ve sin tocar la web.
QUÉ HACE: lee el sitio candidato que P40 ya ha montado (sin calcular nada) y lo agrupa en `comunes` (índices, procedencia, registro
  del visor, `v2/datos/`) y `mapas/<territorio>` (sus ficheros de `datos/<territorio>/` y `mapa/datos/<territorio>/`). Solo la versión vigente
  (D-188): cada fichero vive en `web/actual/<ruta de hoy en el sitio>` (p. ej. `web/actual/datos/nac01/distritos.geojson`), sin códigos ni runs.
  Orden: (1) sube los ficheros cuyo sha256 difiere del índice vigente; (2) los vuelve a bajar y exige su sha256; (3) escribe
  `web/actual/actual.json`; (4) borra los ficheros que estaban en el índice anterior y ya no están. Caché de 60 s en todo. Si algo falla antes
  de (3), el índice no cambia (un fichero ya sobrescrito no casa con él y la web lo rechaza por sha256 hasta la siguiente publicación).
  Sin bucket (`R2_WEB_BUCKET` vacío) no hace nada y sale 0: la fase 1 va en paralelo a GitHub Pages, que sigue igual.
USO: python herramientas/publicar_datos_web.py --sitio /tmp/site-candidate [--bucket B] [--p40-run N] [--simular]
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
from datetime import datetime, timezone
from pathlib import Path

VERSION_FORMATO = 1
ARBOLES_COMUNES = ("datos", "mapa/datos", "v2/datos", "data")
ARBOLES_MAPA = ("datos", "mapa/datos")
PREFIJO = "web/actual/"
INDICE = PREFIJO + "actual.json"
CACHE = "public, max-age=60"
TIPOS = {".json": "application/json", ".geojson": "application/geo+json", ".csv": "text/csv; charset=utf-8",
         ".md": "text/markdown; charset=utf-8", ".txt": "text/plain; charset=utf-8"}


class DatosWebError(RuntimeError):
    pass


def sha256(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def version(ficheros: dict[str, str]) -> str:
    listado = "".join(f"{r} {h}\n" for r, h in sorted(ficheros.items()))
    return sha256(listado.encode("utf-8"))[:16]


def _ficheros(raiz: Path) -> list[Path]:
    return sorted(p for p in raiz.rglob("*") if p.is_file()) if raiz.is_dir() else []


def plan(sitio: Path) -> dict:
    """Agrupa los ficheros del sitio en comunes y mapas por territorio. Devuelve {grupo: {ruta: (sha256, Path)}}."""
    indice = sitio / "datos" / "INDEX.json"
    try:
        territorios = sorted(json.loads(indice.read_text(encoding="utf-8"))["territorios"])
    except (OSError, ValueError, KeyError) as exc:
        raise DatosWebError(f"INDICE_AUSENTE: {indice} sin `territorios`") from exc
    dv = sitio / "mapa" / "datos"
    if dv.is_dir():  # territorios con doble vuelta sin geometría propia (aut): también son mapas
        territorios = sorted(set(territorios) | {p.name for p in dv.iterdir() if p.is_dir() and re.fullmatch(r"(nac|aut)\d{2}", p.name)})
    grupos: dict[str, dict[str, tuple[str, Path]]] = {"comunes": {}}
    for t in territorios:
        grupos[f"mapas/{t}"] = {}
    for arbol in ARBOLES_COMUNES:
        for p in _ficheros(sitio / arbol):
            ruta = p.relative_to(sitio).as_posix()
            rel = p.relative_to(sitio / arbol).parts
            destino = "comunes"
            if arbol in ARBOLES_MAPA and len(rel) > 1 and f"mapas/{rel[0]}" in grupos:
                destino = f"mapas/{rel[0]}"
            grupos[destino][ruta] = (sha256(p.read_bytes()), p)
    vacios = [g for g, f in grupos.items() if not f]
    if vacios:
        raise DatosWebError(f"GRUPO_VACIO: {', '.join(vacios)} sin ficheros en el sitio")
    return grupos


def indice_nuevo(grupos: dict, p40_run: str, runs: dict[str, str], ahora: str) -> dict:
    out = {"version_formato": VERSION_FORMATO, "publicado": ahora, "p40_run": p40_run, "comunes": None, "mapas": {}}
    for g, f in grupos.items():
        hashes = {r: h for r, (h, _) in f.items()}
        entrada = {"version": version(hashes), "ficheros": dict(sorted(hashes.items()))}
        if g == "comunes":
            out["comunes"] = {**entrada, "run": p40_run}
        else:
            t = g.split("/", 1)[1]
            out["mapas"][t] = {**entrada, "run": runs.get(t, "")}
    return out


def ruta_publica(ruta: str) -> str:
    """Clave en el bucket de un fichero del índice: `web/actual/<ruta de hoy en el sitio>`."""
    return PREFIJO + ruta


def _todos(indice: dict) -> dict[str, str]:
    out = dict((indice.get("comunes") or {}).get("ficheros") or {})
    for e in (indice.get("mapas") or {}).values():
        out.update(e.get("ficheros") or {})
    return out


def _endpoint() -> str:
    return f"https://{os.environ['R2_ACCOUNT_ID']}.r2.cloudflarestorage.com"


def _aws(args: list[str], intentos: int = 4) -> subprocess.CompletedProcess:
    for i in range(intentos):
        r = subprocess.run(["aws", "s3", *args, "--endpoint-url", _endpoint(), "--only-show-errors"], capture_output=True, text=True)
        if r.returncode == 0 or "404" in r.stderr or "Not Found" in r.stderr or "NoSuchKey" in r.stderr:
            return r
        time.sleep(2 ** i)
    return r


class R2:
    """Cliente mínimo (aws s3 cp) con reintentos; se sustituye en las pruebas."""

    def __init__(self, bucket: str):
        self.bucket = bucket

    def leer(self, clave: str) -> bytes | None:
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "f"
            r = _aws(["cp", f"s3://{self.bucket}/{clave}", str(p)])
            if r.returncode != 0:
                if "404" in r.stderr or "Not Found" in r.stderr or "NoSuchKey" in r.stderr:
                    return None
                raise DatosWebError(f"R2_LECTURA: {clave}: {r.stderr.strip()[:300]}")
            return p.read_bytes()

    def borrar(self, clave: str) -> None:
        r = _aws(["rm", f"s3://{self.bucket}/{clave}"])
        if r.returncode != 0 and "404" not in r.stderr and "Not Found" not in r.stderr:
            raise DatosWebError(f"R2_BORRADO: {clave}: {r.stderr.strip()[:300]}")

    def escribir(self, clave: str, origen: Path, cache: str) -> None:
        tipo = TIPOS.get(origen.suffix.lower(), "application/octet-stream")
        r = _aws(["cp", str(origen), f"s3://{self.bucket}/{clave}", "--cache-control", cache, "--content-type", tipo])
        if r.returncode != 0:
            raise DatosWebError(f"R2_ESCRITURA: {clave}: {r.stderr.strip()[:300]}")


def _runs_territorio(sitio: Path) -> dict[str, str]:
    d = json.loads((sitio / "datos" / "INDEX.json").read_text(encoding="utf-8"))["territorios"]
    return {t: str(v.get("run_id", "")) for t, v in d.items()}


def publicar(sitio: Path, r2, p40_run: str = "", simular: bool = False, ahora: str = "") -> dict:
    grupos = plan(sitio)
    nuevo = indice_nuevo(grupos, p40_run, _runs_territorio(sitio), ahora or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"))
    previo_b = r2.leer(INDICE)
    previo = _todos(json.loads(previo_b)) if previo_b else {}
    locales = {r: (h, p) for f in grupos.values() for r, (h, p) in f.items()}
    subir = [(r, h, p) for r, (h, p) in sorted(locales.items()) if previo.get(r) != h]
    sobran = sorted(set(previo) - set(locales))
    print(f"[datos_web] {len(grupos)} grupos; {len(subir)} ficheros a subir; {len(sobran)} a borrar; simular={simular}")
    if simular:
        return nuevo
    for r, _, p in subir:
        r2.escribir(ruta_publica(r), p, CACHE)
    malos = [r for r, h, _ in subir if sha256(r2.leer(ruta_publica(r)) or b"") != h]
    if malos:
        raise DatosWebError(f"SHA256_TRAS_SUBIR: {len(malos)} ficheros no casan (p. ej. {malos[0]}); actual.json no cambia")
    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / "actual.json"
        p.write_text(json.dumps(nuevo, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        r2.escribir(INDICE, p, CACHE)
        if r2.leer(INDICE) != p.read_bytes():
            raise DatosWebError("ACTUAL_JSON_DISTINTO tras escribirlo")
    for r in sobran:  # solo la vigente (D-188): lo que ya no está en el índice se borra, después de escribirlo
        r2.borrar(ruta_publica(r))
    print(f"[datos_web] {INDICE} escrito: {len(nuevo['mapas'])} mapas; {len(sobran)} ficheros viejos borrados")
    return nuevo


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--sitio", type=Path, required=True)
    ap.add_argument("--bucket", default=os.environ.get("R2_WEB_BUCKET", ""))
    ap.add_argument("--p40-run", default=os.environ.get("GITHUB_RUN_ID", ""))
    ap.add_argument("--simular", action="store_true")
    a = ap.parse_args(argv)
    if not a.bucket:
        print("[datos_web] sin R2_WEB_BUCKET: no se sube nada (fase 1, opcional)")
        return 0
    try:
        publicar(a.sitio, R2(a.bucket), a.p40_run, a.simular)
    except DatosWebError as exc:
        print(f"::error::{exc}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
