"""Entorno de pruebas de la web: una carpeta por rama en el bucket de pruebas de R2 y su limpieza (T-430, D-193/D-194, paso 3a).

PROYECTO: Diputado de Distrito
VERSIÓN: 1.0.0 · FECHA: 2026-11-23 · ESTADO: candidato
ANTERIOR: ninguna (fichero nuevo)
MOTIVO: D-193/D-194: ver cada cambio de la web antes de publicarlo, en `https://pruebas.diputadodedistrito.es/<rama>/`.
QUÉ HACE:
  montar  — copia `visor/v4/` (sin lo de `NO_PUBLICAR.txt`) como raíz y `visor/v2/vendor/` y `visor/v2/galeria/` (que Explorar usa con
            `../v2/…`); añade `<meta name="robots" content="noindex">` a cada página; si se da la dirección del índice de datos
            (`--datos-actual`), la pone en `mapa/datos.json` (Explorar lee los datos de producción de `datos.`). No calcula nada.
  subir   — `aws s3 sync --delete` del montaje a `s3://<bucket>/<rama>/` (solo esa carpeta; `--delete` no sale de ella), sin caché.
  limpiar — borra las carpetas del bucket de pruebas cuya rama ya no tiene PR abierta (lista de ramas abiertas que se le pasa); nunca
            más de `TOPE_LIMPIEZA` de una vez ni nombres fuera de `[a-z0-9-]`.
  La rama se normaliza a minúsculas, `/` y `_` → `-`, solo `[a-z0-9-]`, máx. 60 caracteres; vacía = error.
USO: python herramientas/pruebas_web_r2.py montar --destino D [--datos-actual URL]
     python herramientas/pruebas_web_r2.py subir --origen D --rama R [--bucket B]
     python herramientas/pruebas_web_r2.py limpiar --abiertas R1,R2,… [--bucket B]
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
TOPE_LIMPIEZA = 20
NOINDEX = '<meta name="robots" content="noindex">'


class PruebasError(RuntimeError):
    pass


def rama_a_carpeta(rama: str) -> str:
    c = re.sub(r"[^a-z0-9-]", "", re.sub(r"[/_]", "-", rama.strip().lower())).strip("-")[:60].strip("-")
    if not c:
        raise PruebasError(f"RAMA_NO_VALIDA: {rama!r}")
    return c


def montar(destino: Path, raiz: Path = RAIZ, datos_actual: str = "") -> int:
    v4 = raiz / "visor" / "v4"
    if destino.exists():
        shutil.rmtree(destino)
    shutil.copytree(v4, destino)
    for linea in (v4 / "NO_PUBLICAR.txt").read_text(encoding="utf-8").splitlines():
        f = linea.strip()
        if f and not f.startswith("#") and ".." not in f and not f.startswith("/"):
            p = destino / f
            shutil.rmtree(p) if p.is_dir() else p.unlink(missing_ok=True)
    for sub in ("vendor", "galeria"):
        shutil.copytree(raiz / "visor" / "v2" / sub, destino / "v2" / sub)
    n = 0
    for p in destino.rglob("*.html"):
        t = p.read_text(encoding="utf-8")
        if NOINDEX not in t:
            if "<head>" not in t:
                raise PruebasError(f"SIN_HEAD: {p.relative_to(destino)}")
            p.write_text(t.replace("<head>", "<head>\n" + NOINDEX, 1), encoding="utf-8")
        n += 1
    if datos_actual:
        if not re.fullmatch(r"https://[a-z0-9.-]+/[^?#\s]*actual\.json", datos_actual):
            raise PruebasError(f"DATOS_ACTUAL_NO_VALIDA: {datos_actual!r}")
        (destino / "mapa" / "datos.json").write_text(json.dumps({"actual": datos_actual}) + "\n", encoding="utf-8")
    print(f"[pruebas_web] montadas {n} páginas en {destino}")
    return n


def _endpoint() -> str:
    return f"https://{os.environ['R2_ACCOUNT_ID']}.r2.cloudflarestorage.com"


def _aws(args: list[str], ejecutar=subprocess.run):
    r = ejecutar(["aws", "s3", *args, "--endpoint-url", _endpoint(), "--only-show-errors"], capture_output=True, text=True)
    if r.returncode != 0:
        raise PruebasError(f"R2: {' '.join(args[:2])}: {r.stderr.strip()[:300]}")
    return r.stdout


def subir(origen: Path, bucket: str, rama: str, ejecutar=subprocess.run) -> str:
    carpeta = rama_a_carpeta(rama)
    if not (origen / "index.html").is_file():
        raise PruebasError("SIN_PORTADA: el montaje no tiene index.html")
    _aws(["sync", str(origen), f"s3://{bucket}/{carpeta}/", "--delete", "--cache-control", "no-cache"], ejecutar)
    return carpeta


def carpetas(bucket: str, ejecutar=subprocess.run) -> list[str]:
    salida = _aws(["ls", f"s3://{bucket}/"], ejecutar)
    return sorted(m.group(1) for m in re.finditer(r"^\s*PRE (\S+)/\s*$", salida, re.M))


def limpiar(bucket: str, abiertas: list[str], ejecutar=subprocess.run) -> list[str]:
    vivas = {rama_a_carpeta(r) for r in abiertas if r.strip()}
    sobran = [c for c in carpetas(bucket, ejecutar) if c not in vivas]
    raras = [c for c in sobran if not re.fullmatch(r"[a-z0-9-]{1,60}", c)]
    if raras:
        raise PruebasError(f"CARPETA_RARA: {raras[0]!r}; no se borra nada")
    if len(sobran) > TOPE_LIMPIEZA:
        raise PruebasError(f"LIMPIEZA_MASIVA: {len(sobran)} carpetas; no se borra nada")
    for c in sobran:
        _aws(["rm", f"s3://{bucket}/{c}/", "--recursive"], ejecutar)
    print(f"[pruebas_web] {len(sobran)} carpetas de ramas cerradas borradas")
    return sobran


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="accion", required=True)
    m = sub.add_parser("montar")
    m.add_argument("--destino", type=Path, required=True)
    m.add_argument("--datos-actual", default=os.environ.get("DATOS_WEB_ACTUAL", ""))
    s = sub.add_parser("subir")
    s.add_argument("--origen", type=Path, required=True)
    s.add_argument("--rama", required=True)
    s.add_argument("--bucket", default=os.environ.get("R2_PRUEBAS_BUCKET", ""))
    li = sub.add_parser("limpiar")
    li.add_argument("--abiertas", required=True, help="ramas con PR abierta, separadas por comas")
    li.add_argument("--bucket", default=os.environ.get("R2_PRUEBAS_BUCKET", ""))
    a = ap.parse_args(argv)
    try:
        if a.accion == "montar":
            montar(a.destino, datos_actual=a.datos_actual)
            return 0
        if not a.bucket:
            print("[pruebas_web] sin R2_PRUEBAS_BUCKET: no se sube ni se borra nada")
            return 0
        ajenos = {os.environ.get(v, "") for v in ("R2_BUCKET", "R2_WEB_BUCKET", "R2_SITIO_BUCKET")} - {""}
        if a.bucket in ajenos:
            raise PruebasError(f"BUCKET_AJENO: {a.bucket} no es el de pruebas")
        if a.accion == "subir":
            c = subir(a.origen, a.bucket, a.rama)
            url = f"https://pruebas.diputadodedistrito.es/{c}/"
            print(f"[pruebas_web] {url}")
            if os.environ.get("GITHUB_STEP_SUMMARY"):
                with open(os.environ["GITHUB_STEP_SUMMARY"], "a", encoding="utf-8") as f:
                    f.write(f"Vista de pruebas: {url}\n")
        else:
            limpiar(a.bucket, a.abiertas.split(","))
    except PruebasError as exc:
        print(f"::error::{exc}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
