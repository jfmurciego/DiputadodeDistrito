#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Reagregación del histórico de generales 2011-2023 a los distritos vigentes (T-83, paso B).

PROYECTO: Diputado de Distrito
VERSIÓN: 1.0.0 · FECHA: 2026-11-08 · ESTADO: candidato
CAMBIOS: 1.0.0: fichero nuevo.
MOTIVO: decisiones D-9, D-10, D-12 y D-13 del propietario: los votos de cada general 2011-2023 se trasladan a los
  distritos vigentes (sin redibujar por elección) con la equivalencia de seccionados de T-85 (peso = población).
ANTERIOR: ninguna (fichero nuevo)
QUÉ HACE: fuera de línea (no lanza ni publica). Por territorio (provincia) y elección: (1) asigna cada sección del
  seccionado INE 2025 al distrito M06 de mayor solape; (2) lleva los votos, censo y votantes de cada sección histórica
  del espejo T-89 a las secciones vigentes con `equivalencia_seccionados.equivalencia` y el peso de población (D-13);
  (3) redondea por el método del mayor resto, partido a partido, para que el total provincial no cambie;
  (4) escribe ganador y votos por partido por distrito en datos/resultados/historico/<elección>/ y el manifiesto con
  la huella (sha256) de cada fuente; (5) cuadre: el total por partido de los distritos más lo perdido es el del espejo
  (exacto) y el total del espejo frente a la fuente oficial (Infoelectoral/BOE, donde hay) con tolerancia explícita:
  el espejo suma las secciones y no incluye el voto CERA (residentes en el extranjero), así que nunca debe superar a la
  oficial y su defecto es el CERA. Votos perdidos (sin geometría, sin sección vigente o fuera de los distritos) se
  informan, nunca se reparten.
Uso: python herramientas/reagregacion_historico.py --espejo DIR --historicos DIR --seccionado ZIP --padron ZIP
       --territorio congreso_huesca --provincia 22 --distritos M06.geojson [--salida datos/resultados/historico]
       [--tolerancia 0.10]
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).parent))
import equivalencia_seccionados as eqs  # noqa: E402
import fuente_nazioenbehatokia as fnb  # noqa: E402

SCHEMA = "ddd.reagregacion-historico/1.0"
TOLERANCIA = fnb.UMBRAL_DEFECTO
CAMPOS = ("censo", "votantes", "votos_candidaturas")


def asignar_distritos(vig: dict, distritos: dict) -> tuple[dict, list]:
    """{cusec vigente: id de distrito de mayor solape}; devuelve también las secciones sin solape con ningún distrito."""
    from shapely.strtree import STRtree
    ids = list(distritos)
    arbol = STRtree([distritos[d] for d in ids])
    asign, fuera = {}, []
    for v, g in sorted(vig.items()):
        mejor, area = None, 0.0
        for i in arbol.query(g):
            a = g.intersection(distritos[ids[i]]).area
            if a > area:
                mejor, area = ids[i], a
        if mejor is None:
            fuera.append(v)
        else:
            asign[v] = mejor
    return asign, fuera


def reagregar(votos: dict, eq: dict, asign: dict, peso: str = "poblacion") -> dict:
    """votos = {cusec_hist: {censo, votantes, votos_candidaturas, votos: {sigla: n}}} (lector T-89).
    Devuelve {"distritos": {d: {campo: x, "votos": {sigla: x}}}, "perdido": {"sin_geometria"|"sin_vigente"|
    "fuera_de_distritos": {"votos_candidaturas": x, "votos": {sigla: x}}}} con valores fraccionarios."""
    dist: dict = {}
    perdido = {k: {"votos_candidaturas": 0.0, "votos": Counter()}
               for k in ("sin_geometria", "sin_vigente", "fuera_de_distritos")}

    def perder(causa, s, w=1.0):
        perdido[causa]["votos_candidaturas"] += s["votos_candidaturas"] * w
        for p, x in s["votos"].items():
            perdido[causa]["votos"][p] += x * w

    for h, s in votos.items():
        e = eq.get(h)
        if e is None:
            perder("sin_geometria", s)
            continue
        if e["tipo"] == "sin_vigente":
            perder("sin_vigente", s)
            continue
        for v, w in e[peso].items():
            d = asign.get(v)
            if d is None:
                perder("fuera_de_distritos", s, w)
                continue
            r = dist.setdefault(d, {**{c: 0.0 for c in CAMPOS}, "votos": Counter()})
            for c in CAMPOS:
                r[c] += s[c] * w
            for p, x in s["votos"].items():
                r["votos"][p] += x * w
    return {"distritos": dist, "perdido": perdido}


