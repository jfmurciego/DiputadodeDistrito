#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Recupera la composición sección→distrito de un M06 publicado por geometría (T-71).

PROYECTO: Diputado de Distrito
VERSIÓN: 1.0.0 · FECHA: 2026-11-07 · ESTADO: candidato
ANTERIOR: ninguna (fichero nuevo)
QUÉ HACE: cuando el CSV ``*_m06_composicion_distritos.csv`` del run ya caducó (T-67), reconstruye la asignación con la
  fuente de M01: un punto interior de cada sección del seccionado INE (colección Secciones_<año>, OGC) se asigna al
  polígono de distrito del M06 publicado (blob de git, sha256 del registro del visor) y la población por sección sale
  del INE 65034 (Total, todas las edades, año de población del territorio). Se valida con
  ``composicion_m06.validar``: nº de secciones y población por distrito idénticos al M06; si no cuadra no se escribe nada
  y el territorio queda como no recuperado con el motivo. Escribe datos/composicion/<territorio>.csv y su entrada en
  MANIFEST.json con ``fuente`` (método, sha256 del seccionado y del padrón).
Uso: python herramientas/recuperar_composicion_ine.py --territorios t1,t2|todos --padron 65034.csv [--cache DIR]
  [--m06-dir DIR] [--anio-secciones 2023] [--anio-poblacion 2023] [--informe JSON]
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import re
import sys
import urllib.parse
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "herramientas"))
import composicion_m06 as cm  # noqa: E402

URL_SECCIONES = ("https://www.ine.es/geoserver/ogc/features/v1/collections/"
                 "WMS_INE_SECCIONES_G01%3ASecciones_{anio}/items")
CONTRATOS = ROOT / "configuracion/contratos_infoelectoral.yaml"
# Territorios que no son circunscripción NAC y no están en el contrato Infoelectoral.
PROVINCIAS_EXTRA = {"aut18": "51", "aut14": "30", "aut19": "52"}


