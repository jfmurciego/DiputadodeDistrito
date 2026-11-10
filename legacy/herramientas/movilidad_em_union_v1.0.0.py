#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Movilidad INE (EM-1, telefonía móvil): conversión a CSV, unión flujos↔áreas y estadísticas por provincia (T-139, paso 1).

PROYECTO: Diputado de Distrito
VERSIÓN: 1.0.0 · FECHA: 2026-11-10 · ESTADO: candidato
ANTERIOR: ninguna (fichero nuevo)
QUÉ HACE: (1) `convertir`: xlsx del INE -> CSV en `datos/movilidad/` + MANIFEST con sha256 de origen y de salida;
  (2) `verificar`: unión código de flujo (`001A`) -> `ID_GRUPO` (`01VI`) por nombre normalizado, exige biyección;
  (3) `candidatas`: por provincia, población en áreas que el plan vigente parte entre distritos.
  Solo indicador de investigación: no toca el motor ni la función de calidad; nada se publica.
FUENTE: https://www.ine.es/experimental/movilidad/experimental_em1.htm (CC BY 4.0, estadística experimental).
LÍMITES: flujos de menos de 16 personas ausentes; datos 2019 a mar-2020; áreas SCD (secciones dispersas de 16 municipios)
  sin correspondencia con secciones: se cuentan aparte como `sin_area`.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import sys
import unicodedata
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIR = ROOT / "datos" / "movilidad"
AREAS_CSV = DIR / "areas_movilidad_2019.csv"
FLUJOS_CSV = DIR / "flujos_em1_origen_destino.csv"
CODIGOS_CSV = DIR / "codigos_flujo.csv"
PSEUDO = {"OTRO"}  # «OTROS DESTINOS»: agregado del INE sin área; se cuenta aparte, no se une
MANIFEST = DIR / "MANIFEST.json"
COMPOSICION = ROOT / "datos" / "composicion"


