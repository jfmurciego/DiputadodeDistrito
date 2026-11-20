#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Votos por distrito de una autonómica vigente para la doble vuelta (P75), desde los adaptadores de T-426.

PROYECTO: Diputado de Distrito
VERSIÓN: 1.0.0 · FECHA: 2026-11-20 · ESTADO: candidato
CAMBIOS: 1.0.0: fichero nuevo.
ANTERIOR: ninguna (fichero nuevo)
MOTIVO: T-426/T-427 (D-183). aut03 (Asturias) solo publica por municipio; aut14 (Murcia), por sección.
QUÉ HACE: lleva `secciones.csv` (section_id, party, votes; Murcia, nivel sección) o `municipios.csv` (municipio, partido, votos;
  Asturias, nivel municipio) al formato de T-427: `<aut>_partidos.csv` (distrito, partido, votos; distrito = el de la composición
  del run M08 vigente) y `MANIFEST.json` (huellas, nivel, aproximado_en_distrito, cuadre). Nivel municipio: el voto de cada partido
  se reparte entre las secciones del municipio (composición del run) en proporción a su población y se redondea por mayor resto,
  partido a partido, a lo largo de los distritos (como `reagregacion_historico.redondear`), así que la suma es exacta y no se inventa ningún voto; cada distrito queda marcado `aproximado_en_distrito`.
NO HACE: descargar, lanzar ni publicar.
Uso: python herramientas/doble_vuelta_votos_aut.py --aut aut03 --eleccion 202305 --run 43742340201 --entrada CSV --nivel municipio --salida DIR [--fuentes K=SHA ...]
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def mayor_resto(valores: dict) -> dict:
    """Como `reagregacion_historico.mayor_resto` (no se importa: arrastra shapely): enteros con la misma suma; desempate por clave."""
    total = round(sum(valores.values()))
    base = {k: int(x) for k, x in valores.items()}
    for k in sorted(valores, key=lambda k: (-(valores[k] - base[k]), str(k)))[:max(total - sum(base.values()), 0)]:
        base[k] += 1
    return base


def construir(aut: str, eleccion: str, run: str, entrada: Path, nivel: str, salida: Path,
              fuentes: dict | None = None, fuera: dict | None = None, raiz: Path = ROOT) -> dict:
    comp_path = raiz / f"datos/composicion/runs/{aut}_{run}.csv"
    with comp_path.open(encoding="utf-8", newline="") as f:
        comp = [(r["seccion"], r["distrito"], int(r["poblacion"])) for r in csv.DictReader(f)]
    dist_de = {s: d for s, d, _ in comp}
    por_distrito: dict[str, dict[str, float]] = defaultdict(lambda: defaultdict(float))
    total_in = 0
    with entrada.open(encoding="utf-8", newline="") as f:
        filas = list(csv.DictReader(f))
    if nivel == "seccion":
        for r in filas:
            s, p, v = r["section_id"], r["party"], int(r["votes"])
            if s not in dist_de:
                raise ValueError(f"sección {s} fuera de la composición del run")
            por_distrito[dist_de[s]][p] += v
            total_in += v
    elif nivel == "municipio":
        secs = defaultdict(list)
        for s, d, pob in comp:
            secs[s[:5]].append((s, d, pob))
        for r in filas:
            m, p, v = r["municipio"], r["partido"], int(r["votos"])
            if m not in secs:
                raise ValueError(f"municipio {m} sin secciones en la composición del run")
            lista = secs[m]
            pesos = [max(pob, 0) for _, _, pob in lista]
            tot = sum(pesos)
            for (s, d, _), w in zip(lista, pesos if tot else [1] * len(lista)):
                por_distrito[d][p] += v * w / (tot or len(lista))
            total_in += v
    else:
        raise ValueError("nivel: seccion o municipio")
    ents: dict[str, dict[str, int]] = {d: {} for d in por_distrito}
    for p in sorted({p for r in por_distrito.values() for p in r}):  # mayor resto, partido a partido, a lo largo de los distritos
        for d, x in mayor_resto({d: r.get(p, 0.0) for d, r in por_distrito.items()}).items():
            ents[d][p] = x
    por_distrito = ents
    total_out = sum(v for d in por_distrito.values() for v in d.values())
    if total_out != total_in:
        raise ValueError(f"cuadre roto: {total_in} != {total_out}")
    salida.mkdir(parents=True, exist_ok=True)
    with (salida / f"{aut}_partidos.csv").open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["distrito", "partido", "votos"])
        for d in sorted(por_distrito, key=lambda x: int(x)):
            for p, v in sorted(por_distrito[d].items()):
                if v:
                    w.writerow([d, p, v])
    man = {"schema": "ddd.doble-vuelta-votos-aut/1.0", "territorio": aut, "eleccion": eleccion, "run_m08": run,
           "composicion_ruta": f"datos/composicion/runs/{aut}_{run}.csv", "composicion_sha256": sha256(comp_path), "aproximado_en_distrito": nivel == "municipio", "nivel": nivel,
           "entrada_sha256": sha256(entrada), "fuentes": {"composicion": sha256(comp_path), **(fuentes or {})},
           "cuadre": {"ok": True, "votos_entrada": total_in, "votos_salida": total_out, "distritos": len(por_distrito),
                      "fuera_de_distritos": fuera or {}}}
    (salida / "MANIFEST.json").write_text(json.dumps(man, ensure_ascii=False, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    return man


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--aut", required=True)
    ap.add_argument("--eleccion", required=True)
    ap.add_argument("--run", required=True)
    ap.add_argument("--entrada", type=Path, required=True)
    ap.add_argument("--nivel", choices=["seccion", "municipio"], required=True)
    ap.add_argument("--salida", type=Path, required=True)
    ap.add_argument("--fuentes", type=Path, help="JSON con las huellas de las fuentes (MANIFEST del adaptador)")
    a = ap.parse_args(argv)
    j = json.loads(a.fuentes.read_text(encoding="utf-8")) if a.fuentes else {}
    fu = j.get("fuentes") or ({"fuente": j["fuente"]} if "fuente" in j else None)
    # votos del total oficial que no llegan a ningún distrito, declarados (C.E.R.A./ausentes y candidaturas sin desglosar)
    fuera = {k: j[k] for k in ("otros_votos", "cera_votos_a_candidaturas_excluidos", "votos_ausentes_no_repartidos", "votos_a_candidaturas") if k in j}
    m = construir(a.aut, a.eleccion, a.run, a.entrada, a.nivel, a.salida, fu, fuera)
    print(json.dumps(m["cuadre"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
