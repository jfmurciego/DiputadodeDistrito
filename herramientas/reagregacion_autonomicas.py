#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Reagregación del histórico AUTONÓMICO a los distritos autonómicos vigentes (T-121, paso 3).

PROYECTO: Diputado de Distrito
VERSIÓN: 1.0.0 · FECHA: 2026-11-09 · ESTADO: candidato
CAMBIOS: 1.0.0: fichero nuevo.
MOTIVO: orden del propietario (09-11): reproducir para las comunidades el paso B de las generales (T-83): votos de cada
  autonómica → distritos vigentes con la equivalencia de seccionados de T-85 y peso por población (D-13).
ANTERIOR: ninguna (fichero nuevo; reutiliza funciones de reagregacion_historico.py y equivalencia_seccionados.py sin modificarlas)
QUÉ HACE: fuera de línea (no lanza ni publica). Por comunidad y elección en alcance de configuracion/calendario_autonomicas.csv:
  (1) descarga del Observatorio data/autonomikoak/sekzioa/<cca>-<AAAAMM>/<provincia>.json y data/autonomikoak/hauteskundea/
  <cca>-<AAAAMM>.json (sha256 en el MANIFEST; la fuente no publica huellas previas); (2) lleva las secciones históricas
  (seccionado INE del año que declara el Observatorio) a las vigentes y de ahí al distrito con `datos/composicion/<c>.csv`
  (peso de población); (3) redondea por mayor resto partido a partido; (4) cuadre: Σ distritos + perdido = Σ fuente
  (exacto) y fuente por sección frente al total autonómico del Observatorio sin voto CERA (tope D-17 0,5 %);
  (5) escribe `<salida>/<comunidad>/<aaaamm>/` (CSV por distrito y por partido, MANIFEST.json) y
  `<salida>/<comunidad>/rotacion.csv` (ganador por distrito y elección; homologado si existe
  datos/homologacion_siglas/homologacion_siglas_autonomicas.csv, D-20; si no, la sigla de la fuente).
  Elecciones sin dato por sección (solo municipio) se listan en `huecos` del MANIFEST de la comunidad, no se inventan.
Uso: python herramientas/reagregacion_autonomicas.py --comunidad galicia madrid --trabajo DIR [--salida datos/resultados/historico/autonomicas]
       (DIR cacheará seccionados históricos y ficheros del Observatorio; --seccionado/--padron por defecto inputs/…zip)
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
import time
import urllib.request
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(ROOT))
import equivalencia_seccionados as eqs  # noqa: E402
import fuente_nazioenbehatokia as fnb  # noqa: E402
import reagregacion_historico as rh  # noqa: E402

SCHEMA = "ddd.reagregacion-autonomicas/1.0"
BASE = "https://nazioenbehatokia.eus/data/autonomikoak/"
INE = "https://www.ine.es/prodyser/cartografia/seccionado_{}.zip"
TOPE_D17 = 0.005
CALENDARIO = "configuracion/calendario_autonomicas.csv"
HOMOLOGACION = "datos/homologacion_siglas/homologacion_siglas_autonomicas.csv"
INDICE = "fuentes/observatorio_autonomicas/index.json"


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def bajar(url: str, destino: Path) -> bytes:
    """Descarga con reintentos y caché; devuelve los bytes."""
    if destino.exists():
        return destino.read_bytes()
    for i in range(5):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "ddd-historico-autonomicas"})
            with urllib.request.urlopen(req, timeout=120) as r:
                datos = r.read()
            break
        except OSError as exc:
            if i == 4:
                raise SystemExit(f"DESCARGA_FALLIDA {url}: {exc}")
            time.sleep(2 ** (i + 1))
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_bytes(datos)
    return datos


def leer_calendario(raiz: Path = ROOT) -> dict[str, list[dict]]:
    """{comunidad: [filas en alcance, ordenadas]}."""
    out: dict[str, list[dict]] = {}
    with open(raiz / CALENDARIO, encoding="utf-8", newline="") as f:
        for r in csv.DictReader(f):
            if r["en_alcance"] == "si":
                out.setdefault(r["comunidad"], []).append(r)
    return out


