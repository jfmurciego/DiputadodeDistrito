#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Datos abiertos 2 (T-476): votos por partido y distrito, doble vuelta y composición, desde lo que hay en git.

PROYECTO: Diputado de Distrito
VERSIÓN: 1.0.0 · FECHA: 2026-11-28 · ESTADO: candidato
ANTERIOR: ninguna (fichero nuevo)
MOTIVO: T-476. Las fichas de datos abiertos solo traen el ganador por distrito; este paquete añade los votos por partido,
  la doble vuelta (dv_base, dv_A, dv_B) y la composición por distrito, con sha256 de entradas y salidas y cuadre con el BOE.
QUÉ HACE: `generar` lee (sin red) los votos por partido y distrito del run M08 vigente de cada nac (2023-07) y, solo en los
  nac cuyo mapa de distritos histórico es la MISMA partición, con las mismas etiquetas, que el vigente, los de 2011-11 a
  2019-11 (T-83). Los demás nac y elecciones se listan en `no_construible.csv` con su motivo; no se construyen: sus votos por
  sección no están en git. La doble vuelta se calcula con herramientas/doble_vuelta.py y configuracion/bloques_partidos_2026-11-25.csv.
  `--comprobar` verifica sha256 de entradas y salidas, el cuadre con el BOE por provincia (defecto ≤ 10 %: voto CERA, que
  el ZIP por mesa no trae; nunca exceso) y que el ganador de 2023 sea el de datos/resultados/<nac>.csv.
  El ganador debe coincidir por nombre; sus votos pueden diferir (aviso si >10 %: secciones del ZIP sin M06 repartidas, T-103/T-104).
  Numeración de distritos: 1..K, como la ficha pública (el run interno va 0..K-1).
SALIDA: docs/ESTUDIOS/T476/votos/ (fuera de datos_abiertos/: la P40 actual no la borra ni la publica).
USO: python herramientas/datos_abiertos_votos.py generar | python herramientas/datos_abiertos_votos.py --comprobar
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "herramientas"))
import doble_vuelta as dv  # noqa: E402
import fuente_nazioenbehatokia as fn  # noqa: E402
from ddd_core import territorio_ids as tid  # noqa: E402

SALIDA = ROOT / "docs" / "ESTUDIOS" / "T476" / "votos"
BLOQUES_CSV = ROOT / "configuracion" / "bloques_partidos_2026-11-25.csv"
ALIAS_CSV = ROOT / "configuracion" / "alias_partidos_generales.csv"
ALIAS_BOE_CSV = ROOT / "configuracion" / "alias_siglas_boe_espejo.csv"
# elección AAAAMM → (AAAA-MM de la tabla de bloques, BOE oficial)
ELECCIONES = {
    "201111": ("2011-11", "configuracion/resultados_oficiales_congreso_2011_11.csv"),
    "201512": ("2015-12", "configuracion/resultados_oficiales_congreso_2015_12.csv"),
    "201606": ("2016-06", "configuracion/resultados_oficiales_congreso_2016_06.csv"),
    "201904": ("2019-04", "configuracion/resultados_oficiales_congreso_2019_04.csv"),
    "201911": ("2019-11", "configuracion/resultados_oficiales_congreso_2019_11.csv"),
    "202307": ("2023-07", "configuracion/resultados_oficiales_congreso_2023.csv"),
}
VIGENTE = "202307"
UMBRAL_DEFECTO = fn.UMBRAL_DEFECTO  # 0,10: el voto CERA no está en el ZIP por mesa
F_VOTOS, F_DV, F_COMP, F_NO, F_MAN = ("votos_partido_distrito.csv", "doble_vuelta.csv", "composicion_distrito.csv",
                                      "no_construible.csv", "MANIFEST.json")
COL_VOTOS = ["territorio", "eleccion", "distrito", "partido", "votos"]
COL_DV = ["territorio", "eleccion"] + dv.COLUMNAS
COL_COMP = ["territorio", "distrito", "poblacion", "secciones"]
COL_NO = ["territorio", "eleccion", "motivo"]
MOTIVO_MAPA = ("histórico sobre un mapa de distritos anterior al vigente: los votos por sección (espejo T-89) no están en git; "
               "no se reagregan")


def rel(p) -> str:
    return str(Path(p).resolve().relative_to(ROOT))


