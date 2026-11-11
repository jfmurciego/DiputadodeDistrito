#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Datos abiertos y fichas por distrito de las provincias nacionales completas (T-60).

PROYECTO: Diputado de Distrito
VERSIÓN: 1.2.0 · FECHA: 2026-11-10 · ESTADO: candidato
ANTERIOR: legacy/herramientas/generar_datos_abiertos_v1.1.0_20261110.py
CAMBIOS 1.2.0 (T-201): `vigentes_m06(registro, eleccion)` elige por (territorio, elección), por defecto 2023-07-23; una entrada de otra
  elección no desplaza a la vigente. Salida idéntica si el registro no trae elecciones.
CAMBIOS 1.1.0 (T-135): distritos numerados de 1 a K en CSV, fichas, INDEX.json, README y GeoJSON público (derivado del blob M06
  con propiedad `distrito`; su sha256 va en geojson.sha256 y el del GeoJSON M06 de origen en geojson.sha256_origen). El blob M06 no cambia.
QUÉ HACE: por cada territorio congreso_* con M06 y M08 vigentes (mismo run) en orchestracion/publicaciones_visor.json:
  - lee el M06 (blob inmutable, verificado con su sha256) y toma población, secciones y municipios de cada distrito;
  - copia el CSV de resultados de datos/resultados/ (T-53) comprobando que su manifiesto acredita el mismo run;
  - escribe datos_abiertos/<territorio>/resultados.csv, una ficha estática distrito-<n>.html por distrito y un
    índice por provincia; escribe datos_abiertos/INDEX.json (licencia, run, blob_sha, sha256 del ZIP de origen, del
    GeoJSON y del CSV), datos_abiertos/README.md (licencia CC BY 4.0) y datos_abiertos/index.html.
  El GeoJSON (~50 MB en total) no se versiona: `--materializar DIR` lo extrae del blob del registro, comprueba su sha256
  contra INDEX.json y lo deja en DIR/<territorio>/distritos.geojson junto al resto del paquete (lo usa el publicador).
  Nombres de distrito: opcionales, en datos_abiertos/nombres.json ({territorio: {"0": "nombre"}}); sin ellos la ficha
  muestra «Distrito N» y el campo nombre queda vacío en INDEX.json (T-59 los rellenará).
  Salida determinista e idempotente: un fichero que no cambia no se reescribe; un territorio con el mismo blob_sha y todos
  sus ficheros presentes no baja el blob.
Uso: python herramientas/generar_datos_abiertos.py [--salida DIR] [--cache DIR] [--m06-dir DIR] [--materializar DIR] [--comprobar]
"""
from __future__ import annotations

import argparse
import hashlib
import html
import io
import json
import shutil
import sys
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import resultados_ligeros as rl  # noqa: E402
from numeracion_publica import csv_publico, geojson_publico, numero_publico  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
SALIDA = ROOT / "datos_abiertos"
RESULTADOS = ROOT / "datos/resultados"
REGISTRO = rl.REGISTRO_VISOR
ESQUEMA = "ddd.datos-abiertos/1.1"
NUMERACION = "1..K"
LICENCIA = {"id": "CC-BY-4.0", "nombre": "Creative Commons Atribución 4.0 Internacional",
            "url": "https://creativecommons.org/licenses/by/4.0/deed.es"}
ATRIBUCION = "Diputado de Distrito (https://github.com/jfmurciego/DiputadodeDistrito)"
ELECCION = "Elecciones generales de 2023 (Congreso)"


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def escribir(ruta: Path, datos: bytes) -> None:
    if not ruta.exists() or ruta.read_bytes() != datos:
        ruta.parent.mkdir(parents=True, exist_ok=True)
        ruta.write_bytes(datos)


def vigentes_m06(registro: Path = REGISTRO, eleccion: str = rl.ELECCION_POR_DEFECTO) -> dict[str, dict]:
    return rl.vigente_por_eleccion(json.loads(registro.read_text(encoding="utf-8"))["products"], "canonical_m06",
                                   eleccion, "congreso_")


def extraer_geojson(zip_bytes: bytes) -> bytes:
    z = zipfile.ZipFile(io.BytesIO(zip_bytes))
    return z.read(next(n for n in sorted(z.namelist()) if n.endswith(".geojson")))


def etiqueta(p: dict) -> str:
    return p["territory_label"].removeprefix("Congreso ").strip()


def _e(x) -> str:
    return html.escape(str(x))


def ficha_html(prov: str, t: str, d: dict, lic: dict) -> str:
    nombre = d["nombre"] or f"Distrito {d['distrito']}"
    n = d["distrito"]
    fila = lambda k, v: f"<tr><th scope=\"row\">{_e(k)}</th><td>{_e(v)}</td></tr>"  # noqa: E731
    ganador = (f"{d['ganador']} ({d['votos_ganador']} votos, {d['porcentaje_ganador']} %)" if d["ganador"] else "sin dato")
    return f"""<!doctype html>
