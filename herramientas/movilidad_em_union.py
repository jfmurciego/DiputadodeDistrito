#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Movilidad INE (EM-1, telefonía móvil): conversión a CSV, unión flujos↔áreas y estadísticas por provincia (T-139, paso 1).

PROYECTO: Diputado de Distrito
VERSIÓN: 1.2.0 · FECHA: 2026-11-10 · ESTADO: candidato
ANTERIOR: legacy/herramientas/movilidad_em_union_v1.1.0.py (1.1.0: indicador; 1.0.0: convertir, verificar, candidatas)
QUÉ HACE: (1) `convertir`: xlsx del INE -> CSV en `datos/movilidad/` + MANIFEST con sha256 de origen y de salida;
  (2) `verificar`: unión código de flujo (`001A`) -> `ID_GRUPO` (`01VI`) por nombre normalizado, exige biyección;
  (3) `candidatas`: por provincia, población en áreas que el plan vigente parte entre distritos;
  (5) `compacidad` (baja el M06 vigente: necesita `gh` y GH_TOKEN) y `tabla` (paso 3: relación indicador/población/compacidad).
  (4) `indicador`: cohesión funcional por distrito y plan (1.1.0, T-139 paso 2), con y sin la capital.
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
import sys as _sys
_RAIZ = str(Path(__file__).resolve().parents[1])
if _RAIZ not in _sys.path:
    _sys.path.insert(0, _RAIZ)
from ddd_core import territorio_ids  # noqa: E402  (T-220: ámbito e ids por el resolutor, nunca por prefijo)

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "herramientas"))
from numeracion_publica import numero_publico  # noqa: E402  (distritos 1..K en lo que sale del módulo)
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
        w.writerow(["cumun", "nmun", "cpro", "tipo", "id_area_geo", "pob_area_geo", "id_grupo", "pob_grupo", "literal_grupo"])
        for r in filas:
            w.writerow([r[0], r[3], r[1], r[4], r[5], r[6], r[8], r[9], r[11]])
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


CAPITALES = {"nac11": "Cádiz", "nac18": "Granada", "nac24": "León",
             "nac17": "Girona", "nac43": "Tarragona"}  # nombre oficial en el xlsx del INE


def codigo_capital(areas: list[dict], nombre: str, cpro: str) -> str:
    c = {a["cumun"] for a in areas if a["cpro"] == cpro and normalizar(a["nmun"]) == normalizar(nombre)}
    if len(c) != 1:
        raise ValueError(f"capital no única: {nombre} {sorted(c)}")
    return next(iter(c))


def indicador_plan(csv_composicion: Path, areas: list[dict], flujos: list[dict], mapa: dict[str, str],
                   capital: str | None = None) -> dict:
    """Cohesión funcional del plan: de los flujos entre áreas DISTINTAS con origen y destino en el territorio,
    fracción que queda dentro del mismo distrito. Un área partida por el plan reparte su peso entre distritos
    en proporción a su población (hipótesis, declarada). Con `capital` (código INE de municipio) se
    excluyen los flujos de los grupos que lo contienen, en origen o destino."""
    ind = indice_secciones(areas)
    peso: dict[str, dict] = defaultdict(lambda: defaultdict(float))
    for r in leer_csv(csv_composicion):
        g = grupo_de_seccion(r["seccion"], ind)
        if g:
            peso[g[0]][r["distrito"]] += int(r["poblacion"])
    for g, d in peso.items():
        t = sum(d.values())
        for k in d:
            d[k] /= t
    excluir = set()
    if capital:
        excluir = {a["id_grupo"] for a in areas if a["cumun"] == capital}
    por_dist = defaultdict(lambda: [0.0, 0.0])  # distrito -> [flujo interno, flujo con destino en el territorio]
    fuera = dentro = 0.0
    for f in flujos:
        o, d = mapa.get(f["cod_origen"]), mapa.get(f["cod_destino"])
        if o is None or o == d or o not in peso or o in excluir:
            continue
        n = float(f["flujo"])
        if d not in peso or d in excluir:
            if d not in excluir:
                fuera += n * 1.0
            continue
        dentro += n
        for k, wo in peso[o].items():
            por_dist[k][1] += n * wo
            por_dist[k][0] += n * wo * peso[d].get(k, 0.0)
    tot_i = sum(v[0] for v in por_dist.values())
    tot_t = sum(v[1] for v in por_dist.values())
    return {"distritos": {k: (v[0] / v[1] if v[1] else None, round(v[1])) for k, v in sorted(por_dist.items(), key=lambda kv: int(kv[0]))},
            "plan": tot_i / tot_t if tot_t else None, "flujo_en_territorio": round(dentro),
            "flujo_hacia_fuera": round(fuera)}