def sha(p) -> str:
    return dv.sha256(p)


def leer(p) -> list[dict]:
    with open(p, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def escribir(p: Path, cols: list[str], filas: list[dict]) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols, lineterminator="\n")
        w.writeheader()
        w.writerows(filas)


def num(d) -> int:
    return int(d) + 1  # interno 0..K-1 → público 1..K


def orden_distrito(f: dict):
    return (f["territorio"], f.get("eleccion", ""), int(f["distrito"]) if f.get("distrito") not in (None, "") else 0)


# --- entradas ------------------------------------------------------------------------------------------------------
def vigentes() -> dict[str, dict]:
    """nacNN → {run_id, run_territorial, votos (ruta), sha256_votos, composicion (ruta), sha256_composicion}. Run = el de INDEX."""
    idx = json.loads((ROOT / "datos_abiertos" / "INDEX.json").read_text(encoding="utf-8"))["territorios"]
    runs = json.loads((ROOT / "datos/resultados/MANIFEST.json").read_text(encoding="utf-8"))["partidos_runs"]
    comp = json.loads((ROOT / "datos/composicion/MANIFEST_RUNS.json").read_text(encoding="utf-8"))["ficheros"]
    out = {}
    for nac in sorted(k for k in idx if tid.es_nacional(k)):
        e = runs[f"{nac}/{idx[nac]['run_id']}"]
        c = f"runs/{nac}_{e['run_id']}.csv"  # MANIFEST_RUNS va por el run M08 (mismo sha256 que el del run territorial)
        out[nac] = {"run_id": e["run_id"], "run_territorial": e["run_territorial"], "votos": e["ruta"],
                    "sha256_votos": e["sha256_csv"], "composicion": "datos/composicion/" + c,
                    "sha256_composicion": comp[c]["sha256_csv"]}
        assert comp[c]["sha256_csv"] == e["sha256_composicion"], f"{nac}: composición ≠ la del run de resultados"
    return out


def mapa(p) -> dict[str, str]:
    return {r["seccion"]: r["distrito"] for r in leer(p)}


def mismo_mapa(nac: str, v: dict) -> bool:
    """El mapa de secciones→distrito del histórico (datos/composicion/<id>.csv) es idéntico al vigente."""
    hist = ROOT / "datos" / "composicion" / f"{tid.id_legacy(nac)}.csv"
    return hist.exists() and mapa(hist) == mapa(ROOT / v["composicion"])


def partidos_historico(nac: str, eleccion: str) -> Path:
    return ROOT / "datos/resultados/historico" / eleccion / f"{tid.id_legacy(nac)}_partidos.csv"


def votos_de(ruta) -> dict[str, dict[str, int]]:
    """distrito público (str) → {partido: votos}. Acumula (un partido por distrito)."""
    out: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for r in leer(ruta):
        out[str(num(r["distrito"]))][r["partido"]] += int(r["votos"])
    return {k: dict(v) for k, v in out.items()}


def doble_vuelta(votos: dict[str, dict[str, int]], eleccion: str) -> list[dict]:
    tabla = dv.cargar_tabla(BLOQUES_CSV, ELECCIONES[eleccion][0])
    bloque_de = {k: v for k, v in tabla.items() if v}
    votos = dv.aplicar_alias(votos, dv.cargar_alias(ALIAS_CSV, ELECCIONES[eleccion][0]))
    filas = []
    for d in sorted(votos, key=int):
        for esc in dv.ESCENARIOS:
            f = dv.resolver(votos[d], bloque_de, esc)
            f["district_id"] = d
            filas.append(f)
    return filas