<html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{_e(nombre)} · {_e(prov)}</title>
<style>body{{font:16px/1.5 system-ui,sans-serif;max-width:40rem;margin:2rem auto;padding:0 1rem}}th{{text-align:left;padding-right:1rem}}</style>
</head><body>
<p><a href="index.html">← {_e(prov)}</a> · <a href="../index.html">Todas las provincias</a></p>
<h1>{_e(nombre)}</h1>
<p>Provincia de {_e(prov)}, distrito {n} de {d['total_distritos']}.</p>
<table>
{fila('Población', d['poblacion'])}
{fila('Municipios', d['municipios'])}
{fila('Secciones censales', d['secciones'])}
{fila('Ganador 2023', ganador)}
{fila('Votos totales', d['votos_totales'])}
</table>
<p>Datos: <a href="distritos.geojson">GeoJSON de distritos</a> · <a href="resultados.csv">CSV de resultados</a>.
Licencia <a href="{_e(lic['url'])}">{_e(lic['id'])}</a>; atribución: {_e(ATRIBUCION)}.
Procedencia: run {_e(d['run_id'])}, blob {_e(d['blob_sha'])}.</p>
</body></html>
"""


def indice_provincia(prov: str, ent: dict) -> str:
    li = "\n".join(f"<li><a href=\"distrito-{d['distrito']}.html\">{_e(d['nombre'] or 'Distrito ' + str(d['distrito']))}</a>"
                   f" · {_e(d['poblacion'])} hab. · {_e(d['ganador'] or '—')}</li>" for d in ent["distritos"])
    return f"""<!doctype html>
<html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{_e(prov)} · datos abiertos</title></head><body style="font:16px/1.5 system-ui,sans-serif;max-width:40rem;margin:2rem auto;padding:0 1rem">
<p><a href="../index.html">← Todas las provincias</a></p>
<h1>{_e(prov)}</h1>
<p>{ent['n_distritos']} distritos · <a href="distritos.geojson">GeoJSON</a> (sha256 {ent['geojson']['sha256'][:12]}…) ·
<a href="resultados.csv">CSV</a> (sha256 {ent['resultados']['sha256'][:12]}…)</p>
<ul>
{li}
</ul></body></html>
"""


def indice_general(idx: dict) -> str:
    li = "\n".join(f"<li><a href=\"{t}/index.html\">{_e(e['provincia'])}</a> · {e['n_distritos']} distritos</li>"
                   for t, e in idx["territorios"].items())
    return f"""<!doctype html>
<html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Datos abiertos · Diputado de Distrito</title></head><body style="font:16px/1.5 system-ui,sans-serif;max-width:40rem;margin:2rem auto;padding:0 1rem">
<h1>Datos abiertos</h1>
<p>Distritos (GeoJSON) y resultados (CSV) por provincia, con fichas por distrito. Licencia
<a href="{_e(LICENCIA['url'])}">{_e(LICENCIA['id'])}</a>. Ver <a href="README.md">README</a> e <a href="INDEX.json">INDEX.json</a>.</p>
<ul>
{li}
</ul></body></html>
"""


def readme(idx: dict) -> str:
    return f"""# Datos abiertos de Diputado de Distrito

Paquete por provincia ({len(idx['territorios'])} provincias nacionales completas) con:

- `<territorio>/distritos.geojson`: distritos del producto territorial M06 publicado (EPSG:4326 / CRS84), con la propiedad `distrito` (1..K) en lugar
  del `district_id` interno del motor; `INDEX.json` lleva su sha256 (`geojson.sha256`) y el del GeoJSON M06 de origen (`sha256_origen`).
- `<territorio>/resultados.csv`: ganador por distrito en las {ELECCION.lower()} (columnas: distrito, poblacion,
  votos_totales, ganador, votos_ganador, porcentaje_ganador). Solo consta el ganador, no los votos de cada partido.
- `<territorio>/distrito-<n>.html`: ficha estática del distrito. Los distritos se numeran de 1 a K en cada provincia
  (no existe el distrito 0); hasta la versión 1.0 del paquete se numeraban desde 0 (`distrito-0.html` pasa a ser `distrito-1.html`, etc.).
- `INDEX.json`: por territorio, run de origen, `blob_sha` del producto en git, sha256 del ZIP de origen, del GeoJSON y del CSV.

## Licencia

**{LICENCIA['nombre']} ({LICENCIA['id']})**, <{LICENCIA['url']}>. Puede copiar, redistribuir, adaptar y usar los datos,
también con fines comerciales, citando la fuente: «{ATRIBUCION}», y el run de procedencia. Se propone CC BY 4.0 por ser
la licencia abierta más usada para datos públicos y exigir solo atribución. Las fuentes oficiales subyacentes (INE,
Ministerio del Interior, BOE) conservan sus propias condiciones de reutilización.