def leer_composicion(comunidad: str, raiz: Path = ROOT) -> dict[str, str]:
    """{cusec vigente: distrito} de datos/composicion/<comunidad>.csv."""
    with open(raiz / f"datos/composicion/{comunidad}.csv", encoding="utf-8", newline="") as f:
        return {r["seccion"]: r["distrito"] for r in csv.DictReader(f)}


def total_autonomico(doc: dict) -> dict:
    """Total de la comunidad del fichero hauteskundea (sin voto CERA): votos por sigla y a candidaturas."""
    siglas = doc["s"]
    _, _, cand, partidos = doc["autonomia"]
    return {"votos_candidaturas": cand, "votos": {siglas[i]: n for i, n in partidos}}


def cuadre_autonomico(votos: dict, res: dict, red: dict, total: dict) -> dict:
    """Σ distritos + perdido = Σ fuente exacto, y fuente por sección frente al total autonómico (D-17)."""
    c = rh.cuadre(votos, res, red, None, TOPE_D17)
    suma_fuente = c["votos_espejo"]
    of = sum(total["votos"].values())
    c["total_autonomico"] = of
    c["defecto_frente_total"] = round((of - suma_fuente) / of, 6) if of else 0.0
    c["dentro_tope_d17"] = abs(c["defecto_frente_total"]) <= TOPE_D17
    c["ok"] = c["dif_max_partido"] == 0 and c["dentro_tope_d17"]
    return c


def homologacion(raiz: Path = ROOT) -> dict:
    """{(comunidad, elección AAAAMM, sigla_fuente): partido_homologado} si existe la tabla (PR de siglas)."""
    p = raiz / HOMOLOGACION
    if not p.exists():
        return {}
    with open(p, encoding="utf-8", newline="") as f:
        return {(r["comunidad"], r["eleccion"], r["sigla_fuente"]): r["partido_homologado"] for r in csv.DictReader(f)}


def ganador_h(votos: dict, hom: dict, com: str, ele: str, sin: set) -> str:
    agr: Counter = Counter()
    for s, n in votos.items():
        h = hom.get((com, ele, s))
        if h is None and hom:
            sin.add((com, ele, s))
        agr[h or s] += n
    return rh.ganador(dict(agr))[0]


def escribir_rotacion(path: Path, ganadores: dict) -> None:
    """ganadores = {AAAAMM: {distrito: ganador}}; columna `cambios` = veces que cambia entre elecciones consecutivas."""
    rh.escribir_rotacion(path, ganadores)