def sha256(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def provincia_de(territorio: str) -> str:
    if territorio in PROVINCIAS_EXTRA:
        return PROVINCIAS_EXTRA[territorio]
    import yaml
    for r in yaml.safe_load(CONTRATOS.read_text(encoding="utf-8"))["contracts"].values():
        if r["territory_id"] == territorio:
            return str(r["province"]).zfill(2)
    raise KeyError(f"sin provincia para {territorio}")


def poblacion_padron(ruta: Path, anio: int, provincias: set[str]) -> dict[str, int]:
    """CUSEC (10 dígitos) → población (Total, todas las edades, ``anio``) del CSV 65034 (ZIP o CSV)."""
    datos = ruta.read_bytes()
    if zipfile.is_zipfile(io.BytesIO(datos)):
        z = zipfile.ZipFile(io.BytesIO(datos))
        datos = z.read(next(n for n in z.namelist() if n.endswith(".csv")))
    out: dict[str, int] = {}
    pat = re.compile(r"^(\d{10}) ")
    for linea in datos.decode("utf-8-sig").splitlines():
        c = linea.split(";")
        if len(c) < 8 or c[4] != "Total" or c[5] != "Todas las edades" or c[6] != str(anio):
            continue
        m = pat.match(c[3])
        if m and m.group(1)[:2] in provincias:
            out[m.group(1)] = int(re.sub(r"\D", "", c[7]) or 0)
    return out


def bajar_secciones(provincia: str, anio: int, cache: Path | None) -> bytes:
    f = cache / f"secciones_{anio}_{provincia}.geojson" if cache else None
    if f and f.exists():
        return f.read_bytes()
    q = urllib.parse.urlencode({"f": "application/geo+json", "filter": f"CPRO='{provincia}'",
                                "filter-lang": "cql2-text", "limit": "10000"})
    with urllib.request.urlopen(URL_SECCIONES.format(anio=anio) + "?" + q, timeout=300) as r:
        datos = r.read()
    if not json.loads(datos).get("features"):
        raise ValueError(f"INE Secciones_{anio} sin secciones para la provincia {provincia}")
    if f:
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_bytes(datos)
    return datos


def asignar(secciones: bytes, m06: bytes, pob: dict[str, int]) -> bytes:
    """CSV (CUSEC_KEY, district_id, section_pop) por punto interior de sección dentro del polígono de distrito."""
    from shapely.geometry import shape
    from shapely.ops import unary_union
    from shapely.strtree import STRtree
    z = zipfile.ZipFile(io.BytesIO(m06))
    gj = json.loads(z.read(next(n for n in sorted(z.namelist()) if n.endswith(".geojson"))))
    polis = [(int(f["properties"]["district_id"]), shape(f["geometry"]).buffer(0)) for f in gj["features"]]
    arbol = STRtree([p for _, p in polis])
    por_cusec: dict[str, list] = {}
    for f in json.loads(secciones)["features"]:
        if f["properties"].get("TIPO") not in ("SECCIONADO", "SECCION") or str(f["properties"].get("CSEC")) == "000":
            continue  # solo secciones: la colección mezcla filas DISTRITO (CSEC 000)
        por_cusec.setdefault(cm.clave_seccion(f["properties"]["CUSEC"]), []).append(shape(f["geometry"]))
    s = io.StringIO()
    w = csv.writer(s, lineterminator="\n")
    w.writerow(["CUSEC_KEY", "district_id", "section_pop"])
    for k in sorted(por_cusec):
        g = unary_union(por_cusec[k])
        pt = g.representative_point()
        cand = [i for i in arbol.query(pt) if polis[i][1].covers(pt)]
        if len(cand) != 1:  # fuera de todo polígono o en solape: el más cercano al punto, solo si es inequívoco
            raise ValueError(f"sección {k}: {len(cand)} polígonos contienen su punto interior")
        w.writerow([k, polis[cand[0]][0], pob.get(k, 0)])
    return s.getvalue().encode("utf-8")


def recuperar(territorio: str, padron: dict[str, int], sha_padron: str, cache: Path | None, salida: Path,
              registro: Path, m06_dir: Path | None, anio_sec: int) -> None:
    """Escribe la composición del territorio o lanza ValueError con el motivo."""
    vig = cm.m06_vigentes(registro)[territorio]
    f = (m06_dir / f"{territorio}_{vig['run_id']}.zip") if m06_dir else None
    m06 = f.read_bytes() if f and f.exists() else cm.bajar_blob(vig)
    if sha256(m06) != vig["sha256"]:
        raise ValueError("SHA-256 del M06 no coincide con el registro")
    prov = provincia_de(territorio)
    sec = bajar_secciones(prov, anio_sec, cache)
    filas = cm.validar(asignar(sec, m06, padron), m06)
    cuerpo = cm.csv_bytes(filas)
    salida.mkdir(parents=True, exist_ok=True)
    (salida / f"{territorio}.csv").write_bytes(cuerpo)
    ruta = salida / "MANIFEST.json"
    man = json.loads(ruta.read_text(encoding="utf-8"))
    man["territorios"][territorio] = {
        "run_id": vig["run_id"], "blob_sha": vig["blob_sha"], "sha256_m06": vig["sha256"], "secciones": len(filas),
        "sha256_csv": sha256(cuerpo),
        "fuente": {"metodo": "punto_interior_seccionado_ine", "anio_secciones": anio_sec,
                   "sha256_seccionado": sha256(sec), "sha256_padron_65034": sha_padron}}
    man["territorios"] = dict(sorted(man["territorios"].items()))
    ruta.write_text(json.dumps(man, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--territorios", required=True)
    ap.add_argument("--padron", type=Path, required=True)
    ap.add_argument("--cache", type=Path)
    ap.add_argument("--m06-dir", type=Path)
    ap.add_argument("--salida", type=Path, default=cm.SALIDA)
    ap.add_argument("--registro", type=Path, default=cm.REGISTRO_VISOR)
    ap.add_argument("--anio-secciones", type=int, default=2023)
    ap.add_argument("--anio-poblacion", type=int, default=2023)
    ap.add_argument("--informe", type=Path)
    a = ap.parse_args(argv)
    vig = cm.m06_vigentes(a.registro)
    ts = list(vig) if a.territorios.strip() == "todos" else [t.strip() for t in a.territorios.split(",")]
    ts = [t for t in ts if t in vig]
    man = json.loads((a.salida / "MANIFEST.json").read_text(encoding="utf-8"))["territorios"]
    pend = [t for t in ts if not (man.get(t, {}).get("blob_sha") == vig[t]["blob_sha"] and (a.salida / f"{t}.csv").exists())]
    padron = poblacion_padron(a.padron, a.anio_poblacion, {provincia_de(t) for t in pend})
    sha_p = sha256(a.padron.read_bytes())
    ok, mal = [], {}
    for t in pend:
        try:
            recuperar(t, padron, sha_p, a.cache, a.salida, a.registro, a.m06_dir, a.anio_secciones)
            ok.append(t)
        except Exception as e:  # noqa: BLE001 — el motivo va al informe, el territorio queda pendiente
            mal[t] = str(e)[:300]
    if a.informe:
        a.informe.write_text(json.dumps({"recuperados": ok, "no_recuperados": mal}, ensure_ascii=False, indent=1) + "\n",
                             encoding="utf-8")
    print(f"recuperados {len(ok)}: {', '.join(ok) or '-'}")
    for t, m in mal.items():
        print(f"NO {t}: {m}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