def cmd_indicador(areas: list[dict]) -> None:
    flujos = leer_csv(FLUJOS_CSV)
    mapa = unir(areas, leer_csv(CODIGOS_CSV))
    w = csv.writer(sys.stdout, lineterminator="\n")
    w.writerow(["territorio", "capital", "ambito", "distrito", "cohesion", "flujo_salida"])
    for t, nombre in CAPITALES.items():
        cpro = leer_csv(COMPOSICION / f"{t}.csv")[0]["seccion"][:2]
        cap = codigo_capital(areas, nombre, cpro)
        for etiqueta, c in (("con", None), ("sin", cap)):
            r = indicador_plan(COMPOSICION / f"{t}.csv", areas, flujos, mapa, c)
            for d, (v, n) in r["distritos"].items():
                w.writerow([t, etiqueta, "distrito", numero_publico(int(d)), f"{v:.4f}" if v is not None else "", n])
            w.writerow([t, etiqueta, "plan", "", f"{r['plan']:.4f}", r["flujo_en_territorio"]])
            w.writerow([t, etiqueta, "hacia_fuera", "", "", r["flujo_hacia_fuera"]])


COMPACIDAD_CSV = DIR / "piloto_compacidad_m06.csv"


def rangos(v: list[float]) -> list[float]:
    o = sorted(range(len(v)), key=lambda i: v[i])
    r = [0.0] * len(v)
    i = 0
    while i < len(o):
        j = i
        while j + 1 < len(o) and v[o[j + 1]] == v[o[i]]:
            j += 1
        for k in range(i, j + 1):
            r[o[k]] = (i + j) / 2 + 1
        i = j + 1
    return r


def spearman(x: list[float], y: list[float]) -> float:
    rx, ry = rangos(x), rangos(y)
    n = len(x)
    mx, my = sum(rx) / n, sum(ry) / n
    num = sum((a - mx) * (b - my) for a, b in zip(rx, ry))
    den = (sum((a - mx) ** 2 for a in rx) * sum((b - my) ** 2 for b in ry)) ** 0.5
    return num / den if den else float("nan")


def cmd_compacidad() -> None:
    import io
    import zipfile
    sys.path.insert(0, str(ROOT / "herramientas"))
    import composicion_m06 as c06
    prods = c06.m06_vigentes()
    w = csv.writer(sys.stdout, lineterminator="\n")
    w.writerow(["territorio", "distrito", "poblacion_m06", "polsby_popper_m06", "run_id", "blob_sha", "sha256_zip_m06"])
    for t in CAPITALES:
        p = prods[t]
        b = c06.bajar_blob(p)
        h = hashlib.sha256(b).hexdigest()
        if h != p["sha256"]:
            raise ValueError(f"{t}: sha256 del blob distinto del registro")
        z = zipfile.ZipFile(io.BytesIO(b))
        gj = json.loads(z.read(next(n for n in z.namelist() if n.endswith(".geojson"))))
        for ft in sorted(gj["features"], key=lambda f: f["properties"]["district_id"]):
            q = ft["properties"]
            w.writerow([t, numero_publico(int(q["district_id"])), q["district_pop"], f"{q['polsby_popper']:.4f}",
                        p["run_id"], p["blob_sha"], h])


