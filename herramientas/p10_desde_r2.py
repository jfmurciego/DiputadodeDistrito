#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""P10 desde la copia de R2 con aviso de cambios del INE (T-323, D-112).

PROYECTO: Diputado de Distrito
VERSIÓN: 1.4.0
NOMBRE DE VERSIÓN: P10 lee de R2 y consulta el INE sin descargar
FECHA: 2026-11-14
ESTADO: candidato
CAMBIOS: 1.4.0: (T-323b) un extracto de referencia ilegible degrada a aviso; los extractos se comparan en forma canónica (tabulador, sin BOM; la copia de R2 va con tabulador y el INE con ';'). (D-119, matiza D-117) la parada del padrón 65034 se aplica al sha256 del EXTRACTO filtrado que entra al motor (misma función
  `_filter_population` de la adquisición, mismas reglas Periodo/Sexo/Edad y provincias del contrato), comparado con el extracto del paquete de R2 del
  contrato; el crudo solo se informa (sha256 normalizado y bytes). Distinto = FUENTE_INE_CAMBIADA (54); igual con crudo distinto = sigue con ::notice::.
  El crudo se lee en streaming (se pre-filtra por filas pertinentes y no se guarda): el coste es el ancho de banda (~1,6 GB), no disco ni memoria.
  1.3.0: (D-112, decisión del propietario) el padrón 65034 se descarga SIEMPRE entero y se compara su sha256 (con ';' → tabulador, como la copia de R2) con
  `contenido_sha256` del índice; distinto = FUENTE_INE_CAMBIADA (54). Coste: ~1,6 GB de descarga por P10 que usa R2. Los .zip siguen con HEAD.
  1.2.0: (T-336) un paquete de R2 cuyo territory_id no es exactamente el canónico no es reutilizable: aviso y ACQUIRE; el resumen del job dice REUTILIZÓ desde R2.
  1.1.0: (1) el paquete de R2 solo se usa si edición y años pedidos son los del contrato; si no, aviso y adquisición como antes. (2) Last-Modified ya no
  para por sí solo (el INE sirve 65034.csv dinámico, sin Content-Length: medido 2026-11-14, Last-Modified 2026-10-27): solo aviso; para solo un Content-Length
  distinto de `bytes` en un .zip. (3) BadZipFile = paquete corrupto (53).
  1.0.0: fichero nuevo (T-323).
MOTIVO: D-112: P10 no descarga del INE en cada ejecución; usa el paquete de R2 (clave por package_sha256 del contrato, sha256 verificado) y
  solo consulta el INE con HEAD (Content-Length, Last-Modified) frente a la huella del índice orchestracion/fuentes_r2.json.
ANTERIOR: ninguna (fichero nuevo; 1.0.0 solo existió en esta PR)
QUÉ HACE: `preparar`: 1) restaura el paquete P10 del contrato desde R2 y lo valida (bateria_motor.paquete_p10_desde_r2); sin paquete o sin
  credenciales: aviso y `desde_r2=false` (P10 adquiere como hasta ahora). 2) con paquete, consulta el INE (HEAD, sin descargar): fichero
  cambiado = evidencia positiva (Content-Length de un .zip distinto de `bytes`) → `::error::FUENTE_INE_CAMBIADA`, salida 54, sin sustituir nada (decide el propietario).
  Padrón 65034.csv (dinámico, sin Content-Length ni ETag, Last-Modified no fiable): se lee entero en streaming, se filtra como lo hace la adquisición y se compara el sha256 del extracto con el del paquete de R2.
  Sin Content-Length/Last-Modified o con el mismo tamaño no hay evidencia de cambio: aviso. Sin paquete en R2 o fallo de `aws cp` (bateria_motor lo devuelve como None) se adquiere del INE sin consultar nada. Sin respuesta,
  503, 403 o red caída → `::warning::` y sigue con R2 (política T-246: solo bloquea la evidencia positiva). Paquete corrupto: salida 53.
USO: python herramientas/p10_desde_r2.py preparar --territory aut02 --edition 2025 --population-year 2025 --section-year 2025 --out .ddd-source-package
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import sys
import urllib.error
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INDICE = ROOT / "orchestracion" / "fuentes_r2.json"
SALIDA_CAMBIADA = 54
SALIDA_CORRUPTO = 53