## Verificación

`sha256sum` de cada fichero debe coincidir con `INDEX.json`. El GeoJSON procede del blob `blob_sha` del repositorio
`{rl.REPO}` (ZIP con huella `sha256_origen`).
"""


def generar(salida: Path = SALIDA, registro: Path = REGISTRO, resultados: Path = RESULTADOS,
            cache: Path | None = None, m06_dir: Path | None = None) -> dict:
    salida.mkdir(parents=True, exist_ok=True)
    previo = {}
    if (salida / "INDEX.json").exists():
        previo = json.loads((salida / "INDEX.json").read_text(encoding="utf-8")).get("territorios", {})
    nombres = {}
    if (salida / "nombres.json").exists():
        nombres = json.loads((salida / "nombres.json").read_text(encoding="utf-8"))
    man = json.loads((resultados / "MANIFEST.json").read_text(encoding="utf-8"))["territorios"]
    m8 = rl.vigentes(registro)
    terr: dict[str, dict] = {}
    for t, p6 in sorted(vigentes_m06(registro).items()):
        p8 = m8.get(t)
        if not p8 or p8["run_id"] != p6["run_id"] or t not in man or man[t]["blob_sha"] != p8["blob_sha"]:
            continue  # sin M08 del mismo run acreditado por el manifiesto de resultados
        csv_bytes = (resultados / f"{t}.csv").read_bytes()
        if sha(csv_bytes) != man[t]["sha256_csv"]:
            raise ValueError(f"CSV de {t} no coincide con datos/resultados/MANIFEST.json")
        ant = previo.get(t)
        nom_t = nombres.get(t, {})
        d_t = salida / t
        fuente = sha(csv_bytes)
        mismo = bool(ant and ant["blob_sha"] == p6["blob_sha"] and ant.get("nombres") == nom_t)
        if (mismo and ant.get("numeracion") == NUMERACION and ant["resultados"].get("fuente_sha256") == fuente
                and ant["geojson"].get("sha256_origen")
                and (d_t / "index.html").exists()
                and all((d_t / f"distrito-{d['distrito']}.html").exists() for d in ant["distritos"])):
            terr[t] = ant
            continue
        filas = {int(r.split(",")[0]): r.split(",") for r in csv_bytes.decode("utf-8").splitlines()[1:]}
        f = (m06_dir or cache or Path("/nonexistent")) / f"{t}_{p6['run_id']}.zip"
        datos = f.read_bytes() if f.exists() else (None if m06_dir else rl.bajar_blob(p6))
        if datos is None:
            continue
        if sha(datos) != p6["sha256"]:
            raise ValueError(f"SHA-256 del M06 de {t} no coincide con el registro")
        gj_bytes = extraer_geojson(datos)
        gj = json.loads(gj_bytes)
        props = sorted((f_["properties"] for f_ in gj["features"]), key=lambda x: int(x["district_id"]))
        ents = []
        for pr in props:
            i = int(pr["district_id"])  # id interno del motor (0..K-1)
            r = filas.get(i)
            ents.append({"distrito": numero_publico(i), "nombre": nom_t.get(str(i)), "poblacion": pr["district_pop"],
                         "municipios": pr.get("municipality_count"), "secciones": pr.get("section_count"),
                         "ganador": r[3] if r else "", "votos_ganador": r[4] if r else "",
                         "porcentaje_ganador": r[5] if r else "", "votos_totales": r[2] if r else ""})
        prov, run_id, blob, sha_origen = etiqueta(p6), p6["run_id"], p6["blob_sha"], p6["sha256"]
        geo = {"ruta": f"{t}/distritos.geojson", "sha256": sha(geojson_publico(gj_bytes)), "sha256_origen": sha(gj_bytes)}
        pub = csv_publico(csv_bytes)
        ent = {"provincia": prov, "run_id": run_id, "blob_sha": blob, "sha256_origen": sha_origen,
               "n_distritos": len(ents), "nombres": nom_t, "numeracion": NUMERACION,
               "geojson": geo,
               "resultados": {"ruta": f"{t}/resultados.csv", "sha256": sha(pub), "fuente_sha256": fuente,
                              "blob_sha_m08": p8["blob_sha"], "run_id": p8["run_id"]},
               "distritos": [{k: v for k, v in e.items() if k in ("distrito", "nombre", "poblacion", "municipios", "secciones", "ganador")}
                             for e in ents]}
        escribir(d_t / "resultados.csv", pub)
        for viejo in d_t.glob("distrito-*.html"):  # fichas de numeraciones anteriores (p. ej. distrito-0.html)
            if viejo.name not in {f"distrito-{e['distrito']}.html" for e in ents}:
                viejo.unlink()
        for e in ents:
            e.update(total_distritos=len(ents), run_id=run_id, blob_sha=blob)
            escribir(d_t / f"distrito-{e['distrito']}.html", ficha_html(prov, t, e, LICENCIA).encode("utf-8"))
        escribir(d_t / "index.html", indice_provincia(prov, ent).encode("utf-8"))
        terr[t] = ent
    idx = {"schema": ESQUEMA, "licencia": LICENCIA, "atribucion": ATRIBUCION, "eleccion": ELECCION,
           "origen": "orchestracion/publicaciones_visor.json (canonical_m06 + canonical_m08, mismo run)",
           "territorios": dict(sorted(terr.items()))}
    escribir(salida / "INDEX.json", (json.dumps(idx, ensure_ascii=False, indent=1) + "\n").encode("utf-8"))
    escribir(salida / "README.md", readme(idx).encode("utf-8"))
    escribir(salida / "index.html", indice_general(idx).encode("utf-8"))
    for viejo in salida.iterdir():  # territorios que ya no están vigentes
        if viejo.is_dir() and viejo.name not in terr:
            shutil.rmtree(viejo)
    return idx


def materializar(destino: Path, salida: Path = SALIDA, registro: Path = REGISTRO, cache: Path | None = None,
                 m06_dir: Path | None = None) -> int:
    """Copia el paquete y añade distritos.geojson (del blob, verificado con el registro y con INDEX.json)."""
    idx = json.loads((salida / "INDEX.json").read_text(encoding="utf-8"))
    prods = vigentes_m06(registro)
    if destino.exists():
        shutil.rmtree(destino)
    shutil.copytree(salida, destino, ignore=shutil.ignore_patterns("nombres.json"))
    for t, e in idx["territorios"].items():
        p = prods.get(t)
        if not p or p["blob_sha"] != e["blob_sha"]:
            raise ValueError(f"INDEX.json desfasado respecto al registro en {t}; regenera datos_abiertos/")
        f = (m06_dir or cache or Path("/nonexistent")) / f"{t}_{p['run_id']}.zip"
        datos = f.read_bytes() if f.exists() else rl.bajar_blob(p)
        if sha(datos) != p["sha256"]:
            raise ValueError(f"SHA-256 del M06 de {t} no coincide con el registro")
        gj = extraer_geojson(datos)
        if sha(gj) != e["geojson"].get("sha256_origen"):
            raise ValueError(f"SHA-256 del GeoJSON M06 de {t} no coincide con INDEX.json")
        pub = geojson_publico(gj)
        if sha(pub) != e["geojson"]["sha256"]:
            raise ValueError(f"SHA-256 del GeoJSON público de {t} no coincide con INDEX.json")
        (destino / t / "distritos.geojson").write_bytes(pub)
    return len(idx["territorios"])


def comprobar(salida: Path = SALIDA, registro: Path = REGISTRO) -> list[str]:
    """Sin red: INDEX.json frente al registro y los sha256 de los CSV frente al disco."""
    err = []
    idx = json.loads((salida / "INDEX.json").read_text(encoding="utf-8"))
    prods = vigentes_m06(registro)
    for t, e in idx["territorios"].items():
        if t not in prods or prods[t]["blob_sha"] != e["blob_sha"]:
            err.append(f"{t}: blob_sha desfasado respecto al registro")
        c = salida / e["resultados"]["ruta"]
        if not c.exists() or sha(c.read_bytes()) != e["resultados"]["sha256"]:
            err.append(f"{t}: CSV ausente o con otra huella")
        for d in e["distritos"]:
            if not (salida / t / f"distrito-{d['distrito']}.html").exists():
                err.append(f"{t}: falta la ficha del distrito {d['distrito']}")
    return err


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--salida", type=Path, default=SALIDA)
    ap.add_argument("--registro", type=Path, default=REGISTRO)
    ap.add_argument("--cache", type=Path)
    ap.add_argument("--m06-dir", type=Path, help="ZIP <territorio>_<run>.zip ya descargados (sin red)")
    ap.add_argument("--materializar", type=Path, help="copia el paquete a DIR con los GeoJSON verificados")
    ap.add_argument("--comprobar", action="store_true", help="solo verifica INDEX.json frente al registro y el disco")
    a = ap.parse_args(argv)
    if a.comprobar:
        err = comprobar(a.salida, a.registro)
        print("\n".join(err) or "datos_abiertos al día")
        return 1 if err else 0
    if a.materializar:
        n = materializar(a.materializar, a.salida, a.registro, a.cache, a.m06_dir)
        print(f"{n} provincias materializadas en {a.materializar}")
        return 0
    idx = generar(a.salida, a.registro, RESULTADOS, a.cache, a.m06_dir)
    print(f"{len(idx['territorios'])} provincias en {a.salida}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