def mayor_resto(valores: dict, objetivo: int | None = None) -> dict:
    """Redondea {clave: x} a enteros conservando la suma (método del mayor resto; desempate por clave)."""
    total = round(sum(valores.values())) if objetivo is None else objetivo
    base = {k: int(x) for k, x in valores.items()}
    faltan = total - sum(base.values())
    orden = sorted(valores, key=lambda k: (-(valores[k] - base[k]), str(k)))
    for k in orden[:max(faltan, 0)]:
        base[k] += 1
    return base


def redondear(res: dict) -> dict:
    """Pasa los valores de `reagregar` a enteros: por campo y por partido, a lo largo de los distritos."""
    dist = res["distritos"]
    out = {d: {"votos": {}} for d in dist}
    for c in CAMPOS:
        for d, x in mayor_resto({d: r[c] for d, r in dist.items()}).items():
            out[d][c] = x
    for p in sorted({p for r in dist.values() for p in r["votos"]}):
        for d, x in mayor_resto({d: r["votos"].get(p, 0.0) for d, r in dist.items()}).items():
            if x:
                out[d]["votos"][p] = x
    return out


def ganador(votos: dict) -> tuple[str, int]:
    if not votos:
        return "", 0
    p = min(votos, key=lambda k: (-votos[k], k))
    return p, votos[p]


def cuadre(votos: dict, res: dict, redondeado: dict, oficial: dict | None, tolerancia: float) -> dict:
    """Cuadre del total provincial. `exacto`: Σ distritos + perdido = Σ espejo, partido a partido (tras redondear,
    diferencia máxima en votos). `oficial`: espejo frente a la fuente oficial (sin CERA) con la tolerancia dada."""
    origen = Counter()
    for s in votos.values():
        origen.update(s["votos"])
    perdido = Counter()
    for v in res["perdido"].values():
        perdido.update(v["votos"])
    final = Counter()
    for r in redondeado.values():
        final.update(r["votos"])
    dif = max((abs(origen[p] - final[p] - round(perdido[p])) for p in origen), default=0)
    out = {"votos_espejo": sum(origen.values()), "votos_distritos": sum(final.values()),
           "votos_perdidos": round(sum(perdido.values()), 3), "dif_max_partido": dif}
    if oficial is None:
        out["oficial"] = "sin fuente oficial local: AVISO"
    else:
        c = fnb.contrastar_provincia(dict(origen), oficial, tolerancia)
        tot_of = sum(oficial[p] for p in c["comparaciones"])
        tot_es = sum(x["secundaria"] for x in c["comparaciones"].values())
        out["oficial"] = {"partidos_comparados": len(c["comparaciones"]), "sin_homologar": c["sin_homologar"],
                          "defecto_total": round((tot_of - tot_es) / tot_of, 5) if tot_of else 0.0,
                          "defecto_max_partido": max([x["defecto"] for x in c["comparaciones"].values()] or [0.0]),
                          "tolerancia": tolerancia, "errores": c["errores"], "avisos": c["avisos"],
                          "explicacion": "el espejo suma secciones y excluye el voto CERA"}
    out["ok"] = dif == 0 and (oficial is None or not out["oficial"]["errores"])
    return out


def escribir(carpeta: Path, territorio: str, redondeado: dict) -> list[Path]:
    carpeta.mkdir(parents=True, exist_ok=True)
    p1, p2 = carpeta / f"{territorio}.csv", carpeta / f"{territorio}_partidos.csv"
    with open(p1, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["distrito", "censo", "votantes", "votos_candidaturas", "ganador", "votos_ganador",
                    "porcentaje_ganador"])
        for d in sorted(redondeado, key=int):
            r = redondeado[d]
            g, n = ganador(r["votos"])
            pct = round(100 * n / r["votos_candidaturas"], 4) if r["votos_candidaturas"] else 0.0
            w.writerow([d, r["censo"], r["votantes"], r["votos_candidaturas"], g, n, pct])
    with open(p2, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["distrito", "partido", "votos", "porcentaje"])
        for d in sorted(redondeado, key=int):
            r = redondeado[d]
            for p, n in sorted(r["votos"].items(), key=lambda kv: (-kv[1], kv[0])):
                w.writerow([d, p, n, round(100 * n / r["votos_candidaturas"], 4) if r["votos_candidaturas"] else 0.0])
    return [p1, p2]