# --- generar -------------------------------------------------------------------------------------------------------
def construir() -> dict:
    vig = vigentes()
    votos, dvs, comps, nos = [], [], [], []
    entradas: dict[str, str] = {}
    sin_casar: dict[str, dict] = {}
    for nac, v in vig.items():
        entradas[v["votos"]] = sha(ROOT / v["votos"])
        entradas[v["composicion"]] = sha(ROOT / v["composicion"])
        distritos: dict[str, list] = defaultdict(list)
        for r in leer(ROOT / v["composicion"]):
            distritos[str(num(r["distrito"]))].append(int(r["poblacion"]))
        for d in sorted(distritos, key=int):
            comps.append({"territorio": nac, "distrito": d, "poblacion": sum(distritos[d]), "secciones": len(distritos[d])})
        series = [(VIGENTE, ROOT / v["votos"])]
        iguales = mismo_mapa(nac, v)
        for e in ELECCIONES:
            if e == VIGENTE:
                continue
            if iguales:
                series.append((e, partidos_historico(nac, e)))
            else:
                nos.append({"territorio": nac, "eleccion": e, "motivo": MOTIVO_MAPA})
        for e, ruta in series:
            if ruta != ROOT / v["votos"]:
                entradas[rel(ruta)] = sha(ruta)
            vt = votos_de(ruta)
            votos += [{"territorio": nac, "eleccion": e, "distrito": d, "partido": p, "votos": n}
                      for d in sorted(vt, key=int) for p, n in sorted(vt[d].items(), key=lambda a: (-a[1], a[0])) if n > 0]
            dvs += [{"territorio": nac, "eleccion": e, **f} for f in doble_vuelta(vt, e)]
            tabla = dv.cargar_tabla(BLOQUES_CSV, ELECCIONES[e][0])
            h = dv.sin_casar(dv.aplicar_alias(vt, dv.cargar_alias(ALIAS_CSV, ELECCIONES[e][0])), tabla)
            if h:
                sin_casar[f"{nac}/{e}"] = {"partidos": len(h), "votos": sum(h.values())}
    return {"votos": votos, "dv": dvs, "comp": comps, "no": nos, "entradas": entradas, "sin_casar": sin_casar}