def cmd_tabla(areas: list[dict]) -> None:
    ind = defaultdict(dict)
    for r in leer_csv(DIR / "piloto_indicador_em1.csv"):
        if r["ambito"] == "distrito" and r["cohesion"]:
            ind[(r["territorio"], r["capital"])][int(r["distrito"])] = float(r["cohesion"])
    plan = {(r["territorio"], r["capital"]): float(r["cohesion"]) for r in leer_csv(DIR / "piloto_indicador_em1.csv")
            if r["ambito"] == "plan"}
    comp = defaultdict(dict)
    for r in leer_csv(COMPACIDAD_CSV):
        comp[r["territorio"]][int(r["distrito"])] = (int(r["poblacion_m06"]), float(r["polsby_popper_m06"]))
    w = csv.writer(sys.stdout, lineterminator="\n")
    w.writerow(["territorio", "K", "poblacion", "pp_medio_m06", "pp_min_m06", "cohesion_plan_con", "cohesion_plan_sin",
                "rho_cohesion_con_vs_pp", "rho_cohesion_sin_vs_pp", "rho_cohesion_con_vs_poblacion_distrito", "n"])
    todo = defaultdict(list)
    for t in CAPITALES:
        ds = sorted(comp[t])
        pob = sum(comp[t][d][0] for d in ds)
        pps = [comp[t][d][1] for d in ds]
        fila = [t, len(ds), pob, f"{sum(pps) / len(pps):.3f}", f"{min(pps):.3f}",
                f"{plan[(t, 'con')]:.3f}", f"{plan[(t, 'sin')]:.3f}"]
        rs = []
        for cap in ("con", "sin"):
            dd = [d for d in ds if d in ind[(t, cap)]]
            rs.append(spearman([ind[(t, cap)][d] for d in dd], [comp[t][d][1] for d in dd]) if len(dd) > 2 else float("nan"))
            for d in dd:
                todo[cap].append((ind[(t, cap)][d], comp[t][d][1], comp[t][d][0]))
        dd = [d for d in ds if d in ind[(t, "con")]]
        rp = spearman([ind[(t, "con")][d] for d in dd], [comp[t][d][0] for d in dd]) if len(dd) > 2 else float("nan")
        w.writerow(fila + [f"{rs[0]:.2f}", f"{rs[1]:.2f}", f"{rp:.2f}", len(dd)])
    for cap in ("con", "sin"):
        v = todo[cap]
        w.writerow([f"TODOS_{cap}", "", "", "", "", "", "", f"{spearman([a for a, _, _ in v], [b for _, b, _ in v]):.2f}"
                    if cap == "con" else "", f"{spearman([a for a, _, _ in v], [b for _, b, _ in v]):.2f}" if cap == "sin" else "",
                    f"{spearman([a for a, _, _ in v], [c for _, _, c in v]):.2f}" if cap == "con" else "", len(v)])


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sp = ap.add_subparsers(dest="cmd", required=True)
    c = sp.add_parser("convertir")
    c.add_argument("areas_xlsx", type=Path)
    c.add_argument("flujos_xlsx", type=Path)
    c.add_argument("--origen-json", type=Path, required=True)
    sp.add_parser("verificar")
    sp.add_parser("candidatas")
    sp.add_parser("indicador")
    sp.add_parser("compacidad")
    sp.add_parser("tabla")
    a = ap.parse_args(argv)
    if a.cmd == "convertir":
        convertir(a.areas_xlsx, a.flujos_xlsx, json.loads(a.origen_json.read_text(encoding="utf-8")))
        return 0
    if a.cmd == "compacidad":
        cmd_compacidad()
        return 0
    areas = leer_csv(AREAS_CSV)
    if a.cmd == "tabla":
        cmd_tabla(areas)
        return 0
    if a.cmd == "verificar":
        m = unir(areas, leer_csv(CODIGOS_CSV))
        print(f"unión OK: {len(m)} códigos de flujo <-> {len({x['id_grupo'] for x in areas})} grupos (biyección)")
        return 0
    if a.cmd == "indicador":
        cmd_indicador(areas)
        return 0
    ind = indice_secciones(areas)
    w = csv.writer(sys.stdout, lineterminator="\n")
    cols = None
    for p in sorted(p for p in COMPOSICION.glob("*.csv") if territorio_ids.es_nacional(p.stem)):
        e = estadisticas_provincia(p, ind)
        if cols is None:
            cols = ["territorio"] + list(e)
            w.writerow(cols)
        w.writerow([p.stem] + list(e.values()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