def procesar(com: str, filas: list[dict], a, indice: dict, vig_all: dict, pob: dict, todos: dict, hom: dict,
             sin: set) -> tuple[dict, dict, list]:
    comp = leer_composicion(com)
    provincias = sorted({s[:2] for s in comp})
    salida_c = a.salida / com
    ganadores, huecos, elecciones = {}, [], {}
    cca = filas[0]["cod_ine"]
    for fila in filas:
        ele = fila["mes"].replace("-", "")
        clave = f"{cca}-{ele}"
        año = indice["sekzioak"].get(clave)
        if año is None:
            huecos.append({"eleccion": ele, "motivo": f"sin datos por sección en el Observatorio ({fila['granularidad']}, {fila['completitud']})"})
            continue
        huellas, votos, eq = {}, {}, {}
        for c in provincias:
            ruta = f"sekzioa/{clave}/{c}.json"
            crudo = bajar(BASE + ruta, a.trabajo / "obs" / ruta)
            huellas[ruta] = sha(crudo)
            v = fnb.leer_provincia(json.loads(crudo))
            hist, _ = eqs.completar_geometrias(v, año, {y: z.get(c, {}) for y, z in todos.items()})
            dx, dy = eqs.desplazamiento_sistematico(hist, vig_all[c])
            if dx or dy:
                from shapely.affinity import translate
                hist = {k: translate(g, dx, dy) for k, g in hist.items()}
            eq.update(eqs.equivalencia(hist, vig_all[c], pob))
            votos.update(v)
        ruta_t = f"hauteskundea/{clave}.json"
        crudo_t = bajar(BASE + ruta_t, a.trabajo / "obs" / ruta_t)
        huellas[ruta_t] = sha(crudo_t)
        total = total_autonomico(json.loads(crudo_t))
        res = rh.reagregar(votos, eq, comp)
        red = rh.redondear(res)
        c = cuadre_autonomico(votos, res, red, total)
        c["distritos"] = len(red)
        rh.escribir(salida_c / ele, com, red)
        (salida_c / ele / "MANIFEST.json").write_text(json.dumps({
            "schema": SCHEMA, "comunidad": com, "eleccion": ele, "seccionado_historico": año, "peso": "poblacion (D-13)",
            "fuentes": {"observatorio": huellas, "seccionado_2025": eqs.sha256(a.seccionado), "padron_65034": eqs.sha256(a.padron),
                        "composicion": eqs.sha256(ROOT / f"datos/composicion/{com}.csv"),
                        "calendario": eqs.sha256(ROOT / CALENDARIO),
                        "historicos": {str(y): eqs.sha256(a.trabajo / "historicos" / f"seccionado_{y}.zip") for y in todos}},
            "cuadre": c}, ensure_ascii=False, indent=1, sort_keys=True) + "\n", encoding="utf-8")
        ganadores[ele] = {d: ganador_h(r["votos"], hom, com, ele, sin) for d, r in red.items()}
        elecciones[ele] = c
        print(com, ele, c["ok"], c["votos_perdidos"], c["defecto_frente_total"], flush=True)
    if ganadores:
        escribir_rotacion(salida_c / "rotacion.csv", ganadores)
    (salida_c / "MANIFEST.json").write_text(json.dumps({
        "schema": SCHEMA, "comunidad": com, "elecciones": {e: {"ok": c["ok"], "defecto_frente_total": c["defecto_frente_total"],
                                                                "votos_perdidos": c["votos_perdidos"]} for e, c in elecciones.items()},
        "huecos": huecos, "no_cuadran": sorted(e for e, c in elecciones.items() if not c["ok"])},
        ensure_ascii=False, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    return elecciones, ganadores, huecos


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--comunidad", nargs="+", required=True)
    ap.add_argument("--trabajo", type=Path, required=True)
    ap.add_argument("--seccionado", type=Path, default=ROOT / "inputs/seccionado_2025.zip")
    ap.add_argument("--padron", type=Path, default=ROOT / "inputs/65034.csv.zip")
    ap.add_argument("--salida", type=Path, default=ROOT / "datos/resultados/historico/autonomicas")
    a = ap.parse_args(argv)
    cal = leer_calendario()
    desconocidas = [c for c in a.comunidad if c not in cal]
    if desconocidas:
        raise SystemExit(f"COMUNIDAD_SIN_CALENDARIO {desconocidas}")
    indice = json.loads((ROOT / INDICE).read_text(encoding="utf-8"))
    años = sorted({y for com in a.comunidad for f in cal[com]
                   if (y := indice["sekzioak"].get(f"{f['cod_ine']}-{f['mes'].replace('-', '')}"))})
    todos = {}
    for y in años:
        z = a.trabajo / "historicos" / f"seccionado_{y}.zip"
        if not z.exists():
            bajar(INE.format(y), z)
        todos[y] = eqs.leer_seccionado(z)
    vig_all, pob = eqs.leer_seccionado(a.seccionado), eqs.leer_padron(a.padron)
    hom, sin, ok = homologacion(), set(), True
    for com in a.comunidad:
        el, _, _ = procesar(com, cal[com], a, indice, vig_all, pob, todos, hom, sin)
        ok &= all(c["ok"] for c in el.values())
    if sin:
        a.salida.mkdir(parents=True, exist_ok=True)
        (a.salida / "siglas_sin_homologar.json").write_text(json.dumps(sorted(sin), ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