def generar(salida: Path = SALIDA) -> dict:
    r = construir()
    escribir(salida / F_VOTOS, COL_VOTOS, r["votos"])
    escribir(salida / F_DV, COL_DV, r["dv"])
    escribir(salida / F_COMP, COL_COMP, r["comp"])
    escribir(salida / F_NO, COL_NO, r["no"])
    nac_con = sorted({x["territorio"] for x in r["votos"] if x["eleccion"] != VIGENTE})
    man = {
        "schema": "ddd.datos-abiertos-votos/1.0", "tarea": "T-476", "numeracion": "1..K",
        "entradas": dict(sorted(r["entradas"].items())),
        "configuracion": {rel(p): sha(p) for p in (BLOQUES_CSV, ALIAS_CSV, ALIAS_BOE_CSV)},
        "salidas": {f: sha(salida / f) for f in (F_VOTOS, F_DV, F_COMP, F_NO)},
        "resumen": {"nac_2023": len({x["territorio"] for x in r["votos"] if x["eleccion"] == VIGENTE}),
                    "nac_con_historico": nac_con, "filas_votos": len(r["votos"]), "filas_no_construible": len(r["no"]),
                    "sin_casar_doble_vuelta": r["sin_casar"]},
    }
    (salida / F_MAN).write_text(json.dumps(man, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return man


# --- comprobar -----------------------------------------------------------------------------------------------------
def boe(eleccion: str) -> dict[str, dict[str, int]]:
    out: dict[str, dict[str, int]] = defaultdict(dict)
    for r in leer(ROOT / ELECCIONES[eleccion][1]):
        out[r["codigo"]][r["partido"]] = int(r["votos"])
    return out


def alias_boe(eleccion: str) -> dict[tuple[str, str], str]:
    """(provincia, sigla BOE) → sigla de la fuente (una sola, sin separadores múltiples)."""
    return {(r["provincia"], r["sigla_boe"]): r["siglas_espejo"] for r in leer(ALIAS_BOE_CSV) if r["eleccion"] == eleccion}


def provincia(nac: str) -> str:
    h = json.loads((ROOT / "datos/resultados/historico/MANIFEST.json").read_text(encoding="utf-8"))["territorios"]
    return h[tid.id_legacy(nac)]["provincia"]


def comprobar(salida: Path = SALIDA) -> list[str]:
    err: list[str] = []
    man = json.loads((salida / F_MAN).read_text(encoding="utf-8"))
    for f, h in man["salidas"].items():
        if sha(salida / f) != h:
            err.append(f"sha256 de la salida {f} distinto del manifiesto")
    for p, h in {**man["entradas"], **man["configuracion"]}.items():
        if not (ROOT / p).exists() or sha(ROOT / p) != h:
            err.append(f"sha256 de la entrada {p} distinto del manifiesto")
    vig = vigentes()
    for nac, v in vig.items():  # entradas 2023 contra el MANIFEST de resultados y de composición
        if man["entradas"].get(v["votos"]) != v["sha256_votos"]:
            err.append(f"{nac}: sha256 de votos distinto del MANIFEST de resultados")
        if man["entradas"].get(v["composicion"]) != v["sha256_composicion"]:
            err.append(f"{nac}: sha256 de composición distinto de MANIFEST_RUNS")
    suma: dict[tuple, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    por_distrito: dict[tuple, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for r in leer(salida / F_VOTOS):
        suma[(r["territorio"], r["eleccion"])][r["partido"]] += int(r["votos"])
        por_distrito[(r["territorio"], r["eleccion"], r["distrito"])][r["partido"]] += int(r["votos"])
    defecto_max: dict[str, float] = {}
    for (nac, e), tot in sorted(suma.items()):  # cuadre BOE por provincia
        prov = provincia(nac)
        al = alias_boe(e)
        oficial = {al.get((prov, s), s): v for s, v in boe(e).get(prov, {}).items()}  # sin fila de alias: misma sigla
        c = fn.contrastar_provincia(dict(tot), oficial, UMBRAL_DEFECTO)
        err += [f"{nac} {e}: {x}" for x in c["errores"] + c["avisos"]]
        if not c["comparaciones"]:
            err.append(f"{nac} {e}: ningún partido casado con el BOE")
        defecto_max[e] = max([defecto_max.get(e, 0.0)] + [x["defecto"] for x in c["comparaciones"].values()])
    dif_ganador = 0.0
    avisos: list[str] = []
    for nac in vig:  # ganador 2023 = datos/resultados/<nac>.csv
        pub = leer(ROOT / "datos/resultados" / f"{nac}.csv")
        for r in pub:
            d = str(num(r["distrito"]))
            propios = por_distrito.get((nac, VIGENTE, d))
            if not propios:
                err.append(f"{nac} distrito {d}: sin votos en la salida")
                continue
            top = max(propios.values())
            if propios.get(r["ganador"]) != top:
                err.append(f"{nac} distrito {d}: ganador de la tabla {r['ganador']} ≠ el de los votos")
            # los votos del ganador pueden diferir poco (M08 del espejo por sección vs ZIP por mesa; contraste_2023.csv)
            dif = abs(int(r["votos_ganador"]) - top) / top
            dif_ganador = max(dif_ganador, dif)
            if dif > UMBRAL_DEFECTO:  # aviso, no error: secciones del ZIP sin M06 repartidas por T-103/T-104 (desajustes.json del run)
                avisos.append(f"{nac} distrito {d}: votos del ganador difieren {dif:.1%} de la tabla (ver desajustes del run)")
    comp_pop = defaultdict(int)
    for r in leer(salida / F_COMP):
        comp_pop[r["territorio"]] += int(r["poblacion"])
    for nac in vig:
        if comp_pop[nac] <= 0:
            err.append(f"{nac}: composición vacía")
    comprobar.defecto_max = defecto_max  # type: ignore[attr-defined]
    comprobar.dif_ganador = dif_ganador  # type: ignore[attr-defined]
    comprobar.avisos = avisos  # type: ignore[attr-defined]
    return err


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("orden", nargs="?", choices=["generar"])
    ap.add_argument("--comprobar", action="store_true")
    ap.add_argument("--salida", type=Path, default=SALIDA)
    a = ap.parse_args(argv)
    if a.comprobar:
        err = comprobar(a.salida)
        for e in err:
            print(f"ERROR {e}", file=sys.stderr)
        for e in comprobar.avisos:  # type: ignore[attr-defined]
            print(f"AVISO {e}", file=sys.stderr)
        print(f"[datos_abiertos_votos] comprobar: {len(err)} errores; defecto máx. por elección: "
              f"{ {k: round(v, 4) for k, v in sorted(comprobar.defecto_max.items())} }; "
              f"votos del ganador vs tabla: dif. máx. {comprobar.dif_ganador:.2%}")  # type: ignore[attr-defined]
        return 1 if err else 0
    m = generar(a.salida)
    print(f"[datos_abiertos_votos] OK {m['resumen']['filas_votos']} filas de votos; nac con histórico: "
          f"{len(m['resumen']['nac_con_historico'])}; no construibles: {m['resumen']['filas_no_construible']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