def normalizar(s: str) -> str:
    return re.sub(r"\s+", " ", unicodedata.normalize("NFC", s or "")).strip().lower()


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def leer_csv(p: Path) -> list[dict]:
    with open(p, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def unir(areas: list[dict], codigos: list[dict]) -> dict[str, str]:
    """codigo de flujo -> ID_GRUPO. Exige correspondencia 1 a 1 por nombre normalizado (salvo pseudo-códigos)."""
    por_nombre: dict[str, set] = defaultdict(set)
    for a in areas:
        por_nombre[normalizar(a["literal_grupo"])].add(a["id_grupo"])
    mapa: dict[str, str] = {}
    for r in codigos:
        c, n = r["codigo"], r["nombre"]
        if c in PSEUDO:
            continue
        g = por_nombre.get(normalizar(n), set())
        if len(g) != 1:
            raise ValueError(f"sin unión única: {c} {n!r} -> {sorted(g)}")
        mapa[c] = next(iter(g))
    if len(set(mapa.values())) != len(mapa):
        raise ValueError("la unión no es inyectiva")
    return mapa


def convertir(areas_xlsx: Path, flujos_xlsx: Path, origen: dict) -> None:
    import openpyxl  # solo aquí: dependencia de la conversión, no del análisis

    DIR.mkdir(parents=True, exist_ok=True)
    wb = openpyxl.load_workbook(areas_xlsx, read_only=True)
    filas = list(wb["NACIONAL_MOVILES"].iter_rows(values_only=True))[1:]
    with open(AREAS_CSV, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["cumun", "cpro", "tipo", "id_area_geo", "pob_area_geo", "id_grupo", "pob_grupo", "literal_grupo"])
        for r in filas:
            w.writerow([r[0], r[1], r[4], r[5], r[6], r[8], r[9], r[11]])
    ws = openpyxl.load_workbook(flujos_xlsx, read_only=True).worksheets[0]
    cods: dict[str, tuple] = {}
    with open(FLUJOS_CSV, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["cod_origen", "cod_destino", "flujo"])
        for r in list(ws.iter_rows(values_only=True))[1:]:
            for c, n, p in ((r[2], r[3], r[1]), (r[6], r[7], r[5])):
                if cods.setdefault(c, (n, p)) != (n, p):
                    raise ValueError(f"código de flujo con dos nombres: {c}")
            w.writerow([r[2], r[6], r[8]])
    with open(CODIGOS_CSV, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["codigo", "nombre", "provincia"])
        for c in sorted(cods):
            w.writerow([c, *cods[c]])
    man = dict(origen)
    man["salida"] = {p.name: sha256(p) for p in (AREAS_CSV, FLUJOS_CSV, CODIGOS_CSV)}
    MANIFEST.write_text(json.dumps(man, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


def indice_secciones(areas: list[dict]) -> dict[str, tuple[str, str]]:
    """Clave (10, 7 o 5 cifras) -> (id_grupo, tipo). SCD (11 caracteres) no se puede casar con secciones."""
    ind = {}
    for a in areas:
        if a["tipo"] in ("SECCIÓN", "DISTRITO", "MUNICIPIO"):
            ind[a["id_area_geo"]] = (a["id_grupo"], a["tipo"])
    return ind


def grupo_de_seccion(sec: str, ind: dict) -> tuple[str, str] | None:
    for k in (sec[:10], sec[:7], sec[:5]):
        if k in ind:
            return ind[k]
    return None


def estadisticas_provincia(csv_composicion: Path, ind: dict) -> dict:
    """Población (secciones del plan vigente) y cuánto del plan corta las áreas de movilidad."""
    filas = leer_csv(csv_composicion)
    grupos: dict[str, dict] = defaultdict(lambda: defaultdict(int))
    mun = defaultdict(int)
    mun_sin_area: dict[str, set] = defaultdict(set)
    sin_area = sub = total = 0
    for r in filas:
        s, d, p = r["seccion"], r["distrito"], int(r["poblacion"])
        total += p
        mun[s[:5]] += p
        g = grupo_de_seccion(s, ind)
        if g is None:
            sin_area += p
            mun_sin_area[s[:5]].add(d)
            continue
        grupos[g[0]][d] += p
        if g[1] != "MUNICIPIO":
            sub += p
    partida = sum(sum(v.values()) for v in grupos.values() if len(v) > 1)
    sin_area_partida = sum(mun[m] for m, ds in mun_sin_area.items() if len(ds) > 1)
    mayores = sorted(mun.values(), reverse=True) + [0, 0]
    return {"poblacion": total, "K": len({r["distrito"] for r in filas}), "municipios": len(mun),
            "pob_mun_1": mayores[0], "pob_mun_2": mayores[1], "pob_mun_3": mayores[2],
            "pob_en_municipios_con_areas_internas": sub, "pob_sin_area": sin_area,
            "pob_sin_area_en_municipios_partidos": sin_area_partida,
            "pob_en_areas_partidas_por_el_plan": partida, "n_areas": len(grupos)}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sp = ap.add_subparsers(dest="cmd", required=True)
    c = sp.add_parser("convertir")
    c.add_argument("areas_xlsx", type=Path)
    c.add_argument("flujos_xlsx", type=Path)
    c.add_argument("--origen-json", type=Path, required=True)
    sp.add_parser("verificar")
    sp.add_parser("candidatas")
    a = ap.parse_args(argv)
    if a.cmd == "convertir":
        convertir(a.areas_xlsx, a.flujos_xlsx, json.loads(a.origen_json.read_text(encoding="utf-8")))
        return 0
    areas = leer_csv(AREAS_CSV)
    if a.cmd == "verificar":
        m = unir(areas, leer_csv(CODIGOS_CSV))
        print(f"unión OK: {len(m)} códigos de flujo <-> {len({x['id_grupo'] for x in areas})} grupos (biyección)")
        return 0
    ind = indice_secciones(areas)
    w = csv.writer(sys.stdout, lineterminator="\n")
    cols = None
    for p in sorted(COMPOSICION.glob("congreso_*.csv")):
        e = estadisticas_provincia(p, ind)
        if cols is None:
            cols = ["territorio"] + list(e)
            w.writerow(cols)
        w.writerow([p.stem] + list(e.values()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
