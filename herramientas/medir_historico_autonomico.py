#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Cobertura del histórico autonómico desde 2011 (T-176, paso 1).

PROYECTO: Diputado de Distrito
VERSIÓN: 1.0.1 · FECHA: 2026-11-12 · ESTADO: candidato
VERSIÓN: 1.0.1 · CAMBIOS 1.0.1 (T-220): ids de territorio nuevos de la tabla maestra (aut01…nac52, D-61); el id viejo se lee vía ddd_core.territorio_ids.
VERSIÓN: 1.0.1 · ANTERIOR: legacy/herramientas/medir_historico_autonomico_v1.0.0_20261112.py
CAMBIOS: 1.0.0: fichero nuevo.
MOTIVO: medir qué elecciones autonómicas existen por comunidad, cuáles tienen dato en el repositorio y cuáles cuadran
  (D-17: ≤0,5 % de voto), y la causa de cada hueco.
QUÉ HACE: fuera de línea, solo lectura de calendario, índice del Observatorio (sha256 en el calendario),
  datos/composicion/ y MANIFEST de cada comunidad; escribe COBERTURA.csv y COBERTURA.md. No descarga nada.
Uso: python herramientas/medir_historico_autonomico.py [--salida DIR]
"""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
import sys as _sys_t220  # noqa: E402
from pathlib import Path as _Path_t220  # noqa: E402
if str(_Path_t220(__file__).resolve().parents[1]) not in _sys_t220.path:
    _sys_t220.path.insert(0, str(_Path_t220(__file__).resolve().parents[1]))
from ddd_core.territorio_ids import fichero_por_id  # noqa: E402  (T-220: id viejo o nuevo)

ROOT = Path(__file__).resolve().parents[1]
CAL = "configuracion/calendario_autonomicas.csv"
INDICE = "fuentes/observatorio_autonomicas/index.json"
DATOS = "datos/resultados/historico/autonomicas"
TOPE = 0.005
CAMPOS = ["comunidad", "eleccion", "fecha_mes", "granularidad_calendario", "seccion_en_observatorio", "composicion_m06",
          "en_repo", "cuadra", "defecto_frente_total", "perdida_geometria", "aproximado_en_distrito", "estado", "causa",
          "accesible_desde_nube", "siglas"]


def medir(raiz: Path = ROOT) -> list[dict]:
    idx = json.loads((raiz / INDICE).read_text(encoding="utf-8"))
    secc = set(idx["sekzioak"])
    filas = []
    with open(raiz / CAL, encoding="utf-8", newline="") as f:
        cal = [r for r in csv.DictReader(f) if r["en_alcance"] == "si"]
    mans: dict = {}
    for r in cal:
        c, aaaamm = r["comunidad"], r["mes"].replace("-", "")
        if c not in mans:
            p = fichero_por_id(raiz / DATOS, "{}/MANIFEST.json", c)  # T-220: carpeta con el id viejo
            mans[c] = json.loads(p.read_text(encoding="utf-8")).get("elecciones", {}) if p.exists() else {}
        comp = fichero_por_id(raiz / "datos/composicion", "{}.csv", c).exists()
        hay_secc = f"{r['cod_ine']}-{aaaamm}" in secc
        m = mans[c].get(aaaamm)
        f_ = {"comunidad": c, "eleccion": aaaamm, "fecha_mes": r["mes"], "granularidad_calendario": r["granularidad"],
              "seccion_en_observatorio": "si" if hay_secc else "no", "composicion_m06": "si" if comp else "no",
              "en_repo": "si" if m else "no", "cuadra": "", "defecto_frente_total": "", "perdida_geometria": "",
              "aproximado_en_distrito": "", "causa": "", "accesible_desde_nube": "si" if hay_secc else "no",
              "siglas": "sin homologar (sigla tal cual)" if m else ""}
        if m:
            ok = bool(m["ok"]) and abs(m["defecto_frente_total"]) <= TOPE and m["perdida_frente_fuente"] <= TOPE
            f_.update(cuadra="si" if ok else "no", defecto_frente_total=m["defecto_frente_total"],
                      perdida_geometria=m["perdida_frente_fuente"],
                      aproximado_en_distrito="si" if m["aproximado_en_distrito"] else "no",
                      estado="COMPLETA_Y_CUADRA" if ok else "EN_REPO_NO_CUADRA")
        elif not hay_secc:
            f_["estado"] = "HUECO"
            f_["causa"] = ("fuente solo por " + r["granularidad"] + " (sin sección): requiere el dato por sección de la "
                           "Junta/instituto autonómico, descarga manual del propietario") if r["granularidad"] != "–" \
                else "sin datos publicados en ninguna fuente localizada"
            f_["accesible_desde_nube"] = "no"
        elif not comp:
            f_["estado"] = "HUECO"
            f_["causa"] = "dato por sección disponible, pero no hay composición M06 (distritos vigentes) de la comunidad"
        else:
            f_["estado"] = "PENDIENTE_DE_REAGREGAR"
            f_["causa"] = "dato por sección y composición disponibles: falta ejecutar la reagregación"
        filas.append(f_)
    return filas


def resumen(filas: list[dict]) -> str:
    com: dict = {}
    for f in filas:
        com.setdefault(f["comunidad"], []).append(f)
    est = lambda l, e: sum(1 for x in l if x["estado"] == e)  # noqa: E731
    out = ["| Comunidad | Elecciones | Completas y cuadran | En repo no cuadran | Pendientes de reagregar | Huecos |",
           "|---|---|---|---|---|---|"]
    for c, l in com.items():
        out.append(f"| {c} | {len(l)} | {est(l, 'COMPLETA_Y_CUADRA')} | {est(l, 'EN_REPO_NO_CUADRA')} | "
                   f"{est(l, 'PENDIENTE_DE_REAGREGAR')} | {est(l, 'HUECO')} |")
    completas = [c for c, l in com.items() if all(x["estado"] == "COMPLETA_Y_CUADRA" for x in l)]
    out.append(f"\nComunidades completas y cuadradas: {len(completas)} de {len(com)} con elecciones autonómicas "
               f"({', '.join(completas)}).")
    out.append(f"Elecciones: {len(filas)} en alcance; {est(filas, 'COMPLETA_Y_CUADRA')} cuadran, "
               f"{est(filas, 'EN_REPO_NO_CUADRA')} en repo sin cuadrar, {est(filas, 'PENDIENTE_DE_REAGREGAR')} pendientes, "
               f"{est(filas, 'HUECO')} huecos.")
    return "\n".join(out)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--salida", default=str(ROOT / "docs/ESTUDIOS/T176_HISTORICO_AUTONOMICO"))
    a = ap.parse_args()
    filas = medir()
    d = Path(a.salida)
    d.mkdir(parents=True, exist_ok=True)
    with open(d / "COBERTURA.csv", "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=CAMPOS, lineterminator="\n")
        w.writeheader()
        w.writerows(filas)
    print(resumen(filas))


if __name__ == "__main__":
    main()
