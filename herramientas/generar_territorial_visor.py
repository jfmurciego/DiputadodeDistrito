#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Vista territorial del visor v2, sin resultados electorales (T-119).

PROYECTO: Diputado de Distrito
VERSIÓN: 1.1.0 · FECHA: 2026-11-09 · ESTADO: candidato
ANTERIOR: legacy/herramientas/generar_territorial_visor_v1.0.0_20261109b.py
CAMBIOS 1.1.0 (T-135): el número de distrito sale en numeración pública 1..K (no existe el 0).
QUÉ HACE: por provincia, copia del M06 publicado (distritos.geojson del paquete de datos abiertos, con el sha256 de INDEX.json
  verificado) lo que describe el reparto territorial: población, objetivo, desviación, suelo, techo, exención de suelo
  (suelo 0 en el M06), nº de secciones y municipios (con topónimo español de datos/distritos/toponimos_es.csv; si no hay,
  nombre INE de municipios_ine_2025.csv). El nombre del distrito sale de datos/distritos/nombres_<territorio>.csv.
  Escribe un único JSON; no usa resultados ni votos y funciona donde no hay M08.
Uso: python herramientas/generar_territorial_visor.py --datos DIR_DATOS_ABIERTOS --salida visor/v2/datos/territorial.json
  [--distritos datos/distritos]
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from numeracion_publica import numero_publico  # noqa: E402

RAIZ = Path(__file__).resolve().parent.parent


def _csv(ruta: Path) -> list[dict]:
    with ruta.open(encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def nombres_municipio(distritos: Path) -> dict[str, str]:
    ine = {r["codigo_ine"]: r["nombre_ine"] for r in _csv(distritos / "municipios_ine_2025.csv")}
    ine.update({r["codigo_ine"]: r["nombre_es"] for r in _csv(distritos / "toponimos_es.csv")})
    return ine


def generar(datos: Path, salida: Path, distritos: Path) -> int:
    indice = json.loads((datos / "INDEX.json").read_text("utf-8"))
    mun = nombres_municipio(distritos)
    provs: dict[str, dict] = {}
    for t, e in sorted(indice["territorios"].items()):
        gj_bytes = (datos / e["geojson"]["ruta"]).read_bytes()
        if hashlib.sha256(gj_bytes).hexdigest() != e["geojson"]["sha256"]:
            raise SystemExit(f"{t}: el GeoJSON no coincide con el sha256 de INDEX.json")
        nom = {int(r["district_id"]): r["nombre_distrito"] for r in _csv(distritos / f"nombres_{t}.csv")} \
            if (distritos / f"nombres_{t}.csv").exists() else {}
        filas, cod = [], None
        for f in sorted(json.loads(gj_bytes)["features"], key=lambda f: f["properties"]["district_id"]):
            p = f["properties"]
            cod = cod or str(p["province_codes"]).split("|")[0].strip()[:2]
            codes = [c.split(":")[0].strip() for c in str(p["municipality_codes"]).split("|")]
            falta = [c for c in codes if c not in mun]
            if falta:
                raise SystemExit(f"{t}: municipios sin nombre en datos/distritos: {falta[:3]}")
            filas.append({"d": numero_publico(p["district_id"]), "n": nom.get(int(p["district_id"])), "p": int(p["district_pop"]),
                          "o": round(p["target"], 1), "dev": round(p["relative_deviation"], 4),
                          "suelo": round(p["population_floor"], 1), "techo": round(p["population_cap"], 1),
                          "exenta": float(p["population_floor"]) == 0.0, "tol": bool(p["within_target_tolerance"]),
                          "hard": bool(p["within_hard_bounds"]), "s": int(p["section_count"]),
                          "m": sorted(mun[c] for c in codes)})
        provs[cod] = {"territorio": t, "sha256_m06": e["sha256_origen"], "distritos": filas}
    salida.parent.mkdir(parents=True, exist_ok=True)
    salida.write_text(json.dumps({"schema": "ddd.territorial-visor/1.0", "provincias": provs}, ensure_ascii=False,
                                 separators=(",", ":")), "utf-8")
    print(f"vista territorial de {len(provs)} provincias")
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--datos", type=Path, required=True)
    ap.add_argument("--salida", type=Path, required=True)
    ap.add_argument("--distritos", type=Path, default=RAIZ / "datos" / "distritos")
    a = ap.parse_args(argv)
    return generar(a.datos, a.salida, a.distritos)


if __name__ == "__main__":
    sys.exit(main())