def head_ine(url: str, timeout: int = 30) -> tuple[int, dict]:
    """HEAD al INE sin descargar el cuerpo. Devuelve (estado, cabeceras en minúsculas)."""
    req = urllib.request.Request(url, method="HEAD", headers={"User-Agent": "DiputadoDeDistrito/2.1 (+GitHub Actions; comprobación de cambios)"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, {k.lower(): v for k, v in r.headers.items()}
    except urllib.error.HTTPError as exc:
        return exc.code, {k.lower(): v for k, v in exc.headers.items()}


def descargar_ine(url: str, timeout: int = 120):
    """GET en trozos de 1 MiB (el cuerpo no se guarda)."""
    req = urllib.request.Request(url, headers={"User-Agent": "DiputadoDeDistrito/2.1 (+GitHub Actions; huella del padrón)"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        while True:
            trozo = r.read(1 << 20)
            if not trozo:
                return
            yield trozo


def extracto_en_streaming(trozos, declaracion: dict, edicion: int, codigos: list[str]) -> dict:
    """Lee el CSV nacional en streaming (sin guardarlo), se queda con las filas pertinentes (Periodo, Sexo y Edad del contrato) y pasa
    ese subconjunto por `_filter_population` de la adquisición: devuelve el extracto que entraría al motor y la huella del crudo."""
    import codecs
    import csv
    import io
    import itertools
    from herramientas import adquirir_fuentes_oficiales as aq
    reglas = aq._population_rules(declaracion)
    crudo, estado = hashlib.sha256(), {"bytes": 0}
    decoder = codecs.getincrementaldecoder("utf-8-sig")()

    def lineas():
        resto = ""
        for t in trozos:
            estado["bytes"] += len(t)
            crudo.update(t.replace(b";", b"\t"))
            resto += decoder.decode(t)
            partes = resto.split("\n")
            resto = partes.pop()
            for linea in partes:
                yield linea + "\n"
        resto += decoder.decode(b"", final=True)
        if resto:
            yield resto

    it = lineas()
    primera = next(it, "")
    delim = aq._detect_delimiter(primera)
    lector = csv.reader(itertools.chain([primera], it), delimiter=delim)
    cab = next(lector, None)
    if not cab:
        raise ValueError("CSV de población sin cabecera")
    falta = [c for c in reglas["required_columns"] if c not in cab]
    if falta:
        raise ValueError("CSV de población sin columnas obligatorias: " + ", ".join(falta))
    ia, isx, ied = cab.index(reglas["year_col"]), cab.index(reglas["sex_col"]), cab.index(reglas["age_col"])
    salida = io.StringIO()
    w = csv.writer(salida, delimiter=delim, lineterminator="\n")
    w.writerow(cab)
    for fila in lector:
        if len(fila) <= max(ia, isx, ied):
            continue
        if (fila[ia].strip() == str(edicion) and fila[isx].strip() in reglas["sex_total_values"]
                and fila[ied].strip() in reglas["age_total_values"]):
            w.writerow(fila)
    extracto, _ = aq._filter_population(salida.getvalue().encode("utf-8"), declaracion, edicion, codigos)
    return {"extracto": extracto, "extracto_sha256": hashlib.sha256(extracto).hexdigest(),
            "crudo_sha256": crudo.hexdigest(), "crudo_bytes": estado["bytes"]}


def canonico(extracto: bytes) -> bytes:
    """Forma comparable de un extracto: sin BOM, delimitador tabulador y fin de línea «\\n». La copia de R2 del padrón va con tabulador y el INE
    sirve ';': sin esto un paquete con tabulador daría un falso FUENTE_INE_CAMBIADA (54). Solo cambia el delimitador, no los valores."""
    import csv
    import io
    from herramientas import adquirir_fuentes_oficiales as aq
    texto = extracto.decode("utf-8-sig")
    if not texto.strip():
        return b""
    delim = aq._detect_delimiter(texto)
    salida = io.StringIO()
    csv.writer(salida, delimiter="\t", lineterminator="\n").writerows(csv.reader(io.StringIO(texto, newline=""), delimiter=delim))
    return salida.getvalue().encode("utf-8")


def extracto_de_paquete(carpeta: Path) -> bytes | None:
    """Extracto de población (65034.csv) que lleva el paquete P10 restaurado, o None si no se encuentra uno único."""
    import io
    manifiesto = json.loads((carpeta / "manifest.json").read_text(encoding="utf-8"))
    with zipfile.ZipFile(carpeta / str(manifiesto["path"])) as bundle:
        nombres = [n for n in bundle.namelist() if n.endswith("65034.csv.zip") or n.endswith("65034.csv")]
        if len(nombres) != 1:
            return None
        datos = bundle.read(nombres[0])
    if zipfile.is_zipfile(io.BytesIO(datos)):
        with zipfile.ZipFile(io.BytesIO(datos)) as z:
            miembros = [n for n in z.namelist() if n.lower().endswith(".csv") and "__macosx/" not in n.lower()]
            if len(miembros) != 1:
                return None
            return z.read(miembros[0])
    return datos


def fuentes_necesarias(population_year: str, section_year: str, indice: Path = INDICE) -> tuple[list[str], list[str]]:
    """(nombres del índice que consume el territorio, nombres que faltan en el índice)."""
    fuentes = json.loads(indice.read_text(encoding="utf-8"))["fuentes"]
    pedidos = [f"seccionado_{section_year}.zip", "65034.csv.zip"]
    return [n for n in pedidos if n in fuentes], [n for n in pedidos if n not in fuentes]


def comprobar_ine(nombres: list[str], head=head_ine, indice: Path = INDICE, descargar=descargar_ine, padron=None) -> tuple[list[str], list[str]]:
    """`padron` = (extracto de referencia del paquete de R2 o None, declaración, edición, códigos de provincia)."""

    """(cambiadas, avisos). Cambiada = evidencia positiva: Content-Length de un .zip distinto de `bytes`. Cualquier otra cosa (red, 5xx, 403, 404, sin cabeceras) es solo un aviso."""
    fuentes = json.loads(indice.read_text(encoding="utf-8"))["fuentes"]
    cambiadas, avisos = [], []
    for n in nombres:
        f = fuentes[n]
        url = f["origen_url"]
        if f.get("contenido_sha256"):
            referencia, declaracion, edicion, codigos = padron or (None, None, None, None)
            if referencia is None or declaracion is None:
                avisos.append(f"{n}: sin extracto de referencia en el paquete de R2 o sin declaración territorial; no se puede comprobar si el padrón cambió")
                continue
            try:
                r = extracto_en_streaming(descargar(url), declaracion, edicion, codigos)
            except Exception as exc:  # noqa: BLE001 - sin red al INE o CSV ilegible: se degrada (T-246)
                avisos.append(f"{n}: no se pudo leer el padrón del INE ({exc}); no se puede comprobar si cambió")
                continue
            try:
                esperado = hashlib.sha256(canonico(referencia)).hexdigest()
                vivo = hashlib.sha256(canonico(r["extracto"])).hexdigest()
            except Exception as exc:  # noqa: BLE001 - extracto de referencia ilegible (no UTF-8 / no CSV delimitado): se degrada, no se rompe
                avisos.append(f"{n}: el extracto de referencia del paquete de R2 no es un CSV legible ({exc}); no se puede comprobar si el padrón cambió")
                continue
            crudo_igual = r["crudo_sha256"] == f["contenido_sha256"]
            info = f"crudo sha256 {r['crudo_sha256']} ({r['crudo_bytes']} bytes), {'igual' if crudo_igual else 'distinto'} del de la copia"
            if vivo != esperado:
                cambiadas.append(f"{n} (extracto filtrado sha256 {vivo} != {esperado}; {info})")
            else:
                print(f"::notice::P10_PADRON_EXTRACTO_IGUAL {n}: extracto {esperado}; " + ("crudo igual" if crudo_igual else "crudo cambió, extracto igual") + f" ({info})")
            continue
        try:
            estado, h = head(url)
        except Exception as exc:  # noqa: BLE001 - sin red al INE: se degrada
            avisos.append(f"{n}: sin respuesta del INE ({exc}); no se puede comprobar si cambió")
            continue
        if not 200 <= estado < 300:
            avisos.append(f"{n}: el INE respondió {estado}; no se puede comprobar si cambió")
            continue
        motivos = []
        cl = h.get("content-length")
        if url.lower().endswith(".zip") and cl and cl.isdigit() and int(cl) != int(f["bytes"]):
            motivos.append(f"tamaño {cl} != {f['bytes']}")
        lm = h.get("last-modified")
        if lm and (not cl or not url.lower().endswith(".zip")):
            avisos.append(f"{n}: Last-Modified {lm} (copia de {f['descargado_en']}); no se usa para parar: no es fiable en este endpoint, se comprueba solo el tamaño de los .zip")
        if not cl and not lm:
            avisos.append(f"{n}: el INE no devolvió Content-Length ni Last-Modified; no se puede comprobar")
        if motivos:
            cambiadas.append(f"{n} ({'; '.join(motivos)})")
    return cambiadas, avisos


def anios_contrato(territorio: str) -> tuple[str, str, str]:
    """(edición, año de población, año de seccionado) del contrato del territorio, como los usa la validación del paquete."""
    from herramientas import bateria_motor as bm
    return tuple(bm._anios_fuentes(territorio))  # type: ignore[return-value]


def _salida(clave: str, valor: str) -> None:
    ruta = os.environ.get("GITHUB_OUTPUT")
    if ruta:
        with open(ruta, "a", encoding="utf-8") as fh:
            fh.write(f"{clave}={valor}\n")


def preparar(territorio: str, edicion: str, anio_poblacion: str, anio_seccion: str, destino: Path, *, restaurar=None, head=head_ine,
             indice: Path = INDICE, anios=None, descargar=descargar_ine, declaracion=None,
             declaracion_ruta: Path | None = None) -> int:
    from herramientas import bateria_motor as bm
    restaurar = restaurar or bm.paquete_p10_desde_r2
    work = destino.parent / "_p10_r2"
    pedido = (str(edicion), str(anio_poblacion), str(anio_seccion))
    try:
        contrato = (anios or anios_contrato)(territorio)
    except Exception as exc:  # noqa: BLE001 - sin contrato legible no hay paquete que reutilizar
        contrato = None
        print(f"::warning::P10_R2_SIN_CONTRATO {territorio}: {exc}")
    if contrato != pedido:
        print(f"::warning::P10_R2_ANIOS_DISTINTOS {territorio}: se pide (edición, población, sección)={pedido} y el contrato de R2 es {contrato}; "
              "no se usa el paquete de R2 y P10 adquiere de la fuente oficial como hasta ahora.")
        _salida("desde_r2", "false")
        return 0
    try:
        carpeta = restaurar(territorio, work)
    except (bm.PaqueteP10Corrupto, zipfile.BadZipFile) as exc:
        print(f"::error::P10_PAQUETE_R2_CORRUPTO {territorio}: {exc}", file=sys.stderr)
        _salida("desde_r2", "false")
        return SALIDA_CORRUPTO
    if carpeta is None:
        print(f"::warning::P10_SIN_PAQUETE_R2 {territorio}: no hay paquete en R2, falló la lectura de R2 o faltan credenciales; P10 adquiere del INE SIN comprobar nada contra R2.")
        _salida("desde_r2", "false")
        return 0
    from herramientas.politica_reutilizacion_fuentes import paquete_territory_mismatch
    mismatch = paquete_territory_mismatch(carpeta, territorio)
    if mismatch:
        print(f"::warning::P10_R2_ID_NO_CANONICO {territorio}: el paquete de R2 no es del id canónico ({'; '.join(mismatch)}); no se reutiliza y P10 adquiere de la fuente oficial (T-336).")
        shutil.rmtree(work, ignore_errors=True)
        _salida("desde_r2", "false")
        return 0
    nombres, faltan = fuentes_necesarias(anio_poblacion, anio_seccion, indice)
    for n in faltan:
        print(f"::warning::P10_FUENTE_SIN_HUELLA {n} no está en fuentes_r2.json: no se comprueba si el INE cambió.")
    padron = None
    try:
        if declaracion is None and declaracion_ruta is not None and declaracion_ruta.is_file():
            import yaml
            declaracion = yaml.safe_load(declaracion_ruta.read_text(encoding="utf-8"))
        if declaracion is not None:
            codigos = [str(c["code"]).zfill(2) for c in (declaracion.get("territory") or {}).get("territorial_codes") or []]
            padron = (extracto_de_paquete(carpeta), declaracion, int(anio_poblacion), codigos)
    except Exception as exc:  # noqa: BLE001 - sin referencia no hay comparación: aviso, no parada
        print(f"::warning::P10_PADRON_SIN_REFERENCIA {territorio}: {exc}")
    cambiadas, avisos = comprobar_ine(nombres, head, indice, descargar, padron)
    for a in avisos:
        print(f"::warning::P10_INE_SIN_COMPROBAR {a}")
    if cambiadas:
        print("::error::FUENTE_INE_CAMBIADA " + "; ".join(cambiadas) + ". P10 se detiene: no se sigue con datos viejos ni se sustituye en silencio. "
              "El propietario decide si se adopta la versión nueva (D-112).", file=sys.stderr)
        _salida("desde_r2", "false")
        return SALIDA_CAMBIADA
    shutil.rmtree(destino, ignore_errors=True)
    shutil.copytree(carpeta, destino)
    shutil.rmtree(work, ignore_errors=True)
    resumen = os.environ.get("GITHUB_STEP_SUMMARY")
    if resumen:
        with open(resumen, "a", encoding="utf-8") as fh:
            fh.write(f"### Fuentes del P10: REUTILIZÓ desde R2\n- Paquete del contrato de {territorio} (sha256 verificado, territory_id canónico); INE consultado sin descargar.\n")
    print(f"p10_desde_r2: {territorio} restaurado desde R2 (sha256 verificado); INE sin cambios detectados ({len(nombres)} fuentes consultadas).")
    _salida("desde_r2", "true")
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("preparar")
    for k in ("territory", "edition", "population-year", "section-year", "out"):
        p.add_argument("--" + k, required=True)
    p.add_argument("--declaration", default=".ddd-generated-sources/fuentes_territorio.yaml")
    a = ap.parse_args(argv)
    return preparar(a.territory, a.edition, a.population_year, a.section_year, Path(a.out), declaracion_ruta=Path(a.declaration))


if __name__ == "__main__":
    raise SystemExit(main())