def leer_oficial(clave: str, cpro: str) -> dict | None:
    rel = fnb.OFICIALES.get(clave)
    if not rel:
        return None
    of: dict = {}
    with open(ROOT / rel, encoding="utf-8", newline="") as f:
        for r in csv.DictReader(f):
            if r["codigo"] == cpro:
                of[r["partido"]] = int(r["votos"])
    return of or None


def leer_distritos(geojson: Path) -> dict:
    """{id: geometría} en EPSG:25830 de un GeoJSON M06 (CRS84)."""
    import geopandas as gpd
    gdf = gpd.read_file(geojson).to_crs(25830)
    return {str(i): (g if g.is_valid else g.buffer(0)) for i, g in zip(gdf["district_id"], gdf.geometry)}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--espejo", type=Path, required=True)
    ap.add_argument("--historicos", type=Path, required=True)
    ap.add_argument("--seccionado", type=Path, required=True)
    ap.add_argument("--padron", type=Path, required=True)
    ap.add_argument("--territorio", required=True, help="p. ej. congreso_huesca")
    ap.add_argument("--provincia", required=True, help="código INE de dos cifras")
    ap.add_argument("--distritos", type=Path, required=True, help="GeoJSON M06 del territorio")
    ap.add_argument("--salida", type=Path, default=ROOT / "datos/resultados/historico")
    ap.add_argument("--tolerancia", type=float, default=TOLERANCIA)
    a = ap.parse_args(argv)
    c = a.provincia
    espejo = json.loads((ROOT / eqs.MANIFIESTO_ESPEJO).read_text(encoding="utf-8"))
    vig = eqs.leer_seccionado(a.seccionado)[c]
    pob = eqs.leer_padron(a.padron)
    distritos = leer_distritos(a.distritos)
    asign, fuera = asignar_distritos(vig, distritos)
    todos = {e["seccionado"]: eqs.leer_seccionado(a.historicos / f"seccionado_{e['seccionado']}.zip").get(c, {})
             for e in espejo["elecciones"]}
    huellas, informe = {}, {}
    for e in espejo["elecciones"]:
        clave, año = e["clave"], e["seccionado"]
        ruta = f"data/{clave}/sekzioa/{c}.json"
        if eqs.sha256(a.espejo / ruta) != espejo["ficheros"][ruta]["sha256"]:
            raise SystemExit(f"HUELLA_ESPEJO_DISTINTA {ruta}")
        huellas[ruta] = espejo["ficheros"][ruta]["sha256"]
        votos = fnb.leer_provincia(json.loads((a.espejo / ruta).read_text(encoding="utf-8")))
        hist, _ = eqs.completar_geometrias(votos, año, todos)
        dx, dy = eqs.desplazamiento_sistematico(hist, vig)
        if dx or dy:
            from shapely.affinity import translate
            hist = {k: translate(g, dx, dy) for k, g in hist.items()}
        eq = eqs.equivalencia(hist, vig, pob)
        res = reagregar(votos, eq, asign)
        red = redondear(res)
        informe[clave] = cuadre(votos, res, red, leer_oficial(clave, c), a.tolerancia)
        informe[clave]["distritos"] = len(red)
        escribir(a.salida / clave, a.territorio, red)
        print(a.territorio, clave, informe[clave]["ok"], informe[clave]["votos_perdidos"], flush=True)
    # fuente con huella; el manifiesto acumula territorios
    mp = a.salida / "MANIFEST.json"
    man = json.loads(mp.read_text(encoding="utf-8")) if mp.exists() else {"schema": SCHEMA, "territorios": {}}
    man["peso"] = "poblacion (D-13)"
    man["tolerancia_cuadre"] = a.tolerancia
    man["territorios"][a.territorio] = {
        "provincia": c, "secciones_vigentes_sin_distrito": fuera,
        "fuentes": {"seccionado_2025": eqs.sha256(a.seccionado), "padron_65034": eqs.sha256(a.padron),
                    "distritos_m06": eqs.sha256(a.distritos), "espejo": huellas,
                    "historicos": {str(y): eqs.sha256(a.historicos / f"seccionado_{y}.zip") for y in todos}},
        "cuadre": informe}
    mp.write_text(json.dumps(man, ensure_ascii=False, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    return 0 if all(x["ok"] for x in informe.values()) else 1


if __name__ == "__main__":
    sys.exit(main())
